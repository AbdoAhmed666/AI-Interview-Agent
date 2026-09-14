"""Starting a new interview retires whatever the candidate left open.

An interview the candidate walked away from used to stay IN_PROGRESS forever:
it competed with the real session for ``resume_interview`` and permanently
dragged down the dashboard's completion rate. Deliberately starting another
interview now moves it to the terminal ABANDONED status.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from conftest import make_fake_interview_service
from database import SessionLocal
from models import InterviewAuditLog, InterviewQuestion, InterviewSession
from schemas import SessionStatus
from services.interview_service import AnswerClaimConflict

pytestmark = pytest.mark.usefixtures("seeded_workflow")


OPEN_SESSION_ID = 23
OPEN_QUESTION_ID = 44
COMPLETED_SESSION_ID = 15
OTHER_USER_SESSION_ID = 24
USER_ID = 9
OTHER_USER_ID = 10


@pytest.fixture
def started_interview():
    """Start a second interview for user 9 and clean it up afterwards."""
    service = make_fake_interview_service()
    result = service.start_interview(user_id=USER_ID, role="backend")

    yield service, result

    db = SessionLocal()
    try:
        session_id = result["session_id"]
        db.query(InterviewAuditLog).filter(
            InterviewAuditLog.session_id == session_id
        ).delete(synchronize_session=False)
        db.query(InterviewQuestion).filter(
            InterviewQuestion.session_id == session_id
        ).delete(synchronize_session=False)
        db.query(InterviewSession).filter(
            InterviewSession.id == session_id
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _status(session_id):
    db = SessionLocal()
    try:
        return db.get(InterviewSession, session_id).status
    finally:
        db.close()


def test_starting_a_new_interview_abandons_the_open_one(started_interview):
    assert _status(OPEN_SESSION_ID) == SessionStatus.ABANDONED.value


def test_the_new_interview_itself_stays_in_progress(started_interview):
    _service, result = started_interview

    assert _status(result["session_id"]) == SessionStatus.IN_PROGRESS.value


def test_abandoning_writes_an_audit_event(started_interview):
    db = SessionLocal()
    try:
        event = (
            db.query(InterviewAuditLog)
            .filter(
                InterviewAuditLog.session_id == OPEN_SESSION_ID,
                InterviewAuditLog.event_type == "SESSION_ABANDONED",
            )
            .one()
        )
        assert event.from_status == SessionStatus.IN_PROGRESS.value
        assert event.to_status == SessionStatus.ABANDONED.value
    finally:
        db.close()


def test_completed_interviews_are_left_alone(started_interview):
    assert _status(COMPLETED_SESSION_ID) == SessionStatus.COMPLETED.value


def test_another_candidates_open_interview_is_left_alone():
    db = SessionLocal()
    try:
        db.get(
            InterviewSession, OTHER_USER_SESSION_ID
        ).status = SessionStatus.IN_PROGRESS.value
        db.commit()
    finally:
        db.close()

    service = make_fake_interview_service()
    result = service.start_interview(user_id=USER_ID, role="backend")

    try:
        assert _status(OTHER_USER_SESSION_ID) == SessionStatus.IN_PROGRESS.value
    finally:
        db = SessionLocal()
        try:
            session_id = result["session_id"]
            db.query(InterviewAuditLog).filter(
                InterviewAuditLog.session_id == session_id
            ).delete(synchronize_session=False)
            db.query(InterviewQuestion).filter(
                InterviewQuestion.session_id == session_id
            ).delete(synchronize_session=False)
            db.query(InterviewSession).filter(
                InterviewSession.id == session_id
            ).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()


def test_resume_returns_the_new_interview_not_the_abandoned_one(started_interview):
    service, result = started_interview

    resumed = service.resume_interview(USER_ID)

    assert resumed["active"] is True
    assert resumed["session_id"] == result["session_id"]
    assert resumed["question_id"] == result["question_id"]


def test_an_abandoned_interview_cannot_accept_an_answer(started_interview):
    service, _result = started_interview

    with pytest.raises(AnswerClaimConflict):
        service.claim_answer(
            user_id=USER_ID,
            session_id=OPEN_SESSION_ID,
            question_id=OPEN_QUESTION_ID,
            answer="too late",
        )
