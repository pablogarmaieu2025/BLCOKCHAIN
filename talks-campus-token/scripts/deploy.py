"""Signed deployment rehearsal / explicit Base Sepolia deployment (synthetic only).
Adapted from the teammate's deploy.py; V2 contracts and separate signers retained.
No public transaction is sent without --base-sepolia.
"""
import argparse
import hashlib
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eth_account import Account
from web3 import EthereumTesterProvider, Web3
from web3.middleware import SignAndSendRawMiddlewareBuilder
from gateway import CampusChain, Roles, to_id

BASE_CHAIN = 84532
EXPLORER = "https://sepolia.basescan.org"

def load_env(path):
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                if key.strip() in {"BASE_SEPOLIA_RPC_URL", "TESTNET_ADMIN_KEY", "TESTNET_GATE_KEY", "TESTNET_STUDENT_KEY"}:
                    os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

def connect(local, smoke):
    if local:
        w3 = Web3(EthereumTesterProvider())
        admin, gate, student = (Account.create() for _ in range(3))
        for account in (admin, gate, student):
            receipt = w3.eth.wait_for_transaction_receipt(w3.eth.send_transaction({
                "from": w3.eth.accounts[0], "to": account.address, "value": w3.to_wei(1, "ether")}))
            if receipt.status != 1:
                raise RuntimeError("Local funding failed")
    else:
        load_env(ROOT / ".env")
        w3 = Web3(Web3.HTTPProvider(os.environ.get("BASE_SEPOLIA_RPC_URL", "https://sepolia.base.org"), request_kwargs={"timeout": 60}))
        if not w3.is_connected() or w3.eth.chain_id != BASE_CHAIN:
            raise RuntimeError("Expected Base Sepolia (84532)")
        admin = Account.from_key(os.environ["TESTNET_ADMIN_KEY"])
        gate = Account.from_key(os.environ["TESTNET_GATE_KEY"])
        student = Account.from_key(os.environ["TESTNET_STUDENT_KEY"]) if smoke else None
    accounts = [a for a in (admin, gate, student) if a is not None]
    if len({a.address for a in accounts}) != len(accounts):
        raise ValueError("Use distinct disposable signing accounts")
    if any(w3.eth.get_balance(a.address) == 0 for a in accounts):
        raise RuntimeError("All signing accounts need test ETH; estimate fees before deploying")
    w3.middleware_onion.inject(SignAndSendRawMiddlewareBuilder.build(accounts), layer=0)
    return w3, admin, gate, student

def receipt_record(receipt, explorer=None):
    tx = Web3.to_hex(receipt.transactionHash)
    return {"hash": tx, "block": receipt.blockNumber, "status": receipt.status,
            "explorer": f"{explorer}/tx/{tx}" if explorer else None}

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def run(local, seed=False, smoke=False, out=None):
    seed = seed or smoke
    name = "local-practice" if local else "base-sepolia"
    out = Path(out) if out is not None else ROOT / "deployments" / f"{name}.json"
    if not local and out.exists():
        raise FileExistsError("Public manifest exists; archive it before another deployment")
    build = ROOT / "build"
    compiler = (build / "compiler.txt").read_text().strip()
    standard_hash = hashlib.sha256((build / "standard-input.json").read_bytes()).hexdigest()
    w3, admin, gate, student = connect(local, smoke)
    explorer = None if local else EXPLORER
    chain = CampusChain.deploy(w3, Roles(admin.address, gate.address))
    addresses = chain.addresses()
    require(all(w3.eth.get_code(addr) for addr in addresses.values()), "Missing deployed code")
    require(chain.pass_.functions.hasRole(chain.pass_.functions.ISSUER_ROLE().call(), admin.address).call(), "Issuer missing")
    require(chain.token.functions.hasRole(chain.token.functions.MINTER_ROLE().call(), addresses["EventCheckIn"]).call(), "Minter missing")
    require(chain.token.functions.hasRole(chain.token.functions.SPENDER_ROLE().call(), addresses["Perks"]).call(), "Spender missing")
    require(chain.checkin.functions.hasRole(chain.checkin.functions.GATE_ROLE().call(), gate.address).call(), "Gate missing")
    require(chain.total_supply() == 0, "Unexpected initial supply")
    args = {
        "StudentPass": [admin.address],
        "CampusToken": [admin.address, addresses["StudentPass"]],
        "EventCheckIn": [admin.address, addresses["StudentPass"], addresses["CampusToken"]],
        "Perks": [admin.address, addresses["StudentPass"], addresses["CampusToken"]],
    }
    record = {"network": name, "chain_id": w3.eth.chain_id, "ephemeral": local,
              "deployed_at": datetime.now(timezone.utc).isoformat(), "admin": admin.address, "gate": gate.address,
              "compiler": compiler, "standard_input_sha256": standard_hash,
              "contracts": {n: {"address": addr, "source": f"contracts/{n}.sol:{n}",
                               "constructor_args": w3.codec.encode(["address"] * len(args[n]), args[n]).hex(),
                               "explorer": f"{explorer}/address/{addr}" if explorer else None,
                               "deployment": receipt_record(chain.deployment_receipts[n], explorer)}
                            for n, addr in addresses.items()},
              "transactions": [], "seeded": False, "smoke_passed": False}
    def save():
        record["transactions"] = [receipt_record(r, explorer) for r in chain.receipts]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(record, indent=2) + "\n")
    # Persist addresses before any optional seeding; retain partial setup evidence on failure.
    save()
    try:
        if seed:
            for event in ("Demo debate", "Demo workshop"):
                chain.create_event(event, 100, capacity=20)
                require(chain.checkin.functions.authorizedGate(to_id(event), gate.address).call(), "Gate not authorized for event")
            chain.create_perk("Demo priority ticket", 200, 20)
            record["seeded"] = True
        if smoke:
            # Same Veil -> Door -> EVM flow, using the third locally signed account.
            from veil import TeammateFaceMatcher, templates
            from gateway import Door, StudentRegistry
            import numpy as np
            registry = StudentRegistry()
            sid = "synthetic-demo"
            raw = templates.simulated_template(11)
            subject = registry.register(sid, student.address)
            chain.issue_pass(student.address, subject.key)
            matcher = TeammateFaceMatcher()
            matcher.enroll(sid, raw)
            door = Door(chain, matcher, registry)
            rng = np.random.default_rng(42)
            def scan(event):
                return door.scan(templates.live_capture(raw, rng=rng), event)
            require(scan("Demo debate").tokens_earned == 100, "First check-in failed")
            duplicate = scan("Demo debate")
            require(duplicate.granted and duplicate.tokens_earned == 0, "Duplicate check failed")
            require(scan("Demo workshop").tokens_earned == 100, "Second check-in failed")
            require(chain.balance(student.address) == 200, "Incorrect reward balance")
            chain.unlock_perk("Demo priority ticket", student.address)
            require(chain.total_supply() == 0 and chain.reputation(student.address) == 2, "Accounting mismatch")
            require(chain.perk_remaining("Demo priority ticket") == 19, "Inventory mismatch")
            record["smoke_passed"] = True
            record["smoke"] = {"student": student.address, "lifetime_minted": 200, "burned": 200, "outstanding": 0, "remaining": 19}
    finally:
        save()
    return record

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--local", action="store_true")
    mode.add_argument("--base-sepolia", action="store_true")
    parser.add_argument("--seed", action="store_true")
    parser.add_argument("--smoke", action="store_true", help="seed, authenticate synthetic student, earn and redeem")
    args = parser.parse_args()
    record = run(args.local, args.seed, args.smoke)
    print(json.dumps(record, indent=2))
    print("Manifest saved. Local addresses expire with the process; public verification is a separate step.")

if __name__ == "__main__":
    main()
