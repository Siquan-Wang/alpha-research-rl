"""Public-pilot replay integration and strict recorded/reconstructed separation."""

import copy
import hashlib
import json
import re
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path

import pytest

from alpha_research_rl import trajectory_explorer
from alpha_research_rl.trajectory_explorer import SCRIPT, prepare_payload, render_html


@pytest.fixture(scope="module")
def inputs():
    root = Path(__file__).resolve().parents[1]
    reports, sources = {}, {}
    for actor in ("base", "sft", "rloo"):
        path = root / f"artifacts/development/{actor}-v1.json"
        raw = path.read_bytes()
        reports[actor] = json.loads(raw)
        sources[actor] = {"file": path.name, "sha256": hashlib.sha256(raw).hexdigest()}
    return reports, sources


@pytest.fixture(scope="module")
def verified_payload(inputs):
    return prepare_payload(*inputs)


def test_real_saved_archive_keeps_all_episodes_base_failures_and_script(verified_payload, inputs):
    payload = verified_payload
    assert payload["counts"] == {"actors": 3, "tasks": 6, "episodes": 18, "steps": 144}
    assert payload["actors"] == ["sft", "rloo", "base"]
    assert payload["episodes"][0]["actor"] == "sft" and payload["episodes"][0]["seed"] == 11000
    base = [episode for episode in payload["episodes"] if episode["actor"] == "base"]
    assert sum(len(episode["steps"]) for episode in base) == 60
    assert all(step["status"] == "invalid" and step["cost"] == 1 for episode in base for step in episode["steps"])
    assert all(episode["terminal_reward"] == -.01 and episode["spent_budget"] == 10 for episode in base)
    for episode in payload["episodes"]:
        original = next(row for row in inputs[0][episode["actor"]]["episodes"] if row["seed"] == episode["seed"])
        assert episode["terminal_reward"] == original["reward"]
        assert [step["text"] for step in episode["steps"]] == [action["text"] for action in original["actions"]]
        assert sum(step["cost"] for step in episode["steps"]) == episode["spent_budget"]
        if episode["actor"] != "base":
            assert [step["action"] for step in episode["steps"]] == SCRIPT
            assert episode["selected"] == [0]
            assert [step["cost"] for step in episode["steps"]] == [2, 1, 1, 1, 1, 1, 0]


def test_reconstructed_observations_are_causal_and_never_historical_prompts(verified_payload):
    assert verified_payload["provenance"]["historical_prompt_authenticated"] is False
    assert verified_payload["provenance"]["reconstructed_observations"] is True
    first = verified_payload["episodes"][0]["steps"][0]
    assert first["observation_before"]["budget"] == 10 and first["budget_after"] == 8
    assert len(first["observation_before"]["candidates"]) == 3
    assert len(first["observation_after"]["candidates"]) == 4
    for episode in verified_payload["episodes"]:
        for step in episode["steps"]:
            compact = step["compact_observation_before"]
            assert not any(key in compact for key in ("done", "history", "seed", "regime", "reward", "terminal_reward",
                                                      "assessment", "prompt_ids", "completion_ids"))
            assert "recent_actions" in compact
    html = render_html(verified_payload)
    assert "not authenticated historical prompts" in html
    assert "Saved terminal assessment reward" in html and "Synthetic data throughout" in html


def test_unverified_or_authenticated_prompt_claim_blocks_exhibit(inputs, monkeypatch):
    for provenance, verified in (({"reconstruction": True, "original_actor_prompt_authenticated": False}, False),
                                 ({"reconstruction": True, "original_actor_prompt_authenticated": True}, True)):
        monkeypatch.setattr(trajectory_explorer.trajectory_replay, "replay_reports",
                            lambda reports, sources, provenance=provenance, verified=verified:
                            {"provenance": provenance, "verified": verified})
        with pytest.raises(ValueError, match="not verified"):
            prepare_payload(*inputs)


def test_modified_saved_reward_cannot_be_replayed_as_original(inputs):
    reports, sources = copy.deepcopy(inputs)
    reports["sft"]["episodes"][0]["reward"] += .1
    with pytest.raises(ValueError):
        prepare_payload(reports, sources)


@pytest.mark.parametrize("collision", ["base", "sft", "rloo"])
def test_cli_output_collision_preserves_all_saved_inputs(tmp_path, monkeypatch, collision):
    paths = {actor: tmp_path / f"{actor}.json" for actor in ("base", "sft", "rloo")}
    original = {actor: json.dumps({"saved_evidence": actor}).encode() for actor in paths}
    args = ["trajectory_explorer"]
    for actor, path in paths.items():
        path.write_bytes(original[actor])
        args += ["--" + actor, str(path)]
    # An equivalent path containing '..' must be detected after resolution.
    alias = tmp_path / "unused" / ".." / paths[collision].name
    args += ["--output", str(alias)]
    monkeypatch.setattr("sys.argv", args)
    with pytest.raises(SystemExit) as error:
        trajectory_explorer.main()
    assert error.value.code == 2
    assert {actor: path.read_bytes() for actor, path in paths.items()} == original


def test_generated_script_closure_stays_inert_exact_text(verified_payload):
    payload = copy.deepcopy(verified_payload)
    attack = '</script><img src=x onerror="alert(1)">'
    payload["episodes"][0]["steps"][0]["text"] = attack
    html = render_html(payload)
    assert attack not in html and "\\u003c/script>" in html and "innerHTML" not in html
    embedded = re.search(r'<script id="trajectory-data" type="application/json">(.*?)</script>', html, re.DOTALL).group(1)
    assert json.loads(embedded)["episodes"][0]["steps"][0]["text"] == attack

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


def test_actual_step_handlers_and_timeline_render_all_144_actions(verified_payload):
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is required to execute the generated browser script")
    html = render_html(verified_payload)
    encoded = re.search(r'<script id="trajectory-data" type="application/json">(.*?)</script>', html, re.DOTALL).group(1)
    script = re.search(r'<script>\s*(.*?)</script>', html, re.DOTALL).group(1)
    harness = r'''
const vm=require('vm'),assert=require('assert'),elements=new Map(),selects=new Set(['actor','task','step']);
class Element{
 constructor(id=''){this.id=id;this.children=[];this.value='';this.textContent='';this.handlers={};this.classList={toggle(){}};}
 appendChild(child){this.children.push(child);if(selects.has(this.id)&&this.children.length===1)this.value=String(child.value);}
 replaceChildren(){this.children=[];if(selects.has(this.id))this.value='';}
 addEventListener(event,handler){this.handlers[event]=handler;}
 setAttribute(){}
}
const document={getElementById(id){if(!elements.has(id))elements.set(id,new Element(id));return elements.get(id);},
 createElement(){return new Element();}};
document.getElementById('trajectory-data').textContent=INPUT_JSON;
vm.runInNewContext(INPUT_SCRIPT+`
assert.strictEqual(byId('actor').value,'sft');assert.strictEqual(byId('step').value,'0');
for(const episode of data.episodes){
 byId('actor').value=episode.actor;byId('actor').handlers.change();
 byId('task').value=episode.task_id;byId('task').handlers.change();
 for(const step of episode.steps){
  byId('step').value=String(step.step);byId('step').handlers.change();
  assert.strictEqual(byId('generated').textContent,step.text);
  assert.strictEqual(byId('action').textContent,pretty(step.action));
  assert.strictEqual(byId('budget').textContent,step.budget_before+' → '+step.budget_after);
  assert.strictEqual(byId('terminalReward').textContent,fmt(episode.terminal_reward));
 }
 assert.strictEqual(byId('timeline').children.length,episode.steps.length);
 byId('timeline').children[0].handlers.click();assert.strictEqual(byId('step').value,'0');
}
assert.strictEqual(byId('episodes').children.length,18);
`,{document,assert});
'''
    program = "const INPUT_JSON=" + json.dumps(encoded) + ";const INPUT_SCRIPT=" + json.dumps(script) + ";" + harness
    result = subprocess.run([node, "-"], input=program, text=True, encoding="utf-8",
                            capture_output=True, timeout=15, check=False)
    assert result.returncode == 0, result.stderr
