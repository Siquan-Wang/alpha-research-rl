"""Archive completeness, byte bindings and safe rendering on artificial traces."""

import copy
import hashlib
import json
import re
import shutil
import subprocess
from html.parser import HTMLParser

import pytest
from test_linkage_analysis import inputs as original_inputs

from alpha_research_rl.financial_analysis import _canonical
from alpha_research_rl.linkage_analysis import CONTROLS, ORIGINALS, ROLES, analyze_linkage
from alpha_research_rl.linkage_explorer import main, prepare_payload, render_html


@pytest.fixture
def archive(tmp_path):
    reports, original_sources = original_inputs.__wrapped__(tmp_path)
    sources = {**original_sources, **{label: {"file": label + ".json",
        "sha256": hashlib.sha256(_canonical(reports[label]).encode()).hexdigest()} for label in CONTROLS}}
    analysis = analyze_linkage(reports, original_sources)
    analysis["source_reports"] = copy.deepcopy(sources)
    return reports, analysis, sources


def test_all_nine_hundred_records_order_signed_pairs_and_unchanged_originals(archive):
    before = copy.deepcopy(archive)
    payload = prepare_payload(*archive)
    assert archive == before
    assert payload["counts"] == {"checkpoints": 5, "tasks": 10, "records": 900,
                                 "original_records": 540, "control_records": 360,
                                 "stochastic_draws_per_task_condition": 8}
    assert payload["checkpoints"] == list(ROLES.values())
    first = payload["records"][0]
    assert (first["checkpoint"], first["task_id"], first["condition"], first["decoding"], first["draw"]) == (
        ORIGINALS[0], "2020-H1", "true", "stochastic", 0)
    assert first["status"] == "invalid" and first["reward"] == -1.01
    for label in ROLES.values():
        records = [record for record in payload["records"] if record["checkpoint"] == label]
        assert len(records) == 180
        assert sum(record["decoding"] == "greedy" for record in records) == 20
    overall = payload["overall"]["metrics"]["stochastic"]
    assert overall["correct_vs_placebo"]["23"]["true"]["reward_delta"] == pytest.approx(.01)
    assert overall["correct_vs_placebo"]["29"]["true"]["reward_delta"] == pytest.approx(-.02)
    assert len(payload["task_rows"]) == 10 and len(payload["year_rows"]) == 5
    for row in [payload["overall"], *payload["task_rows"], *payload["year_rows"]]:
        for decoding in ("stochastic", "greedy"):
            cell = row["metrics"][decoding]
            assert set(cell["policy_vs_sft"]) == set(ROLES.values()) - {ORIGINALS[0]}
            for seed in ("23", "29"):
                delta = cell["correct_vs_placebo"][seed]["true"]
                assert delta["reward_delta"] == pytest.approx(delta["failure_penalty_component_delta"]
                                                            + delta["all_proposal_ic_contribution_delta"])
    original = archive[1]["original_results"]["overall"]["metrics"]["strict"]["stochastic"]
    for label in ORIGINALS:
        assert overall["policies"][label] == original["policies"][label]
    assert payload["integrity"]["original_three_frozen_utc"] < payload["integrity"]["five_checkpoint_frozen_utc"]


@pytest.mark.parametrize("change", ["aggregate", "source_sha", "missing_draw", "wrong_prompt"])
def test_inconsistent_evidence_cannot_be_published(archive, change):
    reports, analysis, sources = archive
    if change == "aggregate":
        analysis["overall"]["metrics"]["strict"]["stochastic"]["correct_vs_placebo"]["29"]["true"]\
            ["reward_delta"] += .1
    elif change == "source_sha":
        sources[CONTROLS[0]]["sha256"] = "0" * 64
    elif change == "missing_draw":
        reports[CONTROLS[0]]["episodes"][0]["records"].pop()
    elif change == "wrong_prompt":
        reports[CONTROLS[1]]["episodes"][0]["records"][0]["prompt_ids"][0] += 1
    with pytest.raises(ValueError):
        prepare_payload(reports, analysis, sources)


def test_decoded_probes_are_actor_evidence_and_whitelist_excludes_private_arrays(archive):
    reports, analysis, sources = archive
    for report in reports.values():
        report["raw_market"] = ["RAW_SENTINEL"]
        report["manifest"]["machine_path"] = "PRIVATE_PATH_SENTINEL"
    observation = {"probe_evidence": [{"expression": expression, "feedback": {"mean_ic": mean},
                     "feedback_usable": True, "windows": []}
                    for expression, mean in (("delay(returns,1)", .777), ("ts_mean(returns,5)", -.222))]}
    text = "<|im_start|>user\n" + json.dumps(observation) + "<|im_end|>"
    calls = []

    def decoder(tokens):
        calls.append(tokens)
        return text

    payload = prepare_payload(reports, analysis, sources, decoder)
    assert len(calls) == len(payload["prompts"]) == 20
    assert payload["prompts"]["2020-H1/true"]["observation"]["probe_evidence"][0]["feedback"]["mean_ic"] == .777
    successful = next(record for record in payload["records"] if record["status"] == "ok")
    assert successful["scorer_feedback"]["mean_ic"] == .1
    encoded = json.dumps(payload)
    for sentinel in ("RAW_SENTINEL", "PRIVATE_PATH_SENTINEL", "prompt_ids", "completion_ids"):
        assert sentinel not in encoded


def test_generated_script_closure_and_prompt_are_inert_exact_text(archive):
    reports, _, sources = archive
    attack = '</script><img src=x onerror="alert(1)">'
    record = reports[ORIGINALS[0]]["episodes"][0]["records"][0]
    record.update(text=attack, action={"action": "invalid"})
    # Bind the changed original artificial bytes honestly in both control registries.
    sources[ORIGINALS[0]]["sha256"] = hashlib.sha256(_canonical(reports[ORIGINALS[0]]).encode()).hexdigest()
    for label in CONTROLS:
        reports[label]["manifest"]["config"]["frozen_suite"]["original_reports"] = {
            label: sources[label] for label in ORIGINALS}
    analysis = analyze_linkage(reports, {label: sources[label] for label in ORIGINALS})
    analysis["source_reports"] = sources
    payload = prepare_payload(reports, analysis, sources, decoder=lambda tokens: attack)
    html = render_html(payload)
    assert attack not in html and "\\u003c/script>" in html
    assert "innerHTML" not in html and "textContent" in html
    embedded = re.search(r'<script id="linkage-data" type="application/json">(.*?)</script>', html, re.DOTALL).group(1)
    assert json.loads(embedded)["records"][0]["text"] == attack
    assert json.loads(embedded)["prompts"]["2020-H1/true"]["exact_prompt"] == attack

    class SecurityParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.scripts = self.external = self.events = 0

        def handle_starttag(self, tag, attrs):
            self.scripts += tag == "script"
            self.external += any(key in {"src", "href"} for key, _ in attrs)
            self.events += any(key.startswith("on") for key, _ in attrs)

    parser = SecurityParser()
    parser.feed(html)
    assert (parser.scripts, parser.external, parser.events) == (2, 0, 0)


def test_cli_reads_actual_bytes_and_refuses_reformatted_original(archive, tmp_path, monkeypatch):
    reports, analysis, sources = archive
    args = ["linkage_explorer"]
    for flag, label in zip(("sft", "rl23", "rl29", "placebo23", "placebo29"), ROLES.values(), strict=True):
        path = tmp_path / sources[label]["file"]
        path.write_text(_canonical(reports[label]), encoding="utf-8")
        args += ["--" + flag, str(path)]
    analysis_path, output = tmp_path / "analysis.json", tmp_path / "explorer.html"
    analysis_path.write_text(json.dumps(analysis), encoding="utf-8")
    args += ["--analysis", str(analysis_path), "--output", str(output)]
    monkeypatch.setattr("sys.argv", args)
    main()
    html = output.read_text(encoding="utf-8")
    embedded = re.search(r'<script id="linkage-data" type="application/json">(.*?)</script>', html, re.DOTALL).group(1)
    payload = json.loads(embedded)
    assert payload["counts"]["records"] == 900
    assert any(source["file"] == "analysis.json" and source["sha256"] == hashlib.sha256(
        analysis_path.read_bytes()).hexdigest() for source in payload["sources"])
    original = tmp_path / sources[ORIGINALS[0]]["file"]
    original.write_text(json.dumps(reports[ORIGINALS[0]], indent=2), encoding="utf-8")
    with pytest.raises(ValueError, match="source report byte identities"):
        main()
    assert output.read_text(encoding="utf-8") == html


def test_actual_selector_handlers_preserve_matched_draw_and_greedy_fallback(archive):
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is required to execute the generated browser script")
    html = render_html(prepare_payload(*archive))
    encoded = re.search(r'<script id="linkage-data" type="application/json">(.*?)</script>', html, re.DOTALL).group(1)
    script = re.search(r'<script>\s*(.*?)</script>', html, re.DOTALL).group(1)
    # Execute the actual page script and its registered change handlers. The
    # small DOM supplies real select defaults and option-clearing behavior.
    harness = r'''
const vm=require('vm'),assert=require('assert'),elements=new Map();
const selects=new Set(['checkpoint','task','condition','decoding','draw']);
class Element{
 constructor(id=''){this.id=id;this.children=[];this.value=id==='condition'?'true':id==='decoding'?'stochastic':'';
  this.textContent='';this.handlers={};this.classList={toggle(){}};}
 appendChild(child){this.children.push(child);if(selects.has(this.id)&&this.children.length===1)this.value=String(child.value);}
 replaceChildren(){this.children=[];if(selects.has(this.id))this.value='';}
 addEventListener(event,handler){this.handlers[event]=handler;}
}
const document={getElementById(id){if(!elements.has(id))elements.set(id,new Element(id));return elements.get(id);},
 createElement(){return new Element();}};
document.getElementById('linkage-data').textContent=INPUT_JSON;
vm.runInNewContext(INPUT_SCRIPT+`
function change(id,value){byId(id).value=value;byId(id).handlers.change();}
function assertTrace(label,task,condition,draw){
 const record=data.records.find(r=>r.checkpoint===label&&r.task_id===task&&r.condition===condition&&r.decoding===byId('decoding').value&&r.draw===draw);
 assert.strictEqual(byId('draw').value,String(draw));
 assert.strictEqual(byId('generated').textContent,record.text);
 assert.strictEqual(byId('reward').textContent,fmt(record.reward));
 assert.strictEqual(byId('feedback').textContent,pretty(record.scorer_feedback));
 assert(byId('traceTitle').textContent.includes('RNG seed '+record.seed));
}
change('checkpoint',data.roles.placebo_seed29);change('task','2023-H1');change('draw','7');
assertTrace(data.roles.placebo_seed29,'2023-H1','true',7);
change('condition','exchanged');assertTrace(data.roles.placebo_seed29,'2023-H1','exchanged',7);
change('condition','true');assertTrace(data.roles.placebo_seed29,'2023-H1','true',7);
change('task','2024-H2');assertTrace(data.roles.placebo_seed29,'2024-H2','true',7);
change('checkpoint',data.roles.rl_seed23);assertTrace(data.roles.rl_seed23,'2024-H2','true',7);
change('decoding','greedy');assertTrace(data.roles.rl_seed23,'2024-H2','true',0);
change('decoding','stochastic');assertTrace(data.roles.rl_seed23,'2024-H2','true',0);
`,{document,assert});
'''
    harness = "const INPUT_JSON=" + json.dumps(encoded) + ";const INPUT_SCRIPT=" + json.dumps(script) + ";" + harness
    result = subprocess.run([node, "-"], input=harness, text=True, capture_output=True, timeout=15, check=False)
    assert result.returncode == 0, result.stderr
