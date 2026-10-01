"""Replay public Astra evidence structurally, without a model, data load, or rescore."""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import math
import re
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath

from . import agentic_research, codex_actor, data, dsl
from .agentic_research import ACTOR_INSTRUCTIONS, ARMS, ResearchEpisode, canonical_json, digest
from .codex_actor import CLI_VERSION_CONTRACT, RESPONSE_SCHEMA, USAGE_KEYS

TASK_IDS = tuple(f"{year}-H{half}" for year in range(2020, 2025) for half in (1, 2))
PAIRS = tuple((task, arm) for task in TASK_IDS for arm in ARMS)
ROUNDS = {f"{task}/{attempt:02d}" for task in TASK_IDS for attempt in range(1, 7)}
SOURCE_NAMES = (
    "astra_study.py", "agentic_research.py", "codex_actor.py", "financial_policy.py",
    "financial_tasks.py", "dsl.py", "evaluation.py", "data.py", "french.py",
    "artifacts.py", "real_baselines.py", "llm.py",
)
MODEL_SETTINGS = {
    "model": "gpt-6-astra", "reasoning_effort": "ultra", "service_tier": "default",
    "sandbox": "read-only", "ephemeral": True, "timeout_seconds": 600,
    "maximum_concurrency": 3, "infrastructure_retries": 0,
}
CONTRASTS = (("full_minus_validity", ARMS[0], ARMS[1]),
             ("full_minus_withheld", ARMS[0], ARMS[2]),
             ("validity_minus_withheld", ARMS[1], ARMS[2]))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _keys(value: object, expected: set[str], name: str) -> None:
    _require(isinstance(value, dict) and set(value) == expected, f"unexpected {name} fields")


def _exact(actual: object, expected: object, name: str) -> None:
    _require(canonical_json(actual) == canonical_json(expected), f"{name} differs from exact replay")


def _number(value: object, name: str) -> float:
    _require(type(value) is float and math.isfinite(value), f"{name} must be a finite float")
    return value


def _computed(actual: object, expected: object, name: str) -> None:
    """Tolerance only for recomputed financial arithmetic; exact other types/keys."""
    if type(expected) is float:
        _require(math.isclose(_number(actual, name), expected, rel_tol=0, abs_tol=1e-12),
                 f"{name} differs from computed arithmetic")
    elif isinstance(expected, dict):
        _keys(actual, set(expected), name)
        for key, value in expected.items():
            _computed(actual[key], value, f"{name}.{key}")
    elif isinstance(expected, list):
        _require(isinstance(actual, list) and len(actual) == len(expected), f"invalid {name} length")
        for index, value in enumerate(expected):
            _computed(actual[index], value, f"{name}[{index}]")
    else:
        _require(type(actual) is type(expected) and actual == expected, f"invalid {name} metadata")


def _hash(value: object, name: str) -> str:
    _require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
             f"invalid {name} SHA256")
    return value


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _timestamp(value: object, name: str) -> datetime:
    _require(isinstance(value, str), f"invalid {name} timestamp")
    result = datetime.fromisoformat(value)
    _require(result.utcoffset() == timedelta(0), f"{name} must use UTC")
    return result


def _pairs(values):
    result = {}
    for key, value in values:
        _require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def _sealed(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_pairs)
    _require(isinstance(value, dict), "artifact must be a JSON object")
    canonical_json(value)
    _require(value.get("body_sha256") == digest({k: v for k, v in value.items() if k != "body_sha256"}),
             "artifact body digest mismatch")
    return value


def _relative(root: Path, relative: object) -> Path:
    _require(isinstance(relative, str) and "\\" not in relative, "invalid public relative path")
    parts = PurePosixPath(relative)
    _require(not parts.is_absolute() and ".." not in parts.parts and ":" not in relative,
             "public path cannot escape source root")
    path = (root / relative).resolve()
    _require(path.is_relative_to(root.resolve()), "public path resolves outside source root")
    return path


def _contract(contract: dict, root: Path) -> None:
    _keys(contract, {
        "study", "created_utc", "task_order", "arms", "attempts_per_episode", "round_order", "data", "plan",
        "source_sha256", "task_manifest_sha256", "model_settings", "interface", "runtime_versions",
        "cli_identity", "actor_context_relative_to_study", "initial_prompt_sha256", "assessment_score_calls",
        "quota_stop_remaining_percent", "assessment_gate", "body_sha256",
    }, "contract")
    _exact({key: contract[key] for key in (
        "study", "task_order", "arms", "attempts_per_episode", "round_order", "model_settings",
        "actor_context_relative_to_study", "assessment_score_calls", "quota_stop_remaining_percent", "assessment_gate",
    )}, {
        "study": "astra-agent-research-v1", "task_order": list(TASK_IDS), "arms": list(ARMS),
        "attempts_per_episode": 6, "round_order": [[t, j] for t in TASK_IDS for j in range(1, 7)],
        "model_settings": MODEL_SETTINGS, "actor_context_relative_to_study": "actor-context",
        "assessment_score_calls": 0, "quota_stop_remaining_percent": 5,
        "assessment_gate": "all 30 six-attempt episodes frozen; separate assess command",
    }, "contract metadata")
    _timestamp(contract["created_utc"], "contract")
    _keys(contract["source_sha256"], {f"src/alpha_research_rl/{name}" for name in SOURCE_NAMES}, "sources")
    for relative, expected in contract["source_sha256"].items():
        _require(_sha(_relative(root, relative)) == _hash(expected, "source"), "source byte identity mismatch")
    # The code actually executing the replay must also match the inspected root.
    for module in (agentic_research, codex_actor, data, dsl):
        relative = f"src/alpha_research_rl/{Path(module.__file__).name}"
        _require(_sha(Path(module.__file__)) == contract["source_sha256"][relative], "loaded replay dependency differs")
    _keys(contract["plan"], {"path", "sha256"}, "plan")
    _require(contract["plan"]["path"] == "docs/astra-agent-research-plan-v1.md", "unexpected plan path")
    _require(_sha(_relative(root, contract["plan"]["path"])) == _hash(contract["plan"]["sha256"], "plan"),
             "plan byte identity mismatch")
    _keys(contract["data"], {"path", "sha256"}, "data identity")
    _relative(root, contract["data"]["path"])  # Validate its name without opening the market data.
    _require(contract["data"]["sha256"] ==
             "8f394fe34bea54d41b9aafed410425ee8f8e252ede3c71a7c1cd20bab83040de", "unexpected data identity")
    for key in ("task_manifest_sha256", "initial_prompt_sha256"):
        _keys(contract[key], set(TASK_IDS), key)
        for value in contract[key].values():
            _hash(value, key)
    _exact(contract["interface"], {
        "actor_instructions_sha256": hashlib.sha256(ACTOR_INSTRUCTIONS.encode()).hexdigest(),
        "response_schema_sha256": digest(RESPONSE_SCHEMA), "cli_version_contract": CLI_VERSION_CONTRACT,
    }, "interface")
    _keys(contract["runtime_versions"], {"python", "numpy", "pandas", "scipy"}, "runtime versions")
    _require(all(isinstance(v, str) and v for v in contract["runtime_versions"].values()), "invalid runtime version")
    _keys(contract["cli_identity"], {"executable_name", "sha256", "version"}, "CLI identity")
    identity = contract["cli_identity"]
    _require(isinstance(identity["executable_name"], str) and identity["executable_name"]
             and not any(c in identity["executable_name"] for c in "/\\:"), "invalid executable basename")
    _hash(identity["sha256"], "CLI")
    _require(identity["version"] == f"codex-cli {CLI_VERSION_CONTRACT}", "unexpected CLI version")


def _transport(summary: dict, prompt: str, raw: str) -> None:
    _keys(summary, {
        "success", "status", "error", "event_error", "returncode", "elapsed_seconds", "started_at_utc",
        "ended_at_utc", "model_requested", "reasoning_effort_requested", "service_tier_requested",
        "model_attested_by_events", "cli_version_contract", "response_only_stream_valid", "tool_event_claim",
        "usage", "reported_usage_records", "usage_source", "attempts_started", "automatic_retries",
        "provider_retry_scope", "artifacts",
    }, "provider summary")
    expected = {
        "success": True, "status": "succeeded", "error": None, "event_error": None, "returncode": 0,
        "model_requested": "gpt-6-astra", "reasoning_effort_requested": "ultra", "service_tier_requested": "default",
        "model_attested_by_events": False, "cli_version_contract": CLI_VERSION_CONTRACT,
        "response_only_stream_valid": True, "tool_event_claim": "No tool events observed in retained stream.",
        "attempts_started": 1, "automatic_retries": 0,
        "provider_retry_scope": "No provider retry; native CLI/service retries are not attested.",
    }
    _exact({key: summary[key] for key in expected}, expected, "successful provider metadata")
    _require(_number(summary["elapsed_seconds"], "elapsed time") >= 0, "negative elapsed time")
    _require(_timestamp(summary["ended_at_utc"], "ended") >= _timestamp(summary["started_at_utc"], "started"),
             "provider end precedes start")
    usage = summary["usage"]
    if usage is None:
        _exact(summary["reported_usage_records"], [], "missing usage records")
        _exact(summary["usage_source"], "unavailable_or_ambiguous", "missing usage source")
    else:
        _require(isinstance(usage, dict) and {"input_tokens", "output_tokens"} <= set(usage) <= USAGE_KEYS
                 and all(type(v) is int and v >= 0 for v in usage.values()), "invalid reported token usage")
        _exact(summary["reported_usage_records"], [{"line_1based": 4, "usage": usage}], "usage records")
        _exact(summary["usage_source"], "validated_completed_stream", "usage source")
    _keys(summary["artifacts"], {"prompt.txt", "schema.json", "request.json", "events.jsonl", "stderr.log",
                                  "response.json"}, "provider artifacts")
    for value in summary["artifacts"].values():
        _keys(value, {"sha256", "bytes"}, "provider artifact identity")
        _hash(value["sha256"], "provider artifact")
        _require(type(value["bytes"]) is int and value["bytes"] >= 0, "invalid artifact byte count")
    for name, text in (("prompt.txt", prompt), ("response.json", raw)):
        encoded = text.encode("utf-8")
        _exact(summary["artifacts"][name], {"sha256": hashlib.sha256(encoded).hexdigest(), "bytes": len(encoded)},
               name)


def _replay_episode(item: dict, contract: dict) -> dict:
    _keys(item, {"task_id", "arm", "submission", "transport_summaries"}, "episode")
    saved = item["submission"]
    _require(isinstance(saved, dict) and isinstance(saved.get("records"), list) and len(saved["records"]) == 6,
             "each episode needs six saved records")
    _require(isinstance(item["transport_summaries"], list) and len(item["transport_summaries"]) == 6,
             "each episode needs six successful provider summaries")
    current = {}

    def saved_feedback(expression):
        _require(isinstance(current.get("packet"), dict) and current["packet"].get("expression") == expression,
                 "saved feedback does not correspond to the proposed expression")
        return copy.deepcopy(current.get("feedback"))

    episode = ResearchEpisode(item["arm"], saved.get("initial_evidence"), saved_feedback)
    _require(hashlib.sha256(episode.prompt().encode()).hexdigest() == contract["initial_prompt_sha256"][item["task_id"]],
             "initial prompt hash differs from contract")
    for record, summary in zip(saved["records"], item["transport_summaries"], strict=True):
        _require(isinstance(record, dict) and isinstance(record.get("raw_response"), str), "invalid saved response")
        current = record
        prompt = episode.prompt()
        _transport(summary, prompt, record["raw_response"])
        reconstructed = episode.submit(record["raw_response"])
        _exact(record, reconstructed, "attempt record, masks, cost and prompt hash")
    reconstructed = episode.freeze()
    _exact(saved, reconstructed, "episode selector and sealed freeze")
    return reconstructed


def _usage(episodes: list[dict]) -> dict:
    result = {}
    for arm in ARMS:
        summaries = [summary for item in episodes if item["arm"] == arm for summary in item["transport_summaries"]]
        fields = {}
        for field in sorted(USAGE_KEYS):
            values = [summary["usage"][field] for summary in summaries
                      if summary["usage"] is not None and field in summary["usage"]]
            fields[field] = {"reported_sum": sum(values), "reported_decisions": len(values),
                             "missing_decisions": 60 - len(values), "complete_sum": sum(values) if len(values) == 60 else None}
        elapsed = [summary["elapsed_seconds"] for summary in summaries]
        result[arm] = {"decision_count": 60, "missing_usage_decisions": sum(s["usage"] is None for s in summaries),
                       "token_fields": fields, "elapsed_seconds": {"total": math.fsum(elapsed),
                       "minimum": min(elapsed), "maximum": max(elapsed)}}
    return result


def _metrics(value: dict) -> bool:
    _keys(value, {"mean_ic", "coverage", "ic_std", "n_dates", "n_signal_dates"}, "assessment metrics")
    for key in ("n_dates", "n_signal_dates"):
        _require(type(value[key]) is int and value[key] >= 0, "invalid metric support count")
    _require(value["n_dates"] <= value["n_signal_dates"], "scored dates exceed signal dates")
    for key, lower, upper in (("mean_ic", -1, 1), ("coverage", 0, 1), ("ic_std", 0, math.inf)):
        if value[key] is not None:
            _require(lower <= _number(value[key], key) <= upper, "metric outside valid range")
    length = value["n_signal_dates"]
    return (value["mean_ic"] is not None and value["coverage"] is not None and value["coverage"] >= 0.8
            and value["n_dates"] >= max(min(20, length), math.ceil(0.8 * length)))


def _assessment(path: Path, submissions_path: Path, episodes: list[dict]) -> dict:
    report = _sealed(path)
    _keys(report, {"study", "stage", "episode_count", "paired_task_count", "results", "paired",
                   "primary_mean_full_minus_validity", "arm_summaries", "contrasts", "year_averages",
                   "submissions_sha256", "interpretation", "body_sha256"}, "assessment")
    metadata = {"study": "astra-agent-research-v1", "stage": "development-assessment-complete",
                "episode_count": 30, "paired_task_count": 10, "submissions_sha256": _sha(submissions_path),
                "interpretation": "descriptive development; no untouched holdout or profitability claim"}
    _exact({key: report[key] for key in metadata}, metadata, "assessment metadata")
    rows = report["results"]
    _require(isinstance(rows, list) and len(rows) == 30, "assessment requires all 30 outcomes")
    values, by_arm = {}, {arm: [] for arm in ARMS}
    for row, episode in zip(rows, episodes, strict=True):
        _keys(row, {"task_id", "arm", "outcome"}, "assessment row")
        _exact([row["task_id"], row["arm"]], [episode["task_id"], episode["arm"]], "assessment row identity")
        outcome, selection = row["outcome"], episode["submission"]["selection"]
        if selection is None:
            _exact(outcome, {"status": "invalid", "reason": "all_proposals_invalid_or_unusable", "reward": -1.06,
                             "cost": 0.06, "oriented_future_ic": None, "assessment_evaluator_called": False},
                   "null selection outcome")
        else:
            _keys(outcome, {"expression", "reward", "cost", "status", "reason", "anchor_reuse", "orientation",
                           "feedback", "assessment", "oriented_future_ic", "zero_feedback_tie",
                           "one_proposal_reward", "assessment_evaluator_called"}, "selected outcome")
            saved = episode["submission"]["records"][selection["attempt"] - 1]
            feedback = {key: value for key, value in saved["feedback"].items() if key != "usable"}
            _require(_metrics(outcome["feedback"]), "selected feedback is unusable")
            _exact(outcome["feedback"], feedback, "frozen selected feedback")
            probe_asts = {ast.dump(ast.parse(expression, mode="eval"), include_attributes=False)
                          for expression in ("ts_mean(returns,5)", "ts_mean(returns,20)")}
            expected = {"expression": selection["expression"], "orientation": selection["orientation"],
                        "cost": 0.06, "assessment_evaluator_called": True,
                        "zero_feedback_tie": selection["feedback_ic"] == 0,
                        "anchor_reuse": saved["canonical_ast"] in probe_asts}
            _exact({key: outcome[key] for key in expected}, expected, "selected outcome metadata")
            _require(outcome["status"] in ("ok", "invalid", "unscorable"), "unknown assessment status")
            usable = False if outcome["assessment"] is None else _metrics(outcome["assessment"])
            if outcome["status"] == "ok":
                _require(usable and outcome["reason"] is None, "successful assessment has unusable support")
                ic = outcome["assessment"]["mean_ic"] * selection["orientation"]
                _computed(outcome["oriented_future_ic"], ic, "oriented assessment IC")
                _computed(outcome["one_proposal_reward"], ic - 0.01, "one-proposal utility")
                _computed(outcome["reward"], ic - 0.06, "six-attempt utility")
            else:
                _require(not usable and outcome["oriented_future_ic"] is None, "failed assessment contains usable IC")
                reason = "invalid_expression" if outcome["status"] == "invalid" else "insufficient_assessment_support"
                _exact(outcome["reason"], reason, "assessment failure reason")
                _computed(outcome["one_proposal_reward"], -1.01, "invalid one-proposal utility")
                _computed(outcome["reward"], -1.06, "invalid six-attempt utility")
        values[row["task_id"], row["arm"]] = outcome["reward"]
        by_arm[row["arm"]].append(outcome)
    paired = [{"task_id": task, **{name: values[task, left] - values[task, right]
                                    for name, left, right in CONTRASTS}} for task in TASK_IDS]
    arms = {}
    for arm, outcomes in by_arm.items():
        valid = [row for row in outcomes if row["status"] == "ok"]
        p = len(valid) / 10
        q = math.fsum(row["oriented_future_ic"] for row in valid) / 10
        mean = math.fsum(row["reward"] for row in outcomes) / 10
        _computed(mean, -1.06 + p + q, "utility decomposition")
        arms[arm] = {"task_count": 10, "valid_assessment_count": len(valid), "validity_fraction_p": p,
                     "predictive_contribution_q": q, "mean_utility": mean,
                     "conditional_valid_mean_ic": q / p if p else None}
    contrasts = {name: {"mean_utility_difference": math.fsum(row[name] for row in paired) / 10,
                        "validity_contribution": arms[left]["validity_fraction_p"] - arms[right]["validity_fraction_p"],
                        "predictive_contribution": arms[left]["predictive_contribution_q"] -
                        arms[right]["predictive_contribution_q"]} for name, left, right in CONTRASTS}
    years = [{"year": year, **{name: math.fsum(row[name] for row in paired
                                               if row["task_id"].startswith(str(year))) / 2
                               for name, _, _ in CONTRASTS}} for year in range(2020, 2025)]
    for key, expected in (("paired", paired), ("arm_summaries", arms), ("contrasts", contrasts),
                           ("year_averages", years), ("primary_mean_full_minus_validity",
                                                      contrasts["full_minus_validity"]["mean_utility_difference"])):
        _computed(report[key], expected, key)
    return {"status": "SAVED_ARITHMETIC_VERIFIED", "file_sha256": _sha(path),
            "outcome_count": 30, "market_scores_recomputed": False}


def replay_study(contract_path: Path, submissions_path: Path, *, source_root: Path,
                 assessment_path: Path | None = None) -> dict:
    """Validate public structure; saved financial feedback is not independently recomputed."""
    contract_path, submissions_path, source_root = map(Path, (contract_path, submissions_path, source_root))
    contract, submissions = _sealed(contract_path), _sealed(submissions_path)
    _contract(contract, source_root)
    _keys(submissions, {"study", "stage", "frozen_utc", "contract_sha256", "episode_count",
                        "completed_response_count", "assessment_score_calls", "episodes", "round_sha256", "body_sha256"},
          "submissions")
    expected = {"study": "astra-agent-research-v1", "stage": "all-submissions-frozen", "episode_count": 30,
                "completed_response_count": 180, "assessment_score_calls": 0, "contract_sha256": _sha(contract_path)}
    _exact({key: submissions[key] for key in expected}, expected, "submission metadata")
    _timestamp(submissions["frozen_utc"], "submission freeze")
    _keys(submissions["round_sha256"], ROUNDS, "round identities")
    for value in submissions["round_sha256"].values():
        _hash(value, "round")
    items = submissions["episodes"]
    _require(isinstance(items, list) and len(items) == 30, "fixed bank requires 30 episodes")
    _require(all(isinstance(item, dict) for item in items), "invalid episode object")
    _exact([[item.get("task_id"), item.get("arm")] for item in items], [list(pair) for pair in PAIRS],
           "fixed ten-task, three-arm episode order")
    reconstructed = [_replay_episode(item, contract) for item in items]
    assessment = None if assessment_path is None else _assessment(Path(assessment_path), submissions_path, items)
    return {
        "status": "STRUCTURALLY_VERIFIED", "study": "astra-agent-research-v1", "episode_count": 30,
        "attempt_count": 180, "contract_sha256": _sha(contract_path), "submissions_sha256": _sha(submissions_path),
        "source_and_plan_bytes_verified": True, "financial_scores_recomputed": False,
        "model_or_network_calls": 0, "market_data_reads": 0, "assessment": assessment,
        "usage_by_arm": _usage(items), "selected_episode_count": sum(row["selection"] is not None for row in reconstructed),
        "limits": ["Saved feedback and assessment metrics are evidence, not independently verified market calculations.",
                   "Token fields are reported separately; reasoning tokens are never added to output tokens.",
                   "Private raw streams, task manifests, round files, publication timing and hidden host context are not revalidated."],
    }


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--submissions", required=True, type=Path)
    parser.add_argument("--source-root", type=Path, default=Path.cwd())
    parser.add_argument("--assessment", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    inputs = [args.contract, args.submissions] + ([args.assessment] if args.assessment is not None else [])
    inputs.extend(args.source_root / "src" / "alpha_research_rl" / name for name in SOURCE_NAMES)
    inputs.append(args.source_root / "docs" / "astra-agent-research-plan-v1.md")
    if args.output.resolve() in {path.resolve() for path in inputs}:
        parser.error("output collides with an input")
    if args.output.exists():
        parser.error("output already exists; evidence is never overwritten")
    report = replay_study(args.contract, args.submissions, source_root=args.source_root, assessment_path=args.assessment)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(canonical_json(report) + "\n")


if __name__ == "__main__":
    main()
