"""Synthetic coverage/citation integrity only; no current study records are read."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/validate_astra_grounding_audit.py"
SPEC = importlib.util.spec_from_file_location("grounding_validator", SCRIPT)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False) + "\n").encode()


def fixture_data():
    records, rows = [], []
    for index, (task, condition, repetition) in enumerate(validator.ORDER):
        response = json.dumps({"action": "propose", "expression": "ts_mean(returns,5)",
                               "hypothesis": "😀 Probe 0.1. Claim 0.9. Roughly stable.",
                               "revision": "Untested mechanism. Guaranteed improvement."}, ensure_ascii=True)
        observation = {"initial_evidence": {"probe_ic": 0.1, "exact_count": 1},
                       "candidate_feedback": [None, None] if condition == "masked" else [{"mean_ic": 0.1}, {"mean_ic": 0.2}]}
        prompt = "Synthetic instruction.\nDo not invent values.\n\nOBSERVATION:\n" + json.dumps(observation) + "\n"
        record = {"slot_id": f"{task}/{condition}/{repetition}", "task_id": task, "condition": condition,
                  "repetition": repetition, "prompt": prompt, "prompt_sha256": validator.raw_sha(prompt),
                  "prompt_path": f"artifacts/astra-matched-prefix-v1/prompts/{task}-{condition}.txt",
                  "response": response, "response_sha256": validator.raw_sha(response),
                  "response_source": "results/astra_matched_prefix_v1_submissions.json",
                  "response_json_pointer": f"/slots/{(index // 8) * 20 + index % 8}/adjudication/raw_response"}
        records.append(record)
        rows.append({**{name: record[name] for name in validator.BINDINGS}, "coverage": "assessed_clean",
                     "coverage_note": "Synthetic review: no factual claim coded.", "claims": [], "annotations": []})
    inputs = {"schema": validator.INPUT_SCHEMA, "created_utc": "2026-10-01T12:00:00+00:00",
              "submissions_sha256": "a" * 64, "scope": validator.SCOPE, "records": records}
    audit = {"schema": validator.AUDIT_SCHEMA, "inputs_sha256": hashlib.sha256(encoded(inputs)).hexdigest(),
             "submissions_sha256": inputs["submissions_sha256"], "audit_plan_sha256": validator.PLAN_SHA256,
             "coding_frozen_utc": "2026-10-01T12:05:00+00:00", "reviewer_statement": "Synthetic coding fixture only.",
             "exposure_log": [{"recorded_utc": "2026-10-01T12:05:00+00:00", "description": "No actual data inspected.",
                               "current_future_outcomes_seen": False}], "rows": rows}
    return inputs, audit


def finding(inputs, row, quote, category, *, field="hypothesis", annotation=False, references=None):
    value = json.loads(inputs["records"][row]["response"])[field]
    start = value.index(quote)
    result = {"category": category, "field": field, "start": start, "end": start + len(quote), "quote": quote,
              "references": references or [{"source": "observation", "pointer": "/initial_evidence/probe_ic",
                                             "exists": True, "value": 0.1}], "reason": "Synthetic reviewer comparison."}
    if not annotation:
        result["secondary_issues"] = []
    return result


def validate(tmp_path, inputs, audit, *, rebind=False):
    if rebind:
        audit["inputs_sha256"] = hashlib.sha256(encoded(inputs)).hexdigest()
    input_path, audit_path = tmp_path / "input.json", tmp_path / "audit.json"
    input_path.write_bytes(encoded(inputs))
    audit_path.write_bytes(encoded(audit))
    return validator.validate_audit(input_path, audit_path)


def test_all_eighty_rows_all_ten_states_and_separate_overlapping_claim_denominators(tmp_path):
    inputs, audit = fixture_data()
    first = audit["rows"][0]
    first["claims"] = [finding(inputs, 0, "Probe 0.1.", "derived-supported"),
                       finding(inputs, 0, "Claim 0.9.", "contradicted"),
                       finding(inputs, 0, "Roughly stable.", "ambiguous")]
    first["coverage"] = "assessed_with_findings"
    first["annotations"] = [finding(inputs, 0, "Guaranteed improvement.", "unsupported_certainty",
                                     field="revision", annotation=True)]
    # Malformed text keeps a coverage row; it must not inflate no-factual-claim N/A.
    inputs["records"][1]["response"] = "SYNTHETIC missing packet"
    inputs["records"][1]["response_sha256"] = validator.raw_sha(inputs["records"][1]["response"])
    audit["rows"][1].update(response_sha256=inputs["records"][1]["response_sha256"], coverage="not_text_assessable")
    result = validate(tmp_path, inputs, audit, rebind=True)
    assert result["status"] == "COMPLETE_CODING_STRUCTURE_VERIFIED"
    assert result["overall"]["packet_denominator"] == 80
    assert len(result["states"]) == 10 and all(item["overall"]["packet_denominator"] == 8 for item in result["states"])
    truth = result["conditions"]["truthful"]
    assert truth["packet_denominator"] == 40 and truth["coded_factual_claims"] == 3
    assert truth["applicable_citation_opportunities"] == 3
    assert truth["not_text_assessable_packets"] == 1 and truth["not_applicable_no_factual_claims_packets"] == 38
    assert [truth["overlapping_packet_flags"][key] for key in (
        "contradicted_or_unsupported_claim", "ambiguous_claim", "derived_supported_claim", "unsupported_certainty")] == [1] * 4
    assert result["semantic_correctness_verified"] is result["clock_or_outcome_blinding_verified"] is False
    assert result["composite_reasoning_score_produced"] is False


@pytest.mark.parametrize("change", ["missing-input", "missing-row", "duplicate-input", "duplicate-row", "wrong-order"])
def test_incomplete_or_duplicate_population_is_rejected(tmp_path, change):
    inputs, audit = fixture_data()
    if change == "missing-input":
        inputs["records"].pop()
    elif change == "missing-row":
        audit["rows"].pop()
    elif change == "duplicate-input":
        inputs["records"][1] = copy.deepcopy(inputs["records"][0])
    elif change == "duplicate-row":
        audit["rows"][1] = copy.deepcopy(audit["rows"][0])
    else:
        audit["rows"][0], audit["rows"][1] = audit["rows"][1], audit["rows"][0]
    with pytest.raises(ValueError):
        validate(tmp_path, inputs, audit, rebind=True)


@pytest.mark.parametrize("change", ["quote", "utf16-span", "bool-span", "input-hash", "response-hash", "bad-reference", "wrong-plan"])
def test_bad_span_hash_or_evidence_binding_is_rejected(tmp_path, change):
    inputs, audit = fixture_data()
    claim = finding(inputs, 0, "Probe 0.1.", "displayed-supported")
    audit["rows"][0]["claims"] = [claim]
    assert claim["start"] == 2  # Emoji is one Unicode code point, not two UTF-16 units.
    if change == "quote":
        claim["quote"] = "different"
    elif change == "utf16-span":
        claim["start"] += 1
        claim["end"] += 1
    elif change == "bool-span":
        claim["start"] = True
    elif change == "input-hash":
        audit["inputs_sha256"] = "0" * 64
    elif change == "response-hash":
        audit["rows"][0]["response_sha256"] = "0" * 64
    elif change == "bad-reference":
        claim["references"][0]["value"] = 0.10000000000000002
    else:
        audit["audit_plan_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        validate(tmp_path, inputs, audit)


def test_supported_claims_and_untested_hypotheses_can_be_clean_with_null_and_absent_references(tmp_path):
    inputs, audit = fixture_data()
    audit["rows"][0]["claims"] = [finding(inputs, 0, "Probe 0.1.", "displayed-supported")]
    audit["rows"][0]["annotations"] = [finding(inputs, 0, "Untested mechanism.", "untested_hypothesis",
        field="revision", annotation=True, references=[{"source": "expression", "text": "ts_mean(returns,5)"}])]
    audit["rows"][4]["claims"] = [finding(inputs, 4, "Claim 0.9.", "unsupported reported measurement/action", references=[
        {"source": "observation", "pointer": "/candidate_feedback/0", "exists": True, "value": None},
        {"source": "observation", "pointer": "/candidate_feedback/0/mean_ic", "exists": False, "value": None},
        {"source": "instruction", "line": 2, "text": "Do not invent values."}])]
    audit["rows"][4]["coverage"] = "assessed_with_findings"
    report = validate(tmp_path, inputs, audit)
    assert report["conditions"]["truthful"]["coverage"]["assessed_clean"] == 40
    assert report["conditions"]["masked"]["main_claim_counts"]["unsupported reported measurement/action"] == 1
    audit["rows"][4]["claims"][0]["references"][0]["exists"] = False
    with pytest.raises(ValueError, match="reference differs"):
        validate(tmp_path, inputs, audit)


@pytest.mark.parametrize("value", [True, 1.0])
def test_source_integer_reference_is_type_exact(tmp_path, value):
    inputs, audit = fixture_data()
    audit["rows"][0]["claims"] = [finding(inputs, 0, "Probe 0.1.", "displayed-supported", references=[
        {"source": "observation", "pointer": "/initial_evidence/exact_count", "exists": True, "value": value}])]
    with pytest.raises(ValueError, match="reference differs"):
        validate(tmp_path, inputs, audit)


def test_pointer_validates_later_escapes_even_after_an_absent_or_null_ancestor():
    observation = {"candidate_feedback": [None, None]}
    for pointer in ("/candidate_feedback/0/missing/~2", "/missing/~2"):
        with pytest.raises(ValueError, match="invalid JSON pointer escape"):
            validator.pointer(observation, pointer)
    assert validator.pointer(observation, "/candidate_feedback/0/missing/~0~1") == (False, None)


@pytest.mark.parametrize("raw", ['{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}'])
def test_duplicate_keys_and_nonfinite_json_are_rejected(raw):
    with pytest.raises(ValueError):
        validator.parse(raw)


def test_duplicate_main_claim_and_false_clean_disposition_rejected(tmp_path):
    inputs, audit = fixture_data()
    claim = finding(inputs, 0, "Probe 0.1.", "contradicted")
    audit["rows"][0]["claims"] = [claim]
    with pytest.raises(ValueError, match="coverage disposition"):
        validate(tmp_path, inputs, audit)
    audit["rows"][0]["coverage"] = "assessed_with_findings"
    audit["rows"][0]["claims"].append(copy.deepcopy(claim))
    with pytest.raises(ValueError, match="multiple main classifications"):
        validate(tmp_path, inputs, audit)


def test_declared_exposure_not_attested_and_cli_never_overwrites_inputs(tmp_path):
    inputs, audit = fixture_data()
    audit["exposure_log"][0]["current_future_outcomes_seen"] = True
    result = validate(tmp_path, inputs, audit)
    assert result["reviewer_declares_current_future_exposure"] is True
    assert result["clock_or_outcome_blinding_verified"] is False
    input_path, audit_path = tmp_path / "input.json", tmp_path / "audit.json"
    original = input_path.read_bytes()
    args = ["--inputs", str(input_path), "--audit", str(audit_path)]
    with pytest.raises(SystemExit):
        validator.main([*args, "--output", str(input_path)])
    output = tmp_path / "verified.json"
    validator.main([*args, "--output", str(output)])
    assert json.loads(output.read_bytes())["overall"]["packet_denominator"] == 80
    with pytest.raises(SystemExit):
        validator.main([*args, "--output", str(output)])
    assert input_path.read_bytes() == original
