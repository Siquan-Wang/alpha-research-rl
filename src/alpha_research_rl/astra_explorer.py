"""Build a self-contained view of a complete, replay-verified Astra study."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from .astra_replay import replay_study


def build_payload(contract: Path, submissions: Path, assessment: Path, *, source_root: Path) -> dict:
    """Accept the full fixed bank only; never invoke actors or market evaluation."""
    captured = {"contract": Path(contract).read_bytes(), "submissions": Path(submissions).read_bytes(),
                "assessment": Path(assessment).read_bytes()}
    # Validate the exact captured bytes that will be embedded, even if the
    # original input paths change during or after the path-based replay.
    with tempfile.TemporaryDirectory(prefix="astra-explorer-") as temporary:
        snapshots = {name: Path(temporary) / (name + ".json") for name in captured}
        for name, raw in captured.items():
            snapshots[name].write_bytes(raw)
        verified = replay_study(snapshots["contract"], snapshots["submissions"], source_root=source_root,
                                assessment_path=snapshots["assessment"])
    bank = json.loads(captured["submissions"])
    histories = {}
    for episode in bank["episodes"]:
        before, history = [], []
        for record in episode["submission"]["records"]:
            before.append(list(history))
            raw = record["raw_response"]
            history.append({"attempt": record["attempt"], "raw_response": raw[:20000],
                            "raw_response_sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                            "raw_response_truncated": len(raw) > 20000,
                            "visible_feedback": record["visible_feedback"]})
        histories[episode["task_id"] + "/" + episode["arm"]] = before
    return {
        "verification": verified,
        "submissions": bank,
        "assessment": json.loads(captured["assessment"]),
        "permitted_histories": histories,
    }


def render(payload: dict) -> str:
    # Script data is inert JSON; all model-authored content is displayed with textContent.
    serialized = json.dumps(payload, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
    for character, escaped in (("&", "\\u0026"), ("<", "\\u003c"), (">", "\\u003e"),
                               ("\u2028", "\\u2028"), ("\u2029", "\\u2029")):
        serialized = serialized.replace(character, escaped)
    return TEMPLATE.replace("__ASTRA_DATA__", serialized)


TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Astra agentic research — recorded evidence</title><style>
:root{color-scheme:light;--ink:#182c3c;--muted:#556673;--line:#d8e2e8;--blue:#225e91;--bg:#f2f6f8}
*{box-sizing:border-box}body{margin:0;color:var(--ink);background:var(--bg);font:15px/1.6 system-ui,Segoe UI,sans-serif}
main{max-width:1320px;margin:auto;padding:36px 24px 64px}h1{font-size:clamp(29px,4vw,44px);line-height:1.15;margin:10px 0 18px}h2{font-size:23px;margin:0 0 12px}h3{font-size:18px;margin:0 0 10px}p{margin:8px 0}
.eyebrow{color:var(--blue);letter-spacing:1.3px;font-size:12px;font-weight:750;text-transform:uppercase}.lede{max-width:980px;color:var(--muted);font-size:17px}.note{font-size:13px;color:var(--muted)}
.card{margin:20px 0;padding:24px;background:white;border:1px solid var(--line);border-radius:14px}.callout{padding:12px 16px;background:#eff6fb;border-left:3px solid var(--blue);margin:14px 0}.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:10px 12px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}th:first-child,td:first-child{text-align:left}th{background:#f4f7f9;color:var(--muted)}
.controls{display:flex;flex-wrap:wrap;gap:16px;margin:18px 0}label{font-size:13px;font-weight:650}select{display:block;min-width:190px;margin-top:5px;padding:9px;border:1px solid #aabcc9;border-radius:6px;background:white;color:var(--ink);font:inherit}
select:focus,summary:focus{outline:2px solid #80b8df;outline-offset:2px}.arms{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.arm{min-width:0;padding:18px;border:1px solid var(--line);border-radius:10px}.arm p{overflow-wrap:anywhere}
pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:370px;overflow:auto;background:#f5f8fa;border:1px solid var(--line);border-radius:6px;padding:12px;font:12px/1.6 ui-monospace,Consolas,monospace}code{overflow-wrap:anywhere;font-family:ui-monospace,Consolas,monospace}.formula{min-height:92px}
.badge{font-size:12px;color:#235f50;background:#e9f4ef;border-radius:12px;padding:3px 9px;display:inline-block}.bad{color:#933c2a;background:#f9ece7}.selected{border:2px solid var(--blue)}.outcome{border-top:2px solid #a697b7;padding-top:10px;margin-top:15px}summary{cursor:pointer;font-weight:600;font-size:13px}details{margin-top:12px}.hash{font-size:12px;overflow-wrap:anywhere}.footer{font-size:12px;color:var(--muted)}
@media(max-width:950px){.arms{grid-template-columns:1fr}.formula{min-height:0}}@media(max-width:600px){main{padding:24px 14px}.card{padding:16px}}
</style></head><body><main>
<header><div class="eyebrow">AlphaResearch-RL · Astra development experiment</div><h1>Does financial feedback improve agentic research?</h1>
<p class="lede">Inspect all 180 recorded proposals, the information each actor could see, and the 30 selections frozen before assessment. Three conditions share six proposals and the same final selector.</p>
<p class="note">Requested model: gpt-6-astra · ultra reasoning · default service tier. Recorded configuration is not an attestation of backend weights.</p></header>
<section class="card"><h2>Complete results, fixed denominator</h2>
<div class="callout">These ten half-year periods from 2020–2024 were already development data. Results are descriptive, with one trajectory per condition and period. They do not establish market generalization, profitable alpha, or Astra weight training.</div>
<div class="scroll"><table><thead><tr><th>Condition</th><th>Periods</th><th>Valid outcomes</th><th>Mean utility</th><th>Validity p</th><th>Predictive q</th></tr></thead><tbody id="armSummary"></tbody></table></div>
<p class="note">Mean utility = −1.06 + p + q, where p is the valid fraction and q is the sum of valid oriented future IC divided by all ten periods. Each valid outcome has utility IC − 0.06; invalid outcomes retain −1.06. The 0.06 is abstract search cost, not trading cost.</p>
<div class="scroll"><table><thead><tr><th>Contrast</th><th>Mean utility difference</th><th>Validity contribution</th><th>Predictive contribution</th></tr></thead><tbody id="contrasts"></tbody></table></div>
<p class="note">Primary contrast: full feedback minus validity only. The other two contrasts are also shown. Ten paired periods, five year averages and 180 decisions are not independent market replications.</p></section>
<section class="card"><h2>Follow the same decision across all three conditions</h2>
<p>All conditions start with the same two historical probes. Later, full feedback receives financial scores; validity only receives grammar and duplicate flags; withheld feedback receives an attempt acknowledgment. The common selector privately uses all eligible historical scores in every condition.</p>
<div class="controls"><label>Development period<select id="task" aria-label="Development period"></select></label><label>Proposal attempt<select id="attempt" aria-label="Proposal attempt"></select></label></div>
<div class="arms" id="arms"></div>
<details><summary>Common initial evidence for this period</summary><pre id="initial"></pre></details>
<p class="note">Public hypotheses and revision notes are saved model outputs, not authenticated hidden reasoning or proof that feedback caused a decision. Assessment is displayed separately below each selection and was never available to the actor.</p></section>
<section class="card"><h2>Every paired period and year</h2><div class="scroll"><table><thead><tr><th>Period</th><th>Full − validity</th><th>Full − withheld</th><th>Validity − withheld</th></tr></thead><tbody id="periods"></tbody></table></div>
<h3 style="margin-top:22px">Five year averages</h3><div class="scroll"><table><thead><tr><th>Year</th><th>Full − validity</th><th>Full − withheld</th><th>Validity − withheld</th></tr></thead><tbody id="years"></tbody></table></div></section>
<section class="card"><h2>All proposals remain accessible</h2><p class="note">All 180 records are retained below, including malformed, unusable and duplicate proposals if present. Selectors use the greatest absolute usable historical feedback IC, with earliest-attempt ties.</p>
<details><summary>Show all 180 proposals and statuses</summary><div class="scroll"><table><thead><tr><th>Period / condition / attempt</th><th>Grammar</th><th>Duplicate</th><th>Feedback usable</th><th>Selected</th><th>Expression</th></tr></thead><tbody id="allProposals"></tbody></table></div></details></section>
<section class="card"><h2>Reported resource use and provenance</h2><div class="scroll"><table><thead><tr><th>Condition</th><th>Input tokens</th><th>Output tokens</th><th>Reasoning tokens</th><th>Sum of call seconds</th></tr></thead><tbody id="usage"></tbody></table></div>
<p class="note">Token fields are reported separately. Reasoning tokens are not added to output tokens. Sum of call durations is not concurrent wall-clock time. Matching supplied prompts does not prove identical hidden host context or compute.</p>
<p class="hash" id="freeze"></p><details><summary>Replay verification, hashes and missing usage fields</summary><pre id="verification"></pre></details>
<p class="note">The builder requires complete structural replay and saved assessment arithmetic verification. It does not rerun market calculations or recover private raw CLI streams. Shared filesystem execution was not an adversarial read-access sandbox; recorded streams were required to contain no tool events.</p></section>
<p class="footer">Self-contained HTML · no remote scripts, fonts, APIs, models or data fetches · model text is rendered as text.</p>
</main><script id="astra-data" type="application/json">__ASTRA_DATA__</script><script>
'use strict';
const data=JSON.parse(document.getElementById('astra-data').textContent),byId=id=>document.getElementById(id),put=(id,value)=>{byId(id).textContent=value;};
const arms=['full_feedback','validity_only','withheld_feedback'],names={full_feedback:'Full feedback',validity_only:'Validity only',withheld_feedback:'Withheld feedback'},contrasts=['full_minus_validity','full_minus_withheld','validity_minus_withheld'];
const contrastNames={'full_minus_validity':'Full − validity · primary','full_minus_withheld':'Full − withheld','validity_minus_withheld':'Validity − withheld'},pretty=value=>JSON.stringify(value,null,2),fmt=value=>value===null||value===undefined?'unavailable':Number(value).toFixed(6);
function el(tag,text,cls){const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(cls)node.className=cls;return node;}
function row(id,values){const tr=el('tr');for(const value of values)tr.appendChild(el('td',value));byId(id).appendChild(tr);}
function option(id,value,text){const node=el('option',text);node.value=value;byId(id).appendChild(node);}
function detail(parent,title,value){const node=el('details');node.append(el('summary',title),el('pre',pretty(value)));parent.appendChild(node);}
for(const task of [...new Set(data.submissions.episodes.map(e=>e.task_id))])option('task',task,task);
for(let i=1;i<=6;i++)option('attempt',String(i),'Attempt '+i+' / 6');
for(const arm of arms){const s=data.assessment.arm_summaries[arm];row('armSummary',[names[arm],s.task_count,s.valid_assessment_count,fmt(s.mean_utility),fmt(s.validity_fraction_p),fmt(s.predictive_contribution_q)]);const u=data.verification.usage_by_arm[arm],tokens=k=>u.token_fields[k].complete_sum??'incomplete';row('usage',[names[arm],tokens('input_tokens'),tokens('output_tokens'),tokens('reasoning_output_tokens'),fmt(u.elapsed_seconds.total)]);}
for(const key of contrasts){const c=data.assessment.contrasts[key];row('contrasts',[contrastNames[key],fmt(c.mean_utility_difference),fmt(c.validity_contribution),fmt(c.predictive_contribution)]);}
for(const p of data.assessment.paired)row('periods',[p.task_id,...contrasts.map(key=>fmt(p[key]))]);
for(const y of data.assessment.year_averages)row('years',[y.year,...contrasts.map(key=>fmt(y[key]))]);
for(const episode of data.submissions.episodes)for(const r of episode.submission.records)row('allProposals',[episode.task_id+' / '+names[episode.arm]+' / '+r.attempt,r.canonical_ast!==null?'valid':'invalid',String(r.canonical_duplicate),r.feedback===null?'unavailable':String(r.feedback.usable),String(episode.submission.selection?.attempt===r.attempt),r.packet?.expression??r.raw_response]);
function update(){
 const task=byId('task').value,attempt=Number(byId('attempt').value);byId('arms').replaceChildren();
 for(const arm of arms){const episode=data.submissions.episodes.find(e=>e.task_id===task&&e.arm===arm),s=episode.submission,r=s.records[attempt-1],selection=s.selection,selected=selection?.attempt===attempt;
  const card=el('article',undefined,'arm'+(selected?' selected':''));card.appendChild(el('h3',names[arm]));card.appendChild(el('span',selected?'Selected after all six proposals':'Proposal '+attempt,'badge'));
  card.appendChild(el('pre',r.packet?.expression??r.raw_response,'formula'));card.appendChild(el('p','Hypothesis: '+(r.packet?.hypothesis??'No valid packet.')));card.appendChild(el('p','Revision: '+(r.packet?.revision??'No valid packet.')));
  card.appendChild(el('h3','Feedback delivered after this proposal'));card.appendChild(el('pre',pretty(r.visible_feedback)));
  detail(card,'Permitted history before this proposal',data.permitted_histories[task+'/'+arm][attempt-1]);
  detail(card,'Selector evidence · may be hidden from this actor',{feedback:r.feedback,canonical_ast:r.canonical_ast,canonical_duplicate:r.canonical_duplicate,failure_code:r.failure_code});
  detail(card,'Saved raw response and prompt hash',{raw_response:r.raw_response,prompt_sha256:r.prompt_sha256});detail(card,'Recorded transport and usage',episode.transport_summaries[attempt-1]);
  const outcome=data.assessment.results.find(x=>x.task_id===task&&x.arm===arm).outcome,box=el('div',undefined,'outcome');box.appendChild(el('h3','Frozen final selection'));
  box.appendChild(el('pre',selection===null?'No eligible selection':pretty(selection)));box.appendChild(el('p','Future outcome: '+outcome.status+' · utility '+fmt(outcome.reward)));box.appendChild(el('p','Oriented future IC: '+fmt(outcome.oriented_future_ic),'note'));detail(box,'Full saved future assessment · never actor-visible',outcome);card.appendChild(box);byId('arms').appendChild(card);
 }
 put('initial',pretty(data.submissions.episodes.find(e=>e.task_id===task).submission.initial_evidence));
}
byId('task').addEventListener('change',update);byId('attempt').addEventListener('change',update);update();
put('freeze','All pools frozen at '+data.submissions.frozen_utc+' · submissions SHA256 '+data.verification.submissions_sha256);put('verification',pretty(data.verification));
</script></body></html>'''


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--submissions", type=Path, required=True)
    parser.add_argument("--assessment", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("output already exists; choose a new path")
    payload = build_payload(args.contract, args.submissions, args.assessment, source_root=args.source_root)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(render(payload))


if __name__ == "__main__":
    main()
