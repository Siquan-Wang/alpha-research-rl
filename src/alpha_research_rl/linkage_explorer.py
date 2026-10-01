"""Build a separate offline explorer of all five-policy reward-linkage traces.

Reads saved reports only. Optional decoding verifies a cached tokenizer and
loads no model, raw market series or remote resources.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from . import evidence_explorer
from .evidence_explorer import _actor_observation, _metrics, local_prompt_decoder
from .linkage_analysis import ORIGINALS, ROLES, analyze_linkage


def _unit(row):
    return {"n_tasks": row["n_tasks"], "metrics": row["metrics"]["strict"], "references": row["references"]}


def prepare_payload(reports, analysis, report_sources, decoder=None):
    """Require exact five-report bindings and recompute every saved aggregate."""
    labels = list(ROLES.values())
    if set(report_sources) != set(labels) or analysis.get("source_reports") != report_sources:
        raise ValueError("saved analysis source report byte identities differ")
    recomputed = analyze_linkage(reports, {label: report_sources[label] for label in ORIGINALS})
    for key, value in recomputed.items():
        if analysis.get(key) != value:
            raise ValueError(f"saved linkage analysis differs from retained outcomes: {key}")
    records, prompts, tasks = [], {}, {}
    for label in labels:
        for episode in sorted(reports[label]["episodes"], key=lambda item: (item["task"]["year"],
                                                                          item["task"]["half"])):
            task = episode["task"]
            task_id = task["task_id"]
            tasks[task_id] = {key: task[key] for key in ("task_id", "year", "half", "feedback_signal_dates",
                                                        "assessment_signal_dates", "horizon_sessions")}
            for record in sorted(episode["records"], key=lambda item: (item["condition"] != "true",
                                                                       item["decoding"] != "stochastic", item["draw"])):
                outcome = record["strict"]
                prompt_key = f"{task_id}/{record['condition']}"
                if decoder is not None and prompt_key not in prompts:
                    decoded = decoder(record["prompt_ids"])
                    prompts[prompt_key] = {"exact_prompt": decoded, "observation": _actor_observation(decoded)}
                records.append({
                    "checkpoint": label, "task_id": task_id, "condition": record["condition"],
                    "decoding": record["decoding"], "draw": record["draw"], "seed": record["seed"],
                    "text": record["text"], "action": record["action"], "terminated": record["terminated"],
                    "expression": outcome.get("expression"), "status": outcome["status"],
                    "reason": outcome.get("reason"), "orientation": outcome.get("orientation"),
                    "oriented_future_ic": outcome.get("oriented_future_ic"), "reward": outcome["reward"],
                    "scorer_feedback": _metrics(outcome.get("feedback")),
                    "scorer_assessment": _metrics(outcome.get("assessment")),
                    "prompt_tokens": len(record["prompt_ids"]), "completion_tokens": len(record["completion_ids"]),
                    "prompt_key": prompt_key,
                })
    old = recomputed["integrity"]["original_analysis"]
    registry = recomputed["integrity"]["five_checkpoint_registry"]
    return {
        "schema": "offline-linkage-evidence-v1", "roles": dict(ROLES), "checkpoints": labels,
        "tasks": [tasks[key] for key in sorted(tasks)], "records": records, "prompts": prompts,
        "counts": {"checkpoints": 5, "tasks": len(tasks), "records": len(records),
                   "original_records": sum(record["checkpoint"] in ORIGINALS for record in records),
                   "control_records": sum(record["checkpoint"] not in ORIGINALS for record in records),
                   "stochastic_draws_per_task_condition": 8},
        "overall": _unit(recomputed["overall"]),
        "task_rows": [{"task_id": row["task_id"], **_unit(row)} for row in recomputed["task_rows"]],
        "year_rows": [{"year": row["year"], **_unit(row)} for row in recomputed["year_rows"]],
        "integrity": {
            "snapshot_sha256": old["snapshot_sha256"],
            "evaluation_contract_sha256": old["evaluation_contract_sha256"],
            "original_three_frozen_utc": old["frozen_suite"]["frozen_utc"],
            "five_checkpoint_frozen_utc": registry["frozen_utc"],
            "original_frozen_suite_sha256": registry["original_frozen_suite_sha256"],
            "original_reports": registry["original_reports"],
            "checkpoint_hashes": {label: checkpoint["combined_sha256"]
                                  for label, checkpoint in registry["checkpoints"].items()},
            "evaluation_started_utc": {label: reports[label]["manifest"]["created_utc"] for label in labels},
            "original_three_validated_unchanged": True, "exact_paired_prompt_tokens_checked": True,
        },
        "sources": [{"file": Path(source["file"].replace("\\", "/")).name, "sha256": source["sha256"]}
                    for source in report_sources.values()],
    }


def render_html(payload):
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c")
    return HTML.replace("__LINKAGE_JSON__", encoded)


HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AlphaResearch-RL · Reward-linkage evidence</title><style>
:root{color-scheme:light;--ink:#172c3c;--muted:#5b6c78;--line:#dbe3e8;--blue:#215c8d;--bg:#f2f5f7}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1320px;margin:auto;padding:34px 28px 64px}h1{font-size:clamp(28px,4vw,42px);line-height:1.15;letter-spacing:-1px;margin:12px 0}
h2{font-size:22px;margin:0 0 12px}h3{font-size:16px;margin:18px 0 8px}p{margin:8px 0}.eyebrow{color:var(--blue);font-size:12px;font-weight:750;letter-spacing:1.5px;text-transform:uppercase}
.lede{max-width:1050px;color:var(--muted);font-size:17px}.chips{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0}.chip{padding:5px 11px;border:1px solid var(--line);border-radius:20px;background:white;font-size:12px}
.card{background:white;border:1px solid var(--line);border-radius:14px;padding:22px;margin:18px 0}.note{color:var(--muted);font-size:13px}
.callout{border-left:3px solid var(--blue);padding:10px 14px;background:#f3f8fc;margin:14px 0}
.controls{display:grid;grid-template-columns:2fr 1fr 1.4fr 1.2fr .8fr;gap:12px;margin:16px 0}label{display:block;font-size:12px;font-weight:650;color:var(--muted)}
select{display:block;width:100%;margin-top:6px;background:white;border:1px solid #b9c8d3;border-radius:7px;padding:10px;color:var(--ink);font:inherit;font-size:14px}
select:focus{outline:2px solid #8bc0e5;outline-offset:1px}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px}
th,td{text-align:right;padding:10px 12px;border-bottom:1px solid var(--line);white-space:nowrap}th:first-child,td:first-child{text-align:left}th{color:var(--muted);background:#f6f8fa;font-weight:600}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.subcard{border:1px solid var(--line);border-radius:10px;padding:16px;min-width:0}
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:14px 0}.metric{background:#f5f8fa;border-radius:8px;padding:12px}.metric b{display:block;font-size:20px;margin-top:4px;font-variant-numeric:tabular-nums}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f6f8fa;border:1px solid var(--line);padding:14px;border-radius:8px;font:12px/1.6 ui-monospace,Consolas,monospace;max-height:400px;overflow:auto}
code{font-family:ui-monospace,Consolas,monospace;overflow-wrap:anywhere}.status{display:inline-block;padding:3px 10px;border-radius:20px;background:#e9f3ef;color:#24796a;font-weight:700;font-size:12px}.status.bad{background:#fbedea;color:#a34235}
details{margin-top:16px}summary{cursor:pointer;font-weight:650}.hashes{display:grid;gap:10px;font-size:12px}.hashes code{display:block;color:var(--muted)}.footer{font-size:12px;color:var(--muted)}
@media(max-width:850px){main{padding:24px 16px 40px}.controls{grid-template-columns:1fr 1fr}.grid{grid-template-columns:1fr}.metrics{grid-template-columns:1fr 1fr}.card{padding:17px}}
@media(max-width:600px){.controls{grid-template-columns:1fr;gap:10px}}
</style></head><body><main>
<header><div class="eyebrow">AlphaResearch-RL · Exploratory follow-up</div><h1>Does reward–proposal linkage matter?</h1>
<p class="lede">Inspect all five saved policies and every retained completion. Two correct-reward RL seeds are compared with matched seeds trained on within-group permuted rewards. This control was designed after the original transfer results were inspected. It is a recorded one-step experiment, not a live or sequential research agent.</p><div class="chips" id="chips"></div></header>
<section class="card"><h2>The exploratory primary comparison</h2><p>Strict JSON · stochastic policy · true evidence · all ten 2020–2024 half-years. Every draw contributes; no best-of-N selection.</p>
<div class="scroll"><table><thead><tr><th>Correct RL minus matched placebo</th><th>Reward difference</th><th>Validity component</th><th>IC contribution difference</th><th>Grounding interaction</th></tr></thead><tbody id="primaryPairs"></tbody></table></div>
<div class="callout">Mean reward = −1.01 + valid fraction + all-proposal oriented IC contribution. The validity component is the difference in valid fraction. Failed proposals have no measured IC; their zero contribution is an accounting convention. Valid-only IC conditions on changing successful subsets.</div>
<h3>All five policies and unchanged numerical references</h3><div class="scroll"><table><thead><tr><th>Policy / reference</th><th>Reward</th><th>Valid</th><th>All-proposal IC</th><th>Valid-only IC</th><th>Draws / choices</th></tr></thead><tbody id="primaryPolicies"></tbody></table></div>
<p class="note">The uniform grid averages all 16 formulas; feedback-greedy observes all 16. The actor observes two probes. Fixed lag-1 was chosen on training data. These reference results are reused unchanged.</p>
<h3>Every trained policy minus the common SFT parent</h3><div class="scroll"><table><thead><tr><th>Policy minus SFT</th><th>Reward difference</th><th>Validity component</th><th>IC contribution difference</th></tr></thead><tbody id="vsSft"></tbody></table></div>
<p class="note">Five dependent assessment years and two training seeds support a descriptive mechanism control. They do not establish significance, causal benefit, profitability, new alpha discovery or sequential research ability.</p></section>
<section class="card"><h2>All 900 traces, in order</h2><p class="note">Default: the first SFT task, true evidence, stochastic draw zero. Policy, task and evidence changes preserve the draw when available. Greedy uses its sole draw zero and remains a separate diagnostic. Placebo is labeled separately from correct-reward RL.</p>
<div class="controls"><label>Policy<select id="checkpoint" aria-label="Policy"></select></label><label>Task<select id="task" aria-label="Task"></select></label><label>Actor evidence<select id="condition" aria-label="Actor evidence"><option value="true">True probe correspondence</option><option value="exchanged">Exchanged probe correspondence</option></select></label><label>Decoding<select id="decoding" aria-label="Decoding"><option value="stochastic">Stochastic (primary)</option><option value="greedy">Greedy (diagnostic)</option></select></label><label>Draw<select id="draw" aria-label="Draw"></select></label></div>
<p class="note" id="traceTitle"></p><p><span class="status" id="status"></span> <span class="note" id="reason"></span></p>
<div class="metrics"><div class="metric"><span class="note">Recorded reward</span><b id="reward"></b></div><div class="metric"><span class="note">Valid oriented future IC</span><b id="ic"></b></div><div class="metric"><span class="note">Feedback-fixed orientation</span><b id="orientation"></b></div><div class="metric"><span class="note">Prompt / completion tokens</span><b id="tokens"></b></div></div>
<p>Expression: <code id="expression"></code></p><div class="grid"><div class="subcard"><h3>Generated text · verbatim</h3><pre id="generated"></pre></div><div class="subcard"><h3>Strict parsed action</h3><pre id="parsed"></pre><p class="note" id="termination"></p></div></div>
<h3>What the actor actually observed</h3><div class="subcard"><p class="note">These two probe bundles come from the saved prompt. They are not the scorer's evaluation of the submitted expression.</p><pre id="observed"></pre><details id="promptDetails"><summary>Exact recorded system and user prompt</summary><pre id="prompt"></pre></details></div>
<h3>Evaluator outputs · after the proposal</h3><div class="grid"><div class="subcard"><h3>True feedback for the submitted expression</h3><pre id="feedback"></pre><p class="note">True feedback fixes orientation even under exchanged actor evidence. This is not an observed third probe.</p></div><div class="subcard"><h3>Later assessment for the submitted expression</h3><pre id="assessment"></pre><p class="note">Future scoring metrics were absent from the actor's prompt. Missing values remain explicit.</p></div></div>
<h3>Selected evidence and decoding · all ten tasks</h3><div class="scroll"><table><thead><tr><th>Policy</th><th>Reward</th><th>Valid</th><th>All-proposal IC</th><th>True − exchanged reward</th><th>Reward − SFT</th></tr></thead><tbody id="conditionPolicies"></tbody></table></div>
<h3>Selected evidence and decoding · correct RL minus placebo</h3><div class="scroll"><table><thead><tr><th>Seed pair</th><th>Reward difference</th><th>Validity component</th><th>IC contribution difference</th><th>Grounding interaction</th></tr></thead><tbody id="conditionPairs"></tbody></table></div></section>
<section class="card"><h2>Every half-year and year, both seeds</h2><p class="note">The tables follow the selected evidence and decoding. A year averages its two half-years equally. Grounding interaction is the difference between policies' true-minus-exchanged reward effects. Negative differences are retained.</p>
<h3>All five years · matched seed comparisons</h3><div class="scroll"><table><thead><tr><th>Year / seed</th><th>Correct RL − placebo</th><th>Validity component</th><th>IC contribution difference</th><th>Grounding interaction</th></tr></thead><tbody id="yearPairs"></tbody></table></div>
<details><summary>All ten half-years · matched seed comparisons</summary><div class="scroll"><table><thead><tr><th>Task / seed</th><th>Correct RL − placebo</th><th>Validity component</th><th>IC contribution difference</th><th>Grounding interaction</th></tr></thead><tbody id="taskPairs"></tbody></table></div></details>
<details><summary>All five policies and SFT differences · every task</summary><div class="scroll"><table><thead><tr><th>Task / policy</th><th>Reward</th><th>Valid</th><th>IC contribution</th><th>Reward − SFT</th><th>Validity − SFT</th><th>IC contribution − SFT</th></tr></thead><tbody id="taskPolicies"></tbody></table></div></details>
<details><summary>All five policies and SFT differences · every year</summary><div class="scroll"><table><thead><tr><th>Year / policy</th><th>Reward</th><th>Valid</th><th>IC contribution</th><th>Reward − SFT</th><th>Validity − SFT</th><th>IC contribution − SFT</th></tr></thead><tbody id="yearPolicies"></tbody></table></div></details></section>
<section class="card"><h2>Two freezes, with distinct chronology</h2><p>The original three-policy freeze predates its original evaluation records. The later five-policy extension predates control scoring and binds the original three checkpoint identities and report bytes. It does not retroactively register the exploratory control before the original outcomes.</p><pre id="chronology"></pre>
<p class="note">The builder validates both studies, all trace slots and paired prompts, checks report byte hashes against the saved analysis, and recomputes every aggregate. No market scoring, generation or model inference occurs.</p><div class="hashes" id="hashes"></div><details><summary>Evaluation identity and checkpoint hashes</summary><pre id="integrity"></pre></details><details><summary>Rebuild this artifact</summary><pre id="command"></pre></details></section>
<p class="footer">Self-contained HTML · no external scripts, fonts, network requests or APIs. Generated content is displayed as text. Strict JSON is primary; fence-tolerant reparsing remains secondary in the saved analysis.</p>
</main><script id="linkage-data" type="application/json">__LINKAGE_JSON__</script><script>
'use strict';
const data=JSON.parse(document.getElementById('linkage-data').textContent),byId=id=>document.getElementById(id);
const put=(id,value)=>{byId(id).textContent=value;},clear=id=>byId(id).replaceChildren();
const fmt=value=>value===null||value===undefined?'Unavailable':Number(value).toFixed(5),pct=value=>value===null?'Unavailable':(100*value).toFixed(1)+'%',pretty=value=>JSON.stringify(value,null,2);
const names={};names[data.roles.sft]='SFT';names[data.roles.rl_seed23]='Correct RL · seed 23';names[data.roles.rl_seed29]='Correct RL · seed 29';names[data.roles.placebo_seed23]='Placebo · seed 23';names[data.roles.placebo_seed29]='Placebo · seed 29';
function row(id,values){const tr=document.createElement('tr');for(const value of values){const td=document.createElement('td');td.textContent=value;tr.appendChild(td);}byId(id).appendChild(tr);}
function option(id,value,text){const item=document.createElement('option');item.value=value;item.textContent=text;byId(id).appendChild(item);}
for(const label of data.checkpoints)option('checkpoint',label,names[label]);for(const task of data.tasks)option('task',task.task_id,task.task_id);
for(const text of ['5 policies','900 retained traces','540 original + 360 control','10 half-years · 5 years','Exploratory, post-original follow-up']){const chip=document.createElement('span');chip.className='chip';chip.textContent=text;byId('chips').appendChild(chip);}
function pairs(id,cell,condition,prefix=''){for(const seed of ['23','29']){const pair=cell.correct_vs_placebo[seed],m=pair[condition];row(id,[prefix+'seed '+seed,fmt(m.reward_delta),fmt(m.failure_penalty_component_delta),fmt(m.all_proposal_ic_contribution_delta),fmt(pair.grounding_interaction.reward_delta)]);}}
const primary=data.overall.metrics.stochastic;pairs('primaryPairs',primary,'true');
for(const label of data.checkpoints){const m=primary.policies[label].true;row('primaryPolicies',[names[label],fmt(m.mean_reward),pct(m.valid_fraction),fmt(m.all_proposal_ic_contribution),fmt(m.mean_oriented_ic_valid_only),m.n_samples]);}
for(const [name,label] of [['uniform_grid','Uniform grid · 16 formulas'],['feedback_greedy_grid','Feedback-greedy grid · extra information'],['training_best_fixed','Fixed lag-1 · training-selected']]){const m=data.overall.references[name];row('primaryPolicies',[label,fmt(m.mean_reward),pct(m.valid_fraction),fmt(m.all_proposal_ic_contribution),fmt(m.mean_oriented_ic_valid_only),m.n_samples]);}
for(const label of data.checkpoints.slice(1)){const m=primary.policy_vs_sft[label].true;row('vsSft',[names[label],fmt(m.reward_delta),fmt(m.failure_penalty_component_delta),fmt(m.all_proposal_ic_contribution_delta)]);}
function updateDraws(){const previous=byId('draw').value;clear('draw');const matching=data.records.filter(r=>r.checkpoint===byId('checkpoint').value&&r.task_id===byId('task').value&&r.condition===byId('condition').value&&r.decoding===byId('decoding').value);for(const record of matching)option('draw',record.draw,record.draw);if(matching.some(record=>String(record.draw)===previous))byId('draw').value=previous;update();}
function unitPolicies(id,units,key,condition,decoding){clear(id);for(const unit of units){const cell=unit.metrics[decoding];for(const label of data.checkpoints){const m=cell.policies[label][condition],delta=label===data.roles.sft?null:cell.policy_vs_sft[label][condition];row(id,[unit[key]+' / '+names[label],fmt(m.mean_reward),pct(m.valid_fraction),fmt(m.all_proposal_ic_contribution),fmt(delta?delta.reward_delta:0),fmt(delta?delta.failure_penalty_component_delta:0),fmt(delta?delta.all_proposal_ic_contribution_delta:0)]);}}}
function update(){
 const condition=byId('condition').value,decoding=byId('decoding').value;
 const record=data.records.find(r=>r.checkpoint===byId('checkpoint').value&&r.task_id===byId('task').value&&r.condition===condition&&r.decoding===decoding&&r.draw===Number(byId('draw').value));
 put('traceTitle',record.checkpoint+' · '+record.task_id+' · '+condition+' evidence · '+decoding+' draw '+record.draw+' · RNG seed '+record.seed);
 put('status',record.status==='ok'?'Valid proposal':'Failed proposal');byId('status').classList.toggle('bad',record.status!=='ok');put('reason',record.reason||'');
 put('reward',fmt(record.reward));put('ic',fmt(record.oriented_future_ic));put('orientation',record.orientation===null?'Unavailable':record.orientation);put('tokens',record.prompt_tokens+' / '+record.completion_tokens);
 put('expression',record.expression||'No scorable expression');put('generated',record.text);put('parsed',pretty(record.action));put('termination',record.terminated?'EOS observed in saved completion.':'No terminating EOS; retained as failure.');
 put('feedback',pretty(record.scorer_feedback));put('assessment',pretty(record.scorer_assessment));const prompt=data.prompts[record.prompt_key];
 put('observed',prompt&&prompt.observation?pretty(prompt.observation):'Actor probes are not decoded in this build. Evaluator feedback below is not a substitute for the actual observation.');byId('promptDetails').hidden=!prompt;if(prompt)put('prompt',prompt.exact_prompt);
 clear('conditionPolicies');const cell=data.overall.metrics[decoding];for(const label of data.checkpoints){const m=cell.policies[label][condition];row('conditionPolicies',[names[label],fmt(m.mean_reward),pct(m.valid_fraction),fmt(m.all_proposal_ic_contribution),fmt(cell.evidence_effects[label].reward_delta),fmt(label===data.roles.sft?0:cell.policy_vs_sft[label][condition].reward_delta)]);}
 clear('conditionPairs');pairs('conditionPairs',cell,condition);clear('yearPairs');for(const unit of data.year_rows)pairs('yearPairs',unit.metrics[decoding],condition,unit.year+' / ');clear('taskPairs');for(const unit of data.task_rows)pairs('taskPairs',unit.metrics[decoding],condition,unit.task_id+' / ');
 unitPolicies('taskPolicies',data.task_rows,'task_id',condition,decoding);unitPolicies('yearPolicies',data.year_rows,'year',condition,decoding);
}
for(const id of ['checkpoint','task','condition','decoding'])byId(id).addEventListener('change',updateDraws);byId('draw').addEventListener('change',update);updateDraws();
put('chronology','Original three-policy freeze: '+data.integrity.original_three_frozen_utc+'\nFive-policy extension: '+data.integrity.five_checkpoint_frozen_utc+'\nOriginal results remain unchanged; extension applies prospectively to controls.');
for(const source of data.sources){const line=document.createElement('div'),label=document.createElement('strong'),hash=document.createElement('code');label.textContent=source.file;hash.textContent='SHA256 '+source.sha256;line.appendChild(label);line.appendChild(hash);byId('hashes').appendChild(line);}
put('integrity',pretty(data.integrity));put('command',data.rebuild_command||'Run python -m alpha_research_rl.linkage_explorer --help.');
</script></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    flags = ("sft", "rl23", "rl29", "placebo23", "placebo29", "analysis")
    for flag in flags:
        parser.add_argument("--" + flag, type=Path, required=True)
    parser.add_argument("--tokenizer", type=Path, help="optional verified local tokenizer only")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = [getattr(args, flag) for flag in flags]
    raw = [path.read_bytes() for path in paths]
    sources = {label: {"file": path.name, "sha256": hashlib.sha256(content).hexdigest()}
               for label, path, content in zip(ROLES.values(), paths[:5], raw[:5], strict=True)}
    reports = {label: json.loads(content) for label, content in zip(ROLES.values(), raw[:5], strict=True)}
    decoder, token_sources = None, []
    if args.tokenizer:
        decoder, token_sources = local_prompt_decoder(args.tokenizer,
            reports[ORIGINALS[0]]["manifest"]["config"]["evaluation_contract"]["tokenizer_files_sha256"])
    payload = prepare_payload(reports, json.loads(raw[5]), sources, decoder)
    payload["sources"].append({"file": args.analysis.name, "sha256": hashlib.sha256(raw[5]).hexdigest()})
    for source in (Path(__file__), Path(evidence_explorer.__file__)):
        payload["sources"].append({"file": source.name, "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
    payload["sources"].extend(token_sources)
    command = ["python -m alpha_research_rl.linkage_explorer"]
    for flag in (*flags, "tokenizer", "output"):
        value = getattr(args, flag)
        if value is not None:
            try:
                value = value.resolve().relative_to(Path.cwd().resolve()).as_posix()
            except ValueError:
                value = value.name
            command.append(f"  --{flag} {value}")
    payload["rebuild_command"] = " \\\n".join(command)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(payload), encoding="utf-8")
    print(json.dumps({"output_file": args.output.name, **payload["counts"]}))


if __name__ == "__main__":
    main()
