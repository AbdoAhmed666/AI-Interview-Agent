"""FastAPI entry point for the AI Interview Agent project.

This file contains the API routes only.
"""

import os
import sys

from fastapi import FastAPI, HTTPException, Depends
import logging

try:
    from pypdf.errors import PdfReadError
except Exception:
    PdfReadError = None
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from security import get_current_user

from api.cv import router as cv_router
from api.interview import router as interview_router
from api.history import router as history_router
from auth import router as auth_router
from config import settings
from evaluator import build_report_pdf, evaluate_answer, summarize_session
from llm_provider import GeminiProvider, get_provider
from schemas import EvaluationRequest, EvaluationResponse, InterviewRequest, InterviewResponse, ReportRequest, SessionSummaryRequest, SessionSummaryResponse
from services.interview_service import InterviewService

app = FastAPI(title="AI Interview Agent API")

# Configure CORS for the frontend origin(s)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(cv_router)
app.include_router(interview_router)
app.include_router(history_router)

interview_service = InterviewService()


@app.get("/")
def read_root() -> dict[str, str]:
    """Simple health-check endpoint for the backend."""
    return {"message": "AI Interview Agent backend is running."}


@app.post("/start-interview")
def start_interview(
    request: InterviewRequest, current_user=Depends(get_current_user)
) -> dict[str, object]:
    """Start the interview flow using the active CV and eligibility checks."""
    try:
        return interview_service.start_interview(user_id=current_user.id, role=request.role)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        # If the error was caused by PDF parsing/analysis, return a 502
        # so the frontend can show a clear message instead of the server
        # crashing or returning a generic 500/Network Error.
        logging.exception("start_interview failed for user_id=%s: %s", getattr(current_user, 'id', None), exc)
        if PdfReadError is not None and isinstance(exc, PdfReadError):
            raise HTTPException(status_code=502, detail=f"CV analysis failed: {str(exc)}") from exc
        # For other exceptions, re-raise as a 500 with detail to help debugging.
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/evaluate-answer", response_model=EvaluationResponse)
def evaluate_answer_endpoint(request: EvaluationRequest) -> EvaluationResponse:
    """Evaluate a candidate answer and validate the returned JSON structure."""
    try:
        return evaluate_answer(request.role, request.question, request.answer)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/summarize-session", response_model=SessionSummaryResponse)
def summarize_session_endpoint(request: SessionSummaryRequest) -> SessionSummaryResponse:
    """Generate a final summary for a complete interview session."""
    try:
        return summarize_session(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post(
    "/download-report",
    response_class=StreamingResponse,
    responses={200: {"content": {"application/pdf": {}}, "description": "PDF download"}},
)
def download_report(request: ReportRequest) -> StreamingResponse:
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
