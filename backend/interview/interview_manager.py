"""Holder for the stateless AI/domain components used by the interview service."""

from cv.analyzer import CVAnalyzer
from cv.eligibility import InterviewEligibility
from cv.storage import CVStorage
from llm_provider import get_provider
from rag.parser import DocumentParser
from rag.prompt_builder import PromptBuilder
from rag.query_builder import QueryBuilder
from rag.rag_service import RAGService


class InterviewManager:
    """Own the stateless AI/domain helpers used to build interview content.

    PostgreSQL is the sole authority for interview workflow state, so this
    class deliberately holds no sessions, questions, id counters, or any other
    process-local workflow bookkeeping. It exists only to construct and share
    the stateless collaborators (CV storage/parsing/analysis, eligibility, RAG,
    prompt/query building, and the LLM provider) that
    :class:`services.interview_service.InterviewService` drives.
    """

    def __init__(self) -> None:
        self.storage = CVStorage()
        self.analyzer = CVAnalyzer()
        self.eligibility = InterviewEligibility()
        self.rag = RAGService()
        self.parser = DocumentParser()
        self.prompt_builder = PromptBuilder()
        self.query_builder = QueryBuilder()
        self.provider = get_provider()
