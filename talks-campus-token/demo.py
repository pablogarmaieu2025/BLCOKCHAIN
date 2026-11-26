"""Unified synthetic demo. No real biometrics, funds, physical door or public deployment."""
from web3 import EthereumTesterProvider, Web3
from gateway import CampusChain, Door, Roles, StudentRegistry
from veil import TeammateFaceMatcher, templates
import numpy as np

class DemoCampus:
    def __init__(self):
        self.w3 = Web3(EthereumTesterProvider())
        self.admin, self.gate, self.sara, self.marco, self.lucas, self.outsider, self.recovery = self.w3.eth.accounts[:7]
        self.chain = CampusChain.deploy(self.w3, Roles(self.admin, self.gate))
        self.registry = StudentRegistry()
        self.matcher = TeammateFaceMatcher()
        self.rng = np.random.default_rng(42)
        self.raw = {}
        self.door = Door(self.chain, self.matcher, self.registry)
        for sid, wallet, seed in [("sara", self.sara, 11), ("marco", self.marco, 29), ("lucas", self.lucas, 47)]:
            self.enroll(sid, wallet, seed)
        self.events = ["SG debate", "Climate talk", "Hackathon"]
        for event in self.events:
            self.chain.create_event(event, 100)
        self.perk = "Priority talks ticket"
        self.chain.create_perk(self.perk, 200, 50)

    def enroll(self, sid, wallet, seed):
        raw = templates.simulated_template(seed)
        record = self.registry.register(sid, wallet)
        self.chain.issue_pass(wallet, record.key)
        self.matcher.enroll(sid, raw)
        self.raw[sid] = raw

    def scan(self, sid, event=None):
        raw = self.raw[sid] if sid in self.raw else templates.simulated_template(999)
        return self.door.scan(templates.live_capture(raw, rng=self.rng), event)

    def revoke(self, sid):
        # Two independent simulated state stores: no atomic cross-store transaction.
        # Revoke the EVM credential first so rewards are denied even if step two fails.
        self.chain.revoke_pass(self.registry.wallet_of(sid))
        self.matcher.revoke(sid)

def main():
    campus = DemoCampus()
    chain = campus.chain
    print("Veil x talks V2 | synthetic vectors | local EVM")
    print("Contracts:", chain.addresses())
    for sid, event in [("unknown", None), ("sara", None), ("sara", "SG debate"),
                       ("sara", "SG debate"), ("sara", "Climate talk"), ("sara", "Hackathon"),
                       ("marco", "SG debate")]:
        result = campus.scan(sid, event)
        print(sid, event, result)
    receipt = chain.unlock_perk(campus.perk, campus.sara)
    print("Redemption transaction:", receipt.transactionHash.hex())
    print("Sara balance:", chain.balance(campus.sara), "reputation:", chain.reputation(campus.sara))
    print("Remaining perks:", chain.perk_remaining(campus.perk))
    campus.revoke("lucas")
    print("Revoked student:", campus.scan("lucas"))
    print("Total supply:", chain.total_supply(), "lifetime minted:", chain.token.functions.lifetimeMinted().call())
    assert chain.total_supply() == 200
    assert chain.balance(campus.sara) == 100
    assert chain.perk_remaining(campus.perk) == 49

if __name__ == "__main__":
    main()
