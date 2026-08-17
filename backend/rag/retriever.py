"""
Similarity retrieval utilities.
"""

import importlib.util
from pathlib import Path

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
rag_models = _load_module("backend_rag_models", rag_dir / "models.py")
rag_vector_store = _load_module("backend_rag_vector_store", rag_dir / "vector_store.py")
DocumentChunk = rag_models.DocumentChunk
VectorStore = rag_vector_store.VectorStore
RetrievalResult = rag_models.RetrievalResult

class Retriever:
    """Retrieve the most relevant chunks."""

    def __init__(self, store: VectorStore):
        self.store = store

    def retrieve(
        self,
        query_embedding: np.ndarray,
        top_k: int = 4,
    ) -> list[DocumentChunk]:
        """
        Retrieve top-k similar chunks.
        """

        if self.store.index is None:
            return [
                RetrievalResult(chunk=chunk, score=0.0)
                for chunk in self.store.metadata[:top_k]
            ]

        distances, indices = self.store.index.search(
            query_embedding.reshape(1, -1),
            top_k,
        )

        results: list[RetrievalResult] = []

        for score, index in zip(
            distances[0],
            indices[0],
        ):

            if index == -1:
                continue

            results.append(
                RetrievalResult(
                    chunk=self.store.metadata[index],
                    score=float(score),
                )
            )

        return results