from rag.parser import DocumentParser

from cv.analyzer import CVAnalyzer

from pathlib import Path

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