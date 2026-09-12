"""Role-coverage tests: every supported role must be reachable end to end.

Hermetic — no DB, no network, no embedding model. Exercises skill detection,
eligibility scoring, and knowledge-base discovery as pure Python.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cv.analyzer import CVAnalyzer
from cv.eligibility import InterviewEligibility
from cv.role_profiles import ROLE_PROFILES
from rag.loader import DocumentLoader

FRONTEND_CV = (
    "Frontend developer skilled in React, Next.js, TypeScript, JavaScript, "
    "HTML5, CSS3, Tailwind CSS, Redux, and Git."
)
DATA_SCIENCE_CV = (
    "Data scientist experienced with Python, NumPy, Pandas, statistics, "
    "feature engineering, machine learning, SQL, and Matplotlib."
)
BACKEND_CV = (
    "Backend engineer using Python, FastAPI, PostgreSQL, SQL, SQLAlchemy, "
    "Alembic, Docker, JWT, Redis, REST APIs, and Git."
)
ML_CV = (
    "Machine learning engineer using Python, TensorFlow, PyTorch, CNN, LSTM, "
    "transformers, NumPy, Pandas, and scikit-learn."
)


def _analyze(text):
    return CVAnalyzer().analyze(text)


def test_every_role_profile_skill_is_detectable():
    """No role can require a skill the analyzer can never detect."""
    required = set().union(*ROLE_PROFILES.values())
    aliases = set(CVAnalyzer.SKILL_ALIASES.keys())
    undetectable = required - aliases
    assert not undetectable, f"undetectable required skills: {sorted(undetectable)}"


def test_all_supported_roles_are_eligible_for_a_matching_cv():
    eligibility = InterviewEligibility()
    cases = {
        "backend": BACKEND_CV,
        "frontend": FRONTEND_CV,
        "ml": ML_CV,
        "data_science": DATA_SCIENCE_CV,
    }
    for role, cv_text in cases.items():
        result = eligibility.evaluate(_analyze(cv_text), role)
        assert result.eligible, (
            f"{role} should be eligible but scored {result.score:.1f}%"
        )


def test_word_boundary_matching_avoids_phantom_skills():
    """Short aliases must not match inside unrelated words."""
    analysis = _analyze("A legitimate consultant delivering strong results.")
    assert "git" not in analysis.skills          # 'git' inside 'legitimate'
    assert "typescript" not in analysis.skills   # 'ts' inside 'results'
    assert "machine learning" not in analysis.skills  # 'ml' inside 'html'/prose
    assert "html" not in analysis.skills


def test_html_does_not_imply_machine_learning():
    analysis = _analyze("Built accessible HTML and CSS layouts.")
    assert "html" in analysis.skills
    assert "css" in analysis.skills
    assert "machine learning" not in analysis.skills


def test_missing_knowledge_base_role_is_graceful():
    """An unknown role returns no documents instead of raising (no 500)."""
    assert DocumentLoader().load_role_documents("no_such_role") == []


def test_supported_roles_have_knowledge_base_docs():
    loader = DocumentLoader()
    for role in ("backend", "frontend", "ml", "data_science"):
        docs = loader.load_role_documents(role)
        assert docs, f"role '{role}' has no knowledge-base documents"
