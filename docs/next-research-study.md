# Next development study: feedback-conditioned formula proposal learning

Written 2026-10-01 before the proposed financial-policy experiment. This is a
prospective development protocol, not a result or a sealed financial test.
Implementation and run manifests must record deviations before scoring the
affected partition. No 2025-or-later outcome is authorized for this study.

## Decision and research question

Run one deliberately narrow experiment: **does on-policy reward training improve
a local LLM's return-only formula proposals on later chronological industry
episodes, and does any improvement depend on the acquired feedback?**

Give the actor two real, precomputed feedback probes. It emits one formula JSON.
A fixed evaluator screens that formula, fixes its sign from feedback, and scores
the next half-year. Compare a frozen formula-SFT actor with its RLOO descendants
under identical prompts, sampling, scoring, and finite proposal budgets.

This is a contextual-bandit proposal task inside the larger research problem.
The expression is generated token by token and the LLM receives real policy
gradient updates. Evidence acquisition, final selection, and stopping are fixed
by the experiment. **It cannot establish that a complete sequential research
policy has been learned.** Keep the existing sequential environment and v1 null
result separate; do not silently change their action or reward contracts.

The expected deliverable in this work window is a reproducible mechanism and
transfer result, which may be negative. A reliable new market predictor is
unlikely to emerge from a 0.6B model, a few dozen dependent training episodes,
and a short run. No choice below presumes that useful market signal exists.

## Why this experiment follows from the source

- `training.py` teaches a repeated proposal/screen prefix, then places reward on
  the whole trajectory. The first 16 RL rollouts explored only two complete
  traces; all proposals were the same volume expression. The six greedy SFT and
  RLOO comparisons were identical. Additional copies of that script are a poor
  test of useful proposal learning.
- `data.py` fixes non-null predictive families and coefficients. Changing seeds
  or signal strength does not require learning a different formula family. A
  strong unconditional prior can look like adaptation in that simulator.
- The constructed 192-example curriculum and paired numeric probes diagnose
  evidence conditioning and ID dependence. Passing those probes would not show
  that realistic research states support useful decisions, that formulas improve
  later-period forecasts, or that RL adds value to SFT.
- `ResearchEnvironment` combines predictive IC and variable research cost.
  Stopping, syntax repair, evidence use, and expression quality are entangled in
  its reward. Fixing the prefix and suffix removes those confounds for this one
  subproblem. No proposal-count or syntactic-novelty bonus is added.
- The real ridge benchmark's interval crosses zero. It does not establish that
  the two probe summaries predict the quality of another formula. A training-only
  opportunity-space check must accompany the LLM comparison.

## Chronological task construction

Use the already pinned official French 49-industry daily value-weighted snapshot,
SHA256 `8f394fe34bea54d41b9aafed410425ee8f8e252ede3c71a7c1cd20bab83040de`.
Load only 2000-01-01 through 2024-12-31. These are industry portfolios, not stocks;
the revised snapshot is not a historical point-in-time vintage. No raw market
panel or per-date output is included in public artifacts.

| Role | Assessment half-years | Count | Permitted use |
| --- | --- | ---: | --- |
| Training | 2002 H1 through 2017 H2 | 32 | SFT feedback labels, RL rewards, opportunity-space checks |
| Feasibility development | 2018 H1 through 2019 H2 | 4 | One frozen syntax/exploration check before transfer |
| Chronological transfer development | 2020 H1 through 2024 H2 | 10 | One matched comparison after checkpoint freeze |
| Excluded | 2025 onward | 0 | No evaluation, tuning, or output inspection |

An episode's feedback is the immediately preceding calendar half-year. H1 ends
at the first session in July and H2 at the first session in January. Use actual
observed trading rows. For horizon five, exclude the final five **signal rows**
of each raw half-year so every target realizes within its own half-year. Feature
history before feedback is permitted. Explicitly save raw boundaries, purged
signal boundaries, and label-support dates in the non-actor manifest.

Assessment blocks do not overlap. Adjacent episodes still share market regimes;
an earlier assessment becomes a later feedback period. That is causal for an
online research workflow, but does not make the episodes independent. The 2020
to 2024 periods have already been inspected for the numerical baseline, so this
study must call them development transfer, never untouched final evaluation.

## Actor-visible evidence and scoring contract

The two fixed probes are `ts_mean(returns,5)` and `ts_mean(returns,20)`.
Each exposes feedback mean daily IC, IC standard deviation, scored-date count,
coverage, and the same summaries in three equal contiguous feedback subwindows.
Five-day targets can overlap across these diagnostic subwindow boundaries;
subwindows are descriptive evidence, not independent validation folds.

The actor receives the expression-to-evidence mapping, supported feature list,
grammar, and fixed task contract. Exclude years, dates, task indices, file paths,
source metadata, teacher labels, assessment values, and latent identifiers from
the prompt. Support counts are legitimate acquired information. Keep separate
public manifests so excluding metadata from prompts does not erase provenance.

Use a dedicated proposal prompt and JSON schema, for example
`{"action":"propose","expression":"ts_mean(returns,10)"}`. State that exactly
one proposal is requested; the sequential actor's menu of screen/select/stop
actions is inappropriate here. Freeze the exact parser and EOS policy for every
LLM comparison. No free retries, inference-time candidate reranking, or hidden
best-of-N selection is allowed.

Only `returns` is an input field. Reject `close` and `volume`, while retaining
the existing bounded DSL's functions, finite constants, and AST/resource limits.
The data adapter's wealth level has arbitrary normalization and volume is absent.
All sampled proposals count, including malformed JSON, unsupported fields,
nonterminated generations, duplicate strings, and unscorable formulas. A formula
equal to an observed probe is permitted in this separate experiment and marked
as reuse; it is not evidence of discovery.

The deterministic evaluator computes the proposal's feedback score and applies
orientation -1 for negative feedback mean IC, +1 otherwise, matching the current
zero convention. It then measures its oriented five-session assessment IC. Both
periods require paired-cell coverage at least .8 and valid IC dates at least
`max(min(20, period_length), ceil(.8 * period_length))`.

- Valid, eligible proposal: `reward = assessment_mean_ic - .01`.
- Malformed, unsupported, nonterminated, constant, or insufficient-support
  proposal: `reward = -1.01`, with an explicit reason.
- The .01 charge is a common fixed-slot accounting convention, not a measurement
  of learned research efficiency. No failed proposal saves that charge.

Report predictive IC, invalid/unscorable incidence, and reward separately. The
strict failure penalty prevents an empty action's zero prediction from becoming
a risk-free competitor to a valid negative forecast. It also means reward can
improve solely through syntax or support repair; validity-conditional IC is only
a secondary diagnostic, since conditioning on success can select different
samples for different actors.

## Fixed reference grid and training-only opportunity check

Freeze this ordered grid before examining its results:

```text
returns
delay(returns,1)
delay(returns,5)
ts_mean(returns,3)
ts_mean(returns,5)
ts_mean(returns,10)
ts_mean(returns,20)
ts_mean(returns,40)
ts_mean(returns,60)
ts_std(returns,5)
ts_std(returns,20)
sub(ts_mean(returns,5),ts_mean(returns,20))
sub(ts_mean(returns,10),ts_mean(returns,40))
div(ts_mean(returns,5),ts_std(returns,20))
div(ts_mean(returns,20),ts_std(returns,20))
mul(returns,ts_mean(returns,5))
```

On the 32 training episodes only, compute:

1. Every fixed formula's aggregate future IC, with its sign always fixed from
   that episode's feedback.
2. Uniform-grid expected reward, calculated exactly by averaging all 16 choices.
3. Feedback-greedy choice: largest absolute eligible feedback IC, ties resolved
   by grid order, then evaluate its feedback-oriented future IC.
4. Assessment-best grid choice using the same feedback-fixed sign. This consumes
   training assessment and is an unattainable opportunity diagnostic, not a
   deployable baseline or evidence of realizable alpha.
5. Counts of teacher target formulas, usable support, and disagreement between
   the two probe rankings. Show whether there is enough variation to teach.

The gap between the grid oracle and a fixed prior distinguishes limited candidate
opportunity from inability to identify it. The feedback-greedy gap distinguishes
opportunity from simple feedback predictability. Neither check proves that a
larger grammar cannot work. Do not choose the reported best grid formula on
transfer outcomes. Do not feed this oracle output into SFT targets or prompts.

The grid-greedy reference screens 16 formulas, more than the two visible actor
probes. Label that information/computation advantage; it is a reference policy,
not a matched-budget competitor. Uniform-grid and any predeclared fixed formula
use the same one-proposal scoring contract as the actor.

## SFT and actual reinforcement updates

Numerical preflight amendment, made before any financial SFT/RL: use float32
model/adapter arithmetic with CUDA and cuDNN TF32 disabled for every financial
proposal checkpoint and comparison. A real Qwen BF16 probe on one training prompt
found exact equality between processed and raw cached logits, confirming the
intended full-softmax sampler, but maximum cached-versus-full-forward token
log-probability difference .464909 and sequence difference .487569 over 21
completion tokens. Preserve that failed numerical check in
`artifacts/development/qwen-sampling-law-v1.json`; it motivated this precision
change, not a financial score. Repeat the identical prompt/seed in float32 and
record the measured discrepancy before training. The completed float32 repeat,
`artifacts/development/qwen-sampling-law-fp32-v2.json`, retained 21 completion
tokens, with processed/raw cached difference zero, maximum token log-probability
difference `2.6226e-5` and sequence difference `2.0981e-5`. This is measured
numerical agreement on that probe, not a universal exact-equality guarantee.
This changes arithmetic on the
cached weights; it does not recover precision absent from their stored values.
Do not silently apply the new precision to earlier BF16 experiments or claim
those runs had exact cached/full-forward numerical equality.

Start a dedicated return-only proposal adapter; do not rely on the v1 volume
proposal habit. The recommended feedback teacher uses the first 12 grid entries,
selecting the largest absolute eligible **training feedback** IC with grid-order
ties. Its targets never use assessment. The last four composite expressions are
reserved from exact SFT targets, although their grammar remains available.

This teacher has evaluated more feedback formulas than the actor sees. State that
it is privileged feedback-teacher distillation and that its target is not ground
truth optimality. Log target counts and every prompt/target. A lack of branch
diversity is a finding, not a reason to fabricate market evidence. Any constructed
augmentation is separately labeled and cannot be represented as an observed
market episode. The agreed run uses all 32 training tasks, three SFT epochs and
learning rate `1e-4`, starting a fresh rank-8 adapter on the cached Qwen3-0.6B
base. Retain one final SFT checkpoint for all comparisons. Freeze the training
example order and all remaining optimizer details before training.

RLOO uses independent full-softmax samples from the current actor, temperature 1,
top-p 1, top-k 0, with a 64-token completion cap and EOS required. Each sample has
one actor completion; the fixed evaluator is not
part of sampled-action likelihood. For four proposals from one task use
`A_i = R_i - mean(R_j for j != i)` and the existing completion-only log-probability
sum. Make one fresh on-policy update per group; skip exactly constant groups.
No replay, group-standard-deviation normalization, KL term, or novelty reward is
silently added.

Agreed bounded run: 16 groups of four proposals, learning rate `1e-5`, no entropy
or KL term. Use one training assessment episode per year 2002 through 2017: H1
in even years, H2 in odd years. This deterministic subset is fixed before
outcomes, not selected for reward. Run seeds 23 and 29 from the same SFT parent
when the window permits, saving each seed's random order of those 16 tasks;
at most 128 RL training proposals across both runs. The source manifest must
also preserve AdamW weight decay zero, gradient clipping at one, and all
sampling settings. Write that manifest before the first rollout.
If time only permits one run, publish that limitation instead of implying
replication; all completed checkpoints must be reported, not the better seed.

The four feasibility episodes are diagnostics, not a hard adaptation gate: a
single formula can be a valid learned prior. Permit eight RL groups as a bounded
mechanism study. After those eight, stop scaling that run if no group contains
at least two legal distinct canonical AST proposals with usable future-IC range
greater than `1e-4`. Otherwise finish the predeclared 16 groups. Invalid-versus-
valid reward variation is syntax exploration and does not satisfy this quality
exploration check. Report the gate as an engineering rule, not a significance
threshold; AST diversity can still include economically equivalent formulas.
Do not select a checkpoint using the later transfer scores.

## Matched evaluation and evidence-use intervention

Freeze SFT and every completed RL checkpoint before transfer scoring. The primary
policy estimand is expected reward under the declared stochastic sampler, not
best-of-N search. Use eight separately seeded proposals per task per checkpoint
and one greedy proposal as a secondary behavior diagnostic. If the time budget
requires four stochastic proposals, freeze that reduced count before any
transfer scoring and disclose the larger Monte Carlo uncertainty. Save every result.
Average all predeclared sampled outcomes within a task, then average tasks with equal weights.
Report the same averages for raw IC with invalid handling explicit. Stochastic
draws improve Monte Carlo precision; they do not create new market episodes.

Required comparisons are SFT, both available RL seeds, uniform grid, and the
feedback-greedy grid reference with its extra information labeled. Base-model
proposal inference may be included as an interface diagnostic if time permits;
SFT versus RL is the scientific comparison. Publish all ten task-level paired
differences, all five year-level paired differences, each training seed, greedy
results, validity, support, and expression frequencies.

Strict JSON is the primary interface for training and all checkpoints. A narrow
whole-fenced-JSON parser can be a secondary reparse of the same saved completions
for every checkpoint. It receives no new generations or retries and must not
replace the primary result because it looks better.

For each LLM checkpoint, generate new completions using the same finite proposal
count and matched random seeds, but with the two probes' **complete feedback
metric bundles exchanged while their expression labels stay fixed**. Do not
reuse the original formula strings: holding actions fixed would make this
intervention's outcome identical by construction. Preserve each bundle's
screen/subwindow/support consistency. No evidence
from another date or future episode is imported. The actual expression evaluator
still uses the true data and fixes sign from the expression's real feedback.
This is a deliberately false evidence-correspondence intervention, not another
valid market scenario or a financial null permutation test.

Define paired descriptive effects:

```text
incremental_RL = reward(RL, true evidence) - reward(SFT, true evidence)
evidence_effect(P) = reward(P, true evidence) - reward(P, exchanged evidence)
grounding_interaction = evidence_effect(RL) - evidence_effect(SFT)
```

Use both reward and valid-proposal predictive metrics, with denominators shown.
An RL gain with no evidence effect can be explained by learning an unconditional
formula prior. An evidence effect with no RL gain is sensitivity without improved
utility. Changed strings alone establish neither. Swapping two correlated probes
may be a weak intervention, which must be reported rather than overinterpreted.

Report exact SFT-target matches, probe reuse, new canonical ASTs, reserved-form
usage, and feedback rank similarity to the nearest teacher formula. Positive
monotone aliases and sign reversals can be economically equivalent after ranking
and feedback orientation. Exact-target novelty is only a compositional diagnostic;
it is not a contribution claim or an objective to maximize.

## Dependence, interpretation, and stop conditions

The evidence is a ten-episode, five-year development comparison with few training
runs. Do not count 49 industries, overlapping five-day labels, generated formulas,
or stochastic samples as independent replications. The main report should use
paired task/year effects and explicit seed variation, without a significance or
financial alpha claim. If a descriptive block interval is added, resample common
date blocks jointly across policies within the same periods, keep a stated block
length, and explain that it conditions on these years and chosen policies. It
does not repair adaptive development reuse or quantify unseen market regimes.

Interpret outcomes in this order:

| Observation | Supported interpretation |
| --- | --- |
| Changed adapter only | Reward-dependent parameter updates occurred |
| Reward rises only because invalids disappear | Interface/support learning |
| Legal formulas diversify without future gain | Exploration without demonstrated usefulness |
| RL improves future reward, but evidence intervention has no effect | Improved proposal prior is plausible; adaptive research is unproven |
| RL improves future reward and evidence-grounding effects recur across seeds/years | Encouraging development evidence for feedback-conditioned proposal learning |
| No improvement over SFT or a simple fixed/grid reference | A documented null result under this budget and task |

Even the strongest row is not novel algorithm evidence, a learned full agent,
causal financial advantage, trading P&L, or stock-level transfer. A later
confirmatory study would need a separately frozen evaluation and stronger
replication. Preserve the 2025+ boundary for that future decision.

Run structural and causal checks before GPU training: date purging, hard upper
date cap, return-only rejection, prefix invariance to assessment perturbations,
feedback-only orientation, strict failure penalty, fixed-cost equality, and
observation/manifest separation. Preserve prompt tokens, completion tokens,
sampler settings, group rewards/advantages, trainable-parameter digests, and
save/reload likelihood checks. Never publish model weights, raw market arrays,
or machine-local private paths inadvertently.

## Implementation ownership and bounded schedule

The parallel CPU implementation is `financial_tasks.py` plus its focused tests:
immutable task factory, half-year manifests, probe-only observations, evaluator,
training-only grid checks, and aggregate output. Root owns the dedicated local
proposal prompt, SFT/RLOO runner, and matched evaluation; only root publishes.
This document owns the question and claim boundaries, not GPU execution.

Prioritize the task/evaluator and preflight, then SFT and the eight-group RL gate,
then bounded training and one frozen transfer comparison. Reserve enough of the
work window for independent review and evidence packaging. If generation or
exploration fails, finish with that measured result and executable reproduction
instructions; do not replace it with more prose, synthetic profitability, or an
unregistered last-minute search.

## Primary references and position

- [AlphaGen (KDD 2023)](https://arxiv.org/abs/2306.12964) optimizes formulaic alpha
  collections using downstream combination performance. Formula-generation RL
  is established prior work; this proposal does not reproduce its market study.
- [AlphaAgentEvo (ICLR 2026)](https://openreview.net/pdf?id=lNmZrawUMu) studies
  multi-turn alpha research with agentic RL and hierarchical rewards. That is
  direct prior art for the larger project. This one-step diagnostic tests a much
  smaller capability and makes no claim to originate agentic factor discovery.
- [Ahmadian et al. (ACL 2024)](https://aclanthology.org/2024.acl-long.662/) motivate
  simple REINFORCE-style LLM optimization. Here rewards come from a numerical
  research evaluator, not human preferences; no reproduction of their results is
  asserted.
- [Agarwal et al. (NeurIPS 2021)](https://arxiv.org/abs/2108.13264) show why few-run
  RL point estimates can be unreliable. Their benchmark inference is not directly
  portable to temporally dependent financial episodes; that motivates explicit
  paired effects and seed limitations here.
- [French's source description](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_49_ind_port.html)
  defines the industry-portfolio source. It does not make these portfolios
  independent assets or establish permission to redistribute the downloaded data.

These references support the design rationale. Whether this particular local
model can learn a useful feedback-conditioned proposal policy remains empirical.

## Design review record

Before the financial preflight, a separate source-first review by the research
environment agent found no fatal chronology, feedback-teacher/assessment-reward,
or claim-boundary issue. It identified an ambiguity in the intervention wording:
reusing formula strings would force zero evidence effect. The protocol now
requires fresh completions under exchanged-evidence prompts with matched random
seeds. This is a conceptual review, not an independent implementation or result
validation. Numerical and training audits still belong with the run artifacts.
