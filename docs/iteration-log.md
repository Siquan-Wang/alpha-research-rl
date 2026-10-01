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

## 8. Actual Astra research agent — implementation verified, collection pending

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
contract-bound staged files match their exact local bytes.

**Limits and next:** no Astra financial candidate has been collected or scored.
Publish and verify the implementation/data contract before collection. The
[execution guide](reproduce-astra-agent-study.md) explains the separate
collection, freeze, publication and assessment stages. Astra inference-time
adaptation is not Astra reinforcement-learning weight updates. The same
previously examined financial periods cannot become an untouched holdout.
