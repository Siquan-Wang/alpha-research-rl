"""Build a self-contained offline explorer of retained financial proposal evidence.

No scoring, model loading or new generation occurs. Optional prompt decoding
loads only an already cached tokenizer with local_files_only=True.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .financial_analysis import analyze_reports

METRIC_KEYS = ("mean_ic", "ic_std", "coverage", "n_dates", "n_signal_dates")


def _metrics(value):
    return None if value is None else {key: value.get(key) for key in METRIC_KEYS}


def _analysis_unit(unit):
    return {"n_tasks": unit["n_tasks"], "metrics": unit["metrics"]["strict"],
            "references": unit["references"]}


def _actor_observation(prompt):
    """Extract the actual serialized user observation, never scorer feedback."""
    try:
        user = prompt.split("<|im_start|>user\n", 1)[1].split("<|im_end|>", 1)[0]
        observation = json.loads(user)
        probes = observation["probe_evidence"]
        if len(probes) != 2:
            return None
        return {"probe_evidence": [{"expression": probe["expression"],
                                    "feedback": _metrics(probe["feedback"]),
                                    "feedback_usable": probe["feedback_usable"],
                                    "windows": [_metrics(window) for window in probe["windows"]]}
                                   for probe in probes]}
    except (ValueError, KeyError, IndexError, TypeError):
        return None


def prepare_payload(reports: dict, analysis: dict, sources: list[dict], decoder=None, gate=None) -> dict:
    """Validate all retained draws and saved analysis before compacting public fields."""
    roles = analysis["roles"]
    labels = [roles[key] for key in ("sft", "rl_seed23", "rl_seed29")]
    recomputed = analyze_reports(reports, labels[0], tuple(labels[1:]))
    for key in ("roles", "integrity", "task_rows", "year_rows", "overall", "rl_seed_summary"):
        if analysis.get(key) != recomputed[key]:
            raise ValueError(f"saved analysis differs from retained proposal outcomes: {key}")
    records, prompts, tasks = [], {}, {}
    for label in labels:
        for episode in sorted(reports[label]["episodes"], key=lambda row: (row["task"]["year"], row["task"]["half"])):
            task = episode["task"]
            task_id = task["task_id"]
            tasks[task_id] = {key: task[key] for key in ("task_id", "year", "half", "feedback_signal_dates",
                                                         "assessment_signal_dates", "horizon_sessions")}
            for record in sorted(episode["records"], key=lambda row: (row["condition"] != "true",
                                                                      row["decoding"] != "stochastic", row["draw"])):
                outcome = record["strict"]
                prompt_key = f"{task_id}/{record['condition']}"
                if decoder is not None and prompt_key not in prompts:
                    decoded = decoder(record["prompt_ids"])
                    prompts[prompt_key] = {"exact_prompt": decoded, "observation": _actor_observation(decoded)}
                records.append({"checkpoint": label, "task_id": task_id, "condition": record["condition"],
                                "decoding": record["decoding"], "draw": record["draw"], "seed": record["seed"],
                                "text": record["text"], "action": record["action"], "terminated": record["terminated"],
                                "expression": outcome.get("expression"), "status": outcome["status"],
                                "reason": outcome.get("reason"), "orientation": outcome.get("orientation"),
                                "oriented_future_ic": outcome.get("oriented_future_ic"), "reward": outcome["reward"],
                                "scorer_feedback": _metrics(outcome.get("feedback")),
                                "scorer_assessment": _metrics(outcome.get("assessment")),
                                "prompt_tokens": len(record["prompt_ids"]),
                                "completion_tokens": len(record["completion_ids"]), "prompt_key": prompt_key})
    integrity = recomputed["integrity"]
    payload = {"schema": "offline-financial-evidence-v1", "roles": roles, "checkpoints": labels,
               "tasks": [tasks[key] for key in sorted(tasks)], "records": records, "prompts": prompts,
               "counts": {"checkpoints": 3, "tasks": len(tasks), "records": len(records),
                          "stochastic_draws_per_task_condition": integrity["stochastic_draws_per_task_condition"]},
               "overall": _analysis_unit(recomputed["overall"]),
               "task_rows": [{"task_id": row["task_id"], **_analysis_unit(row)} for row in recomputed["task_rows"]],
               "year_rows": [{"year": row["year"], **_analysis_unit(row)} for row in recomputed["year_rows"]],
               "sources": [{"file": Path(source["file"].replace("\\", "/")).name,
                            "sha256": source["sha256"]} for source in sources],
               "integrity": {"snapshot_sha256": integrity["snapshot_sha256"],
                             "evaluation_contract_sha256": integrity["evaluation_contract_sha256"],
                             "frozen_utc": integrity["frozen_suite"]["frozen_utc"],
                             "checkpoint_hashes": {label: value["combined_sha256"] for label, value in
                                                   integrity["frozen_suite"]["checkpoints"].items()}},
               "gate": None}
    if gate is not None:
        payload["gate"] = {key: gate[key] for key in ("study", "gate_passed")}
        payload["gate"]["conditions"] = {key: gate["conditions"][key] for key in (
            "pooled_late_minus_cheap_gt_002", "late_minus_cheap_positive_both_folds",
            "pooled_late_minus_fixed_lag1_positive")}
        payload["gate"]["pooled"] = {key: gate["pooled"][key] for key in (
            "n_tasks", "mean_reward", "failure_counts", "valid_fraction", "valid_ic_contribution",
            "all_late_minus_cheap", "all_late_minus_fixed_lag1")}
        payload["gate"]["folds"] = [{key: fold[key] for key in ("fold", "training_years", "evaluation_years",
                                                                  "all_late_minus_cheap", "all_late_minus_fixed_lag1")}
                                    for fold in gate["folds"]]
    return payload


def render_html(payload: dict) -> str:
    # JSON is inert data. Escaping '<' also prevents a generated </script> from
    # closing the data element before JSON.parse; all data rendering uses textContent.
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c")
    return HTML.replace("__EVIDENCE_JSON__", encoded)


def local_prompt_decoder(directory: Path, expected_hashes: dict):
    """Verify the recorded tokenizer identity before decoding saved token IDs."""
    sources = []
    for name, expected in expected_hashes.items():
        if Path(name).name != name or "\\" in name:
            raise ValueError("unsafe tokenizer contract filename")
        path = directory / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"local tokenizer differs from the recorded evaluation: {name}")
        sources.append({"file": name, "sha256": expected})
    if not sources:
        raise ValueError("recorded tokenizer identity is missing")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(directory, local_files_only=True, trust_remote_code=False)
    return lambda tokens: tokenizer.decode(tokens, skip_special_tokens=False), sources


HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AlphaResearch-RL · Recorded evidence explorer</title>
<style>
:root{color-scheme:light;--ink:#172c3c;--muted:#5b6c78;--line:#dbe3e8;--blue:#215c8d;--teal:#24796a;--red:#a34235;--bg:#f2f5f7}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1280px;margin:auto;padding:34px 28px 64px}h1{font-size:clamp(28px,4vw,42px);letter-spacing:-1px;line-height:1.15;margin:12px 0}
h2{font-size:22px;margin:0 0 12px}h3{font-size:16px;margin:0 0 8px}p{margin:8px 0}.eyebrow{color:var(--blue);font-size:12px;font-weight:750;letter-spacing:1.5px;text-transform:uppercase}
.lede{max-width:960px;color:var(--muted);font-size:17px}.chips{display:flex;flex-wrap:wrap;gap:8px;margin:20px 0}.chip{padding:5px 11px;border:1px solid var(--line);border-radius:20px;background:white;font-size:12px}
.card{background:white;border:1px solid var(--line);border-radius:14px;padding:22px;margin:18px 0;box-shadow:0 3px 16px #20374905}
.note{color:var(--muted);font-size:13px}.callout{border-left:3px solid var(--blue);padding:10px 14px;background:#f3f8fc;margin:14px 0}
.controls{display:grid;grid-template-columns:2fr 1fr 1.4fr 1.2fr .8fr;gap:12px;margin:16px 0}label{display:block;font-size:12px;font-weight:650;color:var(--muted)}
select{display:block;width:100%;margin-top:6px;background:#fff;border:1px solid #b9c8d3;border-radius:7px;padding:10px;color:var(--ink);font:inherit;font-size:14px}
select:focus{outline:2px solid #8bc0e5;outline-offset:1px}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:right;padding:10px 12px;border-bottom:1px solid var(--line);white-space:nowrap}
th:first-child,td:first-child{text-align:left}th{color:var(--muted);font-weight:600;background:#f6f8fa}tr:last-child td{border-bottom:0}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}.subcard{border:1px solid var(--line);border-radius:10px;padding:16px;min-width:0}
.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:14px 0}.metric{background:#f5f8fa;border-radius:8px;padding:12px}.metric b{display:block;font-size:20px;margin-top:4px;font-variant-numeric:tabular-nums}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f6f8fa;border:1px solid var(--line);padding:14px;border-radius:8px;font:12px/1.6 ui-monospace,Consolas,monospace;margin:8px 0;max-height:380px;overflow:auto}
code{font-family:ui-monospace,Consolas,monospace;overflow-wrap:anywhere}.status{display:inline-block;padding:3px 10px;border-radius:20px;background:#e9f3ef;color:var(--teal);font-weight:700;font-size:12px}.status.bad{background:#fbedea;color:var(--red)}
.signed{display:flex;align-items:center;gap:10px}.track{position:relative;height:14px;flex:1;background:#f1f4f6;border-radius:3px}.track:after{position:absolute;content:'';width:1px;left:50%;height:100%;background:#97a8b4}.bar{position:absolute;top:2px;height:10px;border-radius:2px;background:var(--teal)}.bar.negative{background:var(--red)}
.signed code{min-width:88px;text-align:right;font-size:12px}.legend{display:flex;gap:15px;font-size:12px;color:var(--muted)}details{margin-top:12px}summary{cursor:pointer;font-weight:650}details pre{max-height:420px}.hashes{display:grid;gap:9px;font-size:12px}.hashes code{display:block;color:var(--muted)}
.footer{font-size:12px;color:var(--muted);padding-top:16px}.section-label{color:var(--muted);font-size:12px;margin:22px 0 6px;text-transform:uppercase;letter-spacing:1px}
@media(max-width:850px){main{padding:24px 16px 40px}.controls{grid-template-columns:1fr 1fr}.grid{grid-template-columns:1fr}.metrics{grid-template-columns:1fr 1fr}.card{padding:17px}h1{letter-spacing:-.5px}}
@media(max-width:600px){.controls{grid-template-columns:1fr;gap:10px}}
</style></head><body><main>
<header><div class="eyebrow">AlphaResearch-RL · Offline evidence</div><h1>Inspect the recorded experiment.</h1>
<p class="lede">One return-formula proposal per episode, generated by a local Qwen3-0.6B adapter. Explore the full registered comparison and every retained completion. This page is a saved record, not a live agent or a learned multi-turn research demonstration.</p>
<div class="chips" id="chips"></div></header>
<section class="card"><h2>The registered comparison</h2><p>Strict JSON, stochastic policy, true evidence · 2020 H1–2024 H2. Every sampled outcome contributes; there is no best-of-N selection.</p>
<div class="scroll"><table><thead><tr><th>Checkpoint / reference</th><th>Mean reward</th><th>Valid</th><th>All-draw IC contribution</th><th>Valid-only IC</th><th>Draws / choices</th></tr></thead><tbody id="primary"></tbody></table></div>
<p class="note">Uniform grid averages all 16 formulas. Feedback-greedy observes 16 feedback formulas; the actor sees two probes. Fixed lag-1 was selected using training data. Valid-only IC conditions on each policy's successful subset.</p>
<div class="callout">Reward = −1.01 + valid fraction + all-draw oriented IC contribution. Failure has no measured IC. Differences in the contribution can reflect changes in which proposals succeed.</div>
<h3>RL minus SFT: separate failures from predictive contribution</h3><div class="scroll"><table><thead><tr><th>RL checkpoint</th><th>Reward difference</th><th>Fewer-failure component</th><th>IC contribution difference</th></tr></thead><tbody id="decomposition"></tbody></table></div>
<p class="note">Two RL seeds share one SFT parent and historical data. Ten dependent half-years and five years support a descriptive development comparison; no significance or profitability claim follows.</p></section>
<section class="card"><h2>Every proposal, in order</h2><p class="note">The default is the first checkpoint, first task and first draw. Change evidence or decoding to inspect their separately generated records. Draw numbers below start at zero.</p>
<div class="controls"><label>Checkpoint<select id="checkpoint" aria-label="Checkpoint"></select></label><label>Task<select id="task" aria-label="Task"></select></label><label>Evidence shown to actor<select id="condition" aria-label="Evidence shown to actor"><option value="true">True probe correspondence</option><option value="exchanged">Exchanged probe correspondence</option></select></label><label>Decoding<select id="decoding" aria-label="Decoding"><option value="stochastic">Stochastic (primary)</option><option value="greedy">Greedy (diagnostic)</option></select></label><label>Draw<select id="draw" aria-label="Draw"></select></label></div>
<div id="traceTitle" class="note"></div><p><span id="status" class="status"></span> <span id="reason" class="note"></span></p>
<div class="metrics"><div class="metric"><span class="note">Recorded reward</span><b id="reward"></b></div><div class="metric"><span class="note">Valid oriented future IC</span><b id="ic"></b></div><div class="metric"><span class="note">Feedback-fixed orientation</span><b id="orientation"></b></div><div class="metric"><span class="note">Prompt / completion tokens</span><b id="tokens"></b></div></div>
<p>Expression: <code id="expression"></code></p><div class="grid"><div class="subcard"><h3>Generated text · verbatim</h3><pre id="generated"></pre></div><div class="subcard"><h3>Strict parsed action</h3><pre id="parsed"></pre><p class="note" id="termination"></p></div></div>
<div class="section-label">What the actor actually observed</div><div class="subcard"><h3>Two probe evidence bundles</h3><p class="note">These are the serialized user-observation probes, decoded from the saved prompt tokens. They are distinct from evaluation of the proposed expression.</p><pre id="observed"></pre><details id="promptDetails"><summary>Exact recorded prompt · system instructions and user observation</summary><pre id="prompt"></pre></details></div>
<div class="section-label">Evaluator outputs · computed after the proposal</div><div class="grid"><div class="subcard"><h3>True feedback for the submitted expression</h3><pre id="feedback"></pre><p class="note">The scorer uses true feedback for orientation even when the actor receives exchanged probe bundles. This summary was not an observed third probe.</p></div><div class="subcard"><h3>Later assessment for the submitted expression</h3><pre id="assessment"></pre><p class="note">These future scoring metrics were absent from the actor's prompt. Missing metrics are shown explicitly.</p></div></div>
<h3 style="margin-top:22px">Selected condition and decoding · all ten tasks</h3><div class="scroll"><table><thead><tr><th>Checkpoint</th><th>Mean reward</th><th>Valid</th><th>IC contribution</th><th>True − exchanged reward</th></tr></thead><tbody id="conditionSummary"></tbody></table></div>
<details><summary>Every task-level comparison · selected condition and decoding</summary><div class="scroll"><table><thead><tr><th>Task</th><th>SFT reward</th><th>RL23 reward</th><th>RL29 reward</th><th>RL23 − SFT</th><th>RL29 − SFT</th></tr></thead><tbody id="taskTable"></tbody></table></div></details>
</section>
<section class="card"><h2>All five assessment years</h2><p class="note">Each row averages its two half-years. Signed differences are retained for both seeds. Decoding and evidence follow the controls above.</p><div class="scroll"><table><thead><tr><th>Year</th><th>RL23 − SFT reward</th><th>RL29 − SFT reward</th><th>RL23 grounding interaction</th><th>RL29 grounding interaction</th></tr></thead><tbody id="yearTable"></tbody></table></div></section>
<section class="card" id="gateSection" hidden><h2>Separate sequential opportunity gate</h2><p class="note">Training-period fixed-grid CPU diagnostic. The privileged ridge sees every late check for free; this is not a two-check agent or an LLM training result.</p><p><span class="status" id="gateStatus"></span></p><pre id="gate"></pre></section>
<section class="card"><h2>Source identity and reproducibility</h2><p class="note">The builder validates the three retained transfer reports and recomputes paired statistics before embedding them. Prompt decoding uses only a cached tokenizer; no new proposal, market score or model inference is produced.</p><div class="hashes" id="hashes"></div><details><summary>Frozen evaluation identity</summary><pre id="integrity"></pre></details><details><summary>Rebuild this artifact</summary><pre id="command"></pre></details></section>
<p class="footer">Self-contained HTML · no remote scripts, fonts, APIs or model access. Generated content is displayed as text. Strict JSON is the registered primary parser; fence-tolerant reparsing remains a secondary analysis in the saved JSON reports.</p>
</main><script id="evidence-data" type="application/json">__EVIDENCE_JSON__</script><script>
'use strict';
const data=JSON.parse(document.getElementById('evidence-data').textContent);
const byId=id=>document.getElementById(id);
const put=(id,value)=>{byId(id).textContent=value;};
const fmt=value=>value===null||value===undefined?'Unavailable':Number(value).toFixed(6);
const pct=value=>(100*value).toFixed(2)+'%';
const pretty=value=>JSON.stringify(value,null,2);
function row(target,values){const tr=document.createElement('tr');for(const value of values){const td=document.createElement('td');td.textContent=String(value);tr.appendChild(td);}byId(target).appendChild(tr);}
function clear(id){byId(id).replaceChildren();}
function options(id,values){clear(id);for(const value of values){const option=document.createElement('option');option.value=String(value);option.textContent=String(value);byId(id).appendChild(option);}}
for(const text of [data.counts.checkpoints+' checkpoints',data.counts.tasks+' dependent half-years',data.counts.records+' retained draws','5-session rank IC','Strict JSON primary']){const chip=document.createElement('span');chip.className='chip';chip.textContent=text;byId('chips').appendChild(chip);}
const primary=data.overall.metrics.stochastic;
for(const label of data.checkpoints){const m=primary.policies[label].true;row('primary',[label,fmt(m.mean_reward),pct(m.valid_fraction),fmt(m.all_proposal_ic_contribution),fmt(m.mean_oriented_ic_valid_only),m.n_samples]);}
for(const [key,label] of [['uniform_grid','Uniform grid · 16 formulas'],['feedback_greedy_grid','Feedback-greedy grid · extra information'],['training_best_fixed','Fixed lag-1 · training-selected']]){const m=data.overall.references[key];row('primary',[label,fmt(m.mean_reward),pct(m.valid_fraction),fmt(m.all_proposal_ic_contribution),fmt(m.mean_oriented_ic_valid_only),m.n_samples]);}
for(const label of data.checkpoints.slice(1)){const m=primary.rl_vs_sft[label].true;row('decomposition',[label,fmt(m.reward_delta),fmt(m.failure_penalty_component_delta),fmt(m.all_proposal_ic_contribution_delta)]);}
options('checkpoint',data.checkpoints);options('task',data.tasks.map(task=>task.task_id));
function updateDraws(){const records=data.records.filter(r=>r.checkpoint===byId('checkpoint').value&&r.task_id===byId('task').value&&r.condition===byId('condition').value&&r.decoding===byId('decoding').value);const old=byId('draw').value;options('draw',records.map(r=>r.draw));if(records.some(r=>String(r.draw)===old))byId('draw').value=old;update();}
function update(){
 const checkpoint=byId('checkpoint').value,taskId=byId('task').value,condition=byId('condition').value,decoding=byId('decoding').value,draw=Number(byId('draw').value);
 const record=data.records.find(r=>r.checkpoint===checkpoint&&r.task_id===taskId&&r.condition===condition&&r.decoding===decoding&&r.draw===draw);
 put('traceTitle',taskId+' · '+condition+' evidence · '+decoding+' draw '+draw+' · recorded RNG seed '+record.seed);
 put('status',record.status==='ok'?'Valid proposal':'Failed proposal');byId('status').classList.toggle('bad',record.status!=='ok');put('reason',record.reason||'');
 put('reward',fmt(record.reward));put('ic',fmt(record.oriented_future_ic));put('orientation',record.orientation===null?'Unavailable':record.orientation);put('tokens',record.prompt_tokens+' / '+record.completion_tokens);
 put('expression',record.expression||'No scorable expression');put('generated',record.text);put('parsed',pretty(record.action));put('termination',record.terminated?'EOS observed in the saved completion.':'Completion did not terminate with EOS; retained as a failure.');
 put('feedback',pretty(record.scorer_feedback));put('assessment',pretty(record.scorer_assessment));
 const prompt=data.prompts[record.prompt_key];put('observed',prompt&&prompt.observation?pretty(prompt.observation):'Observed probes are not decoded in this build. Scorer summaries below are evaluator outputs, not substitutes for the actor observation.');byId('promptDetails').hidden=!prompt;if(prompt)put('prompt',prompt.exact_prompt);
 clear('conditionSummary');const cell=data.overall.metrics[decoding];for(const label of data.checkpoints){const m=cell.policies[label][condition];row('conditionSummary',[label,fmt(m.mean_reward),pct(m.valid_fraction),fmt(m.all_proposal_ic_contribution),fmt(cell.evidence_effects[label].reward_delta)]);}
 clear('taskTable');for(const task of data.task_rows){const cell=task.metrics[decoding];row('taskTable',[task.task_id,...data.checkpoints.map(label=>fmt(cell.policies[label][condition].mean_reward)),...data.checkpoints.slice(1).map(label=>fmt(cell.rl_vs_sft[label][condition].reward_delta))]);}
 clear('yearTable');for(const year of data.year_rows){const cell=year.metrics[decoding];row('yearTable',[year.year,...data.checkpoints.slice(1).map(label=>fmt(cell.rl_vs_sft[label][condition].reward_delta)),...data.checkpoints.slice(1).map(label=>fmt(cell.rl_vs_sft[label].grounding_interaction.reward_delta))]);}
}
for(const id of ['checkpoint','task','condition','decoding'])byId(id).addEventListener('change',updateDraws);byId('draw').addEventListener('change',update);updateDraws();
if(data.gate){byId('gateSection').hidden=false;put('gateStatus',data.gate.gate_passed?'Allocation gate passed':'Allocation gate failed');byId('gateStatus').classList.toggle('bad',!data.gate.gate_passed);put('gate',pretty(data.gate));}
for(const source of data.sources){const line=document.createElement('div');const label=document.createElement('strong');label.textContent=source.file;const hash=document.createElement('code');hash.textContent='SHA256 '+source.sha256;line.appendChild(label);line.appendChild(hash);byId('hashes').appendChild(line);}
put('integrity',pretty(data.integrity));put('command',data.rebuild_command||'Run python -m alpha_research_rl.evidence_explorer --help for the saved-report builder.');
</script></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for role in ("sft", "rl23", "rl29", "analysis"):
        parser.add_argument(f"--{role}", type=Path, required=True)
    parser.add_argument("--gate", type=Path)
    parser.add_argument("--tokenizer", type=Path, help="optional local cached tokenizer directory; no model loading")
    parser.add_argument("--output", type=Path, default=Path("docs/evidence-explorer.html"))
    args = parser.parse_args()
    paths = [args.sft, args.rl23, args.rl29, args.analysis] + ([args.gate] if args.gate else [])
    contents = [path.read_bytes() for path in paths]
    reports = [json.loads(raw) for raw in contents[:3]]
    sources = [{"file": path.name, "sha256": hashlib.sha256(raw).hexdigest()} for path, raw in zip(paths, contents)]
    sources.append({"file": Path(__file__).name, "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    decoder = None
    if args.tokenizer:
        decoder, token_sources = local_prompt_decoder(
            args.tokenizer, reports[0]["manifest"]["config"]["evaluation_contract"]["tokenizer_files_sha256"])
        sources.extend(token_sources)
    payload = prepare_payload({report["manifest"]["config"]["label"]: report for report in reports},
                              json.loads(contents[3]), sources, decoder=decoder,
                              gate=json.loads(contents[4]) if args.gate else None)
    command = ["python -m alpha_research_rl.evidence_explorer"]
    for flag in ("sft", "rl23", "rl29", "analysis", "gate", "tokenizer", "output"):
        value = getattr(args, flag)
        if value is not None:
            # Rebuild instructions intentionally use repository-relative names.
            try:
                relative = value.resolve().relative_to(Path.cwd().resolve()).as_posix()
            except ValueError:
                relative = value.name
            command.append(f"  --{flag} {relative}")
    payload["rebuild_command"] = " \\\n".join(command)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_html(payload), encoding="utf-8")
    print(json.dumps({"output_file": args.output.name, **payload["counts"]}))


if __name__ == "__main__":
    main()
