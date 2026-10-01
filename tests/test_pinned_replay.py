"""Artificial Git snapshots only; never extract a registered historical study."""

import copy
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("pinned_author_tests", ROOT / "scripts/replay_pinned_study.py")
pinned = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pinned)


def _make_repo(tmp_path, monkeypatch, *, nested=False, precreated_root=False):
    git = shutil.which("git")
    if git is None:
        pytest.skip("artificial integration requires existing Git with strict no-lazy-fetch/no-replace flags")
    env = pinned.git_environment(dict(pinned.os.environ))
    probe = subprocess.run([git, "--no-lazy-fetch", "--no-replace-objects", "--version"], env=env,
                           capture_output=True, timeout=10, check=False)
    if probe.returncode:
        pytest.skip("installed Git does not support mandatory no-lazy-fetch/no-replace flags; no fallback/install")
    root = tmp_path if precreated_root else tmp_path / "repo"
    if precreated_root:
        assert root.is_dir() and not any(root.iterdir())
    root.mkdir(parents=True, exist_ok=precreated_root)

    def command(*args):
        result = subprocess.run([git, "--no-replace-objects", "--no-lazy-fetch", "-c", "safe.directory=" + str(root),
                                 "-c", "user.name=Artificial fixture", "-c", "user.email=fixture@example.invalid",
                                 "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false", "-C", str(root), *args],
                                env=env, capture_output=True, check=True, timeout=15)
        return result.stdout

    command("init", "--quiet")
    recipe = copy.deepcopy(pinned.RECIPES["matched-prefix-v1" if nested else "sealed-confirmation-v1"])
    report = b'{"scope":"ARTIFICIAL_TEST_ONLY"}\r\n'
    recipe["report_sha256"] = pinned.sha(report)
    recipe["expected_summary"]["report_sha256"] = pinned.sha(report)
    sources = {
        recipe["report_path"]: report,
        "src/alpha_research_rl/__init__.py": b'IDENTITY = "artificial historical package"\n',
        ".gitattributes": b"ignored.txt export-ignore\nsubstituted.txt export-subst\n*.py -text\n",
        "ignored.txt": b"This tracked file must still be retained.\r\n",
        "substituted.txt": b"$Format:%H$\n",
        "binary.dat": b"a\x00b\r\n\xff\n",
        "same-binary.dat": b"a\x00b\r\n\xff\n",
    }
    script = '''import json
import alpha_research_rl
def forbidden_original(*args, **kwargs):
    raise AssertionError("artificial generator must never run")
feature_bits = generate_inputs = prepare = run = write_once = EventWriter = forbidden_original
def main(args):
    assert args[-1] == "replay"
    assert alpha_research_rl.IDENTITY == "artificial historical package"
    print(json.dumps(SUMMARY))
'''.replace("SUMMARY", repr(recipe["expected_summary"]))
    if nested:
        html = b"<p>ARTIFICIAL ONLY</p>\n"
        recipe["html_sha256"] = pinned.sha(html)
        recipe["expected_summary"]["explorer_html_sha256"] = pinned.sha(html)
        sources[recipe["html_path"]] = html
        sources["scripts/replay_published_results.py"] = b'VALUE = "artificial helper"\n'
        suffix = "artifacts/astra-pool-diagnosis-v1/execution/jobs/001-" + "a" * 64 + "/COMPLETED.json"
        sources[suffix] = b'{"synthetic_nested_path":true}\n'
        script = '''import json
import tempfile
from pathlib import Path
import alpha_research_rl
import replay_published_results
import numpy
import scipy
def main():
    assert alpha_research_rl.IDENTITY == "artificial historical package"
    assert replay_published_results.VALUE == "artificial helper"
    assert numpy.__version__ == scipy.__version__ == "artificial-only"
    with tempfile.TemporaryDirectory(prefix="astra-revision-inputs-") as temporary:
        target = Path(temporary) / SUFFIX
        target.parent.mkdir(parents=True)
        target.write_bytes(b"artificial full nested path")
        assert target.read_bytes() == b"artificial full nested path"
        evidence = {"path": str(target), "utf16_units": len(str(target).encode("utf-16-le")) // 2,
                    "parent_utf16_units": len(str(target.parent).encode("utf-16-le")) // 2}
        (Path(tempfile.gettempdir()) / "nested-path-evidence.json").write_text(json.dumps(evidence))
    assert not target.exists()
    print(json.dumps(SUMMARY))
'''.replace("SUFFIX", repr(suffix)).replace("SUMMARY", repr(recipe["expected_summary"]))
        sources["scripts/replay_published_astra_revision.py"] = script.encode()
    else:
        sources["scripts/check_sealed_confirmation.py"] = script.encode()
    for relative, raw in sources.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    command("add", ".")
    command("commit", "--quiet", "-m", "artificial saved evidence")
    recipe["commit"] = command("rev-parse", "HEAD").decode().strip()
    if nested:
        dependency = tmp_path / "dependencies"
        for name in ("numpy", "scipy"):
            path = dependency / name
            path.mkdir(parents=True)
            (path / "__init__.py").write_text("__version__ = 'artificial-only'\n")
        monkeypatch.setattr(pinned, "_dependency_dirs", lambda _: [str(dependency.resolve())])
    monkeypatch.setitem(pinned.RECIPES, "synthetic-test-only", recipe)
    return root, recipe, sources


@pytest.fixture
def artificial_repo(tmp_path, monkeypatch):
    return _make_repo(tmp_path, monkeypatch)


def test_real_nested_snapshot_uses_owned_short_scratch(monkeypatch):
    # Do not depend on pytest's often-long per-test directory. This fresh,
    # ignored artificial repository is the only directory this test cleans.
    base = ROOT / ".local"
    base.mkdir(exist_ok=True)
    temporary = tempfile.TemporaryDirectory(prefix="pn", dir=base)
    owned_root = Path(temporary.name).resolve()
    try:
        suffix = "artifacts/astra-pool-diagnosis-v1/execution/jobs/001-" + "a" * 64 + "/COMPLETED.json"
        try:
            pinned.check_path_budget(owned_root / ".local/pinned-replay-runs/nested/tree",
                                     owned_root / ".local/p" / ("0" * 16), [{"path": suffix}])
        except pinned.ReplayError as error:
            if pinned.os.name == "nt" and "Windows path budget" in str(error):
                pytest.skip("checkout itself is too long for the real Windows nested fixture; path rejection tests still run")
            raise
        _assert_real_nested_snapshot(owned_root, monkeypatch)
    finally:
        pinned._no_reparse_ancestors(owned_root)
        assert owned_root.resolve().parent == base.resolve() and owned_root.name.startswith("pn")
        temporary.cleanup()


def _assert_real_nested_snapshot(owned_root, monkeypatch):
    root, recipe, _ = _make_repo(owned_root, monkeypatch, nested=True, precreated_root=True)
    output = root / ".local/pinned-replay-runs/nested"
    result = pinned.run_pinned("synthetic-test-only", output, repository_root=root)
    scratch = root / result["scratch_relative"]
    owner = pinned.strict_json((scratch / "OWNER.json").read_bytes())
    assert owner["capsule_relative"] == output.relative_to(root).as_posix()
    assert owner["commit"] == recipe["commit"]
    evidence = pinned.strict_json((scratch / "nested-path-evidence.json").read_bytes())
    assert "/execution/jobs/001-" in evidence["path"].replace("\\", "/")
    if pinned.os.name == "nt":
        assert evidence["utf16_units"] <= 259 and evidence["parent_utf16_units"] <= 247
    assert not Path(evidence["path"]).exists()  # Historical-style TemporaryDirectory cleans its own child.
    assert scratch.exists() and (scratch / "OWNER.json").exists()  # Launcher does not clean its allocation.
    assert not (output / "scratch").exists()
    request = pinned.strict_json((output / "child-request.json").read_bytes())
    started = pinned.strict_json((output / "STARTED.json").read_bytes())
    proof = pinned.strict_json((output / "child-proof.json").read_bytes())
    assert result["scratch_relative"] == request["scratch_relative"] == started["scratch_relative"] == proof["scratch_relative"]


def test_windows_budget_counts_utf16_units_and_rejects_long_root_or_output(tmp_path):
    root = tmp_path.resolve()
    long_root = root / ("x" * 180)
    entries = [{"path": "artifacts/" + "y" * 100 + "/COMPLETED.json"}]
    with pytest.raises(pinned.ReplayError, match="Windows path budget"):
        pinned.check_path_budget(long_root / "tree", long_root / ".local/p" / ("a" * 16), entries, windows=True)
    with pytest.raises(pinned.ReplayError, match="Windows path budget"):
        pinned.check_path_budget(root / ("z" * 180) / "tree", root / ".local/p" / ("a" * 16), [], windows=True)
    # One astral character occupies two UTF-16 units. Tune a filename exactly to
    # 259 with BMP spelling, then replace its last unit by an astral character.
    tree, scratch = root / "t", root / "s"
    count = 259 - len(str(tree).encode("utf-16-le")) // 2 - 1
    pinned.check_path_budget(tree, scratch, [{"path": "a" * count}], snapshots=False, windows=True)
    with pytest.raises(pinned.ReplayError, match="Windows path budget"):
        pinned.check_path_budget(tree, scratch, [{"path": "a" * (count - 1) + "\U0001f600"}], snapshots=False, windows=True)


def test_actual_artificial_git_tree_and_child_preserve_bytes_without_checkout(artificial_repo):
    root, recipe, sources = artificial_repo
    # The current checkout deliberately differs; historical imports must still win.
    (root / "src/alpha_research_rl/__init__.py").write_text('raise AssertionError("CURRENT CHECKOUT EXECUTED")\n')
    output = root / ".local/pinned-replay-runs/one"
    result = pinned.run_pinned("synthetic-test-only", output, repository_root=root)
    assert result["status"] == "VERIFIED_PINNED_SAVED_REPLAY"
    assert result["commit"] == recipe["commit"]
    assert result["tracked_files_unchanged"] is True
    assert result["child_summary"] == recipe["expected_summary"]
    for relative, raw in sources.items():
        assert (output / "tree" / relative).read_bytes() == raw
    manifest = pinned.strict_json((output / "tree-manifest.json").read_bytes())
    assert manifest["total_bytes"] == sum(map(len, sources.values()))
    assert {row["path"] for row in manifest["files"]} == set(sources)
    assert result["import_origins"]["alpha_research_rl"]["sha256"] == pinned.sha(sources["src/alpha_research_rl/__init__.py"])
    assert (output / "stdout.txt").read_bytes()
    assert (output / "stderr.txt").read_bytes() == b""
    assert not (output / "FAILED.json").exists()
    with pytest.raises(pinned.ReplayError, match="already exists"):
        pinned.run_pinned("synthetic-test-only", output, repository_root=root)


def test_wrong_registered_identity_fails_before_any_child(artificial_repo, monkeypatch):
    root, recipe, _ = artificial_repo
    recipe["report_sha256"] = "0" * 64
    original = pinned._process

    def forbid_child(argv, **kwargs):
        assert "--_child" not in argv
        return original(argv, **kwargs)

    monkeypatch.setattr(pinned, "_process", forbid_child)
    output = root / ".local/pinned-replay-runs/wrong"
    with pytest.raises(pinned.ReplayError, match="registered report"):
        pinned.run_pinned("synthetic-test-only", output, repository_root=root)
    assert (output / "FAILED.json").exists() and (output / "tree-manifest.json").exists()
    assert not (output / "COMPLETE.json").exists()
    assert not (output / "child-request.json").exists()


def test_missing_local_commit_is_retained_failure_without_fetch(artificial_repo):
    root, recipe, _ = artificial_repo
    recipe["commit"] = "f" * 40
    output = root / ".local/pinned-replay-runs/missing"
    with pytest.raises(pinned.ReplayError, match="Git failed"):
        pinned.run_pinned("synthetic-test-only", output, repository_root=root)
    failure = pinned.strict_json((output / "FAILED.json").read_bytes())
    assert failure["stage"] == "extract" and failure["retry_permitted"] is False
    assert not (output / "tree").exists()


@pytest.mark.parametrize("action", ["raise SystemExit(7)", "print('noise before JSON')"])
def test_failed_or_malformed_child_retains_logs_and_cannot_succeed(artificial_repo, monkeypatch, action):
    root, _, _ = artificial_repo
    original = pinned._process
    calls = []

    def replace_only_child(argv, **kwargs):
        if "--_child" in argv:
            calls.append(argv)
            argv = [sys.executable, "-I", "-S", "-B", "-c", action]
        return original(argv, **kwargs)

    monkeypatch.setattr(pinned, "_process", replace_only_child)
    output = root / ".local/pinned-replay-runs/badchild"
    with pytest.raises((pinned.ReplayError, json.JSONDecodeError)):
        pinned.run_pinned("synthetic-test-only", output, repository_root=root)
    assert len(calls) == 1
    assert (output / "stdout.txt").exists() and (output / "stderr.txt").exists()
    assert (output / "FAILED.json").exists() and not (output / "COMPLETE.json").exists()


def test_capped_process_retains_bounded_log_and_fails(tmp_path):
    log = tmp_path / "stdout.txt"
    with pytest.raises(pinned.ReplayError, match="limit exceeded"):
        pinned._process([sys.executable, "-I", "-S", "-c", "print('x'*10000)"], cwd=tmp_path,
                        env=dict(pinned.os.environ), timeout=5, stdout_limit=64, stderr_limit=1024,
                        stdout_path=log, stderr_path=tmp_path / "stderr.txt")
    assert len(log.read_bytes()) == 64


def test_process_timeout_retains_partial_output_and_fails(tmp_path):
    log = tmp_path / "stdout.txt"
    with pytest.raises(pinned.ReplayError, match="timeout"):
        pinned._process([sys.executable, "-I", "-S", "-c", "import time; print('started',flush=True); time.sleep(5)"],
                        cwd=tmp_path, env=dict(pinned.os.environ), timeout=0.3,
                        stdout_limit=1024, stderr_limit=1024, stdout_path=log, stderr_path=tmp_path / "stderr.txt")
    assert log.read_bytes().strip() == b"started"
