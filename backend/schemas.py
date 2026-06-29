"""Pydantic models for the AI Interview Agent backend.

This module keeps request and response contracts separate from API routes.
"""

from pydantic import BaseModel, Field


class InterviewRequest(BaseModel):
    """Request payload for starting an interview."""

    role: str


class InterviewResponse(BaseModel):
    """Response payload with a mock interview question."""

    role: str
    question: str


class EvaluationRequest(BaseModel):

    role: str

    question: str

    answer: str

    current_difficulty: int = Field(ge=1, le=5)


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