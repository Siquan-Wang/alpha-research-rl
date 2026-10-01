"""Artificial renderer data and verifier doubles; no model, market or actual-bank use."""

import copy
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest
from test_astra_pool_explorer import Scripts
from test_astra_revision_core import feedback, packet, state

from alpha_research_rl import astra_revision_core as core
from alpha_research_rl import astra_revision_explorer as explorer
from alpha_research_rl import astra_revision_study as study


def synthetic_payload():
    """Presentation fixture; a seal is not a replacement for driver verification."""
    rows, keys, contexts, seen = [], {}, {}, set()
    for task in core.TASK_IDS:
        private = state(task)
        contexts[task] = {"baseline": private["baseline"], "prefix": private["prefix"], "prompts": {
            condition: {"text": core.prompt(private, condition),
                        "sha256": hashlib.sha256(core.prompt(private, condition).encode()).hexdigest()}
            for condition in core.CONDITIONS}}
        baseline_id = task + "/baseline"
        keys[baseline_id] = {"key": {"key_id": baseline_id}, "raw_evaluator_outcome": {
            "expression": private["baseline"]["expression"], "status": "ok", "reason": None},
            "provenance": {"kind": "prior_pool_cache"}, "quality": {"valid": True, "Q": 0.12}}
        for generator in core.GENERATORS:
            for repetition in core.REPETITIONS:
                expression = "delay(returns,45)"
                metrics = feedback(0.5)
                if generator in core.CHEAP_TEXT:
                    response = core.cheap_packet(private, generator, repetition)["raw_response"]
                    expression = json.loads(response)["expression"]
                    metrics = feedback(0.3)
                elif generator == "truthful" and repetition == 2:
                    response, metrics = "SYNTHETIC invalid JSON", None
                elif generator == "truthful" and repetition == 3:
                    response, metrics = packet("delay(delay(returns,60),1)"), None
                elif generator == "truthful" and repetition == 4:
                    response = packet("ts_mean(returns,7)")
                    metrics = {"mean_ic": None, "ic_std": None, "n_dates": 0, "n_signal_dates": private["feedback_length"],
                               "coverage": 0.0, "usable": False}
                else:
                    expression = {1: "delta(returns,48)", 2: "delay(returns,46)",
                                  3: private["baseline"]["expression"], 4: expression}.get(repetition, expression)
                    response = packet(expression)
                proposal = core.validate_proposal(response)
                for prefix in private["prefix"]:
                    if proposal["canonical_ast"] == prefix["canonical_ast"]:
                        metrics = prefix["feedback"]
                record = core.adjudicate(response, private, metrics)
                valid = record["historically_usable"] and not (generator == "masked" and repetition == 1)
                q = 0.2 if valid else -1.0
                key_id = None
                if record["historically_usable"]:
                    key_id = task + "/" + hashlib.sha256(record["canonical_ast"].encode()).hexdigest()
                    if record["canonical_ast"] == private["baseline"]["canonical_ast"]:
                        key_id, q = baseline_id, 0.12
                    elif key_id not in keys:
                        keys[key_id] = {"key": {"key_id": key_id}, "raw_evaluator_outcome": {
                            "expression": record["packet"]["expression"], "status": "ok" if valid else "unscorable",
                            "reason": None if valid else "insufficient_assessment_support"},
                            "provenance": {"kind": "new_evaluation"}, "quality": {"valid": valid, "Q": q}}
                    valid, q = keys[key_id]["quality"].values()
                scores = core.resolve_branch(record, core.quality(valid, q), core.quality(True, 0.12))
                ast_id = (task, record["canonical_ast"])
                rows.append({"slot_id": f"{task}/{generator}/{repetition}", "task_id": task,
                             "generator": generator, "repetition": repetition, "adjudication": record,
                             "canonical_duplicate_across_new_slots": record["canonical_ast"] is not None and ast_id in seen,
                             "candidate_key_id": key_id, "baseline_key_id": baseline_id,
                             "selected_key_id": key_id if record["selected_new"] else baseline_id,
                             "candidate_outcome_source": "not_assessed" if key_id is None else keys[key_id]["provenance"]["kind"],
                             **scores})
                seen.add(ast_id)
    report = explorer.saved._sealed({"schema": "astra-revision-result-v1", "study": core.STUDY,
        "status": "COMPLETE_MATCHED_PREFIX_DEVELOPMENT", "population": {"states": 10, "new_slots": 200},
        "call_accounting": {"hosted_calls": 80, "new_future_calls": 12, "reused_future_keys": 10},
        "rows": rows, "keys": list(keys.values()), "analysis": core.analyze(rows),
        "duplicate_and_cache_counts": {}, "provider_usage": {}, "limits": ["SYNTHETIC presentation fixture."]})
    raw = (json.dumps(report, ensure_ascii=True, sort_keys=True) + "\n").encode()
    identity = hashlib.sha256(raw).hexdigest()
    return {"schema": "astra-revision-explorer-payload-v1", "report_json": raw.decode(),
            "report_sha256": identity, "report_bytes": len(raw), "contexts": contexts,
            "renderer_sha256": "f" * 64, "captured_execution_file_count": 0,
            "verification": {"status": "SAVED_REVISION_VERIFIED", "report_sha256": identity,
                             "contract_sha256": "a" * 64, "submissions_sha256": "b" * 64}}


@pytest.fixture
def captured_tree(tmp_path, monkeypatch):
    payload = synthetic_payload()
    root = tmp_path / "synthetic"
    execution = root / study.PUBLIC_DIRECTORY / "execution"
    execution.mkdir(parents=True)
    for name in ("batches", "setup-commands", "assessment-jobs"):
        (execution / name).mkdir()
    report = root / study.RESULT_PATH
    report.parent.mkdir()
    report.write_bytes(payload["report_json"].encode())
    (execution / "COMPLETE.json").write_bytes(report.read_bytes())
    contract = {"states": {task: state(task) for task in core.TASK_IDS}}
    bound = {study.PUBLIC_DIRECTORY + "/contract.json": json.dumps(contract).encode(),
             "synthetic-public-source.txt": b"SYNTHETIC source binding"}
    for relative, content in bound.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    monkeypatch.setattr(study, "_verified_contract", lambda actual: (contract, {}, {}, dict(bound)))
    monkeypatch.setattr(study, "_verified_submissions", lambda actual, *_: ({}, dict(bound)))
    monkeypatch.setattr(study, "_load_task", lambda *_: pytest.fail("renderer cannot load tasks"))
    monkeypatch.setattr(explorer.saved, "_versions", lambda: pytest.fail("renderer cannot require scoring runtime"))
    monkeypatch.setattr(explorer.saved, "_data_bytes", lambda *_: pytest.fail("renderer cannot read market data"))
    return root, report, execution, bound, payload


def test_verifier_reads_immutable_snapshot_and_exact_verified_bytes_are_embedded(captured_tree, monkeypatch):
    root, report, execution, bound, payload = captured_tree
    raw = report.read_bytes()
    called = []

    def verifier(*, source_root, report_path):
        called.append(source_root)
        assert source_root != root and report_path != report
        assert report_path.read_bytes() == raw
        assert (source_root / study.PUBLIC_DIRECTORY / "execution/COMPLETE.json").read_bytes() == raw
        assert (source_root / study.PUBLIC_DIRECTORY / "execution/assessment-jobs").is_dir()
        assert all((source_root / path).read_bytes() == value for path, value in bound.items())
        report.write_bytes(b"changed original after capture")
        (execution / "COMPLETE.json").write_bytes(b"changed original retained report")
        return payload["verification"]

    monkeypatch.setattr(study, "replay_revision_study", verifier)
    built = explorer.build_payload(source_root=root)
    assert len(called) == 1 and built["report_json"].encode() == raw
    assert built["captured_execution_file_count"] == 1
    parsed = Scripts()
    parsed.feed(explorer.render(built))
    assert [item["id"] for item in parsed.blocks] == ["revision-data", None]
    assert json.loads(parsed.blocks[0]["text"])["report_json"].encode() == raw


@pytest.mark.parametrize("failure", ["missing-completion", "active-lock", "replay-rejected", "wrong-verified-hash"])
def test_no_output_for_incomplete_or_unverified_evidence(captured_tree, monkeypatch, failure):
    root, _, execution, _, payload = captured_tree
    if failure == "missing-completion":
        (execution / "COMPLETE.json").unlink()
    if failure == "active-lock":
        (execution / ".execution-lock").mkdir()

    def verifier(**kwargs):
        if failure == "replay-rejected":
            raise ValueError("synthetic replay rejection")
        return {**payload["verification"], "report_sha256": "0" * 64}

    monkeypatch.setattr(study, "replay_revision_study", verifier)
    output = root / "never.html"
    with pytest.raises(ValueError):
        explorer.main(["--source-root", str(root), "--output", str(output)])
    assert not output.exists()


NODE_DOM = r"""
const fs=require('fs'),vm=require('vm'),input=JSON.parse(fs.readFileSync(0,'utf8'));
class Element{constructor(tag){this.tag=tag;this.children=[];this.textContent='';this.value='';this.listeners={};}
 appendChild(node){this.children.push(node);if(this.tag==='select'&&!this.value)this.value=node.value;return node;}
 replaceChildren(...nodes){this.children=[];for(const node of nodes)this.appendChild(node);}
 addEventListener(name,callback){this.listeners[name]=callback;}}
const elements=new Map(),document={getElementById(id){if(!elements.has(id))elements.set(id,new Element(['task','generator'].includes(id)?'select':'div'));return elements.get(id);},createElement(tag){return new Element(tag);}};
document.getElementById('revision-data').textContent=input.data;
vm.runInNewContext(input.script,{document},{timeout:3000});
const rows=id=>document.getElementById(id).children.map(tr=>tr.children.map(td=>String(td.textContent)));
const cells=[];
for(const task of document.getElementById('task').children)for(const generator of document.getElementById('generator').children){
 document.getElementById('task').value=task.value;document.getElementById('generator').value=generator.value;document.getElementById('task').listeners.change();
 cells.push({task:task.value,generator:generator.value,rows:rows('candidates'),explanations:rows('explanations'),
 evidence:JSON.parse(document.getElementById('candidate-evidence').textContent),
 provenance:JSON.parse(document.getElementById('candidate-provenance').textContent),
 truthful:document.getElementById('truthful-prompt').textContent,masked:document.getElementById('masked-prompt').textContent});}
process.stdout.write(JSON.stringify({cells,summaries:rows('summaries'),contrasts:rows('contrasts'),states:rows('states'),years:rows('years'),allSlots:rows('all-slots'),allocation:rows('allocation'),raw:document.getElementById('raw-report').textContent}));
"""


def execute_script(payload):
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is optional for synthetic DOM coverage")
    parsed = Scripts()
    parsed.feed(explorer.render(payload))
    result = subprocess.run([node, "-e", NODE_DOM], input=json.dumps({"data": parsed.blocks[0]["text"],
                            "script": parsed.blocks[1]["text"]}), capture_output=True, text=True,
                            encoding="utf-8", check=True, timeout=15, shell=False)
    return json.loads(result.stdout)


def test_all_fifty_cells_and_two_hundred_slots_keep_penalties_selection_and_prompt_context():
    payload = synthetic_payload()
    actual = execute_script(payload)
    assert len(actual["cells"]) == len(actual["states"]) == 50
    assert len(actual["allSlots"]) == 200 and len(actual["years"]) == 25
    assert len(actual["summaries"]) == 5 and all(row[1] == "40" for row in actual["summaries"])
    assert len(actual["contrasts"]) == 4 and len(actual["allocation"]) == 13
    assert actual["raw"] == payload["report_json"]
    seen, failures = set(), set()
    for cell in actual["cells"]:
        assert len(cell["rows"]) == len(cell["evidence"]) == 4
        assert cell["truthful"] == payload["contexts"][cell["task"]]["prompts"]["truthful"]["text"]
        assert cell["masked"] == payload["contexts"][cell["task"]]["prompts"]["masked"]["text"]
        for row, saved_row in zip(cell["rows"], cell["evidence"], strict=True):
            seen.add(saved_row["slot_id"])
            assert float(row[10]) == saved_row["candidate_Q"] and float(row[12]) == saved_row["G"]
            assert row[8] == ("New candidate (attempt 3)" if saved_row["adjudication"]["selected_new"]
                              else "Prefix attempt " + str(saved_row["adjudication"]["selection"]["attempt"]))
            if not saved_row["candidate_valid"]:
                assert row[10] == "-1"
                failures.add(row[9])
        expected_keys = {row[name] for row in cell["evidence"] for name in (
            "candidate_key_id", "baseline_key_id", "selected_key_id") if row[name] is not None}
        assert {value["key"]["key_id"] for value in cell["provenance"]} == expected_keys
    assert len(seen) == 200 and len(failures) >= 3
    assert all(len(row[5].splitlines()) == 4 for row in actual["states"])


def test_hostile_explanations_surrogates_and_long_previews_remain_inert_and_lossless():
    payload = synthetic_payload()
    report = json.loads(payload["report_json"])
    hostile = '</ScRiPt><script>alert(1)</script><img src=x onerror=alert(1)>\ud800&\u2028\u2029'
    report["rows"][0]["adjudication"]["packet"]["hypothesis"] = hostile
    report["rows"][0]["adjudication"]["packet"]["revision"] = "😀" * 281
    report.pop("body_sha256")
    payload["report_json"] = json.dumps(explorer.saved._sealed(report), ensure_ascii=True)
    payload["report_bytes"] = len(payload["report_json"].encode())
    payload["report_sha256"] = hashlib.sha256(payload["report_json"].encode()).hexdigest()
    payload["verification"]["report_sha256"] = payload["report_sha256"]
    parsed = Scripts()
    html = explorer.render(payload)
    assert explorer.render(payload) == html
    html.encode("utf-8")
    parsed.feed(html)
    assert [item["id"] for item in parsed.blocks] == ["revision-data", None]
    assert "innerHTML" not in parsed.blocks[1]["text"] and "fetch(" not in parsed.blocks[1]["text"]
    assert json.loads(parsed.blocks[0]["text"])["report_json"] == payload["report_json"]
    actual = execute_script(payload)
    assert actual["cells"][0]["explanations"][0][1] == hostile
    assert actual["cells"][0]["explanations"][0][2] == "😀" * 280 + " [truncated; full text below]"


@pytest.mark.parametrize("target", ["verification", "report", "prompt"])
def test_payload_identity_tampering_fails_closed(target):
    payload = copy.deepcopy(synthetic_payload())
    if target == "verification":
        payload["verification"]["status"] = "NOT_VERIFIED"
    elif target == "report":
        payload["report_json"] += " "
    else:
        payload["contexts"]["2020-H1"]["prompts"]["truthful"]["text"] += "changed"
    with pytest.raises(ValueError):
        explorer.render(payload)


def test_cli_refuses_overwrite_and_evidence_collisions_before_validation(tmp_path, monkeypatch):
    monkeypatch.setattr(explorer, "build_payload", lambda **_: pytest.fail("must reject before verification"))
    existing = tmp_path / "kept.html"
    existing.write_text("unchanged", encoding="utf-8")
    for path in (existing, tmp_path / "artifacts/new.html", tmp_path / study.RESULT_PATH,
                 tmp_path / "src/new.html", tmp_path / "tests/new.html",
                 tmp_path / study.TRANSPORT_DIRECTORY / "actor-context/new.html"):
        with pytest.raises(SystemExit):
            explorer.main(["--source-root", str(tmp_path), "--output", str(path)])
    assert existing.read_text(encoding="utf-8") == "unchanged"
    assert "astra_revision_explorer import main" in (
        Path(__file__).resolve().parents[1] / "scripts/render_astra_revision_explorer.py").read_text(encoding="utf-8")
