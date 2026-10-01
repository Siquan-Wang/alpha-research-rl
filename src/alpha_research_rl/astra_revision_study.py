"""Durable matched-prefix study with separate historical and held-output gates.

Only prepare/collect/assess execution paths may inspect the pinned local runtime
or raw archive. Saved reconstruction receives captured public evidence only.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import math
import re
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from . import astra_pool_diagnosis as pool
from . import astra_replay
from . import astra_revision_core as core
from .agentic_research import canonical_json, digest

PUBLIC_DIRECTORY = "artifacts/astra-matched-prefix-v1"
TRANSPORT_DIRECTORY = ".local/astra-matched-prefix-v1"
SUBMISSIONS_PATH = "results/astra_matched_prefix_v1_submissions.json"
RESULT_PATH = "results/astra_matched_prefix_v1.json"
PLAN_PATH = "docs/astra-matched-prefix-plan-v1.md"
INPUT_PATHS = {
    "v1_contract": "artifacts/astra-agent-v1/contract.json",
    "v1_submissions": "results/astra_agent_v1_submissions.json",
    "v1_assessment": "results/astra_agent_v1_assessment.json",
    "pool_contract": "artifacts/astra-pool-diagnosis-v1/contract.json",
    "pool_result": "results/astra_pool_diagnosis_v1.json",
}
INPUT_HASHES = {
    "v1_contract": "63848687bb44ea7d835b0a2d6ebe88d95dd7ed7257c8ca27dd216a6c37d8b17a",
    "v1_submissions": "89b9cd42d4d248393c2c3c2b9f29714fb9ba023b511d9b3741196d99a321def7",
    "v1_assessment": "30aafbc089f6017c99c6d23c14fca077ffcdf59e9cbf0599d28560c4446ff2a0",
    "pool_contract": "612b426cd843fa44956ccdbb3cc12692c8cada53590f781eef2bf3d00af81979",
    "pool_result": "ed50f86cbe876585b9de81c0960ca0a0a9d9c588345e82001ef5706141f0df2c",
}
AUTHOR_PATHS = (
    "src/alpha_research_rl/astra_revision_core.py", "src/alpha_research_rl/astra_revision_study.py",
    "tests/test_astra_revision_core.py", "tests/test_astra_revision_study.py",
    "docs/reproduce-astra-revision-study.md",
    "scripts/verify_astra_revision_publication.py", "tests/test_astra_revision_publication_script.py",
)
MODEL_SETTINGS = {"model": "gpt-6-astra", "reasoning_effort": "ultra", "service_tier": "default",
                  "sandbox": "read-only", "ephemeral": True, "timeout_seconds": 600,
                  "maximum_concurrency": 2, "infrastructure_retries": 0}
RUNTIME = pool.RUNTIME


def _sealed(value):
    return pool._sealed(value)


def _identity(raw):
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def _cli(identity):
    from .codex_actor import CLI_VERSION_CONTRACT

    pool._keys(identity, {"executable_name", "sha256", "version"}, "CLI identity")
    name = identity["executable_name"]
    pool._require(type(name) is str and name and not any(character in name for character in "/\\:"),
                  "invalid executable basename")
    astra_replay._hash(identity["sha256"], "CLI executable")
    pool._exact(identity["version"], "codex-cli " + CLI_VERSION_CONTRACT, "CLI version")


def _snapshot(captured, root):
    for relative, raw in captured.items():
        path = pool._path(root, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)


def _old_pool_files(root):
    """Only discover/capture file bytes here; do not parse any future outcome."""
    directory = root / Path(INPUT_PATHS["pool_contract"]).parent / "execution"
    pool._execution_tree(directory)
    pool._require({path.name for path in directory.iterdir()} == {
        "jobs", "request.json", "publication-receipt.json", "COMPLETE.json"}, "prior pool is not complete")
    files = [directory / name for name in ("request.json", "publication-receipt.json", "COMPLETE.json")]
    jobs = list((directory / "jobs").iterdir())
    pool._require(len(jobs) == 108 and all(path.is_dir() and not path.is_symlink() for path in jobs),
                  "prior pool needs exactly 108 completed job directories")
    for job in jobs:
        pool._require({path.name for path in job.iterdir()} == {"STARTED.json", "COMPLETED.json"},
                      "prior pool job evidence differs")
        files.extend(job / name for name in ("STARTED.json", "COMPLETED.json"))
    pool._require(all(path.is_file() and not path.is_symlink() for path in files), "invalid prior evidence file")
    return files


def executable_identity():
    """Execution-only version/hash check; no auth inspection or actor inference."""
    from .codex_actor import CLI_VERSION_CONTRACT

    executable = shutil.which("codex")
    if executable is None:
        raise FileNotFoundError("existing Codex executable is unavailable")
    path = Path(executable).resolve()
    result = subprocess.run([str(path), "--version"], capture_output=True, check=True, timeout=30, shell=False)
    version = result.stdout.decode("utf-8").strip()
    pool._exact(version, "codex-cli " + CLI_VERSION_CONTRACT, "CLI version")
    return {"path": str(path), "identity": {"executable_name": path.name,
                                            "sha256": pool._sha(path.read_bytes()), "version": version}}


def _capture_originals(root):
    captured = {relative: pool._path(root, relative).read_bytes() for relative in INPUT_PATHS.values()}
    for name, relative in INPUT_PATHS.items():
        pool._require(pool._sha(captured[relative]) == INPUT_HASHES[name], "registered prior input byte identity differs")
    # These are the only parsed prior study inputs before Gate 2: contract and
    # historical proposals. Prior assessment/pool outcome/ledger bytes stay opaque.
    original = pool._read(captured[INPUT_PATHS["v1_contract"]])
    bank = pool._read(captured[INPUT_PATHS["v1_submissions"]])
    pool._exact(original["runtime_versions"], RUNTIME, "registered scoring runtime")
    dependencies = {*original["source_sha256"], original["plan"]["path"], pool.PLAN_PATH,
                    *pool.IMPLEMENTATION_PATHS, *AUTHOR_PATHS, PLAN_PATH}
    for relative in dependencies:
        captured[relative] = pool._path(root, relative).read_bytes()
    for relative, expected in original["source_sha256"].items():
        pool._require(pool._sha(captured[relative]) == expected, "frozen v1 source changed")
    pool._require(pool._sha(captured[original["plan"]["path"]]) == original["plan"]["sha256"],
                  "frozen v1 plan changed")
    tasks = {}
    task_directory = Path(INPUT_PATHS["pool_contract"]).parent / "tasks"
    for task in core.TASK_IDS:
        relative = (task_directory / (task + ".json")).as_posix()
        captured[relative] = pool._path(root, relative).read_bytes()
        initial = next(item["submission"]["initial_evidence"] for item in bank["episodes"] if item["task_id"] == task)
        tasks[task] = pool._task_record(captured[relative], task, original["task_manifest_sha256"][task], initial)
    for path in _old_pool_files(root):
        captured[pool._relative(path, root)] = path.read_bytes()
    return original, bank, tasks, captured, dependencies


def _historical(bank, tasks):
    cache = {}
    for task, task_record in tasks.items():
        bounds = task_record["financial_manifest"]["feedback_bounds_half_open"]
        for index, probe in enumerate(task_record["initial_observation"]["probe_evidence"], start=1):
            raw = canonical_json({"action": "propose", "expression": probe["expression"], "hypothesis": "", "revision": ""})
            proposal = core.validate_proposal(raw)
            value = core.checked_feedback({**probe["feedback"], "usable": probe["feedback_usable"]}, bounds[1] - bounds[0])
            key = digest([task, proposal["canonical_ast"]])
            cache[key] = {"feedback": value, "sources": [{"kind": "saved_initial_probe", "task_id": task,
                                                         "probe_index": index, "expression": probe["expression"]}]}
    for episode in bank["episodes"]:
        task = episode["task_id"]
        bounds = tasks[task]["financial_manifest"]["feedback_bounds_half_open"]
        for record in episode["submission"]["records"]:
            if record["canonical_ast"] is None:
                continue
            key = digest([task, record["canonical_ast"]])
            value = core.checked_feedback(record["feedback"], bounds[1] - bounds[0])
            source = {"kind": "v1_saved_historical", "task_id": task, "arm": episode["arm"],
                      "attempt": record["attempt"], "expression": record["packet"]["expression"]}
            if key in cache:
                pool._exact(cache[key]["feedback"], value, "repeated historical cache key")
                cache[key]["sources"].append(source)
            else:
                cache[key] = {"feedback": value, "sources": [source]}
    return cache


def _assemble(root, cli_identity, *, verify_environment):
    original, bank, tasks, captured, dependencies = _capture_originals(root)
    for module, relative in ((core, AUTHOR_PATHS[0]), (pool, "src/alpha_research_rl/astra_pool_diagnosis.py"),
                             (astra_replay, "src/alpha_research_rl/astra_replay.py")):
        pool._exact(pool._sha(Path(module.__file__).read_bytes()), pool._sha(captured[relative]), "loaded dependency")
    pool._exact(pool._sha(Path(__file__).read_bytes()), pool._sha(captured[AUTHOR_PATHS[1]]), "loaded study source")
    if verify_environment:
        pool._exact(pool._versions(), RUNTIME, "current scoring runtime")
        pool._data_bytes(pool._path(root, original["data"]["path"]), original["data"]["sha256"])
    with tempfile.TemporaryDirectory(prefix="astra-revision-inputs-") as temporary:
        snapshot_root = Path(temporary)
        _snapshot(captured, snapshot_root)
        verified = astra_replay.replay_study(snapshot_root / INPUT_PATHS["v1_contract"],
                                            snapshot_root / INPUT_PATHS["v1_submissions"], source_root=snapshot_root)
    states = {}
    mirrors = {}
    cheap = []
    for task in core.TASK_IDS:
        episode = next(item for item in bank["episodes"] if item["task_id"] == task
                       and item["arm"] == "withheld_feedback")
        states[task] = core.make_state(tasks[task], episode["submission"]["records"][:2])
        pool._require(states[task]["baseline"]["dependency_lag"] <= 19, "registered baseline lag differs")
        original_task = (Path(INPUT_PATHS["pool_contract"]).parent / "tasks" / (task + ".json")).as_posix()
        mirrors[f"{PUBLIC_DIRECTORY}/tasks/{task}.json"] = captured[original_task]
        mirrors[f"{PUBLIC_DIRECTORY}/states/{task}.json"] = (
            canonical_json(_sealed(states[task])) + "\n").encode()
        for condition in core.CONDITIONS:
            mirrors[f"{PUBLIC_DIRECTORY}/prompts/{task}-{condition}.txt"] = core.prompt(states[task], condition).encode()
        for generator in core.CHEAP_TEXT:
            for repetition in core.REPETITIONS:
                packet = core.cheap_packet(states[task], generator, repetition)
                pool._require(core.validate_proposal(packet["raw_response"])["eligible"], "registered cheap packet ineligible")
                cheap.append({"task_id": task, "generator": generator, "repetition": repetition, **packet})
    mirrors[f"{PUBLIC_DIRECTORY}/cheap.json"] = (canonical_json(_sealed({"packets": cheap})) + "\n").encode()
    body = {"schema": "astra-revision-contract-v1", "study": core.STUDY, "status": "PREPARED_NO_CALLS",
            "inputs": {name: {"path": path, **_identity(captured[path])} for name, path in INPUT_PATHS.items()},
            "bound_files": {path: _identity(raw) for path, raw in captured.items()},
            "mirror_files": {path: _identity(raw) for path, raw in mirrors.items()},
            "source_sha256": {path: pool._sha(captured[path]) for path in sorted(dependencies)},
            "data": original["data"], "runtime_versions": RUNTIME, "cli_identity": cli_identity,
            "model_settings": MODEL_SETTINGS, "actor_instructions": core.ACTOR_INSTRUCTIONS,
            "actor_instructions_sha256": pool._sha(core.ACTOR_INSTRUCTIONS.encode()),
            "states": states, "cheap_packets": cheap,
            "population": {"states": 10, "hosted_calls": 80, "cheap_slots": 120, "new_slots": 200,
                           "repetitions": 4, "maximum_new_feedback_calls": 200, "maximum_new_future_calls": 200},
            "round_order": [list(item) for item in core.ROUND_ORDER],
            "slot_order": [list(item) for item in core.SLOT_ORDER],
            "execution_directory": PUBLIC_DIRECTORY + "/execution", "transport_directory": TRANSPORT_DIRECTORY,
            "neutral_actor_context": TRANSPORT_DIRECTORY + "/actor-context",
            "submissions_path": SUBMISSIONS_PATH, "result_path": RESULT_PATH,
            "prior_structural_verification": verified, "new_model_calls": 0, "new_feedback_calls": 0,
            "new_future_calls": 0, "old_future_outcomes_parsed": False}
    return _sealed(body), tasks, _historical(bank, tasks), captured, mirrors


def prepare_revision_study(*, source_root, executable_probe=executable_identity):
    root = Path(source_root).resolve()
    destination = root / PUBLIC_DIRECTORY
    pool._require(not destination.exists(), "new study output already exists")
    executable = executable_probe()
    _cli(executable["identity"])
    contract, _, _, _, mirrors = _assemble(root, executable["identity"], verify_environment=True)
    destination.mkdir(parents=True, exist_ok=False)
    try:
        for relative, raw in mirrors.items():
            path = pool._path(root, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            pool._write_bytes(path, raw)
        pool._write(destination / "contract.json", contract)
    except BaseException:
        pool._write(destination / "INCOMPLETE.json", _sealed({"stage": "prepare", "created_utc": pool._now()}))
        raise
    return contract


def _verified_contract(root, *, verify_environment=False):
    path = root / PUBLIC_DIRECTORY / "contract.json"
    pool._require(not (path.parent / "INCOMPLETE.json").exists(), "preparation is permanently INCOMPLETE")
    raw = path.read_bytes()
    saved = pool._read(raw)
    expected, tasks, history, captured, mirrors = _assemble(root, saved["cli_identity"],
                                                          verify_environment=verify_environment)
    _cli(saved["cli_identity"])
    pool._exact(saved, expected, "prepared revision contract")
    for relative, value in mirrors.items():
        pool._require(pool._path(root, relative).read_bytes() == value, "prepared mirror changed")
    bound = {**captured, **mirrors, pool._relative(path, root): raw}
    return saved, tasks, history, bound


def _receipt(raw, stage, bound):
    value = pool._read(raw)
    pool._keys(value, {"schema", "study", "stage", "commit", "verified_utc", "verification_method",
                       "public_repository_url", "paths_sha256", "body_sha256"}, "publication receipt")
    pool._exact({key: value[key] for key in ("schema", "study", "stage", "verification_method")},
                {"schema": "astra-matched-prefix-publication-receipt-v1", "study": core.STUDY, "stage": stage,
                 "verification_method": "root-verified unauthenticated public retrieval"}, "receipt identity")
    pool._require(type(value["commit"]) is str and re.fullmatch(r"[0-9a-f]{40}", value["commit"]),
                  "receipt requires a full lowercase commit")
    pool._require(type(value["public_repository_url"]) is str and re.fullmatch(
        r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", value["public_repository_url"]), "invalid repository URL")
    pool._utc(value["verified_utc"])
    pool._exact(value["paths_sha256"], {path: pool._sha(raw) for path, raw in bound.items()}, "publication hashes")
    return value


def _gate(receipt_path, stage, bound, root, verifier):
    raw = Path(receipt_path).read_bytes()
    receipt = _receipt(raw, stage, bound)
    pool._require(pool._utc(receipt["verified_utc"]) <= pool._utc(pool._now()), "publication receipt is future-dated")
    proof = verifier(root, receipt["commit"], bound)
    pool._exact(proof, {"commit": receipt["commit"], "local_committed_bytes_verified": True}, "local publication proof")
    return raw, receipt


def _execution(root):
    directory = root / PUBLIC_DIRECTORY / "execution"
    pool._require(not directory.is_symlink(), "execution directory cannot be a link")
    if directory.exists():
        pool._require(directory.is_dir(), "execution path is not a directory")
        pool._require(not (directory / "INCOMPLETE.json").exists(), "study is permanently INCOMPLETE")
        allowed = {".execution-lock", "collection-request.json", "preparation-receipt.json", "batches",
                   "setup-commands",
                   "SUBMISSIONS.json", "assessment-request.json", "submissions-receipt.json", "assessment-plan.json",
                   "assessment-jobs", "COMPLETE.json"}
        pool._require(all(path.name in allowed and not path.is_symlink() for path in directory.iterdir()),
                      "unexplained execution evidence")
    return directory


def _incomplete(directory, stage, error=None, *, reason=None):
    path = directory / "INCOMPLETE.json"
    if not path.exists():
        pool._write(path, _sealed({"study": core.STUDY, "stage": stage, "created_utc": pool._now(),
                                  "error_type": None if error is None else type(error).__name__,
                                  "reason": reason, "automatic_retries": 0}))


def _read_public(path, captured):
    raw = path.read_bytes()
    captured[path] = raw
    return pool._read(raw)


def _batch_name(task, repetition):
    return f"{core.TASK_IDS.index(task) * 4 + repetition:02d}-{task}-r{repetition}"


def _slot(task, generator, repetition, adjudication, feedback_source, generation=None, transport=None):
    return {"slot_id": f"{task}/{generator}/{repetition}", "task_id": task, "generator": generator,
            "repetition": repetition, "adjudication": adjudication, "feedback_source": feedback_source,
            "generation": generation, "transport": transport}


def _historical_adjudication(raw, state, cache, *, slot_id, feedback_tool=None):
    proposal = core.validate_proposal(raw)
    feedback, source = None, None
    called = False
    if proposal["eligible"]:
        key = digest([state["task_id"], proposal["canonical_ast"]])
        if key in cache:
            feedback = copy.deepcopy(cache[key]["feedback"])
            source = copy.deepcopy(cache[key]["sources"][0])
        else:
            pool._require(feedback_tool is not None, "missing saved historical feedback")
            feedback = core.checked_feedback(feedback_tool(proposal["packet"]["expression"]), state["feedback_length"])
            source = {"kind": "new_feedback", "first_slot_id": slot_id, "expression": proposal["packet"]["expression"]}
            cache[key] = {"feedback": copy.deepcopy(feedback), "sources": [source]}
            called = True
    return core.adjudicate(raw, state, feedback), source, called


def _saved_slot(value, state, cache, *, generation=None, prompt_text=None):
    pool._keys(value, {"slot_id", "task_id", "generator", "repetition", "adjudication", "feedback_source",
                       "generation", "transport"}, "slot")
    raw = value["adjudication"]["raw_response"]
    if generation is not None:
        pool._exact(raw, generation["raw_response"], "scheduled cheap response")
        pool._exact(value["generation"], generation["generation"], "cheap generation provenance")
        pool._exact(value["transport"], None, "cheap provider absence")
    else:
        pool._exact(value["generation"], None, "hosted generation metadata")
        astra_replay._transport(value["transport"], prompt_text, raw)
    validated, source, called = _historical_adjudication(
        raw, state, cache, slot_id=value["slot_id"],
        feedback_tool=lambda expression: value["adjudication"]["feedback"],
    )
    pool._exact(value["adjudication"], validated, "saved historical adjudication/selector")
    pool._exact(value["feedback_source"], source, "historical cache provenance")
    return called


def _collection_prefix(root, contract, history, bound):
    directory = _execution(root)
    captured, completed, slots = {}, [], []
    request_path = directory / "collection-request.json"
    if not directory.exists() or not request_path.exists():
        pool._require(not directory.exists() or {p.name for p in directory.iterdir()} <= {".execution-lock"},
                      "collection files exist without request")
        return completed, slots, history, captured, None
    request = _read_public(request_path, captured)
    pool._keys(request, {"study", "contract_sha256", "created_utc", "preparation_receipt_sha256",
                         "preparation_receipt", "body_sha256"}, "collection request")
    contract_hash = pool._sha(bound[PUBLIC_DIRECTORY + "/contract.json"])
    pool._exact([request["study"], request["contract_sha256"]], [core.STUDY, contract_hash], "collection identity")
    receipt_path = directory / "preparation-receipt.json"
    receipt_raw = receipt_path.read_bytes()
    captured[receipt_path] = receipt_raw
    receipt = _receipt(receipt_raw, "preparation", bound)
    pool._exact(receipt, request["preparation_receipt"], "saved preparation receipt")
    pool._exact(pool._sha(receipt_raw), request["preparation_receipt_sha256"], "preparation receipt bytes")
    previous_time = pool._utc(request["created_utc"])
    pool._require(previous_time >= pool._utc(receipt["verified_utc"]), "collection request predates publication")
    previous = request["body_sha256"]
    setup_records = _setup_prefix(directory, request, captured)
    batches = directory / "batches"
    pool._require(batches.is_dir() and not batches.is_symlink(), "missing batch bank")
    entries = sorted(batches.iterdir())
    expected_names = [_batch_name(*item) for item in core.ROUND_ORDER[:len(entries)]]
    pool._require([path.name for path in entries] == expected_names and len(entries) <= 40, "batch order/membership changed")
    for path, (task, repetition) in zip(entries, core.ROUND_ORDER, strict=False):
        pool._require(path.is_dir() and not path.is_symlink(), "invalid batch directory")
        expected_files = {"STARTED.json", "COMPLETED.json", "truthful-STARTED.json", "masked-STARTED.json",
                          "truthful-RESPONSE.json", "masked-RESPONSE.json", "truthful-prompt.txt", "masked-prompt.txt",
                          "truthful-DISPATCH.json", "masked-DISPATCH.json"}
        pool._require({p.name for p in path.iterdir()} == expected_files and all(p.is_file() and not p.is_symlink()
                      for p in path.iterdir()), "ambiguous or unexpected batch evidence")
        start = _read_public(path / "STARTED.json", captured)
        end = _read_public(path / "COMPLETED.json", captured)
        pool._keys(start, {"study", "contract_sha256", "task_id", "repetition", "previous_body_sha256", "started_utc",
                          "quota", "launch_order", "setup_completed_body_sha256", "body_sha256"}, "batch start")
        pool._exact([start["study"], start["contract_sha256"], start["task_id"], start["repetition"], start["previous_body_sha256"]],
                    [core.STUDY, contract_hash, task, repetition, previous], "batch start chain")
        started = pool._utc(start["started_utc"])
        pool._require(started >= previous_time, "batch chronology reversed")
        setup = next((value for value in setup_records if value["body_sha256"] == start["setup_completed_body_sha256"]), None)
        pool._require(setup is not None and setup["status"] == "READY" and setup["task_id"] == task
                      and setup["repetition"] == repetition and pool._utc(setup["completed_utc"]) <= started,
                      "batch lacks its completed setup command")
        _quota(start["quota"], now=start["started_utc"], require_ready=True)
        offset = (core.TASK_IDS.index(task) + repetition - 1) % 2
        order = list(core.CONDITIONS[offset:] + core.CONDITIONS[:offset])
        pool._exact(start["launch_order"], order, "condition launch order")
        pool._keys(end, {"study", "status", "started_body_sha256", "completed_utc", "slots", "accounting",
                        "response_sha256", "body_sha256"}, "batch completion")
        pool._exact([end["study"], end["status"], end["started_body_sha256"]],
                    [core.STUDY, "BATCH_COMPLETE", start["body_sha256"]], "batch completion identity")
        completed_time = pool._utc(end["completed_utc"])
        pool._require(completed_time >= started, "batch completion predates start")
        state = contract["states"][task]
        responses = {}
        for condition in core.CONDITIONS:
            prompt_text = core.prompt(state, condition)
            prompt_path = path / (condition + "-prompt.txt")
            captured[prompt_path] = prompt_path.read_bytes()
            pool._require(captured[prompt_path] == prompt_text.encode(), "recorded prompt bytes differ")
            actor_start = _read_public(path / (condition + "-STARTED.json"), captured)
            pool._keys(actor_start, {"batch_started_body_sha256", "condition", "prompt_sha256", "created_utc", "body_sha256"},
                       "actor start")
            pool._exact([actor_start["batch_started_body_sha256"], actor_start["condition"], actor_start["prompt_sha256"]],
                        [start["body_sha256"], condition, pool._sha(prompt_text.encode())], "actor start identity")
            pool._require(started <= pool._utc(actor_start["created_utc"]) <= completed_time, "actor start chronology")
            dispatch = _read_public(path / (condition + "-DISPATCH.json"), captured)
            pool._keys(dispatch, {"actor_started_body_sha256", "quota_checked_utc", "body_sha256"}, "dispatch record")
            pool._exact(dispatch["actor_started_body_sha256"], actor_start["body_sha256"], "dispatch identity")
            pool._require(pool._utc(actor_start["created_utc"]) <= pool._utc(dispatch["quota_checked_utc"])
                          <= completed_time, "dispatch chronology")
            _quota(start["quota"], now=dispatch["quota_checked_utc"], require_ready=True)
            response = _read_public(path / (condition + "-RESPONSE.json"), captured)
            pool._keys(response, {"actor_started_body_sha256", "completed_utc", "raw_response", "transport", "body_sha256"},
                       "actor response")
            pool._exact(response["actor_started_body_sha256"], actor_start["body_sha256"], "actor response chain")
            pool._require(pool._utc(actor_start["created_utc"]) <= pool._utc(response["completed_utc"]) <= completed_time,
                          "actor response chronology")
            astra_replay._transport(response["transport"], prompt_text, response["raw_response"])
            pool._require(pool._utc(dispatch["quota_checked_utc"]) <= pool._utc(response["transport"]["started_at_utc"])
                          <= pool._utc(response["transport"]["ended_at_utc"]) <= pool._utc(response["completed_utc"]),
                          "provider timing lies outside dispatch/response bounds")
            responses[condition] = response
        pool._exact(end["response_sha256"], {name: response["body_sha256"] for name, response in responses.items()},
                    "response digests")
        pool._require(type(end["slots"]) is list and len(end["slots"]) == 5, "batch must retain five proposals")
        calls = 0
        for value, generator in zip(end["slots"], core.GENERATORS, strict=True):
            pool._exact([value["slot_id"], value["task_id"], value["generator"], value["repetition"]],
                        [f"{task}/{generator}/{repetition}", task, generator, repetition], "slot identity")
            if generator in core.CONDITIONS:
                response = responses[generator]
                pool._exact([value["adjudication"]["raw_response"], value["transport"]],
                            [response["raw_response"], response["transport"]], "hosted slot response")
                calls += _saved_slot(value, state, history, prompt_text=core.prompt(state, generator))
            else:
                calls += _saved_slot(value, state, history, generation=core.cheap_packet(state, generator, repetition))
        pool._exact(end["accounting"], {"hosted_calls": 2, "new_feedback_calls": calls,
                                       "task_constructions": 1, "initial_probe_checks": 2, "future_calls": 0},
                    "batch accounting")
        slots.extend(end["slots"])
        completed.append(end)
        previous, previous_time = end["body_sha256"], completed_time
    return completed, slots, history, captured, request


def _setup_prefix(directory, request, captured):
    path = directory / "setup-commands"
    pool._require(path.is_dir() and not path.is_symlink(), "missing setup-command ledger")
    entries = sorted(path.iterdir())
    pool._require([item.name for item in entries] == [f"{i:03d}" for i in range(1, len(entries) + 1)],
                  "setup command membership differs")
    previous, previous_time = request["body_sha256"], pool._utc(request["created_utc"])
    completed = []
    for item in entries:
        pool._require(item.is_dir() and not item.is_symlink() and {p.name for p in item.iterdir()}
                      == {"STARTED.json", "COMPLETED.json"} and all(p.is_file() and not p.is_symlink()
                      for p in item.iterdir()), "ambiguous setup command")
        start = _read_public(item / "STARTED.json", captured)
        end = _read_public(item / "COMPLETED.json", captured)
        pool._keys(start, {"task_id", "repetition", "created_utc", "previous_body_sha256", "quota", "body_sha256"},
                   "setup start")
        pool._require((start["task_id"], start["repetition"]) in core.ROUND_ORDER and type(start["repetition"]) is int,
                      "invalid setup task/repetition")
        pool._exact(start["previous_body_sha256"], previous, "setup chain")
        pool._require(pool._utc(start["created_utc"]) >= previous_time, "setup chronology reversed")
        pool._keys(end, {"task_id", "repetition", "started_body_sha256", "completed_utc", "status",
                        "task_constructions", "initial_probe_checks", "body_sha256"}, "setup completion")
        pool._exact([end["task_id"], end["repetition"], end["started_body_sha256"],
                     end["task_constructions"], end["initial_probe_checks"]],
                    [start["task_id"], start["repetition"], start["body_sha256"], 1, 2], "setup completion identity/counts")
        pool._require(end["status"] in {"READY", "WAIT_QUOTA"} and pool._utc(end["completed_utc"])
                      >= pool._utc(start["created_utc"]), "invalid completed setup status/time")
        _quota(start["quota"], now=start["created_utc"], require_ready=True)
        pool._exact(end["status"], _quota(start["quota"], now=end["completed_utc"]), "setup quota status")
        previous, previous_time = end["body_sha256"], pool._utc(end["completed_utc"])
        completed.append(end)
    return completed


def _quota(value, *, now=None, require_ready=False):
    pool._keys(value, {"remaining_percent", "checked_utc", "provenance"}, "quota observation")
    pool._require(type(value["provenance"]) is str and value["provenance"], "quota provenance missing")
    if value["remaining_percent"] is None or value["checked_utc"] is None:
        pool._require(not require_ready, "quota was not known at dispatch")
        return "WAIT_QUOTA"
    remaining = value["remaining_percent"]
    pool._require(type(remaining) in (int, float) and math.isfinite(remaining) and 0 <= remaining <= 100,
                  "invalid remaining quota")
    age = (pool._utc(now or pool._now()) - pool._utc(value["checked_utc"])).total_seconds()
    pool._require(age >= 0, "quota observation is future-dated")
    if age > 60:
        pool._require(not require_ready, "quota observation stale at dispatch")
        return "WAIT_QUOTA"
    if remaining <= 5:
        pool._require(not require_ready, "quota threshold was reached at dispatch")
        return "STOP_QUOTA"
    return "READY"


def _load_task(data_path, task_id):
    from .financial_policy import load_pinned_panel
    from .financial_tasks import make_task

    return make_task(load_pinned_panel(data_path), int(task_id[:4]), int(task_id[-1]))


def _task(loader, root, contract, tasks, task_id):
    result = loader(pool._path(root, contract["data"]["path"]), task_id)
    pool._exact(result.public_manifest, tasks[task_id]["financial_manifest"], "loaded task manifest")
    pool._exact(result.observation(), tasks[task_id]["initial_observation"], "loaded initial probes")
    return result


def _assert_bound(root, bound, contract):
    for relative, raw in bound.items():
        pool._require(pool._path(root, relative).read_bytes() == raw, "bound public bytes changed")
    pool._exact(pool._versions(), contract["runtime_versions"], "current scoring runtime")
    pool._data_bytes(pool._path(root, contract["data"]["path"]), contract["data"]["sha256"])


def _private_first_use(local, receipt_path):
    if local.exists():
        pool._require(local.is_dir() and not local.is_symlink(), "invalid local transport directory")
        allowed = Path(receipt_path).resolve()
        for path in local.rglob("*"):
            pool._require(not path.is_symlink() and (path.resolve() == allowed
                          or path.is_dir() and path.resolve() in allowed.parents),
                          "unexplained local transport files before first collection")
    else:
        local.mkdir(parents=True, exist_ok=False)
    (local / "actor-context").mkdir(exist_ok=False)


def _provider_response(prompt_text, destination, context, executable, actor_runner):
    """Retain private results before deciding success; no historical or future callback."""
    destination.mkdir(parents=True, exist_ok=False)
    try:
        result = actor_runner(prompt_text, destination / "provider", timeout_seconds=600,
                              cwd=context, executable=executable)
        summary = result.public_summary
        pool._write(destination / "actor-result.json", {
            "success": result.success, "status": result.status, "error": result.error,
            "final_text": result.final_text, "usage": result.usage, "returncode": result.returncode,
            "artifact_paths": result.artifact_paths, "public_summary": summary,
        })
        pool._require(result.success is True and type(result.final_text) is str, "provider failed without retry")
        astra_replay._transport(summary, prompt_text, result.final_text)
        pool._exact([result.status, result.error, result.returncode, result.usage],
                    [summary["status"], summary["error"], summary["returncode"], summary["usage"]], "provider result metadata")
        for name, identity in summary["artifacts"].items():
            path = destination / "provider" / name
            pool._require(path.is_file() and not path.is_symlink(), "private provider artifact missing")
            pool._exact(_identity(path.read_bytes()), identity, "private provider artifact bytes")
        return {"raw_response": result.final_text, "transport": summary}
    except BaseException as error:
        path = destination / "FAILED.json"
        if not path.exists():
            pool._write(path, {"error_type": type(error).__name__, "created_utc": pool._now()})
        raise


def collect_pair(task_id, repetition, *, source_root, publication_receipt_path, quota,
                 actor_runner=None, task_loader=_load_task, executable_probe=executable_identity,
                 publication_verifier=pool.verify_local_commit):
    """One explicitly invoked two-call batch; never loop, retry or repair a slot."""
    quota = copy.deepcopy(quota)
    status = _quota(quota)
    if status == "WAIT_QUOTA":
        return {"status": status, "new_calls": 0}
    root = Path(source_root).resolve()
    directory = _execution(root)
    pool._require(not (directory / "SUBMISSIONS.json").exists(), "submissions are frozen; collection cannot resume")
    contract, tasks, history, bound = _verified_contract(root, verify_environment=True)
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / ".execution-lock"
    lock.mkdir(exist_ok=False)
    started = False
    setup_attempted = False
    try:
        try:
            completed, _, history, _, request = _collection_prefix(root, contract, history, bound)
        except BaseException as error:
            _incomplete(directory, "corrupt-or-ambiguous-collection-prefix", error)
            raise
        pool._require(len(completed) < 40 and (task_id, repetition) == core.ROUND_ORDER[len(completed)]
                      and type(repetition) is int, "request is not the next fixed batch")
        if status == "STOP_QUOTA":
            _incomplete(directory, "quota-reserve-stop")
            return {"status": "INCOMPLETE", "reason": "quota-reserve-stop", "new_calls": 0}
        receipt_raw, receipt = _gate(publication_receipt_path, "preparation", bound, root, publication_verifier)
        local = root / contract["transport_directory"]
        setup_attempted = True
        if request is None:
            _private_first_use(local, publication_receipt_path)
            request = _sealed({"study": core.STUDY, "contract_sha256": pool._sha(bound[PUBLIC_DIRECTORY + "/contract.json"]),
                               "created_utc": pool._now(), "preparation_receipt_sha256": pool._sha(receipt_raw),
                               "preparation_receipt": receipt})
            pool._write_bytes(directory / "preparation-receipt.json", receipt_raw)
            pool._write(directory / "collection-request.json", request)
            (directory / "batches").mkdir()
            (directory / "setup-commands").mkdir()
        else:
            pool._require((directory / "preparation-receipt.json").read_bytes() == receipt_raw,
                          "preparation receipt changed during collection")
        context = root / contract["neutral_actor_context"]
        pool._require(context.is_dir() and not context.is_symlink() and not any(context.iterdir()),
                      "neutral context changed or is unavailable")
        status = _quota(quota)
        if status != "READY":
            return {"status": status, "new_calls": 0}
        prior_setup = _setup_prefix(directory, request, {})
        setup_started_utc = pool._now()
        status = _quota(quota, now=setup_started_utc)
        if status != "READY":
            return {"status": status, "new_calls": 0}
        setup_path = directory / "setup-commands" / f"{len(prior_setup) + 1:03d}"
        setup_path.mkdir(exist_ok=False)
        setup_start = _sealed({"task_id": task_id, "repetition": repetition, "created_utc": setup_started_utc,
                               "previous_body_sha256": prior_setup[-1]["body_sha256"]
                               if prior_setup else request["body_sha256"], "quota": quota})
        pool._write(setup_path / "STARTED.json", setup_start)
        executable = executable_probe()
        pool._exact(executable["identity"], contract["cli_identity"], "CLI identity changed")
        task = _task(task_loader, root, contract, tasks, task_id)
        _assert_bound(root, bound, contract)
        setup_time = pool._now()
        status = _quota(quota, now=setup_time)
        setup_end = _sealed({"task_id": task_id, "repetition": repetition, "started_body_sha256": setup_start["body_sha256"],
                             "completed_utc": setup_time, "status": status, "task_constructions": 1,
                             "initial_probe_checks": 2})
        pool._write(setup_path / "COMPLETED.json", setup_end)
        if status != "READY":
            if status == "STOP_QUOTA":
                _incomplete(directory, "quota-reserve-stop")
            return {"status": status, "new_calls": 0}
        name = _batch_name(task_id, repetition)
        batch = directory / "batches" / name
        batch.mkdir(exist_ok=False)
        offset = (core.TASK_IDS.index(task_id) + repetition - 1) % 2
        launch_order = list(core.CONDITIONS[offset:] + core.CONDITIONS[:offset])
        start = _sealed({"study": core.STUDY, "contract_sha256": request["contract_sha256"], "task_id": task_id,
                         "repetition": repetition, "previous_body_sha256": completed[-1]["body_sha256"]
                         if completed else request["body_sha256"], "started_utc": pool._now(), "quota": quota,
                         "launch_order": launch_order, "setup_completed_body_sha256": setup_end["body_sha256"]})
        pool._write(batch / "STARTED.json", start)
        started = True
        actor_starts, responses, failures, dispatch_times = {}, {}, [], {}
        for condition in launch_order:
            text = core.prompt(contract["states"][task_id], condition)
            pool._write_bytes(batch / (condition + "-prompt.txt"), text.encode())
            actor_starts[condition] = _sealed({"batch_started_body_sha256": start["body_sha256"], "condition": condition,
                                              "prompt_sha256": pool._sha(text.encode()), "created_utc": pool._now()})
            pool._write(batch / (condition + "-STARTED.json"), actor_starts[condition])
        if actor_runner is None:
            from .codex_actor import run_actor
            actor_runner = run_actor
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}
            for condition in launch_order:
                try:
                    dispatch_time = pool._now()
                    _quota(quota, now=dispatch_time, require_ready=True)
                    dispatch_times[condition] = dispatch_time
                    future = executor.submit(_provider_response, core.prompt(contract["states"][task_id], condition),
                                             local / "batches" / name / condition, context, executable["path"], actor_runner)
                    futures[future] = condition
                    pool._write(batch / (condition + "-DISPATCH.json"), _sealed({
                        "actor_started_body_sha256": actor_starts[condition]["body_sha256"],
                        "quota_checked_utc": dispatch_time}))
                except BaseException as error:  # noqa: BLE001 - retain already dispatched siblings, then fail closed.
                    failures.append(type(error).__name__)
                    break
            for future in as_completed(futures):
                condition = futures[future]
                try:
                    response = future.result()
                    value = _sealed({"actor_started_body_sha256": actor_starts[condition]["body_sha256"],
                                     "completed_utc": pool._now(), **response})
                    pool._write(batch / (condition + "-RESPONSE.json"), value)
                    pool._require(pool._utc(dispatch_times[condition]) <= pool._utc(response["transport"]["started_at_utc"])
                                  <= pool._utc(response["transport"]["ended_at_utc"]) <= pool._utc(value["completed_utc"]),
                                  "provider timing lies outside dispatch/response bounds")
                    responses[condition] = value
                except BaseException as error:  # noqa: BLE001 - retain every sibling result, never retry failures.
                    failures.append(type(error).__name__)
        pool._require(not failures and len(responses) == 2, "one or more hosted calls failed; no retry")
        slots, feedback_calls = [], 0
        state = contract["states"][task_id]
        for generator in core.GENERATORS:
            cheap = None if generator in core.CONDITIONS else core.cheap_packet(state, generator, repetition)
            raw = responses[generator]["raw_response"] if cheap is None else cheap["raw_response"]
            record, source, called = _historical_adjudication(raw, state, history,
                                                            slot_id=f"{task_id}/{generator}/{repetition}",
                                                            feedback_tool=task.feedback_score)
            feedback_calls += called
            slots.append(_slot(task_id, generator, repetition, record, source,
                               generation=None if cheap is None else cheap["generation"],
                               transport=responses[generator]["transport"] if cheap is None else None))
        result = _sealed({"study": core.STUDY, "status": "BATCH_COMPLETE", "started_body_sha256": start["body_sha256"],
                          "completed_utc": pool._now(), "slots": slots,
                          "accounting": {"hosted_calls": 2, "new_feedback_calls": feedback_calls,
                                         "task_constructions": 1, "initial_probe_checks": 2, "future_calls": 0},
                          "response_sha256": {condition: responses[condition]["body_sha256"] for condition in core.CONDITIONS}})
        pool._write(batch / "COMPLETED.json", result)
        return result
    except BaseException as error:
        if started or setup_attempted:
            _incomplete(directory, "collection-failure", error)
        raise
    finally:
        lock.rmdir()


def _submission_body(contract, bound, completed, slots, captured, request, root):
    pool._require(len(completed) == 40 and len(slots) == 200, "the entire 80-call/200-slot bank is required")
    indexed = {(slot["task_id"], slot["generator"], slot["repetition"]): slot for slot in slots}
    pool._require(set(indexed) == set(core.SLOT_ORDER), "fixed slot membership differs")
    ordered = [copy.deepcopy(indexed[key]) for key in core.SLOT_ORDER]
    seen = {}
    for slot in ordered:
        key = slot["adjudication"]["canonical_ast"]
        scope = None if key is None else digest([slot["task_id"], key])
        slot["canonical_duplicate_across_new_slots"] = scope is not None and scope in seen
        slot["first_new_slot_with_ast"] = None if scope is None else seen.setdefault(scope, slot["slot_id"])
    new_feedback = sum(item["accounting"]["new_feedback_calls"] for item in completed)
    setup = [pool._read(raw) for path, raw in captured.items()
             if "setup-commands" in path.parts and path.name == "COMPLETED.json"]
    pool._require(new_feedback <= 200, "new historical feedback budget exceeded")
    return _sealed({"schema": "astra-revision-submissions-v1", "study": core.STUDY,
                    "status": "ALL_200_SLOTS_FROZEN_NO_JOINED_FUTURE_OUTCOMES",
                    "contract_sha256": pool._sha(bound[PUBLIC_DIRECTORY + "/contract.json"]),
                    "collection_request_body_sha256": request["body_sha256"],
                    "last_collection_completed_utc": completed[-1]["completed_utc"],
                    "preparation_receipt": request["preparation_receipt"], "slots": ordered,
                    "collection_files": {pool._relative(path, root): _identity(raw) for path, raw in captured.items()},
                    "accounting": {"hosted_calls": 80, "cheap_slots": 120, "new_slots": 200,
                                   "new_feedback_calls": new_feedback, "task_constructions": len(setup),
                                   "initial_probe_checks": 2 * len(setup), "future_calls": 0,
                                   "cached_future_outcomes_joined": 0, "automatic_retries": 0}})


def freeze_revision_study(*, source_root):
    root = Path(source_root).resolve()
    contract, _, history, bound = _verified_contract(root)
    directory = _execution(root)
    pool._require(not (directory / "SUBMISSIONS.json").exists() and not (root / SUBMISSIONS_PATH).exists(),
                  "submission output already exists")
    lock = directory / ".execution-lock"
    lock.mkdir(exist_ok=False)
    writing = False
    try:
        completed, slots, _, captured, request = _collection_prefix(root, contract, history, bound)
        body = _submission_body(contract, bound, completed, slots, captured, request, root)
        writing = True
        pool._write(directory / "SUBMISSIONS.json", body)
        (root / SUBMISSIONS_PATH).parent.mkdir(parents=True, exist_ok=True)
        pool._write(root / SUBMISSIONS_PATH, body)
        return body
    except BaseException as error:
        if writing:
            _incomplete(directory, "submission-freeze-write-failure", error)
        raise
    finally:
        lock.rmdir()


def _verified_submissions(root, contract, history, bound):
    completed, slots, _, captured, request = _collection_prefix(root, contract, history, bound)
    expected = _submission_body(contract, bound, completed, slots, captured, request, root)
    path = root / SUBMISSIONS_PATH
    raw = path.read_bytes()
    saved = pool._read(raw)
    pool._exact(saved, expected, "frozen all-slot bank and historical selectors")
    counterpart = root / PUBLIC_DIRECTORY / "execution" / "SUBMISSIONS.json"
    pool._require(counterpart.read_bytes() == raw, "public and retained submission bytes differ")
    files = {**bound, **{pool._relative(path, root): value for path, value in captured.items()},
             SUBMISSIONS_PATH: raw, pool._relative(counterpart, root): raw}
    return saved, files


def publication_files(*, source_root, stage):
    """Exact required public map at either gate; never parses old future outcomes."""
    pool._require(stage in {"preparation", "submissions"}, "unknown publication stage")
    root = Path(source_root).resolve()
    contract, _, history, bound = _verified_contract(root)
    if stage == "submissions":
        _, bound = _verified_submissions(root, contract, history, bound)
    return {path: pool._sha(raw) for path, raw in bound.items()}


def _cache_and_plan(root, contract, submissions, bound):
    """Gate-2-only: full prior arithmetic validation and exact future-cache lookup."""
    with tempfile.TemporaryDirectory(prefix="astra-revision-cache-") as temporary:
        snapshot = Path(temporary)
        _snapshot(bound, snapshot)
        pool_path = snapshot / INPUT_PATHS["pool_contract"]
        pool.replay_pool_diagnosis(pool_path, pool_path.parent / "execution", source_root=snapshot,
                                  report_path=snapshot / INPUT_PATHS["pool_result"])
    previous = pool._read(bound[INPUT_PATHS["pool_result"]])
    cache = {item["key"]["key_id"]: item for item in previous["key_results"]}
    pool._require(len(cache) == len(previous["key_results"]) == 132, "prior cache must have exactly 132 unique keys")
    used, jobs = {}, []

    def lookup(task, item, source_slot):
        key_id = digest([task, item["canonical_ast"], item["orientation"]])
        feedback = {key: value for key, value in item["feedback"].items() if key != "usable"}
        if key_id in cache:
            existing = cache[key_id]
            pool._exact([existing["key"]["task_id"], existing["key"]["canonical_ast"], existing["key"]["orientation"],
                         existing["key"]["feedback"]], [task, item["canonical_ast"], item["orientation"], feedback],
                        "cache key historical identity")
        if key_id not in used:
            used[key_id] = {"key_id": key_id, "task_id": task, "canonical_ast": item["canonical_ast"],
                            "orientation": item["orientation"], "feedback": feedback,
                            "representative_expression": item["expression"], "first_new_slot_id": source_slot,
                            "cached": key_id in cache}
            if key_id not in cache:
                jobs.append({"job_number": len(jobs) + 1, "key_id": key_id, "task_id": task,
                             "expression": item["expression"]})
        else:
            pool._exact(used[key_id]["feedback"], feedback, "same new cache key historical metrics")
            if used[key_id]["first_new_slot_id"] is None and source_slot is not None:
                used[key_id]["first_new_slot_id"] = source_slot
        return key_id

    prefixes = {}
    for task in core.TASK_IDS:
        prefixes[task] = []
        for item in contract["states"][task]["prefix"]:
            key_id = lookup(task, item, None)
            pool._require(key_id in cache and cache[key_id]["diagnosis"]["valid"], "valid prefix cache is missing")
            prefixes[task].append(key_id)
    slot_keys = {}
    for slot in submissions["slots"]:
        record = slot["adjudication"]
        key_id = None
        if record["eligible"] and record["historically_usable"]:
            key_id = lookup(slot["task_id"], {"canonical_ast": record["canonical_ast"], "orientation": record["orientation"],
                                             "feedback": record["feedback"], "expression": record["packet"]["expression"]},
                            slot["slot_id"])
        slot_keys[slot["slot_id"]] = key_id
    pool._require(len(jobs) <= 200, "new future job budget exceeded")
    selected_cache = {key: cache[key] for key in used if key in cache}
    return _sealed({"study": core.STUDY, "submissions_sha256": pool._sha(bound[SUBMISSIONS_PATH]),
                    "prior_pool_result_sha256": pool._sha(bound[INPUT_PATHS["pool_result"]]),
                    "keys": list(used.values()), "prefix_keys": prefixes, "slot_keys": slot_keys,
                    "cached_outcomes": selected_cache, "jobs": jobs})


def _quality_from_outcome(raw, key, task, expression):
    validated = pool._outcome(raw, key, task, evaluated_expression=expression)
    return core.quality(validated["valid"], validated["oriented_future_ic"] if validated["valid"] else -1.0)


def _assessment_request(root, contract, bound):
    directory = _execution(root)
    path = directory / "assessment-request.json"
    value = pool._read(path.read_bytes())
    pool._keys(value, {"study", "contract_sha256", "submissions_sha256", "submissions_receipt_sha256",
                       "submissions_receipt", "created_utc", "body_sha256"}, "assessment request")
    pool._exact([value["study"], value["contract_sha256"], value["submissions_sha256"]],
                [core.STUDY, pool._sha(bound[PUBLIC_DIRECTORY + "/contract.json"]), pool._sha(bound[SUBMISSIONS_PATH])],
                "assessment request identity")
    raw = (directory / "submissions-receipt.json").read_bytes()
    receipt = _receipt(raw, "submissions", bound)
    pool._exact(receipt, value["submissions_receipt"], "saved submissions receipt")
    pool._exact(pool._sha(raw), value["submissions_receipt_sha256"], "saved submissions receipt bytes")
    pool._require(pool._utc(value["created_utc"]) >= pool._utc(receipt["verified_utc"]), "assessment predates publication")
    bank = pool._read(bound[SUBMISSIONS_PATH])
    pool._require(pool._utc(receipt["verified_utc"]) >= pool._utc(bank["last_collection_completed_utc"]),
                  "submissions publication receipt predates the complete collection")
    return value


def _assessment_prefix(directory, request, plan, tasks):
    parent = directory / "assessment-jobs"
    pool._require(parent.is_dir() and not parent.is_symlink(), "missing assessment job directory")
    entries = sorted(parent.iterdir())
    jobs = plan["jobs"]
    pool._require([path.name for path in entries] == [f"{job['job_number']:03d}" for job in jobs[:len(entries)]]
                  and len(entries) <= len(jobs), "assessment job membership/order changed")
    previous, previous_time = request["body_sha256"], pool._utc(request["created_utc"])
    completed, commands = [], {}
    key_map = {key["key_id"]: key for key in plan["keys"]}
    for path, job in zip(entries, jobs, strict=False):
        pool._require(path.is_dir() and not path.is_symlink() and {p.name for p in path.iterdir()}
                      == {"STARTED.json", "COMPLETED.json"} and all(p.is_file() and not p.is_symlink()
                      for p in path.iterdir()), "ambiguous assessment job; no retry permitted")
        start, end = (pool._read((path / name).read_bytes()) for name in ("STARTED.json", "COMPLETED.json"))
        pool._keys(start, {"job", "assessment_request_body_sha256", "previous_body_sha256", "created_utc",
                          "command_start_job_number", "task_constructions", "initial_probe_checks", "body_sha256"},
                   "assessment job start")
        pool._exact(start["job"], job, "assessment job identity")
        pool._exact([start["assessment_request_body_sha256"], start["previous_body_sha256"]],
                    [request["body_sha256"], previous], "assessment job chain")
        command = start["command_start_job_number"]
        pool._require(type(command) is int and 1 <= command <= job["job_number"], "invalid assessment command identity")
        if command not in commands:
            pool._require(command == job["job_number"], "assessment command must begin at its first job")
            commands[command] = set()
        else:
            pool._require(command == max(commands), "assessment command chronology reversed")
        setup = int(job["task_id"] not in commands[command])
        pool._exact([start["task_constructions"], start["initial_probe_checks"]], [setup, 2 * setup], "assessment setup counts")
        commands[command].add(job["task_id"])
        pool._require(pool._utc(start["created_utc"]) >= previous_time, "assessment start chronology reversed")
        pool._keys(end, {"started_body_sha256", "completed_utc", "raw_outcome", "quality", "body_sha256"},
                   "assessment job completion")
        pool._exact(end["started_body_sha256"], start["body_sha256"], "assessment completion chain")
        pool._require(pool._utc(end["completed_utc"]) >= pool._utc(start["created_utc"]), "assessment completion chronology")
        expected = _quality_from_outcome(end["raw_outcome"], key_map[job["key_id"]], tasks[job["task_id"]], job["expression"])
        pool._keys(end["quality"], {"valid", "Q"}, "completed quality")
        pool._exact(end["quality"]["valid"], expected["valid"], "assessment validity")
        pool._arithmetic(end["quality"]["Q"], expected["Q"], "assessment Q")
        completed.append({"job": job, "start": start, "completion": end})
        previous, previous_time = end["body_sha256"], pool._utc(end["completed_utc"])
    return completed


def _usage(slots):
    from .codex_actor import USAGE_KEYS

    result = {}
    for generator in core.CONDITIONS:
        summaries = [slot["transport"] for slot in slots if slot["generator"] == generator]
        usage = {}
        for field in sorted(USAGE_KEYS):
            values = [summary["usage"][field] for summary in summaries
                      if summary["usage"] is not None and field in summary["usage"]]
            usage[field] = {"reported_sum": sum(values), "reported_decisions": len(values),
                            "missing_decisions": 40 - len(values), "complete_sum": sum(values) if len(values) == 40 else None}
        times = [summary["elapsed_seconds"] for summary in summaries]
        result[generator] = {"decisions": 40, "usage": usage,
                             "elapsed_seconds": {"sum": math.fsum(times), "min": min(times), "max": max(times)}}
    return {"conditions": result, "reasoning_output_is_not_added_to_output_tokens": True,
            "elapsed_is_sum_of_calls_not_wall_clock": True}


def _report(root, contract, tasks, submissions, bound, request, plan, completed):
    pool._require(len(completed) == len(plan["jobs"]), "all new future jobs must complete before reporting")
    by_new = {item["job"]["key_id"]: item for item in completed}
    resolved = {}
    for key in plan["keys"]:
        key_id = key["key_id"]
        if key["cached"]:
            previous = plan["cached_outcomes"][key_id]
            raw = previous["raw_evaluator_outcome"]
            provenance = {"kind": "prior_pool_cache", "pool_result_sha256": plan["prior_pool_result_sha256"],
                          "source_key_record": previous}
        else:
            job = by_new[key_id]
            raw = job["completion"]["raw_outcome"]
            provenance = {"kind": "new_evaluation", "job_number": job["job"]["job_number"],
                          "completed_record_body_sha256": job["completion"]["body_sha256"]}
        quality = _quality_from_outcome(raw, key, tasks[key["task_id"]], raw["expression"])
        resolved[key_id] = {"key": key, "raw_evaluator_outcome": raw, "provenance": provenance, "quality": quality}
    rows = []
    for slot in submissions["slots"]:
        task_id = slot["task_id"]
        baseline_attempt = contract["states"][task_id]["baseline"]["attempt"]
        baseline_key = plan["prefix_keys"][task_id][baseline_attempt - 1]
        candidate_key = plan["slot_keys"][slot["slot_id"]]
        baseline = resolved[baseline_key]["quality"]
        candidate = core.quality(False, -1.0) if candidate_key is None else resolved[candidate_key]["quality"]
        if slot["generator"] == "copy":
            pool._exact(candidate_key, baseline_key, "copy must retain the baseline key")
            pool._exact(candidate, baseline, "copy quality must equal baseline")
        scores = core.resolve_branch(slot["adjudication"], candidate, baseline)
        rows.append({**slot, "candidate_key_id": candidate_key, "baseline_key_id": baseline_key,
                     "selected_key_id": candidate_key if slot["adjudication"]["selected_new"] else baseline_key,
                     "candidate_outcome_source": "ineligible_or_historically_unusable" if candidate_key is None
                     else resolved[candidate_key]["provenance"]["kind"], **scores})
    counts = {name: {"denominator": 40,
                     "across_new_slots_ast_duplicates": sum(slot["canonical_duplicate_across_new_slots"]
                                                            for slot in submissions["slots"] if slot["generator"] == name),
                     "prior_cache_matched_slots": sum(row["candidate_outcome_source"] == "prior_pool_cache"
                                                       for row in rows if row["generator"] == name)}
              for name in core.GENERATORS}
    return _sealed({"schema": "astra-revision-result-v1", "study": core.STUDY,
                    "status": "COMPLETE_MATCHED_PREFIX_DEVELOPMENT",
                    "contract_sha256": pool._sha(bound[PUBLIC_DIRECTORY + "/contract.json"]),
                    "submissions_sha256": pool._sha(bound[SUBMISSIONS_PATH]),
                    "assessment_request_body_sha256": request["body_sha256"],
                    "assessment_plan_body_sha256": plan["body_sha256"],
                    "publication": request["submissions_receipt"],
                    "population": {"states": 10, "hosted_calls": 80, "cheap_slots": 120, "new_slots": 200, "repetitions": 4},
                    "call_accounting": {"hosted_calls": 80, "cheap_slots": 120, "new_slots": 200,
                                         "new_feedback_calls": submissions["accounting"]["new_feedback_calls"],
                                         "new_future_calls": len(completed), "completed_new_future_calls": len(completed),
                                         "reused_future_keys": len(plan["cached_outcomes"]), "unique_future_keys": len(resolved),
                                         "collection_task_constructions": submissions["accounting"]["task_constructions"],
                                         "collection_initial_probe_checks": submissions["accounting"]["initial_probe_checks"],
                                         "assessment_task_constructions": sum(item["start"]["task_constructions"] for item in completed),
                                         "assessment_initial_probe_checks": sum(item["start"]["initial_probe_checks"] for item in completed),
                                         "automatic_retries": 0},
                    "rows": rows, "keys": list(resolved.values()), "analysis": core.analyze(rows),
                    "duplicate_and_cache_counts": counts, "provider_usage": _usage(submissions["slots"]),
                    "limits": ["Reused 2020-2024 development periods, not an untouched holdout.",
                               "One-step matched states do not establish long-horizon discovery or profitable alpha.",
                               "Fresh provider draws have unverified independence and unknown hidden context.",
                               "Initial common probes can reveal some candidate feedback indirectly.",
                               "No Astra weight training; allocation passing authorizes no automatic next study."]})


def assess_revision_study(*, source_root, publication_receipt_path, max_jobs=200,
                          task_loader=_load_task, publication_verifier=pool.verify_local_commit):
    pool._require(type(max_jobs) is int and 1 <= max_jobs <= 200, "max_jobs must be an integer in 1..200")
    root = Path(source_root).resolve()
    directory = _execution(root)
    pool._require(not (directory / "COMPLETE.json").exists() and not (root / RESULT_PATH).exists(),
                  "assessment complete; replay only")
    contract, tasks, history, bound = _verified_contract(root, verify_environment=True)
    lock = directory / ".execution-lock"
    lock.mkdir(exist_ok=False)
    attempted = False
    try:
        submissions, bound = _verified_submissions(root, contract, history, bound)
        receipt_raw, receipt = _gate(publication_receipt_path, "submissions", bound, root, publication_verifier)
        pool._require(pool._utc(receipt["verified_utc"]) >= pool._utc(submissions["last_collection_completed_utc"]),
                      "submissions publication receipt predates the complete collection")
        attempted = True
        # No old future field is parsed before the entire bank and Gate 2 proof above.
        plan = _cache_and_plan(root, contract, submissions, bound)
        if not (directory / "assessment-request.json").exists():
            pool._require(not any((directory / name).exists() for name in (
                "submissions-receipt.json", "assessment-plan.json", "assessment-jobs")), "ambiguous assessment initialization")
            request = _sealed({"study": core.STUDY, "contract_sha256": pool._sha(bound[PUBLIC_DIRECTORY + "/contract.json"]),
                               "submissions_sha256": pool._sha(bound[SUBMISSIONS_PATH]),
                               "submissions_receipt_sha256": pool._sha(receipt_raw), "submissions_receipt": receipt,
                               "created_utc": pool._now()})
            pool._write_bytes(directory / "submissions-receipt.json", receipt_raw)
            pool._write(directory / "assessment-request.json", request)
            pool._write(directory / "assessment-plan.json", plan)
            (directory / "assessment-jobs").mkdir()
        else:
            request = _assessment_request(root, contract, bound)
            pool._require((directory / "submissions-receipt.json").read_bytes() == receipt_raw, "assessment receipt changed")
            pool._exact(pool._read((directory / "assessment-plan.json").read_bytes()), plan, "assessment job/cache plan")
        completed = _assessment_prefix(directory, request, plan, tasks)
        command_start = len(completed) + 1
        task_cache = {}
        key_map = {key["key_id"]: key for key in plan["keys"]}
        for job in plan["jobs"][len(completed):len(completed) + max_jobs]:
            _assert_bound(root, bound, contract)
            pool._require(Path(publication_receipt_path).read_bytes() == receipt_raw, "publication receipt changed")
            _receipt(receipt_raw, "submissions", bound)
            path = directory / "assessment-jobs" / f"{job['job_number']:03d}"
            path.mkdir(exist_ok=False)
            setup = int(job["task_id"] not in task_cache)
            start = _sealed({"job": job, "assessment_request_body_sha256": request["body_sha256"],
                             "previous_body_sha256": completed[-1]["completion"]["body_sha256"]
                             if completed else request["body_sha256"], "created_utc": pool._now(),
                             "command_start_job_number": command_start,
                             "task_constructions": setup, "initial_probe_checks": 2 * setup})
            pool._write(path / "STARTED.json", start)
            if setup:
                task_cache[job["task_id"]] = _task(task_loader, root, contract, tasks, job["task_id"])
            raw = task_cache[job["task_id"]].evaluate(job["expression"])
            try:
                quality = _quality_from_outcome(raw, key_map[job["key_id"]], tasks[job["task_id"]], job["expression"])
            except BaseException:
                # Retain a JSON-safe unexpected outcome privately when possible.
                private = root / TRANSPORT_DIRECTORY / "assessment-failures"
                private.mkdir(parents=True, exist_ok=True)
                try:
                    pool._write(private / f"{job['job_number']:03d}.json", {"raw_outcome": raw})
                except (ValueError, TypeError):
                    pool._write(private / f"{job['job_number']:03d}-type.json", {"raw_type": type(raw).__name__})
                raise
            end = _sealed({"started_body_sha256": start["body_sha256"], "completed_utc": pool._now(),
                           "raw_outcome": raw, "quality": quality})
            pool._write(path / "COMPLETED.json", end)
            completed.append({"job": job, "start": start, "completion": end})
        if len(completed) != len(plan["jobs"]):
            return {"status": "CLEAN_COMPLETED_ASSESSMENT_PREFIX", "completed_new_future_calls": len(completed),
                    "total_new_future_calls": len(plan["jobs"])}
        result = _report(root, contract, tasks, submissions, bound, request, plan, completed)
        pool._write(directory / "COMPLETE.json", result)
        pool._write(root / RESULT_PATH, result)
        return result
    except BaseException as error:
        if attempted:
            _incomplete(directory, "assessment-failure", error)
        raise
    finally:
        lock.rmdir()


def _validate_report(saved, expected):
    pool._keys(saved, set(expected), "complete revision report")
    retained = set(expected) - {"body_sha256", "analysis", "rows"}
    pool._exact({name: saved[name] for name in retained}, {name: expected[name] for name in retained},
                "retained report evidence/provenance")
    pool._require(type(saved["rows"]) is list and len(saved["rows"]) == 200, "report must contain all 200 rows")
    computed = {"candidate_Q", "selected_Q", "baseline_Q", "G", "terminal_utility", "baseline_utility", "incremental_net_gain"}
    for actual, wanted in zip(saved["rows"], expected["rows"], strict=True):
        pool._keys(actual, set(wanted), "resolved report row")
        pool._exact({name: actual[name] for name in actual if name not in computed},
                    {name: wanted[name] for name in wanted if name not in computed}, "retained slot/cost/provenance")
        for name in computed:
            pool._arithmetic(actual[name], wanted[name], "resolved " + name)
    pool._arithmetic(saved["analysis"], expected["analysis"], "computed analysis")


def replay_revision_study(*, source_root, report_path=None):
    """Saved public evidence only; no environment/data/provider/scorer operations."""
    root = Path(source_root).resolve()
    contract, tasks, history, bound = _verified_contract(root)
    directory = _execution(root)
    pool._require(not (directory / ".execution-lock").exists(), "an execution lock remains")
    submissions, bound = _verified_submissions(root, contract, history, bound)
    request = _assessment_request(root, contract, bound)  # Saved Gate 2 proof precedes every cache parse.
    plan = _cache_and_plan(root, contract, submissions, bound)
    pool._exact(pool._read((directory / "assessment-plan.json").read_bytes()), plan, "saved assessment plan")
    completed = _assessment_prefix(directory, request, plan, tasks)
    expected = _report(root, contract, tasks, submissions, bound, request, plan, completed)
    raw = (directory / "COMPLETE.json").read_bytes()
    saved = pool._read(raw)
    _validate_report(saved, expected)
    report = root / RESULT_PATH if report_path is None else Path(report_path)
    pool._require(report.read_bytes() == raw, "public report bytes differ from retained completion")
    return _sealed({"schema": "astra-revision-replay-v1", "study": core.STUDY, "status": "SAVED_REVISION_VERIFIED",
                    "contract_sha256": expected["contract_sha256"], "submissions_sha256": expected["submissions_sha256"],
                    "report_sha256": pool._sha(raw), "state_count": 10, "slot_count": 200,
                    "hosted_calls": 80, "cheap_slots": 120, "repetitions": 4,
                    "new_future_calls": len(completed), "completed_new_future_calls": len(completed),
                    "reused_future_keys": len(plan["cached_outcomes"]), "unique_future_keys": len(plan["keys"]),
                    "new_model_calls": 0, "new_financial_scores": 0, "raw_market_data_reads": 0,
                    "installed_runtime_revalidated": False})


def stop_revision_study(*, source_root, reason):
    pool._require(type(reason) is str and reason, "a stop reason is required")
    root = Path(source_root).resolve()
    _verified_contract(root)
    directory = _execution(root)
    pool._require(not (directory / "COMPLETE.json").exists(), "completed study is replay-only")
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / ".execution-lock"
    lock.mkdir(exist_ok=False)
    try:
        _incomplete(directory, "explicit-root-stop", reason=reason)
        return {"status": "INCOMPLETE", "reason": reason, "new_calls": 0}
    finally:
        lock.rmdir()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("prepare")
    publish = commands.add_parser("publication-files")
    publish.add_argument("--stage", required=True, choices=("preparation", "submissions"))
    collect = commands.add_parser("collect-pair")
    collect.add_argument("--task", required=True, choices=core.TASK_IDS)
    collect.add_argument("--repetition", required=True, type=int, choices=core.REPETITIONS)
    collect.add_argument("--receipt", type=Path, required=True)
    collect.add_argument("--quota-remaining", type=float)
    collect.add_argument("--quota-checked-utc")
    collect.add_argument("--quota-provenance", required=True)
    commands.add_parser("freeze")
    assess = commands.add_parser("assess")
    assess.add_argument("--receipt", type=Path, required=True)
    assess.add_argument("--max-jobs", type=int, default=200)
    replay = commands.add_parser("replay")
    replay.add_argument("--report", type=Path)
    stop = commands.add_parser("stop")
    stop.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    common = {"source_root": args.source_root}
    if args.command == "prepare":
        value = prepare_revision_study(**common)
    elif args.command == "publication-files":
        value = publication_files(**common, stage=args.stage)
    elif args.command == "collect-pair":
        value = collect_pair(args.task, args.repetition, **common, publication_receipt_path=args.receipt,
                             quota={"remaining_percent": args.quota_remaining, "checked_utc": args.quota_checked_utc,
                                    "provenance": args.quota_provenance})
    elif args.command == "freeze":
        value = freeze_revision_study(**common)
    elif args.command == "assess":
        value = assess_revision_study(**common, publication_receipt_path=args.receipt, max_jobs=args.max_jobs)
    elif args.command == "replay":
        value = replay_revision_study(**common, report_path=args.report)
    else:
        value = stop_revision_study(**common, reason=args.reason)
    print(canonical_json(value))


if __name__ == "__main__":
    main()
