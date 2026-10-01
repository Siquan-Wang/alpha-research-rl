"""Independent presentation boundary: slot aliases must not replace evaluated provenance."""

import json

from test_astra_pool_explorer import completed, execute_script, payload


def test_alias_spelling_and_key_evaluation_provenance_stay_distinct(tmp_path, monkeypatch):
    # A deliberately changed synthetic renderer payload tests display semantics;
    # it is not presented as a newly verified financial report.
    harness = completed.__wrapped__(tmp_path, monkeypatch)
    value = payload(harness)
    report = json.loads(value["report_json"])
    slot = report["slot_results"][0]
    key = next(row for row in report["key_results"] if row["key"]["key_id"] == slot["key_id"])
    evaluated_expression = key["key"]["evaluation_expression"]
    alias = "  " + slot["expression"].replace(",", ", ") + "  "
    assert alias != evaluated_expression
    slot["expression"] = alias
    value["report_json"] = json.dumps(report, ensure_ascii=True)

    actual = execute_script(value)
    state = next(item for item in actual["states"]
                 if item["task"] == slot["task_id"] and item["arm"] == slot["arm"])
    displayed = next(row for row in state["rows"] if row[0] == str(slot["attempt"]))
    assert displayed[1] == alias
    retained = next(row for row in state["provenance"] if row["key"]["key_id"] == slot["key_id"])
    assert retained == key
    assert retained["key"]["evaluation_expression"] == evaluated_expression
    assert state["evidence"]["selector_metadata"] == next(
        row for row in report["selector_rows"]
        if row["task_id"] == slot["task_id"] and row["arm"] == slot["arm"]
    )
    assert sum(alias == row[1] for row in actual["allSlots"]) == 1
    assert len(actual["allSlots"]) == 180
