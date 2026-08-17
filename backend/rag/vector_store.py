"""
FAISS vector store utilities.
"""

import importlib.util
import json
from pathlib import Path

import faiss
import numpy as np


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
INDEX_FILE_NAME = rag_config.INDEX_FILE_NAME
METADATA_FILE_NAME = rag_config.METADATA_FILE_NAME
DocumentChunk = rag_models.DocumentChunk


class VectorStore:
    """Manage FAISS indexes."""

    def __init__(self):
        self.index = None
        self.metadata: list[DocumentChunk] = []

    def build(
        self,
        embeddings: np.ndarray,
        chunks: list[DocumentChunk],
    ) -> None:
        """
        Build a FAISS index.
        """

        if embeddings.size == 0:
            raise ValueError("No embeddings provided.")

        # vectors = np.asarray(embeddings, dtype="float32")

        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatIP(dimension)

        vectors = embeddings.astype(np.float32)

        self.index.add(vectors)

        self.metadata = chunks

    def save(self, directory: Path) -> None:
        """
        Save FAISS index and metadata.
        """

        directory.mkdir(parents=True, exist_ok=True)

        if self.index is not None:
            faiss.write_index(
                self.index,
                str(directory / INDEX_FILE_NAME),
            )
        else:
            index_path = directory / INDEX_FILE_NAME
            if index_path.exists():
                index_path.unlink()

        metadata = [
            {
                "content": chunk.content,
                "source": str(chunk.source),
                "role": chunk.role,
                "document_type": chunk.document_type,
                "chunk_id": chunk.chunk_id,
            }
            for chunk in self.metadata
        ]

        with open(
            directory / METADATA_FILE_NAME,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                metadata,
                file,
                ensure_ascii=False,
                indent=2,
            )

    def load(self, directory: Path) -> None:
        """
        Load an existing FAISS index.
        """

        index_path = directory / INDEX_FILE_NAME
        metadata_path = directory / METADATA_FILE_NAME

        if not index_path.exists() or not metadata_path.exists():
            self.index = None
            self.metadata = []
            return

        self.index = faiss.read_index(str(index_path))

        with open(metadata_path, encoding="utf-8") as file:
            data = json.load(file)

        self.metadata = [
            DocumentChunk(
                content=item["content"],
                source=Path(item["source"]),
                role=item["role"],
                document_type=item["document_type"],
                chunk_id=item["chunk_id"],
            )
            for item in data
        ]