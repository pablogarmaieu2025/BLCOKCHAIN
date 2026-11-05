"""Encryption of the protected template and the 2-of-3 key split.

- AES-256-GCM encrypts the protected template, which then lives only in the
  student's wallet app.
- Shamir secret sharing splits the AES key into three shares (student phone,
  campus HSM, recovery vault). Any two rebuild the key; one alone is useless.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass

import numpy as np
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# A Mersenne prime larger than any 256-bit key, so shares work in GF(P).
_P = 2**521 - 1


# ------------------------------------------------------------------ AES-GCM
@dataclass(frozen=True)
class Ciphertext:
    nonce: bytes
    data: bytes

    def hex_preview(self, n: int = 24) -> str:
        return self.data.hex()[:n] + "…"


def new_key() -> bytes:
    return AESGCM.generate_key(bit_length=256)


def encrypt_template(protected: np.ndarray, key: bytes, associated: bytes = b"") -> Ciphertext:
    nonce = os.urandom(12)
    raw = np.asarray(protected, dtype=np.float64).tobytes()
    return Ciphertext(nonce, AESGCM(key).encrypt(nonce, raw, associated))


def decrypt_template(ct: Ciphertext, key: bytes, associated: bytes = b"") -> np.ndarray:
    raw = AESGCM(key).decrypt(ct.nonce, ct.data, associated)
    return np.frombuffer(raw, dtype=np.float64).copy()


# ---------------------------------------------------------- Shamir 2-of-3
@dataclass(frozen=True)
class Share:
    holder: str
    x: int
    y: int

    def preview(self) -> str:
        return hex(self.y)[2:18] + "…"


def split_key(key: bytes, holders=("Student phone", "Campus HSM", "Recovery vault"),
              threshold: int = 2) -> list[Share]:
    """Split a key so that any `threshold` of the holders can rebuild it."""
    secret = int.from_bytes(key, "big")
    coeffs = [secret] + [secrets.randbelow(_P) for _ in range(threshold - 1)]
    shares = []
    for i, holder in enumerate(holders, start=1):
        y = 0
        for power, c in enumerate(coeffs):
            y = (y + c * pow(i, power, _P)) % _P
        shares.append(Share(holder, i, y))
    return shares


def combine_shares(shares: list[Share], key_len: int = 32) -> bytes:
    """Rebuild the key from enough shares (Lagrange interpolation at x=0)."""
    secret = 0
    for j, sj in enumerate(shares):
        num, den = 1, 1
        for m, sm in enumerate(shares):
            if m != j:
                num = (num * -sm.x) % _P
                den = (den * (sj.x - sm.x)) % _P
        secret = (secret + sj.y * num * pow(den, -1, _P)) % _P
    if secret.bit_length() > key_len * 8:
        raise ValueError("Shares don't belong to the same key.")
    return secret.to_bytes(key_len, "big")
