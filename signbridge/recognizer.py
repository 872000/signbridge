"""Prototype shape recognizer: synthetic silhouettes + from-scratch contour features.

HONEST FRAMING — READ THIS:
This module is a *prototype stand-in*, not real hand tracking. It generates
simple geometric silhouettes per letter programmatically (a palm blob plus
finger-like protrusions), extracts contour/shape features from them, and
matches against templates with nearest-neighbor. It demonstrates the
*technique* (contour features + template matching) that a real system would
use, without claiming to recognize real hands from a camera. No ML model,
no training data, fully offline.

Technique summary:
  * Silhouette generation: palm ellipse + protrusions per extended digit,
    drawn with OpenCV on a blank canvas (deterministic, seeded per letter).
  * Features: Hu moments (log-scaled) + aspect ratio + extent + solidity +
    normalized convexity-defect count — all computed from the raw contour.
  * Matching: nearest template by Euclidean distance over the feature vector.
"""

from __future__ import annotations

import math

import cv2
import numpy as np

CANVAS = 200  # square canvas side in px

# Angle (degrees) at which each digit's protrusion leaves the palm blob.
DIGIT_ANGLES = {"T": 35.0, "I": 68.0, "M": 90.0, "R": 112.0, "P": 145.0}

# Per-letter silhouette parameters: digits extended, finger length factor,
# finger thickness factor, palm radius factor, and optional modifiers.
# Modifiers keep letters that share digit sets visually distinct:
#   fist  -> compact palm, short stubs      (A, S, T, M, N)
#   curved-> ring arc                        (C)
#   ring  -> closed ellipse ring             (O)
#   claw  -> short inward hooks              (E)
#   cross -> fingers overlapping             (R)
#   hook  -> single bent protrusion          (X)
#   angle -> L-shaped thumb+index            (L)
#   circle-> circle protrusion at base        (D)
#   flat  -> straight protrusions            (B, F, I, U, V, W, Y)
#   vee   -> spread protrusions              (K, P)
#   point -> protrusions aimed sideways      (G, H, Q)
#   motion-> extra trailing arc              (J, Z)
SHAPE_PARAMS = {
    "A": {"mod": "fist", "thumb_side": True},
    "B": {"mod": "flat", "len": 1.25},
    "C": {"mod": "curved"},
    "D": {"mod": "circle"},
    "E": {"mod": "claw"},
    "F": {"mod": "flat", "len": 1.15},
    "G": {"mod": "point"},
    "H": {"mod": "point", "spread": 1.4},
    "I": {"mod": "flat"},
    "J": {"mod": "flat", "trail": True},
    "K": {"mod": "vee"},
    "L": {"mod": "angle"},
    "M": {"mod": "fist", "humps": 3},
    "N": {"mod": "fist", "humps": 2},
    "O": {"mod": "ring"},
    "P": {"mod": "vee", "tilt": -70.0},
    "Q": {"mod": "point", "tilt": -70.0},
    "R": {"mod": "cross"},
    "S": {"mod": "fist", "thumb_front": True},
    "T": {"mod": "fist", "thumb_peek": True},
    "U": {"mod": "flat", "spread": 0.6},
    "V": {"mod": "vee", "spread": 1.6},
    "W": {"mod": "flat", "spread": 1.2},
    "X": {"mod": "hook"},
    "Y": {"mod": "flat", "spread": 1.8},
    "Z": {"mod": "flat", "trail": True, "zigzag": True},
}


def generate_silhouette(letter: str, digits: list[str]) -> np.ndarray:
    """Draw a deterministic synthetic hand-silhouette-ish image for a letter.

    Returns a single-channel uint8 image (white shape on black background).
    """
    letter = letter.upper()
    rng = np.random.default_rng(ord(letter))  # deterministic per letter
    params = SHAPE_PARAMS[letter]
    mod = params["mod"]

    img = np.zeros((CANVAS, CANVAS), dtype=np.uint8)
    cx, cy = CANVAS // 2, CANVAS // 2 + 18
    palm_r = int(46 * params.get("palm", 1.0))

    tilt = params.get("tilt", 0.0)

    def angle_for(digit: str, idx: int, total: int) -> float:
        base = DIGIT_ANGLES[digit] + tilt
        spread = params.get("spread", 1.0)
        if total > 1:
            base += (idx - (total - 1) / 2) * 9.0 * (spread - 1.0)
        return math.radians(base)

    # Palm blob
    axes = (palm_r, int(palm_r * 1.15))
    cv2.ellipse(img, (cx, cy), axes, 0, 0, 360, 255, -1)

    finger_len = 58 * params.get("len", 1.0)
    finger_w = 17

    if mod == "fist":
        # Compact blob with small bumps on top and a thumb marker blob.
        for i in range(params.get("humps", 2)):
            bx = cx - 26 + i * 26
            cv2.circle(img, (bx, cy - palm_r + 4), 12, 255, -1)
        # thumb marker: side (A), front bar (S), or small peek (T)
        if params.get("thumb_side"):
            cv2.ellipse(img, (cx - palm_r - 6, cy - 8), (12, 22), 25, 0, 360, 255, -1)
        elif params.get("thumb_front"):
            cv2.ellipse(img, (cx, cy - 2), (30, 11), 0, 0, 360, 255, -1)
        elif params.get("thumb_peek"):
            cv2.circle(img, (cx, cy - palm_r - 2), 9, 255, -1)
        else:  # M / N: draw the thumb lump under the folded fingers
            cv2.ellipse(img, (cx + 10, cy - palm_r + 12), (18, 10), 0, 0, 360, 255, -1)
    elif mod == "curved":  # C: thick open ring
        cv2.ellipse(img, (cx, cy - 30), (44, 52), 0, 40, 320, 255, 22)
    elif mod == "ring":  # O: closed ring
        cv2.ellipse(img, (cx, cy - 34), (38, 44), 0, 0, 360, 255, 18)
    elif mod == "claw":  # E: palm with short inward hooks
        for i, x in enumerate([cx - 33, cx - 11, cx + 11, cx + 33]):
            cv2.ellipse(img, (x, cy - palm_r + 2), (11, 16), 0, 180, 360, 255, -1)
    elif mod == "circle":  # D: single finger + circle at its base
        cv2.ellipse(img, (cx, cy - palm_r - 22), (13, 30), 0, 0, 360, 255, -1)
        cv2.circle(img, (cx + 6, cy - palm_r + 18), 20, 255, 10)
    elif mod == "angle":  # L: thumb out to the side, index up
        cv2.ellipse(img, (cx, cy - palm_r - 20), (12, 30), 0, 0, 360, 255, -1)
        cv2.ellipse(img, (cx - palm_r - 22, cy - 14), (26, 11), -20, 0, 360, 255, -1)
    elif mod == "hook":  # X: single bent protrusion
        pts = np.array(
            [
                [cx - 10, cy - palm_r + 10],
                [cx - 8, cy - palm_r - 26],
                [cx + 12, cy - palm_r - 30],
            ],
            np.int32,
        )
        cv2.polylines(img, [pts], False, 255, 22)
    elif mod == "cross":  # R: two overlapping protrusions
        cv2.ellipse(img, (cx - 12, cy - palm_r - 22), (12, 32), -14, 0, 360, 255, -1)
        cv2.ellipse(img, (cx + 12, cy - palm_r - 22), (12, 32), 14, 0, 360, 255, -1)
    else:
        # flat / vee / point: protrusions per extended digit
        n = len(digits)
        for idx, digit in enumerate(digits):
            ang = angle_for(digit, idx, n)
            ex = cx + int(math.cos(ang) * (palm_r * 0.55))
            ey = cy - int(math.sin(ang) * (palm_r * 0.55))
            tx = cx + int(math.cos(ang) * (palm_r + finger_len))
            ty = cy - int(math.sin(ang) * (palm_r + finger_len))
            thick = finger_w
            cv2.line(img, (ex, ey), (tx, ty), 255, thick)
            cv2.circle(img, (tx, ty), thick // 2, 255, -1)
        if params.get("trail"):  # J / Z: motion trail arc
            cv2.ellipse(img, (cx + 30, cy - palm_r - 40), (30, 26), 0, 200, 340, 255, 6)

    # Deterministic speckle so each template is a touch unique yet stable.
    speckle = (rng.random((CANVAS, CANVAS)) > 0.985).astype(np.uint8) * 255
    img = cv2.bitwise_or(img, speckle)
    _, img = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    return img


def _largest_contour(img: np.ndarray):
    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    return max(contours, key=cv2.contourArea)


def extract_features(img: np.ndarray) -> np.ndarray:
    """Extract a contour/shape feature vector from a binary silhouette.

    Features: log-scaled Hu moments (7) + aspect ratio + extent + solidity
    + normalized convexity-defect count = 11 dimensions.
    """
    contour = _largest_contour(img)
    if contour is None or cv2.contourArea(contour) < 10:
        return np.zeros(11, dtype=float)

    moments = cv2.moments(contour)
    hu = cv2.HuMoments(moments).flatten()
    hu_log = np.array([-math.copysign(math.log10(abs(h) + 1e-30), h) for h in hu])

    x, y, w, h = cv2.boundingRect(contour)
    aspect = w / h if h else 0.0
    area = cv2.contourArea(contour)
    extent = area / (w * h) if w and h else 0.0
    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    solidity = area / hull_area if hull_area else 0.0

    # Convexity defects (finger gaps proxy), normalized by perimeter.
    defects_count = 0
    try:
        hull_idx = cv2.convexHull(contour, returnPoints=False)
        if hull_idx is not None and len(hull_idx) > 3:
            defects = cv2.convexityDefects(contour, hull_idx)
            if defects is not None:
                defects_count = sum(1 for d in defects.reshape(-1, 4) if d[3] / 256.0 > 8.0)
    except cv2.error:
        defects_count = 0
    perimeter = cv2.arcLength(contour, True)
    defect_ratio = defects_count / (perimeter / 100.0 + 1e-9)

    return np.concatenate([hu_log, [aspect, extent, solidity, defect_ratio]])


class TemplateRecognizer:
    """Nearest-template matcher over contour feature vectors.

    Build once from the dataset's synthetic silhouettes; recognize by
    minimum Euclidean distance to a stored template vector.
    """

    def __init__(self, alphabet: list[dict] | None = None):
        from .dataset import load_alphabet  # lazy: avoid import cycle

        self.alphabet = alphabet or load_alphabet()
        self.templates: dict[str, np.ndarray] = {}
        for entry in self.alphabet:
            letter = entry["letter"]
            img = generate_silhouette(letter, entry["digits"])
            self.templates[letter] = extract_features(img)

    def recognize(self, img: np.ndarray) -> tuple[str, float]:
        """Return (best_letter, distance) for a silhouette image."""
        vec = extract_features(img)
        best, best_dist = None, float("inf")
        for letter, tmpl in self.templates.items():
            dist = float(np.linalg.norm(vec - tmpl))
            if dist < best_dist:
                best, best_dist = letter, dist
        return best, best_dist

    def recognize_letter(self, letter: str) -> tuple[str, float]:
        """Regenerate a letter's silhouette and recognize it (self-check)."""
        from .dataset import get_letter

        entry = get_letter(letter)
        img = generate_silhouette(entry["letter"], entry["digits"])
        return self.recognize(img)

    def evaluate_self_consistency(self) -> dict:
        """Recognize every template against itself; prototype sanity check."""
        correct = 0
        mistakes = []
        for entry in self.alphabet:
            letter = entry["letter"]
            guess, _ = self.recognize_letter(letter)
            if guess == letter:
                correct += 1
            else:
                mistakes.append((letter, guess))
        return {"total": len(self.alphabet), "correct": correct, "mistakes": mistakes}
