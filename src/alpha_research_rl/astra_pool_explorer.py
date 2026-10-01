"""Self-contained, saved-replay-verified view of the post-hoc frozen-pool diagnosis."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from . import astra_pool_diagnosis as diagnosis


def build_payload(contract_path, execution_dir, report_path, *, source_root):
    """Validate immutable copies of all public evidence, then retain the exact report JSON."""
    root = Path(source_root).resolve()
    contract_path, execution_dir, report_path = map(Path, (contract_path, execution_dir, report_path))
    contract, _, _, captured = diagnosis._verified_contract(contract_path, root, verify_environment=False)
    expected_execution = diagnosis._path(root, contract["execution_directory"])
    if execution_dir.resolve() != expected_execution:
        raise ValueError("execution directory differs from the bound contract")
    diagnosis._execution_tree(expected_execution)
    if {p.name for p in expected_execution.iterdir()} != {
        "jobs", "request.json", "publication-receipt.json", "COMPLETE.json",
    }:
        raise ValueError("explorer requires completed evidence with no remaining execution lock")
    expected_jobs = {diagnosis._job_name(job) for job in contract["pending_jobs"]}
    jobs = expected_execution / "jobs"
    if (not jobs.is_dir() or {p.name for p in jobs.iterdir()} != expected_jobs
            or any(not p.is_dir() or p.is_symlink() for p in jobs.iterdir())):
        raise ValueError("explorer requires the entire completed job bank")
    execution_paths = [expected_execution / name for name in ("request.json", "publication-receipt.json", "COMPLETE.json")]
    for name in sorted(expected_jobs):
        directory = jobs / name
        if ({p.name for p in directory.iterdir()} != {"STARTED.json", "COMPLETED.json"}
                or any(not p.is_file() or p.is_symlink() for p in directory.iterdir())):
            raise ValueError("ambiguous or unexpected job evidence")
        execution_paths.extend(directory / name for name in ("STARTED.json", "COMPLETED.json"))
    for path in execution_paths:
        captured[diagnosis._relative(path, root)] = path.read_bytes()
    contract_relative = diagnosis._relative(contract_path, root)
    report_relative = diagnosis._relative(report_path, root)
    if report_relative not in captured:
        captured[report_relative] = report_path.read_bytes()
    report_raw = captured[report_relative]
    # Copy the complete path-bound public tree. Replay sees only these captured bytes,
    # including source files and the exact execution directory named in the contract.
    with tempfile.TemporaryDirectory(prefix="astra-pool-explorer-") as temporary:
        snapshot_root = Path(temporary)
        for relative, raw in captured.items():
            path = diagnosis._path(snapshot_root, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        verified = diagnosis.replay_pool_diagnosis(
            snapshot_root / contract_relative, snapshot_root / contract["execution_directory"],
            source_root=snapshot_root, report_path=snapshot_root / report_relative,
        )
    if hashlib.sha256(report_raw).hexdigest() != verified["report_sha256"]:
        raise ValueError("captured report differs from verified report bytes")
    return {
        "schema": "astra-pool-explorer-payload-v1", "verification": verified,
        "report_sha256": hashlib.sha256(report_raw).hexdigest(), "report_bytes": len(report_raw),
        "report_json": report_raw.decode("utf-8"),
        "captured_execution_file_count": len(execution_paths),
        "renderer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


def render(payload):
    serialized = json.dumps(payload, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
    for character, escaped in (("&", "\\u0026"), ("<", "\\u003c"), (">", "\\u003e")):
        serialized = serialized.replace(character, escaped)
    return TEMPLATE.replace("__POOL_DATA__", serialized)


TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Astra frozen-pool diagnosis · post-hoc evidence</title><style>
:root{color-scheme:light;--ink:#1d303d;--muted:#526572;--line:#d8e1e7;--blue:#235a88;--purple:#6a497f;--bg:#f2f5f8}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 system-ui,Segoe UI,sans-serif}
main{max-width:1390px;margin:auto;padding:34px 24px 60px}h1{font-size:clamp(29px,4vw,43px);line-height:1.18;margin:10px 0 18px}h2{font-size:23px;margin:0 0 12px}h3{font-size:18px;margin:16px 0 8px}p{margin:8px 0}.eyebrow{color:var(--purple);font-size:12px;letter-spacing:1.2px;font-weight:750;text-transform:uppercase}.lede{max-width:1100px;font-size:17px;color:var(--muted)}
.card{margin:20px 0;padding:24px;background:white;border:1px solid var(--line);border-radius:12px}.note{font-size:13px;color:var(--muted)}.callout{padding:13px 17px;background:#f4eef8;border-left:3px solid var(--purple);margin:15px 0}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:10px 11px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}th{background:#f3f6f8;color:var(--muted)}th:first-child,td:first-child{text-align:left}.formula-cell{white-space:normal;min-width:260px;max-width:510px;text-align:left;overflow-wrap:anywhere;font-family:ui-monospace,Consolas,monospace}.flags-cell{white-space:normal;min-width:180px;text-align:left}.oracle{color:var(--purple)}
.controls{display:flex;flex-wrap:wrap;gap:18px;margin:18px 0}label{font-size:13px;font-weight:650}select{display:block;min-width:200px;padding:9px;margin-top:5px;border:1px solid #a9bac6;border-radius:6px;font:inherit;color:var(--ink);background:white}select:focus,summary:focus{outline:2px solid #77aacc;outline-offset:2px}summary{cursor:pointer;font-weight:600;font-size:13px}details{margin-top:13px}pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:400px;overflow:auto;font:12px/1.6 ui-monospace,Consolas,monospace;padding:14px;background:#f4f7f9;border:1px solid var(--line);border-radius:6px}.hash{font-size:12px;overflow-wrap:anywhere}.footer{font-size:12px;color:var(--muted)}
@media(max-width:650px){main{padding:24px 12px}.card{padding:16px}.formula-cell{min-width:220px}}
</style></head><body><main>
<header><div class="eyebrow">Separate post-hoc diagnosis · frozen Astra candidate pools</div>
<h1>What was available inside the recorded pools?</h1>
<p class="lede">Compare three fixed selection rules with an unattainable hindsight oracle. Every original proposal remains visible, with its historical direction fixed before its future assessment.</p>
<div class="callout">This analysis was designed after the original selected outcomes were known. It uses the same 2020–2024 development periods and one realized trajectory per condition and period. The oracle is at least as good as original selection by construction; a positive gap is not evidence that a feasible selector could identify a better candidate.</div>
<p class="note" id="population"></p></header>
<section class="card"><h2>All conditions and all four selection rules</h2>
<p class="note">Original, first proposal and minimum-AST rules were fixed before the missing candidate outcomes were computed. The unattainable hindsight oracle chooses using future outcomes. All rules keep the original six-proposal cost of 0.06.</p>
<div class="scroll"><table><thead><tr><th>Condition / selector</th><th>Periods</th><th>Valid</th><th>Invalid</th><th>Mean utility</th><th>Validity p</th><th>Predictive q</th><th>Valid-only mean IC</th><th>Valid-only n</th></tr></thead><tbody id="summaries"></tbody></table></div>
<p class="note">Mean utility = −1.06 + p + q. Every valid slot has utility oriented future IC − 0.06; every invalid or unscorable slot retains −1.06. Conditional means display their valid-only denominator and never replace the all-period mean.</p>
<h3>Original-selector contrast and hindsight decomposition</h3>
<div class="scroll"><table><thead><tr><th>Contrast</th><th>ΔS: original</th><th>ΔO: unattainable hindsight</th><th>ΔR: selection gap</th><th>Identity residual</th></tr></thead><tbody id="contrasts"></tbody></table></div>
<p class="note">S is original selection utility, O is the unattainable hindsight ceiling and R = O − S. The identity ΔS = ΔO − ΔR is bookkeeping. ΔO is not a causal generation contribution.</p></section>
<section class="card"><h2>Inspect all six candidates in a fixed pool</h2>
<div class="controls"><label>Development period<select id="task" aria-label="Development period"></select></label><label>Condition<select id="arm" aria-label="Condition"></select></label></div>
<p class="note" id="pool-summary"></p>
<div class="scroll"><table><thead><tr><th>Attempt</th><th>Original expression</th><th>Historical IC</th><th>Fixed direction</th><th>Future oriented IC</th><th>Future status</th><th>Utility</th><th>AST nodes</th><th>Selector flags</th></tr></thead><tbody id="candidates"></tbody></table></div>
<p class="note">Historical feedback fixes direction (negative → −1, otherwise +1). Direction is never selected from future performance. An assessment failure stays in its slot and keeps its penalty; first/minimum-AST rules do not skip failed future outcomes.</p>
<details><summary>Full six-slot evidence and selector metadata</summary><pre id="pool-evidence"></pre></details>
<details><summary>Evaluation and cache provenance for these slots</summary><pre id="pool-provenance"></pre></details></section>
<section class="card"><h2>Every development period</h2>
<div class="scroll"><table><thead><tr><th>Period / condition</th><th>Original utility</th><th>First utility</th><th>Minimum-AST utility</th><th>Unattainable hindsight utility</th><th>Selection gap</th><th>First − original</th><th>Minimum AST − original</th></tr></thead><tbody id="periods"></tbody></table></div>
<h3>All five year averages</h3><div class="scroll"><table><thead><tr><th>Year / condition</th><th>Periods</th><th>Original utility</th><th>First utility</th><th>Minimum-AST utility</th><th>Unattainable hindsight utility</th><th>Selection gap</th></tr></thead><tbody id="years"></tbody></table></div>
<details><summary>All task/year contrasts and validity decompositions</summary><pre id="all-contrasts"></pre></details></section>
<section class="card"><h2>Every slot remains accessible</h2><p class="note">Cache reuse reduces evaluator calls, not the 180-slot denominator. Different canonical ASTs do not establish different economic signals. Original expression spellings and the expressions actually evaluated remain separate provenance fields.</p>
<details><summary>All 180 original candidate slots</summary><div class="scroll"><table><thead><tr><th>Period / condition / attempt</th><th>Original expression</th><th>Grammar valid</th><th>Within-episode AST duplicate</th><th>Fixed direction</th><th>Future status</th><th>Utility</th></tr></thead><tbody id="all-slots"></tbody></table></div></details>
<details><summary>Slot and unique-key validity denominators</summary><pre id="validity"></pre></details></section>
<section class="card"><h2>Recorded allocation rule and evidence</h2>
<p class="note">The full-feedback ceiling bounds selection within these exact pools and directions. It does not cover abstention, another generator, new trajectories or new periods. A positive ceiling is only hindsight headroom and authorizes no automatic next experiment.</p>
<pre id="allocation"></pre><p class="hash" id="identity"></p>
<details><summary>Saved replay verification and input identities</summary><pre id="verification"></pre></details>
<details><summary>Exact captured report JSON</summary><pre id="raw-report"></pre></details>
<p class="note">The page builder validates immutable copies of the complete public evidence. Saved replay checks structure, accounting and arithmetic; it does not recompute market scores, attest package binaries or prove hidden model context. This post-hoc result establishes no profitable alpha, fresh holdout performance, factor originality or Astra weight training.</p></section>
<p class="footer">Self-contained HTML · no remote scripts, fonts, APIs, model calls or market-data reads · text is displayed without interpreting it as markup.</p>
</main><script id="pool-data" type="application/json">__POOL_DATA__</script><script>
'use strict';
const envelope=JSON.parse(document.getElementById('pool-data').textContent),data=JSON.parse(envelope.report_json);
const arms=['full_feedback','validity_only','withheld_feedback'],names={full_feedback:'Full feedback',validity_only:'Validity only',withheld_feedback:'Withheld feedback'};
const selectors=['original','first','minimum_ast','oracle'],labels={original:'Original feedback selector',first:'First charged proposal',minimum_ast:'Minimum AST nodes',oracle:'Unattainable hindsight oracle'};
const contrasts=['full_minus_validity','full_minus_withheld','validity_minus_withheld'],contrastNames={full_minus_validity:'Full − validity',full_minus_withheld:'Full − withheld',validity_minus_withheld:'Validity − withheld'};
const byId=id=>document.getElementById(id),put=(id,value)=>{byId(id).textContent=value;},pretty=value=>JSON.stringify(value,null,2),fmt=value=>value===null||value===undefined?'unavailable':Number(value).toFixed(6),direction=value=>value===null?'unavailable':value>0?'+1':'−1';
function el(tag,text,cls){const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(cls)node.className=cls;return node;}
function row(id,values,classes={}){const tr=el('tr');values.forEach((value,index)=>tr.appendChild(el('td',value,classes[index])));byId(id).appendChild(tr);}
function option(id,value,text){const node=el('option',text);node.value=value;byId(id).appendChild(node);}
put('population',data.population.slot_count+' original slots · '+data.population.key_count+' task/AST/direction keys · '+data.call_accounting.reused_key_count+' reused keys · '+data.call_accounting.new_evaluator_calls_completed+' new CPU evaluations · '+data.call_accounting.model_calls+' new model calls.');
for(const arm of arms)for(const selector of selectors){const s=data.arm_summaries[arm].selectors[selector];row('summaries',[names[arm]+' / '+labels[selector],s.denominator,s.valid_count,s.invalid_count,fmt(s.mean_utility),fmt(s.validity_fraction_p),fmt(s.predictive_contribution_q),fmt(s.conditional_valid_mean_ic),s.conditional_valid_count],selector==='oracle'?{0:'oracle'}:{});}
for(const name of contrasts){const c=data.contrasts[name];row('contrasts',[contrastNames[name],fmt(c.delta_S),fmt(c.delta_O),fmt(c.delta_R),fmt(c.decomposition_residual)]);}
for(const p of data.paired)option('task',p.task_id,p.task_id);for(const arm of arms)option('arm',arm,names[arm]);
for(const pool of data.selector_rows)row('periods',[pool.task_id+' / '+names[pool.arm],...selectors.map(name=>fmt(pool.selectors[name].diagnosis.utility)),fmt(pool.selection_gap_R),fmt(pool.first_minus_original),fmt(pool.minimum_ast_minus_original)]);
for(const year of data.year_averages)for(const arm of arms){const s=year.arm_summaries[arm];row('years',[year.year+' / '+names[arm],s.selectors.original.denominator,...selectors.map(name=>fmt(s.selectors[name].mean_utility)),fmt(s.mean_selection_gap_R)]);}
for(const slot of data.slot_results)row('all-slots',[slot.task_id+' / '+names[slot.arm]+' / '+slot.attempt,slot.expression??'No valid expression',String(slot.canonical_ast!==null),String(slot.canonical_duplicate),direction(slot.orientation),slot.diagnosis.status,fmt(slot.diagnosis.utility)],{1:'formula-cell'});
function update(){
 const task=byId('task').value,arm=byId('arm').value,pool=data.selector_rows.find(p=>p.task_id===task&&p.arm===arm),slots=data.slot_results.filter(s=>s.task_id===task&&s.arm===arm);
 byId('candidates').replaceChildren();
 for(const slot of slots){const flags=selectors.filter(name=>pool.selectors[name].slot_id===slot.slot_id).map(name=>labels[name]);row('candidates',[slot.attempt,slot.expression??'No valid expression',fmt(slot.feedback?.mean_ic),direction(slot.orientation),fmt(slot.diagnosis.oriented_future_ic),slot.diagnosis.status,fmt(slot.diagnosis.utility),slot.ast_node_count??'unavailable',flags.length?flags.join(' · '):'None'],{1:'formula-cell',8:'flags-cell'});}
 put('pool-summary',task+' / '+names[arm]+' · '+slots.length+' charged slots retained · Original utility '+fmt(pool.S)+' · Unattainable hindsight utility '+fmt(pool.O)+' · Selection gap '+fmt(pool.selection_gap_R));
 put('pool-evidence',pretty({selector_metadata:pool,slots}));const keys=new Set(slots.map(s=>s.key_id).filter(key=>key!==null));put('pool-provenance',pretty(data.key_results.filter(record=>keys.has(record.key.key_id))));
}
byId('task').addEventListener('change',update);byId('arm').addEventListener('change',update);update();
put('all-contrasts',pretty({overall:data.contrasts,periods:data.paired,years:data.year_averages}));put('validity',pretty({slots:data.slot_validity,unique_keys:data.unique_key_validity}));put('allocation',pretty(data.allocation));
put('identity','Captured report SHA256 '+envelope.report_sha256+' · '+envelope.report_bytes+' bytes · Contract SHA256 '+envelope.verification.contract_sha256);
put('verification',pretty({verification:envelope.verification,inputs:data.inputs,renderer_sha256:envelope.renderer_sha256,captured_execution_file_count:envelope.captured_execution_file_count}));put('raw-report',envelope.report_json);
</script></body></html>'''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--execution-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("output already exists; choose a new path")
    output = args.output.resolve()
    if output.is_relative_to(args.execution_dir.resolve()) or output in {
        args.contract.resolve(), args.report.resolve(), Path(__file__).resolve(),
    }:
        parser.error("output collides with protected evidence")
    payload = build_payload(args.contract, args.execution_dir, args.report, source_root=args.source_root)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(render(payload))


if __name__ == "__main__":
    main()
