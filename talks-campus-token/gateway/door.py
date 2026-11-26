"""Demo gateway: local authentication -> registrar -> authorized on-chain check-in."""
from dataclasses import dataclass
from typing import Any, Optional
from web3.logs import DISCARD
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
    tx_hash: Optional[str] = None

class Door:
    def __init__(self, chain: CampusChain, matcher: FaceMatcher, registry: StudentRegistry):
        self.chain, self.matcher, self.registry = chain, matcher, registry

    def scan(self, image: Any, event: Optional[str] = None) -> ScanResult:
        try:
            student_id = self.matcher.identify(image)
        except Exception:
            return ScanResult(False, "authentication unavailable")
        if student_id is None:
            return ScanResult(False, "face not recognised")
        wallet = self.registry.wallet_of(student_id)
        if wallet is None:
            return ScanResult(False, "no wallet registered", student_id)
        try:
            if not self.chain.is_valid(wallet):
                return ScanResult(False, "pass missing or revoked", student_id, wallet)
            if event is None:
                return ScanResult(True, "access granted", student_id, wallet)
            if self.chain.already_checked_in(event, wallet):
                return ScanResult(True, "already checked in; no new tokens", student_id, wallet)
            receipt = self.chain.check_in(event, wallet)
            logs = self.chain.checkin.events.CheckedIn().process_receipt(receipt, errors=DISCARD)
            if len(logs) != 1:
                return ScanResult(False, "receipt requires reconciliation", student_id, wallet, tx_hash=receipt.transactionHash.hex())
            earned = int(logs[0]["args"]["reward"])
            return ScanResult(True, "checked in", student_id, wallet, earned, receipt.transactionHash.hex())
        except Exception:
            # Do not claim success on RPC failure or a reverted transaction.
            # An ambiguous submission may already have landed; reconcile on-chain before retrying.
            return ScanResult(False, "check-in unavailable or rejected; verify chain state", student_id, wallet)
