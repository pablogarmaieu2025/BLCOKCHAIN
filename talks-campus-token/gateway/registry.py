"""Links a student id to their wallet address. Kept OFF-chain, by IE.

The blockchain only ever sees wallet addresses, never names or student ids.
"""
from __future__ import annotations

from typing import Optional


class StudentRegistry:
    def __init__(self):
        self._wallets: dict[str, str] = {}

    def register(self, student_id: str, wallet: str) -> None:
        self._wallets[student_id] = wallet

    def wallet_of(self, student_id: str) -> Optional[str]:
        return self._wallets.get(student_id)
