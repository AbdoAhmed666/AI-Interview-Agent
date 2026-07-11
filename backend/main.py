"""FastAPI entry point for the AI Interview Agent project.

This file contains the API routes only.
"""

import os
import sys

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from auth import router as auth_router
from adaptive_engine import AdaptiveEngine

from config import settings

from evaluator import (
    build_report_pdf,
    evaluate_answer,
    summarize_session,
)

from interview import generate_question

from llm_provider import GeminiProvider, get_provider

from schemas import (
    AdaptiveEvaluationResponse,
    EvaluationRequest,
    EvaluationResponse,
    FinishInterviewRequest,
    FinishInterviewResponse,
    InterviewRequest,
    InterviewResponse,
    InterviewSessionResponse,
    ReportRequest,
    SessionSummaryRequest,
    SessionSummaryResponse,
    SessionDetails,
)


from security import get_current_user
from models import User
from fastapi import Depends

from sqlalchemy.orm import Session

from database import get_db
from crud import create_interview_session, create_question, get_question_by_id, get_session_by_id, update_question_result

from services import (
    calculate_overall_score,
    get_recommendation,
)

from crud import (
    finish_interview_session,
    get_questions_by_session,
    get_session_by_id,
    get_session_with_questions, 
)
from crud import get_sessions_by_user

app = FastAPI(title="AI Interview Agent API")
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root() -> dict[str, str]:
    """Simple health-check endpoint for the backend."""
    return {"message": "AI Interview Agent backend is running."}


@app.post("/start-interview", response_model=InterviewResponse)
def start_interview(
    request: InterviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InterviewResponse:
    """Return a mock interview question for the selected role."""
    interview_session = create_interview_session(
        db=db,
        user_id=current_user.id,
        role=request.role,
    )

    question = generate_question(
        role=request.role,
        difficulty=3,
    )

    db_question = create_question(
        db=db,
        session_id=interview_session.id,
        question=question,
        difficulty=3,
    )

    return InterviewResponse(
        session_id=interview_session.id,
        question_id=db_question.id,
        role=request.role,
        question=db_question.question,
    )


@app.post("/evaluate-answer", response_model=EvaluationResponse)
def evaluate_answer_endpoint(
    request: EvaluationRequest,
    db: Session = Depends(get_db),
) -> EvaluationResponse:
    """Evaluate a candidate answer and validate the returned JSON structure."""
    try:
        db_question = get_question_by_id(
            db,
            request.question_id,
        )

        if db_question is None:
            raise HTTPException(
                status_code=404,
                detail="Question not found."
            )
        
        db_session = get_session_by_id(
            db,
            db_question.session_id,
        )

        if db_session is None:
            raise HTTPException(
                status_code=404,
                detail="Question not found."
            )

        evaluation = evaluate_answer(
            db_session.role,
            db_question.question,
            request.answer,
            db_question.difficulty,
        )

        update_question_result(
            db=db,
            question=db_question,
            answer=request.answer,
            score=evaluation.score,
            feedback=evaluation.feedback,
        )
        return evaluation
        
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
@app.post(
    "/adaptive-interview",
    response_model=AdaptiveEvaluationResponse,
)
def adaptive_interview(
    request: EvaluationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AdaptiveEvaluationResponse:

    db_question = get_question_by_id(
        db,
        request.question_id,
    )

    if db_question is None:
        raise HTTPException(
            status_code=404,
            detail="Question not found.",
        )

    session = get_session_by_id(
        db,
        db_question.session_id,
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Interview session not found.",
        )

    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Access denied.",
        )

    evaluation = evaluate_answer(
        role=session.role,
        question=db_question.question,
        answer=request.answer,
        difficulty=db_question.difficulty,
    )

    update_question_result(
        db=db,
        question=db_question,
        answer=request.answer,
        score=evaluation.score,
        feedback=evaluation.feedback,
    )

    next_difficulty, decision = AdaptiveEngine.get_next_difficulty(
        evaluation.level,
        db_question.difficulty,
    )

    next_question = generate_question(
        role=session.role,
        difficulty=next_difficulty,
    )   

    new_question = create_question(
        db=db,
        session_id=session.id,
        question=next_question,
        difficulty=next_difficulty,
    )

    return AdaptiveEvaluationResponse(
        evaluation=evaluation,
        question_id=new_question.id,
        next_question=new_question.question,
        difficulty=next_difficulty,
        decision=decision,
    )

@app.post("/summarize-session", response_model=SessionSummaryResponse)
def summarize_session_endpoint(
    request: SessionSummaryRequest,
    current_user: User = Depends(get_current_user),) -> SessionSummaryResponse:
    """Generate a final summary for a complete interview session."""
    try:
        return summarize_session(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post(
    "/finish-interview",
    response_model=FinishInterviewResponse,
)
def finish_interview(
    request: FinishInterviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = get_session_by_id(
        db,
        request.session_id,
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Interview session not found.",
        )
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Access denied.",
        )
    questions = get_questions_by_session(
        db,
        session.id,
    )
    overall = calculate_overall_score(
        questions,
    )
    recommendation = get_recommendation(
        overall,
    )

    finish_interview_session(
        db=db,
        session=session,
        overall_score=overall,
        recommendation=recommendation,
    )

    return FinishInterviewResponse(
        overall_score=overall,
        recommendation=recommendation,
    )


@app.post(
    "/download-report",
    response_class=StreamingResponse,
    responses={200: {"content": {"application/pdf": {}}, "description": "PDF download"}},
)
def download_report(
    request: ReportRequest,
    current_user: User = Depends(get_current_user),) -> StreamingResponse:
    """Generate and return an interview report PDF in memory."""
    pdf_bytes = build_report_pdf(request)
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="interview_report.pdf"',
            "Content-Type": "application/pdf",
        },
    )


@app.get("/debug/provider")
def debug_provider() -> dict[str, object]:
    """Return provider selection metadata for debugging purposes."""
    return {
        "provider": type(get_provider()).__name__,
        "model_name": settings.model_name,
        "has_gemini_key": bool(settings.gemini_api_key),
    }


@app.get("/debug/gemini")
def debug_gemini() -> dict[str, object]:
    """Temporarily test Gemini provider behavior and capture errors."""
    try:
        response = GeminiProvider().generate_question("Say hello")
        return {
            "success": True,
            "response": response,
            "error_type": None,
            "error_message": None,
        }
    except Exception as exc:
        return {
            "success": False,
            "response": None,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        }


@app.get("/debug/imports")
def debug_imports() -> dict[str, object]:
    """Inspect Python import resolution inside the FastAPI process."""
    import_result = {"sys_executable": sys.executable, "sys_path": sys.path, "cwd": os.getcwd()}

    try:
        import google

        import_result["google_file"] = getattr(google, "__file__", None)
    except Exception as exc:
        import_result["google_import_error_type"] = type(exc).__name__
        import_result["google_import_error_message"] = str(exc)

    try:
        from google import genai

        import_result["genai_import_success"] = True
        import_result["genai_import_error_type"] = None
        import_result["genai_import_error_message"] = None
        import_result["genai_file"] = getattr(genai, "__file__", None)
    except Exception as exc:
        import_result["genai_import_success"] = False
        import_result["genai_import_error_type"] = type(exc).__name__
        import_result["genai_import_error_message"] = str(exc)

    return import_result

@app.get(
    "/my-sessions",
    response_model=list[InterviewSessionResponse],
)
def my_sessions(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):

    return get_sessions_by_user(
        db,
        current_user.id,
    )


@app.get(
    "/session/{session_id}",
    response_model=SessionDetails,
)
def session_details(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    session = get_session_with_questions(
        db,
        session_id,
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found.",
        )

    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Access denied.",
        )

    return session

