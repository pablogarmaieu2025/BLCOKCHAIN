import math
from scripts.calibration import chi2_cdf_even, experiment

def test_chi_square_two_degrees():
    assert math.isclose(chi2_cdf_even(2, 2), 1 - math.exp(-1))

def test_projection_experiment_reproducible_and_consistent():
    rows = list(experiment(samples=20000, seed=123))
    assert rows == list(experiment(samples=20000, seed=123))
    assert len(rows) == 28
    assert all(abs(r["flip_rate"] - r["theory"]) < 0.025 for r in rows)
