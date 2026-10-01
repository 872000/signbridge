"""Tests for SQLite progress tracking."""

import pytest

from signbridge.progress import ProgressDB, format_progress_table, mastery_level


@pytest.fixture()
def db(tmp_path):
    database = ProgressDB(tmp_path / "progress.db")
    yield database
    database.close()


def test_record_attempt_updates_stats(db):
    db.record_attempt("K", True)
    db.record_attempt("K", False)
    db.record_attempt("K", True)
    stats = db.letter_stats()["K"]
    assert stats["attempts"] == 3
    assert stats["correct"] == 2
    assert stats["accuracy"] == pytest.approx(2 / 3)


def test_unattempted_letters_are_learning(db):
    stats = db.letter_stats()
    assert stats["Q"]["attempts"] == 0
    assert stats["Q"]["mastery"] == "Learning"


def test_mastery_level_thresholds():
    assert mastery_level(0, 0.0) == "Learning"
    assert mastery_level(4, 1.0) == "Learning"      # too few attempts
    assert mastery_level(6, 0.5) == "Learning"      # accuracy too low
    assert mastery_level(6, 0.7) == "Practicing"
    assert mastery_level(12, 0.8) == "Practicing"
    assert mastery_level(10, 0.9) == "Mastered"
    assert mastery_level(30, 0.85) == "Mastered"


def test_overall_stats(db):
    db.record_attempt("A", True)
    db.record_attempt("B", False)
    overall = db.overall()
    assert overall["attempts"] == 2
    assert overall["accuracy"] == pytest.approx(0.5)


def test_reset_clears_history(db):
    db.record_attempt("A", True)
    db.reset()
    assert db.overall()["attempts"] == 0


def test_format_progress_table_lists_all_letters(db):
    table = format_progress_table(db.letter_stats())
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        assert f"  {letter} " in table
