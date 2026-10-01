# A controlled test of sequential financial evidence acquisition

Protocol written on 2026-10-01 before running this feasibility study. The current
financial proposal experiment is a contextual bandit. Its trained proposal model
does not establish learned sequential research. This next study asks whether a
policy can improve its final choice by deciding which historical measurements to
acquire under an equal, finite budget.

The immediate experiment is a **CPU, fixed-grid, privileged-information
feasibility diagnostic**. It is neither a GenAI experiment nor a two-check agent.
Only if that diagnostic supports further work should we spend GPU time on the
sequential controller. A negative result is a useful capability limit for this
particular representation and dataset, not proof that financial learning is
impossible. The loader caps the study panel at 2024-12-31: no 2025-or-later
samples may reach the study, actor or scorer, and no policy outcomes on those
periods may be evaluated. The previously downloaded upstream ZIP itself contains
later rows; this rule describes the retained panel and evaluation boundary.

## Why this question, and what is already known

The training-only one-shot preflight found a hindsight opportunity gap, but its
feedback-greedy rule was worse than the uniform grid and fixed lag-1. Hindsight
maxima do not demonstrate that the available evidence predicts future quality.
Adding turns to that weak objective would make a larger demonstration without
resolving its main scientific uncertainty.

The following primary sources establish substantial prior art; their reported
returns are not benchmarks reproduced here.

| Primary source | Relevant prior art | Consequence for this study |
| --- | --- | --- |
| [R&D-Agent-Quant, sections 2.2–2.5](https://arxiv.org/html/2505.15155v2) | A feedback-driven factor/model research loop, including contextual linear Thompson sampling to schedule optimization directions | Combining an LLM generator with a learned numerical scheduler is already established. |
| [AlphaAgent, sections 3.2–3.3](https://arxiv.org/html/2502.16789v2) | LLM hypothesis/factor/evaluation agents, AST originality and complexity constraints, hypothesis alignment and iterative feedback | Neither a bounded formula grammar nor a multi-agent refinement loop is a new contribution. |
| [AlphaForge](https://arxiv.org/html/2406.18394v2) | A generative-predictive factor miner and a separate model that dynamically selects and combines generated factors | Separating generation from downstream selection is established; a frozen generator alone is not novelty. |
| [AlphaQCM, ICML 2025](https://proceedings.mlr.press/v267/zhu25ag.html) | Distributional RL for synergistic formulaic alpha discovery, addressing sparse rewards and a changing reward process | Formula search as sequential RL, uncertainty-based exploration and learned factor pools have direct predecessors. |
| [AlphaAgentEvo, ICLR 2026](https://openreview.net/pdf?id=lNmZrawUMu) | Tool-interacting alpha evolution trained through agentic RL and hierarchical trajectory rewards | Training an LLM through multi-turn alpha research cannot be claimed as new here. This paper was inspected during the preceding study; the present OpenReview fetch encountered its browser-verification page. |

The proposed contribution is a **controlled empirical identification study**:
hold the generator, candidate banks, numeric evidence and measurement budget
fixed; distinguish the benefit of acquired information, adaptive acquisition,
selection, and language-model parameter updates. Report failures and feedback
interventions, with every market period retained. This is a research question and
an experimental distinction, not a claim of firstness, new RL theory, or superior
market performance. A literature table does not establish the absence of similar
ablation studies elsewhere.

## Chronology and environment contract

Use the same pinned French49 file as the financial proposal study, SHA256
`8f394fe34bea54d41b9aafed410425ee8f8e252ede3c71a7c1cd20bab83040de`.
The implementation uses the repository's authoritative `EXPECTED_RAW_SHA256`
constant and checks the digest before processing.
Keep the input cap at 2024-12-31 and the five-trading-session label horizon.

Each named assessment half-year is C. Its preceding half-year is B, which supplies
the controller's historical evidence. A is the half-year preceding B. For example,
assessment 2020 H1 uses proposal context 2019 H1 and controller evidence 2019 H2.
This extra separation matters: the existing proposal actor normally sees two
whole-half-year probes. Generating candidates from all of B and subsequently
pretending that part of B is hidden would leak that information through the bank.

Let B have raw row bounds `[l,r)` and set `m=l+floor(2*(r-l)/3)`. The common cheap
signal interval is `[l,m-5)` and the later check interval is `[m,r-5)`. Labels for
cheap observations end before m; labels for later checks end before r. The five
signal rows immediately before each boundary are purged. Assessment C retains
its own five-row purge. Evaluate formulas causally on prefixes ending at the
appropriate boundary; do not expose dates, absolute row indices, task identity,
future metrics or unrequested checks to the actor.

Every candidate receives its cheap historical summary upfront. This cost is
identical across policies and is recorded. There are exactly two check slots,
followed by one final selection; a check reveals that candidate's actual later-B
summary. The second check may depend on the first result. Checks must name
different candidate IDs. Selection can choose any cheap-usable candidate,
including one not checked. There is no early-stop reward or cost saving in this
primary task. There are at most three action attempts. Any malformed, duplicate,
out-of-phase or otherwise invalid action terminates immediately with -1.01 and
the same fixed .01 cost; there is no retry. Invalid final selection or no
usable selection also receives that failure reward. Do not silently repair outputs or
resample invalid proposals. For this first study, duplicated formula slots may
remain in the bank and checking either is charged; log their redundant evidence.

The selected candidate's orientation is fixed once from cheap IC: -1 if negative,
+1 otherwise. A missing cheap mean is unusable. Later feedback never changes
orientation. Terminal reward is this orientation times assessment IC minus .01,
or -1.01 if cheap/assessment support is unusable or final selection fails.
A failed later check is observable missing evidence, not an automatic failure of
an otherwise usable selected factor. Support requires finite IC, at least .8
paired-cell coverage, and at least `max(min(20,L),ceil(.8*L))` scored dates for
that particular purged interval. The constant .01 is an abstract common research
cost, not a transaction-cost estimate. Report IC and failures separately.

This is a new environment, not an extension that inherits the legacy synthetic
environment's empty-selection zero reward or its action-cost conventions.

## Registered immediate CPU feasibility experiment

Use all 16 formulas in the existing ordered `FORMULA_GRID`, unchanged, on the
32 assessment half-years 2002 H1 through 2017 H2. The factor grid is deliberately
privileged, fixed and hand specified. No generated candidates or actual actor
completions enter this phase. Compute candidate outcomes in private evaluator
storage; the full-information regression below may use all later-B checks as an
explicitly privileged diagnostic. Never insert those checks into ordinary agent
observations before acquisition.

Fit two fixed ridge models with an unpenalized intercept. Their target is each
candidate's terminal reward as defined above, including -1.01 failures. One sees
only cheap features. The other additionally sees every candidate's later check.
Neither model observes assessment features. Formula identity is a predictor in
this diagnostic and restricts its interpretation to the fixed 16-formula grid.

The exact cheap feature vector has 28 entries, in this order:

1. Six scalars: absolute cheap mean IC; orientation; cheap daily-IC standard
   deviation; cheap paired-cell coverage; cheap scored-date fraction
   `n_dates/n_signal_dates`; cheap usability as 0 or 1.
2. Six corresponding missing-value flags, each 1 only if its scalar is missing
   or nonfinite. Missing scalars are replaced by zero. Orientation is missing if
   cheap mean IC is missing; usability remains an observed 0.
3. Sixteen formula-identity indicators in `FORMULA_GRID` order.

The privileged vector has 38 entries: append five scalars (cheap-oriented later
mean IC, later daily-IC standard deviation, later coverage, later scored-date
fraction, later usability), then their five corresponding missing flags. If
cheap orientation or later IC is missing, the oriented later mean is missing.
No extra trend, regime, year, date, task ID or feature is selected after outcomes.

For each fold, use training rows only to compute each column's population mean
and standard deviation, including indicators and missing flags. Replace a zero
standard deviation by one. Apply those same constants to evaluation rows. Every
training candidate has weight 1/16, so each training half-year contributes total
weight one. Minimize

```text
sum_training_halfyears mean_16_candidates (reward - intercept - w'z)^2
    + 10 * ||w||^2
```

The regularization coefficient is exactly 10; do not tune it. Fit with the
weighted linear system, leaving the intercept unpenalized. At evaluation, choose
the highest predicted reward among cheap-usable candidates, with grid-order tie
breaking. If none is usable, retain a failed -1.01 outcome.

Two forward folds are mandatory:

| Fold | Fit assessment outcomes | Evaluate assessment outcomes |
| --- | --- | --- |
| 1 | 2002–2009, both half-years | 2010–2013, both half-years |
| 2 | 2002–2013, both half-years | 2014–2017, both half-years |

Report each of the 16 evaluation half-years, both four-year fold means, every
year, and the equally weighted pooled mean. Keep both ridge selectors, fixed
`delay(returns,1)` with no fallback, and the maximum-absolute-cheap-IC selector
with grid-order ties. Also report uniform-grid expectation and a future-reward
oracle as descriptive diagnostics. The oracle must not supply features, teacher
targets, hyperparameters or acquisition rules.

Proceed to a sequential training experiment only if **all** these predeclared
engineering allocation gates pass:

- Pooled privileged-ridge minus cheap-ridge reward is greater than .002.
- That difference is strictly positive in each of the two evaluation folds.
- Pooled privileged-ridge minus fixed lag-1 reward is strictly positive.

These thresholds allocate compute; they are not statistical tests or claims of
economic significance. The privileged ridge is neither a feasible two-check
policy nor a mathematical upper bound. Its failure can reflect model
misspecification. Its success does not show that two checks suffice, that an LLM
can learn their value, or that generated candidates have the grid's opportunity.
Publish the plan before the run and retain failed gates and all comparator rows.

## Conditional sequential study with the actual frozen GenAI component

After a successful CPU gate, create one fixed candidate-bank artifact per task
using the existing financial SFT checkpoint, chosen by its prespecified role,
never by the current transfer results. Generate six proposals with fixed seeds
from **A-only** probe observations; retain every attempt without cherry-picking,
repair or replacement. Add the two predeclared anchors `delay(returns,1)` and
`ts_mean(returns,20)`, giving eight slots. Invalid and duplicate generated slots
remain visible as such. Freeze completion traces, proposal context bounds,
checkpoint hashes, seeds and bank hashes before controller training/evaluation.
All compared controllers receive the exact same banks. Count the common GenAI
calls and common cheap screens in resource reporting.

Before training a bank-based acquisition policy, require at least four distinct,
cheap-usable candidate ASTs in at least 24 of the 32 training tasks. Report the
full per-task counts and a second diagnostic that clusters near-equivalent
cheap-period factor ranks (absolute mean daily Spearman at least .9999). This
diversity gate must be registered and assessed before any controller training;
if it fails, stop rather than make free generation retries or silently insert
extra factors. Passing the AST gate alone does not prove useful behavioral
diversity. If only two usable alternatives remain, two checks exhaust them and
the task cannot identify useful adaptive acquisition.

Use 2002–2017 for controller training, 2018–2019 for one frozen feasibility check,
and 2020–2024 only as explicitly exploratory development. Reusing those years
after multiple study designs forfeits a confirmatory interpretation. The SFT
generator itself was trained on the full pre-2018 training collection, so
training-era bank diagnostics are not clean prospective cross-validation of the
entire GenAI system. The grid gate avoids that particular generator confound.

Compare a small permutation-equivariant numerical controller and a direct LLM
controller, each deciding `check`, `check`, `select`. The numerical controller
needs cheap numeric evidence, observed later evidence, missing/acquisition masks,
and fixed AST descriptors; it must not use formula-ID embeddings learned on a
closed grid as a claimed solution for unseen formulas. Both controllers need the
same available numeric fields and candidate semantics, and legal-action handling
must be documented. The LLM may read expression strings while the numerical
controller uses explicit structural descriptors; this representational difference
must remain visible in the comparison.

The frozen generator plus learned small controller is a **hybrid**. A direct LLM
controller trained through sampled action log-probabilities and terminal reward
is genuine LLM policy training; it still is not end-to-end generator training
while its proposal bank is frozen. A prompt-only direct controller is a baseline,
not RL. Register actual controller feature tensors, architecture, optimizer,
update budget, two seeds, warm-start data and sampler law before that phase.
Do not claim a sequential RL result from the present CPU ridge diagnostic.

The natural RL estimator is trajectory RLOO: independently sample K complete
three-action trajectories for one task, use leave-one-out terminal-return
baselines, and multiply each detached advantage by the sum of that trajectory's
three actor-generated action log-probabilities. Tool text receives no policy
gradient. A shared task is valid for variance reduction; do not reuse the
trajectory's own return in its leave-one-out baseline. Preserve FP32 numerical
checks, normalized sampling-law consistency, and checkpoint roundtrip evidence.
Only genuine training-period outcomes provide policy gradients.

## Controls that identify the benefit

The strongest primary contrast is the learned controller against a fixed
acquisition schedule **with the same final selector**, the same two checks,
bank, target and seeds. A fixed schedule checks the two best cheap candidates;
its final selector is the frozen learned selection component. This isolates the
acquisition decisions more closely than comparing two entirely different agents,
though changed observation distributions remain a limitation. Also retain a
random-two-check schedule with that selector, the scripted cheap selector, and
fixed lag-1. A zero-check ablation should consume two dummy slots and receive the
same constant cost so that differences concern information rather than savings.

For evidence intervention, freeze a candidate-ID derangement within each task.
When candidate i is checked, return the later metric bundle of its predetermined
partner while retaining i's identity; apply i's frozen cheap orientation to the
partner's raw late IC. The true bank, cheap evidence and terminal scorer remain
unchanged. Regenerate complete trajectories with matched random streams rather
than merely rescoring the original actions. This intervention tests dependence
on correct feedback assignment; it does not identify a universal causal value of
all financial information. Record every query, response provenance and selected
formula. An actor that never changes actions under this perturbation has not
demonstrated useful feedback conditioning.

For each controller report paired true-minus-deranged reward and its interaction
with training, plus adaptive-minus-fixed acquisition. Preserve both training
seeds, every half-year and all five development years. Separate the -1.01 failure
component from valid IC, generated-versus-anchor selections, duplicate attempts,
query redundancy, and candidate behavior similarity. Token draws, repeated
trajectories and cloned formula slots are not independent market observations.

## Allocation in the current work window

Complete the already frozen one-shot evaluations first. In parallel, implement
and test the CPU environment and ridge gate on artificial fixtures, publish this
protocol, and then run the training-only gate. Those results are the next
substantive experiment that can realistically be completed without interrupting
the active GPU evaluation. If the gate fails, publish that failure and stop this
branch. If it passes, freeze the actual proposal-bank study and run a small
controller feasibility experiment before committing to multi-turn LLM training.
A complete fair two-controller sequential comparison should not be promised
within the remaining two-hour window.
