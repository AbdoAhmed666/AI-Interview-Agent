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


def evaluate_answer(
        role: str,
        question: str,
        answer: str,
        difficulty: int
) -> EvaluationResponse:
    """Generate an evaluation result and validate it before returning it."""
    prompt = build_evaluation_prompt(
        role=role,
        question=question,
        answer=answer,
        difficulty=difficulty
    )
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
    title_style.spaceAfter = 20
    heading_style.spaceAfter = 10
    body_style.spaceAfter = 5

    story = []
    story.append(Paragraph("<b>AI Interview Report</b>", title_style))
    story.append(Spacer(1, 5))
    story.append(Paragraph("<font color='grey'>Generated AI-powered interview analysis</font>", body_style))
    story.append(Spacer(1, 15))

    first_eval = report.evaluations[0]
    eval_dict = (
        first_eval.model_dump()
        if hasattr(first_eval, "model_dump")
        else first_eval.dict()
    )

    story.append(Paragraph(f"<b>First Question Level:</b> {eval_dict.get('level', 'N/A')}", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Concept Gaps (Sample):</b>", body_style))

    for gap in eval_dict.get("concept_gaps", [])[:5]:
        story.append(Paragraph(f"• {gap}", body_style))

    story.append(Spacer(1, 15))

    summary_data = [
        ["Role", report.role],
        ["Overall Score", f"{report.overall_score}/10"],
        ["Recommendation", report.hiring_recommendation],
    ]

    summary_table = Table(summary_data, colWidths=[160, 340])

    summary_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
            ]
        )
    )

    story.append(summary_table)

    story.append(Spacer(1, 20))

    story.append(Paragraph("Overall Strengths", heading_style))

    for item in report.overall_strengths:
        story.append(Paragraph(f"• {item}", body_style))

    story.append(Spacer(1, 12))

    story.append(Paragraph("Areas for Improvement", heading_style))

    for item in report.overall_weaknesses:
        story.append(Paragraph(f"• {item}", body_style))

    story.append(Spacer(1, 20))

    story.append(Paragraph("Question Scores", heading_style))

    score_table_data = [["Question", "Score", "Level"]]

    for i, evaluation in enumerate(report.evaluations):

        eval_dict = (
            evaluation.model_dump()
            if hasattr(evaluation, "model_dump")
            else evaluation.dict()
        )

        score_table_data.append(
            [
                f"Question {i+1}",
                str(eval_dict.get("score", "N/A")),
                eval_dict.get("level", "N/A")
            ]
        )

    score_table = Table(score_table_data,colWidths=[220, 80, 100])

    score_table.setStyle(
        TableStyle(
            [
                ("GRID", (0,0), (-1,-1), 1, colors.black),
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#4472C4")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS",
                    (0,1), (-1,-1),
                    [colors.whitesmoke, colors.lightgrey]),
            ]
        )
    )

    story.append(score_table)

    story.append(Spacer(1, 20))

    story.append(Paragraph("Interview Details", heading_style))
    story.append(Spacer(1, 10))

    for i, question in enumerate(report.questions):

        story.append(
            Paragraph(
                f"<b>Question {i+1}</b>",
                heading_style,
            )
        )

        story.append(Paragraph(f"<b>Q{i+1}:</b> {question}", body_style))
        story.append(Spacer(1, 5))

        story.append(
            Paragraph(
                "<b>Candidate Answer</b>",
                body_style,
            )
        )

        story.append(Paragraph("<b>Answer:</b>", body_style))
        story.append(Paragraph(report.answers[i], body_style))

        evaluation = report.evaluations[i]

        eval_dict = evaluation.model_dump() if hasattr(evaluation, "model_dump") else evaluation.dict()

        story.append(
            Paragraph(
                f"<b>Score:</b> {eval_dict.get('score', 'N/A')}/10",
                body_style,
            )
        )

        story.append(
            Paragraph(
                f"<b>Level:</b> {eval_dict.get('level', 'N/A')}",
                body_style,
            )
        )

        story.append(
            Paragraph(
                f"<b>Feedback:</b> {eval_dict.get('feedback', '')}",
                body_style,
            )
        )

        story.append(
            Paragraph(
                "<b>Concept Gaps:</b>",
                body_style,
            )
        )

        for gap in eval_dict.get("concept_gaps", []):

            story.append(
                Paragraph(
                    f"- {gap}",
                    body_style,
                )
            )

        story.append(
            Spacer(1, 15)
        )

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
