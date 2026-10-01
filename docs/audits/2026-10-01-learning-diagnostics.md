# Learning and behavior diagnostics, 2026-10-01

Status: exploratory diagnosis on synthetic development artifacts. No financial
evidence, final evaluation, or demonstrated RL improvement. This audit ran no
model inference or training. It inspected saved reports and replayed the current
scripted teacher on deterministic synthetic panels to examine public feedback.
Recommendations below are a proposed new version, not completed experiments.

## Inspected evidence

| Artifact | Observed result |
| --- | --- |
| `models/runs/sft-v1/training-report.json` | 84 examples and 84 optimizer updates; 2,293,760 trainable parameters; adapter digest changed. |
| `models/runs/rloo-v1/training-report.json` | 16 sampled trajectories across four groups; two groups had exactly equal rewards and skipped updates; two groups updated. |
| `artifacts/development/base-v1.json` | Six tasks, mean reward -0.010000; 60 invalid actions; no submitted factor or accepted proposal. |
| `artifacts/development/sft-v1.json` | Six tasks, mean reward 0.0328327566; zero invalid or duplicate actions; six accepted proposals. |
| `artifacts/development/rloo-v1.json` | Exactly the same greedy action objects and rewards as SFT on all six tasks. |

Development seeds are 11000–11005, cycling signal/null/decay. Their observations
and scores have now been inspected; they cannot subsequently become untouched
final evaluation. The development decoding was greedy, budget 10, with a 64-token
completion cap. No inference about stochastic-development performance follows.

Training-report source hashes differ from the development hash, and the current
source has additional fixes. The v1 reports do not preserve all teacher examples,
raw completion IDs, per-group parameter digests, or a complete start-of-run task
manifest. Current-source teacher replays below are diagnostic reconstructions,
not an assertion that every historical training example was identical.

## Base failure is a format mismatch

All 60 base completions terminate with EOS and contain the same text:

````text
```json
{
  "action": "screen",
  "candidate": 0
}
```
````

`parse_action` requires the entire completion to be a JSON object. Markdown fences
therefore become `{"action":"invalid"}`. Each attempt spends one budget unit;
after ten attempts the empty submitted pool earns zero predictive score and a
0.010 budget charge. This explains all six -0.010 outcomes without invoking token
truncation, missing EOS, hidden assessment errors, or inability to identify a
candidate. The base also fails to correct its repeated formatting after the
visible invalid-action history, but the artifact cannot establish how it would
research under a different parser.

A secondary matched-parser control could accept an exact fenced JSON block for
every actor and separately report that changed interface. It must not replace the
strict-parser comparison retrospectively or provide repeated free retries. Any
constrained decoding alternative must apply to every actor and its exact sampling
distribution must also be used when recomputing training log probabilities.

## SFT learns the action shell, with weak evidence of research adaptation

Every SFT development episode follows:

1. Propose `delta(log(volume),1)`.
2. Screen candidate IDs 3, 0, 1, 2 in that order.
3. Select candidate 0 (`returns`).
4. Stop, after seven budget units.

No episode requests stability or mutation. All six proposed expressions are the
same demonstration template, and none of those generated candidates is selected.
The proposal count proves legal proposal execution, not useful generated-factor
discovery. Canonical AST novelty alone would not establish economic or statistical
novelty either.

The SFT loss falls from mean 0.607435 over the first 20 updates to 0.067870 over
the last 20; 15 of 84 losses are below 0.001. These are teacher-forced losses on
different examples, not a matched validation-loss series or evidence of improved
research. The current teacher has a fixed proposal and screen order, with only
its select/stop branch depending on observed numeric evidence. Its second declared
proposal template is unused by this implementation. Current-source replay of the
12 training seeds produces 12 propose, 48 screen, 12 select, and 12 stop actions;
selected-ID counts are `{0:4, 1:1, 2:5, 3:2}`. Thus fixed prefix imitation has many
repeated examples, while feedback-dependent selection has only twelve examples.
Candidate 0 is not even the majority selection label in that replay.

Public-feedback reconstruction on the six development seeds gives:

| Seed | Regime | IC for ID 3 | IC for ID 0 | IC for ID 1 | IC for ID 2 | Current teacher choice | SFT choice |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 11000 | signal | 0.092318 | 0.151765 | 0.147958 | -0.033287 | 0 | 0 |
| 11001 | null | 0.005225 | -0.000450 | -0.003356 | 0.101176 | 2 | 0 |
| 11002 | decay | 0.049965 | -0.009273 | -0.085917 | 0.040242 | 1 | 0 |
| 11003 | signal | 0.086505 | 0.126505 | 0.045121 | -0.009965 | 0 | 0 |
| 11004 | null | -0.002388 | -0.051626 | -0.054602 | -0.014118 | 1 | 0 |
| 11005 | decay | 0.038754 | 0.073495 | 0.005121 | -0.038754 | 0 | 0 |

The SFT choices match that teacher on three of six tasks. Its mean reward by
regime is 0.126841 signal, 0.006997 null, and -0.035339 decay (only two tasks each).
The teacher is not an assessment oracle: copying its higher absolute feedback IC
can still worsen assessment reward, as the null and decay replays illustrate.
Use agreement to diagnose numeric feedback conditioning, not as the final reward
objective or a claim that the teacher's selection is optimal.

The synthetic generator is also narrow: non-null tasks always use the same
one-day return and log-volume-change families, with fixed coefficients 0.004 and
0.006. Regimes change strength, not which family or lag predicts. That supports
learning a fixed prior and does not require broad adaptive formula discovery.

## RLOO has little exploration and no observed development improvement

The v1 group rewards are:

| Group / task | Regime | Four rewards | Update |
| --- | --- | --- | --- |
| 0 / 2000 | signal | 0.09649481 four times | No |
| 1 / 2001 | null | -0.01558131 three times; -0.01616955 once | Yes |
| 2 / 2002 | decay | 0.07445329 four times | No |
| 3 / 2003 | signal | 0.06680623 three times; 0.01812111 once | Yes |

There are only two distinct action traces among the 16 trajectories: the same
seven-action script selecting ID 0 versus ID 2. Proposal expressions, research
order, and stopping behavior never vary. Fourteen trajectories select ID 0, two
select ID 2; each nonconstant group contains a three-versus-one split. The first
nonconstant group's reward range is only 0.00058824. Adapter changes verify
parameter updates, not improved research. Greedy SFT and RLOO action/reward equality
on six development tasks is a null result for that comparison.

A separate unit fixture found that the old uncentered leave-one-out arithmetic
returned -1.38777878e-17 for three identical rewards of 0.1, causing a spurious
optimizer step. The current centered implementation passes exact-zero and
actual-trainer skip-update tests. That bug is a reason to supersede the v1 trainer
with a registered corrected version; it must not be offered as the observed cause
of this specific run's collapse, because both equal-reward groups actually skipped
their updates in the saved report.

The CPU toy-model tests also verify completion-only next-token alignment, prompt
gradient masking, EOS inclusion, whole-action log-probability sums, and correct
SFT/RLOO gradient direction. They do not establish GPU adapter save/reload fidelity
or equality of actual generation probabilities and recomputed probabilities; those
need the separate local-model probe.

## Proposed small v2 experiment

The immediate goal is to separate syntax learning, evidence-dependent decisions,
and useful expression generation. Keep the current budget charges, horizon
purging, feedback-only orientation, common eligible-asset ranks, and predeclared
coverage/valid-date guards. Do not reward proposal count or AST novelty. Register
the new task manifest, teacher rules, sampling law, source hash at run start, and
failure criteria before running; preserve v1 artifacts.

### 1. Build a small feedback-conditioned teacher set

Use at most 192 decision examples from new training seeds 3000–3023, with one SFT
epoch from the base actor. Include reachable states for every action, weak evidence
and stop cases, unsupported features, exhausted-budget cases, and negative-IC
orientation. Balance decision branches rather than duplicating one seven-action
trace. Generate all teacher labels from acquired feedback, never assessment.

Randomize initial-candidate order before constructing episodes and remap every ID
in evidence, history, selected pools, and mutation provenance. Include paired
numeric decision states where a different screened expression is strongest, and
paired weak/strong states where stop versus continued research is warranted.
Record whether a pair is a real reached state or an explicitly constructed
synthetic diagnostic state. Keep feedback metadata consistent; never relabel
assessment results as feedback.

For generation, the teacher must propose or mutate based on previous acquired
evidence. A small bounded rule can screen two temporal lookbacks, then choose an
intermediate/adjacent unused lookback for the stronger family, or combine two
families that have positive oriented IC across predeclared feedback subwindows.
Use the same source-valid grammar and cost as the LLM. This teacher supplies an
adaptive grammar curriculum; copying its rules alone still does not prove learned
research improvement. Reserve at least two compositional AST forms absent from
the teacher's exact targets for generation diagnostics.

The current task generator does not require family/lag adaptation. A subsequent
version should add predeclared return-only, volume-only, mixed, null, and decay
tasks with lags drawn from a small set such as 1/3/5/10. Task family, coefficients,
and latent regime identifiers must remain outside observations. A new causal
generator requires its own numerical/leakage checks and versioned manifest before
it can support an adaptation claim; do not silently change v1 data.

### 2. Gate SFT behavior before another RL run

Use 24 new paired development decision probes plus twelve new synthetic episodes
(seeds 12000–12011, four per current regime). These are development only. Freeze
probe construction before evaluating and keep probe pairs together when splitting
training and development. Compare strict-parser base, SFT-v1, and SFT-v2 under the
same interface; evaluate the feedback teacher as an imperfect control.

| Development gate | Failure criterion |
| --- | --- |
| JSON and termination | Fewer than 95% valid JSON objects or fewer than 95% EOS-terminated actions. Report the two rates separately. |
| Feedback sensitivity | Fewer than 80% of 24 paired probes change to the intended legal branch when acquired evidence changes. |
| ID permutation | Fewer than 90% of paired permutations preserve the intended selected expression after ID remapping. |
| Grounded generation | Fewer than three distinct accepted non-initial ASTs across twelve episodes, or no accepted expression from the reserved exact-target forms. Novel strings alone are insufficient. |
| Useful generated-factor path | Fewer than 25% of the eight non-null episodes screen and submit at least one generated candidate; separately report its matched assessment reward against a no-generation control. |
| Null behavior | Report early-stop rate, budget spend, and reward separately; do not require discovery or positive reward on null tasks. |

These thresholds are feasibility gates, not significance tests or error-control
guarantees. The usefulness gate can fail when generated expressions are inferior;
do not tune on assessment or force submission merely to pass it. A failed gate
means revise training tasks/teacher evidence and register another development
version, not simply repeat more epochs of the same trace.

### 3. At most eight RLOO groups before reassessing

If SFT-v2 passes those gates, run eight new training tasks (seeds 4000–4007), four
fresh stochastic trajectories per task, one optimizer step per group, corrected
leave-one-out advantages, and the exact logged full-softmax distribution. Keep
temperature 1/top-p 1/top-k 0 while the current likelihood implementation assumes
that law. Do not increase sampling temperature without changing and testing its
likelihood computation. Stop scaling this run if fewer than four of eight groups
have at least two distinct legal action traces and reward range above 1e-4; report
the failed exploration gate and exact skipped-update count.

Log completion IDs, complete public observations or their independently retained
content-addressed records, per-group adapter digests, reward ranges, selection and
proposal diversity, truncations, and invalid/duplicate costs. Prefer a less
overconfident SFT checkpoint selected by the frozen development gates over adding
an undocumented sampler that makes off-policy gradients. Any entropy bonus or KL
constraint would be a separately registered objective change with an exact
implementation and tests, not a retroactive explanation of improvement.

Compare SFT-v2 and RLOO-v2 on the same twelve development episodes, with stop,
matched-budget scripted research, no-generation, and evidence-ablated controls.
Report every paired reward difference and its regime. If mean RLOO-minus-SFT reward
is nonpositive, or fewer than seven of twelve paired tasks improve, call the
development result unsuccessful. Even passing that screening rule does not prove
RL superiority: a larger separately frozen study with new seeds, replicated
training runs, and prespecified uncertainty analysis is still required. Existing
or newly inspected development tasks must remain outside any final sealed study.

## Required interpretation

The demonstrated v1 result is local LoRA training that repairs strict JSON action
formatting and reproduces a largely fixed research script on six synthetic tasks.
It does not demonstrate feedback-sensitive research, useful generated-factor
selection, RL improvement over SFT, generalization across causal signal families,
or financial alpha. V2 should be justified by its observable decision and
generation failures, and should retain null results rather than treating an
adapter digest change as the learning outcome.
