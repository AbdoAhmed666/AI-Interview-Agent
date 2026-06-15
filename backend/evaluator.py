"""Evaluation-related backend module.

This module turns provider output into a structured evaluation result and
supports reusable PDF report generation for interview summaries.
"""

import json
import logging
import re
from io import BytesIO
from datetime import datetime

from pydantic import ValidationError
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .history import save_interview_history
from .llm_provider import get_provider
from .prompts import build_evaluation_prompt, build_session_summary_prompt
from .schemas import EvaluationResponse, ReportRequest, SessionSummaryRequest, SessionSummaryResponse

logger = logging.getLogger(__name__)


def _extract_json_payload(text: str) -> str:
    """Extract the JSON object from model output, even if it is wrapped in markdown."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.IGNORECASE)

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]

    return cleaned.strip()


def evaluate_answer(role: str, question: str, answer: str) -> EvaluationResponse:
    """Generate an evaluation result and validate it before returning it."""
    prompt = build_evaluation_prompt(role=role, question=question, answer=answer)
    raw_response = get_provider().evaluate_answer(prompt)

    if logger.handlers:
        logger.info("RAW_EVALUATION_RESPONSE=%s", raw_response)
    else:
        print("RAW_EVALUATION_RESPONSE_START")
        print(raw_response)
        print("RAW_EVALUATION_RESPONSE_END")

    try:
        json_text = _extract_json_payload(raw_response)
        payload = json.loads(json_text)
        return EvaluationResponse.model_validate(payload)
    except (json.JSONDecodeError, TypeError, ValueError, ValidationError) as exc:
        raise ValueError(f"Invalid evaluation JSON returned by provider: {exc}") from exc


def summarize_session(session: SessionSummaryRequest) -> SessionSummaryResponse:
    """Generate a final summary for a full interview session."""
    prompt = build_session_summary_prompt(
        role=session.role,
        questions=session.questions,
        answers=session.answers,
        evaluations=session.evaluations,
    )
    raw_response = get_provider().summarize_session(prompt)

    if logger.handlers:
        logger.info("RAW_SESSION_SUMMARY_RESPONSE=%s", raw_response)
    else:
        print("RAW_SESSION_SUMMARY_RESPONSE_START")
        print(raw_response)
        print("RAW_SESSION_SUMMARY_RESPONSE_END")

    try:
        json_text = _extract_json_payload(raw_response)
        payload = json.loads(json_text)
        summary = SessionSummaryResponse.model_validate(payload)

        save_interview_history(
            role=session.role,
            overall_score=summary.overall_score,
            hiring_recommendation=summary.hiring_recommendation,
        )

        return summary
    except (json.JSONDecodeError, TypeError, ValueError, ValidationError) as exc:
        raise ValueError(f"Invalid session summary JSON returned by provider: {exc}") from exc


def build_report_pdf(report: ReportRequest) -> bytes:
    """Generate a PDF report in memory for the provided interview summary."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, title="AI Interview Report")

    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    heading_style = styles["Heading2"]
    body_style = styles["BodyText"]

    story = []
    story.append(Paragraph("AI Interview Report", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Interview Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style))
    story.append(Spacer(1, 12))

    summary_data = [
        ["Candidate Role", report.role],
        ["Score", f"{report.score}/10"],
    ]
    summary_table = Table(summary_data, colWidths=[160, 340])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5EEF7")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 18))

    def add_section(title: str, content: str | list[str]) -> None:
        story.append(Paragraph(title, heading_style))
        story.append(Spacer(1, 6))
        if isinstance(content, list):
            for item in content:
                story.append(Paragraph(f"• {item}", body_style))
        else:
            story.append(Paragraph(content, body_style))
        story.append(Spacer(1, 12))

    add_section("Interview Question", report.question)
    add_section("Candidate Answer", report.answer)
    add_section("Strengths", report.strengths or ["No strengths provided."])
    add_section("Weaknesses", report.weaknesses or ["No weaknesses provided."])
    add_section("Feedback", report.feedback)
    add_section("Follow-up Question", report.follow_up_question)

    story.append(Spacer(1, 24))
    story.append(Paragraph("Generated by AI Interview Agent", styles["Italic"]))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
