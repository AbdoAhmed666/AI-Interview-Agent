"""
Utilities for building retrieval queries.
"""

from cv.models import CVAnalysis


class QueryBuilder:
    """Build semantic search queries."""

    def build(
        self,
        analysis: CVAnalysis,
        role: str,
        difficulty: str,
    ) -> str:

        skills = " ".join(
            analysis.skills[:8]
        )

        projects = " ".join(
            analysis.projects[:3]
        )

        return (
            f"{role} "
            f"{difficulty} "
            f"{skills} "
            f"{projects}"
        ) 