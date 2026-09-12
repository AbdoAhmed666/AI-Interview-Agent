import pytest
from pathlib import Path

if not Path("uploads/user_1").exists():
    pytest.skip(
        "legacy manual script: needs uncommitted local CV fixtures under "
        "uploads/user_1/. Hermetic coverage lives in test_role_coverage.py.",
        allow_module_level=True,
    )

from rag.parser import DocumentParser

from cv.analyzer import CVAnalyzer

parser = DocumentParser()


document = parser.parse(
    file_path=Path("uploads/user_1/cv_v1.pdf"),
    role="user",
    document_type="cv",
)

analysis = CVAnalyzer().analyze(
    document.content,
)

print()

print("Skills")
print(analysis.skills)

print()

print("Projects")
print(analysis.projects)

print()

print("Frameworks")
print(analysis.frameworks)

print()

print("Databases")
print(analysis.databases)

print()

print("AI Topics")
print(analysis.ai_topics)