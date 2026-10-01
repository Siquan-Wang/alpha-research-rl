# Financial proposal reliability: post-hoc analysis

Analysis contract fixed before computing these diagnostics on 2026-10-01.
This uses the existing five-policy reports and their paired analysis. It makes
no new generation, training, market scoring, checkpoint selection or holdout
claim. The original comparisons and reward remain unchanged.

## Target and calculation

The target is each policy contrast's mean reward over fresh generation draws,
**conditional on the exact trained checkpoints, ten market episodes and prompt
condition**. Six contrasts are retained: each of the two correct RL runs and
two permutation controls versus SFT, and each correct RL run versus its matched
control. Both true and exchanged evidence conditions are analyzed separately.
Only strict stochastic decoding is used: eight draws per task and ten tasks.
The 100 greedy completions are outside this diagnostic; all 900 original
records still pass the existing five-report integrity validation.

For matched draw differences `d[t,j]`, let `s[t]^2` be the sample variance of the
eight differences within half-year `t`, with denominator seven. Equal weighting
of the ten task means gives the plug-in Monte Carlo standard error

```text
MCSE = sqrt(sum_t s[t]^2 / 8) / 10.
```

This formula uses an i.i.d. pseudorandom-draw approximation within each task
and independent generation streams across distinct task/draw slots. It is not
proof that the chosen deterministic PRNG seeds supply independent randomness.
Policy comparisons retain matched-seed covariance by taking differences first;
policy variances are not added as if their draws were independent. Task means
are not pooled as 80 identically distributed market observations. The six
contrasts and two conditions share data and randomness with one another.

The same calculation is applied jointly to reward, usable-indicator difference
and all-attempt IC-contribution difference. Their exact identity is
`reward_difference = validity_difference + IC_contribution_difference`.
The variance identity retains their covariance. Invalid proposals contribute
their registered failure reward and zero to the IC-contribution term; that
zero is accounting, not an observed predictive IC. Conditional usable-only IC
is not assigned a Monte Carlo error estimate here.

All five leave-one-year-out means are reported for every contrast and
condition, including both accounting components. These describe sensitivity to
which observed years are included; they are not a market confidence interval,
a jackknife standard error, independent year replications, or a future-market
guarantee. Each omission changes the fixed-panel target and still contains
finite generation noise.

## Validation and limits

The CLI verifies all five report file-byte hashes against the saved analysis,
reruns the unchanged original/five-report validators, and compares the complete
regenerated paired analysis with its saved version. Structure, scalar types,
metadata and identities remain exact; finite arithmetic floats allow only
absolute/relative `1e-12` roundoff. Paired means and
components are checked against saved aggregates to floating-point arithmetic
precision; this does not change any scoring or replay tolerance.

Eight draws per task give only seven degrees of freedom for each within-task
variance estimate. Rare invalid actions can dominate both mean and variance;
unseen failures and proposals are absent from the plug-in estimate. A zero
sample variance does not establish zero population variance. These MCSEs do
not cover training-seed uncertainty, dependent market variation, revised-data
vintages, pretraining exposure or post-hoc analysis selection. No normal
confidence intervals, p-values, selected winner, or significance claims are
produced. No concentration interval is derived.

## Results

The calculation passed all source-byte and five-report checks and reproduces
the [original paired analysis](../results/financial_linkage_paired_v1.json).
The [complete diagnostic JSON](../results/financial_reliability_v1.json)
retains all twelve contrasts, their ten task results and paired draw ledgers,
all sixty year omissions, validity counts and covariance terms. No policy
ranking or original result was changed.

The estimated generation error is material relative to the reward contrasts.
For true evidence, correct RL minus its matched control is `+0.023032` with
MCSE `0.013041` for seed 23 and `+0.018368` with MCSE `0.018558` for seed 29.
The validity components come from only one and two paired slots, respectively.
This small number of observed failures makes the plug-in variance particularly
fragile; these numbers are standard errors, not confidence limits or tests.

The two correct RL reward advantages remain positive in every true-evidence
single-year omission. Their components differ: seed 23's IC-contribution
advantage over its control remains positive in every omission, while seed
29's remains negative in every omission. Under exchanged evidence, seed 29's
reward advantage over its control becomes negative when 2024 is removed.
The placebo runs also improve over SFT in the full fixed sample; placebo 23's
improvement becomes negative without 2024 in both conditions. These are
descriptions of overlapping subsets of the observed development data, not
independent confirmations.

### All paired means and generation MCSEs

`RL23`/`RL29` denote correctly linked reward training; `P23`/`P29` denote the
matching reward-permutation controls. `IC contribution` is the all-attempt
accounting term described above, not conditional usable-only IC. Each cell
below is `mean (estimated MCSE)`, rounded to six decimals. Every row uses 80
paired draws over the same ten tasks; the rows are statistically dependent.

| Contrast | Evidence | Reward | Validity | IC contribution |
|---|---|---:|---:|---:|
| RL23 - SFT | true | +0.031458 (0.018185) | +0.025000 (0.017678) | +0.006458 (0.002580) |
| RL23 - SFT | exchanged | +0.030336 (0.018135) | +0.025000 (0.017678) | +0.005336 (0.002706) |
| RL29 - SFT | true | +0.026180 (0.018246) | +0.025000 (0.017678) | +0.001180 (0.002224) |
| RL29 - SFT | exchanged | +0.022250 (0.018178) | +0.025000 (0.017678) | -0.002750 (0.002282) |
| P23 - SFT | true | +0.008426 (0.012873) | +0.012500 (0.012500) | -0.004074 (0.002021) |
| P23 - SFT | exchanged | +0.005447 (0.012999) | +0.012500 (0.012500) | -0.007053 (0.002709) |
| P29 - SFT | true | +0.007812 (0.003414) | +0.000000 (0.000000) | +0.007812 (0.003414) |
| P29 - SFT | exchanged | +0.017346 (0.012886) | +0.012500 (0.012500) | +0.004846 (0.002611) |
| RL23 - P23 | true | +0.023032 (0.013041) | +0.012500 (0.012500) | +0.010532 (0.002990) |
| RL23 - P23 | exchanged | +0.024889 (0.013219) | +0.012500 (0.012500) | +0.012389 (0.003659) |
| RL29 - P29 | true | +0.018368 (0.018558) | +0.025000 (0.017678) | -0.006632 (0.003438) |
| RL29 - P29 | exchanged | +0.004904 (0.013152) | +0.012500 (0.012500) | -0.007596 (0.003400) |

### Every leave-one-year-out contrast

Columns identify the omitted year. Each entry is the mean across the eight
remaining half-years, with the original equal task weights renormalized.
No interval or standard error is attached to these omissions. All values
are rounded to six decimals; signs and all three accounting components are
retained.

**Reward difference**

| Contrast | Evidence | Omit 2020 | Omit 2021 | Omit 2022 | Omit 2023 | Omit 2024 |
|---|---|---:|---:|---:|---:|---:|
| RL23 - SFT | true | +0.040069 | +0.039033 | +0.033403 | +0.022795 | +0.021988 |
| RL23 - SFT | exchanged | +0.035167 | +0.038200 | +0.037309 | +0.020524 | +0.020481 |
| RL29 - SFT | true | +0.032725 | +0.032079 | +0.030869 | +0.017149 | +0.018078 |
| RL29 - SFT | exchanged | +0.027813 | +0.027813 | +0.030150 | +0.011286 | +0.014190 |
| P23 - SFT | true | +0.010765 | +0.010532 | +0.012129 | +0.012430 | -0.003728 |
| P23 - SFT | exchanged | +0.006809 | +0.006809 | +0.012599 | +0.007755 | -0.006737 |
| P29 - SFT | true | +0.006442 | +0.010122 | +0.004691 | +0.008419 | +0.009387 |
| P29 - SFT | exchanged | +0.018359 | +0.022039 | +0.021071 | +0.004331 | +0.020929 |
| RL23 - P23 | true | +0.029304 | +0.028501 | +0.021274 | +0.010365 | +0.025716 |
| RL23 - P23 | exchanged | +0.028358 | +0.031391 | +0.024710 | +0.012768 | +0.027218 |
| RL29 - P29 | true | +0.026283 | +0.021956 | +0.026178 | +0.008730 | +0.008690 |
| RL29 - P29 | exchanged | +0.009454 | +0.005774 | +0.009079 | +0.006955 | -0.006739 |

**Validity-indicator difference**

| Contrast | Evidence | Omit 2020 | Omit 2021 | Omit 2022 | Omit 2023 | Omit 2024 |
|---|---|---:|---:|---:|---:|---:|
| RL23 - SFT | true | +0.031250 | +0.031250 | +0.031250 | +0.015625 | +0.015625 |
| RL23 - SFT | exchanged | +0.031250 | +0.031250 | +0.031250 | +0.015625 | +0.015625 |
| RL29 - SFT | true | +0.031250 | +0.031250 | +0.031250 | +0.015625 | +0.015625 |
| RL29 - SFT | exchanged | +0.031250 | +0.031250 | +0.031250 | +0.015625 | +0.015625 |
| P23 - SFT | true | +0.015625 | +0.015625 | +0.015625 | +0.015625 | +0.000000 |
| P23 - SFT | exchanged | +0.015625 | +0.015625 | +0.015625 | +0.015625 | +0.000000 |
| P29 - SFT | true | +0.000000 | +0.000000 | +0.000000 | +0.000000 | +0.000000 |
| P29 - SFT | exchanged | +0.015625 | +0.015625 | +0.015625 | +0.000000 | +0.015625 |
| RL23 - P23 | true | +0.015625 | +0.015625 | +0.015625 | +0.000000 | +0.015625 |
| RL23 - P23 | exchanged | +0.015625 | +0.015625 | +0.015625 | +0.000000 | +0.015625 |
| RL29 - P29 | true | +0.031250 | +0.031250 | +0.031250 | +0.015625 | +0.015625 |
| RL29 - P29 | exchanged | +0.015625 | +0.015625 | +0.015625 | +0.015625 | +0.000000 |

**All-attempt IC-contribution difference**

| Contrast | Evidence | Omit 2020 | Omit 2021 | Omit 2022 | Omit 2023 | Omit 2024 |
|---|---|---:|---:|---:|---:|---:|
| RL23 - SFT | true | +0.008819 | +0.007783 | +0.002153 | +0.007170 | +0.006363 |
| RL23 - SFT | exchanged | +0.003917 | +0.006950 | +0.006059 | +0.004899 | +0.004856 |
| RL29 - SFT | true | +0.001475 | +0.000829 | -0.000381 | +0.001524 | +0.002453 |
| RL29 - SFT | exchanged | -0.003437 | -0.003437 | -0.001100 | -0.004339 | -0.001435 |
| P23 - SFT | true | -0.004860 | -0.005093 | -0.003496 | -0.003195 | -0.003728 |
| P23 - SFT | exchanged | -0.008816 | -0.008816 | -0.003026 | -0.007870 | -0.006737 |
| P29 - SFT | true | +0.006442 | +0.010122 | +0.004691 | +0.008419 | +0.009387 |
| P29 - SFT | exchanged | +0.002734 | +0.006414 | +0.005446 | +0.004331 | +0.005304 |
| RL23 - P23 | true | +0.013679 | +0.012876 | +0.005649 | +0.010365 | +0.010091 |
| RL23 - P23 | exchanged | +0.012733 | +0.015766 | +0.009085 | +0.012768 | +0.011593 |
| RL29 - P29 | true | -0.004967 | -0.009294 | -0.005072 | -0.006895 | -0.006935 |
| RL29 - P29 | exchanged | -0.006171 | -0.009851 | -0.006546 | -0.008670 | -0.006739 |


### Interpretation boundary

The validity MCSE for true-evidence P29 minus SFT is zero because their usable
indicators agree in all 80 observed pairs, including three shared failures.
It does not imply that their future generation validity will always agree.
Similarly, the table's six-decimal zeros must not be read as proof of a zero
population effect or variance. The JSON retains full numerical precision.

These diagnostics do not supply independent market replications or convert
the study into a holdout alpha result. Market periods and checkpoints remain
fixed, market labels overlap, and 2020-2024 was already development data. The
original study's possible foundation-model pretraining exposure remains
unresolved. The [reward-linkage results](reward-linkage-results-v1.md) retain
the financial baselines, evidence interventions and identical greedy-policy
limitation; the present analysis adds only generation-error estimates and
descriptive sensitivity to removing a year.

## Reproduction and checks

```powershell
python -m alpha_research_rl.reliability_analysis `
  --analysis results/financial_linkage_paired_v1.json `
  --reports-dir artifacts/development `
  --output .local/financial-reliability-reproduction.json
```

This runs entirely on saved outcomes. It refuses to overwrite an input report
or the input analysis, and records all five input byte hashes, the saved
analysis hash and its own source-file hash. Mean/component comparisons use
absolute and relative arithmetic tolerances of `1e-12`; input byte validation
is exact. Complete saved-analysis comparison preserves exact keys, list order,
scalar types and metadata; finite arithmetic floats alone permit `1e-12`
roundoff. The 28 artificial tests cover
common-seed covariance cancellation, one rare paired failure, covariance
accounting, separation from between-year variation, every contrast and year
omission, source-byte tampering, seed mismatch and input preservation.

The initial public Linux Python 3.11 run failed the earlier whole-dictionary
equality check after passing the existing 900-record analysis replay; Python
3.12 passed. This portability correction replaces that overstrict arithmetic
comparison without relaxing input byte identities or changing any saved outcome.
The traceback alone does not identify the exact upstream arithmetic operation
responsible. New cross-version CI must pass before portability is claimed.
