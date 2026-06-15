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
    """Request payload for evaluating an interview answer."""

    role: str
    question: str
    answer: str


class EvaluationResponse(BaseModel):
    """Response payload with structured evaluation results."""

    score: int = Field(ge=0, le=10)
    strengths: list[str]
    weaknesses: list[str]
    feedback: str
    follow_up_question: str


class ReportRequest(BaseModel):
    """Request payload for generating a PDF interview report."""

    role: str
    question: str
    answer: str
    score: int = Field(ge=0, le=10)
    strengths: list[str]
    weaknesses: list[str]
    feedback: str
    follow_up_question: str


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
