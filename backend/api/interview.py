from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from schemas import EvaluationRequest
from services.interview_service import InterviewService
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


@router.post("/adaptive-interview", response_model=dict)
def adaptive_interview(request: EvaluationRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Evaluate an answer and return the next adaptive question."""
    if request.question_id is None:
        raise HTTPException(status_code=400, detail="question_id is required")
    if request.session_id is None:
        raise HTTPException(status_code=400, detail="session_id is required")

    try:
        # fetch session and check ownership
        session_obj = get_session_by_id(db=db, session_id=request.session_id) if request.session_id else None
        if session_obj and session_obj.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Forbidden")

        service = _get_interview_service()
        return service.submit_answer(
            user_id=current_user.id,
            session_id=request.session_id,
            question_id=request.question_id,
            answer=request.answer,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/finish-interview", response_model=dict)
def finish_interview(request: FinishInterviewRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Return an overall summary for a completed interview."""
    session_obj = get_session_by_id(db=db, session_id=request.session_id)
    if session_obj is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session_obj.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    service = _get_interview_service()
    return service.finish_interview(session_id=request.session_id)
