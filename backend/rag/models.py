from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Document:
    """Represents a parsed document."""

    content: str
    source: Path
    role: str
    document_type: str


@dataclass(slots=True)
class DocumentChunk:
    """Represents a chunk ready for embedding."""

    content: str
    source: Path
    role: str
    document_type: str
    chunk_id: int

@dataclass(slots=True)
class RetrievalResult:
    """Represents a retrieved chunk with its similarity score."""

    chunk: DocumentChunk
    score: float