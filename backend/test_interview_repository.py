import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from database import SessionLocal
from models import InterviewAuditLog, InterviewQuestion, InterviewSession
from repositories.interview_repository import (
    create_audit_event,
    create_question,
    create_session,
    get_current_question,
    get_question,
    get_question_for_session,
    get_session,
    get_session_for_update,
    list_questions,
    update_question,
    update_session_state,
)
from schemas import QuestionStatus, SessionStatus


def test_get_session_and_current_question():
    db = SessionLocal()
    try:
        session = get_session(db, 23)
        assert session is not None
        assert get_current_question(db, session.id).id == 44
        assert get_question(db, 44).id == 44
        assert get_question_for_session(db, 23, 44).id == 44
    finally:
        db.close()


def test_get_session_for_update_uses_row_lock():
    db = SessionLocal()
    try:
        session = get_session_for_update(db, 23, user_id=9)
        assert session is not None
        assert session.id == 23
        assert get_current_question(db, session.id, for_update=True).id == 44
    finally:
        db.rollback()
        db.close()


def test_repository_mutations_do_not_commit_and_audit_uses_caller_transaction():
    db = SessionLocal()
    created_session_id = None
    created_question_id = None
    try:
        session = create_session(db, user_id=9, role="backend")
        created_session_id = session.id
        question = create_question(
            db,
            session.id,
            "Repository question",
            difficulty=3,
            question_number=1,
        )
        created_question_id = question.id
        update_question(
            db,
            question,
            status=QuestionStatus.EVALUATED,
            answer="Answer",
            score=8,
            feedback="Good",
            evaluation={
                "score": 8,
                "level": "strong",
                "strengths": [],
                "weaknesses": [],
                "feedback": "Good",
                "concept_gaps": [],
                "follow_up_question": "Next",
            },
            evaluated_at=datetime.utcnow(),
        )
        update_session_state(db, session, status=SessionStatus.IN_PROGRESS)
        audit = create_audit_event(
            db,
            session.id,
            "TEST_EVENT",
            question_id=question.id,
            question_number=1,
            from_status=QuestionStatus.ACTIVE,
            to_status=QuestionStatus.EVALUATED,
            details={"source": "test"},
        )
        assert audit.id is not None
        assert list_questions(db, session.id)[0].id == question.id
        assert get_session(db, session.id).status == SessionStatus.IN_PROGRESS.value
    finally:
        db.rollback()
        db.close()

    verification_db = SessionLocal()
    try:
        assert verification_db.get(InterviewSession, created_session_id) is None
        assert verification_db.get(InterviewQuestion, created_question_id) is None
        assert verification_db.query(InterviewAuditLog).filter_by(event_type="TEST_EVENT").count() == 0
    finally:
        verification_db.close()


def test_question_ordering_places_archived_null_number_last():
    db = SessionLocal()
    try:
        questions = list_questions(db, 24)
        assert [question.question_number for question in questions] == [1, 2, 3, 4, 5, None]
        assert questions[-1].status == QuestionStatus.LEGACY_ARCHIVED.value
    finally:
        db.close()
