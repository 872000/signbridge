"""SQLite progress tracking: per-letter attempts, accuracy, mastery."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DEFAULT_DB = Path.home() / ".signbridge" / "progress.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    letter TEXT NOT NULL,
    correct INTEGER NOT NULL CHECK (correct IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def mastery_level(attempts: int, accuracy: float) -> str:
    """Map attempt count + accuracy to a mastery label.

    - Learning:   fewer than 5 attempts, or accuracy below 60%
    - Practicing: 5+ attempts with 60-84% accuracy
    - Mastered:   10+ attempts with >= 85% accuracy
    """
    if attempts >= 10 and accuracy >= 0.85:
        return "Mastered"
    if attempts >= 5 and accuracy >= 0.60:
        return "Practicing"
    return "Learning"


class ProgressDB:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path else DEFAULT_DB
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path)
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def record_attempt(self, letter: str, correct: bool) -> None:
        self._conn.execute(
            "INSERT INTO attempts (letter, correct) VALUES (?, ?)",
            (letter.upper(), 1 if correct else 0),
        )
        self._conn.commit()

    def letter_stats(self) -> dict[str, dict]:
        """Return per-letter {attempts, correct, accuracy, mastery}."""
        stats: dict[str, dict] = {}
        for letter in (chr(c) for c in range(ord("A"), ord("Z") + 1)):
            row = self._conn.execute(
                "SELECT COUNT(*), COALESCE(SUM(correct), 0) FROM attempts WHERE letter = ?",
                (letter,),
            ).fetchone()
            attempts, correct = row[0], row[1]
            accuracy = correct / attempts if attempts else 0.0
            stats[letter] = {
                "attempts": attempts,
                "correct": correct,
                "accuracy": accuracy,
                "mastery": mastery_level(attempts, accuracy),
            }
        return stats

    def overall(self) -> dict:
        row = self._conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(correct), 0) FROM attempts"
        ).fetchone()
        attempts, correct = row[0], row[1]
        return {
            "attempts": attempts,
            "correct": correct,
            "accuracy": (correct / attempts) if attempts else 0.0,
        }

    def reset(self) -> None:
        self._conn.execute("DELETE FROM attempts")
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()


def format_progress_table(stats: dict[str, dict]) -> str:
    """Render a terminal mastery table with an accuracy bar per letter."""
    lines = ["Letter  Attempts  Accuracy  Mastery", "-" * 38]
    for letter in sorted(stats):
        s = stats[letter]
        bar = "█" * round(s["accuracy"] * 10) + "░" * (10 - round(s["accuracy"] * 10))
        lines.append(
            f"  {letter}       {s['attempts']:>3}     {s['accuracy']:>5.0%} {bar}  {s['mastery']}"
        )
    return "\n".join(lines)


def run_progress(args) -> int:
    db = ProgressDB(args.db)
    stats = db.letter_stats()
    overall = db.overall()
    print("=== SignBridge progress ===")
    print(f"Total attempts: {overall['attempts']} | Overall accuracy: {overall['accuracy']:.0%}")
    print()
    print(format_progress_table(stats))
    mastered = sum(1 for s in stats.values() if s["mastery"] == "Mastered")
    print(f"\nLetters mastered: {mastered}/26")
    return 0
