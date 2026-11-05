"""Adapter for the talks. token team's Python door.

Their door asks one question: "which student is this?" It expects an object
with two methods:

    enroll(student_id, image)
    identify(image) -> student_id or None

and is wired in with one line:

    Door(chain, TeammateFaceMatcher(), registry)

This class answers that question with Veil's protected templates, so the
token contracts and tests don't change. `image` can be a path to a photo
(needs the optional face_recognition package) or a ready-made template
vector (for demos and tests).
"""

from __future__ import annotations

import numpy as np

from . import templates
from .system import Veil, Wallet


class TeammateFaceMatcher:
    def __init__(self, veil: Veil | None = None, gate: str = "talks. door"):
        self.veil = veil or Veil()
        self.gate = gate
        # In production each wallet stays on its owner's phone and the phone
        # presents it over NFC. For the demo door we keep them in memory.
        self._wallets: dict[str, Wallet] = {}

    @staticmethod
    def _to_template(image) -> np.ndarray:
        if isinstance(image, (str, bytes)) or hasattr(image, "__fspath__"):
            return templates.template_from_image(str(image))
        return np.asarray(image, dtype=float)

    def enroll(self, student_id: str, image) -> None:
        self._wallets[student_id] = self.veil.enroll(student_id, self._to_template(image))

    def identify(self, image) -> str | None:
        live = self._to_template(image)
        best_id, best_d = None, float("inf")
        for student_id, wallet in self._wallets.items():
            result = self.veil.verify(wallet, live, self.gate, log=False)
            if result.granted and result.distance < best_d:
                best_id, best_d = student_id, result.distance
        self.veil.log_event(best_id is not None, self.gate)
        return best_id

    def revoke(self, student_id: str) -> None:
        """Lost phone: cancel the face key. The door denies them at once."""
        wallet = self._wallets[student_id]
        old = self.veil.ledger.active_commitment(wallet.did)
        self.veil.ledger.append("REVOKE", {"did": wallet.did, "revoked": old, "reason": "device lost"})
