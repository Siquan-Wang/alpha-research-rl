# Constructed feedback curriculum v2

This specification precedes any curriculum GPU run. The fixtures are explicitly
constructed feedback values with no underlying market panel, hidden assessment,
or claim of financial discovery. They diagnose whether a small actor reads its
public state and composes bounded expressions. They are not environment-return
targets, research-optimal labels, or evidence of useful alpha generation.

The registered first execution continues `models/runs/sft-v1/adapter` for two
epochs over all 192 training examples, using AdamW learning rate 1e-4,
completion-token-normalized loss, gradient clipping at 1, and seed 47. That is 384
optimizer updates with epoch checkpoints. It retains the already learned strict
JSON format while testing correction of evidence conditioning. It is a revision
of the earlier diagnosis's suggested base-model/one-epoch feasibility sketch;
neither configuration has been run by the curriculum author. Evaluate the
predeclared final checkpoint against SFT-v1 on the fixed 24 development pairs;
any reported epoch comparison is development, not selection on a final holdout.

## API and partitions

`build_curriculum(split="train"|"dev")` returns `{"examples": [...], "metadata": {...}}`.
Each example has `observation`, `action`, `task_id`, `family`, and `provenance`.
Only `observation` goes into the actor prompt. The other fields support partitioning
and audit. `curriculum_action(observation)` is the complete transparent teacher;
it does not consume any task, family, category, or provenance metadata.

The training partition contains 32 underlying tasks (seeds 5000–5031), each with
two control, two selection, and two generation fixtures: exactly 192 examples,
64 in each category. Four training expression families cover observed returns,
volume transforms, price transforms, and volatility. The development partition
contains twelve tasks (seeds 6000–6011) in two disjoint families: mixed composition
and restricted return features. Task/family assignment precedes deterministic
candidate-order permutations; every variant of a task stays in its partition.

`build_counterfactual_pairs()` returns 24 development pairs with `pair_id`,
`task_id`, `family`, `left`, and `right`. Twelve pairs test select/stop or changing
the selected ID; twelve test propose versus mutate. Flattening these pairs gives
the 48 development examples. Within a pair, only visible screening mean ICs change;
candidate order, scores' support, history, orientation, budget, and provenance stay
fixed. The expected action changes. Development targets and measured results must
not be used for gradient updates or example selection.

## Visible teaching rules

All fixtures have four initial expressions, supported features, initial-candidate
provenance, screen evidence with 80 defined dates/coverage 1, consistent orientations,
and charged history. The IC values are synthetic labels, not measurements. Ordinary
screen IC standard deviation is 0.05; diagnostic fixtures use 0.25. Both positive
and negative IC occur for every selected/mutated ID. Train selection and mutation
targets are each exactly eight examples for IDs 0, 1, 2, and 3.

The predeclared heuristic is:

1. Stop after an existing submission, or when fewer than two budget units remain.
2. Acquire stability for a screened factor with IC standard deviation above 0.15
   if its stability has not been acquired.
3. Screen the lowest unscreened ID when at least three units remain.
4. Among eligible scores (finite IC, coverage at least 0.8, at least 64 defined
   dates), choose highest absolute IC, breaking ties by lowest ID.
5. Stop if that IC magnitude is below 0.04. With two units left, select it.
6. With more budget and generation enabled, propose `ts_mean(parent,3)` for
   magnitude below 0.14; otherwise mutate the visible parent with
   `ts_mean(parent,10)`. Generation-disabled states select instead.

Selection fixtures start with budget six, then spend four screening units,
leaving two. Generation fixtures start with ten and spend four, leaving six.
The different research phase is therefore visible; no hidden category produces
conflicting labels for the same observation. The fixed lookback rule is a grammar
teaching exercise, not a justified improvement to the parent factor. Proposed
expressions are validated by the actual safe DSL in CPU tests and differ from
every expression already in their pool. Restricted-feature development fixtures
contain no volume expressions.

These rules deliberately leave broader policy optimization to actual environment
rollouts. In particular, IC standard deviation is not a calibrated uncertainty
bound, the 0.04 threshold provides no error control, and a generated expression
must still be screened before selection in the real environment.

## Before and after training

CPU checks must pass for deterministic rebuilding, exact category/ID balance,
mixed signs, budget accounting, evidence/history/selection coherence, supported
DSL expression legality, and seed/family disjointness. Counterfactual pairs must
change only visible scores and require different actions. Capture this plan,
dataset metadata/digest, exact examples, and source version before any GPU run.

Report development exact-action accuracy by category, counterfactual pair success
(both sides correct), selected-expression identity under permutations, JSON/EOS
validity, and results separately for each held-out family. No assessment rewards
exist for these fixtures. A rise in these diagnostics is evidence of controlled
state-conditioned action/grammar learning only. Actual usefulness and RL improvement
require separate matched-budget synthetic episodes with feedback-only observations,
predeclared terminal rewards, null tasks, and a frozen untouched evaluation design.
