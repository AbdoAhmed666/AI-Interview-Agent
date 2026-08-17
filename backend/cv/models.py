"""
Models used by the CV Analyzer.
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class CVAnalysis:
    """Structured information extracted from a CV."""

    skills: list[str] = field(default_factory=list)

    projects: list[str] = field(default_factory=list)

    technologies: list[str] = field(default_factory=list)

    frameworks: list[str] = field(default_factory=list)

    databases: list[str] = field(default_factory=list)

    ai_topics: list[str] = field(default_factory=list)

    cloud: list[str] = field(default_factory=list)

    tools: list[str] = field(default_factory=list)

    education: list[str] = field(default_factory=list)

    experience: list[str] = field(default_factory=list)

@dataclass(slots=True)
class RoleMatch:
    """Represents the CV matching result for a role."""

    role: str

    score: float

    matched_skills: list[str]

    missing_skills: list[str]

    recommendation: str