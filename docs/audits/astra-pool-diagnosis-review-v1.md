# Astra frozen-pool diagnosis: independent implementation review

Date: 2026-10-01. **Status: PASS within the frozen-contract scope below; no
remaining implementation blocker found.** Root's actual preparation was
independently checked after the synthetic review. Public byte verification
and execution remain separate steps. No new financial scoring has been
performed by this reviewer.

## Review scope and authorship

This reviewer authored the earlier v1 study orchestrator and independently
critiqued the proposed next study. The reviewer did not author the new pool
diagnosis implementation or its protocol. This is an internal source-first
implementation review, not external peer review or an independent review of
the reviewer's own earlier orchestrator. Its statistical requirements were
discussed with the protocol and implementation authors before implementation.

The authorized write scope is this audit and, if useful, a separate synthetic
review-test module. Frozen v1 sources, protocol, contract, candidate bank and
assessment are outside that scope. No Git, model, tokenizer, market-data load,
or financial evaluator is used for this review; synthetic injected evaluators
may be used to verify the new orchestration.

## Saved-input prechecks completed

Static counting of the immutable candidate bank found 180 slots, 132 distinct
task/AST/feedback-direction keys, and 24 distinct keys covered by the original
30 selected assessment records. Thus the proposed additional scoring budget
is at most 108 calls. Candidate directions are 167 positive and 13 negative;
the new diagnostic must not infer them from assessment results.

Every repeated candidate key has exactly equal saved feedback. Every repeated
cached selected key has exactly equal saved financial content after excluding
literal expression spelling. The actual bank has no multiple-spelling alias
groups; alias provenance therefore requires a synthetic test rather than a
claim of real-input coverage.

All 30 original selected outcomes are valid and their oriented IC exceeds -1.
Consequently every actual pool has a valid member strictly above the invalid
penalty. The actual pool oracle must select a valid member; its uncosted
maximum can be interpreted as ordinary oriented IC. This does not generalize
to synthetic pools with no valid member or permit a valid-only denominator.

Before any new scoring, a separate AST-only script computed all 30 expected
original/first/minimum-AST selections, including minimum node counts. In fixed
task/arm order, canonical JSON of the projection `{task_id, arm,
original_attempt, first_attempt, minimum_ast_attempt, minimum_ast_nodes}` has
SHA256 `daff1d71da70aa1a9b21de8551bb5388012446e9f6ccd8f6ad71384d29ad98a0`.
This provides an independent static target for the prepared selector table;
it uses no assessment metric to select a candidate.
The completed implementation's `_tables` output was then checked against this
independent target using only the actual saved JSON: the projection hash and
all population counts agree, with 108 pending jobs and zero new evaluator
calls. No market array or task was constructed for this check.

## Requirements resolved before source review

- The analysis is a new explicitly post-hoc version. Original v1 assessment
  remains its 30 registered calls and all original artifacts stay immutable.
- Missing or changed historical feedback, direction, support or metadata is
  an integrity failure, not an ordinary new invalid candidate.
- A legitimate insufficient-assessment-support result retains the exact saved
  historical fields and has status `unscorable`. A caught future-side invalid
  result must retain those fields, use `invalid_expression`, and have absent
  assessment and absent oriented IC. A failed status with usable assessment
  cannot be accepted. The frozen scorer's reason may collapse numerical and
  other caught future-side exceptions; it is not a causal explanation.
- Each scoring attempt must have a durable exclusive STARTED record before
  calling its evaluator and a validated COMPLETED record before the next job.
  Explicit continuation may reuse only a clean completed prefix. An ambiguous
  STARTED, failed or corrupted attempted job blocks that version. Completed
  diagnoses are replay-only. Concurrent executors require an exclusive claim.
- Cached outcomes retain the spelling actually evaluated, separate from the
  original candidate-slot spelling. Canonical alias reuse must not relabel an
  old result as if another expression string had been evaluated.
- The first-slot reference never skips a bad outcome. Minimum AST complexity
  uses the protocol's explicit eligibility set and earliest ties. Oracle
  maxima include failure penalties. Every arm aggregate retains ten tasks.
- For selected utility S, oracle O and regret R=O-S, every arm comparison must
  satisfy the exact saved-arithmetic decomposition: delta S = delta O - delta R.
  Oracle headroom is hindsight, not an attainable selector or learned policy.

## Source and adversarial validation

The complete draft protocol `docs/astra-pool-diagnosis-plan-v1.md` has been
read. No pre-score design blocker was found: it states separate provenance,
production population checks, exact reuse, strict future-failure fields,
fixed selectors, all-task denominators, signed decomposition, exclusive
execution and continuation rules, and bounded oracle interpretation. This
judgment concerns the protocol, not its forthcoming implementation.

The landed metric/outcome/cache helpers were reviewed before the execution
state machine was complete. The final separate review test module has **27
passing artificial cases** (9.25 seconds). The author's **17 artificial cases**
were also independently rerun against the final source and passed in 18.59
seconds. Thus 44 distinct cases were executed in these two final runs; earlier
overlapping runs are not additional cases. Source and both test modules are
Ruff-clean. The independent tests cover both signs of
future IC under a fixed negative historical direction, exact historical drift
including a one-ULP change, Boolean/tie metadata, future failure versus missing
history, the unscorable/invalid distinction, expression-alias provenance, and
conflicting alias-cache values below the arithmetic tolerance. These helpers
were tested with manually specified synthetic dictionaries, not market arrays.
An additional hand-calculated nonzero case has delta S=-0.03, delta O=0.05 and
delta R=0.08, with unequal invalid counts and a first-year contrast of -0.55;
the code preserves the ten-task and two-half-year denominators and conditional
valid counts. A separate invalid/duplicate-slot fixture checks literal first
selection and minimum-AST eligibility without consulting future outcomes.

Two draft findings raised by root were independently confirmed:

1. Contract reconstruction initially opened the market ZIP and checked the
   installed pinned runtime, which would make saved public replay depend on
   execution inputs. The author introduced an environment-free reconstruction
   mode. A complete synthetic replay now passes after the fake ZIP is removed,
   with data-byte access, installed-runtime checking, task loading and imports
   of the financial task/loader modules all set to fail. This tests independence
   from the execution environment; it is not a claim to have run an actual
   second Python interpreter.
2. Metric validation accepted impossible date-count/null combinations. Six
   independent cases initially failed because no error was raised. The author
   now enforces zero valid dates iff mean IC and IC standard deviation are
   null; positive counts require finite values. All six now pass.

A further replay integrity blocker was identified in the complete draft:
the recursive arithmetic comparator was applied to the entire COMPLETE report,
including copied raw feedback and cache evidence. It would allow a resealed
one-ULP change in fields that the protocol requires to remain exact. The author
now compares retained evidence and provenance exactly, reserving arithmetic
tolerance for derived results. The end-to-end regression rejects resealed
one-ULP changes in slot feedback, key feedback, new raw historical/future
metrics and cached source outcomes. A one-ULP change in a computed mean remains
accepted under the declared tolerance, confirming that exact evidence checks
were not replaced by indiscriminate exact comparison of derived arithmetic.

The author identified a related final hardening: fixed costs 0.01 and 0.06 are
metadata, not approximate computations. Two focused tests initially reproduced
their acceptance of a one-ULP change. The repaired code rejects those changes
both in raw/v1 outcomes and nested job/report diagnoses. The final review suite
also rejects a whitespace-only byte difference in the optional public result,
while accepting the exact retained COMPLETE bytes.

The complete synthetic execution uses the production-sized population and
fake task/publication dependencies. It makes exactly 108 distinct fake calls,
retains all 180 slots and 132 keys, and replays the completed result. Author-
written cases independently exercised clean-prefix continuation without a
second call, exclusive-lock rejection, interruption before and after durable
completion, permanent failure retention, changed publication/source/data/task
gates before loading, fixed execution-directory enforcement, and corruption of
a completed prefix. The separate review case reseals a second job's timestamp
to precede its predecessor's completion; continuation is rejected before a
third fake call and the incomplete state is retained.

These end-to-end review cases reuse the author's synthetic `Harness` for input
construction; their tampering, dependency traps and assertions were written by
this reviewer. The hand-calculated arithmetic and small boundary/alias fixtures
are separately constructed. No test fixture invokes Git, an actual financial
evaluator, a market-data loader, or a model.

One initial end-to-end run stopped before its first fake evaluator because a
long pytest temporary path exceeded this Windows host's path limit. Retrying
the tests in shorter ignored repository-local directories resolved that test
environment issue. No evidence directory was erased to bypass a failed study.

## Final reviewed identities

| File | SHA256 |
|---|---|
| `src/alpha_research_rl/astra_pool_diagnosis.py` | `4e788a8ab50181222835c9aa053d7353390eb2a8270fe940404d69a2c7aeddd4` |
| `tests/test_astra_pool_diagnosis.py` | `2c19f41fa4100e4d56f67d6fb54baabba112eab598c9d1657f8e703dd45c5457` |
| `tests/test_astra_pool_diagnosis_review.py` | `6345de93670705e20b26ecc7a60645291db4c1e12ee7825f346da4fb9f249916` |
| `docs/astra-pool-diagnosis-plan-v1.md` | `a484bdbe9297c7e0d3d3ab0645cd583c694fe36b34f1fc03c73fbe4c3809582d` |
| `docs/reproduce-astra-pool-diagnosis.md` | `afb2f8f5b3b584a0b4deedb95b3a6c12f0242f43f8d3e1c033937141b442ff32` |

The final commands were `python -m pytest tests/test_astra_pool_diagnosis_review.py
-q -p no:cacheprovider` and `python -m pytest tests/test_astra_pool_diagnosis.py
-q -p no:cacheprovider`, each with a fresh short repository-local basetemp.

## Actual preparation check before publication and scoring

After root prepared the canonical contract, a separate standard-library-only
script rebuilt every slot, key, cache-reuse source, selector and pending job
directly from the immutable v1 bank and saved assessment. It did not call the
implementation's `_tables`, a market loader, or a financial evaluator. All
four prepared tables match exactly, including literal expression provenance,
fixed historical directions and the complete cached source outcomes. The
population is 180 slots, 30 episodes, 132 keys, 24 reused keys and 108 pending
jobs, with 167 positive and 13 negative directions. The 30-row selector
projection matches the predeclared independent target above exactly.

All ten public task mirrors match the original sealed v1 task files byte for
byte, their declared byte counts, file hashes and body hashes. All 18 bound
source/plan files match current bytes, including the reviewed diagnosis
source identity. The original v1 input hashes, runtime declarations and data
identity are preserved; this check did not read or recompute market data.
The execution directory was absent at this check, and the prepared contract
records zero model calls, new formulas and new evaluations.

The inspected contract is `artifacts/astra-pool-diagnosis-v1/contract.json`:
323,832 bytes, SHA256
`612b426cd843fa44956ccdbb3cc12692c8cada53590f781eef2bf3d00af81979`,
with verified body SHA256
`35af62465bff359a6022ce57c1f7f344b441f387542fb55809ea9a8d99a77a30`.
This is a local preparation check, not proof of subsequent public retrieval
or completed scoring.

## Supplemental public replay entrypoint review

The separate `scripts/replay_published_astra_pool.py` received a read-only
source review and an independent rerun of its 41 fake-callback/process-guard
tests: **41 passed in 2.78 seconds**. These are additional to the 44 core
module/reviewer cases above. No real pool replay or market scoring was run.
The reviewed wrapper requires the bound public execution directory and
complete report, exact integer population/call accounting, and matching
contract/report byte hashes. Its guards reject cached or newly imported
financial/training modules and tested process, network and private-data
accesses. The script accurately limits these guards to execution checks,
not an adversarial sandbox; platform detection precedes guard installation.
No blocker was found in this additional entrypoint review.

Reviewed wrapper SHA256:
`5ca481c180c69e06d9d0c7f3cf8e6c340d67ecda083a9ff12388a89a1a9246db`.
Reviewed wrapper-test SHA256:
`206cac9556531efa3d0156c857a72cfe593b9e71a4fe184b601d1be581b66555`.

## Enforcement and interpretation limits

The program binds one execution directory and prevents retry/reexecution for
**this prepared contract**, including ambiguous or failed jobs. It does not
provide a repository-wide or cryptographic single-study ledger. Preparing and
publishing a different contract remains an explicit human research decision;
the publication gate must not be used to disguise a same-version replacement.
Root states that this version will use the canonical artifact directory and
will not generate a replacement. A fresh public receipt is not automatic
authorization for a new study.

The receipt records root's public retrieval verification; synthetic tests of
that boundary are not an independent network/publication audit. Source hashes
and runtime version strings are not package-binary or host-integrity
attestations. Replay checks retained records and arithmetic, not whether raw
market calculations are economically valid or every possible external action
was logged. An execution-side caught `invalid_expression` outcome does not
identify which future numerical failure occurred.

The oracle is a bound for one choice from each of the fixed six-candidate
pools, with frozen directions and costs. It excludes abstention, larger pooled
search, a new generator, new trajectories and new periods. Positive headroom
is hindsight and authorizes no further model call or selector training. The
fixed cheap selectors were chosen after v1's selected outcomes were known;
this is post-hoc development diagnosis, not an untouched-holdout test,
profitability result, evidence that LLM generation is necessary, or Astra
weight training. All original v1 artifacts and its 30-call assessment remain
outside this new diagnosis.
