import pytest
from pathlib import Path

try:
    from rag.embeddings import EmbeddingGenerator

    EmbeddingGenerator()
except Exception as exc:  # pragma: no cover - environment dependent
    pytest.skip(
        f"legacy integration script: requires the embedding model "
        f"(unavailable offline): {exc}",
        allow_module_level=True,
    )

from rag.rag_service import RAGService

service = RAGService()

index_dir = Path("backend_index")

service.build_knowledge_base_index(
    role="backend",
    output_directory=index_dir,
)

print("Knowledge Base Index Built")

service.load_index(index_dir)

print("Index Loaded")

results = service.retrieve(
    "Explain FastAPI dependency injection."
)

print()

for result in results:
    print("=" * 50)
    print(result.chunk.source.name)
    print(result.chunk.content[:200])
