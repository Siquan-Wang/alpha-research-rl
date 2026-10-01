# Financial research red-team review

Reviewed 2026-10-01. Scope: scientific identification and allocation decisions,
not a repeat of the separate arithmetic audit. I read the registered financial
study and analysis plan, task/policy/training/evaluation/analysis source, and
saved training/paired results before reading the financial results narrative.
I then inspected the registered sequential protocol, ridge source and completed
saved gate. No model inference, new market scoring, checkpoint selection or
2025+ analysis was performed.

**Disposition:** no new blocker to publishing the conservative financial result
or the failed allocation gate. The evidence supports actual LLM reinforcement
updates and a small change in sampled proposal behavior. It does not establish
useful learned evidence acquisition, robust financial improvement, or a learned
sequential financial research agent. The current narrative largely respects
those boundaries. The priority improvements below concern interpretation and
provenance, not changing the registered result.

## 1. Evidence assignment sensitivity is narrower than evidence conditioning

`exchange_probe_bundles` preserves the two probe labels and swaps complete metric
bundles; `evaluate_task_runner` regenerates proposals with paired seeds while
the evaluator retains the true history. This is a valid implemented intervention
on the *assignment* of evidence to expressions. It is not a financial permutation
test, an intervention on all available information, or a removal of information.
In particular, the unordered pair of bundles remains unchanged. A policy could
use their average, dispersion or other symmetric regime information and be
unaffected by the swap. Thus a null swap result cannot establish that the actor
ignores every aspect of the observation. Conversely, changed outputs can reflect
sensitivity to false text without economically useful interpretation.

The saved strict/stochastic effects are -0.002859, -0.001737 and +0.001071 for
SFT, RL 23 and RL 29. The positive RL 23 interaction (+0.001122) is a reduction
in a negative correct-evidence effect, not positive evidence value. The strong
2022-H1 interaction for RL 29 occurs when RL 29 itself has zero evidence effect;
the SFT parent does worse with correctly assigned evidence in that period.
Positive interactions therefore cannot carry the central grounding claim.

One bounded follow-up was completed using saved records only. Pairing every
stochastic record by task and draw gives:

| Checkpoint | Exact parsed expression changes, true vs exchanged | Reward changes | Pairs with discordant usability |
| --- | ---: | ---: | ---: |
| SFT | 5/80 | 5/80 | 0/80 |
| RL 23 | 9/80 | 9/80 | 0/80 |
| RL 29 | 6/80 | 6/80 | 0/80 |

These are expression-string comparisons, not behavioral-equivalence clusters.
Only 5–9 sampled pairs carry each measured evidence effect. This describes the
realized paired-seed experiment; it is not an estimate of the probability that
the underlying output distributions differ. The unchanged greedy mode adds no
evidence for useful conditioning.

**Priority clarification:** retain “no consistent useful feedback grounding was
demonstrated,” and add that the swap leaves symmetric uses of the two bundles
untested. The saved-record census above is a sufficient small addition; a new
intervention suite is not required to publish this result.

## 2. Utility accounting is valid, but utility dominance is not a training mechanism

The fixed -1.01 failure reward and the matched denominator make the primary
utility well defined. Two fewer invalid proposals produce +0.025 of the
+0.031458/+0.026180 gains. The smaller IC contributions cannot be interpreted as
causal quality improvements on a common successful population. The narrative
and exploratory penalty sensitivity correctly expose this dependence. Moving
the penalty to make a comparison favorable would change the objective, not
repair the result.

Do not overcorrect by dismissing the training as merely syntax learning. Saved
RL 29 training has **64/64 usable proposals**, with 15 nonconstant quality groups
and real updates. RL 23 has only one invalid proposal in 64; that group's
pre-clipping gradient norm is 11.576, versus at most 1.361 in its other groups,
and the implementation clips all groups at one. This is evidence of a large
failure-related raw gradient in one run, not evidence that this update caused
the transfer improvement. Reward decomposition identifies where evaluation
utility moved, not which gradients caused the change.

All sampled policies lose to exact uniform-grid expected utility. The greedy
mean-60 policy does better on these years but is identical before and after RL;
it cannot retrospectively replace the registered sampler. SFT versus RL isolates
the consequence of the declared additional reward-training procedure from its
common parent. It does not establish RLOO's superiority over other fine-tuning
methods, an unconditional formula-mixture learner, or a numeric conditional
selector. Those absent comparisons limit a superiority claim; they are not
blockers to reporting this narrow experiment.

## 3. Chronology does not certify an unseen financial world

Half-year purges and prefix-only observations are appropriate. Reusing an
earlier assessment as a later historical observation is temporally causal, but
does not make adjacent episodes independent. The 80 draws, 49 industries,
overlapping targets and two descendants of one SFT parent do not supply
independent market replications. Previously inspected 2020–2024 outcomes remain
development history despite checkpoint freezing for this particular comparison.

The revised-data-vintage limitation is disclosed. A separate limitation from
`docs/research-protocol.md` is missing from the financial result's own limits:
the pinned Qwen model revision establishes identity, **not exclusion of these
historical periods or public financial knowledge from base-model pretraining**.
No evidence reviewed here establishes contamination, and hidden dates in prompts
reduce a direct lookup route; neither proves absence of prior exposure.

**Priority clarification:** add one sentence that historical pretraining exposure
is unverified, so chronological adapter separation is not a contamination-free
base-model holdout. Do not invent a cutoff date. This is a limitation, not a
reason to discard the measured within-suite differences.

## 4. The failed CPU gate justifies a stop, not an impossibility claim

The implemented gate has training-only standardization, equal task weighting,
the declared fixed ridge penalty and forward-fitting folds. Its result is:

| Quantity | Saved value |
| --- | ---: |
| Pooled all-late minus cheap reward | +0.004610 |
| Fold 1 all-late minus cheap | -0.011295 |
| Fold 2 all-late minus cheap | +0.020514 |
| Pooled all-late minus fixed lag-1 | -0.012052 |

There are no candidate failures in these gate outcomes, so the gate failure is
not another invalid-penalty artifact. All-late and cheap selectors change choices
in only 6/16 assessment half-years; fold 2's entire positive difference comes
from 2014 H1 and 2015 H1. The positive pooled difference is insufficient under
the prospectively stated conjunction, and retaining the stop is appropriate.

The lag-1 benchmark was selected in the earlier **whole-2002–2017** training-grid
preflight. It was fixed before this gate, but its original selection includes
years reused as gate assessment. Therefore it is an informed development
reference, not a comparator independently selected before each forward fold.
The changed cheap-orientation contract also means the earlier selection and
current gate are not identical objectives. Disclose this comparator provenance;
do not describe every part of the gate as a pristine forward test. The negative
first-fold late-minus-cheap effect independently fails the gate anyway.

Finally, an all-checks ridge has more observations than a feasible two-check
agent but a restricted linear decision rule. It has no guarantee to dominate a
nonlinear or adaptive policy. Its failure can reflect misspecification,
regularization or unstable selection, and is not proof that no information is
available. “Insufficient evidence to allocate further compute to this registered
branch” is justified. “Sequential research cannot work” is not.

## Priority actions and future scope

1. Publish the result and failed gate with the three concise qualifications above:
   assignment-specific intervention, unverified pretraining exposure, and the
   previously selected lag-1 comparator. Preserve the primary objective and gate.
2. Keep the portfolio claim concrete: reproducible local GenAI proposal training,
   actual reward-dependent LLM updates, controlled financial development
   comparisons, and a documented decision to stop. A complete learned sequential
   financial agent remains unestablished. The stopped CPU ridge experiment is
   neither GenAI inference nor RL.
3. Do not start a monthly-episode financial study simply to get more contexts or
   a passing gate. Shorter episodes would reuse the same history, retain heavily
   overlapping long-lookback observations and estimate five-session quality from
   fewer signal rows. The observed failures do not specifically identify
   half-year granularity as the bottleneck. A different temporal-resolution task
   could be future, separately registered exploratory research if motivated by a
   concrete hypothesis; it is not a necessary correction to these results.

No further GPU run, penalty tuning, new market period or new method search is
needed to resolve the present review. The saved-trace census is the sole added
diagnostic in this review; no new financial scores were generated.

### Optional reward-linkage control, assessed before any such run

The root subsequently proposed a bounded control that is better motivated than
changing temporal resolution: restart from the same SFT parent, but uniformly
permute each freshly sampled group's four rewards before calculating RLOO
advantages. This directly tests whether the observed changes can also arise
when the correct action–reward assignment is removed. I support one separately
registered exploratory comparison, conditional on completing both seeds and
all declared evaluation draws, not selecting a successful control.

Use each control's own on-policy samples, an independent permutation RNG, and
all permutations including identity. Freeze 16 groups, retain constant groups
and actual update counts, and log true/assigned rewards and permutations. The
conditional expected **pre-clipping gradient** is zero under uniform reward
permutation; clipping and stateful Adam do not guarantee zero expected parameter
change. Equal task/seed schedules do not mean identical trajectories after
policies diverge. Two signed seed comparisons remain descriptive. This would
be a new post-result training-control study with reused development years, not
a revision of v1's primary estimand, a revival of the stopped sequential branch,
or a confirmatory reward-grounding claim. Preserve original checkpoint identities
instead of relabeling controls to bypass the three-role analysis validator.

## Inspected evidence

- `docs/next-research-study.md`, `docs/financial-analysis-plan.md`, and
  `docs/next-sequential-study.md`.
- `src/alpha_research_rl/financial_tasks.py`, `financial_policy.py`,
  `financial_training.py`, `financial_evaluation.py`, `financial_analysis.py`,
  and `sequential_gate.py`.
- `results/financial_training_v1.json`,
  `results/financial_proposal_paired_v1.json`, and saved SFT/RL transfer records
  under `artifacts/development/`.
- `artifacts/development/financial-training-grid-v1.json` and
  `artifacts/development/sequential-grid-gate-v1.json`.
- Only after source/result review: `docs/financial-proposal-results-v1.md`;
  `docs/research-protocol.md` for the existing pretraining limitation.
