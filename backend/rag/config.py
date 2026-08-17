"""Configuration for the RAG module.

This file centralizes all configurable values used by the RAG pipeline.
Keeping them in one place avoids hardcoded values across the project.
"""

from pathlib import Path

from config import RUNTIME_DIR

# ==========================
# Base Directories
# ==========================

RAG_DIR = Path(__file__).resolve().parent

BASE_DIR = Path(__file__).resolve().parent.parent

BACKEND_DIR = RAG_DIR.parent

KNOWLEDGE_BASE_DIR = BACKEND_DIR / "knowledge_base"

UPLOADS_DIR = RUNTIME_DIR / "uploads"
KNOWLEDGE_INDEX_DIR = RUNTIME_DIR / "knowledge_indexes"

# ==========================
# Supported File Types
# ==========================

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".md",
    ".txt",
}

# ==========================
# Chunking
# ==========================

CHUNK_SIZE = 500

CHUNK_OVERLAP = 100

# ==========================
# Retrieval
# ==========================

TOP_K = 4

# ==========================
# Embedding Model
# ==========================

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

# ==========================
# Vector Store
# ==========================

INDEX_FILE_NAME = "faiss.index"

METADATA_FILE_NAME = "metadata.json"

# ==========================
# SIMILARITY_SCORE
# ==========================
MIN_SIMILARITY_SCORE = 0.45

