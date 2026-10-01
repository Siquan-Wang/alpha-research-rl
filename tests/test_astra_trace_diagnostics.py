"""Synthetic bookkeeping regressions; no actual bank, market array, or actor call."""

import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from test_astra_replay import ROOT, initial, metrics, packet, seal, synthetic, transport, write_fixture

from alpha_research_rl import astra_trace_diagnostics as diagnostics
from alpha_research_rl.agentic_research import ARMS, ResearchEpisode, digest


@pytest.fixture(scope="module")
def evidence():
    return synthetic.__wrapped__()


def invoke(paths):
    return diagnostics.diagnose_traces(paths[0], paths[1], source_root=ROOT)


def rebuild(item, *, raws=None, observation=None, feedback=None):
    episode = ResearchEpisode(item["arm"], observation or item["submission"]["initial_evidence"],
                              feedback or (lambda expression: {
                                  **metrics(-0.4 if expression == "neg(returns)" else 0.1), "usable": True,
                              }))
    summaries = []
    for attempt, raw in enumerate(raws or [r["raw_response"] for r in item["submission"]["records"]], start=1):
        summaries.append(transport(episode.prompt(), raw, attempt))
        episode.submit(raw)
    item.update(submission=episode.freeze(), transport_summaries=summaries)


def test_complete_denominators_ast_scopes_null_selections_and_probes(tmp_path, evidence, monkeypatch):
    monkeypatch.setattr(subprocess, "Popen", lambda *_, **__: pytest.fail("must not start a process"))
    paths = write_fixture(tmp_path, evidence)
    report = invoke(paths)
    counts = report["all"]["counts"]
    assert counts == {
        "episode_count": 30, "charged_attempt_count": 180,
        "grammar_valid_count": 116, "grammar_invalid_count": 64,
        "feedback_usable_count": 116, "feedback_unusable_count": 0, "feedback_unavailable_count": 64,
        "within_episode_ast_duplicate_count": 29, "selector_eligible_unique_proposal_count": 87,
        "global_unique_ast_count": 3, "sum_episode_unique_ast_counts": 87,
        "initial_probe_entries_across_episodes": 60, "selected_episode_count": 29,
        "selected_attempt_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 29, "6": 0, "unavailable": 1},
    }
    assert report["common_initial_probe_count"] == 20  # Shared probes are not 60 independent probes.
    assert [p["task_id"] for p in report["periods"]] == list(diagnostics.TASK_IDS)
    for period in report["periods"]:
        assert period["counts_all_arms"]["charged_attempt_count"] == 18
        assert list(period["by_arm"]) == list(ARMS)
        assert period["common_initial_probes"]["probe_count"] == 2
        assert period["common_initial_probes"]["best_usable_probe"]["probe_index"] == 1  # Earliest tie.
    withheld = report["by_arm"][ARMS[2]]
    assert withheld["counts"]["charged_attempt_count"] == 60
    assert withheld["historical_comparisons"]["selected_abs_ic"] == {
        "episode_denominator": 10, "available_episodes": 9, "unavailable_episodes": 1,
        "mean_available": 0.4, "minimum_available": 0.4, "maximum_available": 0.4,
    }
    missing = report["periods"][0]["by_arm"][ARMS[2]]
    assert missing["selected_attempt"] is None and missing["first_charged_eligible_proposal"] is None
    assert missing["historical_comparisons"] == {
        "selected_abs_ic": None, "best_initial_probe_abs_ic": 0.1, "first_charged_eligible_abs_ic": None,
        "selected_minus_best_initial_probe_abs_ic": None, "selected_minus_first_charged_eligible_abs_ic": None,
    }
    selected = report["periods"][0]["by_arm"][ARMS[0]]["historical_comparisons"]
    assert selected["selected_minus_best_initial_probe_abs_ic"] == pytest.approx(0.3)
    assert selected["selected_minus_first_charged_eligible_abs_ic"] == pytest.approx(0.3)
    assert report["status"] == "POST_HOC_TRACE_BOOKKEEPING"
    assert report["verification"]["assessment"] is None
    assert report["financial_scores_recomputed"] is False and report["assessment_artifact_read"] is False
    assert report["inputs"]["submissions"] == {
        "sha256": hashlib.sha256(paths[1].read_bytes()).hexdigest(), "bytes": len(paths[1].read_bytes()),
    }
    assert report["body_sha256"] == digest({k: v for k, v in report.items() if k != "body_sha256"})
    assert report == invoke(paths)  # Same bytes and source produce the same report.


def test_token_fields_missingness_and_cached_input_are_separate(tmp_path, evidence):
    def change(_, submissions):
        summary = submissions["episodes"][0]["transport_summaries"][0]
        summary["usage"].update(cached_input_tokens=31, cache_write_input_tokens=7)
        summary["reported_usage_records"] = [{"line_1based": 4, "usage": summary["usage"].copy()}]

    report = invoke(write_fixture(tmp_path, evidence, mutate=change))
    usage = report["all"]["reported_usage"]
    assert usage["decision_count"] == 180 and usage["missing_usage_decisions"] == 1
    assert usage["token_fields"]["output_tokens"] == {
        "reported_sum": 3580, "reported_decisions": 179, "missing_decisions": 1, "complete_sum": None,
    }
    assert usage["token_fields"]["reasoning_output_tokens"] == {
        "reported_sum": 890, "reported_decisions": 178, "missing_decisions": 2, "complete_sum": None,
    }
    assert usage["token_fields"]["cached_input_tokens"] == {
        "reported_sum": 31, "reported_decisions": 179, "missing_decisions": 1, "complete_sum": None,
    }
    assert usage["token_fields"]["cache_write_input_tokens"]["reported_sum"] == 7
    assert usage["elapsed_seconds"] == {"total": 630.0, "minimum": 1.0, "maximum": 6.0}
    for arm in ARMS:
        assert report["by_arm"][arm]["reported_usage"] == report["verification"]["usage_by_arm"][arm]


def test_entirely_invalid_bank_retains_all_nulls_without_zero_imputation(tmp_path, evidence):
    def change(_, submissions):
        for item in submissions["episodes"]:
            rebuild(item, raws=["invalid JSON"] * 6)

    report = invoke(write_fixture(tmp_path, evidence, mutate=change))
    counts = report["all"]["counts"]
    assert counts["charged_attempt_count"] == counts["grammar_invalid_count"] == 180
    assert counts["global_unique_ast_count"] == counts["selected_episode_count"] == 0
    assert counts["selected_attempt_distribution"]["unavailable"] == 30
    comparison = report["all"]["historical_comparisons"]["selected_minus_first_charged_eligible_abs_ic"]
    assert comparison == {"episode_denominator": 30, "available_episodes": 0, "unavailable_episodes": 30,
                          "mean_available": None, "minimum_available": None, "maximum_available": None}
    assert report["first_attempt_matching"]["formula_matching"]["all_three_arms"]["exact_expression_match"] == {
        "period_denominator": 10, "matching_periods": 0, "different_periods": 0, "unavailable_periods": 10,
    }


def test_first_formula_string_identity_is_distinct_from_ast_and_prompt_identity(tmp_path, evidence):
    def change(_, submissions):
        item = submissions["episodes"][3]  # Full feedback, 2020-H2: all three first records are valid.
        raws = [packet("(returns)")] + [r["raw_response"] for r in item["submission"]["records"][1:]]
        rebuild(item, raws=raws)

    report = invoke(write_fixture(tmp_path, evidence, mutate=change))
    matching = report["first_attempt_matching"]
    assert matching["identical_supplied_prompt_periods"] == 10
    assert matching["formula_matching"]["all_three_arms"] == {
        "exact_expression_match": {"period_denominator": 10, "matching_periods": 8,
                                   "different_periods": 1, "unavailable_periods": 1},
        "canonical_ast_match": {"period_denominator": 10, "matching_periods": 9,
                                "different_periods": 0, "unavailable_periods": 1},
    }
    first = report["periods"][1]["first_attempt"]
    assert first["distinct_supplied_prompt_count"] == 1
    assert first["all_three_arms"] == {
        "all_grammar_valid": True, "exact_expression_match": False, "canonical_ast_match": True,
    }
    assert report["periods"][0]["first_attempt"]["all_three_arms"]["exact_expression_match"] is None


@pytest.mark.parametrize("first_invalid", [True, False], ids=["invalid-first", "unusable-first"])
def test_first_charged_eligible_baseline_skips_invalid_and_unusable_records(tmp_path, evidence, first_invalid):
    def change(_, submissions):
        item = submissions["episodes"][0]
        raws = [r["raw_response"] for r in item["submission"]["records"]]
        if first_invalid:
            raws[0] = "invalid JSON"
            rebuild(item, raws=raws)
        else:
            rebuild(item, feedback=lambda expression: {
                **metrics(-0.4 if expression == "neg(returns)" else 0.1),
                "usable": expression not in ("returns", "(returns)"),
            })

    row = invoke(write_fixture(tmp_path, evidence, mutate=change))["periods"][0]["by_arm"][ARMS[0]]
    assert row["first_charged_eligible_proposal"]["attempt"] == (2 if first_invalid else 5)
    assert row["historical_comparisons"]["selected_minus_first_charged_eligible_abs_ic"] == pytest.approx(
        0.3 if first_invalid else 0.0)
    assert row["counts"]["feedback_unusable_count"] == (0 if first_invalid else 2)
    assert row["counts"]["charged_attempt_count"] == 6


@pytest.mark.parametrize("values,usable,expected", [
    ([0.0, 0.0], [True, True], 0.0), ([-0.9, 0.2], [False, True], 0.2),
    ([-0.9, 0.2], [False, False], None),
])
def test_initial_probe_benchmark_uses_usability_and_preserves_zero_and_unavailable(
    tmp_path, evidence, values, usable, expected,
):
    def change(contract, submissions):
        observation = initial()
        for probe, value, flag in zip(observation["probe_evidence"], values, usable, strict=True):
            probe.update(feedback=metrics(value), feedback_usable=flag)
        for item in submissions["episodes"][:3]:
            rebuild(item, observation=observation)
        prompt = ResearchEpisode(ARMS[0], observation, lambda _: None).prompt()
        contract["initial_prompt_sha256"]["2020-H1"] = hashlib.sha256(prompt.encode()).hexdigest()

    report = invoke(write_fixture(tmp_path, evidence, mutate=change))
    period = report["periods"][0]
    assert period["common_initial_probes"]["usable_probe_count"] == sum(usable)
    row = period["by_arm"][ARMS[0]]["historical_comparisons"]
    assert row["best_initial_probe_abs_ic"] == expected
    if expected is None:
        assert row["selected_minus_best_initial_probe_abs_ic"] is None
        assert report["all"]["historical_comparisons"]["best_initial_probe_abs_ic"]["unavailable_episodes"] == 3
    else:
        assert row["selected_minus_best_initial_probe_abs_ic"] == pytest.approx(0.4 - expected)


@pytest.mark.parametrize("count", [1, 3])
def test_wrong_initial_probe_count_fails_replay_before_diagnostics(tmp_path, evidence, count):
    def change(_, submissions):
        saved = submissions["episodes"][0]["submission"]
        probes = saved["initial_evidence"]["probe_evidence"]
        if count == 1:
            probes.pop()
        else:
            probes.append(copy.deepcopy(probes[0]))
        saved.update(seal(saved))

    with pytest.raises(ValueError, match="two initial probes"):
        invoke(write_fixture(tmp_path, evidence, mutate=change))


@pytest.mark.parametrize("mode", ["missing-episode", "changed-duplicate", "changed-prompt"])
def test_resealed_tampering_does_not_produce_partial_diagnostics(tmp_path, evidence, mode):
    def change(_, submissions):
        if mode == "missing-episode":
            submissions["episodes"].pop()
        else:
            saved = submissions["episodes"][0]["submission"]
            record = saved["records"][0]
            if mode == "changed-duplicate":
                record["canonical_duplicate"] = True
            else:
                record["prompt_sha256"] = "f" * 64
            saved.update(seal(saved))

    with pytest.raises(ValueError):
        invoke(write_fixture(tmp_path, evidence, mutate=change))


@pytest.mark.parametrize("index", [0, 1], ids=["contract", "submissions"])
def test_analysis_uses_same_immutable_bytes_as_replay(tmp_path, evidence, monkeypatch, index):
    paths = write_fixture(tmp_path, evidence)
    original = paths[index].read_bytes()
    actual_replay = diagnostics.replay_study

    def verify_and_change_original(contract, submissions, **kwargs):
        assert contract != paths[0] and submissions != paths[1]
        verified = actual_replay(contract, submissions, **kwargs)
        paths[index].write_bytes(b"changed after successful verification")
        return verified

    monkeypatch.setattr(diagnostics, "replay_study", verify_and_change_original)
    report = invoke(paths)
    assert report["all"]["counts"]["charged_attempt_count"] == 180
    assert report["inputs"]["contract" if index == 0 else "submissions"] == {
        "sha256": hashlib.sha256(original).hexdigest(), "bytes": len(original),
    }


def test_cli_new_output_only_and_no_artifact_on_failed_gate(tmp_path, evidence, monkeypatch):
    paths = write_fixture(tmp_path, evidence)
    base = ["--contract", str(paths[0]), "--submissions", str(paths[1]), "--source-root", str(ROOT)]
    output = tmp_path / "diagnostics.json"
    diagnostics.main(base + ["--output", str(output)])
    original = output.read_bytes()
    assert json.loads(original)["all"]["counts"]["charged_attempt_count"] == 180
    for destination in (output, paths[0], paths[1], Path(diagnostics.__file__)):
        with pytest.raises(SystemExit):
            diagnostics.main(base + ["--output", str(destination)])
    assert output.read_bytes() == original
    failed = tmp_path / "failed.json"

    def reject(*_, **__):
        raise ValueError("invalid fixed bank")

    monkeypatch.setattr(diagnostics, "replay_study", reject)
    with pytest.raises(ValueError, match="invalid fixed bank"):
        diagnostics.main(base + ["--output", str(failed)])
    assert not failed.exists()
