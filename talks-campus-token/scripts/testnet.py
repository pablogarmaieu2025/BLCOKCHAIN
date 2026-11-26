"""Deploy contracts with an externally supplied disposable Base Sepolia key.
No real student data. No secrets in output or repository.
Run from project root: python scripts/testnet.py
"""
import json
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web3 import Web3
from web3.middleware import SignAndSendRawMiddlewareBuilder
from eth_account import Account
from gateway import CampusChain, Roles

def main():
    rpc = os.environ["BASE_SEPOLIA_RPC_URL"]
    admin = Account.from_key(os.environ["TESTNET_ADMIN_KEY"])
    gate = Account.from_key(os.environ["TESTNET_GATE_KEY"])
    if admin.address == gate.address:
        raise ValueError("Use separate disposable admin and gate accounts")
    w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 30}))
    if not w3.is_connected() or w3.eth.chain_id != 84532:
        raise RuntimeError("Expected Base Sepolia, chain ID 84532")
    if not w3.eth.get_balance(admin.address) or not w3.eth.get_balance(gate.address):
        raise RuntimeError("Fund both disposable accounts with test ETH first")
    w3.middleware_onion.inject(SignAndSendRawMiddlewareBuilder.build([admin, gate]), layer=0)
    chain = CampusChain.deploy(w3, Roles(admin.address, gate.address))
    manifest = {"chainId": w3.eth.chain_id, "admin": admin.address, "gate": gate.address,
                "contracts": chain.addresses(), "block": w3.eth.block_number}
    target = Path("deployments/base-sepolia.json")
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
