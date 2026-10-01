"""Artificial panels and lifecycle checks only; never the canonical 512+128 bank."""

import copy
import hashlib
import importlib.util
import itertools
import json
import math
from fractions import Fraction
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("sealed_fixture_runner", ROOT / "scripts/check_sealed_confirmation.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def forbidden(*args, **kwargs):
    raise AssertionError("a forbidden generator or owner was invoked")


def fraction(value):
    assert value["encoding"] == "unsigned-base16-rational"
    return Fraction(int(value["numerator_hex"], 16), int(value["denominator_hex"], 16))


def test_exact_thresholds_and_discrete_envelopes_without_simulation():
    value = runner.exact_thresholds()
    assert (value["K_reject_at_least"], value["null_upper_inclusive"], value["oracle_lower_inclusive"]) == (142, 37, 128)
    pi0 = Fraction(sum(math.comb(256, k) for k in range(142, 257)), 2**256)
    assert fraction(value["pi0"]) == pi0
    assert pi0 <= Fraction(1, 20) < Fraction(sum(math.comb(256, k) for k in range(141, 257)), 2**256)
    assert fraction(value["null_exceedance_at_upper"]) <= Fraction(1, 300)
    assert fraction(value["null_exceedance_at_previous"]) > Fraction(1, 300)
    assert fraction(value["oracle_count_below_lower"]) == 1 - fraction(value["pi1"])**128
    assert fraction(value["oracle_single_panel_miss"]) == 1 - fraction(value["pi1"])
    assert fraction(value["orientation_only_naive_rate"]) == 2*pi0
    assert value["fault_exceedances_are_validation_gates"] is False


def test_artificial_stream_encoding_and_all_parities():
    namespace = "artificial-fixture-only"
    raw = hashlib.shake_256(b"artificial-fixture-only|731|null|0009|search_features").digest(3)
    expected = [int(bit) for byte in raw for bit in reversed(f"{byte:08b}")][:17]
    assert runner.feature_bits(namespace, "null", 9, "search_features", 17) == expected
    features = tuple(itertools.product((-1, 1), repeat=6))
    all_vectors = []
    for mask in range(64):
        expected = tuple((-1)**sum(row[j] == -1 for j in range(6) if mask & 2**j) for row in features)
        assert runner.predict(mask, 1, features) == expected
        assert runner.predict(mask, -1, features) == tuple(-x for x in expected)
        all_vectors.append(expected)
    assert len(set(all_vectors)) == 64
    assert all(sum(a*b for a, b in zip(all_vectors[i], all_vectors[j])) == 0
               for i in range(64) for j in range(i))


def test_search_earliest_ties_preserve_every_repeated_attempt():
    calls = []

    def feedback(mask):
        calls.append(mask)
        return {"alignment": 0, "denominator": 8}

    found = runner.search("adaptive", feedback)
    assert calls == [0] + [1 << (i % 6) for i in range(31)]
    assert found["selected"]["attempt"] == 1 and found["selected"]["orientation"] == 1
    assert found["attempt_count"] == 32 and found["unique_masks"] == 7 and found["duplicate_attempts"] == 25
    assert [x["attempt"] for x in found["attempts"]] == list(range(1, 33))
    assert all(x["incumbent_attempt"] == 1 for x in found["attempts"])


def test_adaptive_queries_really_depend_on_feedback():
    def feedback(mask):
        return {"alignment": -8 if mask == 1 else 0, "denominator": 8}

    found = runner.search("adaptive", feedback)
    assert [x["mask"] for x in found["attempts"][:4]] == [0, 1, 3, 5]
    assert found["selected"]["mask"] == 1 and found["selected"]["orientation"] == -1
    fixed = runner.search("fixed", feedback)
    assert [x["mask"] for x in fixed["attempts"]] == list(range(32))
    assert fixed["duplicate_attempts"] == 0


@pytest.fixture
def fake_root(tmp_path, monkeypatch):
    """Two handcrafted panels, explicitly different namespace and eight rows."""
    for relative in runner.SOURCE_PATHS:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / relative).read_bytes())
    (tmp_path / "results").mkdir()
    monkeypatch.setattr(runner, "STUDY", "artificial-lifecycle-only")
    monkeypatch.setattr(runner, "PANELS", (("null", 91), ("planted", 92)))
    monkeypatch.setattr(runner, "N_ROWS", 8)
    monkeypatch.setattr(runner, "_thresholds_json", lambda: json.dumps({
        "scope": "ARTIFICIAL_LIFECYCLE_METADATA_NOT_CANONICAL_CALIBRATION",
        "null_upper_inclusive": 1, "oracle_lower_inclusive": 0}))
    monkeypatch.setattr(runner, "generate_inputs", forbidden)
    return tmp_path


def make_receipt(root):
    value = {"schema": "sealed-confirmation-publication-v1", "study": runner.STUDY,
             "commit": "a"*40, "public_repository_url": "https://github.com/Siquan-Wang/alpha-research-rl",
             "verified_utc": "2000-01-01T00:00:00+00:00", "paths_sha256": runner.publication_files(root)}
    path = root / "artificial-receipt.json"
    runner.write_once(path, value)
    return path


def artificial_inputs(law, index, *, namespace, rows):
    assert namespace == "artificial-lifecycle-only" and rows == 8 and index in (91, 92)
    x = [list(row) for row in itertools.product((-1, 1), repeat=3)]
    x = [row + [1, -1, 1] for row in x]
    sy = [row[0]*row[1] for row in x]
    cy = sy if law == "planted" else [1]*8
    return x, sy, copy.deepcopy(x), lambda: list(cy)


def complete_artificial(root, monkeypatch):
    contract = runner.prepare(root)
    receipt = make_receipt(root)
    monkeypatch.setattr(runner, "generate_inputs", artificial_inputs)
    report = runner.run(root, receipt)
    return contract, receipt, report


def test_prepare_never_generates_and_failed_namespace_is_terminal(fake_root):
    contract = runner.prepare(fake_root)
    assert contract["canonical_panel_generations"] == 0
    assert contract["study"] == "artificial-lifecycle-only"
    assert contract["population"]["total_panels"] == 2
    runner.write_once(fake_root / runner.DIRECTORY / "PREPARE_FAILED.json", {"failed": True})
    with pytest.raises(ValueError, match="preparation namespace"):
        runner.publication_files(fake_root)
    with pytest.raises(ValueError, match="already exists"):
        runner.prepare(fake_root)


@pytest.mark.parametrize("relative", ["scripts/check_sealed_confirmation.py", "src/alpha_research_rl/sealed_confirmation.py"])
def test_loaded_source_must_equal_source_root(fake_root, relative):
    path = fake_root / relative
    path.write_bytes(path.read_bytes() + b"\n# different checkout\n")
    with pytest.raises(ValueError, match="loaded runner/core"):
        runner.prepare(fake_root)
    assert not (fake_root / runner.DIRECTORY).exists()


def test_partial_prepare_write_remains_permanently_failed(fake_root, monkeypatch):
    original = runner.write_once

    def failing(path, body):
        original(path, body)
        if Path(path).name == "contract.json":
            raise OSError("artificial failure after complete bytes")

    monkeypatch.setattr(runner, "write_once", failing)
    with pytest.raises(OSError):
        runner.prepare(fake_root)
    assert (fake_root / runner.CONTRACT).is_file()
    assert (fake_root / runner.DIRECTORY / "PREPARE_FAILED.json").is_file()
    with pytest.raises(ValueError, match="preparation namespace"):
        runner.publication_files(fake_root)


def test_full_artificial_run_replay_uses_saved_arrays_and_retains_every_arm(fake_root, monkeypatch):
    contract, _, report = complete_artificial(fake_root, monkeypatch)
    assert report["study"] == "artificial-lifecycle-only"
    assert report["population"]["total_panels"] == report["execution"]["panel_generations"] == 2
    assert report["analysis"]["calibration"]["fixed_correct_null"]["n"] == 1
    assert report["source_sha256"] == contract["source_sha256"]
    for row in report["panels"]:
        assert row["n_rows"] == 8
        for arm, outcome in row["outcomes"].items():
            assert outcome["statistic_role"] == ("confirmation" if arm in runner.ARMS[:3] else "naive_diagnostic")
            assert outcome["attempt_count"] == (0 if arm == "oracle" else 1 if arm == "orientation_only_leak" else 32)
    monkeypatch.setattr(runner, "generate_inputs", forbidden)
    monkeypatch.setattr(runner, "feature_bits", forbidden)
    before = {p.relative_to(fake_root): p.read_bytes() for p in fake_root.rglob("*") if p.is_file()}
    result = runner.replay(fake_root)
    after = {p.relative_to(fake_root): p.read_bytes() for p in fake_root.rglob("*") if p.is_file()}
    assert result["panels"] == 2 and result["new_panel_generations"] == result["writes"] == 0
    assert before == after
    with pytest.raises(ValueError, match="already exists"):
        runner.run(fake_root, fake_root / "artificial-receipt.json")


@pytest.mark.parametrize("mutation", ["no_hash", "extra_field", "clock"])
def test_replay_rejects_start_schema_and_chronology(fake_root, monkeypatch, mutation):
    complete_artificial(fake_root, monkeypatch)
    path = fake_root / runner.EXECUTION / "STARTED.json"
    value = runner.read_json(path)
    value.pop("body_sha256")
    if mutation == "extra_field":
        value["unexpected"] = True
    elif mutation == "clock":
        value["created_utc"] = "1999-01-01T00:00:00+00:00"
    if mutation != "no_hash":
        value = runner.sealed(value)
    path.write_text(runner.canonical(value), encoding="ascii")
    with pytest.raises(ValueError, match="schema|preceded publication"):
        runner.replay(fake_root)


def test_bad_receipt_never_claims_execution(fake_root):
    runner.prepare(fake_root)
    path = make_receipt(fake_root)
    value = runner.read_json(path)
    value["paths_sha256"][runner.CONTRACT] = "0"*64
    path.write_text(runner.canonical(value), encoding="ascii")
    with pytest.raises(ValueError, match="publication file map"):
        runner.run(fake_root, path)
    assert not (fake_root / runner.EXECUTION).exists()


def test_failed_generation_preserves_started_and_forbids_retry(fake_root):
    runner.prepare(fake_root)
    receipt = make_receipt(fake_root)
    with pytest.raises(AssertionError, match="forbidden generator"):
        runner.run(fake_root, receipt)
    execution = fake_root / runner.EXECUTION
    assert (execution / "FAILED.json").is_file()
    assert runner._events(execution / "panels/null-0091/events.jsonl")[0]["event"] == "STARTED"
    assert not (fake_root / runner.RESULT).exists()
    with pytest.raises(ValueError, match="already exists"):
        runner.run(fake_root, receipt)
    with pytest.raises(ValueError, match="failed or active"):
        runner.replay(fake_root)


def test_fault_detection_is_never_a_pass_gate(fake_root, monkeypatch):
    _, _, report = complete_artificial(fake_root, monkeypatch)
    rows = copy.deepcopy(report["panels"])
    for row in rows:
        for arm in runner.ARMS:
            row["outcomes"][arm]["statistic"]["reject"] = False
    analysis = runner.summarize(rows, {"null_upper_inclusive": 1, "oracle_lower_inclusive": 0})
    assert analysis["validation_pass"] is True
    assert all(not x["exceeds_correct_null_upper"] and not x["used_as_validation_gate"]
               for x in analysis["fault_statistics"].values())


def test_replay_rejects_saved_array_change_even_with_rehashed_event_chain(fake_root, monkeypatch):
    complete_artificial(fake_root, monkeypatch)
    path = fake_root / runner.EXECUTION / "panels/null-0091/events.jsonl"
    events = runner._events(path)
    owner = next(x for x in events if x["event"] == "INPUT_OWNER")
    owner["body"]["search_labels"][0] *= -1
    previous = None
    rebuilt = []
    for event in events:
        event.pop("body_sha256")
        event["previous_body_sha256"] = previous
        event = runner.sealed(event)
        previous = event["body_sha256"]
        rebuilt.append(event)
    path.write_bytes(b"".join((runner.canonical(e)+"\n").encode("ascii") for e in rebuilt))
    with pytest.raises(ValueError, match="recomputation"):
        runner.replay(fake_root)


def test_receipt_is_parsed_from_the_same_single_read_that_is_retained(fake_root, monkeypatch):
    runner.prepare(fake_root)
    path = make_receipt(fake_root)
    raw = path.read_bytes()
    original = Path.read_bytes
    reads = []

    def single_read(candidate):
        if candidate == path:
            reads.append(candidate)
            assert len(reads) == 1
        return original(candidate)

    monkeypatch.setattr(Path, "read_bytes", single_read)
    value, retained = runner._receipt(fake_root, path)
    assert retained == raw and value == json.loads(raw)


def test_panel_start_identity_does_not_coerce_float_to_integer(fake_root, monkeypatch):
    complete_artificial(fake_root, monkeypatch)
    path = fake_root / runner.EXECUTION / "panels/null-0091/events.jsonl"
    events = runner._events(path)
    events[0]["body"]["index"] = 91.0
    previous, rebuilt = None, []
    for event in events:
        event.pop("body_sha256")
        event["previous_body_sha256"] = previous
        event = runner.sealed(event)
        previous = event["body_sha256"]
        rebuilt.append(event)
    path.write_bytes(b"".join((runner.canonical(e)+"\n").encode("ascii") for e in rebuilt))
    with pytest.raises(ValueError, match="panel start identity"):
        runner.replay(fake_root)


def test_evidence_change_after_validation_cannot_return_an_unverified_hash(fake_root, monkeypatch):
    complete_artificial(fake_root, monkeypatch)
    original_report = runner._report
    path = fake_root / runner.RESULT

    def mutate_after_compute(*args):
        value = original_report(*args)
        path.write_bytes(path.read_bytes() + b" ")
        return value

    monkeypatch.setattr(runner, "_report", mutate_after_compute)
    with pytest.raises(ValueError, match="changed during replay"):
        runner.replay(fake_root)
