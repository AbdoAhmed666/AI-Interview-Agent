import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import SessionLocal
from models import InterviewAuditLog, InterviewQuestion
from repositories.interview_repository import get_current_question
from schemas import QuestionStatus
from services.interview_service import (
    AnswerClaimConflict,
    AnswerClaimNotFound,
    InterviewService,
)
import services.interview_service as interview_service_module


def _service_without_manager():
    return InterviewService.__new__(InterviewService)


def test_active_question_claim_is_durable_with_atomic_audit_then_rolls_back_test_data():
    db = SessionLocal()
    try:
        result = _service_without_manager()._claim_answer_in_transaction(
            db=db,
            user_id=9,
            session_id=23,
            question_id=44,
            answer="authoritative answer",
        )

        question = db.get(InterviewQuestion, 44)
        audit_rows = (
            db.query(InterviewAuditLog)
            .filter(
                InterviewAuditLog.session_id == 23,
                InterviewAuditLog.event_type == "ANSWER_SUBMITTED",
            )
            .all()
        )

        assert result["status"] == QuestionStatus.EVALUATING.value
        assert question.answer == "authoritative answer"
        assert question.status == QuestionStatus.EVALUATING.value
        assert question.answer_submitted_at is not None
        assert question.evaluation is None
        assert question.evaluated_at is None
        assert question.score is None
        assert question.feedback is None
        assert len(audit_rows) == 1
        assert audit_rows[0].question_id == 44
    finally:
        db.rollback()
        db.close()

    verification_db = SessionLocal()
    try:
        question = verification_db.get(InterviewQuestion, 44)
        assert question.status == QuestionStatus.ACTIVE.value
        assert question.answer is None
        assert verification_db.query(InterviewAuditLog).filter_by(
            session_id=23, event_type="ANSWER_SUBMITTED"
        ).count() == 0
    finally:
        verification_db.close()


def test_claim_rejects_already_submitted_question_without_overwrite():
    db = SessionLocal()
    try:
        question = db.get(InterviewQuestion, 44)
        question.status = QuestionStatus.EVALUATING.value
        question.answer = "original answer"
        db.flush()

        with pytest.raises(AnswerClaimConflict):
            _service_without_manager()._claim_answer_in_transaction(
                db=db,
                user_id=9,
                session_id=23,
                question_id=44,
                answer="replacement answer",
            )
        assert question.answer == "original answer"
    finally:
        db.rollback()
        db.close()


def test_claim_rejects_unauthorized_session_without_mutation():
    service = _service_without_manager()
    with pytest.raises(AnswerClaimNotFound):
        service.claim_answer(
            user_id=10,
            session_id=23,
            question_id=44,
            answer="unauthorized answer",
        )

    db = SessionLocal()
    try:
        question = db.get(InterviewQuestion, 44)
        assert question.status == QuestionStatus.ACTIVE.value
        assert question.answer is None
    finally:
        db.close()


def test_claim_rolls_back_answer_and_audit_when_audit_insert_fails(monkeypatch):
    def fail_audit(*args, **kwargs):
        raise RuntimeError("audit failure")

    monkeypatch.setattr(interview_service_module, "create_audit_event", fail_audit)

    with pytest.raises(RuntimeError, match="audit failure"):
        _service_without_manager().claim_answer(
            user_id=9,
            session_id=23,
            question_id=44,
            answer="rolled back answer",
        )

    db = SessionLocal()
    try:
        question = db.get(InterviewQuestion, 44)
        assert question.status == QuestionStatus.ACTIVE.value
        assert question.answer is None
        assert db.query(InterviewAuditLog).filter_by(
            session_id=23, event_type="ANSWER_SUBMITTED"
        ).count() == 0
    finally:
        db.close()


def test_claim_rejects_archived_question_outside_active_progression():
    db = SessionLocal()
    try:
        assert get_current_question(db, 24) is None
    finally:
        db.close()

    with pytest.raises(AnswerClaimConflict):
        _service_without_manager().claim_answer(
            user_id=10,
            session_id=24,
            question_id=50,
            answer="archived answer",
        )


def test_claim_rejects_completed_session():
    with pytest.raises(AnswerClaimConflict):
        _service_without_manager().claim_answer(
            user_id=9,
            session_id=15,
            question_id=29,
            answer="completed answer",
        )


def test_claim_rejects_question_number_outside_domain(monkeypatch):
    monkeypatch.setattr(
        interview_service_module,
        "get_session_for_update",
        lambda db, session_id, user_id: SimpleNamespace(
            id=session_id,
            user_id=user_id,
            status="IN_PROGRESS",
        ),
    )
    monkeypatch.setattr(
        interview_service_module,
        "get_current_question",
        lambda db, session_id, for_update: SimpleNamespace(
            id=44,
            question_number=6,
            status=QuestionStatus.ACTIVE.value,
        ),
    )

    with pytest.raises(AnswerClaimConflict, match="outside the interview range"):
        _service_without_manager()._claim_answer_in_transaction(
            db=object(),
            user_id=9,
            session_id=23,
            question_id=44,
            answer="invalid number answer",
        )


def test_same_answer_duplicate_returns_persisted_state():
    db = SessionLocal()
    try:
        question = db.get(InterviewQuestion, 44)
        question.status = QuestionStatus.EVALUATING.value
        question.answer = "same answer"
        question.answer_submitted_at = question.created_at
        db.flush()
        result = _service_without_manager()._claim_answer_in_transaction(
            db, 9, 23, 44, " same answer "
        )
        assert result["already_submitted"] is True
        assert question.answer == "same answer"
    finally:
        db.rollback()
        db.close()


def test_conflicting_duplicate_is_rejected():
    db = SessionLocal()
    try:
        question = db.get(InterviewQuestion, 44)
        question.status = QuestionStatus.EVALUATING.value
        question.answer = "original"
        question.answer_submitted_at = question.created_at
        db.flush()
        with pytest.raises(AnswerClaimConflict):
            _service_without_manager()._claim_answer_in_transaction(
                db, 9, 23, 44, "different"
            )
        assert question.answer == "original"
    finally:
        db.rollback()
        db.close()
