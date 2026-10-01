"""Original artificial complete-suite fixtures; no market data or model calls."""

import copy
import hashlib
import json
from datetime import date, timedelta

import pytest

from alpha_research_rl.financial_analysis import AnalysisInputError, analyze_reports
from alpha_research_rl.financial_evaluation import evaluation_contract
from alpha_research_rl.financial_tasks import EXPECTED_RAW_SHA256

LABELS = ("sft", "rl23", "rl29")


def checkpoint(label):
    files = [{"file": name, "sha256": hashlib.sha256((label + name).encode()).hexdigest(), "bytes": 32}
             for name in ("adapter_config.json", "adapter_model.safetensors")]
    digest = hashlib.sha256()
    for row in files:
        digest.update(row["file"].encode())
        digest.update(row["sha256"].encode())
    return {"adapter_name": label, "files": files, "combined_sha256": digest.hexdigest()}


def outcome(expression, ic, valid=True):
    if not valid:
        return {"expression": None, "status": "invalid", "reason": "invalid_json_action", "reward": -1.01,
                "cost": .01, "oriented_future_ic": None, "orientation": None, "feedback": None, "assessment": None}
    metrics = {"mean_ic": ic, "coverage": 1., "n_dates": 100, "n_signal_dates": 100, "ic_std": .2}
    return {"expression": expression, "status": "ok", "reason": None, "reward": ic - .01, "cost": .01,
            "oriented_future_ic": ic, "orientation": 1, "feedback": metrics | {"mean_ic": .1},
            "assessment": metrics}


def reference(ic, count, expression=None):
    result = {"mean_reward": ic - .01, "n_samples": count, "valid_samples": count,
              "invalid_or_unscorable_samples": 0, "valid_fraction": 1., "mean_oriented_ic_valid_only": ic}
    if expression:
        result["expression"] = expression
    return result


def task_manifest(year, half, task_index):
    """Artificial but internally consistent complete-period date/count metadata."""
    assessment_start = date(year, 1 if half == 1 else 7, 1)
    assessment_stop = date(year, 7, 1) if half == 1 else date(year + 1, 1, 1)
    feedback_start = date(year - 1, 7, 1) if half == 1 else date(year, 1, 1)
    result = {"task_id": f"{year}-H{half}", "year": year, "half": half,
              "horizon_sessions": 5, "split": "transfer"}
    for index, (period, start, stop) in enumerate((("feedback", feedback_start, assessment_start),
                                                  ("assessment", assessment_start, assessment_stop))):
        left = 4000 + 105 * (task_index + index)
        result.update({f"{period}_bounds_half_open": [left, left + 100],
                       f"raw_{period}_bounds_half_open": [left, left + 105],
                       f"{period}_label_boundary": left + 105,
                       f"{period}_signal_dates": [start.isoformat(), (stop - timedelta(days=8)).isoformat()],
                       f"{period}_label_support_dates": [(start + timedelta(days=7)).isoformat(),
                                                         (stop - timedelta(days=1)).isoformat()]})
    return result


@pytest.fixture
def reports(tmp_path):
    # Tokenizer content is a marked artificial fixture, not a downloaded model.
    (tmp_path / "tokenizer.json").write_text('{"fixture":true}', encoding="utf-8")
    contract = evaluation_contract(tmp_path)
    suite = {"study": "financial-proposal-v1", "frozen_utc": "2026-10-01T04:00:00+00:00",
             "checkpoints": {label: checkpoint(label) for label in LABELS},
             "fixed_reference": "delay(returns,1)", "stochastic_draws_per_task_condition": 8,
             "greedy_draws_per_task_condition": 1}
    result = {}
    for actor_index, label in enumerate(LABELS):
        config = {"study": "financial-proposal-v1", "split": "transfer", "label": label,
                  "snapshot_sha256": EXPECTED_RAW_SHA256, "checkpoint": checkpoint(label),
                  "frozen_suite": copy.deepcopy(suite), "stochastic_draws_per_task_condition": 8,
                  "greedy_draws_per_task_condition": 1, "conditions": ["true", "exchanged"], "max_tokens": 64,
                  "strict_primary": True, "secondary_reparse_same_completion": True,
                  "evaluation_contract": copy.deepcopy(contract)}
        actor = {"precision": "float32", "tf32": False, "use_model_defaults": False,
                 "starting_adapter_name": label, "base_model": {"model_id": "artificial fixture"},
                 "generation_config": {"do_sample": True, "temperature": 1., "top_p": 1., "top_k": 0,
                                       "eos_token_id": [7]}}
        episodes = []
        for task_index in range(10):
            year, half = 2020 + task_index // 2, 1 + task_index % 2
            base = .01 * (task_index - 4)
            records = []
            for condition_index, condition in enumerate(("true", "exchanged")):
                for decoding in ("stochastic", "greedy"):
                    for draw in range(8 if decoding == "stochastic" else 1):
                        slot_number = draw if decoding == "stochastic" else 8
                        k = 1 + actor_index * 18 + condition_index * 9 + slot_number
                        expression = f"delay(returns,{k})"
                        # Different signed effects across years and seeds. Greedy
                        # deliberately reverses one stochastic effect.
                        delta = 0 if actor_index == 0 else (.02 if actor_index == 1 else -.01)
                        delta *= 1 if task_index % 2 == 0 else -2
                        if decoding == "greedy":
                            delta = -.04 if actor_index == 1 else 0
                        evidence_penalty = .003 * actor_index if condition == "exchanged" else 0
                        ic = base + delta - evidence_penalty
                        valid = not (actor_index == 0 and decoding == "stochastic" and draw == 0)
                        scored = outcome(expression, ic, valid)
                        action = {"action": "propose", "expression": expression} if valid else {"action": "stop"}
                        records.append({"condition": condition, "decoding": decoding, "draw": draw,
                            "seed": 80000 + task_index * 100 + (draw if decoding == "stochastic" else 99),
                            "prompt_ids": [1, year, half, 30 + condition_index],
                            "completion_ids": [100 + k, 7], "terminated": True,
                            "text": json.dumps(action), "action": action, "outcome": copy.deepcopy(scored),
                            "strict": copy.deepcopy(scored), "fence_tolerant_secondary": copy.deepcopy(scored)})
            episodes.append({"task": task_manifest(year, half, task_index), "records": records,
                             "means": {"deliberately": "untrusted and ignored"},
                             "references": {"uniform_grid": reference(.005, 16),
                                            "feedback_greedy_grid": reference(-.01, 1),
                                            "training_best_fixed": reference(.015, 1, "delay(returns,1)")}})
        result[label] = {"manifest": {"created_utc": "2026-10-01T04:10:00+00:00", "config": config,
                                      "actor": actor, "packages": {"fixture": "original-artificial"}},
                         "training_teacher_target_expressions": ["returns"], "episodes": episodes}
    return result


def analyze(reports):
    return analyze_reports(reports, "sft", ("rl23", "rl29"))


def test_all_signed_task_year_effects_and_both_seeds_retained(reports):
    report = analyze(reports)
    assert len(report["task_rows"]) == 10 and len(report["year_rows"]) == 5
    task = report["task_rows"][0]["metrics"]["strict"]["stochastic"]
    assert task["policies"]["sft"]["true"]["valid_samples"] == 7
    # Task zero: RL23 IC=-.02, SFT usable IC=-.04, seven successes.
    expected = (-.02 - .01) - (7 * (-.04 - .01) - 1.01) / 8
    assert task["rl_vs_sft"]["rl23"]["true"]["reward_delta"] == pytest.approx(expected)
    assert task["rl_vs_sft"]["rl23"]["true"]["failure_penalty_component_delta"] == .125
    assert task["rl_vs_sft"]["rl23"]["true"]["all_proposal_ic_contribution_delta"] == pytest.approx(.015)
    yearly = report["year_rows"][0]["metrics"]["strict"]["stochastic"]["rl_vs_sft"]["rl23"]["true"]
    halves = [row["metrics"]["strict"]["stochastic"]["rl_vs_sft"]["rl23"]["true"]["reward_delta"]
              for row in report["task_rows"][:2]]
    assert yearly["reward_delta"] == pytest.approx(sum(halves) / 2)
    seed_summary = report["rl_seed_summary"]["strict"]["stochastic"]["true"]
    assert set(seed_summary["per_rl_seed"]) == {"rl23", "rl29"}
    assert seed_summary["observed_min"] == min(seed_summary["per_rl_seed"].values())
    assert seed_summary["observed_max"] == max(seed_summary["per_rl_seed"].values())
    assert seed_summary["range_is_not_confidence_interval"] is True
    greedy = report["overall"]["metrics"]["strict"]["greedy"]["rl_vs_sft"]["rl23"]["true"]
    assert greedy["reward_delta"] == pytest.approx(-.04)


def test_evidence_grounding_is_difference_of_paired_differences(reports):
    cell = analyze(reports)["overall"]["metrics"]["strict"]["stochastic"]
    assert cell["evidence_effects"]["sft"]["reward_delta"] == pytest.approx(0)
    assert cell["evidence_effects"]["rl23"]["reward_delta"] == pytest.approx(.003)
    assert cell["rl_vs_sft"]["rl29"]["grounding_interaction"]["reward_delta"] == pytest.approx(.006)


def test_all_invalid_retains_penalty_and_null_conditional_ic(reports):
    for episode in reports["rl23"]["episodes"]:
        for record in episode["records"]:
            invalid = outcome(None, 0, False)
            record.update(text='{"action":"stop"}', action={"action": "stop"}, outcome=copy.deepcopy(invalid),
                          strict=copy.deepcopy(invalid), fence_tolerant_secondary=copy.deepcopy(invalid))
    cell = analyze(reports)["overall"]["metrics"]["strict"]["stochastic"]
    rl = cell["policies"]["rl23"]["true"]
    assert rl["mean_reward"] == -1.01 and rl["valid_samples"] == 0
    assert rl["all_proposal_ic_contribution"] == 0 and rl["mean_oriented_ic_valid_only"] is None
    assert cell["rl_vs_sft"]["rl23"]["true"]["conditional_valid_ic_delta_secondary"] is None


def test_fence_is_secondary_and_does_not_add_proposal_draws(reports):
    record = reports["rl23"]["episodes"][0]["records"][0]
    valid = copy.deepcopy(record["strict"])
    record["text"] = "```json\n" + record["text"] + "\n```"
    record["action"] = {"action": "invalid"}
    record["strict"] = outcome(None, 0, False)
    record["outcome"] = copy.deepcopy(record["strict"])
    record["fence_tolerant_secondary"] = valid
    report = analyze(reports)
    strict = report["task_rows"][0]["metrics"]["strict"]["stochastic"]["policies"]["rl23"]["true"]
    secondary = report["task_rows"][0]["metrics"]["fence_tolerant_secondary"]["stochastic"]["policies"]["rl23"]["true"]
    assert strict["n_samples"] == secondary["n_samples"] == 8
    assert strict["valid_samples"] == 7 and secondary["valid_samples"] == 8


@pytest.mark.parametrize("mutation,match", [
    (lambda r: r["rl23"]["manifest"]["config"].update(snapshot_sha256="0" * 64), "snapshot"),
    (lambda r: r["rl23"]["manifest"]["config"].update(stochastic_draws_per_task_condition=4), "draw count"),
    (lambda r: r["rl23"]["manifest"]["config"]["checkpoint"].update(combined_sha256="0" * 64), "combined hash"),
    (lambda r: r["rl23"]["manifest"]["config"]["evaluation_contract"].update(proposal_system_sha256="0" * 64),
     "contract hash"),
    (lambda r: r["rl23"]["episodes"][0]["records"][0].update(seed=999), "RNG"),
    (lambda r: r["rl23"]["episodes"][0]["records"][0].update(prompt_ids=[999]), "prompt tokens"),
    (lambda r: r["rl23"]["episodes"][0]["records"].pop(), "missing proposal"),
    (lambda r: r["rl23"]["episodes"].pop(), "ten transfer"),
    (lambda r: r["rl23"]["episodes"][0]["task"].update(horizon_sessions=6), "horizon"),
    (lambda r: r["rl23"]["manifest"]["actor"].update(precision="bfloat16"), "precision"),
    (lambda r: r["rl23"]["episodes"][0]["records"][0]["strict"].update(reward=float("nan")), "finite"),
])
def test_rejects_mismatched_or_incomplete_comparisons(reports, mutation, match):
    mutation(reports)
    with pytest.raises(AnalysisInputError, match=match):
        analyze(reports)


def test_duplicate_slot_and_missing_seed_are_never_silently_dropped(reports):
    records = reports["rl23"]["episodes"][0]["records"]
    records.append(copy.deepcopy(records[0]))
    with pytest.raises(AnalysisInputError, match="duplicate"):
        analyze(reports)
    del reports["rl29"]
    with pytest.raises(AnalysisInputError, match="exactly one SFT"):
        analyze(reports)


def test_rejects_post_start_freeze_and_reference_drift(reports):
    reports["sft"]["manifest"]["config"]["frozen_suite"]["frozen_utc"] = "2026-10-01T05:00:00+00:00"
    with pytest.raises(AnalysisInputError, match="before"):
        analyze(reports)
    reports["sft"]["manifest"]["config"]["frozen_suite"]["frozen_utc"] = "2026-10-01T04:00:00+00:00"
    reports["rl23"]["episodes"][0]["references"]["training_best_fixed"]["mean_reward"] += .1
    with pytest.raises(AnalysisInputError, match="reference outcomes"):
        analyze(reports)


def test_saved_summary_values_do_not_determine_analysis(reports):
    # Production analysis uses individual outcomes, not saved display summaries.
    first = analyze(reports)
    reports["rl23"]["summary"] = {"mean_reward": 999999.}
    assert analyze(reports)["overall"] == first["overall"]


@pytest.mark.parametrize("field,value,match", [
    ("assessment_signal_dates", ["2025-01-02", "2025-06-23"], "outside declared"),
    ("assessment_label_support_dates", ["2020-01-08", "2020-07-01"], "outside declared"),
    ("raw_feedback_bounds_half_open", [4000, 4104], "purge/boundary"),
    ("assessment_label_boundary", 4211, "purge/boundary"),
    ("feedback_signal_dates", ["2019-08-01", "2019-12-24"], "incomplete"),
])
def test_consistently_wrong_shared_chronology_is_rejected(reports, field, value, match):
    for report in reports.values():
        report["episodes"][0]["task"][field] = value
    with pytest.raises(AnalysisInputError, match=match):
        analyze(reports)


def test_consistently_fabricated_short_metric_support_is_rejected(reports):
    for report in reports.values():
        for record in report["episodes"][0]["records"]:
            for parser in ("strict", "fence_tolerant_secondary", "outcome"):
                if record[parser]["status"] == "ok":
                    for period in ("feedback", "assessment"):
                        record[parser][period].update(n_dates=1, n_signal_dates=1)
    with pytest.raises(AnalysisInputError, match="purged task bounds"):
        analyze(reports)


def test_boolean_draw_cannot_alias_integer_slot(reports):
    reports["sft"]["episodes"][0]["records"][0]["draw"] = False
    with pytest.raises(AnalysisInputError, match="noninteger draw"):
        analyze(reports)
