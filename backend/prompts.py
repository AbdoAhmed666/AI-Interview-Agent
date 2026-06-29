"""Prompt templates for the AI Interview Agent backend.

This module keeps prompt engineering separate from business logic.
"""


def build_interview_question_prompt(
    role: str,
    difficulty: int = 3,
    interview_type: str = "technical",
) -> str:
    """Generate one medium difficulty question."""
    return (
        f"You are a senior technical interviewer. "
        f"Generate ONE {interview_type} interview question for role '{role}'. "
        f"Difficulty level is {difficulty}/5 where: "
        "1 = beginner, "
        "2 = junior, "
        "3 = intermediate, "
        "4 = advanced, "
        "5 = expert level. "
        "Return ONLY the question text. "
        "No markdown. No explanation."
    )


def build_evaluation_prompt(
            role: str,
            question: str,
            answer: str,
            difficulty: int
    ) -> str:

    return (

        "You are a senior FAANG technical interviewer. "

        f"The question difficulty level is {difficulty}/5 where "

        "1 = beginner, 5 = expert. "

        "Score the candidate RELATIVE to this difficulty level. "

        "Harder questions require deeper answers. "

        "Evaluate based on: technical depth, correctness, architecture understanding, scalability, edge cases, explanation quality. "

        "Return VALID JSON ONLY with EXACTLY these fields: "

        "score (integer 0-10), "

        "level (weak or medium or strong), "

        "strengths (array), "

        "weaknesses (array), "

        "feedback (string), "

        "concept_gaps (array), "

        "follow_up_question (string). "

        "NO markdown. NO extra text. "

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
        "You are acting as a senior recruiter making final hiring decision. "
        
        "Analyze the entire interview session deeply. "

        "Consider: "

        "scores, "

        "candidate technical level progression, "

        "concept gaps, "

        "weakness patterns, "

        "learning ability, "

        "communication quality. "

        "Return valid JSON only with exactly these fields: "

        "overall_score (integer 0-10), "

        "overall_strengths (array), "

        "overall_weaknesses (array), "

        "hiring_recommendation (one of: Hire, Reject, Consider). "

        f"Role: {role}\n"
        f"Interview session:\n{question_block}"
    )
