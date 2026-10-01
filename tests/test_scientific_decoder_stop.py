"""Saved-only verification and artificial tampering; no benchmark execution."""

import builtins
import copy
import importlib.util
import io
import json
import shutil
import socket
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_scientific_decoder_stop.py"


@pytest.fixture(scope="module")
def checker():
    spec = importlib.util.spec_from_file_location("stop_checker_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def evidence(tmp_path, checker):
    for relative in (checker.BASE, checker.RESULT, checker.GUIDE, checker.TRANSPORT):
        source, target = ROOT / relative, tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copyfile(source, target)
    return tmp_path


def test_actual_public_saved_check_has_no_execution_network_or_writes(checker, monkeypatch, capsys):
    original_import = builtins.__import__
    original_open = io.open
    original_decode = checker.decode
    checked_json = []

    def deny(*args, **kwargs):
        raise AssertionError("forbidden side effect")

    def guarded_import(name, *args, **kwargs):
        assert name.split(".")[0] not in {
            "alpha_research_rl", "numpy", "scipy", "torch", "transformers", "modules", "utils",
            "newton_scalar_worker_v1", "adaptivity_adapter_contract", "codex_actor",
        }
        return original_import(name, *args, **kwargs)

    def readonly_open(file, mode="r", *args, **kwargs):
        assert not any(flag in mode for flag in "wax+")
        return original_open(file, mode, *args, **kwargs)

    def json_only(raw):
        assert raw.lstrip().startswith(b"{")
        checked_json.append(len(raw))
        return original_decode(raw)

    with monkeypatch.context() as guarded:
        guarded.setattr(builtins, "__import__", guarded_import)
        guarded.setattr(io, "open", readonly_open)
        guarded.setattr(builtins, "open", readonly_open)
        guarded.setattr(subprocess, "Popen", deny)
        guarded.setattr(socket, "socket", deny)
        guarded.setattr(socket, "create_connection", deny)
        guarded.setattr(checker, "decode", json_only)
        result = checker.check_scientific_decoder_stop(ROOT)
        assert checker.main(["--root", str(ROOT)]) == 0
    assert result["status"] == "SAVED_STOP_VERIFIED"
    assert [result[k] for k in ("snapshot_files", "receipt_files", "execution_files")] == [36, 40, 13]
    assert [result[k] for k in ("attempted_training_targets", "finite_training_targets",
                               "failed_training_targets", "not_attempted_training_targets")] == [135, 134, 1, 121]
    assert result["predictive_scores"] is None and result["hosted_calls"] == 0
    assert result["new_oracle_calls"] == result["new_hosted_calls"] == result["network_requests"] == 0
    assert len(checked_json) == 24  # Twelve JSON documents per check, never source payloads.
    assert json.loads(capsys.readouterr().out)["result_sha256"] == checker.RESULT_SHA256


@pytest.mark.parametrize("relative", [
    "artifacts/scientific-decoder-dev-v1/snapshot/newton_scalar_worker_v1.py",
    "artifacts/scientific-decoder-dev-v1/execution/t2-train-request.json",
    "artifacts/scientific-decoder-dev-v1/execution/publication-preflight.json",
    "results/scientific_decoder_dev_v1.json",
])
def test_changed_bound_bytes_fail_even_when_change_is_only_whitespace(evidence, checker, relative):
    path = evidence / relative
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(checker.EvidenceError, match="SHA256 mismatch"):
        checker.check_scientific_decoder_stop(evidence)


@pytest.mark.parametrize("change", ["bool_value", "false_order", "failure_as_zero", "skip_failure"])
def test_record_semantics_are_checked_independently_of_file_hashes(checker, change):
    output = json.loads((ROOT / checker.BASE / "execution/t2-train-output.json").read_bytes())
    if change == "bool_value":
        output["records"][0]["value"] = True
    elif change == "false_order":
        output["records"][0]["index"] = False
    elif change == "failure_as_zero":
        output["records"][6]["value"] = 0
    else:
        output["records"][6] = {"index": 6, "status": "not_attempted", "value": None, "error_code": None}
        output["attempted_count"] = 6
    with pytest.raises(checker.EvidenceError):
        checker.validate_rows(output, 2)


@pytest.mark.parametrize("change", ["bool_count", "count", "score", "status", "order"])
def test_result_cannot_relabel_missing_performance_or_population(checker, change):
    result = json.loads((ROOT / checker.RESULT).read_bytes())
    tasks = copy.deepcopy(result["tasks"])
    if change == "bool_count":
        result["failed_training_targets"] = True
    elif change == "count":
        result["not_attempted_training_targets"] = 57
    elif change == "score":
        result["predictive_scores"] = {"mean": 0}
    elif change == "status":
        result["status"] = "COMPLETE"
    else:
        result["tasks"][0], result["tasks"][1] = result["tasks"][1], result["tasks"][0]
    with pytest.raises(checker.EvidenceError):
        checker.validate_result(result, tasks)


@pytest.mark.parametrize("directory", ["snapshot", "execution"])
def test_unrecorded_files_fail_complete_inventory(evidence, checker, directory):
    (evidence / checker.BASE / directory / "unrecorded.json").write_text("{}", encoding="utf-8")
    with pytest.raises(checker.EvidenceError, match="inventory mismatch"):
        checker.check_scientific_decoder_stop(evidence)


def test_json_and_path_ambiguities_fail_without_reading_outside_root(checker, tmp_path):
    for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}'):
        with pytest.raises(checker.EvidenceError):
            checker.decode(raw)
    for relative in ("../outside.json", "/absolute", "C:/outside.json", "a\\b", "a/../b", "a. /b"):
        with pytest.raises(checker.EvidenceError, match="unsafe"):
            checker.safe_path(tmp_path, relative)
