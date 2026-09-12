import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import SessionLocal
from models import InterviewAuditLog, InterviewQuestion
from schemas import EvaluationLevel, EvaluationResponse, QuestionStatus
from services.interview_service import (
    AnswerClaimConflict,
    InterviewService,
)
import services.interview_service as interview_service_module

pytestmark = pytest.mark.usefixtures("seeded_workflow")


QUESTION_ID = 44
SESSION_ID = 23
USER_ID = 9


def _service_without_manager():
    return InterviewService.__new__(InterviewService)


def _prepare_question(status, answer="persisted answer", evaluation=None):
    db = SessionLocal()
    try:
        question = db.get(InterviewQuestion, QUESTION_ID)
        question.status = status
        question.answer = answer
        question.evaluation = evaluation
        question.score = evaluation.get("score") if evaluation else None
        question.feedback = evaluation.get("feedback") if evaluation else None
        question.evaluated_at = None
        question.answer_submitted_at = datetime.utcnow() - timedelta(minutes=10)
        db.query(InterviewAuditLog).filter(
            InterviewAuditLog.session_id == SESSION_ID,
            InterviewAuditLog.question_id == QUESTION_ID,
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _restore_question():
    db = SessionLocal()
    try:
        question = db.get(InterviewQuestion, QUESTION_ID)
        question.status = QuestionStatus.ACTIVE.value
        question.answer = None
        question.evaluation = None
        question.score = None
        question.feedback = None
        question.answer_submitted_at = None
        question.evaluated_at = None
        db.query(InterviewAuditLog).filter(
            InterviewAuditLog.session_id == SESSION_ID,
            InterviewAuditLog.question_id == QUESTION_ID,
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


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


def test_successful_evaluation_persists_canonical_json_and_projections(monkeypatch):
    _prepare_question(QuestionStatus.EVALUATING.value)
    monkeypatch.setattr(interview_service_module, "evaluate_answer_with_llm", lambda **kwargs: _evaluation())
    try:
        result = _service_without_manager().evaluate_claimed_answer(
            USER_ID, SESSION_ID, QUESTION_ID
        )

        db = SessionLocal()
        try:
            question = db.get(InterviewQuestion, QUESTION_ID)
            events = db.query(InterviewAuditLog).filter_by(
                session_id=SESSION_ID,
                question_id=QUESTION_ID,
                event_type="EVALUATION_SUCCEEDED",
            ).all()
            assert result["status"] == QuestionStatus.EVALUATED.value
            assert question.status == QuestionStatus.EVALUATED.value
            assert question.evaluation == _evaluation().model_dump(mode="json")
            assert question.score == 8
            assert question.feedback == "Good answer."
            assert question.evaluated_at is not None
            assert len(events) == 1
        finally:
            db.close()
    finally:
        _restore_question()


def test_invalid_llm_output_marks_evaluation_failed_without_losing_answer(monkeypatch):
    _prepare_question(QuestionStatus.EVALUATING.value, answer="keep this answer")
    monkeypatch.setattr(
        interview_service_module,
        "evaluate_answer_with_llm",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("invalid output")),
    )
    try:
        with pytest.raises(ValueError, match="invalid output"):
            _service_without_manager().evaluate_claimed_answer(
                USER_ID, SESSION_ID, QUESTION_ID
            )
        db = SessionLocal()
        try:
            question = db.get(InterviewQuestion, QUESTION_ID)
            event = db.query(InterviewAuditLog).filter_by(
                session_id=SESSION_ID,
                question_id=QUESTION_ID,
                event_type="EVALUATION_FAILED",
            ).one()
            assert question.answer == "keep this answer"
            assert question.status == QuestionStatus.EVALUATION_FAILED.value
            assert question.evaluation is None
            assert question.score is None
            assert question.feedback is None
            assert event.details == {"error_type": "ValueError", "question_number": 3}
        finally:
            db.close()
    finally:
        _restore_question()


def test_provider_exception_has_same_failure_contract(monkeypatch):
    _prepare_question(QuestionStatus.EVALUATING.value)
    monkeypatch.setattr(
        interview_service_module,
        "evaluate_answer_with_llm",
        lambda **kwargs: (_ for _ in ()).throw(TimeoutError("provider timeout")),
    )
    try:
        with pytest.raises(TimeoutError):
            _service_without_manager().evaluate_claimed_answer(
                USER_ID, SESSION_ID, QUESTION_ID
            )
        db = SessionLocal()
        try:
            question = db.get(InterviewQuestion, QUESTION_ID)
            assert question.status == QuestionStatus.EVALUATION_FAILED.value
            assert question.answer == "persisted answer"
            assert question.evaluation is None
        finally:
            db.close()
    finally:
        _restore_question()


def test_already_evaluated_question_is_not_overwritten(monkeypatch):
    existing = _evaluation().model_dump(mode="json")
    _prepare_question(QuestionStatus.EVALUATED.value, evaluation=existing)
    monkeypatch.setattr(
        interview_service_module,
        "evaluate_answer_with_llm",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("LLM must not be called")),
    )
    try:
        result = _service_without_manager().evaluate_claimed_answer(
            USER_ID, SESSION_ID, QUESTION_ID
        )
        assert result["evaluation"] == existing
    finally:
        _restore_question()


def test_evaluation_persistence_failure_rolls_back_evaluation_and_audit(monkeypatch):
    _prepare_question(QuestionStatus.EVALUATING.value, answer="keep on rollback")
    monkeypatch.setattr(interview_service_module, "evaluate_answer_with_llm", lambda **kwargs: _evaluation())
    monkeypatch.setattr(
        interview_service_module,
        "create_audit_event",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("audit failure")),
    )
    try:
        with pytest.raises(RuntimeError, match="audit failure"):
            _service_without_manager().evaluate_claimed_answer(
                USER_ID, SESSION_ID, QUESTION_ID
            )
        db = SessionLocal()
        try:
            question = db.get(InterviewQuestion, QUESTION_ID)
            assert question.answer == "keep on rollback"
            assert question.status == QuestionStatus.EVALUATING.value
            assert question.evaluation is None
            assert question.score is None
            assert question.feedback is None
        finally:
            db.close()
    finally:
        _restore_question()


def test_ownership_rejection_does_not_call_llm(monkeypatch):
    monkeypatch.setattr(
        interview_service_module,
        "evaluate_answer_with_llm",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("LLM must not be called")),
    )
    with pytest.raises(Exception):
        _service_without_manager().evaluate_claimed_answer(
            10, SESSION_ID, QUESTION_ID
        )


def test_evaluation_schema_rejects_invalid_payloads():
    with pytest.raises(ValueError):
        EvaluationResponse.model_validate({
            "score": 11,
            "level": "strong",
            "strengths": [],
            "weaknesses": [],
            "feedback": "ok",
            "concept_gaps": [],
            "follow_up_question": "next",
        })
    with pytest.raises(ValueError):
        EvaluationResponse.model_validate({
            "score": 8,
            "level": "unknown",
            "strengths": [],
            "weaknesses": [],
            "feedback": "ok",
            "concept_gaps": [],
            "follow_up_question": "next",
        })
    with pytest.raises(ValueError):
        EvaluationResponse.model_validate({"score": 8})
    with pytest.raises(ValueError):
        EvaluationResponse.model_validate({
            "score": 8,
            "level": "strong",
            "strengths": [],
            "weaknesses": [],
            "feedback": "ok",
            "concept_gaps": [],
            "follow_up_question": "next",
            "extra": True,
        })


def test_evaluation_retry_succeeds_from_failed_state(monkeypatch):
    _prepare_question(QuestionStatus.EVALUATION_FAILED.value, answer="retry answer")
    monkeypatch.setattr(interview_service_module, "evaluate_answer_with_llm", lambda **kwargs: _evaluation())
    try:
        result = _service_without_manager().evaluate_claimed_answer(
            USER_ID, SESSION_ID, QUESTION_ID
        )
        assert result["status"] == QuestionStatus.EVALUATED.value
        db = SessionLocal()
        try:
            assert db.get(InterviewQuestion, QUESTION_ID).status == QuestionStatus.EVALUATED.value
            assert db.query(InterviewAuditLog).filter_by(
                session_id=SESSION_ID, event_type="EVALUATION_RETRY_STARTED"
            ).count() == 1
            assert db.query(InterviewAuditLog).filter_by(
                session_id=SESSION_ID, event_type="EVALUATION_RETRY_SUCCEEDED"
            ).count() == 1
        finally:
            db.close()
    finally:
        _restore_question()


def test_evaluation_retry_failure_remains_retryable(monkeypatch):
    _prepare_question(QuestionStatus.EVALUATION_FAILED.value, answer="retry answer")
    monkeypatch.setattr(
        interview_service_module,
        "evaluate_answer_with_llm",
        lambda **kwargs: (_ for _ in ()).throw(TimeoutError("retry timeout")),
    )
    try:
        with pytest.raises(TimeoutError):
            _service_without_manager().evaluate_claimed_answer(
                USER_ID, SESSION_ID, QUESTION_ID
            )
        db = SessionLocal()
        try:
            assert db.get(InterviewQuestion, QUESTION_ID).status == QuestionStatus.EVALUATION_FAILED.value
            assert db.query(InterviewAuditLog).filter_by(
                session_id=SESSION_ID, event_type="EVALUATION_RETRY_FAILED"
            ).count() == 1
        finally:
            db.close()
    finally:
        _restore_question()
