import numpy as np
import pytest

from alpha_research_rl.data import MarketPanel, make_synthetic_panel
from alpha_research_rl.dsl import ExpressionError, evaluate_expression


@pytest.fixture
def panel():
    return make_synthetic_panel(seed=11, n_dates=40, n_assets=8)


@pytest.mark.parametrize("expression", [
    "delay(returns,1)", "delta(close,3)", "ts_mean(volume,5)", "ts_std(returns,7)",
    "rank(ts_mean(returns,3))", "zscore(delta(log(volume),1))", "close/ts_mean(close,8)-1",
    "add(mul(returns,2),neg(div(delta(volume,1),volume)))",
])
def test_future_perturbation_cannot_change_current_or_past_factors(panel, expression):
    close, volume = panel.close.copy(), panel.volume.copy()
    close[24:] *= np.linspace(1, 2, len(close) - 24)[:, None]
    volume[24:] *= 10
    returns = np.full_like(close, np.nan)
    returns[1:] = close[1:] / close[:-1] - 1
    changed = MarketPanel(close, volume, returns, panel.dates, panel.assets)
    original_factor = evaluate_expression(expression, panel)
    changed_factor = evaluate_expression(expression, changed)
    np.testing.assert_allclose(original_factor[:24], changed_factor[:24], equal_nan=True)


def test_delay_delta_and_rolling_are_aligned(panel):
    delay = evaluate_expression("delay(close,3)", panel)
    assert np.isnan(delay[:3]).all()
    np.testing.assert_array_equal(delay[3:], panel.close[:-3])
    delta = evaluate_expression("delta(close,3)", panel)
    np.testing.assert_array_equal(delta[3:], panel.close[3:] - panel.close[:-3])
    mean = evaluate_expression("ts_mean(close,3)", panel)
    std = evaluate_expression("ts_std(close,3)", panel)
    assert np.isnan(mean[:2]).all()
    np.testing.assert_allclose(mean[2], panel.close[:3].mean(axis=0))
    np.testing.assert_allclose(std[2], panel.close[:3].std(axis=0))


def test_missing_rolling_rows_scalar_arithmetic_and_safe_undefined_values(panel):
    panel.volume[10, 0] = np.nan
    values = evaluate_expression("ts_mean(volume,3)", panel)
    assert np.isnan(values[10:13, 0]).all()
    assert np.isfinite(values[13, 0])
    np.testing.assert_array_equal(evaluate_expression("2", panel), np.full(panel.close.shape, 2))
    np.testing.assert_allclose(evaluate_expression("returns*2 + 1", panel), panel.returns * 2 + 1)
    assert np.isnan(evaluate_expression("1/0", panel)).all()
    assert np.isnan(evaluate_expression("log(-1)", panel)).all()
    assert np.isnan(evaluate_expression("zscore(1)", panel)).all()
    np.testing.assert_array_equal(evaluate_expression("rank(1)", panel), np.full(panel.close.shape, 0.5))


@pytest.mark.parametrize("expression", [
    "delay(close,-1)", "delay(close,0)", "delay(close,61)", "delay(close,1.0)",
    "delay(close,True)", "delay(close,1+1)", "close.__class__", "close[1:]",
    "__import__('os')", "sum(close)", "ts_mean(close,k=2)", "close**2",
    "[close]", "lambda: close", "True", "1e309", "1000001", "9" * 200, "abs(close,volume)",
    "(x for x in close)", "close if 1 else volume", "close @ volume",
    "abs(" * 20 + "close" + ")" * 20,
    "+".join(["close"] * 100),
])
def test_rejects_unsafe_or_unbounded_grammar(panel, expression):
    with pytest.raises(ExpressionError):
        evaluate_expression(expression, panel)


def test_evaluation_does_not_mutate_panel_or_alias_result(panel):
    original = panel.close.copy()
    values = evaluate_expression("close", panel)
    values[:] = 0
    np.testing.assert_array_equal(panel.close, original)
