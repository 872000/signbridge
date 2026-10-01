"""Tests for the prototype contour recognizer."""

import numpy as np

from signbridge.dataset import load_alphabet
from signbridge.recognizer import (
    TemplateRecognizer,
    extract_features,
    generate_silhouette,
)


def test_silhouette_is_binary_image():
    img = generate_silhouette("K", ["T", "I", "M"])
    assert img.dtype == np.uint8
    assert img.shape == (200, 200)
    assert set(np.unique(img)).issubset({0, 255})
    assert img.sum() > 0  # something was drawn


def test_silhouettes_are_deterministic():
    a = generate_silhouette("V", ["I", "M"])
    b = generate_silhouette("V", ["I", "M"])
    assert np.array_equal(a, b)


def test_feature_extraction_returns_11d_vector():
    img = generate_silhouette("B", ["I", "M", "R", "P"])
    feats = extract_features(img)
    assert feats.shape == (11,)
    assert np.all(np.isfinite(feats))


def test_feature_extraction_handles_blank_image():
    feats = extract_features(np.zeros((200, 200), dtype=np.uint8))
    assert feats.shape == (11,)
    assert np.all(feats == 0)


def test_templates_match_themselves():
    alphabet = load_alphabet()
    rec = TemplateRecognizer(alphabet)
    result = rec.evaluate_self_consistency()
    assert result["total"] == 26
    assert result["correct"] == 26, f"mistakes: {result['mistakes']}"


def test_recognize_returns_letter_and_distance():
    alphabet = load_alphabet()
    rec = TemplateRecognizer(alphabet)
    guess, dist = rec.recognize_letter("L")
    assert guess == "L"
    assert dist == 0.0  # exact template hit
