from rag.loader import DocumentLoader
from rag.parser import DocumentParser
from rag.chunker import TextChunker

loader = DocumentLoader()
parser = DocumentParser()
chunker = TextChunker()

files = loader.load_role_documents("backend")

print(f"Found {len(files)} files")

for file in files:

    document = parser.parse(
        file_path=file,
        role="backend",
        document_type="knowledge_base",
    )

    chunks = chunker.split(document)

    print("=" * 50)
    print(file.name)
    print(f"Chunks: {len(chunks)}")

    for chunk in chunks:

        print(chunk.chunk_id)

        print(chunk.content[:80])

        print()