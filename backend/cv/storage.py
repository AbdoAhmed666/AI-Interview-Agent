"""
CV storage utilities.

Responsible for storing and retrieving user CVs.
"""

from pathlib import Path
import json
import shutil
import logging

import importlib.util


def _load_rag_config():
    """Load the RAG config module from file to support package-relative imports."""
    config_path = Path(__file__).resolve().parent.parent / "rag" / "config.py"
    spec = importlib.util.spec_from_file_location("backend_rag_config", config_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load RAG config from {config_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rag_config = _load_rag_config()
UPLOADS_DIR = rag_config.UPLOADS_DIR


ACTIVE_FILE = "active.json"


class CVStorage:
    """Manage uploaded CV files."""

    def __init__(self):
        self.uploads_dir = UPLOADS_DIR
        self.logger = logging.getLogger("cv.storage")

    def get_user_directory(
        self,
        user_id: int,
    ) -> Path:
        """
        Return the user's upload directory.
        """

        directory = self.uploads_dir / f"user_{user_id}"

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.logger.debug("get_user_directory user_id=%s -> %s", user_id, str(directory))
        return directory

    def save_cv(
        self,
        user_id: int,
        cv_file: Path,
        activate: bool = True,
    ) -> Path:
        """
        Save a new CV version.
        """

        user_dir = self.get_user_directory(
            user_id
        )

        versions = sorted(
            user_dir.glob("cv_v*.pdf")
        )

        version = len(versions) + 1

        destination = (
            user_dir /
            f"cv_v{version}.pdf"
        )

        shutil.copy2(
            cv_file,
            destination,
        )

        if activate:
            self.set_active_cv(
                user_id,
                destination.name,
            )

        self.logger.info("save_cv user_id=%s saved=%s", user_id, str(destination))

        return destination

    def set_active_cv(
        self,
        user_id: int,
        filename: str,
    ) -> None:
        """
        Update active CV.
        """

        user_dir = self.get_user_directory(
            user_id
        )

        with open(
            user_dir / ACTIVE_FILE,
            "w",
            encoding="utf-8",
        ) as file:

            data = {"active_cv": filename}

            json.dump(
                data,
                file,
                indent=2,
            )

        self.logger.info("set_active_cv user_id=%s active=%s file=%s", user_id, filename, str(user_dir / ACTIVE_FILE))

    def get_active_cv(
        self,
        user_id: int,
    ) -> Path:
        """
        Return the active CV path.
        """

        user_dir = self.get_user_directory(
            user_id
        )

        with open(
            user_dir / ACTIVE_FILE,
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        active = user_dir / data["active_cv"]
        self.logger.debug("get_active_cv user_id=%s -> %s", user_id, str(active))

        return active

    def list_versions(
        self,
        user_id: int,
    ) -> list[Path]:
        """
        List all uploaded CV versions.
        """

        user_dir = self.get_user_directory(
            user_id
        )

        return sorted(
            user_dir.glob("cv_v*.pdf")
        )
    def has_cv(
        self,
        user_id: int,
    ) -> bool:
        """
        Check whether the user has an active CV.
        """

        try:
            return self.get_active_cv(user_id).exists()
        except Exception:
            self.logger.debug("has_cv: active file missing for user_id=%s", user_id)
            return False
