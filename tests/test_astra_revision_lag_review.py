"""Protocol-author checks of the separately authored core; artificial arrays only."""

import copy
import json

import numpy as np
import pytest

from alpha_research_rl import astra_revision_core as core
from alpha_research_rl.data import MarketPanel
from alpha_research_rl.dsl import evaluate_expression


def packet(expression):
    return json.dumps({"action": "propose", "expression": expression,
                       "hypothesis": "Artificial review case.", "revision": "Fixed test input."})


def state(expression, task="2020-H1"):
    return {"task_id": task, "baseline": {"expression": expression, "attempt": 2}}


@pytest.mark.parametrize("expression,lag,eligible", [
    ("-1e6", 0, True),
    ("++(-0.5)", 0, True),
    ("(returns + -1) / +2", 0, True),
    ("-(delay(returns,60)-(-2.5))", 60, True),
    ("delay(returns,0x3c)", 60, True),
    ("delay(returns,6_0)", 60, True),
    ("ts_mean(delay(returns,0x2),0x3c)", 61, False),
    ("delay(delay(-1,60),1)", 61, False),
])
def test_valid_frozen_dsl_forms_keep_their_structural_budget(expression, lag, eligible):
    result = core.validate_proposal(packet(expression))
    assert result["packet"]["expression"] == expression
    assert result["packet_valid"] and result["grammar_valid"]
    assert result["dependency_lag"] == lag
    assert result["within_dependency_limit"] is eligible
    assert result["eligible"] is eligible
    assert result["failure_code"] == (None if eligible else "study_ineligible_dependency_lag")


@pytest.mark.parametrize("window", ["+60", "-1", "60.0", "True", "30+30", "int(60)", "k"])
def test_nonliteral_or_wrong_typed_windows_fail_grammar_before_lag(window):
    expression = f"delay(returns,{window})"
    result = core.validate_proposal(packet(expression))
    assert result["packet"]["expression"] == expression
    assert result["packet_valid"] is True
    assert result["grammar_valid"] is False
    assert result["canonical_ast"] is result["dependency_lag"] is None
    assert result["eligible"] is result["within_dependency_limit"] is False
    assert result["failure_code"] == "invalid_expression"


def artificial_panel(values):
    length = len(values)
    close = np.cumprod(1 + values, axis=0)
    returns = values.copy()
    returns[0] = np.nan
    return MarketPanel(close, np.ones_like(values), returns,
                       np.datetime64("2000-01-01") + np.arange(length),
                       ("artificial-A", "artificial-B", "artificial-C"),
                       {"supported_features": ["returns"], "synthetic": True})


@pytest.mark.parametrize("expression,lag", [
    ("ts_mean(delay(returns,31),30)", 60),
    ("ts_std(delta(returns,31),30)", 60),
    ("delay(ts_mean(returns,30),32)", 61),
])
def test_observed_dependency_edge_on_artificial_arrays_agrees_with_new_filter(expression, lag):
    """Perturb data support, without implementing a second recursive lag function."""
    values = np.random.default_rng(731).normal(0, .01, (180, 3))
    target = 150
    baseline = evaluate_expression(expression, artificial_panel(values))[target, 0]
    assert np.isfinite(baseline)

    at_boundary = values.copy()
    at_boundary[target-lag, 0] += 1
    moved = evaluate_expression(expression, artificial_panel(at_boundary))[target, 0]
    assert abs(moved-baseline) > 1e-5

    outside_boundary = values.copy()
    outside_boundary[target-lag-1, 0] += 1
    outside_boundary[target+1, 0] += 1
    untouched = evaluate_expression(expression, artificial_panel(outside_boundary))[target, 0]
    assert untouched == baseline

    result = core.validate_proposal(packet(expression))
    assert result["grammar_valid"] and result["dependency_lag"] == lag
    assert result["eligible"] is (lag <= 60)


def test_window_edit_preserves_all_other_nodes_and_never_repairs_new_over_cap_expression():
    original = state("delay(ts_mean(add(returns,-0.5),60),1)")
    snapshot = copy.deepcopy(original)
    first = core.cheap_packet(original, "window_edit", 1)
    second = core.cheap_packet(original, "window_edit", 2)
    assert json.loads(first["raw_response"])["expression"] == "delay(ts_mean(add(returns, -0.5), 60), 1)"
    assert json.loads(second["raw_response"])["expression"] == "delay(ts_mean(add(returns, -0.5), 60), 2)"
    assert core.validate_proposal(first["raw_response"])["dependency_lag"] == 60
    rejected = core.validate_proposal(second["raw_response"])
    assert rejected["grammar_valid"] and not rejected["eligible"]
    assert rejected["dependency_lag"] == 61
    assert rejected["failure_code"] == "study_ineligible_dependency_lag"
    assert original == snapshot
    assert core.cheap_packet(original, "window_edit", 1) == first


@pytest.mark.parametrize("task,repetition,expression,digest,lag", [
    ("2020-H1", 3, "neg(ts_mean(delay(returns,3),3))",
     "375062694f078dd772713cf64d6b949f9a0d4036a32984d39986a468f3f69f4a", 5),
    ("2021-H2", 1, "sub(ts_mean(returns,5),ts_mean(returns,5))",
     "04954d6a486e64bebae0ac049994f196b7ad6655d604860e0b9d2680483a3394", 4),
    ("2024-H1", 1, "neg(ts_mean(delay(returns,1),20))",
     "f7833a208d232cfbd0ebccce20c2003d5e108e7158c2a9d09d1efe7c9439c010", 20),
])
def test_selected_seed_goldens_preserve_raw_digest_schedule(task, repetition, expression, digest, lag):
    emitted = core.cheap_packet(state("ts_mean(returns,20)", task), "grammar_draw", repetition)
    body = json.loads(emitted["raw_response"])
    assert body == {"action": "propose", "expression": expression,
                    "hypothesis": "Deterministic cheap reference.", "revision": "Generator: grammar_draw."}
    assert emitted["generation"]["seed_sha256"] == digest
    assert core.validate_proposal(emitted["raw_response"])["dependency_lag"] == lag


def test_degenerate_grammar_draw_is_retained_once_without_outcome_search():
    private = state("ts_mean(returns,20)", "2021-H2")
    result = core.cheap_packet(private, "grammar_draw", 1)
    expression = json.loads(result["raw_response"])["expression"]
    assert expression == "sub(ts_mean(returns,5),ts_mean(returns,5))"
    values = np.random.default_rng(931).normal(0, .01, (80, 3))
    factor = evaluate_expression(expression, artificial_panel(values))
    assert np.array_equal(factor[5:], np.zeros((75, 3)))
    assert core.validate_proposal(result["raw_response"])["eligible"]
    assert core.cheap_packet(private, "grammar_draw", 1) == result


def test_copy_retains_literal_alias_spelling_instead_of_normalizing_it():
    private = state("(ts_mean(returns,0x14))")
    for repetition in (1, 2, 3, 4):
        result = core.cheap_packet(private, "copy", repetition)
        assert json.loads(result["raw_response"])["expression"] == "(ts_mean(returns,0x14))"
        assert result["generation"]["baseline_attempt"] == 2
