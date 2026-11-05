"""The door / event scanner: face -> student -> wallet -> pass check -> tokens.

    image --(FaceMatcher, local)--> student id
          --(StudentRegistry, IE)--> wallet
          --(StudentPass, chain)---> valid?  -> door opens
          --(EventCheckIn, chain)--> +reward tokens (once per event)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .chain import CampusChain
from .identity import FaceMatcher
from .registry import StudentRegistry


@dataclass
class ScanResult:
    granted: bool
    reason: str
    student_id: Optional[str] = None
    wallet: Optional[str] = None
    tokens_earned: int = 0


class Door:
    def __init__(self, chain: CampusChain, matcher: FaceMatcher, registry: StudentRegistry):
        self.chain = chain
        self.matcher = matcher
        self.registry = registry

    def scan(self, image: Any, event: Optional[str] = None) -> ScanResult:
        student_id = self.matcher.identify(image)
        if student_id is None:
            return ScanResult(False, "face not recognised")

        wallet = self.registry.wallet_of(student_id)
        if wallet is None:
            return ScanResult(False, "no wallet registered", student_id)

        if not self.chain.is_valid(wallet):
            return ScanResult(False, "pass missing or revoked", student_id, wallet)

        if event is None:
            return ScanResult(True, "access granted", student_id, wallet)

        if self.chain.already_checked_in(event, wallet):
            return ScanResult(True, "access granted (already checked in, no new tokens)", student_id, wallet)

        before = self.chain.balance(wallet)
        self.chain.check_in(event, wallet)
        earned = self.chain.balance(wallet) - before
        return ScanResult(True, "checked in", student_id, wallet, earned)
