# Astra frozen-pool diagnosis v1: post-hoc protocol

Date: 2026-10-01. Study ID: `astra-frozen-pool-diagnosis-v1`.
This separately versioned, CPU-only diagnosis is adopted after reading v1's
selected outcomes, but before evaluating its unselected candidates. It asks
whether the realized six-candidate pools contain missed assessment opportunity,
and how much the original selector falls below that hindsight ceiling.
It is not a new confirmatory study. **Zero model calls, zero new formulas,
zero new sign variants, and zero new periods** are permitted.

## Immutable inputs and pre-score publication

The original v1 protocol, bank, 30 selected assessments, and report remain
unchanged. The additional assessments belong only to this diagnosis. The
following input file SHA256 values are mandatory, in addition to their sealed
canonical-body hashes:

| Input | SHA256 of exact file bytes |
|---|---|
| `artifacts/astra-agent-v1/contract.json` | `63848687bb44ea7d835b0a2d6ebe88d95dd7ed7257c8ca27dd216a6c37d8b17a` |
| `results/astra_agent_v1_submissions.json` | `89b9cd42d4d248393c2c3c2b9f29714fb9ba023b511d9b3741196d99a321def7` |
| `results/astra_agent_v1_assessment.json` | `30aafbc089f6017c99c6d23c14fca077ffcdf59e9cbf0599d28560c4446ff2a0` |

Preparation reads saved JSON, source bytes, and the raw ZIP's bytes for hashing;
it must not load market arrays, construct financial tasks, or call an evaluator.
Require the ten original sealed task files, verifying their exact bytes against
`contract.task_manifest_sha256`, their body hashes, and task IDs. Bind the
original plan and all twelve source files named in `contract.source_sha256`,
including the frozen `financial_tasks.py`, `dsl.py`, `evaluation.py`, data parser,
and pinned loader. Do not edit these dependencies or substitute another scorer.

Use the same runtime versions as v1: Python 3.12.14, NumPy 2.5.3, pandas 3.0.6,
SciPy 1.18.1. These are version checks, not claims that package binaries match.
The raw ZIP SHA256 is
`8f394fe34bea54d41b9aafed410425ee8f8e252ede3c71a7c1cd20bab83040de`.
The frozen loader caps the panel at 2024-12-31; no later samples enter a task
or scorer. The ZIP can physically contain later rows. Task boundaries, five-
session horizon, purging, and support thresholds remain exactly those in v1.

Preparation creates a new, exclusive study directory and public contract at
`artifacts/astra-pool-diagnosis-v1/contract.json`. Its sealed body includes the
input hashes, original task/source/runtime/data identities, new plan and
implementation hashes, ordered slot/key/job tables, fixed selectors, costs,
failure rules, and expected population counts. Mirror the ten original task
files byte-for-byte under `artifacts/astra-pool-diagnosis-v1/tasks/` so the bound
inputs are inspectable. These contain aggregate evidence, not raw market arrays.

Before the first new evaluator call, root publishes the plan, contract, task
files, implementation, tests, and reproduction instructions, with the unchanged
v1 inputs and source dependencies available at the same public commit. Execution
requires local commit/blob byte verification plus a saved publication receipt
identifying that commit, UTC verification time, public paths and matching hashes.
Root verifies unauthenticated public retrieval. A local Git check alone does not
prove publication; the receipt records this separately. Raw market data is not
published. No contract includes its own hash or its later publication receipt.

## Fixed population, cache keys, and order

Use task order `2020-H1, 2020-H2, ..., 2024-H2`; arm order
`full_feedback, validity_only, withheld_feedback`; attempt order 1 through 6.
Preserve all **180 slots** in **30 episodes**. Actual preparation must assert:

- 132 distinct `(task_id, canonical_ast, feedback_orientation)` keys;
- 24 keys covered by the original 30 selected outcomes and 108 pending keys;
- 167 positive and 13 negative slot orientations;
- unique-key counts by chronological task `[13,12,15,14,13,14,12,12,14,13]`;
- all 180 saved proposals grammar-valid and feedback-usable, with no duplicate
  AST inside an episode, as already observed in the immutable bank.

Canonical AST is the frozen `ast.dump(ast.parse(expression.strip(), mode="eval"),
include_attributes=False)` identity, after original strict grammar validation.
No repaired expression is scored. Orientation is -1 for negative saved feedback
mean IC, otherwise +1, including zero. Hash canonical JSON of the three-element
key to obtain a stable key ID. Canonical JSON uses sorted keys, compact
separators, `ensure_ascii=True`, and `allow_nan=False`.

Traverse all 180 slots in the stated order. Each unique key's representative is
its first occurrence. Its pending job uses that occurrence's exact original
expression string, not an AST serialization or a selected alternative alias.
Number pending jobs in first-occurrence order. **108 is the maximum number of
new calls to `FinancialTask.evaluate`; no cache verification calls are allowed.**
Repeated slots share a result but keep their identities, expressions, feedback,
and provenance in output. AST caching is not economic/rank-equivalence merging
and does not establish 132 distinct signals. Do not add the two initial probes
unless they already occupy candidate slots; do not score a fixed grid or any
other candidate in this diagnosis.

## Exact reuse and outcome validation

Verify every original selected row against its own episode: exact selected
expression string, selected attempt, saved feedback IC, direction, task, and
recomputed canonical AST. Verify the v1 selector against saved feedback only.
The original assessment must bind the exact frozen-bank file hash. Validate
its original cost, one-proposal reward, status, support, raw future mean IC,
oriented IC, and adjusted utility. Each of the 24 reusable keys retains all
contributing selected-row references and their unmodified source outcomes.

For shared keys, feedback must agree exactly, with scalar types preserved.
Original selected outcomes sharing a key must agree exactly on every outcome
field except the original expression string; retain each string as provenance.
Do not overwrite it with the representative expression. Missing or conflicting
reuse evidence terminates preparation; it never authorizes a replacement call.

Before execution and each job, recheck bound inputs, source/runtime identities,
and data hash. Construct/cache tasks only after the publication gate. Before a
task's first new call, its reconstructed `public_manifest` and initial
observation must match the original sealed task record exactly. The scorer must
return the submitted expression exactly. Its five historical metric fields
must match the slot's saved feedback exactly after removing only `usable`.
The saved usability calculation, orientation, zero-feedback flag, and probe-
reuse flag must also agree. Changed historical information is an integrity
failure, never a new financial outcome.

Require the complete frozen evaluator schema, exact scalar types, finite
numeric values except specified nulls, and counts consistent with the frozen
task lengths. Counts are integers, not booleans, with `0<=n_dates<=L` and
`n_signal_dates=L`; coverage lies in `[0,1]`, nonnull mean IC in `[-1,1]`, and
nonnull IC standard deviation is nonnegative. Support usability is the frozen rule: finite mean IC, coverage
at least .8, and `n_dates >= max(min(20,L), ceil(.8*L))`, where `L` is the
purged signal-window length. Reward identities use finite arithmetic checks
with absolute and relative tolerance `1e-12`; source/input hashes, identities,
saved feedback values and scalar types remain exact.

Only these new outcomes are accepted for this actual feedback-usable bank:

| Status / reason | Required assessment state | Outcome |
|---|---|---|
| `ok` / null | Well-formed, usable assessment; finite oriented IC equals frozen direction times raw mean IC | Preserve original reward `z-.01`; diagnosis utility `z-.06` |
| `unscorable` / `insufficient_assessment_support` | Well-formed, unusable assessment; oriented IC null | Preserve original reward `-1.01`; diagnosis utility `-1.06` |
| `invalid` / `invalid_expression` | Assessment null and oriented IC null, but complete matching usable historical feedback and direction | Preserve original reward `-1.01`; diagnosis utility `-1.06` |

The last label is the frozen scorer's coarse caught-exception label; it can
collapse future numerical/evaluation exceptions and does not identify an
economic cause. Missing/changed historical feedback, a missing/wrong direction,
an unexplained status/field combination, nonfinite output, or an uncaught
exception makes the diagnosis **INCOMPLETE**. Do not relabel these integrity or
infrastructure failures as penalized candidate outcomes or modify the scorer.

## Costs, fixed selectors, and synthetic failure cases

Every candidate slot receives the same six-proposal cost `.06`, independent of
cache reuse or selection rule. For a valid assessment let `z` be the frozen-
direction oriented IC and define `u=z-.06`; otherwise `z` is null and
`u=-1.06`. Preserve original evaluator outputs alongside derived diagnosis
fields. No one-call-cost sensitivity is part of this protocol.

Freeze these three feasible selectors before the missing outcomes are read:

1. `original`: the immutable v1 selection, checked as maximum absolute saved
   feedback IC among grammar-valid, feedback-usable, nonduplicate candidates;
   earliest attempt breaks ties. Never replace a poor future outcome.
2. `first`: literal attempt 1, with no skipping of an invalid/unusable first
   proposal and no fallback to a later candidate.
3. `minimum_ast`: among grammar-valid, feedback-usable, nonduplicate candidates,
   minimize `sum(1 for _ in ast.walk(ast.parse(expression.strip(), mode="eval")))`;
   earliest attempt breaks ties. Count all AST node types, including expression,
   call, name, load and constant nodes. Eligibility uses no assessment fields.

Synthetic tests must preserve invalid/unscorable/duplicate slots. A grammar-
invalid or feedback-unusable slot has null orientation and known utility
`-1.06`, requires no new market call, and is not eligible for `original` or
`minimum_ast`. If neither has an eligible candidate, its selected attempt is
null and utility is `-1.06`. `first` still selects slot 1. An eligible candidate
with future failure keeps `-1.06`; neither feasible selector skips it. These
generic fixture rules cannot relax the actual bank's frozen population checks.

## Estimands and mandatory complete output

For each task/arm, let `S` be original utility,
`O=max(u_1,...,u_6)` the **unattainable hindsight oracle ceiling**, and
`R=O-S` the selection gap. Earliest attempt breaks oracle ties for descriptive
reporting only; no oracle choice is deployed. Keep all six slots in the maximum,
including failures. Assert `R>=0` up to the arithmetic tolerance.

Report each feasible selector and the oracle for all 30 task/arm pools, all
three arms, all ten task comparisons, and all five years. Each year averages
its two half-years; each overall mean equally weights all ten tasks. For every
task, year and overall arm comparison, retain the signed quantities and verify
`Delta S = Delta O - Delta R`. The three fixed contrasts are full-minus-validity,
full-minus-withheld, and validity-minus-withheld. Do not label `Delta O` a causal
generation contribution. Also retain first-minus-original and minimum-AST-
minus-original within every arm and period.

For every selector summary, report denominator, valid/invalid counts, mean
utility, valid IC sum divided by the full denominator `q`, valid fraction `p`,
and conditional-valid mean IC with its explicit valid count (null if none).
The accounting identity is `mean(u)=-1.06+p+q`; contrast components are
`Delta p + Delta q`. Report slot validity both over all 180 slots (60 per arm)
and over unique keys, with clearly different denominators. Never drop failed
slots/tasks or replace an unconditional mean by a valid-only mean.

The complete JSON, `results/astra_pool_diagnosis_v1.json`, includes schema/study
version, input/publication/provenance hashes, all 180 slot mappings, all 132 key
records with original source outcomes and reuse/job references, all 30 selector
rows, ten paired rows, five year rows, full arm summaries, decompositions,
exact call accounting, and the allocation result below. Original-selector
metrics must reproduce the immutable v1 assessment within the arithmetic
tolerance. It contains aggregate metrics, never raw return or per-date arrays.

## Durable execution, partial states, and replay

The wrapper exposes prepare, bounded execute, and saved-record replay phases.
The contract binds the sole execution directory to `output_dir/execution`.
Execution and replay reject every other directory; another empty directory
cannot reset this contract's call ledger.
Production execute defaults to at most 108 new jobs and may stop at a smaller
explicit `max_jobs` only after a fully completed job. An exclusive study lock
prevents concurrent execution. Before each evaluator call, exclusively create
a durable STARTED record with contract hash, job/key/expression, UTC time and
prior-record digest. Only after full validation may it exclusively write the
sealed COMPLETED record containing the exact returned outcome. Never overwrite
an input, contract, started/completed record, or final report; resolved aliases
to protected paths must be rejected.

A clean, verified completed prefix may continue explicitly from its first
unstarted job. This is continuation, not retry: completed or started keys are
never reevaluated. Any failed job, corrupt prefix, unexplained extra record,
or STARTED without a matching valid COMPLETED permanently blocks further
scoring under this version. Preserve the failing raw return when available,
record INCOMPLETE, and retain all earlier results. Do not clear a stale lock
to bypass an ambiguous job. A completed diagnosis refuses execution and allows
saved-record replay only. No automatic retry, replacement run, expanded budget,
or partial-bank headline is permitted.

Only after all 132 keys and 180 mappings are complete may aggregation publish a
COMPLETE report; otherwise publish status/counts and partial evidence only.
Replay must use saved JSON exclusively, verify all input/job/body hashes and
accounting, and reproduce summaries without importing/calling a market loader
or evaluator. Artificial tests must cover reuse conflicts, exact alias
provenance, invalid/future-unscorable cases, ties, nonzero decomposition,
no-overwrite, concurrency, interruption before/after completion, clean-prefix
continuation and rejection of any second call to the same key.

## Allocation rule and limits

For the full-feedback arm report mean oracle utility and mean `O+.06` without
rounding before the decision. This bank already has a valid original selected
candidate with oriented IC strictly greater than -1 in every pool, so an invalid
alternative cannot win the oracle. Consequently `O+.06` here is valid oriented
IC. Verify that condition; in a generic all-failure fixture it is instead an
invalidity-penalized score, never a conditional-valid mean.

If mean `O+.06 <= 0`, declare no-go for rescuing **these fixed full-feedback
pools and directions** through selection alone to obtain positive mean oriented
IC. Independently, mean `O<=0` rules out positive mean utility at the fixed cost.
Neither bound covers abstention, pooled eighteen-candidate searches, another
generator, a different trajectory or new periods. If the ceiling is positive,
report realized hindsight headroom only: it triggers no model calls, selector
training or automatic next experiment. A feasible rule would need a separately
reviewed validation design; the oracle does not establish predictability.

Stop after the bounded evaluations, fixed analysis and saved-arithmetic audit,
including negative or null results. The first/minimum-AST rules address the need
for sophisticated selection inside these realized Astra pools, not whether an
LLM was needed to generate them. They were selected after v1 outcomes were
known. There is one sampled trajectory per arm/period, dependent market blocks,
and reused 2020-2024 development data. No significance, generation-MCSE,
fresh-holdout, profitability, factor-originality, Astra weight-RL, or general
causal claim follows. This does not restart the stopped sequential gate or the
deferred local-model mechanism experiment.
