import json

import numpy as np
import pytest

from alpha_research_rl.data import MarketPanel, make_synthetic_panel
from alpha_research_rl.factor_diagnostics import FeedbackRankAnalyzer, diagnose_report


@pytest.fixture(scope="module")
def panel():
    return make_synthetic_panel(seed=23, n_dates=1200, n_assets=16, regime="null")


@pytest.mark.parametrize("expression,sign", [
    ("returns", 1), ("returns*2+1", 1), ("neg(returns)", -1),
    ("rank(returns)", 1), ("zscore(returns)", 1), ("log(returns+1)", 1),
])
def test_identical_positive_negative_monotone_aliases_have_unit_rank_similarity(panel, expression, sign):
    analyzer = FeedbackRankAnalyzer.from_panel(panel, 2002, 1)
    result = analyzer.pair_similarity(expression, "returns")
    assert result["status"] == "ok"
    assert result["mean_daily_spearman"] == pytest.approx(sign)
    assert result["absolute_mean_daily_spearman"] == pytest.approx(1)
    assert result["near_exact_rank_equivalent"] is True
    assert result["paired_cell_coverage"] == 1


def test_unrelated_null_return_lag_does_not_look_rank_equivalent(panel):
    analyzer = FeedbackRankAnalyzer.from_panel(panel, 2002, 1)
    result = analyzer.pair_similarity("delay(returns,1)", "returns")
    assert result["status"] == "ok"
    assert result["absolute_mean_daily_spearman"] < 0.15
    assert result["near_exact_rank_equivalent"] is False


@pytest.mark.parametrize("expression", ["1", "returns/0", "volume", "close", "delay(returns,-1)"])
def test_constants_missing_and_unsupported_are_unscorable(panel, expression):
    result = FeedbackRankAnalyzer.from_panel(panel, 2002, 1).pair_similarity(expression, "returns")
    assert result["status"] == "unscorable"
    assert result["near_exact_rank_equivalent"] is False


def test_missing_pair_coverage_does_not_falsely_pass_unit_correlation_gate(panel):
    close = panel.close.copy()
    close[:, :4] = np.nan
    returns = np.full_like(close, np.nan)
    returns[1:] = close[1:] / close[:-1] - 1
    missing = MarketPanel(close, panel.volume, returns, panel.dates, panel.assets)
    result = FeedbackRankAnalyzer.from_panel(missing, 2002, 1).pair_similarity("returns", "returns")
    assert result["absolute_mean_daily_spearman"] == pytest.approx(1)
    assert result["paired_cell_coverage"] == 0.75
    assert result["status"] == "unscorable"
    assert result["near_exact_rank_equivalent"] is False


def test_future_perturbation_cannot_change_feedback_diagnostics(panel):
    analyzer = FeedbackRankAnalyzer.from_panel(panel, 2002, 1)
    boundary = len(analyzer._visible.close)
    close = panel.close.copy()
    close[boundary:] *= np.linspace(1.1, 2, len(close) - boundary)[:, None]
    returns = np.full_like(close, np.nan)
    returns[1:] = close[1:] / close[:-1] - 1
    changed = MarketPanel(close, panel.volume, returns, panel.dates, panel.assets)
    altered = FeedbackRankAnalyzer.from_panel(changed, 2002, 1)
    assert analyzer.diagnose("rank(returns)") == altered.diagnose("rank(returns)")


def test_saved_report_deduplicates_calculation_and_publishes_aggregates_only(panel, monkeypatch):
    import alpha_research_rl.factor_diagnostics as module

    original = module.evaluate_expression
    calls = []

    def counted(expression, visible):
        calls.append(expression)
        return original(expression, visible)

    monkeypatch.setattr(module, "evaluate_expression", counted)
    outcome = {"status": "ok", "expression": "rank(returns)"}
    record = {"condition": "true", "decoding": "stochastic", "strict": outcome,
              "fence_tolerant_secondary": outcome}
    report = {"episodes": [{"task": {"year": 2002, "half": 1}, "records": [record, record]}]}
    result = diagnose_report(report, panel)
    assert result["summary"]["unique_task_expression_pairs"] == 1
    assert result["summary"]["near_exact_rank_equivalent_pairs"] == 1
    assert calls.count("rank(returns)") == 1
    assert len(calls) == 13  # One unique generated factor plus the fixed twelve teachers.
    serialized = json.dumps(result, allow_nan=False)
    assert "daily_ic" not in serialized
    assert "assessment" not in result["episodes"][0]["unique_valid_expression_diagnostics"][0]


def test_nearest_teacher_reports_signed_and_absolute_similarity_separately(panel):
    result = FeedbackRankAnalyzer.from_panel(panel, 2002, 1).diagnose("neg(returns)")
    assert result["nearest_teacher"]["reference"] == "returns"
    assert result["nearest_teacher"]["mean_daily_spearman"] == pytest.approx(-1)
    assert result["nearest_teacher"]["absolute_mean_daily_spearman"] == pytest.approx(1)
