from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from database import Base

from sqlalchemy import ForeignKey, Float
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
        default="in_progress",
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

    session = relationship(
        "InterviewSession",
        back_populates="questions",
    )