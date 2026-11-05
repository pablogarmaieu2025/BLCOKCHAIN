"""Veil: protected face entry for campuses, anchored on a permissioned blockchain.

Pitch prototype. Not for real biometric data.
"""

from .ledger import Ledger
from .matcher import TeammateFaceMatcher
from .system import GateResult, Veil, Wallet

__all__ = ["Ledger", "Veil", "Wallet", "GateResult", "TeammateFaceMatcher"]
