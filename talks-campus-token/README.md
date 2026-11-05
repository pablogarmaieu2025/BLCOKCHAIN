# talks. Campus Token

One verified **Student Pass** and one **campus token** for IE University.
The pass gets you through the door and checks you in at events; every check-in
earns tokens; tokens buy scarce perks such as early access to a sold-out
talks. event. Faces never go on the blockchain.

Status (Nov 2026): first working version. Runs on a local test blockchain.
Not yet deployed to a public test network. Face recognition is a stand-in
until the biometric code is plugged in.

---

## Quick start (macOS, conda)

```bash
conda create -n talks-token python=3.12 nodejs -y
conda activate talks-token
npm install                         # Solidity compiler + OpenZeppelin
pip install -r requirements.txt     # web3 + local test chain + pytest
npm run compile                     # contracts/ -> build/*.json
python demo.py                      # full story, end to end
python -m pytest -q                 # 16 tests
```

## What's in the repo

| Path | What it is |
| --- | --- |
| `contracts/StudentPass.sol` | One non-transferable pass per verified student. Issue, revoke, `isValid`. No personal or biometric data. |
| `contracts/CampusToken.sol` | The token (`TALK`, whole units). Only wallets with a valid pass can receive it (closed network). |
| `contracts/EventCheckIn.sol` | Organisers create events; gates check students in once per event; pays the reward and counts reputation. |
| `contracts/Perks.sol` | Scarce perks with a public supply. `unlock` burns the price. |
| `gateway/chain.py` | Python wrapper around the four contracts. The only file that talks to web3. |
| `gateway/identity.py` | `FaceMatcher` interface + `DemoFaceMatcher` stand-in. **The biometric plug-in point.** |
| `gateway/teammate_face_matcher.py` | Template for the real face recognition code. |
| `gateway/registry.py` | Student id → wallet. Off-chain, kept by IE. |
| `gateway/door.py` | The door: face → student → wallet → pass check → tokens. |
| `demo.py` | The whole story on a local chain. |
| `tests/test_system.py` | 16 tests: every rule and every refusal. |

## How it fits together

```
  camera image
      |
      v
  FaceMatcher.identify()        LOCAL device only (templates never leave it)
      |  student id
      v
  StudentRegistry.wallet_of()   OFF-chain, kept by IE
      |  wallet address
      v
  StudentPass.isValid()         ON-chain  -> door opens or stays shut
      |
      v
  EventCheckIn.checkIn()        ON-chain  -> +reward tokens, +1 reputation
      |
      v
  Perks.unlock()                ON-chain  -> tokens burned, perk recorded
```

Roles (permissions enforced by the contracts):

| Role | Who | Can |
| --- | --- | --- |
| Issuer / admin | IE | Issue and revoke passes, create events and perks |
| Gate | Door / event scanner device | Check students in (nothing else) |
| EventCheckIn contract | — | Mint tokens (nothing else can) |
| Perks contract | — | Burn tokens when a perk is unlocked |
| Student | Pass holder | Send tokens to other students, unlock perks |

## Merging the face recognition (for the biometric teammate)

The door needs exactly one answer from your code: **"which student is this?"**

1. Open `gateway/teammate_face_matcher.py` and fill in two methods:
   - `enroll(student_id, image)`: store the face template **locally**.
   - `identify(image)`: return the matching `student_id`, or `None`.
2. Use **face embeddings and a distance threshold**, not hashes. Two photos of
   the same face never produce the same hash, so hash comparison always fails.
3. Swap it in: `Door(chain, TeammateFaceMatcher(), registry)` instead of
   `DemoFaceMatcher()`. Nothing else changes.
4. Add a test in `tests/` with two photos of the same person and one of
   someone else.

Rules: never write images or templates to the chain, the registry or any server.

## Known future problems (most important first)

1. **Face matching should move to the phone.** Today it runs on the door laptop.
   The target design: the phone matches the face and signs the door's challenge
   (like a passkey), so no device but the student's own ever holds a template.
2. **Biometrics are legally high-risk in Spain.** The AEPD treats biometric access
   control as high-risk processing of special-category data; a real rollout needs
   a data protection impact assessment. For the class: volunteers only, with consent.
3. **Photo spoofing.** A simple matcher can be fooled by a printed photo. Needs
   liveness detection before any real use.
4. **Gas fees.** Students need a little test currency to unlock perks. Fix: the
   project pays fees for them (account abstraction / paymaster on Base).
5. **Gate key security.** If a door's key is stolen, it could check in any pass
   holder. Limits today: once per event, only active events. Later: one key per
   device, quick revocation.
6. **Attendance is visible on-chain.** `CheckedIn` events show that a wallet
   attended an event. Wallets aren't names, but patterns can identify people.
   Later: hide event ids or use zero-knowledge proofs.
7. **IE's admin key controls everything.** Later: a multisig shared by IE and
   student government.
8. **talks. is not our app.** Real integration and any pilot need the founder's permission.

## Next steps

- [ ] Deploy to Base Sepolia test network (`CampusChain.connect` is ready for it)
- [ ] Plug in the real face matcher (see above)
- [ ] Simple web page for students: balance, perks, unlock button
- [ ] Live class demo: classmates scan in, earn and spend
