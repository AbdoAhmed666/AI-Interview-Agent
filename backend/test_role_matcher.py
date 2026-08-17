from pathlib import Path

from rag.parser import DocumentParser

from cv.analyzer import CVAnalyzer
from cv.role_matcher import RoleMatcher

parser = DocumentParser()

document = parser.parse(
    file_path=Path("uploads/user_1/cv_v1.pdf"),
    role="user",
    document_type="cv",
)

analysis = CVAnalyzer().analyze(
    document.content,
)

matcher = RoleMatcher()

result = matcher.match(
    analysis,
    "backend",
)

print()

print("Role:", result.role)

print("Score:", result.score)

print()

print("Matched Skills")

for skill in result.matched_skills:
    print("-", skill)

print()

print("Missing Skills")

for skill in result.missing_skills:
    print("-", skill)

print()

print(result.recommendation)