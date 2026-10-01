"""Post-hoc bookkeeping of replay-verified Astra traces; no new financial scores."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
from pathlib import Path

from . import astra_replay
from .agentic_research import ARMS, canonical_json, digest
from .astra_replay import SOURCE_NAMES, TASK_IDS, replay_study
from .codex_actor import USAGE_KEYS

COMPARISONS = (
    "selected_abs_ic", "best_initial_probe_abs_ic", "first_charged_eligible_abs_ic",
    "selected_minus_best_initial_probe_abs_ic", "selected_minus_first_charged_eligible_abs_ic",
)
ARM_PAIRS = ((ARMS[0], ARMS[1]), (ARMS[0], ARMS[2]), (ARMS[1], ARMS[2]))
LIMITS = [
    "Post-hoc descriptive bookkeeping, not a preregistered confirmatory analysis.",
    "Saved historical feedback is evidence, not independently verified market calculation.",
    "Selected absolute IC is an in-sample maximum; its differences do not prove adaptive benefit.",
    "Distinct canonical ASTs do not establish semantic inequivalence or financially novel signals.",
    "Matching supplied prompt hashes do not establish identical hidden host context or backend computation.",
    "Token fields are separate reports; reasoning tokens are not added to output tokens.",
    "Summed call durations are not concurrent study wall-clock duration.",
    "No assessment artifact is read; no unselected future candidate is scored.",
]


def _identity(raw: bytes) -> dict:
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def _eligible(record: dict) -> bool:
    return record["feedback"] is not None and record["feedback"]["usable"] and not record["canonical_duplicate"]


def _counts(episodes: list[dict]) -> dict:
    records = [record for episode in episodes for record in episode["submission"]["records"]]
    asts = {record["canonical_ast"] for record in records if record["canonical_ast"] is not None}
    grammar_valid = sum(record["canonical_ast"] is not None for record in records)
    usable = sum(record["feedback"] is not None and record["feedback"]["usable"] for record in records)
    choices = {str(attempt): 0 for attempt in range(1, 7)}
    choices["unavailable"] = 0
    for episode in episodes:
        selection = episode["submission"]["selection"]
        choices["unavailable" if selection is None else str(selection["attempt"])] += 1
    return {
        "episode_count": len(episodes), "charged_attempt_count": len(records),
        "grammar_valid_count": grammar_valid, "grammar_invalid_count": len(records) - grammar_valid,
        "feedback_usable_count": usable,
        "feedback_unusable_count": sum(r["feedback"] is not None and not r["feedback"]["usable"] for r in records),
        "feedback_unavailable_count": sum(r["feedback"] is None for r in records),
        "within_episode_ast_duplicate_count": sum(r["canonical_duplicate"] for r in records),
        "selector_eligible_unique_proposal_count": sum(_eligible(r) for r in records),
        "global_unique_ast_count": len(asts),
        "sum_episode_unique_ast_counts": sum(len({r["canonical_ast"] for r in e["submission"]["records"]
                                                 if r["canonical_ast"] is not None}) for e in episodes),
        "initial_probe_entries_across_episodes": sum(len(e["submission"]["initial_evidence"]["probe_evidence"])
                                                     for e in episodes),
        "selected_episode_count": len(episodes) - choices["unavailable"],
        "selected_attempt_distribution": choices,
    }


def _usage(episodes: list[dict]) -> dict:
    summaries = [summary for episode in episodes for summary in episode["transport_summaries"]]
    fields = {}
    for field in sorted(USAGE_KEYS):
        values = [s["usage"][field] for s in summaries if s["usage"] is not None and field in s["usage"]]
        fields[field] = {"reported_sum": sum(values), "reported_decisions": len(values),
                         "missing_decisions": len(summaries) - len(values),
                         "complete_sum": sum(values) if len(values) == len(summaries) else None}
    elapsed = [summary["elapsed_seconds"] for summary in summaries]
    return {"decision_count": len(summaries), "missing_usage_decisions": sum(s["usage"] is None for s in summaries),
            "token_fields": fields, "elapsed_seconds": {
                "total": math.fsum(elapsed), "minimum": min(elapsed), "maximum": max(elapsed),
            }}


def _probes(episode: dict) -> dict:
    probes = episode["submission"]["initial_evidence"]["probe_evidence"]
    candidates = [{"probe_index": i, "expression": probe["expression"],
                   "abs_ic": abs(probe["feedback"]["mean_ic"])}
                  for i, probe in enumerate(probes, start=1) if probe["feedback_usable"]]
    return {"probe_count": len(probes), "usable_probe_count": len(candidates),
            "unusable_probe_count": len(probes) - len(candidates),
            "best_usable_probe": max(candidates, key=lambda row: row["abs_ic"]) if candidates else None}


def _episode(episode: dict, common_probes: dict) -> dict:
    saved = episode["submission"]
    selection = saved["selection"]
    first = next((r for r in saved["records"] if _eligible(r)), None)
    selected_ic = None if selection is None else abs(selection["feedback_ic"])
    best_probe = common_probes["best_usable_probe"]
    probe_ic = None if best_probe is None else best_probe["abs_ic"]
    first_ic = None if first is None else abs(first["feedback"]["mean_ic"])
    return {
        "counts": _counts([episode]), "reported_usage": _usage([episode]),
        "selected_attempt": None if selection is None else selection["attempt"],
        "first_charged_eligible_proposal": None if first is None else {
            "attempt": first["attempt"], "expression": first["packet"]["expression"], "abs_ic": first_ic,
        },
        "historical_comparisons": {
            "selected_abs_ic": selected_ic, "best_initial_probe_abs_ic": probe_ic,
            "first_charged_eligible_abs_ic": first_ic,
            "selected_minus_best_initial_probe_abs_ic": None if selected_ic is None or probe_ic is None
            else selected_ic - probe_ic,
            "selected_minus_first_charged_eligible_abs_ic": None if selected_ic is None or first_ic is None
            else selected_ic - first_ic,
        },
    }


def _match(first: dict, arms: tuple[str, ...]) -> dict:
    valid = all(first[arm]["grammar_valid"] for arm in arms)
    return {
        "all_grammar_valid": valid,
        "exact_expression_match": len({first[arm]["expression"] for arm in arms}) == 1 if valid else None,
        "canonical_ast_match": len({first[arm]["canonical_ast"] for arm in arms}) == 1 if valid else None,
    }


def _first_attempt(episodes: list[dict]) -> dict:
    first = {}
    for episode in episodes:
        record = episode["submission"]["records"][0]
        first[episode["arm"]] = {
            "grammar_valid": record["canonical_ast"] is not None,
            "expression": None if record["packet"] is None else record["packet"]["expression"],
            "canonical_ast": record["canonical_ast"], "supplied_prompt_sha256": record["prompt_sha256"],
        }
    prompt_count = len({record["supplied_prompt_sha256"] for record in first.values()})
    return {"by_arm": first, "distinct_supplied_prompt_count": prompt_count,
            "all_supplied_prompt_hashes_equal": prompt_count == 1, "all_three_arms": _match(first, ARMS),
            "pairs": {left + "__" + right: _match(first, (left, right)) for left, right in ARM_PAIRS}}


def _comparison_summary(rows: list[dict]) -> dict:
    result = {}
    for field in COMPARISONS:
        values = [row["historical_comparisons"][field] for row in rows
                  if row["historical_comparisons"][field] is not None]
        result[field] = {
            "episode_denominator": len(rows), "available_episodes": len(values),
            "unavailable_episodes": len(rows) - len(values),
            "mean_available": math.fsum(values) / len(values) if values else None,
            "minimum_available": min(values) if values else None, "maximum_available": max(values) if values else None,
        }
    return result


def _matching_summary(periods: list[dict]) -> dict:
    result = {}
    groups = {"all_three_arms": [row["first_attempt"]["all_three_arms"] for row in periods]}
    groups.update({left + "__" + right: [row["first_attempt"]["pairs"][left + "__" + right] for row in periods]
                   for left, right in ARM_PAIRS})
    for name, rows in groups.items():
        result[name] = {field: {"period_denominator": len(rows),
                               "matching_periods": sum(row[field] is True for row in rows),
                               "different_periods": sum(row[field] is False for row in rows),
                               "unavailable_periods": sum(row[field] is None for row in rows)}
                        for field in ("exact_expression_match", "canonical_ast_match")}
    return {"period_denominator": len(periods),
            "identical_supplied_prompt_periods": sum(p["first_attempt"]["all_supplied_prompt_hashes_equal"]
                                                      for p in periods), "formula_matching": result}


def diagnose_traces(contract_path: Path, submissions_path: Path, *, source_root: Path) -> dict:
    """Require all 180 recorded decisions, then summarize only saved historical evidence."""
    captured = {"contract": Path(contract_path).read_bytes(), "submissions": Path(submissions_path).read_bytes()}
    with tempfile.TemporaryDirectory(prefix="astra-trace-diagnostics-") as temporary:
        snapshots = {name: Path(temporary) / (name + ".json") for name in captured}
        for name, raw in captured.items():
            snapshots[name].write_bytes(raw)
        verified = replay_study(snapshots["contract"], snapshots["submissions"], source_root=Path(source_root))
    contract, bank = (json.loads(captured[name]) for name in ("contract", "submissions"))
    episodes = bank["episodes"]
    periods = []
    for task in TASK_IDS:
        items = [episode for episode in episodes if episode["task_id"] == task]
        probes = _probes(items[0])
        periods.append({"task_id": task, "common_initial_probes": probes, "counts_all_arms": _counts(items),
                        "first_attempt": _first_attempt(items),
                        "by_arm": {episode["arm"]: _episode(episode, probes) for episode in items}})
    report = {
        "schema": "astra-trace-diagnostics-v1", "status": "POST_HOC_TRACE_BOOKKEEPING",
        "study": "astra-agent-research-v1", "analysis_timing": "post-hoc",
        "financial_scores_recomputed": False, "assessment_artifact_read": False,
        "market_data_reads": 0, "model_or_network_calls": 0,
        "inputs": {name: _identity(raw) for name, raw in captured.items()},
        "source_identity": {
            "diagnostics_module": _identity(Path(__file__).read_bytes()),
            "replay_module": _identity(Path(astra_replay.__file__).read_bytes()),
            "frozen_source_sha256": contract["source_sha256"], "frozen_plan": contract["plan"],
        },
        "verification": verified,
        "common_initial_probe_count": sum(row["common_initial_probes"]["probe_count"] for row in periods),
        "all": {"counts": _counts(episodes), "reported_usage": _usage(episodes),
                "historical_comparisons": _comparison_summary([p["by_arm"][arm] for p in periods for arm in ARMS])},
        "by_arm": {arm: {"counts": _counts([e for e in episodes if e["arm"] == arm]),
                         "reported_usage": _usage([e for e in episodes if e["arm"] == arm]),
                         "historical_comparisons": _comparison_summary([p["by_arm"][arm] for p in periods])}
                   for arm in ARMS},
        "first_attempt_matching": _matching_summary(periods), "periods": periods, "limits": LIMITS,
    }
    return {**report, "body_sha256": digest(report)}


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--submissions", required=True, type=Path)
    parser.add_argument("--source-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    inputs = [args.contract, args.submissions, Path(__file__), Path(astra_replay.__file__)]
    inputs.extend(args.source_root / "src" / "alpha_research_rl" / name for name in SOURCE_NAMES)
    inputs.append(args.source_root / "docs/astra-agent-research-plan-v1.md")
    if args.output.resolve() in {path.resolve() for path in inputs}:
        parser.error("output collides with an input")
    if args.output.exists():
        parser.error("output already exists; evidence is never overwritten")
    report = diagnose_traces(args.contract, args.submissions, source_root=args.source_root)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(canonical_json(report) + "\n")


if __name__ == "__main__":
    main()
