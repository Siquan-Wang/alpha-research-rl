"""CPU reconstruction of the original saved synthetic sequential trajectories.

Actions and episode totals are original evidence. Observations, per-step costs
and compact actor views are reconstructions, never authenticated model prompts.
No actor, tokenizer, torch, or transformers module is imported.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path

from .artifacts import json_safe, source_digest, write_json
from .data import make_synthetic_panel
from .environment import ResearchEnvironment
from .protocol import make_chronological_split

HISTORICAL_COMMIT = "99eda9525831e9ec01e857ca2f5546f5e7b97760"
HISTORICAL_PACKAGE_SHA256 = "701992ddc61c59d691f93a746f47c6b779b55aab893b243c16a24fd55bc8f736"
LABELS = ("base", "sft", "rloo")
# Exact original report bytes, plus canonical bodies to bind parsed API inputs.
# The latter prevents a caller from supplying an old digest for changed content.
REPORT_PINS = {
    "base": {"sha256": "d387a5312cb9d539f052cd0f7e0fd7a85417e8ce8d6a380c489217a46611b6b6",
             "canonical_sha256": "508495780400951d4e2e3bb9bfdf07e9df0c7257cdf53fd2cf731e4f7844eeb1"},
    "sft": {"sha256": "5a7c50d80fe83d8e72d953e5b37c4cb2596e5f6acb955e28a3fc2de62f3e7832",
            "canonical_sha256": "75427be673ed884bf44857aaead80039c3c5eb8d551ccb44b5fc578620dcafd7"},
    "rloo": {"sha256": "63688be94a6487daf7891d744deacb5fe50c079097efe509c8238f924aacdc27",
             "canonical_sha256": "2faa8a143ff2c0da0164c7aace203854aa0bb937f1cb1a1e6627d3b4b217a634"},
}
TASKS = tuple((11000 + i, ("signal", "null", "decay")[i % 3]) for i in range(6))
REPLAY_CONFIG = {"n_dates": 300, "n_assets": 16, "horizon": 5, "fit_fraction": .4,
                 "feedback_fraction": .3, "budget": 10, "budget_cost": .001,
                 "allow_generation": True, "max_candidates": 64,
                 "initial_factors": ["returns", "ts_mean(returns,5)", "ts_std(returns,20)"]}
SOURCE_PINS = {
    "artifacts.py": "40778baf42dea55c284ccb45e0d0dbb8654a6f016ff6260e637041e83ae891e6",
    "data.py": "21be3b5df887acdfc97d3ebfe2b191c91db2f647f44516d9f5c987e33f39b48c",
    "dsl.py": "47c311c0d2b4074653789bf1275081a58517822d0f1fc0a6fb811fd796e8ba97",
    "environment.py": "739d7fc8136ebd5923b4b8ae82b9c45e34f5a76008abc9a490a0a12f932ef538",
    "evaluation.py": "19262b9412b2f6cfe275650d2f6b27096b0140ccc85e3f73d69005c3bdd872c7",
    "protocol.py": "628607151f70041d6aecdd5af0f06b55cd07d99805b4698fc3667166525fe2f9",
    "llm_evaluation.py": "bd733c21eadaba783434fdb93530f5e285744fe0f39a1b12192054dbfe8b9e7e",
}
AST_PINS = {
    "training.py": {"INITIAL_FACTORS": "399e9ee2689edb81c5706f600949d21283b2b2f4a0d4b900eb0ef90085f55e1b",
                    "make_training_env": "ecd882372d02350b38e811c7129a46447236ed5f4c4cbfa81bf5c7dea827b12b"},
    "llm.py": {"parse_action": "44e80bb35e19fa21a145087fac3e94b1faa6ab7ab713c943ffc6c837c49161c4",
               "compact_observation": "d1493c36bc070ccaed65b3f22afe231316f68b6908d327f6de4f910d39aaaa5d",
               "SYSTEM": "1e58e08c7df621e9ab24cf8a3d641218ed133f5a8f8af0be6589df9a891f6939"},
}
HISTORICAL_MODULE_HASHES = {
    "training.py": "8ce2fa8abc6d5db625a3290494236428f78960ef3c8b27526796ebdd3a6abcff",
    "llm.py": "c7c02555d2339aaae14228b1674877bdf72f5756a9f06e3c2c84509cc287dc09",
}


class ReplayMismatch(ValueError):
    """Saved evidence or the matching replay contract cannot be verified."""


def _require(condition, context, expected, actual):
    if not condition:
        raise ReplayMismatch(f"{context}: expected {expected!r}; actual {actual!r}")


def _hash(raw):
    return hashlib.sha256(raw).hexdigest()


def _ast_hash(raw, name):
    nodes = [node for node in ast.parse(raw).body if getattr(node, "name", None) == name
             or isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name
                                                     for target in node.targets)]
    _require(len(nodes) == 1, "AST provenance " + name, "one named definition", len(nodes))
    return _hash(ast.dump(nodes[0], include_attributes=False).encode())


def verify_replay_sources() -> dict:
    """Pin replay semantics; unrelated actor/optimizer edits are not imported."""
    root = Path(__file__).parent
    source_hashes, ast_hashes = {}, {}
    for filename, expected in SOURCE_PINS.items():
        actual = _hash((root / filename).read_bytes())
        _require(actual == expected, "source mismatch " + filename, expected, actual)
        source_hashes[filename] = actual
    for filename, definitions in AST_PINS.items():
        raw = (root / filename).read_bytes()
        source_hashes[filename] = _hash(raw)
        ast_hashes[filename] = {}
        for name, expected in definitions.items():
            actual = _ast_hash(raw, name)
            _require(actual == expected, f"source AST mismatch {filename}/{name}", expected, actual)
            ast_hashes[filename][name] = actual
    current = source_digest()
    return {"historical_commit": HISTORICAL_COMMIT,
            "historical_package_sha256": HISTORICAL_PACKAGE_SHA256,
            "historical_package_digest_verified_from_commit_blobs": True,
            "historical_commit_blob_verification_scope": "One-time author source assessment; not rerun by replay",
            "historical_package_hash_method": "SHA256 of sorted package-relative .py names followed by exact commit-blob bytes",
            "runtime_commit_blobs_checked": False,
            "current_package_sha256": current,
            "whole_package_matches_original": current == HISTORICAL_PACKAGE_SHA256,
            "current_source_files_sha256": source_hashes, "historical_replay_file_pins": dict(SOURCE_PINS),
            "matching_config_parser_serializer_ast_sha256": ast_hashes,
            "historical_other_module_sha256": dict(HISTORICAL_MODULE_HASHES),
            "other_module_whole_file_drift": {name: source_hashes[name] != expected
                                             for name, expected in HISTORICAL_MODULE_HASHES.items()},
            "replay_module_sha256": _hash(Path(__file__).read_bytes())}


def _parse_action(text):
    # Exact small CPU copy of the pinned historical parse_action definition.
    try:
        result = json.loads(text.strip())
    except (ValueError, TypeError):
        return {"action": "invalid"}
    return result if isinstance(result, dict) else {"action": "invalid"}


def _state(observation):
    environment = json_safe(copy.deepcopy(observation))
    compact = {key: value for key, value in environment.items() if key not in {"history", "done"}}
    compact["recent_actions"] = environment.get("history", [])[-3:]
    serialized = json.dumps(compact, separators=(",", ":"), allow_nan=False)
    return {"reconstructed": True, "environment": environment,
            "actor_visible": compact, "actor_visible_json": serialized}


def _make_env(seed, regime):
    # The original factory's AST and INITIAL_FACTORS are pinned above. Its
    # otherwise implicit defaults are explicit here, without importing training.
    c = REPLAY_CONFIG
    panel = make_synthetic_panel(seed, n_dates=c["n_dates"], n_assets=c["n_assets"], regime=regime)
    split = make_chronological_split(c["n_dates"], c["horizon"], c["fit_fraction"], c["feedback_fraction"])
    env = ResearchEnvironment(panel, split, list(c["initial_factors"]), budget=c["budget"],
                              budget_cost=c["budget_cost"], allow_generation=c["allow_generation"],
                              max_candidates=c["max_candidates"])
    return env, split


def _finite_json(value):
    if isinstance(value, dict):
        return all(isinstance(key, str) and _finite_json(item) for key, item in value.items())
    if isinstance(value, list):
        return all(_finite_json(item) for item in value)
    return value is None or isinstance(value, (str, bool, int)) or isinstance(value, float) and math.isfinite(value)


def replay_reports(reports: dict[str, dict], source_reports: dict[str, dict]) -> dict:
    """Reconstruct all 18 episodes; fail rather than publish a partial replay."""
    _require(set(reports) == set(LABELS) == set(source_reports), "report roles", LABELS, tuple(reports))
    proof = verify_replay_sources()
    packages = {name: importlib.metadata.version(name) for name in ("numpy", "scipy")}
    episodes = []
    for label in LABELS:
        source = source_reports[label]
        filename, digest = source.get("file"), source.get("sha256")
        _require(isinstance(filename, str) and filename and not any(c in filename for c in "/\\:"),
                 label + " source name", "public basename", filename)
        _require(isinstance(digest, str) and len(digest) == 64 and all(c in "0123456789abcdef" for c in digest),
                 label + " source hash", "SHA256", digest)
        _require(digest == REPORT_PINS[label]["sha256"], label + " original report byte identity",
                 REPORT_PINS[label]["sha256"], digest)
        report = reports[label]
        _require(_finite_json(report), label + " report", "finite JSON", "nonfinite or unsupported value")
        manifest, config = report["manifest"], report["manifest"]["config"]
        _require(manifest.get("source_sha256") == HISTORICAL_PACKAGE_SHA256, label + " historical source",
                 HISTORICAL_PACKAGE_SHA256, manifest.get("source_sha256"))
        _require(config == {"label": label, "tasks": [{"seed": seed, "regime": regime} for seed, regime in TASKS],
                            "decoding": "greedy", "data": "synthetic development only", "max_action_tokens": 64,
                            "budget": 10, "not_final_holdout": True}, label + " evaluation configuration",
                 "exact original six-task greedy configuration", config)
        for name, actual in packages.items():
            _require(manifest["packages"].get(name) == actual, label + " numeric dependency " + name,
                     manifest["packages"].get(name), actual)
        _require(len(report["episodes"]) == len(TASKS), label + " episode count", 6, len(report["episodes"]))
        for saved, (seed, regime) in zip(report["episodes"], TASKS, strict=True):
            context = f"{label}/{seed}/{regime}"
            _require(type(saved.get("seed")) is int and (saved["seed"], saved.get("regime")) == (seed, regime),
                     context + " task identity/order", (seed, regime), (saved.get("seed"), saved.get("regime")))
            env, split = _make_env(seed, regime)
            observation, steps, total_cost = env.reset(), [], 0
            actions = saved["actions"]
            _require(isinstance(actions, list) and 0 < len(actions) <= 11, context + " action count", "1..11", len(actions))
            reward, done = None, False
            for index, recorded in enumerate(actions):
                step_context = f"{context}/step{index}"
                _require(not done, step_context + " trailing action", "unfinished episode", "already done")
                _require(isinstance(recorded.get("text"), str) and type(recorded.get("terminated")) is bool,
                         step_context + " saved generation", "text + saved EOS boolean", recorded)
                parsed = _parse_action(recorded["text"]) if recorded["terminated"] else {"action": "invalid"}
                _require(recorded.get("action") == parsed, step_context + " strict parsed action", parsed, recorded.get("action"))
                before = _state(observation)
                observation, reward, done, info = env.step(copy.deepcopy(recorded["action"]))
                for field in ("status", "reason"):
                    _require(info[field] == recorded.get(field), step_context + " " + field, recorded.get(field), info[field])
                cost = observation["history"][-1]["cost"]
                _require(cost == before["environment"]["budget"] - observation["budget"], step_context + " derived cost",
                         before["environment"]["budget"] - observation["budget"], cost)
                total_cost += cost
                for field, actual in (("cost", cost), ("reward", reward), ("selected", observation["selected"])):
                    if field in recorded:
                        _require(actual == recorded[field], step_context + " saved " + field, recorded[field], actual)
                steps.append({"index": index, "saved": copy.deepcopy(recorded), "before": before,
                              "after": _state(observation), "cost": cost, "reward": reward, "done": done,
                              "status": info["status"], "reason": info["reason"]})
            _require(done, context + " terminal state", True, done)
            for field, actual in (("spent_budget", observation["spent_budget"]), ("selected", observation["selected"]),
                                  ("reward", reward)):
                _require(actual == saved.get(field), context + " terminal " + field, saved.get(field), actual)
            _require(total_cost == saved["spent_budget"], context + " summed reconstructed costs", saved["spent_budget"], total_cost)
            episodes.append({"label": label, "seed": seed, "regime": regime, "synthetic": True,
                             "environment_config": copy.deepcopy(REPLAY_CONFIG), "split": split.to_dict(),
                             "steps": steps, "terminal": {"reward": reward, "spent_budget": total_cost,
                                                          "selected": observation["selected"]},
                             "checks": {"action_status_reason_exact": True, "terminal_reward_exact": True,
                                        "terminal_spend_selection_exact": True, "no_missing_or_trailing_actions": True}})
        # Run detailed semantic checks first to preserve exact mismatch locations.
        canonical = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
        actual = _hash(canonical)
        _require(actual == REPORT_PINS[label]["canonical_sha256"], label + " original report canonical identity",
                 REPORT_PINS[label]["canonical_sha256"], actual)
    result = {"study": "synthetic-sequential-trajectory-reconstruction-v1", "verified": True,
              "provenance": {**proof, "source_reports": copy.deepcopy(source_reports), "numeric_packages": packages,
                  "original_report_identity_pins": copy.deepcopy(REPORT_PINS),
                  "original_report_byte_and_canonical_identities_verified": True,
                  "reconstruction": True, "original_actor_prompt_authenticated": False,
                  "original_eos_tokens_authenticated": False, "original_action_token_count_authenticated": False,
                  "directly_checked_saved_fields": ["action", "status", "reason", "terminal_reward", "spent_budget", "selected"],
                  "reconstructed_fields": ["before_after_observations", "compact_actor_views", "step_costs", "step_rewards"],
                  "limits": ["Original reports omitted observations, prompt/completion token IDs and per-action costs",
                             "Saved EOS boolean is retained; original token-level EOS/64-token compliance cannot be authenticated",
                             "Compact JSON is reconstructed state serialization, not the historical system/chat-template/token prompt",
                             "Whole-package drift includes unrelated additions; replay dependencies and config/parser/serializer are pinned",
                             "Automatic feedback orientation is environment behavior, not evidence of actor adaptation"]},
              "episodes": episodes,
              "summary": {"n_episodes": len(episodes), "n_steps": sum(len(e["steps"]) for e in episodes),
                          "maximum_terminal_reward_difference": 0.0, "all_recorded_outcome_checks_exact": True}}
    _require(_finite_json(result), "replay output", "finite JSON", "nonfinite or unsupported value")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for label in LABELS:
        parser.add_argument("--" + label, type=Path, default=Path(f"artifacts/development/{label}-v1.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    for label in LABELS:
        path = getattr(args, label).resolve()
        _require(output != path, "output/input path collision", "output distinct from all original reports", label)
    reports, sources = {}, {}
    for label in LABELS:
        path = getattr(args, label)
        raw = path.read_bytes()
        reports[label] = json.loads(raw.decode("utf-8"))
        sources[label] = {"file": path.name, "sha256": _hash(raw)}
    try:
        result = replay_reports(reports, sources)
    except (KeyError, TypeError, AttributeError) as exc:
        raise ReplayMismatch(f"malformed saved report; original inputs preserved: {exc}") from exc
    write_json(args.output, result)
    print(json.dumps(result["summary"]))


if __name__ == "__main__":
    main()
