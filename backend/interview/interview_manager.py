"""High-level interview orchestration."""

import json
import re
from typing import Any

from adaptive_engine import AdaptiveEngine
from cv.analyzer import CVAnalyzer
from cv.eligibility import InterviewEligibility
from cv.storage import CVStorage
from evaluator import build_report_pdf, summarize_session
from llm_provider import get_provider
from rag.parser import DocumentParser
from rag.prompt_builder import PromptBuilder
from rag.query_builder import QueryBuilder
from rag.rag_service import RAGService
from schemas import EvaluationResponse, SessionSummaryRequest


class InterviewManager:
    """Coordinate interview startup and adaptive follow-up questions."""

    def __init__(self) -> None:
        self.storage = CVStorage()
        self.analyzer = CVAnalyzer()
        self.eligibility = InterviewEligibility()
        self.rag = RAGService()
        self.parser = DocumentParser()
        self.prompt_builder = PromptBuilder()
        self.query_builder = QueryBuilder()
        self.provider = get_provider()
        self._sessions: dict[int, dict[str, Any]] = {}
        self._question_to_session: dict[int, int] = {}
        self._next_session_id = 1
        self._next_question_id = 1

    def start_interview(self, user_id: int, role: str) -> dict[str, Any]:
        """Start a new interview and return the first question and session metadata."""
        if not self.storage.has_cv(user_id):
            raise FileNotFoundError("Please upload your CV first.")

        cv_path = self.storage.get_active_cv(user_id)
        document = self.parser.parse(
            file_path=cv_path,
            role="user",
            document_type="cv",
        )
        analysis = self.analyzer.analyze(document.content)

        eligibility_result = self.eligibility.evaluate(analysis, role)
        if not eligibility_result.eligible:
            return {
                "eligible": False,
                "message": eligibility_result.message,
                "score": eligibility_result.score,
                "recommended_roles": [
                    item.role for item in eligibility_result.recommended_roles
                ],
            }

        difficulty = "medium"
        difficulty_value = 3
        query = self.query_builder.build(analysis, role, difficulty)

        self.rag.ensure_cv_index(user_id, cv_path)
        self.rag.ensure_knowledge_index(role)

        results = self.rag.retrieve_hybrid(query)

        prompt = self.prompt_builder.build_question_prompt(
            role=role,
            difficulty=difficulty,
            cv_chunks=[item.chunk for item in results if item.chunk.role == "user"],
            knowledge_chunks=[item.chunk for item in results if item.chunk.role != "user"],
        )
        first_question = self.provider.generate_question(prompt)

        session_id = self._next_session_id
        self._next_session_id += 1
        question_id = self._next_question_id
        self._next_question_id += 1

        self._sessions[session_id] = {
            "user_id": user_id,
            "role": role,
            "current_difficulty": difficulty_value,
            "current_question": first_question,
            "questions": [first_question],
            "answers": [],
            "question_number": 1,
            "session_id": session_id,
            "question_id": question_id,
            "evaluations": [],
        }
        self._question_to_session[question_id] = session_id

        return {
            "eligible": True,
            "role": role,
            "difficulty": difficulty_value,
            "next_question": first_question,
            "first_question": first_question,
            "question": first_question,
            "session_id": session_id,
            "question_id": question_id,
        }

    def submit_answer(self, user_id: int, session_id: int, question_id: int, answer: str) -> dict[str, Any]:
        """Evaluate an answer, adapt the next difficulty, and generate the next question."""
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Unknown session id: {session_id}")

        if self._question_to_session.get(question_id) != session_id:
            raise KeyError(f"Unknown question id: {question_id}")

        role = session["role"]
        current_difficulty = int(session["current_difficulty"])
        current_question = session["current_question"]

        cv_path = self.storage.get_active_cv(user_id)
        document = self.parser.parse(
            file_path=cv_path,
            role="user",
            document_type="cv",
        )
        analysis = self.analyzer.analyze(document.content)

        self.rag.ensure_cv_index(user_id, cv_path)
        self.rag.ensure_knowledge_index(role)

        query = self.query_builder.build(analysis, role, self._difficulty_label(current_difficulty))
        results = self.rag.retrieve_hybrid(query)

        evaluation_prompt = self.prompt_builder.build_evaluation_prompt(
            question=current_question,
            answer=answer,
            cv_chunks=[item.chunk for item in results if item.chunk.role == "user"],
            knowledge_chunks=[item.chunk for item in results if item.chunk.role != "user"],
        )
        raw_evaluation = self.provider.evaluate_answer(evaluation_prompt)
        payload = self._parse_evaluation_payload(raw_evaluation)
        evaluation = EvaluationResponse.model_validate(payload).model_dump()

        level = str(payload.get("level", "medium")).lower()
        next_difficulty_int, _ = AdaptiveEngine.get_next_difficulty(level, current_difficulty)
        next_difficulty = self._difficulty_label(next_difficulty_int)

        next_query = self.query_builder.build(analysis, role, next_difficulty)
        next_results = self.rag.retrieve_hybrid(next_query)
        next_prompt = self.prompt_builder.build_question_prompt(
            role=role,
            difficulty=next_difficulty,
            cv_chunks=[item.chunk for item in next_results if item.chunk.role == "user"],
            knowledge_chunks=[item.chunk for item in next_results if item.chunk.role != "user"],
        )
        next_question = self.provider.generate_question(next_prompt)

        new_question_id = self._next_question_id
        self._next_question_id += 1
        self._question_to_session[new_question_id] = session_id
        session["current_question"] = next_question
        session["current_difficulty"] = next_difficulty_int
        session["questions"].append(next_question)
        session["answers"].append(answer)
        session["question_number"] = int(session["question_number"]) + 1
        session["question_id"] = new_question_id
        session["evaluations"].append(evaluation)

        return {
            "evaluation": evaluation,
            "next_question": next_question,
            "next_difficulty": next_difficulty,
            "difficulty": next_difficulty_int,
            "question_id": new_question_id,
            "session_id": session_id,
            "question_number": session["question_number"],
        }

    def finish_interview(self, session_id: int) -> dict[str, Any]:
        """Return a summary, recommendation, final score, and PDF path for a completed interview."""
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Unknown session id: {session_id}")

        evaluations = session.get("evaluations", [])
        if not evaluations:
            summary = "Overall score: 0/10"
            recommendation = "Hold"
            final_score = 0.0
        else:
            final_score = round(sum(item["score"] for item in evaluations) / len(evaluations), 1)
            if final_score >= 9:
                recommendation = "Strong Hire"
            elif final_score >= 6:
                recommendation = "Hire"
            elif final_score >= 4:
                recommendation = "Hold"
            else:
                recommendation = "Reject"
            summary = f"Overall score: {final_score}/10"

        summary_request = SessionSummaryRequest(
            role=session["role"],
            questions=session.get("questions", []),
            answers=session.get("answers", []),
            evaluations=evaluations,
        )
        summary_payload = summarize_session(summary_request)
        summary_text = (
            f"Overall score: {summary_payload.overall_score}/10\n"
            f"Strengths: {', '.join(summary_payload.overall_strengths) or 'None'}\n"
            f"Weaknesses: {', '.join(summary_payload.overall_weaknesses) or 'None'}"
        )
        pdf_bytes = build_report_pdf(
            {
                "role": session["role"],
                "score": int(final_score),
                "overall_score": int(final_score),
                "overall_strengths": list(summary_payload.overall_strengths),
                "overall_weaknesses": list(summary_payload.overall_weaknesses),
                "hiring_recommendation": recommendation,
                "questions": session.get("questions", []),
                "answers": session.get("answers", []),
                "evaluations": evaluations,
            }
        )
        pdf_path = f"D:/projects/AI-Interview-Agent/backend/temp/interview_{session_id}.pdf"
        import os
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        with open(pdf_path, "wb") as handle:
            handle.write(pdf_bytes)

        return {
            "summary": summary_text,
            "recommendation": recommendation,
            "final_score": final_score,
            "pdf_path": pdf_path,
        }

    @staticmethod
    def _difficulty_label(difficulty: int) -> str:
        if difficulty <= 2:
            return "easy"
        if difficulty >= 4:
            return "hard"
        return "medium"

    @staticmethod
    def _parse_evaluation_payload(raw_response: str) -> dict[str, Any]:
        cleaned = raw_response.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.IGNORECASE)
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]

        return json.loads(cleaned)

    def _generate_first_question(self, role: str) -> str:
        """Generate the first interview question."""
        raise NotImplementedError