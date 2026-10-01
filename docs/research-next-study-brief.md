# Proposed next question: useful diagnostic feedback for program revision

**Proposal only—neither adopted nor executed.** Does structured diagnostic feedback improve generated program revisions beyond the same raw observations, matched computation budgets and cheap repair, separately from gains supplied by the final selector?

The substantive uncertainty is whether a diagnostic module helps an agent construct a better executable hypothesis, rather than merely describe errors, follow a supplied repair, or produce candidates that an external selector rescues. A controlled empirical answer could be a contribution without a new theorem. This brief makes no novelty, feasibility, conference-readiness or acceptance claim and authorizes no new calls.

## Minimal comparison

Start each comparison from an identical incumbent program, public task description, historical observations and candidate grammar. Freeze these states independently of the compared agents' outcomes. At the first revision checkpoint, compare:

1. **Raw-observation agent:** incumbent, raw input/output records and their ordinary historical evaluation.
2. **Diagnostic agent:** the same inputs and model, plus a frozen structured report computed exclusively from those records and the incumbent. Candidate reports might describe residual patterns or domain violations; they must not access hidden targets, reference formulas or assessment feedback.
3. **Cheap repair/search:** a competent deterministic or classical procedure using the same permitted observations and diagnostic report. Give it the same candidate family and relevant domain knowledge; do not conceal a known basis or handicap an exact solver.

Retain the unchanged incumbent as a reference and qualify a competent direct solver on the same observations. The raw-observation agent must receive comparable proposal and reasoning opportunities, not one call against an iterative diagnostic workflow. Predeclare observable resource limits; record proposal attempts, diagnostic/search computation, tokens and latency separately. Equal call counts cannot establish equal hidden hosted computation. A second decoder is required to test whether a finding depends on one model; it is not an already available result or allocated resource.

Evaluate each submitted revision before selection. Then apply the same frozen historical selection rule to each arm's incumbent and candidate set. This separates revision quality from the selector's contribution. Assessment outcomes must never choose candidates, repair responses or enter subsequent prompts. Invalid and repeated attempts retain their costs and denominators.

## Suitable tasks and measurements

The next design needs **two source-defined task families**, not two parameterizations of a convenient toy. Existing symbolic-regression and executable rule-induction environments are possible starting points, subject to license, interface and suitability review. This brief asserts no ready dataset, task count or affordable call budget.

Each family needs an independently specified state population, a safe executable hypothesis language, representable targets, sufficient permitted observations, and an objective held-out evaluator. A diagnostic report must be reproducible from visible inputs. A baseline that solves development cases is necessary to distinguish agent failure from an unusable task or grammar.

Where defensible, pair synthetic worlds that share prior context, incumbent, grammar and fixed observation coordinates but require different useful revisions. Change only the world-dependent response values. Score both frozen proposals in both worlds: compare correct-world performance with cross-swapped performance, alongside improvement over the incumbent. Evidence-sensitive changes can still worsen prediction, so report both; textual differences alone are insufficient. Fixing coordinates excludes action-location communication from this comparison and does **not** measure adaptive acquisition value.

Primary outcomes should retain every attempt and separately report executable revision quality, usability and post-selector quality. Conditional-valid scores are supplementary. Define loss scales, aggregation units, meaningful improvements and uncertainty before results; repeated generations are not independent task families. No financial or weight-RL conclusion follows from this inference study.

## Cheapest rejection criteria and next milestone

The minimal polynomial twin-world construction is **closed**: its public finite basis and sufficient observations allow exact interpolation. Hosted success there would demonstrate elementary inference, while failure would add little beyond existing counterfactual evaluations. Do not manufacture difficulty by weakening this control.

Likewise, stop before hosted allocation if a cheap repair solves the proposed population, the report contains privileged information, the grammar cannot represent the targets, or the comparison merely duplicates an existing ablation. Retain and report a negligible or negative diagnostic effect, without extra draws chosen to reverse it.

Closest overlap is substantial: [Deliberate Evolution, §3.2 and Tables 4–5](https://arxiv.org/html/2606.04360v1) already studies residual diagnostics and same-state revisions; [SIRBench, §5.6](https://arxiv.org/html/2509.16226v1) tests counterfactual scientific rules; [Qiu et al., §§2–4](https://arxiv.org/html/2310.08559v2) distinguish hypothesis proposal from executable application. The remaining question is the incremental, transferable value of diagnosis after strong computational and selection controls—not whether feedback or counterfactual testing is new.

**Next milestone:** a reviewable source-and-control specification naming two eligible families, one diagnostic module, the complete state-selection rule, strong cheap solvers and a finite resource ledger. Review that specification against the near art before considering implementation or execution. Existing stopped studies remain stopped.
