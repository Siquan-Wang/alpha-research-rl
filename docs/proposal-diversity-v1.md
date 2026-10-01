# Saved financial proposal diversity, version 1

This descriptive analysis was specified on 2026-10-01 before computing its
five-policy results. It uses the 900 saved strict-parser proposals from the
frozen SFT, correct-reward RL seeds 23/29, and permuted-reward controls 23/29.
It performs no model generation, checkpoint selection, future-label scoring,
or post-2024 evaluation. Invalid proposals remain in every attempt denominator.

## Method fixed before calculation

Validate the original three-policy study and declared five-checkpoint
extension using the existing linkage validator, including original report-byte
bindings, shared prompts/seeds/tasks/scorer, and actual checkpoint identities.
Calculate true and exchanged evidence separately, with eight stochastic draws
and one greedy draw per task/condition. Preserve all ten half-year task cells.
Greedy observations are descriptive and are not substituted for stochastic ones.

Report raw completion-text and attempted-expression-string frequencies, plus
canonical AST frequencies for all attempts with a parseable expression. These
all-attempt frequencies can include invalid/unsupported expressions. Separately
report strict usable proposals: exact strings, canonical ASTs, unique counts,
Shannon entropy in natural logarithms, effective number exp(entropy), and
Herfindahl concentration sum(p squared). These distribution statistics use the
valid-proposal denominator; an all-invalid cell has null entropy/concentration.
Here usable/valid means the saved strict scorer returned status `ok`, including
both feedback and assessment support; it does not mean merely grammatical
syntax or a favorable future score. Normalized entropy divides by the logarithm
of the observed unique valid forms, not the size of the expression grammar.
Top-one and top-three valid-formula exposure use both valid and all-attempt
denominators. Ties are resolved by canonical AST lexical order for display only.
Probe reuse and membership in the twelve-formula teacher grid are canonical-AST
matches; neither is a semantic equivalence test. Counts of actual SFT target
membership and the four reserved grid forms are also descriptive.

Use the published feedback-only rank diagnostics for each task/canonical AST
when their union covers a control proposal. Require the pinned snapshot, exact
task/feedback manifest, twelve teacher references, support thresholds, and
1e-10 near-equivalence tolerance. Reject conflicting duplicate diagnostics.
If the original three files do not cover all valid control proposals, run at most
the two control diagnostic CLIs on the pinned raw snapshot, without constructing
assessment targets. Preserve the original three diagnostic files byte for byte.

Occurrence-weighted rank-equivalent exposure is reported within the same
condition and decoding as each saved proposal. Also report unique task/AST
counts, supported counts, nearest-reference similarities and paired coverage.
Adequate support requires paired-cell coverage at least .8 and valid dates at
least max(min(20,L),ceil(.8L)), where L is the purged feedback signal length.
Near equivalence means abs(mean daily cross-sectional Spearman) at least
1-1e-10. This recognizes sign and monotone aliases on that particular feedback
panel; it is not universal formula identity or evidence of independent alpha.

The calculation never filters proposals by accuracy or chooses formulas from
future scores. Repeated draws share episodes and are not independent market
observations. No significance tests, novelty bonus, alpha-discovery claims,
profitability claims, or additional predictive advantage are inferred from
strings, AST counts, entropy, or feedback rank similarity.

## Reproduction

The CLI reads all five saved transfer reports and all five rank files by
default. The original three files alone missed three control task/formula
pairs, so the two bounded feedback-only control diagnostics are required.
An explicit diagnostic file set can be supplied with repeated `--diagnostic`
arguments. Source identities use public basenames and
SHA256 of actual bytes. The output contains aggregate frequencies/support only,
without prompt/completion token arrays, raw market arrays, or daily correlations.

```powershell
python -m alpha_research_rl.proposal_diversity --output .local/financial-diversity-reproduction.json
```

## Observed results

All 900 strict proposal slots passed the existing five-policy provenance
validator. There are 881 usable proposals and 19 invalid/unscorable attempts;
all 19 remain represented. The usable proposals contain 13 pooled exact
strings and 13 canonical ASTs. Of the usable proposals, 861 match a teacher-grid
AST and are near-exact teacher rank equivalents on their matched feedback
panels. The remaining 20 occurrences occupy five task/AST pairs. Across all
policies and conditions there are 45 distinct valid task/AST pairs, of which
40 are near-exact teacher equivalents; all 45 have adequate paired support.
These are repeated exposures to formulas on shared panels, not 45 independent
discoveries or independent market observations.

The stochastic cells below each contain all 80 attempts (eight draws per
half-year). Exact-string and canonical-AST unique counts are identical within
these observed cells. Entropy, effective number and concentration condition on
usable proposals. Counts and raw frequencies, all ten task cells, support and
the matched source mapping are retained in
[the JSON report](../results/financial_proposal_diversity_v1.json).

| Policy | Evidence | Usable/80 | Unique valid strings/ASTs | Entropy (nats) | Effective number | Concentration |
|---|---|---:|---:|---:|---:|---:|
| SFT | True | 77 | 9/9 | 1.366298 | 3.920808 | .347276 |
| RL 23 | True | 79 | 9/9 | 1.400895 | 4.058832 | .323826 |
| RL 29 | True | 79 | 10/10 | 1.359110 | 3.892726 | .357475 |
| Permuted-reward control 23 | True | 78 | 10/10 | 1.461279 | 4.311470 | .324458 |
| Permuted-reward control 29 | True | 77 | 8/8 | 1.357773 | 3.887524 | .334458 |
| SFT | Exchanged | 77 | 9/9 | 1.396430 | 4.040748 | .336482 |
| RL 23 | Exchanged | 79 | 9/9 | 1.500863 | 4.485560 | .294985 |
| RL 29 | Exchanged | 79 | 9/9 | 1.345863 | 3.841500 | .357475 |
| Permuted-reward control 23 | Exchanged | 78 | 9/9 | 1.406696 | 4.082444 | .335963 |
| Permuted-reward control 29 | Exchanged | 78 | 9/9 | 1.484524 | 4.412864 | .299474 |

The most frequent valid formula is `ts_std(returns,20)` for SFT, both correct-RL
policies, and control 23. It is `ts_mean(returns,60)` for control 29. Top-one
counts below use the all-attempt denominator of 80; top-three exposure uses the
usable denominator. Teacher/probe counts include only usable proposals. In
these particular results, teacher membership and near-exact teacher rank
equivalence counts are the same; this equality is an observation, not an
assumption in the analysis.

| Policy | Evidence | Top-one count/80 | Top-three usable exposure | Teacher matches / rank equivalents | Probe reuse |
|---|---|---:|---:|---:|---:|
| SFT | True | 36 | 85.7143% | 75 / 75 | 5 |
| RL 23 | True | 34 | 88.6076% | 76 / 76 | 9 |
| RL 29 | True | 39 | 87.3418% | 77 / 77 | 5 |
| Permuted-reward control 23 | True | 36 | 84.6154% | 76 / 76 | 4 |
| Permuted-reward control 29 | True | 33 | 87.0130% | 76 / 76 | 9 |
| SFT | Exchanged | 35 | 85.7143% | 76 / 76 | 7 |
| RL 23 | Exchanged | 31 | 84.8101% | 76 / 76 | 11 |
| RL 29 | Exchanged | 39 | 86.0759% | 77 / 77 | 6 |
| Permuted-reward control 23 | Exchanged | 37 | 85.8974% | 76 / 76 | 5 |
| Permuted-reward control 29 | Exchanged | 30 | 83.3333% | 76 / 76 | 11 |

All 100 greedy proposals, retained separately across the five policies and two
evidence conditions, are usable and identical: `ts_mean(returns,60)`. Each
10-proposal cell has one valid AST, zero entropy, effective number one,
concentration one, and 100% top-one/teacher-rank-equivalent exposure. No proposal
in any cell matches the four reserved composite grid ASTs.

The five non-equivalent task/formula pairs have nearest-teacher similarities
below the 1-1e-10 threshold:

| Task | Generated expression | Nearest teacher | Absolute mean daily rank correlation |
|---|---|---|---:|
| 2022 H1 | `ts_mean(returns,8)` | `ts_mean(returns,10)` | .856965 |
| 2024 H1 | `ts_mean(returns,30)` | `ts_mean(returns,40)` | .829368 |
| 2024 H2 | `delay(ts_mean(returns,20),10)` | `ts_mean(returns,40)` | .624087 |
| 2024 H2 | `ts_mean(returns,8)` | `ts_mean(returns,10)` | .851815 |
| 2024 H2 | `ts_std(returns,60)` | `ts_std(returns,20)` | .876777 |

The original diagnostic union missed control 23's `ts_mean(returns,40)` in
2024 H1 and `delay(ts_mean(returns,20),10)` in 2024 H2, plus control 29's
`ts_mean(returns,5)` in 2023 H2. Exactly two new feedback-only diagnostic files
were computed with the existing CLI; the original three remain byte-identical
to their published Git blobs. Duplicate task/AST comparison bodies agree.
All source-file byte hashes are recorded in the output.

The sampled policies are concentrated around teacher templates. Correct-reward
RL does not consistently increase entropy relative to SFT or the controls:
seed 23's true-evidence entropy is slightly higher than SFT's, while seed 29's
is slightly lower. A different window length or nested delay is a different
AST, but these counts and feedback correlations do not show novel alpha,
predictive advantage, or general sequential research behavior. This analysis
does not alter the existing financial utility conclusions.
