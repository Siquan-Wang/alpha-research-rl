"""Check the fixed public stopped-study evidence; never execute its snapshot.

This is provenance/count verification, not scientific reproduction, a network
publication check, or a sandbox for executing benchmark code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import stat
from datetime import datetime, timedelta
from pathlib import Path, PurePosixPath

BASE = "artifacts/scientific-decoder-dev-v1"
RESULT = "results/scientific_decoder_dev_v1.json"
RESULT_SHA256 = "06950ce985f5fd7f05ba8ecb3fe9966f09cba3c352ce7fec32f54ef7682b2db3"
PREFLIGHT_SHA256 = "dd48fa13b1110e6ff36428f009bcc384e70254694e96310ecef6d4d16f590841"
COMMIT = "3d818347f286e15ce673f5814411f7d27261a026"
UPSTREAM = "912a4ba5f4356ddd06acc16e44460ca30be4abc2"
CACHE = "newtonbench-source-912a4ba"
GUIDE = "docs/scientific-decoder-dev-plan-v1.md"
TRANSPORT = "src/alpha_research_rl/codex_actor.py"
LAW_IDS = (
    "m8_sound_speed:medium:v0", "m8_sound_speed:hard:v1",
    "m10_be_distribution:medium:v2", "m10_be_distribution:hard:v0",
)
COUNTS = {
    "planned_training_targets": 256, "requested_training_targets": 192,
    "attempted_training_targets": 135, "finite_training_targets": 134,
    "failed_training_targets": 1, "not_attempted_training_targets": 121,
    "training_stage_invocations": 1, "worker_invocations": 3,
    "hosted_calls": 0, "confirmation_target_evaluations": 0,
    "model_prediction_evaluations": 0, "reference_prediction_evaluations": 0,
}


class EvidenceError(ValueError):
    """Missing, changed, malformed, or inconsistent saved evidence."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def exact(actual, expected, message: str) -> None:
    """JSON identity including bool/int/float distinctions, independent of key order."""
    require(json.dumps(actual, sort_keys=True, allow_nan=False)
            == json.dumps(expected, sort_keys=True, allow_nan=False), message)


def decode(raw: bytes):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key")
            result[key] = value
        return result

    def bad_constant(value):
        raise EvidenceError(f"nonfinite JSON constant: {value}")

    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=bad_constant)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def safe_path(root: Path, relative: str) -> Path:
    require(type(relative) is str and relative != "", "empty evidence path")
    parts = relative.split("/")
    require(not PurePosixPath(relative).is_absolute()
            and all(p not in ("", ".", "..") and p == p.rstrip(" .")
                    and not any(c in p for c in '\\:<>"|?*') for p in parts), "unsafe evidence path")
    path = root
    for part in parts:
        path = path / part
        info = path.lstat()
        require(not stat.S_ISLNK(info.st_mode)
                and not getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT,
                "redirected evidence path")
    require(path.resolve().is_relative_to(root), "evidence path escaped root")
    return path


def read(root: Path, relative: str, sha256: str | None = None, size: int | None = None) -> bytes:
    path = safe_path(root, relative)
    require(path.is_file(), f"not a regular evidence file: {relative}")
    require(path.stat().st_size <= 2_000_000, "unexpected evidence file size")
    raw = path.read_bytes()
    if sha256 is not None:
        require(digest(raw) == sha256, f"SHA256 mismatch: {relative}")
    if size is not None:
        require(type(size) is int and len(raw) == size, f"byte count mismatch: {relative}")
    return raw


def inventory(root: Path, relative: str) -> set[str]:
    directory = safe_path(root, relative)
    require(directory.is_dir(), "missing evidence directory")
    found = set()
    pending = [directory]
    while pending:
        for candidate in pending.pop().iterdir():
            checked = safe_path(root, candidate.relative_to(root).as_posix())
            if checked.is_dir():
                pending.append(checked)
            else:
                require(checked.is_file(), "nonregular evidence entry")
                found.add(checked.relative_to(directory).as_posix())
    return found


def utc(value: str) -> datetime:
    result = datetime.fromisoformat(value)
    require(result.utcoffset() == timedelta(0), "timestamp must be UTC")
    return result


def validate_rows(output: dict, task: int) -> dict:
    """Independently count every recorded slot; a failure is never a zero score."""
    rows = output["records"]
    require(type(rows) is list and len(rows) == 64, "expected 64 ordered output slots")
    counts = {"attempted": 0, "successful": 0, "failed": 0, "not_attempted": 0}
    first_failure = None
    for index, row in enumerate(rows):
        require(type(row) is dict and set(row) == {"index", "status", "value", "error_code"},
                "output row schema")
        require(type(row["index"]) is int and row["index"] == index, "output row order/type")
        expected = "ok" if task < 2 or index < 6 else "failed" if index == 6 else "not_attempted"
        require(row["status"] == expected, "stopped output prefix/status mismatch")
        if expected == "ok":
            require(type(row["value"]) in (int, float) and math.isfinite(row["value"])
                    and row["error_code"] is None, "invalid successful scalar")
            counts["successful"] += 1
            counts["attempted"] += 1
        else:
            require(row["value"] is None, "failed/unattempted value must be null")
            error = "nonfinite_or_nonscalar_output" if expected == "failed" else None
            require(row["error_code"] == error, "failure code mismatch")
            counts[expected] += 1
            if expected == "failed":
                counts["attempted"] += 1
                first_failure = row
    exact(output["attempted_count"], counts["attempted"], "worker attempted count mismatch")
    return {"task": task, "canonical_law_id": LAW_IDS[task], "planned": 64, **counts,
            "status": "COMPLETE" if task < 2 else "INCOMPLETE", "first_failure": first_failure}


def validate_result(result: dict, tasks: list[dict]) -> None:
    require(result["schema"] == "scientific-decoder-dev-stop-v1", "result schema")
    require(result["status"] == "INCOMPLETE_ORACLE_TARGETS" and result["version_stopped"] is True,
            "version must remain stopped and incomplete")
    require(result["predictive_scores"] is None and result["allocation_inequalities"] == "NOT_EVALUATED",
            "unavailable performance cannot become a score")
    for key, value in COUNTS.items():
        exact(result[key], value, f"result count mismatch: {key}")
    exact(result["tasks"], tasks, "result task population/order mismatch")
    for key, field in (("attempted_training_targets", "attempted"),
                       ("finite_training_targets", "successful"),
                       ("failed_training_targets", "failed"),
                       ("not_attempted_training_targets", "not_attempted")):
        require(result[key] == sum(t[field] for t in tasks), f"aggregate mismatch: {key}")


def check_scientific_decoder_stop(root: Path) -> dict:
    root = Path(root).resolve(strict=True)
    result = decode(read(root, RESULT, RESULT_SHA256))
    preflight = decode(read(root, f"{BASE}/preflight-manifest.json", PREFLIGHT_SHA256))
    require(preflight["schema"] == "scientific-decoder-dev-preflight-v1"
            and preflight["stage"] == "PRE_TARGETS_PRE_HOSTED_CALLS", "preflight stage")
    for key in ("training_targets", "confirmation_targets", "hosted_calls"):
        exact(preflight[key], 0, "nonzero preflight count")
    snapshot = preflight["files"]
    require(len(snapshot) == 36, "snapshot population mismatch")
    require(inventory(root, f"{BASE}/snapshot") == set(snapshot), "snapshot inventory mismatch")
    expected_map = {}
    captured = {}
    for name, meta in snapshot.items():
        require(set(meta) == {"bytes", "reconstruct_at", "sha256"}, "snapshot entry schema")
        require(meta["reconstruct_at"] == f".local/{name}", "snapshot reconstruction path mismatch")
        relative = f"{BASE}/snapshot/{name}"
        captured[name] = read(root, relative, meta["sha256"], meta["bytes"])
        expected_map[relative] = meta["sha256"]
    execution_names = {"publication-preflight.json"} | {
        f"t{i}-train-{suffix}" for i in range(3)
        for suffix in ("request.json", "output.json", "stdout.log", "stderr.log")
    }
    require(set(result["execution_files"]) == execution_names, "execution map mismatch")
    require(inventory(root, f"{BASE}/execution") == execution_names, "execution inventory mismatch")
    execution = {}
    for name, meta in result["execution_files"].items():
        require(set(meta) == {"bytes", "sha256"}, "execution entry schema")
        execution[name] = read(root, f"{BASE}/execution/{name}", meta["sha256"], meta["bytes"])
        if name.endswith(".log"):
            require(execution[name] == b"", "unexpected retained library output")
    receipt_raw = execution["publication-preflight.json"]
    receipt = decode(receipt_raw)
    require(digest(receipt_raw) == result["publication_receipt_sha256"], "receipt binding mismatch")
    require(receipt["schema"] == "decoder-publication-receipt-v1" and receipt["stage"] == "preflight"
            and receipt["outcome"] == "ALL_BYTES_MATCH"
            and receipt["authentication"] == "anonymous public raw URLs", "receipt status/schema")
    require(receipt["commit"] == result["publication_commit"] == COMMIT, "publication commit mismatch")
    for name in (f"{BASE}/binding-public.json", f"{BASE}/preflight-manifest.json", GUIDE, TRANSPORT):
        expected_map[name] = digest(read(root, name))
    exact(receipt["files"], expected_map, "complete 40-file receipt map mismatch")
    require(len(expected_map) == 40, "receipt population mismatch")
    exact(preflight["existing_transport"], {"path": TRANSPORT, "sha256": expected_map[TRANSPORT]},
          "transport binding mismatch")
    binding = decode(read(root, f"{BASE}/binding-public.json"))
    require(binding["private_binding_sha256"] == result["private_binding_sha256"], "private hash mismatch")
    exact(binding["omitted_fields"], ["neutral_actor_cwd", "actor_executable"], "redaction metadata")
    require(len(binding["files"]) == 11, "binding population mismatch")
    reconstruction = {m["reconstruct_at"]: m["sha256"] for m in snapshot.values()}
    reconstruction[TRANSPORT] = expected_map[TRANSPORT]
    for name, sha in binding["files"].items():
        require(reconstruction.get(name) == sha, "bound source missing from snapshot/transport")
    require(receipt["verified_at_utc"] == result["public_bytes_verified_at_utc"], "receipt timestamp mismatch")
    require(utc(binding["created_at_utc"]) < utc(preflight["created_at_utc"])
            < utc(receipt["verified_at_utc"]) < utc(result["recorded_at_utc"]), "metadata chronology mismatch")

    cache = decode(captured[f"{CACHE}/manifest.json"])
    require(cache["schema"] == "newtonbench-minimal-source-v1"
            and cache["commit"] == UPSTREAM and len(cache["files"]) == 13, "upstream manifest")
    for name, sha in cache["files"].items():
        require(digest(captured[f"{CACHE}/{name}"]) == sha, "upstream source byte mismatch")
    coordinates = decode(captured["adaptivity-dev-coordinates-v1.json"])
    require(len(coordinates["tasks"]) == 4, "coordinate task population")
    tasks = []
    for task, law in enumerate(LAW_IDS):
        coordinate = coordinates["tasks"][task]
        require(coordinate["canonical_law_id"] == law, "coordinate task ordering")
        if task == 3:
            tasks.append({"task": 3, "canonical_law_id": law, "planned": 64, "attempted": 0,
                          "successful": 0, "failed": 0, "not_attempted": 64,
                          "status": "NOT_ATTEMPTED", "first_failure": None})
            continue
        domain, difficulty, version = law.split(":")
        request_raw = execution[f"t{task}-train-request.json"]
        request = decode(request_raw)
        exact(request, {"domain": domain, "difficulty": difficulty, "law_version": version,
                        "noise0": 0, "rows": coordinate["coordinates"]["train"]["x"]},
              "request differs from fixed training coordinates")
        require(len(request["rows"]) == 64, "request row count")
        output = decode(execution[f"t{task}-train-output.json"])
        expected_metadata = {
            "schema": "newton-scalar-output-v1", "domain": domain, "difficulty": difficulty,
            "law_version": version, "system": "vanilla_equation", "noise": 0.0, "row_count": 64,
            "stage": "finished", "status": "COMPLETE" if task < 2 else "INCOMPLETE",
            "failure_class": None if task < 2 else "oracle_row_failure",
            "library_output_observed": False, "request_sha256": digest(request_raw),
            "worker_sha256": digest(captured["newton_scalar_worker_v1.py"]),
            "upstream_commit": UPSTREAM, "source_manifest_sha256": digest(captured[f"{CACHE}/manifest.json"]),
            "source_files": cache["files"],
        }
        require(set(output) == set(expected_metadata) | {"records", "attempted_count", "vendor_import_origins"},
                "worker output schema mismatch")
        exact({k: output[k] for k in expected_metadata}, expected_metadata, "worker provenance/status mismatch")
        origins = output["vendor_import_origins"]
        names = {"modules.common.types", f"modules.{domain}.core", f"modules.{domain}.laws",
                 f"modules.{domain}.{'m8' if task < 2 else 'm10'}_types", "utils.noise"}
        if task < 2:
            names.add(f"modules.{domain}.physics")
        require(set(origins) == names, "recorded import-origin population")
        for name, entry in origins.items():
            path = name.replace(".", "/") + ".py"
            exact(entry, {"path": path, "sha256": cache["files"][path]}, "recorded import origin mismatch")
        tasks.append(validate_rows(output, task))
    validate_result(result, tasks)
    return {
        "schema": "scientific-decoder-stop-verification-v1", "status": "SAVED_STOP_VERIFIED",
        "result_sha256": RESULT_SHA256, "snapshot_files": 36, "receipt_files": 40,
        "execution_files": 13, "upstream_payload_files_hashed": 13, "tasks": 4,
        **COUNTS, "predictive_scores": None, "allocation_inequalities": "NOT_EVALUATED",
        "new_oracle_calls": 0, "new_hosted_calls": 0, "network_requests": 0,
        "scope": "Exact saved public bytes, recorded provenance and complete slot counts; no scientific rerun.",
        "chronology_limit": "Coordinator receipt metadata only; no independent per-call timestamps.",
        "failure_limit": "Collapsed conversion code does not identify the underlying numerical cause.",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        verification = check_scientific_decoder_stop(args.root)
    except (EvidenceError, OSError, ValueError, KeyError, TypeError, OverflowError) as exc:
        print(json.dumps({"status": "VERIFICATION_FAILED", "error": str(exc)}, ensure_ascii=True))
        return 1
    print(json.dumps(verification, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
