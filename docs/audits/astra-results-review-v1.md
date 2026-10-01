# Astra v1: independent frozen-bank and results review

**Initial review stage: submissions inspected before receiving assessment
results or root's result prose.** This reviewer authored the prospective
protocol and independently inspected the collected evidence and interpretation
limits. This is an [internal AI-assisted review](README.md), not external peer
review or an independent review of the reviewer's own protocol. No model call,
market-array access, candidate evaluation, or assessment was performed here.
The initial judgment below was written before assessment inspection; the later
assessment review is explicitly separated at the end.

## Independently checked evidence

The [frozen bank](../../results/astra_agent_v1_submissions.json) contains 30
episodes, 180 completed responses and 60 round hashes, with freeze time
`2026-10-01T09:03:42.501498+00:00`. Its file SHA256 is
`89b9cd42d4d248393c2c3c2b9f29714fb9ba023b511d9b3741196d99a321def7`.
The reviewer independently verified the bank/episode body hashes, contract
binding, plan/source byte identities, six-attempt costs, saved packet/AST
identities, all 180 reconstructed prompt hashes and feedback masks, raw-response
hashes, and the feedback-only argmax selection/orientation. This uses saved
records; it does not recalculate market metrics. Retained provider summaries
report success, a valid response-only stream, exit zero, one attempt and no
wrapper retry for every call. The reviewer did not independently reread all
180 private raw event streams; root's separate transport replay covers those.

All 180 records have no packet/grammar failure, usable saved feedback and no
canonical duplicate **within their respective episode**. All 30 selections are
non-null and use positive orientation. These are collection/feedback facts;
they do not establish assessment usability or predictive performance.

| Saved-record measure | Full feedback | Validity-only | Withheld feedback |
| --- | ---: | ---: | ---: |
| Completed proposals | 60 | 60 | 60 |
| Distinct ASTs across this arm's ten episodes | 51 | 43 | 41 |
| Reported input tokens | 987,445 | 979,666 | 977,813 |
| Reported output tokens | 27,052 | 30,006 | 28,781 |
| Reported reasoning-output field | 20,181 | 23,590 | 22,417 |
| Selected absolute feedback IC minus best initial probe: mean | +.024231 | +.021324 | +.022538 |
| Same feedback comparison: positive / equal / negative periods | 9 / 1 / 0 | 10 / 0 / 0 | 9 / 0 / 1 |

Usage columns reproduce provider fields; reasoning-output counts must not be
added again to output counts as if guaranteed disjoint. There are 95 distinct
ASTs across all 180 proposals. Cached-input fields are nonzero in all arms;
fresh ephemeral conversations do not imply cache-cold execution or equal
compute. All ten initial three-arm **supplied prompts** match byte-for-byte.
Four triplets produced the same first formula in all arms; six produced at
least two different formulas. The 2021-H1 full arm reports 15,900 initial input
tokens versus 15,888 for each control, despite the matching supplied-prompt
hash. The cause is not established. Identical full provider context, coupled
sampling randomness and backend checkpoint identity are not attested.

## Interpretation formed before assessment

1. **The observed procedure is a real six-step proposal workflow.** It uses
   actual Astra responses and brokered historical feedback. For example,
   2020-H1 full-feedback revisions cite the saved `.0698` and `.0874` scores
   when removing volatility scaling and then varying the return window.
   The 2022-H1 and 2023-H1 revision statements likewise reference prior saved
   values correctly in the inspected examples. This supports observable
   feedback-referenced behavior. These public statements are neither hidden
   reasoning nor a counterfactual test that altered feedback would change the
   same policy decision. There is no Astra weight update or reinforcement
   learning in this experiment.
2. **Success messages are not observed repairs.** Every proposal is valid and
   usable. Validity-only therefore receives the same successful grammar and
   nonduplicate acknowledgment throughout, while withheld receives the neutral
   acknowledgment. Any difference between these controls is not evidence of
   correcting invalid formulas in this realized sample.
3. **The common selector is part of every arm.** It privately sees all six
   candidate scores, including the sixth response that has no subsequent actor
   turn. It chooses and orients the winner. Do not attribute final selection
   skill to Astra or describe withheld as financially uninformed: all arms
   receive both initial probes and the same informed terminal selector.
4. **Historical search gains are not assessment gains.** The table's probe
   comparison uses saved feedback only and is descriptive/post hoc. Increasing
   the best-so-far score is partly guaranteed by retaining a maximum across
   candidates; unadaptive candidate generation also benefits. Choosing by the
   same feedback used to report improvement creates selection optimism.
   All arms frequently beat the probes on feedback. That does not establish
   the incremental future value of full feedback, an unbiased estimate of a
   new signal, or superiority to a preregistered six-call financial baseline.
5. **AST diversity is not factor novelty.** The bank mainly varies return
   windows, lagging, scaling and cross-sectional transformations. In 2024-H2,
   the full selection wraps the volatility-normalized five-day return in
   `neg(rank(...))`; the validity-only selection uses `neg(...)` around the
   same inner expression. The frozen DSL's outer rank preserves the relevant
   cross-sectional ordering, and their saved feedback ICs agree exactly.
   Distinct ASTs therefore need not identify distinct Spearman signals.
   This source-based example is not a computed global semantic-novelty score.
6. **One trajectory cannot estimate its own generation uncertainty.** There
   is one sampled six-step trajectory per arm/period, with no controllable
   shared seed. Initial formula differences precede any intervention feedback.
   The ten chronological market periods are dependent, and adjacent periods
   also exchange assessment/feedback roles. Do not use 180 calls as financial
   replications, derive a generation MCSE from six within-trajectory steps,
   or present an independence-based significance/general causal claim.

The registered primary remains full minus validity-only, with the other two
contrasts retained regardless of sign. Root's assessment should show all ten
paired periods and all five years, selected-assessment validity, and the
`-1.06 + p + q` decomposition. No assessment result has informed the judgments
above. Initial-probe future comparators were not adopted as new v1 score calls;
any later reuse of already saved comparator outcomes must be labeled separately
and must not replace the registered primary comparison. The 2020–2024 periods
remain development data, model pretraining exposure is unknown, and IC is not
a transaction-cost-aware profit measure.

## Assessment review

Root reported publishing the complete bank at
`b204714539c1ebdf38511631120a1119ce68a3d0`, verifying 15 downloaded public files
at 09:07:06 UTC, and then running the separate assessment once. This reviewer
subsequently read only the saved 30-selection result, not root's narrative,
and performed independent arithmetic from individual outcomes. Assessment file
SHA256 is `30aafbc089f6017c99c6d23c14fca077ffcdf59e9cbf0599d28560c4446ff2a0`;
body hash is `aca23cdd5b05d699d4b91e2f1e02db0a208cb4c5b430ccab4c715f20f523beef`.
The intended public copy is
[astra_agent_v1_assessment.json](../../results/astra_agent_v1_assessment.json).

The reviewer verified all 30 selected expressions and orientations against the
freeze, feedback values, assessment status/support, IC orientation, one-proposal
reward and `.06` total-cost arithmetic. All three means, 30 paired contrasts,
15 annual contrasts and validity/predictive decompositions were reconstructed
without the implementation's aggregation helpers. All 189 checked numeric
relations agree within `1e-12`; the largest floating discrepancy is `5.55e-17`.
No market evaluation or alternative-candidate selection was performed.

| Arm | Valid assessments | Mean oriented assessment IC | Mean utility |
| --- | ---: | ---: | ---: |
| Full feedback | 10/10 | -.033823 | -.093823 |
| Validity-only | 10/10 | -.027459 | -.087459 |
| Withheld feedback | 10/10 | -.028719 | -.088719 |

All assessments have full saved cell/date support. Thus every contrast below
has **zero validity contribution**: it is an IC difference, with the equal
search cost canceling. All three mean ICs are negative even before search
cost. The cost contributes to the absolute utility level but cannot explain
the between-arm ranking. Positive IC occurs in 1/10 full, 2/10 validity-only
and 2/10 withheld periods; all 30 utilities are negative.

| Period | Full − validity | Full − withheld | Validity − withheld |
| --- | ---: | ---: | ---: |
| 2020H1 | -.009683 | -.009683 | .000000 |
| 2020H2 | -.006247 | +.018635 | +.024882 |
| 2021H1 | -.007313 | -.007313 | .000000 |
| 2021H2 | +.007773 | +.007773 | .000000 |
| 2022H1 | +.023715 | +.023715 | .000000 |
| 2022H2 | +.013208 | +.013208 | .000000 |
| 2023H1 | +.007267 | -.032461 | -.039728 |
| 2023H2 | -.017489 | -.017489 | .000000 |
| 2024H1 | -.074870 | -.047582 | +.027288 |
| 2024H2 | .000000 | +.000153 | +.000153 |
| **Equal-period mean** | **-.006364** | **-.005104** | **+.001260** |

| Year | Full − validity | Full − withheld | Validity − withheld |
| --- | ---: | ---: | ---: |
| 2020 | -.007965 | +.004476 | +.012441 |
| 2021 | +.000230 | +.000230 | .000000 |
| 2022 | +.018461 | +.018461 | .000000 |
| 2023 | -.005111 | -.024975 | -.019864 |
| 2024 | -.037435 | -.023715 | +.013720 |

The supported finding is **no observed advantage for quantitative feedback in
this completed development sample**: the primary realized mean is negative,
with four positive periods, five negative periods and one tie. It does not
prove that feedback generally harms Astra research. As a clearly post-hoc
descriptive sensitivity, omitting each year in order 2020–2024 gives primary
means `[-.005963, -.008012, -.012570, -.006677, +.001404]`; omitting 2024 changes
the sign. This sensitivity is not a confidence interval or a reason to remove
2024 from the headline. The six exact validity/withheld ties and the observed
rank-equivalent full/validity 2024H2 tie also limit how many distinct selected
financial decisions these aggregates represent.

The higher selected historical feedback in all arms did not transfer to
positive mean assessment IC. The data do not separate selection optimism,
period instability, misspecified signals, and stochastic proposal variation
well enough to assign one cause. Do not reverse the frozen directions after
seeing the negative future means, change the selector, or recast these periods
as a fresh holdout. No numerical or interpretation blocker was found in the
saved assessment; the limitations constrain the strength of the claim.

## Review of the main result report

The reviewer subsequently compared
[astra-agent-results-v1.md](../astra-agent-results-v1.md) against the prior
independent judgment and saved arithmetic. Its three-arm, period, annual and
usage tables agree; its negative-result, feedback-versus-validity and
inference-versus-weight-training claims are appropriately limited. No numerical
correction was needed. The reviewer recommended removing wording that would
make a separate feedback-dependence experiment mandatory before any future
improvement claim; the author revised that paragraph. Mechanism identification
and reliable financial performance are different questions.

## Refined next-step recommendation — design advice only

**Withdraw the proposed 60-call two-number choice test as the next main
experiment.** Its truthful/swapped/withheld candidate-choice design could
measure score following, but a deterministic argmax already solves that task.
Success would add little to the observed accurate score citations, would not
explain negative assessment IC, and would not establish nontrivial research or
formula quality. Reversing order between only two draws also fails to provide
two repetitions of the exact same presentation. More generally, changing a
bundle changes uncertainty information as well as its mean. Neither a changed
AST nor an argmax choice is a sufficient research-quality endpoint. The proposal
was never adopted or executed; allowance availability is not a reason to run it.

The more informative first question is: **did these actual generated pools
contain better assessment signals that the common historical selector missed,
or is even their retrospective performance ceiling poor?** V1 scored only its
30 frozen selections, so the present record cannot answer this. Recommend one
separately registered **post-hoc CPU-only diagnosis**, named
`astra-frozen-pool-diagnosis-v1`, with a separate output such as
`results/astra_pool_diagnosis_v1.json`. Keep every v1 plan, submission,
selection, score and headline immutable. This is a new diagnostic after seeing
selected outcomes, not part of v1's original assessment budget or a new holdout.

Proposed contract, to be reviewed and frozen before any new scoring:

- Retain all 180 proposal slots, including their arm/period/ordinal identities.
  An independent static count gives 132 distinct `(task, canonical AST,
  feedback-fixed orientation)` keys. The 30 selected records already cover
  24 keys. Reuse them only after identity and duplicate-outcome agreement checks;
  the upper budget is **108 additional unique evaluations and zero model
  calls**. Do not introduce new formulas, probes, data periods or sign choices.
  There are 167 positive and 13 negative proposal orientations; preserve them.
- Use the original scorer and data identity. For each slot, retain
  `u = feedback-oriented assessment IC − .06` when valid, otherwise `−1.06`.
  Keep invalid/unscorable records in every denominator. This `.06` is the
  common cost of the already generated six-proposal pool, not a claim about
  how much a cheaper prospective policy would have spent.
- For each of the 30 six-candidate pools, compute `S`, the immutable v1 chosen
  utility; `O = max(u_1,…,u_6)`, the unattainable future-informed ceiling; and
  `R = O − S`, the nonnegative selection gap. For every arm contrast,
  `ΔS = ΔO − ΔR`. Call `ΔO` a **realized pool-ceiling difference**, not a causal
  contribution from generation. Do not create a replacement v1 winner or
  policy from the maximizing future score.
- Freeze two inexpensive nonoracle references before the missing outcomes are
  inspected: the first proposal, and the proposal with fewest `ast.walk` nodes
  (earliest-attempt tie). Both use feedback-fixed orientation. They select from
  the same completed pool; report their actual information requirements and
  do not present their retrospective comparison as prospective validation.
- Report all three arms, all ten periods and all five years, complete validity
  counts, the `S/O/R` identity and both references. No independence-based
  significance, success-picked subset, or claim that 132 scores are 132
  independent financial observations is justified.

The prospective **allocation rule** is deliberately asymmetric. Every full-arm
pool already has a valid selected member with IC strictly above -1. Its oracle
therefore necessarily chooses a valid member rather than an invalid `-1.06`
outcome, so `mean(O_full) + .06` is its maximum achievable mean oriented IC
under retrospective selection. A generic pool lacking that guarantee would
instead require an invalidity-penalized score interpretation. If this bank's bound is
nonpositive, no selector restricted to those realized six-candidate full-arm
pools can produce positive mean IC: stop trying to rescue that bank with a new
selector or more model reasoning. This is a finite-bank mathematical statement,
not impossibility for other data, candidates or future periods. If the bound
is positive, it establishes only realized headroom; **do not automatically
authorize another Astra experiment**. A better first/minimum-complexity result
would favor validating cheap selection before attributing a need for
sophisticated selection within these already Astra-generated pools; it cannot
determine whether an LLM was needed to generate the pools. The bound also says
nothing about an abstaining policy or a different generator. Positive oracle
headroom alone does not establish a
predictable selection rule or justify controller training.

If a later model study is warranted, the stronger alternative to number
following is a matched fixed research state with repeated actual DSL revisions,
a predeclared proposal-quality endpoint, and deterministic copy/local-mutation
controls. That requires a separate chronological validation and information
boundary review; neither the old failed fixed-grid gate nor these already seen
2020–2024 outcomes may be relabeled as confirmation. No follow-up protocol has
been adopted and no new inference or market scoring was performed by this
reviewer.
