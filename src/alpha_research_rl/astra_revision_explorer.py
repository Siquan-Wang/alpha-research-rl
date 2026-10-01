"""Deterministic offline view of complete, saved-replay-verified revision evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from . import astra_pool_diagnosis as saved
from . import astra_revision_core as core
from . import astra_revision_study as study


def build_payload(*, source_root, report_path=None):
    """Replay immutable captured evidence and embed precisely the verified bytes."""
    root = Path(source_root).resolve()
    directory = study._execution(root)
    if not (directory / "COMPLETE.json").is_file() or (directory / ".execution-lock").exists():
        raise ValueError("explorer requires a complete, inactive revision study")
    report_path = root / study.RESULT_PATH if report_path is None else Path(report_path).resolve()
    report_relative = saved._relative(report_path, root)
    saved._path(root, report_relative)
    contract, _, history, captured = study._verified_contract(root)
    _, captured = study._verified_submissions(root, contract, history, captured)
    directories = [directory]
    execution_paths = []
    for path in sorted(directory.rglob("*")):
        relative = saved._relative(path, root)
        saved._path(root, relative)
        if path.is_symlink():
            raise ValueError("execution evidence cannot contain a link")
        if path.is_dir():
            directories.append(path)
        elif path.is_file():
            raw = path.read_bytes()
            if relative in captured and captured[relative] != raw:
                raise ValueError("execution evidence changed during capture")
            captured[relative] = raw
            execution_paths.append(relative)
        else:
            raise ValueError("unexpected execution evidence type")
    report_raw = report_path.read_bytes()
    if report_relative in captured and captured[report_relative] != report_raw:
        raise ValueError("report changed during capture")
    captured[report_relative] = report_raw
    # Neither subsequent reads nor external changes can alter the verifier's
    # inputs or the exact report and prompt text later embedded in the page.
    with tempfile.TemporaryDirectory(prefix="astra-revision-view-") as temporary:
        snapshot = Path(temporary)
        for path in directories:
            saved._path(snapshot, saved._relative(path, root)).mkdir(parents=True, exist_ok=True)
        for relative, raw in captured.items():
            path = saved._path(snapshot, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        verification = study.replay_revision_study(source_root=snapshot, report_path=snapshot / report_relative)
    return payload_from_verified_records(
        contract, report_raw, verification, execution_file_count=len(execution_paths),
        renderer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    )


def payload_from_verified_records(contract, report_raw, verification, *, execution_file_count, renderer_sha256):
    """Package already verified records entirely in memory; perform no I/O.

    Callers must bind the contract and report to saved replay's exact hashes.
    The builder does so through its immutable snapshot; the public verifier uses
    its captured contract/report bytes and checks the returned replay identities.
    """
    if verification["report_sha256"] != hashlib.sha256(report_raw).hexdigest():
        raise ValueError("captured report differs from saved replay's verified bytes")
    if type(execution_file_count) is not int or execution_file_count < 0:
        raise ValueError("invalid captured execution file count")
    contexts = {}
    for task in core.TASK_IDS:
        state = contract["states"][task]
        contexts[task] = {"baseline": state["baseline"], "prefix": state["prefix"], "prompts": {}}
        for condition in core.CONDITIONS:
            prompt = core.prompt(state, condition)
            contexts[task]["prompts"][condition] = {
                "text": prompt, "sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            }
    return {
        "schema": "astra-revision-explorer-payload-v1", "verification": verification,
        "report_json": report_raw.decode("utf-8"), "report_sha256": hashlib.sha256(report_raw).hexdigest(),
        "report_bytes": len(report_raw), "contexts": contexts,
        "captured_execution_file_count": execution_file_count,
        "renderer_sha256": renderer_sha256,
    }


def render(payload):
    """Render a verified payload without interpreting any evidence as markup."""
    if (payload.get("schema") != "astra-revision-explorer-payload-v1"
            or payload.get("verification", {}).get("status") != "SAVED_REVISION_VERIFIED"):
        raise ValueError("saved revision verification is required")
    report_raw = payload["report_json"].encode("utf-8")
    actual_hash = hashlib.sha256(report_raw).hexdigest()
    if (payload["report_sha256"] != actual_hash or payload["verification"]["report_sha256"] != actual_hash
            or payload["report_bytes"] != len(report_raw)):
        raise ValueError("payload report byte identity differs")
    report = saved._read(report_raw)
    if (report.get("status") != "COMPLETE_MATCHED_PREFIX_DEVELOPMENT"
            or [(row["task_id"], row["generator"], row["repetition"]) for row in report["rows"]]
            != list(core.SLOT_ORDER) or set(payload["contexts"]) != set(core.TASK_IDS)):
        raise ValueError("complete fixed revision population is required")
    for task in core.TASK_IDS:
        for condition in core.CONDITIONS:
            prompt = payload["contexts"][task]["prompts"][condition]
            if hashlib.sha256(prompt["text"].encode("utf-8")).hexdigest() != prompt["sha256"]:
                raise ValueError("actor prompt byte identity differs")
    serialized = json.dumps(payload, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
    for character, escaped in (("&", "\\u0026"), ("<", "\\u003c"), (">", "\\u003e")):
        serialized = serialized.replace(character, escaped)
    return TEMPLATE.replace("__REVISION_DATA__", serialized)


TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Astra matched-prefix study · complete development evidence</title><style>
:root{color-scheme:light;--ink:#20323e;--muted:#586b76;--line:#d5dfe5;--accent:#315e82;--warn:#6b4378;--bg:#f3f6f8}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 system-ui,Segoe UI,sans-serif}main{max-width:1450px;margin:auto;padding:32px 24px 60px}h1{font-size:clamp(29px,4vw,43px);line-height:1.2;margin:10px 0 16px}h2{font-size:23px;margin:0 0 10px}h3{font-size:17px;margin:18px 0 8px}p{margin:8px 0}.eyebrow{font-size:12px;color:var(--accent);letter-spacing:1.1px;font-weight:750;text-transform:uppercase}.lede{font-size:17px;max-width:1100px;color:var(--muted)}.card{background:white;border:1px solid var(--line);border-radius:12px;padding:23px;margin:20px 0}.note{font-size:13px;color:var(--muted)}.callout{padding:13px 17px;background:#f3edf6;border-left:3px solid var(--warn);margin:16px 0}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px}th,td{padding:10px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}th{background:#f2f6f8;color:var(--muted)}th:first-child,td:first-child{text-align:left}.formula{font-family:ui-monospace,Consolas,monospace;min-width:235px;max-width:430px;white-space:normal;text-align:left;overflow-wrap:anywhere}.wrap{white-space:normal;min-width:150px;max-width:330px;text-align:left;overflow-wrap:anywhere}.four{white-space:pre-line;text-align:left;min-width:280px;font-family:ui-monospace,Consolas,monospace;font-size:12px}.controls{display:flex;flex-wrap:wrap;gap:18px;margin:15px 0}label{font-size:13px;font-weight:650}select{display:block;min-width:195px;margin-top:5px;padding:9px;border:1px solid #aabac5;border-radius:6px;font:inherit;background:white;color:var(--ink)}select:focus,summary:focus{outline:2px solid #79a6c5;outline-offset:2px}details{margin-top:15px}summary{cursor:pointer;font-size:13px;font-weight:650}pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:420px;overflow:auto;padding:14px;background:#f4f7f9;border:1px solid var(--line);border-radius:6px;font:12px/1.6 ui-monospace,Consolas,monospace}.prompts{display:grid;grid-template-columns:1fr 1fr;gap:16px}.hash{font-size:12px;overflow-wrap:anywhere}.pass{color:#28624c}.fail{color:#7b4554}.footer{font-size:12px;color:var(--muted)}@media(max-width:700px){main{padding:23px 12px}.card{padding:16px}.prompts{grid-template-columns:1fr}}
</style></head><body><main>
<header><div class="eyebrow">One-step matched-prefix study · all development evidence</div>
<h1>Does numerical feedback improve the next proposal?</h1>
<p class="lede">Two hosted conditions share the same historical prefix. Truthful reveals its candidate metrics; masked replaces only those bundles with null. Three fixed cheap generators provide references. Every charged slot, including failed proposals and negative outcomes, remains visible.</p>
<div class="callout">These are reused 2020–2024 development periods, not a fresh holdout. One-step revisions do not establish long-horizon discovery, original economic signals, profitable alpha or Astra weight training. Common initial probes can reveal some masked feedback indirectly.</div>
<p class="note" id="population"></p></header>
<section class="card"><h2>All five generators, fixed denominators</h2>
<div class="scroll"><table><thead><tr><th>Generator</th><th>Slots</th><th>Valid Q</th><th>Failed Q</th><th>Mean Q</th><th>Validity p</th><th>Predictive q</th><th>Valid-only IC</th><th>Valid-only n</th><th>Selected mean Q</th><th>Mean G</th><th>Mean net gain</th></tr></thead><tbody id="summaries"></tbody></table></div>
<p class="note">Q = fixed-direction future IC for a valid candidate; otherwise Q = −1. Mean Q = −1 + p + q, where q includes the all-slot denominator. G is the future Q of the fixed historical selector minus baseline Q. A duplicate retains its Q; copy has G = 0. Terminal cost is 0.03, baseline cost 0.02 and incremental cost 0.01, so net gain = G − 0.01. The four draws are separate branches, never a best-of-four search.</p>
<h3>Truthful contrasts and validity decomposition</h3>
<div class="scroll"><table><thead><tr><th>Truthful minus</th><th>ΔQ</th><th>Δp</th><th>Δq</th><th>ΔG</th><th>Δ selected Q</th><th>Δ selected p</th><th>Δ selected q</th></tr></thead><tbody id="contrasts"></tbody></table></div>
<p class="note" id="mcse"></p><p class="note">Conditional generation MCSE uses within-state sample variation across four hosted calls. It assumes independent draws, which is unverified; it is not uncertainty across market periods or a generalization guarantee. Rounded cells are for display; all raw values remain below.</p></section>
<section class="card"><h2>Inspect one state and generator</h2>
<div class="controls"><label>Development period<select id="task" aria-label="Development period"></select></label><label>Generator<select id="generator" aria-label="Generator"></select></label></div>
<p class="note" id="state-summary"></p>
<div class="scroll"><table><thead><tr><th>Draw</th><th>Proposed factor</th><th>Lag</th><th>Packet / DSL / lag / eligible</th><th>Historical IC</th><th>Historically usable</th><th>Fixed direction</th><th>Duplicates: prefix / new bank</th><th>Selector choice</th><th>Future status / reason</th><th>Candidate Q</th><th>Selected Q</th><th>G</th><th>Outcome provenance</th></tr></thead><tbody id="candidates"></tbody></table></div>
<p class="note">Study eligibility requires the original packet and DSL checks and structural dependency lag ≤ 60. Eligibility alone does not establish usable feedback or future validity. Any failed candidate keeps Q = −1; the selector may still retain the valid prefix baseline. Direction and selection use historical feedback only. No future value is shown in the actor prompt.</p>
<details><summary>Two original prefix candidates and fixed historical winner</summary><pre id="prefix-evidence"></pre></details>
<h3>Public proposal explanations</h3><div class="scroll"><table><thead><tr><th>Draw</th><th>Hypothesis</th><th>Revision</th></tr></thead><tbody id="explanations"></tbody></table></div>
<p class="note">These are the recorded proposal's own explanations, not independently verified reasons for its outcome. Short previews disclose truncation; complete text is in the retained rows below.</p>
<details><summary>Four full rows, raw responses and historical selector evidence</summary><pre id="candidate-evidence"></pre></details>
<details><summary>Candidate, selected and baseline outcome/cache provenance</summary><pre id="candidate-provenance"></pre></details>
<h3>Matched actor context for this period</h3>
<p class="note">Exact prompts are identical across the four draws within each hosted condition. Their only observation difference is the two candidate-feedback bundles. Cheap controls receive no hosted call. The baseline shown above is diagnostic metadata, not an extra actor-visible field.</p>
<div class="prompts"><details><summary>Truthful: exact actor prompt</summary><p class="hash" id="truthful-hash"></p><pre id="truthful-prompt"></pre></details><details><summary>Masked: exact actor prompt</summary><p class="hash" id="masked-hash"></p><pre id="masked-prompt"></pre></details></div></section>
<section class="card"><h2>Every state × generator, with all four raw Q/G pairs</h2>
<div class="scroll"><table><thead><tr><th>Period / generator</th><th>Slots</th><th>Valid / failed Q</th><th>Mean Q</th><th>Mean G</th><th>Draw 1–4: raw Q and G</th></tr></thead><tbody id="states"></tbody></table></div>
<h3>All five years</h3><div class="scroll"><table><thead><tr><th>Year / generator</th><th>Periods</th><th>Slots</th><th>Valid / failed Q</th><th>Mean Q</th><th>Mean G</th></tr></thead><tbody id="years"></tbody></table></div>
<details><summary>All period/year contrasts, decompositions and hosted sample deviations</summary><pre id="period-evidence"></pre></details>
<details><summary>All 200 charged slots</summary><div class="scroll"><table><thead><tr><th>Period / generator / draw</th><th>Factor</th><th>Eligible</th><th>Historical usable</th><th>Future status</th><th>Q</th><th>Selected Q</th><th>G</th><th>Net gain</th></tr></thead><tbody id="all-slots"></tbody></table></div></details></section>
<section class="card"><h2>Registered allocation checklist</h2>
<p class="note">Each requirement is a strict comparison of unrounded saved values. Every condition must pass. Passing is a point-estimate engineering criterion, not a statistical claim or permission for an automatic next experiment.</p>
<div class="scroll"><table><thead><tr><th>Requirement</th><th>Left</th><th>Right</th><th>Saved result</th></tr></thead><tbody id="allocation"></tbody></table></div><p id="allocation-summary"></p>
<details><summary>Call accounting, token missingness and AST/cache duplicate counts</summary><pre id="accounting"></pre></details>
<p class="note">Cache reuse reduces evaluations, not the 200-slot denominator. Distinct ASTs do not prove distinct financial signals. Original proposal spelling and the expression actually evaluated remain separate. Reasoning and output tokens are reported separately; their containment is not assumed.</p>
<p class="hash" id="identity"></p><details><summary>Saved replay verification and renderer identity</summary><pre id="verification"></pre></details><details><summary>Exact captured report JSON</summary><pre id="raw-report"></pre></details>
<p class="note">This page was built from immutable captured public bytes and complete saved-driver replay. It checks recorded structure and arithmetic without recomputing market scores. It does not attest hidden hosted context or model identity. All saved limitations are retained below.</p><pre id="limits"></pre></section>
<p class="footer">Self-contained HTML · no remote scripts, fonts, model calls, market-data reads or network requests · evidence text is never interpreted as markup.</p>
</main><script id="revision-data" type="application/json">__REVISION_DATA__</script><script>
'use strict';
const envelope=JSON.parse(document.getElementById('revision-data').textContent),data=JSON.parse(envelope.report_json),analysis=data.analysis;
const generators=['truthful','masked','copy','window_edit','grammar_draw'],names={truthful:'Truthful feedback',masked:'Masked feedback',copy:'Copy baseline',window_edit:'Fixed window edit',grammar_draw:'Seeded grammar draw'};
const byId=id=>document.getElementById(id),put=(id,value)=>{byId(id).textContent=value;},pretty=value=>JSON.stringify(value,null,2),fmt=value=>value===null||value===undefined?'unavailable':Number(value).toFixed(6),raw=value=>value===null||value===undefined?'unavailable':String(value),yes=value=>value?'yes':'no';
const keys=new Map(data.keys.map(value=>[value.key.key_id,value]));
function el(tag,text,cls){const node=document.createElement(tag);if(text!==undefined)node.textContent=String(text);if(cls)node.className=cls;return node;}
function row(id,values,classes={}){const node=el('tr');values.forEach((value,index)=>node.appendChild(el('td',value,classes[index])));byId(id).appendChild(node);}
function option(id,value,text){const node=el('option',text);node.value=value;byId(id).appendChild(node);}
function future(value){if(value.candidate_key_id===null)return 'not assessed: '+(value.adjudication.failure_code??'historically unusable');const outcome=keys.get(value.candidate_key_id).raw_evaluator_outcome;return outcome.status+(outcome.reason?' / '+outcome.reason:'');}
function short(value){if(value===null||value===undefined)return 'No valid packet';const chars=Array.from(value);return chars.length<=280?value:chars.slice(0,280).join('')+' [truncated; full text below]';}
put('population',data.population.new_slots+' charged slots · '+data.population.states+' fixed historical states · 5 generators × 4 draws · '+data.call_accounting.hosted_calls+' hosted calls · '+data.call_accounting.new_future_calls+' new future evaluations · '+data.call_accounting.reused_future_keys+' reused future keys.');
for(const name of generators){const summary=analysis.generators[name],q=summary.candidate;row('summaries',[names[name],q.denominator,q.valid_count,q.invalid_count,fmt(q.mean_Q),fmt(q.validity_p),fmt(q.predictive_q),fmt(q.conditional_valid_mean_ic),q.conditional_valid_count,fmt(summary.selected.mean_Q),fmt(summary.mean_G),fmt(summary.mean_incremental_net_gain)]);}
for(const name of generators.slice(1)){const value=analysis.contrasts['truthful_minus_'+name];row('contrasts',[names[name],...['Q_difference','validity_contribution','predictive_contribution','G_difference','selected_Q_difference','selected_validity_contribution','selected_predictive_contribution'].map(field=>fmt(value[field]))]);}
put('mcse','Primary ΔQ = '+raw(analysis.primary_truthful_minus_masked_Q)+'; secondary ΔG = '+raw(analysis.secondary_truthful_minus_masked_G)+'; conditional generation MCSE for ΔQ = '+raw(analysis.conditional_generation_mc_se)+'.');
for(const state of analysis.states){option('task',state.task_id,state.task_id);for(const name of generators){const summary=state.generators[name],q=summary.candidate,values=state.repeated_values[name];row('states',[state.task_id+' / '+names[name],q.denominator,q.valid_count+' / '+q.invalid_count,fmt(q.mean_Q),fmt(summary.mean_G),values.candidate_Q.map((value,index)=>'r'+(index+1)+' Q='+raw(value)+'; G='+raw(values.G[index])).join('\n')],{5:'four'});}}
for(const name of generators)option('generator',name,names[name]);
for(const year of analysis.years)for(const name of generators){const summary=year.generators[name],q=summary.candidate;row('years',[year.year+' / '+names[name],year.period_count,q.denominator,q.valid_count+' / '+q.invalid_count,fmt(q.mean_Q),fmt(summary.mean_G)]);}
for(const value of data.rows)row('all-slots',[value.task_id+' / '+names[value.generator]+' / '+value.repetition,value.adjudication.packet?.expression??'No valid expression',yes(value.adjudication.eligible),yes(value.adjudication.historically_usable),future(value),raw(value.candidate_Q),raw(value.selected_Q),raw(value.G),raw(value.incremental_net_gain)],{1:'formula',4:'wrap'});
function update(){
 const task=byId('task').value,name=byId('generator').value,rows=data.rows.filter(value=>value.task_id===task&&value.generator===name),context=envelope.contexts[task],baseline=context.baseline;
 byId('candidates').replaceChildren();byId('explanations').replaceChildren();
 for(const value of rows){const a=value.adjudication;row('candidates',[value.repetition,a.packet?.expression??'No valid expression',raw(a.dependency_lag),[a.packet_valid,a.grammar_valid,a.within_dependency_limit,a.eligible].map(yes).join(' / '),fmt(a.feedback?.mean_ic),yes(a.historically_usable),a.orientation===null?'unavailable':a.orientation>0?'+1':'−1',yes(a.canonical_duplicate_with_prefix)+' / '+yes(value.canonical_duplicate_across_new_slots),a.selected_new?'New candidate (attempt 3)':'Prefix attempt '+a.selection.attempt,future(value),raw(value.candidate_Q),raw(value.selected_Q),raw(value.G),value.candidate_outcome_source],{1:'formula',3:'wrap',8:'wrap',9:'wrap',13:'wrap'});row('explanations',[value.repetition,short(a.packet?.hypothesis),short(a.packet?.revision)],{1:'wrap',2:'wrap'});}
 put('state-summary',task+' / '+names[name]+' · all 4 charged branches · Historical prefix winner: attempt '+baseline.attempt+', '+baseline.expression+' · historical IC '+fmt(baseline.feedback.mean_ic)+' · fixed direction '+(baseline.orientation>0?'+1':'−1')+' · baseline future Q '+raw(rows[0].baseline_Q));
 put('candidate-evidence',pretty(rows));const ids=new Set(rows.flatMap(value=>[value.candidate_key_id,value.baseline_key_id,value.selected_key_id]).filter(value=>value!==null));put('candidate-provenance',pretty(data.keys.filter(value=>ids.has(value.key.key_id))));
 put('prefix-evidence',pretty({prefix:context.prefix,historical_winner:baseline,selector_candidates:'Two prefix candidates plus one new candidate per branch.'}));
 for(const condition of ['truthful','masked']){put(condition+'-prompt',context.prompts[condition].text);put(condition+'-hash','Prompt SHA256 '+context.prompts[condition].sha256);}
}
byId('task').addEventListener('change',update);byId('generator').addEventListener('change',update);update();
const checks=analysis.allocation.strict_unrounded_inequalities;
for(const name of generators.slice(1))for(const [metric,field,key] of [['Mean candidate Q','mean_Q','Q'],['Predictive q','predictive_q','predictive_q'],['Mean selector G','mean_G','G']]){const left=field==='mean_G'?analysis.generators.truthful[field]:analysis.generators.truthful.candidate[field],right=field==='mean_G'?analysis.generators[name][field]:analysis.generators[name].candidate[field],pass=checks[key+'_truthful_exceeds_'+name];row('allocation',[metric+': truthful > '+names[name],raw(left),raw(right),pass?'PASS':'FAIL'],{3:pass?'pass':'fail'});}
row('allocation',['Mean truthful G > incremental cost',raw(analysis.generators.truthful.mean_G),'0.01',checks.mean_truthful_G_exceeds_incremental_cost?'PASS':'FAIL']);
put('allocation-summary','All registered point conditions pass: '+yes(analysis.allocation.all_point_conditions_pass)+'. Automatic next study authorized: '+yes(analysis.allocation.automatic_next_study_authorized)+'.');
put('period-evidence',pretty({states:analysis.states,years:analysis.years}));put('accounting',pretty({call_accounting:data.call_accounting,duplicates_and_cache:data.duplicate_and_cache_counts,provider_usage:data.provider_usage}));put('limits',pretty(data.limits));
put('identity','Exact report SHA256 '+envelope.report_sha256+' · '+envelope.report_bytes+' bytes · Contract SHA256 '+envelope.verification.contract_sha256+' · Submissions SHA256 '+envelope.verification.submissions_sha256);
put('verification',pretty({verification:envelope.verification,renderer_sha256:envelope.renderer_sha256,captured_execution_file_count:envelope.captured_execution_file_count}));put('raw-report',envelope.report_json);
</script></body></html>'''


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path.cwd())
    parser.add_argument("--report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root, output = args.source_root.resolve(), args.output.resolve()
    if args.output.exists():
        parser.error("output already exists; choose a new path")
    if any(output.is_relative_to(root / directory) for directory in (
            "artifacts", "results", "src", "tests", "scripts", "data", "models", study.TRANSPORT_DIRECTORY)):
        parser.error("output collides with an evidence or source directory")
    if args.report is not None and output == args.report.resolve():
        parser.error("output collides with the report")
    payload = build_payload(source_root=root, report_path=args.report)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(render(payload))


if __name__ == "__main__":
    main()
