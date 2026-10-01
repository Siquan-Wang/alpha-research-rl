"""Synthetic-only structural, byte-binding and browser-script checks."""

import hashlib
import json
import shutil
import subprocess
from html.parser import HTMLParser

import pytest
from test_astra_pool_diagnosis import Harness, metrics

from alpha_research_rl import astra_pool_diagnosis as diagnosis
from alpha_research_rl import astra_pool_explorer as explorer


class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.blocks = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.current = {"id": dict(attrs).get("id"), "text": ""}
            self.blocks.append(self.current)

    def handle_endtag(self, tag):
        if tag == "script":
            self.current = None

    def handle_data(self, value):
        if self.current is not None:
            self.current["text"] += value


@pytest.fixture
def completed(tmp_path, monkeypatch):
    harness = Harness(tmp_path, monkeypatch)
    harness.prepare()
    harness.publish()

    def future_failure(raw, call):
        if call <= 2:
            raw.update(status="invalid" if call == 1 else "unscorable",
                       reason="invalid_expression" if call == 1 else "insufficient_assessment_support",
                       assessment=None if call == 1 else {
                           **metrics(None), "ic_std": None, "coverage": 0.0, "n_dates": 0,
                       }, reward=-1.01, oriented_future_ic=None)
        return raw

    harness.transform = future_failure
    harness.execute()
    harness.public_report = harness.root / "public-report.json"
    harness.public_report.write_bytes((harness.execution / "COMPLETE.json").read_bytes())
    return harness


def payload(harness):
    return explorer.build_payload(harness.contract_path, harness.execution, harness.public_report,
                                  source_root=harness.root)


def test_complete_saved_snapshot_uses_exact_bytes_without_market_or_runtime_access(completed, monkeypatch):
    raw = completed.public_report.read_bytes()
    completed.data.unlink()
    monkeypatch.setattr(diagnosis, "_data_bytes", lambda *_: pytest.fail("no raw data reads"))
    monkeypatch.setattr(diagnosis, "_versions", lambda: pytest.fail("no scoring-runtime requirement"))
    monkeypatch.setattr(diagnosis, "_load_tasks", lambda *_: pytest.fail("no task construction"))
    value = payload(completed)
    assert value["report_json"].encode("utf-8") == raw
    assert value["report_sha256"] == hashlib.sha256(raw).hexdigest()
    assert value["captured_execution_file_count"] == 219
    assert value["verification"]["status"] == "SAVED_ARITHMETIC_VERIFIED"
    assert value["verification"]["new_financial_scores"] == 0
    assert len(completed.calls) == 108  # No additional fake evaluator calls from the renderer.
    parsed = Scripts()
    parsed.feed(explorer.render(value))
    assert [block["id"] for block in parsed.blocks] == ["pool-data", None]
    assert json.loads(parsed.blocks[0]["text"])["report_json"].encode("utf-8") == raw


@pytest.mark.parametrize("target", ["public-report", "execution-report", "completed-job"])
def test_original_file_changes_after_snapshot_verification_cannot_change_page(completed, monkeypatch, target):
    raw = completed.public_report.read_bytes()
    path = {"public-report": completed.public_report,
            "execution-report": completed.execution / "COMPLETE.json",
            "completed-job": next((completed.execution / "jobs").glob("*/COMPLETED.json"))}[target]
    actual_replay = diagnosis.replay_pool_diagnosis

    def verify_then_mutate(*args, **kwargs):
        assert kwargs["source_root"] != completed.root
        verified = actual_replay(*args, **kwargs)
        path.write_bytes(b'{"tampered_after_snapshot_verification":true}')
        return verified

    monkeypatch.setattr(diagnosis, "replay_pool_diagnosis", verify_then_mutate)
    value = payload(completed)
    assert value["report_json"].encode("utf-8") == raw
    assert value["report_sha256"] == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize("kind", ["missing-job", "unknown-job-file", "report-whitespace", "tampered-job"])
def test_incomplete_or_changed_evidence_never_produces_html(completed, kind):
    job = next((completed.execution / "jobs").glob("*/COMPLETED.json"))
    if kind == "missing-job":
        job.unlink()
    elif kind == "unknown-job-file":
        (job.parent / "unexplained.json").write_text("{}", encoding="utf-8")
    elif kind == "report-whitespace":
        completed.public_report.write_bytes(completed.public_report.read_bytes() + b" ")
    else:
        job.write_bytes(b'{"tampered":true}')
    destination = completed.root / "new.html"
    with pytest.raises(ValueError):
        explorer.main(["--contract", str(completed.contract_path), "--execution-dir", str(completed.execution),
                       "--report", str(completed.public_report), "--source-root", str(completed.root),
                       "--output", str(destination)])
    assert not destination.exists()


def test_hostile_json_and_surrogates_are_inert_writable_and_lossless():
    value = {"report_json": '\ud800</ScRiPt><script>alert("x")</script><img src=x onerror=alert(1)>\udfff&\u2028\u2029'}
    html = explorer.render(value)
    html.encode("utf-8")
    parsed = Scripts()
    parsed.feed(html)
    assert [block["id"] for block in parsed.blocks] == ["pool-data", None]
    assert json.loads(parsed.blocks[0]["text"]) == value
    assert "innerHTML" not in parsed.blocks[1]["text"]
    assert "fetch(" not in parsed.blocks[1]["text"]


NODE_DOM = r"""
const fs=require('fs'),vm=require('vm'),input=JSON.parse(fs.readFileSync(0,'utf8'));
class Element {
 constructor(tag){this.tag=tag;this.children=[];this.textContent='';this.value='';this.listeners={};}
 appendChild(node){this.children.push(node);if(this.tag==='select'&&!this.value)this.value=node.value;return node;}
 replaceChildren(...nodes){this.children=[];for(const node of nodes)this.appendChild(node);}
 addEventListener(name,callback){this.listeners[name]=callback;}
}
const elements=new Map(),document={
 getElementById(id){if(!elements.has(id))elements.set(id,new Element(['task','arm'].includes(id)?'select':'div'));return elements.get(id);},
 createElement(tag){return new Element(tag);}
};
document.getElementById('pool-data').textContent=input.data;
vm.runInNewContext(input.script,{document},{timeout:3000});
const rows=id=>document.getElementById(id).children.map(tr=>tr.children.map(td=>String(td.textContent)));
const states=[];
for(const task of document.getElementById('task').children)for(const arm of document.getElementById('arm').children){
 document.getElementById('task').value=task.value;document.getElementById('task').listeners.change();
 document.getElementById('arm').value=arm.value;document.getElementById('arm').listeners.change();
 states.push({task:task.value,arm:arm.value,rows:rows('candidates'),
             evidence:JSON.parse(document.getElementById('pool-evidence').textContent),
             provenance:JSON.parse(document.getElementById('pool-provenance').textContent)});
}
process.stdout.write(JSON.stringify({states,summaries:rows('summaries'),periods:rows('periods'),
 years:rows('years'),allSlots:rows('all-slots'),raw:document.getElementById('raw-report').textContent,
 population:document.getElementById('population').textContent}));
"""


def execute_script(value):
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node needed for the small synthetic DOM check")
    parsed = Scripts()
    parsed.feed(explorer.render(value))
    result = subprocess.run([node, "-e", NODE_DOM],
                            input=json.dumps({"data": parsed.blocks[0]["text"], "script": parsed.blocks[1]["text"]}),
                            capture_output=True, text=True, encoding="utf-8", check=True, timeout=15, shell=False)
    return json.loads(result.stdout)


def test_all_controls_slots_selectors_null_failures_and_denominators_are_rendered(completed):
    value = payload(completed)
    report = json.loads(value["report_json"])
    actual = execute_script(value)
    assert len(actual["states"]) == 30
    assert len(actual["summaries"]) == 12
    assert all(row[1] == "10" for row in actual["summaries"])
    assert len(actual["periods"]) == 30 and len(actual["years"]) == 15
    assert all(row[1] == "2" for row in actual["years"])
    assert len(actual["allSlots"]) == 180
    assert "180 original slots" in actual["population"]
    assert actual["raw"] == value["report_json"]
    flags = {"original": "Original feedback selector", "first": "First charged proposal",
             "minimum_ast": "Minimum AST nodes", "oracle": "Unattainable hindsight oracle"}
    seen, failed = set(), set()
    for state in actual["states"]:
        assert len(state["rows"]) == len(state["evidence"]["slots"]) == 6
        selection = state["evidence"]["selector_metadata"]["selectors"]
        for slot, row in zip(state["evidence"]["slots"], state["rows"], strict=True):
            seen.add(slot["slot_id"])
            assert row[0] == str(slot["attempt"]) and row[1] == slot["expression"]
            assert row[3] == ("−1" if slot["orientation"] == -1 else "+1")
            expected_flags = [label for name, label in flags.items() if selection[name]["slot_id"] == slot["slot_id"]]
            assert row[8] == (" · ".join(expected_flags) if expected_flags else "None")
            if not slot["diagnosis"]["valid"]:
                failed.add(slot["diagnosis"]["status"])
                assert row[4] == "unavailable" and row[6] == "-1.060000"
        assert {key["key"]["key_id"] for key in state["provenance"]} == {
            slot["key_id"] for slot in state["evidence"]["slots"]}
    assert seen == {slot["slot_id"] for slot in report["slot_results"]}
    assert failed == {"invalid", "unscorable"}


def test_null_expression_and_hostile_text_use_text_nodes_without_dropping_slot(completed):
    # Deliberately mutate a synthetic renderer payload, not verified financial evidence.
    value = payload(completed)
    report = json.loads(value["report_json"])
    slot = report["slot_results"][0]
    slot.update(expression=None, canonical_ast=None, feedback=None, orientation=None, ast_node_count=None)
    hostile = '<img src=x onerror=alert("unsafe")>\ud800'
    report["slot_results"][1]["expression"] = hostile
    value["report_json"] = json.dumps(report, ensure_ascii=True)
    actual = execute_script(value)
    row, hostile_row = actual["states"][0]["rows"][:2]
    assert row[1] == "No valid expression"
    assert row[2] == row[3] == row[7] == "unavailable"
    assert hostile_row[1] == hostile
    assert len(actual["allSlots"]) == 180


def test_cli_refuses_overwrite_and_execution_collision_before_validation(tmp_path, monkeypatch):
    monkeypatch.setattr(explorer, "build_payload", lambda *_args, **_kwargs: pytest.fail("must reject before reads"))
    output = tmp_path / "existing.html"
    output.write_text("preserved", encoding="utf-8")
    args = ["--contract", str(tmp_path / "contract.json"), "--execution-dir", str(tmp_path / "execution"),
            "--report", str(tmp_path / "report.json"), "--source-root", str(tmp_path)]
    for path in (output, tmp_path / "execution" / "new.html", tmp_path / "report.json"):
        with pytest.raises(SystemExit):
            explorer.main([*args, "--output", str(path)])
    assert output.read_text(encoding="utf-8") == "preserved"
