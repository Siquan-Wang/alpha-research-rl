"""Exploratory saved-outcome comparison of correct and permuted-reward RL.

The original three-checkpoint study is validated unchanged. Only the declared
five-checkpoint registry extension is accepted for the two new placebo reports.
No market series, model generation, or policy selection is performed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path

from .artifacts import write_json
from .financial_analysis import (
    CONDITIONS,
    DECODINGS,
    PARSERS,
    TASKS,
    AnalysisInputError,
    _checkpoint,
    _contract,
    _difference,
    _interaction,
    _outcome,
    _reference_summary,
    _require,
    _schema,
    _sha,
    _summary,
    _task_lengths,
    _valid_hash,
    analyze_reports,
)
from .format_ablation import parse_completion
from .llm import parse_action

STUDY = "financial-reward-linkage-control-v1"
ROLES = {"sft": "financial-sft-v1", "rl_seed23": "financial-rloo23-v1",
         "rl_seed29": "financial-rloo29-v1", "placebo_seed23": "financial-placebo23-v1",
         "placebo_seed29": "financial-placebo29-v1"}
ORIGINALS = tuple(ROLES[role] for role in ("sft", "rl_seed23", "rl_seed29"))
CONTROLS = tuple(ROLES[role] for role in ("placebo_seed23", "placebo_seed29"))


def _before(frozen, started):
    try:
        left, right = datetime.fromisoformat(frozen), datetime.fromisoformat(started)
    except (TypeError, ValueError) as exc:
        raise AnalysisInputError("invalid registry/evaluation timestamp") from exc
    _require(left.tzinfo is not None and right.tzinfo is not None and left <= right,
             "five-checkpoint registry was not frozen before control evaluation")


def _registry(reports, original_analysis, original_sources):
    old = original_analysis["integrity"]["frozen_suite"]
    new = reports[CONTROLS[0]]["manifest"]["config"]["frozen_suite"]
    _require(new == reports[CONTROLS[1]]["manifest"]["config"]["frozen_suite"],
             "control registries differ")
    _require(new.get("study") == STUDY and set(new.get("checkpoints", {})) == set(ROLES.values()),
             "only the declared five-checkpoint registry extension is permitted")
    _require(set(original_sources) == set(ORIGINALS), "all three original report file identities are required")
    for label, source in original_sources.items():
        _require(isinstance(source.get("file"), str) and source["file"]
                 and not any(char in source["file"] for char in "/\\:"), "unsafe original report name")
        _require(_valid_hash(source.get("sha256")), "invalid original report file hash")
        _require(new["checkpoints"][label] == old["checkpoints"][label],
                 "original checkpoint differs from the original freeze")
    _require(new.get("original_reports") == original_sources, "original saved-report file binding differs")
    _require(new.get("original_frozen_suite_sha256") == _sha(old), "original suite binding differs")
    _require(new.get("stochastic_draws_per_task_condition") == 8,
             "reward-linkage plan requires eight stochastic draws")
    for label in ORIGINALS:
        _before(reports[label]["manifest"]["created_utc"], new["frozen_utc"])
    for field, value in old.items():
        if field not in ("study", "frozen_utc", "checkpoints"):
            _require(new.get(field) == value, f"registry extension changed original field: {field}")
    for checkpoint in new["checkpoints"].values():
        _checkpoint(checkpoint)
    return new


def _validate_controls(reports, original_analysis, sources):
    registry = _registry(reports, original_analysis, sources)
    sft = reports[ORIGINALS[0]]
    base_manifest, base_config = sft["manifest"], sft["manifest"]["config"]
    originals = {episode["task"]["task_id"]: episode for episode in sft["episodes"]}
    indexed, formula_outcomes = {}, {}
    for label in ORIGINALS:
        indexed[label] = {}
        for episode in reports[label]["episodes"]:
            key = episode["task"]["year"], episode["task"]["half"]
            indexed[label][key] = {(r["condition"], r["decoding"], r["draw"]): r for r in episode["records"]}
            for record in episode["records"]:
                for parser in PARSERS:
                    expression = record[parser].get("expression")
                    if isinstance(expression, str):
                        formula_outcomes[key, expression] = record[parser]
    actor_fields = {k: v for k, v in base_manifest["actor"].items() if k != "starting_adapter_name"}
    for label in CONTROLS:
        report, manifest = reports[label], reports[label]["manifest"]
        config = manifest["config"]
        _require(config.get("label") == label, "control label differs from declared identity")
        # The frozen runner still identifies its scorer as financial-proposal-v1;
        # the registry and this analysis identify the new exploratory study.
        _require(config.get("study") == "financial-proposal-v1", "control runner/scorer study mismatch")
        _require(config.get("checkpoint") == registry["checkpoints"][label], "control checkpoint differs from freeze")
        _before(registry["frozen_utc"], manifest["created_utc"])
        _contract(config["evaluation_contract"])
        for field in ("split", "snapshot_sha256", "stochastic_draws_per_task_condition",
                      "greedy_draws_per_task_condition", "conditions", "max_tokens", "strict_primary",
                      "secondary_reparse_same_completion", "evaluation_contract"):
            _require(config.get(field) == base_config.get(field), f"control shared config mismatch: {field}")
        _require({k: v for k, v in manifest["actor"].items() if k != "starting_adapter_name"} == actor_fields,
                 "control actor/model/precision/sampling provenance differs")
        _require(manifest["actor"].get("tf32") is False and manifest["actor"].get("use_model_defaults") is False,
                 "control precision flags must be explicit false booleans")
        _require(manifest["packages"] == base_manifest["packages"], "control runtime packages differ")
        _require(report["training_teacher_target_expressions"] == sft["training_teacher_target_expressions"],
                 "control teacher target provenance differs")
        draws = config["stochastic_draws_per_task_condition"]
        eos = manifest["actor"]["generation_config"]["eos_token_id"]
        eos = {eos} if type(eos) is int else set(eos or [])
        _require(len(report["episodes"]) == len(TASKS), "control missing task episodes")
        indexed[label] = {}
        for episode in report["episodes"]:
            task = episode["task"]
            key = task["year"], task["half"]
            _require(all(type(value) is int for value in key), "noninteger control task identity")
            _require(key in TASKS and key not in indexed[label], "unknown/duplicate control task")
            _require(task == originals[f"{key[0]}-H{key[1]}"]["task"], "control chronology/task manifest differs")
            lengths = _task_lengths(task, label)
            _require(episode["references"] == originals[task["task_id"]]["references"],
                     "control reference outcomes differ")
            slots = {(condition, decoding, draw) for condition in CONDITIONS for decoding in DECODINGS
                     for draw in range(draws if decoding == "stochastic" else 1)}
            records = {}
            for record in episode["records"]:
                slot = record["condition"], record["decoding"], record["draw"]
                _require(type(record["draw"]) is int and slot in slots and slot not in records,
                         "unknown/duplicate control proposal slot")
                expected = indexed[ORIGINALS[0]][key][slot]
                _require(type(record.get("seed")) is int and record["seed"] == expected["seed"],
                         "control RNG seed differs")
                _require(record.get("prompt_ids") == expected["prompt_ids"], "control paired prompt tokens differ")
                _require(all(type(token) is int for token in record["prompt_ids"]), "noninteger control prompt tokens")
                tokens = record.get("completion_ids")
                _require(isinstance(tokens, list) and tokens and len(tokens) <= 64
                         and all(type(t) is int and t >= 0 for t in tokens), "invalid control completion tokens")
                _require(type(record.get("terminated")) is bool and record["terminated"] == (tokens[-1] in eos),
                         "control EOS status mismatch")
                _require(isinstance(record.get("text"), str), "missing control completion text")
                strict = parse_action(record["text"]) if record["terminated"] else {"action": "invalid"}
                _require(record.get("action") == strict, "control action/text mismatch")
                parsed = {"strict": strict,
                          "fence_tolerant_secondary": parse_completion(record["text"], record["terminated"]).action}
                for parser in PARSERS:
                    scored = record[parser]
                    _outcome(scored, label, lengths)
                    if record["terminated"] and _schema(parsed[parser]):
                        _require(scored.get("expression") == parsed[parser]["expression"],
                                 "control expression differs from parsed completion")
                    else:
                        _require(scored["status"] == "invalid", "invalid/nonterminated control action scored usable")
                    expression = scored.get("expression")
                    if isinstance(expression, str):
                        formula_key = key, expression
                        if formula_key in formula_outcomes:
                            _require(scored == formula_outcomes[formula_key], "same formula evaluator outcomes differ")
                        else:
                            formula_outcomes[formula_key] = scored
                _require(record.get("outcome") == record["strict"], "control strict trace differs")
                records[slot] = record
            _require(set(records) == slots, "missing control proposal slots")
            indexed[label][key] = records
        _require(set(indexed[label]) == set(TASKS), "incomplete control task set")
    return indexed, registry


def analyze_linkage(reports: dict[str, dict], original_sources: dict[str, dict]) -> dict:
    """Validate the unchanged original study before its declared extension."""
    _require(set(reports) == set(ROLES.values()), "exactly the five declared checkpoint labels are required")
    original = analyze_reports({label: reports[label] for label in ORIGINALS}, ORIGINALS[0], ORIGINALS[1:])
    try:
        indexed, registry = _validate_controls(reports, original, original_sources)
    except (KeyError, TypeError, AttributeError) as exc:
        raise AnalysisInputError(f"malformed linkage input: {exc}") from exc

    def unit(keys):
        metrics = {}
        for parser in PARSERS:
            metrics[parser] = {}
            for decoding in DECODINGS:
                policies = {label: {condition: _summary([
                    row[parser] for key in keys for slot, row in indexed[label][key].items()
                    if slot[0] == condition and slot[1] == decoding], len(keys))
                    for condition in CONDITIONS} for label in ROLES.values()}
                evidence = {label: _difference(row["true"], row["exchanged"]) for label, row in policies.items()}
                vs_sft = {label: {condition: _difference(policies[label][condition], policies[ORIGINALS[0]][condition])
                                 for condition in CONDITIONS} | {
                                 "grounding_interaction": _interaction(evidence[label], evidence[ORIGINALS[0]])}
                          for label in (*ORIGINALS[1:], *CONTROLS)}
                pairs = {str(seed): {"correct_label": correct, "placebo_label": placebo,
                                    **{condition: _difference(policies[correct][condition], policies[placebo][condition])
                                       for condition in CONDITIONS},
                                    "grounding_interaction": _interaction(evidence[correct], evidence[placebo])}
                         for seed, correct, placebo in zip((23, 29), ORIGINALS[1:], CONTROLS, strict=True)}
                metrics[parser][decoding] = {"policies": policies, "evidence_effects": evidence,
                                              "policy_vs_sft": vs_sft, "correct_vs_placebo": pairs}
        reference_by_task = {(episode["task"]["year"], episode["task"]["half"]): episode["references"]
                             for episode in reports[ORIGINALS[0]]["episodes"]}
        references = {name: _reference_summary([reference_by_task[key][name] for key in keys])
                      for name in ("uniform_grid", "feedback_greedy_grid", "training_best_fixed")}
        return {"n_tasks": len(keys), "task_ids": [f"{year}-H{half}" for year, half in keys],
                "metrics": metrics, "references": references}

    tasks = [{"task_id": f"{year}-H{half}", "year": year, "half": half, **unit([(year, half)])}
             for year, half in TASKS]
    years = [{"year": year, **unit([(year, 1), (year, 2)])} for year in range(2020, 2025)]
    overall = unit(TASKS)
    seed_summary = {parser: {decoding: {condition: {
        "per_seed": {seed: row[condition]["reward_delta"] for seed, row in overall["metrics"][parser][decoding]
                     ["correct_vs_placebo"].items()},
        "mean": sum(row[condition]["reward_delta"] for row in overall["metrics"][parser][decoding]
                    ["correct_vs_placebo"].values()) / 2,
        "range_is_not_confidence_interval": True} for condition in (*CONDITIONS, "grounding_interaction")}
        for decoding in DECODINGS} for parser in PARSERS}
    return {"study": STUDY + "-analysis", "status": "exploratory control designed after original transfer inspection",
            "roles": dict(ROLES), "integrity": {"validated": True, "n_checkpoints": 5,
                "n_tasks": 10, "n_years": 5, "stochastic_draws_per_task_condition": 8,
                "original_three_validated_unchanged": True, "original_analysis": original["integrity"],
                "five_checkpoint_registry": registry, "exact_paired_prompt_tokens_checked": True,
                "statistics_recomputed_from_outcomes": True},
            "original_results": original, "task_rows": tasks, "year_rows": years, "overall": overall,
            "correct_vs_placebo_seed_summary": seed_summary,
            "limitations": ["Exploratory reward-linkage control; original primary results remain unchanged",
                "Control trajectories are freshly generated, not copies of original RL trajectories",
                "Uniform permutation includes failures and can leave reward/action associations unchanged by chance",
                "Finite two-seed outcomes cannot prove causality, alpha, significance or sequential research",
                "Ten dependent half-years; generated draws are not independent market observations",
                "All failures retained; valid-only IC is secondary and conditions on a changing subset"]}


def plot_linkage(report: dict, destination: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True, constrained_layout=True)
    years = [row["year"] for row in report["year_rows"]]
    for axis, effect in zip(axes, ("true", "grounding_interaction"), strict=True):
        for seed, marker in (("23", "o"), ("29", "s")):
            values = [row["metrics"]["strict"]["stochastic"]["correct_vs_placebo"][seed][effect]["reward_delta"]
                      for row in report["year_rows"]]
            axis.plot(years, values, marker=marker, label=f"correct minus placebo, seed {seed}")
        axis.axhline(0, color=".45", linewidth=.8)
        axis.set(xlabel="Assessment year", xticks=years,
                 title="Correct minus placebo reward" if effect == "true" else "Evidence-effect interaction")
        axis.grid(alpha=.2)
        axis.legend(frameon=False, fontsize=8)
    axes[0].set_ylabel("Paired mean reward difference")
    fig.suptitle("Exploratory reward-linkage control: both seeds, every year\n"
                 "Strict stochastic; no confidence intervals or independent-draw inference", fontsize=10)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for role in ("sft", "rl23", "rl29", "placebo23", "placebo29"):
        parser.add_argument("--" + role, required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--plot", type=Path)
    args = parser.parse_args()
    paths = [getattr(args, role) for role in ("sft", "rl23", "rl29", "placebo23", "placebo29")]
    reports, sources = {}, {}
    for label, path in zip(ROLES.values(), paths, strict=True):
        raw = path.read_bytes()
        reports[label] = json.loads(raw.decode("utf-8"))
        sources[label] = {"file": path.name, "sha256": hashlib.sha256(raw).hexdigest()}
    result = analyze_linkage(reports, {label: sources[label] for label in ORIGINALS})
    result["source_reports"] = sources
    write_json(args.output, result)
    if args.plot:
        plot_linkage(result, args.plot)
    print(json.dumps(result["correct_vs_placebo_seed_summary"]["strict"]["stochastic"]))


if __name__ == "__main__":
    main()
