"""Tests for quiz grading and scoring math."""

import random

from signbridge.quiz import check_answer, pick_round_letters, score_quiz
from signbridge.dataset import load_alphabet


def test_check_answer_is_case_and_space_insensitive():
    assert check_answer("k", "K")
    assert check_answer("  K ", "K")
    assert not check_answer("V", "K")
    assert not check_answer("", "K")


def test_score_quiz_math():
    s = score_quiz([True, True, False, True, False, False, True])
    assert s["total"] == 7
    assert s["correct"] == 4
    assert s["wrong"] == 3
    assert s["accuracy"] == 4 / 7
    assert s["best_streak"] == 2  # T,T then later T alone


def test_score_quiz_all_correct_streak():
    s = score_quiz([True] * 5)
    assert s["best_streak"] == 5
    assert s["accuracy"] == 1.0


def test_score_quiz_empty():
    s = score_quiz([])
    assert s == {"total": 0, "correct": 0, "wrong": 0, "accuracy": 0.0, "best_streak": 0}


def test_pick_round_letters_is_reproducible_with_seed():
    alphabet = load_alphabet()
    a = pick_round_letters(alphabet, 20, random.Random(7))
    b = pick_round_letters(alphabet, 20, random.Random(7))
    assert [e["letter"] for e in a] == [e["letter"] for e in b]
    assert len(a) == 20
    assert all(e["letter"] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" for e in a)
