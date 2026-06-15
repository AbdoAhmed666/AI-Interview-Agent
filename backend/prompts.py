"""Prompt templates for the AI Interview Agent backend.

This module keeps prompt engineering separate from business logic.
"""


def build_interview_question_prompt(
    role: str,
    difficulty: str = "medium",
    interview_type: str = "technical",
) -> str:
    """Build a prompt for generating a clean interview question."""
    return (
        f"Generate one {difficulty} difficulty {interview_type} interview question "
        f"for a candidate applying for the role '{role}'. "
        "Return only the question text. "
        "Do not include explanations, difficulty analysis, bullet points, or markdown."
    )


def build_evaluation_prompt(role: str, question: str, answer: str) -> str:
    """Build a prompt that forces Gemini to return valid JSON only."""
    return (
        "You are evaluating a technical interview answer as a senior interviewer. "
        "Assess the answer on correctness, efficiency, scalability, edge cases, readability, and explanation quality. "
        "Do not give 10/10 unless the answer is truly exceptional. "
        "A correct answer can still lose points for weak performance discussion, missing trade-offs, or poor clarity. "
        "Return valid JSON only with exactly these fields: "
        "score (an integer from 0 to 10), "
        "strengths (an array of short strings), "
        "weaknesses (an array of short strings), "
        "feedback (a concise string), "
        "follow_up_question (a concise deeper question on the same topic). "
        "Do not include markdown, code fences, explanations, or any extra text. "
        "Ensure the output is valid JSON that can be parsed directly. "
        f"Role: {role}\n"
        f"Question: {question}\n"
        f"Candidate answer: {answer}"
    )


def build_session_summary_prompt(role: str, questions: list[str], answers: list[str], evaluations: list[dict]) -> str:
    """Build a summary prompt for a full interview session."""
    question_block = "\n".join(
        f"{idx + 1}. Q: {q}\n   A: {a}\n   Evaluation: {eval_item}" 
        for idx, (q, a, eval_item) in enumerate(zip(questions, answers, evaluations))
    )

    return (
        "You are producing a final hiring summary for a complete interview session. "
        "Use all question-answer pairs and their individual evaluations. "
        "Return valid JSON only with exactly these fields: "
        "overall_score (an integer from 0 to 10), "
        "overall_strengths (an array of short strings), "
        "overall_weaknesses (an array of short strings), "
        "hiring_recommendation (a concise string). "
        "Do not include markdown, code fences, explanations, or extra text. "
        "Ensure the output is valid JSON that can be parsed directly. "
        f"Role: {role}\n"
        f"Interview session:\n{question_block}"
    )
