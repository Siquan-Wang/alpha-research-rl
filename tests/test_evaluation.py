import numpy as np
import pytest

from alpha_research_rl.data import MarketPanel, make_synthetic_panel
from alpha_research_rl.evaluation import forward_returns, score_factor


def test_forward_label_alignment_and_unavailable_tail():
    close = np.array([[1, 2, 4], [2, 3, 5], [4, 7, 6], [8, 9, 8]], dtype=float)
    realized = np.full_like(close, np.nan)
    realized[1:] = close[1:] / close[:-1] - 1
    panel = MarketPanel(close, np.ones_like(close), realized,
                        np.arange("2000-01-01", "2000-01-05", dtype="datetime64[D]"), ("A", "B", "C"))
    labels = forward_returns(panel, horizon=2)
    np.testing.assert_array_equal(labels[:2], close[2:] / close[:-2] - 1)
    assert np.isnan(labels[-2:]).all()
    # A row's label begins at its own close, not at the previous realized return.
    np.testing.assert_allclose(forward_returns(panel, 1)[:-1], realized[1:])
    assert np.isnan(forward_returns(panel, 5)).all()


@pytest.mark.parametrize("horizon", [0, -1, True, 1.5])
def test_invalid_horizon_rejected(horizon):
    with pytest.raises(ValueError):
        forward_returns(make_synthetic_panel(n_dates=6, n_assets=4), horizon)


def test_spearman_ties_half_open_interval_and_missing_pairs():
    x = np.array([[1, 2, 2, 4], [4, 3, 2, 1], [1, 2, 3, np.nan], [1, 2, 3, 4]])
    y = np.array([[10, 20, 20, 40], [1, 2, 3, 4], [3, 2, 1, 0], [1, 2, 3, 4]])
    result = score_factor(x, y, 0, 3)
    np.testing.assert_allclose(result["daily_ic"], [1, -1, -1])
    assert result["mean_ic"] == pytest.approx(-1 / 3)
    assert result["coverage"] == pytest.approx(11 / 12)
    assert result["n_dates"] == 3
    assert result["n_signal_dates"] == 3
    assert result["ic_std"] == pytest.approx(np.std([1, -1, -1], ddof=1))


def test_constants_insufficient_assets_and_empty_interval_are_explicit():
    x = np.array([[1, 1, 1, 1], [1, 2, np.nan, np.nan], [1, 2, 3, 4]])
    y = np.array([[1, 2, 3, 4], [4, 3, 2, 1], [2, 2, 2, 2]])
    result = score_factor(x, y, 0, 3)
    assert result["daily_ic"] == [None, None, None]
    assert result["n_dates"] == 0
    assert result["coverage"] == pytest.approx(10 / 12)
    assert np.isnan(result["mean_ic"]) and np.isnan(result["ic_std"])
    empty = score_factor(x, y, 2, 2)
    assert empty["coverage"] == 0 and empty["n_dates"] == 0
    assert empty["daily_ic"] == []


def test_single_valid_day_has_zero_descriptive_std():
    result = score_factor(np.array([[1, 2, 3]]), np.array([[1, 2, 3]]), 0, 1)
    assert result["ic_std"] == 0
    assert result["mean_ic"] == pytest.approx(1)


@pytest.mark.parametrize("start,stop", [(-1, 3), (3, 2), (0, 5), (0.0, 2), (False, 2)])
def test_invalid_score_intervals_rejected(start, stop):
    with pytest.raises(ValueError):
        score_factor(np.ones((4, 3)), np.ones((4, 3)), start, stop)
