# Independent reward-linkage results review

Reviewed 2026-10-01 from all five saved raw evaluation reports, the declared
freezes, paired analysis JSON, and yearly plot. The reviewer independently
recomputed arithmetic from individual outcomes, then compared it with the
analysis output. No new generation, market scoring, GPU run, policy selection,
or analysis/scorer adjustment was performed in response to outcomes.

This is an internal AI-assisted review conducted separately from the report
author, under the [audit scope statement](README.md). It is not external peer
review, human certification, or statistically independent judgment.

## Completeness and integrity

All five reports contain ten half-years, each with 18 retained records:
eight stochastic plus one greedy draw under each of true and exchanged evidence.
The two new controls therefore contribute the full 360 planned completions;
the original three contribute 540. Original reports retain their earlier
three-checkpoint freezes and timestamps. Both new reports bind the exact
five-checkpoint registry frozen at `2026-10-01T04:58:36.053875+00:00`, before
their entry times `05:00:53.361711` and `05:05:05.404119` UTC.

The unchanged original-trio validation and declared extension validation pass.
Actual source-report byte hashes, original-suite binding, checkpoint identities,
seven-file/scorer/tokenizer contract, pinned snapshot, packages, FP32 sampling
provenance, task dates/purges/support, exact prompt tokens, RNG seeds, completion
slots, EOS/parsing, and same-expression outcomes match. Entry manifest files
equal the result manifests, and both controls' saved token counts match their
token arrays. Regenerating `analyze_linkage` reproduces every corresponding
field of the saved paired JSON exactly. The source-report hash dictionary also
matches actual file bytes.

## Primary direct arithmetic

These are strict/stochastic true-evidence means, retaining all 80 attempts.

| Policy | Usable/all | Mean reward | All-attempt oriented IC contribution |
| --- | ---: | ---: | ---: |
| SFT | 77/80 | -0.051585615 | -0.004085615 |
| Correct RL 23 | 79/80 | -0.020128011 | +0.002371989 |
| Placebo 23 | 78/80 | -0.043159945 | -0.008159945 |
| Correct RL 29 | 79/80 | -0.025405592 | -0.002905592 |
| Placebo 29 | 77/80 | -0.043773216 | +0.003726784 |

Correct-minus-placebo reward is **+0.023031934** for seed 23, decomposing into
**+0.012500000 validity** and **+0.010531934 IC contribution**. For seed 29 it is
**+0.018367624 = +0.025000000 validity -0.006632376 IC contribution**. Seed 29's
predictive contribution and conditional valid IC favor its placebo, despite
the correct run's higher primary reward. All stochastic true-evidence policy
means remain negative and below the uniform-grid reference.

Both placebos also exceed SFT reward, by +0.008425670 and +0.007812399.
Thus an increase from the SFT parent alone does not isolate correct reward
linkage. Positive paired pooled reward differences in both seeds are evidence
about this finite declared utility comparison, not general financial quality.

| Year | Correct minus placebo 23 | Correct minus placebo 29 |
| --- | ---: | ---: |
| 2020 | -0.002057459 | -0.013292594 |
| 2021 | +0.001157314 | +0.004012404 |
| 2022 | +0.030062986 | -0.012874199 |
| 2023 | +0.073700151 | +0.056916264 |
| 2024 | +0.012296676 | +0.057076243 |

The ten half-year effects and annual two-half means were checked, including
negative/zero values. The plot visibly retains both seeds and signed years.

## Evidence intervention and secondary behavior

Correct-minus-placebo evidence-effect interactions are -0.001857068 (seed 23)
and +0.013463129 (seed 29). Seed 29's positive interaction contains +0.012500000
validity and only +0.000963129 IC contribution: its placebo has three failures
under true evidence and two under exchanged evidence. This is not a uniform
predictive grounding improvement. All five policies greedily emit
`ts_mean(returns,60)` throughout both conditions, with identical reward;
strict and same-completion fence-tolerant outcomes agree on every record.

## Publication and limits

Recursive string checks found no absolute Windows/private-zone paths in the
five reports or paired JSON. Retained arrays are token traces or aggregate
metadata; no raw market series or daily IC arrays are published by this analysis.
The output preserves original results and distinctly labels both placebos.

No blocking integrity or arithmetic discrepancy was found. Interpretation must
remain exploratory: two training seeds, fresh divergent control trajectories,
ten dependent development half-years, overlapping labels, policy-dependent
usable subsets, and matched RNG do not support significance, general causal
financial advantage, alpha discovery, or sequential-agent claims. These checks
do not independently authenticate a historical raw calendar or audit backbone
pretraining exposure.

The completed `docs/reward-linkage-results-v1.md` was then checked against this
raw-outcome reconstruction. It accurately retains the two positive pooled
utility contrasts, seed 29's negative IC-contribution contrast, the controls'
own SFT gains, mixed evidence effects and signed years. The README's new study
row also matches. The evidence explorer still covers the original 540 draws;
its description should identify that original-study scope, alongside the new
360 control completions in their linked reports.
