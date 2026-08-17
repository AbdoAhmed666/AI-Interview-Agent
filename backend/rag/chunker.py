"""
Text chunking utilities.

This module is responsible for splitting parsed documents into
smaller overlapping chunks while preserving document metadata.
"""

import importlib.util
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter


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
rag_models = _load_module("backend_rag_models", rag_dir / "models.py")
CHUNK_OVERLAP = rag_config.CHUNK_OVERLAP
CHUNK_SIZE = rag_config.CHUNK_SIZE
Document = rag_models.Document
DocumentChunk = rag_models.DocumentChunk


class TextChunker:
    """Split parsed documents into chunks."""

    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )

    def split(self, document: Document) -> list[DocumentChunk]:
        """
        Split a parsed document into chunks.

        Args:
            document: Parsed document.

        Returns:
            List of DocumentChunk objects.
        """

        if not document.content.strip():
            return []

        chunks = self.splitter.split_text(document.content)

        return [
            DocumentChunk(
                content=chunk,
                source=document.source,
                role=document.role,
                document_type=document.document_type,
                chunk_id=index,
            )
            for index, chunk in enumerate(chunks)
        ]