# Financial proposal study: paired analysis plan

Written 2026-10-01 before inspecting any transfer-policy output. This plan governs
the analysis of the frozen SFT, RL seed 23 and RL seed 29 reports. The analysis
code receives saved reports only; it does not generate formulas, select a new
checkpoint, change rewards, or inspect 2025-or-later outcomes.

## Inputs and comparison integrity

Require exactly the three declared checkpoint roles, ten half-years from 2020 H1
through 2024 H2, both true and exchanged-evidence conditions, and separately
labeled stochastic and greedy outputs. The expected stochastic count is eight
draws per task/condition; the protocol's four-draw fallback is accepted only if
that count was frozen identically for all three reports. Greedy has one. Strict JSON is primary and the narrow
fence parser is secondary, using the same completions.

Before aggregation, reject mismatched study/split, pinned data snapshot,
checkpoint-suite freeze, checkpoint identities, draw counts, task manifests,
seed schedules, prompt tokens, precision/sampling settings, prompt/scoring
contract, conditions, parsers, missing/duplicate records, or nonfinite rewards.
Every report must identify its own frozen checkpoint, and all must refer to the
same three-checkpoint suite. Compare relevant execution-contract fingerprints;
the whole-repository source digest may differ because unrelated analysis code
was added, so that digest alone is not the prompt/scorer contract.

Check shared task manifests semantically as well as for equality: preceding
feedback half-year, named assessment half-year, adjacent row boundaries,
five-session purges, ordered signal/label-support dates, and the 2024 hard cap.
Reported signal counts must equal the corresponding purged interval length.
These are structural provenance checks on saved reports, not an independent
reconstruction or authentication of the market calendar from raw data.

Recompute statistics from retained individual outcomes instead of trusting
existing rounded summaries. Verify both parsers' outcome shapes, constant cost,
success/failure reward rule, and available predictive metrics. Preserve failures
in every reward denominator. A secondary parser reuses completion text/tokens;
it does not receive extra samples. Compare prompt tokens at each paired record,
not just task names. The deliberately exchanged prompts must remain identical
across checkpoints for each paired condition.

## Predeclared estimands

For each checkpoint, parser, condition and decoding, first average all sampled
rewards within a half-year, then average the ten half-years equally. Each yearly
mean averages its two half-years. Report every half-year and every year,
including zero and negative differences.

For RL run j, define for every half-year and year:

```text
incremental_RL_j = R(j, true) - R(SFT, true)
evidence_effect(P) = R(P, true) - R(P, exchanged)
grounding_interaction_j = evidence_effect(j) - evidence_effect(SFT)
```

Also report RL-minus-SFT under exchanged evidence. Keep the two RL seeds
separate; an across-seed mean and observed min/max range are descriptive additions,
never a selected best seed or confidence interval. Greedy output is a secondary
behavior diagnostic, not a substitute for the stochastic objective. Keep strict
and fence-tolerant results separate.

## Validity and predictive-score accounting

The score is oriented future IC minus .01 for a usable proposal and -1.01 for a
failed proposal. For each unit report total, usable, invalid/unscorable counts,
failure reasons, valid fraction, and conditional mean IC with its exact count.
Do not impute a missing valid-only mean as a measured zero IC.

Define the all-proposal predictive contribution as the sum of oriented IC over
usable proposals divided by the count of all proposals. Then

```text
mean reward = -1.01 + valid_fraction + all_proposal_predictive_contribution
reward difference = change in valid_fraction
                  + change in all_proposal_predictive_contribution
```

The first term is the exact change in the failure-penalty component. The second
can still move because the successful subset changes; it is not by itself a
causal estimate of improved formula quality. Report conditional usable IC beside
it rather than calling the entire reward gain alpha. The same accounting applies
to evidence effects and grounding interactions. All-invalid cells retain a
finite mean reward and a null conditional IC.

Summarize fixed lag-1, exact uniform-grid expectation and feedback-greedy grid
references only after confirming that their saved task outcomes agree across
checkpoint reports. Preserve the grid-greedy reference's extra-information
qualification. Report each RL policy's paired difference against the fixed
formula; it is not a selected post-transfer comparator.

## Dependence, reporting, and visualization

Stochastic samples are Monte Carlo draws on the same market episode. Shared
random seeds across actors and conditions couple comparisons; they are not
additional independent market samples. Five-session targets overlap and years
can share economic regimes. Two RL runs also share one SFT parent and the same
training data. No p-values, significance claims, annualized profitability,
independent-draw confidence intervals, or best-of-many conclusions are produced.

The output contains public aggregate metrics, every paired task/year difference,
checkpoint/data/contract fingerprints, draw-count evidence and explicit
limitations. It need not duplicate token traces or source market arrays.

An optional static plot has one point for each year's strict/stochastic
RL-minus-SFT reward for each RL seed and a visible zero line. A second panel may
show grounding interactions for those same years. Show negative values and both
seeds with the same scale; no confidence bars are inferred from two seeds.

## Validation and failure behavior

Artificial fixtures must establish correct task/year pairing, both-seed
retention, exact failure-penalty decomposition, all-invalid handling, stochastic
versus greedy separation, parser separation, and rejection of altered frozen
checkpoints, contract/prompt/seed/draw/task mismatches and duplicate records.
Tests use deliberately different positive and negative effects, not only a
uniform happy path. An input mismatch stops report production; it is never
silently repaired, dropped, or averaged away.

Changes to this plan after reading transfer results must be identified as
exploratory. No transfer outputs have been inspected to choose these estimands.
