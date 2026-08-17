"""
Role matching utilities.
"""

import importlib.util
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


def _load_module(module_name: str, module_path: Path):
    """Load a sibling module from a file path for consistent imports."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module {module_name} from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cv_models = _load_cv_models()
CVAnalysis = cv_models.CVAnalysis
RoleMatch = cv_models.RoleMatch

ROLE_PROFILES = _load_module(
    "backend_cv_role_profiles",
    Path(__file__).resolve().parent / "role_profiles.py",
).ROLE_PROFILES


class RoleMatcher:
    """Compare a CV against role requirements."""

    def match(
        self,
        analysis: CVAnalysis,
        role: str,
    ) -> RoleMatch:

        required = ROLE_PROFILES[role]

        candidate = set(
            skill.lower()
            for skill in analysis.skills
        )

        matched = sorted(
            required & candidate
        )

        missing = sorted(
            required - candidate
        )

        score = (
            len(matched)
            / len(required)
        ) * 100

        if score >= 80:
            recommendation = (
                "Strong match."
            )

        elif score >= 60:
            recommendation = (
                "Potential match."
            )

        else:
            recommendation = (
                "Weak match."
            )

        return RoleMatch(
            role=role,
            score=round(score, 2),
            matched_skills=matched,
            missing_skills=missing,
            recommendation=recommendation,
        )