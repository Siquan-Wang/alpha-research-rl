"""Strict paired analysis of three frozen financial proposal development reports.

No model or market data are loaded. All effects are descriptive, paired by the
ten declared half-years, and recomputed from retained proposal outcomes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

from .artifacts import write_json
from .financial_tasks import EXPECTED_RAW_SHA256
from .format_ablation import parse_completion
from .llm import parse_action

PARSERS = ("strict", "fence_tolerant_secondary")
CONDITIONS = ("true", "exchanged")
DECODINGS = ("stochastic", "greedy")
TASKS = tuple((year, half) for year in range(2020, 2025) for half in (1, 2))
FIXED_EXPRESSION = "delay(returns,1)"
COST = .01
INVALID = -1.01
DELTA_KEYS = ("reward_delta", "failure_penalty_component_delta", "all_proposal_ic_contribution_delta")


class AnalysisInputError(ValueError):
    """An input cannot support the registered matched comparison."""


def _require(condition, message):
    if not condition:
        raise AnalysisInputError(message)


def _finite(value, name):
    _require(type(value) in (int, float) and math.isfinite(value), f"{name}: expected finite number")
    return float(value)


def _close(left, right, name):
    _require(math.isclose(left, right, rel_tol=1e-10, abs_tol=1e-10), f"{name}: inconsistent value")


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha(value):
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _valid_hash(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _checkpoint(checkpoint):
    files = checkpoint.get("files", [])
    _require(files and len({row["file"] for row in files}) == len(files), "checkpoint: missing/duplicate files")
    digest = hashlib.sha256()
    for row in sorted(files, key=lambda item: item["file"]):
        name = row["file"]
        _require(isinstance(name, str) and not any(c in name for c in "/\\:"), "checkpoint: unsafe file name")
        _require(_valid_hash(row.get("sha256")), "checkpoint: invalid file hash")
        _require(type(row.get("bytes")) is int and row["bytes"] > 0, "checkpoint: invalid file size")
        digest.update(name.encode())
        digest.update(row["sha256"].encode())
    _require(digest.hexdigest() == checkpoint.get("combined_sha256"), "checkpoint: combined hash mismatch")


def _contract(contract):
    payload = {key: value for key, value in contract.items() if key != "shared_contract_sha256"}
    _require(_sha(payload) == contract.get("shared_contract_sha256"), "evaluation contract hash mismatch")
    _require(_valid_hash(contract.get("proposal_system_sha256")), "prompt contract hash missing")
    required = {"financial_evaluation.py", "financial_policy.py", "financial_tasks.py", "dsl.py",
                "evaluation.py", "llm.py", "format_ablation.py"}
    sources = contract.get("source_files_sha256", {})
    _require(required <= sources.keys() and all(_valid_hash(v) for v in sources.values()),
             "evaluation contract missing relevant source hashes")
    tokenizers = contract.get("tokenizer_files_sha256", {})
    _require(tokenizers and all(_valid_hash(v) for v in tokenizers.values()), "tokenizer contract missing")
    numeric = contract["numeric_protocol"]
    for key, value in {"horizon": 5, "cost": COST, "invalid_reward": INVALID, "min_coverage": .8,
                       "min_valid_fraction": .8, "min_valid_dates": 20, "max_lookback": 60,
                       "purged_signal_rows_at_each_halfyear_end": 5}.items():
        _require(numeric.get(key) == value, f"numeric contract mismatch: {key}")
    _require(numeric.get("supported_features") == ["returns"], "input field contract mismatch")
    _require(numeric.get("orientation") == "feedback mean IC<0 => -1; otherwise +1", "orientation mismatch")
    _require(contract.get("fixed_reference") == FIXED_EXPRESSION, "fixed reference mismatch")
    _require(contract.get("action_schema") == {"exact_keys": ["action", "expression"], "action": "propose",
             "requires_eos": True, "strict_json_primary": True}, "action schema mismatch")
    _require(contract.get("sampling") == {"temperature": 1.0, "top_p": 1.0, "top_k": 0, "max_tokens": 64,
             "seed_rule": "80000 + task_index*100 + draw; greedy draw=99"}, "sampling contract mismatch")


def _task_lengths(task, name):
    """Check declared chronology without loading or reconstructing market data."""
    year, half = task["year"], task["half"]
    _require(task.get("split") == "transfer", name + ": task split mismatch")
    assessment_start = date(year, 1 if half == 1 else 7, 1)
    assessment_stop = date(year, 7, 1) if half == 1 else date(year + 1, 1, 1)
    feedback_start = date(year - 1, 7, 1) if half == 1 else date(year, 1, 1)
    lengths, raw_intervals = {}, {}
    for period, start, stop in (("feedback", feedback_start, assessment_start),
                                ("assessment", assessment_start, assessment_stop)):
        raw = task.get(f"raw_{period}_bounds_half_open")
        purged = task.get(f"{period}_bounds_half_open")
        for bounds in (raw, purged):
            _require(isinstance(bounds, list) and len(bounds) == 2
                     and all(type(v) is int for v in bounds) and 0 <= bounds[0] < bounds[1],
                     name + ": invalid chronological row bounds")
        _require(raw[0] == purged[0] and raw[1] == purged[1] + 5
                 and task.get(f"{period}_label_boundary") == raw[1],
                 name + ": incorrect five-session purge/boundary")
        endpoints = []
        for field in (f"{period}_signal_dates", f"{period}_label_support_dates"):
            values = task.get(field)
            _require(isinstance(values, list) and len(values) == 2, name + ": missing period dates")
            try:
                parsed = [date.fromisoformat(v) for v in values]
            except (TypeError, ValueError) as exc:
                raise AnalysisInputError(name + ": invalid period dates") from exc
            _require(all(v.isoformat() == original for v, original in zip(parsed, values, strict=True)),
                     name + ": noncanonical period dates")
            _require(start <= parsed[0] <= parsed[1] < stop
                     and parsed[1] <= date(2024, 12, 31), name + ": dates outside declared half-year/hard cap")
            endpoints.append(parsed)
        signal, support = endpoints
        _require(signal[0] < support[0] <= signal[1] < support[1]
                 and signal[0] <= start + timedelta(days=7)
                 and support[1] >= stop - timedelta(days=7), name + ": incomplete or unordered period dates")
        lengths[period] = purged[1] - purged[0]
        _require(lengths[period] >= 20, name + ": truncated half-year signal support")
        raw_intervals[period] = raw
    _require(raw_intervals["feedback"][1] == raw_intervals["assessment"][0],
             name + ": feedback and assessment half-years are not adjacent")
    return lengths


def _metrics(metrics, name):
    mean = _finite(metrics.get("mean_ic"), name + ".mean_ic")
    coverage = _finite(metrics.get("coverage"), name + ".coverage")
    count, length = metrics.get("n_dates"), metrics.get("n_signal_dates")
    _require(-1 <= mean <= 1 and .8 <= coverage <= 1, name + ": unusable IC/coverage")
    _require(type(count) is int and type(length) is int and length > 0 and count <= length,
             name + ": invalid date counts")
    _require(count >= max(min(20, length), math.ceil(.8 * length)), name + ": insufficient dates")


def _outcome(outcome, name, lengths):
    reward = _finite(outcome.get("reward"), name + ".reward")
    _close(_finite(outcome.get("cost"), name + ".cost"), COST, name + ".cost")
    status = outcome.get("status")
    _require(status in ("ok", "invalid", "unscorable"), name + ": unknown status")
    for period, expected_length in lengths.items():
        metrics = outcome.get(period)
        if metrics is not None:
            _require(type(metrics.get("n_signal_dates")) is int
                     and metrics["n_signal_dates"] == expected_length,
                     name + ": signal support disagrees with purged task bounds")
            _require(type(metrics.get("n_dates")) is int and 0 <= metrics["n_dates"] <= expected_length,
                     name + ": invalid scored-date count")
    if status == "ok":
        _metrics(outcome["feedback"], name + ".feedback")
        _metrics(outcome["assessment"], name + ".assessment")
        orientation = -1 if outcome["feedback"]["mean_ic"] < 0 else 1
        _require(type(outcome.get("orientation")) is int and outcome["orientation"] == orientation,
                 name + ": orientation not fixed from feedback")
        ic = _finite(outcome.get("oriented_future_ic"), name + ".oriented_ic")
        _close(ic, orientation * outcome["assessment"]["mean_ic"], name + ".oriented_ic")
        _close(reward, ic - COST, name + ".reward")
        _require(isinstance(outcome.get("expression"), str) and outcome["expression"].strip(),
                 name + ": successful proposal has no expression")
    else:
        _close(reward, INVALID, name + ".failure_reward")
        _require(outcome.get("oriented_future_ic") is None, name + ": failure has predictive IC")
        _require(isinstance(outcome.get("reason"), str) and outcome["reason"], name + ": missing failure reason")


def _schema(action):
    return (isinstance(action, dict) and set(action) == {"action", "expression"}
            and action.get("action") == "propose" and isinstance(action.get("expression"), str))


def _summary(outcomes, n_tasks=1):
    valid = [row for row in outcomes if row["status"] == "ok"]
    n = len(outcomes)
    p = len(valid) / n
    contribution = math.fsum(row["oriented_future_ic"] for row in valid) / n
    reward = math.fsum(row["reward"] for row in outcomes) / n
    _close(reward, INVALID + p + contribution, "reward decomposition")
    return {"mean_reward": reward, "valid_fraction": p, "n_samples": n, "valid_samples": len(valid),
            "failed_samples": n - len(valid), "n_tasks": n_tasks,
            "all_proposal_ic_contribution": contribution,
            "mean_oriented_ic_valid_only": contribution * n / len(valid) if valid else None,
            "mean_raw_ic_valid_only": math.fsum(row["assessment"]["mean_ic"] for row in valid) / len(valid)
            if valid else None,
            "failure_reason_counts": dict(Counter(row["reason"] for row in outcomes if row["status"] != "ok"))}


def _difference(current, prior):
    valid = current["mean_oriented_ic_valid_only"], prior["mean_oriented_ic_valid_only"]
    result = {"reward_delta": current["mean_reward"] - prior["mean_reward"],
              "failure_penalty_component_delta": current["valid_fraction"] - prior["valid_fraction"],
              "all_proposal_ic_contribution_delta": current["all_proposal_ic_contribution"]
              - prior["all_proposal_ic_contribution"],
              "conditional_valid_ic_delta_secondary": valid[0] - valid[1] if None not in valid else None,
              "denominators": {"current_valid": current["valid_samples"], "prior_valid": prior["valid_samples"],
                               "current_all": current["n_samples"], "prior_all": prior["n_samples"]}}
    _close(result["reward_delta"], result["failure_penalty_component_delta"]
           + result["all_proposal_ic_contribution_delta"], "paired reward decomposition")
    return result


def _interaction(current, prior):
    result = {key: current[key] - prior[key] for key in DELTA_KEYS}
    _close(result["reward_delta"], result["failure_penalty_component_delta"]
           + result["all_proposal_ic_contribution_delta"], "grounding decomposition")
    return result


def _reference_summary(references):
    n = len(references)
    count = sum(row["n_samples"] for row in references)
    valid = sum(row["valid_samples"] for row in references)
    p = sum(row["valid_fraction"] for row in references) / n
    contribution = sum(row["valid_fraction"] * (row["mean_oriented_ic_valid_only"] or 0.)
                       for row in references) / n
    reward = sum(row["mean_reward"] for row in references) / n
    _close(reward, INVALID + p + contribution, "reference reward decomposition")
    return {"mean_reward": reward, "valid_fraction": p, "all_proposal_ic_contribution": contribution,
            "n_samples": count, "valid_samples": valid, "failed_samples": count - valid, "n_tasks": n,
            "mean_oriented_ic_valid_only": contribution * count / valid if valid else None}


def _validate_reports(reports, sft_label, rl_labels):
    labels = (sft_label, *rl_labels)
    _require(len(rl_labels) == 2 and len(set(labels)) == 3 and set(reports) == set(labels),
             "exactly one SFT and two separately identified RL reports are required")
    common, indexed, prompts = None, {}, {}
    task_manifests, common_references, formula_outcomes = {}, {}, {}
    for label in labels:
        report = reports[label]
        manifest, config = report["manifest"], report["manifest"]["config"]
        _require(config.get("study") == "financial-proposal-v1" and config.get("split") == "transfer",
                 f"{label}: only registered transfer reports can be combined")
        _require(config.get("label") == label, f"{label}: manifest label mismatch")
        _require(config.get("snapshot_sha256") == EXPECTED_RAW_SHA256, f"{label}: snapshot mismatch")
        suite = config["frozen_suite"]
        draws = config.get("stochastic_draws_per_task_condition")
        _require(draws in (4, 8) and type(draws) is int, f"{label}: unregistered draw count")
        _require(set(suite.get("checkpoints", {})) == set(labels), "frozen suite must contain exactly all three roles")
        _require(suite.get("study") == "financial-proposal-v1" and suite.get("fixed_reference") == FIXED_EXPRESSION,
                 "frozen suite study/reference mismatch")
        _require(suite.get("stochastic_draws_per_task_condition") == draws
                 and suite.get("greedy_draws_per_task_condition") == 1, "frozen suite draw count mismatch")
        frozen_at = datetime.fromisoformat(suite["frozen_utc"])
        started_at = datetime.fromisoformat(manifest["created_utc"])
        _require(frozen_at.tzinfo is not None and started_at.tzinfo is not None and frozen_at <= started_at,
                 "suite was not frozen before this evaluation started")
        _checkpoint(config["checkpoint"])
        _require(config["checkpoint"] == suite["checkpoints"][label], f"{label}: checkpoint differs from freeze")
        _contract(config["evaluation_contract"])
        _require(config.get("conditions") == list(CONDITIONS) and config.get("max_tokens") == 64
                 and config.get("greedy_draws_per_task_condition") == 1 and config.get("strict_primary") is True
                 and config.get("secondary_reparse_same_completion") is True,
                 f"{label}: prompt/decoding/parser contract mismatch")
        actor = manifest["actor"]
        _require(actor.get("precision") == "float32" and actor.get("tf32") is False
                 and actor.get("use_model_defaults") is False, f"{label}: precision/sampling mode mismatch")
        generation = actor["generation_config"]
        _require(generation.get("do_sample") is True and generation.get("temperature") == 1
                 and generation.get("top_p") == 1 and generation.get("top_k") == 0,
                 f"{label}: actor is not the declared full-softmax sampler")
        actor_contract = {key: value for key, value in actor.items() if key != "starting_adapter_name"}
        identity = {"suite": suite, "draws": draws, "contract": config["evaluation_contract"],
                    "actor": actor_contract, "packages": manifest["packages"],
                    "teacher_targets": report["training_teacher_target_expressions"]}
        if common is None:
            common = identity
        else:
            _require(identity == common, f"{label}: frozen suite/prompt/scorer/tokenizer/runtime contract differs")
        episodes = report["episodes"]
        _require(len(episodes) == 10, f"{label}: all ten transfer tasks are required")
        indexed[label] = {}
        eos = generation.get("eos_token_id")
        eos = {eos} if type(eos) is int else set(eos or [])
        for episode in episodes:
            task = episode["task"]
            key = task["year"], task["half"]
            _require(type(key[0]) is int and type(key[1]) is int and task.get("horizon_sessions") == 5,
                     f"{label}: invalid task year/half/horizon")
            _require(key in TASKS and key not in indexed[label], f"{label}: unknown/duplicate task")
            _require(task.get("task_id") == f"{key[0]}-H{key[1]}", f"{label}: task identity mismatch")
            lengths = _task_lengths(task, f"{label}/{key}")
            if key in task_manifests:
                _require(task == task_manifests[key], f"{label}: task chronology differs")
            else:
                task_manifests[key] = task
            records = {}
            slots = {(condition, decoding, draw) for condition in CONDITIONS for decoding in DECODINGS
                     for draw in range(draws if decoding == "stochastic" else 1)}
            for record in episode["records"]:
                slot = record["condition"], record["decoding"], record["draw"]
                _require(type(record["draw"]) is int and type(record.get("seed")) is int,
                         f"{label}/{key}: noninteger draw/seed")
                _require(slot in slots and slot not in records, f"{label}/{key}: missing/duplicate/unknown proposal slot")
                expected_seed = 80000 + TASKS.index(key) * 100 + (slot[2] if slot[1] == "stochastic" else 99)
                _require(record.get("seed") == expected_seed, f"{label}/{key}: RNG seed mismatch")
                for field in ("prompt_ids", "completion_ids"):
                    tokens = record.get(field)
                    _require(isinstance(tokens, list) and tokens and all(type(t) is int and t >= 0 for t in tokens),
                             f"{label}/{key}: invalid {field}")
                _require(len(record["completion_ids"]) <= 64 and len(record["prompt_ids"]) <= 4096,
                         f"{label}/{key}: token budget exceeded")
                _require(type(record.get("terminated")) is bool
                         and record["terminated"] == (record["completion_ids"][-1] in eos),
                         f"{label}/{key}: EOS status mismatch")
                _require(isinstance(record.get("text"), str), f"{label}/{key}: missing completion text")
                strict_action = parse_action(record["text"]) if record["terminated"] else {"action": "invalid"}
                _require(record.get("action") == strict_action, f"{label}/{key}: strict action/text mismatch")
                parsed = {"strict": strict_action,
                          "fence_tolerant_secondary": parse_completion(record["text"], record["terminated"]).action}
                prompt_key = key, slot[0]
                if prompt_key in prompts:
                    _require(record["prompt_ids"] == prompts[prompt_key], f"{label}/{key}: paired prompt tokens differ")
                else:
                    prompts[prompt_key] = record["prompt_ids"]
                for parser in PARSERS:
                    _outcome(record[parser], f"{label}/{key}/{slot}/{parser}", lengths)
                    _require(record[parser]["status"] != "ok" or record["terminated"],
                             f"{label}/{key}: nonterminated proposal marked usable")
                    if _schema(parsed[parser]) and record["terminated"]:
                        _require(record[parser].get("expression") == parsed[parser]["expression"],
                                 f"{label}/{key}: {parser} outcome expression differs from parsed completion")
                    else:
                        _require(record[parser]["status"] == "invalid", f"{label}/{key}: invalid schema scored")
                    expression = record[parser].get("expression")
                    if isinstance(expression, str):
                        formula_key = key, expression
                        if formula_key in formula_outcomes:
                            _require(record[parser] == formula_outcomes[formula_key],
                                     f"{label}/{key}: same formula has inconsistent evaluator outcomes")
                        else:
                            formula_outcomes[formula_key] = record[parser]
                _require(record.get("outcome") == record["strict"], f"{label}/{key}: strict outcome trace mismatch")
                records[slot] = record
            _require(records.keys() == slots, f"{label}/{key}: missing proposal slots/draw count")
            references = episode["references"]
            _require(set(references) == {"uniform_grid", "feedback_greedy_grid", "training_best_fixed"},
                     "missing required fixed/grid references")
            _require(references["training_best_fixed"].get("expression") == FIXED_EXPRESSION,
                     "fixed comparison expression changed")
            if key in common_references:
                _require(references == common_references[key], f"{label}/{key}: reference outcomes differ")
            else:
                common_references[key] = references
            for name, reference in references.items():
                total = 16 if name == "uniform_grid" else 1
                count = reference.get("valid_samples")
                _require(reference.get("n_samples") == total and type(count) is int and 0 <= count <= total,
                         "reference sample count mismatch")
                _close(_finite(reference["valid_fraction"], "reference valid fraction"), count / total,
                       "reference valid fraction")
                _finite(reference["mean_reward"], "reference reward")
                ic = reference.get("mean_oriented_ic_valid_only")
                _require((ic is None) == (count == 0), "reference valid-only denominator mismatch")
                if ic is not None:
                    _require(-1 <= _finite(ic, "reference IC") <= 1, "reference IC outside rank bounds")
                _reference_summary([reference])
            indexed[label][key] = records
        _require(set(indexed[label]) == set(TASKS), f"{label}: incomplete task set")
    return indexed, common_references, common, task_manifests


def analyze_reports(reports: dict[str, dict], sft_label: str, rl_labels: tuple[str, str]) -> dict:
    """Validate and recompute all paired estimands; never select a winning seed."""
    try:
        indexed, references, common, task_manifests = _validate_reports(reports, sft_label, rl_labels)
    except (KeyError, TypeError, AttributeError) as exc:
        raise AnalysisInputError(f"malformed input report: {exc}") from exc
    labels = (sft_label, *rl_labels)

    def unit(keys):
        reference_means = {name: _reference_summary([references[key][name] for key in keys])
                           for name in ("uniform_grid", "feedback_greedy_grid", "training_best_fixed")}
        result = {}
        for parser in PARSERS:
            result[parser] = {}
            for decoding in DECODINGS:
                policies = {label: {condition: _summary([
                    record[parser] for key in keys for slot, record in indexed[label][key].items()
                    if slot[0] == condition and slot[1] == decoding], len(keys))
                    for condition in CONDITIONS} for label in labels}
                evidence = {label: _difference(policies[label]["true"], policies[label]["exchanged"])
                            for label in labels}
                comparisons = {label: {condition: _difference(policies[label][condition],
                               policies[sft_label][condition]) for condition in CONDITIONS} | {
                               "grounding_interaction": _interaction(evidence[label], evidence[sft_label])}
                               for label in rl_labels}
                result[parser][decoding] = {"policies": policies, "evidence_effects": evidence,
                    "rl_vs_sft": comparisons,
                    "policy_vs_training_fixed": {label: _difference(policies[label]["true"],
                                                     reference_means["training_best_fixed"]) for label in labels}}
        return {"n_tasks": len(keys), "task_ids": [task_manifests[key]["task_id"] for key in keys],
                "metrics": result, "references": reference_means}

    task_rows = [{"task_id": task_manifests[key]["task_id"], "year": key[0], "half": key[1],
                  **unit([key])} for key in TASKS]
    year_rows = [{"year": year, **unit([(year, 1), (year, 2)])} for year in range(2020, 2025)]
    overall = unit(list(TASKS))
    seed_summary = {}
    for parser in PARSERS:
        seed_summary[parser] = {}
        for decoding in DECODINGS:
            rows = overall["metrics"][parser][decoding]["rl_vs_sft"]
            seed_summary[parser][decoding] = {}
            for effect in (*CONDITIONS, "grounding_interaction"):
                values = {label: rows[label][effect]["reward_delta"] for label in rl_labels}
                seed_summary[parser][decoding][effect] = {
                    "per_rl_seed": values, "mean": sum(values.values()) / 2,
                    "observed_min": min(values.values()), "observed_max": max(values.values()),
                    "range_is_not_confidence_interval": True}
    return {"study": "financial-proposal-v1-paired-analysis", "status": "descriptive development comparison",
            "roles": {"sft": sft_label, "rl_seed23": rl_labels[0], "rl_seed29": rl_labels[1]},
            "integrity": {"validated": True, "n_checkpoints": 3, "n_tasks": 10, "n_years": 5,
                          "stochastic_draws_per_task_condition": common["draws"],
                          "frozen_suite": common["suite"],
                          "evaluation_contract_sha256": common["contract"]["shared_contract_sha256"],
                          "snapshot_sha256": EXPECTED_RAW_SHA256,
                          "exact_paired_prompt_tokens_checked": True,
                          "statistics_recomputed_from_outcomes": True},
            "task_rows": task_rows, "year_rows": year_rows, "overall": overall,
            "rl_seed_summary": seed_summary,
            "limitations": ["Ten dependent half-years and five years; generated draws are not independent markets",
                            "Shared RNG couples comparisons; two RL seeds share one SFT parent and historical data",
                            "Valid-only IC is conditional on a policy-dependent subset, not the primary estimand",
                            "Predictive-contribution changes also reflect validity composition; not causal attribution",
                            "Grid-greedy observes 16 feedback formulas versus the actor's two probes",
                            "Both RL seeds and every signed task/year difference are retained; no best-seed selection",
                            "No significance, confidence-interval, final-holdout or profitability claim"]}


def plot_yearly(report, destination):
    """Static publication artifact from saved aggregate effects, no new scoring."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    roles = report["roles"]
    labels = (roles["rl_seed23"], roles["rl_seed29"])
    years = [row["year"] for row in report["year_rows"]]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True, constrained_layout=True)
    for axis, effect, title in zip(axes, ("true", "grounding_interaction"),
                                   ("RL minus SFT reward", "Evidence-grounding interaction")):
        for label, marker in zip(labels, ("o", "s")):
            values = [row["metrics"]["strict"]["stochastic"]["rl_vs_sft"][label][effect]["reward_delta"]
                      for row in report["year_rows"]]
            axis.plot(years, values, marker=marker, label=label, linewidth=1.4)
        axis.axhline(0, color="0.35", linewidth=.8)
        axis.set(title=title, xlabel="Assessment year", xticks=years)
        axis.grid(alpha=.2)
    axes[0].set_ylabel("Paired mean reward difference")
    axes[1].legend(frameon=False)
    fig.suptitle("French49 development transfer: strict JSON, stochastic policy\n"
                 "Paired yearly effects; no confidence intervals or independent-draw inference", fontsize=10)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sft", required=True, type=Path)
    parser.add_argument("--rl23", required=True, type=Path)
    parser.add_argument("--rl29", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--plot", type=Path)
    args = parser.parse_args()
    paths = (args.sft, args.rl23, args.rl29)
    inputs = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    labels = [report["manifest"]["config"]["label"] for report in inputs]
    if len(set(labels)) != 3:
        parser.error("the three input reports must identify distinct checkpoints")
    report = analyze_reports(dict(zip(labels, inputs)), labels[0], tuple(labels[1:]))
    report["source_reports"] = [{"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                                for path in paths]
    write_json(args.output, report)
    if args.plot:
        plot_yearly(report, args.plot)
    print(json.dumps({"output": args.output.name, "primary": report["rl_seed_summary"]["strict"]["stochastic"]}))


if __name__ == "__main__":
    main()
