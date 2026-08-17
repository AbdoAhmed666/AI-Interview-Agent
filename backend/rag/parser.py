"""
Document parsing utilities.

Responsible for extracting raw text from supported document types.
"""

import importlib.util
import logging
from pathlib import Path

from pypdf import PdfReader


def _load_rag_models():
    """Load the RAG models module from file for consistent imports."""
    models_path = Path(__file__).resolve().parent / "models.py"
    spec = importlib.util.spec_from_file_location("backend_rag_models", models_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load RAG models from {models_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rag_models = _load_rag_models()
Document = rag_models.Document

logger = logging.getLogger(__name__)


class DocumentParser:
    """Extract raw text from documents."""

    def parse(
        self,
        file_path: Path,
        role: str,
        document_type: str,
    ) -> Document:
        """Extract text based on file extension."""

        extension = file_path.suffix.lower()

        if extension == ".pdf":
            return self._parse_pdf(
                file_path,
                role,
                document_type,
            )

        if extension in {".md", ".txt"}:
            text = file_path.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            return Document(
                content=text,
                source=file_path,
                role=role,
                document_type=document_type,
            )

        raise ValueError(f"Unsupported file type: {extension}")

    def _parse_pdf(
        self,
        file_path: Path,
        role: str,
        document_type: str,
    ) -> Document:
        """Extract text from PDF."""

        reader = PdfReader(file_path)

        pages = []

        for page in reader.pages:
            pages.append(page.extract_text() or "")

        text = "\n".join(pages)

        logger.info(
            "Parsed PDF '%s' (%d characters).",
            file_path.name,
            len(text),
        )

        return Document(
            content=text,
            source=file_path,
            role=role,
            document_type=document_type,
        )