# Astra: critique of the next-study options

Date: 2026-10-01. **Design advice only; no new study is adopted or executed.**
This review used the completed public v1 protocol, candidate bank, assessment,
and the unadopted proposal in `astra-results-review-v1.md`. It performed only
saved-record counting. No model, market evaluation, network, or Git operation
was run. The reviewer authored the v1 orchestrator and the separate retained-
evidence audit, not the original next-study proposal. This is internal design
critique, not external peer review.

## Recommendation

Do **one separately registered, explicitly post-hoc frozen-pool diagnostic**
before another model experiment. It should score only the already frozen
candidates whose assessments are missing, preserve their historical-feedback
orientations, compare a few fixed deterministic selectors, and calculate an
unattainable oracle ceiling. This resolves information missing from v1: were
the realized candidate pools uniformly poor, or did the fixed selector miss
better candidates? It cannot establish that a better selector was learnable.

The v1 registered assessment remains exactly its original **30 selected calls**.
The diagnostic needs a new protocol, manifest, wrapper/output namespace, and
report, for example `astra-pool-diagnostic-v1`. Nothing below amends v1 or
relabels extra calls as part of its prospective evaluation. Root must review
and adopt that separate plan before any scoring.

V1's mean full-minus-validity contrast was -0.006363865, all 30 selected
assessments were valid, and all three arm means were negative before cost.
These observations do not identify whether selection optimism, candidate
quality, changing periods, or generation variation dominates. Spending more
model calls before resolving the simplest missing measurement is premature.

## Why the 60-call score-swap study is not the next main experiment

The proposed two-candidate truth/swap/withheld interface would test whether
displayed evidence changes a declared candidate choice. That is a legitimate
narrow interface check, but the main choice is solved by a few lines of
deterministic argmax code. V1 already contains public revisions that correctly
cite supplied scores. Another success at following those numbers would add
little evidence about useful quantitative research, formula improvement,
selection under uncertainty, or transferable planning.

There are additional interpretation problems:

- A declared parent choice is not evidence that the generated formula is a
  meaningful revision of that parent. Counting different ASTs rewards syntax
  changes and rank-equivalent wrappers. Explanations are not a mechanism test.
- One fresh response in each presentation does not identify a per-response
  counterfactual. Stochastic variation can change a formula without feedback
  doing so. Reversing candidate order on the second response makes it another
  presentation, not an identical-prompt replication. Two samples are coarse
  even after this distinction is made explicit.
- Swapping whole bundles changes uncertainty and support as well as the mean
  IC. It therefore tests response to a reassigned evidence package, not just
  sensitivity to a numerical score. Holding other fields fixed would instead
  create a potentially incoherent synthetic package and require a different
  declared estimand.
- Deleting initial probes and narrative text helps prevent the original score
  association from leaking, but produces a new simplified task. It is not an
  exact continuation of v1. Keeping the text could instead reveal the original
  association and make the intervention internally contradictory.
- Strong numerical responsiveness could reflect uncritical score following;
  weak responsiveness could reflect a rational prior or stochastic variation.
  Neither direction establishes predictive usefulness. A benchmark whose easy
  positive result is merely compliance should not become the portfolio's
  headline agent-research result.

The proposal's author subsequently agreed to withdraw it as the next main
experiment. That revision does not make it an executed or adopted protocol.

## Comparison with actual model experiments

| Option | Uncertainty it can address | Main limitation | Call budget example |
|---|---|---|---:|
| Repeat full six-step trajectories | How much the realized arm contrast varies with new sampled research trajectories on the same periods | Still development data; only a few repeats cannot precisely estimate generation variability or market uncertainty | One additional full/validity repeat across ten periods costs 120 calls; two cost 240 |
| Matched-prefix feedback intervention with actual revisions | Whether showing feedback improves the next proposed formula, conditional on identical supplied research states | Needs repeated continuations and a quality endpoint; expression differences alone do not answer it | Ten fixed states × two conditions × three identical-prompt repeats = 60 calls |
| Frozen-pool diagnostic | Whether the already generated pools contain any missed assessment opportunity under fixed directions | Its oracle is hindsight and says nothing about learnability or new trajectories | Zero model calls; at most 108 additional CPU candidate evaluations |

Repeated trajectories would be appropriate if the immediate question were
stability of the v1 realized contrast. Repeating until its sign turns positive,
choosing favorable seeds, or changing the budget after inspecting repetitions
would not be. Replication cannot create new independent market periods, and
three sequential actions within one trajectory are not three replications.

A matched-prefix revision design is the more substantive **future model
experiment**, if the diagnostic leaves a question that warrants it. Freeze a
common formula history independently of assessment quality, keep the same
initial probes in both branches, and reveal truthful historical candidate
feedback in one branch while masking it in the other. Any sanitized history
must be identical outside the intervention and acknowledged as a new interface.
Use three repetitions of each exact prompt; do not silently count order
changes as replications. No model-controlled candidate-choice answer is needed.

Its primary outcome should be incremental assessment utility from adding one
actual DSL proposal to the common prefix, using the same frozen feedback-only
selector in both branches. Compare with the prefix's pre-fixed selected
baseline. Copying that baseline cannot improve this endpoint; a decorative
AST change is not success. Average the three continuations rather than taking
the best one. Cheap deterministic copy and fixed local-mutation controls must
be specified prospectively with their proposal/scoring budgets disclosed.
Freeze all continuations before assessment. This would test the conditional
value of feedback for proposal generation, not weight learning, and would
still be development evidence on these reused periods. It is not adopted here.

## Exact proposed diagnostic population and budget

The saved bank has 180 candidate records in 30 six-candidate episodes. Counting
only saved ASTs, task IDs, and feedback signs gives:

- **132** distinct `(task, canonical AST, feedback-fixed orientation)` keys.
- **24** unique keys covered by v1's 30 selected assessment records.
- **108** remaining unique keys: the hard upper bound on new evaluator calls
  if all reusable records pass identity checks.
- **167 positive and 13 negative** feedback-fixed candidate orientations.

The unique counts per chronological task are
`[13, 12, 15, 14, 13, 14, 12, 12, 14, 13]`. These are syntax-based cache keys,
not a claim of 132 distinct economic signals. Every original candidate slot
must remain mapped to an outcome even when a cached evaluation serves several
slots. Duplicate reuse reduces execution, not the denominator or candidate
population. No new expression, sign variant, probe, period, or generated repair
may be added. Model calls and new proposed candidates are both fixed at zero.

Before scoring, publish the new plan and manifest binding the existing bank,
existing assessment, frozen evaluator/source/data identities, all 180 slot
mappings, all 132 keys, 24 provenance-checked reuses, 108 ordered pending jobs,
orientation/tie rules, selectors, failure handling and exact analysis fields.
Reuse must verify the saved expression/AST, task, feedback sign, support and
raw assessment fields. A mismatch stops the diagnostic; it must not trigger an
unplanned replacement assessment. Preserve the unchanged chronological task
boundaries and data cap. Any new wrapper should be separate from frozen v1.

## Outcomes, deterministic references, and exact decomposition

For task `i`, arm `a`, and candidate slot `j`, fix the direction solely from
its saved feedback sign, including the already specified zero-feedback tie.
Never choose direction, expression, or validity using future results.

Let `z[i,a,j]` be that direction times saved/new assessment IC when assessment
is usable. Define the cost-matched utility for **every** candidate slot as
`u = z - 0.06` when usable and `u = -1.06` otherwise. The cost remains the
six-proposal v1 search cost for this selection diagnostic; the new CPU analysis
is not six additional agent proposals. Candidate-level invalidity, empty
support, or a constant factor remains an outcome, not a reason to omit a task
or substitute the next-best candidate.

Freeze three feasible rules before reading the missing outcomes:

1. **Original selector:** largest absolute saved feedback IC, earliest tie;
   retain the v1 selected expression even if its assessment is poor.
2. **First proposal:** select attempt one without accessing future values.
3. **Minimum AST complexity:** select the candidate with the fewest nodes in
   the validated expression AST, with earliest attempt as the only tie break.

The latter two are cheap descriptive references, not claims that simplicity
or first proposals are good financial policies. Use the same cost in their
primary comparison to isolate selection. A first-proposal utility using its
hypothetical one-call cost would answer a different budget question and must
not silently replace the cost-matched result. No score penalty, window rule,
ensemble weight, or selector family may be tuned after seeing the missing
outcomes. These rules can be prospective to the **unselected** outcomes, but
their choice remains post-hoc to v1's already known selected outcomes.

Separately define the hindsight oracle `O[i,a] = max_j u[i,a,j]` over all six
slots, and regret `R[i,a] = O[i,a] - S[i,a]`, where `S` is the frozen original
selection utility. For every task and every arm comparison, verify exactly:

`S[left] - S[right] = (O[left] - O[right]) - (R[left] - R[right])`.

Report all ten task rows, all three arm contrasts, five year summaries,
validity counts and conditional-valid denominators. Every unconditional mean
uses all ten tasks. Do not average only valid candidates, only positive
oracle states, or only states where the selector changed. A nonnegative
oracle gap is guaranteed by construction and is not a discovered achievement.
The ceiling difference is not a causal “generation contribution”; each pool
is one realized stochastic trajectory with its own selected history.

If a pool's mean oracle utility is nonpositive, no selector restricted to
that exact realized pool and cost can attain positive mean utility. For an
uncosted bound, report `u + 0.06`: valid outcomes contribute oriented IC and
invalid outcomes contribute -1. In a generic bank this is an invalidity-
penalized score, not conditional mean IC. This particular bank has a stronger
guarantee: every pool already contains its valid v1 selected candidate with
oriented IC strictly above -1. Thus an invalid alternative can never attain
the oracle maximum, and `O + 0.06` here is the ordinary oriented IC of a valid
oracle-selected candidate. A nonpositive mean bounds every policy that must
choose one candidate from each of these same ten pools, with the fixed
directions. It does not bound abstention, a different pool, or a new generator.

A positive oracle only establishes that better candidates existed **in
hindsight**. It neither proves a feasible selector could identify them nor
estimates what another Astra trajectory, a larger search budget, or an unseen
period would produce. The finite-pool maximum also rewards random variation;
do not treat it as expected attainable alpha or compare it to a deployable
policy without the “oracle” label.

## Failure, stopping, and claims

Stop before scoring for any manifest/source/data mismatch, ambiguous cached
identity, unreviewed rule, or missing publication gate. Retain candidate-level
financial failures at the declared penalty. A transport/execution, schema,
checkpoint, or accounting failure leaves the separate diagnostic incomplete;
preserve finished records and start no automatic replacement or expanded
budget. Publish no full-bank aggregate until all 180 slots are mapped and all
132 unique keys are accounted for. If an interrupted scorer's completion is
ambiguous, do not rescore it under a new identity.

Finish after the 108-or-fewer new jobs, fixed aggregate checks, and a saved-
arithmetic review. Report null or unfavorable ceilings and controls. Do not
expand the candidate bank, flip a direction, search additional selectors,
drop 2024, or launch model repetitions in response to an unwanted result.
Publish this new analysis independently of v1, retaining both provenance and
the explicit post-hoc label. The recommendation authorizes no execution.

This is useful Agentic/GenAI quantitative-research failure analysis of actual
model-generated proposals. It does not itself show that an LLM is needed;
there is no deterministic candidate-generator baseline in this frozen bank.
It cannot establish profitability, a fresh holdout result, reliable general
causal effects, or Astra post-training. Reused development periods and the
already observed v1 outcomes constrain every interpretation. A later formula-
revision experiment would require another reviewed protocol and a stated
residual question; weekly quota availability is not a reason to run it.
