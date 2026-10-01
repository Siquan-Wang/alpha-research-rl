"""Separate post-hoc assessment of the immutable Astra candidate pool.

Preparation and saved-record replay never import a market loader or evaluator.
Only explicitly gated execution can make the bounded additional CPU calls.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import re
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from . import astra_replay
from .agentic_research import ARMS, canonical_json, digest
from .astra_replay import CONTRASTS, TASK_IDS, replay_study

STUDY = "astra-frozen-pool-diagnosis-v1"
PUBLIC_DIRECTORY = "artifacts/astra-pool-diagnosis-v1"
PLAN_PATH = "docs/astra-pool-diagnosis-plan-v1.md"
IMPLEMENTATION_PATHS = (
    "src/alpha_research_rl/astra_pool_diagnosis.py", "src/alpha_research_rl/astra_replay.py",
    "tests/test_astra_pool_diagnosis.py", "docs/reproduce-astra-pool-diagnosis.md",
)
INPUT_HASHES = {
    "contract": "63848687bb44ea7d835b0a2d6ebe88d95dd7ed7257c8ca27dd216a6c37d8b17a",
    "submissions": "89b9cd42d4d248393c2c3c2b9f29714fb9ba023b511d9b3741196d99a321def7",
    "assessment": "30aafbc089f6017c99c6d23c14fca077ffcdf59e9cbf0599d28560c4446ff2a0",
}
RUNTIME = {"python": "3.12.14", "numpy": "2.5.3", "pandas": "3.0.6", "scipy": "1.18.1"}
POPULATION = {
    "slot_count": 180, "episode_count": 30, "key_count": 132, "reuse_key_count": 24,
    "pending_job_count": 108, "positive_slot_orientations": 167, "negative_slot_orientations": 13,
    "null_slot_orientations": 0, "within_episode_duplicates": 0,
    "keys_by_task": [13, 12, 15, 14, 13, 14, 12, 12, 14, 13],
}
RULES = {
    "six_proposal_cost": 0.06, "invalid_utility": -1.06, "max_new_evaluations": 108,
    "key": "canonical_json([task_id, canonical_ast, feedback_orientation]) SHA256",
    "job_order": "first occurrence in chronological task, registered arm, attempt order",
    "original": "frozen feedback absolute-IC maximum; earliest-attempt tie",
    "first": "literal attempt 1, including invalid/unusable",
    "minimum_ast": "fewest ast.walk nodes among grammar-valid usable nonduplicates; earliest tie",
    "oracle": "hindsight maximum over all six fixed-cost utilities; earliest tie",
    "continuation": "explicit clean completed prefix only; no retry or ambiguous continuation",
    "invalid_future": "invalid/invalid_expression, matching historical fields, assessment null",
    "arithmetic_absolute_tolerance": 1e-12, "arithmetic_relative_tolerance": 1e-12,
}
RAW_FIELDS = {"expression", "reward", "cost", "status", "reason", "anchor_reuse", "orientation",
              "feedback", "assessment", "oriented_future_ic", "zero_feedback_tie"}
METRIC_FIELDS = {"mean_ic", "coverage", "ic_std", "n_dates", "n_signal_dates"}
FINANCIAL_MANIFEST_FIELDS = {
    "task_id", "split", "year", "half", "feedback_signal_dates", "assessment_signal_dates", "horizon_sessions",
    "feedback_bounds_half_open", "assessment_bounds_half_open", "raw_feedback_bounds_half_open",
    "raw_assessment_bounds_half_open", "feedback_label_support_dates", "assessment_label_support_dates",
    "feedback_label_boundary", "assessment_label_boundary", "diagnostic_windows",
}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _keys(value, fields, name):
    _require(type(value) is dict and set(value) == fields, f"unexpected {name} schema")


def _exact(actual, expected, name):
    _require(canonical_json(actual) == canonical_json(expected), f"{name} differs from frozen evidence")


def _arithmetic(actual, expected, name):
    if type(expected) is float:
        _require(type(actual) is float and math.isfinite(actual)
                 and math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12), f"invalid {name} arithmetic")
    elif type(expected) is dict:
        _keys(actual, set(expected), name)
        for key in expected:
            if key == "cost":
                _exact(actual[key], expected[key], name + "." + key)
            else:
                _arithmetic(actual[key], expected[key], name + "." + key)
    elif type(expected) is list:
        _require(type(actual) is list and len(actual) == len(expected), f"invalid {name} length")
        for left, right in zip(actual, expected, strict=True):
            _arithmetic(left, right, name)
    else:
        _require(type(actual) is type(expected) and actual == expected, f"invalid {name} metadata")


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _sealed(body):
    _require("body_sha256" not in body, "body already sealed")
    return {**body, "body_sha256": digest(body)}


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        _require(key not in value, "duplicate JSON field")
        value[key] = item
    return value


def _read(raw):
    value = json.loads(raw, object_pairs_hook=_pairs)
    _require(type(value) is dict, "artifact is not an object")
    canonical_json(value)
    _require(value.get("body_sha256") == digest({k: v for k, v in value.items() if k != "body_sha256"}),
             "artifact body digest mismatch")
    return value


def _write(path, value):
    raw = (canonical_json(value) + "\n").encode("utf-8")
    _write_bytes(path, raw)


def _write_bytes(path, raw):
    with Path(path).open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def _relative(path, root):
    return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()


def _path(root, relative):
    _require(type(relative) is str and relative and "\\" not in relative and ":" not in relative,
             "invalid relative public path")
    result = (Path(root) / relative).resolve()
    _require(result.is_relative_to(Path(root).resolve()), "path escapes source root")
    return result


def _now():
    return datetime.now(UTC).isoformat()


def _utc(value):
    _require(type(value) is str, "timestamp must be a string")
    stamp = datetime.fromisoformat(value)
    _require(stamp.utcoffset() is not None and stamp.utcoffset().total_seconds() == 0, "timestamp must use UTC")
    return stamp


def _versions():
    return {"python": platform.python_version(),
            **{name: importlib.metadata.version(name) for name in ("numpy", "pandas", "scipy")}}


def _data_bytes(path, expected):
    raw = Path(path).read_bytes()
    _require(_sha(raw) == expected, "raw data byte identity mismatch")
    return raw


def _metric(value, length):
    _keys(value, METRIC_FIELDS, "metric")
    _require(type(value["n_dates"]) is int and 0 <= value["n_dates"] <= length
             and type(value["n_signal_dates"]) is int and value["n_signal_dates"] == length,
             "metric support differs from frozen task length")
    for name, lower, upper in (("mean_ic", -1, 1), ("coverage", 0, 1), ("ic_std", 0, math.inf)):
        number = value[name]
        if name == "coverage" or number is not None:
            _require(type(number) is float and math.isfinite(number) and lower <= number <= upper,
                     "invalid metric scalar")
    _require((value["n_dates"] == 0 and value["mean_ic"] is None and value["ic_std"] is None)
             or (value["n_dates"] > 0 and value["mean_ic"] is not None and value["ic_std"] is not None),
             "metric nulls disagree with valid-date count")
    return (value["mean_ic"] is not None and value["coverage"] >= 0.8
            and value["n_dates"] >= max(min(20, length), math.ceil(0.8 * length)))


def _task_record(raw, task_id, expected_hash, initial):
    _require(_sha(raw) == expected_hash, "original task bytes differ from v1 contract")
    record = _read(raw)
    _keys(record, {"task_id", "interpretation", "financial_manifest", "initial_observation", "body_sha256"},
          "task record")
    _exact(record["task_id"], task_id, "task ID")
    _exact(record["interpretation"], "previously examined chronological DEVELOPMENT", "task interpretation")
    _exact(record["initial_observation"], initial, "initial task observation")
    manifest = record["financial_manifest"]
    _keys(manifest, FINANCIAL_MANIFEST_FIELDS, "financial manifest")
    _exact([manifest["task_id"], manifest["year"], manifest["half"], manifest["horizon_sessions"]],
           [task_id, int(task_id[:4]), int(task_id[-1]), 5], "task identity/horizon")
    _require(type(manifest["split"]) is str and type(manifest["diagnostic_windows"]) is str,
             "invalid task labels")
    for period in ("feedback", "assessment"):
        bounds = manifest[period + "_bounds_half_open"]
        raw_bounds = manifest["raw_" + period + "_bounds_half_open"]
        _require(type(bounds) is list and len(bounds) == 2 and all(type(x) is int for x in bounds)
                 and 0 <= bounds[0] < bounds[1], "invalid frozen task bounds")
        _exact(raw_bounds, [bounds[0], bounds[1] + 5], "purged task boundary")
        _exact(manifest[period + "_label_boundary"], raw_bounds[1], "label boundary")
        for suffix in ("signal_dates", "label_support_dates"):
            dates = manifest[period + "_" + suffix]
            _require(type(dates) is list and len(dates) == 2
                     and all(type(x) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}", x) for x in dates),
                     "invalid task date metadata")
    _require(manifest["feedback_bounds_half_open"][1] < manifest["assessment_bounds_half_open"][0],
             "historical/future boundaries overlap")
    return record


def _node_count(expression):
    return sum(1 for _ in ast.walk(ast.parse(expression.strip(), mode="eval")))


def _outcome(raw, key, task_record, *, evaluated_expression=None):
    """Validate original one-call scorer output before deriving fixed-cost utility."""
    _keys(raw, RAW_FIELDS, "frozen evaluator outcome")
    expression = key["evaluation_expression"] if evaluated_expression is None else evaluated_expression
    _exact(raw["expression"], expression, "evaluated expression spelling")
    _exact(ast.dump(ast.parse(expression.strip(), mode="eval"), include_attributes=False), key["canonical_ast"],
           "evaluated AST")
    bounds = task_record["financial_manifest"]
    historical_length = bounds["feedback_bounds_half_open"][1] - bounds["feedback_bounds_half_open"][0]
    future_length = bounds["assessment_bounds_half_open"][1] - bounds["assessment_bounds_half_open"][0]
    _require(_metric(raw["feedback"], historical_length), "returned historical feedback is unusable")
    _exact(raw["feedback"], key["feedback"], "historical feedback")
    _exact(raw["orientation"], key["orientation"], "feedback-fixed orientation")
    _exact(raw["zero_feedback_tie"], key["feedback"]["mean_ic"] == 0, "zero-feedback tie")
    probes = {ast.dump(ast.parse(e, mode="eval"), include_attributes=False)
              for e in ("ts_mean(returns,5)", "ts_mean(returns,20)")}
    _exact(raw["anchor_reuse"], key["canonical_ast"] in probes, "probe AST identity")
    _exact(raw["cost"], 0.01, "original cost")
    usable = False if raw["assessment"] is None else _metric(raw["assessment"], future_length)
    if raw["status"] == "ok":
        _require(usable and raw["reason"] is None, "successful outcome has unusable assessment")
        ic = key["orientation"] * raw["assessment"]["mean_ic"]
        _arithmetic(raw["oriented_future_ic"], ic, "oriented future IC")
        _arithmetic(raw["reward"], ic - 0.01, "original reward")
        return {"status": "ok", "valid": True, "oriented_future_ic": ic, "utility": ic - 0.06, "cost": 0.06}
    _require((raw["status"] == "unscorable" and raw["reason"] == "insufficient_assessment_support"
              and raw["assessment"] is not None and not usable)
             or (raw["status"] == "invalid" and raw["reason"] == "invalid_expression"
                 and raw["assessment"] is None), "unexplained evaluator failure state")
    _exact(raw["oriented_future_ic"], None, "failed future IC")
    _arithmetic(raw["reward"], -1.01, "invalid original reward")
    return {"status": raw["status"], "valid": False, "oriented_future_ic": None, "utility": -1.06, "cost": 0.06}


def _raw_from_v1(outcome):
    _keys(outcome, RAW_FIELDS | {"one_proposal_reward", "assessment_evaluator_called"}, "v1 selected outcome")
    _exact(outcome["assessment_evaluator_called"], True, "v1 evaluator called")
    _exact(outcome["cost"], 0.06, "v1 search cost")
    raw = {name: copy.deepcopy(outcome[name]) for name in RAW_FIELDS}
    raw.update(cost=0.01, reward=outcome["one_proposal_reward"])
    return raw


def _population(slots, keys, selectors):
    return {
        "slot_count": len(slots), "episode_count": len(selectors), "key_count": len(keys),
        "reuse_key_count": sum(bool(k["reuse_sources"]) for k in keys),
        "pending_job_count": sum(not k["reuse_sources"] for k in keys),
        "positive_slot_orientations": sum(s["orientation"] == 1 for s in slots),
        "negative_slot_orientations": sum(s["orientation"] == -1 for s in slots),
        "null_slot_orientations": sum(s["orientation"] is None for s in slots),
        "within_episode_duplicates": sum(s["canonical_duplicate"] for s in slots),
        "keys_by_task": [sum(k["task_id"] == task for k in keys) for task in TASK_IDS],
    }


def _tables(bank, assessment, tasks):
    """Generic bookkeeping also retains invalid slots in adversarial synthetic fixtures."""
    slots, keys, selectors, key_map, slot_map = [], [], [], {}, {}
    for episode in bank["episodes"]:
        task, arm, saved = episode["task_id"], episode["arm"], episode["submission"]
        candidates = []
        for record in saved["records"]:
            eligible_feedback = record["canonical_ast"] is not None and record["feedback"] is not None
            eligible_feedback = eligible_feedback and record["feedback"]["usable"]
            orientation = (-1 if record["feedback"]["mean_ic"] < 0 else 1) if eligible_feedback else None
            expression = None if record["packet"] is None else record["packet"]["expression"]
            key_id = digest([task, record["canonical_ast"], orientation]) if eligible_feedback else None
            slot_id = f"{task}/{arm}/{record['attempt']}"
            slot = {"slot_id": slot_id, "task_id": task, "arm": arm, "attempt": record["attempt"],
                    "expression": expression, "canonical_ast": record["canonical_ast"],
                    "canonical_duplicate": record["canonical_duplicate"], "feedback": record["feedback"],
                    "orientation": orientation, "key_id": key_id,
                    "ast_node_count": None if record["canonical_ast"] is None else _node_count(expression)}
            slots.append(slot)
            slot_map[slot_id] = slot
            if key_id is not None:
                feedback = {name: record["feedback"][name] for name in METRIC_FIELDS}
                bounds = tasks[task]["financial_manifest"]["feedback_bounds_half_open"]
                _require(_metric(feedback, bounds[1] - bounds[0]), "saved usability disagrees with frozen support rule")
                if key_id not in key_map:
                    key = {"key_id": key_id, "task_id": task, "canonical_ast": record["canonical_ast"],
                           "orientation": orientation, "feedback": feedback, "representative_slot_id": slot_id,
                           "representative_expression": expression, "evaluation_expression": expression,
                           "slot_ids": [], "reuse_sources": []}
                    keys.append(key)
                    key_map[key_id] = key
                key_map[key_id]["slot_ids"].append(slot_id)
                _exact(feedback, key_map[key_id]["feedback"], "same-key historical feedback")
                if not record["canonical_duplicate"]:
                    candidates.append(slot)
        original = saved["selection"]
        selectors.append({"task_id": task, "arm": arm,
                          "original": None if original is None else f"{task}/{arm}/{original['attempt']}",
                          "first": f"{task}/{arm}/1",
                          "minimum_ast": min(candidates, key=lambda s: s["ast_node_count"])["slot_id"]
                          if candidates else None})
    for index, row in enumerate(assessment["results"]):
        selector = selectors[index]
        if selector["original"] is None:
            continue
        slot = slot_map[selector["original"]]
        key, source = key_map[slot["key_id"]], copy.deepcopy(row["outcome"])
        _exact(source["expression"], slot["expression"], "v1 selected expression")
        derived = _outcome(_raw_from_v1(source), key, tasks[key["task_id"]], evaluated_expression=source["expression"])
        _arithmetic(source["reward"], derived["utility"], "v1 fixed-cost utility")
        if key["reuse_sources"]:
            previous = key["reuse_sources"][0]["outcome"]
            _exact({k: v for k, v in source.items() if k != "expression"},
                   {k: v for k, v in previous.items() if k != "expression"}, "conflicting cache reuse")
        else:
            key["evaluation_expression"] = source["expression"]
        key["reuse_sources"].append({"assessment_row_index": index, "task_id": row["task_id"], "arm": row["arm"],
                                     "slot_id": slot["slot_id"], "outcome": source})
    jobs = [{"job_number": number, "key_id": key["key_id"], "task_id": key["task_id"],
             "expression": key["representative_expression"]}
            for number, key in enumerate((key for key in keys if not key["reuse_sources"]), start=1)]
    return slots, keys, selectors, jobs


def _verify_saved_inputs(captured, root):
    for name, raw in captured.items():
        _require(_sha(raw) == INPUT_HASHES[name], f"immutable v1 {name} file identity mismatch")
    with tempfile.TemporaryDirectory(prefix="astra-pool-inputs-") as temporary:
        paths = {name: Path(temporary) / (name + ".json") for name in captured}
        for name, raw in captured.items():
            paths[name].write_bytes(raw)
        verified = replay_study(paths["contract"], paths["submissions"], source_root=root,
                                assessment_path=paths["assessment"])
    return {name: _read(raw) for name, raw in captured.items()}, verified


def _assemble(input_paths, captured, task_raw, *, root, output_dir, verify_environment=True):
    values, verified = _verify_saved_inputs(captured, root)
    original, bank, assessment = (values[name] for name in ("contract", "submissions", "assessment"))
    _exact(original["runtime_versions"], RUNTIME, "registered runtime")
    if verify_environment:
        _exact(_versions(), RUNTIME, "current runtime")
        _data_bytes(_path(root, original["data"]["path"]), original["data"]["sha256"])
    tasks = {}
    for task in TASK_IDS:
        initial = next(e["submission"]["initial_evidence"] for e in bank["episodes"] if e["task_id"] == task)
        tasks[task] = _task_record(task_raw[task], task, original["task_manifest_sha256"][task], initial)
    slots, keys, selectors, jobs = _tables(bank, assessment, tasks)
    population = _population(slots, keys, selectors)
    _exact(population, POPULATION, "registered diagnosis population")
    plan_path = _path(root, PLAN_PATH)
    implementation = {name: _sha(_path(root, name).read_bytes()) for name in IMPLEMENTATION_PATHS}
    _require(_sha(Path(__file__).read_bytes()) == implementation[IMPLEMENTATION_PATHS[0]],
             "loaded diagnosis source differs from inspected source")
    _require(_sha(Path(astra_replay.__file__).read_bytes()) == implementation[IMPLEMENTATION_PATHS[1]],
             "loaded replay source differs from inspected source")
    body = {
        "schema": "astra-pool-contract-v1", "study": STUDY, "status": "PREPARED_POST_HOC",
        "execution_directory": _relative(output_dir / "execution", root),
        "inputs": {name: {"path": _relative(input_paths[name], root), "sha256": _sha(raw), "bytes": len(raw)}
                   for name, raw in captured.items()},
        "original_source_sha256": original["source_sha256"], "original_plan": original["plan"],
        "data": original["data"], "runtime_versions": RUNTIME,
        "diagnosis_plan": {"path": PLAN_PATH, "sha256": _sha(plan_path.read_bytes())},
        "implementation_sha256": implementation,
        "task_files": {task: {"path": _relative(output_dir / "tasks" / (task + ".json"), root),
                              "sha256": _sha(task_raw[task]), "bytes": len(task_raw[task])} for task in TASK_IDS},
        "population": population, "rules": RULES, "slots": slots, "keys": keys,
        "selectors": selectors, "pending_jobs": jobs, "original_evidence_verification": verified,
        "new_evaluator_calls": 0, "model_calls": 0, "new_formulas": 0,
    }
    return _sealed(body), tasks, assessment


def prepare_pool_diagnosis(contract_path, submissions_path, assessment_path, task_manifest_dir, *,
                           source_root, output_dir=None):
    """Hash/replay saved evidence and mirror ten task files; never construct a task."""
    root = Path(source_root).resolve()
    output_dir = root / PUBLIC_DIRECTORY if output_dir is None else Path(output_dir)
    _relative(output_dir, root)
    _require(not output_dir.exists(), "preparation output already exists")
    input_paths = dict(zip(("contract", "submissions", "assessment"),
                          map(Path, (contract_path, submissions_path, assessment_path)), strict=True))
    captured = {name: path.read_bytes() for name, path in input_paths.items()}
    task_raw = {task: (Path(task_manifest_dir) / (task + ".json")).read_bytes() for task in TASK_IDS}
    contract, _, _ = _assemble(input_paths, captured, task_raw, root=root, output_dir=output_dir)
    output_dir.mkdir(parents=True, exist_ok=False)
    try:
        (output_dir / "tasks").mkdir()
        for task, raw in task_raw.items():
            _write_bytes(output_dir / "tasks" / (task + ".json"), raw)
        _write(output_dir / "contract.json", contract)
    except BaseException as error:
        _write(output_dir / "INCOMPLETE.json", _sealed({"stage": "prepare", "error_type": type(error).__name__}))
        raise
    return contract


def _verified_contract(contract_path, root, *, verify_environment=True):
    path = Path(contract_path)
    raw = path.read_bytes()
    contract = _read(raw)
    _keys(contract, {"schema", "study", "status", "inputs", "original_source_sha256", "original_plan", "data",
                     "runtime_versions", "diagnosis_plan", "implementation_sha256", "task_files", "population",
                     "rules", "slots", "keys", "selectors", "pending_jobs", "original_evidence_verification",
                     "new_evaluator_calls", "model_calls", "new_formulas", "execution_directory", "body_sha256"},
          "diagnosis contract")
    _keys(contract["inputs"], set(INPUT_HASHES), "bound inputs")
    _keys(contract["task_files"], set(TASK_IDS), "bound tasks")
    paths = {}
    captured = {}
    for name, identity in contract["inputs"].items():
        _keys(identity, {"path", "sha256", "bytes"}, "input identity")
        paths[name] = _path(root, identity["path"])
        captured[name] = paths[name].read_bytes()
    task_raw = {task: _path(root, identity["path"]).read_bytes()
                for task, identity in contract["task_files"].items()}
    expected, tasks, assessment = _assemble(paths, captured, task_raw, root=root, output_dir=path.parent,
                                            verify_environment=verify_environment)
    _exact(contract, expected, "diagnosis contract")
    bound = {contract["inputs"][name]["path"]: value for name, value in captured.items()}
    bound.update({contract["task_files"][task]["path"]: value for task, value in task_raw.items()})
    bound[_relative(path, root)] = raw
    identities = {**contract["original_source_sha256"], **contract["implementation_sha256"],
                  contract["original_plan"]["path"]: contract["original_plan"]["sha256"],
                  contract["diagnosis_plan"]["path"]: contract["diagnosis_plan"]["sha256"]}
    for relative, expected_hash in identities.items():
        value = _path(root, relative).read_bytes()
        _require(_sha(value) == expected_hash, "published source/plan identity changed")
        bound[relative] = value
    return contract, tasks, assessment, bound


def publication_files(contract_path, *, source_root):
    """Return the exact public path/hash map required by the independent root receipt."""
    _, _, _, bound = _verified_contract(contract_path, Path(source_root).resolve())
    return {relative: _sha(raw) for relative, raw in bound.items()}


def verify_local_commit(root, commit, bound):
    """Read local Git blobs only; the separately supplied receipt attests public retrieval."""
    _require(type(commit) is str and re.fullmatch(r"[0-9a-f]{40}", commit), "full lowercase commit required")
    for relative, raw in bound.items():
        result = subprocess.run(["git", "-c", f"safe.directory={Path(root).resolve().as_posix()}",
                                 "show", f"{commit}:{relative}"], cwd=root, capture_output=True, check=True,
                                timeout=30, shell=False)
        _require(result.stdout == raw, "local committed blob differs from bound bytes")
    return {"commit": commit, "local_committed_bytes_verified": True}


def _receipt(raw, commit, bound):
    receipt = _read(raw)
    _keys(receipt, {"schema", "study", "commit", "verified_utc", "verification_method",
                    "public_repository_url", "paths_sha256", "body_sha256"}, "publication receipt")
    _exact({name: receipt[name] for name in ("schema", "study", "commit", "verification_method")},
           {"schema": "astra-pool-publication-receipt-v1", "study": STUDY, "commit": commit,
            "verification_method": "root-verified unauthenticated public retrieval"}, "publication receipt identity")
    _require(type(commit) is str and re.fullmatch(r"[0-9a-f]{40}", commit), "invalid receipt commit")
    _utc(receipt["verified_utc"])
    _require(type(receipt["public_repository_url"]) is str
             and re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", receipt["public_repository_url"]),
             "invalid public repository URL")
    _exact(receipt["paths_sha256"], {name: _sha(value) for name, value in bound.items()}, "publication path hashes")
    return receipt


def _assert_bound(root, bound, contract):
    for relative, raw in bound.items():
        _require(_path(root, relative).read_bytes() == raw, "bound input/source bytes changed")
    _exact(_versions(), contract["runtime_versions"], "execution runtime")
    return _data_bytes(_path(root, contract["data"]["path"]), contract["data"]["sha256"])


def _load_tasks(data_path):
    # These imports are execute-only. Saved replay imports neither module.
    from .financial_policy import load_pinned_panel
    from .financial_tasks import make_task

    panel = load_pinned_panel(data_path)
    return {task: make_task(panel, int(task[:4]), int(task[-1])) for task in TASK_IDS}


def _task_matches(task, original):
    _exact(task.public_manifest, original["financial_manifest"], "reconstructed financial task")
    _exact(task.observation(), original["initial_observation"], "reconstructed initial observation")


def _job_name(job):
    return f"{job['job_number']:03d}-{job['key_id']}"


def _completed_prefix(directory, contract, contract_hash, tasks, receipt):
    jobs_dir = directory / "jobs"
    expected_names = {_job_name(job) for job in contract["pending_jobs"]}
    if not jobs_dir.exists():
        return []
    _require(not jobs_dir.is_symlink(), "job directory cannot be a symlink")
    _require(all(path.name in expected_names and path.is_dir() and not path.is_symlink()
                 for path in jobs_dir.iterdir()), "unexplained job evidence")
    completed, missing, previous, previous_time = [], False, contract_hash, _utc(receipt["verified_utc"])
    key_map = {key["key_id"]: key for key in contract["keys"]}
    for job in contract["pending_jobs"]:
        path = jobs_dir / _job_name(job)
        if not path.exists():
            missing = True
            continue
        _require(not missing, "job prefix contains a gap")
        _require({p.name for p in path.iterdir()} == {"STARTED.json", "COMPLETED.json"}
                 and all(p.is_file() and not p.is_symlink() for p in path.iterdir()),
                 "ambiguous, failed or unexplained job evidence")
        started_raw, completed_raw = (path / "STARTED.json").read_bytes(), (path / "COMPLETED.json").read_bytes()
        started, result = _read(started_raw), _read(completed_raw)
        _keys(started, {"study", "status", "contract_sha256", "job", "started_utc", "prior_record_sha256",
                        "body_sha256"}, "STARTED")
        _exact({k: started[k] for k in ("study", "status", "contract_sha256", "job", "prior_record_sha256")},
               {"study": STUDY, "status": "STARTED", "contract_sha256": contract_hash,
                "job": job, "prior_record_sha256": previous}, "started job identity")
        _require(_utc(started["started_utc"]) >= _utc(receipt["verified_utc"]), "job predates public verification")
        _require(_utc(started["started_utc"]) >= previous_time, "job predates prior completion")
        _keys(result, {"study", "status", "contract_sha256", "job", "started_sha256", "completed_utc",
                       "raw_outcome", "diagnosis", "body_sha256"}, "COMPLETED")
        _exact({k: result[k] for k in ("study", "status", "contract_sha256", "job", "started_sha256")},
               {"study": STUDY, "status": "COMPLETED", "contract_sha256": contract_hash,
                "job": job, "started_sha256": _sha(started_raw)}, "completed job identity")
        _require(_utc(result["completed_utc"]) >= _utc(started["started_utc"]), "completion predates start")
        diagnosis = _outcome(result["raw_outcome"], key_map[job["key_id"]], tasks[job["task_id"]])
        _arithmetic(result["diagnosis"], diagnosis, "saved diagnosis")
        completed.append(result)
        previous = _sha(completed_raw)
        previous_time = _utc(result["completed_utc"])
    return completed


def _null_outcome():
    return {"status": "known_invalid_or_unusable", "valid": False, "oriented_future_ic": None,
            "utility": -1.06, "cost": 0.06}


def _aggregate(outcomes):
    count = len(outcomes)
    valid = [row for row in outcomes if row["valid"]]
    p = len(valid) / count
    q = math.fsum(row["oriented_future_ic"] for row in valid) / count
    mean = math.fsum(row["utility"] for row in outcomes) / count
    _arithmetic(mean, -1.06 + p + q, "validity decomposition")
    return {"denominator": count, "valid_count": len(valid), "invalid_count": count - len(valid),
            "mean_utility": mean, "validity_fraction_p": p, "predictive_contribution_q": q,
            "conditional_valid_count": len(valid),
            "conditional_valid_mean_ic": math.fsum(row["oriented_future_ic"] for row in valid) / len(valid)
            if valid else None}


def _arm_summaries(episodes):
    result = {}
    for arm in ARMS:
        rows = [row for row in episodes if row["arm"] == arm]
        result[arm] = {"selectors": {name: _aggregate([row["selectors"][name]["diagnosis"] for row in rows])
                                     for name in ("original", "first", "minimum_ast", "oracle")},
                       "mean_selection_gap_R": math.fsum(row["selection_gap_R"] for row in rows) / len(rows),
                       "first_minus_original": math.fsum(row["first_minus_original"] for row in rows) / len(rows),
                       "minimum_ast_minus_original": math.fsum(row["minimum_ast_minus_original"] for row in rows)
                       / len(rows)}
    return result


def _contrasts(arms):
    result = {}
    for name, left, right in CONTRASTS:
        selectors = {}
        for selector in ("original", "first", "minimum_ast", "oracle"):
            a, b = arms[left]["selectors"][selector], arms[right]["selectors"][selector]
            difference = a["mean_utility"] - b["mean_utility"]
            dp = a["validity_fraction_p"] - b["validity_fraction_p"]
            dq = a["predictive_contribution_q"] - b["predictive_contribution_q"]
            _arithmetic(difference, dp + dq, "contrast validity decomposition")
            selectors[selector] = {"utility_difference": difference, "validity_contribution": dp,
                                   "predictive_contribution": dq}
        ds = selectors["original"]["utility_difference"]
        do = selectors["oracle"]["utility_difference"]
        dr = arms[left]["mean_selection_gap_R"] - arms[right]["mean_selection_gap_R"]
        _arithmetic(ds, do - dr, "Delta S = Delta O - Delta R")
        result[name] = {"selectors": selectors, "delta_S": ds, "delta_O": do, "delta_R": dr,
                        "decomposition_residual": ds - (do - dr)}
    return result


def _analysis(contract, tasks, assessment, completed):
    _require(len(completed) == len(contract["pending_jobs"]), "cannot aggregate a partial candidate bank")
    jobs = {row["job"]["key_id"]: row for row in completed}
    key_outcomes, key_records = {}, []
    for key in contract["keys"]:
        if key["reuse_sources"]:
            raw = _raw_from_v1(key["reuse_sources"][0]["outcome"])
            provenance = {"kind": "reused_v1_selected", "source_outcomes": key["reuse_sources"],
                          "job_number": None, "completed_record_body_sha256": None,
                          "raw_fields_reconstructed_from_v1": True}
        else:
            row = jobs[key["key_id"]]
            raw = row["raw_outcome"]
            provenance = {"kind": "new_diagnosis_evaluation", "source_outcomes": [],
                          "job_number": row["job"]["job_number"], "completed_record_body_sha256": row["body_sha256"],
                          "raw_fields_reconstructed_from_v1": False}
        diagnosis = _outcome(raw, key, tasks[key["task_id"]])
        key_outcomes[key["key_id"]] = diagnosis
        key_records.append({"key": key, "raw_evaluator_outcome": raw, "provenance": provenance, "diagnosis": diagnosis})
    slots = [{**slot, "diagnosis": _null_outcome() if slot["key_id"] is None else key_outcomes[slot["key_id"]]}
             for slot in contract["slots"]]
    slot_map = {row["slot_id"]: row for row in slots}
    episodes = []
    for frozen in contract["selectors"]:
        pool = [row for row in slots if row["task_id"] == frozen["task_id"] and row["arm"] == frozen["arm"]]
        _require(len(pool) == 6, "six-slot denominator changed")
        oracle = max(pool, key=lambda row: row["diagnosis"]["utility"])
        choices = {name: frozen[name] for name in ("original", "first", "minimum_ast")}
        choices["oracle"] = oracle["slot_id"]
        selectors = {}
        for name, slot_id in choices.items():
            slot = None if slot_id is None else slot_map[slot_id]
            selectors[name] = {"slot_id": slot_id, "attempt": None if slot is None else slot["attempt"],
                               "diagnosis": _null_outcome() if slot is None else slot["diagnosis"]}
        s, o = (selectors[name]["diagnosis"]["utility"] for name in ("original", "oracle"))
        gap = o - s
        _require(gap >= -1e-12, "negative oracle selection gap")
        episodes.append({"task_id": frozen["task_id"], "arm": frozen["arm"], "selectors": selectors,
                         "S": s, "O": o, "selection_gap_R": gap,
                         "first_minus_original": selectors["first"]["diagnosis"]["utility"] - s,
                         "minimum_ast_minus_original": selectors["minimum_ast"]["diagnosis"]["utility"] - s})
    arms = _arm_summaries(episodes)
    paired = []
    for task in TASK_IDS:
        summaries = _arm_summaries([row for row in episodes if row["task_id"] == task])
        paired.append({"task_id": task, "arm_summaries": summaries, "contrasts": _contrasts(summaries)})
    years = []
    for year in range(2020, 2025):
        summaries = _arm_summaries([row for row in episodes if row["task_id"].startswith(str(year))])
        years.append({"year": year, "arm_summaries": summaries, "contrasts": _contrasts(summaries)})
    contrasts = _contrasts(arms)
    # Original selectors must reproduce v1, including every invalid denominator.
    for arm in ARMS:
        original, current = assessment["arm_summaries"][arm], arms[arm]["selectors"]["original"]
        for destination, source in (("denominator", "task_count"), ("valid_count", "valid_assessment_count"),
                                    ("mean_utility", "mean_utility"), ("validity_fraction_p", "validity_fraction_p"),
                                    ("predictive_contribution_q", "predictive_contribution_q"),
                                    ("conditional_valid_mean_ic", "conditional_valid_mean_ic")):
            _arithmetic(current[destination], original[source], "original selector reproduces v1")
    for actual, original in zip(paired, assessment["paired"], strict=True):
        _exact(actual["task_id"], original["task_id"], "paired task order")
        for name, _, _ in CONTRASTS:
            _arithmetic(actual["contrasts"][name]["delta_S"], original[name], "v1 task contrast")
    for actual, original in zip(years, assessment["year_averages"], strict=True):
        _exact(actual["year"], original["year"], "year order")
        for name, _, _ in CONTRASTS:
            _arithmetic(actual["contrasts"][name]["delta_S"], original[name], "v1 year contrast")
    for name, _, _ in CONTRASTS:
        _arithmetic(contrasts[name]["delta_S"], assessment["contrasts"][name]["mean_utility_difference"],
                    "v1 overall contrast")
    full = [row for row in episodes if row["arm"] == ARMS[0]]
    original_valid_guarantee = all(row["selectors"]["original"]["diagnosis"]["valid"]
                                   and row["selectors"]["original"]["diagnosis"]["oriented_future_ic"] > -1
                                   for row in episodes)
    mean_o = math.fsum(row["O"] for row in full) / len(full)
    mean_uncosted = math.fsum(row["O"] + 0.06 for row in full) / len(full)
    return {
        "slot_results": slots, "key_results": key_records, "selector_rows": episodes,
        "paired": paired, "year_averages": years, "arm_summaries": arms, "contrasts": contrasts,
        "slot_validity": {"all": _aggregate([row["diagnosis"] for row in slots]),
                          "by_arm": {arm: _aggregate([row["diagnosis"] for row in slots if row["arm"] == arm])
                                     for arm in ARMS}},
        "unique_key_validity": _aggregate(list(key_outcomes.values())) if key_outcomes else None,
        "allocation": {"arm": ARMS[0], "mean_oracle_utility": mean_o,
                       "mean_oracle_plus_cost": mean_uncosted,
                       "all_original_selected_valid_and_ic_above_minus_one": original_valid_guarantee,
                       "oracle_plus_cost_interpretation": "valid_oriented_IC" if original_valid_guarantee
                       else "invalidity_penalized_score",
                       "positive_mean_IC_selection_only_no_go": mean_uncosted <= 0 if original_valid_guarantee else None,
                       "positive_mean_fixed_cost_utility_selection_only_no_go": mean_o <= 0,
                       "automatic_next_experiment_authorized": False},
    }


def _request(request_raw, contract_hash, bound):
    request = _read(request_raw)
    _keys(request, {"study", "contract_sha256", "publication_receipt", "publication_receipt_sha256",
                    "local_publication", "body_sha256"}, "execution request")
    _exact(request["study"], STUDY, "execution study")
    _exact(request["contract_sha256"], contract_hash, "execution contract")
    receipt = request["publication_receipt"]
    # The exact received receipt bytes are retained in a separate file and bound below.
    _receipt((canonical_json(receipt) + "\n").encode(), receipt["commit"], bound)
    _exact(request["local_publication"], {"commit": receipt["commit"], "local_committed_bytes_verified": True},
           "recorded local commit check")
    return request


def _execution_tree(directory):
    allowed = {"jobs", "request.json", "publication-receipt.json", "COMPLETE.json", "INCOMPLETE.json",
               ".execution-lock"}
    _require(directory.is_dir() and not directory.is_symlink(), "invalid execution directory")
    _require(all(path.name in allowed and not path.is_symlink() for path in directory.iterdir()),
             "unexplained execution evidence")
    _require(not (directory / "INCOMPLETE.json").exists(), "diagnosis is permanently INCOMPLETE")


def _complete_report(contract, contract_hash, request, tasks, assessment, completed):
    analysis = _analysis(contract, tasks, assessment, completed)
    return _sealed({
        "schema": "astra-pool-diagnosis-result-v1", "study": STUDY, "status": "COMPLETE_POST_HOC",
        "contract_sha256": contract_hash, "publication": request["publication_receipt"],
        "execution_request_body_sha256": request["body_sha256"], "inputs": contract["inputs"],
        "original_source_sha256": contract["original_source_sha256"], "original_plan": contract["original_plan"],
        "diagnosis_plan": contract["diagnosis_plan"], "implementation_sha256": contract["implementation_sha256"],
        "data_identity": contract["data"], "runtime_versions": contract["runtime_versions"],
        "population": contract["population"], "rules": contract["rules"],
        "call_accounting": {"new_evaluator_calls_started": len(completed), "new_evaluator_calls_completed": len(completed),
                            "reused_key_count": sum(bool(k["reuse_sources"]) for k in contract["keys"]),
                            "total_key_count": len(contract["keys"]), "total_slot_count": len(contract["slots"]),
                            "model_calls": 0, "new_formulas": 0, "automatic_retries": 0},
        **analysis,
        "limits": ["Post-hoc diagnosis of one realized trajectory per arm and reused development period.",
                   "Oracle is unattainable hindsight headroom; Delta O is not a causal generation contribution.",
                   "AST keys do not establish distinct economic signals; all original slots retain their cost.",
                   "Publication receipt records root verification; local Git checks alone do not establish public access.",
                   "Saved replay checks evidence and arithmetic, not new market scoring or package binary identity.",
                   "No profitability, untouched holdout, factor originality, general causal effect or Astra weight-training claim."]})


def _validate_report(saved, expected):
    """Tolerance is restricted to computed results, never retained evidence or identities."""
    _keys(saved, set(expected), "complete report")
    computed = {"selector_rows", "paired", "year_averages", "arm_summaries", "contrasts", "slot_validity",
                "unique_key_validity", "allocation"}
    for name in set(expected) - computed - {"slot_results", "key_results", "body_sha256"}:
        _exact(saved[name], expected[name], "retained report " + name)
    for name in ("slot_results", "key_results"):
        _require(type(saved[name]) is list and len(saved[name]) == len(expected[name]), "retained row count differs")
        for actual, target in zip(saved[name], expected[name], strict=True):
            _keys(actual, set(target), name)
            _exact({k: v for k, v in actual.items() if k != "diagnosis"},
                   {k: v for k, v in target.items() if k != "diagnosis"}, "retained " + name)
            _arithmetic(actual["diagnosis"], target["diagnosis"], "derived slot/key diagnosis")
    for name in computed:
        _arithmetic(saved[name], expected[name], "computed report " + name)


def _failure(directory, error, *, stage, job=None, raw_available=False, raw=None):
    body = {"study": STUDY, "status": "INCOMPLETE", "stage": stage, "error_type": type(error).__name__,
            "job": job, "created_utc": _now(), "automatic_retries": 0, "raw_return_available": raw_available}
    if raw_available:
        try:
            canonical_json(raw)
            body["raw_return"] = raw
            body["raw_return_representation"] = "json"
        except (TypeError, ValueError, OverflowError, RecursionError):
            body["raw_return"] = repr(raw)
            body["raw_return_representation"] = "python_repr_for_invalid_non_json_return"
    if not (directory / "INCOMPLETE.json").exists():
        _write(directory / "INCOMPLETE.json", _sealed(body))


def execute_pool_diagnosis(contract_path, publication_receipt_path, *, source_root, execution_dir,
                           published_commit, max_jobs=108, task_loader=None, publication_verifier=verify_local_commit):
    """Run at most the next max_jobs; an ambiguous/failed key is never evaluated again."""
    _require(type(max_jobs) is int and 1 <= max_jobs <= 108, "max_jobs must be an integer between 1 and 108")
    root, directory = Path(source_root).resolve(), Path(execution_dir).resolve()
    _relative(directory, root)
    contract_path = Path(contract_path)
    # Read-only precheck binds the only allowed state directory, without launching or loading anything.
    initial_contract = _read(contract_path.read_bytes())
    _require(directory == _path(root, initial_contract.get("execution_directory")),
             "execution directory differs from frozen contract")
    _require(not (directory / "COMPLETE.json").exists(), "completed diagnosis allows replay only")
    directory.mkdir(parents=True, exist_ok=True)
    _require(directory.is_dir() and not directory.is_symlink(), "invalid execution directory")
    lock = directory / ".execution-lock"
    lock.mkdir(exist_ok=False)
    job = None
    raw, raw_available = None, False
    completed = []
    try:
        _execution_tree(directory)
        contract, tasks, assessment, bound = _verified_contract(contract_path, root)
        contract_hash = _sha(bound[_relative(contract_path, root)])
        receipt_raw = Path(publication_receipt_path).read_bytes()
        receipt = _receipt(receipt_raw, published_commit, bound)
        _require(_utc(receipt["verified_utc"]) <= datetime.now(UTC), "publication receipt is from the future")
        local = publication_verifier(root, published_commit, bound)
        _exact(local, {"commit": published_commit, "local_committed_bytes_verified": True}, "local publication gate")
        expected_request = _sealed({"study": STUDY, "contract_sha256": contract_hash,
                                    "publication_receipt": receipt, "publication_receipt_sha256": _sha(receipt_raw),
                                    "local_publication": local})
        request_path = directory / "request.json"
        if request_path.exists():
            request = _request(request_path.read_bytes(), contract_hash, bound)
            _exact(request, expected_request, "continuation publication request")
            _require((directory / "publication-receipt.json").read_bytes() == receipt_raw, "receipt bytes changed")
        else:
            _require({p.name for p in directory.iterdir()} == {".execution-lock"}, "unexplained pre-request state")
            _write_bytes(directory / "publication-receipt.json", receipt_raw)
            _write(request_path, expected_request)
            request = expected_request
        completed = _completed_prefix(directory, contract, contract_hash, tasks, receipt)
        jobs = contract["pending_jobs"][len(completed):len(completed) + max_jobs]
        if not (directory / "jobs").exists():
            (directory / "jobs").mkdir()
        key_map = {key["key_id"]: key for key in contract["keys"]}
        loader = _load_tasks if task_loader is None else task_loader
        loaded_tasks = None
        checked_tasks = set()
        with tempfile.TemporaryDirectory(prefix="astra-pool-data-") as temporary:
            for job in jobs:
                raw, raw_available = None, False
                data_raw = _assert_bound(root, bound, contract)
                if loaded_tasks is None:
                    snapshot = Path(temporary) / Path(contract["data"]["path"]).name
                    snapshot.write_bytes(data_raw)
                    loaded_tasks = loader(snapshot)
                    _keys(loaded_tasks, set(TASK_IDS), "loaded tasks")
                if job["task_id"] not in checked_tasks:
                    _task_matches(loaded_tasks[job["task_id"]], tasks[job["task_id"]])
                    checked_tasks.add(job["task_id"])
                path = directory / "jobs" / _job_name(job)
                path.mkdir(exist_ok=False)
                previous = contract_hash if not completed else _sha(
                    (directory / "jobs" / _job_name(completed[-1]["job"]) / "COMPLETED.json").read_bytes())
                stamp = _now()
                prior_time = receipt["verified_utc"] if not completed else completed[-1]["completed_utc"]
                _require(_utc(stamp) >= _utc(prior_time), "system timestamp predates prior durable record")
                started = _sealed({"study": STUDY, "status": "STARTED", "contract_sha256": contract_hash,
                                   "job": job, "started_utc": stamp, "prior_record_sha256": previous})
                _write(path / "STARTED.json", started)
                raw = loaded_tasks[job["task_id"]].evaluate(job["expression"])
                raw_available = True
                derived = _outcome(raw, key_map[job["key_id"]], tasks[job["task_id"]])
                finished = _now()
                _require(_utc(finished) >= _utc(stamp), "system timestamp predates start")
                result = _sealed({"study": STUDY, "status": "COMPLETED", "contract_sha256": contract_hash,
                                  "job": job, "started_sha256": _sha((path / "STARTED.json").read_bytes()),
                                  "completed_utc": finished, "raw_outcome": raw, "diagnosis": derived})
                _write(path / "COMPLETED.json", result)
                completed.append(result)
        # Validate the complete saved prefix again; disk records, not only in-memory results, are authoritative.
        completed = _completed_prefix(directory, contract, contract_hash, tasks, receipt)
        _assert_bound(root, bound, contract)
        if len(completed) != len(contract["pending_jobs"]):
            return {"study": STUDY, "status": "CLEAN_COMPLETED_PREFIX", "completed_new_jobs": len(completed),
                    "remaining_new_jobs": len(contract["pending_jobs"]) - len(completed), "automatic_retries": 0}
        report = _complete_report(contract, contract_hash, request, tasks, assessment, completed)
        _write(directory / "COMPLETE.json", report)
        return report
    except BaseException as error:
        # A fully written, valid completion is enough to establish a clean prefix after an interruption.
        # No evaluator is called during this recovery check. Any ambiguity permanently blocks scoring.
        clean_interruption = False
        if isinstance(error, (KeyboardInterrupt, SystemExit)) and job is not None:
            try:
                recovered = _completed_prefix(directory, contract, contract_hash, tasks, receipt)
                clean_interruption = bool(recovered) and recovered[-1]["job"] == job
            except BaseException:  # noqa: BLE001 - recovery cannot replace or conceal the original interruption.
                clean_interruption = False  # Failed recovery blocks scoring and preserves the original interruption.
        if not clean_interruption:
            _failure(directory, error, stage="execute", job=job, raw_available=raw_available, raw=raw)
        raise
    finally:
        lock.rmdir()


def replay_pool_diagnosis(contract_path, execution_dir, *, source_root, report_path=None):
    """Validate only public saved evidence/arithmetic; never open the raw ZIP or construct tasks."""
    root, directory = Path(source_root).resolve(), Path(execution_dir).resolve()
    contract, tasks, assessment, bound = _verified_contract(contract_path, root, verify_environment=False)
    _require(directory == _path(root, contract["execution_directory"]), "replay directory differs from contract")
    _execution_tree(directory)
    _require(not (directory / ".execution-lock").exists(), "execution lock remains; replay cannot attest completion")
    contract_hash = _sha(bound[_relative(contract_path, root)])
    request = _request((directory / "request.json").read_bytes(), contract_hash, bound)
    receipt_raw = (directory / "publication-receipt.json").read_bytes()
    _require(_sha(receipt_raw) == request["publication_receipt_sha256"], "saved receipt file changed")
    receipt = _receipt(receipt_raw, request["publication_receipt"]["commit"], bound)
    _exact(receipt, request["publication_receipt"], "saved receipt")
    completed = _completed_prefix(directory, contract, contract_hash, tasks, receipt)
    _require(len(completed) == len(contract["pending_jobs"]), "diagnosis is incomplete")
    expected = _complete_report(contract, contract_hash, request, tasks, assessment, completed)
    saved_raw = (directory / "COMPLETE.json").read_bytes()
    saved = _read(saved_raw)
    _validate_report(saved, expected)
    if report_path is not None:
        _require(Path(report_path).read_bytes() == saved_raw, "public complete report bytes differ")
    return _sealed({"schema": "astra-pool-replay-v1", "study": STUDY, "status": "SAVED_ARITHMETIC_VERIFIED",
                    "contract_sha256": contract_hash, "report_sha256": _sha(saved_raw),
                    "population": contract["population"], "completed_new_jobs": len(completed),
                    "model_calls": 0, "new_financial_scores": 0, "raw_market_data_reads": 0,
                    "installed_runtime_revalidated": False})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    prepare = subcommands.add_parser("prepare")
    prepare.add_argument("--v1-contract", type=Path, required=True)
    prepare.add_argument("--submissions", type=Path, required=True)
    prepare.add_argument("--assessment", type=Path, required=True)
    prepare.add_argument("--task-manifest-dir", type=Path, required=True)
    prepare.add_argument("--output-dir", type=Path)
    execute = subcommands.add_parser("execute")
    execute.add_argument("--contract", type=Path, required=True)
    execute.add_argument("--publication-receipt", type=Path, required=True)
    execute.add_argument("--published-commit", required=True)
    execute.add_argument("--execution-dir", type=Path, required=True)
    execute.add_argument("--max-jobs", type=int, default=108)
    replay = subcommands.add_parser("replay")
    replay.add_argument("--contract", type=Path, required=True)
    replay.add_argument("--execution-dir", type=Path, required=True)
    replay.add_argument("--report", type=Path)
    replay.add_argument("--output", type=Path, required=True)
    for command in (prepare, execute, replay):
        command.add_argument("--source-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = prepare_pool_diagnosis(args.v1_contract, args.submissions, args.assessment, args.task_manifest_dir,
                                        source_root=args.source_root, output_dir=args.output_dir)
    elif args.command == "execute":
        result = execute_pool_diagnosis(args.contract, args.publication_receipt, source_root=args.source_root,
                                        execution_dir=args.execution_dir, published_commit=args.published_commit,
                                        max_jobs=args.max_jobs)
    else:
        protected = [args.contract, args.execution_dir, args.source_root / PLAN_PATH]
        protected.extend(args.source_root / name for name in IMPLEMENTATION_PATHS)
        if args.report is not None:
            protected.append(args.report)
        output = args.output.resolve()
        if output.exists() or any(output == path.resolve() or output.is_relative_to(path.resolve())
                                  for path in protected):
            parser.error("output exists or collides with protected evidence")
        result = replay_pool_diagnosis(args.contract, args.execution_dir, source_root=args.source_root,
                                       report_path=args.report)
        _write(args.output, result)
    print(canonical_json({name: result[name] for name in ("study", "status")}), flush=True)


if __name__ == "__main__":
    main()
