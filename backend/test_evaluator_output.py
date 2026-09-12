"""Hermetic tests for evaluator output handling (no DB, no network, no model)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import evaluator
from llm_provider import MockLLMProvider


def test_evaluate_answer_does_not_write_raw_output_to_stdout(capsys, monkeypatch):
    monkeypatch.setattr(evaluator, "get_provider", lambda: MockLLMProvider())
    result = evaluator.evaluate_answer("backend", "What is a closure?", "An answer")
    out = capsys.readouterr().out
    assert "RAW_EVALUATION_RESPONSE" not in out
    assert result.level is not None
    assert 0 <= result.score <= 10


def test_summarize_session_does_not_write_raw_output_to_stdout(capsys, monkeypatch):
    from schemas import SessionSummaryRequest

    monkeypatch.setattr(evaluator, "get_provider", lambda: MockLLMProvider())
    # save_interview_history writes a CSV; stub it so the test stays hermetic.
    monkeypatch.setattr(evaluator, "save_interview_history", lambda **kwargs: None)
    request = SessionSummaryRequest(
        role="backend",
        questions=["Q1"],
        answers=["A1"],
        evaluations=[{"score": 8}],
    )
    result = evaluator.summarize_session(request)
    out = capsys.readouterr().out
    assert "RAW_SESSION_SUMMARY_RESPONSE" not in out
    assert result.hiring_recommendation
