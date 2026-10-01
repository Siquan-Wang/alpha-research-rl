import json

import numpy as np
import pytest

from alpha_research_rl.data import MarketPanel, make_synthetic_panel
from alpha_research_rl.financial_tasks import (
    FORMULA_GRID,
    INVALID_REWARD,
    PROPOSAL_COST,
    feedback_teacher,
    make_task,
    task_periods,
)


@pytest.fixture(scope="module")
def panel():
    return make_synthetic_panel(seed=404, n_dates=1200, n_assets=8)


def test_exact_task_counts_order_and_dates():
    assert len(task_periods("train")) == 32
    assert task_periods("train")[0] == (2002, 1) and task_periods("train")[-1] == (2017, 2)
    assert len(task_periods("feasibility")) == 4
    assert task_periods("transfer")[0] == (2020, 1) and task_periods("transfer")[-1] == (2024, 2)
    assert len(FORMULA_GRID) == 16


def test_observation_contains_true_feedback_only_and_no_period_identity(panel):
    task = make_task(panel, 2002, 1)
    observation = task.observation()
    serialized = json.dumps(observation, allow_nan=False)
    for forbidden in ("assessment", "year", "half", "seed", "source", "date", "regime"):
        # Count fields n_dates/n_signal_dates describe support; period identities are absent.
        if forbidden == "date":
            continue
        assert forbidden not in serialized
    assert observation["supported_features"] == ["returns"]
    assert len(observation["probe_evidence"]) == 2
    for probe in observation["probe_evidence"]:
        assert len(probe["windows"]) == 3
        scored = task.evaluate(probe["expression"])
        assert probe["feedback"] == scored["feedback"]
        assert scored["anchor_reuse"] is True
    observation["probe_evidence"][0]["feedback"]["mean_ic"] = 99
    assert task.observation()["probe_evidence"][0]["feedback"]["mean_ic"] != 99


def test_future_perturbation_preserves_observation_teacher_and_orientation(panel):
    task = make_task(panel, 2002, 1)
    boundary = task.public_manifest["feedback_label_boundary"]
    close = panel.close.copy()
    close[boundary:] *= np.linspace(1.1, 1.7, len(close) - boundary)[:, None]
    realized = np.full_like(close, np.nan)
    realized[1:] = close[1:] / close[:-1] - 1
    changed = MarketPanel(close, panel.volume.copy(), realized, panel.dates, panel.assets)
    altered_task = make_task(changed, 2002, 1)
    assert task.observation() == altered_task.observation()
    assert feedback_teacher(task) == feedback_teacher(altered_task)
    assert task.feedback_score("returns") == altered_task.feedback_score("returns")
    original, altered = task.evaluate("returns"), altered_task.evaluate("returns")
    assert original["feedback"] == altered["feedback"]
    assert original["orientation"] == altered["orientation"]


def test_labels_are_purged_at_both_halfyear_boundaries(panel):
    manifest = make_task(panel, 2002, 1).public_manifest
    assert manifest["feedback_bounds_half_open"][1] - 1 + 5 < manifest["feedback_label_boundary"]
    assert manifest["assessment_bounds_half_open"][1] - 1 + 5 < manifest["assessment_label_boundary"]
    assert manifest["feedback_label_boundary"] == manifest["assessment_bounds_half_open"][0]


@pytest.mark.parametrize("expression", ["volume", "close", "close.__class__", "delay(returns,-1)", "1", "returns/0"])
def test_invalid_unsupported_and_constant_formulas_have_strict_penalty(panel, expression):
    result = make_task(panel, 2002, 1).evaluate(expression)
    assert result["reward"] == INVALID_REWARD
    assert result["cost"] == PROPOSAL_COST
    assert result["status"] in {"invalid", "unscorable"}


def test_rewards_fix_orientation_on_feedback_and_charge_same_cost(panel):
    task = make_task(panel, 2002, 1)
    positive, negative = task.evaluate("returns"), task.evaluate("neg(returns)")
    assert positive["status"] == negative["status"] == "ok"
    assert positive["reward"] == pytest.approx(negative["reward"])
    assert positive["orientation"] == -negative["orientation"]
    assert positive["reward"] == pytest.approx(positive["oriented_future_ic"] - PROPOSAL_COST)


def test_assessment_support_failure_gets_penalty_without_changing_feedback(panel):
    task = make_task(panel, 2002, 1)
    start, stop = task.public_manifest["assessment_bounds_half_open"]
    close = panel.close.copy()
    close[start:stop] = close[start - 1]
    realized = np.full_like(close, np.nan)
    realized[1:] = close[1:] / close[:-1] - 1
    flat = MarketPanel(close, panel.volume.copy(), realized, panel.dates, panel.assets)
    altered = make_task(flat, 2002, 1)
    assert altered.observation() == task.observation()
    result = altered.evaluate("returns")
    assert result["status"] == "unscorable"
    assert result["reason"] == "insufficient_assessment_support"
    assert result["reward"] == INVALID_REWARD


def test_panel_hard_cap_rejects_post2024_dates(panel):
    shifted_dates = panel.dates + np.timedelta64(24 * 365, "D")
    shifted = MarketPanel(panel.close, panel.volume, panel.returns, shifted_dates, panel.assets)
    with pytest.raises(ValueError, match="capped"):
        make_task(shifted, 2025, 1)


def test_feedback_teacher_never_calls_future_evaluation(monkeypatch, panel):
    task = make_task(panel, 2002, 1)

    def forbidden_future(self, expression):
        raise AssertionError("teacher must not consult assessment")

    monkeypatch.setattr(type(task), "evaluate", forbidden_future)
    assert feedback_teacher(task) in FORMULA_GRID[:12]


def test_missing_assessment_assets_fail_coverage_gate(panel):
    original = make_task(panel, 2002, 1)
    boundary = original.public_manifest["assessment_bounds_half_open"][0]
    close = panel.close.copy()
    close[boundary:, :2] = np.nan
    realized = np.full_like(close, np.nan)
    realized[1:] = close[1:] / close[:-1] - 1
    changed = MarketPanel(close, panel.volume, realized, panel.dates, panel.assets)
    task = make_task(changed, 2002, 1)
    assert task.observation() == original.observation()
    result = task.evaluate("returns")
    assert result["assessment"]["coverage"] == 0.75
    assert result["reward"] == INVALID_REWARD
