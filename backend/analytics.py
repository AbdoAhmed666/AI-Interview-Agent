"""Helpers for reading interview history from the local CSV file."""

from pathlib import Path

import pandas as pd

HISTORY_FILE = Path(__file__).resolve().parent.parent / "data" / "history.csv"


def load_history_dataframe() -> pd.DataFrame:
    """Load interview history from the CSV file, returning an empty DataFrame if unavailable."""
    if not HISTORY_FILE.exists() or HISTORY_FILE.stat().st_size == 0:
        return pd.DataFrame(columns=["timestamp", "role", "overall_score", "hiring_recommendation"])

    dataframe = pd.read_csv(HISTORY_FILE)
    if "overall_score" in dataframe:
        dataframe["overall_score"] = pd.to_numeric(dataframe["overall_score"], errors="coerce")
    return dataframe


def get_history_metrics(dataframe: pd.DataFrame) -> dict[str, float | int]:
    """Return summary metrics for the provided interview history."""
    valid_scores = dataframe["overall_score"].dropna()
    if valid_scores.empty:
        return {"total_interviews": 0, "average_score": 0, "highest_score": 0, "lowest_score": 0}

    return {
        "total_interviews": int(len(dataframe)),
        "average_score": float(valid_scores.mean()),
        "highest_score": int(valid_scores.max()),
        "lowest_score": int(valid_scores.min()),
    }
