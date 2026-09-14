"""Shared pytest fixtures that make the durable-workflow tests hermetic.

The interview state-machine tests were originally written against a
developer's local database and referenced fixed row IDs (users 9/10,
sessions 15/23/24, question 44). On a clean database those rows do not
exist, so the tests failed at import/lookup time.

``seeded_workflow`` recreates exactly that canonical state deterministically
before each test that opts in, and tears it down afterwards, so the suite
runs green on any fresh database (local or CI).

A test module opts in with a single line::

    pytestmark = pytest.mark.usefixtures("seeded_workflow")

Database imports are deferred into the fixtures so that DB-free tests
(``test_rag_isolation``, ``test_role_coverage``) never import the database
layer and keep running without a configured ``DATABASE_URL``.
"""
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Canonical fixed identifiers the durable-workflow tests reference directly.
SEED_USER_ID = 9
OTHER_USER_ID = 10
COMPLETED_SESSION_ID = 15
IN_PROGRESS_SESSION_ID = 23
HISTORICAL_SESSION_ID = 24
CURRENT_QUESTION_ID = 44
_SEED_SESSION_IDS = (
    COMPLETED_SESSION_ID,
    IN_PROGRESS_SESSION_ID,
    HISTORICAL_SESSION_ID,
)
# Auto-increment floor so DB-generated ids never collide with the fixed seed.
_ID_FLOOR = 100_000

_STRONG_EVAL = {
    "score": 8,
    "level": "strong",
    "strengths": [],
    "weaknesses": [],
    "feedback": "Seed",
    "concept_gaps": [],
    "follow_up_question": "Next",
}


def _delete_session_tree(db, session_id):
    from models import InterviewAuditLog, InterviewQuestion, InterviewSession

    db.query(InterviewAuditLog).filter(
        InterviewAuditLog.session_id == session_id
    ).delete(synchronize_session=False)
    db.query(InterviewQuestion).filter(
        InterviewQuestion.session_id == session_id
    ).delete(synchronize_session=False)
    db.query(InterviewSession).filter(
        InterviewSession.id == session_id
    ).delete(synchronize_session=False)


def _ensure_users(db):
    from models import User

    for uid, name, email in (
        (SEED_USER_ID, "Seed User 9", "seed9@example.com"),
        (OTHER_USER_ID, "Seed User 10", "seed10@example.com"),
    ):
        if db.get(User, uid) is None:
            now = datetime.utcnow()
            db.add(
                User(
                    id=uid,
                    name=name,
                    email=email,
                    hashed_password="not-a-real-hash",
                    is_active=True,
                    is_superuser=False,
                    created_at=now,
                    updated_at=now,
                )
            )


def _evaluated_question(**overrides):
    from models import InterviewQuestion
    from schemas import QuestionStatus

    now = datetime.utcnow()
    fields = dict(
        difficulty=3,
        status=QuestionStatus.EVALUATED.value,
        answer="seed answer",
        evaluation=dict(_STRONG_EVAL),
        score=8,
        feedback="Seed",
        evaluated_at=now,
        answer_submitted_at=now,
        created_at=now,
    )
    fields.update(overrides)
    return InterviewQuestion(**fields)


def _reset_sequences(db):
    from sqlalchemy import text

    for table in (
        "users",
        "interview_sessions",
        "interview_questions",
        "interview_audit_log",
    ):
        db.execute(
            text(
                "SELECT setval(pg_get_serial_sequence(:t, 'id'), :floor, true)"
            ),
            {"t": table, "floor": _ID_FLOOR},
        )


def _seed(db):
    from models import InterviewQuestion, InterviewSession
    from schemas import QuestionStatus, SessionStatus

    now = datetime.utcnow()
    for session_id in _SEED_SESSION_IDS:
        _delete_session_tree(db, session_id)
    _ensure_users(db)

    # Session 15 — completed, owned by user 9. No questions required: the
    # workflow rejects it on the status check before any question lookup.
    db.add(
        InterviewSession(
            id=COMPLETED_SESSION_ID,
            user_id=SEED_USER_ID,
            role="backend",
            status=SessionStatus.COMPLETED.value,
            started_at=now,
            updated_at=now,
            finished_at=now,
            overall_score=8.0,
            recommendation="Hire",
        )
    )

    # Session 23 — in progress, owned by user 9. Questions 1 and 2 evaluated,
    # question 3 (id 44) is the single ACTIVE (current) question.
    db.add(
        InterviewSession(
            id=IN_PROGRESS_SESSION_ID,
            user_id=SEED_USER_ID,
            role="backend",
            status=SessionStatus.IN_PROGRESS.value,
            started_at=now,
            updated_at=now,
        )
    )
    db.add(_evaluated_question(id=42, session_id=IN_PROGRESS_SESSION_ID, question="Q1?", question_number=1))
    db.add(_evaluated_question(id=43, session_id=IN_PROGRESS_SESSION_ID, question="Q2?", question_number=2))
    db.add(
        InterviewQuestion(
            id=CURRENT_QUESTION_ID,
            session_id=IN_PROGRESS_SESSION_ID,
            question="Q3?",
            difficulty=3,
            question_number=3,
            status=QuestionStatus.ACTIVE.value,
            created_at=now,
        )
    )

    # Session 24 — historical completed case, owned by user 10: questions 1..5
    # evaluated plus one archived question with a NULL number.
    db.add(
        InterviewSession(
            id=HISTORICAL_SESSION_ID,
            user_id=OTHER_USER_ID,
            role="backend",
            status=SessionStatus.COMPLETED.value,
            started_at=now,
            updated_at=now,
            finished_at=now,
            overall_score=8.0,
            recommendation="Hire",
        )
    )
    for number, qid in enumerate((60, 61, 62, 63, 64), start=1):
        db.add(
            _evaluated_question(
                id=qid,
                session_id=HISTORICAL_SESSION_ID,
                question=f"Historical {number}?",
                question_number=number,
            )
        )
    db.add(
        InterviewQuestion(
            id=65,
            session_id=HISTORICAL_SESSION_ID,
            question="Archived question",
            difficulty=3,
            question_number=None,
            status=QuestionStatus.LEGACY_ARCHIVED.value,
            created_at=now,
        )
    )

    db.flush()
    _reset_sequences(db)
    db.commit()


DEFAULT_FAKE_QUESTION = "Why is CI/CD important for backend engineers?"


def make_fake_interview_service(
    first_question: str = DEFAULT_FAKE_QUESTION,
    eligible: bool = True,
):
    """An InterviewService wired to stub AI/domain helpers, with no __init__.

    PostgreSQL is the workflow authority, so the manager holds no session
    state: ``start_interview`` only needs these stateless components to check
    eligibility and generate the first question.
    """
    from services.interview_service import InterviewService

    chunks = [
        SimpleNamespace(chunk=SimpleNamespace(role="user", content="cv context")),
        SimpleNamespace(
            chunk=SimpleNamespace(role="knowledge", content="knowledge context")
        ),
    ]
    service = InterviewService.__new__(InterviewService)
    service.manager = SimpleNamespace(
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
            ensure_cv_store=lambda user_id, cv_path: None,
            ensure_knowledge_store=lambda role: None,
            retrieve_hybrid_isolated=lambda query, cv_store, knowledge_store: chunks,
        ),
        prompt_builder=SimpleNamespace(
            build_question_prompt=(
                lambda role, difficulty, cv_chunks, knowledge_chunks: "prompt"
            )
        ),
        provider=SimpleNamespace(generate_question=lambda prompt: first_question),
    )
    return service


@pytest.fixture
def seeded_workflow():
    """Seed the canonical durable-workflow state before a test; clean up after."""
    from database import SessionLocal

    db = SessionLocal()
    try:
        _seed(db)
    finally:
        db.close()

    yield

    db = SessionLocal()
    try:
        for session_id in _SEED_SESSION_IDS:
            _delete_session_tree(db, session_id)
        db.commit()
    finally:
        db.close()
