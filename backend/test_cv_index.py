from pathlib import Path

from rag.rag_service import RAGService

service = RAGService()

cv_path = Path("uploads/user_1/cv.pdf")

service.build_user_cv_index(
    user_id=1,
    cv_path=cv_path,
)

print("CV index created successfully.")



service.load_knowledge_index(
    Path("backend_index")
)

service.load_cv_index(
    Path("uploads/user_1")
)

results = service.retrieve_hybrid(
    "What technologies does the candidate know?"
)


print()

for result in results:
    print("=" * 50)
    print(f"Score : {result.score:.4f}")
    print(f"Source: {result.chunk.source.name}")
    print(f"Role  : {result.chunk.role}")
    print()
    print(result.chunk.content[:250])