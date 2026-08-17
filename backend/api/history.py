from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from security import get_current_user
from crud import get_sessions_by_user, get_session_with_questions
from models import User

router = APIRouter()


@router.get("/my-sessions")
def my_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return a lightweight list of sessions for the authenticated user."""
    sessions = get_sessions_by_user(db, current_user.id)

    out = []
    for s in sessions:
        out.append(
            {
                "id": s.id,
                "role": s.role,
                "status": s.status,
                "overall_score": s.overall_score,
                "recommendation": s.recommendation,
                "started_at": s.started_at.isoformat() if s.started_at else None,
            }
        )

    return out


@router.get("/session/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = get_session_with_questions(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    questions = []
    for q in session.questions:
        questions.append(
            {
                "id": q.id,
                "question": q.question,
                "answer": q.answer,
                "score": q.score,
                "feedback": q.feedback,
                "difficulty": q.difficulty,
                "created_at": q.created_at.isoformat() if q.created_at else None,
            }
        )

    return {
        "id": session.id,
        "role": session.role,
        "status": session.status,
        "overall_score": session.overall_score,
        "recommendation": session.recommendation,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "finished_at": session.finished_at.isoformat() if session.finished_at else None,
        "questions": questions,
    }
