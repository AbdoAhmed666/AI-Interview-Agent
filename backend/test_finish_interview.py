"""Durable finish-interview tests against PostgreSQL.

These tests prove that ``/finish-interview`` is PostgreSQL-authoritative: the
final score/recommendation are derived from persisted evaluations, the
InterviewManager in-memory state is never consulted, and the
READY_TO_FINISH -> COMPLETED transition is atomic.
"""
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import SessionLocal
from models import InterviewAuditLog, InterviewQuestion, InterviewSession
from schemas import QuestionStatus, SessionStatus
import services.interview_service as interview_service_module
from services.interview_service import (
    FinishConflict,
    FinishForbidden,
    FinishNotFoundError,
    InterviewService,
)

USER_ID = 9
SCORES = [8, 8, 8, 8, 8]
EXPECTED_SCORE = 8.0
EXPECTED_REC = "Hire"


def _service():
    """A service with an empty (manager-memory-loss) manager -> DB-only proof."""
    service = InterviewService.__new__(InterviewService)
    service.manager = SimpleNamespace(_sessions={}, _question_to_session={})
    return service


@contextmanager
def _db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _make_question(session_id, number, score):
    return InterviewQuestion(
        session_id=session_id,
        question=f"Question {number}?",
        difficulty=3,
        question_number=number,
        status=QuestionStatus.EVALUATED.value,
        score=float(score),
        answer=f"answer {number}",
        feedback="ok",
        evaluation={"score": score, "level": "medium", "feedback": "ok"},
        evaluated_at=datetime.utcnow(),
        answer_submitted_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )


def _create_evaluated_session(
    user_id=USER_ID, scores=SCORES, status=SessionStatus.READY_TO_FINISH,
    extra_questions=None,
):
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        session = InterviewSession(
            user_id=user_id, role="backend", status=status.value,
            started_at=now, updated_at=now,
        )
        db.add(session)
        db.flush()
        for i, sc in enumerate(scores, start=1):
            db.add(_make_question(session.id, i, sc))
        if extra_questions:
            for eq in extra_questions:
                db.add(InterviewQuestion(session_id=session.id, **eq))
        db.commit()
        return session.id
    finally:
        db.close()


def _delete_session_tree(session_id):
    db = SessionLocal()
    try:
        with db.begin():
            db.query(InterviewAuditLog).filter(
                InterviewAuditLog.session_id == session_id
            ).delete(synchronize_session=False)
            db.query(InterviewQuestion).filter(
                InterviewQuestion.session_id == session_id
            ).delete(synchronize_session=False)
            db.query(InterviewSession).filter(
                InterviewSession.id == session_id
            ).delete(synchronize_session=False)
    finally:
        db.close()


@contextmanager
def _persisted_ready_session(**kwargs):
    session_id = _create_evaluated_session(**kwargs)
    try:
        yield session_id
    finally:
        _delete_session_tree(session_id)


def test_finish_from_persisted_state():
    with _persisted_ready_session() as session_id:
        result = _service().finish_interview(user_id=USER_ID, session_id=session_id)
        assert result["status"] == SessionStatus.COMPLETED.value
        assert result["overall_score"] == EXPECTED_SCORE
        assert result["recommendation"] == EXPECTED_REC
        assert result["finished_at"] is not None
        assert result["questions_evaluated"] == 5

        with _db() as db:
            session = db.get(InterviewSession, session_id)
            assert session.status == SessionStatus.COMPLETED.value
            assert session.overall_score == EXPECTED_SCORE
            assert session.recommendation == EXPECTED_REC
            assert session.finished_at is not None
            assert session.updated_at is not None
            audit = db.query(InterviewAuditLog).filter(
                InterviewAuditLog.session_id == session_id,
                InterviewAuditLog.event_type == "INTERVIEW_COMPLETED",
            ).one()
            assert audit.from_status == SessionStatus.READY_TO_FINISH.value
            assert audit.to_status == SessionStatus.COMPLETED.value
            details = audit.details or {}
            assert details.get("question_count") == 5
            assert "question" not in details
            assert "answer" not in details


def test_finish_survives_manager_memory_loss():
    with _persisted_ready_session() as session_id:
        # The manager has no knowledge of this session; finish must still
        # succeed using PostgreSQL only.
        result = _service().finish_interview(user_id=USER_ID, session_id=session_id)
        assert result["status"] == SessionStatus.COMPLETED.value
        assert result["overall_score"] == EXPECTED_SCORE
        assert result["recommendation"] == EXPECTED_REC


def test_finish_rejects_incomplete_session():
    with _persisted_ready_session(scores=[8, 8, 8]) as session_id:
        service = _service()
        with pytest.raises(FinishConflict):
            service.finish_interview(user_id=USER_ID, session_id=session_id)
        with _db() as db:
            session = db.get(InterviewSession, session_id)
            assert session.status == SessionStatus.READY_TO_FINISH.value
            assert session.overall_score is None
            assert session.recommendation is None
            assert db.query(InterviewAuditLog).filter(
                InterviewAuditLog.session_id == session_id,
                InterviewAuditLog.event_type == "INTERVIEW_COMPLETED",
            ).count() == 0


def test_finish_rejects_non_ready_status():
    with _persisted_ready_session(status=SessionStatus.IN_PROGRESS) as session_id:
        service = _service()
        with pytest.raises(FinishConflict):
            service.finish_interview(user_id=USER_ID, session_id=session_id)
        with _db() as db:
            assert (
                db.get(InterviewSession, session_id).status
                == SessionStatus.IN_PROGRESS.value
            )
# __FINISH_TESTS_MARKER__
