# Sequential evidence-acquisition feasibility: gate failed

The registered CPU feasibility gate **failed**. Giving a ridge selector every
candidate's later historical check improved pooled reward over its cheap-only
counterpart by +0.004610, but the effect changed sign between folds, and the
privileged selector remained below fixed lag-1. The prescribed decision is to
stop this branch: **no GenAI candidate-bank generation or sequential-controller
training follows this run**. This is a failed engineering allocation gate for
one representation and dataset, not evidence that financial learning is
impossible.

The [protocol](next-sequential-study.md) was published before the run. The
[saved results](../artifacts/development/sequential-grid-gate-v1.json) preserve
every method's choice and outcome for all 16 evaluation half-years, model
coefficients, normalization constants, folds and gates. The
[entry manifest](../artifacts/development/sequential-grid-gate-v1.manifest.json),
created at 2026-10-01 04:36:07 UTC, records source-file hashes, the pinned data
snapshot, exact feature vectors and all 32 training-period task boundaries.
This interpretation uses those saved outputs; it does not tune or rerun the
experiment.

## What the diagnostic measured

The candidate set is the same predefined 16-formula grid on each task. There
are no generated candidates, LLM calls, policy-gradient updates or actual
two-check decisions in this diagnostic. Both ridge models predict a candidate's
next-half-year reward from preceding historical evidence and formula identity.
The cheap model has 28 features. The privileged model has 38 and receives all
16 later checks for free, rather than choosing two of them.

For each preceding feedback half-year, the cheap interval covers approximately
the first two thirds and the later interval the final third. Both intervals
separately purge five signal rows, as does the assessment half-year. The sign
is fixed from cheap IC and never changed using later or assessment evidence.
Ridge regularization is 10, the intercept is unpenalized, every training task
has total weight one, and normalization uses each fold's training rows only.

Fold 1 fits assessment outcomes from 2002–2009 and evaluates 2010–2013; fold 2
fits 2002–2013 and evaluates 2014–2017. Each evaluation fold has eight half-years.
These are chronological fits within previously examined training history, not
new final-holdout evidence. No 2018-or-later assessment outcomes enter this gate.

## Every comparator and the exact decision

All six methods had zero failed evaluations in the evaluated tasks. Reward is
therefore oriented IC minus the same .01 cost throughout this table; differences
are not caused by invalid-action penalties.

| Method | 2010–2013 mean reward | 2014–2017 mean reward | Pooled 16-task reward | Pooled oriented IC |
| --- | ---: | ---: | ---: | ---: |
| Cheap-only ridge | -0.002714 | -0.032149 | -0.017432 | -0.007432 |
| Privileged all-late ridge | -0.014009 | -0.011635 | -0.012822 | -0.002822 |
| Fixed `delay(returns,1)` | -0.001616 | +0.000075 | -0.000771 | +0.009229 |
| Maximum absolute cheap IC | -0.015889 | -0.039738 | -0.027813 | -0.017813 |
| Uniform 16-formula expectation | -0.005312 | -0.018058 | -0.011685 | -0.001685 |
| Future-reward oracle, unattainable | +0.054364 | +0.047260 | +0.050812 | +0.060812 |

| Registered requirement | Observed value | Outcome |
| --- | --- | --- |
| Pooled all-late minus cheap greater than .002 | +0.004610 | Pass |
| All-late minus cheap strictly positive in both folds | -0.011295; +0.020514 | **Fail** |
| Pooled all-late minus fixed lag-1 strictly positive | -0.012052 | **Fail** |
| All three requirements pass | One passes, two fail | **Stop** |

The all-late selector also trails the uniform-grid expectation by -0.001137.
Its hindsight oracle gap does not establish that the available features can
identify the better candidate. The oracle sees the very outcome being evaluated;
it supplies neither training features nor the registered decision rule.

## Yearly heterogeneity

Every year is retained, including zero and negative differences. Each annual
value averages its two half-years equally.

| Assessment year | All-late minus cheap | All-late minus fixed lag-1 |
| --- | ---: | ---: |
| 2010 | +0.000000 | -0.005716 |
| 2011 | +0.015103 | -0.019200 |
| 2012 | -0.022044 | +0.013583 |
| 2013 | -0.038239 | -0.038239 |
| 2014 | +0.061645 | -0.021799 |
| 2015 | +0.020413 | -0.023749 |
| 2016 | +0.000000 | -0.004193 |
| 2017 | +0.000000 | +0.002900 |

The privileged model changes the cheap model's selected candidate in six of
16 half-years: four changes improve reward and two worsen it. The strongest
improvement is in 2014, when the cheap-only selector performs particularly
poorly. Pooling obscures the deterioration in the first fold; the prespecified
fold-consistency gate correctly prevents the positive pooled mean from being
treated as sufficient evidence to proceed.

## Interpretation and limits

The fixed lag-1 reference was chosen in the preceding one-shot training-grid
preflight using the full 2002–2017 history, including years now appearing in these
gate evaluation folds. Its identity was frozen before this gate, but it was not
selected using only information available by 2009. The reward orientation also
differs between the two studies. Therefore its comparison here is an exploratory
benchmark on reused development history, not an unbiased prospective contest
against a baseline chosen at each fold's historical start. The negative
first-fold late-versus-cheap effect independently fails the gate regardless.

The all-late ridge is not a mathematical upper bound and not a feasible
two-check agent. A different model class could use the evidence differently,
and a different candidate population could change the problem. The fixed grid,
formula-identity features, small number of dependent market periods and single
regularization setting limit the scope of this result. No significance,
profitability, general impossibility or LLM-capability claim follows from it.

The measured conclusion is narrower: **this registered fixed-grid probe did not
show sufficiently consistent incremental selection value to justify the planned
sequential-training branch**. Its negative result is retained alongside the
[completed one-shot financial study](financial-proposal-results-v1.md). The
three-action environment and its artificial tests remain engineering artifacts;
their existence does not demonstrate that a learned sequential policy works.
