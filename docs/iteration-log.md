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

The completed batch was published at `5640368`. Its
[public CI](https://github.com/Siquan-Wang/alpha-research-rl/actions/runs/36850046341)
passed Python 3.11, Python 3.12 and training-math. Pages deployed successfully;
the live [pool explorer](https://siquan-wang.github.io/alpha-research-rl/astra-pool-explorer.html)
shows the exact completed report identity and corrected oracle interpretation.

**Next decision:** a separately reviewed matched-prefix proposal-quality study
is being designed. The reason is the remaining conditional generation question
under identical starting states, not merely the presence of positive hindsight
headroom. It will not restart local-model or stopped financial branches. No
new hosted calls have been made for that proposed follow-up.

## Iteration 11 — matched starts and proposal-quality controls

**Problem:** the original feedback conditions followed different sampled
trajectories. The pool diagnosis cannot isolate how the same starting evidence
changes the next generated formula, and an improved historical selector alone
would not demonstrate better generation.

**Change:** the [new protocol](astra-matched-prefix-plan-v1.md) fixes ten
two-proposal starts, four fresh calls per displayed/masked condition, and three
cheap references. Its 200-slot population separates proposed-factor quality Q
from gain G after a frozen historical selector. Two public-byte gates precede
hosted collection and later-period scoring; failures consume their slots.
The implementation records quota checks, actual starts, raw-response digests,
historical cache reuse and terminal incomplete states without replacement calls.

**Validation before execution:** root's full integrated suite passed **968 tests**
with one Windows symlink-permission skip in **427.33 seconds**. Ruff passed.
Independent reviews cover the scoring decomposition, cumulative lag limit,
publication gates, interruption handling and synthetic replay. Preparation then
created the exact contract, ten states, twenty prompts and 120 cheap packets,
with no model call or new financial score. Publication verification and actual
collection remain the next steps; test success is not a research result.

**Limit:** this remains a development-panel study. Common probes can reveal some
masked information, four provider draws need not be independent, and Astra's
weights are not trained. The next decision follows the fixed allocation rule,
not a favorable subset of periods or post-hoc prompt changes.

### Complete collection, before future joins — 2026-10-01 12:13 UTC

Preparation was published at `a33070e81651635edbd38bbf8425de4f5d790501`.
All 302 required paths matched anonymous public downloads at 11:29:57 UTC,
before the first dispatch. Public CI passed Python 3.11, Python 3.12 and
training-math; Pages also deployed successfully.

Exactly 80 Astra/ultra/default-tier calls completed, with 120 predetermined cheap
slots and no replacement or retry. All 200 slots were frozen after the final
batch completed at 12:13:30.476560 UTC. Submission SHA-256 is
`672d93cd8faababc71a7b3b5ff3823da840061479798f0ec1f2b6eef1cc9577d`.
Collection used 98 new historical-feedback calls, 40 task constructions and 80
initial-probe checks, with zero future joins or assessments.

All 80 hosted proposals were historically usable. The grammar control retained
two zero-signal failures. Historical selection admitted 18/40 truthful, 6/40
masked, 0/40 copy, 10/40 window-edit and 6/40 grammar proposals. These counts
describe historical admission, not future quality. Public provider records
report 1,290,644 input tokens, 693,376 cached input tokens, 54,599 output tokens
and 43,175 reasoning-output tokens; these fields are not added as independent
token totals. Equal literal prompts sometimes have different reported input
counts, and neither hidden context nor independent draws are attested.

A separate all-80 public-rationale audit was planned after collection began.
It uses only exact supplied prompts and final public packets, with coding frozen
before current future outcomes are exposed. It is descriptive internal
AI-assisted review, not a registered primary endpoint or peer review. Its
[plan](audits/astra-revision-grounding-plan-v1.md) changes no experiment rule.
The offline explorer passed 11 author and two independent synthetic tests;
the auxiliary citation-record validator passed 22 synthetic tests after a
JSON-pointer escape fix. Actual result rendering remains pending. Next are
complete-bank publication verification, blinded coding and bounded assessment.

The frozen bank was published at `184f4227f830f7df4feedb709d310f37a4ff1e2e`.
All 786 Gate 2 paths matched anonymous downloads at **12:21:45.963655 UTC**.
Independent reconstruction verified all 200 historical choices, 120 cheap
expressions, 482 collection-file identities and 80 dispatch chains.

The ancillary [public-rationale coding](audits/astra-revision-grounding-results-v1.md)
froze at **12:22:03.025077 UTC**, with 80/80 assessable packets and 329 coded
factual units: 159 displayed-supported, 165 derived-supported and five ambiguous.
The reviewer coded no numerical contradiction or unsupported reported measurement.
This is one internal reviewer's coding, not established semantic truth or a
predictive finding. The exact coding SHA-256 is
`1fd4c13ab8530f0d71ee3d562aa8e1dd099a2fa8d88a028308316b30c395efce`.
Root independently ran the integrity validator and verified that no assessment
request existed at that check. This coding is published before financial
assessment and will not be rewritten to match those outcomes.

Root's final wrapper/explorer/reviewer checks passed **121 tests in 67.89 seconds**,
including the real frozen replay over a completely artificial bank inside a
guarded child process. The public entrypoint now requires the exact saved report
and full HTML, with all actor prompts and renderer identity checked. The frozen
replay creates disposable public-evidence snapshots; it does not promise zero
temporary writes. Actual financial assessment and actual report/page replay
remain pending at this publication point.

### Complete assessment, failed allocation gate and result inspection

The rationale audit was published at `39a3522` and anonymously byte-verified at
12:33:10 UTC while the assessment request was absent. The preserved
[receipt](../artifacts/astra-revision-grounding-v1/publication-receipt.json)
records that additional chronology check. The existing Gate 2 receipt remains
12:21:45 UTC at `184f422`.

One assessment command began at 12:33:46 and completed its last new evaluation
at 12:34:35 UTC: **99 new future calls, 34 exact prior-cache keys and all 200
retained slots**, with zero retries. All 133 future keys were usable; the two
historical constant-zero grammar proposals remained Q = −1, without a future
call. The [complete report](astra-matched-prefix-results-v1.md) retains every
comparison. Truthful minus masked Q was **−.0067496**; the G contrast was
**+.0014969**, but truthful G itself was **−.0010982**. The grammar Q advantage
contains +.05 validity and −.0114486 predictive contribution. Only **5/13**
allocation conditions pass; the overall gate fails and this version stops.

Independent Decimal reconstruction checked 4,570 float comparisons with
maximum deviation 5.55e−17, all 786 saved Gate 2 identities and 99 job chains.
Narrative review corrected treatment framing in the title and explicitly
identified historical zero-signal failures. No market scores were recomputed.
The earlier text audit remains frozen; its mostly supported factual statements
are not evidence of better prediction or of a hidden generation mechanism.

The [new explorer](astra-revision-explorer.html) renders the exact complete
report, all twenty prompts, all 200 rows, 50 state/generator cells, 25 year rows
and 13 gate checks. Root's browser checks matched every row and all fifty
selector combinations, including both failed grammar slots. The actual guarded
public replay passed, capturing 685 execution files and exact HTML/report/prompt
agreement with zero model calls, financial rescoring or raw-data reads. Static
figure labels now retain six decimal places, so the small positive window-edit
G is not visually rounded to zero. Both result figure and page layout were
visually inspected. CI now requires this replay on both Python versions.

No new draws or prompt tuning follow this failed gate. The next design review
asks whether a separately named, constructed evidence-acquisition task can
isolate a response-dependent query decision; it has not started a new model
experiment and does not revive the stopped financial or local-training branches.


## Iteration 12 — exact actor-visible split integrity

**Problem:** raw task IDs can appear disjoint while the actor sees the same
input. The earlier constructed-query review found 1,152 raw transformations
but only 144 visible kernels, with eight aliases each. That finding lacked a
reusable exact-input checker. Existing temporal, sampling-law and metric tests
already cover their distinct properties, so this iteration does not repackage
those tests or run another easy hosted benchmark.

**Change:** a new standard-library-only checker groups exact final prompt bytes
and optionally supplied token sequences within a declared tokenizer/template
namespace. It retains duplicates, exposes cross-split witnesses, rejects
inconsistent metadata, preserves literal Unicode/newlines and marks missing
or incomparable token evidence explicitly. It cannot attest actual hosted
context or completeness of an omitted population. The [guide](presentation-integrity.md)
includes a CLI and API; no model or network access is required.

**Observed validation:** an independent integer-matrix construction retained
all 1,152 aliases and matched all 144 prompt groups. Raw-index splitting creates
144 cross-split groups and 2,952 equal cross-split pairs; whole-group splitting
creates none. A single moved alias creates exactly one conflict group and seven
pairs. All three fixture populations remain complete. Root ran 72 author,
independent-reviewer and fixture tests in .28 seconds, with Ruff clean. The
normal exclusive-output CLI then wrote the [complete regression](../results/presentation_alias_regression_v1.json).
One additional published-artifact rebuild check passed separately on root
and the author; normal CPU CI now exercises that saved-result identity.
The expected alias collapse was known beforehand: this is engineering
validation, not an empirical discovery or a held-out-policy result.

**Limits and next:** tokenization was not run in the exhaustive fixture and its
token checks remain UNCHECKED. Exact distinctness does not establish semantic
novelty, independent mechanisms or absence of pretraining exposure. All 144
presentations relabel one constructed mechanism. Complete deterministic
checking solves this declared task; no hosted LLM experiment is justified by
that result. The failed financial and matched-prefix branches stay stopped.
A possible separate statistical calibration fixture remains design advice only.

The prior completed financial publication `7e0f7b3` passed both Python CPU jobs
and the training-math job in run `36863716268`; Pages run `36863714569` succeeded.
Root verified the live 200-slot explorer and its exact report identity.

Publication of iteration 12 at `ff19162` passed both Python versions and the
training-math job in CPU run `36866623391`; Pages run `36866623124` succeeded.

## Iteration 13 — seal predictions before confirmation

**Problem:** input disjointness alone cannot prevent a researcher from using
confirmation labels to select or orient its prediction. A numerically correct
single-candidate p-value can become invalid after that reuse. The existing
financial IC evaluator does not have an exact Bernoulli inference contract;
this iteration must not claim to calibrate those financial results.

**Change:** a new standalone staged interface freezes all
prediction vectors before a one-shot reveal. A [finite synthetic plan](sealed-confirmation-plan-v1.md)
uses independent fair-sign null labels and a known planted oracle, with explicit
confirmation-selection and fitted-sign faults. The [guide](sealed-confirmation.md)
explains why faulty arithmetic is retained as an invalid diagnostic.

**Pre-outcome evidence:** root and a separate reviewer independently computed
the exact thresholds without generating any canonical panels: 142 matches
out of 256, null upper count 37/512 for each correct search, and planted-oracle
lower count 128/128. A fixed direction selected after viewing confirmation
labels doubles the theoretical single-panel rejection probability from about
.045656 to .091312. Those known probabilities are mathematical controls,
not observed experimental findings.

**Pre-run implementation validation:** root's final combined suite passed
111 tests in 3.34 seconds; one symbolic-link fixture was skipped because this
Windows host could not create it. Ruff passed. Review found and repaired
malformed-access recovery, ignored preparation-failure markers, source-root
versus loaded-module mismatches, double-read receipt ambiguity, loose STARTED
types and evidence-leaf path checks. The [audit](audits/sealed-confirmation-review-v1.md)
records the checks and their limits. Metadata-only preparation completed with
zero panel generations and fixed thresholds. The protocol and exact source
identities must be publicly verified before the one canonical run. At that pre-run checkpoint, no outcomes,
hosted calls, local training, financial scores or new market periods have been
generated in this iteration.

**Completed result:** all seven frozen public files from `00c17f4` were
anonymously verified at 13:40:23 UTC, before the one canonical execution began
at 13:40:37. All 640 panels completed with zero retries. Correct fixed and adaptive
null counts were 23/512 and 21/512 against upper 37; the known planted oracle
was 128/128 against lower 128. All three checks passed. The three leaking controls
remain structurally invalid; their 39/480/294 naive null rejections are
descriptive, not extra pass conditions. Correct adaptive search rejected on 72
planted panels versus fixed 128, while selecting the planted mask on 69; those
are different endpoints. The [complete report](sealed-confirmation-results-v1.md)
retains all six arms and 82,560 charged requests.

**Actual evidence checks:** an independent implementation reviewer reconstructed
all 640 panels, 8,960 events and 3,840 arm outcomes without importing the driver/core
or regenerating panels. A separate guarded replay passed all 640 panels with
zero prohibited-operation attempts and all 1,291 permitted files unchanged.
Its reviewer authored the core; that participation is disclosed. Root rendered
and inspected the actual-result chart, preserving the report hash. CPU CI now
includes unconditional saved-panel replay on both supported Python versions.

**Limit and next:** these are known synthetic laws and interface regression
evidence. Existing financial results and stopped branches remain unchanged.
A useful maintenance gap remains: current replay checks imported code against
the historical source bytes, so old results need an exact original source tree
when the main implementation eventually changes. A separate bounded design will
consider commit-pinned saved replay; it does not authorize rewriting old
contracts, outcomes or stopped-study source.

Publication of the complete 640-panel evidence at `58dc66e` passed both Python
versions and the training-math job in CPU run `36871820628`; Pages run
`36871818701` succeeded.

## Iteration 14 — replay the actual historical code

**Problem:** the existing saved verifiers bind loaded modules to their original
source bytes. Copying old evidence while importing today's editable package
does not satisfy that contract. A future source change can therefore prevent
historical replay even when the saved results themselves are intact.

**Change:** a small launcher has exactly two
fixed recipes: the complete matched-prefix evidence at `7e0f7b3` and complete
sealed-confirmation evidence at `58dc66e`. It materializes exact regular-file
Git blobs from local objects, runs one isolated child over that source tree and
verifies the expected report and required HTML identities. It does not fetch
objects, install dependencies or rerun the original experiment. Existing frozen
files and current CI routing remain unchanged.

**Evidence before implementation:** root read the three registered report/HTML
blobs directly from the two local commits; every SHA-256 matched its published
identity. Their full tracked trees contain 1,251 files / 56,802,037 bytes and
2,560 files / 99,747,310 bytes respectively. Two design reviews found the narrow
source-isolation benefit justified implementation. Those metadata checks were
kept separate from subsequent actual historical replay.

**Observed validation and correction:** review caught loose summary identities,
missing nested proof validation and a log-flush failure that could otherwise be
reported as success. Initial artificial checks passed, but the first actual
matched-prefix invocation failed on a deep Windows temporary path. Its exact
failure and source remain published. A short, exclusively owned scratch path
and UTF-16 preflight corrected that compatibility issue. The combined revised
suite passed 109 tests with two Windows permission skips; a later test-only
change removed dependence on pytest's path length and its targeted check passed.
Ruff passed. No historical verifier or outcome was changed to make replay pass.

Both real recipes succeeded on the fixed launcher: 200 matched-prefix slots
and exact HTML in 13.047 seconds; 640 sealed panels in 30.938 seconds. Root's
separate inspection matched every committed byte and all 12 / 3 loaded project
module origins. The [actual integration audit](audits/pinned-replay-integration-v1.md)
links the complete records, runtime, preserved failure and validation chronology.
The [guide](reproduce-pinned-studies.md) provides the two commands and prerequisites.

**Limits:** this is reproducibility tooling. It adds no model call, financial
score, synthetic panel or evidence of research-policy improvement. Installed
binary dependencies are recorded rather than reconstructed; process checks
are not an adversarial security sandbox.

Publication at `ff40981` passed both Python 3.11/3.12 jobs and the training-math
job in CPU run `36878839035`; Pages run `36878837388` succeeded. The CPU jobs
exercise the artificial launcher tests and existing saved-study routes; the
two actual historical launcher invocations above remain Windows runtime evidence.

## Iteration 15 — separate evaluated reward gains from training credit

**Question:** fewer failed outputs accounted for much of the original evaluated
RL reward gain. That accounting did not determine which reward components
supplied the training coefficients. A proposed switch to public financial QA
was declined after three design reviews: it would change the task without
resolving the existing research-policy question. No QA corpus or question bank
was downloaded, and no hosted calls were allocated to it.

**Change:** a compact standard-library analysis reconstructs R=-1.01+V+C and
the corresponding leave-one-out advantages and sampled surrogate values from
all four saved correct/permuted training runs. It applies each control's exact
logged permutation jointly to all reward components and retains all 64 groups
and 256 attempts. The [post-hoc plan](reward-credit-plan-v1.md) explicitly
discloses prior knowledge of the outcomes and missing component gradients.

**Observed result:** 62/64 groups have zero direct validity coefficients;
61/63 actual optimizer steps do. The two mixed groups appear in correct seed 23
and permuted seed 29. One additional all-valid group had constant rewards and
skipped its update. This refines interpretation without changing the previous
evaluation results or claiming that RL learned useful prediction. Counts and
coefficient magnitudes are not gradient or Adam-update shares.

**Verification:** review exposed a tolerance accepting an impossible tiny
logged advantage for exactly constant rewards. Exact-zero validation repaired
that case without suppressing genuine tiny nonconstant variation. Direct reward
copies and indexed assignments now also require exact numeric equality.
The combined 64 artificial tests passed in .26 seconds and Ruff passed. One
actual saved-data run completed at 15:08:12 UTC; root's separate 60-digit Decimal
check passed 3,752 comparisons with maximum absolute discrepancy 2.93e-16.
No model, gradient, training, market-data or financial-scoring execution occurred.

The [complete report](reward-credit-results-v1.md) links all groups, the observed
mixed-group example, execution/inspection records, static figure and commands.
All frozen scientific inputs remain unchanged. Internal reviews disclose their
roles; this is post-hoc accounting, not external replication or new causal
learning evidence.

Publication at `21bf13e` passed Python 3.11, Python 3.12 and training-math in CPU
run `36883178509`; Pages run `36883176988` succeeded.

## Iteration 16 — connect the evidence in a compact research note

**Problem:** individual reports preserved their evidence, but a reader had to
assemble the controlled questions, follow-up decisions and scope limits across
many files. That obscured both the agentic implementation and what the financial
results actually establish.

**Change:** a [seven-page English research note](../output/pdf/alpha-research-note-v1.pdf)
connects the original Astra comparison, explicitly post-hoc pool analysis,
prospective matched-prefix test, separate Qwen weight training and controls,
and the saved training-credit finding. Two paper-sized figures read exact
published JSON bytes; no model, training or market assessment ran. The original
figures, results and stopped scientific branches remain unchanged.

**Review and verification:** two internal review lanes corrected winner-versus-
admission counts, control seed naming, comparison populations, remaining masked
information, gate interpretation and gradient-attribution wording. The final
source has 2,581 whitespace-delimited words. The coordinator rendered and
visually inspected all seven final pages and checked 83 source text segments,
page geometry and 18 link annotations. Ruff passed for the two new scripts.
The [build guide](research-note-build.md) records commands, review boundaries,
artifact digests and renderer warnings; it does not claim accessibility
certification or external peer review.

**Limit:** this is a synthesis of existing evidence, not a new algorithm or a
claim of top-conference readiness. Further methodological research requires a
distinct contribution, close prior-art comparison and decisive controls. Merely
repeating the failed comparisons on the same development periods would not
provide that contribution.
