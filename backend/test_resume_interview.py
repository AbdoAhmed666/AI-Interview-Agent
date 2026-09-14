"""Tests for resuming an unfinished interview after the browser was reloaded.

Interview state is durable in PostgreSQL, but the client used to keep the
session id only in React state: a refresh lost the interview and left the row
stranded as IN_PROGRESS forever. ``resume_interview`` rebuilds the client's
view from the authoritative rows and recovers a session that stopped part-way
through the workflow.
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import api.interview as interview_api
from database import SessionLocal
from models import InterviewQuestion, InterviewSession, User
from schemas import (
    EvaluationLevel,
    EvaluationResponse,
    QuestionStatus,
    SessionStatus,
)
from services.interview_service import InterviewService
import services.interview_service as interview_service_module

pytestmark = pytest.mark.usefixtures("seeded_workflow")


SESSION_ID = 23
QUESTION_ID = 44
USER_ID = 9
OTHER_USER_ID = 10
GENERATED_QUESTION = "What would you shard on, and why?"


def _service():
    return InterviewService.__new__(InterviewService)


def _evaluation():
    return EvaluationResponse(
        score=7,
        level=EvaluationLevel.STRONG,
        strengths=["Recovered"],
        weaknesses=[],
        feedback="Recovered evaluation.",
        concept_gaps=[],
        follow_up_question="And at scale?",
    )


@pytest.fixture
def stubbed_ai(monkeypatch):
    monkeypatch.setattr(
        interview_service_module,
        "evaluate_answer_with_llm",
        lambda **kwargs: _evaluation(),
    )
    monkeypatch.setattr(
        InterviewService,
        "_generate_question_text",
        lambda self, **kwargs: GENERATED_QUESTION,
    )


def _set_question(**fields):
    db = SessionLocal()
    try:
        question = db.get(InterviewQuestion, QUESTION_ID)
        for key, value in fields.items():
            setattr(question, key, value)
        db.commit()
    finally:
        db.close()


def _set_session_status(status):
    db = SessionLocal()
    try:
        db.get(InterviewSession, SESSION_ID).status = status
        db.commit()
    finally:
        db.close()


def test_no_unfinished_interview_reports_inactive():
    # User 10 owns only a COMPLETED session.
    assert _service().resume_interview(OTHER_USER_ID) == {"active": False}


def test_completed_sessions_are_never_resumed():
    _set_session_status(SessionStatus.COMPLETED.value)

    assert _service().resume_interview(USER_ID) == {"active": False}


def test_resume_returns_the_open_question_and_the_last_evaluation():
    result = _service().resume_interview(USER_ID)

    assert result["active"] is True
    assert result["session_id"] == SESSION_ID
    assert result["role"] == "backend"
    assert result["status"] == QuestionStatus.ACTIVE.value
    assert result["question_id"] == QUESTION_ID
    assert result["question"] == "Q3?"
    assert result["question_number"] == 3
    assert result["total_questions"] == 5
    assert result["difficulty"] == 3
    # The feedback for question 2 survives the reload.
    assert result["evaluation"]["score"] == 8


def test_resume_finishes_an_evaluation_that_never_landed(stubbed_ai):
    # The browser died between claiming the answer and persisting its result.
    _set_question(
        status=QuestionStatus.EVALUATING.value,
        answer="an answer that was never evaluated",
        answer_submitted_at=datetime.utcnow() - timedelta(minutes=10),
    )

    result = _service().resume_interview(USER_ID)

    assert result["status"] == QuestionStatus.ACTIVE.value
    assert result["question"] == GENERATED_QUESTION
    assert result["question_number"] == 4
    # The recovered evaluation is the one the candidate never got to see.
    assert result["evaluation"]["score"] == 7

    db = SessionLocal()
    try:
        assert db.get(InterviewQuestion, QUESTION_ID).status == (
            QuestionStatus.EVALUATED.value
        )
    finally:
        db.close()


def test_resume_waits_for_an_evaluation_that_is_still_in_flight(monkeypatch):
    monkeypatch.setattr(
        interview_service_module,
        "evaluate_answer_with_llm",
        lambda **kwargs: pytest.fail("must not evaluate behind a live worker"),
    )
    _set_question(
        status=QuestionStatus.EVALUATING.value,
        answer="an answer being evaluated right now",
        answer_submitted_at=datetime.utcnow(),
    )

    result = _service().resume_interview(USER_ID)

    assert result["status"] == InterviewService.RESUME_PENDING_EVALUATION
    # The question stays on screen instead of the interview disappearing.
    assert result["question"] == "Q3?"
    assert result["question_id"] == QUESTION_ID


def test_resume_reports_a_session_that_is_ready_to_finish():
    _set_question(
        status=QuestionStatus.EVALUATED.value,
        answer="the last answer",
        evaluation={
            "score": 9,
            "level": "strong",
            "strengths": [],
            "weaknesses": [],
            "feedback": "Done",
            "concept_gaps": [],
            "follow_up_question": "",
        },
        score=9,
        feedback="Done",
        evaluated_at=datetime.utcnow(),
    )
    _set_session_status(SessionStatus.READY_TO_FINISH.value)

    result = _service().resume_interview(USER_ID)

    assert result["active"] is True
    assert result["status"] == SessionStatus.READY_TO_FINISH.value
    assert result["question"] is None
    assert result["evaluation"]["score"] == 9


def test_route_serves_the_resumable_interview(monkeypatch):
    service = _service()
    monkeypatch.setattr(interview_api, "_get_interview_service", lambda: service)

    db = SessionLocal()
    try:
        user = db.get(User, USER_ID)
    finally:
        db.close()

    response = interview_api.active_interview(current_user=user)

    assert response["active"] is True
    assert response["session_id"] == SESSION_ID
    assert response["question_id"] == QUESTION_ID


def test_route_reports_nothing_to_resume(monkeypatch):
    service = _service()
    monkeypatch.setattr(interview_api, "_get_interview_service", lambda: service)

    db = SessionLocal()
    try:
        user = db.get(User, OTHER_USER_ID)
    finally:
        db.close()

    assert interview_api.active_interview(current_user=user) == {"active": False}
