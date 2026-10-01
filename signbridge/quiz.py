"""The `quiz` CLI: identify random letters from their handshape descriptions.

The quiz is typed-answer based on purpose: the prompt shows a letter's
handshape description and the user types which letter it is. Typed answers
are honest, deterministic, and testable — no fragile camera input involved.
"""

from __future__ import annotations

import random
import sys

from .dataset import load_alphabet
from .learn import digit_diagram
from .progress import ProgressDB


def check_answer(user_input: str, correct_letter: str) -> bool:
    """Case/whitespace-insensitive single-letter grading."""
    return user_input.strip().upper() == correct_letter.upper()


def score_quiz(results: list[bool]) -> dict:
    """Aggregate quiz results: score, best streak, and per-round detail."""
    total = len(results)
    correct = sum(1 for r in results if r)
    best_streak = current = 0
    for r in results:
        current = current + 1 if r else 0
        best_streak = max(best_streak, current)
    accuracy = correct / total if total else 0.0
    return {
        "total": total,
        "correct": correct,
        "wrong": total - correct,
        "accuracy": accuracy,
        "best_streak": best_streak,
    }


def pick_round_letters(alphabet: list[dict], rounds: int, rng: random.Random) -> list[dict]:
    """Pick random letters with replacement for a quiz session."""
    return [rng.choice(alphabet) for _ in range(rounds)]


def run_quiz(args) -> int:
    alphabet = load_alphabet()
    rng = random.Random(args.seed) if args.seed is not None else random.Random()
    letters = pick_round_letters(alphabet, args.rounds, rng)
    db = ProgressDB(args.db)

    print(f"SignBridge quiz — {args.rounds} rounds. Type the letter (A-Z) for each handshape.")
    print("Type 'quit' to stop early.\n")

    results: list[bool] = []
    streak = 0
    for i, entry in enumerate(letters, 1):
        print(f"--- Round {i}/{args.rounds} ---")
        print(f"Handshape: {entry['description']}")
        print(digit_diagram(entry))
        try:
            answer = input("Which letter is this? > ")
        except (EOFError, KeyboardInterrupt):
            print("\nQuiz stopped.")
            break
        if answer.strip().lower() == "quit":
            print("Quiz stopped.")
            break
        correct = check_answer(answer, entry["letter"])
        results.append(correct)
        db.record_attempt(entry["letter"], correct)
        if correct:
            streak += 1
            print(f"✔ Correct! (streak: {streak})")
        else:
            streak = 0
            print(f"✘ It was {entry['letter']}. Tip: {entry['practice_tip']}")

    summary = score_quiz(results)
    print("\n=== Quiz results ===")
    print(f"Score: {summary['correct']}/{summary['total']} ({summary['accuracy']:.0%})")
    print(f"Best streak: {summary['best_streak']}")
    if summary["total"] and summary["accuracy"] == 1.0:
        print("Flawless — fingerspelling champion!")
    return 0
