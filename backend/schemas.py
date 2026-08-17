"""Pydantic models for the AI Interview Agent backend.

This module keeps request and response contracts separate from API routes.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional


InterviewRole = Literal[
    "backend",
    "frontend",
    "ml",
    "data_science",
]


class InterviewRequest(BaseModel):
    """Request payload for starting an interview with a canonical role key."""

    role: InterviewRole


class Token(BaseModel):
    access_token: str
    token_type: str


class UserRegister(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: Optional[bool] = True


class InterviewResponse(BaseModel):
    """Response payload with a mock interview question."""

    role: str
    question: str


class EvaluationRequest(BaseModel):
    """Request payload for evaluating an interview answer."""

    role: str | None = None
    question: str | None = None
    answer: str
    session_id: int | None = None
    question_id: int | None = None


class EvaluationResponse(BaseModel):
    """Response payload with structured evaluation results."""

    score: int = Field(ge=0, le=10)
    level: str
    strengths: list[str]
    weaknesses: list[str]
    feedback: str
    concept_gaps: list[str]
    follow_up_question: str


class ReportRequest(BaseModel):
    role: str

    overall_score: int = Field(ge=0, le=10)

    overall_strengths: list[str]
    overall_weaknesses: list[str]

    hiring_recommendation: str

    questions: list[str]
    answers: list[str]

    evaluations: list[dict]


class SessionSummaryRequest(BaseModel):
    """Request payload for a full interview session summary."""

    role: str
    questions: list[str]
    answers: list[str]
    evaluations: list[dict]


class SessionSummaryResponse(BaseModel):
    """Response payload for a final interview summary."""

    overall_score: int = Field(ge=0, le=10)
    overall_strengths: list[str]
    overall_weaknesses: list[str]
    hiring_recommendation: str
