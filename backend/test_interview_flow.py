import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

from evaluator import build_report_pdf
from interview.interview_manager import InterviewManager
from services.interview_service import InterviewService


class DummyRAG:
    def ensure_cv_index(self, user_id, cv_path):
        return None

    def ensure_knowledge_index(self, role):
        return None

    def retrieve_hybrid(self, query):
        return [
            SimpleNamespace(chunk=SimpleNamespace(role="user", content="cv context")),
            SimpleNamespace(chunk=SimpleNamespace(role="knowledge", content="knowledge context")),
        ]


class DummyPromptBuilder:
    def build_evaluation_prompt(self, question, answer, cv_chunks, knowledge_chunks):
        return "evaluation prompt"

    def build_question_prompt(self, role, difficulty, cv_chunks, knowledge_chunks):
        return "next question prompt"


class DummyQueryBuilder:
    def build(self, analysis, role, difficulty):
        return "query"


class DummyProvider:
    def evaluate_answer(self, prompt):
        return '{"score": 7, "level": "medium", "strengths": ["Clear"], "weaknesses": ["Needs detail"], "feedback": "Good", "concept_gaps": ["trade-offs"], "follow_up_question": "How would you improve it?"}'

    def generate_question(self, prompt):
        return "How would you scale this solution?"


class DummyStorage:
    def get_active_cv(self, user_id):
        return Path("dummy.pdf")


class DummyParser:
    def parse(self, file_path, role, document_type):
        return SimpleNamespace(content="experience with backend systems")


def test_interview_service_reuses_a_single_manager():
    first_service = InterviewService()
    second_service = InterviewService()

    assert first_service.manager is second_service.manager


def test_submit_answer_returns_evaluation_and_next_question():
    manager = InterviewManager()
    manager._sessions = {
        101: {
            "role": "backend engineer",
            "current_difficulty": 3,
            "current_question": "What is dependency injection?",
            "questions": ["What is dependency injection?"],
            "answers": [],
            "question_number": 1,
            "evaluations": [],
        }
    }
    manager._question_to_session = {101: 101}
    manager._next_question_id = 102
    manager.rag = DummyRAG()
    manager.prompt_builder = DummyPromptBuilder()
    manager.query_builder = DummyQueryBuilder()
    manager.provider = DummyProvider()
    manager.storage = DummyStorage()
    manager.parser = DummyParser()

    response = manager.submit_answer(user_id=101, session_id=101, question_id=101, answer="I would use dependency injection")

    assert response["evaluation"]["score"] == 7
    assert response["evaluation"]["level"] == "medium"
    assert response["next_question"] == "How would you scale this solution?"
    assert response["next_difficulty"] == "medium"


def test_finish_interview_returns_summary_and_pdf_path(monkeypatch):
    manager = InterviewManager()
    manager._sessions = {
        202: {
            "role": "backend engineer",
            "questions": ["Question 1"],
            "answers": ["Answer 1"],
            "evaluations": [{"score": 8, "feedback": "Great"}],
        }
    }

    monkeypatch.setattr(
        "interview.interview_manager.summarize_session",
        lambda request: SimpleNamespace(
            overall_score=8,
            overall_strengths=["Strong"],
            overall_weaknesses=["Needs depth"],
            hiring_recommendation="Hire",
        ),
    )
    monkeypatch.setattr("interview.interview_manager.build_report_pdf", lambda request: b"pdf-bytes")

    response = manager.finish_interview(session_id=202)

    assert response["recommendation"] == "Hire"
    assert response["final_score"] == 8.0
    assert response["summary"].startswith("Overall score")
    assert response["pdf_path"].endswith(".pdf")


def test_build_report_pdf_accepts_dict_payload():
    payload = {
        "role": "backend engineer",
        "score": 8,
        "overall_score": 8,
        "overall_strengths": ["Strong"],
        "overall_weaknesses": ["Needs depth"],
        "hiring_recommendation": "Hire",
        "questions": ["Question 1"],
        "answers": ["Answer 1"],
        "evaluations": [{"score": 8, "feedback": "Great"}],
    }

    pdf_bytes = build_report_pdf(payload)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b'%PDF')
