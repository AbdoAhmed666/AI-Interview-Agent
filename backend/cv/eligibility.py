"""
Interview eligibility utilities.
"""

from dataclasses import dataclass

from cv.role_recommender import RoleRecommender
from cv.models import RoleMatch

@dataclass(slots=True)
class EligibilityResult:
    """Eligibility decision for a selected role."""

    eligible: bool
    score: float
    selected_role: str
    recommended_roles: list[RoleMatch]
    message: str


class InterviewEligibility:
    """Decide whether a candidate should proceed with an interview."""

    MINIMUM_SCORE = 65.0

    def __init__(self):
        self.recommender = RoleRecommender()

    from cv.models import CVAnalysis

    def evaluate(
        self,
        analysis: CVAnalysis,
        selected_role: str,
    )-> EligibilityResult:

        recommendations = self.recommender.recommend(
            analysis
        )

        score = 0.0

        for item in recommendations:

            if item.role == selected_role:

                score = item.score

                break

        eligible = score >= self.MINIMUM_SCORE

        if eligible:

            message = (
                f"Your CV matches the {selected_role} role."
            )

        else:

            top_match = recommendations[0]

            top_role = top_match.role

            top_score = top_match.score

            message = (
                f"Your CV is not a strong match for "
                f"{selected_role}. "
                f"Consider applying for {top_role} "
                f"({top_score:.2f}%)."
            )

        return EligibilityResult(
            eligible=eligible,
            score=score,
            selected_role=selected_role,
            recommended_roles=recommendations,
            message=message,
        )