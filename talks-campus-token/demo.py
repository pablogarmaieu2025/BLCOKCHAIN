"""CLI entry point for the integrated synthetic campus demonstration."""
from gateway.demo_campus import DemoCampus

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
