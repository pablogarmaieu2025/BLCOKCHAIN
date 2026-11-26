"""Reproducible synthetic experiment: ideal Gaussian projection, not biometric FAR/FRR."""
import argparse
import csv
import math
from pathlib import Path
import numpy as np

DIMENSIONS = (32, 64, 96, 128)
DISTANCES = (0.50, 0.55, 0.575, 0.60, 0.625, 0.65, 0.70)


def chi2_cdf_even(x, k):
    """Exact chi-square CDF for positive even degrees of freedom."""
    if k <= 0 or k % 2 or x < 0:
        raise ValueError("Need positive even k and nonnegative x")
    z = x / 2
    return min(1.0, max(0.0, 1 - math.exp(-z) * sum(z**j / math.factorial(j) for j in range(k // 2))))


def experiment(samples=50000, seed=20261126, threshold=0.6):
    if samples < 1 or threshold <= 0:
        raise ValueError("Positive samples and threshold required")
    rng = np.random.default_rng(seed)
    for k in DIMENSIONS:
        # For a fixed nonzero difference vector, Gaussian rotational invariance
        # gives ||M delta|| / ||delta|| = sqrt(chi-square(k)/k).
        # Draw squared Gaussian coordinates directly, equivalent to projecting delta.
        ratio = np.sqrt(np.sum(rng.standard_normal((samples, k))**2, axis=1) / k)
        for d in DISTANCES:
            original_accept = d <= threshold
            projected_accept = d * ratio <= threshold
            flips = projected_accept != original_accept
            rate = float(np.mean(flips))
            cdf = chi2_cdf_even(k * (threshold / d)**2, k)
            theory = 1 - cdf if original_accept else cdf
            yield {"dimensions": k, "distance": d, "threshold": threshold,
                   "direction": "accept_to_reject" if original_accept else "reject_to_accept",
                   "samples": samples, "seed": seed, "flip_rate": rate,
                   "theory": theory, "mc_se": math.sqrt(rate * (1-rate) / samples)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=50000)
    parser.add_argument("--seed", type=int, default=20261126)
    parser.add_argument("--threshold", type=float, default=0.6)
    parser.add_argument("--output", type=Path, default=Path("results/projection.csv"))
    args = parser.parse_args()
    rows = list(experiment(args.samples, args.seed, args.threshold))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        if row["dimensions"] == 64:
            print(f'd={row["distance"]:.3f}: simulated {row["flip_rate"]:.2%}; theory {row["theory"]:.2%}')
    print(f"Saved {len(rows)} scenarios to {args.output}. Synthetic projection distortion only.")


if __name__ == "__main__":
    main()
