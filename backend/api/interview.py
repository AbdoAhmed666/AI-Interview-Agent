from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from schemas import EvaluationRequest
from services.interview_service import InterviewService
from services.interview_service import (
    AnswerClaimConflict,
    AnswerClaimNotFound,
    EvaluationPersistenceConflict,
    GenerationConflict,
    FinishConflict,
    FinishForbidden,
    FinishNotFoundError,
)
from security import get_current_user
from models import User
from database import get_db
from sqlalchemy.orm import Session
from crud import get_session_by_id

router = APIRouter()


def _get_interview_service() -> InterviewService:
    """Return the shared interview service instance for the app lifecycle."""
    from main import interview_service

    return interview_service


class FinishInterviewRequest(BaseModel):
    session_id: int


class RetryInterviewRequest(BaseModel):
    session_id: int
    question_id: int | None = None


@router.post("/adaptive-interview", response_model=dict)
def adaptive_interview(request: EvaluationRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Claim an answer durably before the later evaluation workflow."""
    if request.question_id is None:
        raise HTTPException(status_code=400, detail="question_id is required")
    if request.session_id is None:
        raise HTTPException(status_code=400, detail="session_id is required")

    try:
        service = _get_interview_service()
        claim_result = service.claim_answer(
            user_id=current_user.id,
            session_id=request.session_id,
            question_id=request.question_id,
            answer=request.answer,
        )
        if claim_result.get("already_submitted"):
            if claim_result.get("status") == "EVALUATED":
                return service.generate_next_question(
                    user_id=current_user.id,
                    session_id=request.session_id,
                    question_id=request.question_id,
                )
            return claim_result
        evaluation_result = service.evaluate_claimed_answer(
            user_id=current_user.id,
            session_id=request.session_id,
            question_id=request.question_id,
        )
        if evaluation_result.get("status") == "EVALUATED":
            return service.generate_next_question(
                user_id=current_user.id,
                session_id=request.session_id,
                question_id=request.question_id,
            )
        return evaluation_result
    except AnswerClaimNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AnswerClaimConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except EvaluationPersistenceConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except GenerationConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/finish-interview", response_model=dict)
def finish_interview(request: FinishInterviewRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Return an overall summary for a completed interview."""
    session_obj = get_session_by_id(db=db, session_id=request.session_id)
    if session_obj is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session_obj.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

        service = _get_interview_service()
    try:
        return service.finish_interview(
            user_id=current_user.id, session_id=request.session_id
        )
    except FinishNotFoundError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except FinishForbidden as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except FinishConflict as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/retry-evaluation", response_model=dict)
def retry_evaluation(
    request: RetryInterviewRequest,
    current_user: User = Depends(get_current_user),
) -> dict:
    if request.question_id is None:
        raise HTTPException(status_code=400, detail="question_id is required")
    try:
        return _get_interview_service().evaluate_claimed_answer(
            user_id=current_user.id,
            session_id=request.session_id,
            question_id=request.question_id,
        )
    except AnswerClaimNotFound as exc:
        raise HTTPException(status_code=404, detail="Interview not found") from exc
    except EvaluationPersistenceConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/retry-generation", response_model=dict)
def retry_generation(
    request: RetryInterviewRequest,
    current_user: User = Depends(get_current_user),
) -> dict:
    if request.question_id is None:
        raise HTTPException(status_code=400, detail="question_id is required")
    try:
        return _get_interview_service().generate_next_question(
            user_id=current_user.id,
            session_id=request.session_id,
            question_id=request.question_id,
        )
    except AnswerClaimNotFound as exc:
        raise HTTPException(status_code=404, detail="Interview not found") from exc
    except GenerationConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
