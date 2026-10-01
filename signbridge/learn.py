"""The `learn` CLI: browse the ASL alphabet with text/visual references."""

from __future__ import annotations

from .dataset import DIGIT_NAMES, load_alphabet

DIGIT_ORDER = ["T", "I", "M", "R", "P"]


def digit_diagram(entry: dict) -> str:
    """Render a simple finger-state diagram for a letter.

    Extended digits are shown as raised blocks; folded digits as dots.
    Example for L (thumb + index extended)::

        T I M R P
        █ █ · · ·
    """
    extended = set(entry["digits"])
    blocks = ["█" if d in extended else "·" for d in DIGIT_ORDER]
    header = " ".join(DIGIT_ORDER)
    row = " ".join(blocks)
    names = ", ".join(DIGIT_NAMES[d] for d in DIGIT_ORDER if d in extended)
    return f"{header}\n{row}\n(extended: {names or 'none — fingers folded/curved'})"


def format_letter(entry: dict) -> str:
    """Format one letter's full reference card for the terminal."""
    lines = [
        f"=== {entry['letter']} ===",
        f"Handshape: {entry['description']}",
        "",
        digit_diagram(entry),
        "",
        f"Practice tip: {entry['practice_tip']}",
    ]
    return "\n".join(lines)


def list_letters(alphabet: list[dict]) -> str:
    """One-line index of all 26 letters."""
    return " ".join(entry["letter"] for entry in alphabet)


def run_learn(args) -> int:
    alphabet = load_alphabet()
    if args.letter:
        entry = next((e for e in alphabet if e["letter"] == args.letter.upper()), None)
        if entry is None:
            print(f"Unknown letter: {args.letter}")
            return 1
        print(format_letter(entry))
    else:
        print("ASL Alphabet — pick a letter to study its handshape:")
        print(list_letters(alphabet))
        print()
        for entry in alphabet:
            print(format_letter(entry))
            print()
    return 0
