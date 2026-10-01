"""Replay two completed local Git snapshots; never fetch, install or rescore."""

from __future__ import annotations

import argparse
import hashlib
import importlib.abc
import importlib.machinery
import importlib.util
import io
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import sysconfig
import threading
import time
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

MAX_FILES = 4096
MAX_BLOB = 8 * 1024 * 1024
MAX_TOTAL = 160 * 1024 * 1024
MAX_LISTING = 8 * 1024 * 1024
MAX_GIT_ERROR = 1024 * 1024
MAX_LOG = 10 * 1024 * 1024
GIT_TIMEOUT = 120
CHILD_TIMEOUT = 300
TOTAL_TIMEOUT = 600
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
ROOT = Path(__file__).resolve().parents[1]
GUARD_SCOPE = "Local Python instrumentation; not an adversarial sandbox. Platform preflight precedes guards."


class ReplayError(ValueError):
    """A failed integrity/preflight check, never a successful partial replay."""


def require(condition, message):
    if not condition:
        raise ReplayError(message)


def _recipe(commit, adapter, report_path, report_sha256, html_sha256=None):
    if adapter == "revision":
        expected = {
            "status": "matches_published_astra_revision_evidence", "states": 10,
            "slots": 200, "repetitions": 4, "historical_hosted_calls": 80,
            "historical_cheap_slots": 120, "historical_new_feedback_calls": 98,
            "historical_new_future_calls": 99,
            "reused_future_keys": 34, "unique_future_keys": 133,
            "replay_model_calls": 0, "replay_financial_scores": 0,
            "market_scores_recomputed": False, "raw_market_data_read": False,
            "installed_scoring_runtime_revalidated": False,
            "explorer_payload_and_template_match": True,
            "explorer_report_and_prompt_bytes_exact": True,
            "explorer_html_sha256": html_sha256,
            "captured_execution_file_count": 685,
            "disposable_public_evidence_snapshots_used_by_saved_replay": True,
            "presentation_rebuild_performs_no_writes": True,
            "training_and_financial_imports_private_data_subprocesses_and_network_disallowed": True,
            "stdlib_platform_detection_precedes_execution_guards": True,
            "guards_are_not_an_adversarial_sandbox": True,
            "contract_sha256": "9f531a0cc6bffc81d010f54b49a4a717703bfef81197d75ddac890373da9b574",
            "submissions_sha256": "672d93cd8faababc71a7b3b5ff3823da840061479798f0ec1f2b6eef1cc9577d",
            "renderer_sha256": "3dfb34a58dc934c7a585b3b675dcbed6aaa3b86010fec84f64086bfccc33e568",
        }
    else:
        expected = {"status": "SAVED_SYNTHETIC_CONFIRMATION_VERIFIED", "panels": 640,
                    "new_panel_generations": 0, "new_model_calls": 0,
                    "new_market_scores": 0, "writes": 0,
                    "scope": "Saved-array recomputation; not an independent PRNG or hidden-access attestation."}
    expected["report_sha256"] = report_sha256
    value = {"commit": commit, "adapter": adapter, "report_path": report_path,
             "report_sha256": report_sha256, "expected_summary": expected,
             "third_party": adapter == "revision"}
    if html_sha256 is not None:
        value.update(html_path="docs/astra-revision-explorer.html", html_sha256=html_sha256)
    return value


RECIPES = {
    "matched-prefix-v1": _recipe(
        "7e0f7b35618ace986de6ce0cfa1a6231e7716080", "revision",
        "results/astra_matched_prefix_v1.json",
        "89162112ddad384ed8917a8b1198ce94044abc90ff15e1680bfe88b66eb43c37",
        "8bb1ff7013c8c7906f9223daca87287296103f8643e41216037d2bbf39d9b772"),
    "sealed-confirmation-v1": _recipe(
        "58dc66ed2a4af7add8ee79f54337e278d9bd7d13", "sealed",
        "results/sealed_confirmation_v1.json",
        "ec6d9076d70f50d436c3d69a9ec126d23489f2ce4f98bbf4e25064e6d9c7306d"),
}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":"))


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def strict_json(raw):
    def invalid(_):
        raise ReplayError("nonfinite JSON value")
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=invalid)
    canonical(value)  # Also rejects overflow such as 1e999.
    return value


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def utc():
    return datetime.now(UTC).isoformat()


def write_new(path, value):
    raw = value if isinstance(value, bytes) else (canonical(value) + "\n").encode("ascii")
    with Path(path).open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def git_environment(environ):
    result = {key: value for key, value in environ.items() if not key.upper().startswith("GIT_")}
    result.update(GIT_NO_REPLACE_OBJECTS="1", GIT_NO_LAZY_FETCH="1", GIT_CONFIG_NOSYSTEM="1",
                  GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")
    return result


def _path_key(path):
    require(type(path) is str and path and not path.startswith("/"), "invalid relative tree path")
    require(not any(ord(c) < 32 or ord(c) == 127 or c in '\\:<>"|?*' for c in path),
            "unsafe tree path character")
    parts = path.split("/")
    for part in parts:
        require(part and part not in {".", ".."} and not part.endswith((".", " ")), "unsafe path segment")
        folded = part.casefold()
        require(folded not in {".git", "__pycache__"} and not folded.endswith((".pyc", ".pyo")),
                "Git metadata or bytecode is not supported")
        require(not re.match(r"^(con|prn|aux|nul|com[1-9¹²³]|lpt[1-9¹²³])(?:\.|$)", folded),
                "Windows device path is not supported")
    return unicodedata.normalize("NFC", path).casefold()


def parse_tree(raw):
    require(type(raw) is bytes and len(raw) <= MAX_LISTING and raw.endswith(b"\0"), "invalid tree framing")
    rows, names = [], set()
    for record in raw[:-1].split(b"\0"):
        try:
            header, name = record.split(b"\t", 1)
            mode, kind, oid = header.decode("ascii").split(" ")
            path = name.decode("utf-8", errors="strict")
        except (ValueError, UnicodeError) as error:
            raise ReplayError("malformed tree entry") from error
        require(mode in {"100644", "100755"} and kind == "blob", "non-regular tree entry")
        require(HEX40.fullmatch(oid) is not None, "invalid blob object ID")
        key = _path_key(path)
        require(key not in names, "duplicate or aliased tree path")
        names.add(key)
        rows.append({"path": path, "mode": mode, "oid": oid})
        require(len(rows) <= MAX_FILES, "tracked file limit exceeded")
    for name in names:
        parts = name.split("/")
        require(not any("/".join(parts[:i]) in names for i in range(1, len(parts))), "file/directory prefix conflict")
    return sorted(rows, key=lambda row: row["path"])


def read_blob(stream, expected_oid):
    require(type(expected_oid) is str and HEX40.fullmatch(expected_oid) is not None, "invalid expected blob ID")
    header = stream.readline(128)
    match = re.fullmatch(rb"([0-9a-f]{40}) blob (0|[1-9][0-9]*)\n", header)
    require(match is not None and match[1].decode("ascii") == expected_oid, "blob header/type/ID differs")
    size = int(match[2])
    require(size <= MAX_BLOB, "blob size limit exceeded")
    body = stream.read(size)
    require(len(body) == size and stream.read(1) == b"\n", "truncated or malformed blob framing")
    actual = hashlib.sha1(b"blob " + str(size).encode("ascii") + b"\0" + body).hexdigest()
    require(actual == expected_oid, "blob bytes differ from Git object identity")
    return body


def validate_summary(recipe, summary):
    require(type(summary) is dict, "verifier summary must be an object")
    expected = recipe["expected_summary"]
    for key, value in expected.items():
        require(key in summary and type(summary[key]) is type(value) and summary[key] == value,
                "verifier summary differs: " + key)
    require(recipe["adapter"] in {"revision", "sealed"} and set(summary) == set(expected),
            "verifier summary field set differs")


class HistoricalFinder(importlib.abc.MetaPathFinder):
    """Resolve project/helpers from this tree before any fallback can execute."""

    def __init__(self, tree, adapter):
        self.tree = Path(tree).resolve()
        self.helpers = {"replay_published_results"} if adapter == "revision" else set()

    def find_spec(self, fullname, path=None, target=None):
        if fullname == "alpha_research_rl" or fullname.startswith("alpha_research_rl."):
            search = [str(self.tree / "src")] if fullname == "alpha_research_rl" else path
        elif fullname in self.helpers:
            search = [str(self.tree / "scripts")]
        else:
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, search)
        require(spec is not None and spec.origin is not None, "historical module missing: " + fullname)
        origin = Path(spec.origin).resolve()
        require(origin.is_relative_to(self.tree) and origin.suffix == ".py", "historical import escaped tree")
        if spec.submodule_search_locations is not None:
            require(all(Path(p).resolve().is_relative_to(self.tree) for p in spec.submodule_search_locations),
                    "historical package path escaped tree")
        return spec


def _no_reparse_ancestors(path):
    for part in (path, *path.parents):
        if part.exists() or part.is_symlink():
            info = part.lstat()
            require(not part.is_symlink() and not (getattr(info, "st_file_attributes", 0) & 1024),
                    "symlink/junction path is not supported")


def _output_path(root, output):
    output = Path(output)
    if not output.is_absolute():
        output = root / output
    _no_reparse_ancestors(output)
    output = output.resolve()
    base = root / ".local" / "pinned-replay-runs"
    require(output.parent == base, "output must be a new direct child of .local/pinned-replay-runs")
    _path_key(output.name)
    require(not output.exists(), "output already exists; no resume or overwrite")
    return output


def _process(argv, *, cwd, env, timeout, stdout_limit, stderr_limit, input_bytes=b"",
             stdout_path=None, stderr_path=None):
    """Drain capped pipes concurrently; never retry or wait indefinitely."""
    outputs, errors, streams, threads = {}, [], [], []
    process = None

    def drain(pipe, label, limit, target):
        data = bytearray()
        stream = None
        try:
            if target is not None:
                stream = Path(target).open("xb", buffering=0)  # noqa: SIM115 -- closed in the failure-reporting finally.
            while True:
                chunk = pipe.read(65536)
                if not chunk:
                    break
                remaining = limit - len(data)
                keep = chunk[:remaining]
                data.extend(keep)
                if stream is not None:
                    stream.write(keep)
                if len(chunk) > remaining:
                    errors.append(label + " limit exceeded")
                    process.kill()
                    break
        except BaseException as error:  # noqa: BLE001 -- worker exceptions become a parent failure after join.
            errors.append(label + ": " + type(error).__name__)
            if process.poll() is None:
                process.kill()
        finally:
            if stream is not None:
                try:
                    stream.flush()
                    os.fsync(stream.fileno())
                except BaseException as error:  # noqa: BLE001 -- durable-log failure must not disappear in a thread.
                    errors.append(label + " persistence: " + type(error).__name__)
                finally:
                    try:
                        stream.close()
                    except BaseException as error:  # noqa: BLE001 -- retain close failures as failed execution.
                        errors.append(label + " close: " + type(error).__name__)
            outputs[label] = bytes(data)
            try:
                pipe.close()
            except BaseException as error:  # noqa: BLE001 -- retain pipe failures as failed execution.
                errors.append(label + " pipe close: " + type(error).__name__)

    def feed():
        try:
            process.stdin.write(input_bytes)
            process.stdin.close()
        except (BrokenPipeError, OSError):
            process.stdin.close()

    try:
        require(timeout > 0, "invocation deadline exceeded")
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        streams = [process.stdout, process.stderr]
        for pipe, label, limit, target in (
            (process.stdout, "stdout", stdout_limit, stdout_path),
            (process.stderr, "stderr", stderr_limit, stderr_path),
        ):
            thread = threading.Thread(target=drain, args=(pipe, label, limit, target), daemon=True)
            thread.start()
            threads.append(thread)
        thread = threading.Thread(target=feed, daemon=True)
        thread.start()
        threads.append(thread)
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            errors.append("process timeout")
            process.kill()
            process.wait(timeout=5)
    except BaseException:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        raise
    finally:
        for thread in threads:
            thread.join(timeout=5)
            if thread.is_alive():
                errors.append("pipe thread did not finish")
        for stream in streams:
            if not stream.closed:
                stream.close()
    require(not errors, "; ".join(errors))
    return process.returncode, outputs.get("stdout", b""), outputs.get("stderr", b"")


def _git(root, arguments, deadline, *, input_bytes=b"", limit=MAX_LISTING, allowed_codes=(0,)):
    executable = shutil.which("git")
    require(executable is not None, "existing Git executable is required")
    result = _process([executable, "--no-replace-objects", "--no-lazy-fetch", "-c", "safe.directory=" + str(root),
                       "-C", str(root), *arguments],
                      cwd=root, env=git_environment(os.environ),
                      timeout=min(GIT_TIMEOUT, deadline - time.monotonic()), stdout_limit=limit,
                      stderr_limit=MAX_GIT_ERROR, input_bytes=input_bytes)
    code, stdout, stderr = result
    require(code in allowed_codes, "local Git failed: " + stderr.decode("utf-8", errors="replace")[:2000])
    return code, stdout


def extract_tree(root, tree, recipe_id, recipe, deadline):
    _, top = _git(root, ["rev-parse", "--show-toplevel"], deadline)
    require(Path(top.decode("utf-8").strip()).resolve() == root, "Git repository root differs")
    code, _ = _git(root, ["config", "--local", "--get-regexp",
                          r"^(extensions\.partialclone|remote\..*\.promisor)$"], deadline, allowed_codes=(0, 1))
    require(code == 1, "promisor/partial-clone repositories are not supported")
    commit = recipe["commit"]
    require(type(commit) is str and HEX40.fullmatch(commit), "invalid registered commit")
    _, resolved = _git(root, ["rev-parse", "--verify", commit + "^{commit}"], deadline)
    require(resolved == (commit + "\n").encode("ascii"), "registered local commit is missing or differs")
    _, tree_raw = _git(root, ["rev-parse", "--verify", commit + "^{tree}"], deadline)
    tree_oid = tree_raw.decode("ascii").strip()
    require(HEX40.fullmatch(tree_oid), "invalid Git tree identity")
    _, listing = _git(root, ["ls-tree", "-r", "-z", "--full-tree", commit], deadline)
    entries = parse_tree(listing)
    objects = sorted({entry["oid"] for entry in entries})
    _, batch = _git(root, ["cat-file", "--batch"], deadline,
                    input_bytes="".join(oid + "\n" for oid in objects).encode("ascii"),
                    limit=MAX_TOTAL + MAX_FILES * 128)
    source, bodies = io.BytesIO(batch), {}
    for oid in objects:
        bodies[oid] = read_blob(source, oid)
    require(source.read(1) == b"", "unexpected trailing batch bytes")
    total = sum(len(bodies[row["oid"]]) for row in entries)
    require(total <= MAX_TOTAL, "total tracked byte limit exceeded")
    tree.mkdir(exist_ok=False)
    for row in entries:
        target = tree / row["path"]
        require(target.resolve().is_relative_to(tree.resolve()), "extraction path escaped tree")
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = bodies[row["oid"]]
        write_new(target, raw)
        row.update(size=len(raw), sha256=sha(raw))
    return {"schema": "pinned-tree-manifest-v1", "recipe": recipe_id, "commit": commit,
            "tree_oid": tree_oid, "total_bytes": total, "files": entries}


def verify_tree(tree, manifest):
    require(type(manifest) is dict and set(manifest) == {"schema", "recipe", "commit", "tree_oid", "total_bytes", "files"}
            and manifest["schema"] == "pinned-tree-manifest-v1", "manifest schema differs")
    require(type(manifest["files"]) is list and 0 < len(manifest["files"]) <= MAX_FILES, "manifest population differs")
    entries = manifest["files"]
    encoded = []
    total = 0
    for row in entries:
        require(type(row) is dict and set(row) == {"path", "mode", "oid", "size", "sha256"}, "manifest file schema differs")
        require(type(row["size"]) is int and 0 <= row["size"] <= MAX_BLOB, "manifest file size differs")
        require(type(row["sha256"]) is str and HEX64.fullmatch(row["sha256"]), "manifest hash differs")
        encoded.append(f'{row["mode"]} blob {row["oid"]}\t{row["path"]}\0'.encode())
        total += row["size"]
    parsed = parse_tree(b"".join(encoded))
    require([row["path"] for row in parsed] == [row["path"] for row in entries], "manifest is not in canonical order")
    require(type(manifest["total_bytes"]) is int and total == manifest["total_bytes"] <= MAX_TOTAL,
            "manifest byte total differs")
    actual = []
    for path in tree.rglob("*"):
        _no_reparse_ancestors(path)
        if path.is_file():
            actual.append(path.relative_to(tree).as_posix())
        else:
            require(path.is_dir(), "unexpected extracted special file")
    require(sorted(actual) == [row["path"] for row in entries], "extracted tree membership differs")
    for row in entries:
        raw = (tree / row["path"]).read_bytes()
        require(len(raw) == row["size"] and sha(raw) == row["sha256"], "extracted file bytes differ")
        require(hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest() == row["oid"],
                "extracted Git blob identity differs")


def _recipe_identities(tree, recipe):
    require(recipe["adapter"] in {"revision", "sealed"} and type(recipe["third_party"]) is bool
            and recipe["third_party"] == (recipe["adapter"] == "revision"), "invalid recipe adapter")
    for name in ("report", "html"):
        if name + "_path" in recipe:
            relative = recipe[name + "_path"]
            _path_key(relative)
            require(sha((tree / relative).read_bytes()) == recipe[name + "_sha256"], "registered " + name + " bytes differ")


def _dependency_dirs(recipe):
    if not recipe["third_party"]:
        return []
    values = sysconfig.get_paths()
    return sorted({str(Path(values[key]).resolve()) for key in ("purelib", "platlib")})


def _module_origins(tree, finder, manifest):
    files = {row["path"]: row["sha256"] for row in manifest["files"]}
    result = {}
    for name, module in tuple(sys.modules.items()):
        if not (name == "alpha_research_rl" or name.startswith("alpha_research_rl.")
                or name in finder.helpers or name in {"pinned_sealed_confirmation_runner", "pinned_revision_entrypoint"}):
            continue
        origin = getattr(module, "__file__", None)
        require(origin is not None, "project module has no source origin")
        path = Path(origin).resolve()
        require(path.is_relative_to(tree), "loaded project module escaped historical tree")
        relative = path.relative_to(tree).as_posix()
        require(relative in files and sha(path.read_bytes()) == files[relative], "loaded source bytes differ from manifest")
        for location in getattr(module, "__path__", ()):
            require(Path(location).resolve().is_relative_to(tree), "loaded package path escaped tree")
        result[name] = {"path": relative, "sha256": files[relative]}
    return result


def validate_child_proof(recipe, proof, manifest):
    require(type(proof) is dict and set(proof) == {"schema", "import_origins", "runtime", "prohibited_operations",
            "guard_scope", "scratch_writes_permitted"} and proof["schema"] == "pinned-replay-child-v1",
            "child proof schema differs")
    require(type(proof["prohibited_operations"]) is list and not proof["prohibited_operations"]
            and proof["guard_scope"] == GUARD_SCOPE, "child guard proof differs")
    require(type(proof["scratch_writes_permitted"]) is bool
            and proof["scratch_writes_permitted"] == (recipe["adapter"] == "revision"), "child scratch scope differs")
    origins = proof["import_origins"]
    require(type(origins) is dict, "child origins must be an object")
    entry_name = "pinned_revision_entrypoint" if recipe["adapter"] == "revision" else "pinned_sealed_confirmation_runner"
    entry_path = "scripts/replay_published_astra_revision.py" if recipe["adapter"] == "revision" else "scripts/check_sealed_confirmation.py"
    required = {"alpha_research_rl": "src/alpha_research_rl/__init__.py", entry_name: entry_path}
    if recipe["adapter"] == "revision":
        required["replay_published_results"] = "scripts/replay_published_results.py"
    require(set(required) <= set(origins), "required historical import origin missing")
    files = {row["path"]: row["sha256"] for row in manifest["files"]}
    for name, item in origins.items():
        require(type(name) is str and (name in required or name.startswith("alpha_research_rl.")), "unexpected project origin")
        require(type(item) is dict and set(item) == {"path", "sha256"}, "origin entry schema differs")
        _path_key(item["path"])
        require(item["path"] in files and item["sha256"] == files[item["path"]], "origin manifest identity differs")
        if name in required:
            require(item["path"] == required[name], "entrypoint origin path differs")
        else:
            base = "src/" + name.replace(".", "/")
            require(item["path"] in {base + ".py", base + "/__init__.py"}, "package origin path differs")
    runtime = proof["runtime"]
    require(type(runtime) is dict and set(runtime) == {"python", "implementation", "platform", "third_party_versions",
                                                       "third_party_origins"},
            "runtime proof schema differs")
    for key in ("python", "implementation"):
        require(type(runtime[key]) is str and runtime[key].strip(), "runtime identity missing")
    require(type(runtime["platform"]) is dict and set(runtime["platform"]) == {"system", "release", "machine"}
            and all(type(value) is str and value.strip() for value in runtime["platform"].values()), "platform identity missing")
    versions = runtime["third_party_versions"]
    expected_packages = {"numpy", "scipy"} if recipe["third_party"] else set()
    require(type(versions) is dict and set(versions) == expected_packages
            and all(type(value) is str and value.strip() for value in versions.values()), "dependency identity differs")
    dependency_origins = runtime["third_party_origins"]
    require(type(dependency_origins) is dict and set(dependency_origins) == expected_packages, "dependency origins differ")
    for package, origin in dependency_origins.items():
        require(type(origin) is dict and set(origin) == {"dependency_directory_index", "relative_path"},
                "dependency origin schema differs")
        require(type(origin["dependency_directory_index"]) is int and origin["dependency_directory_index"] >= 0,
                "dependency directory index differs")
        _path_key(origin["relative_path"])
        require(origin["relative_path"].startswith(package + "/"), "dependency origin package differs")


def _child(request_path, request_hash):
    """Trusted parent-to-child capsule; not an untrusted-manifest execution API."""
    import tempfile

    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode, "child isolation flags are required")
    output = Path(__file__).resolve().parent
    require(Path(__file__).name == "bootstrap.py" and Path(request_path).resolve() == output / "child-request.json",
            "internal child requires a retained capsule request")
    raw = (output / "child-request.json").read_bytes()
    require(sha(raw) == request_hash, "child request bytes differ")
    request = strict_json(raw)
    require(type(request) is dict and set(request) == {"schema", "recipe_id", "recipe", "manifest_sha256", "dependency_dirs"}
            and request["schema"] == "pinned-replay-request-v1", "child request schema differs")
    recipe = request["recipe"]
    fields = {"commit", "adapter", "report_path", "report_sha256", "expected_summary", "third_party"}
    require(type(recipe) is dict and set(recipe) in (fields, fields | {"html_path", "html_sha256"}), "recipe schema differs")
    require(recipe["adapter"] in {"revision", "sealed"}, "unknown fixed adapter")
    manifest_raw = (output / "tree-manifest.json").read_bytes()
    require(sha(manifest_raw) == request["manifest_sha256"], "child manifest bytes differ")
    manifest = strict_json(manifest_raw)
    require(manifest["commit"] == recipe["commit"] and manifest["recipe"] == request["recipe_id"], "manifest identity differs")
    started = strict_json((output / "STARTED.json").read_bytes())
    require(started["recipe"] == request["recipe_id"] and started["commit"] == recipe["commit"], "capsule start differs")
    tree, scratch = output / "tree", output / "scratch"
    require(tree.is_dir() and scratch.is_dir() and not (output / "child-proof.json").exists(), "child is not a fresh capsule")
    verify_tree(tree, manifest)
    _recipe_identities(tree, recipe)
    directories = request["dependency_dirs"]
    require(type(directories) is list and all(type(p) is str and Path(p).is_absolute() and Path(p).is_dir()
                                            for p in directories), "invalid existing dependency directories")
    require(recipe["third_party"] or not directories, "stdlib recipe cannot add dependency directories")
    require(not any(name == "alpha_research_rl" or name.startswith("alpha_research_rl.") for name in sys.modules),
            "project imported before historical isolation")
    # -I -S gives stdlib-only startup. No addsitedir/.pth or current-checkout path.
    stdlib_paths = list(sys.path)
    sys.path[:] = [str(tree / "src"), *stdlib_paths, *directories]
    finder = HistoricalFinder(tree, recipe["adapter"])
    sys.meta_path.insert(0, finder)
    tempfile.tempdir = str(scratch)
    for name in ("TMPDIR", "TEMP", "TMP"):
        os.environ[name] = str(scratch)
    host = platform.uname()  # May invoke the Windows version command; outside replay guards.
    runtime = {"python": sys.version, "implementation": sys.implementation.name,
               "platform": {"system": host.system, "release": host.release, "machine": host.machine},
               "third_party_versions": {}, "third_party_origins": {}}
    active = True
    prohibited = []
    scoring = {"alpha_research_rl.financial_tasks", "alpha_research_rl.financial_policy",
               "alpha_research_rl.evaluation", "alpha_research_rl.french", "alpha_research_rl.astra_study",
               "alpha_research_rl.llm"}

    def deny(label):
        prohibited.append(label)
        raise ReplayError("replay guard: " + label)

    class NoScoring(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split(".")[0] in {"torch", "transformers", "peft", "accelerate"} or any(
                fullname == value or fullname.startswith(value + ".") for value in scoring
            ):
                deny("model/market import " + fullname)

    sys.meta_path.insert(0, NoScoring())

    def located(value, dir_fd=None):
        require(isinstance(value, (str, bytes, os.PathLike)), "unsupported filesystem descriptor")
        path = Path(os.fsdecode(value))
        if not path.is_absolute() and dir_fd not in (None, -1):
            # Linux's stdlib rmtree uses fd-relative unlink/rmdir; Windows uses paths.
            require(type(dir_fd) is int and sys.platform.startswith("linux"), "unsupported fd-relative filesystem action")
            path = Path(os.readlink("/proc/self/fd/" + str(dir_fd))) / path
        return path.resolve()

    readable = [tree, scratch, *[Path(p).resolve() for p in stdlib_paths if p],
                *[Path(p).resolve() for p in directories]]
    forbidden = [tree / name for name in (".local", "models", "data/raw", "data/cache", "artifacts/private")]

    def audit(event, args):
        if not active:
            return
        if event.startswith("socket.") or event in {"urllib.Request", "http.client.connect", "http.client.send",
                "subprocess.Popen", "os.system", "os.posix_spawn", "os.exec", "os.fork", "os.startfile", "os.startfile/2"}:
            deny("network/process " + event)
        if event == "open":
            path = located(args[0])
            mode, flags = args[1:3]
            writing = ((isinstance(mode, str) and any(c in mode for c in "wax+")) or
                       (isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)))
            if writing and (recipe["adapter"] == "sealed" or not path.is_relative_to(scratch)):
                deny("write outside scratch")
            if not writing and (not any(path == p or path.is_relative_to(p) for p in readable) or
                                any(path == p or path.is_relative_to(p) for p in forbidden)):
                deny("read outside public/runtime scope")
        if event in {"os.remove", "os.rmdir", "os.mkdir", "os.chmod", "os.utime", "os.truncate", "shutil.rmtree"}:
            fd_index = {"os.remove": 1, "os.rmdir": 1, "os.mkdir": 2, "os.chmod": 2, "os.utime": 3,
                        "shutil.rmtree": 1}.get(event)
            fd = args[fd_index] if fd_index is not None and len(args) > fd_index else None
            if recipe["adapter"] == "sealed" or not located(args[0], fd).is_relative_to(scratch):
                deny("mutation outside scratch")
        if event in {"os.rename", "os.link", "os.symlink"}:
            for index in (0, 1):
                fd = args[index + 2] if event != "os.symlink" and len(args) > index + 2 else None
                if recipe["adapter"] == "sealed" or not located(args[index], fd).is_relative_to(scratch):
                    deny("link/rename outside scratch")

    sys.addaudithook(audit)
    entry = "scripts/replay_published_astra_revision.py" if recipe["adapter"] == "revision" else "scripts/check_sealed_confirmation.py"
    name = "pinned_revision_entrypoint" if recipe["adapter"] == "revision" else "pinned_sealed_confirmation_runner"
    spec = importlib.util.spec_from_file_location(name, tree / entry)
    require(spec is not None and spec.loader is not None, "historical entrypoint is missing")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    _module_origins(tree, finder, manifest)
    if recipe["adapter"] == "sealed":
        def forbidden_call(*args, **kwargs):
            deny("sealed generation/execution/write helper")
        for attribute in ("feature_bits", "generate_inputs", "prepare", "run", "write_once", "EventWriter"):
            require(hasattr(module, attribute), "sealed guard target is missing")
            setattr(module, attribute, forbidden_call)
        hashlib.shake_256 = forbidden_call
        module.main(["--root", str(tree), "replay"])
    else:
        module.main()
    require(not prohibited, "a prohibited action was caught by historical code")
    origins = _module_origins(tree, finder, manifest)
    require("alpha_research_rl" in origins and name in origins, "historical verifier/package was not loaded")
    for package in ("numpy", "scipy"):
        if package in sys.modules:
            dependency = sys.modules[package]
            runtime["third_party_versions"][package] = dependency.__version__
            origin = Path(dependency.__file__).resolve()
            locations = [(i, origin.relative_to(Path(p).resolve()).as_posix()) for i, p in enumerate(directories)
                         if origin.is_relative_to(Path(p).resolve())]
            require(locations, "third-party origin escaped explicit installed directories")
            index, relative = locations[0]
            runtime["third_party_origins"][package] = {"dependency_directory_index": index, "relative_path": relative}
    expected_packages = {"numpy", "scipy"} if recipe["third_party"] else set()
    require(set(runtime["third_party_versions"]) == expected_packages, "required dependency import population differs")
    active = False
    verify_tree(tree, manifest)
    write_new(output / "child-proof.json", {"schema": "pinned-replay-child-v1", "import_origins": origins,
              "runtime": runtime, "prohibited_operations": prohibited,
              "guard_scope": GUARD_SCOPE,
              "scratch_writes_permitted": recipe["adapter"] == "revision"})


def run_pinned(recipe_id, output_dir, *, repository_root=None):
    require(recipe_id in RECIPES, "unknown registered recipe")
    recipe = strict_json(canonical(RECIPES[recipe_id]))
    root = (ROOT if repository_root is None else Path(repository_root)).resolve()
    output = _output_path(root, output_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir(exist_ok=False)
    began, started = time.monotonic(), utc()
    deadline, stage, child_code = began + TOTAL_TIMEOUT, "started", None
    try:
        write_new(output / "STARTED.json", {"schema": "pinned-replay-start-v1", "recipe": recipe_id,
                  "commit": recipe["commit"], "started_utc": started})
        stage = "extract"
        manifest = extract_tree(root, output / "tree", recipe_id, recipe, deadline)
        write_new(output / "tree-manifest.json", manifest)
        _recipe_identities(output / "tree", recipe)
        verify_tree(output / "tree", manifest)
        (output / "scratch").mkdir()
        bootstrap = Path(__file__).read_bytes()
        write_new(output / "bootstrap.py", bootstrap)
        request = {"schema": "pinned-replay-request-v1", "recipe_id": recipe_id, "recipe": recipe,
                   "manifest_sha256": sha((output / "tree-manifest.json").read_bytes()),
                   "dependency_dirs": _dependency_dirs(recipe)}
        write_new(output / "child-request.json", request)
        request_raw = (output / "child-request.json").read_bytes()
        env = {key: value for key, value in os.environ.items() if not key.upper().startswith("PYTHON")}
        env.update(TMP=str(output / "scratch"), TEMP=str(output / "scratch"), TMPDIR=str(output / "scratch"))
        stage = "child"
        child_code, stdout, _ = _process(
            [sys.executable, "-I", "-S", "-B", str(output / "bootstrap.py"), "--_child",
             str(output / "child-request.json"), sha(request_raw)], cwd=output / "tree", env=env,
            timeout=min(CHILD_TIMEOUT, deadline - time.monotonic()), stdout_limit=MAX_LOG, stderr_limit=MAX_LOG,
            stdout_path=output / "stdout.txt", stderr_path=output / "stderr.txt")
        require(child_code == 0, "historical child failed; inspect retained stderr")
        stage = "verify"
        summary = strict_json(stdout)
        validate_summary(recipe, summary)
        proof = strict_json((output / "child-proof.json").read_bytes())
        validate_child_proof(recipe, proof, manifest)
        require(all(value["dependency_directory_index"] < len(request["dependency_dirs"])
                    for value in proof["runtime"]["third_party_origins"].values()), "dependency directory index is out of range")
        verify_tree(output / "tree", manifest)
        require(time.monotonic() <= deadline, "whole invocation deadline exceeded")
        complete = {"schema": "pinned-saved-replay-v1", "status": "VERIFIED_PINNED_SAVED_REPLAY",
                    "recipe": recipe_id, "commit": recipe["commit"], "report_sha256": recipe["report_sha256"],
                    "child_summary": summary, "child_exit_code": child_code,
                    "manifest_sha256": request["manifest_sha256"], "bootstrap_sha256": sha(bootstrap),
                    "import_origins": proof["import_origins"], "runtime": proof["runtime"],
                    "started_utc": started, "ended_utc": utc(), "elapsed_seconds": time.monotonic() - began,
                    "tracked_files_unchanged": True}
        if "html_sha256" in recipe:
            complete["html_sha256"] = recipe["html_sha256"]
        # FAILED dominates COMPLETE if a late flush/fsync raises after bytes were written.
        write_new(output / "COMPLETE.json", complete)
        return complete
    except BaseException as error:
        failure = {"schema": "pinned-replay-failure-v1", "recipe": recipe_id, "commit": recipe["commit"],
                   "stage": stage, "error_type": type(error).__name__, "error": str(error),
                   "child_exit_code": child_code, "started_utc": started, "ended_utc": utc(), "retry_permitted": False}
        if not (output / "FAILED.json").exists():
            write_new(output / "FAILED.json", failure)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipe", choices=tuple(RECIPES), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    complete = run_pinned(args.recipe, args.output)
    print(canonical({key: complete[key] for key in ("status", "recipe", "commit", "report_sha256", "elapsed_seconds")}))


if __name__ == "__main__":
    if Path(__file__).name == "bootstrap.py" and len(sys.argv) == 4 and sys.argv[1] == "--_child":
        _child(sys.argv[2], sys.argv[3])
    else:
        main()
