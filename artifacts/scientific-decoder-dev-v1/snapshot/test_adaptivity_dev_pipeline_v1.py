"""Artificial preparation/prompt checks; never run an actor or scientific oracle.

The author wrote the prompt renderer, so these are not an independent review of
that component. Driver tests operate only in pytest temporary directories with
an explicitly fake actor package and substituted numerical worker.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

LOCAL = Path(__file__).resolve().parent


def load_local(name, filename):
    spec = importlib.util.spec_from_file_location(name, LOCAL / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def renderer():
    return load_local("artificial_dev_renderer", "adaptivity_dev_prompts_v1.py")


def _json(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, allow_nan=False) + "\n", encoding="utf-8")


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _task(domain="m8_sound_speed"):
    if domain == "m8_sound_speed":
        specification = {
            "variables": ["gamma", "T", "M"],
            "units": ["dimensionless", "Kelvin", "kg/mol"],
            "bounds": [[.14, 14.], [29.315, 2931.5], [.002897, .2897]],
            "output": "speed of sound", "output_unit": "m/s",
            "runtime_keys": ["PRIVATE_RUNTIME_KEY"] * 3,
        }
        x = [[1. + index / 100, 100. + index, .02] for index in range(64)]
    else:
        specification = {
            "variables": ["omega", "T"],
            "units": ["angular frequency in benchmark input units",
                      "temperature in benchmark input units"],
            "bounds": [[1e8, 1e16], [10., 10000.]],
            "output": "average occupation number of photons in a quantum state",
            "output_unit": "dimensionless occupation number",
            "runtime_keys": ["PRIVATE_RUNTIME_KEY"] * 2,
        }
        x = [[1e8 + index * 1e6, 100. + index] for index in range(64)]
    return {
        "domain_id": domain, "difficulty": "PRIVATE_DIFFICULTY",
        "law_version": "PRIVATE_VERSION", "canonical_law_id": "PRIVATE_LAW_ID",
        "specification": specification,
        "coordinates": {
            "train": {"seed": "PRIVATE_SEED", "x": x},
            "test": {"x": "PRIVATE_CONFIRMATION_COORDINATES"},
        },
        "path": "PRIVATE_SOURCE_PATH",
    }


GRAMMAR = {"schema": "ARTIFICIAL_TEST_ONLY", "operators": ["+", "*"],
           "variables": ["x0", "x1", "x2"]}


class ForbiddenConfirmation:
    def __getitem__(self, key):
        raise AssertionError("confirmation data were accessed")

    def __iter__(self):
        raise AssertionError("confirmation data were iterated")


@pytest.mark.parametrize("with_data", [False, True])
def test_private_fields_and_confirmation_are_prompt_invariant(renderer, with_data):
    original = _task()
    values = [float(index + 1) for index in range(64)] if with_data else None
    before = renderer.render_prompt(original, GRAMMAR, values)
    changed = copy.deepcopy(original)
    for key in ("difficulty", "law_version", "canonical_law_id", "path"):
        changed[key] = "CHANGED_SECRET_" + key
    changed["coordinates"]["train"]["seed"] = "CHANGED_SECRET_SEED"
    changed["specification"]["runtime_keys"] = ["CHANGED_SECRET_RUNTIME"] * 3
    changed["coordinates"]["test"] = ForbiddenConfirmation()
    assert renderer.render_prompt(changed, GRAMMAR, values) == before
    assert "PRIVATE_" not in before and "CHANGED_SECRET" not in before
    observation = json.loads(before.split("OBSERVATION_JSON\n", 1)[1])
    assert set(observation) == {
        "schema", "public_problem", "input_variables", "output",
        "expression_grammar", "observations",
    }
    assert len(observation["observations"]) == (64 if with_data else 0)
    assert before.endswith("\n") and "\r" not in before


def test_same_domain_prior_aliases_are_preserved_not_identified(renderer):
    for domain in ("m8_sound_speed", "m10_be_distribution"):
        first = _task(domain)
        second = copy.deepcopy(first)
        second["difficulty"] = "DIFFERENT_DIFFICULTY"
        second["law_version"] = "DIFFERENT_VERSION"
        second["coordinates"] = ForbiddenConfirmation()
        assert renderer.render_prompt(first, GRAMMAR) == renderer.render_prompt(second, GRAMMAR)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf"), True, "1", None])
def test_invalid_training_response_never_enters_prompt(renderer, bad):
    outputs = [1.] * 64
    outputs[17] = bad
    with pytest.raises(ValueError):
        renderer.render_prompt(_task(), GRAMMAR, outputs)


@pytest.mark.parametrize("size", [0, 63, 65])
def test_reference_condition_requires_complete_64_vector(renderer, size):
    with pytest.raises(ValueError):
        renderer.render_prompt(_task(), GRAMMAR, [1.] * size)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True, 0.])
def test_bad_training_coordinate_never_enters_prompt(renderer, bad):
    task = _task()
    task["coordinates"]["train"]["x"][0][0] = bad
    with pytest.raises(ValueError):
        renderer.render_prompt(task, GRAMMAR, [1.] * 64)


@pytest.fixture
def driver(tmp_path, monkeypatch):
    actor_calls = []
    forbidden_worker_calls = []
    package = ModuleType("alpha_research_rl")
    package.__path__ = []
    actor_module = ModuleType("alpha_research_rl.codex_actor")

    def actor_stub(prompt, output, *, timeout_seconds, cwd, executable):
        actor_calls.append({"prompt": prompt, "timeout": timeout_seconds,
                            "cwd": cwd, "executable": executable})
        output.mkdir(exist_ok=False)
        _json(output / "result.json", {"success": True, "status": "succeeded",
                                      "error": None, "scope": "ARTIFICIAL_TEST_ONLY"})
        _json(output / "response.json", {"action": "propose", "expression": "x0",
                                        "hypothesis": "Artificial test.", "revision": "Artificial test."})
        return SimpleNamespace(success=True, status="succeeded", error=None)

    def forbidden_worker(*args, **kwargs):
        forbidden_worker_calls.append((args, kwargs))
        raise AssertionError("no real scientific worker is permitted in these tests")

    actor_module.run_actor = actor_stub
    package.codex_actor = actor_module
    monkeypatch.setitem(sys.modules, "alpha_research_rl", package)
    monkeypatch.setitem(sys.modules, "alpha_research_rl.codex_actor", actor_module)
    # Even a later import refactor cannot execute the real numerical-worker file.
    monkeypatch.setitem(sys.modules, "newton_scalar_worker_v1", ModuleType("newton_scalar_worker_v1"))
    monkeypatch.setattr(subprocess, "run", forbidden_worker)
    monkeypatch.setattr(subprocess, "Popen", forbidden_worker)
    # Restore sys.path after the driver's explicit source-path insertion.
    monkeypatch.setattr(sys, "path", list(sys.path))
    module = load_local("artificial_dev_driver", "run_adaptivity_decoder_dev_v1.py")
    module.REPO = tmp_path
    module.BASE = tmp_path / ".local"
    module.RUN = module.BASE / "ARTIFICIAL_TEST_ONLY"
    module.RUN.mkdir(parents=True)
    module.COORDS = module.BASE / "adaptivity-dev-coordinates-v1.json"
    neutral = tmp_path / "neutral"
    neutral.mkdir()
    # Preserve the production binding key set but use only artificial bytes in
    # this temporary repository. No fake source file is imported or executed.
    for relative in module.BOUND_FILES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ARTIFICIAL_BOUND_BYTES\n", encoding="utf-8")
    _json(module.COORDS, {"scope": "ARTIFICIAL_TEST_ONLY", "tasks": [
        _task("m8_sound_speed"), _task("m8_sound_speed"),
        _task("m10_be_distribution"), _task("m10_be_distribution"),
    ]})
    module.COORDS_SHA = _sha(module.COORDS)
    executable = tmp_path / "ARTIFICIAL_NOT_EXECUTABLE.bin"
    executable.write_bytes(b"ARTIFICIAL_NOT_EXECUTABLE")
    bound = module.BASE / "adaptivity-decoder-dev-plan-v1.md"
    _json(module.RUN / "binding.json", {
        "files": {relative: _sha(tmp_path / relative) for relative in module.BOUND_FILES},
        "neutral_actor_cwd": str(neutral), "actor_executable": str(executable),
        "actor_executable_sha256": _sha(executable), "scope": "ARTIFICIAL_TEST_ONLY",
    })
    records = []
    for task in range(4):
        for condition in ("prior", "data"):
            path = module.RUN / f"t{task}-{condition}-prompt.txt"
            path.write_text(f"ARTIFICIAL task={task} condition={condition}\n", encoding="utf-8")
            records.append({"task": task, "condition": condition,
                            "path": path.name, "sha256": _sha(path)})
    _json(module.RUN / "prompts.json", records)
    module._artificial_actor_calls = actor_calls
    module._artificial_forbidden_worker_calls = forbidden_worker_calls
    module._artificial_bound = bound
    monkeypatch.setattr(module, "worker", forbidden_worker)
    return module


def _now():
    return datetime.now(UTC).isoformat()


@pytest.mark.parametrize("remaining", [float("nan"), float("inf"), -float("inf"), 0., 5., 7., 101.])
def test_invalid_or_reserved_quota_never_calls_actor(driver, remaining):
    with pytest.raises(ValueError):
        driver.pair(0, remaining, _now())
    assert not driver._artificial_actor_calls
    assert not driver._artificial_forbidden_worker_calls


@pytest.mark.parametrize("kind", ["stale", "future", "naive"])
def test_unusable_quota_timestamp_never_calls_actor(driver, kind):
    now = datetime.now(UTC)
    checked = {
        "stale": (now - timedelta(seconds=61)).isoformat(),
        "future": (now + timedelta(seconds=30)).isoformat(),
        "naive": now.replace(tzinfo=None).isoformat(),
    }[kind]
    with pytest.raises(ValueError):
        driver.pair(0, 80., checked)
    assert not driver._artificial_actor_calls


def test_bound_source_hash_failure_precedes_actor_import_or_call(driver):
    driver._artificial_bound.write_text("CHANGED_ARTIFICIAL_BYTES", encoding="utf-8")
    with pytest.raises(ValueError, match="bound file changed"):
        driver.pair(0, 80., _now())
    assert not driver._artificial_actor_calls


def test_both_prompt_hashes_checked_before_either_actor_launch(driver):
    # This detects a race if verification occurs inside the two call closures.
    (driver.RUN / "t0-data-prompt.txt").write_text("CHANGED_PROMPT", encoding="utf-8")
    with pytest.raises((ValueError, AssertionError)):
        driver.pair(0, 80., _now())
    assert not driver._artificial_actor_calls


def test_completed_pair_cannot_be_called_again(driver):
    driver.pair(0, 80., _now())
    assert len(driver._artificial_actor_calls) == 2
    assert all(call["timeout"] == 600 for call in driver._artificial_actor_calls)
    with pytest.raises(ValueError, match="already exist|rerun|retry"):
        driver.pair(0, 80., _now())
    assert len(driver._artificial_actor_calls) == 2
    assert not driver._artificial_forbidden_worker_calls


def test_partial_call_directory_prevents_retry(driver):
    (driver.RUN / "t0-r0-prior").mkdir()
    with pytest.raises(ValueError, match="already exist|rerun|retry"):
        driver.pair(0, 80., _now())
    assert not driver._artificial_actor_calls


def test_first_future_exception_preserves_sibling_and_refuses_retry(driver, monkeypatch):
    actor_module = sys.modules["alpha_research_rl.codex_actor"]
    successful_stub = actor_module.run_actor
    attempts = []

    def one_failure(prompt, output, **kwargs):
        condition = "prior" if output.name.endswith("-prior") else "data"
        attempts.append(condition)
        assert (driver.RUN / "pair-0-started.json").exists()
        if condition == "prior":
            output.mkdir(exist_ok=False)
            (output / "ARTIFICIAL_FAILURE.txt").write_text("stub raised", encoding="utf-8")
            raise RuntimeError("ARTIFICIAL_FIRST_FUTURE_FAILURE")
        return successful_stub(prompt, output, **kwargs)

    monkeypatch.setattr(actor_module, "run_actor", one_failure)
    with pytest.raises(SystemExit, match="INCOMPLETE_TRANSPORT_STOP"):
        driver.pair(0, 80., _now())
    assert sorted(attempts) == ["data", "prior"]
    assert driver.read(driver.RUN / "pair-0-started.json")["conditions"] == ["prior", "data"]
    calls = driver.read(driver.RUN / "pair-0.json")["calls"]
    assert len(calls) == 2
    failed, succeeded = calls
    assert (failed["condition"], failed["success"], failed["status"], failed["error"]) == (
        "prior", False, "driver_exception", "RuntimeError",
    )
    assert (succeeded["condition"], succeeded["success"], succeeded["status"]) == (
        "data", True, "succeeded",
    )
    assert succeeded["result_sha256"] == _sha(driver.RUN / succeeded["directory"] / "result.json")
    assert succeeded["response_sha256"] == _sha(driver.RUN / succeeded["directory"] / "response.json")
    assert (driver.RUN / "t0-r0-prior" / "ARTIFICIAL_FAILURE.txt").exists()
    with pytest.raises(ValueError, match="already exist|rerun|retry"):
        driver.pair(0, 80., _now())
    assert len(attempts) == 2
    assert len(driver._artificial_actor_calls) == 1
    assert not driver._artificial_forbidden_worker_calls


def test_previous_incomplete_pair_prevents_later_calls(driver):
    _json(driver.RUN / "pair-0.json", {"calls": [
        {"task": 0, "repetition": 0, "condition": condition, "success": False,
         "status": "failed", "error": "ARTIFICIAL_FAILURE"}
        for condition in ("prior", "data")
    ]})
    with pytest.raises(ValueError, match="earlier incomplete transport"):
        driver.pair(1, 80., _now())
    assert not driver._artificial_actor_calls


def test_empty_pair_records_cannot_be_declared_frozen_bank(driver):
    for index in range(8):
        _json(driver.RUN / f"pair-{index}.json", {"calls": []})
    with pytest.raises(ValueError):
        driver.freeze_responses()
    assert not (driver.RUN / "responses-frozen.json").exists()
    assert not driver._artificial_actor_calls


def test_training_stage_only_requests_training_splits(driver, monkeypatch):
    seen = []

    def numerical_stub(task_index, split):
        assert split == "train", "confirmation cannot be requested here"
        seen.append((task_index, split))
        path = driver.RUN / f"artificial-t{task_index}-train-output.json"
        _json(path, {"status": "COMPLETE", "scope": "ARTIFICIAL_TEST_ONLY",
                     "records": [{"value": float(i)} for i in range(64)]})
        return path

    monkeypatch.setattr(driver, "worker", numerical_stub)
    driver.collect_training()
    assert seen == [(i, "train") for i in range(4)]
    assert len(driver.read(driver.RUN / "training.json")) == 4
    with pytest.raises(ValueError, match="already collected"):
        driver.collect_training()
    assert len(seen) == 4
    assert not driver._artificial_actor_calls


def test_prompt_stage_uses_only_saved_training_and_keeps_alias_records(driver, renderer, monkeypatch):
    binding = driver.read(driver.RUN / "binding.json")
    driver.RUN = driver.BASE / "ARTIFICIAL_RENDER_ONLY"
    _json(driver.RUN / "binding.json", binding)
    training = []
    for index in range(4):
        output = driver.RUN / f"artificial-{index}.json"
        _json(output, {"status": "COMPLETE", "scope": "ARTIFICIAL_TEST_ONLY",
                      "records": [{"value": float(index * 100 + point)} for point in range(64)]})
        training.append({"task": index, "output": output.name, "sha256": _sha(output)})
    _json(driver.RUN / "training.json", training)
    grammar_stub = ModuleType("adaptivity_adapter_contract")
    grammar_stub.GRAMMAR = GRAMMAR
    monkeypatch.setitem(sys.modules, "adaptivity_adapter_contract", grammar_stub)
    monkeypatch.setitem(sys.modules, "adaptivity_dev_prompts_v1", renderer)
    driver.render_prompts()
    records = driver.read(driver.RUN / "prompts.json")
    assert len(records) == 8
    assert len({record["sha256"] for record in records}) == 6
    for record in records:
        text = (driver.RUN / record["path"]).read_text(encoding="utf-8")
        assert "PRIVATE_" not in text
        observation = json.loads(text.split("OBSERVATION_JSON\n", 1)[1])
        assert len(observation["observations"]) == (0 if record["condition"] == "prior" else 64)
    assert not driver._artificial_actor_calls
    assert not driver._artificial_forbidden_worker_calls


def test_repeated_identity_cannot_fill_a_complete_response_bank(driver):
    output = driver.RUN / "t0-r0-prior"
    _json(output / "result.json", {"scope": "ARTIFICIAL_TEST_ONLY"})
    _json(output / "response.json", {"action": "propose", "expression": "0",
                                     "hypothesis": "Artificial.", "revision": "Artificial."})
    call = {"task": 0, "repetition": 0, "condition": "prior", "directory": output.name,
            "success": True, "status": "succeeded", "error": None,
            "result_sha256": _sha(output / "result.json"),
            "response_sha256": _sha(output / "response.json")}
    for index in range(8):
        _json(driver.RUN / f"pair-{index}.json", {"calls": [call, dict(call)]})
    with pytest.raises(ValueError):
        driver.freeze_responses()
    assert not (driver.RUN / "responses-frozen.json").exists()


def test_prior_observation_is_a_defensive_value(renderer):
    task = _task()
    grammar = copy.deepcopy(GRAMMAR)
    observation = renderer.make_observation(task, grammar)
    observation["input_variables"][0]["bounds"][0] = -99
    observation["expression_grammar"]["operators"].append("EVIL")
    assert task["specification"]["bounds"][0][0] == .14
    assert grammar == GRAMMAR
