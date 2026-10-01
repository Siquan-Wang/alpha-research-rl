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
