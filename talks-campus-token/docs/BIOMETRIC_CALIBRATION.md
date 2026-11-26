# Projection distortion — synthetic analysis (V2.1)

The teammate's 25 November archive identified the threshold distortion problem
and reported approximately 14–21% decision flips for distances 0.55–0.65.
This document extends that observation, not a reproduction of their unspecified
experiment. No real faces or biometric records are used.

## Model

For a fixed nonzero embedding difference delta in R^128, d = ||delta||.
The ideal random projection M has k rows with independent N(0,1/k) entries.
Then the projected distance D = ||M delta|| satisfies k D^2/d^2 ~ chi-square(k).
Squared distance is unbiased and its relative standard deviation is sqrt(2/k).
The implementation uses a deterministic pseudorandom matrix derived from each
salt. The ideal model averages over random matrices; it does not model the
distribution of real identities, repeated attempts at one fixed salt, or the
minimum across multiple enrolled candidates.

With threshold t = 0.6, a raw distance d <= t is accepted. For those pairs,
the probability of projection-induced rejection is 1-F_k(k(t/d)^2).
For d > t the probability of projection-induced acceptance is F_k(k(t/d)^2).
F_k is the chi-square CDF. The raw threshold is a reference decision, not
ground truth about whether two embeddings belong to the same person.

## Reproduce

Run from talks-campus-token:

    python scripts/calibration.py

This writes results/projection.csv: 28 scenarios, 50,000 Gaussian draws for
each dimension, seed 20261126. Same ratios are reused across distances within
each dimension (so rows are correlated). The CSV includes Monte Carlo standard
errors and exact even-degree chi-square CDF values. Increasing k usually
reduces distortion away from the boundary, but does not establish privacy.

Executed reference result (synthetic ideal model, k=64):

| Raw d | Monte Carlo flip | Analytic flip |
|---|---:|---:|
| 0.500 | 1.26% | 1.21% |
| 0.550 | 14.21% | 14.19% |
| 0.575 | 29.54% | 29.22% |
| 0.600 | 47.69% | 47.65% |
| 0.625 | 34.70% | 34.59% |
| 0.650 | 20.58% | 20.54% |
| 0.700 | 5.54% | 5.50% |

All 28 analytical probabilities were cross-checked against scipy.stats.chi2
to 1e-12 absolute tolerance in the development environment. All simulated rates
were within 1.5 percentage points of theory. SciPy is not required to run the script.

## Limits and next steps

The rates are decision-disagreement probabilities, not false acceptance or
false rejection rates, biometric accuracy, or proof of one-wayness. At d=0.6
the unprojected rule accepts exactly at the threshold, so even a small
upward distortion changes the decision. At k=128 the random matrix no longer
reduces dimension. Increasing k can reduce distortion without improving
privacy; a rank-deficient linear map is not inherently cryptographically secure.

The actual matcher still uses k=64 and t=0.6. No automatic recalibration was
made based on synthetic data. A future approved study would define genuine and
impostor trial distributions, use held-out validation, evaluate both error
rates and uncertainty by threshold and group, and consider spoofing and
accessibility. Do not collect student biometric data for the classroom demo.
