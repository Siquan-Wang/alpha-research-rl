"""Durable, one-round-at-a-time Astra development study orchestration.

The collecting process only obtains feedback. A separate command verifies all
180 frozen submissions before calling the existing chronological evaluator.
Root checks the shared allowance before each explicitly requested round.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

from .agentic_research import (
    ACTOR_INSTRUCTIONS,
    ARMS,
    PROPOSAL_BUDGET,
    ResearchEpisode,
    canonical_json,
    digest,
)

TASK_IDS = tuple(f"{year}-H{half}" for year in range(2020, 2025) for half in (1, 2))
ROUND_ORDER = tuple((task_id, attempt) for task_id in TASK_IDS for attempt in range(1, 7))
PUBLIC_CONTRACT = Path("artifacts/astra-agent-v1/contract.json")
PUBLIC_SUBMISSIONS = Path("results/astra_agent_v1_submissions.json")
SOURCE_FILES = (
    "astra_study.py", "agentic_research.py", "codex_actor.py", "financial_policy.py",
    "financial_tasks.py", "dsl.py", "evaluation.py", "data.py", "french.py",
    "artifacts.py", "real_baselines.py", "llm.py",
)
MODEL_SETTINGS = {
    "model": "gpt-6-astra", "reasoning_effort": "ultra", "service_tier": "default",
    "sandbox": "read-only", "ephemeral": True, "timeout_seconds": 600,
    "maximum_concurrency": 3, "infrastructure_retries": 0,
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _sha(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())


def _write(path: Path, value: dict) -> None:
    _write_text(path, canonical_json(value) + "\n")


def _sealed(body: dict) -> dict:
    if "body_sha256" in body:
        raise ValueError("body already contains a digest")
    return {**body, "body_sha256": digest(body)}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate artifact key")
        result[key] = value
    return result


def _read(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    canonical_json(result)
    if not isinstance(result, dict):
        raise TypeError("artifact must be an object")
    return result


def _read_sealed(path: Path) -> dict:
    value = _read(path)
    body = {key: item for key, item in value.items() if key != "body_sha256"}
    if value.get("body_sha256") != digest(body):
        raise ValueError(f"artifact digest mismatch: {path.name}")
    return value


def _sources(root: Path) -> dict:
    return {f"src/alpha_research_rl/{name}": _sha(root / "src" / "alpha_research_rl" / name)
            for name in SOURCE_FILES}


def _interface() -> dict:
    from .codex_actor import CLI_VERSION_CONTRACT, RESPONSE_SCHEMA

    return {"actor_instructions_sha256": hashlib.sha256(ACTOR_INSTRUCTIONS.encode("utf-8")).hexdigest(),
            "response_schema_sha256": digest(RESPONSE_SCHEMA), "cli_version_contract": CLI_VERSION_CONTRACT}


def _versions() -> dict:
    return {"python": platform.python_version(),
            **{name: importlib.metadata.version(name) for name in ("numpy", "pandas", "scipy")}}


def executable_identity() -> dict:
    """Read the resolved binary/version without starting an actor or reading auth."""
    executable = shutil.which("codex")
    if executable is None:
        raise FileNotFoundError("the existing Codex executable was not found")
    path = Path(executable).resolve()
    completed = subprocess.run([str(path), "--version"], capture_output=True, check=True, timeout=30)
    version = completed.stdout.decode("utf-8").strip()
    expected = f"codex-cli {_interface()['cli_version_contract']}"
    if version != expected:
        raise ValueError("installed CLI version differs from the frozen provider contract")
    return {"path": str(path), "identity": {"executable_name": path.name,
                                            "sha256": _sha(path), "version": version}}


def load_tasks(data_path: Path, task_ids: tuple[str, ...]):
    """Use the pinned local snapshot; do not download data or score assessment."""
    from .financial_policy import load_pinned_panel
    from .financial_tasks import make_task

    panel = load_pinned_panel(data_path)
    return tuple(make_task(panel, int(task_id[:4]), int(task_id[-1])) for task_id in task_ids)


def _tasks(loader, data_path: Path, task_ids: tuple[str, ...]) -> dict:
    tasks = tuple(loader(data_path, task_ids))
    if tuple(task.public_manifest["task_id"] for task in tasks) != task_ids:
        raise ValueError("task loader changed the registered task order or membership")
    return dict(zip(task_ids, tasks, strict=True))


def verify_committed_files(root: Path, commit: str, paths: tuple[Path, ...]) -> dict:
    """Check local Git bytes. Root separately verifies the commit was published."""
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("a complete lowercase contract commit is required")
    for path in paths:
        relative = _relative(path, root)
        completed = subprocess.run(
            ["git", "-c", f"safe.directory={root.resolve().as_posix()}",
             "show", f"{commit}:{relative}"], cwd=root, capture_output=True, check=True,
        )
        if completed.stdout != path.read_bytes():
            raise ValueError(f"artifact differs from the named committed bytes: {relative}")
    return {"commit": commit, "local_committed_bytes_verified": True,
            "remote_publication_verification": "root responsibility; not checked by this function"}


def prepare_study(study_dir: Path, data_path: Path, plan_path: Path, *, root: Path,
                  task_loader=load_tasks, executable_probe=executable_identity) -> dict:
    """Freeze ten development tasks and input identities before any actor call."""
    for path in (study_dir, data_path, plan_path):
        _relative(path, root)
    if study_dir.exists() or (root / PUBLIC_CONTRACT).exists():
        raise FileExistsError("study directory already exists; never replace an attempt")
    identities = _sources(root)
    data_identity = {"path": _relative(data_path, root), "sha256": _sha(data_path)}
    plan_identity = {"path": _relative(plan_path, root), "sha256": _sha(plan_path)}
    study_dir.mkdir(parents=True, exist_ok=False)
    try:
        (study_dir / "actor-context").mkdir()
        executable = executable_probe()
        _write(study_dir / "cli-runtime.json", executable)
        tasks = _tasks(task_loader, data_path, TASK_IDS)
        task_files = {}
        for task_id, task in tasks.items():
            observation = task.observation()
            ResearchEpisode(ARMS[0], observation, task.feedback_score)
            task_record = _sealed({
                "task_id": task_id, "interpretation": "previously examined chronological DEVELOPMENT",
                "financial_manifest": task.public_manifest, "initial_observation": observation,
            })
            path = study_dir / "tasks" / f"{task_id}.json"
            _write(path, task_record)
            task_files[task_id] = _sha(path)
        body = {
            "study": "astra-agent-research-v1", "created_utc": _now(),
            "task_order": list(TASK_IDS), "arms": list(ARMS), "attempts_per_episode": PROPOSAL_BUDGET,
            "round_order": [[task_id, attempt] for task_id, attempt in ROUND_ORDER],
            "data": data_identity, "plan": plan_identity, "source_sha256": identities,
            "task_manifest_sha256": task_files, "model_settings": MODEL_SETTINGS.copy(),
            "interface": _interface(), "runtime_versions": _versions(),
            "cli_identity": executable["identity"],
            "actor_context_relative_to_study": "actor-context",
            "initial_prompt_sha256": {task_id: hashlib.sha256(ResearchEpisode(
                ARMS[0], tasks[task_id].observation(), tasks[task_id].feedback_score,
            ).prompt().encode("utf-8")).hexdigest() for task_id in TASK_IDS},
            "assessment_score_calls": 0, "quota_stop_remaining_percent": 5,
            "assessment_gate": "all 30 six-attempt episodes frozen; separate assess command",
        }
        if _sources(root) != identities or _sha(data_path) != data_identity["sha256"]:
            raise ValueError("inputs changed while preparing the study")
        if _sha(plan_path) != plan_identity["sha256"]:
            raise ValueError("plan changed while preparing the study")
        contract = _sealed(body)
        _write(study_dir / "contract.json", contract)
        _write(root / PUBLIC_CONTRACT, contract)
        return contract
    except Exception as error:
        _write(study_dir / "INCOMPLETE.json", {"stage": "prepare", "error_type": type(error).__name__,
                                               "error": str(error), "created_utc": _now()})
        raise


def _verify_contract(study_dir: Path, root: Path) -> dict:
    _relative(study_dir, root)
    if (study_dir / "INCOMPLETE.json").exists():
        raise ValueError("study is INCOMPLETE; no retry or further scoring is permitted")
    contract = _read_sealed(study_dir / "contract.json")
    if (study_dir / "contract.json").read_bytes() != (root / PUBLIC_CONTRACT).read_bytes():
        raise ValueError("local contract differs from its public counterpart")
    if (contract["task_order"] != list(TASK_IDS) or contract["arms"] != list(ARMS)
            or contract["attempts_per_episode"] != PROPOSAL_BUDGET
            or contract["round_order"] != [list(item) for item in ROUND_ORDER]
            or contract["model_settings"] != MODEL_SETTINGS
            or contract["actor_context_relative_to_study"] != "actor-context"):
        raise ValueError("contract differs from the registered study interface")
    if contract["source_sha256"] != _sources(root):
        raise ValueError("source changed after preparation")
    if contract["interface"] != _interface() or contract["runtime_versions"] != _versions():
        raise ValueError("runtime/interface changed after preparation")
    for name in ("data", "plan"):
        path = root / contract[name]["path"]
        _relative(path, root)
        if _sha(path) != contract[name]["sha256"]:
            raise ValueError(f"{name} changed after preparation")
    if set(contract["task_manifest_sha256"]) != set(TASK_IDS):
        raise ValueError("task manifest membership changed")
    for task_id in TASK_IDS:
        path = study_dir / "tasks" / f"{task_id}.json"
        if _sha(path) != contract["task_manifest_sha256"][task_id]:
            raise ValueError("frozen task manifest changed")
        if _read_sealed(path)["task_id"] != task_id:
            raise ValueError("frozen task identity changed")
    return contract


def _publication_paths(study_dir: Path, root: Path, contract: dict, *, include_freeze=False) -> tuple[Path, ...]:
    paths = [root / contract["plan"]["path"], root / PUBLIC_CONTRACT]
    paths.extend(root / name for name in contract["source_sha256"])
    if include_freeze:
        paths.append(root / PUBLIC_SUBMISSIONS)
    return tuple(paths)


def _tree(path: Path, exclude=()) -> dict:
    result = {}
    for child in sorted(path.rglob("*")):
        if child.is_symlink():
            raise ValueError("study evidence must not contain symlinks")
        if child.is_file():
            relative = _relative(child, path)
            if relative not in exclude:
                result[relative] = _sha(child)
    return result


def _round_path(study_dir: Path, task_id: str, attempt: int) -> Path:
    return study_dir / "rounds" / task_id / f"{attempt:02d}"


def _completed_rounds(study_dir: Path) -> list[dict]:
    completed = []
    missing = False
    for task_id, attempt in ROUND_ORDER:
        path = _round_path(study_dir, task_id, attempt)
        if not path.exists():
            missing = True
            continue
        if missing:
            raise ValueError("rounds contain a gap or violate the fixed task order")
        record = _read_sealed(path / "round.json")
        if (record["task_id"] != task_id or record["attempt"] != attempt
                or record["status"] != "COMPLETE" or set(record["arms"]) != set(ARMS)
                or any(value != "COMPLETE" for value in record["arms"].values())):
            raise ValueError("a round is incomplete or has changed identity")
        if record["artifact_sha256"] != _tree(path, exclude=("round.json",)):
            raise ValueError("round evidence differs from its durable hashes")
        completed.append(record)
    return completed


def _episode(study_dir: Path, task, task_id: str, arm: str, count: int) -> ResearchEpisode:
    frozen_task = _read_sealed(study_dir / "tasks" / f"{task_id}.json")
    if (canonical_json(task.public_manifest) != canonical_json(frozen_task["financial_manifest"])
            or canonical_json(task.observation()) != canonical_json(frozen_task["initial_observation"])):
        raise ValueError("current task/probe evidence differs from preparation")
    episode = ResearchEpisode(arm, frozen_task["initial_observation"], task.feedback_score)
    for attempt in range(1, count + 1):
        path = _round_path(study_dir, task_id, attempt) / "arms" / arm
        if (path / "prompt.txt").read_bytes().decode("utf-8") != episode.prompt():
            raise ValueError("replayed prompt differs from the exact saved prompt")
        result = _read(path / "actor-result.json")
        raw = (path / "response.txt").read_bytes().decode("utf-8")
        if result["success"] is not True or result["final_text"] != raw:
            raise ValueError("prior provider response is inconsistent")
        episode.submit(raw)
        if canonical_json(episode.checkpoint()) != canonical_json(_read_sealed(path / "checkpoint.json")):
            raise ValueError("feedback replay differs from a prior frozen checkpoint")
    return episode


def _json_value(value):
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    return value


def _run_arm(episode: ResearchEpisode, path: Path, actor_runner, timeout_seconds: int,
             executable: str, neutral_cwd: Path) -> str:
    path.mkdir(parents=True, exist_ok=False)
    prompt = episode.prompt()
    _write_text(path / "prompt.txt", prompt)
    status = "INCOMPLETE"
    try:
        result = actor_runner(prompt, path / "provider", timeout_seconds=timeout_seconds,
                              cwd=neutral_cwd, executable=executable)
        summary = getattr(result, "public_summary", None)
        summary = summary() if callable(summary) else summary
        provider = _json_value({
            "success": result.success, "error": result.error, "final_text": result.final_text,
            "usage": result.usage, "artifact_paths": result.artifact_paths, "public_summary": summary,
        })
        _write(path / "actor-result.json", provider)
        if isinstance(result.final_text, str):
            _write_text(path / "response.txt", result.final_text)
        if result.success is not True or not isinstance(result.final_text, str):
            episode.failed = True
            raise RuntimeError("provider attempt failed; the study must stop without retry")
        episode.submit(result.final_text)
        status = "COMPLETE"
    except Exception as error:  # noqa: BLE001 - retain every failed actor/broker attempt; never retry.
        episode.failed = True
        _write(path / "failure.json", {"stage": "actor-or-broker", "error_type": type(error).__name__,
                                       "error": str(error), "created_utc": _now()})
    finally:
        _write(path / "checkpoint.json", episode.checkpoint())
    return status


def collect_round(study_dir: Path, task_id: str, attempt: int, *, root: Path, contract_commit: str,
                  quota_remaining_percent: float, task_loader=load_tasks, actor_runner=None,
                  publication_verifier=verify_committed_files, executable_probe=executable_identity) -> dict:
    """Launch at most three calls, for one registered task and proposal ordinal."""
    if (type(quota_remaining_percent) not in (int, float) or not math.isfinite(quota_remaining_percent)
            or not 0 <= quota_remaining_percent <= 100):
        raise ValueError("root must report a fresh verified shared quota reading")
    if quota_remaining_percent <= 5:
        stop_collection(study_dir, root=root, reason="registered quota threshold reached",
                        quota_remaining_percent=quota_remaining_percent)
        raise ValueError("quota stop: no new actor call is permitted at or below 5% remaining")
    contract = _verify_contract(study_dir, root)
    if (study_dir / "submissions.json").exists():
        raise FileExistsError("all submissions are already frozen")
    completed = _completed_rounds(study_dir)
    if len(completed) >= len(ROUND_ORDER) or (task_id, attempt) != ROUND_ORDER[len(completed)]:
        raise ValueError("request is not the next registered task/attempt; rounds cannot be rerun")
    publication = publication_verifier(root, contract_commit, _publication_paths(study_dir, root, contract))
    executable = executable_probe()
    if executable["identity"] != contract["cli_identity"]:
        raise ValueError("CLI executable/version changed after preparation")
    neutral_cwd = study_dir / contract["actor_context_relative_to_study"]
    if not neutral_cwd.is_dir() or neutral_cwd.is_symlink():
        raise ValueError("the registered neutral actor context is unavailable")
    task = _tasks(task_loader, root / contract["data"]["path"], (task_id,))[task_id]
    episodes = {arm: _episode(study_dir, task, task_id, arm, attempt - 1) for arm in ARMS}
    if any(len(episode.records) != attempt - 1 for episode in episodes.values()):
        raise ValueError("all arms must have exactly the same prior attempt count")
    if actor_runner is None:
        from .codex_actor import run_actor
        actor_runner = run_actor
    path = _round_path(study_dir, task_id, attempt)
    path.mkdir(parents=True, exist_ok=False)
    offset = (TASK_IDS.index(task_id) + attempt - 1) % 3
    launch_order = ARMS[offset:] + ARMS[:offset]
    _write(path / "request.json", _sealed({
        "task_id": task_id, "attempt": attempt, "created_utc": _now(),
        "contract_sha256": _sha(study_dir / "contract.json"), "publication": publication,
        "root_reported_quota_remaining_percent": quota_remaining_percent,
        "maximum_actor_calls": 3, "timeout_seconds": MODEL_SETTINGS["timeout_seconds"],
        "launch_order": list(launch_order),
        "cli_identity": executable["identity"],
    }))
    statuses = {}
    try:
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(_run_arm, episodes[arm], path / "arms" / arm,
                                       actor_runner, MODEL_SETTINGS["timeout_seconds"], executable["path"],
                                       neutral_cwd): arm
                       for arm in launch_order}
            for future in as_completed(futures):
                arm = futures[future]
                try:
                    statuses[arm] = future.result()
                except Exception as error:  # noqa: BLE001 - preserve sibling results after a worker failure.
                    statuses[arm] = "INCOMPLETE"
                    _write(path / f"{arm}-worker-failure.json", {
                        "error_type": type(error).__name__, "error": str(error), "created_utc": _now(),
                    })
    except BaseException as error:
        # Executor shutdown joins already-launched workers; their own artifacts
        # remain available even when no complete round summary can be produced.
        _write(study_dir / "INCOMPLETE.json", {
            "stage": "collection-interrupted", "task_id": task_id, "attempt": attempt,
            "error_type": type(error).__name__, "created_utc": _now(), "retries": 0,
        })
        raise
    status = "COMPLETE" if all(statuses[arm] == "COMPLETE" for arm in ARMS) else "INCOMPLETE"
    report = _sealed({"task_id": task_id, "attempt": attempt, "status": status,
                      "arms": {arm: statuses[arm] for arm in ARMS}, "completed_utc": _now(),
                      "artifact_sha256": _tree(path), "assessment_score_calls": 0})
    _write(path / "round.json", report)
    if status != "COMPLETE":
        _write(study_dir / "INCOMPLETE.json", {"stage": "collect", "task_id": task_id,
                                               "attempt": attempt, "round_sha256": _sha(path / "round.json"),
                                               "created_utc": _now(), "retries": 0})
    return report


def stop_collection(study_dir: Path, *, root: Path, reason: str,
                    quota_remaining_percent: float | None = None) -> dict:
    """Root may stop conservatively without launching or replacing any actor."""
    _verify_contract(study_dir, root)
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("an explicit stop reason is required")
    completed = _completed_rounds(study_dir)
    if len(completed) == 60:
        return {"status": "ALL_ROUNDS_COMPLETE", "assessment_score_calls": 0}
    report = {"stage": "collection-stop", "status": "INCOMPLETE", "reason": reason,
              "completed_round_count": len(completed), "created_utc": _now(),
              "root_reported_quota_remaining_percent": quota_remaining_percent,
              "assessment_score_calls": 0}
    _write(study_dir / "INCOMPLETE.json", report)
    return report


def _all_episodes(study_dir: Path, root: Path, contract: dict, task_loader) -> tuple[dict, list[dict]]:
    completed = _completed_rounds(study_dir)
    if len(completed) != 60:
        raise ValueError("all 60 three-arm rounds must complete before a freeze or assessment")
    tasks = _tasks(task_loader, root / contract["data"]["path"], TASK_IDS)
    episodes = []
    for task_id in TASK_IDS:
        for arm in ARMS:
            episode = _episode(study_dir, tasks[task_id], task_id, arm, PROPOSAL_BUDGET)
            transports = [_read(_round_path(study_dir, task_id, attempt) / "arms" / arm /
                                "actor-result.json")["public_summary"] for attempt in range(1, 7)]
            episodes.append({"task_id": task_id, "arm": arm, "submission": episode.freeze(),
                             "transport_summaries": transports})
    if len(episodes) != 30 or sum(item["submission"]["attempt_count"] for item in episodes) != 180:
        raise ValueError("the fixed 30-episode/180-response denominator changed")
    return tasks, episodes


def freeze_study(study_dir: Path, *, root: Path, task_loader=load_tasks) -> dict:
    if (study_dir / "submissions.json").exists() or (root / PUBLIC_SUBMISSIONS).exists():
        raise FileExistsError("submissions already frozen")
    contract = _verify_contract(study_dir, root)
    _, episodes = _all_episodes(study_dir, root, contract, task_loader)
    report = _sealed({
        "study": "astra-agent-research-v1", "stage": "all-submissions-frozen", "frozen_utc": _now(),
        "contract_sha256": _sha(study_dir / "contract.json"), "episode_count": 30,
        "completed_response_count": 180, "assessment_score_calls": 0, "episodes": episodes,
        "round_sha256": {f"{task_id}/{attempt:02d}": _sha(_round_path(study_dir, task_id, attempt) / "round.json")
                         for task_id, attempt in ROUND_ORDER},
    })
    _write(study_dir / "submissions.json", report)
    _write(root / PUBLIC_SUBMISSIONS, report)
    return report


def assess_study(study_dir: Path, *, root: Path, published_commit: str, task_loader=load_tasks,
                 publication_verifier=verify_committed_files) -> dict:
    """Score only the 30 previously frozen selections; import/call no actor."""
    contract = _verify_contract(study_dir, root)
    frozen = _read_sealed(study_dir / "submissions.json")
    if (study_dir / "submissions.json").read_bytes() != (root / PUBLIC_SUBMISSIONS).read_bytes():
        raise ValueError("local submissions differ from their public counterpart")
    if (frozen["stage"] != "all-submissions-frozen" or frozen["episode_count"] != 30
            or frozen["completed_response_count"] != 180 or frozen["assessment_score_calls"] != 0
            or frozen["contract_sha256"] != _sha(study_dir / "contract.json")):
        raise ValueError("submission freeze is incomplete or belongs to another contract")
    publication = publication_verifier(
        root, published_commit, _publication_paths(study_dir, root, contract, include_freeze=True),
    )
    tasks, episodes = _all_episodes(study_dir, root, contract, task_loader)
    rounds = {f"{task_id}/{attempt:02d}": _sha(_round_path(study_dir, task_id, attempt) / "round.json")
              for task_id, attempt in ROUND_ORDER}
    if canonical_json(episodes) != canonical_json(frozen["episodes"]) or rounds != frozen["round_sha256"]:
        raise ValueError("current submissions/evidence differ from the pre-assessment freeze")
    output = study_dir / "assessment"
    output.mkdir(exist_ok=False)
    _write(output / "request.json", _sealed({"created_utc": _now(), "publication": publication,
                                             "submissions_sha256": _sha(study_dir / "submissions.json")}))
    results = []
    try:
        for item in frozen["episodes"]:
            selection = item["submission"]["selection"]
            if selection is None:
                outcome = {"status": "invalid", "reason": "all_proposals_invalid_or_unusable",
                           "reward": -1.06, "cost": 0.06, "oriented_future_ic": None,
                           "assessment_evaluator_called": False}
            else:
                outcome = dict(tasks[item["task_id"]].evaluate(selection["expression"]))
                if outcome.get("orientation") != selection["orientation"]:
                    raise ValueError("assessment orientation differs from feedback-frozen selection")
                if outcome.get("status") not in ("ok", "invalid", "unscorable"):
                    raise ValueError("unexpected assessment status")
                original_reward = outcome.get("reward")
                if type(original_reward) not in (int, float) or not math.isfinite(original_reward):
                    raise ValueError("assessment reward must be finite")
                if outcome.get("status") == "ok":
                    ic = outcome.get("oriented_future_ic")
                    if type(ic) not in (int, float) or not math.isfinite(ic) or not -1 <= ic <= 1:
                        raise ValueError("assessment produced an invalid IC")
                    if not math.isclose(original_reward, ic - 0.01, rel_tol=0, abs_tol=1e-12):
                        raise ValueError("one-proposal evaluator reward differs from its frozen rule")
                else:
                    if not math.isclose(original_reward, -1.01, rel_tol=0, abs_tol=1e-12):
                        raise ValueError("one-proposal invalid reward differs from its frozen rule")
                outcome.update(reward=original_reward - 0.05, cost=0.06,
                               one_proposal_reward=original_reward, assessment_evaluator_called=True)
            record = {"task_id": item["task_id"], "arm": item["arm"], "outcome": outcome}
            _write(output / f"{item['task_id']}-{item['arm']}.json", _sealed(record))
            results.append(record)
        if len(results) != 30:
            raise ValueError("assessment denominator must remain exactly 30 episodes")
        values = {(item["task_id"], item["arm"]): item["outcome"]["reward"] for item in results}
        paired = [{"task_id": task_id,
                   "full_minus_validity": values[task_id, ARMS[0]] - values[task_id, ARMS[1]],
                   "full_minus_withheld": values[task_id, ARMS[0]] - values[task_id, ARMS[2]],
                   "validity_minus_withheld": values[task_id, ARMS[1]] - values[task_id, ARMS[2]]}
                  for task_id in TASK_IDS]
        summaries = {}
        for arm in ARMS:
            rows = [item["outcome"] for item in results if item["arm"] == arm]
            valid = [row for row in rows if row["status"] == "ok"]
            p = len(valid) / 10
            q = math.fsum(row["oriented_future_ic"] for row in valid) / 10
            mean = math.fsum(row["reward"] for row in rows) / 10
            if not math.isclose(mean, -1.06 + p + q, rel_tol=0, abs_tol=1e-12):
                raise ValueError("utility decomposition failed")
            summaries[arm] = {"task_count": 10, "valid_assessment_count": len(valid),
                              "validity_fraction_p": p, "predictive_contribution_q": q,
                              "mean_utility": mean, "conditional_valid_mean_ic": q / p if p else None}
        contrasts = {}
        for name, left, right in (("full_minus_validity", ARMS[0], ARMS[1]),
                                  ("full_minus_withheld", ARMS[0], ARMS[2]),
                                  ("validity_minus_withheld", ARMS[1], ARMS[2])):
            contrasts[name] = {"mean_utility_difference": math.fsum(row[name] for row in paired) / 10,
                               "validity_contribution": summaries[left]["validity_fraction_p"] -
                               summaries[right]["validity_fraction_p"],
                               "predictive_contribution": summaries[left]["predictive_contribution_q"] -
                               summaries[right]["predictive_contribution_q"]}
        years = [{"year": year, **{name: math.fsum(row[name] for row in paired
                                                   if row["task_id"].startswith(str(year))) / 2
                                   for name in contrasts}} for year in range(2020, 2025)]
        report = _sealed({"study": "astra-agent-research-v1", "stage": "development-assessment-complete",
                          "episode_count": 30, "paired_task_count": 10, "results": results,
                          "paired": paired, "primary_mean_full_minus_validity": math.fsum(
                              row["full_minus_validity"] for row in paired) / 10,
                          "arm_summaries": summaries, "contrasts": contrasts, "year_averages": years,
                          "submissions_sha256": _sha(study_dir / "submissions.json"),
                          "interpretation": "descriptive development; no untouched holdout or profitability claim"})
        _write(output / "results.json", report)
        return report
    except Exception as error:
        failure = {"stage": "assessment", "completed_outcome_count": len(results),
                   "error_type": type(error).__name__, "error": str(error), "created_utc": _now()}
        _write(output / "failure.json", failure)
        _write(study_dir / "INCOMPLETE.json", failure)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--study-dir", type=Path, required=True)
    prepare.add_argument("--data", type=Path, required=True)
    prepare.add_argument("--plan", type=Path, required=True)
    collect = commands.add_parser("collect-round")
    collect.add_argument("--study-dir", type=Path, required=True)
    collect.add_argument("--task", choices=TASK_IDS, required=True)
    collect.add_argument("--attempt", type=int, choices=range(1, 7), required=True)
    collect.add_argument("--contract-commit", required=True)
    collect.add_argument("--quota-remaining-percent", type=float, required=True)
    freeze = commands.add_parser("freeze")
    freeze.add_argument("--study-dir", type=Path, required=True)
    assess = commands.add_parser("assess")
    assess.add_argument("--study-dir", type=Path, required=True)
    assess.add_argument("--published-commit", required=True)
    stop = commands.add_parser("stop")
    stop.add_argument("--study-dir", type=Path, required=True)
    stop.add_argument("--reason", required=True)
    stop.add_argument("--quota-remaining-percent", type=float)
    args = parser.parse_args()
    root = Path.cwd()
    if args.command == "prepare":
        result = prepare_study(args.study_dir, args.data, args.plan, root=root)
    elif args.command == "collect-round":
        result = collect_round(args.study_dir, args.task, args.attempt, root=root,
                               contract_commit=args.contract_commit,
                               quota_remaining_percent=args.quota_remaining_percent)
    elif args.command == "freeze":
        result = freeze_study(args.study_dir, root=root)
    elif args.command == "stop":
        result = stop_collection(args.study_dir, root=root, reason=args.reason,
                                 quota_remaining_percent=args.quota_remaining_percent)
    else:
        result = assess_study(args.study_dir, root=root, published_commit=args.published_commit)
    print(canonical_json({"command": args.command, "body_sha256": result.get("body_sha256"),
                          "status": result.get("status", result.get("stage", "PREPARED"))}))


if __name__ == "__main__":
    main()
