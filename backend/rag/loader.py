"""Utilities for loading documents for the RAG pipeline.

This module is responsible only for discovering and validating supported files.
It does not parse file contents.
"""

import importlib.util
import logging
from pathlib import Path


def _load_module(module_name: str, module_path: Path):
    """Load a sibling module from a file path for consistent imports."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module {module_name} from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rag_dir = Path(__file__).resolve().parent
rag_config = _load_module("backend_rag_config", rag_dir / "config.py")
KNOWLEDGE_BASE_DIR = rag_config.KNOWLEDGE_BASE_DIR
SUPPORTED_EXTENSIONS = rag_config.SUPPORTED_EXTENSIONS

logger = logging.getLogger(__name__)


class DocumentLoader:
    """Loads supported documents from the knowledge base."""

    def __init__(self, knowledge_base_dir: Path = KNOWLEDGE_BASE_DIR):
        self.knowledge_base_dir = knowledge_base_dir

    def load_role_documents(self, role: str) -> list[Path]:
        """Return all supported documents for a given role."""

        role_dir = self.knowledge_base_dir / role

        if not role_dir.exists():
            raise FileNotFoundError(
                f"Knowledge base directory not found: {role_dir}"
            )

        documents: list[Path] = []

        for file_path in role_dir.rglob("*"):
            if (
                file_path.is_file()
                and file_path.suffix.lower() in SUPPORTED_EXTENSIONS
            ):
                documents.append(file_path)

        logger.info(
            "Loaded %d documents for role '%s'.",
            len(documents),
            role,
        )

        return sorted(documents)

    def load_user_documents(self, user_dir: Path) -> list[Path]:
        """Return all supported uploaded documents for a user."""

        if not user_dir.exists():
            raise FileNotFoundError(
                f"User upload directory not found: {user_dir}"
            )

        documents: list[Path] = []

        for file_path in user_dir.rglob("*"):
            if (
                file_path.is_file()
                and file_path.suffix.lower() in SUPPORTED_EXTENSIONS
            ):
                documents.append(file_path)

        logger.info(
            "Loaded %d user documents.",
            len(documents),
        )

        return sorted(documents)

    def load_user_cv(
        self,
        cv_path: Path,
    ) -> Path:
        """
        Validate and return the uploaded CV path.
        """

        if not cv_path.exists():
            raise FileNotFoundError(
                f"CV not found: {cv_path}"
            )

        return cv_path
