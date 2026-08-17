"""
Embedding utilities for the RAG pipeline.
"""
import importlib.util
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


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
EMBEDDING_MODEL = rag_config.EMBEDDING_MODEL
DocumentChunk = rag_models.DocumentChunk

_MODEL = None
class EmbeddingGenerator:
    """Generate embeddings for document chunks."""

    def __init__(self):
        global _MODEL

        if _MODEL is None:
            _MODEL = SentenceTransformer(EMBEDDING_MODEL)

        self.model = _MODEL

    def encode(self, chunks: list[DocumentChunk]) -> np.ndarray:
        """
        Convert document chunks into embedding vectors.
        """

        if not chunks:
            return np.empty((0, 0), dtype=np.float32)

        texts = [chunk.content for chunk in chunks]

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return embeddings


    def encode_query(
        self,
        query: str,
    ) -> np.ndarray:
        """
        Generate an embedding for a search query.
        """

        return self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )[0]
