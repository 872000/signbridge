"""SignBridge command-line interface."""

from __future__ import annotations

import argparse

from .demo import run_demo
from .learn import run_learn
from .progress import run_progress
from .quiz import run_quiz
from .recognize import run_recognize


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="signbridge",
        description="SignBridge — an ASL fingerspelling trainer with a prototype shape recognizer.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    learn = sub.add_parser("learn", help="Browse the 26-letter ASL alphabet reference.")
    learn.add_argument("letter", nargs="?", help="Show a single letter, e.g. 'learn K'.")

    quiz = sub.add_parser("quiz", help="Quiz yourself: name the letter from its handshape.")
    quiz.add_argument("--rounds", type=int, default=10, help="Number of quiz rounds (default: 10).")
    quiz.add_argument("--seed", type=int, default=None, help="Random seed for reproducible quizzes.")
    quiz.add_argument("--db", default=None, help="Progress database path.")

    prog = sub.add_parser("progress", help="Show per-letter mastery from your quiz history.")
    prog.add_argument("--db", default=None, help="Progress database path.")

    rec = sub.add_parser("recognize", help="Demo the prototype contour recognizer on synthetic silhouettes.")
    rec.add_argument("letter", nargs="?", help="Recognize one letter's synthetic silhouette.")
    rec.add_argument("--self-test", action="store_true", help="Check all 26 templates against themselves.")

    demo = sub.add_parser("demo", help="Run the bundled out-of-the-box demo.")
    demo.add_argument("--db", default=None, help="Progress database path for the demo.")
    demo.add_argument("--outdir", default="assets", help="Where to write demo images.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "learn":
        return run_learn(args)
    if args.command == "quiz":
        return run_quiz(args)
    if args.command == "progress":
        return run_progress(args)
    if args.command == "recognize":
        return run_recognize(args)
    if args.command == "demo":
        return run_demo(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
