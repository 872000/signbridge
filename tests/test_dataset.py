"""Tests for the ASL alphabet dataset."""

import pytest

from signbridge.dataset import REQUIRED_FIELDS, get_letter, load_alphabet


def test_dataset_has_exactly_26_letters_a_to_z():
    alphabet = load_alphabet()
    assert len(alphabet) == 26
    assert [e["letter"] for e in alphabet] == [chr(c) for c in range(ord("A"), ord("Z") + 1)]


def test_every_entry_has_required_fields():
    for entry in load_alphabet():
        for field in REQUIRED_FIELDS:
            assert field in entry, f"{entry['letter']} missing {field}"
        assert entry["description"].strip(), f"{entry['letter']} empty description"
        assert entry["practice_tip"].strip(), f"{entry['letter']} empty tip"


def test_digit_codes_are_valid():
    from signbridge.dataset import DIGIT_NAMES

    for entry in load_alphabet():
        for digit in entry["digits"]:
            assert digit in DIGIT_NAMES


def test_get_letter_roundtrip():
    entry = get_letter("k")
    assert entry["letter"] == "K"
    assert "thumb" in entry["description"].lower()
    with pytest.raises(KeyError):
        get_letter("1")
