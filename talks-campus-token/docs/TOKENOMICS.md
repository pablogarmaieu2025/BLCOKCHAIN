# TALK economics (proposed V2 parameters)

TALK is an application reward and access token, not a stablecoin, investment,
legal entitlement to a ticket, or native gas asset. Genesis issuance is zero.
Only the configured check-in contract initially has the mint role, and the
admin can alter role assignments. Each event has capacity, expiry, scoped gates
and a reward between 1 and 1,000. Lifetime issuance is capped at 1,000,000 TALK;
burns do not replenish the issuance budget. Demo reward: 100, perk cost: 200.

Supply identity: S(t+1) = S(t) + sum of event rewards - sum of redemption costs.
Transfers and same-subject recovery conserve supply. Lifetime minted is separately
observable. Participation reputation is nontransferable and survives recovery.
TALK transfers require active sender and recipient; transfers can create informal
markets and weaken personal attendance incentives. Retained for prototype
compatibility; the team should decide whether to disable them.

Example monthly scenario: 500 students x 4 eligible events x 100 = 200,000 issued.
200 redemptions x 200 = 40,000 burned. Net growth 160,000. At that pace the
lifetime issuance budget is exhausted after five months, even if burns occur.
This cap is an illustrative design decision, not a requirement or sustainable
long-term monetary policy. A production program would budget rewards against
available perks, measured demand and cohort fairness, and revisit the cap through
explicit governance. No speculative market or DEX is necessary.

Success metrics: legitimate participation uplift vs baseline, redemption rate,
repeat usage after rewards decline, inventory utilization and cost per incremental
participant. Token scarcity is not proof of product-market fit.
