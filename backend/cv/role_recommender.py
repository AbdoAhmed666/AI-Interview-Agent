"""
Recommend the best matching roles for a candidate.
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


cv_models = _load_cv_models()
CVAnalysis = cv_models.CVAnalysis
RoleMatch = cv_models.RoleMatch


def _load_module(module_name: str, module_path: Path):
    """Load a sibling module from a file path for consistent imports."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module {module_name} from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cv_dir = Path(__file__).resolve().parent
RoleMatcher = _load_module(
    "backend_cv_role_matcher",
    cv_dir / "role_matcher.py",
).RoleMatcher
ROLE_PROFILES = _load_module(
    "backend_cv_role_profiles",
    cv_dir / "role_profiles.py",
).ROLE_PROFILES


class RoleRecommender:
    """Evaluate all roles and rank them."""

    def __init__(self):
        self.matcher = RoleMatcher()

    def recommend(
        self,
        analysis: CVAnalysis,
    ) -> list[RoleMatch]:

        matches = []

        for role in ROLE_PROFILES:

            result = self.matcher.match(
                analysis,
                role,
            )

            matches.append(result)

        matches.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return matches