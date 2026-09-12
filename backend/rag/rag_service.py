"""
High-level RAG service.

This class orchestrates the complete RAG pipeline without exposing
low-level implementation details to the rest of the application.
"""

import importlib.util
import threading
from pathlib import Path


def _load_module(module_name: str, module_path: Path):
    """Load a sibling module from a file path for consistent imports."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module {module_name} from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rag_dir = Path(__file__).resolve().parent
TextChunker = _load_module("backend_rag_chunker", rag_dir / "chunker.py").TextChunker
EmbeddingGenerator = _load_module("backend_rag_embeddings", rag_dir / "embeddings.py").EmbeddingGenerator
DocumentLoader = _load_module("backend_rag_loader", rag_dir / "loader.py").DocumentLoader
DocumentParser = _load_module("backend_rag_parser", rag_dir / "parser.py").DocumentParser
Retriever = _load_module("backend_rag_retriever", rag_dir / "retriever.py").Retriever
VectorStore = _load_module("backend_rag_vector_store", rag_dir / "vector_store.py").VectorStore
rag_config = _load_module("backend_rag_config", rag_dir / "config.py")
KNOWLEDGE_BASE_DIR = rag_config.KNOWLEDGE_BASE_DIR
KNOWLEDGE_INDEX_DIR = rag_config.KNOWLEDGE_INDEX_DIR
INDEX_FILE_NAME = rag_config.INDEX_FILE_NAME


# Per-directory locks serialize index build/load on the same on-disk location
# (a user's CV dir, or a role's knowledge dir) so two concurrent requests never
# write the same faiss.index/metadata.json at once or read a half-written index.
# Different users/roles use different directories and proceed in parallel.
_DIR_LOCKS: dict[str, threading.Lock] = {}
_DIR_LOCKS_GUARD = threading.Lock()


def _directory_lock(directory: Path) -> threading.Lock:
    key = str(Path(directory).resolve())
    with _DIR_LOCKS_GUARD:
        lock = _DIR_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _DIR_LOCKS[key] = lock
        return lock

class RAGService:
    """High-level interface for RAG operations."""

    def __init__(self):
        self.loader = DocumentLoader()
        self.parser = DocumentParser()
        self.chunker = TextChunker()
        self.embedder = EmbeddingGenerator()
        self.knowledge_store = VectorStore()
        self.cv_store = VectorStore()

    def build_knowledge_base_index(
        self,
        role: str,
        output_directory: Path,
    ) -> None:
        """
        Build a FAISS index for a role knowledge base.
        """

        files = self.loader.load_role_documents(role)

        documents = [
            self.parser.parse(
                file_path=file,
                role=role,
                document_type="knowledge_base",
            )
            for file in files
        ]

        chunks = []

        for document in documents:
            chunks.extend(
                self.chunker.split(document)
            )

        embeddings = self.embedder.encode(chunks)

        if embeddings.size == 0:
            self.knowledge_store.metadata = chunks
            self.knowledge_store.index = None
            self.knowledge_store.save(output_directory)
            return

        self.knowledge_store.build(
            embeddings,
            chunks,
        )

        self.knowledge_store.save(output_directory)

    def build_user_cv_index(
        self,
        user_id: int,
        cv_path: Path,
    ) -> None:
        """
        Build a FAISS index for a user's uploaded CV.
        """

        user_directory = cv_path.parent


        cv_file = self.loader.load_user_cv(cv_path)

        document = self.parser.parse(
            file_path=cv_file,
            role="user",
            document_type="cv",
        )

        chunks = self.chunker.split(document)

        embeddings = self.embedder.encode(chunks)

        if embeddings.size == 0:
            self.cv_store.metadata = chunks
            self.cv_store.index = None
            self.cv_store.save(user_directory)
            return

        self.cv_store.build(
            embeddings,
            chunks,
        )

        self.cv_store.save(user_directory)

    def load_knowledge_index(
        self,
        directory: Path,
    ) -> None:
        """
        Load the knowledge base index.
        """

        self.knowledge_store.load(directory)

    def load_index(
        self,
        directory: Path,
    ) -> None:
        """
        Load a previously saved index from the given directory.
        """

        self.knowledge_store.load(directory)


    def load_cv_index(
        self,
        directory: Path,
    ) -> None:
        """
        Load a user's CV index.
        """

        self.cv_store.load(directory)

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
    ):
        """
        Retrieve relevant chunks.
        """

        embedding = self.embedder.encode_query(query)

        retriever = Retriever(self.knowledge_store)

        return retriever.retrieve(
            embedding,
            top_k=top_k,
        )
    def retrieve_hybrid(
        self,
        query: str,
        top_k: int = 4,
    ):
        """
        Retrieve results from both the knowledge base
        and the user's CV.
        """

        embedding = self.embedder.encode_query(query)

        knowledge_results = Retriever(
            self.knowledge_store,
        ).retrieve(
            embedding,
            top_k,
        )

        cv_results = Retriever(
            self.cv_store,
        ).retrieve(
            embedding,
            top_k,
        )

        results = knowledge_results + cv_results

        results.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return results

    def ensure_cv_index(
        self,
        user_id: int,
        cv_path: Path,
    ) -> None:
        """
        Build the user's CV index only once.
        """

        user_directory = cv_path.parent

        index_path = (
            user_directory
            / "faiss.index"
        )

        if index_path.exists():

            self.cv_store.load(
                user_directory
            )

            return

        self.build_user_cv_index(
            user_id=user_id,
            cv_path=cv_path,
        )

        self.cv_store.load(
            user_directory
        )

    def ensure_knowledge_index(
        self,
        role: str,
    ) -> None:
        """
        Build or load the knowledge base index.
        """

        index_directory = KNOWLEDGE_INDEX_DIR / role

        index_file = (
            index_directory
            / "faiss.index"
        )

        if index_file.exists():
            try:
                self.knowledge_store.load(
                    index_directory
                )
                return
            except Exception:
                pass

        self.build_knowledge_base_index(
            role,
            index_directory,
        )

        self.knowledge_store.load(
            index_directory
        )

    # ------------------------------------------------------------------
    # Isolated (per-request) retrieval
    #
    # The methods above keep index state on ``self.knowledge_store`` /
    # ``self.cv_store``. Because a single ``RAGService`` instance is shared
    # process-wide, reading that mutable state on a concurrent request path
    # can leak one user's CV into another user's interview. The methods below
    # never touch shared store state: they return fresh, call-local
    # ``VectorStore`` instances, so concurrent callers are fully isolated.
    # ------------------------------------------------------------------

    @staticmethod
    def _load_store(directory: Path) -> "VectorStore":
        """Return a fresh VectorStore loaded from ``directory`` (empty if none)."""
        store = VectorStore()
        store.load(directory)
        return store

    def ensure_cv_store(self, user_id: int, cv_path: Path) -> "VectorStore":
        """Build the user's CV index if missing and return an isolated store.

        The build+load critical section is serialized per user directory so
        concurrent requests never corrupt or half-read the same index files.
        """
        user_directory = cv_path.parent
        index_path = user_directory / INDEX_FILE_NAME
        with _directory_lock(user_directory):
            if not index_path.exists():
                self.build_user_cv_index(user_id=user_id, cv_path=cv_path)
            return self._load_store(user_directory)

    def ensure_knowledge_store(self, role: str) -> "VectorStore":
        """Build the role knowledge index if missing and return an isolated store."""
        index_directory = KNOWLEDGE_INDEX_DIR / role
        index_file = index_directory / INDEX_FILE_NAME
        with _directory_lock(index_directory):
            if index_file.exists():
                try:
                    return self._load_store(index_directory)
                except Exception:
                    pass
            self.build_knowledge_base_index(role, index_directory)
            return self._load_store(index_directory)

    def retrieve_hybrid_isolated(
        self,
        query: str,
        cv_store: "VectorStore",
        knowledge_store: "VectorStore",
        top_k: int = 4,
    ):
        """Retrieve from caller-provided stores only (no shared state)."""
        embedding = self.embedder.encode_query(query)
        knowledge_results = Retriever(knowledge_store).retrieve(embedding, top_k)
        cv_results = Retriever(cv_store).retrieve(embedding, top_k)
        results = knowledge_results + cv_results
        results.sort(key=lambda item: item.score, reverse=True)
        return results
