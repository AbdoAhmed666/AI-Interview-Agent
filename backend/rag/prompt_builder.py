"""
Prompt building utilities.
"""

from rag.models import DocumentChunk


class PromptBuilder:
    """Build prompts for evaluation."""
    def _build_context(
        self,
        chunks: list[DocumentChunk],
    ) -> str:
        """
        Build a formatted context string from retrieved chunks.
        """

        if not chunks:
            return "No relevant context found."

        return "\n\n".join(
            chunk.content.strip()
            for chunk in chunks
        )

    def build_question_prompt(
        self,
        role: str,
        difficulty: str,
        cv_chunks: list[DocumentChunk],
        knowledge_chunks: list[DocumentChunk],
    ) -> str:

        cv_context = self._build_context(
            cv_chunks
        )

        knowledge_context = self._build_context(
            knowledge_chunks
        )

        return f"""
                You are an experienced Senior Software Engineer
                conducting a real technical interview.

                Your goal is to evaluate the candidate's real-world
                engineering experience.

                Role:
                {role}

                Interview Difficulty:
                {difficulty}

                ==========================
                Candidate CV Context
                ==========================

                {cv_context}

                ==========================
                Knowledge Base Context
                ==========================

                {knowledge_context}

                Instructions:

                1. Prioritize the candidate's projects,
                technologies and experience from the CV.

                2. If the candidate worked on a project,
                ask about implementation details.

                3. Ask questions that require reasoning,
                not memorization.

                4. Avoid generic textbook questions.

                5. If the CV mentions FastAPI,
                Docker, JWT or PostgreSQL,
                prefer asking about those.

                6. Use the knowledge base only
                to verify technical correctness.

                7. Generate exactly ONE interview question.

                Return only the question.
                """

    def build_evaluation_prompt(
        self,
        question: str,
        answer: str,
        cv_chunks: list[DocumentChunk],
        knowledge_chunks: list[DocumentChunk],
    ) -> str:
        cv_context = self._build_context(
            cv_chunks
        )

        knowledge_context = self._build_context(
            knowledge_chunks
        )

        return f"""
                You are an experienced Senior Software Engineer
                conducting a real technical interview.

                Your goal is to evaluate the candidate's real-world
                engineering experience.

                ==========================
                Candidate CV Context
                ==========================

                {cv_context}

                ==========================
                Knowledge Base Context
                ==========================

                {knowledge_context}

                Question:
                {question}

                Candidate Answer:
                {answer}

                Instructions:

                1. Evaluate the technical correctness.
                2. Consider the candidate's experience from the CV.
                3. Use the knowledge base to verify correctness.
                4. Identify strengths.
                5. Identify weaknesses.
                6. Identify missing concepts.
                7. Suggest the next interview difficulty.
                8. Suggest one follow-up question.
                9. Return JSON only.

                Expected JSON:

                {{
                "score": 0,
                "level": "",
                "strengths": [],
                "weaknesses": [],
                "feedback": "",
                "concept_gaps": [],
                "follow_up_question": ""
                }}
                """
