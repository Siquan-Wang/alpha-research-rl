# Exploratory reward-linkage control results

Correctly linked RLOO exceeds its paired reward-permuted control in mean
stochastic reward for both seeds: **+0.023032** for seed 23 and **+0.018368** for
seed 29. This is a narrow, exploratory indication that reward assignment matters
for this pipeline's utility. The predictive component does not improve
consistently: seed 29's gain comes from fewer invalid proposals despite a lower
IC contribution. Correct use of historical evidence also remains inconsistent,
and all five policies have identical greedy behavior.

This follow-up was designed after the
[original financial proposal results](financial-proposal-results-v1.md) were
inspected. Its [control plan](reward-linkage-control-plan.md) was published
before either control trained. The original primary comparison is unchanged.
The completed [five-report analysis](../results/financial_linkage_paired_v1.json)
passed all declared integrity checks; the
[annual plot](../results/financial_linkage_yearly_v1.png) retains both seeds and
negative years. There is no significance or general causal financial claim.

## What this comparison tests

Two additional policies start from the same financial SFT checkpoint as the
correctly linked RL runs. Each control generates its own four-proposal group,
scores every proposal on the true training task, and uniformly permutes the
four rewards before computing leave-one-out advantages. Failure penalties,
identity permutations and repeated rewards remain eligible. The control keeps
its group's reward multiset while randomizing which completion receives which
reward. It does not replay the original RL trajectories.

The controls use training seeds 23 and 29, the corresponding original 16-task
orders, and a separate permutation generator seeded with `700000+seed`. Both
attempt all 16 groups without a quality early stop. A constant group consumes
its permutation draw and is retained, but skips the optimizer step. Training
uses the original FP32, full-softmax, maximum-64-token proposal contract and
AdamW settings. No checkpoint or reward penalty is selected from control
evaluation results.

Conditioned on the current parameters and a sampled group, the expected
**pre-clipping score-function gradient** over uniform reward assignments is
zero. Realized gradients, clipped gradients, Adam updates and subsequent policy
trajectories need not be zero. This is a reward-linkage control, not a frozen
policy, no-gradient baseline or syntax-only training intervention.

Both controls completed 16 groups and 16 optimizer steps. Seed 23 had 64/64
usable training proposals and seed 29 had 63/64. No group had constant rewards;
three and two permutations, respectively, preserved reward assignments because
of repeated values. Every recorded optimizer step changed the adapter digest,
and both saved-adapter reload checks preserved the digest and completion
log-probability exactly. These execution details are retained in the
[training export](../results/financial_linkage_training_v1.json) and its
[trace review](audits/reward-linkage-training-independent-review.md).

## Evaluation and provenance

The three original reports retain their original three-checkpoint freeze and
evaluation timestamps. The new five-checkpoint registry preserves those
checkpoint identities and binds the original report file bytes; it precedes
both control evaluations. The analysis validates the old trio first and then
the exact declared extension. It does not relabel a control as an original RL
role or invent a retroactive five-policy freeze.

The [five-policy registry](../artifacts/development/financial-linkage-suite-freeze-v1.json)
was frozen at `2026-10-01T04:58:36.053875+00:00`. Its checkpoint entries and
original report-byte bindings passed validation. All five reports share the
same prompt/scorer/tokenizer contract hash,
`001dd03271d27ff55a2d1e7763f364afba991655f3747d8bc8e970f573499df6`.

Each policy is evaluated on the same ten development half-years, 2020 H1
through 2024 H2, under true and exchanged probe evidence. Each condition has
eight stochastic draws and one separate greedy draw per task. Matched prompt
tokens, random seeds, task manifests, tokenizer, seven-file scoring contract
and numerical settings are required. The original 540 completions are reused;
the two controls contribute 360 new completions. The strict parser is primary;
the narrow fence-tolerant parser reuses exactly the same completions.

The primary utility is `oriented_future_IC-.01` for usable proposals and
`-1.01` for failures. Orientation uses true historical feedback even when the
actor sees exchanged evidence. Half-years receive equal weight. Invalid
proposals remain in all-attempt denominators; conditional usable IC is
secondary and can compare different subsets.

## All five policies and fixed references

The stochastic primary under true evidence is below. `C` is the sum of usable
oriented ICs divided by **all 80 attempts**; conditional IC uses only the usable
count in its row. Numbers are rounded to six decimals.

| Policy | Mean reward | Usable/all | Failed | C | Conditional usable IC |
| --- | ---: | ---: | ---: | ---: | ---: |
| SFT | -0.051586 | 77/80 | 3 | -0.004086 | -0.004245 |
| Correct RL 23 | -0.020128 | 79/80 | 1 | +0.002372 | +0.002402 |
| Correct RL 29 | -0.025406 | 79/80 | 1 | -0.002906 | -0.002942 |
| Permuted control 23 | -0.043160 | 78/80 | 2 | -0.008160 | -0.008369 |
| Permuted control 29 | -0.043773 | 77/80 | 3 | +0.003727 | +0.003872 |

| Frozen reference | Mean reward | Usable/all | Conditional usable IC |
| --- | ---: | ---: | ---: |
| Uniform choice over 16 formulas, exact expectation | -0.015411 | 160/160 | -0.005411 |
| Best absolute-feedback-IC formula from the grid | -0.015813 | 10/10 | -0.005813 |
| Training-best fixed `delay(returns,1)` | -0.020189 | 10/10 | -0.010189 |

All five stochastic policies remain below the uniform-grid and feedback-greedy
references on the registered utility. Correct RL 23 is approximately tied with
the fixed lag-1 reference, exceeding it by +0.000061; correct RL 29 is lower by
0.005217. Both controls are below that fixed reference. The grid-greedy policy
has access to all grid feedback scores, exceeding the actor's two-probe
information. These are contextual comparators, not evidence of alpha or profit.

## Per-seed correct-minus-control comparisons

The exact accounting identity is
`mean_reward=-1.01+valid_fraction+C`, hence
`reward_difference=change_in_valid_fraction+change_in_C`.

| True-evidence contrast | Reward difference | Validity component | C difference | Conditional IC difference |
| --- | ---: | ---: | ---: | ---: |
| Correct RL 23 minus SFT | +0.031458 | +0.025000 | +0.006458 | +0.006647 |
| Correct RL 29 minus SFT | +0.026180 | +0.025000 | +0.001180 | +0.001302 |
| Control 23 minus SFT | +0.008426 | +0.012500 | -0.004074 | -0.004124 |
| Control 29 minus SFT | +0.007812 | +0.000000 | +0.007812 | +0.008117 |
| Correct RL 23 minus control 23 | +0.023032 | +0.012500 | +0.010532 | +0.010771 |
| Correct RL 29 minus control 29 | +0.018368 | +0.025000 | -0.006632 | -0.006814 |

Correct RL 23 avoids one additional failure relative to its control and also
has a higher IC contribution. Correct RL 29 avoids two additional failures,
but its IC contribution is lower. Its conditional usable IC is also lower,
with denominators 79 versus 77; these are not the same usable subset. Thus both
paired utility differences are positive without consistent predictive-score
improvement. The two-seed reward range is [+0.018368, +0.023032], a descriptive
range rather than a confidence interval.

Both controls also improve on SFT in realized utility, through different
accounting components. Improvement over SFT alone therefore does not establish
that correct reward linkage caused the whole gain. These finite control
trajectories can move validity and formula frequencies despite their zero
conditional expected pre-clipping gradient.

## Historical evidence effects

The evidence effect is **true minus exchanged** for a fixed checkpoint.
The scorer always uses true historical data; fresh completions are generated
under each prompt condition with matched random seeds.

| Policy | Exchanged reward | Usable/all | Failed | Exchanged conditional IC | True-minus-exchanged reward |
| --- | ---: | ---: | ---: | ---: | ---: |
| SFT | -0.048727 | 77/80 | 3 | -0.001275 | -0.002859 |
| Correct RL 23 | -0.018391 | 79/80 | 1 | +0.004161 | -0.001737 |
| Correct RL 29 | -0.026477 | 79/80 | 1 | -0.004027 | +0.001071 |
| Control 23 | -0.043280 | 78/80 | 2 | -0.008492 | +0.000120 |
| Control 29 | -0.031381 | 78/80 | 2 | +0.003712 | -0.012392 |

| Contrast | Exchanged reward difference | Difference in evidence effects |
| --- | ---: | ---: |
| Correct RL 23 minus SFT | +0.030336 | +0.001122 |
| Correct RL 29 minus SFT | +0.022250 | +0.003930 |
| Control 23 minus SFT | +0.005447 | +0.002979 |
| Control 29 minus SFT | +0.017346 | -0.009533 |
| Correct RL 23 minus control 23 | +0.024889 | -0.001857 |
| Correct RL 29 minus control 29 | +0.004904 | +0.013463 |

Correct RL 23 has a negative evidence effect and a negative interaction against
its control. Correct RL 29 has a small positive evidence effect; its larger
interaction against the control decomposes into +0.012500 validity and only
+0.000963 IC contribution. Control 29 has one extra invalid proposal under true
evidence in 2023 H1, which accounts for that validity term. Reward-linkage
sensitivity is therefore distinct from demonstrated use of financial feedback;
this comparison does not show consistent improvement in evidence grounding.

## Every development half-year and year

Both tables show correct RL minus its corresponding control. The interaction
is the difference between their true-minus-exchanged effects. Each half-year
averages eight draws per condition, each year averages its two half-years, and
the overall result weights all ten half-years equally.

| Half-year | True reward, seed 23 | True reward, seed 29 | Interaction, seed 23 | Interaction, seed 29 |
| --- | ---: | ---: | ---: | ---: |
| 2020-H1 | -0.004115 | -0.006425 | -0.005977 | +0.000000 |
| 2020-H2 | +0.000000 | -0.020161 | -0.020161 | +0.000000 |
| 2021-H1 | +0.002931 | +0.007408 | +0.005170 | +0.005170 |
| 2021-H2 | -0.000616 | +0.000616 | -0.000616 | +0.000000 |
| 2022-H1 | +0.060126 | -0.023590 | +0.008914 | +0.000000 |
| 2022-H2 | +0.000000 | -0.002159 | +0.000000 | -0.002159 |
| 2023-H1 | +0.135647 | +0.107539 | +0.000655 | +0.120425 |
| 2023-H2 | +0.011753 | +0.006293 | +0.000000 | +0.000000 |
| 2024-H1 | +0.020576 | -0.012911 | -0.006556 | +0.011195 |
| 2024-H2 | +0.004017 | +0.127064 | +0.000000 | +0.000000 |

| Year | True reward, seed 23 | True reward, seed 29 | Interaction, seed 23 | Interaction, seed 29 |
| --- | ---: | ---: | ---: | ---: |
| 2020 | -0.002057 | -0.013293 | -0.013069 | +0.000000 |
| 2021 | +0.001157 | +0.004012 | +0.002277 | +0.002585 |
| 2022 | +0.030063 | -0.012874 | +0.004457 | -0.001079 |
| 2023 | +0.073700 | +0.056916 | +0.000328 | +0.060213 |
| 2024 | +0.012297 | +0.057076 | -0.003278 | +0.005597 |

Both seeds lose to their control in 2020, and seed 29 also loses in 2022.
Seed 23's 2023 reward difference includes +0.062500 from one avoided failure
among 16 yearly attempts. Seed 29 has the same +0.062500 validity contribution
in both 2023 and 2024. Those gains are concentrated, not uniform improvements
across years. The saved report also retains every policy's task-level outcomes,
exchanged contrasts and decomposition without rounding.

## Greedy and parser diagnostics

All 100 greedy completions across five checkpoints, two conditions and ten
tasks select `ts_mean(returns,60)`. Every proposal is usable. Each policy has
mean reward +0.005007 and oriented IC +0.015007 under either condition; every
greedy RL/control increment and evidence effect is zero. This fixed-formula
behavior scores better than the stochastic policies, but it is shared by the
SFT parent and provides no incremental RL result.

The secondary fence-tolerant parser produces identical metrics for every
checkpoint, half-year, year and decoding condition. The failures in these
reports are invalid DSL expressions such as unsupported function names and
an out-of-range lookback, not a difference in handling fenced JSON.

## Evidence and limits

The [trainer and analysis source review](audits/reward-linkage-control-review.md),
[training/freeze review](audits/reward-linkage-training-independent-review.md)
and [saved-result reconstruction](audits/reward-linkage-results-independent-review.md)
describe their specific checks. The result reviewer independently recomputed
the comparisons from individual retained outcomes and found no blocking
discrepancy. These are internal, AI-assisted development
reviews under the [audit scope statement](audits/README.md), not external peer
review or an independent human certification.

The complete saved reports are
[SFT](../artifacts/development/financial-sft-transfer-v1.json),
[correct RL 23](../artifacts/development/financial-rloo23-transfer-v1.json),
[correct RL 29](../artifacts/development/financial-rloo29-transfer-v1.json),
[control 23](../artifacts/development/financial-placebo23-transfer-v1.json) and
[control 29](../artifacts/development/financial-placebo29-transfer-v1.json).
They retain all prompts, completions, failures, true-data scores and manifests.

This is an exploratory comparison with two training seeds and ten dependent
development episodes. The runs share their SFT parent, task data and evaluation
seeds; overlapping forward returns and repeated formulas add dependence. It is
not a significance test or evidence of general causal financial superiority.
Reward decomposition is accounting, not a causal separation of validity and
financial learning. Correct-minus-control differences can be affected by
finite-sample drift and diverging on-policy trajectories.

The pretrained backbone's exposure to public financial information is not
audited. Chronological local SFT/RL splits do not make this a pretraining-clean
historical forecasting test. The data are industry portfolios from a downloaded
historical vintage, the objective is rank correlation rather than net trading
profit, and the policy makes one proposal per episode. No 2025-or-later samples
reach the actor or scorer. This study does not establish alpha discovery or
sequential research capability, and it does not reopen the stopped
[sequential feasibility branch](sequential-gate-results-v1.md).
