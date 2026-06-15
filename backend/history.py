"""Simple CSV history persistence for completed interview sessions."""

import csv
from datetime import datetime
from pathlib import Path


HISTORY_COLUMNS = ["timestamp", "role", "overall_score", "hiring_recommendation"]


def save_interview_history(role: str, overall_score: int, hiring_recommendation: str, timestamp: str | None = None) -> Path:
    """Append a completed interview summary to the local history CSV file."""
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    history_file = data_dir / "history.csv"
    file_exists = history_file.exists()

    with history_file.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if not file_exists:
            writer.writerow(HISTORY_COLUMNS)
        writer.writerow([
            timestamp or datetime.now().isoformat(timespec="seconds"),
            role,
            overall_score,
            hiring_recommendation,
        ])

    return history_file
