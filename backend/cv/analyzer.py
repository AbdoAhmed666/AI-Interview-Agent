"""
CV analysis utilities.
"""

import importlib.util
import re
from pathlib import Path


def _load_cv_models():
    """Load the CV models module from file for consistent imports."""
    models_path = Path(__file__).resolve().parent / "models.py"
    spec = importlib.util.spec_from_file_location("backend_cv_models", models_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load CV models from {models_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cv_models = _load_cv_models()
CVAnalysis = cv_models.CVAnalysis


class CVAnalyzer:
    """Extract structured information from a CV."""

    SKILL_ALIASES = {
        "python": [
            "python",
        ],
        "fastapi": [
            "fastapi",
        ],
        "flask": [
            "flask",
        ],
        "django": [
            "django",
        ],
        "docker": [
            "docker",
            "docker compose",
            "dockerfile",
        ],
        "jwt": [
            "jwt",
            "json web token",
        ],
        "postgresql": [
            "postgresql",
            "postgres",
        ],
        "mysql": [
            "mysql",
        ],
        "mongodb": [
            "mongodb",
            "mongo",
        ],
        "redis": [
            "redis",
        ],
        "sql": [
            "sql",
            "structured query language",
        ],
        "sqlalchemy": [
            "sqlalchemy",
            "sql alchemy",
        ],
        "alembic": [
            "alembic",
        ],
        "rest api": [
            "rest api",
            "rest apis",
            "restful api",
            "restful apis",
            "rest services",
        ],
        "git": [
            "git",
            "github",
            "gitlab",
        ],
        "react": [
            "react",
            "reactjs",
            "react.js",
        ],
        "next.js": [
            "next.js",
            "nextjs",
        ],
        "typescript": [
            "typescript",
            "ts",
        ],
        "javascript": [
            "javascript",
            "js",
        ],
        "tensorflow": [
            "tensorflow",
        ],
        "pytorch": [
            "pytorch",
        ],
        "cnn": [
            "cnn",
            "convolutional neural network",
        ],
        "lstm": [
            "lstm",
            "long short-term memory",
        ],
        "transformers": [
            "transformer",
            "transformers",
        ],
        "numpy": [
            "numpy",
        ],
        "pandas": [
            "pandas",
        ],
        "scikit-learn": [
            "scikit-learn",
            "sklearn",
        ],
        "machine learning": [
            "machine learning",
            "ml",
        ],
        "feature engineering": [
            "feature engineering",
        ],
        "statistics": [
            "statistics",
            "statistical analysis",
        ],
    }

    PROJECT_PATTERNS = [
        r"•\s+(.*?)\s+\|",
        r"-\s+(.*?)\s+\|",
        r"Project\s*:\s*(.*)",
    ]

    def analyze(
        self,
        text: str,
    ) -> CVAnalysis:

        analysis = CVAnalysis()

        lower = text.lower()

        # -----------------------------
        # Skills
        # -----------------------------
        for skill, aliases in self.SKILL_ALIASES.items():

            if any(
                alias in lower
                for alias in aliases
            ):
                analysis.skills.append(skill)

        analysis.skills = sorted(
            set(analysis.skills)
        )

        # -----------------------------
        # Frameworks
        # -----------------------------
        analysis.frameworks = [
            item
            for item in analysis.skills
            if item in {
                "fastapi",
                "flask",
                "django",
                "react",
                "next.js",
                "tensorflow",
                "pytorch",
                "sqlalchemy",
            }
        ]

        # -----------------------------
        # Databases
        # -----------------------------
        analysis.databases = [
            item
            for item in analysis.skills
            if item in {
                "postgresql",
                "mysql",
                "mongodb",
                "redis",
            }
        ]

        # -----------------------------
        # AI Topics
        # -----------------------------
        analysis.ai_topics = [
            item
            for item in analysis.skills
            if item in {
                "cnn",
                "lstm",
                "transformers",
                "tensorflow",
                "pytorch",
            }
        ]

        # -----------------------------
        # Tools
        # -----------------------------
        analysis.tools = [
            item
            for item in analysis.skills
            if item in {
                "docker",
                "git",
            }
        ]

        # -----------------------------
        # Technologies
        # -----------------------------
        analysis.technologies = sorted(
            set(
                analysis.frameworks
                + analysis.databases
                + analysis.ai_topics
                + analysis.tools
            )
        )

        # -----------------------------
        # Projects
        # -----------------------------
        projects = []

        for pattern in self.PROJECT_PATTERNS:

            projects.extend(
                re.findall(
                    pattern,
                    text,
                    re.IGNORECASE,
                )
            )

        analysis.projects = sorted(
            set(
                project.strip()
                for project in projects
                if project.strip()
            )
        )

        # -----------------------------
        # Experience
        # -----------------------------
        if re.search(
            r"experience",
            text,
            re.IGNORECASE,
        ):
            analysis.experience.append(
                "Experience section found"
            )

        return analysis