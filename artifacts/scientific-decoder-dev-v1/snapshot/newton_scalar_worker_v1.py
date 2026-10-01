"""Root-only pinned NewtonBench scalar worker. Never import this in an actor.

No automatic download/install, symbolic judge, generated Python, or remote API.
The input rows are supplied by the prospective study owner; this worker does not
certify their study-specific compact bounds or train/confirmation timing.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib
import importlib.abc
import io
import json
import math
import numbers
import os
from pathlib import Path
import sys
import types

COMMIT = "912a4ba5f4356ddd06acc16e44460ca30be4abc2"
MANIFEST_SHA256 = "87c7d18f6987461b403c3f87b95873cc4f8fa7b19caf32ca52964ee87d9f9010"
CACHE = Path(__file__).resolve().parent / "newtonbench-source-912a4ba"
PARAMETERS = {
    "m8_sound_speed": ("adiabatic_index", "temperature", "molar_mass"),
    "m10_be_distribution": ("omega", "temperature"),
}
SAFE_CODES = {"source_manifest_identity", "commit_identity", "source_path", "source_bytes",
              "unlisted_cache_file", "bytecode_cache", "vendor_import_origin",
              "prohibited_import", "prohibited_operation", "not_a_fresh_worker",
              "symbolic_evaluation_disabled", "nonfinite_or_nonscalar_output"}


class WorkerError(ValueError):
    pass


def strict_json(raw: bytes) -> object:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise WorkerError("duplicate_key")
            result[key] = value
        return result
    def bad(_):
        raise WorkerError("nonfinite_json")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=bad)


def validate_request(obj: object) -> dict:
    if type(obj) is not dict or set(obj) != {"domain", "difficulty", "law_version", "rows", "noise0"}:
        raise WorkerError("request_keys")
    if type(obj["domain"]) is not str or obj["domain"] not in PARAMETERS:
        raise WorkerError("domain")
    if obj["difficulty"] not in ("medium", "hard") or type(obj["difficulty"]) is not str:
        raise WorkerError("difficulty")
    if obj["law_version"] not in ("v0", "v1", "v2") or type(obj["law_version"]) is not str:
        raise WorkerError("law_version")
    if type(obj["noise0"]) not in (int, float) or obj["noise0"] != 0:
        raise WorkerError("noise_must_be_zero")
    rows = obj["rows"]
    if type(rows) is not list or not 1 <= len(rows) <= 1024:
        raise WorkerError("rows_count")
    for row in rows:
        if type(row) is not list or len(row) != len(PARAMETERS[obj["domain"]]):
            raise WorkerError("row_dimension")
        for value in row:
            if type(value) not in (int, float):
                raise WorkerError("row_number")
            try:
                okay = math.isfinite(float(value)) and value > 0
            except OverflowError:
                okay = False
            if not okay:
                raise WorkerError("row_requires_finite_positive")
    return obj


def verify_cache() -> dict[str, str]:
    if CACHE.resolve() != CACHE.absolute():
        raise WorkerError("source_path")
    manifest_raw = (CACHE / "manifest.json").read_bytes()
    if hashlib.sha256(manifest_raw).hexdigest() != MANIFEST_SHA256:
        raise WorkerError("source_manifest_identity")
    manifest = strict_json(manifest_raw)
    if manifest["commit"] != COMMIT:
        raise WorkerError("commit_identity")
    for path in CACHE.rglob("*"):
        if path.resolve() != path.absolute():
            raise WorkerError("source_path")
        if path.name == "__pycache__" or path.suffix in {".pyc", ".pyo"}:
            raise WorkerError("bytecode_cache")
        if path.is_file() and path.relative_to(CACHE).as_posix() not in {*manifest["files"], "manifest.json"}:
            raise WorkerError("unlisted_cache_file")
    for relative, expected in manifest["files"].items():
        path = CACHE / relative
        if path.resolve() != path.absolute() or not path.is_file():
            raise WorkerError("source_path")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise WorkerError("source_bytes")
    return manifest["files"]


def verify_vendor_origins(hashes: dict[str, str], domain: str) -> dict:
    origins = {}
    namespaces = {"modules", "modules.common", "modules." + domain, "utils", "modules.common.evaluation"}
    for name, module in list(sys.modules.items()):
        if not (name == "modules" or name.startswith("modules.") or name == "utils" or name.startswith("utils.")):
            continue
        location = getattr(module, "__file__", None)
        if location is None and name in namespaces:
            continue
        if type(location) is not str:
            raise WorkerError("vendor_import_origin")
        path = Path(location).resolve()
        try:
            relative = path.relative_to(CACHE.resolve()).as_posix()
        except ValueError as exc:
            raise WorkerError("vendor_import_origin") from exc
        if path.suffix != ".py" or relative not in hashes:
            raise WorkerError("vendor_import_origin")
        if hashlib.sha256(path.read_bytes()).hexdigest() != hashes[relative]:
            raise WorkerError("vendor_import_origin")
        origins[name] = {"path": relative, "sha256": hashes[relative]}
    if "modules." + domain + ".core" not in origins or "modules." + domain + ".laws" not in origins:
        raise WorkerError("vendor_import_origin")
    return origins


class _NoApis(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"openai", "anthropic", "requests", "httpx", "dotenv", "torch", "transformers"}:
            raise WorkerError("prohibited_import")
        return None


def _audit(event, args):
    if event in {"socket.connect", "socket.connect_ex", "socket.getaddrinfo", "subprocess.Popen", "os.system", "os.posix_spawn", "os.spawn"}:
        raise WorkerError("prohibited_operation")


def _disabled_evaluator(*args, **kwargs):
    raise WorkerError("symbolic_evaluation_disabled")


def load_scalar(domain: str):
    """Trusted source import; called only after all request/source checks."""
    if any(n == "modules" or n.startswith("modules.") or n == "utils" or n.startswith("utils.") for n in sys.modules):
        raise WorkerError("not_a_fresh_worker")
    sys.dont_write_bytecode = True
    sys.meta_path.insert(0, _NoApis())
    sys.addaudithook(_audit)
    for name, path in (("modules", CACHE / "modules"),
                       ("modules.common", CACHE / "modules/common"),
                       ("modules." + domain, CACHE / "modules" / domain),
                       ("utils", CACHE / "utils")):
        package = types.ModuleType(name)
        package.__path__ = [str(path)]
        sys.modules[name] = package
    stub = types.ModuleType("modules.common.evaluation")
    stub.evaluate_law = _disabled_evaluator
    sys.modules[stub.__name__] = stub
    core = importlib.import_module("modules." + domain + ".core")
    return core.run_experiment_for_module


def run(request: dict, *, scalar) -> dict:
    """Small injectable artificial seam; never constructs an oracle itself."""
    validate_request(request)
    records, failed = [], False
    for index, row in enumerate(request["rows"]):
        record = {"index": index, "status": "not_attempted", "value": None, "error_code": None}
        records.append(record)
        if failed:
            continue
        try:
            value = scalar(noise_level=0.0, difficulty=request["difficulty"],
                           system="vanilla_equation", law_version=request["law_version"],
                           **dict(zip(PARAMETERS[request["domain"]], map(float, row))))
            if isinstance(value, bool) or not isinstance(value, numbers.Real) or not math.isfinite(float(value)):
                raise WorkerError("nonfinite_or_nonscalar_output")
            record["value"], record["status"] = float(value), "ok"
        except BaseException as exc:
            failed, record["status"] = True, "failed"
            record["error_code"] = (str(exc) if isinstance(exc, WorkerError) and str(exc) in SAFE_CODES
                                    else "interrupted" if isinstance(exc, (KeyboardInterrupt, SystemExit))
                                    else "oracle_arithmetic_error" if isinstance(exc, ArithmeticError)
                                    else "oracle_exception")
    return {"schema": "newton-scalar-output-v1", "status": "INCOMPLETE" if failed else "COMPLETE",
            "domain": request["domain"], "difficulty": request["difficulty"],
            "law_version": request["law_version"], "system": "vanilla_equation", "noise": 0.0,
            "row_count": len(records), "attempted_count": sum(r["status"] != "not_attempted" for r in records),
            "records": records}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.output.resolve() == args.request.resolve():
        parser.error("output must be a new distinct path")
    result = {"schema": "newton-scalar-output-v1", "status": "INCOMPLETE",
              "error_code": "precheck_failed", "attempted_count": 0}
    captured = io.StringIO()
    stage = "request_validation"
    try:
        raw = args.request.read_bytes()
        request = validate_request(strict_json(raw))
        stage = "source_verification"
        hashes = verify_cache()
        with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured):
            stage = "oracle_import"
            scalar = load_scalar(request["domain"])
            verify_vendor_origins(hashes, request["domain"])
            stage = "oracle_run"
            result["attempted_count"] = None  # An unexpected outer interruption is ambiguous.
            result = run(request, scalar=scalar)
        stage = "post_run_verification"
        verify_cache()
        origins = verify_vendor_origins(hashes, request["domain"])
        result.update({"upstream_commit": COMMIT, "source_manifest_sha256": MANIFEST_SHA256,
                       "source_files": hashes, "request_sha256": hashlib.sha256(raw).hexdigest(),
                       "vendor_import_origins": origins,
                       "library_output_observed": bool(captured.getvalue()),
                       "worker_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                       "failure_class": None if result["status"] == "COMPLETE" else "oracle_row_failure"})
        stage = "finished"
    except BaseException as exc:
        # Never export traceback, exception text, law source or symbolic gold.
        result["status"], result["error_code"] = "INCOMPLETE", "worker_failure"
        result["failure_class"] = {
            "request_validation": "request_failure", "source_verification": "source_integrity_failure",
            "oracle_import": "dependency_or_import_failure", "oracle_run": "ambiguous_oracle_failure",
            "post_run_verification": "post_run_integrity_failure",
        }.get(stage, "worker_failure")
        if isinstance(exc, WorkerError) and str(exc) in SAFE_CODES:
            result["error_code"] = str(exc)
    result["stage"] = stage
    try:
        with args.output.open("xb") as file:
            file.write((json.dumps(result, ensure_ascii=True, sort_keys=True, allow_nan=False, indent=2) + "\n").encode())
            file.flush()
            os.fsync(file.fileno())
    except BaseException:
        print("output_write_failed", file=sys.stderr)
        return 2
    return 0 if result["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
