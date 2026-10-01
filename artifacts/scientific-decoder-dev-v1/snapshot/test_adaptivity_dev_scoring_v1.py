"""Internal independent scorer review; artificial records, no real outputs.

The reviewer authored the expression/utility primitive, not this scoring driver.
No test calls the real worker, provider, source cache or benchmark.
"""
import importlib.util
import json
from pathlib import Path
import sys

import pytest


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("reviewed_dev_scorer", HERE / "score_adaptivity_decoder_dev_v1.py")
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
driver = sys.modules["run_adaptivity_decoder_dev_v1"]


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, allow_nan=False), encoding="utf-8")


def test_single_failed_prediction_preserves_secondary_denominator():
    result = s.score_vector([1.] * 255 + [None], [1.] * 256, "nonfinite_or_domain_prediction")
    assert result["U"] == 0 and result["status"] == "invalid_candidate"
    assert result["pointwise_mean_U"] == 255 / 256
    assert result["finite_prediction_count"] == 255
    assert result["finite_prediction_fraction"] == 255 / 256
    assert result["native_magnitude_rmsle"] is None


def test_malformed_formula_cannot_receive_partial_credit():
    result = s.score_vector([], [1.] * 256, "packet_or_grammar_invalid")
    assert result["U"] == result["pointwise_mean_U"] == 0
    assert result["finite_prediction_count"] == 0


def test_signed_metrics_and_zero_targets_differ_from_magnitude_diagnostic():
    result = s.score_vector([-1.] * 256, [1.] * 256)
    assert result["U"] == result["pointwise_mean_U"] == .2
    assert result["native_magnitude_rmsle"] == 0
    mixed = s.score_vector([0., 1., 0., 1.], [0., 0., 1., 1.])
    assert mixed["pointwise_mean_U"] == (1 + 0 + .5 + 1) / 4
    assert mixed["zero_target_count"] == 2
    assert s.stable_mean([1e308, -1e308, 1e308, -1e308]) == 0


@pytest.fixture
def bank(tmp_path, monkeypatch):
    root = tmp_path / "artificial"
    root.mkdir()
    coords = root / "coordinates.json"
    tasks = [{"canonical_law_id": f"artificial-{i}", "domain_id": f"artificial-domain-{i // 2}",
              "specification": {"variables": [{"name": "x0"}]},
              "coordinates": {"test": {"x": [[3.]] * 256}, "train": {"x": [[1.]] * 64}}}
             for i in range(4)]
    put(coords, {"tasks": tasks})
    monkeypatch.setattr(s, "RUN", root)
    monkeypatch.setattr(driver, "RUN", root)
    monkeypatch.setattr(s, "COORDS", coords)
    monkeypatch.setattr(s, "verify", lambda: None)
    all_calls = []
    for index in range(8):
        task, rep = divmod(index, 2)
        conditions = ("prior", "data") if (task + rep) % 2 == 0 else ("data", "prior")
        calls = []
        for condition in conditions:
            directory = f"t{task}-r{rep}-{condition}"
            put(root / directory / "response.json", {"action": "propose", "expression": "0" if condition == "prior" else "x0",
                                                    "hypothesis": "artificial", "revision": "artificial"})
            put(root / directory / "result.json", {"success": True, "status": "succeeded", "error": None})
            calls.append({"task": task, "repetition": rep, "condition": condition,
                          "directory": directory, "success": True, "status": "succeeded", "error": None,
                          "response_sha256": s.digest(root / directory / "response.json"),
                          "result_sha256": s.digest(root / directory / "result.json")})
        put(root / f"pair-{index}.json", {"calls": calls})
        all_calls.extend(calls)
    put(root / "responses-frozen.json", {"frozen_at_utc": "2026-01-01T00:00:00+00:00", "calls": all_calls})
    training = []
    for i in range(4):
        path = root / f"t{i}-train-output.json"
        put(path, {"status": "COMPLETE", "row_count": 64, "attempted_count": 64,
                   "records": [{"index": j, "status": "ok", "value": 1.} for j in range(64)]})
        training.append({"task": i, "output": path.name, "sha256": s.digest(path)})
    put(root / "training.json", training)
    attempts = []
    def artificial_worker(index, split):
        assert split == "test"
        assert len(json.loads((root / "responses-frozen.json").read_bytes())["calls"]) == 16
        attempts.append(index)
        path = root / f"t{index}-test-output.json"
        put(path, {"status": "COMPLETE", "row_count": 256, "attempted_count": 256,
                   "records": [{"index": j, "status": "ok", "value": 3.} for j in range(256)]})
        return path
    monkeypatch.setattr(s, "worker", artificial_worker)
    return root, attempts


def test_complete_synthetic_bank_has_exact_counts_and_training_only_mean(bank):
    root, attempts = bank
    s.main()
    result = json.loads((root / "scores.json").read_bytes())
    assert attempts == list(range(4))
    assert len(result["rows"]) == 16 and len(result["references"]) == 8 and len(result["by_law"]) == 4
    assert result["actual_hosted_prediction_evaluations"] == 4096
    assert result["deterministic_reference_predictions"] == 2048
    assert result["confirmation_target_evaluations"] == 1024
    assert result["hosted_calls"] == 16
    assert result["means"]["data"] == 1 and result["means"]["prior"] == .5
    assert result["means"]["observed_mean"] == pytest.approx(9 / 13)
    assert len(result["by_domain"]) == 2 and all(row["laws"] == 2 for row in result["by_domain"])
    assert all(row["data"] == 1 and row["data_pointwise"] == 1 for row in result["by_domain"])
    assert all(r["constant"] == 1 for r in result["references"] if r["condition"] == "observed_mean")
    assert result["all_gates_pass"] is True
    with pytest.raises(ValueError):
        s.main()
    assert attempts == list(range(4))


@pytest.mark.parametrize("tamper", ["missing", "duplicate", "relabel_directory", "boolean_identity", "success_integer"])
def test_bad_frozen_bank_rejected_before_any_artificial_target(bank, tamper):
    root, attempts = bank
    path = root / "responses-frozen.json"
    frozen = json.loads(path.read_bytes())
    if tamper == "missing":
        frozen["calls"].pop()
    elif tamper == "duplicate":
        frozen["calls"][-1] = frozen["calls"][0]
    elif tamper == "relabel_directory":
        for key in ("directory", "response_sha256", "result_sha256"):
            frozen["calls"][0][key] = frozen["calls"][1][key]
    elif tamper == "boolean_identity":
        frozen["calls"][0]["task"] = False
    else:
        frozen["calls"][0]["success"] = 1
    put(path, frozen)
    with pytest.raises(ValueError):
        s.main()
    assert attempts == [] and not (root / "scores.json").exists()


def test_response_tamper_rejected_before_targets(bank):
    root, attempts = bank
    path = root / "t0-r0-prior" / "response.json"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError):
        s.main()
    assert attempts == []


def test_preexisting_later_target_refuses_all_new_queries(bank):
    root, attempts = bank
    put(root / "t3-test-output.json", {"status": "artificial_previous_attempt"})
    with pytest.raises(ValueError):
        s.main()
    assert attempts == []


@pytest.mark.parametrize("target", ["responses-frozen.json", "t0-r0-prior/response.json"])
def test_input_change_during_artificial_target_generation_cannot_publish(bank, monkeypatch, target):
    root, attempts = bank
    original = s.worker
    def altered(index, split):
        result = original(index, split)
        if index == 0:
            path = root / target
            path.write_bytes(path.read_bytes() + b" ")
        return result
    monkeypatch.setattr(s, "worker", altered)
    with pytest.raises(ValueError):
        s.main()
    assert attempts == list(range(4))
    assert not (root / "scores.json").exists()


@pytest.mark.parametrize("tamper", ["duplicate_task", "relabeled_output", "short_values"])
def test_training_reference_ledger_identity_before_targets(bank, tamper):
    root, attempts = bank
    path = root / "training.json"
    ledger = json.loads(path.read_bytes())
    if tamper == "duplicate_task":
        ledger.append(ledger[0])
    elif tamper == "relabeled_output":
        ledger[0]["output"], ledger[0]["sha256"] = ledger[1]["output"], ledger[1]["sha256"]
    else:
        output = root / ledger[0]["output"]
        record = json.loads(output.read_bytes())
        record["records"].pop()
        put(output, record)
        ledger[0]["sha256"] = s.digest(output)
    put(path, ledger)
    with pytest.raises(ValueError):
        s.main()
    assert attempts == []
