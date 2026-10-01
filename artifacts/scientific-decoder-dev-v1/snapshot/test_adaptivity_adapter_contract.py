"""Artificial fixtures only: no Newton law import or simulator calls."""
import importlib.util
import hashlib
import json
import math
from pathlib import Path
import sys

import pytest


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


c = load("adaptivity_adapter_contract")
w = load("newton_scalar_worker_v1")


@pytest.mark.parametrize("source", ["__import__('os')", "x0.real", "x0[0]", "[x0]", "x0 if x0 else 1",
                                   "lambda: 1", "sin(x0,x0)", "log(x0,base=2)", "x0**x0", "x0**(1+1)",
                                   "True", "1e309", " x0", "unknown", "sum(x0)"])
def test_grammar_rejects_programs_and_variable_powers(source):
    with pytest.raises(c.ExpressionError):
        c.SafeExpression(source, ["x0"])


def test_exact_float_interpreter_and_literal_exponent():
    expression = c.SafeExpression("sqrt(x0) + x1**-2 + sin(pi/2) + log(e) - abs(-2)", ["x0", "x1"])
    assert expression.evaluate([9, 2]) == pytest.approx(3.25)
    assert c.SafeExpression("x0**+2", ["x0"]).evaluate([-2]) == 4
    assert c.SafeExpression("2e-20*x0", ["x0"]).evaluate([1e20]) == 2


@pytest.mark.parametrize("source", ["1/x0", "log(x0)", "sqrt(-1)", "exp(1000)", "(-1)**0.5"])
def test_numerical_failure_never_clips(source):
    with pytest.raises(c.ExpressionError):
        c.SafeExpression(source, ["x0"]).evaluate([0])


@pytest.mark.parametrize("scale", [1e-200, 1e-20, 1, 1e20, 1e200])
def test_utility_units_and_signed_error(scale):
    y = [scale, -2 * scale]
    assert c.signed_utility(y, y)["U"] == 1
    assert c.signed_utility([0, 0], y)["U"] == .5
    assert c.signed_utility([-x for x in y], y)["U"] == .2
    assert c.signed_utility([2 * x for x in y], y)["U"] == .5


def test_degenerate_and_invalid_predictions_are_explicit():
    assert c.signed_utility([0, -0.0], [0, 0]) == {
        "U": 1., "status": "degenerate_target", "degenerate_target": True,
        "relative_squared_error": None, "numerical_limit": "relative error undefined for exact zero target"}
    assert c.signed_utility([1, 0], [0, 0])["U"] == 0
    for value in [math.nan, math.inf, -math.inf, True, "1"]:
        result = c.signed_utility([value], [1])
        assert result["U"] == 0 and result["status"] == "invalid_prediction"
    for p, y in [([], []), ([1], [1, 2]), ([1], [math.nan]), ([1], [True])]:
        with pytest.raises(c.ContractError):
            c.signed_utility(p, y)


@pytest.mark.parametrize("p,y", [([1., 1e-200], [1., 0.]), ([1e308, 1e-100], [1e308, 0.])])
def test_nonzero_residual_underflow_does_not_report_exact_zero_error(p, y):
    result = c.signed_utility(p, y)
    assert result["U"] == 1
    assert result["relative_squared_error"] is None
    assert "residual lost" in result["numerical_limit"]
    assert not result["degenerate_target"]


def test_target_underflow_not_degenerate():
    result = c.signed_utility([1e308], [1e-308])
    assert result["U"] == 0 and not result["degenerate_target"]
    assert result["relative_squared_error"] is None
    assert "raw target was nonzero" in result["numerical_limit"]


def test_broker_charges_invalid_and_duplicate_keeps_all_attempts():
    seen = []
    broker = c.ScalarBroker([(1, 3)], 6, lambda x: seen.append(x) or x[0] * 2)
    for raw in ['{"x":[0]}', '{"x":[1],"x":[2]}', '{"x":[NaN]}', '{"x":[true]}']:
        assert broker.submit(raw)["status"] == "invalid_request"
    first = broker.submit('{"x":[2]}')
    duplicate = broker.submit('{"x":[2.0]}')
    assert len(seen) == 2 and first["attempt"] == 5 and duplicate["duplicate_of"] == 5
    assert len(broker.trace) == 6
    duplicate["value"] = 100
    assert broker.trace[-1]["value"] == 4
    with pytest.raises(c.ContractError):
        broker.submit('{"x":[2]}')


def test_freeze_and_failed_oracle_cannot_retry():
    broker = c.ScalarBroker([(1, 3)], 2, lambda x: x[0])
    frozen = broker.freeze()
    assert frozen == []  # Primitive freeze does not certify full-budget completion.
    with pytest.raises(c.ContractError):
        broker.submit('{"x":[1]}')
    def interrupt(_):
        raise KeyboardInterrupt
    failed = c.ScalarBroker([(1, 3)], 2, interrupt)
    with pytest.raises(KeyboardInterrupt):
        failed.submit('{"x":[1]}')
    assert failed.state == "FAILED" and failed.trace[0]["status"] == "oracle_failure"
    with pytest.raises(c.ContractError):
        failed.submit('{"x":[2]}')


def request(domain="m8_sound_speed"):
    return {"domain": domain, "difficulty": "medium", "law_version": "v1", "noise0": 0,
            "rows": [[1.4, 300., .03], [1.5, 400., .02]] if domain == "m8_sound_speed" else [[1e9, 300.]]}


def test_worker_artificial_callback_mapping_no_real_import(monkeypatch):
    monkeypatch.setattr(w, "load_scalar", lambda _: pytest.fail("must not load actual oracle"))
    seen = []
    result = w.run(request(), scalar=lambda **kwargs: seen.append(kwargs) or 7.)
    assert result["status"] == "COMPLETE" and result["attempted_count"] == 2
    assert seen[0] == {"noise_level": 0., "difficulty": "medium", "law_version": "v1",
                       "system": "vanilla_equation", "adiabatic_index": 1.4, "temperature": 300., "molar_mass": .03}
    seen.clear()
    w.run(request("m10_be_distribution"), scalar=lambda **kwargs: seen.append(kwargs) or 8.)
    assert seen[0]["omega"] == 1e9 and seen[0]["temperature"] == 300.


def test_worker_validates_all_rows_before_any_call_and_retains_failure_tail():
    invalid = request()
    invalid["rows"][-1][0] = False
    with pytest.raises(w.WorkerError):
        w.run(invalid, scalar=lambda **kw: pytest.fail("invalid request must not call oracle"))
    calls = []
    result = w.run(request(), scalar=lambda **kw: calls.append(kw) or math.nan)
    assert len(calls) == 1 and result["status"] == "INCOMPLETE"
    assert [r["status"] for r in result["records"]] == ["failed", "not_attempted"]
    assert result["records"][0]["error_code"] == "nonfinite_or_nonscalar_output"
    assert "traceback" not in json.dumps(result)


def test_worker_strict_json_and_scope():
    for raw in [b'{"a":1,"a":2}', b'{"a":NaN}']:
        with pytest.raises(w.WorkerError):
            w.strict_json(raw)
    for key, value in [("domain", "m0_gravity"), ("difficulty", "easy"), ("law_version", "v3"), ("noise0", True)]:
        obj = request()
        obj[key] = value
        with pytest.raises(w.WorkerError):
            w.validate_request(obj)


def test_worker_rejects_unbound_bytecode_and_other_files(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    cache.mkdir()
    source = cache / "safe.py"
    source.write_bytes(b"# artificial\n")
    raw = json.dumps({"commit": w.COMMIT, "files": {"safe.py": hashlib.sha256(source.read_bytes()).hexdigest()}}).encode()
    (cache / "manifest.json").write_bytes(raw)
    monkeypatch.setattr(w, "CACHE", cache)
    monkeypatch.setattr(w, "MANIFEST_SHA256", hashlib.sha256(raw).hexdigest())
    assert w.verify_cache() == {"safe.py": hashlib.sha256(source.read_bytes()).hexdigest()}
    extra = cache / "safe.pyc"
    extra.write_bytes(b"untrusted artificial bytecode")
    with pytest.raises(w.WorkerError, match="bytecode_cache"):
        w.verify_cache()
    extra.unlink()
    (cache / "other.py").write_bytes(b"# unbound")
    with pytest.raises(w.WorkerError, match="unlisted_cache_file"):
        w.verify_cache()


def test_worker_prohibited_operation_is_not_numeric_failure():
    def forbidden(**_):
        raise w.WorkerError("symbolic_evaluation_disabled")
    result = w.run(request(), scalar=forbidden)
    assert result["records"][0]["error_code"] == "symbolic_evaluation_disabled"
    assert result["attempted_count"] == 1


@pytest.mark.parametrize("stage", ["source_verification", "oracle_import"])
def test_worker_pre_run_failure_proves_zero_attempts(tmp_path, monkeypatch, stage):
    input_path, output_path = tmp_path / "input.json", tmp_path / "output.json"
    input_path.write_text(json.dumps(request()), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["worker", "--request", str(input_path), "--output", str(output_path)])
    def fail(*_):
        raise OSError("secret artificial traceback text must not be exported")
    monkeypatch.setattr(w, "verify_cache", fail if stage == "source_verification" else lambda: {})
    monkeypatch.setattr(w, "load_scalar", fail)
    monkeypatch.setattr(w, "run", lambda *_args, **_kw: pytest.fail("must not call actual or artificial oracle"))
    assert w.main() == 1
    result = json.loads(output_path.read_bytes())
    assert result["stage"] == stage and result["attempted_count"] == 0
    assert result["status"] == "INCOMPLETE" and "secret" not in output_path.read_text()
