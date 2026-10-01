import json

import numpy as np
import pytest

from alpha_research_rl.data import MarketPanel, make_synthetic_panel
from alpha_research_rl.evaluation import forward_returns
from alpha_research_rl.real_baselines import (
    block_bootstrap_mean_ci,
    build_features,
    calendar_split,
    fit_ridge,
    run_fixed_baselines,
)


def test_ridge_train_only_standardization_and_coefficients_ignore_assessment():
    rng = np.random.default_rng(12)
    features = rng.normal(size=(80, 6, 3))
    features[:, :, 2] = 7
    labels = features[:, :, 0] * 0.03 - features[:, :, 1] * 0.01 + 0.2
    original = fit_ridge(features, labels, 0, 60)
    changed_features, changed_labels = features.copy(), labels.copy()
    changed_features[60:] *= 100
    changed_labels[60:] += 10
    changed = fit_ridge(changed_features, changed_labels, 0, 60)
    np.testing.assert_array_equal(original.mean, changed.mean)
    np.testing.assert_array_equal(original.scale, changed.scale)
    np.testing.assert_array_equal(original.coefficients, changed.coefficients)
    assert original.scale[2] == 1
    assert original.n_training_samples == 360
    assert np.mean((original.predict(features[:60]) - labels[:60]) ** 2) < 1e-7


def test_complete_case_fit_and_missing_prediction_are_explicit():
    features = np.arange(60, dtype=float).reshape(10, 3, 2)
    labels = features[:, :, 0] / 100
    features[1, 1, 0] = np.nan
    labels[2, 1] = np.nan
    model = fit_ridge(features, labels, 0, 8)
    assert model.n_training_samples == 22
    assert np.isnan(model.predict(features)[1, 1])


def test_causal_features_and_purged_fit_survive_future_return_perturbation():
    panel = make_synthetic_panel(seed=42, n_dates=2600, n_assets=4)
    split = calendar_split(panel.dates, 2006)
    boundary = split["fit_label_boundary"]
    features = build_features(panel)
    labels = forward_returns(panel, 5)
    first = fit_ridge(features, labels, *split["fit"])
    close = panel.close.copy()
    close[boundary:] *= np.linspace(1.2, 1.8, len(close) - boundary)[:, None]
    changed_returns = np.full_like(close, np.nan)
    changed_returns[1:] = close[1:] / close[:-1] - 1
    changed = MarketPanel(close, panel.volume.copy(), changed_returns, panel.dates, panel.assets)
    new_features, new_labels = build_features(changed), forward_returns(changed, 5)
    np.testing.assert_allclose(features[:boundary], new_features[:boundary], equal_nan=True)
    second = fit_ridge(new_features, new_labels, *split["fit"])
    np.testing.assert_array_equal(first.mean, second.mean)
    np.testing.assert_array_equal(first.coefficients, second.coefficients)
    assert split["fit"][1] - 1 + 5 < boundary
    assert split["assessment"][1] - 1 + 5 < split["assessment_label_boundary"]


def test_bootstrap_fixed_seed_constant_series_and_timeblock_preservation():
    blocks = [np.full(43, 0.1), np.full(57, -0.2)]
    first = block_bootstrap_mean_ci(blocks, block_length=20, n_bootstrap=100, seed=5)
    second = block_bootstrap_mean_ci(blocks, block_length=20, n_bootstrap=100, seed=5)
    assert first == second
    expected = (43 * 0.1 + 57 * -0.2) / 100
    assert first["lower"] == pytest.approx(expected)
    assert first["upper"] == pytest.approx(expected)
    assert first["n_dates"] == 100


def test_summary_is_strict_json_aggregate_only_and_sanitizes_provenance():
    panel = make_synthetic_panel(seed=10, n_dates=2600, n_assets=4)
    panel.metadata["download_manifest"] = {"raw_path": "C:/sensitive/input.zip"}
    results = run_fixed_baselines(panel, years=(2006,), bootstrap_replicates=40)
    serialized = json.dumps(results, allow_nan=False)
    assert "sensitive" not in serialized and "daily_ic" not in serialized
    assert "coefficients" not in serialized and "predictions" not in serialized
    assert results["synthetic"] is True
    assert results["yearly"][0]["year"] == 2006
    assert set(results["pooled"]) == {"ridge", "momentum20", "reversal20"}


@pytest.mark.parametrize("blocks,kwargs", [([], {}), ([np.array([])], {}),
    ([np.array([np.nan])], {}), ([np.ones(3)], {"block_length": 0}),
    ([np.ones(3)], {"n_bootstrap": 1})])
def test_bootstrap_invalid_input_rejected(blocks, kwargs):
    with pytest.raises(ValueError):
        block_bootstrap_mean_ci(blocks, **kwargs)
