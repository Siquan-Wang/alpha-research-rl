"""Saved-only public entrypoint: fixed accounting, routing, and active guard checks."""

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
SCRIPT = SCRIPTS / "replay_published_astra_pool.py"


@pytest.fixture
def api(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    return runpy.run_path(str(SCRIPT))


@pytest.fixture
def saved(api, tmp_path):
    contract = tmp_path / api["CONTRACT_PATH"]
    report = tmp_path / api["REPORT_PATH"]
    directory = contract.parent / "execution"
    directory.mkdir(parents=True)
    report.parent.mkdir(parents=True)
    contract.write_text(json.dumps({"execution_directory": directory.relative_to(tmp_path).as_posix()}))
    original = {"study": api["STUDY"], "status": "COMPLETE_POST_HOC",
                "call_accounting": copy.deepcopy(api["EXPECTED_ACCOUNTING"]),
                "population": copy.deepcopy(api["EXPECTED_POPULATION"])}
    report.write_text(json.dumps(original))
    for name in ("COMPLETE.json", "request.json", "publication-receipt.json"):
        (directory / name).write_text("{}")
    verified = {"study": api["STUDY"], "status": "SAVED_ARITHMETIC_VERIFIED",
                "population": copy.deepcopy(api["EXPECTED_POPULATION"]), "completed_new_jobs": 108,
                "model_calls": 0, "new_financial_scores": 0, "raw_market_data_reads": 0,
                "contract_sha256": hashlib.sha256(contract.read_bytes()).hexdigest(),
                "report_sha256": hashlib.sha256(report.read_bytes()).hexdigest()}
    return tmp_path, contract, report, directory, original, verified


def test_routes_all_bound_public_files_to_saved_only_replay(api, saved):
    root, contract, report, directory, _, verified = saved
    calls = []

    def replay(*args, **kwargs):
        calls.append((args, kwargs))
        return verified

    result = api["verify_published_pool"](root, replay=replay)
    assert calls == [((contract, directory), {"source_root": root, "report_path": report})]
    assert (result["historical_new_evaluations"], result["reused_keys"], result["keys"], result["slots"]) == (
        108, 24, 132, 180,
    )
    assert result["model_calls"] == 0
    assert result["market_scores_recomputed"] is False


@pytest.mark.parametrize("artifact", ["contract", "report", "COMPLETE.json", "request.json"])
def test_missing_artifact_is_a_failure_without_calling_replay(api, saved, artifact):
    root, contract, report, directory, _, _ = saved
    {"contract": contract, "report": report}.get(artifact, directory / artifact).unlink()

    def forbidden(*args, **kwargs):
        pytest.fail("A missing artifact cannot invoke or silently skip replay")

    with pytest.raises(FileNotFoundError, match="Missing published pool artifacts"):
        api["verify_published_pool"](root, replay=forbidden)


@pytest.mark.parametrize("field,value", [
    ("new_evaluator_calls_started", 109), ("new_evaluator_calls_completed", 107),
    ("reused_key_count", 23), ("total_key_count", 133), ("total_slot_count", 179),
    ("model_calls", False), ("model_calls", 1), ("new_formulas", 1), ("automatic_retries", 1),
    ("reused_key_count", 24.0),
])
def test_historical_budget_is_exact_not_coerced(api, saved, field, value):
    root, _, report, _, body, verified = saved
    body["call_accounting"][field] = value
    report.write_text(json.dumps(body))
    verified["report_sha256"] = hashlib.sha256(report.read_bytes()).hexdigest()
    with pytest.raises(AssertionError, match="call_accounting"):
        api["verify_published_pool"](root, replay=lambda *a, **kw: verified)


@pytest.mark.parametrize("field,value", [
    ("status", "INCOMPLETE"), ("new_financial_scores", 1),
    ("raw_market_data_reads", True), ("report_sha256", "0" * 64),
])
def test_replay_must_verify_zero_new_scoring_and_exact_input_hashes(api, saved, field, value):
    root, _, _, _, _, verified = saved
    verified[field] = value
    with pytest.raises(AssertionError):
        api["verify_published_pool"](root, replay=lambda *a, **kw: verified)


def test_saved_report_cannot_be_partial_even_if_callback_claims_verified(api, saved):
    root, _, report, _, body, verified = saved
    body["status"] = "CLEAN_COMPLETED_PREFIX"
    report.write_text(json.dumps(body))
    verified["report_sha256"] = hashlib.sha256(report.read_bytes()).hexdigest()
    with pytest.raises(AssertionError, match="COMPLETE_POST_HOC"):
        api["verify_published_pool"](root, replay=lambda *a, **kw: verified)


@pytest.mark.parametrize("target", ["saved", "replayed"])
def test_population_is_checked_on_both_saved_and_replayed_sides(api, saved, target):
    root, _, report, _, body, verified = saved
    (body if target == "saved" else verified)["population"]["slot_count"] = 179
    report.write_text(json.dumps(body))
    verified["report_sha256"] = hashlib.sha256(report.read_bytes()).hexdigest()
    with pytest.raises(AssertionError, match="population.slot_count"):
        api["verify_published_pool"](root, replay=lambda *a, **kw: verified)


@pytest.mark.parametrize("relative", ["../elsewhere", ".local/execution", "C:/outside", ""])
def test_alternate_execution_directory_is_rejected_before_replay(api, saved, relative):
    root, contract, _, _, _, _ = saved
    contract.write_text(json.dumps({"execution_directory": relative}))
    with pytest.raises(AssertionError, match="[Ee]xecution directory"):
        api["verify_published_pool"](root, replay=lambda *a, **kw: pytest.fail("called replay"))


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
    ("__import__('torch')", "ImportError"),
    ("__import__('alpha_research_rl.financial_tasks')", "ImportError"),
    ("__import__('alpha_research_rl.financial_policy')", "ImportError"),
    ("__import__('alpha_research_rl.evaluation')", "ImportError"),
    ("__import__('alpha_research_rl.french')", "ImportError"),
    ("(root / 'data/raw/secret.json').read_bytes()", "RuntimeError"),
    ("(root / 'data/cache/secret.json').read_bytes()", "RuntimeError"),
    ("(root / '.local/secret.json').read_bytes()", "RuntimeError"),
    ("(root / 'models/secret.json').read_bytes()", "RuntimeError"),
    ("__import__('socket').socket()", "RuntimeError"),
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


def test_platform_cache_is_primed_before_subprocess_guard(tmp_path):
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


def test_cached_financial_import_cannot_bypass_guard(tmp_path):
    result = child(
        "import types\n"
        "sys.modules['alpha_research_rl.financial_tasks'] = types.ModuleType('preloaded')\n"
        "try:\n"
        "    api['install_guards'](root)\n"
        "except ImportError:\n"
        "    print('cached module rejected')\n", tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "cached module rejected"


def test_synthetic_saved_only_callback_runs_under_real_guards(api, saved):
    root, _, _, _, _, verified = saved
    result = child(
        f"verified = {verified!r}\n"
        "api['install_guards'](root)\n"
        "result = api['verify_published_pool'](root, replay=lambda *a, **kw: verified)\n"
        "print(result['status'])\n", root,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "matches_published_astra_pool_evidence"


def test_real_replay_module_imports_without_financial_or_training_modules(tmp_path):
    result = child(
        "api['install_guards'](root)\n"
        "from alpha_research_rl.astra_pool_diagnosis import replay_pool_diagnosis\n"
        "assert callable(replay_pool_diagnosis)\n"
        "assert not any(name in sys.modules for name in api['SCORING_MODULES'])\n"
        "print('import only; no replay or scoring')\n", tmp_path,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "import only; no replay or scoring"
