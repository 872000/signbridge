"""The `recognize` CLI: exercise the prototype contour recognizer."""

from __future__ import annotations

from .dataset import get_letter
from .recognizer import TemplateRecognizer, generate_silhouette


def run_recognize(args) -> int:
    print("Prototype recognizer — synthetic silhouettes only, not real hand tracking.\n")
    rec = TemplateRecognizer()
    if args.self_test or not args.letter:
        result = rec.evaluate_self_consistency()
        print(f"Self-consistency: {result['correct']}/{result['total']} templates matched themselves.")
        for letter, guess in result["mistakes"]:
            print(f"  {letter} -> misclassified as {guess}")
        return 0
    entry = get_letter(args.letter)
    img = generate_silhouette(entry["letter"], entry["digits"])
    guess, dist = rec.recognize(img)
    print(f"Input: {entry['letter']}  ->  Recognized: {guess} (distance {dist:.3f})")
    return 0
