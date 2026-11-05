"""Face templates: extraction, cancellable protection and matching.

A face template is a vector of numbers (an "embedding"). Two photos of the
same face give vectors that are CLOSE, never identical, so matching uses the
distance between vectors, never a hash.

Protection uses a salted random projection (a "cancellable biometric"):
    protected = M(salt) @ template
The projection is one-way (64 numbers from 128, so the face can't be rebuilt)
and depends on a secret salt. Change the salt and every old protected copy
stops matching, without re-scanning the face.
"""

from __future__ import annotations

import hashlib

import numpy as np

RAW_DIM = 128          # size of the raw face template
PROTECTED_DIM = 64     # size of the protected template
MATCH_THRESHOLD = 0.6  # max distance between protected templates for a match

try:  # optional: real face embeddings from a photo
    import face_recognition  # type: ignore
    HAVE_FACE_RECOGNITION = True
except Exception:  # pragma: no cover - depends on the machine
    HAVE_FACE_RECOGNITION = False


# ---------------------------------------------------------------- extraction
def simulated_template(seed: int) -> np.ndarray:
    """A stand-in face template for a sample person (unit length)."""
    rng = np.random.default_rng(seed * 7919)
    v = rng.standard_normal(RAW_DIM)
    return v / np.linalg.norm(v)


def live_capture(template: np.ndarray, noise: float = 0.02, rng=None) -> np.ndarray:
    """Simulate a new scan of the same face: the template plus a little noise."""
    rng = rng or np.random.default_rng()
    v = template + rng.standard_normal(template.shape) * noise
    return v / np.linalg.norm(v)


def template_from_image(path: str) -> np.ndarray:
    """Extract a real 128-number template from a photo.

    Needs the optional `face_recognition` package. Raises ValueError if no
    face (or more than one face) is found.
    """
    if not HAVE_FACE_RECOGNITION:
        raise RuntimeError(
            "Install the optional face_recognition package to use real photos "
            "(pip install face_recognition)."
        )
    image = face_recognition.load_image_file(path)
    encodings = face_recognition.face_encodings(image)
    if len(encodings) != 1:
        raise ValueError(f"Expected exactly one face in {path}, found {len(encodings)}.")
    # The photo itself is never kept: only the vector leaves this function.
    del image
    return np.asarray(encodings[0], dtype=float)


# ---------------------------------------------------------------- protection
def _projection_matrix(salt: bytes) -> np.ndarray:
    """A random Gaussian matrix seeded by the salt.

    Entries ~ N(0, 1/k) so distances between templates are roughly preserved
    (Johnson-Lindenstrauss), which keeps matching accurate after protection.
    """
    seed = int.from_bytes(hashlib.sha256(b"veil-projection|" + salt).digest()[:8], "big")
    rng = np.random.default_rng(seed)
    return rng.standard_normal((PROTECTED_DIM, RAW_DIM)) / np.sqrt(PROTECTED_DIM)


def protect(template: np.ndarray, salt: bytes) -> np.ndarray:
    """Turn a raw template into a cancellable, one-way protected template."""
    return _projection_matrix(salt) @ np.asarray(template, dtype=float)


def distance(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(np.asarray(a) - np.asarray(b)))


def is_match(a: np.ndarray, b: np.ndarray, threshold: float = MATCH_THRESHOLD) -> bool:
    return distance(a, b) <= threshold


def similarity_percent(d: float) -> float:
    """A friendly 0-100 score for display (100 = identical)."""
    return max(0.0, 100.0 * (1.0 - d / 1.5))
