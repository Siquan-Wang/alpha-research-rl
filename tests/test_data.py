import csv

import numpy as np
import pytest

from alpha_research_rl.data import MarketPanel, load_panel_csv, make_synthetic_panel
from alpha_research_rl.dsl import evaluate_expression
from alpha_research_rl.evaluation import forward_returns, score_factor


def test_synthetic_reproducibility_identity_and_causal_prefix():
    panel = make_synthetic_panel(seed=19, n_dates=80, n_assets=8)
    repeated = make_synthetic_panel(seed=19, n_dates=80, n_assets=8)
    extended = make_synthetic_panel(seed=19, n_dates=100, n_assets=8)
    np.testing.assert_array_equal(panel.close, repeated.close)
    np.testing.assert_array_equal(panel.close, extended.close[:80])
    np.testing.assert_array_equal(panel.volume, extended.volume[:80])
    np.testing.assert_allclose(panel.returns[1:], panel.close[1:] / panel.close[:-1] - 1)
    assert np.isnan(panel.returns[0]).all()
    assert panel.metadata["synthetic"] is True
    assert "volume[t-1]/volume[t-2]" in panel.metadata["signal_equation"]


def test_observable_signal_and_null_are_distinct_development_controls():
    # This checks the advertised generator mechanism, not a financial alpha claim.
    scores = {}
    for regime in ("signal", "null", "decay"):
        panel = make_synthetic_panel(seed=7, n_dates=600, n_assets=32, regime=regime)
        factor = evaluate_expression("delta(log(volume),1)", panel)
        labels = forward_returns(panel, 1)
        scores[regime] = score_factor(factor, labels, 2, 599)["mean_ic"]
        if regime == "decay":
            first = score_factor(factor, labels, 2, 200)["mean_ic"]
            last = score_factor(factor, labels, 400, 599)["mean_ic"]
            assert first > last + 0.15
    assert scores["signal"] > 0.35
    assert abs(scores["null"]) < 0.05
    assert scores["null"] < scores["decay"] < scores["signal"]


def test_csv_roundtrip_exact_column_and_realized_return_identity(tmp_path):
    panel = make_synthetic_panel(seed=2, n_dates=12, n_assets=4)
    path = tmp_path / "panel.csv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["date", "asset", "close", "volume"])
        for t in reversed(range(12)):
            for j in reversed(range(4)):
                writer.writerow([str(panel.dates[t]), panel.assets[j], panel.close[t, j], panel.volume[t, j]])
    loaded = load_panel_csv(path)
    assert loaded.assets == panel.assets
    np.testing.assert_array_equal(loaded.dates, panel.dates)
    np.testing.assert_array_equal(loaded.close, panel.close)
    np.testing.assert_array_equal(loaded.volume, panel.volume)
    np.testing.assert_allclose(loaded.returns, panel.returns, equal_nan=True)
    assert loaded.metadata["source_file"] == "panel.csv"
    assert loaded.metadata["synthetic"] is None


@pytest.mark.parametrize("rows", [
    "2000-01-01,A,100,10\n2000-01-01,A,100,10\n",
    "2000-01-01,A,100,10\n2000-01-01,B,100,10\n2000-01-02,A,101,10\n",
    "2000-01-01,A,,10\n",
    "2000-01-01,A,NaN,10\n",
    "2000-01-01,A,100,-1\n",
    "NaT,A,100,10\n",
    "9999-01-01,A,100,10\n",
    "2000-01-01,A,100,10,extra\n",
])
def test_csv_rejects_missing_duplicate_and_invalid_cells(tmp_path, rows):
    path = tmp_path / "bad.csv"
    path.write_text("date,asset,close,volume\n" + rows, encoding="utf-8")
    with pytest.raises(ValueError):
        load_panel_csv(path)


def test_market_panel_rejects_misaligned_returns_and_nonchronological_dates():
    panel = make_synthetic_panel(n_dates=8, n_assets=4)
    bad_returns = panel.returns.copy()
    bad_returns[2, 0] += 0.1
    with pytest.raises(ValueError, match="returns must equal"):
        MarketPanel(panel.close, panel.volume, bad_returns, panel.dates, panel.assets)
    with pytest.raises(ValueError, match="chronological"):
        MarketPanel(panel.close[::-1], panel.volume, panel.returns, panel.dates[::-1], panel.assets)


@pytest.mark.parametrize("kwargs", [{"regime": "unknown"}, {"n_dates": 2}, {"n_assets": True}])
def test_synthetic_rejects_invalid_dimensions_or_regime(kwargs):
    with pytest.raises(ValueError):
        make_synthetic_panel(**kwargs)
