"""Artificial public files and fresh-process checks; no market/provider execution."""

import copy
import hashlib
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "replay_published_astra_revision.py"


@pytest.fixture
def api(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    return runpy.run_path(str(SCRIPT))


class Saved:
    def __init__(self, root, api):
        self.root, self.api = root, api
        self.paths = {name: root / api[name.upper() + "_PATH"]
                      for name in ("contract", "submissions", "report")}
        self.directory = root / api["EXECUTION_DIRECTORY"]
        self.directory.mkdir(parents=True)
        self.paths["report"].parent.mkdir(parents=True)
        for name in api["REQUIRED_EXECUTION_FILES"]:
            (self.directory / name).write_text("{}", encoding="utf-8")
        self.bodies = {
            "contract": {"execution_directory": api["EXECUTION_DIRECTORY"]},
            "submissions": {"schema": "astra-revision-submissions-v1", "study": api["STUDY"],
                            "status": "ALL_200_SLOTS_FROZEN_NO_JOINED_FUTURE_OUTCOMES"},
            "report": {"schema": "astra-revision-result-v1", "study": api["STUDY"],
                       "status": "COMPLETE_MATCHED_PREFIX_DEVELOPMENT",
                       "population": copy.deepcopy(api["EXPECTED_POPULATION"]),
                       "call_accounting": {"hosted_calls": 80, "cheap_slots": 120, "new_slots": 200,
                                           "automatic_retries": 0, "new_feedback_calls": 139,
                                           "new_future_calls": 113, "completed_new_future_calls": 113,
                                           "reused_future_keys": 21,
                                           "unique_future_keys": 134},
                       "analysis": {"state_count": 10, "slot_count": 200},
                       "rows": [{"task_id": task, "generator": generator, "repetition": repetition}
                                for task, generator, repetition in api["SLOT_ORDER"]]},
        }
        self.verified = {"schema": "astra-revision-replay-v1", "study": api["STUDY"],
                         "status": "SAVED_REVISION_VERIFIED", **api["EXPECTED_REPLAY_COUNTS"],
                         "new_future_calls": 113, "completed_new_future_calls": 113,
                         "reused_future_keys": 21, "unique_future_keys": 134,
                         "installed_runtime_revalidated": False}
        self.sync()

    def sync(self):
        for name, path in self.paths.items():
            path.write_bytes(json.dumps(self.bodies[name]).encode("utf-8"))
            self.verified[name + "_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        for name, mirror in (("submissions", "SUBMISSIONS.json"), ("report", "COMPLETE.json")):
            (self.directory / mirror).write_bytes(self.paths[name].read_bytes())

    def verify(self, callback=None):
        return self.api["verify_published_revision"](self.root, replay=callback or (lambda **kw: self.verified))


@pytest.fixture
def saved(api, tmp_path):
    return Saved(tmp_path, api)


def test_routes_only_public_files_to_saved_replay_and_separates_historical_calls(saved):
    calls = []

    def replay(**kwargs):
        calls.append(kwargs)
        return saved.verified

    result = saved.verify(replay)
    assert calls == [{"source_root": saved.root, "report_path": saved.paths["report"]}]
    assert result["historical_hosted_calls"] == 80
    assert result["historical_new_feedback_calls"] == 139
    assert result["historical_new_future_calls"] == 113
    assert result["replay_model_calls"] == result["replay_financial_scores"] == 0
    assert result["market_scores_recomputed"] is result["raw_market_data_read"] is False


@pytest.mark.parametrize("name", ["contract", "submissions", "report", *(
    "collection-request.json", "preparation-receipt.json", "SUBMISSIONS.json", "assessment-request.json",
    "submissions-receipt.json", "assessment-plan.json", "COMPLETE.json",
)])
def test_missing_artifact_never_invokes_replay(saved, name):
    saved.paths.get(name, saved.directory / name).unlink()
    with pytest.raises(FileNotFoundError, match="Missing published revision artifact"):
        saved.verify(lambda **kw: pytest.fail("missing evidence invoked replay"))


@pytest.mark.parametrize("marker", ["INCOMPLETE.json", ".execution-lock"])
def test_failed_or_still_running_study_rejected_before_replay(saved, marker):
    (saved.directory / marker).write_text("{}", encoding="utf-8")
    with pytest.raises(AssertionError, match="complete and inactive"):
        saved.verify(lambda **kw: pytest.fail("partial evidence invoked replay"))


@pytest.mark.parametrize("relative", ["../outside", ".local/execution", "C:/outside", "", None,
                                       "artifacts/astra-matched-prefix-v1/other-execution"])
def test_alternate_execution_directory_rejected(saved, relative):
    saved.bodies["contract"]["execution_directory"] = relative
    saved.sync()
    with pytest.raises(AssertionError, match="Execution directory"):
        saved.verify(lambda **kw: pytest.fail("alternate evidence invoked replay"))


@pytest.mark.parametrize("name,field,value", [
    ("report", "status", "INCOMPLETE"), ("report", "schema", "astra-revision-result-v2"),
    ("report", "study", "astra-matched-prefix-v2"), ("submissions", "status", "PARTIAL"),
    ("submissions", "study", "astra-matched-prefix-v2"),
])
def test_complete_study_identity_required(saved, name, field, value):
    saved.bodies[name][field] = value
    saved.sync()
    with pytest.raises(AssertionError, match="identity/status"):
        saved.verify()


@pytest.mark.parametrize("field,value", [
    ("hosted_calls", 79), ("cheap_slots", 121), ("new_slots", 199), ("automatic_retries", True),
    ("automatic_retries", 1), ("new_feedback_calls", 201), ("new_feedback_calls", -1),
    ("new_future_calls", 201), ("new_future_calls", 113.0), ("completed_new_future_calls", 112),
    ("reused_future_keys", False),
    ("reused_future_keys", -1), ("unique_future_keys", 133),
])
def test_exact_accounting_and_bounds_reject_coercions(saved, field, value):
    saved.bodies["report"]["call_accounting"][field] = value
    saved.sync()
    with pytest.raises(AssertionError, match="call_accounting|unique keys"):
        saved.verify()


def test_unique_keys_can_exceed_slots_due_to_cached_prefix_keys(saved):
    saved.bodies["report"]["call_accounting"].update(
        new_future_calls=200, completed_new_future_calls=200, reused_future_keys=20, unique_future_keys=220,
    )
    saved.verified.update(new_future_calls=200, completed_new_future_calls=200,
                          reused_future_keys=20, unique_future_keys=220)
    saved.sync()
    assert saved.verify()["unique_future_keys"] == 220


def test_zero_new_future_calls_is_valid_when_all_keys_are_reused(saved):
    saved.bodies["report"]["call_accounting"].update(
        new_future_calls=0, completed_new_future_calls=0, reused_future_keys=20, unique_future_keys=20,
    )
    saved.verified.update(new_future_calls=0, completed_new_future_calls=0,
                          reused_future_keys=20, unique_future_keys=20)
    saved.sync()
    assert saved.verify()["historical_new_future_calls"] == 0


@pytest.mark.parametrize("target,key,value", [
    ("population", "states", 9), ("population", "repetitions", 4.0),
    ("analysis", "slot_count", 199), ("analysis", "state_count", True),
])
def test_complete_denominators_required(saved, target, key, value):
    saved.bodies["report"][target][key] = value
    saved.sync()
    with pytest.raises(AssertionError, match=target):
        saved.verify()


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "reordered", "boolean_repetition", "wrong_arm"])
def test_all_200_slot_identities_retained_exactly(saved, mutation):
    rows = saved.bodies["report"]["rows"]
    if mutation == "missing":
        rows.pop()
    elif mutation == "duplicate":
        rows[-1] = copy.deepcopy(rows[0])
    elif mutation == "reordered":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "boolean_repetition":
        rows[0]["repetition"] = True
    else:
        rows[0]["generator"] = "withheld"
    saved.sync()
    with pytest.raises(AssertionError, match="200|row identity"):
        saved.verify()


@pytest.mark.parametrize("field,value", [
    ("schema", "old"), ("study", "wrong"), ("status", "PARTIAL"), ("hosted_calls", 0),
    ("new_model_calls", 1), ("new_financial_scores", True), ("raw_market_data_reads", 1),
    ("installed_runtime_revalidated", 0), ("installed_runtime_revalidated", True),
    ("completed_new_future_calls", 112), ("unique_future_keys", 133),
    ("contract_sha256", "0" * 64), ("submissions_sha256", "0" * 64), ("report_sha256", "0" * 64),
])
def test_replay_must_match_identity_accounting_hashes_and_zero_new_activity(saved, field, value):
    saved.verified[field] = value
    with pytest.raises(AssertionError):
        saved.verify()


@pytest.mark.parametrize("mirror", ["SUBMISSIONS.json", "COMPLETE.json"])
def test_internal_public_mirrors_require_exact_bytes_even_for_same_json(saved, mirror):
    path = saved.directory / mirror
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(AssertionError, match="exactly mirror"):
        saved.verify(lambda **kw: pytest.fail("nonmatching mirror invoked replay"))


@pytest.mark.parametrize("name", ["contract", "submissions", "report", "SUBMISSIONS.json", "COMPLETE.json"])
def test_files_changed_during_replay_cannot_succeed(saved, name):
    path = saved.paths.get(name, saved.directory / name)

    def replay(**kwargs):
        path.write_bytes(path.read_bytes() + b"\n")
        return saved.verified

    with pytest.raises(AssertionError, match="bytes"):
        saved.verify(replay)


@pytest.mark.parametrize("payload", [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}',
                                     b'{"x":1e999}', b'[]'])
def test_ambiguous_nonfinite_or_nonobject_json_rejected_before_replay(saved, payload):
    saved.paths["report"].write_bytes(payload)
    with pytest.raises((ValueError, AssertionError)):
        saved.verify(lambda **kw: pytest.fail("malformed JSON invoked replay"))


def test_semantic_replay_failure_is_not_suppressed(saved):
    def replay(**kwargs):
        raise AssertionError("retained outcome hash mismatch")

    with pytest.raises(AssertionError, match="retained outcome hash mismatch"):
        saved.verify(replay)


def child(source, root):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    prefix = (
        "import sys, runpy\nfrom pathlib import Path\n"
        f"sys.path.insert(0, {str(SCRIPTS)!r})\n"
        f"api = runpy.run_path({str(SCRIPT)!r})\n"
        f"root = Path({str(root)!r})\n"
    )
    return subprocess.run([sys.executable, "-c", prefix + source], text=True, capture_output=True,
                          timeout=30, env=env, check=False)


@pytest.mark.parametrize("operation,expected", [
    ("__import__('torch')", "ImportError"), ("__import__('transformers')", "ImportError"),
    ("__import__('alpha_research_rl.financial_tasks')", "ImportError"),
    ("__import__('alpha_research_rl.financial_policy')", "ImportError"),
    ("__import__('alpha_research_rl.evaluation')", "ImportError"),
    ("__import__('alpha_research_rl.french')", "ImportError"),
    ("(root / 'data/raw/secret.json').read_bytes()", "RuntimeError"),
    ("(root / 'data/cache/secret.json').read_bytes()", "RuntimeError"),
    ("(root / '.local/secret.json').read_bytes()", "RuntimeError"),
    ("(root / 'models/secret.json').read_bytes()", "RuntimeError"),
    ("__import__('socket').socket()", "RuntimeError"),
    ("__import__('socket').gethostbyname('localhost')", "RuntimeError"),
    ("__import__('subprocess').run([sys.executable, '-c', 'pass'])", "RuntimeError"),
])
def test_active_guards_prevent_forbidden_operations(tmp_path, operation, expected):
    result = child(
        "api['install_guards'](root)\n"
        "try:\n"
        f"    {operation}\n"
        "except (ImportError, RuntimeError) as error:\n"
        "    print(type(error).__name__)\n"
        "else:\n"
        "    raise AssertionError('forbidden operation succeeded')\n", tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == expected


def test_platform_is_primed_before_replay_prohibits_subprocesses(tmp_path):
    result = child(
        "import subprocess\n"
        "def prime():\n"
        "    subprocess.run([sys.executable, '-c', 'pass'], check=True)\n"
        "api['platform'].uname = prime\n"
        "api['install_guards'](root)\n"
        "try:\n"
        "    subprocess.run([sys.executable, '-c', 'pass'])\n"
        "except RuntimeError:\n"
        "    print('primed then blocked')\n", tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "primed then blocked"


@pytest.mark.parametrize("module", ["alpha_research_rl.financial_tasks", "torch"])
def test_preloaded_forbidden_module_cannot_bypass_guard(tmp_path, module):
    result = child(
        "import types\n"
        f"sys.modules[{module!r}] = types.ModuleType('preloaded')\n"
        "try:\n"
        "    api['install_guards'](root)\n"
        "except ImportError:\n"
        "    print('cached module rejected')\n", tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "cached module rejected"


def test_complete_artificial_callback_runs_under_real_guards(saved):
    result = child(
        f"verified = {saved.verified!r}\n"
        "api['install_guards'](root)\n"
        "result = api['verify_published_revision'](root, replay=lambda **kw: verified)\n"
        "print(result['status'])\n", saved.root,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "matches_published_astra_revision_evidence"


def test_real_driver_module_import_does_not_load_scorers_or_training_dependencies(tmp_path):
    result = child(
        "api['install_guards'](root)\n"
        "from alpha_research_rl.astra_revision_study import replay_revision_study\n"
        "assert callable(replay_revision_study)\n"
        "assert not any(name in sys.modules for name in api['SCORING_MODULES'])\n"
        "print('import only; no replay, provider, or scoring')\n", tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "import only; no replay, provider, or scoring"
