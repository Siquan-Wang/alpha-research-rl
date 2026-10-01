"""Descriptive diversity of all five frozen financial policies' saved proposals.

No model, market panel, forward label, or new proposal is loaded/generated.
Feedback rank comparisons come from validated, matched saved diagnostics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from .artifacts import write_json
from .factor_diagnostics import RANK_EQUIVALENCE_TOLERANCE
from .financial_analysis import CONDITIONS, DECODINGS, AnalysisInputError, _require, _sha, _valid_hash
from .financial_policy import expression_key
from .financial_tasks import EXPECTED_RAW_SHA256, GRID, PROBES, TEACHER_GRID
from .linkage_analysis import ORIGINALS, ROLES, analyze_linkage

LABELS = tuple(ROLES.values())
DEFAULT_REPORTS = tuple(f"artifacts/development/{name}-transfer-v1.json" for name in
                        ("financial-sft", "financial-rloo23", "financial-rloo29", "financial-placebo23", "financial-placebo29"))
DEFAULT_DIAGNOSTICS = tuple(f"artifacts/development/{name}-rank-diagnostics-v1.json" for name in
                            ("financial-sft", "financial-rloo23", "financial-rloo29", "financial-placebo23", "financial-placebo29"))
SUPPORT = {"paired_cell_coverage": .8, "valid_date_fraction": .8, "min_valid_dates": 20}


def _public_sources(sources):
    for source in sources.values():
        name = source.get("file")
        _require(isinstance(name, str) and name and not any(c in name for c in "/\\:"), "unsafe public source name")
        _require(_valid_hash(source.get("sha256")), "invalid source byte SHA256")


def _pair(pair, expression, reference, length):
    """Validate saved support/arithmetic; never recompute a factor or label."""
    _require(expression_key(pair.get("expression")) == expression_key(expression)
             and pair.get("reference") == reference, "rank comparison formula mismatch")
    count, coverage = pair.get("n_valid_dates"), pair.get("paired_cell_coverage")
    required = max(min(20, length), math.ceil(.8 * length))
    _require(type(count) is int and 0 <= count <= length and pair.get("n_signal_dates") == length
             and pair.get("required_valid_dates") == required, "rank comparison support/count mismatch")
    _require(type(coverage) in (float, int) and math.isfinite(coverage) and 0 <= coverage <= 1,
             "rank comparison coverage invalid")
    mean, absolute, std = (pair.get(key) for key in
                          ("mean_daily_spearman", "absolute_mean_daily_spearman", "daily_spearman_std"))
    if mean is None:
        _require(absolute is None and std is None, "rank comparison missing metric mismatch")
    else:
        _require(type(mean) in (float, int) and math.isfinite(mean) and -1 <= mean <= 1
                 and absolute == abs(mean) and type(std) in (float, int) and math.isfinite(std) and std >= 0,
                 "rank comparison signed/absolute metric mismatch")
    usable = mean is not None and coverage >= .8 and count >= required
    equivalent = usable and absolute >= 1 - RANK_EQUIVALENCE_TOLERANCE
    _require(pair.get("status") == ("ok" if usable else "unscorable")
             and type(pair.get("near_exact_rank_equivalent")) is bool
             and pair["near_exact_rank_equivalent"] == equivalent
             and pair.get("tolerance") == RANK_EQUIVALENCE_TOLERANCE, "rank comparison gate mismatch")
    return {key: pair.get(key) for key in ("reference", "status", "reason", "mean_daily_spearman",
                "absolute_mean_daily_spearman", "daily_spearman_std", "paired_cell_coverage", "n_valid_dates",
                "n_signal_dates", "required_valid_dates", "near_exact_rank_equivalent", "tolerance")}


def diagnostic_index(reports, sources, diagnostics, diagnostic_sources):
    """Join only matching task+AST feedback evidence; reject conflicting reuse."""
    _require(set(diagnostics) == set(diagnostic_sources) and diagnostics, "rank diagnostic source identities missing")
    _public_sources(diagnostic_sources)
    by_filename = {sources[label]["file"]: reports[label] for label in LABELS}
    _require(len(by_filename) == 5, "duplicate report source names")
    index = {}
    for name, diagnostic in diagnostics.items():
        _require(diagnostic.get("study") == "financial-feedback-rank-alias-diagnostics-v1"
                 and diagnostic.get("snapshot_sha256") == EXPECTED_RAW_SHA256
                 and diagnostic.get("references") == list(TEACHER_GRID)
                 and diagnostic.get("similarity_definition") == "abs(mean daily cross-sectional Spearman)"
                 and diagnostic.get("rank_equivalence_tolerance") == RANK_EQUIVALENCE_TOLERANCE
                 and diagnostic.get("support") == SUPPORT, "rank diagnostic contract mismatch")
        _require(diagnostic.get("input_report") in by_filename, "rank diagnostic input report identity unknown")
        report = by_filename[diagnostic["input_report"]]
        tasks = {episode["task"]["task_id"]: episode for episode in report["episodes"]}
        seen = set()
        for episode in diagnostic["episodes"]:
            task = episode["task"]
            task_id = task["task_id"]
            _require(task_id in tasks and task_id not in seen and task == tasks[task_id]["task"],
                     "rank diagnostic task/feedback manifest mismatch")
            seen.add(task_id)
            bounds = task["feedback_bounds_half_open"]
            length = bounds[1] - bounds[0]
            source_valid = {expression_key(record[parser].get("expression")) for record in tasks[task_id]["records"]
                            for parser in ("strict", "fence_tolerant_secondary") if record[parser]["status"] == "ok"}
            row_seen = set()
            for row in episode["unique_valid_expression_diagnostics"]:
                expression, key = row.get("expression"), row.get("canonical_ast")
                _require(isinstance(expression, str) and key is not None and key == expression_key(expression) and key in source_valid
                         and key not in row_seen, "rank diagnostic AST/source proposal mismatch")
                row_seen.add(key)
                comparisons = row["teacher_comparisons"]
                _require(len(comparisons) == len(TEACHER_GRID), "rank diagnostic incomplete teacher comparisons")
                normalized = [_pair(pair, expression, reference, length)
                              for pair, reference in zip(comparisons, TEACHER_GRID, strict=True)]
                usable = [pair for pair in normalized if pair["status"] == "ok"]
                nearest = max(usable, key=lambda pair: pair["absolute_mean_daily_spearman"]) if usable else None
                _require(row.get("status") == ("ok" if nearest else "unscorable"), "nearest diagnostic status mismatch")
                actual_nearest = (_pair(row["nearest_teacher"], expression, row["nearest_teacher"]["reference"], length)
                                  if row.get("nearest_teacher") is not None else None)
                _require(actual_nearest == nearest, "nearest teacher selection mismatch")
                value = {"canonical_ast": key, "status": row["status"], "nearest_teacher": nearest,
                         "teacher_comparisons": normalized}
                identity = task_id, key
                if identity in index:
                    _require(index[identity]["diagnostic"] == value, "conflicting reused task/AST rank diagnostics")
                    index[identity]["source_diagnostics"].append(name)
                else:
                    index[identity] = {"diagnostic": value, "source_diagnostics": [name]}
        _require(seen == set(tasks), "rank diagnostic incomplete task set")
    return index


def _distribution(counts):
    total = sum(counts.values())
    if not total:
        return {"unique": 0, "entropy_nats": None, "effective_number": None, "herfindahl_concentration": None,
                "normalized_entropy": None, "frequencies": {}}
    probabilities = [count / total for count in counts.values()]
    entropy = -sum(p * math.log(p) for p in probabilities)
    return {"unique": len(counts), "entropy_nats": entropy, "effective_number": math.exp(entropy),
            "herfindahl_concentration": sum(p * p for p in probabilities),
            "normalized_entropy": entropy / math.log(len(counts)) if len(counts) > 1 else 0.,
            "frequencies": dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))}


def summarize(records, rank_index, teacher_targets):
    """records are (task_id, saved_record); every invalid slot stays counted."""
    valid = [(task, record) for task, record in records if record["strict"]["status"] == "ok"]
    n, v = len(records), len(valid)
    attempted = [record["action"].get("expression") for _, record in records
                 if isinstance(record.get("action"), dict) and isinstance(record["action"].get("expression"), str)]
    strings = Counter(record["strict"]["expression"] for _, record in valid)
    asts = Counter(expression_key(expression) for expression in strings.elements())
    pairs = {(task, expression_key(record["strict"]["expression"])) for task, record in valid}
    _require(all(pair in rank_index for pair in pairs), "missing valid task/AST feedback rank diagnostic")
    weighted = [rank_index[task, expression_key(record["strict"]["expression"])]["diagnostic"] for task, record in valid]
    supported = [row for row in weighted if row["status"] == "ok"]
    equivalents = [row for row in supported if row["nearest_teacher"]["near_exact_rank_equivalent"]]
    ordered = sorted(asts.items(), key=lambda item: (-item[1], item[0]))
    top = [{"canonical_ast": key, "example_expressions": sorted(expression for expression in strings if expression_key(expression) == key),
            "count": count, "exposure_all_attempts": count / n, "exposure_valid_only": count / v}
           for key, count in ordered]
    keys = {"probe_reuse": {expression_key(expression) for expression in PROBES},
            "teacher_grid_match": {expression_key(expression) for expression in TEACHER_GRID},
            "exact_sft_target_match": {expression_key(expression) for expression in teacher_targets},
            "reserved_grid_match": {expression_key(expression) for expression in GRID[len(TEACHER_GRID):]}}
    memberships = {name: {"count_valid": sum(count for key, count in asts.items() if key in reference),
                         "fraction_all_attempts": sum(count for key, count in asts.items() if key in reference) / n,
                         "fraction_valid_only": sum(count for key, count in asts.items() if key in reference) / v if v else None}
                   for name, reference in keys.items()}
    unique_rows = [rank_index[pair]["diagnostic"] for pair in sorted(pairs)]
    return {"n_attempts": n, "n_valid": v, "n_invalid_or_unscorable": n - v,
            "valid_fraction": v / n, "failure_reasons": dict(Counter(record["strict"].get("reason") or "unspecified"
                for _, record in records if record["strict"]["status"] != "ok")),
            "all_attempt_frequencies": {"completion_text": dict(Counter(record["text"] for _, record in records)),
                "expression_strings": dict(Counter(attempted)),
                "parseable_canonical_asts": dict(Counter(key for expression in attempted if (key := expression_key(expression)) is not None)),
                "scope": "including invalid/unsupported attempts; not generated discoveries"},
            "valid_expression_strings": _distribution(strings), "valid_canonical_asts": _distribution(asts),
            "valid_ast_exposure": top,
            "top1_ast_exposure_all_attempts": top[0]["count"] / n if top else 0.,
            "top1_ast_exposure_valid_only": top[0]["count"] / v if top else None,
            "top3_ast_exposure_all_attempts": sum(row["count"] for row in top[:3]) / n,
            "top3_ast_exposure_valid_only": sum(row["count"] for row in top[:3]) / v if v else None,
            "memberships": memberships,
            "feedback_rank_equivalence": {"n_valid_proposals": v, "n_supported_proposals": len(supported),
                "n_near_exact_teacher_equivalent_proposals": len(equivalents),
                "fraction_all_attempts": len(equivalents) / n,
                "fraction_valid_only": len(equivalents) / v if v else None,
                "fraction_supported_valid_only": len(equivalents) / len(supported) if supported else None,
                "mean_nearest_similarity_supported_only": sum(row["nearest_teacher"]["absolute_mean_daily_spearman"]
                    for row in supported) / len(supported) if supported else None,
                "unique_task_ast_pairs": len(pairs),
                "unique_supported_task_ast_pairs": sum(row["status"] == "ok" for row in unique_rows),
                "unique_near_exact_task_ast_pairs": sum(row["status"] == "ok" and row["nearest_teacher"]["near_exact_rank_equivalent"]
                                                       for row in unique_rows)}}


def analyze_diversity(reports, sources, diagnostics, diagnostic_sources):
    _require(set(reports) == set(sources) == set(LABELS), "exactly five report source identities required")
    _public_sources(sources)
    validated = analyze_linkage(reports, {label: sources[label] for label in ORIGINALS})
    rank_index = diagnostic_index(reports, sources, diagnostics, diagnostic_sources)
    task_ids = [episode["task"]["task_id"] for episode in reports[LABELS[0]]["episodes"]]
    targets = reports[LABELS[0]]["training_teacher_target_expressions"]
    policies = {}
    all_pairs = set()
    for label in LABELS:
        episodes = {episode["task"]["task_id"]: episode for episode in reports[label]["episodes"]}

        def cells(selected, episodes=episodes):
            return {condition: {decoding: summarize([(task, record) for task in selected for record in episodes[task]["records"]
                if record["condition"] == condition and record["decoding"] == decoding], rank_index, targets)
                for decoding in DECODINGS} for condition in CONDITIONS}

        policies[label] = {"overall": cells(task_ids),
                           "tasks": [{"task_id": task, "cells": cells([task])} for task in task_ids]}
        all_pairs.update((task, expression_key(record["strict"]["expression"])) for task in task_ids
                         for record in episodes[task]["records"] if record["strict"]["status"] == "ok")
    _require(sum(cell["n_attempts"] for policy in policies.values() for c in policy["overall"].values() for cell in c.values()) == 900,
             "all900 strict slots must be retained")
    return {"study": "financial-proposal-diversity-descriptive-v1", "scope": "post-hoc descriptive; saved strict completions only",
            "integrity": {"all_five_linkage_report_validation_passed": True, "original_three_preserved": True,
                "evaluation_contract_sha256": reports[LABELS[0]]["manifest"]["config"]["evaluation_contract"]["shared_contract_sha256"],
                "five_checkpoint_registry_sha256": _sha(validated["integrity"]["five_checkpoint_registry"]),
                "snapshot_sha256": EXPECTED_RAW_SHA256, "n_policies": 5, "n_tasks": 10, "n_strict_proposals": 900},
            "source_reports": sources, "source_rank_diagnostics": diagnostic_sources,
            "method": {"parser": "strict", "conditions": list(CONDITIONS), "decodings": list(DECODINGS),
                "entropy": "Shannon, natural logarithm, valid-only empirical formula frequencies",
                "normalized_entropy": "Shannon entropy divided by log(observed unique valid forms); not full-grammar entropy",
                "validity": "Saved strict scorer status ok: syntax/schema, feedback and assessment support usable; not accuracy filtering",
                "canonical_ast": "Python expression AST; excludes formatting, not algebraic/monotone equivalence",
                "feedback_rank_similarity": "abs(mean daily cross-sectional Spearman)",
                "rank_equivalence_tolerance": RANK_EQUIVALENCE_TOLERANCE, "rank_support": SUPPORT,
                "teacher_grid": list(TEACHER_GRID), "probe_expressions": list(PROBES)},
            "policies": policies,
            "used_rank_mapping": [{"task_id": task, **rank_index[task, key]} for task, key in sorted(all_pairs)],
            "limitations": ["Different strings/ASTs are not novel alpha discoveries or independent useful factors",
                "Rank equivalence is empirical on a particular historical feedback panel with explicit support; not universal formula identity",
                "No assessment labels/returns loaded or rescored; stored outcomes used only to authenticate strict usability",
                "Repeated stochastic draws share episodes; entropy/concentration are descriptive, not inferential",
                "Conditions and decodings remain separate; all invalid attempts are retained",
                "No model/GPU runs, new proposals, raw market series, or post-2024 data"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    roles = ("sft", "rl23", "rl29", "placebo23", "placebo29")
    for role, default in zip(roles, DEFAULT_REPORTS, strict=True):
        parser.add_argument("--" + role, type=Path, default=Path(default))
    parser.add_argument("--diagnostic", action="append", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report_paths = [getattr(args, role) for role in roles]
    diagnostic_paths = args.diagnostic or [Path(path) for path in DEFAULT_DIAGNOSTICS]
    _require(all(args.output.resolve() != path.resolve() for path in (*report_paths, *diagnostic_paths)),
             "output collides with original source evidence")
    reports, sources, diagnostics, diagnostic_sources = {}, {}, {}, {}
    for label, path in zip(LABELS, report_paths, strict=True):
        raw = path.read_bytes()
        reports[label] = json.loads(raw)
        sources[label] = {"file": path.name, "sha256": hashlib.sha256(raw).hexdigest()}
    for path in diagnostic_paths:
        _require(path.name not in diagnostics, "duplicate rank diagnostic basename")
        raw = path.read_bytes()
        diagnostics[path.name] = json.loads(raw)
        diagnostic_sources[path.name] = {"file": path.name, "sha256": hashlib.sha256(raw).hexdigest()}
    try:
        result = analyze_diversity(reports, sources, diagnostics, diagnostic_sources)
    except (KeyError, TypeError, AttributeError) as exc:
        raise AnalysisInputError(f"malformed diversity evidence: {exc}") from exc
    result["analysis_source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    write_json(args.output, result)
    print(json.dumps(result["integrity"]), flush=True)


if __name__ == "__main__":
    main()
