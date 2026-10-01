"""Loading and validation for the 26-letter ASL reference dataset."""

from __future__ import annotations

import json
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "asl_alphabet.json"

REQUIRED_FIELDS = ("letter", "description", "practice_tip", "digits", "shape")

# Digit key -> display name, used by the learn CLI schematic.
DIGIT_NAMES = {"T": "Thumb", "I": "Index", "M": "Middle", "R": "Ring", "P": "Pinky"}


def load_alphabet(path: Path | str | None = None) -> list[dict]:
    """Load the ASL alphabet dataset, validating shape and contents."""
    with open(path or DATA_PATH, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("Dataset must be a list of letter entries")
    letters = [entry["letter"] for entry in data]
    if letters != [chr(c) for c in range(ord("A"), ord("Z") + 1)]:
        raise ValueError("Dataset must contain exactly letters A-Z in order")
    for entry in data:
        for field in REQUIRED_FIELDS:
            if field not in entry:
                raise ValueError(f"Entry {entry.get('letter', '?')} missing field: {field}")
        for digit in entry["digits"]:
            if digit not in DIGIT_NAMES:
                raise ValueError(f"Entry {entry['letter']} has unknown digit code: {digit}")
    return data


def get_letter(letter: str, path: Path | str | None = None) -> dict:
    """Fetch one letter's entry by its uppercase letter."""
    letter = letter.upper()
    for entry in load_alphabet(path):
        if entry["letter"] == letter:
            return entry
    raise KeyError(f"Unknown letter: {letter}")
