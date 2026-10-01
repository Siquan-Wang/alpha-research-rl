"""Root-operated staged development gate. No automatic scientific retries."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
REPO = BASE.parent
RUN = BASE / "adaptivity-decoder-dev-v1"
COORDS = BASE / "adaptivity-dev-coordinates-v1.json"
COORDS_SHA = "1555c66e856f1451dbf151bb1aafe48474cae2fe1885f9cf37762d966e26211d"
BOUND_FILES = [".local/adaptivity-dev-coordinates-v1.json", ".local/adaptivity-metadata-order-v1.json",
    ".local/newton-adapter-metadata-v1.json", ".local/adaptivity-decoder-dev-plan-v1.md",
    ".local/adaptivity_adapter_contract.py", ".local/newton_scalar_worker_v1.py",
    ".local/adaptivity_dev_prompts_v1.py", ".local/newtonbench-source-912a4ba/manifest.json",
    ".local/run_adaptivity_decoder_dev_v1.py", ".local/score_adaptivity_decoder_dev_v1.py",
    "src/alpha_research_rl/codex_actor.py"]
sys.path.insert(0, str(REPO / "src"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_new(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as file:
        file.write(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n")
        file.flush()
        import os
        os.fsync(file.fileno())


def verify():
    binding = read(RUN / "binding.json")
    if (type(binding) is not dict or set(binding.get("files", {})) != set(BOUND_FILES)
            or digest(COORDS) != COORDS_SHA):
        raise ValueError("incomplete binding or wrong coordinate identity")
    for rel, sha in binding["files"].items():
        if digest(REPO / rel) != sha:
            raise ValueError("bound file changed: " + rel)
    if digest(Path(binding["actor_executable"])) != binding["actor_executable_sha256"]:
        raise ValueError("actor executable changed")
    return binding


def freeze():
    if digest(COORDS) != COORDS_SHA:
        raise ValueError("wrong coordinate bytes")
    files = {rel: digest(REPO / rel) for rel in BOUND_FILES}
    executable = shutil.which("codex")
    if executable is None:
        raise ValueError("codex executable unavailable")
    RUN.mkdir(exist_ok=False)
    cwd = tempfile.mkdtemp(prefix="alpha-newton-actor-dev-v1-")
    write_new(RUN / "binding.json", {"created_at_utc": datetime.now(UTC).isoformat(),
              "files": files, "neutral_actor_cwd": cwd, "actor_executable": executable,
              "actor_executable_sha256": digest(Path(executable)),
              "scope": "Four-law decoder development only; no main bank or adaptive planner allocation"})
    print("FROZEN", digest(RUN / "binding.json"))


def worker(task_index, split):
    task = read(COORDS)["tasks"][task_index]
    stem = f"t{task_index}-{split}"
    request, output = RUN / (stem + "-request.json"), RUN / (stem + "-output.json")
    write_new(request, {"domain": task["domain_id"], "difficulty": task["difficulty"],
                       "law_version": task["law_version"], "rows": task["coordinates"][split]["x"], "noise0": 0})
    process = subprocess.run([str(REPO / ".venv/Scripts/python.exe"), "-I", "-B",
        str(BASE / "newton_scalar_worker_v1.py"), "--request", str(request), "--output", str(output)],
        cwd=REPO, capture_output=True, timeout=60, check=False)
    (RUN / (stem + "-stdout.log")).write_bytes(process.stdout)
    (RUN / (stem + "-stderr.log")).write_bytes(process.stderr)
    if process.returncode != 0 or not output.exists() or read(output)["status"] != "COMPLETE":
        raise ValueError("worker incomplete; do not retry or replace task: " + stem)
    return output


def collect_training():
    verify()
    if (RUN / "training.json").exists():
        raise ValueError("training already collected")
    records = []
    for index in range(4):
        output = worker(index, "train")
        records.append({"task": index, "output": output.name, "sha256": digest(output)})
    write_new(RUN / "training.json", records)
    print("TRAINING_COMPLETE", "256 responses; confirmation targets not generated")


def render_prompts():
    verify()
    from adaptivity_adapter_contract import GRAMMAR
    from adaptivity_dev_prompts_v1 import render_prompt
    record = []
    tasks = read(COORDS)["tasks"]
    for item in read(RUN / "training.json"):
        path = RUN / item["output"]
        if digest(path) != item["sha256"]:
            raise ValueError("training output changed")
        values = [r["value"] for r in read(path)["records"]]
        for condition in ("prior", "data"):
            prompt = render_prompt(tasks[item["task"]], GRAMMAR, None if condition == "prior" else values)
            target = RUN / f"t{item['task']}-{condition}-prompt.txt"
            with target.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(prompt)
            record.append({"task": item["task"], "condition": condition, "path": target.name, "sha256": digest(target)})
    write_new(RUN / "prompts.json", record)
    print("PROMPTS_FROZEN", len(record), "records", len({x["sha256"] for x in record}), "unique hashes")


def pair(index, remaining, checked):
    binding = verify()
    now = datetime.now(UTC)
    check_time = datetime.fromisoformat(checked)
    if (check_time.tzinfo is None or not 0 <= (now - check_time).total_seconds() <= 60
            or not math.isfinite(remaining) or not 7 < remaining <= 100):
        raise ValueError("fresh ordinary quota above reserve required; no launch")
    if not 0 <= index < 8:
        raise ValueError("pair index")
    for earlier in range(index):
        previous = read(RUN / f"pair-{earlier}.json")
        validate_pair(earlier, previous)
        if not all(v["success"] for v in previous["calls"]):
            raise ValueError("earlier incomplete transport; no continuation")
    task, rep = divmod(index, 2)
    conditions = ["prior", "data"] if (task + rep) % 2 == 0 else ["data", "prior"]
    if (any((RUN / f"pair-{index}{suffix}.json").exists() for suffix in ("", "-started"))
            or any((RUN / f"t{task}-r{rep}-{c}").exists() for c in conditions)):
        raise ValueError("pair artifacts already exist; no rerun or partial retry")
    prompts = {(p["task"], p["condition"]): p for p in read(RUN / "prompts.json")}
    prepared = {}
    for condition in conditions:
        item = prompts[(task, condition)]
        raw = (RUN / item["path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError("prompt bytes changed before any pair launch")
        prepared[condition] = raw.decode("utf-8")
    write_new(RUN / f"pair-{index}-started.json", {"started_at_utc": datetime.now(UTC).isoformat(),
              "task": task, "repetition": rep, "conditions": conditions,
              "quota_remaining_at_launch": remaining, "quota_checked_at_utc": checked,
              "scope": "Durable no-retry claim; not a parent-liveness or child-termination guarantee"})
    from alpha_research_rl.codex_actor import run_actor
    def call(condition):
        output = RUN / f"t{task}-r{rep}-{condition}"
        result = run_actor(prepared[condition], output, timeout_seconds=600,
                           cwd=binding["neutral_actor_cwd"], executable=binding["actor_executable"])
        return {"task": task, "repetition": rep, "condition": condition, "directory": output.name,
                "success": result.success, "status": result.status, "error": result.error,
                "result_sha256": digest(output / "result.json"),
                "response_sha256": digest(output / "response.json") if (output / "response.json").exists() else None}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(call, c) for c in conditions]
        records = []
        for condition, future in zip(conditions, futures, strict=True):
            try:
                records.append(future.result())
            except BaseException as exc:  # noqa: BLE001 - preserve both launched outcomes; never retry.
                records.append({"task": task, "repetition": rep, "condition": condition,
                                "success": False, "status": "driver_exception", "error": type(exc).__name__})
    write_new(RUN / f"pair-{index}.json", {"quota_remaining_at_launch": remaining,
              "quota_checked_at_utc": checked, "calls": records})
    print(json.dumps({"pair": index, "calls": [{k: v for k, v in r.items() if k in {"condition", "success", "status", "error"}} for r in records]}))
    if not all(r["success"] for r in records):
        raise SystemExit("INCOMPLETE_TRANSPORT_STOP")


def validate_pair(index, group):
    task, rep = divmod(index, 2)
    calls = group.get("calls") if type(group) is dict else None
    expected = {(task, rep, c) for c in ("prior", "data")}
    if (type(calls) is not list or len(calls) != 2 or any(type(c) is not dict for c in calls)
            or any(type(c.get("task")) is not int or type(c.get("repetition")) is not int
                   or type(c.get("condition")) is not str or type(c.get("success")) is not bool for c in calls)
            or {(c.get("task"), c.get("repetition"), c.get("condition")) for c in calls} != expected):
        raise ValueError("pair identities must match the exact two-call schedule")
    for call in calls:
        if call.get("success") is True:
            if call.get("status") != "succeeded" or call.get("error") is not None:
                raise ValueError("successful transport requires provider succeeded status")
            expected_dir = f"t{task}-r{rep}-{call['condition']}"
            if call.get("directory") != expected_dir:
                raise ValueError("call directory identity")
            for name in ("result", "response"):
                path = RUN / expected_dir / (name + ".json")
                if digest(path) != call.get(name + "_sha256"):
                    raise ValueError("call evidence changed")
            provider = read(RUN / expected_dir / "result.json")
            if (provider.get("success") is not True or provider.get("status") != "succeeded"
                    or provider.get("error") is not None):
                raise ValueError("provider result does not establish successful transport")


def freeze_responses():
    verify()
    records = []
    for index in range(8):
        group = read(RUN / f"pair-{index}.json")
        validate_pair(index, group)
        for call in group["calls"]:
            if not call["success"]:
                raise ValueError("incomplete transport bank")
            for name in ("result", "response"):
                path = RUN / call["directory"] / (name + ".json")
                if digest(path) != call[name + "_sha256"]:
                    raise ValueError("call evidence changed")
            records.append(call)
    write_new(RUN / "responses-frozen.json", {"frozen_at_utc": datetime.now(UTC).isoformat(), "calls": records})
    print("RESPONSES_FROZEN", len(records), digest(RUN / "responses-frozen.json"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["freeze", "training", "prompts", "pair", "freeze-responses"])
    parser.add_argument("--index", type=int)
    parser.add_argument("--remaining", type=float)
    parser.add_argument("--checked")
    args = parser.parse_args()
    {"freeze": freeze, "training": collect_training, "prompts": render_prompts,
     "pair": lambda: pair(args.index, args.remaining, args.checked), "freeze-responses": freeze_responses}[args.stage]()


if __name__ == "__main__":
    main()
