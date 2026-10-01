# Decoder development v1 stopped during target collection

**Outcome: incomplete target collection; no model comparison was run.** The
[prospective protocol](scientific-decoder-dev-plan-v1.md) was published at
[`3d818347`](https://github.com/Siquan-Wang/alpha-research-rl/commit/3d818347f286e15ce673f5814411f7d27261a026),
and all 40 required public files were anonymously byte-verified at
2026-10-01 17:01:31.675904 UTC before the coordinator invoked training-target
collection once. The original source, coordinate bank and stopping rule remain
unchanged.

| Fixed task | Planned training points | Attempted | Finite successes | Failed | Unattempted |
| --- | ---: | ---: | ---: | ---: | ---: |
| sound speed, medium v0 | 64 | 64 | 64 | 0 | 0 |
| sound speed, hard v1 | 64 | 64 | 64 | 0 | 0 |
| Bose–Einstein, medium v2 | 64 | 7 | 6 | 1 | 57 |
| Bose–Einstein, hard v0 | 64 | 0 | 0 | 0 | 64 |
| **Total** | **256** | **135** | **134** | **1** | **121** |

The seventh point of task 2 (zero-based index 6) received the retained worker code
`nonfinite_or_nonscalar_output`. This code combines several rejected return types
and nonfinite values; it does not establish a particular overflow, infinity or
NaN cause. No repeat query or hidden-formula inspection was used to obtain a more
specific diagnosis. The remainder of that task was explicitly marked unattempted;
the fourth task was never requested.

The fixed support was an adapted, prospectively chosen measurement domain, not an
upstream finite-domain guarantee. Source determinism and successful import did
not prove finite scalar outputs everywhere in that support. This failed readiness
check says that the declared target collection could not complete. It says
nothing about Astra's inference quality, the expression grammar's adequacy,
adaptive acquisition or financial prediction.

There were **zero hosted calls, zero confirmation-target evaluations, zero model
or reference prediction evaluations, and no predictive scores**. The allocation
inequalities were not evaluated; they are not reported as empirical failures of
a model. The version is stopped. No points were removed, ranges narrowed, tasks
replaced, grammar repaired, scores imputed or main-study calls allocated.

The [machine-readable stop record](../results/scientific_decoder_dev_v1.json)
binds the three original requests, all 192 retained row records, six empty worker
logs and the [preflight publication receipt](../artifacts/scientific-decoder-dev-v1/execution/publication-preflight.json).
The [execution directory](../artifacts/scientific-decoder-dev-v1/execution/)
contains their exact bytes. Local request/output file times corroborate the
coordinator's reported sequence, but worker records contain no independent
embedded per-call timestamps; the publication receipt is a coordinator-produced
verification record, not an external experiment attestation.

See the [internal saved-evidence audit](audits/scientific-decoder-dev-stop-review-v1.md)
for source/request binding and count checks. Reading these records does not run
an oracle. The original scoring script **does** call the benchmark and must not
be used as a saved-result viewer.
