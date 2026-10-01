# Research contribution and current limits

Updated 1 October 2026. **This repository is a reproducible empirical research
project; it has not established a new method or top-conference readiness.** Its
strongest current claim concerns the difference between executable research
behavior, evaluated reward, and useful evidence-dependent proposals in a bounded
financial task. The [research note](research-note-v1.md) states that claim and its
negative results. Internal AI reviews are not external peer review.

## What the evidence supports

The hosted studies contain actual generated proposals, prospectively frozen
comparison rules and later assessment. The local training study contains actual
weight updates and reward-permutation controls. Together they show that the
tested implementations' successful execution or improved failure-penalized
reward did not establish improved evidence-dependent factor discovery beyond
their declared cheap controls.
They do not prove feedback is generally harmful or RL cannot improve research.

The evidence reuses ten development periods and a narrow return-only grammar.
Repeated generations are not independent markets. The data are revised industry
portfolios; historical data vintage and model pretraining exposure remain
unaudited. The hosted model's weights and hidden serving state are not controlled.
These limits matter more to a scientific submission than the number of software
checks or public artifacts.

The [scientific-decoder extension](scientific-decoder-dev-results-v1.md) stopped
before any hosted inference. Its failed target collection supplies no additional
model-performance contrast and cannot strengthen the financial conclusions.

## Three method screens that did not justify a new experiment

These were bounded literature and mathematical checks, with no new model calls,
training or benchmark measurements. A close antecedent can defeat a proposed
novelty claim without proving that an entire research area is solved.

| Candidate | What survived scrutiny | Why the current formulation was closed |
| --- | --- | --- |
| Variance-sensitive feedback for small program edits | Paired comparisons can reduce variance; limiting released feedback can constrain adaptive overfitting. | The [Ladder](https://proceedings.mlr.press/v37/blum15.pdf) already includes thresholded incumbent updates and a practical paired-test variant. [Feldman–Steinke](https://proceedings.mlr.press/v75/feldman18a/feldman18a.pdf) address variance-sensitive adaptive answers, and [Guess-and-Check](https://proceedings.mlr.press/v108/rogers20a/rogers20a.pdf) wraps heuristic answers with validity guarantees. A short code edit is not a certificate of small population disagreement. |
| Information conveyed by adaptive query locations | Removing measured values does not necessarily remove earlier information encoded in the chosen locations. | [Machine teaching](https://proceedings.neurips.cc/paper/2013/file/9c01802ddb981e6bcfbec0f0516b8e35-Paper.pdf) explicitly discusses coordinate encoding; [Deep Adaptive Design](https://proceedings.mlr.press/v139/foster21a/foster21a.pdf) gives the sequential information identity. This is a useful interpretation/control distinction, not a new theorem. It does not invalidate legitimate adaptive data acquisition. |
| RL over certified program-equivalence classes | Distinguishing spelling probability from executed-behavior probability can matter under restricted model parameterization and approximate optimization. | [Marginal Policy Gradients](https://arxiv.org/pdf/1806.05134) already supplies transformed-action score marginalization and variance reduction. [Action Redundancy](https://proceedings.mlr.press/v161/baram21a/baram21a.pdf) regularizes execution effects; [WPR](https://arxiv.org/html/2602.01685v1) studies semantic policy distance; [GraphPO](https://arxiv.org/html/2606.18954v1) shares computation across approximate reasoning states. These methods are distinct, but ordinary probability aggregation is insufficient novelty. |

## A precise limit of the equivalence-class proposal

For a fixed certified class map c(s), write a normalized string policy as
`p(s)=q(c) a(s|c)` and its reference as `p0(s)=q0(c) a0(s|c)`. Assume reward R(c)
is identical throughout each class, beta is positive, and support and finiteness
conditions hold. The ordinary KL chain rule gives

```text
KL(p || p0) = KL(q || q0) + sum_c q(c) KL(a(.|c) || a0(.|c)).
```

This does not establish a better optimal class policy from replacing string KL
with class KL. With unrestricted distributions, both objectives have
`q*(c) proportional to q0(c) exp(R(c)/beta)`; ordinary KL also preserves the
reference spelling distribution within each class. A useful improvement must
therefore concern restricted parameterization, computation or estimation, and
must beat canonical generation with a matched class prior. This is an elementary
consequence of the decomposition, not a new algorithmic result.

Counting sampled equivalent strings does not recover an entire class's model
probability. Grouping all unseen strings into one OTHER bucket can merge different
true classes and split others, destroying a simple KL bound. Equal ranks on a
finite observed panel are also not a proof of program identity. Costs, numerical
domain behavior and missing-data handling must be included in any claimed
equivalence. The present hosted interface supplies neither Astra weight gradients
nor the full probabilities needed for exact class-policy optimization.

## What would justify a larger study

A new methodological study needs a specific claim that survives the closest
existing algorithm, an implementable estimator or mechanism, and a strong cheap
control that could defeat it. The task population and observation process must
be usable under declared numerical and statistical assumptions. Evaluation must
separate validity, predictive contribution, selection and actual compute, with
failure rules fixed before outcomes and meaningful confirmation beyond reused
development data.

A repaired simulator range, another prompt, more repeated samples or a renamed
established estimator would not by itself meet that standard. The existing
evidence can support a bounded empirical submission if a venue welcomes that
scope; no venue acceptance, methodological breakthrough or submission has been
claimed. Further work should be judged by the uncertainty it resolves and the
strength of its contribution, not by quota spent or artifact count.

The [proposed next study](research-next-study-brief.md) narrows this to the
incremental value of structured diagnostics for executable program revision,
separately from external selection. It specifies strong cheap controls and the
missing source-defined task population. It is a research proposal, not an
adopted experiment or an additional empirical result.
