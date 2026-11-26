# Veil × talks. V2

A classroom prototype for authenticated campus participation and programmable
rewards. Original V1 remains on main. This branch integrates both team prototypes.

## Run locally (Python 3.12, Node 20 recommended)

From this directory:

```sh
python -m venv .venv
source .venv/bin/activate
npm ci
python -m pip install -r requirements.txt
npm run compile
python demo.py
python -m pytest -q tests veil-python/tests
streamlit run app.py
```

Windows: activate .venv using the platform-specific activation script.
The app is a trusted, ephemeral classroom simulation with synthetic identities.
Do not upload faces or use real funds. No public deployment is claimed.

## Classroom walkthrough

The CLI and Streamlit each start their own fresh local chain. In the app, open
Event scanner, select Sara and SG debate, then Authenticate and check in (100 TALK).
Repeat the same event (0 extra), then scan Climate talk (200 total). Open Student
and redeem the priority ticket (0 balance, 49 remaining). Evidence shows 200 minted,
200 burned and 0 outstanding if no other rewards were issued. In Administrator,
revoke Sara and attempt another scan: no reward. Reset clears this local session.

## Architecture

Veil synthetic vector -> protected template comparison -> local student registry
-> StudentPass eligibility -> event-scoped authorized gate -> EventCheckIn ->
TALK issuance and reputation -> Perks redemption and burn.

Four Solidity contracts implement application state. Veil's separate HMAC-linked
Python ledger simulates biometric credential commitments; it is not a real
distributed network and no cross-chain bridge is needed. The local EVM is also
a test environment. An Ethereum signing account is distinct from a Veil wallet.

## Files

- contracts/: StudentPass, CampusToken, EventCheckIn, Perks.
- gateway/: registrar, transaction wrapper and door. DemoFaceMatcher is a unit test double only.
- veil-python/veil/: the biometric group's packaged experimental implementation.
- demo.py: integrated CLI entry point.
- gateway/demo_campus.py: uniquely named shared synthetic campus fixture.
- app.py: integrated Student, Event scanner, Administrator and Evidence tabs.
- tests/: contract and integrated regression suites.
- veil-python/tests/: biometric and simulated ledger tests.
- scripts/testnet.py: deployment preparation, not a deployment record.
- docs/TOKENOMICS.md and docs/THREAT_MODEL.md: design and explicit limitations.

## Testnet (optional, not executed)

Use disposable test-only keys, separate admin/gate accounts funded with test ETH.
Set BASE_SEPOLIA_RPC_URL, TESTNET_ADMIN_KEY and TESTNET_GATE_KEY securely in your
local environment. Never commit them, send them to chat or reuse real wallets.
Run python scripts/testnet.py after compilation. It checks chain ID 84532 and
writes a public-address-only deployment manifest. Inspect each contract and role
in an explorer. The classroom UI remains local; testnet student signing and
end-to-end testnet UI are not implemented. No deployment is required to run tests.

## Course defense

Session 2–3: authorization, state transitions, public vs permissioned applications,
oracle trust, explorer evidence and finality. Session 4: utility, reward, supply,
sources/sinks, distribution, farming and token necessity. Session 7: custody and
recovery; Shamir is not multisig. Session 8: privacy and regulatory uncertainty.
Sessions 10–12: shared institutional state, protocol-market fit, and admin governance.
Compare with SQL and ordinary points. Do not claim decentralization or biometric
security solely because blockchain/encryption are used.

## Status and acknowledgement

V2 is an AI-assisted implementation based on the team's V1 and project audit.
Students must inspect, run, understand, verify and acknowledge AI assistance per
the course syllabus. See the threat model before making presentation claims.
No real campus partnership, biometric performance or public deployment established.
