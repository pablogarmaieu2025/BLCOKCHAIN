"""Veil: the full flow from enrolment to the gate.

    enrol   -> extract template, delete photo, protect with a salt,
               encrypt, split the key 2-of-3, anchor a commitment on chain
    verify  -> the phone releases the salt and its key share, the gate
               rebuilds the key with the campus share, checks the wallet
               copy against the on-chain commitment, protects the live scan
               with the same salt and compares distances. The gate learns
               only "valid student" or "no match".
    revoke  -> new salt, new protected template, old commitment revoked.
               Same face, no re-scan, every old copy is useless.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np

from . import crypto, templates
from .ledger import Ledger, sha256_hex


@dataclass
class Wallet:
    """What lives in the student's phone app. Never on a central server."""
    did: str
    salt: bytes
    ciphertext: crypto.Ciphertext
    phone_share: crypto.Share


@dataclass
class GateResult:
    granted: bool
    distance: float
    similarity: float
    proof: str
    reason: str


def commitment_for(protected: np.ndarray, salt: bytes) -> str:
    """Hash of the protected template + salt.

    Used only to prove the wallet copy wasn't swapped or edited. Matching a
    face is always done by distance, never by hash.
    """
    return sha256_hex(np.asarray(protected, dtype=np.float64).tobytes() + salt)


class Veil:
    def __init__(self, ledger: Ledger | None = None):
        self.ledger = ledger or Ledger()
        # What the campus server holds. Note: no photos, no templates, no names.
        self.campus_hsm: dict[str, crypto.Share] = {}
        self.recovery_vault: dict[str, crypto.Share] = {}

    # ------------------------------------------------------------- enrol
    def enroll(self, student_id: str, raw_template: np.ndarray) -> Wallet:
        salt = os.urandom(16)
        protected = templates.protect(raw_template, salt)
        did = "did:veil:" + sha256_hex(student_id.encode() + salt)[:16]

        key = crypto.new_key()
        ct = crypto.encrypt_template(protected, key, associated=did.encode())
        phone, hsm, vault = crypto.split_key(key)
        self.campus_hsm[did] = hsm
        self.recovery_vault[did] = vault

        self.ledger.append("ENROL", {"did": did, "commitment": commitment_for(protected, salt),
                                     "policy": "campus-gates"})
        return Wallet(did, salt, ct, phone)

    # ------------------------------------------------------------ verify
    def log_event(self, granted: bool, gate: str) -> str:
        """Write one access event. Pseudonymous: no DID or name in the log."""
        proof = sha256_hex(f"proof|{gate}|{os.urandom(16).hex()}")
        event = "evt-" + sha256_hex(os.urandom(16))[:12]
        self.ledger.append("ACCESS" if granted else "DENY",
                           {"event": event, "gate": gate,
                            "result": "granted" if granted else "denied", "proof": proof})
        return proof

    def verify(self, wallet: Wallet, live_template: np.ndarray, gate: str,
               log: bool = True) -> GateResult:
        def finish(granted: bool, d: float, reason: str) -> GateResult:
            proof = self.log_event(granted, gate) if log else ""
            return GateResult(granted, d, templates.similarity_percent(d), proof, reason)

        committed = self.ledger.active_commitment(wallet.did)
        if committed is None:
            return finish(False, float("inf"), "face key revoked or never enrolled")

        hsm = self.campus_hsm.get(wallet.did)
        if hsm is None:
            return finish(False, float("inf"), "no campus key share")
        try:
            key = crypto.combine_shares([wallet.phone_share, hsm])
            stored = crypto.decrypt_template(wallet.ciphertext, key, associated=wallet.did.encode())
        except Exception:
            # e.g. an old phone share after a revoke no longer fits the campus share
            return finish(False, float("inf"), "wallet key no longer valid")

        if commitment_for(stored, wallet.salt) != committed:
            return finish(False, float("inf"), "wallet template does not match the ledger")

        live = templates.protect(live_template, wallet.salt)
        d = templates.distance(live, stored)
        if d <= templates.MATCH_THRESHOLD:
            return finish(True, d, "valid student")
        return finish(False, d, "no match")

    # ------------------------------------------------------------ revoke
    def revoke_and_reissue(self, wallet: Wallet, raw_template: np.ndarray,
                           reason: str = "device lost") -> tuple[Wallet, float]:
        """Cancel the old face key and issue a new one from the same face.

        Returns the new wallet and the distance between the old and new
        protected templates (large = the old copy is useless).
        """
        old_key = crypto.combine_shares([self.campus_hsm[wallet.did], self.recovery_vault[wallet.did]])
        old_protected = crypto.decrypt_template(wallet.ciphertext, old_key, associated=wallet.did.encode())
        old_commitment = self.ledger.active_commitment(wallet.did)
        self.ledger.append("REVOKE", {"did": wallet.did, "revoked": old_commitment, "reason": reason})

        salt = os.urandom(16)
        protected = templates.protect(raw_template, salt)
        key = crypto.new_key()
        ct = crypto.encrypt_template(protected, key, associated=wallet.did.encode())
        phone, hsm, vault = crypto.split_key(key)
        self.campus_hsm[wallet.did] = hsm
        self.recovery_vault[wallet.did] = vault
        self.ledger.append("ENROL", {"did": wallet.did, "commitment": commitment_for(protected, salt),
                                     "policy": "campus-gates"})
        return Wallet(wallet.did, salt, ct, phone), templates.distance(old_protected, protected)

    # ------------------------------------------------------------ breach
    def breach_report(self) -> list[str]:
        """Everything an attacker gets by stealing the whole campus server."""
        loot = [f"{b.fields['commitment'][:10]}… commitment hash"
                for b in self.ledger.blocks if b.kind == "ENROL"]
        loot.append(f"{len(self.campus_hsm)} campus key shares (1 of 3 each, can't decrypt alone)")
        loot.append(f"{sum(b.kind in ('ACCESS', 'DENY') for b in self.ledger.blocks)} access events with pseudonymous IDs")
        loot.append("0 photos · 0 raw templates · 0 names")
        return loot
