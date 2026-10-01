# Financial proposal policy: frozen development evaluation

This study completed real Qwen3-0.6B LoRA training on chronological French49
tasks: 96 supervised updates and 31 RL optimizer steps across two runs. Both RL
policies improved sampled mean reward relative to their common SFT parent, but
most of the increase came from two fewer invalid formulas per 80 proposals.
Correct feedback did not consistently outperform exchanged feedback, every
greedy policy chose the same formula, and nearly all usable proposals matched
teacher formulas or their historical rank behavior. These results establish
policy updates and a small change in sampled behavior; they do **not** establish
new alpha discovery, robust financial improvement, or learned sequential research.

The machine-readable source is
[`financial_proposal_paired_v1.json`](../results/financial_proposal_paired_v1.json).
Its statistics were recomputed from individual saved outcomes after validating
all three frozen checkpoints, ten task manifests, paired prompt tokens, draw
counts, random seeds, parser outcomes, chronology, support counts, and the shared
evaluation contract. The [analysis plan](financial-analysis-plan.md) was written
before transfer results were inspected. All figures below use strict JSON and
stochastic decoding unless explicitly labeled otherwise.

## Experiment and actual training

The [registered study](next-research-study.md) uses 49 industry portfolios from
the pinned French daily-return snapshot, with a five-session forward-return
target and a returns-only bounded expression grammar. Each observation contains
two computed historical probes and their three subwindow summaries. The actor
proposes one formula. The evaluator fixes its sign from the preceding half-year's
feedback IC, then scores its next-half-year IC. Both periods purge their final
five signal rows. A usable proposal receives oriented IC minus .01; an invalid or
unscorable proposal receives -1.01. The .01 is an abstract common research cost,
not an estimate of financial trading costs.

SFT uses 32 half-years from 2002–2017, repeated for three epochs. Its teacher
chooses the greatest absolute feedback IC among 12 fixed formulas. That teacher
has more information than the actor's two probes: this is explicitly privileged
distillation. The teacher does not use that task's assessment score. RL uses
training assessment outcomes as rewards; those outcomes are training data.
Each RL run starts from the same SFT checkpoint and samples four proposals on
each of 16 prespecified training tasks, in seed-dependent order.

| Run | Seed | Optimizer updates | Sampled RL groups | Usable RL proposals | Groups with legal quality variation |
| --- | ---: | ---: | ---: | ---: | ---: |
| SFT | 61 | 96 | — | — | — |
| RLOO | 23 | 16 | 16 | 63/64 | 16 |
| RLOO | 29 | 15 | 16 | 64/64 | 15 |

The rank-8 adapter has 2,293,760 trainable parameters. Seed 29's last group had
identical rewards and exact zero advantages, so no optimizer step occurred.
Every actual RL step changed the recorded parameter digest. Both runs passed
the predeclared eight-group quality gate. Leave-one-out advantages, digest chains,
task order and saved prompt traces were independently checked in the
[training evidence audit](audits/2026-10-01-financial-training-evidence.md).
The [public training export](../results/financial_training_v1.json) preserves
the underlying evidence. Actual updates are a mechanism result, not proof of
financial improvement.

Financial training uses FP32 with TF32 disabled, temperature 1, top-p 1, top-k 0
and a maximum 64 generated tokens, including required EOS. The initial BF16
sampling-law probe failed the numerical gate; the retained FP32 probe reduced
maximum cached-versus-full-forward token-log-probability disagreement from
0.464909 to approximately 0.0000262. Saved reload checks for all three final
adapters have identical digests and zero completion-log-probability difference.
These bounded checks do not establish universal bitwise equivalence. See the
[policy audit](audits/2026-10-01-financial-policy-review.md).

The checkpoint suite was frozen at **2026-10-01 04:13:02 UTC**. Evaluation uses
all ten half-years in 2020–2024, with eight independently drawn completions per
task and evidence condition, plus one greedy completion. Corresponding draws
reuse the same random seeds across checkpoints and conditions. All three runs
share contract hash
`001dd03271d27ff55a2d1e7763f364afba991655f3747d8bc8e970f573499df6`.
The relevant seven-file prompt/scorer contract and tokenizer fingerprints match;
whole-package source hashes differ because separate analysis code was added.
These years had already been used for numerical benchmark development, so this
is a **development transfer evaluation**, not an untouched final holdout.
The retained panel ends in 2024; no 2025-or-later policy outcomes were evaluated.

## Primary reward and validity results

Each row averages eight draws within each half-year and then weights all ten
half-years equally. “Valid IC” conditions on usable proposals and therefore has
a policy-dependent denominator. “IC contribution” divides the sum of valid
oriented ICs by **all** 80 attempted proposals.

| Policy | Evidence | Usable / all | Mean reward | Valid oriented IC | IC contribution |
| --- | --- | ---: | ---: | ---: | ---: |
| SFT | True | 77/80 | -0.051586 | -0.004245 | -0.004086 |
| RL 23 | True | 79/80 | -0.020128 | +0.002402 | +0.002372 |
| RL 29 | True | 79/80 | -0.025406 | -0.002942 | -0.002906 |
| SFT | Exchanged | 77/80 | -0.048727 | -0.001275 | -0.001227 |
| RL 23 | Exchanged | 79/80 | -0.018391 | +0.004161 | +0.004109 |
| RL 29 | Exchanged | 79/80 | -0.026477 | -0.004027 | -0.003977 |

The exact identity is `mean reward = -1.01 + valid fraction + IC contribution`.
Consequently, the true-evidence RL gains decompose as follows:

| RL seed | Reward change from SFT | Failure-penalty component | IC-contribution component | Conditional valid-IC change |
| --- | ---: | ---: | ---: | ---: |
| 23 | +0.031458 | +0.025000 | +0.006458 | +0.006647 |
| 29 | +0.026180 | +0.025000 | +0.001180 | +0.001302 |

The observed across-seed mean gain is +0.028819 and range is
[+0.026180, +0.031458]. This two-run range is not a confidence interval. The
positive IC-contribution remainders are smaller than the failure component, and
can also reflect which proposals became usable. They are not a causal estimate
of improved factor quality on a fixed successful subset.
This is validity accounting of evaluated outcomes, not evidence that training
learned only syntax or that its gradient-level learning mechanism has been isolated.

The SFT failures were the unsupported operator `ms_mean`, the unsupported
operator `ts_sub`, and lookback 80 outside the allowed range. Both RL runs retain
the `ms_mean` failure and avoid the other two on the matched draws. These are
formula-validity failures, not missing JSON fences. Reparsing the same outputs
with the narrow whole-fence parser changes none of the reported results.

## Fixed and finite-grid comparisons

The lag-1 formula was selected using training-only mean reward and frozen before
transfer. It is not the best formula selected after seeing these outcomes.
Uniform-grid performance is the exact expectation over the 16 predefined
formulas, while feedback-greedy observes all 16 feedback scores and thus has more
information than the actor's two probes.

| Reference | Mean reward | Oriented IC | Usable evaluations |
| --- | ---: | ---: | ---: |
| Fixed `delay(returns,1)` | -0.020189 | -0.010189 | 10/10 |
| Uniform 16-formula grid | -0.015411 | -0.005411 | 160/160 |
| Feedback-greedy 16-formula grid | -0.015813 | -0.005813 | 10/10 |

RL 23's sampled reward is only +0.000061 above fixed lag-1; RL 29 is -0.005217
below it. Both sampled RL policies remain below the uniform-grid expectation
and feedback-greedy reference. Their conditional valid ICs exceed the fixed
formula's IC, but their remaining failures are penalized in the primary reward.
No conclusion should replace that full denominator with only successful draws.

## Correct versus exchanged evidence

The intervention exchanges the two complete probe metric bundles within the
current episode, retaining the probe identities. It then generates new
completions with matched seeds; the true data and terminal scorer remain fixed.
This tests sensitivity to the correct assignment of those summaries, not every
possible use of market information.

| Policy | True minus exchanged reward | Grounding interaction relative to SFT |
| --- | ---: | ---: |
| SFT | -0.002859 | — |
| RL 23 | -0.001737 | +0.001122 |
| RL 29 | +0.001071 | +0.003930 |

Both relative interactions are positive, but RL 23 still scores worse with the
correct evidence than with exchanged evidence. Its positive interaction means
the negative effect became smaller. RL 29 has a small positive correct-evidence
effect. Validity is unchanged between evidence conditions within each policy,
so these particular effects concern sampled predictive contributions rather
than failure counts. The mixed signs do not establish consistent useful
feedback grounding.

## Every evaluation period, including negative and zero effects

“Interaction” is `(RL true − RL exchanged) − (SFT true − SFT exchanged)`.

| Half-year | RL 23 − SFT | RL 29 − SFT | Interaction 23 | Interaction 29 |
| --- | ---: | ---: | ---: | ---: |
| 2020 H1 | -0.005977 | +0.000000 | -0.007840 | +0.000000 |
| 2020 H2 | +0.000000 | +0.000000 | -0.020161 | +0.000000 |
| 2021 H1 | +0.002931 | +0.005170 | +0.005170 | +0.005170 |
| 2021 H2 | -0.000616 | +0.000000 | -0.000616 | +0.000000 |
| 2022 H1 | +0.047351 | +0.014847 | +0.042460 | +0.033545 |
| 2022 H2 | +0.000000 | +0.000000 | +0.000000 | +0.000000 |
| 2023 H1 | +0.128036 | +0.120425 | -0.006956 | -0.007611 |
| 2023 H2 | +0.004180 | +0.004180 | +0.000000 | +0.000000 |
| 2024 H1 | +0.008212 | -0.009885 | -0.000841 | +0.008193 |
| 2024 H2 | +0.130459 | +0.127064 | +0.000000 | +0.000000 |

| Year | RL 23 − SFT | RL 29 − SFT | Failure component, each seed | Interaction 23 | Interaction 29 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2020 | -0.002989 | +0.000000 | +0.000000 | -0.014000 | +0.000000 |
| 2021 | +0.001157 | +0.002585 | +0.000000 | +0.002277 | +0.002585 |
| 2022 | +0.023676 | +0.007424 | +0.000000 | +0.021230 | +0.016773 |
| 2023 | +0.066108 | +0.062302 | +0.062500 | -0.003478 | -0.003805 |
| 2024 | +0.069336 | +0.058589 | +0.062500 | -0.000421 | +0.004097 |

The largest reward gains occur in 2023 and 2024, when one fewer invalid proposal
per year contributes +0.0625 to each annual difference. The main positive
grounding interaction occurs in 2022 H1. This heterogeneity is retained rather
than summarized as a uniformly improved policy.

![Paired yearly reward differences and grounding interactions for both RL seeds](../results/financial_proposal_yearly_v1.png)

## Greedy mode and factor behavior

Every checkpoint, on every task, under both evidence conditions, greedily emits
`ts_mean(returns,60)`. All 10 greedy proposals per condition are usable. Their
mean reward is +0.005007 and oriented IC is +0.015007. All greedy RL-minus-SFT
differences and evidence effects are exactly zero. This favorable fixed-mode
score does not show an RL improvement and cannot replace the registered
stochastic comparison.

Feedback-only diagnostics compare generated factors with the 12 teacher
formulas using absolute mean daily cross-sectional Spearman correlation.
“Near-exact” means at least `1 − 1e-10`, with the registered coverage/date support.
The calculation uses historical factor ranks, not future assessment targets.

| Policy | Near-exact teacher matches / usable primary draws | Near-exact / all unique task-expression pairs across conditions and decodings |
| --- | ---: | ---: |
| SFT | 75/77 | 33/35 |
| RL 23 | 76/79 | 32/35 |
| RL 29 | 77/79 | 34/36 |

The two dominant primary formulas, `ts_std(returns,20)` and
`ts_mean(returns,60)`, account for 63/77, 62/79 and 65/79 usable draws,
respectively. The remaining non-equivalent task/formula pairs are simple
lookback variations such as mean-8, mean-30 and standard-deviation-60; their
nearest teacher correlations are approximately 0.829–0.877. These are descriptive
differences, not demonstrated novel financial mechanisms. Distinct ASTs or
parameter values alone do not establish independent signals or alpha discovery.

## Exploratory sensitivity to the invalid-action penalty

This diagnostic was designed **after** inspecting the transfer results. It
rescored the same saved primary proposals under
`R(lambda) = valid_IC_sum/N − .01 − lambda*(1 − valid_fraction)`; it generated no
new samples and selected no checkpoint. The registered primary remains
`lambda=1`. At `lambda=0`, failures contribute no predictive score, which is a
surrogate convention rather than a measured zero IC for an invalid formula.

The observed RL-minus-SFT gains are +0.006458 and +0.001180 at lambda zero,
compared with +0.031458 and +0.026180 at the registered lambda one. On these
fixed samples, RL 23's mean utility crosses the uniform-grid reference at
approximately lambda .622625 and RL 29's at .200418. Thus the uniform-grid
ordering depends on how utility penalizes failures. Changing that penalty
changes the research objective; these descriptive crossing points are neither
recommended settings nor evidence that the primary comparison was won.

The [saved sensitivity values](../results/financial_penalty_sensitivity_v1.json)
and [plot](../results/financial_penalty_sensitivity_v1.png) preserve the complete
declared penalty grid. This exploratory analysis leaves all registered primary
results and the separate sequential-study gates unchanged.

## Evidence and limits

Full saved reports preserve prompts, generated tokens, parsing, failures and
scoring outcomes: [SFT](../artifacts/development/financial-sft-transfer-v1.json),
[RL 23](../artifacts/development/financial-rloo23-transfer-v1.json),
[RL 29](../artifacts/development/financial-rloo29-transfer-v1.json).
Historical rank diagnostics are available for
[SFT](../artifacts/development/financial-sft-rank-diagnostics-v1.json),
[RL 23](../artifacts/development/financial-rloo23-rank-diagnostics-v1.json) and
[RL 29](../artifacts/development/financial-rloo29-rank-diagnostics-v1.json).
The [independent analysis review](audits/financial-analysis-independent-source-review.md)
checked the aggregation and identified a shared-chronology validation gap, which
was corrected and covered by artificial tests before analysis.

There are ten dependent half-years and five calendar years, not 80 independent
markets. Five-session labels overlap; both RL runs share an SFT parent and
training history; matched seeds couple the comparisons. Two RL seeds and eight
draws per task leave substantial training and Monte Carlo uncertainty. No
significance test or independent-draw confidence interval is claimed. The study
uses industry portfolios, restricted return-only formulas, a small privileged
teacher curriculum and one proposal per episode. It evaluates predictive rank
correlation rather than executed trades, portfolio risk or net profitability.
The downloaded historical data can be revised and are not a point-in-time data
vintage from each assessment period.

The pretrained backbone's corpus exposure is not audited here. Chronological
splits and removal of dates from prompts constrain this project's local SFT/RL
and scoring; they do not certify that Qwen never encountered public factor
definitions, financial information or benchmark-period data during pretraining.
This is therefore not a pretraining-clean historical forecasting test.

The separately registered [CPU feasibility gate](sequential-gate-results-v1.md)
has now failed: additional historical evidence helped its privileged ridge
selector in the pooled mean but harmed one forward fold and did not beat the
fixed lag-1 reference. The prescribed sequential-training branch stops; no
GenAI candidate bank or controller is trained for it. This measured failure
does not establish impossibility, and the present contextual-bandit result
remains separate from evidence of a learned research agent.
