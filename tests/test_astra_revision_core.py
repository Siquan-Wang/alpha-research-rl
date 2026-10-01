"""Artificial matched-prefix states, isolated eligibility and exact bookkeeping."""

import copy
import json
import math
from pathlib import Path

import pytest
from test_astra_pool_diagnosis import financial_manifest, metrics
from test_astra_replay import initial

from alpha_research_rl import astra_revision_core as core


def packet(expression):
    return core.canonical_json({"action": "propose", "expression": expression,
                                "hypothesis": "SYNTHETIC old narrative must not enter the prompt.",
                                "revision": "SYNTHETIC prior decision must not enter the prompt."})


def feedback(mean):
    return {**metrics(mean), "usable": True}


def state(task="2020-H1"):
    records = []
    for attempt, (expression, ic) in enumerate((("ts_mean(returns,5)", -0.4), ("delay(returns,3)", 0.1)), start=1):
        raw = packet(expression)
        validated = core.validate_proposal(raw)
        records.append({"attempt": attempt, "raw_response": raw, "packet": validated["packet"],
                        "canonical_ast": validated["canonical_ast"], "canonical_duplicate": False,
                        "feedback": feedback(ic)})
    record = {"task_id": task, "initial_observation": initial(), "financial_manifest": financial_manifest(task)}
    return core.make_state(record, records)


@pytest.mark.parametrize("expression,lag,eligible", [
    ("returns", 0, True), ("1.0", 0, True), ("-rank(returns)", 0, True),
    ("delay(returns,60)", 60, True), ("ts_mean(delay(returns,1),60)", 60, True),
    ("delay(ts_mean(returns,60),2)", 61, False), ("ts_std(delta(returns,2),60)", 61, False),
    ("add(delay(returns,40),ts_mean(returns,60))", 59, True),
    ("sub(delay(delay(returns,60),1),delay(delay(returns,60),1))", 61, False),
])
def test_cumulative_lag_including_nested_boundaries_and_no_algebraic_cancellation(expression, lag, eligible):
    result = core.validate_proposal(packet(expression))
    assert result["grammar_valid"] is True
    assert result["dependency_lag"] == lag and result["eligible"] is eligible
    assert result["failure_code"] == (None if eligible else "study_ineligible_dependency_lag")


@pytest.mark.parametrize("raw,packet_valid", [("not JSON", False), (packet(" returns"), True),
                                             (packet("delay(returns,61)"), True)])
def test_original_packet_and_grammar_failures_are_not_repaired(raw, packet_valid):
    result = core.adjudicate(raw, state(), None)
    assert result["raw_response"] == raw and result["packet_valid"] is packet_valid
    assert result["grammar_valid"] is False and result["dependency_lag"] is None
    assert result["selected_new"] is False and result["selection"]["attempt"] == 1


def test_literal_protocol_prompt_treatment_and_observation_boundary():
    plan = (Path(__file__).resolve().parents[1] / "docs/astra-matched-prefix-plan-v1.md").read_text(encoding="utf-8")
    literal = plan.split("```text\n", 1)[1].split("```", 1)[0]
    assert core.ACTOR_INSTRUCTIONS == literal
    private = state()
    truthful, masked = (core.observation(private, condition) for condition in core.CONDITIONS)
    assert masked == {**truthful, "candidate_feedback": [None, None]}
    assert set(truthful) == {"initial_evidence", "prefix", "candidate_feedback", "attempt", "attempt_budget",
                             "max_dependency_lag"}
    for condition in core.CONDITIONS:
        prompt = core.prompt(private, condition)
        assert prompt == literal + "\nOBSERVATION:\n" + core.canonical_json(core.observation(private, condition)) + "\n"
        assert all(core.prompt(private, condition) == prompt for _ in range(4))
        assert "SYNTHETIC" not in prompt and "2020" not in prompt
        assert '"baseline"' not in prompt and '"orientation"' not in prompt
        assert '"assessment"' not in prompt and '"raw_response"' not in prompt
    truthful["prefix"][0]["expression"] = "changed"
    truthful["candidate_feedback"][0]["mean_ic"] = 0.9
    assert core.observation(private, "truthful")["prefix"][0]["expression"] == "ts_mean(returns,5)"
    assert private["prefix"][0]["feedback"]["mean_ic"] == -0.4


def test_single_preorder_window_edit_starts_fresh_and_clamps_once():
    private = state()
    private["baseline"]["expression"] = "add(rank(ts_mean(returns,5)),delay(returns,20))"
    expected = ["add(rank(ts_mean(returns,4)),delay(returns,20))",
                "add(rank(ts_mean(returns,6)),delay(returns,20))",
                "add(rank(ts_mean(returns,2)),delay(returns,20))",
                "add(rank(ts_mean(returns,10)),delay(returns,20))"]
    for repetition, expression in enumerate(expected, start=1):
        value = core.cheap_packet(private, "window_edit", repetition)
        assert json.loads(value["raw_response"])["expression"].replace(" ", "") == expression
        assert value["generation"]["original_window"] == 5
    private["baseline"]["expression"] = "delay(returns,1)"
    assert json.loads(core.cheap_packet(private, "window_edit", 1)["raw_response"])["expression"] == "delay(returns, 1)"
    private["baseline"]["expression"] = "delay(returns,60)"
    assert json.loads(core.cheap_packet(private, "window_edit", 4)["raw_response"])["expression"] == "delay(returns, 60)"


def test_all_forty_grammar_draws_and_cheap_packet_literals_are_fixed():
    templates = {}
    for task in core.TASK_IDS:
        for repetition in core.REPETITIONS:
            for generator in core.CHEAP_TEXT:
                emitted = core.cheap_packet(state(task), generator, repetition)
                proposal = core.validate_proposal(emitted["raw_response"])
                assert proposal["eligible"]
                assert proposal["packet"]["hypothesis"] == "Deterministic cheap reference."
                assert proposal["packet"]["revision"] == f"Generator: {generator}."
                if generator == "grammar_draw":
                    index = emitted["generation"]["template_index"]
                    templates[index] = templates.get(index, 0) + 1
                    assert proposal["dependency_lag"] <= 29
    assert templates == {0: 4, 1: 6, 2: 4, 3: 3, 4: 9, 5: 2, 6: 10, 7: 2}


def test_copy_duplicate_quality_is_reused_not_zero_and_cannot_replace_prefix():
    private = state()
    for prefix in private["prefix"]:
        record = core.adjudicate(packet(prefix["expression"]), private, prefix["feedback"])
        assert record["canonical_duplicate_with_prefix"] and not record["admitted_to_selector"]
        result = core.resolve_branch(record, core.quality(True, -0.3), core.quality(True, 0.1))
        assert result["candidate_Q"] == -0.3 and result["selected_Q"] == 0.1
        assert result["G"] == 0.0 and result["incremental_net_gain"] == -0.01
        assert result["terminal_utility"] == pytest.approx(0.07)


def test_historical_admission_and_ties_are_fixed_before_future_failure():
    private = state()
    raw = packet("delay(returns,9)")
    tie = core.adjudicate(raw, private, feedback(0.4))
    assert tie["admitted_to_selector"] and not tie["selected_new"]
    selected = core.adjudicate(raw, private, feedback(-0.5))
    assert selected["selected_new"] and selected["selection"]["orientation"] == -1
    failed = core.resolve_branch(selected, core.quality(False, -1.0), core.quality(True, 0.1))
    assert failed["G"] == -1.1 and failed["selected_Q"] == -1.0
    rejected = core.adjudicate(raw, private, {**metrics(None), "ic_std": None, "n_dates": 0,
                                            "coverage": 0.0, "usable": False})
    assert not rejected["admitted_to_selector"] and rejected["orientation"] is None
    assert core.resolve_branch(rejected, core.quality(False, -1.0), core.quality(True, 0.1))["G"] == 0


def analysis_rows():
    rows = []
    for task, generator, repetition in core.SLOT_ORDER:
        private = state(task)
        if generator == "copy":
            record = core.adjudicate(packet(private["baseline"]["expression"]), private,
                                     private["baseline"]["feedback"])
            valid, q = True, 0.1
        elif generator == "window_edit":
            record = core.adjudicate("invalid JSON", private, None)
            valid, q = False, -1.0
        else:
            high = generator == "truthful"
            record = core.adjudicate(packet(f"delay(returns,{repetition + 10})"), private,
                                     feedback(0.5 if high else 0.2))
            q = {"truthful": [0.5, -1.0, 0.3, 0.1], "masked": [0.0, 0.1, 0.2, 0.3],
                 "grammar_draw": [-1.0, -1.0, -0.2, -0.2]}[generator][repetition - 1]
            valid = q != -1.0
        rows.append({"task_id": task, "generator": generator, "repetition": repetition,
                     "adjudication": record, **core.resolve_branch(record, core.quality(valid, q),
                                                                    core.quality(True, 0.1))})
    return rows


def test_full_denominators_signed_quality_and_selector_decomposition():
    rows = analysis_rows()
    result = core.analyze(rows)
    assert result["slot_count"] == 200 and len(result["states"]) == 10 and len(result["years"]) == 5
    truthful = result["generators"]["truthful"]
    assert truthful["candidate"]["denominator"] == 40 and truthful["candidate"]["valid_count"] == 30
    assert truthful["candidate"]["mean_Q"] == pytest.approx(-0.025)
    assert truthful["mean_G"] == pytest.approx(-0.125)
    assert result["primary_truthful_minus_masked_Q"] == pytest.approx(-0.175)
    assert result["secondary_truthful_minus_masked_G"] == pytest.approx(-0.125)
    contrast = result["contrasts"]["truthful_minus_masked"]
    assert contrast["validity_contribution"] == -0.25
    assert contrast["predictive_contribution"] == pytest.approx(0.075)
    assert result["generators"]["window_edit"]["candidate"]["conditional_valid_mean_ic"] is None
    assert result["generators"]["window_edit"]["selected"]["valid_count"] == 40
    assert all(year["generators"]["truthful"]["candidate"]["denominator"] == 8 for year in result["years"])
    assert result["conditional_generation_mc_se"] == pytest.approx(math.sqrt(10 * (1.3475 / 3 + 0.05 / 3) / 4) / 10)
    assert result["allocation"]["all_point_conditions_pass"] is False
    assert result["allocation"]["automatic_next_study_authorized"] is False
    with pytest.raises(ValueError, match="all 200"):
        core.analyze(rows[:-1])
    changed = copy.deepcopy(rows)
    changed[0]["terminal_cost"] = math.nextafter(0.03, math.inf)
    with pytest.raises(ValueError, match="arithmetic"):
        core.analyze(changed)
