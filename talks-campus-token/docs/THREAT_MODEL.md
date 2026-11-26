# Scope and security limitations

Classroom prototype, not a security audit or approved biometric deployment.

- Registrar is trusted to verify one real student per random subject key; contracts
  cannot infer human uniqueness. Public subject keys, addresses and event hashes
  are linkable. Event IDs hashed from predictable names are not confidential.
- Authorized event gate is an oracle, not a proof of physical presence. Compromised
  authorized gate can falsely attest participation within event and issuance limits.
  No live-camera, liveness, secure hardware, signed phone challenge or anti-spoofing.
- Veil projection is dimension reduction, not proven cryptographic irreversibility.
  AES-GCM protects ciphertext under key secrecy. Shamir 2-of-3 sharing is simulated:
  all shares and the wallet can coexist in the local Python process. No actual
  HSM, independent vault, physical phone, network isolation, or distributed consensus.
  The Python HMAC ledger is a tamper-detection demonstration under trusted keys,
  not a Byzantine-fault-tolerant chain. Access proof strings are not ZK proofs.
- Matching searches a small in-memory list of synthetic wallets. Threshold 0.6 is
  uncalibrated on real faces. No measured FAR/FRR. Do not upload real biometric data.
- Credential revocation across the local Veil store and EVM is not atomic. EVM
  pass revocation is performed first. The registry is in-memory and not durable.
  Recovery of balances is privileged and separate from pass replacement; failure
  requires reconciliation. No real lost-device recovery without fresh authentication.
- Admin can grant roles and approve wallet replacement. No deployed multisig,
  emergency pause, independent organizers or audited key custody. Local UI tabs
  are not an access control boundary. Use separate accounts in testnet deployment.
- Receipt success is not finality. An RPC timeout can leave transaction status
  ambiguous. Check chain state before retry. No reorg handling, RPC failover,
  transaction queue, fee sponsorship or production operations.
- Public testnet must use synthetic identities and event labels only. Do not put
  biometric templates, real student identifiers or keys on-chain or in logs.
- Scarce perks are on-chain claims only. Organizers must actually deliver benefits.
- GDPR/MiCA applicability is fact-specific. No production legal compliance claim;
  real pilot needs institutional permission, necessity/proportionality evaluation,
  appropriate lawful basis and safeguards, and accessible non-biometric alternatives.

Baseline alternative: an IE-only SQL database is likely simpler and more private.
A shared ledger is justified only if independent organizers or institutions need
shared, auditable issuance and redemption rules. This is a hypothesis to validate.
