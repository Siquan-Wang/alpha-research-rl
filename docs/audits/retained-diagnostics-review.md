# Retained diagnostics: independent source and evidence review

2026-10-01. Internal AI-assisted review found no blocking denominator,
arithmetic or lookahead issue in the saved-proposal diversity analysis or the
public diagnostic verifier. Source and the prewritten method were inspected
before reading the diversity result. The reviewer did not edit the analysis,
its tests or the verifier, run models, or construct new market labels/scores.

This review covers **diversity and verifier behavior**. The reliability
estimator's independent mathematical review is a separate contribution:
[reliability-analysis-review.md](reliability-analysis-review.md). Executing a
verifier that reproduces reliability JSON is not an additional independent
derivation of that estimator.

## Diversity checks

The source retains all 900 strict-parser slots and separates five policies,
true/exchanged evidence and stochastic/greedy decoding. Each overall stochastic
cell has 80 attempts; each greedy cell has ten. Every task cell has eight or one,
respectively. Invalid/unscorable attempts remain in those denominators.

Exact-string and canonical-AST entropy, effective number and concentration use
usable-proposal frequencies. An all-invalid cell returns null distribution
statistics. Exposure and membership provide both all-attempt and usable-only
denominators. Rank-equivalent exposure weights repeated proposal occurrences;
unique task/AST counts are separately labeled. The nearest-reference statistic
is `abs(mean daily Spearman)`, with the specified paired-cell and scored-date
support checks and `1e-10` tolerance. It describes empirical feedback-panel
equivalence, including fixed sign aliases, rather than universal algebraic
identity, independent factors or alpha discovery.

The following were independently checked against the saved evidence using
standard-library counters, AST parsing and explicit arithmetic, without calling
the diversity summarizer:

- All 20 overall policy/condition/decoding cells and all 200 task cells matched
  their attempt/usable counts and AST frequencies. Overall entropy,
  concentration, effective number, top-one exposure and occurrence-weighted
  rank-equivalence counts matched; task-level entropy also matched.
- The full archive contains 881 usable proposals and 19 failures. It has 13
  pooled exact strings and 13 ASTs, with 45 usable task/AST pairs. The 861
  near-equivalent occurrences and five non-equivalent task/AST pairs matched
  the result and discussion. Repeated exposure is not independent evidence.
- All five transfer-report and five rank-diagnostic byte hashes matched the
  saved result's identities. The original three rank files were independently
  compared as bytes with the public `dd2a2ec` release blobs and were unchanged.
  Duplicate task/AST rank evidence agreed. Two additional control files cover
  the previously missing pairs; no original file replacement was needed.
- The diagnostic join requires the pinned snapshot, complete matched task
  manifests, teacher references, support/count/tolerance fields, canonical AST
  membership in the declared source report and consistent duplicate evidence.
  The analysis adds no assessment scores or raw arrays. Stored strict status
  is used to identify usable proposals; no proposal is selected by future IC.

Three wording refinements were sent to the author and resolved: usable means
saved strict scorer `status == "ok"`, which requires both feedback and
assessment support; normalized entropy divides by the logarithm of observed
unique forms; the module describes *validated matched diagnostics*. Recording
byte hashes and checking task/formula correspondence is not independently
recomputing the rank evidence or authenticating unavailable execution details.
The result was regenerated after the source wording changed, and its saved
analysis-source SHA matched the updated module.

## Public verifier checks

The source of `scripts/replay_published_diagnostics.py` was reviewed, including
its shared `same` comparator and import guards. A fresh invocation completed
successfully and reported 12 reliability contrasts, 60 year omissions and all
900 diversity records. These counts derive from the reproduced objects rather
than a hardcoded successful printout.

The verifier checks transfer-report byte identities through the shared input
loader, recomputes and validates the original five-policy analysis, records its
actual input-analysis SHA, checks every declared rank file's actual bytes,
recomputes both complete result objects and checks each current analysis-module
SHA against the saved result. Dictionary keys, list lengths/order and
non-numeric types/values must agree; numeric fields use absolute and relative
tolerance `1e-12`. No aggregate-only shortcut omits task rows or source fields.

The standalone process installs the shared training-import blocker before
importing analysis modules. Python audit hooks reject `socket.connect` and
opens under repository `models/` and `data/raw/`. The executed analysis paths
read saved public reports and diagnostics, never call market evaluation or
generation, and do not load a training stack. These are execution checks, not
an OS sandbox or a general adversarial network/filesystem policy. The CPU CI
matrix invokes the same verifier after installing only the base/dev package;
this review's actual invocation was on the current Windows host.

## Validation and checked identities

The reviewer independently ran the 18 focused diversity tests: all passed.
The public verifier subsequently passed against the regenerated final JSON.
Full-repository test totals reported by root are not claimed as this reviewer's
own run.

| Artifact | SHA-256 at review |
| --- | --- |
| `proposal_diversity.py` | `165174c1e4cb0c757306632d02df1a55cd77de2257004fb11943b58d2a4b88ba` |
| `replay_published_diagnostics.py` | `835ce47bb4596ed48275cfdaaeeee3587e8791249f7074ff0b7e381322420721` |
| `financial_proposal_diversity_v1.json` | `159f70684d3539c63eecfdf189acdb162b782beafd0e52f6faef7ebae921c551` |

The evidence supports the descriptive accounting and its offline replay.
It does not establish new predictive benefit, causality, significance,
profitability, model retraining reproducibility or general sequential research
ability. See [the saved-proposal method and results](../proposal-diversity-v1.md)
and [the installed-package boundary check](installed-package-reproduction-review.md).

## 2026-10-01 addition: constructed mechanism gate replay

The verifier subsequently added a complete replay of the newly adopted
[exact query opportunity gate](../mechanism-gate-results-v1.md). This supersedes
the verifier SHA in the earlier table; that table remains the identity of the
diversity/reliability review snapshot, not the current verifier.

The added operation computes the gate report from the published plan and
compares its complete canonical JSON with the retained JSON, including all twelve query
plans, all response trees, exact numerator/denominator fields and source/plan
byte hashes. Sorted-key JSON comparison with `allow_nan=False` preserves scalar
types and all values without a numerical tolerance; object key order is immaterial.
It derives the displayed plan count from the recalculated object.
The existing financial diagnostic paths and their tolerance remain unchanged.
The operation runs inside the same import, raw-data/weights and network guards
and uses only standard-library finite arithmetic. It does not rescore market
data, run a model or load an adapter.

The reviewer checked this wrapper addition and the result document's claims,
then freshly invoked the verifier on the current Windows host: it passed with
12 reliability contrasts, 60 year omissions, 900 diversity records and 12 exact
query plans. The report correctly separates the deliberately engineered,
previously hand-calculated channel from a held-out discovery or learned policy.
The threshold is a task-quality rule; it does not authorize language-model
training or reopen the stopped financial/curriculum gates.

This reviewer authored the mechanism solver and its tests, so this addition is
**not an independent review of that solver**. Its separate source-first review
is recorded in [mechanism-gate-review.md](mechanism-gate-review.md).

At the final fresh invocation the verifier SHA was
`98bc1b33095059b9611dde39d986cb2670629f1d5f7e22720eb7b393162d619d`;
the retained gate JSON SHA was
`2392835610b41fe5c7da88954faa1996ac8239eaeed3b6a1c4b795f1b08a0cc5`.
One minor validation refinement was reported and resolved: ordinary Python
dictionary equality accepts scalar type aliases such as `True == 1` and
`81 == 81.0`. Root replaced that gate-only comparison with canonical JSON
comparison. The reviewer read the final operation and freshly reran the
complete verifier successfully after the correction. No remaining finding
changes the recorded rational values or the stated information boundary.
