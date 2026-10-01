# Design context: identifying useful feedback in alpha research

Reviewed 2026-10-01. This compares two accessible primary works and records an
access limitation for a third. It is design advice, **not an adopted follow-up
model experiment**. No new model calls, candidate assessments, or pool-diagnosis
outcomes informed this note. We have not reproduced these systems on a common
dataset, action space, or budget; their reported scores cannot rank this project.

## What the primary sources establish

**RD-Agent-Quant.** Its five-unit system jointly optimizes factors and models,
with experiment feedback and a contextual bandit choosing the next branch.
Factor-only/model-only ablations and random/LLM/bandit schedulers are useful
controls. The scheduler table fixes twelve hours, with different completed loop
counts. Its stated training/validation/test division is chronological.
These are system/component comparisons; they do not by themselves identify the
effect of truthful numerical feedback on a new proposal from an identical
research state. For our next design, report both attempted evaluations and actual
compute rather than treating either as the other.
[Paper v2, §§2–4 and D.2](https://arxiv.org/html/2505.15155v2).

**QuantEvolver.** It trains a factor generator using executable rewards,
seed-by-window tasks, and diversity/complementarity terms. Its evaluation
separates candidate generation from validation-ranked, decorrelated selection
and fusion. Seed/diversity/DSL ablations distinguish several interventions,
but do not isolate feedback availability within an otherwise identical prompt.
The backbone description needs clarification before reproduction: §IV-A names
Qwen3-14B by default, while §IV-C says all methods use Qwen-3.6-Plus.
[Paper v1, §§III–IV](https://arxiv.org/html/2605.15412v1).
The official release provides reusable interfaces but explicitly omits trained
checkpoints, experiment logs, private data and paper-specific reproduction
scripts. It is therefore a useful design reference, not a verified turnkey
baseline for our resource budget.
[Official README](https://raw.githubusercontent.com/QuantLLM/QuantEvolver/main/README.md).

**AlphaAgentEvo: source limitation.** The task encountered an OpenReview
verification challenge. An [author's publication page](https://wissingchen.github.io/#publications)
confirms the title, but this review found no authoritative alternative full text.
The [primary paper link](https://openreview.net/pdf?id=lNmZrawUMu) remains recorded;
we did not bypass the challenge or substitute third-party summaries for its
methods. No detailed budget, chronology, ablation or replication claim is made
here about that work.

Feedback loops, factor-generation post-training and component ablations are
already established approaches. A useful contribution here would be a cleanly
identified, reproducible result about a narrower decision. From the materials
examined, I did not establish a directly reusable protocol for repeated,
identical-state truthful-versus-masked proposal generation. That is a limitation
of this review's evidence, not a novelty claim or a claim that no such work exists.

## What our evidence still cannot distinguish

[Astra v1](astra-agent-results-v1.md) completed genuine six-step proposal loops,
but generated only one trajectory per arm and period. Its negative full-minus-
validity mean does not locate the failure in generation, selection, feedback
informativeness, or ordinary generation variability. Correctly citing a score
and changing expression text do not establish useful revision. AST uniqueness
also does not exclude rank-equivalent or economically redundant signals.

The separately registered [pool diagnosis](astra-pool-diagnosis-plan-v1.md)
can bound selection headroom inside the already generated pools. Its oracle
cannot establish that the best candidates were recognizable before assessment.
First/minimum-AST selectors cannot establish whether an LLM was needed to
generate those pools. We still lack a matched cheap generator comparison,
replicated hosted generations at identical supplied states, and demonstrated
financial generalization on an untouched evaluation setting.

## A potentially informative next model experiment — unadopted

The falsifiable question should be: **given exactly the same candidate history,
does revealing its truthful historical numerical evidence improve the expected
assessment quality of one newly proposed expression, and its value under a fixed
selector, relative to masking that evidence?** This requires a fresh expression
and a predictive endpoint; choosing the larger of two displayed scores cannot
answer it.

Freeze a small state bank by an explicit history-index rule, independent of
candidate assessment quality. Do not select states where the new pool oracle
looks favorable. Give both conditions the same formulas, initial probes, DSL,
order and grammar status. Remove prior narratives that disclose masked scores
from both conditions; preserve the common text exactly. This is a controlled
new interface, not an untouched continuation of each original actor's history.
Truthful versus masked evidence avoids inventing incoherent score/support bundles.

Collect repeated fresh continuations of each exact prompt. Each continuation
adds exactly one attempted proposal; do not pool repetitions and choose their
best. Freeze repetition count, interleaved launch order, stop rule and total
budget before calls. Record supplied prompts, requested settings, observed
provider events and token usage. Matching calls does not match hidden compute,
and fresh CLI histories do not attest identical hosted model weights or context.

Measure two prespecified quantities: the all-attempt utility of the new candidate
itself, and the change in selected assessment quality after adding it to the
common history under the same feedback-only selector. These separate proposal
quality from the selector's acceptance decisions. Charge the common extra
proposal cost explicitly and retain invalid attempts. Report mean continuations,
not maximum quality, all states and all years. Different strings or a favorable
hindsight replacement are not successful outcomes.

Include inexpensive generators under the same attempted-proposal/evaluation
budget: copy the frozen historical winner; apply one deterministically scheduled
legal AST edit to that parent; and sample from a frozen bounded grammar.
Specify mutation locations, window changes and random seeds before outcomes.
Do not give a cheap baseline an uncounted grid search to choose its one proposal,
or give the LLM free invalid/duplicate retries. Copying supplies a useful
no-quality-improvement reference; matched controls establish whether the LLM
adds value beyond routine local search. Freeze the downstream selector for all
generators and keep any correlation diagnostics separate from selection.

Repeated continuations estimate generation variation conditional on those
fixed states and market panels. They do not create independent financial
histories. Purge label boundaries, freeze directions on historical feedback,
and keep 2025+ sealed. Reusing 2020–2024 would remain explicitly exploratory
development evidence, regardless of how many new expressions are sampled.

Before adopting this experiment, use the completed pool diagnosis only to state
the residual question and an engineering allocation rule. A positive oracle is
insufficient. If no useful question remains beyond selector arithmetic, stop.
If adopted, predeclare that failure to improve the fixed endpoint over masked
feedback and cheap generators ends that version without extra repetitions or
prompt tuning to reverse its sign. No numerical threshold, repetition count,
market extension or training budget is adopted by this note. A future learned
controller would be a separate experiment; hosted Astra inference is not Astra
weight reinforcement learning.
