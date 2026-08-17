from pathlib import Path

from cv.analyzer import CVAnalyzer
from cv.eligibility import InterviewEligibility
from rag.parser import DocumentParser

parser = DocumentParser()

document = parser.parse(
    file_path=Path("uploads/user_1/cv_v1.pdf"),
    role="user",
    document_type="cv",
)

analysis = CVAnalyzer().analyze(
    document.content
)

engine = InterviewEligibility()

result = engine.evaluate(
    analysis,
    "backend",
)

print()
print(result.message)
print()

print("Eligible:", result.eligible)
print("Score:", result.score)

print()
print("Recommendations")

for item in result.recommended_roles:

    print(
        f"{item.role:<15} {item.score:.2f}%"
    )