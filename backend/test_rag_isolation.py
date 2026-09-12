"""Concurrency isolation tests for the RAG retrieval hot path.

These prove that ``RAGService.ensure_cv_store`` / ``retrieve_hybrid_isolated``
never share mutable index state between concurrent callers, so one user's CV
can never leak into another user's interview. They are fully hermetic: no
PostgreSQL, no network, and no embedding-model download (a stub query encoder
and hand-built FAISS indexes are used instead).
"""
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rag.rag_service import RAGService
from rag.models import DocumentChunk
from rag.vector_store import VectorStore

DIM = 8
N_USERS = 8
ROUNDS = 40


def _fixed_vector() -> np.ndarray:
    vec = np.ones(DIM, dtype=np.float32)
    return vec / np.linalg.norm(vec)


def _service_without_model() -> RAGService:
    """A RAGService whose embedder is stubbed so no model is ever loaded."""
    service = RAGService.__new__(RAGService)
    service.embedder = SimpleNamespace(encode_query=lambda query: _fixed_vector())
    return service


def _build_cv_index(directory: Path, content: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    chunk = DocumentChunk(
        content=content,
        source=directory / "cv_v1.pdf",
        role="user",
        document_type="cv",
        chunk_id=0,
    )
    store = VectorStore()
    store.build(_fixed_vector().reshape(1, DIM), [chunk])
    store.save(directory)


def _knowledge_store() -> VectorStore:
    chunk = DocumentChunk(
        content="SHARED-KNOWLEDGE",
        source=Path("kb/backend.md"),
        role="knowledge",
        document_type="knowledge_base",
        chunk_id=0,
    )
    store = VectorStore()
    store.build(_fixed_vector().reshape(1, DIM), [chunk])
    return store


def test_ensure_cv_store_returns_isolated_instances(tmp_path):
    """Two calls must never hand back the same (shared) store object."""
    service = _service_without_model()
    _build_cv_index(tmp_path / "user_1", "USER-1-CV")
    first = service.ensure_cv_store(1, tmp_path / "user_1" / "cv_v1.pdf")
    second = service.ensure_cv_store(1, tmp_path / "user_1" / "cv_v1.pdf")
    assert first is not second
    assert first.metadata[0].content == "USER-1-CV"
    assert second.metadata[0].content == "USER-1-CV"


def test_concurrent_users_never_cross_contaminate(tmp_path):
    """Hammer the hot path from many threads; each user only sees their own CV."""
    service = _service_without_model()
    knowledge = _knowledge_store()

    cv_paths = {}
    for user_id in range(1, N_USERS + 1):
        user_dir = tmp_path / f"user_{user_id}"
        _build_cv_index(user_dir, f"USER-{user_id}-CV")
        cv_paths[user_id] = user_dir / "cv_v1.pdf"

    errors: list[str] = []
    barrier = threading.Barrier(N_USERS)

    def worker(user_id: int) -> None:
        expected = f"USER-{user_id}-CV"
        barrier.wait()  # maximize interleaving of the retrieval hot path
        for _ in range(ROUNDS):
            cv_store = service.ensure_cv_store(user_id, cv_paths[user_id])
            results = service.retrieve_hybrid_isolated(
                "any query", cv_store=cv_store, knowledge_store=knowledge
            )
            cv_hits = [r.chunk.content for r in results if r.chunk.role == "user"]
            if cv_hits != [expected]:
                errors.append(f"user {user_id} saw {cv_hits}, expected [{expected}]")
            # knowledge must always be present and shared
            if not any(r.chunk.role == "knowledge" for r in results):
                errors.append(f"user {user_id} lost knowledge context")

    threads = [threading.Thread(target=worker, args=(uid,)) for uid in cv_paths]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors, errors[:10]
