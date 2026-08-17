from pathlib import Path

from rag.loader import DocumentLoader
from rag.parser import DocumentParser
from rag.chunker import TextChunker
from rag.embeddings import EmbeddingGenerator
from rag.vector_store import VectorStore
from rag.retriever import Retriever

print("=" * 60)
print("RAG Integration Test")
print("=" * 60)

loader = DocumentLoader()
parser = DocumentParser()
chunker = TextChunker()
embedder = EmbeddingGenerator()
store = VectorStore()

# -----------------------
# Load Documents
# -----------------------

files = loader.load_role_documents("backend")

print(f"\nLoaded Files: {len(files)}")

documents = []

for file in files:
    document = parser.parse(
        file_path=file,
        role="backend",
        document_type="knowledge_base",
    )

    documents.append(document)

# -----------------------
# Chunking
# -----------------------

chunks = []

for document in documents:
    chunks.extend(chunker.split(document))

print(f"Chunks: {len(chunks)}")

# -----------------------
# Embeddings
# -----------------------

embeddings = embedder.encode(chunks)

print(f"Embedding Shape: {embeddings.shape}")

# -----------------------
# Build FAISS
# -----------------------

store.build(
    embeddings,
    chunks,
)

print("FAISS Index Built")

# -----------------------
# Save
# -----------------------

output_dir = Path("test_index")

store.save(output_dir)

print("Index Saved")

# -----------------------
# Load Again
# -----------------------

loaded_store = VectorStore()

loaded_store.load(output_dir)

print("Index Loaded")

# -----------------------
# Query
# -----------------------

query = "Explain dependency injection in FastAPI."

query_embedding = embedder.model.encode(
    [query],
    convert_to_numpy=True,
    normalize_embeddings=True,
)[0]

retriever = Retriever(loaded_store)

results = retriever.retrieve(query_embedding)

print("\nRetrieved Results")
print("-" * 60)

for index, result in enumerate(results, start=1):
    print(f"\nResult {index}")
    print(f"File: {result.chunk.source.name}")
    print(f"Chunk ID: {result.chunk.chunk_id}")
    print(result.chunk.content[:200])
