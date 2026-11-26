"""In-memory registrar for synthetic demo identities. Not a production identity store."""
from dataclasses import dataclass
import secrets

@dataclass(frozen=True)
class StudentRecord:
    student_id: str
    wallet: str
    key: bytes

class StudentRegistry:
    def __init__(self):
        self._records: dict[str, StudentRecord] = {}
        self._used_wallets: set[str] = set()

    def register(self, student_id: str, wallet: str) -> StudentRecord:
        if not student_id or student_id in self._records or wallet.lower() in self._used_wallets:
            raise ValueError("Duplicate or invalid enrollment")
        record = StudentRecord(student_id, wallet, secrets.token_bytes(32))
        self._records[student_id] = record
        self._used_wallets.add(wallet.lower())
        return record

    def wallet_of(self, student_id: str) -> str | None:
        record = self._records.get(student_id)
        return record.wallet if record else None

    def record_of(self, student_id: str) -> StudentRecord:
        return self._records[student_id]

    def replace_wallet(self, student_id: str, wallet: str) -> StudentRecord:
        old = self.record_of(student_id)
        if wallet.lower() in self._used_wallets:
            raise ValueError("Wallet already assigned")
        record = StudentRecord(student_id, wallet, old.key)
        self._records[student_id] = record
        self._used_wallets.add(wallet.lower())
        return record
