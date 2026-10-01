# Independent agent review: fixed-panel reliability analysis

Reviewed 2026-10-01 by the data/evaluation agent, separately from the reliability
module's author. This is an internal AI-assisted engineering/method review,
not an external human statistical audit. No model, generation, market scoring,
raw market panel, or post-2024 data was used in this review.

## Source-first judgment

The reviewer read `reliability_analysis.py` and its artificial tests before
reading the observed reliability results and narrative. No blocking source
finding was identified.

Within each task and condition, the code forms the eight common-draw/seed
policy differences before estimating sample variance with denominator seven.
It therefore retains covariance induced by the paired generation seeds. The
equal-weight ten-task estimator uses sum of within-task variances divided by
8 and then by 10 squared. It does not mistake the between-task/year spread
for generation Monte Carlo error.

The validity and all-attempt IC accounting components sum to the reward
contrast, and both their sample covariance and its contribution to total
variance are retained. Invalid proposals stay in every denominator and
contribute zero to the IC accounting term; zero is not imputed measured IC.
All six declared policy contrasts, both evidence conditions, ten half-years,
and five year omissions remain present. Each omission retains eight tasks
and changes the fixed-panel estimand; it is not a jackknife confidence interval.

The CLI binds every report to its actual byte hash in the saved paired
analysis, reruns the existing original/five-report validators, and requires
the full regenerated paired analysis to equal the saved analysis. It also
records the original paired-analysis bytes and its own source identity.
Output/input path collisions are rejected. No frozen scorer file was edited.

## Independently executed checks

The reviewer ran all 14 artificial reliability tests and Ruff; both passed.
The tests include common-seed cancellation, a rare paired failure, component
covariance, exclusion of between-year variation from MCSE, complete comparison
and omission sets, report-byte tampering, seed mismatch, and input protection.

A separate NumPy calculation read the five actual saved reports directly,
without using the reliability module's mathematical helper functions. It
constructed ten-by-eight paired arrays separately for each of the twelve
comparison/condition cells, used `var(ddof=1)` for within-task variances and
`cov(ddof=1)` for validity/IC covariance, and recomputed each equal-task mean,
MC variance, MCSE, and all year-omission component means.

All 36 component means, 36 variances, 36 MCSEs, 12 covariances, and 180
year-omission component means matched the saved JSON. The largest observed
absolute numerical difference in the mean/variance/MCSE checks was
`6.938893903907228e-18`; the independent check required differences below
`1e-14`. These arithmetic checks do not relax any financial scorer or replay
rule. The report byte hashes, paired-analysis hash, and analysis-source hash
also matched their retained provenance.

The reviewer checked the result narrative and accounting interpretation.
True-evidence RL23 minus control23 is approximately `+.023031934` with
generation MCSE `.013040858`; RL29 minus control29 is `+.018367624` with MCSE
`.018557794`. Their net validity components come from only one and two
current-only-valid paired slots, respectively, with no prior-only-valid slots.
The seed29 IC-contribution contrast is negative despite its positive total
reward contrast. True-evidence control29 versus SFT has 77 shared valid pairs
and three shared failures, explaining its zero observed validity variance.

Every true-evidence correct-RL-minus-control reward contrast remains positive
under each single-year omission. Seed23's IC component stays positive and
seed29's stays negative in those omissions. Under exchanged evidence,
RL29 minus control29 becomes negative when 2024 is omitted. The document
reports these qualifications rather than selecting favorable omissions.

## Interpretation boundary and disposition

No blocking finding remains. The output estimates generation Monte Carlo
error conditional on the exact checkpoints, prompts and ten observed market
episodes, under an explicit pseudorandom i.i.d./independent-stream approximation.
Eight draws give fragile variance estimates and can miss rare invalid actions.
Zero observed variance is not zero population variance. Shared policies and
random streams make contrasts dependent; year omissions overlap and are not
new market replications.

The estimates omit training-seed uncertainty, future-market variation,
overlapping-label dependence as market uncertainty, possible foundation-model
pretraining exposure, and post-hoc analysis selection. The review does not
establish significance, causality, profitability, holdout alpha, or general
sequential research behavior. The published interpretation respects these
limits and leaves the original policy comparison unchanged.

## Subsequent public-CI portability diagnosis

The actual Linux Python 3.11 CI later failed the exact
`rebuilt == saved_analysis` assertion, after the preceding saved-diagnostic
replay accepted its aggregate arithmetic at `1e-12`. Python 3.12 passed.
The [Python 3.12 documentation for `sum`](https://docs.python.org/3.12/library/functions.html#sum)
documents a change to more accurate float summation on most builds. This is
relevant background, not proof of the entire failing runner's execution path.

The reviewer performed a bounded local diagnostic on actual Python **3.12.14**:
first regenerate the five-report analysis natively, then replace only the
`sum` name in `financial_analysis` and `linkage_analysis` module namespaces
with `total = total + value` left-fold arithmetic. Restore those namespaces
afterward. No source files or original evidence were changed. Native rebuilding
equaled the saved full analysis exactly; the left-fold version differed at
26 float leaves, with maximum absolute difference
`6.938893903907228e-18`. Every difference was inside absolute/relative `1e-12`.
No keys, collection sizes, types, token IDs, checkpoints, hashes, or nonfloat
values differed. No market panel or new model/scorer execution was involved.

The complete set of differing values is summarized below. Each reference
field appears at both `original_results/overall/references` and
`overall/references`; this accounts for 14 leaves. The two IC fields in each
listed row have the same values.

| Reference / field | Saved and native 3.12 | Emulated left-fold | Absolute difference |
|---|---:|---:|---:|
| Uniform grid / mean_reward | -.015410820748547624 | -.015410820748547627 | 3.469446951953614e-18 |
| Uniform grid / all_proposal_ic_contribution and mean_oriented_ic_valid_only | -.005410820748547625 | -.005410820748547624 | 8.673617379884035e-19 |
| Feedback-greedy grid / mean_reward | -.015812982332572143 | -.015812982332572147 | 3.469446951953614e-18 |
| Feedback-greedy grid / all_proposal_ic_contribution and mean_oriented_ic_valid_only | -.005812982332572142 | -.005812982332572140 | 1.734723475976807e-18 |
| Training fixed lag-1 / mean_reward | -.020188992685050686 | -.020188992685050690 | 3.469446951953614e-18 |

The remaining 12 leaves are derived `reward_delta` values under
`original_results/overall/metrics/{strict,fence_tolerant_secondary}/`
`{stochastic,greedy}/policy_vs_training_fixed/<policy>`. Both parser branches
have the same values; all three greedy policies share the listed greedy value.

| Decoding / policy | Saved and native 3.12 | Emulated left-fold | Absolute difference |
|---|---:|---:|---:|
| Stochastic / financial-sft-v1 | -.031396621930907840 | -.031396621930907836 | 6.938893903907228e-18 |
| Stochastic / financial-rloo23-v1 | .00006098134414912054 | .00006098134414912401 | 3.469446951953614e-18 |
| Stochastic / financial-rloo29-v1 | -.005216599184880037 | -.005216599184880034 | 3.469446951953614e-18 |
| Greedy / all three original policies | .025195590476735960 | .025195590476735967 | 6.938893903907228e-18 |

The affected ordinary sums occur in the reference-summary arithmetic; the
principal paired-policy means already use `math.fsum` and did not change in
this diagnostic. This strongly supports interpreter-dependent summation as
the explanation for exact full-dictionary equality failing on tiny aggregate
roundoff. It is **not an actual Python 3.11 or Linux reproduction** and cannot
exclude additional runner differences. The ignored diagnostic script and JSON
retain all 26 explicit paths and actual report-byte/source identities.

The appropriate repair is a finite-float arithmetic comparator at `1e-12`
while preserving exact types, structure, all nonfloat values, and source/report
byte hashes. It must not relax frozen raw scorer records or original contracts.
Actual public Linux 3.11/3.12 CI success remains the required portability check;
local emulation does not substitute for it.
