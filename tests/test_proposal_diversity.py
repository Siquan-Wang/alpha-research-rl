"""Artificial saved-proposal accounting; no model/data/future-label scoring."""

import copy
import json
import math
import sys

import pytest
from test_linkage_analysis import inputs as linkage_inputs

from alpha_research_rl.financial_analysis import AnalysisInputError, _sha
from alpha_research_rl.financial_policy import expression_key
from alpha_research_rl.financial_tasks import EXPECTED_RAW_SHA256, TEACHER_GRID
from alpha_research_rl.proposal_diversity import (
    LABELS,
    SUPPORT,
    _distribution,
    analyze_diversity,
    summarize,
)


@pytest.fixture
def inputs(tmp_path):
    reports, originals = linkage_inputs.__wrapped__(tmp_path)
    sources = {label: originals.get(label, {"file": label + ".json", "sha256": _sha(reports[label])}) for label in LABELS}
    diagnostics, identities = {}, {}
    for label, report in reports.items():
        episodes = []
        for episode in report["episodes"]:
            task = episode["task"]
            length = task["feedback_bounds_half_open"][1] - task["feedback_bounds_half_open"][0]
            expressions = {record["strict"]["expression"] for record in episode["records"] if record["strict"]["status"] == "ok"}
            rows = []
            for expression in sorted(expressions):
                comparisons = [{"expression": expression, "reference": reference, "status": "ok", "reason": None,
                    "mean_daily_spearman": .5 if index == 0 else .2, "absolute_mean_daily_spearman": .5 if index == 0 else .2,
                    "daily_spearman_std": .1, "paired_cell_coverage": 1., "n_valid_dates": length,
                    "n_signal_dates": length, "required_valid_dates": math.ceil(.8 * length),
                    "near_exact_rank_equivalent": False, "tolerance": 1e-10} for index, reference in enumerate(TEACHER_GRID)]
                rows.append({"expression": expression, "canonical_ast": expression_key(expression), "status": "ok",
                             "nearest_teacher": copy.deepcopy(comparisons[0]), "teacher_comparisons": comparisons})
            episodes.append({"task": copy.deepcopy(task), "unique_valid_expression_diagnostics": rows})
        name = label + "-rank.json"
        diagnostics[name] = {"study": "financial-feedback-rank-alias-diagnostics-v1", "snapshot_sha256": EXPECTED_RAW_SHA256,
                            "references": list(TEACHER_GRID), "similarity_definition": "abs(mean daily cross-sectional Spearman)",
                            "rank_equivalence_tolerance": 1e-10, "support": dict(SUPPORT),
                            "input_report": sources[label]["file"], "episodes": episodes}
        identities[name] = {"file": name, "sha256": _sha(diagnostics[name])}
    return reports, sources, diagnostics, identities


def test_all900_attempts_conditions_decodings_and_tasks_remain_separate(inputs):
    before = copy.deepcopy(inputs)
    result = analyze_diversity(*inputs)
    assert inputs == before
    assert result["integrity"]["n_strict_proposals"] == 900
    assert result["integrity"]["all_five_linkage_report_validation_passed"] is True
    assert set(result["policies"]) == set(LABELS)
    for policy in result["policies"].values():
        assert len(policy["tasks"]) == 10
        for condition in ("true", "exchanged"):
            assert policy["overall"][condition]["stochastic"]["n_attempts"] == 80
            assert policy["overall"][condition]["greedy"]["n_attempts"] == 10
            assert all(task["cells"][condition]["stochastic"]["n_attempts"] == 8 for task in policy["tasks"])
    cell = result["policies"][LABELS[0]]["overall"]["true"]["stochastic"]
    assert cell["n_invalid_or_unscorable"] == 10
    assert cell["n_attempts"] == cell["n_valid"] + cell["n_invalid_or_unscorable"]
    serialized = json.dumps(result, allow_nan=False)
    assert "prompt_ids" not in serialized and "completion_ids" not in serialized and "oriented_future_ic" not in serialized


def test_entropy_concentration_and_all_invalid_are_explicit():
    result = _distribution({"a": 1, "b": 1})
    assert result["entropy_nats"] == pytest.approx(math.log(2))
    assert result["effective_number"] == pytest.approx(2)
    assert result["herfindahl_concentration"] == .5
    assert result["normalized_entropy"] == 1
    assert _distribution({"a": 4})["entropy_nats"] == 0
    assert _distribution({})["entropy_nats"] is None


def test_strings_ast_sign_aliases_invalids_and_weighted_rank_exposure():
    def record(expression, valid):
        return {"action": {"action": "propose", "expression": expression}, "text": json.dumps(expression),
                "strict": {"status": "ok" if valid else "invalid", "expression": expression,
                           "reason": None if valid else "unsupported_expression"}}

    records = [("2020-H1", record(expression, valid)) for expression, valid in
               (("returns", True), (" returns ", True), ("neg(returns)", True), ("close", False))]
    rank = {("2020-H1", expression_key(expression)): {"diagnostic": {"status": "ok", "nearest_teacher": {
                "near_exact_rank_equivalent": True, "absolute_mean_daily_spearman": 1}}}
            for expression in ("returns", "neg(returns)")}
    result = summarize(records, rank, ["returns"])
    assert result["n_attempts"] == 4 and result["n_valid"] == 3
    assert result["valid_expression_strings"]["unique"] == 3
    assert result["valid_canonical_asts"]["unique"] == 2
    assert result["all_attempt_frequencies"]["expression_strings"]["close"] == 1
    assert expression_key("close") not in result["valid_canonical_asts"]["frequencies"]
    assert result["top1_ast_exposure_all_attempts"] == .5
    assert result["top1_ast_exposure_valid_only"] == pytest.approx(2 / 3)
    assert result["memberships"]["teacher_grid_match"]["count_valid"] == 2
    assert result["feedback_rank_equivalence"]["n_near_exact_teacher_equivalent_proposals"] == 3
    assert result["feedback_rank_equivalence"]["fraction_all_attempts"] == .75
    invalid = summarize([("2020-H1", record("close", False))], {}, ["returns"])
    assert invalid["valid_canonical_asts"]["entropy_nats"] is None
    assert invalid["top1_ast_exposure_valid_only"] is None
    assert invalid["feedback_rank_equivalence"]["fraction_valid_only"] is None


@pytest.mark.parametrize("change", ["snapshot", "references", "tolerance", "task", "support", "missing_pair",
                                     "missing_expression", "ast", "equivalence", "nearest", "unknown_source"])
def test_reject_unmatched_or_incomplete_rank_diagnostics(inputs, change):
    _, _, diagnostics, _ = inputs
    diagnostic = next(iter(diagnostics.values()))
    episode = diagnostic["episodes"][0]
    row = episode["unique_valid_expression_diagnostics"][0]
    if change == "snapshot":
        diagnostic["snapshot_sha256"] = "0" * 64
    elif change == "references":
        diagnostic["references"] = diagnostic["references"][:-1]
    elif change == "tolerance":
        diagnostic["rank_equivalence_tolerance"] = .01
    elif change == "task":
        episode["task"]["feedback_bounds_half_open"][0] += 1
    elif change == "support":
        row["teacher_comparisons"][0]["n_valid_dates"] = 2
    elif change == "missing_pair":
        row["teacher_comparisons"].pop()
    elif change == "missing_expression":
        episode["unique_valid_expression_diagnostics"].pop(0)
    elif change == "ast":
        row["canonical_ast"] = expression_key("close")
    elif change == "equivalence":
        row["teacher_comparisons"][0]["near_exact_rank_equivalent"] = True
    elif change == "nearest":
        row["nearest_teacher"] = copy.deepcopy(row["teacher_comparisons"][1])
    else:
        diagnostic["input_report"] = "not-saved.json"
    with pytest.raises(AnalysisInputError):
        analyze_diversity(*inputs)


def test_duplicate_diagnostics_can_be_reused_but_conflicts_fail(inputs):
    _, _, diagnostics, identities = inputs
    _, value = next(iter(diagnostics.items()))
    diagnostics["copy.json"] = copy.deepcopy(value)
    identities["copy.json"] = {"file": "copy.json", "sha256": _sha(value)}
    result = analyze_diversity(*inputs)
    assert any("copy.json" in row["source_diagnostics"] for row in result["used_rank_mapping"])
    row = diagnostics["copy.json"]["episodes"][0]["unique_valid_expression_diagnostics"][0]
    row["teacher_comparisons"][0]["daily_spearman_std"] = .3
    row["nearest_teacher"]["daily_spearman_std"] = .3
    with pytest.raises(AnalysisInputError, match="conflicting reused"):
        analyze_diversity(*inputs)


def test_missing_or_mismatched_saved_draw_cannot_be_filtered(inputs):
    inputs[0][LABELS[-1]]["episodes"][0]["records"].pop()
    with pytest.raises(AnalysisInputError, match="missing control proposal slots"):
        analyze_diversity(*inputs)


def test_analysis_never_calls_market_evaluator_or_loads_a_panel(inputs, monkeypatch):
    import alpha_research_rl.factor_diagnostics as factor
    import alpha_research_rl.financial_tasks as tasks

    def forbidden(*args, **kwargs):
        raise AssertionError("new market scoring is forbidden")

    monkeypatch.setattr(factor, "evaluate_expression", forbidden)
    monkeypatch.setattr(factor, "load_pinned_panel", forbidden)
    monkeypatch.setattr(tasks.FinancialTask, "evaluate", forbidden)
    result = analyze_diversity(*inputs)
    assert result["integrity"]["n_strict_proposals"] == 900


def test_cli_output_collision_is_refused_before_read_or_write(tmp_path, monkeypatch):
    from alpha_research_rl.proposal_diversity import main

    evidence = tmp_path / "saved.json"
    evidence.write_bytes(b"preserve original bytes")
    monkeypatch.setattr(sys, "argv", ["proposal_diversity", "--sft", str(evidence), "--output",
                                    str(tmp_path / "alias" / ".." / "saved.json")])
    with pytest.raises(AnalysisInputError, match="output collides"):
        main()
    assert evidence.read_bytes() == b"preserve original bytes"
