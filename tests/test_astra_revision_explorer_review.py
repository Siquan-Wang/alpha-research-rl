"""Independent presentation edges on synthetic data; no real-bank access."""

import hashlib
import json

from test_astra_revision_core import state
from test_astra_revision_explorer import execute_script, synthetic_payload

from alpha_research_rl import astra_revision_core as core
from alpha_research_rl import astra_revision_explorer as explorer


def reseal_presentation_fixture(payload, report):
    """A verifier double for UI tests, never a substitute for driver replay."""
    report.pop("body_sha256")
    report["analysis"] = core.analyze(report["rows"])
    raw = json.dumps(explorer.saved._sealed(report), ensure_ascii=True).encode()
    payload["report_json"] = raw.decode()
    payload["report_bytes"] = len(raw)
    payload["report_sha256"] = hashlib.sha256(raw).hexdigest()
    payload["verification"]["report_sha256"] = payload["report_sha256"]
    return payload


def test_all_invalid_generator_retains_forty_slots_and_null_conditional_ic():
    payload = synthetic_payload()
    report = json.loads(payload["report_json"])
    for row in report["rows"]:
        if row["generator"] != "truthful":
            continue
        record = core.adjudicate("SYNTHETIC invalid packet", state(row["task_id"]), None)
        row.update(adjudication=record, candidate_key_id=None,
                   selected_key_id=row["baseline_key_id"],
                   candidate_outcome_source="ineligible_or_historically_unusable",
                   canonical_duplicate_across_new_slots=False,
                   **core.resolve_branch(record, core.quality(False, -1.0), core.quality(True, 0.12)))
    actual = execute_script(reseal_presentation_fixture(payload, report))
    summary = next(row for row in actual["summaries"] if row[0] == "Truthful feedback")
    assert summary[1:9] == ["40", "0", "40", "-1.000000", "0.000000", "0.000000", "unavailable", "0"]
    assert summary[9:] == ["0.120000", "0.000000", "-0.010000"]
    assert len(actual["allSlots"]) == 200 and len(actual["states"]) == 50
    for cell in actual["cells"]:
        if cell["generator"] == "truthful":
            assert len(cell["rows"]) == 4
            assert all(row[10:13] == ["-1", "0.12", "0"] for row in cell["rows"])


def test_literal_proposal_alias_and_evaluated_cache_spelling_remain_distinct():
    payload = synthetic_payload()
    report = json.loads(payload["report_json"])
    row = report["rows"][0]
    original = row["adjudication"]["packet"]["expression"]
    alias = original.replace(",", ", ")
    assert alias != original
    row["adjudication"]["packet"]["expression"] = alias
    row["adjudication"]["raw_response"] = json.dumps(row["adjudication"]["packet"])
    assert core.validate_proposal(row["adjudication"]["raw_response"])["canonical_ast"] == row["adjudication"]["canonical_ast"]
    key = next(key for key in report["keys"] if key["key"]["key_id"] == row["candidate_key_id"])
    assert key["raw_evaluator_outcome"]["expression"] == original
    actual = execute_script(reseal_presentation_fixture(payload, report))
    first = actual["cells"][0]
    assert first["rows"][0][1] == actual["allSlots"][0][1] == alias
    provenance = next(key for key in first["provenance"] if key["key"]["key_id"] == row["candidate_key_id"])
    assert provenance["raw_evaluator_outcome"]["expression"] == original
    assert first["evidence"][0]["adjudication"]["packet"]["expression"] == alias
