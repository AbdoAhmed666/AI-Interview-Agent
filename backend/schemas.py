"""Pydantic models for the AI Interview Agent backend.

This module keeps request and response contracts separate from API routes.
"""

from datetime import datetime

from pydantic import BaseModel, Field
from pydantic import ConfigDict

class InterviewRequest(BaseModel):
    """Request payload for starting an interview."""

    role: str


class InterviewResponse(BaseModel):
    """Response payload for starting an interview."""

    session_id: int
    question_id: int
    role: str
    question: str


# class EvaluationRequest(BaseModel):

#     role: str

#     question: str

#     answer: str

#     current_difficulty: int = Field(ge=1, le=5)
class EvaluationRequest(BaseModel):
    question_id: int
    answer: str


class EvaluationResponse(BaseModel):

    score: int = Field(ge=0, le=10)

    level: str

    strengths: list[str]

    weaknesses: list[str]

    feedback: str

    concept_gaps: list[str]

    follow_up_question: str


class QuestionEvaluation(BaseModel):

    score: int = Field(ge=0, le=10)

    level: str

    strengths: list[str]

    weaknesses: list[str]

    feedback: str

    concept_gaps: list[str]

    follow_up_question: str

class AdaptiveEvaluationResponse(BaseModel):

    evaluation: EvaluationResponse

    question_id: int

    next_question: str

    difficulty: int

    decision: str

class ReportRequest(BaseModel):
    role: str

    overall_score: int = Field(ge=0, le=10)

    overall_strengths: list[str]
    overall_weaknesses: list[str]

    hiring_recommendation: str

    questions: list[str]
    answers: list[str]

    evaluations: list[QuestionEvaluation]


class SessionSummaryRequest(BaseModel):
    """Request payload for a full interview session summary."""

    role: str
    questions: list[str]
    answers: list[str]
    evaluations: list[QuestionEvaluation]


class SessionSummaryResponse(BaseModel):
    """Response payload for a final interview summary."""

    overall_score: int = Field(ge=0, le=10)
    overall_strengths: list[str]
    overall_weaknesses: list[str]
    hiring_recommendation: str


from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

    model_config = {
        "from_attributes": True
    }


class Token(BaseModel):
    access_token: str
    token_type: str

class FinishInterviewRequest(BaseModel):
    session_id: int

class FinishInterviewResponse(BaseModel):
    overall_score: float
    recommendation: str

class Config:
    orm_mode = True

class InterviewSessionResponse(BaseModel):
    id: int
    role: str
    status: str
    overall_score: float | None
    recommendation: str | None
    started_at: datetime
    finished_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True,
    )

class QuestionHistory(BaseModel):

    id: int

    question: str

    answer: str | None

    score: float | None

    feedback: str | None

    difficulty: int

    model_config = ConfigDict(
        from_attributes=True,
    )

class SessionDetails(BaseModel):

    id: int

    role: str

    overall_score: float | None

    recommendation: str | None

    status: str

    started_at: datetime

    finished_at: datetime | None

    questions: list[QuestionHistory]

    model_config = ConfigDict(
        from_attributes=True,
    )