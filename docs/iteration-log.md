# Research iteration log

This retrospective index was assembled on 2026-10-01 UTC after the initial
experiments. It summarizes actual changes and decisions; it did not preregister
them. Linked plans, manifests, freezes and Git history retain their chronology.

## 1. Sequential environment and local training — completed

**Problem:** a scripted interface alone would not demonstrate generative modeling
or learned decisions.

**Change:** implemented bounded formula generation, evidence actions, explicit
budgets, LoRA SFT and trajectory RLOO, with parameter and reload checks.

**Evidence:** [six-task synthetic results](results-v1.md) showed identical
SFT/RLOO greedy behavior. The [144-action explorer](trajectory-explorer.html)
retains the repeated seven-step script and base-parser failures. This establishes
an implemented sequential interface and actual training, not useful adaptation.

## 2. Evidence conditioning and sampling — completed

**Problem:** familiar action scripts could ignore feedback; model defaults could
change the requested sampling law.

**Change:** ran a paired-feedback curriculum, audited generation configuration,
and measured cached/full-forward likelihood disagreement. The separate financial
actor adopted the tested FP32 configuration.

**Evidence:** [the curriculum](curriculum-results-v2.md) reached 8/24 correct
pairs, below its declared 80% gate; that branch stopped. The
[sampler correction](audits/2026-10-01-generation-config-merge.md) is an engineering
finding, not evidence of better financial prediction.

## 3. Chronological financial proposals — completed

**Problem:** synthetic rewards do not establish performance on market histories.

**Change:** ran a one-action study on pinned French49 data: 96 SFT and 31 actual
RLOO updates across two seeds, freezes, paired evidence interventions and simple
numerical references.

**Evidence:** [original results](financial-proposal-results-v1.md) retain 540
draws. RL reward gains over SFT were +.03146 / +.02618; in each case +.025 came
from fewer invalid formulas. Neither sampled RL policy exceeded the uniform
formula-grid reference. The financial task remains a contextual bandit.

## 4. Sequential feasibility and reward-linkage controls — completed

**Problem:** higher reward did not identify useful evidence acquisition or the
effect of correct reward assignment.

**Change:** tested a training-only sequential gate, then separately trained two
fresh on-policy reward-permutation controls with a declared plan and a new freeze
before their evaluation.

**Evidence:** the [sequential gate](sequential-gate-results-v1.md) failed and its
controller branch stopped. The [five-policy comparison](reward-linkage-results-v1.md)
contains 900 total draws, including the original 540. Correct RL exceeds matched
controls by +.02303 / +.01837 reward, but IC-contribution differences have opposite
signs. Both controls also improve over SFT. These findings narrow the supported claim.

## 5. Inspectable evidence and published checkpoints — completed

**Problem:** reports and local adapters were difficult for another reader to
inspect or reproduce. Local tests missed a Python-version difference.

**Change:** published three standalone explorers, CPU arithmetic replay, exact
adapter verification and the
[v0.1.0 release](https://github.com/Siquan-Wang/alpha-research-rl/releases/tag/v0.1.0).
Reconstructed states remain distinct from missing historical prompt tokens.
Fixed AST portability and protected published benchmark files from accidental
CLI overwrites.

**Validation:** 431 local tests passed. Public
[Python 3.11/3.12 CPU and training-math jobs](https://github.com/Siquan-Wang/alpha-research-rl/actions/runs/36822130448)
passed. All five publicly downloaded adapters were actually loaded and their
parameter digests matched the original records; see the
[load verification](../results/financial_adapter_load_verification_v1.json).
This verifies distribution and loading, not cross-hardware stochastic behavior
or additional financial performance.

## 6. Reliability, diversity and installed-package replay — completed

**Problem:** an average reward and a count of different formulas do not explain
sampling uncertainty, period sensitivity, or effective signal diversity.
Editable-source execution also leaves an installation boundary untested.

**Change:** three parallel checks retained all six policy contrasts, both
evidence conditions, all five yearly omissions, and all 900 original draws.
The new public replay script recomputes both complete diagnostic reports using
saved evidence, with no training imports, weights, raw data or network access.

**Evidence:** the [reliability report](reliability-analysis-v1.md) gives
true-evidence correct-RL-minus-control reward differences +.023032 / +.018368,
with conditional generation MCSEs .013041 / .018558. These are not market
standard errors or significance claims. Seed 29's IC contribution remains
negative under every yearly omission. The
[diversity report](proposal-diversity-v1.md) finds 861 teacher-template matches
among 881 usable proposals; all 19 failures remain counted. Correct RL does not
consistently increase entropy, and all 100 greedy proposals remain identical.

**Validation:** 463 local tests and Ruff passed. Separate reviewers
[reconstructed the reliability arithmetic](audits/reliability-analysis-review.md)
and [checked diversity and the replay verifier](audits/retained-diagnostics-review.md).
An [installed-wheel check](audits/installed-package-reproduction-review.md)
reproduced the 900-draw analysis and 144-action synthetic replay on the original
host while importing project modules from a fresh installation. This is not a
fresh-machine training reproduction. Public CI at `3defd2c` passed Python
3.12 and training-math, but Python 3.11 failed the new reliability wrapper's
full-object equality check after the existing tolerance-based full replay
passed. That failure was retained and repaired before claiming a cross-version
pass; the earlier release CI is in round 5.

The subsequent [portability correction](audits/reliability-portability-review.md)
keeps metadata, types and input bytes exact while using the existing `1e-12`
arithmetic tolerance for computed floats. All reliability values are unchanged;
only the analysis-source identity was updated. The complete local suite now
passes 503 tests. The subsequent public run at `b2c0beb`
[passed all three jobs](https://github.com/Siquan-Wang/alpha-research-rl/actions/runs/36825754766):
Linux Python 3.11, Python 3.12 and training-math. Their completed success states
were independently read from the public jobs API on 2026-10-01 at 06:48 UTC.

These are post-hoc robustness and reproduction checks. No new model training,
transfer-period scoring, stopped-branch restart or financial advantage is claimed.

## 7. Constructed adaptive-query opportunity — completed

**Problem:** weak financial information and a policy that ignores useful evidence
can both produce a failed agent. A new mechanism test needs an identifiable
adaptive opportunity before spending more model-training compute.

**Change:** adopted a separately versioned four-candidate task with exactly two
queries. Published its kernel, gate and hand-calculated expectations at `3defd2c`
before producing the result. An exact rational solver enumerates all twelve
query plans and gives every fixed comparator an optimal final selector using
both observed responses.

**Evidence:** [exact results](mechanism-gate-results-v1.md) give adaptive value
81/100, best fixed-query value 63/100 and gap 9/50. The gate passes. These values
were deliberately engineered and anticipated analytically; they are not a
held-out discovery, a financial improvement or a learned-model result.

**Validation:** 26 focused tests, a separate solver review and the full 489-test
local suite passed. Unqueried bits cannot enter policy decisions. The public
diagnostic verifier reproduces the complete gate report with scalar types,
source hashes and plan hashes checked. A tokenizer-only check identifies a
compatible action alphabet and a prefix-boundary pitfall; it does not validate
a future sampling law or model behavior.

The complete gate and corrected financial diagnostics were published at
`b2c0beb` and passed the same three-job public CI run linked in round 6.

**Next:** freeze a separate parent-policy preflight before any new RL. Check
the action law and whether the untrained model already reaches the constructed
ceiling. The [design advice](research-next-steps.md) and its
[critique](audits/next-mechanism-design-review.md) distinguish this narrow task
from general research and formula discovery. No new GPU experiment has run.

## 8. Actual Astra research agent — implementation verified, collection in progress

**Problem:** developer-side LLM assistance does not show that a strong model can
conduct the factor search. The completed financial study tested a small local
model and mostly reduced invalid outputs.

**Change:** the next mainline uses actual Astra decisions through the existing
Codex CLI. The prospective three-arm protocol fixes ten development periods,
six proposals per episode, quantitative/validity-only/withheld feedback, and a
common selector. All thirty candidate pools must be frozen before assessment.
The unrun local-model mechanism preflight is deferred; old results stay intact.

**Observed validation:** the feedback broker and native CLI provider passed 81
focused tests before the final mask correction tests were added. A real
nonfinancial structured-packet check completed at 07:34 UTC on 2026-10-01 with
requested `gpt-6-astra`, `ultra`, and default service tier. The saved stream
contained exactly one final assistant message, no tool event, and reported
15,282 input tokens, 395 output tokens and 317 reasoning tokens. These are
reported usage fields, not an attestation of model weights or private context.

Independent review removed extra syntax-error detail from the full-feedback arm
so it differs from the validity control only by quantitative candidate feedback.
A separate review caught task/arm names in the subprocess working directory;
the runner now uses one common neutral context before any study call.

The final integrated suite passed **613 tests** in 203.51 seconds, and Ruff
passed. The [orchestration review](audits/astra-study-review-v1.md) checked
quota stops, interruption retention, full-bank CRLF replay, all three nonzero
contrasts and negative annual values using artificial providers/tasks. The
[broker review](audits/astra-broker-review-v1.md) independently checked the
feedback masks and real nonfinancial transport evidence. Actual cached-data
initial observations validated for all ten periods with zero assessment calls.
The [prepared contract](../artifacts/astra-agent-v1/contract.json) binds the
reviewed source, plan, executable, data and task identities; all fourteen
contract-bound staged files match their exact local bytes. The protocol,
implementation and contract were published at `63394d7`; root independently
downloaded all fourteen files at that public commit and verified exact bytes
before collection. Public [CI](https://github.com/Siquan-Wang/alpha-research-rl/actions/runs/36832512626)
passed Python 3.11, Python 3.12 and training-math; root read the completed states
at 07:55 UTC on 2026-10-01.

The separate [public replay module](replay-astra-evidence.md) passed 41 additional
synthetic tests, independently rerun by root. It checks all 180 broker decisions,
prompt/response identities, masks, costs and common selection, and optionally
reconstructs the saved 30-outcome arithmetic. It does not recompute financial
scores or establish hidden provider context. Usage fields remain separate,
with missing observations explicit. These 41 tests are additional to the
613-test integration run, not a claim that one 654-test run was executed.

**Limits and next:** registered financial candidate collection has started;
future assessment remains sealed until all thirty pools are completed, frozen
and published. There is no completed financial comparison yet. The
[execution guide](reproduce-astra-agent-study.md) explains the separate
collection, freeze, publication and assessment stages. Astra inference-time
adaptation is not Astra reinforcement-learning weight updates. The same
previously examined financial periods cannot become an untouched holdout.

### Collection freeze before assessment — 2026-10-01 09:03 UTC

All sixty registered three-arm rounds completed: **180 actual Astra decisions,
30 six-proposal episodes**, with every provider stream accepted. All 180
proposals were grammar-valid and usable on historical feedback; none repeated
an earlier canonical AST within its episode. This does not establish semantic
signal diversity or future predictive value. All ten periods had byte-identical
supplied first prompts across the three conditions.

The [complete candidate pools](../results/astra_agent_v1_submissions.json) were
frozen at `2026-10-01T09:03:42.501498+00:00`, with **zero future assessment calls**.
Root ran the [structural replay](../results/astra_agent_v1_submission_replay.json)
successfully against the full bank and exact frozen source/plan bytes. It made
no model/network calls or market-data reads. All 30 feedback-only selections
exist. A targeted export scan found no email, host path, private-zone identifier,
unexpected URL or credential-prefix match; raw provider streams remain private.

This checkpoint publishes the complete submissions before later-period scoring.
It contains no assessment headline. Recorded token usage is complete for all
180 calls but differs across conditions; equal proposal counts are not a claim
of equal hidden context or computation. The next step is to verify the public
commit's exact files, then assess only its 30 fixed selections.

## 9. Completed Astra comparison and inspectable research traces

**Problem:** valid model-generated formulas and persuasive hypotheses do not
establish useful research. The completed bank needed a frozen assessment and
an interface that distinguishes what the actor saw from what the evaluator knew.

**Change:** published all 180 proposals at `b204714`, independently downloaded
and matched all fifteen bound public files at 09:07 UTC on 2026-10-01, then
assessed exactly the thirty already selected expressions. Added an
[interactive explorer](https://siquan-wang.github.io/alpha-research-rl/astra-explorer.html)
for every supplied history, feedback mask, proposal, fixed selection and outcome.
Separate [trace bookkeeping](astra-trace-diagnostics.md) uses saved evidence
without new inference or market scoring.

**Observed result:** mean oriented assessment IC is −0.033823 for full feedback,
−0.027459 for validity-only and −0.028719 for withheld feedback. Full minus
validity is **−0.006364** over all ten registered periods. All thirty assessments
are valid; the common search cost cancels in arm contrasts. There is no observed
feedback advantage in this realized development sample. This is not proof that
feedback generally harms research. The [complete report](astra-agent-results-v1.md)
retains all three comparisons, ten paired periods, five year summaries and
provider usage fields.

**Validation:** the complete integrated local suite passed **679 tests** in
195.09 seconds; Ruff passed. Three distinct reviews covered private-to-public
transport evidence, source-first result arithmetic and interpretation, and the
new explorer. They are internal agent reviews, with authorship disclosed in
their records. All 180 rendered formulas across sixty period/attempt controls
match the saved bank; ten paired rows and five year rows render without browser
errors. The renderer now validates and embeds the same captured input bytes,
escapes hostile strings, and preserves full-history hashes and truncation flags.
No market score is recomputed by either replay or the explorer.

The new public CI step replays the actual complete bank, assessment arithmetic,
trace bookkeeping and generated page. Its local run passed with raw/private
data, training imports, network and replay subprocesses prohibited. Windows
standard-library platform detection precedes those guards; its OS version
command initially triggered the strict subprocess check and this boundary is
now explicit. The completed result, explorer and replay were published at
`3b0f946`; [public CI](https://github.com/Siquan-Wang/alpha-research-rl/actions/runs/36843534765)
passed Python 3.11, Python 3.12 and training-math, including the actual-bank
replay. GitHub Pages deployed successfully and the live Astra page was inspected.

**Limits and next:** all calls requested Astra Ultra through the existing Codex
CLI; provider-reported usage and accepted event streams do not attest hidden
model context or weights. This is inference-time research, not Astra weight RL.
The previously examined 2020–2024 data are development evidence. A separate,
explicitly post-hoc frozen-pool diagnosis will distinguish a poor candidate-pool
ceiling from missed selection opportunities. Its plan and code must be frozen
before any additional candidate is scored; it cannot change the v1 winner,
direction, denominator or result.

## 10. Frozen-pool diagnosis: prepared before additional scoring

**Problem:** the negative selected results alone cannot tell whether the six
proposals contained better future signals that the historical selector missed.
They also do not establish that a more elaborate selector would help.

**Change:** prepared a separately versioned, explicitly post-hoc
[protocol](astra-pool-diagnosis-plan-v1.md) and
[frozen contract](../artifacts/astra-pool-diagnosis-v1/contract.json). All 180
original slots remain; 132 task/AST/historical-direction keys reduce the maximum
additional scoring to 108 calls after reusing 24 keys covered by original
selected assessments. Ten original task files are mirrored exactly. No new
model calls, formulas, sign choices or market periods are permitted.

Original, first-proposal and minimum-AST selectors are fixed before the new
scores. An unattainable future-informed maximum will diagnose headroom, with
the accounting identity `Delta S = Delta O - Delta R`; it cannot replace the
original result. All choices retain the same six-proposal cost and denominator.

**Validation:** the complete local suite passed **728 tests** in 223.16 seconds;
the new public saved-replay entrypoint separately passed **41 tests** in 3.05
seconds. Ruff passed. The [independent review](audits/astra-pool-diagnosis-review-v1.md)
resolved exact-versus-tolerant comparisons of retained evidence and fixed cost,
impossible metric support, immutable public report bytes, raw-data-free replay,
and interruption/retry boundaries. Enforcement covers this frozen contract,
not an adversarial repository-wide single-study ledger.

**Current status:** preparation completed on 2026-10-01 at approximately 10:08
UTC, with **zero additional financial evaluations**. The contract file SHA256 is
`612b426cd843fa44956ccdbb3cc12692c8cada53590f781eef2bf3d00af81979`.
Public byte verification must precede the bounded execution. Results will be
reported only after the entire fixed bank and saved-arithmetic audit complete;
a failed or ambiguous attempt instead preserves an incomplete study.

**Limits and next:** this is diagnosis after seeing v1 outcomes on already
examined development periods. A positive oracle ceiling would establish only
hindsight opportunity, not a predictable selector or authorization for another
model study. The [reproduction guide](reproduce-astra-pool-diagnosis.md) separates
preparation, public verification, execution and saved replay.

### Completed bounded diagnosis — 2026-10-01 10:12 UTC

All 32 bound files at `8afcf868` were downloaded anonymously and matched at
10:11:42 UTC. Exactly 108 new evaluator calls then completed between 10:12:12
and 10:12:45 UTC, with no retries, new formulas or model calls. All 180 slots
have usable future assessment support. The original 24 cache keys were reused
with exact provenance; all original study artifacts remain unchanged.

**Observed result:** full feedback's hindsight mean IC is +0.015711, versus
−0.033823 for its original selector, −0.016355 for the literal first proposal,
and −0.026670 for minimum AST. Its hindsight utility is still −0.044289 at the
fixed abstract cost .06. Every arm's three tested feasible selectors have
negative mean IC. Full feedback has a lower pool ceiling than either control,
but a slightly smaller selection gap; the original deficit is not explained
simply by uniquely worse selection. The
[complete result report](astra-pool-diagnosis-results-v1.md) retains every
period, all comparisons and the post-hoc interpretation limits.

**Validation:** independent saved-record reconstruction made 4,227 arithmetic
checks, with maximum discrepancy 6.25e-17, and exact retained evidence checks.
Root's guarded replay reproduces the report and offline page with no new market
score, model, network or raw-data access. The new explorer's twelve synthetic
tests passed independently and on root (36.66 seconds on root). Actual browser
checks matched all 180 formulas, displayed future ICs and utilities across all
thirty period/arm controls; twelve summary rows, thirty period rows and fifteen
year/arm rows render with no console errors. An independent explorer review
also covers expression-alias provenance. A final prose-only change clarifies
that the oracle gap is guaranteed nonnegative, rather than strictly positive.

The pre-score publication's
[public CI](https://github.com/Siquan-Wang/alpha-research-rl/actions/runs/36847550656)
passed both Python versions and training-math. Results, final explorer and the
expanded CI replay are a subsequent publication batch.

**Next decision:** a separately reviewed matched-prefix proposal-quality study
is being designed. The reason is the remaining conditional generation question
under identical starting states, not merely the presence of positive hindsight
headroom. It will not restart local-model or stopped financial branches. No
new hosted calls have been made for that proposed follow-up.
