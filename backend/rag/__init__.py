class EmbeddingGenerator:
    """Generate embeddings for document chunks."""

    def __init__(self):
        global _MODEL

        if _MODEL is None:
            _MODEL = SentenceTransformer(EMBEDDING_MODEL)

        self.model = _MODEL