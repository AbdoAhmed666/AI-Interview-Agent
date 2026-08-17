from dataclasses import dataclass, field

from rag.models import RetrievalResult


@dataclass(slots=True)
class InterviewContext:
    """
    Runtime interview state.
    """

    user_id: int

    role: str

    difficulty: str

    current_question: str

    question_number: int

    retrieved_cv: list[RetrievalResult] = field(
        default_factory=list
    )

    retrieved_knowledge: list[RetrievalResult] = field(
        default_factory=list
    )