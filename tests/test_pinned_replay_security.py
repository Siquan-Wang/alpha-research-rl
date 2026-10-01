"""Independent artificial extraction/lifecycle checks; no historical replay or Git calls."""

import hashlib
import importlib.util
import io
import os
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "replay_pinned_study.py"
SPEC = importlib.util.spec_from_file_location("pinned_replay_security_subject", SCRIPT)
launcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launcher)


def entry(path, *, mode="100644", kind="blob", oid="a" * 40):
    name = path.encode("utf-8") if isinstance(path, str) else path
    return f"{mode} {kind} {oid}\t".encode("ascii") + name + b"\0"


def blob(raw):
    oid = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    return oid, f"{oid} blob {len(raw)}\n".encode("ascii") + raw + b"\n"


def test_manifest_preserves_utf8_names_mode_and_order_independent_identity():
    raw = entry("z/draft.py", mode="100755", oid="b" * 40) + entry("données/原样.txt")
    expected = [
        {"path": "données/原样.txt", "mode": "100644", "oid": "a" * 40},
        {"path": "z/draft.py", "mode": "100755", "oid": "b" * 40},
    ]
    assert launcher.parse_tree(raw) == expected
    assert launcher.parse_tree(entry("données/原样.txt") + entry(
        "z/draft.py", mode="100755", oid="b" * 40)) == expected


@pytest.mark.parametrize("paths", [
    ("docs/readme.md", "docs/readme.md"),
    ("Folder/a.py", "folder/A.py"),
    ("café/a.py", "cafe\u0301/a.py"),
    ("docs", "docs/x.txt"),
    ("DOS", "dos/x.txt"),
    ("café", "cafe\u0301/x.txt"),
])
def test_complete_manifest_rejects_aliases_and_file_directory_conflicts(paths):
    for ordered in (paths, tuple(reversed(paths))):
        with pytest.raises(launcher.ReplayError):
            launcher.parse_tree(b"".join(entry(path) for path in ordered))


@pytest.mark.parametrize("path", [
    "../escape", "/rooted", "a/../../escape", "a//b", "a/./b", "a/",
    "C:/drive", "C:relative", "//server/share", "a\\b", "a:b",
    "a/CON.txt", "LPT9", "COM¹.log", "aux", "a/NUL.txt", "file.", "dir /x",
    "a?b", 'a"b', "a<b", "a>b", "a|b", "a*b", "a\x01b", "a\x7fb",
    ".GiT/config", "pkg/__PYCACHE__/code.py", "pkg/code.PYC", "pkg/code.pyo",
    b"bad\xffname",
])
def test_unsafe_tree_path_never_reaches_materialization(path):
    with pytest.raises(launcher.ReplayError):
        launcher.parse_tree(entry(path))


@pytest.mark.parametrize("mode,kind", [
    ("120000", "blob"), ("160000", "commit"), ("040000", "tree"),
    ("100600", "blob"), ("100644", "commit"),
])
def test_git_type_and_mode_jointly_require_a_regular_blob(mode, kind):
    with pytest.raises(launcher.ReplayError):
        launcher.parse_tree(entry("safe.py", mode=mode, kind=kind))


def test_manifest_resource_caps_fail_without_partial_result(monkeypatch):
    monkeypatch.setattr(launcher, "MAX_FILES", 1)
    with pytest.raises(launcher.ReplayError):
        launcher.parse_tree(entry("a") + entry("b"))
    monkeypatch.setattr(launcher, "MAX_LISTING", 3)
    with pytest.raises(launcher.ReplayError):
        launcher.parse_tree(entry("a"))


def test_git_environment_drops_all_case_variants_of_repository_and_config_injection():
    original = {
        "PATH": "existing tools", "SystemRoot": "existing OS", "HOME": "existing home",
        "GIT_DIR": "other repository", "git_work_tree": "other checkout",
        "GIT_COMMON_DIR": "other metadata", "GIT_OBJECT_DIRECTORY": "other objects",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": "other alternates", "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "alias.fake", "GIT_CONFIG_VALUE_0": "unwanted command",
        "GIT_CONFIG_PARAMETERS": "injected config", "GIT_NO_LAZY_FETCH": "0",
        "GIT_NO_REPLACE_OBJECTS": "0", "GIT_TRACE": "unwanted log",
    }
    snapshot = original.copy()
    expected = {key: original[key] for key in ("PATH", "SystemRoot", "HOME")}
    expected.update(GIT_NO_REPLACE_OBJECTS="1", GIT_NO_LAZY_FETCH="1",
                    GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")
    assert launcher.git_environment(original) == expected
    assert original == snapshot


def test_blob_reader_handles_empty_binary_and_crlf_bodies_without_normalization():
    bodies = [b"", b"line\r\nline\n", bytes(range(256)), b"\n\x00\n\x00" * 13]
    packets = [blob(body) for body in bodies]
    stream = io.BytesIO(b"".join(packet for _, packet in packets))
    for raw, (oid, _) in zip(bodies, packets, strict=True):
        assert launcher.read_blob(stream, oid) == raw
    assert stream.read() == b""


@pytest.mark.parametrize("fault", ["wrong_id", "wrong_type", "bad_size", "leading_zero",
                                  "truncated_body", "missing_separator", "changed_body", "missing"])
def test_blob_protocol_rejects_malformed_or_mismatched_evidence(fault):
    oid, packet = blob(b"binary\0data\r\n")
    header, body = packet.split(b"\n", 1)
    malformed = {
        "wrong_id": b"0" * 40 + packet[40:],
        "wrong_type": header.replace(b" blob ", b" tree ") + b"\n" + body,
        "bad_size": header.rsplit(b" ", 1)[0] + b" -1\n" + body,
        "leading_zero": header.rsplit(b" ", 1)[0] + b" 013\n" + body,
        "truncated_body": packet[:-4],
        "missing_separator": packet[:-1],
        "changed_body": header + b"\n" + b"B" + body[1:],
        "missing": oid.encode("ascii") + b" missing\n",
    }[fault]
    with pytest.raises(launcher.ReplayError):
        launcher.read_blob(io.BytesIO(malformed), oid)


def test_blob_size_refusal_occurs_before_body_read(monkeypatch):
    class HeaderOnly:
        def readline(self, limit):
            assert limit <= 128
            return b"a" * 40 + b" blob 9\n"

        def read(self, count):
            pytest.fail("oversized blob body must not be read")

    monkeypatch.setattr(launcher, "MAX_BLOB", 8)
    with pytest.raises(launcher.ReplayError, match="size"):
        launcher.read_blob(HeaderOnly(), "a" * 40)


def test_output_scope_and_reuse_are_checked_without_creating_paths(tmp_path):
    root = tmp_path.resolve()
    allowed = root / ".local" / "pinned-replay-runs" / "one"
    assert launcher._output_path(root, allowed) == allowed
    assert not allowed.parent.exists()
    for path in (root / "wrong" / "one", allowed / "nested", allowed.parent / ".." / "elsewhere"):
        with pytest.raises(launcher.ReplayError):
            launcher._output_path(root, path)
    allowed.mkdir(parents=True)
    marker = allowed / "STARTED.json"
    marker.write_bytes(b"retained")
    with pytest.raises(launcher.ReplayError, match="already exists"):
        launcher._output_path(root, allowed)
    assert marker.read_bytes() == b"retained"


def test_output_ancestor_symlink_is_rejected_before_resolving_to_an_allowed_name(tmp_path):
    root = tmp_path.resolve()
    real = root / "real"
    real.mkdir()
    redirect = root / ".local"
    try:
        redirect.symlink_to(real, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"Symlink creation unavailable on this host: {error.winerror if os.name == 'nt' else error.errno}")
    with pytest.raises(launcher.ReplayError, match="symlink|junction"):
        launcher._output_path(root, redirect / "pinned-replay-runs" / "one")
    assert list(real.iterdir()) == []


def test_every_git_query_passes_restrictions_and_sanitized_environment(tmp_path, monkeypatch):
    captured = []

    def fake_process(argv, **options):
        captured.append((argv, options))
        return 0, b"saved object output", b""

    monkeypatch.setattr(launcher.shutil, "which", lambda name: "existing-git" if name == "git" else None)
    monkeypatch.setattr(launcher, "_process", fake_process)
    monkeypatch.setenv("GIT_DIR", "wrong repository")
    monkeypatch.setenv("GIT_CONFIG_PARAMETERS", "injected settings")
    code, raw = launcher._git(tmp_path, ["cat-file", "--batch"], launcher.time.monotonic() + 30,
                              input_bytes=b"a" * 40 + b"\n")
    assert (code, raw) == (0, b"saved object output")
    assert len(captured) == 1
    argv, options = captured[0]
    assert argv == ["existing-git", "--no-replace-objects", "--no-lazy-fetch", "-c", "safe.directory=" + str(tmp_path),
                    "-C", str(tmp_path),
                    "cat-file", "--batch"]
    assert options["cwd"] == tmp_path
    assert "GIT_DIR" not in options["env"] and "GIT_CONFIG_PARAMETERS" not in options["env"]
    assert options["env"]["GIT_NO_LAZY_FETCH"] == options["env"]["GIT_NO_REPLACE_OBJECTS"] == "1"
    assert 0 < options["timeout"] <= 30
    assert options["input_bytes"] == b"a" * 40 + b"\n"


def artificial_git(root, files):
    """Exact handwritten local-object protocol; no Git executable or repository."""
    commit, tree_id = "c" * 40, "d" * 40
    packets = {blob(raw)[0]: blob(raw)[1] for raw in files.values()}
    listing = b"".join(entry(path, oid=blob(raw)[0]) for path, raw in reversed(tuple(files.items())))
    calls = []

    def respond(supplied_root, arguments, deadline, **options):
        assert supplied_root == root
        assert deadline > 0
        calls.append((arguments, options))
        if arguments == ["rev-parse", "--show-toplevel"]:
            return 0, (str(root) + "\n").encode("utf-8")
        if arguments[:3] == ["config", "--local", "--get-regexp"]:
            return 1, b""
        if arguments == ["rev-parse", "--verify", commit + "^{commit}"]:
            return 0, (commit + "\n").encode("ascii")
        if arguments == ["rev-parse", "--verify", commit + "^{tree}"]:
            return 0, (tree_id + "\n").encode("ascii")
        if arguments == ["ls-tree", "-r", "-z", "--full-tree", commit]:
            return 0, listing
        assert arguments == ["cat-file", "--batch"]
        assert options["input_bytes"] == b"".join(oid.encode("ascii") + b"\n" for oid in sorted(packets))
        return 0, b"".join(packets[oid] for oid in sorted(packets))

    return respond, calls, {"commit": commit}, tree_id


def test_extraction_uses_raw_blob_bytes_deduplicates_requests_and_binds_every_file(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    files = {".gitattributes": b"*.txt export-subst\n", "a.txt": b"$Format:%H$\r\n\0",
             "nested/b.txt": b"$Format:%H$\r\n\0"}
    fake_git, calls, recipe, tree_id = artificial_git(root, files)
    monkeypatch.setattr(launcher, "_git", fake_git)
    tree = root / "tree"
    manifest = launcher.extract_tree(root, tree, "artificial-only", recipe, 100)
    assert len(calls) == 6
    assert manifest["tree_oid"] == tree_id and manifest["commit"] == recipe["commit"]
    assert manifest["total_bytes"] == sum(map(len, files.values()))
    assert {path.relative_to(tree).as_posix(): path.read_bytes() for path in tree.rglob("*") if path.is_file()} == files
    for row in manifest["files"]:
        raw = files[row["path"]]
        assert row == {"path": row["path"], "mode": "100644", "oid": blob(raw)[0],
                       "size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    launcher.verify_tree(tree, manifest)
    (tree / "a.txt").write_bytes(files["a.txt"].replace(b"\r\n", b"\n"))
    with pytest.raises(launcher.ReplayError, match="bytes differ"):
        launcher.verify_tree(tree, manifest)


def test_duplicate_blob_files_count_against_total_extraction_limit(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    fake_git, _, recipe, _ = artificial_git(root, {"one": b"12345", "two": b"12345"})
    monkeypatch.setattr(launcher, "_git", fake_git)
    monkeypatch.setattr(launcher, "MAX_TOTAL", 9)
    with pytest.raises(launcher.ReplayError, match="total tracked byte"):
        launcher.extract_tree(root, root / "tree", "artificial-only", recipe, 100)
    assert not (root / "tree").exists()


def test_failed_stderr_persistence_cannot_be_reported_as_success(tmp_path, monkeypatch):
    class BrokenLog(io.BytesIO):
        def flush(self):
            raise OSError("artificial log persistence failure")

    class FakeProcess:
        def __init__(self, *args, **kwargs):
            self.stdin, self.stdout, self.stderr = io.BytesIO(), io.BytesIO(b"{}"), io.BytesIO(b"warning")
            self.returncode = 0

        def wait(self, timeout):
            return self.returncode

        def poll(self):
            return self.returncode

        def kill(self):
            self.returncode = -9

    target = tmp_path / "stderr.log"
    original_open = Path.open

    def open_log(path, *args, **kwargs):
        return BrokenLog() if path == target else original_open(path, *args, **kwargs)

    monkeypatch.setattr(launcher.subprocess, "Popen", FakeProcess)
    monkeypatch.setattr(Path, "open", open_log)
    with pytest.raises(launcher.ReplayError):
        launcher._process(["artificial-only"], cwd=tmp_path, env={}, timeout=1,
                          stdout_limit=100, stderr_limit=100, stderr_path=target)


def fake_capsule(tmp_path, monkeypatch, *, fault=None):
    """Parent-only artificial lifecycle; the process and Git are both replaced."""
    # Keep artificial capsule trees within the same now-enforced Windows limits.
    root = tmp_path.parent / ("r" + hashlib.sha256(tmp_path.name.encode()).hexdigest()[:8])
    root.mkdir()
    root = root.resolve()
    report_path, report_raw = "results/artificial.json", b'{"artificial_only":true}\n'
    files = {report_path: report_raw, "src/alpha_research_rl/__init__.py": b"# artificial only\n",
             "scripts/check_sealed_confirmation.py": b"# never executed\n"}
    fake_git, git_calls, recipe_stub, _ = artificial_git(root, files)
    recipe = launcher._recipe(recipe_stub["commit"], "sealed", report_path, hashlib.sha256(report_raw).hexdigest())
    monkeypatch.setattr(launcher, "RECIPES", {"artificial-only": recipe})
    monkeypatch.setattr(launcher, "_git", fake_git)
    output = root / ".local" / "pinned-replay-runs" / "artificial"
    process_calls = []

    def fake_child(argv, **options):
        process_calls.append((argv, options))
        assert argv[:4] == [launcher.sys.executable, "-I", "-S", "-B"]
        assert options["cwd"] == output / "tree"
        request = launcher.strict_json((output / "child-request.json").read_bytes())
        assert options["env"]["TEMP"] == str(root / request["scratch_relative"])
        launcher.write_new(options["stdout_path"], b"retained child stdout\n")
        launcher.write_new(options["stderr_path"], b"retained child stderr\n")
        if fault == "interruption":
            raise KeyboardInterrupt("artificial interruption")
        if fault == "bad_summary":
            return 0, b"{}", b"retained child stderr\n"
        origins = {
            "alpha_research_rl": {"path": "src/alpha_research_rl/__init__.py",
                                  "sha256": hashlib.sha256(files["src/alpha_research_rl/__init__.py"]).hexdigest()},
            "pinned_sealed_confirmation_runner": {"path": "scripts/check_sealed_confirmation.py",
                "sha256": hashlib.sha256(files["scripts/check_sealed_confirmation.py"]).hexdigest()},
        }
        proof = {"schema": "pinned-replay-child-v1", "import_origins": origins,
                 "runtime": {"python": "artificial test", "implementation": "cpython",
                    "platform": {"system": "artificial", "release": "test", "machine": "test"},
                    "third_party_versions": {}, "third_party_origins": {}},
                 "prohibited_operations": [],
                 "guard_scope": "Local Python instrumentation; not an adversarial sandbox. Platform preflight precedes guards.",
                 "scratch_writes_permitted": False, "scratch_relative": request["scratch_relative"]}
        launcher.write_new(output / "child-proof.json", proof)
        if fault == "changed_tree":
            (output / "tree" / "extra.py").write_bytes(b"# unexpected")
        return 0, launcher.canonical(recipe["expected_summary"]).encode("ascii"), b"retained child stderr\n"

    monkeypatch.setattr(launcher, "_process", fake_child)
    return root, output, process_calls, git_calls


def test_artificial_success_is_exclusive_and_preserves_original_capsule(tmp_path, monkeypatch):
    root, output, process_calls, git_calls = fake_capsule(tmp_path, monkeypatch)
    complete = launcher.run_pinned("artificial-only", output, repository_root=root)
    assert complete["status"] == "VERIFIED_PINNED_SAVED_REPLAY"
    assert len(process_calls) == 1 and len(git_calls) == 6
    assert (output / "STARTED.json").exists() and (output / "COMPLETE.json").exists()
    assert not (output / "FAILED.json").exists()
    assert launcher.validate_scratch(root, output, complete["scratch_relative"], "artificial-only", "c" * 40).is_dir()
    original = {p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()}
    with pytest.raises(launcher.ReplayError, match="already exists"):
        launcher.run_pinned("artificial-only", output, repository_root=root)
    assert len(process_calls) == 1 and len(git_calls) == 6
    assert {p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()} == original


@pytest.mark.parametrize("fault,error_type", [("bad_summary", launcher.ReplayError),
                                              ("changed_tree", launcher.ReplayError),
                                              ("interruption", KeyboardInterrupt)])
def test_artificial_failure_retains_evidence_and_never_retries(tmp_path, monkeypatch, fault, error_type):
    root, output, process_calls, _ = fake_capsule(tmp_path, monkeypatch, fault=fault)
    with pytest.raises(error_type):
        launcher.run_pinned("artificial-only", output, repository_root=root)
    assert len(process_calls) == 1 and not (output / "COMPLETE.json").exists()
    failure = launcher.strict_json((output / "FAILED.json").read_bytes())
    assert failure["retry_permitted"] is False
    assert launcher.validate_scratch(root, output, failure["scratch_relative"], "artificial-only", "c" * 40).is_dir()
    assert (output / "tree-manifest.json").exists()
    assert (output / "stdout.txt").read_bytes() == b"retained child stdout\n"
    assert (output / "stderr.txt").read_bytes() == b"retained child stderr\n"
    with pytest.raises(launcher.ReplayError, match="already exists"):
        launcher.run_pinned("artificial-only", output, repository_root=root)
    assert len(process_calls) == 1


def test_missing_local_object_stops_before_child_and_keeps_started_failure(tmp_path, monkeypatch):
    root, output, process_calls, _ = fake_capsule(tmp_path, monkeypatch)
    requests = []

    def no_object(*args, **kwargs):
        requests.append((args, kwargs))
        raise launcher.ReplayError("artificial absent local object; no fetch")

    monkeypatch.setattr(launcher, "_git", no_object)
    with pytest.raises(launcher.ReplayError, match="absent local object"):
        launcher.run_pinned("artificial-only", output, repository_root=root)
    assert len(requests) == 1 and process_calls == []
    assert (output / "STARTED.json").exists() and (output / "FAILED.json").exists()
    assert not (output / "COMPLETE.json").exists() and not (output / "tree").exists()


def test_failed_completion_persistence_is_failure_even_if_complete_bytes_exist(tmp_path, monkeypatch):
    root, output, process_calls, _ = fake_capsule(tmp_path, monkeypatch)
    ordinary_write = launcher.write_new

    def fail_after_complete_bytes(path, value):
        ordinary_write(path, value)
        if Path(path).name == "COMPLETE.json":
            raise OSError("artificial completion persistence failure")

    monkeypatch.setattr(launcher, "write_new", fail_after_complete_bytes)
    with pytest.raises(OSError, match="completion persistence"):
        launcher.run_pinned("artificial-only", output, repository_root=root)
    assert (output / "COMPLETE.json").exists() and (output / "FAILED.json").exists()
    failure = launcher.strict_json((output / "FAILED.json").read_bytes())
    assert failure["stage"] == "verify" and failure["retry_permitted"] is False
    assert len(process_calls) == 1
    with pytest.raises(launcher.ReplayError, match="already exists"):
        launcher.run_pinned("artificial-only", output, repository_root=root)
    assert len(process_calls) == 1


@pytest.mark.parametrize("fault", ["timeout", "stdout_limit"])
def test_fake_process_timeout_and_log_cap_retain_bytes_and_kill_without_retry(tmp_path, monkeypatch, fault):
    instances = []

    class FakeProcess:
        def __init__(self, *args, **kwargs):
            assert kwargs["shell"] is False
            self.stdin, self.stdout, self.stderr = io.BytesIO(), io.BytesIO(b"abcdefgh"), io.BytesIO(b"diagnostic")
            self.returncode, self.waits, self.kills = None, 0, 0
            instances.append(self)

        def wait(self, timeout):
            self.waits += 1
            if fault == "timeout" and self.waits == 1:
                raise launcher.subprocess.TimeoutExpired("artificial-only", timeout)
            if self.returncode is None:
                self.returncode = 0
            return self.returncode

        def poll(self):
            return self.returncode

        def kill(self):
            self.kills += 1
            self.returncode = -9

    monkeypatch.setattr(launcher.subprocess, "Popen", FakeProcess)
    with pytest.raises(launcher.ReplayError, match="timeout|limit exceeded"):
        launcher._process(["artificial-only"], cwd=tmp_path, env={}, timeout=1,
                          stdout_limit=100 if fault == "timeout" else 3, stderr_limit=100,
                          stdout_path=tmp_path / "stdout.log", stderr_path=tmp_path / "stderr.log")
    assert len(instances) == 1 and instances[0].kills >= 1
    assert (tmp_path / "stdout.log").read_bytes() == (b"abcdefgh" if fault == "timeout" else b"abc")
    assert (tmp_path / "stderr.log").read_bytes() == b"diagnostic"


def test_short_scratch_is_exclusive_owned_and_cannot_move_to_another_capsule(tmp_path):
    root = tmp_path.resolve()
    first = root / ".local/pinned-replay-runs/first"
    second = root / ".local/pinned-replay-runs/second"
    relative = ".local/p/0123456789abcdef"
    scratch = launcher.allocate_scratch(root, first, relative, "artificial-only", "c" * 40)
    original = (scratch / "OWNER.json").read_bytes()
    assert launcher.strict_json(original) == {
        "schema": "pinned-scratch-owner-v1", "capsule_relative": ".local/pinned-replay-runs/first",
        "recipe": "artificial-only", "commit": "c" * 40, "scratch_relative": relative,
    }
    assert launcher.validate_scratch(root, first, relative, "artificial-only", "c" * 40) == scratch
    with pytest.raises(launcher.ReplayError, match="no reuse"):
        launcher.allocate_scratch(root, first, relative, "artificial-only", "c" * 40)
    for output, recipe, commit in ((second, "artificial-only", "c" * 40),
                                   (first, "other-recipe", "c" * 40), (first, "artificial-only", "d" * 40)):
        with pytest.raises(launcher.ReplayError, match="ownership differs"):
            launcher.validate_scratch(root, output, relative, recipe, commit)
    assert (scratch / "OWNER.json").read_bytes() == original


@pytest.mark.parametrize("relative", [".local/p/ABCDEF0123456789", ".local/p/0123456789abcde",
                                      ".local/p/0123456789abcdef/extra", ".local/p/../escape",
                                      ".local\\p\\0123456789abcdef", "/.local/p/0123456789abcdef"])
def test_scratch_reference_must_be_one_exact_relative_engineering_nonce(tmp_path, relative):
    root = tmp_path.resolve()
    with pytest.raises(launcher.ReplayError, match="scratch reference"):
        launcher.allocate_scratch(root, root / ".local/pinned-replay-runs/x", relative,
                                  "artificial-only", "c" * 40)
    assert list(root.iterdir()) == []


def test_corrupted_scratch_owner_cannot_validate_as_available_scratch(tmp_path):
    root = tmp_path.resolve()
    output, relative = root / ".local/pinned-replay-runs/one", ".local/p/0123456789abcdef"
    scratch = launcher.allocate_scratch(root, output, relative, "artificial-only", "c" * 40)
    owner = launcher.strict_json((scratch / "OWNER.json").read_bytes())
    owner["scratch_relative"] = ".local/p/fedcba9876543210"
    (scratch / "OWNER.json").write_bytes(launcher.canonical(owner).encode("ascii"))
    with pytest.raises(launcher.ReplayError, match="ownership differs"):
        launcher.validate_scratch(root, output, relative, "artificial-only", "c" * 40)


def test_windows_path_budget_counts_utf16_and_separately_limits_parent_directory():
    tree, scratch = Path("C:/artificial/tree"), Path("C:/artificial/s")
    units = lambda path: len(str(path).encode("utf-16-le")) // 2
    max_filename = "x" * (259 - units(tree) - 1)
    launcher.check_path_budget(tree, scratch, [{"path": max_filename}], snapshots=False, windows=True)
    with pytest.raises(launcher.ReplayError, match="path budget"):
        launcher.check_path_budget(tree, scratch, [{"path": max_filename + "x"}], snapshots=False, windows=True)
    directory = "x" * (247 - units(tree) - 1)
    launcher.check_path_budget(tree, scratch, [{"path": directory + "/f"}], snapshots=False, windows=True)
    with pytest.raises(launcher.ReplayError, match="path budget"):
        launcher.check_path_budget(tree, scratch, [{"path": directory + "x/f"}], snapshots=False, windows=True)
    # Python character count fits while UTF-16 count exceeds the file limit.
    astral = "🙂" * ((259 - units(tree)) // 2 + 1)
    assert len(str(tree / astral)) < 259
    with pytest.raises(launcher.ReplayError, match="path budget"):
        launcher.check_path_budget(tree, scratch, [{"path": astral}], snapshots=False, windows=True)


def test_snapshot_projection_reserves_temp_component_before_any_file_is_created():
    tree, scratch = Path("C:/artificial/tree"), Path("C:/artificial/s")
    snapshot = scratch / ("t" * 32)
    suffix = "x" * (259 - len(str(snapshot).encode("utf-16-le")) // 2 - 1)
    launcher.check_path_budget(tree, scratch, [{"path": suffix}], snapshots=True, windows=True)
    with pytest.raises(launcher.ReplayError, match="path budget"):
        launcher.check_path_budget(tree, scratch, [{"path": suffix + "x"}], snapshots=True, windows=True)
    # The same extra byte is allowed for the sealed adapter, which makes no snapshots.
    launcher.check_path_budget(tree, scratch, [{"path": suffix + "x"}], snapshots=False, windows=True)


def test_short_scratch_reparse_ancestor_is_rejected_without_touching_target(tmp_path):
    root = tmp_path.resolve()
    target = root / "target"
    target.mkdir()
    (root / ".local").mkdir()
    redirect = root / ".local/p"
    try:
        redirect.symlink_to(target, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"Symlink creation unavailable on this host: {error.winerror if os.name == 'nt' else error.errno}")
    with pytest.raises(launcher.ReplayError, match="symlink|junction"):
        launcher.allocate_scratch(root, root / ".local/pinned-replay-runs/one", ".local/p/0123456789abcdef",
                                  "artificial-only", "c" * 40)
    assert list(target.iterdir()) == []
