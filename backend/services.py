def calculate_overall_score(
    questions: list,
) -> float:

    scores = [
        q.score
        for q in questions
        if q.score is not None
    ]

    if not scores:
        return 0

    return round(
        sum(scores) / len(scores),
        2,
    )

def get_recommendation(
    score: float,
) -> str:

    if score >= 8:
        return "Strong Hire"

    if score >= 6:
        return "Hire"

    if score >= 4:
        return "Hold"

    return "Reject"