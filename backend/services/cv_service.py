"""
Business logic for CV management.
"""

import importlib.util
from pathlib import Path
from typing import Any


def _load_module(module_name: str, module_path: Path):
    """Load a sibling module from a file path for consistent imports."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module {module_name} from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


backend_dir = Path(__file__).resolve().parent.parent

CVStorage = _load_module(
    "backend_cv_storage",
    backend_dir / "cv" / "storage.py",
).CVStorage
CVAnalyzer = _load_module(
    "backend_cv_analyzer",
    backend_dir / "cv" / "analyzer.py",
).CVAnalyzer
RoleRecommender = _load_module(
    "backend_cv_role_recommender",
    backend_dir / "cv" / "role_recommender.py",
).RoleRecommender
DocumentParser = _load_module(
    "backend_document_parser",
    backend_dir / "rag" / "parser.py",
).DocumentParser
RAGService = _load_module(
    "backend_rag_service",
    backend_dir / "rag" / "rag_service.py",
).RAGService


class CVService:
    """High-level service for uploaded CVs."""

    def __init__(self):
        self.storage = CVStorage()
        self.parser = DocumentParser()
        self.analyzer = CVAnalyzer()
        self.recommender = RoleRecommender()
        self.rag = RAGService()
        import logging
        self.logger = logging.getLogger("cv.service")

    def _validate_pdf(self, uploaded_file: Path) -> None:
        """Ensure the uploaded file is a PDF."""
        if uploaded_file.suffix.lower() != ".pdf":
            raise ValueError("Only PDF files are supported.")

    def process_uploaded_cv(
        self,
        user_id: int,
        uploaded_file: Path,
    ) -> dict[str, Any]:
        """
        Store the uploaded CV, build its index,
        analyze it and recommend suitable roles.
        """
        self._validate_pdf(uploaded_file)

        saved_cv = self.storage.save_cv(
            user_id=user_id,
            cv_file=uploaded_file,
            activate=False,
        )

        self.logger.info("process_uploaded_cv user_id=%s saved_cv=%s", user_id, str(saved_cv))

        self.rag.build_user_cv_index(
            user_id=user_id,
            cv_path=saved_cv,
        )

        document = self.parser.parse(
            file_path=saved_cv,
            role="user",
            document_type="cv",
        )

        analysis = self.analyzer.analyze(
            document.content,
        )

        recommendations = self.recommender.recommend(
            analysis,
        )

        self.storage.set_active_cv(user_id, saved_cv.name)

        self.logger.info("process_uploaded_cv user_id=%s analysis_skills=%s recommendations=%s", user_id, getattr(analysis, 'skills', []), [r.role for r in recommendations])

        return {
            "cv_path": saved_cv,
            "analysis": analysis,
            "recommendations": recommendations,
        }

    def get_cv_summary(self, user_id: int) -> dict[str, Any]:
        """Return current CV status for the user."""
        active_file = self.storage.get_user_directory(user_id) / "active.json"

        if not active_file.exists():
            return {
                "active_cv": None,
                "versions": [],
            }

        active_cv_path = self.storage.get_active_cv(user_id)

        versions = [
            version.name
            for version in self.storage.list_versions(user_id)
        ]

        return {
            "active_cv": active_cv_path.name,
            "versions": versions,
        }

    def get_cv_analysis(self, user_id: int) -> dict[str, Any]:
        """Return analysis details for the active CV."""
        active_file = self.storage.get_user_directory(user_id) / "active.json"

        if not active_file.exists():
            return {
                "skills": [],
                "frameworks": [],
                "databases": [],
                "projects": [],
                "recommended_roles": [],
            }

        active_cv_path = self.storage.get_active_cv(user_id)
        document = self.parser.parse(
            file_path=active_cv_path,
            role="user",
            document_type="cv",
        )

        analysis = self.analyzer.analyze(document.content)
        recommendations = self.recommender.recommend(analysis)

        return {
            "skills": analysis.skills,
            "frameworks": analysis.frameworks,
            "databases": analysis.databases,
            "projects": analysis.projects,
            "recommended_roles": [
                recommendation.role
                for recommendation in recommendations
            ],
        }
