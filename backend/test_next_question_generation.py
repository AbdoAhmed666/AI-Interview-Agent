import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import SessionLocal
from models import InterviewAuditLog, InterviewQuestion, InterviewSession
from repositories.interview_repository import create_question
from schemas import QuestionStatus, SessionStatus
from services.interview_service import (
    GenerationConflict,
    InterviewService,
)
import services.interview_service as interview_service_module

SESSION_ID = 23
USER_ID = 9
EVALUATED_QUESTION_ID = 44


def _service_without_manager():
    return InterviewService.__new__(InterviewService)


def _clear_test_rows(db):
    db.query(InterviewAuditLog).filter(
        InterviewAuditLog.session_id == SESSION_ID,
        InterviewAuditLog.event_type.in_(
            [
                "GENERATION_STARTED",
                "GENERATION_SUCCEEDED",
                "GENERATION_FAILED",
                "INTERVIEW_READY_TO_FINISH",
            ]
        ),
    ).delete(synchronize_session=False)
    db.query(InterviewQuestion).filter(
        InterviewQuestion.session_id == SESSION_ID,
        InterviewQuestion.question_number > 3,
    ).delete(synchronize_session=False)


def _prepare_evaluated_question():
    db = SessionLocal()
    try:
        _clear_test_rows(db)
        question = db.get(InterviewQuestion, EVALUATED_QUESTION_ID)
        question.status = QuestionStatus.EVALUATED.value
        question.answer = "persisted answer"
        question.evaluation = {
            "score": 8,
            "level": "strong",
            "strengths": [],
            "weaknesses": [],
            "feedback": "Good",
            "concept_gaps": [],
            "follow_up_question": "Next",
        }
        question.score = 8
        question.feedback = "Good"
        question.evaluated_at = question.created_at
        question.answer_submitted_at = question.created_at
        session = db.get(InterviewSession, SESSION_ID)
        session.status = SessionStatus.IN_PROGRESS.value
        db.commit()
    finally:
        db.close()


def _restore_session():
    db = SessionLocal()
    try:
        _clear_test_rows(db)
        question = db.get(InterviewQuestion, EVALUATED_QUESTION_ID)
        question.status = QuestionStatus.ACTIVE.value
        question.answer = None
        question.evaluation = None
        question.score = None
        question.feedback = None
        question.answer_submitted_at = None
        question.evaluated_at = None
        session = db.get(InterviewSession, SESSION_ID)
        session.status = SessionStatus.IN_PROGRESS.value
        db.commit()
    finally:
        db.close()


def test_successful_generation_persists_next_question(monkeypatch):
    _prepare_evaluated_question()
    observed = {}

    def generate(user_id, role, difficulty):
        db = SessionLocal()
        try:
            observed["session_status_during_llm"] = db.get(
                InterviewSession, SESSION_ID
            ).status
        finally:
            db.close()
        assert difficulty == 4
        return "What trade-off would you revisit?"

    service = _service_without_manager()
    monkeypatch.setattr(service, "_generate_question_text", generate)
    try:
        result = service.generate_next_question(USER_ID, SESSION_ID, EVALUATED_QUESTION_ID)
        db = SessionLocal()
        try:
            question = db.query(InterviewQuestion).filter_by(
                session_id=SESSION_ID, question_number=4
            ).one()
            events = db.query(InterviewAuditLog).filter(
                InterviewAuditLog.session_id == SESSION_ID,
                InterviewAuditLog.question_id.in_([EVALUATED_QUESTION_ID, question.id]),
                InterviewAuditLog.event_type.in_(["GENERATION_STARTED", "GENERATION_SUCCEEDED"]),
            ).all()
            assert observed["session_status_during_llm"] == SessionStatus.GENERATING.value
            assert result["question_id"] == question.id
            assert question.status == QuestionStatus.ACTIVE.value
            assert question.answer is None
            assert question.evaluation is None
            assert question.score is None
            assert question.feedback is None
            assert len([event for event in events if event.event_type == "GENERATION_STARTED"]) == 1
            assert len([event for event in events if event.event_type == "GENERATION_SUCCEEDED"]) == 1
            assert db.get(InterviewSession, SESSION_ID).status == SessionStatus.IN_PROGRESS.value
        finally:
            db.close()
    finally:
        _restore_session()


def test_generation_failure_preserves_evaluation_and_marks_session(monkeypatch):
    _prepare_evaluated_question()
    service = _service_without_manager()
    monkeypatch.setattr(
        service,
        "_generate_question_text",
        lambda **kwargs: (_ for _ in ()).throw(TimeoutError("provider timeout")),
    )
    try:
        with pytest.raises(TimeoutError):
            service.generate_next_question(USER_ID, SESSION_ID, EVALUATED_QUESTION_ID)
        db = SessionLocal()
        try:
            session = db.get(InterviewSession, SESSION_ID)
            question = db.get(InterviewQuestion, EVALUATED_QUESTION_ID)
            event = db.query(InterviewAuditLog).filter_by(
                session_id=SESSION_ID,
                event_type="GENERATION_FAILED",
            ).one()
            assert session.status == SessionStatus.GENERATION_FAILED.value
            assert question.status == QuestionStatus.EVALUATED.value
            assert question.evaluation is not None
            assert event.details["error_type"] == "TimeoutError"
            assert db.query(InterviewQuestion).filter_by(
                session_id=SESSION_ID, question_number=4
            ).count() == 0
        finally:
            db.close()
    finally:
        _restore_session()


def test_five_evaluated_questions_become_ready_without_llm(monkeypatch):
    _prepare_evaluated_question()
    db = SessionLocal()
    try:
        for number in (4, 5):
            create_question(
                db,
                session_id=SESSION_ID,
                question=f"Historical test question {number}",
                difficulty=3,
                question_number=number,
                status=QuestionStatus.EVALUATED,
            )
            row = db.query(InterviewQuestion).filter_by(
                session_id=SESSION_ID, question_number=number
            ).one()
            row.answer = "answer"
            row.evaluation = {
                "score": 7,
                "level": "medium",
                "strengths": [],
                "weaknesses": [],
                "feedback": "Good",
                "concept_gaps": [],
                "follow_up_question": "Next",
            }
            row.score = 7
            row.feedback = "Good"
        db.commit()
    finally:
        db.close()

    service = _service_without_manager()
    monkeypatch.setattr(
        service,
        "_generate_question_text",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("LLM must not run")),
    )
    try:
        result = service.generate_next_question(USER_ID, SESSION_ID, EVALUATED_QUESTION_ID)
        db = SessionLocal()
        try:
            assert result["status"] == SessionStatus.READY_TO_FINISH.value
            assert db.get(InterviewSession, SESSION_ID).status == SessionStatus.READY_TO_FINISH.value
            assert db.query(InterviewQuestion).filter_by(
                session_id=SESSION_ID, question_number=6
            ).count() == 0
        finally:
            db.close()
    finally:
        _restore_session()


def test_completed_session_rejects_generation():
    with pytest.raises(GenerationConflict):
        _service_without_manager().generate_next_question(USER_ID, 15, 29)


def test_generation_persistence_failure_leaves_generation_state_recoverable(monkeypatch):
    _prepare_evaluated_question()
    service = _service_without_manager()
    monkeypatch.setattr(service, "_generate_question_text", lambda **kwargs: "Generated question")
    monkeypatch.setattr(
        interview_service_module,
        "create_question",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("insert failure")),
    )
    try:
        with pytest.raises(RuntimeError, match="insert failure"):
            service.generate_next_question(USER_ID, SESSION_ID, EVALUATED_QUESTION_ID)
        db = SessionLocal()
        try:
            assert db.get(InterviewSession, SESSION_ID).status == SessionStatus.GENERATING.value
            assert db.query(InterviewQuestion).filter_by(
                session_id=SESSION_ID, question_number=4
            ).count() == 0
        finally:
            db.close()
    finally:
        _restore_session()


def test_generation_retry_succeeds_from_failed_state(monkeypatch):
    _prepare_evaluated_question()
    db = SessionLocal()
    try:
        db.get(InterviewSession, SESSION_ID).status = SessionStatus.GENERATION_FAILED.value
        db.commit()
    finally:
        db.close()
    service = _service_without_manager()
    monkeypatch.setattr(service, "_generate_question_text", lambda **kwargs: "Retry question")
    try:
        result = service.generate_next_question(USER_ID, SESSION_ID, EVALUATED_QUESTION_ID)
        assert result["question_number"] == 4
        db = SessionLocal()
        try:
            assert db.get(InterviewSession, SESSION_ID).status == SessionStatus.IN_PROGRESS.value
            assert db.query(InterviewAuditLog).filter_by(
                session_id=SESSION_ID, event_type="GENERATION_RETRY_STARTED"
            ).count() == 1
            assert db.query(InterviewAuditLog).filter_by(
                session_id=SESSION_ID, event_type="GENERATION_RETRY_SUCCEEDED"
            ).count() == 1
        finally:
            db.close()
    finally:
        _restore_session()


def test_generation_retry_failure_remains_failed(monkeypatch):
    _prepare_evaluated_question()
    db = SessionLocal()
    try:
        db.get(InterviewSession, SESSION_ID).status = SessionStatus.GENERATION_FAILED.value
        db.commit()
    finally:
        db.close()
    service = _service_without_manager()
    monkeypatch.setattr(
        service,
        "_generate_question_text",
        lambda **kwargs: (_ for _ in ()).throw(TimeoutError("retry timeout")),
    )
    try:
        with pytest.raises(TimeoutError):
            service.generate_next_question(USER_ID, SESSION_ID, EVALUATED_QUESTION_ID)
        db = SessionLocal()
        try:
            assert db.get(InterviewSession, SESSION_ID).status == SessionStatus.GENERATION_FAILED.value
            assert db.query(InterviewAuditLog).filter_by(
                session_id=SESSION_ID, event_type="GENERATION_RETRY_FAILED"
            ).count() == 1
        finally:
            db.close()
    finally:
        _restore_session()


def test_stale_generating_state_can_be_recovered(monkeypatch):
    _prepare_evaluated_question()
    db = SessionLocal()
    try:
        session = db.get(InterviewSession, SESSION_ID)
        session.status = SessionStatus.GENERATING.value
        session.updated_at = session.updated_at.replace(year=2020)
        db.commit()
    finally:
        db.close()
    service = _service_without_manager()
    monkeypatch.setattr(service, "_generate_question_text", lambda **kwargs: "Stale recovery question")
    try:
        assert service.generate_next_question(USER_ID, SESSION_ID, EVALUATED_QUESTION_ID)["question_number"] == 4
    finally:
        _restore_session()
