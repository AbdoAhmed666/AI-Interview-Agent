"""Database primitives for the PostgreSQL-authoritative interview workflow.

These functions participate in a caller-owned SQLAlchemy transaction. They add,
mutate, flush, or query ORM objects but never commit or close the session.
"""

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from models import InterviewAuditLog, InterviewQuestion, InterviewSession
from schemas import QuestionStatus, SessionStatus


_ACTIVE_QUESTION_STATUSES = (
    QuestionStatus.ACTIVE.value,
    QuestionStatus.EVALUATING.value,
    QuestionStatus.EVALUATION_FAILED.value,
)
_UNSET = object()


def _value(value: str | SessionStatus | QuestionStatus) -> str:
    return value.value if isinstance(value, (SessionStatus, QuestionStatus)) else value


def get_session(db: Session, session_id: int) -> InterviewSession | None:
    return (
        db.query(InterviewSession)
        .filter(InterviewSession.id == session_id)
        .first()
    )


def get_session_for_update(
    db: Session,
    session_id: int,
    user_id: int | None = None,
) -> InterviewSession | None:
    query = db.query(InterviewSession).filter(InterviewSession.id == session_id)
    if user_id is not None:
        query = query.filter(InterviewSession.user_id == user_id)
    return query.with_for_update().first()


def create_session(
    db: Session,
    user_id: int,
    role: str,
    *,
    status: str | SessionStatus = SessionStatus.IN_PROGRESS,
    started_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> InterviewSession:
    now = datetime.utcnow()
    session = InterviewSession(
        user_id=user_id,
        role=role,
        status=_value(status),
        started_at=started_at or now,
        updated_at=updated_at or now,
    )
    db.add(session)
    db.flush()
    return session


def update_session_state(
    db: Session,
    session: InterviewSession,
    *,
    status: str | SessionStatus,
    updated_at: datetime | None = None,
    overall_score: float | None | object = _UNSET,
    recommendation: str | None | object = _UNSET,
    finished_at: datetime | None | object = _UNSET,
) -> InterviewSession:
    session.status = _value(status)
    session.updated_at = updated_at or datetime.utcnow()
    if overall_score is not _UNSET:
        session.overall_score = overall_score
    if recommendation is not _UNSET:
        session.recommendation = recommendation
    if finished_at is not _UNSET:
        session.finished_at = finished_at
    db.flush()
    return session


def get_question(db: Session, question_id: int) -> InterviewQuestion | None:
    return (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.id == question_id)
        .first()
    )


def get_question_for_session(
    db: Session,
    session_id: int,
    question_id: int,
) -> InterviewQuestion | None:
    return (
        db.query(InterviewQuestion)
        .filter(
            InterviewQuestion.session_id == session_id,
            InterviewQuestion.id == question_id,
        )
        .first()
    )


def get_question_for_session_for_update(
    db: Session,
    session_id: int,
    question_id: int,
) -> InterviewQuestion | None:
    return (
        db.query(InterviewQuestion)
        .filter(
            InterviewQuestion.session_id == session_id,
            InterviewQuestion.id == question_id,
        )
        .with_for_update()
        .first()
    )


def get_current_question(
    db: Session,
    session_id: int,
    *,
    for_update: bool = False,
) -> InterviewQuestion | None:
    query = (
        db.query(InterviewQuestion)
        .filter(
            InterviewQuestion.session_id == session_id,
            InterviewQuestion.status.in_(_ACTIVE_QUESTION_STATUSES),
        )
        .order_by(InterviewQuestion.question_number.asc())
    )
    if for_update:
        query = query.with_for_update()
    return query.first()


def get_question_by_number(
    db: Session,
    session_id: int,
    question_number: int,
) -> InterviewQuestion | None:
    return (
        db.query(InterviewQuestion)
        .filter(
            InterviewQuestion.session_id == session_id,
            InterviewQuestion.question_number == question_number,
        )
        .first()
    )


def list_questions(db: Session, session_id: int) -> list[InterviewQuestion]:
    return (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.session_id == session_id)
        .order_by(
            InterviewQuestion.question_number.asc().nullslast(),
            InterviewQuestion.id.asc(),
        )
        .all()
    )


def create_question(
    db: Session,
    session_id: int,
    question: str,
    difficulty: int,
    *,
    question_number: int | None = None,
    status: str | QuestionStatus = QuestionStatus.ACTIVE,
    created_at: datetime | None = None,
) -> InterviewQuestion:
    question_row = InterviewQuestion(
        session_id=session_id,
        question=question,
        difficulty=difficulty,
        question_number=question_number,
        status=_value(status),
        created_at=created_at or datetime.utcnow(),
    )
    db.add(question_row)
    db.flush()
    return question_row


def update_question(
    db: Session,
    question: InterviewQuestion,
    *,
    status: str | QuestionStatus | object = _UNSET,
    answer: str | None | object = _UNSET,
    score: float | None | object = _UNSET,
    feedback: str | None | object = _UNSET,
    evaluation: dict[str, Any] | None | object = _UNSET,
    answer_submitted_at: datetime | None | object = _UNSET,
    evaluated_at: datetime | None | object = _UNSET,
) -> InterviewQuestion:
    if status is not _UNSET:
        question.status = _value(status)
    if answer is not _UNSET:
        question.answer = answer
    if score is not _UNSET:
        question.score = score
    if feedback is not _UNSET:
        question.feedback = feedback
    if evaluation is not _UNSET:
        question.evaluation = evaluation
    if answer_submitted_at is not _UNSET:
        question.answer_submitted_at = answer_submitted_at
    if evaluated_at is not _UNSET:
        question.evaluated_at = evaluated_at
    db.flush()
    return question


def create_audit_event(
    db: Session,
    session_id: int,
    event_type: str,
    *,
    question_id: int | None = None,
    details: dict[str, Any] | None = None,
    question_number: int | None = None,
    from_status: str | SessionStatus | QuestionStatus | None = None,
    to_status: str | SessionStatus | QuestionStatus | None = None,
    created_at: datetime | None = None,
) -> InterviewAuditLog:
    audit_details = dict(details) if details is not None else None
    if question_number is not None:
        audit_details = audit_details or {}
        audit_details.setdefault("question_number", question_number)

    audit = InterviewAuditLog(
        session_id=session_id,
        question_id=question_id,
        event_type=event_type,
        from_status=_value(from_status) if from_status is not None else None,
        to_status=_value(to_status) if to_status is not None else None,
        details=audit_details,
        created_at=created_at or datetime.utcnow(),
    )
    db.add(audit)
    db.flush()
    return audit


def list_audit_events(
    db: Session,
    session_id: int,
) -> list[InterviewAuditLog]:
    return (
        db.query(InterviewAuditLog)
        .filter(InterviewAuditLog.session_id == session_id)
        .order_by(InterviewAuditLog.created_at.asc(), InterviewAuditLog.id.asc())
        .all()
    )
