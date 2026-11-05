"""A small permissioned blockchain run by three campus validators.

Each block links to the previous block's hash and needs approval from at
least 2 of the 3 validators (proof of authority). Approvals are HMAC
signatures here; a real network would use public-key signatures.

The ledger NEVER holds a face, a template or a name: only pseudonymous IDs,
commitment hashes and access events.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone

VALIDATORS = ("Registrar", "IT Security", "Student Council")
REQUIRED_APPROVALS = 2


def sha256_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()


def short(h: str) -> str:
    return f"{h[:10]}…{h[-6:]}"


@dataclass
class Block:
    index: int
    kind: str                      # GENESIS, ENROL, ACCESS, DENY, REVOKE
    fields: dict
    prev_hash: str
    timestamp: str
    approvals: dict = field(default_factory=dict)  # validator -> signature
    hash: str = ""

    def body(self) -> str:
        return json.dumps(
            {"i": self.index, "kind": self.kind, "fields": self.fields,
             "prev": self.prev_hash, "t": self.timestamp},
            sort_keys=True,
        )


class Ledger:
    def __init__(self, validators=VALIDATORS):
        self._keys = {v: secrets.token_bytes(32) for v in validators}
        self.blocks: list[Block] = []
        self.append("GENESIS", {"network": "veil-campus", "validators": len(validators),
                                "consensus": f"PoA, {REQUIRED_APPROVALS}-of-{len(validators)}"})

    # -------------------------------------------------------------- writing
    def append(self, kind: str, fields: dict, approvers=None) -> Block:
        approvers = list(approvers or self._keys)[:]
        prev = self.blocks[-1].hash if self.blocks else "0" * 64
        block = Block(len(self.blocks), kind, fields, prev,
                      datetime.now(timezone.utc).isoformat(timespec="seconds"))
        block.hash = sha256_hex(block.body())
        for v in approvers:
            block.approvals[v] = hmac.new(self._keys[v], block.hash.encode(), "sha256").hexdigest()
        if len(block.approvals) < REQUIRED_APPROVALS:
            raise PermissionError(f"Block needs {REQUIRED_APPROVALS} validator approvals.")
        self.blocks.append(block)
        return block

    # -------------------------------------------------------------- reading
    def verify_chain(self) -> bool:
        """Check every hash link and every approval. Any tampering fails."""
        prev = "0" * 64
        for b in self.blocks:
            if b.prev_hash != prev or sha256_hex(b.body()) != b.hash:
                return False
            good = sum(
                hmac.compare_digest(sig, hmac.new(self._keys[v], b.hash.encode(), "sha256").hexdigest())
                for v, sig in b.approvals.items() if v in self._keys
            )
            if good < REQUIRED_APPROVALS:
                return False
            prev = b.hash
        return True

    def active_commitment(self, did: str) -> str | None:
        """The latest commitment enrolled for a pseudonymous ID, unless revoked."""
        commitment = None
        for b in self.blocks:
            if b.fields.get("did") != did:
                continue
            if b.kind == "ENROL":
                commitment = b.fields["commitment"]
            elif b.kind == "REVOKE" and b.fields.get("revoked") == commitment:
                commitment = None
        return commitment

    def print_tail(self, n: int = 3) -> None:
        for b in self.blocks[-n:]:
            shown = ", ".join(f"{k}={short(v) if isinstance(v, str) and len(v) == 64 else v}"
                              for k, v in b.fields.items())
            print(f"    #{b.index} {b.kind:<7} {shown}  [hash {short(b.hash)}]")
