# Check the stopped scientific-decoder evidence

Run from a checkout containing the published evidence, with Python 3.11 or later:

```console
python scripts/check_scientific_decoder_stop.py
```

An optional `--root PATH` checks a copied public evidence tree. No packages, API credentials, private workspace, network access, or benchmark runtime are needed. The command prints JSON and exits zero only for `SAVED_STOP_VERIFIED`; missing, modified, or inconsistent evidence returns a nonzero exit. It writes no files.

The checker pins [the stopped result](../results/scientific_decoder_dev_v1.json) and [preflight manifest](../artifacts/scientific-decoder-dev-v1/preflight-manifest.json), checks all 36 snapshot files, the complete 40-file publication receipt map, and all 13 retained execution files. It verifies saved source and request identities, fixed training-coordinate order, worker metadata, all 192 requested row statuses, and the four-task accounting. The 13 upstream source payloads are hashed as bytes; they are never imported, executed, or interpreted as formulas. Neither the public snapshot nor its reconstruction instructions are executed.

The retained result is **incomplete target collection**, with 135 attempts, 134 finite values, one failure, and 121 of 256 planned slots unattempted. There were zero hosted calls and zero confirmation, model-prediction, or reference-prediction evaluations. Predictive scores remain null and allocation inequalities remain unevaluated. This is not a negative model-performance result.

The checker validates **saved provenance and counts**, not independent scientific reproduction. It does not fetch the publication URLs, reproduce the oracle values, prove that no unrecorded actions occurred, or attest a remote model/runtime. Timestamp checks establish consistency of the coordinator's recorded metadata; the worker files have no independent per-call timestamps. The saved conversion error combines several failure causes, so the checker does not diagnose which numerical cause occurred. Exact byte pins intentionally make this a checker for the stopped v1 evidence, not a general facility for accepting a changed study.

The focused [tests](../tests/test_scientific_decoder_stop.py) check real saved artifacts under import/network/process/write guards, altered source/request/receipt/result bytes, typed row and aggregate semantics, and unexpected inventory/path/JSON entries. These guards exercise the checker; they are not a security sandbox for arbitrary code. See the [result account](scientific-decoder-dev-results-v1.md) and [internal saved-evidence review](audits/scientific-decoder-dev-stop-review-v1.md) for interpretation.
