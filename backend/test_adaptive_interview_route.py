"""Route-level tests for POST /adaptive-interview.

The service-level tests exercise ``claim_answer`` and ``evaluate_claimed_answer``
separately. This module drives the route the browser actually calls, so the
claim -> evaluate -> generate sequence is covered as one request: a first
submission used to fail with 409 because the request read back its own
brand-new claim as another worker's in-flight evaluation.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import HTTPException

import api.interview as interview_api
import services.interview_service as interview_service_module
from database import SessionLocal
from models import InterviewQuestion, User
from schemas import (
    EvaluationLevel,
    EvaluationRequest,
    EvaluationResponse,
    QuestionStatus,
)
from services.interview_service import InterviewService

pytestmark = pytest.mark.usefixtures("seeded_workflow")


SESSION_ID = 23
QUESTION_ID = 44
USER_ID = 9
NEXT_QUESTION = "How would you scale that design to ten times the traffic?"


def _evaluation():
    return EvaluationResponse(
        score=8,
        level=EvaluationLevel.STRONG,
        strengths=["Clear reasoning"],
        weaknesses=["Needs more edge cases"],
        feedback="Good answer.",
        concept_gaps=["Failure handling"],
        follow_up_question="How would you test it?",
    )


@pytest.fixture
def wired_route(monkeypatch):
    """Point the route at a manager-less service with the AI calls stubbed."""
    service = InterviewService.__new__(InterviewService)
    monkeypatch.setattr(interview_api, "_get_interview_service", lambda: service)
    monkeypatch.setattr(
        interview_service_module,
        "evaluate_answer_with_llm",
        lambda **kwargs: _evaluation(),
    )
    monkeypatch.setattr(
        InterviewService,
        "_generate_question_text",
        lambda self, **kwargs: NEXT_QUESTION,
    )
    return service


def _current_user() -> User:
    db = SessionLocal()
    try:
        return db.get(User, USER_ID)
    finally:
        db.close()


def _call(answer: str) -> dict:
    return interview_api.adaptive_interview(
        EvaluationRequest(
            answer=answer,
            session_id=SESSION_ID,
            question_id=QUESTION_ID,
        ),
        current_user=_current_user(),
        db=None,
    )


def test_first_submission_returns_the_evaluation_and_the_next_question(wired_route):
    response = _call("A thorough answer about indexes.")

    assert response["evaluation"]["score"] == 8
    assert response["next_question"] == NEXT_QUESTION
    assert response["question_id"] != QUESTION_ID
    assert response["question_number"] == 4

    db = SessionLocal()
    try:
        answered = db.get(InterviewQuestion, QUESTION_ID)
        assert answered.status == QuestionStatus.EVALUATED.value
        assert answered.answer == "A thorough answer about indexes."
        assert answered.score == 8
    finally:
        db.close()


def test_resubmitting_the_same_answer_replays_the_same_next_question(wired_route):
    first = _call("A thorough answer about indexes.")
    # A double click, or a client retry after a dropped response.
    second = _call("A thorough answer about indexes.")

    assert second["next_question"] == first["next_question"]
    assert second["question_id"] == first["question_id"]
    assert second["evaluation"]["score"] == 8

    db = SessionLocal()
    try:
        # The replay must not create a second question for the same slot.
        assert db.query(InterviewQuestion).filter_by(
            session_id=SESSION_ID, question_number=4
        ).count() == 1
    finally:
        db.close()


def test_a_different_answer_for_an_answered_question_is_rejected(wired_route):
    _call("A thorough answer about indexes.")

    with pytest.raises(HTTPException) as excinfo:
        _call("A completely different answer.")

    assert excinfo.value.status_code == 409
