"""Independent renderer regressions using synthetic evidence and a tiny Node DOM."""

import json
import shutil
import subprocess
from html.parser import HTMLParser

import pytest

from alpha_research_rl import astra_explorer as explorer
from alpha_research_rl.agentic_research import ResearchEpisode


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


def synthetic_files(tmp_path, *, oversized=None):
    # Reuse only the synthetic fixture builders, not any real study submission.
    from test_astra_replay import ROOT, initial, metrics, synthetic, transport, write_fixture

    expected_history = None

    def change_first_episode(_, submissions):
        nonlocal expected_history
        item = submissions["episodes"][0]
        raws = [oversized] + [r["raw_response"] for r in item["submission"]["records"][1:]]
        episode = ResearchEpisode(item["arm"], initial(), lambda expression: {
            **metrics(-0.4 if expression == "neg(returns)" else 0.1), "usable": True,
        })
        summaries = []
        for attempt, raw in enumerate(raws, start=1):
            summaries.append(transport(episode.prompt(), raw, attempt))
            episode.submit(raw)
            if attempt == 1:
                expected_history = episode.observation()["history"]
        item.update(submission=episode.freeze(), transport_summaries=summaries)

    paths = write_fixture(tmp_path, synthetic.__wrapped__(), assess=True,
                          mutate=change_first_episode if oversized is not None else None)
    return paths, ROOT, expected_history


@pytest.mark.parametrize("target", ["submissions", "assessment"])
def test_page_never_embeds_bytes_changed_after_their_verification(tmp_path, monkeypatch, target):
    paths, root, _ = synthetic_files(tmp_path)
    index = 1 if target == "submissions" else 2
    original = json.loads(paths[index].read_text(encoding="utf-8"))
    actual_replay = explorer.replay_study

    def verify_then_change_original(*args, **kwargs):
        verified = actual_replay(*args, **kwargs)
        changed = json.loads(paths[index].read_text(encoding="utf-8"))
        if target == "submissions":
            changed["episodes"].pop()
        else:
            changed["primary_mean_full_minus_validity"] = 999.0
        paths[index].write_text(json.dumps(changed), encoding="utf-8")
        return verified

    monkeypatch.setattr(explorer, "replay_study", verify_then_change_original)
    try:
        payload = explorer.build_payload(paths[0], paths[1], paths[2], source_root=root)
    except ValueError:
        return  # Explicitly rejecting changed input is also safe.
    assert payload[target] == original  # Rendering the verified immutable snapshot is safe.


def test_json_valid_lone_surrogates_remain_writable_utf8_and_inert():
    payload = {"model_text": '\ud800</ScRiPt><script>alert("x")</script>\udfff&\u2028\u2029'}
    rendered = explorer.render(payload)
    rendered.encode("utf-8")  # JSON may contain escaped surrogate code points even when UTF-8 cannot.
    parsed = Scripts()
    parsed.feed(rendered)
    assert [block["id"] for block in parsed.blocks] == ["astra-data", None]
    assert json.loads(parsed.blocks[0]["text"]) == payload


NODE_DOM = r"""
const fs=require('fs'),vm=require('vm'),input=JSON.parse(fs.readFileSync(0,'utf8'));
class Element {
 constructor(tag){this.tag=tag;this.children=[];this.textContent='';this.value='';this.listeners={};}
 appendChild(node){this.children.push(node);if(this.tag==='select'&&!this.value)this.value=node.value;return node;}
 append(...nodes){for(const node of nodes)this.appendChild(node);}
 replaceChildren(...nodes){this.children=[];this.append(...nodes);}
 addEventListener(name,callback){this.listeners[name]=callback;}
}
const elements=new Map(),document={
 getElementById(id){if(!elements.has(id))elements.set(id,new Element(['task','attempt'].includes(id)?'select':'div'));return elements.get(id);},
 createElement(tag){return new Element(tag);}
};
document.getElementById('astra-data').textContent=input.data;
vm.runInNewContext(input.script,{document,console},{timeout:2000});
document.getElementById('attempt').value='2';document.getElementById('attempt').listeners.change();
const card=document.getElementById('arms').children[0];
const history=card.children.find(node=>node.tag==='details'&&node.children[0].textContent==='Permitted history before this proposal');
process.stdout.write(history.children[1].textContent);
"""


@pytest.mark.parametrize("raw", ["x" * 20005, "x" * 19999 + "\U0001f642tail"],
                         ids=["ascii", "unicode-code-point-boundary"])
def test_permitted_history_matches_actual_observation_including_truncation_metadata(tmp_path, raw):
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is needed only to execute the renderer against a minimal test DOM")
    paths, root, expected = synthetic_files(tmp_path, oversized=raw)
    payload = explorer.build_payload(paths[0], paths[1], paths[2], source_root=root)
    parsed = Scripts()
    parsed.feed(explorer.render(payload))
    completed = subprocess.run(
        [node, "-e", NODE_DOM], input=json.dumps({"data": parsed.blocks[0]["text"], "script": parsed.blocks[1]["text"]}),
        text=True, encoding="utf-8", capture_output=True, check=True, timeout=10, shell=False,
    )
    actual = json.loads(completed.stdout)
    assert expected[0]["raw_response_truncated"] is True
    assert len(expected[0]["raw_response"]) == 20000
    assert actual == expected
