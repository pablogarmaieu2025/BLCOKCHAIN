# Veil × talks. V2.1

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
- scripts/deploy.py: signed local rehearsal, optional explicit testnet deployment, seeding and public manifest.
- scripts/calibration.py: synthetic random-projection experiment.
- docs/BIOMETRIC_CALIBRATION.md and docs/CONTRIBUTIONS.md: mathematical analysis and provenance.
- docs/TOKENOMICS.md and docs/THREAT_MODEL.md: design and explicit limitations.

## Signed deployment rehearsal (no public transactions)

    npm run compile
    python scripts/deploy.py --local --smoke
    python scripts/calibration.py
    python -m pytest -q tests veil-python/tests

The rehearsal generates three distinct disposable local signing keys, deploys
and checks roles, seeds two events and a perk, runs Veil matching and check-ins,
rejects duplicate rewards and redeems a perk. Local manifest addresses are
ephemeral, not explorer links. It does not reuse the Streamlit chain.

## Public Base Sepolia (optional, not executed)

Use only disposable test wallets, funded with free test ETH. Copy .env.example
to .env locally and set separate TESTNET_ADMIN_KEY and TESTNET_GATE_KEY
(and TESTNET_STUDENT_KEY for --smoke). Never commit or share keys or use real
wallets. BASE_SEPOLIA_RPC_URL defaults to https://sepolia.base.org. Confirm that
you have sufficient test ETH for fees. Run the local rehearsal first.

    python scripts/deploy.py --base-sepolia --seed

Optional --smoke also executes synthetic check-ins and redemption on the testnet.
No public write occurs without the explicit --base-sepolia flag. A manifest
records addresses, deployment/setup receipts, compiler version, constructor
arguments and explorer links. A public manifest must be archived before another
deployment. If a deployment fails before a manifest exists, inspect account
transaction history before retrying; deployment/setup transactions are not atomic.

For each deployed contract, open its BaseScan address and use Verify & Publish
with Solidity Standard JSON Input, the exact build/compiler.txt version and
build/standard-input.json, the manifest's fully qualified source and encoded
constructor arguments if requested. The compiler exports all dependency sources
and checks that recompiling the input reproduces creation bytecode. Preserve
the exact artifacts used for deployment (manifest includes SHA-256 of JSON).
Explorer verification is manual and separate from successful deployment.
The UI remains a local simulation, not a testnet frontend.

## Course defense

Session 2–3: authorization, state transitions, public vs permissioned applications,
oracle trust, explorer evidence and finality. Session 4: utility, reward, supply,
sources/sinks, distribution, farming and token necessity. Session 7: custody and
recovery; Shamir is not multisig. Session 8: privacy and regulatory uncertainty.
Sessions 10–12: shared institutional state, protocol-market fit, and admin governance.
Compare with SQL and ordinary points. Do not claim decentralization or biometric
security solely because blockchain/encryption are used.

## Status and acknowledgement

V2.1 builds on V1, the tested V2 and the teammate's independent merge.
See docs/CONTRIBUTIONS.md for provenance and AI-assistance disclosure.
Students must inspect, run, understand, verify and acknowledge AI assistance per
the course syllabus. See the threat model before making presentation claims.
No real campus partnership, biometric performance or public deployment established.
