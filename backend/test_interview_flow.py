import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from evaluator import build_report_pdf
from services.interview_service import InterviewService

# Constructing a real InterviewService loads the embedding model (via the
# shared InterviewManager -> RAGService). Skip that single test when the model
# is unavailable (e.g. offline CI) instead of failing the run.
try:
    from rag.embeddings import EmbeddingGenerator

    EmbeddingGenerator()
    _MODEL_AVAILABLE = True
except Exception:  # pragma: no cover - environment dependent
    _MODEL_AVAILABLE = False


@pytest.mark.skipif(not _MODEL_AVAILABLE, reason="requires the embedding model")
def test_interview_service_reuses_a_single_manager():
    first_service = InterviewService()
    second_service = InterviewService()

    assert first_service.manager is second_service.manager


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
