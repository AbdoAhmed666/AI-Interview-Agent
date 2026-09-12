from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

from database import Base

from sqlalchemy import Float
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    email = Column(String(255), unique=True, nullable=False, index=True)

    hashed_password = Column(String(255), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)

    is_superuser = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    interview_sessions = relationship(
        "InterviewSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    role = Column(
        String(100),
        nullable=False,
    )

    overall_score = Column(
        Float,
        nullable=True,
    )

    recommendation = Column(
        String(50),
        nullable=True,
    )

    status = Column(
        String(30),
        default="IN_PROGRESS",
        nullable=False,
    )

    started_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    finished_at = Column(
        DateTime,
        nullable=True,
    )

    updated_at = Column(
        DateTime,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('IN_PROGRESS', 'GENERATING', 'GENERATION_FAILED', 'READY_TO_FINISH', 'COMPLETED')",
            name="ck_interview_sessions_status",
        ),
        Index(
            "ix_interview_sessions_user_status",
            "user_id",
            "status",
        ),
    )

    user = relationship(
        "User",
        back_populates="interview_sessions",
    )

    questions = relationship(
        "InterviewQuestion",
        back_populates="session",
        cascade="all, delete-orphan",
    )

class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    session_id = Column(
        Integer,
        ForeignKey("interview_sessions.id"),
        nullable=False,
    )

    question = Column(
        String,
        nullable=False,
    )

    answer = Column(
        String,
        nullable=True,
    )

    score = Column(
        Float,
        nullable=True,
    )

    feedback = Column(
        String,
        nullable=True,
    )

    difficulty = Column(
        Integer,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    question_number = Column(
        Integer,
        nullable=True,
    )

    status = Column(
        String(30),
        default="ACTIVE",
        nullable=False,
    )

    evaluation = Column(
        JSONB,
        nullable=True,
    )

    answer_submitted_at = Column(
        DateTime,
        nullable=True,
    )

    evaluated_at = Column(
        DateTime,
        nullable=True,
    )

    __table_args__ = (
        CheckConstraint(
            "question_number IS NULL OR question_number BETWEEN 1 AND 5",
            name="ck_interview_questions_number_range",
        ),
        CheckConstraint(
            "status <> 'LEGACY_ARCHIVED' OR question_number IS NULL",
            name="ck_interview_questions_archived_number",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'EVALUATING', 'EVALUATION_FAILED', 'EVALUATED', 'LEGACY_EVALUATED', 'LEGACY_ARCHIVED')",
            name="ck_interview_questions_status",
        ),
        Index(
            "uq_interview_questions_session_number",
            "session_id",
            "question_number",
            unique=True,
            postgresql_where=question_number.isnot(None),
        ),
        Index(
            "uq_interview_questions_one_active",
            "session_id",
            unique=True,
            postgresql_where=status.in_(
                ("ACTIVE", "EVALUATING", "EVALUATION_FAILED")
            ),
        ),
    )

    session = relationship(
        "InterviewSession",
        back_populates="questions",
    )


class InterviewAuditLog(Base):
    __tablename__ = "interview_audit_log"

    id = Column(Integer, primary_key=True)

    session_id = Column(
        Integer,
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    question_id = Column(
        Integer,
        ForeignKey("interview_questions.id", ondelete="CASCADE"),
        nullable=True,
    )

    event_type = Column(
        String(50),
        nullable=False,
    )

    from_status = Column(
        String(30),
        nullable=True,
    )

    to_status = Column(
        String(30),
        nullable=True,
    )

    details = Column(
        JSONB,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_interview_audit_log_session_created",
            "session_id",
            "created_at",
        ),
    )