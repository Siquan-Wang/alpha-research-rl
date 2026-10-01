"""Post-hoc generation Monte Carlo error and descriptive year omissions.

Conditions on the five frozen policies and existing ten market episodes.
Consumes saved outcomes only: no model, generation, training or market scoring.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from .artifacts import write_json
from .financial_analysis import CONDITIONS, TASKS, AnalysisInputError
from .linkage_analysis import ORIGINALS, ROLES, analyze_linkage

COMPONENTS = ("reward", "validity", "ic_contribution")
SAVED_COMPONENTS = ("reward_delta", "failure_penalty_component_delta", "all_proposal_ic_contribution_delta")
COMPARISONS = (
    ("rl23_minus_sft", ROLES["rl_seed23"], ROLES["sft"]),
    ("rl29_minus_sft", ROLES["rl_seed29"], ROLES["sft"]),
    ("placebo23_minus_sft", ROLES["placebo_seed23"], ROLES["sft"]),
    ("placebo29_minus_sft", ROLES["placebo_seed29"], ROLES["sft"]),
    ("rl23_minus_placebo23", ROLES["rl_seed23"], ROLES["placebo_seed23"]),
    ("rl29_minus_placebo29", ROLES["rl_seed29"], ROLES["placebo_seed29"]),
)


def _require(condition, message):
    if not condition:
        raise AnalysisInputError(message)


def _close(left, right, context):
    _require(math.isfinite(left) and math.isfinite(right)
             and math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12), context)


def _compare_complete(current, saved, path="analysis", float_roundoff=True):
    """Exact structure/scalar types; tolerate finite float arithmetic only."""
    context = f"saved five-report analysis differs at {path}"
    _require(type(current) is type(saved), context + ": scalar/container type")
    if isinstance(current, dict):
        _require(current.keys() == saved.keys(), context + ": keys")
        for key in current:
            arithmetic = float_roundoff and key not in {
                "study", "status", "roles", "integrity", "source_reports", "limitations"}
            _compare_complete(current[key], saved[key], f"{path}.{key}", arithmetic)
    elif isinstance(current, list):
        _require(len(current) == len(saved), context + ": length")
        for index, (left, right) in enumerate(zip(current, saved, strict=True)):
            _compare_complete(left, right, f"{path}[{index}]", float_roundoff)
    elif isinstance(current, float):
        if float_roundoff:
            _close(current, saved, context + ": finite float")
        else:
            _require(math.isfinite(current) and math.isfinite(saved) and current == saved,
                     context + ": exact metadata float")
    else:
        _require(current == saved, context + ": value")


def _mean(values):
    return math.fsum(values) / len(values)


def _covariance(left, right):
    _require(len(left) == len(right) and len(left) >= 2, "sample covariance requires paired observations")
    a, b = _mean(left), _mean(right)
    return math.fsum((x - a) * (y - b) for x, y in zip(left, right, strict=True)) / (len(left) - 1)


def _components(outcome):
    valid = outcome["status"] == "ok"
    return {"reward": outcome["reward"], "validity": int(valid),
            "ic_contribution": outcome["oriented_future_ic"] if valid else 0.0}


def paired_task(current, prior, year, half):
    """Eight already-validated outcome pairs, preserving common-seed covariance."""
    _require(len(current) == len(prior) == 8, "exactly eight paired draws are required")
    left, right = [_components(row) for row in current], [_components(row) for row in prior]
    differences = {name: [a[name] - b[name] for a, b in zip(left, right, strict=True)] for name in COMPONENTS}
    for reward, validity, ic in zip(*(differences[name] for name in COMPONENTS), strict=True):
        _close(reward, validity + ic, "per-draw reward decomposition differs")
    components = {name: {"mean": _mean(values), "sample_variance": _covariance(values, values)}
                  for name, values in differences.items()}
    covariance = _covariance(differences["validity"], differences["ic_contribution"])
    _close(components["reward"]["sample_variance"], components["validity"]["sample_variance"]
           + components["ic_contribution"]["sample_variance"] + 2 * covariance,
           "paired component variance decomposition differs")
    validity_pairs = [(a["validity"], b["validity"]) for a, b in zip(left, right, strict=True)]
    return {"task_id": f"{year}-H{half}", "year": year, "half": half, "n_draws": 8,
            "components": components, "validity_ic_sample_covariance": covariance,
            "paired_draw_differences": [{"draw": i, **{name: differences[name][i] for name in COMPONENTS}}
                                        for i in range(8)],
            "counts": {"current_valid": sum(a for a, _ in validity_pairs),
                       "prior_valid": sum(b for _, b in validity_pairs),
                       "both_valid": sum(a == b == 1 for a, b in validity_pairs),
                       "both_failed": sum(a == b == 0 for a, b in validity_pairs),
                       "current_only_valid": sum(a == 1 and b == 0 for a, b in validity_pairs),
                       "prior_only_valid": sum(a == 0 and b == 1 for a, b in validity_pairs)}}


def combine_tasks(tasks):
    """Equal task weights; estimates generation noise, not between-task noise."""
    _require(bool(tasks) and all(row["n_draws"] == 8 for row in tasks), "nonempty eight-draw task set required")
    n = len(tasks)
    components = {}
    for name in COMPONENTS:
        mc_variance = math.fsum(row["components"][name]["sample_variance"] / 8 for row in tasks) / n**2
        components[name] = {"mean": _mean([row["components"][name]["mean"] for row in tasks]),
                            "estimated_mc_variance": mc_variance,
                            "estimated_mc_standard_error": math.sqrt(mc_variance),
                            "zero_observed_within_task_variance_count": sum(
                                row["components"][name]["sample_variance"] == 0 for row in tasks)}
    covariance = math.fsum(row["validity_ic_sample_covariance"] / 8 for row in tasks) / n**2
    _close(components["reward"]["mean"], components["validity"]["mean"] + components["ic_contribution"]["mean"],
           "aggregate mean decomposition differs")
    _close(components["reward"]["estimated_mc_variance"], components["validity"]["estimated_mc_variance"]
           + components["ic_contribution"]["estimated_mc_variance"] + 2 * covariance,
           "aggregate Monte Carlo variance decomposition differs")
    return {"n_tasks": n, "draws_per_task": 8, "paired_draw_count": n * 8,
            "components": components, "estimated_mc_covariance_validity_ic": covariance,
            "counts": {key: sum(row["counts"][key] for row in tasks) for key in tasks[0]["counts"]}}


def leave_one_year_out(tasks):
    _require(len(tasks) == 10 and {(r["year"], r["half"]) for r in tasks} == set(TASKS),
             "year omission requires every original half-year")
    full = combine_tasks(tasks)
    result = []
    for year in range(2020, 2025):
        kept = [row for row in tasks if row["year"] != year]
        means = {name: _mean([row["components"][name]["mean"] for row in kept]) for name in COMPONENTS}
        result.append({"omitted_year": year, "retained_tasks": [row["task_id"] for row in kept],
                       "n_tasks": len(kept), "paired_draw_count": 8 * len(kept), "means": means,
                       "changes_from_full_mean": {name: means[name] - full["components"][name]["mean"]
                                                  for name in COMPONENTS}})
    return result


def analyze_reliability(reports, saved_analysis, sources):
    """Require the complete existing analysis before deriving any diagnostic."""
    _require(set(sources) == set(ROLES.values()), "five source-report identities required")
    original_sources = {label: sources[label] for label in ORIGINALS}
    rebuilt = analyze_linkage(reports, original_sources)
    rebuilt["source_reports"] = sources
    _compare_complete(rebuilt, saved_analysis)
    indexed = {label: {(episode["task"]["year"], episode["task"]["half"]): {
        (record["condition"], record["draw"]): record for record in episode["records"]
        if record["decoding"] == "stochastic"} for episode in report["episodes"]}
        for label, report in reports.items()}
    saved_tasks = {(r["year"], r["half"]): r for r in saved_analysis["task_rows"]}
    results = []
    for name, current, prior in COMPARISONS:
        for condition in CONDITIONS:
            tasks = []
            for year, half in TASKS:
                a, b = indexed[current][year, half], indexed[prior][year, half]
                records = [(a[condition, draw], b[condition, draw]) for draw in range(8)]
                _require(all(x["seed"] == y["seed"] and x["prompt_ids"] == y["prompt_ids"] for x, y in records),
                         "paired generation seed/prompt differs")
                task = paired_task([x["strict"] for x, _ in records], [y["strict"] for _, y in records], year, half)
                for draw, (x, _) in zip(task["paired_draw_differences"], records, strict=True):
                    draw["seed"] = x["seed"]
                saved = saved_tasks[year, half]["metrics"]["strict"]["stochastic"]
                contrast = (saved["policy_vs_sft"][current] if prior == ROLES["sft"] else
                            saved["correct_vs_placebo"]["23" if current == ROLES["rl_seed23"] else "29"])[condition]
                for component, field in zip(COMPONENTS, SAVED_COMPONENTS, strict=True):
                    _close(task["components"][component]["mean"], contrast[field], "saved per-task contrast differs")
                tasks.append(task)
            overall = combine_tasks(tasks)
            saved = saved_analysis["overall"]["metrics"]["strict"]["stochastic"]
            contrast = (saved["policy_vs_sft"][current] if prior == ROLES["sft"] else
                        saved["correct_vs_placebo"]["23" if current == ROLES["rl_seed23"] else "29"])[condition]
            for component, field in zip(COMPONENTS, SAVED_COMPONENTS, strict=True):
                _close(overall["components"][component]["mean"], contrast[field], "saved overall contrast differs")
            omissions = leave_one_year_out(tasks)
            results.append({"comparison": name, "current": current, "prior": prior, "condition": condition,
                            "overall": overall, "tasks": tasks, "leave_one_year_out": omissions,
                            "yearly_means": [{"year": year, "means": {component: _mean([
                                row["components"][component]["mean"] for row in tasks if row["year"] == year])
                                for component in COMPONENTS}} for year in range(2020, 2025)]})
    return {"study": "financial-fixed-panel-reliability-v1", "status": "post-hoc descriptive robustness",
            "source_reports": sources, "integrity": {"existing_five_report_validation_passed": True,
                "complete_saved_analysis_reproduced": True, "n_comparisons": 6, "n_conditions": 2,
                "n_tasks": 10, "draws_per_task_condition": 8, "parser": "strict", "decoding": "stochastic",
                "retained_original_records": 900, "stochastic_records_used": 800,
                "paired_seed_and_prompt_equality_checked": True},
            "estimand": "Equal-weight conditional mean generation-reward differences on ten fixed episodes and frozen policies",
            "method": {"mcse": "sqrt(sum_t sample_variance(d_t, ddof=1)/8)/10",
                       "coupling": "Differences formed within common task/condition/draw/seed before variance estimation",
                       "components": list(COMPONENTS), "component_covariance_retained": True,
                       "mean_arithmetic_comparison_tolerance": {"absolute": 1e-12, "relative": 1e-12},
                       "leave_one_year_out": "Five descriptive eight-task means; not confidence intervals or a market jackknife"},
            "comparisons": results,
            "limitations": ["Assumes within-task iid pseudorandom generation and independent streams across task/draw slots; not proven",
                "Conditions on fixed checkpoints, prompts and market periods; excludes training and future-market uncertainty",
                "Eight draws give unstable variance estimates and can miss rare invalid actions or proposals",
                "Zero observed within-task variance does not establish zero population variance",
                "Overlapping market labels, reused years and shared policies are not independent market replications",
                "All six contrasts and both conditions share observations and random streams",
                "Year omission changes the fixed-panel estimand and retains generation noise; its range is not an interval",
                "No p-values, normal confidence intervals, significance, selected winner or holdout alpha claim"]}


def load_inputs(analysis_path, reports_dir):
    raw_analysis = analysis_path.read_bytes()
    saved = json.loads(raw_analysis.decode("utf-8"))
    sources = saved["source_reports"]
    _require(set(sources) == set(ROLES.values()), "five source-report identities required")
    reports, paths = {}, []
    for label, source in sources.items():
        filename = source.get("file")
        _require(isinstance(filename, str) and filename and not any(c in filename for c in "/\\:"),
                 "source report must use a safe basename")
        path = reports_dir / filename
        raw = path.read_bytes()
        _require(hashlib.sha256(raw).hexdigest() == source.get("sha256"), "source report file-byte identity differs")
        reports[label] = json.loads(raw.decode("utf-8"))
        paths.append(path)
    return reports, saved, sources, paths, hashlib.sha256(raw_analysis).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, default=Path("results/financial_linkage_paired_v1.json"))
    parser.add_argument("--reports-dir", type=Path, default=Path("artifacts/development"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    reports, saved, sources, paths, analysis_sha = load_inputs(args.analysis, args.reports_dir)
    _require(args.output.resolve() not in {path.resolve() for path in [args.analysis, *paths]},
             "output must not overwrite original reports or analysis")
    result = analyze_reliability(reports, saved, sources)
    result["source_analysis"] = {"file": args.analysis.name, "sha256": analysis_sha}
    result["analysis_source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    write_json(args.output, result)
    print(json.dumps({"contrasts": len(result["comparisons"]), "status": result["status"]}))


if __name__ == "__main__":
    main()
