# Research note: source-first evidence review

2026-10-01. Internal AI-assisted review of the consolidation manuscript, with
the factual checklist prepared **before reading its draft**. The reviewer did
not author the manuscript, but participated in underlying implementation and
authored the reward-credit analysis core. This is not external peer review,
independent implementation review of that core, or an independent economic
replication. This pass reads published source/result records; it runs no model,
training, market scoring, experiment, or saved replay.

## Pre-draft claim checklist

| Claim suitable for the note | Exact evidence pointer | Required unit or qualification |
|---|---|---|
| Original Astra: 180 decisions, 30 six-proposal episodes, ten periods; full minus validity utility −0.006363865179299209. | [Assessment](../../results/astra_agent_v1_assessment.json): `episode_count`, `paired_task_count`, `primary_mean_full_minus_validity`; [protocol](../astra-agent-research-plan-v1.md); [results](../astra-agent-results-v1.md). | One trajectory per arm/half-year. All thirty final outcomes usable, so the contrast has zero validity contribution and equal IC/utility differences under common .06 cost. Not 180 independent markets. |
| All original arms received the initial probes; all used the same private historical selector. | [Original results](../astra-agent-results-v1.md), “What actually ran”; [protocol](../astra-agent-research-plan-v1.md). | Treatment changes new quantitative feedback visible to the proposal generator. “No feedback anywhere” is not the control. Final selection is deterministic, not another model decision. |
| Full-arm future IC −.0338231248; validity −.0274592596; withheld −.0287187641. | Assessment `arm_summaries.<arm>.conditional_valid_mean_ic` and `mean_utility`. | Means weight ten half-years equally. Utility subtracts .06; IC is not return, P&L or Sharpe. Every arm's mean is negative before cost. |
| Pool diagnosis adds 108 evaluations and reuses 24 keys, covering 132 task/AST/fixed-direction keys and all 180 slots. | [Pool report](../../results/astra_pool_diagnosis_v1.json): `population`, `call_accounting`. | New CPU scorer calls, zero new formulas/model calls. Key counts and proposal-slot counts are different units; duplicates/reuse remain in slot denominators. |
| Full-arm hindsight IC +.0157112025, but hindsight utility −.0442887975; all three tested feasible rules have negative mean IC. | Pool `arm_summaries.full_feedback.selectors`; `allocation`; [pool results](../astra-pool-diagnosis-results-v1.md). | Post-hoc bounded-pool diagnosis. Oracle is an unattainable maximum with fixed historical directions and .06 cost, not an available policy or proof of profitability. Nonnegative selection gap is guaranteed; strict positivity is a property of this bank. |
| Original deficit is not explained simply by a larger full-arm selection gap. | Pool `contrasts.full_minus_validity`: ΔS=−.0063638652, ΔO=−.0087683645, ΔR=−.0024044993. | ΔS=ΔO−ΔR is accounting. The lower realized pool ceiling is not an identified causal generation effect. Do not call the first/minimum-AST rules prospectively validated. |
| Matched-prefix: 80 hosted calls plus 120 cheap slots, ten states, five generators, four branches per cell. | [Matched report](../../results/astra_matched_prefix_v1.json): `population`, `call_accounting`; [protocol](../astra-matched-prefix-plan-v1.md). | Exactly 200 branches. Each selector compares the two fixed prefix candidates with one new candidate. It never selects the best of four repeated generations. |
| Truthful minus masked candidate Q −.006749596592294661; selected-gain contrast +.0014969201695758517. | Matched `analysis.primary_truthful_minus_masked_Q`, `secondary_truthful_minus_masked_G`. | Q is fixed-direction future IC or −1, while G is selected Q minus the prefix baseline Q. A positive G contrast does not imply positive truthful G. |
| Truthful G −.0010982116248438576; copying G=0; scheduled window edit G≈+.0000460342; all incremental net gains negative. | Matched `analysis.generators.<generator>.mean_G`, `mean_incremental_net_gain`; `analysis.allocation`. | Common new-attempt cost .01 is abstract. All thirteen allocation inequalities are point rules, not significance tests; five pass/eight fail and the gate fails. Copying retains baseline Q, not zero Q. |
| Matched assessment: 99 new evaluations and 34 reused keys, 133 unique keys. | Matched `call_accounting`; `analysis.generators.grammar_draw.candidate`. | These are not 200 new financial scores. Two grammar slots are historically unusable constant expressions, retained at Q=−1/G=0; neither is a failed future assessment. |
| Qwen: 96 SFT updates, 31 original RL steps, 32 later reward-permutation control steps. | [Training export](../../results/financial_training_v1.json): `runs.<id>.counts`; [control training](../../results/financial_linkage_training_v1.json): `runs.<id>.training_report.optimizer_steps`. | One common SFT parent; original RL seeds take 16 and 15 steps, controls 16 each. All four RL runs have sixteen four-sample groups. SFT is not a fifth RL run; the financial episode is a one-proposal contextual bandit. |
| Original RL reward gains +.0314576033 and +.0261800227 include +.025 validity each. | [Original paired analysis](../../results/financial_proposal_paired_v1.json): `overall.metrics.strict.stochastic.rl_vs_sft.<id>.true`. | Two fewer failures per eighty evaluation attempts. All-attempt IC contributions are +.0064576033 / +.0011800227; conditional usable IC has different denominators and is not the decomposition term. |
| Correct linkage minus own-policy permutation control: utility +.0230319336 / +.0183676237, IC contributions +.0105319336 / −.0066323763. | [Linkage paired analysis](../../results/financial_linkage_paired_v1.json): `overall.metrics.strict.stochastic.correct_vs_placebo.23/29.true`. | Exploratory follow-up after original results. Controls generate fresh trajectories; they are not shuffled labels on the original exact trajectories or a zero-update policy. Both seed signs must remain for IC. |
| Reward credit: 62/64 groups, or 61/63 actual updates, have zero direct validity advantages. | [Credit report](../../results/reward_credit_v1.json): `runs[*].summary`; [credit results](../reward-credit-results-v1.md). | Complete four-run accounting: 254/256 usable proposals, two mixed groups, one skipped group. Counts are not percentages of learning or gradient mass. C is training-assessment IC and is itself validity-gated. |

The direct JSON inspection confirmed these saved values and schema paths. It
did not reconstruct market metrics or rerun their validators. In the credit
report the run order is correct23, correct29, placebo23, placebo29; usable
counts are 63,64,64,63, active-validity-group counts 1,0,0,1, and optimizer-step
counts 16,15,16,16. This prevents confusing 62/64 with 61/63 or counting the
skipped group as an actual update.

## Interpretation checks to apply to the draft

- Keep completed execution, inference-time behavior, parameter learning and
  financial usefulness as different claims. Astra supplies actual generation;
  Qwen supplies actual adapter updates. Neither establishes useful learned
  multistep financial research. No Astra weight training is recorded.
- All financial studies reuse previously examined 2020–2024 industry-portfolio
  development periods. Purging and freezing do not make them an untouched,
  point-in-time, pretraining-clean holdout. Overlapping targets, repeated
  formulas, shared SFT parent and common data prevent treating draws as
  independent market replications.
- Matched conditional-generation MCSE is .002127476282207234 in
  `analysis.conditional_generation_mc_se`. It assumes independent provider
  draws and conditions on the fixed states; it is not a market SE or a
  generalization interval. Equal call counts are not equal token budgets or
  attested identical hidden context/backend weights.
- The truthful-versus-grammar Q advantage +.0385514 comprises +.05 validity and
  −.0114486 all-slot IC contribution. Both the penalized score and its component
  must be retained; grammar's 38-valid conditional mean cannot replace forty
  attempted slots. Selection gain and standalone proposal quality answer
  different questions.
- Accurate public rationale citations do not establish an internal causal
  mechanism or predictive success. The eighty-response grounding audit was
  secondary, planned after collection began, and coded by one internal AI
  reviewer who knew prior outcomes; no semantic-truth or hidden-reasoning
  certification follows.
- The credit result contradicts the inference “most evaluation gain is failure
  avoidance, therefore most training updates were driven by direct validity
  contrasts.” It does not show the two rare mixed updates were unimportant,
  that zero-V groups learned economic skill, or that coefficient L1/squares
  identify gradient/Adam shares. Controls permute all reward components before
  centering; the assigned IC need not belong to the scored completion.
- Prior-work comparison may use the already verified sources in
  [research positioning](../research-positioning.md) and
  [related work](../related-work.md). RLOO, LLM factor generation and automated
  quant research loops are existing methods. Do not claim novelty for their
  combination, a small model, free execution, or negative results alone.
- Saved replay establishes agreement of retained evidence and arithmetic under
  the documented checks; it does not independently reproduce market scores,
  recover model pretraining history, certify timestamps or create an
  adversarial sandbox. Internal AI reviews must be described as such.

## Draft findings and resolutions

The first complete draft was read only after the checklist above. Its central
numerical claims agreed with the saved evidence. The author, rather than this
reviewer, made the following corrections:

| Finding | Resolution confirmed in the revised manuscript |
|---|---|
| The 18/40 truthful and 6/40 masked counts were called admission to selection, but all forty in each condition were admitted. | They are now explicitly the counts of new proposals becoming the final historical winner. |
| “Permutation seed 29” could identify the wrong RNG; the actual permutation RNG seed is 700029. | Text identifies the reward-permutation control's **training** seed 29. |
| Pool cache keys were described as expression keys, potentially implying literal strings. | Text specifies canonical syntax tree identity. |
| The abstract could apply validity-dominated gains to every trained policy, although control29-versus-SFT has zero validity contribution. | The statement now names the two correct-RL-versus-SFT contrasts; predictive inconsistency separately names the control comparison. |
| The abstract's 61/63 optimizer updates could be confused with all training, including 96 SFT steps. | It explicitly says RLOO optimizer updates. |
| The matched-prefix treatment did not state which numerical evidence remains common. | Text names shared numerical probes/formulas, the masked candidate metric/support bundles, inferable facts, and the common current-plus-sixty-prior-row dependency limit. |
| The gradient nonidentifiability wording could conflate parameter space and the vector of completion coefficients. | Perturbations now act across completions with coefficients orthogonal to the total-advantage vector. |
| The 861/881 teacher-template statement lacked its most direct diagnostic link. | The manuscript links [proposal diversity](../proposal-diversity-v1.md). |

The extra generation-error figures were checked against
[reliability JSON](../../results/financial_reliability_v1.json),
`comparisons` entries `rl23_minus_placebo23` and `rl29_minus_placebo29`, condition
`true`: `overall.components.reward.estimated_mc_standard_error` is
.013040857721726827 and .0185577935028239, respectively. Their
`overall.counts.current_only_valid` values are one and two, with zero
`prior_only_valid`. The 861/881 syntax-match count and its occurrence-level scope
match the published diversity diagnostic; it is not a count of unique factors.

The BF16/FP32 numerical probe magnitudes and the distinction from generation
configuration merging agree with the
[pre-training policy audit](2026-10-01-financial-policy-review.md). Prior-method
descriptions agree with the repository's previously verified primary-source
comparison; this review did not refresh those external pages or make a new
performance comparison.

**Disposition: no unresolved fact, unit, provenance or counterfactual-claim
blocker in the reviewed manuscript.** Reviewed file:
`docs/research-note-v1.md`, 19,108 bytes, SHA-256
`cbcb1c843b0be5cb7f448f99306b7d5b2ee610fbbb6b77ce0d34f7ccfeb932a1`.
This disposition applies to that text, not to unseen subsequent edits. PDF
rendering and figure-image inspection are root's separate responsibility; no
layout or final-PDF identity claim is made here. No original study file was
edited and no new experimental or replay execution occurred in this review.

## Final text and compact-figure delta closure

The final text was checked at SHA-256
`ed3882b51ac0f66d97fd10bfe374cadf2e342209abd50eaa2b3c93e784c5dd0a`.
Its added explanation of the thirteen allocation conditions is consistent with
the saved point-estimate gate: three contrasts against each of four references,
plus the selected-quality gain threshold. These are not thirteen significance
tests. The revised wording also correctly distinguishes evaluated reward,
common structural statuses, the actor-hidden deterministic selector, and a
window edit of the prefix's historical winner. No numerical finding changed.

The reviewer read `scripts/plot_research_note.py` and visually inspected its two
existing PNGs without executing the script. The script pins the matched-prefix
report to `89162112ddad384ed8917a8b1198ce94044abc90ff15e1680bfe88b66eb43c37`
and the reward-credit report to
`59d31578928894581208c8928fd38690b839d0c12264c38e64779ffc19957cb7`.

- The matched-prefix chart retains five generators with forty candidate slots
  each. Q includes the two grammar failures at minus one; G is the change in the
  three-candidate historical selection, not selection of the best of four
  repetitions. Its displayed values, 38/40 grammar usability, and negative
  cost-adjusted mean gains agree with the saved evidence. No uncertainty bars or
  significance claims are inferred from the plotted point estimates.
- The credit chart retains all four runs and sixteen groups per run. The two
  validity-present cells are correct seed 23, group 9, and permuted seed 29,
  group 11, using one-based labels. Correct seed 29, group 16, has all-zero
  coefficients and no update. The other sixty-one cells have nonzero assigned
  IC-channel coefficients and zero direct validity coefficients. Thus the grid
  shows 64 groups, 63 updates, and 61/63 updates without direct validity
  contrast. Its "IC only" legend denotes coefficient-channel presence; the
  adjacent footnote and manuscript explicitly exclude gradient-size, Adam,
  financial-skill, or ungated-economic-credit interpretations.

Reviewed presentation identities:

| File | SHA-256 |
|---|---|
| `scripts/plot_research_note.py` | `2c7694505268fce2e6600d3445bfd9b4f43cc790ec653b51856dd41ba669d8c3` |
| `docs/figures/research-note-matched-prefix-v1.png` | `d7abe586e4d7cde2fb84b4495518c5805fd12c68b30d4e3021372eba018b8241` |
| `docs/figures/research-note-reward-credit-v1.png` | `db9647f9c675818f1bb8216dfbfe0e7fd196c535831541bb84221553b1d64067` |

**Final disposition: no unresolved factual or category/denominator blocker in
the held text and these two figures.** This supersedes the earlier text identity
for this review's content closure. Root's seven-page PDF inspection remains a
separate check; this reviewer did not inspect or authenticate the PDF itself.
