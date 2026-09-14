"""Hermetic tests for merging the per-answer evaluation into the response."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from api.interview import _with_evaluation


def test_merges_evaluation_when_next_question_has_none():
    result = {"next_question": "Q4?", "evaluation": None, "status": "ACTIVE"}
    evaluation = {"score": 8, "level": "strong", "feedback": "Good"}
    merged = _with_evaluation(result, evaluation)
    assert merged["evaluation"] == evaluation
    assert merged["next_question"] == "Q4?"
    assert merged["status"] == "ACTIVE"


def test_does_not_overwrite_existing_evaluation():
    existing = {"score": 5}
    result = {"status": "READY_TO_FINISH", "evaluation": existing, "next_question": None}
    merged = _with_evaluation(result, {"score": 9})
    assert merged["evaluation"] == existing


def test_ignores_missing_evaluation():
    result = {"next_question": "Q2?", "evaluation": None}
    merged = _with_evaluation(result, None)
    assert merged["evaluation"] is None
