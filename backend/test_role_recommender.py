from pathlib import Path

from rag.parser import DocumentParser

from cv.analyzer import CVAnalyzer
from cv.role_recommender import RoleRecommender

document = DocumentParser().parse(
    file_path=Path("uploads/user_1/cv_v1.pdf"),
    role="user",
    document_type="cv",
)

analysis = CVAnalyzer().analyze(
    document.content,
)

results = RoleRecommender().recommend(
    analysis,
)

print()

for result in results:

    print(
        f"{result.role:15}"
        f"{result.score:6.2f}%"
    )