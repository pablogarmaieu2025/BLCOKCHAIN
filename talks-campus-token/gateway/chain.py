"""Python wrapper around the four smart contracts.

Everything the door, talks. and the demo need from the blockchain goes
through this one class, so the rest of the code never touches web3 directly.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from web3 import Web3

BUILD_DIR = Path(__file__).resolve().parent.parent / "build"


def _artifact(name: str) -> dict:
    path = BUILD_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing. Run: node scripts/compile.js")
    return json.loads(path.read_text())


def to_id(name: str) -> bytes:
    """Turns a readable event or perk name into the bytes32 id used on-chain."""
    return Web3.keccak(text=name)


@dataclass
class Roles:
    admin: str  # "IE": issues passes, creates events and perks
    gate: str   # the door / scanner device


class CampusChain:
    def __init__(self, w3: Web3, roles: Roles, contracts: dict):
        self.w3 = w3
        self.roles = roles
        self.pass_ = contracts["StudentPass"]
        self.token = contracts["CampusToken"]
        self.checkin = contracts["EventCheckIn"]
        self.perks = contracts["Perks"]

    # ---------- setup ----------
    @classmethod
    def deploy(cls, w3: Web3, roles: Roles) -> "CampusChain":
        """Deploys all contracts and wires up their permissions."""
        def deploy_one(name, *args):
            art = _artifact(name)
            factory = w3.eth.contract(abi=art["abi"], bytecode=art["bytecode"])
            receipt = w3.eth.wait_for_transaction_receipt(
                factory.constructor(*args).transact({"from": roles.admin})
            )
            return w3.eth.contract(address=receipt.contractAddress, abi=art["abi"])

        p = deploy_one("StudentPass", roles.admin)
        t = deploy_one("CampusToken", roles.admin, p.address)
        c = deploy_one("EventCheckIn", roles.admin, p.address, t.address)
        k = deploy_one("Perks", roles.admin, p.address, t.address)

        chain = cls(w3, roles, {"StudentPass": p, "CampusToken": t, "EventCheckIn": c, "Perks": k})
        chain._tx(t.functions.grantRole(t.functions.MINTER_ROLE().call(), c.address), roles.admin)
        chain._tx(t.functions.grantRole(t.functions.SPENDER_ROLE().call(), k.address), roles.admin)
        chain._tx(c.functions.grantRole(c.functions.GATE_ROLE().call(), roles.gate), roles.admin)
        return chain

    @classmethod
    def connect(cls, w3: Web3, roles: Roles, addresses: dict) -> "CampusChain":
        """Connects to contracts that are already deployed (e.g. on Base Sepolia)."""
        contracts = {n: w3.eth.contract(address=a, abi=_artifact(n)["abi"]) for n, a in addresses.items()}
        return cls(w3, roles, contracts)

    def addresses(self) -> dict:
        return {
            "StudentPass": self.pass_.address,
            "CampusToken": self.token.address,
            "EventCheckIn": self.checkin.address,
            "Perks": self.perks.address,
        }

    def _tx(self, fn, sender: str):
        return self.w3.eth.wait_for_transaction_receipt(fn.transact({"from": sender}))

    # ---------- Student Pass (IE) ----------
    def issue_pass(self, wallet: str):
        return self._tx(self.pass_.functions.issue(wallet), self.roles.admin)

    def revoke_pass(self, wallet: str):
        return self._tx(self.pass_.functions.revoke(wallet), self.roles.admin)

    def is_valid(self, wallet: str) -> bool:
        return self.pass_.functions.isValid(wallet).call()

    # ---------- events (student government, talks.) ----------
    def create_event(self, name: str, reward: int):
        return self._tx(self.checkin.functions.createEvent(to_id(name), reward), self.roles.admin)

    def already_checked_in(self, event: str, wallet: str) -> bool:
        return self.checkin.functions.checkedIn(to_id(event), wallet).call()

    def check_in(self, event: str, wallet: str):
        """Called by the gate after the face was matched off-chain."""
        return self._tx(self.checkin.functions.checkIn(to_id(event), wallet), self.roles.gate)

    def reputation(self, wallet: str) -> int:
        return self.checkin.functions.reputation(wallet).call()

    # ---------- tokens ----------
    def balance(self, wallet: str) -> int:
        return self.token.functions.balanceOf(wallet).call()

    def total_supply(self) -> int:
        return self.token.functions.totalSupply().call()

    def send(self, sender: str, to: str, amount: int):
        return self._tx(self.token.functions.transfer(to, amount), sender)

    # ---------- perks ----------
    def create_perk(self, name: str, price: int, supply: int):
        return self._tx(self.perks.functions.createPerk(to_id(name), price, supply), self.roles.admin)

    def unlock_perk(self, name: str, student: str):
        return self._tx(self.perks.functions.unlock(to_id(name)), student)

    def has_perk(self, name: str, wallet: str) -> bool:
        return self.perks.functions.hasPerk(to_id(name), wallet).call()

    def perk_remaining(self, name: str) -> int:
        return self.perks.functions.remaining(to_id(name)).call()
