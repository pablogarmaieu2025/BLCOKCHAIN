"""End-to-end demo on a local, in-memory blockchain (no internet, no real money).

Run:  python demo.py
"""
from web3 import EthereumTesterProvider, Web3

from gateway import CampusChain, DemoFaceMatcher, Door, Roles, StudentRegistry


def step(title):
    print(f"\n=== {title} ===")


def show(result):
    mark = "OPEN  " if result.granted else "DENIED"
    extra = f" (+{result.tokens_earned} tokens)" if result.tokens_earned else ""
    print(f"  [{mark}] {result.student_id or 'unknown'}: {result.reason}{extra}")


def main():
    w3 = Web3(EthereumTesterProvider())
    ie, gate, sara, marco, lucas, outsider = w3.eth.accounts[:6]

    step("1. IE deploys the system")
    chain = CampusChain.deploy(w3, Roles(admin=ie, gate=gate))
    for name, addr in chain.addresses().items():
        print(f"  {name:<13} {addr}")

    step("2. IE verifies three students and issues their passes")
    matcher, registry = DemoFaceMatcher(), StudentRegistry()
    for sid, wallet in [("sara", sara), ("marco", marco), ("lucas", lucas)]:
        matcher.enroll(sid, f"{sid}-enrolment-photo")  # face stays local
        registry.register(sid, wallet)                   # off-chain, kept by IE
        chain.issue_pass(wallet)                         # on-chain: wallet only
        print(f"  pass issued to {sid} ({wallet[:10]}...)")

    door = Door(chain, matcher, registry)

    step("3. Students scan in at the campus door")
    show(door.scan("sara-morning-photo"))
    show(door.scan("stranger-photo"))

    step("4. Student government runs events; check-ins earn tokens")
    for event in ["SG debate", "Climate talk", "Hackathon"]:
        chain.create_event(event, reward=100)
    show(door.scan("sara-debate", event="SG debate"))
    show(door.scan("sara-again", event="SG debate"))  # no double reward
    show(door.scan("sara-climate", event="Climate talk"))
    show(door.scan("sara-hack", event="Hackathon"))
    show(door.scan("marco-debate", event="SG debate"))
    print(f"  balances: sara={chain.balance(sara)}, marco={chain.balance(marco)}")
    print(f"  reputation (check-ins): sara={chain.reputation(sara)}, marco={chain.reputation(marco)}")

    step("5. talks. offers a scarce perk: early access to the exam-week party")
    perk = "Exam-week party early access"
    chain.create_perk(perk, price=200, supply=50)
    chain.unlock_perk(perk, sara)
    print(f"  sara unlocked it: {chain.has_perk(perk, sara)}; sara now has {chain.balance(sara)} tokens")
    print(f"  spots left: {chain.perk_remaining(perk)} of 50")
    try:
        chain.unlock_perk(perk, marco)
    except Exception:
        print("  marco tried with 100 tokens: refused (not enough tokens)")

    step("6. Tokens move between students, but never outside the network")
    chain.send(sara, marco, 50)
    print(f"  sara sent 50 to marco: sara={chain.balance(sara)}, marco={chain.balance(marco)}")
    try:
        chain.send(sara, outsider, 10)
    except Exception:
        print("  sara tried to send 10 to a non-student wallet: refused (closed network)")

    step("7. Lucas loses his phone; IE revokes his pass")
    show(door.scan("lucas-photo"))
    chain.revoke_pass(lucas)
    show(door.scan("lucas-photo"))

    step("8. Anyone can verify the supply")
    print(f"  minted 400, burned 200 -> total supply on-chain: {chain.total_supply()}")


if __name__ == "__main__":
    main()
