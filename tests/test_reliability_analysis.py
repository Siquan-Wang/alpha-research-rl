"""Artificial paired Monte Carlo calculations and saved-evidence integrity."""

import copy
import hashlib
import json
import math

import pytest
from test_linkage_analysis import inputs as linkage_inputs

from alpha_research_rl.financial_analysis import TASKS, AnalysisInputError, _sha
from alpha_research_rl.linkage_analysis import CONTROLS, ORIGINALS, ROLES, analyze_linkage
from alpha_research_rl.reliability_analysis import (
    COMPARISONS,
    _compare_complete,
    analyze_reliability,
    combine_tasks,
    leave_one_year_out,
    main,
    paired_task,
)


def outcome(ic=0.0, valid=True):
    return {"status": "ok" if valid else "invalid", "reward": ic - .01 if valid else -1.01,
            "oriented_future_ic": ic if valid else None}


def task(current, prior, index=0):
    return paired_task(current, prior, *TASKS[index])


def test_common_seed_covariance_cancels_shared_generation_noise():
    prior = [outcome(i / 16) for i in range(8)]
    current = [outcome(i / 16 + .125) for i in range(8)]
    paired = task(current, prior)
    wrong_pairing = task(current, list(reversed(prior)))
    assert paired["components"]["reward"]["mean"] == pytest.approx(.125)
    assert paired["components"]["reward"]["sample_variance"] < 1e-28
    assert wrong_pairing["components"]["reward"]["sample_variance"] > .01


def test_one_rare_avoided_failure_has_exact_mean_and_mcse():
    valid = [outcome()] * 8
    rare = task(valid, [outcome(valid=False), *valid[1:]])
    rows = [rare, *[task(valid, valid, i) for i in range(1, 10)]]
    summary = combine_tasks(rows)
    assert rare["components"]["reward"]["sample_variance"] == pytest.approx(1 / 8)
    assert summary["components"]["reward"]["mean"] == pytest.approx(.0125)
    assert summary["components"]["reward"]["estimated_mc_standard_error"] == pytest.approx(.0125)
    assert summary["components"]["validity"]["estimated_mc_standard_error"] == pytest.approx(.0125)
    assert summary["components"]["ic_contribution"]["estimated_mc_standard_error"] == 0
    assert summary["counts"]["current_only_valid"] == 1
    assert summary["counts"]["current_valid"] == 80 and summary["counts"]["prior_valid"] == 79


def test_component_covariance_is_retained_in_mc_variance():
    current = [outcome(-.5) if i % 2 else outcome(valid=False) for i in range(8)]
    prior = [outcome()] * 8
    rows = [task(current, prior, i) for i in range(10)]
    summary = combine_tasks(rows)
    a, b, c = [summary["components"][key] for key in ("reward", "validity", "ic_contribution")]
    covariance = summary["estimated_mc_covariance_validity_ic"]
    assert covariance < 0
    assert a["estimated_mc_variance"] == pytest.approx(
        b["estimated_mc_variance"] + c["estimated_mc_variance"] + 2 * covariance)
    assert a["estimated_mc_variance"] < b["estimated_mc_variance"] + c["estimated_mc_variance"]


def test_between_year_variation_is_not_generation_mcse_and_every_omission_is_retained():
    rows = [task([outcome(i / 32)] * 8, [outcome()] * 8, i) for i in range(10)]
    full = combine_tasks(rows)
    assert full["components"]["reward"]["estimated_mc_standard_error"] == 0
    omitted = leave_one_year_out(rows)
    assert [row["omitted_year"] for row in omitted] == list(range(2020, 2025))
    assert all(row["n_tasks"] == 8 and row["paired_draw_count"] == 64 for row in omitted)
    assert omitted[0]["means"]["reward"] == pytest.approx(sum(i / 32 for i in range(2, 10)) / 8)
    assert omitted[-1]["means"]["reward"] == pytest.approx(sum(i / 32 for i in range(8)) / 8)
    assert omitted[0]["changes_from_full_mean"]["reward"] > 0
    assert omitted[-1]["changes_from_full_mean"]["reward"] < 0
    for row in omitted:
        assert row["means"]["reward"] == pytest.approx(row["means"]["validity"] + row["means"]["ic_contribution"])


@pytest.mark.parametrize("current,prior", [(7, 8), (8, 7), (9, 9)])
def test_incomplete_or_inflated_draw_counts_are_rejected(current, prior):
    with pytest.raises(AnalysisInputError, match="eight"):
        task([outcome()] * current, [outcome()] * prior)


@pytest.fixture
def inputs(tmp_path):
    reports, original_sources = linkage_inputs.__wrapped__(tmp_path)
    sources = original_sources | {label: {"file": label + ".json", "sha256": _sha(reports[label])}
                                  for label in CONTROLS}
    saved = analyze_linkage(reports, original_sources)
    saved["source_reports"] = sources
    return reports, saved, sources


def test_all_six_pairs_both_conditions_and_accounting_reproduce_saved_analysis(inputs):
    before = copy.deepcopy(inputs)
    result = analyze_reliability(*inputs)
    assert inputs == before
    assert len(result["comparisons"]) == 12
    assert {(row["comparison"], row["condition"]) for row in result["comparisons"]} == {
        (name, condition) for name, _, _ in COMPARISONS for condition in ("true", "exchanged")}
    assert result["integrity"]["retained_original_records"] == 900
    assert result["integrity"]["stochastic_records_used"] == 800
    for row in result["comparisons"]:
        assert len(row["tasks"]) == 10 and len(row["leave_one_year_out"]) == 5
        assert row["overall"]["paired_draw_count"] == 80
        counts = row["overall"]["counts"]
        assert sum(counts[key] for key in ("both_valid", "both_failed", "current_only_valid", "prior_only_valid")) == 80
        assert counts["current_valid"] == counts["both_valid"] + counts["current_only_valid"]
        assert counts["prior_valid"] == counts["both_valid"] + counts["prior_only_valid"]
        assert all(len(t["paired_draw_differences"]) == 8 for t in row["tasks"])
        assert math.isfinite(row["overall"]["components"]["reward"]["estimated_mc_standard_error"])
    assert any("Zero observed" in text for text in result["limitations"])


def test_changed_saved_aggregate_cannot_be_silently_recomputed(inputs):
    reports, saved, sources = copy.deepcopy(inputs)
    saved["overall"]["metrics"]["strict"]["stochastic"]["correct_vs_placebo"]["23"]["true"]["reward_delta"] += .001
    with pytest.raises(AnalysisInputError, match="saved five-report analysis differs"):
        analyze_reliability(reports, saved, sources)


def test_tiny_finite_saved_float_arithmetic_drift_is_accepted(inputs):
    reports, saved, sources = copy.deepcopy(inputs)
    saved["overall"]["metrics"]["strict"]["stochastic"]["correct_vs_placebo"]["23"]["true"]["reward_delta"] += 1e-14
    assert analyze_reliability(reports, saved, sources)["integrity"]["complete_saved_analysis_reproduced"]


@pytest.mark.parametrize("current,saved", [
    ({"count": 1}, {"count": True}),
    ({"count": 1}, {"count": 1.0}),
    ({"count": 1}, {"count": 2}),
    ({"sha256": "abc"}, {"sha256": "abd"}),
    ({"rows": [1, 2]}, {"rows": [2, 1]}),
    ({"rows": [1, 2]}, {"rows": [1]}),
    ({"a": 1}, {"a": 1, "b": 2}),
    ({"a": None}, {"b": None}),
    ({"value": 0.25}, {"value": 0.25000001}),
    ({"value": float("nan")}, {"value": float("nan")}),
    ({"value": float("inf")}, {"value": float("inf")}),
    ({"integrity": {"constant": .25}}, {"integrity": {"constant": .25 + 1e-14}}),
])
def test_complete_comparison_retains_structure_metadata_and_float_boundaries(current, saved):
    with pytest.raises(AnalysisInputError, match="saved five-report analysis differs"):
        _compare_complete(current, saved)


def test_complete_comparison_accepts_nested_finite_float_roundoff_only():
    _compare_complete({"values": [0.0, 1.0, 100.0], "flag": True, "count": 3},
                      {"values": [1e-13, 1.0 + 1e-13, 100.0 + 1e-11], "flag": True, "count": 3})


def test_seed_mismatch_is_rejected_before_uncertainty_calculation(inputs):
    reports, saved, sources = copy.deepcopy(inputs)
    reports[CONTROLS[0]]["episodes"][0]["records"][0]["seed"] += 1
    with pytest.raises(AnalysisInputError, match="RNG seed differs"):
        analyze_reliability(reports, saved, sources)


@pytest.fixture
def saved_files(inputs, tmp_path):
    reports, _, _ = copy.deepcopy(inputs)
    folder = tmp_path / "reports"
    folder.mkdir()
    sources = {}
    for label in ORIGINALS:
        path = folder / (label + ".json")
        raw = json.dumps(reports[label], indent=2).encode()
        path.write_bytes(raw)
        sources[label] = {"file": path.name, "sha256": hashlib.sha256(raw).hexdigest()}
    originals = copy.deepcopy(sources)
    for label in CONTROLS:
        reports[label]["manifest"]["config"]["frozen_suite"]["original_reports"] = originals
        path = folder / (label + ".json")
        raw = json.dumps(reports[label], indent=2).encode()
        path.write_bytes(raw)
        sources[label] = {"file": path.name, "sha256": hashlib.sha256(raw).hexdigest()}
    saved = analyze_linkage(reports, originals)
    saved["source_reports"] = sources
    analysis = tmp_path / "paired.json"
    analysis.write_text(json.dumps(saved), encoding="utf-8")
    return analysis, folder, tmp_path / "reliability.json"


def test_cli_emits_source_binding_and_rejects_whitespace_byte_mutation(saved_files, monkeypatch):
    analysis, folder, output = saved_files
    monkeypatch.setattr("sys.argv", ["reliability", "--analysis", str(analysis), "--reports-dir", str(folder),
                                     "--output", str(output)])
    main()
    result = json.loads(output.read_text())
    assert result["source_analysis"]["sha256"] == hashlib.sha256(analysis.read_bytes()).hexdigest()
    assert len(result["comparisons"]) == 12
    original_output = output.read_bytes()
    report_path = folder / (ROLES["sft"] + ".json")
    with report_path.open("ab") as handle:
        handle.write(b"\n")
    with pytest.raises(AnalysisInputError, match="file-byte identity"):
        main()
    assert output.read_bytes() == original_output


@pytest.mark.parametrize("target", ["analysis", "report"])
def test_cli_never_overwrites_inputs(saved_files, monkeypatch, target):
    analysis, folder, _ = saved_files
    output = analysis if target == "analysis" else folder / (ROLES["sft"] + ".json")
    original = output.read_bytes()
    monkeypatch.setattr("sys.argv", ["reliability", "--analysis", str(analysis), "--reports-dir", str(folder),
                                     "--output", str(output)])
    with pytest.raises(AnalysisInputError, match="must not overwrite"):
        main()
    assert output.read_bytes() == original


def test_unsafe_report_filename_is_rejected_before_reading(saved_files, monkeypatch):
    analysis, folder, output = saved_files
    saved = json.loads(analysis.read_text())
    saved["source_reports"][ROLES["sft"]]["file"] = "../outside.json"
    analysis.write_text(json.dumps(saved), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["reliability", "--analysis", str(analysis), "--reports-dir", str(folder),
                                     "--output", str(output)])
    with pytest.raises(AnalysisInputError, match="safe basename"):
        main()
    assert not output.exists()
