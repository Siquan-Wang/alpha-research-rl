"""Artificial five-report provenance and signed reward-linkage comparisons."""

import copy
import hashlib
import json

import pytest
from test_financial_analysis import checkpoint, outcome
from test_financial_analysis import reports as base_reports

from alpha_research_rl.financial_analysis import AnalysisInputError, _sha
from alpha_research_rl.linkage_analysis import CONTROLS, ORIGINALS, ROLES, STUDY, analyze_linkage


@pytest.fixture
def inputs(tmp_path):
    base = base_reports.__wrapped__(tmp_path)
    reports = {}
    rename = dict(zip(("sft", "rl23", "rl29"), ORIGINALS, strict=True))
    suite = copy.deepcopy(base["sft"]["manifest"]["config"]["frozen_suite"])
    suite["checkpoints"] = {rename[label]: value for label, value in suite["checkpoints"].items()}
    for old, new in rename.items():
        report = copy.deepcopy(base[old])
        config = report["manifest"]["config"]
        config.update(label=new, frozen_suite=copy.deepcopy(suite))
        reports[new] = report
    sources = {label: {"file": label + ".json", "sha256": _sha(reports[label])} for label in ORIGINALS}
    extended = copy.deepcopy(suite)
    extended.update(study=STUDY, frozen_utc="2026-10-01T04:20:00+00:00", original_reports=copy.deepcopy(sources),
                    original_frozen_suite_sha256=_sha(suite))
    extended["checkpoints"].update({label: checkpoint(label) for label in CONTROLS})
    for index, label in enumerate(CONTROLS):
        report = copy.deepcopy(reports[ORIGINALS[index + 1]])
        report["manifest"]["created_utc"] = "2026-10-01T04:30:00+00:00"
        report["manifest"]["config"].update(label=label, checkpoint=checkpoint(label),
                                             frozen_suite=copy.deepcopy(extended))
        report["manifest"]["actor"]["starting_adapter_name"] = label
        for episode in report["episodes"]:
            for record in episode["records"]:
                expression = f"mul({record['strict']['expression']},{index + 2})"
                ic = record["strict"]["oriented_future_ic"] - (.01 if index == 0 else -.02)
                scored = outcome(expression, ic)
                # Give the two controls different evidence effects too.
                if record["condition"] == "exchanged":
                    scored = outcome(expression, ic - .002 * (index + 1))
                action = {"action": "propose", "expression": expression}
                record.update(action=action, text=json.dumps(action), outcome=copy.deepcopy(scored),
                              strict=copy.deepcopy(scored), fence_tolerant_secondary=copy.deepcopy(scored))
        reports[label] = report
    return reports, sources


def analyze(inputs):
    return analyze_linkage(*inputs)


def test_exact_five_roles_signed_seed_pairs_and_unchanged_originals(inputs):
    before = copy.deepcopy(inputs)
    result = analyze(inputs)
    assert inputs == before
    assert result["roles"] == ROLES
    assert len(result["task_rows"]) == 10 and len(result["year_rows"]) == 5
    cell = result["overall"]["metrics"]["strict"]["stochastic"]
    assert cell["correct_vs_placebo"]["23"]["true"]["reward_delta"] == pytest.approx(.01)
    assert cell["correct_vs_placebo"]["29"]["true"]["reward_delta"] == pytest.approx(-.02)
    assert cell["correct_vs_placebo"]["23"]["grounding_interaction"]["reward_delta"] == pytest.approx(-.002)
    assert cell["correct_vs_placebo"]["29"]["grounding_interaction"]["reward_delta"] == pytest.approx(-.004)
    assert set(cell["policy_vs_sft"]) == {*ORIGINALS[1:], *CONTROLS}
    assert set(cell["policies"]) == set(ROLES.values())
    assert cell["policies"][ORIGINALS[0]]["true"]["n_samples"] == 80
    assert result["overall"]["references"] == result["original_results"]["overall"]["references"]
    for role in ORIGINALS:
        assert cell["policies"][role] == result["original_results"]["overall"]["metrics"]["strict"]\
            ["stochastic"]["policies"][role]


def test_year_means_equal_two_halves_and_all_tasks_retained(inputs):
    result = analyze(inputs)
    for index, row in enumerate(result["year_rows"]):
        annual = row["metrics"]["strict"]["stochastic"]["correct_vs_placebo"]["29"]["true"]["reward_delta"]
        halves = [task["metrics"]["strict"]["stochastic"]["correct_vs_placebo"]["29"]["true"]["reward_delta"]
                  for task in result["task_rows"][2 * index:2 * index + 2]]
        assert annual == pytest.approx(sum(halves) / 2)
    assert set(result["correct_vs_placebo_seed_summary"]["strict"]["stochastic"]["true"]["per_seed"]) == {"23", "29"}
    assert result["correct_vs_placebo_seed_summary"]["strict"]["stochastic"]["true"]["mean"] == pytest.approx(-.005)


def test_control_all_invalid_included_in_denominator_and_decomposition(inputs):
    for episode in inputs[0][CONTROLS[0]]["episodes"]:
        for record in episode["records"]:
            invalid = outcome(None, 0, False)
            record.update(text='{"action":"stop"}', action={"action": "stop"}, outcome=copy.deepcopy(invalid),
                          strict=copy.deepcopy(invalid), fence_tolerant_secondary=copy.deepcopy(invalid))
    cell = analyze(inputs)["overall"]["metrics"]["strict"]["stochastic"]
    placebo = cell["policies"][CONTROLS[0]]["true"]
    assert placebo["mean_reward"] == -1.01 and placebo["n_samples"] == placebo["failed_samples"] == 80
    assert placebo["mean_oriented_ic_valid_only"] is None
    delta = cell["correct_vs_placebo"]["23"]["true"]
    assert delta["reward_delta"] == pytest.approx(delta["failure_penalty_component_delta"]
                                                + delta["all_proposal_ic_contribution_delta"])
    assert delta["conditional_valid_ic_delta_secondary"] is None


def test_secondary_fence_reparse_and_greedy_remain_separate(inputs):
    record = inputs[0][CONTROLS[0]]["episodes"][0]["records"][0]
    record["text"] = "```json\n" + record["text"] + "\n```"
    record["action"] = {"action": "invalid"}
    record["strict"] = outcome(None, 0, False)
    record["outcome"] = copy.deepcopy(record["strict"])
    result = analyze(inputs)["overall"]["metrics"]
    assert result["strict"]["stochastic"]["policies"][CONTROLS[0]]["true"]["valid_samples"] == 79
    assert result["fence_tolerant_secondary"]["stochastic"]["policies"][CONTROLS[0]]["true"]["valid_samples"] == 80
    assert result["strict"]["greedy"]["policies"][CONTROLS[0]]["true"]["n_samples"] == 10


@pytest.mark.parametrize("change", ["subset_checkpoint", "original_file", "old_suite_hash", "extra_checkpoint",
                                     "wrong_study", "late_freeze", "before_original", "wrong_own_checkpoint"])
def test_reject_undeclared_suite_extension_or_bad_frozen_identity(inputs, change):
    reports, _ = inputs
    suites = [reports[label]["manifest"]["config"]["frozen_suite"] for label in CONTROLS]
    for suite in suites:
        if change == "subset_checkpoint":
            suite["checkpoints"][ORIGINALS[0]] = checkpoint("different original")
        elif change == "original_file":
            suite["original_reports"][ORIGINALS[0]]["sha256"] = "0" * 64
        elif change == "old_suite_hash":
            suite["original_frozen_suite_sha256"] = "0" * 64
        elif change == "extra_checkpoint":
            suite["checkpoints"]["extra"] = checkpoint("extra")
        elif change == "wrong_study":
            suite["study"] = "financial-proposal-v1"
        elif change == "late_freeze":
            suite["frozen_utc"] = "2026-10-01T04:40:00+00:00"
        elif change == "before_original":
            suite["frozen_utc"] = "2026-10-01T04:05:00+00:00"
    if change == "wrong_own_checkpoint":
        reports[CONTROLS[0]]["manifest"]["config"]["checkpoint"] = checkpoint("wrong")
    with pytest.raises(AnalysisInputError):
        analyze(inputs)


@pytest.mark.parametrize("change", ["prompt", "seed", "missing_slot", "duplicate_slot", "runtime", "data",
                                     "contract", "task", "reward", "eos", "schema", "true_study"])
def test_reject_control_contract_trace_or_scorer_mismatch(inputs, change):
    report = inputs[0][CONTROLS[0]]
    config = report["manifest"]["config"]
    episode = report["episodes"][0]
    record = episode["records"][0]
    if change == "prompt":
        record["prompt_ids"][0] += 1
    elif change == "seed":
        record["seed"] += 1
    elif change == "missing_slot":
        episode["records"].pop()
    elif change == "duplicate_slot":
        episode["records"].append(copy.deepcopy(record))
    elif change == "runtime":
        report["manifest"]["actor"]["precision"] = "bfloat16"
    elif change == "data":
        config["snapshot_sha256"] = "0" * 64
    elif change == "contract":
        config["evaluation_contract"]["numeric_protocol"]["cost"] = .02
    elif change == "task":
        episode["task"]["assessment_signal_dates"][0] = "2025-01-01"
    elif change == "reward":
        record["strict"]["reward"] += .01
    elif change == "eos":
        record["terminated"] = False
    elif change == "schema":
        record["text"] = '{"action":"stop"}'
        record["action"] = {"action": "stop"}
    elif change == "true_study":
        config["study"] = STUDY
    with pytest.raises(AnalysisInputError):
        analyze(inputs)


def test_validate_original_trio_before_considering_controls(inputs):
    reports = inputs[0]
    reports[ORIGINALS[0]]["episodes"][0]["records"][0]["seed"] += 1
    reports[CONTROLS[0]]["manifest"]["config"]["frozen_suite"] = None
    with pytest.raises(AnalysisInputError, match="RNG seed mismatch"):
        analyze(inputs)


def test_unchanged_same_formula_score_required_across_all_five(inputs):
    record = inputs[0][CONTROLS[0]]["episodes"][0]["records"][0]
    old = inputs[0][ORIGINALS[1]]["episodes"][0]["records"][0]
    record["action"] = copy.deepcopy(old["action"])
    record["text"] = old["text"]
    for parser in ("strict", "fence_tolerant_secondary", "outcome"):
        record[parser]["expression"] = old[parser]["expression"]
    with pytest.raises(AnalysisInputError, match="same formula"):
        analyze(inputs)


def test_cli_validates_original_file_bytes_and_emits_separate_control_roles(inputs, tmp_path, monkeypatch):
    from alpha_research_rl.linkage_analysis import main

    reports, _ = inputs
    paths, sources = {}, {}
    for label in ORIGINALS:
        paths[label] = tmp_path / (label + ".json")
        raw = json.dumps(reports[label], indent=2).encode()
        paths[label].write_bytes(raw)
        sources[label] = {"file": paths[label].name, "sha256": hashlib.sha256(raw).hexdigest()}
    for label in CONTROLS:
        reports[label]["manifest"]["config"]["frozen_suite"]["original_reports"] = copy.deepcopy(sources)
        paths[label] = tmp_path / (label + ".json")
        paths[label].write_text(json.dumps(reports[label]), encoding="utf-8")
    destination = tmp_path / "paired-linkage.json"
    argv = ["linkage_analysis"]
    for flag, label in zip(("sft", "rl23", "rl29", "placebo23", "placebo29"), ROLES.values(), strict=True):
        argv.extend(["--" + flag, str(paths[label])])
    argv.extend(["--output", str(destination)])
    monkeypatch.setattr("sys.argv", argv)
    main()
    result = json.loads(destination.read_text(encoding="utf-8"))
    assert result["source_reports"][ORIGINALS[0]] == sources[ORIGINALS[0]]
    assert result["roles"]["placebo_seed23"] == CONTROLS[0]
    # Even a whitespace-only change retains parsed outcomes but invalidates
    # the byte identity that was frozen before control evaluation.
    with paths[ORIGINALS[0]].open("ab") as handle:
        handle.write(b"\n")
    with pytest.raises(AnalysisInputError, match="file binding"):
        main()
