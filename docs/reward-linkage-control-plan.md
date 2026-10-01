# Exploratory reward-linkage control: frozen plan

Written 2026-10-01 after inspecting the original financial proposal results and
before either control run is trained. This is one bounded exploratory follow-up,
not part of the original registered comparison. It tests whether the observed
changes depend on linking a sampled proposal to the reward that proposal earned.
The original results, primary reward, checkpoints and labels remain unchanged.
This study does not reopen the failed sequential-acquisition branch.

## Question and control mechanism

For each original RL seed, train one additional control from the **same financial
SFT checkpoint**. The control generates its own fresh on-policy groups. Evaluate
all four proposals on the task's true training data, then uniformly permute the
four rewards before computing the leave-one-out advantages. The group keeps its
reward multiset, including invalid-action penalties, while the assignment to
individual completions is randomized.

This is a reward-linkage placebo. It is not syntax-only training, a no-gradient
baseline, a frozen model, or an exact replication of the original sampled
trajectories. Once parameters diverge, the controls' own on-policy samples and
true reward multisets can differ from the correctly linked runs.

## Exact training contract

There are exactly two control runs, paired with original training seeds 23 and
29. Both initialize from `financial-sft-v1`, whose recorded final parameter
digest is
`2de3acf5ae1f6dee2b5b335f083e2c2b5e76f224a1f1de7eb2b151d709a01c53`.
Record the actual adapter-file hashes before loading and verify the initialized
parameter digest. Preserve the original SFT checkpoint and both original RL
checkpoints without modification.

For each seed, use the same 16 training tasks as its original correctly linked
run: H1 in even years and H2 in odd years from 2002 through 2017, in that seed's
original deterministic permutation. Generate K=4 new completions per task,
using the original training seed/sampling schedule and prompt contract. Do not
replay the original completions or reuse their rewards. The control must remain
on-policy with respect to its own current parameters.

Keep the same rank-8 trainable adapter configuration, FP32 execution, disabled
TF32, disabled generation-config model-default merging, temperature 1, top-p 1,
top-k 0, maximum 64 completion tokens and required EOS. Compute the complete
autoregressive completion log-probability, including EOS and excluding prompt
tokens. Use AdamW learning rate `1e-5`, betas `(0.9,0.999)`, weight decay zero,
gradient-norm clipping at one, and no KL penalty or entropy term.

Each run executes **all 16 groups**. There is no quality-gate early stop.
Constant-reward groups retain their full logs and skip the optimizer step when
all advantages are zero. Both original runs actually completed 16 groups, so
this preserves their attempted-group budget. Optimizer-step counts need not
match when constant groups differ. Do not add groups to compensate.

Create a dedicated permutation generator `np.random.default_rng(700000 + seed)`.
Call `permutation(4)` exactly once per group, in group order; do not use this
generator for task order or token sampling. For returned permutation `p`, define
`assigned_reward[i] = true_reward[p[i]]`. All 24 permutations, including the
identity and permutations that leave repeated reward values unchanged, are
allowed. Do not force derangements, shuffle only valid outcomes, replace
penalties, resample inconvenient permutations, or condition the permutation on
completion content. Draw and log the permutation even for a constant group.

The assigned rewards feed the unchanged RLOO calculation:

```text
A_i = assigned_reward[i] - sum(assigned_reward[j] for j != i) / 3
loss = -(1/4) * sum_i A_i.detach() * log pi_theta(completion_i | prompt_i)
```

The true outcomes remain unchanged in each sample's evaluator record. Store
assigned rewards separately so they cannot be mistaken for financial scores.

## What the placebo does mathematically

Condition on the current parameters, prompt, four generated completions and
their four true rewards. Uniform permutation gives every completion the same
expected assigned reward, the group mean. Its expected leave-one-out advantage
is therefore zero. Since its score-function gradient is fixed under this
conditioning, the expected **pre-clipping policy gradient**, over the reward
permutation alone, is zero.

This statement is not that a realized gradient is zero. It is also not that
clipped gradients, Adam parameter updates, parameter trajectories or evaluation
effects have zero expectation: clipping and adaptive optimization are nonlinear,
and optimizer history and future samples depend on previous perturbations. The
control can change validity or formula frequencies by finite-sample drift. Its
within-group reward distribution can also depend on the control's current
policy. These limitations are part of the mechanism being tested, not reasons
to remove unsuccessful control runs.

Before training, artificial checks should cover reward-multiset preservation,
exact permutation indexing, repeated rewards, invalid penalties, constant-group
zero advantages and optimizer skipping, and zero average un-clipped score
gradient over an exhaustive set of all 24 permutations for a fixed artificial
group. This does not require another real-data experiment.

## Required training and checkpoint evidence

Write an entry manifest before optimization, including this plan's version,
source hashes, parent adapter hashes, model/tokenizer revision, optimizer,
precision/sampling settings, task order, training seed and permutation seed.
For every group preserve:

- Task manifest and exact actor observations/prompt tokens.
- All four completion texts/token IDs, EOS flags, parsing and true evaluator
  outcomes, including invalid and unscorable proposals.
- True reward vector, permutation indices, assigned reward vector and assigned
  leave-one-out advantages, with enough information to reconstruct them exactly.
- Recomputed pre-update completion log-probabilities, pre-clipping gradient norm,
  whether an optimizer step occurred, and before/after parameter digests.

Retain constant groups and every failure. Save both final controls and perform
the same FP32 adapter reload/digest/log-probability check. Publish aggregate and
trace evidence under the existing privacy/data rules; do not redistribute raw
market arrays or model weights.

## Freeze and evaluation provenance

Before evaluating either control, write a new joint registry containing the
saved hashes of **all five** checkpoints: the original SFT, original correctly
linked RL 23/29, and control 23/29. Bind the byte-level hashes of the three
already completed original evaluation reports into that registry as well.
Use `original_reports={label: {file: basename, sha256: file_bytes_sha256}}`
and retain `original_frozen_suite_sha256`, computed from canonical JSON of the
unchanged original three-checkpoint suite (sorted keys, compact separators).

The original reports retain their genuine earlier three-checkpoint freeze and
evaluation timestamps. The new registry is frozen before **control evaluation**;
it is not retroactively described as preceding the original evaluations. Do not
rewrite original manifests, rename a placebo as an original RL role, or force
five reports through a three-role analysis by silently changing provenance.

Evaluate each control once on the same ten development half-years, 2020 H1
through 2024 H2, with eight stochastic draws plus one greedy draw under both
true and exchanged probe evidence. Generate fresh completions for each evidence
condition. Use the same seeds, `80000 + task_index*100 + draw`, with greedy draw
99. Keep the original true-data scorer, feedback-fixed orientation, strict JSON
primary parser, same-completion fence-tolerant secondary parser, support rules,
valid reward `oriented_future_IC-.01`, and failure reward `-1.01`.

The original three reports are reused, not regenerated. Their seven-file
prompt/scorer contract, tokenizer fingerprints and numeric contract must match
the controls exactly; the original shared contract hash is
`001dd03271d27ff55a2d1e7763f364afba991655f3747d8bc8e970f573499df6`.
Analysis validates each report against its actual applicable freeze, then
validates the five-way checkpoint registry, pinned snapshot, all ten task
manifests, draw counts, random seeds and paired prompt tokens. A mismatch stops
the combined analysis rather than being repaired by relabeling reports.

The retained data panel stays capped at 2024-12-31. No 2025-or-later samples
reach the actor or scorer and no policy outcomes from those periods are used.
The upstream downloaded ZIP can contain later rows; this is a retained-panel
and scoring restriction.

## Predeclared comparisons and interpretation

The primary exploratory contrast is **correctly linked RL minus its
corresponding reward-permuted control**, separately for seeds 23 and 29, under
true evidence. Also report both controls and both original RL policies relative
to the common SFT parent. Do not choose a favorable seed or combine two seeds
as independent market replications.

For every policy report the true-minus-exchanged evidence effect. For each seed,
report the difference in that effect between correct RL and its control, as
well as their respective interactions relative to SFT. Retain exchanged-condition
reward contrasts. Average draws within half-years, weight the ten half-years
equally, and report all ten differences and all five annual means, including
negative and zero values. Keep greedy results separate.

For every comparison preserve the exact validity accounting:

```text
mean_reward = -1.01 + valid_fraction + valid_IC_sum/all_attempts
reward_difference = change_in_valid_fraction
                  + change_in_all_attempt_IC_contribution
```

Include usable/failed counts and conditional usable IC with its denominator.
The IC-contribution term can change when the usable subset changes; this is
accounting, not a causal separation of syntax learning from financial learning.
Retain fixed lag-1 and uniform-grid references as context; no reward-penalty
tuning or new checkpoint selection belongs to this control study.

If correctly linked RL does not consistently exceed its corresponding control,
the earlier reward gains cannot be attributed confidently to correct reward
assignment in this small experiment. If it does, that is evidence of
reward-linkage sensitivity under this particular pipeline, with only two runs
and ten dependent development episodes. Neither outcome establishes a general
causal financial advantage, alpha discovery, significance, useful sequential
research, or clean historical forecasting by a pretrained model. The backbone's
pretraining exposure to public financial information is not audited here.

## Bound and stop rule

This authorization covers only two control training runs, their two frozen
evaluations, and the five-report analysis. Attempted training groups total 32
and sampled training completions total 128. New evaluation completions total
360; existing original reports contribute the other 540 retained completions.
There are no additional seeds, hyperparameter sweeps, quality-triggered retries,
new datasets or sequential-controller runs. Expected GPU work is approximately
15 minutes, subject to actual runtime; the enclosing work-window deadline takes
precedence. Record any incomplete run transparently instead of treating partial
evidence as the planned five-report comparison.
