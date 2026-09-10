"""Durable start-interview tests against PostgreSQL."""
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import SessionLocal
from models import InterviewAuditLog, InterviewQuestion, InterviewSession
from repositories.interview_repository import get_question, get_session
from schemas import QuestionStatus, SessionStatus
import services.interview_service as interview_service_module
from services.interview_service import InterviewService

QUESTION_TEXT = "Why is CI/CD important for backend engineers?"


def _fake_manager(first_question=QUESTION_TEXT, eligible=True):
    """A manager exposing only the stateless AI/domain helpers the service uses.

    PostgreSQL is the workflow authority, so the manager has no session state.
    ``start_interview`` now drives eligibility + first-question generation
    directly through these helper components (and ``_generate_question_text``).
    """
    chunks = [
        SimpleNamespace(chunk=SimpleNamespace(role="user", content="cv context")),
        SimpleNamespace(
            chunk=SimpleNamespace(role="knowledge", content="knowledge context")
        ),
    ]
    return SimpleNamespace(
        storage=SimpleNamespace(
            has_cv=lambda user_id: True,
            get_active_cv=lambda user_id: Path("dummy.pdf"),
        ),
        parser=SimpleNamespace(
            parse=lambda file_path, role, document_type: SimpleNamespace(
                content="backend experience"
            )
        ),
        analyzer=SimpleNamespace(
            analyze=lambda content: SimpleNamespace(skills=["python"])
        ),
        eligibility=SimpleNamespace(
            evaluate=lambda analysis, role: SimpleNamespace(
                eligible=eligible,
                message="eligible" if eligible else "not eligible",
                score=100.0,
                recommended_roles=[],
            )
        ),
        query_builder=SimpleNamespace(build=lambda analysis, role, difficulty: "query"),
        rag=SimpleNamespace(
            ensure_cv_index=lambda user_id, cv_path: None,
            ensure_knowledge_index=lambda role: None,
            retrieve_hybrid=lambda query: chunks,
        ),
        prompt_builder=SimpleNamespace(
            build_question_prompt=lambda role, difficulty, cv_chunks, knowledge_chunks: "prompt"
        ),
        provider=SimpleNamespace(generate_question=lambda prompt: first_question),
    )


def _service_with_fake_manager(first_question=QUESTION_TEXT):
    """InterviewService without the heavy __init__, wired to a stateless manager."""
    service = InterviewService.__new__(InterviewService)
    service.manager = _fake_manager(first_question=first_question)
    return service


def _delete_session_tree(db, session_id):
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


@contextmanager
def _fresh_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def _started_session():
    service = _service_with_fake_manager()
    result = service.start_interview(user_id=9, role="backend")
    try:
        yield service, result
    finally:
        cleanup_db = SessionLocal()
        try:
            _delete_session_tree(cleanup_db, result["session_id"])
        finally:
            cleanup_db.close()


def test_start_creates_session_and_first_question():
    with _started_session() as (service, result):
        session_id = result["session_id"]
        question_id = result["question_id"]
        with _fresh_db() as db:
            session = get_session(db, session_id)
            assert session is not None
            assert session.user_id == 9
            assert session.role == "backend"
            assert session.status == SessionStatus.IN_PROGRESS.value
            assert session.started_at is not None
            assert session.updated_at is not None
            question = get_question(db, question_id)
            assert question is not None
            assert question.session_id == session_id
            assert question.question_number == 1
            assert question.status == QuestionStatus.ACTIVE.value
            assert question.question == QUESTION_TEXT
            assert question.created_at is not None
            assert question.difficulty == 3
            assert question.answer is None
            assert question.evaluation is None


def test_first_question_is_durable_after_service_return():
    with _started_session() as (service, result):
        with _fresh_db() as db:
            assert get_question(db, result["question_id"]) is not None
            assert get_session(db, result["session_id"]) is not None


def test_returned_question_id_exists_in_postgresql():
    with _started_session() as (service, result):
        with _fresh_db() as db:
            question = get_question(db, result["question_id"])
            assert question is not None
            assert question.id == result["question_id"]
            assert question.status == QuestionStatus.ACTIVE.value
            assert question.question_number == 1


def test_start_writes_durable_session_started_audit():
    with _started_session() as (service, result):
        with _fresh_db() as db:
            audit = (
                db.query(InterviewAuditLog)
                .filter(
                    InterviewAuditLog.session_id == result["session_id"],
                    InterviewAuditLog.event_type == "SESSION_STARTED",
                )
                .one()
            )
            assert audit.question_id == result["question_id"]
            details = audit.details or {}
            assert details.get("question_number") == 1
            assert "question" not in details
            assert "answer" not in details
            assert audit.from_status is None
            assert audit.to_status == SessionStatus.IN_PROGRESS.value


def test_start_rolls_back_session_when_question_creation_fails(monkeypatch):
    service = _service_with_fake_manager()
    captured = {}

    def _boom(db, session_id, question, difficulty, **kwargs):
        captured["session_id"] = session_id
        raise RuntimeError("simulated question insert failure")

    monkeypatch.setattr(interview_service_module, "create_question", _boom)
    with pytest.raises(RuntimeError, match="simulated question insert failure"):
        service.start_interview(user_id=9, role="backend")
    with _fresh_db() as db:
        assert captured["session_id"] is not None
        assert get_session(db, captured["session_id"]) is None
        assert db.query(InterviewAuditLog).filter(
            InterviewAuditLog.session_id == captured["session_id"]
        ).count() == 0


def test_created_first_question_is_immediately_claimable():
    with _started_session() as (service, result):
        claim = service.claim_answer(
            user_id=9,
            session_id=result["session_id"],
            question_id=result["question_id"],
            answer="Automated pipelines that build, test and deploy on every push.",
        )
        assert claim["status"] == QuestionStatus.EVALUATING.value
        assert claim["question_number"] == 1
        with _fresh_db() as db:
            question = get_question(db, result["question_id"])
            assert question is not None
            assert question.status == QuestionStatus.EVALUATING.value
            assert (
                question.answer
                == "Automated pipelines that build, test and deploy on every push."
            )
            assert question.answer_submitted_at is not None
