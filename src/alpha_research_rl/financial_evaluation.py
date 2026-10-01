"""Frozen matched financial proposal evaluation and newly generated evidence intervention."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from .artifacts import run_manifest, write_json
from .financial_policy import (
    PROPOSAL_SYSTEM,
    ProposalActor,
    evaluate_sample,
    exchange_probe_bundles,
    expression_key,
    load_pinned_panel,
    sample_record,
)
from .financial_tasks import (
    GRID,
    HORIZON,
    INVALID_REWARD,
    PROBES,
    PROPOSAL_COST,
    TEACHER_GRID,
    feedback_teacher,
    list_tasks,
)
from .format_ablation import parse_completion
from .training import seed_everything

FIXED_EXPRESSION = "delay(returns,1)"
CONDITIONS = ("true", "exchanged")
PARSERS = ("strict", "fence_tolerant_secondary")
DECODINGS = ("stochastic", "greedy")


def evaluation_contract(model_path: str | Path) -> dict:
    """Comparable prompt/scorer identity; excludes unrelated analysis modules."""
    module_names = ("financial_evaluation.py", "financial_policy.py", "financial_tasks.py",
                    "dsl.py", "evaluation.py", "llm.py", "format_ablation.py")
    source_files = {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                    for name in module_names}
    tokenizer_names = ("tokenizer.json", "tokenizer_config.json", "special_tokens_map.json",
                       "vocab.json", "merges.txt")
    tokenizer_files = {name: hashlib.sha256((Path(model_path) / name).read_bytes()).hexdigest()
                       for name in tokenizer_names if (Path(model_path) / name).is_file()}
    contract = {
        "proposal_system_sha256": hashlib.sha256(PROPOSAL_SYSTEM.encode()).hexdigest(),
        "source_files_sha256": source_files, "tokenizer_files_sha256": tokenizer_files,
        "numeric_protocol": {"horizon": HORIZON, "cost": PROPOSAL_COST, "invalid_reward": INVALID_REWARD,
                             "min_coverage": 0.8, "min_valid_fraction": 0.8, "min_valid_dates": 20,
                             "orientation": "feedback mean IC<0 => -1; otherwise +1",
                             "supported_features": ["returns"], "max_lookback": 60,
                             "purged_signal_rows_at_each_halfyear_end": HORIZON},
        "action_schema": {"exact_keys": ["action", "expression"], "action": "propose",
                          "requires_eos": True, "strict_json_primary": True},
        "sampling": {"temperature": 1.0, "top_p": 1.0, "top_k": 0, "max_tokens": 64,
                     "seed_rule": "80000 + task_index*100 + draw; greedy draw=99"},
        "secondary": "whole-json-fence reparse of same completion; no new generations",
        "fixed_reference": FIXED_EXPRESSION,
    }
    return {**contract, "shared_contract_sha256": hashlib.sha256(
        json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}


def checkpoint_manifest(adapter: str | Path) -> dict:
    """Hash actual frozen adapter files independently of requires_grad flags."""
    adapter = Path(adapter)
    files = sorted(set(adapter.glob("adapter_model*.safetensors")) | set(adapter.glob("adapter_model*.bin")))
    config = adapter / "adapter_config.json"
    if not files or not config.is_file():
        raise ValueError("adapter must contain saved adapter weights and adapter_config.json")
    files.append(config)
    records = []
    combined = hashlib.sha256()
    for path in sorted(files):
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        record = {"file": path.name, "sha256": digest.hexdigest(), "bytes": path.stat().st_size}
        combined.update(path.name.encode())
        combined.update(record["sha256"].encode())
        records.append(record)
    return {"adapter_name": adapter.parent.name, "files": records, "combined_sha256": combined.hexdigest()}


def freeze_checkpoints(adapters: dict[str, str | Path], draws: int = 8) -> dict:
    """Root saves this once after training, before any transfer scoring."""
    if not adapters:
        raise ValueError("at least one checkpoint must be frozen")
    if draws not in (4, 8):
        raise ValueError("registered suite requires four or eight stochastic draws")
    return {"study": "financial-proposal-v1", "frozen_utc": datetime.now(UTC).isoformat(),
            "checkpoints": {label: checkpoint_manifest(adapter) for label, adapter in adapters.items()},
            "fixed_reference": FIXED_EXPRESSION,
            "fixed_reference_selection": "best mean reward on 2002-2017 training grid, frozen before transfer",
            "seed_rule": "80000 + task_index*100 + draw; greedy draw=99; identical across checkpoints/conditions",
            "stochastic_draws_per_task_condition": draws, "greedy_draws_per_task_condition": 1}


def _outcome_summary(outcomes: list[dict]) -> dict:
    valid = [outcome for outcome in outcomes if outcome["status"] == "ok"]
    return {"mean_reward": float(np.mean([outcome["reward"] for outcome in outcomes])) if outcomes else None,
            "mean_oriented_ic_invalid_as_minus_one": float(np.mean([
                outcome["oriented_future_ic"] if outcome["status"] == "ok" else -1.0 for outcome in outcomes]))
            if outcomes else None,
            "invalid_ic_convention": "penalty surrogate -1, not an observed IC; valid-only IC reported separately",
            "n_samples": len(outcomes), "valid_samples": len(valid),
            "invalid_or_unscorable_samples": len(outcomes) - len(valid),
            "valid_fraction": len(valid) / len(outcomes) if outcomes else None,
            "mean_oriented_ic_valid_only": float(np.mean([outcome["oriented_future_ic"] for outcome in valid]))
            if valid else None,
            "mean_raw_ic_valid_only": float(np.mean([outcome["assessment"]["mean_ic"] for outcome in valid]))
            if valid else None,
            "mean_coverage_valid_only": float(np.mean([outcome["assessment"]["coverage"] for outcome in valid]))
            if valid else None,
            "mean_scored_dates_valid_only": float(np.mean([outcome["assessment"].get("n_dates", 0)
                                                          for outcome in valid])) if valid else None,
            "failure_reason_counts": dict(Counter(outcome.get("reason", "unspecified") for outcome in outcomes
                                                  if outcome["status"] != "ok"))}


def _formula_flags(outcome: dict, teacher_targets: tuple[str, ...]) -> dict:
    key = expression_key(outcome.get("expression"))
    return {"canonical_ast": key, "probe_reuse": key is not None and key in {expression_key(x) for x in PROBES},
            "teacher_grid_match": key is not None and key in {expression_key(x) for x in TEACHER_GRID},
            "exact_sft_target_match": key is not None and key in {expression_key(x) for x in teacher_targets},
            "reserved_grid_form": key is not None and key in {expression_key(x) for x in GRID[12:]}}


def _frequency_summary(records: list[dict], parser: str) -> dict:
    outcomes = [record[parser] for record in records]
    expressions = Counter(outcome["expression"] for outcome in outcomes if isinstance(outcome["expression"], str))
    asts = Counter(record[parser + "_flags"]["canonical_ast"] for record in records
                   if record[parser + "_flags"]["canonical_ast"] is not None)
    flags = {name: sum(record[parser + "_flags"][name] for record in records)
             for name in ("probe_reuse", "teacher_grid_match", "exact_sft_target_match", "reserved_grid_form")}
    valid_records = [record for record in records if record[parser]["status"] == "ok"]
    valid_expressions = Counter(record[parser]["expression"] for record in valid_records)
    valid_asts = Counter(record[parser + "_flags"]["canonical_ast"] for record in valid_records)
    valid_flags = {name: sum(record[parser + "_flags"][name] for record in valid_records)
                   for name in flags}
    return {"expression_frequencies": dict(expressions), "canonical_ast_frequencies": dict(asts),
            "unique_expressions": len(expressions), "unique_canonical_asts": len(asts), **flags,
            "denominator_all_proposals": len(records),
            "frequency_scope": "all attempts, including unsupported or unscorable expressions",
            "valid_only": {"expression_frequencies": dict(valid_expressions),
                           "canonical_ast_frequencies": dict(valid_asts),
                           "unique_expressions": len(valid_expressions), "unique_canonical_asts": len(valid_asts),
                           "denominator_valid_proposals": len(valid_records), **valid_flags},
            "novelty_caveat": "string/AST differences can be economically equivalent; no discovery claim"}


def reference_outcomes(task) -> dict:
    """Fixed CPU references; no assessment-based candidate selection."""
    outcomes = [task.evaluate(expression) for expression in GRID]
    greedy_expression = feedback_teacher(task, GRID)
    greedy = next((outcome for outcome in outcomes if outcome["expression"] == greedy_expression), None)
    if greedy is None:
        greedy = task.evaluate(None)
    fixed = next(outcome for outcome in outcomes if outcome["expression"] == FIXED_EXPRESSION)
    return {"uniform_grid": {**_outcome_summary(outcomes), "expected_over_exact_grid": True,
                             "single_slot_choices": len(GRID)},
            "feedback_greedy_grid": {**_outcome_summary([greedy]), "expression": greedy_expression,
                                     "extra_information": "16 feedback formulas versus actor's two probes"},
            "training_best_fixed": {**_outcome_summary([fixed]), "expression": FIXED_EXPRESSION,
                                    "selection": "training-only best grid, frozen before transfer"}}


def evaluate_task_runner(actor, tasks, draws: int = 8, seed_fn=seed_everything,
                         teacher_targets: tuple[str, ...] = (), include_references: bool = True) -> dict:
    """Injectable runner; each exchanged-evidence condition generates fresh samples."""
    if type(draws) is not int or not 1 <= draws <= 8:
        raise ValueError("draws must be an integer between one and eight")
    episodes = []
    for task_index, task in enumerate(tasks):
        observation = task.observation()
        records = []
        for condition in CONDITIONS:
            conditioned = observation if condition == "true" else exchange_probe_bundles(observation)
            for decoding in DECODINGS:
                for draw in range(draws if decoding == "stochastic" else 1):
                    seed = 80000 + task_index * 100 + (draw if decoding == "stochastic" else 99)
                    seed_fn(seed)
                    sample = actor.sample(conditioned, stochastic=decoding == "stochastic", max_tokens=64)
                    strict = evaluate_sample(task, sample)
                    reparsed = parse_completion(sample.text, sample.terminated)
                    secondary = evaluate_sample(task, replace(sample, action=reparsed.action))
                    record = {**sample_record(sample, strict), "condition": condition, "decoding": decoding,
                              "draw": draw, "seed": seed, "strict": strict,
                              "prompt_token_count": len(sample.prompt_ids),
                              "completion_token_count": len(sample.completion_ids),
                              "fence_tolerant_secondary": secondary,
                              "secondary_accepted_format": reparsed.accepted_format,
                              "secondary_parse_failure": reparsed.failure,
                              "strict_flags": _formula_flags(strict, teacher_targets),
                              "fence_tolerant_secondary_flags": _formula_flags(secondary, teacher_targets)}
                    records.append(record)
        means = {}
        for parser in PARSERS:
            means[parser] = {condition: {decoding: _outcome_summary([
                record[parser] for record in records
                if record["condition"] == condition and record["decoding"] == decoding])
                for decoding in DECODINGS} for condition in CONDITIONS}
        effects = {parser: {decoding: means[parser]["true"][decoding]["mean_reward"]
                           - means[parser]["exchanged"][decoding]["mean_reward"]
                           for decoding in DECODINGS} for parser in PARSERS}
        episodes.append({"task": task.public_manifest, "records": records, "means": means,
                         "evidence_effect_reward": effects,
                         "references": reference_outcomes(task) if include_references else {}})

    def summarize_group(selected_episodes, parser, condition, decoding):
        all_records = [record for episode in selected_episodes for record in episode["records"]
                       if record["condition"] == condition and record["decoding"] == decoding]
        metrics = _outcome_summary([record[parser] for record in all_records])
        task_means = [episode["means"][parser][condition][decoding]["mean_reward"] for episode in selected_episodes]
        metrics["mean_reward"] = float(np.mean(task_means)) if task_means else None
        return metrics | {"n_tasks": len(selected_episodes), "frequencies": _frequency_summary(all_records, parser)}

    summary = {parser: {condition: {decoding: summarize_group(episodes, parser, condition, decoding)
                                   for decoding in DECODINGS} for condition in CONDITIONS} for parser in PARSERS}
    years = sorted({episode["task"]["year"] for episode in episodes})
    yearly = {str(year): {parser: {condition: {decoding: summarize_group(
        [episode for episode in episodes if episode["task"]["year"] == year], parser, condition, decoding)
        for decoding in DECODINGS} for condition in CONDITIONS} for parser in PARSERS} for year in years}
    def reference_group(selected_episodes):
        if not include_references or not selected_episodes:
            return {}
        result = {}
        for name in selected_episodes[0]["references"]:
            rows = [episode["references"][name] for episode in selected_episodes]
            valid_count = sum(row["valid_samples"] for row in rows)
            sample_count = sum(row["n_samples"] for row in rows)
            valid_ic = sum(row["mean_oriented_ic_valid_only"] * row["valid_samples"] for row in rows
                           if row["valid_samples"])
            result[name] = {
                "mean_reward": float(np.mean([row["mean_reward"] for row in rows])),
                "n_tasks": len(selected_episodes), "n_formula_outcomes": sample_count,
                "valid_formula_outcomes": valid_count, "invalid_or_unscorable_formula_outcomes": sample_count - valid_count,
                "mean_oriented_ic_valid_only": valid_ic / valid_count if valid_count else None,
                "per_task_aggregate_only": True, "matched_information": name != "feedback_greedy_grid",
            }
        return result

    reference_summary = reference_group(episodes)
    yearly_references = {str(year): reference_group([episode for episode in episodes if episode["task"]["year"] == year])
                         for year in years}
    return {"episodes": episodes, "summary": summary, "yearly": yearly,
            "reference_summary": reference_summary, "yearly_references": yearly_references,
            "limitations": ["development transfer, not untouched final evaluation",
                            "all invalid proposals remain in reward denominators; valid-only IC is secondary",
                            "eight draws improve Monte Carlo precision, not the number of market episodes",
                            "new generations under deliberately exchanged evidence; true evaluator unchanged",
                            "no best-of-N, raw daily market arrays, significance or profitability claim"]}


def compare_reports(reports: dict[str, dict], sft_label: str = "sft") -> dict:
    """Paired task/year effects from every frozen checkpoint, without reselection."""
    if sft_label not in reports:
        raise ValueError("comparison requires the named SFT reference report")
    reference = reports[sft_label]
    ref_episodes = {episode["task"]["task_id"]: episode for episode in reference["episodes"]}
    comparisons = {}
    for label, report in reports.items():
        if label == sft_label:
            continue
        episodes = {episode["task"]["task_id"]: episode for episode in report["episodes"]}
        if episodes.keys() != ref_episodes.keys():
            raise ValueError("reports must have exactly matched task IDs")
        rows = []
        for identifier, episode in episodes.items():
            sft = ref_episodes[identifier]
            if episode["task"] != sft["task"]:
                raise ValueError("task chronology/scoring manifests differ across reports")
            rng = [(record["condition"], record["decoding"], record["draw"], record["seed"])
                   for record in episode["records"]]
            sft_rng = [(record["condition"], record["decoding"], record["draw"], record["seed"])
                       for record in sft["records"]]
            if rng != sft_rng:
                raise ValueError("reports do not preserve matched proposal slots and RNG seeds")
            effects = {}
            for parser in PARSERS:
                effects[parser] = {}
                for decoding in DECODINGS:
                    current = episode["means"][parser]
                    prior = sft["means"][parser]
                    policy_evidence = current["true"][decoding]["mean_reward"] - current["exchanged"][decoding]["mean_reward"]
                    sft_evidence = prior["true"][decoding]["mean_reward"] - prior["exchanged"][decoding]["mean_reward"]
                    effects[parser][decoding] = {
                        "incremental_reward_vs_sft": current["true"][decoding]["mean_reward"] - prior["true"][decoding]["mean_reward"],
                        "policy_evidence_effect_reward": policy_evidence,
                        "sft_evidence_effect_reward": sft_evidence,
                        "grounding_interaction_reward": policy_evidence - sft_evidence,
                        "valid_only_ic_secondary": {"policy_true": current["true"][decoding]["mean_oriented_ic_valid_only"],
                                                     "sft_true": prior["true"][decoding]["mean_oriented_ic_valid_only"]},
                        "denominators": {"policy": current["true"][decoding]["valid_samples"],
                                         "sft": prior["true"][decoding]["valid_samples"],
                                         "total_each": current["true"][decoding]["n_samples"]},
                    }
            rows.append({"task_id": identifier, "year": episode["task"]["year"],
                         "half": episode["task"]["half"], "effects": effects})
        years = sorted({row["year"] for row in rows})
        effect_keys = ("incremental_reward_vs_sft", "policy_evidence_effect_reward",
                       "sft_evidence_effect_reward", "grounding_interaction_reward")
        yearly = {str(year): {parser: {decoding: {key: float(np.mean([
            row["effects"][parser][decoding][key] for row in rows if row["year"] == year])) for key in effect_keys}
            for decoding in DECODINGS} for parser in PARSERS} for year in years}
        pooled = {parser: {decoding: {key: float(np.mean([
            row["effects"][parser][decoding][key] for row in rows])) for key in effect_keys}
            for decoding in DECODINGS} for parser in PARSERS}
        comparisons[label] = {"paired_tasks": rows, "yearly": yearly, "pooled": pooled}
    return {"reference_label": sft_label, "comparisons": comparisons,
            "interpretation": "paired descriptive development effects; few years/seeds, no significance claim"}


def evaluate_checkpoint(panel, model: str, adapter: str, output: str | Path, label: str,
                        split: str, draws: int = 8, frozen_suite: dict | None = None) -> dict:
    if split not in {"feasibility", "transfer"}:
        raise ValueError("evaluation split must be feasibility or transfer")
    checkpoint = checkpoint_manifest(adapter)
    if split == "transfer":
        if frozen_suite is None or label not in frozen_suite.get("checkpoints", {}):
            raise ValueError("transfer requires a prewritten suite freeze manifest containing this checkpoint")
        if frozen_suite["checkpoints"][label]["combined_sha256"] != checkpoint["combined_sha256"]:
            raise ValueError("checkpoint changed after suite freeze")
        if frozen_suite.get("stochastic_draws_per_task_condition") != draws:
            raise ValueError("draw count differs from the frozen suite")
    output = Path(output)
    contract = evaluation_contract(model)
    manifest = run_manifest({"study": "financial-proposal-v1", "label": label, "split": split,
                             "snapshot_sha256": panel.metadata.get("raw_sha256"), "checkpoint": checkpoint,
                             "frozen_suite": frozen_suite, "stochastic_draws_per_task_condition": draws,
                             "greedy_draws_per_task_condition": 1, "conditions": list(CONDITIONS),
                             "seed_rule": "80000 + task_index*100 + draw; greedy draw=99",
                             "max_tokens": 64, "sampling": "temperature1,top_p1,top_k0,full_softmax",
                             "strict_primary": True, "secondary_reparse_same_completion": True,
                             "fixed_reference": FIXED_EXPRESSION,
                             "evaluation_contract": contract,
                             "manifest_capture": "entry before actor load and evaluation scoring"})
    write_json(output.with_suffix(".manifest.json"), manifest)
    tasks = list_tasks(panel, split)
    training_targets = tuple(dict.fromkeys(feedback_teacher(task) for task in list_tasks(panel, "train")))
    training_targets = tuple(expression for expression in training_targets if expression is not None)
    actor = ProposalActor(model, adapter)
    manifest["actor"] = actor.provenance
    write_json(output.with_suffix(".manifest.json"), manifest)
    results = evaluate_task_runner(actor, tasks, draws, teacher_targets=training_targets)
    if checkpoint_manifest(adapter)["combined_sha256"] != checkpoint["combined_sha256"]:
        raise ValueError("checkpoint files changed during evaluation")
    report = {"manifest": manifest, "training_teacher_target_expressions": list(training_targets), **results}
    write_json(output, report)
    print(json.dumps({"label": label, "split": split,
                      "strict_true_stochastic": results["summary"]["strict"]["true"]["stochastic"],
                      "strict_exchanged_stochastic": results["summary"]["strict"]["exchanged"]["stochastic"]}),
          flush=True)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/raw/french49-v1/49_Industry_Portfolios_daily_CSV.zip")
    parser.add_argument("--model", default="models/Qwen3-0.6B")
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--split", choices=["feasibility", "transfer"], required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--draws", type=int, choices=[4, 8], default=8)
    parser.add_argument("--freeze-manifest", type=Path)
    args = parser.parse_args()
    frozen = json.loads(args.freeze_manifest.read_text(encoding="utf-8")) if args.freeze_manifest else None
    panel = load_pinned_panel(args.input)
    evaluate_checkpoint(panel, args.model, args.adapter, args.output, args.label, args.split, args.draws, frozen)


if __name__ == "__main__":
    main()
