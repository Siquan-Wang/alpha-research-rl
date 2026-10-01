"""Offline exhibit of saved synthetic pilot actions and verified reconstruction."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from . import trajectory_replay

SCRIPT = [{"action": "propose", "expression": "delta(log(volume),1)"},
          *[{"action": "screen", "candidate": identifier} for identifier in (3, 0, 1, 2)],
          {"action": "select", "candidate": 0}, {"action": "stop"}]


def prepare_payload(reports, sources):
    """Publish only verified reconstruction, preserving the saved/replayed distinction."""
    replay = trajectory_replay.replay_reports(reports, sources)
    provenance = replay["provenance"]
    if (replay.get("verified") is not True or provenance.get("reconstruction") is not True
            or provenance.get("original_actor_prompt_authenticated") is not False):
        raise ValueError("Replay is not verified or reconstruction provenance is missing")
    actors = ["sft", "rloo", "base"]
    episodes, tasks = [], {}
    for episode in sorted(replay["episodes"], key=lambda item: (actors.index(item["label"]), item["seed"])):
        label = episode["label"]
        task_id = f"seed-{episode['seed']}"
        tasks[task_id] = {"task_id": task_id, "seed": episode["seed"], "regime": episode["regime"]}
        terminal = episode["terminal"]
        if label != "base" and ([step["saved"]["action"] for step in episode["steps"]] != SCRIPT
                                or terminal["selected"] != [0]):
            raise ValueError("Saved SFT/RL behavior does not support the stated seven-step-script finding")
        steps = []
        for step in episode["steps"]:
            saved = step["saved"]
            steps.append({
                "step": step["index"], "text": saved["text"], "action": saved["action"],
                "terminated": saved["terminated"], "status": step["status"], "reason": step["reason"],
                "cost": step["cost"], "budget_before": step["before"]["environment"]["budget"],
                "budget_after": step["after"]["environment"]["budget"],
                "observation_before": step["before"]["environment"],
                "observation_after": step["after"]["environment"],
                "compact_observation_before": step["before"]["actor_visible"],
            })
        episodes.append({"actor": label, "task_id": task_id, "seed": episode["seed"],
                         "regime": episode["regime"], "steps": steps,
                         "terminal_reward": terminal["reward"], "spent_budget": terminal["spent_budget"],
                         "selected": terminal["selected"]})
    if len(episodes) != 18 or len(tasks) != 6:
        raise ValueError("The exhibit requires all 18 episodes and six synthetic tasks")
    for seed in (task["seed"] for task in tasks.values()):
        pair = [next(episode for episode in episodes if episode["seed"] == seed and episode["actor"] == label)
                for label in ("sft", "rloo")]
        if any(pair[0][key] != pair[1][key] for key in ("terminal_reward", "spent_budget", "selected")):
            raise ValueError("Saved pilot outcomes do not support the stated lack of incremental RL benefit")
    return {
        "schema": "offline-synthetic-trajectory-v1", "actors": actors,
        "tasks": [tasks[key] for key in sorted(tasks)], "episodes": episodes,
        "counts": {"actors": 3, "tasks": 6, "episodes": 18,
                   "steps": sum(len(episode["steps"]) for episode in episodes)},
        "sources": [{"file": source["file"], "sha256": source["sha256"]} for source in sources.values()],
        "provenance": {"initial_budget": trajectory_replay.REPLAY_CONFIG["budget"], "replay": provenance,
                       "reconstructed_observations": True, "historical_prompt_authenticated": False,
                       "environment_config": replay["episodes"][0]["environment_config"],
                       "split": replay["episodes"][0]["split"]},
    }


def render_html(payload):
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c")
    return HTML.replace("__TRAJECTORY_JSON__", encoded)


HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AlphaResearch-RL · Synthetic trajectory pilot</title><style>
:root{color-scheme:light;--ink:#172c3c;--muted:#5b6c78;--line:#dbe3e8;--blue:#215c8d;--bg:#f2f5f7}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1200px;margin:auto;padding:34px 28px 64px}h1{font-size:clamp(28px,4vw,42px);line-height:1.15;letter-spacing:-1px;margin:12px 0}
h2{font-size:22px;margin:0 0 12px}h3{font-size:16px;margin:14px 0 8px}p{margin:8px 0}.eyebrow{color:var(--blue);font-size:12px;font-weight:750;letter-spacing:1.5px;text-transform:uppercase}
.lede{max-width:980px;color:var(--muted);font-size:17px}.chips{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0}.chip{padding:5px 11px;border:1px solid var(--line);border-radius:20px;background:white;font-size:12px}
.card{background:white;border:1px solid var(--line);border-radius:14px;padding:22px;margin:18px 0}.note{color:var(--muted);font-size:13px}
.callout{border-left:3px solid var(--blue);padding:10px 14px;background:#f3f8fc;margin:14px 0}.terminal{border:2px solid #8b72aa;background:#fbf8ff}.terminal b{font-size:28px;color:#674783}
.controls{display:grid;grid-template-columns:1fr 1.6fr 1.4fr;gap:12px;margin:16px 0}label{display:block;font-size:12px;font-weight:650;color:var(--muted)}
select{display:block;width:100%;margin-top:6px;background:white;border:1px solid #b9c8d3;border-radius:7px;padding:10px;color:var(--ink);font:inherit;font-size:14px}
select:focus,button:focus{outline:2px solid #8bc0e5;outline-offset:1px}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px}
th,td{text-align:right;padding:10px 12px;border-bottom:1px solid var(--line);white-space:nowrap}th:first-child,td:first-child{text-align:left}th{color:var(--muted);background:#f6f8fa;font-weight:600}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.subcard{border:1px solid var(--line);border-radius:10px;padding:16px;min-width:0}
.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:14px 0}.metric{background:#f5f8fa;border-radius:8px;padding:12px}.metric b{display:block;font-size:20px;margin-top:4px;font-variant-numeric:tabular-nums}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f6f8fa;border:1px solid var(--line);padding:14px;border-radius:8px;font:12px/1.6 ui-monospace,Consolas,monospace;max-height:400px;overflow:auto}
code{font-family:ui-monospace,Consolas,monospace;overflow-wrap:anywhere}.status{display:inline-block;padding:3px 10px;border-radius:20px;background:#e9f3ef;color:#24796a;font-weight:700;font-size:12px}.status.bad{background:#fbedea;color:#a34235}
button{font:inherit;color:var(--ink);cursor:pointer;border:1px solid var(--line);border-radius:8px;background:white;padding:8px 12px;text-align:left;width:100%}button[aria-current="step"]{border:2px solid var(--blue);background:#eef6fc}
.timeline{display:grid;gap:8px;margin:16px 0}button small{display:block;color:var(--muted)}details{margin-top:16px}summary{cursor:pointer;font-weight:650}.hashes{display:grid;gap:10px;font-size:12px}.hashes code{display:block;color:var(--muted)}.footer{font-size:12px;color:var(--muted)}
@media(max-width:850px){main{padding:24px 16px 40px}.grid{grid-template-columns:1fr}.card{padding:17px}}
@media(max-width:600px){.controls,.metrics{grid-template-columns:1fr;gap:10px}}
</style></head><body><main>
<header><div class="eyebrow">AlphaResearch-RL · Synthetic development pilot</div><h1>A sequential interface, a repeated script.</h1>
<p class="lede">Inspect the saved greedy behavior of base, SFT and SFT + RLOO actors on six synthetic tasks. SFT and RL followed the same seven-step script on every task and selected initial candidate 0. This pilot shows no incremental RL benefit or adaptive financial research.</p><div class="chips" id="chips"></div></header>
<section class="card"><h2>Recorded actions, reconstructed context</h2><div class="callout">The original reports saved generated text and effective actions, but no prompt tokens or observations. The state and compact actor-input panels below are reconstructed by CPU replay under the pinned environment. They are not authenticated historical prompts or recovered model reasoning.</div>
<p>The tasks are deliberately synthetic signal, null and decay generators. Rewards are later synthetic rank IC minus research cost, not market returns or financial alpha. This is a development pilot, not an untouched final test.</p>
<div class="scroll"><table><thead><tr><th>Actor</th><th>Tasks</th><th>Mean terminal reward</th><th>Invalid actions</th><th>Action count</th></tr></thead><tbody id="summary"></tbody></table></div>
<p class="note">Base emits JSON inside Markdown fences, rejected by the original strict parser. Its failures remain in this exhibit. The base/SFT gap is partly an interface confound.</p></section>
<section class="card"><h2>Every saved episode and step</h2><p class="note">Default: SFT, first ordered task, step zero. All 18 episodes are accessible. Switching actor or task preserves the step if available.</p>
<div class="controls"><label>Actor<select id="actor" aria-label="Actor"></select></label><label>Synthetic task<select id="task" aria-label="Synthetic task"></select></label><label>Recorded step<select id="step" aria-label="Recorded step"></select></label></div>
<p class="note" id="stepTitle"></p><p><span class="status" id="status"></span> <span class="note" id="reason"></span></p>
<div class="metrics"><div class="metric"><span class="note">Action budget cost</span><b id="cost"></b></div><div class="metric"><span class="note">Budget before → after</span><b id="budget"></b></div><div class="metric"><span class="note">Selected after this action</span><b id="selected"></b></div></div>
<div class="grid"><div class="subcard"><h3>Saved generated text · verbatim</h3><pre id="generated"></pre></div><div class="subcard"><h3>Saved effective action</h3><pre id="action"></pre><p class="note" id="termination"></p></div></div>
<h3>Reconstructed input before this action</h3><div class="subcard"><p class="note">Compact actor observation from replay. No historical token IDs were saved, so this is not the exact original serialized prompt.</p><pre id="compact"></pre><details><summary>Full reconstructed environment observation before the action</summary><pre id="before"></pre></details></div>
<details><summary>Reconstructed environment state after the action</summary><pre id="after"></pre></details>
<h3>Episode timeline · select any step</h3><div class="timeline" id="timeline"></div>
<div class="card terminal"><h3>Saved terminal assessment reward · separate from actor evidence</h3><b id="terminalReward"></b><p class="note" id="terminalDetails"></p><p class="note">This final outcome is shown to the reader for context. It is not an observation the actor received before its decisions. Replay must match the saved reward, selected IDs, spent budget and statuses.</p></div></section>
<section class="card"><h2>All 18 episodes</h2><div class="scroll"><table><thead><tr><th>Actor / synthetic task</th><th>Saved terminal reward</th><th>Spent budget</th><th>Selected IDs</th><th>Steps</th></tr></thead><tbody id="episodes"></tbody></table></div></section>
<section class="card"><h2>Saved identities and replay provenance</h2><p class="note">CPU replay verifies the recorded actions against a deterministic synthetic environment. No model loads, generation or real-market scoring occur. A mismatch prevents building this exhibit. Matching replay does not authenticate missing historical observations, prompt tokens or checkpoint weights.</p><div class="hashes" id="hashes"></div><details><summary>Environment, reconstruction and validation provenance</summary><pre id="provenance"></pre></details><details><summary>Rebuild this artifact</summary><pre id="command"></pre></details></section>
<p class="footer">Synthetic data throughout · self-contained HTML · no remote scripts, fonts, APIs or model access. Generated text is rendered as text.</p>
</main><script id="trajectory-data" type="application/json">__TRAJECTORY_JSON__</script><script>
'use strict';
const data=JSON.parse(document.getElementById('trajectory-data').textContent),byId=id=>document.getElementById(id);
const put=(id,value)=>{byId(id).textContent=value;},clear=id=>byId(id).replaceChildren(),pretty=value=>JSON.stringify(value,null,2),fmt=value=>Number(value).toFixed(6);
const names={sft:'SFT',rloo:'SFT + RLOO',base:'Base · strict parser'};
function option(id,value,text){const item=document.createElement('option');item.value=value;item.textContent=text;byId(id).appendChild(item);}
function row(id,values){const tr=document.createElement('tr');for(const value of values){const td=document.createElement('td');td.textContent=value;tr.appendChild(td);}byId(id).appendChild(tr);}
for(const actor of data.actors)option('actor',actor,names[actor]);for(const task of data.tasks)option('task',task.task_id,task.task_id+' · '+task.regime);
for(const text of ['Synthetic only','3 actors · 6 tasks · 18 episodes','SFT = RL seven-step script','Reconstructed observations','No authenticated historical prompts']){const chip=document.createElement('span');chip.className='chip';chip.textContent=text;byId('chips').appendChild(chip);}
for(const actor of data.actors){const episodes=data.episodes.filter(e=>e.actor===actor);row('summary',[names[actor],episodes.length,fmt(episodes.reduce((sum,e)=>sum+e.terminal_reward,0)/episodes.length),episodes.reduce((sum,e)=>sum+e.steps.filter(s=>s.status!=='ok').length,0),episodes.reduce((sum,e)=>sum+e.steps.length,0)]);}
for(const episode of data.episodes)row('episodes',[names[episode.actor]+' / '+episode.task_id+' · '+episode.regime,fmt(episode.terminal_reward),episode.spent_budget,pretty(episode.selected),episode.steps.length]);
function episode(){return data.episodes.find(e=>e.actor===byId('actor').value&&e.task_id===byId('task').value);}
function updateSteps(){const previous=byId('step').value;clear('step');for(const step of episode().steps)option('step',step.step,step.step+' · '+step.action.action);if(episode().steps.some(step=>String(step.step)===previous))byId('step').value=previous;update();}
function update(){
 const current=episode(),step=current.steps.find(s=>s.step===Number(byId('step').value));
 put('stepTitle',names[current.actor]+' · '+current.task_id+' · '+current.regime+' synthetic regime · step '+step.step);
 put('status',step.status);byId('status').classList.toggle('bad',step.status!=='ok');put('reason',step.reason||'');put('cost',step.cost);put('budget',step.budget_before+' → '+step.budget_after);put('selected',pretty(step.observation_after.selected));
 put('generated',step.text);put('action',pretty(step.action));put('termination',step.terminated?'Saved report marks EOS termination; original completion tokens were not retained.':'Saved report marks no EOS termination; original completion tokens were not retained.');
 put('compact',pretty(step.compact_observation_before));put('before',pretty(step.observation_before));put('after',pretty(step.observation_after));
 clear('timeline');for(const item of current.steps){const button=document.createElement('button');button.type='button';button.setAttribute('aria-current',item.step===step.step?'step':'false');button.textContent='Step '+item.step+' · '+item.action.action;const details=document.createElement('small');details.textContent='Cost '+item.cost+' · budget '+item.budget_before+' → '+item.budget_after+' · '+item.status;button.appendChild(details);button.addEventListener('click',()=>{byId('step').value=String(item.step);update();});byId('timeline').appendChild(button);}
 put('terminalReward',fmt(current.terminal_reward));put('terminalDetails','Selected '+pretty(current.selected)+' · spent '+current.spent_budget+' / '+data.provenance.initial_budget+' budget units · '+current.steps.length+' recorded actions.');
}
byId('actor').addEventListener('change',updateSteps);byId('task').addEventListener('change',updateSteps);byId('step').addEventListener('change',update);updateSteps();
for(const source of data.sources){const line=document.createElement('div'),label=document.createElement('strong'),hash=document.createElement('code');label.textContent=source.file;hash.textContent='SHA256 '+source.sha256;line.appendChild(label);line.appendChild(hash);byId('hashes').appendChild(line);}
put('provenance',pretty(data.provenance));put('command',data.rebuild_command||'Run python -m alpha_research_rl.trajectory_explorer --help.');
</script></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for label in ("base", "sft", "rloo"):
        parser.add_argument("--" + label, type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() in {getattr(args, label).resolve() for label in ("base", "sft", "rloo")}:
        parser.error("output must not overwrite any saved input report")
    reports, sources = {}, {}
    for label in ("base", "sft", "rloo"):
        path = getattr(args, label)
        raw = path.read_bytes()
        reports[label] = json.loads(raw)
        sources[label] = {"file": path.name, "sha256": hashlib.sha256(raw).hexdigest()}
    payload = prepare_payload(reports, sources)
    for path in (Path(__file__), Path(trajectory_replay.__file__)):
        payload["sources"].append({"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    command = ["python -m alpha_research_rl.trajectory_explorer"]
    for label in ("base", "sft", "rloo", "output"):
        path = getattr(args, label)
        try:
            value = path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except ValueError:
            value = path.name
        command.append(f"  --{label} {value}")
    payload["rebuild_command"] = " \\\n".join(command)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(payload), encoding="utf-8")
    print(json.dumps({"output_file": args.output.name, **payload["counts"]}))


if __name__ == "__main__":
    main()
