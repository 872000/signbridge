"""Bundled demo: everything runs out of the box.

Runs a short scripted quiz (answers auto-played), records progress, exercises
the prototype recognizer, and regenerates the alphabet reference grid and the
progress chart images under ``assets/``.
"""

from __future__ import annotations

import random
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .dataset import load_alphabet
from .progress import ProgressDB
from .quiz import check_answer, score_quiz
from .recognizer import TemplateRecognizer, generate_silhouette


def make_reference_grid(alphabet: list[dict], outpath: Path) -> None:
    """Render a 26-cell reference grid of the synthetic silhouettes (real output)."""
    fig, axes = plt.subplots(4, 7, figsize=(14, 8))
    fig.suptitle("SignBridge — ASL alphabet reference silhouettes (prototype, synthetic)", fontsize=14)
    cells = list(alphabet) + [None]  # 27th cell stays empty
    for ax, entry in zip(axes.flat, cells):
        if entry is None:
            ax.axis("off")
            ax.set_visible(False)
            continue
        ax.axis("off")
        img = generate_silhouette(entry["letter"], entry["digits"])
        ax.imshow(img, cmap="gray")
        ax.set_title(entry["letter"], fontsize=12, fontweight="bold", pad=2)
    fig.tight_layout()
    fig.savefig(outpath, dpi=120)
    plt.close(fig)


def make_progress_chart(db: ProgressDB, outpath: Path) -> None:
    """Render a per-letter accuracy chart from the progress DB (real output)."""
    stats = db.letter_stats()
    letters = sorted(stats)
    acc = [stats[l]["accuracy"] for l in letters]
    colors = {"Learning": "#e74c3c", "Practicing": "#f39c12", "Mastered": "#27ae60"}
    bar_colors = [colors[stats[l]["mastery"]] for l in letters]

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.bar(letters, acc, color=bar_colors)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Accuracy")
    ax.set_xlabel("Letter")
    ax.set_title("SignBridge — per-letter quiz accuracy & mastery")
    for label, color in colors.items():
        ax.bar([], [], color=color, label=label)
    ax.legend()
    fig.tight_layout()
    fig.savefig(outpath, dpi=120)
    plt.close(fig)


def run_demo(args) -> int:
    alphabet = load_alphabet()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print("=== SignBridge demo ===")
    print("1) Reference dataset:", len(alphabet), "letters loaded (A-Z).")

    # 2) Scripted quiz with deterministic simulated answers.
    rng = random.Random(42)
    rounds = [rng.choice(alphabet) for _ in range(12)]
    db = ProgressDB(args.db)
    db.reset()
    results = []
    for i, entry in enumerate(rounds, 1):
        # Simulate a learner who knows the first half of the alphabet well.
        simulated = entry["letter"] if ord(entry["letter"]) <= ord("M") else "Z"
        correct = check_answer(simulated, entry["letter"])
        results.append(correct)
        db.record_attempt(entry["letter"], correct)
        mark = "✔" if correct else "✘"
        print(f"   Round {i:>2}: handshape of {entry['letter']} -> answered '{simulated}' {mark}")
    summary = score_quiz(results)
    print(f"   Demo quiz score: {summary['correct']}/{summary['total']} "
          f"({summary['accuracy']:.0%}), best streak {summary['best_streak']}")

    # 3) Prototype recognizer self-consistency check.
    rec = TemplateRecognizer(alphabet)
    check = rec.evaluate_self_consistency()
    print(f"2) Prototype recognizer self-consistency: {check['correct']}/{check['total']}")

    # 4) Regenerate real visual outputs.
    grid_path = outdir / "alphabet_grid.png"
    chart_path = outdir / "progress_chart.png"
    make_reference_grid(alphabet, grid_path)
    make_progress_chart(db, chart_path)
    print(f"3) Wrote {grid_path}")
    print(f"   Wrote {chart_path}")
    print("\nDemo complete. Try: python3 -m signbridge learn K | quiz | progress")
    return 0


if __name__ == "__main__":
    raise SystemExit("Use: python3 -m signbridge demo")
