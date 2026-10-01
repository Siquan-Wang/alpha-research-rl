# Next research decision: isolate learned evidence acquisition

**Recommendation: do not scale the current financial proposal runs.** The best
next experiment is a new, small information-acquisition benchmark with a known
optimal policy, followed by a bounded test of whether LLM policy training learns
the required feedback-dependent branch. This is future design advice, **not an
executed experiment, a registered protocol, or a restart of either stopped branch**.
It would establish a prerequisite for research agents, not financial alpha or
novel factor generation.

## Why this is the next uncertainty to resolve

The completed studies demonstrate working training and provenance machinery,
but leave the behavioral claim unresolved:

- [Five-policy results](reward-linkage-results-v1.md): correct-reward RL improves
  the sampled failure-penalized objective over its controls, but one seed's
  all-attempt IC contribution is worse. Every greedy policy emits the same
  expression, and evidence interventions do not show a consistent benefit.
- [Proposal diversity](proposal-diversity-v1.md): 861 of 881 usable occurrences
  match teacher-grid ASTs and near-exact teacher ranks on their feedback panels.
  These are repeated exposures across shared tasks, not independent discoveries.
- [Reliability analysis](reliability-analysis-v1.md): true-evidence
  correct-minus-control gains of .023032 and .018368 have estimated conditional
  generation MCSEs .013041 and .018558. Their validity components arise from one
  and two paired slots. More sampling would clarify these particular checkpoint
  means; it would not create adaptive greedy behavior, new candidate diversity,
  independent market periods, or a demonstrated acquisition policy.
- The [constructed curriculum](curriculum-results-v2.md) improved selection
  behavior but passed only 8/24 paired cases and failed every generation pair.
  Its continuation stopped. The [financial sequential gate](sequential-gate-results-v1.md)
  also stopped: privileged extra evidence harmed one forward fold and did not
  beat fixed lag-1. Changing its features or thresholds now would be a different,
  exploratory study, not completion of the failed registration.

There are at least three separate obstacles: usable information may be weak,
the proposal population is narrow, and the actor may not condition correctly
on feedback. Another real-data RL run confounds all three. The proposed task
holds the first two under experimental control to test the third directly.

## One falsifiable experiment: a finite research-choice simulator

Create a separately named environment version. Each episode has four candidate
IDs and one hidden successful candidate, drawn uniformly from the four. Candidates
are a closed catalog; no formula originality or market-return claim is attached
to them. There are three measurement tools and exactly two queries, followed by
one selection. No stop option or unequal cost is available.

A minimal diagnostic channel is a binary hierarchy. Its exact response model is:

| Probability of response 1 | Hidden H0 | Hidden H1 | Hidden H2 | Hidden H3 |
|---|---:|---:|---:|---:|
| Coarse query | .9 | .9 | .1 | .1 |
| Left-pair query | .9 | .1 | .5 | .5 |
| Right-pair query | .5 | .5 | .9 | .1 |

One measurement distinguishes the two pairs. Each other measurement distinguishes
the candidates within one pair and is a fair bit outside that pair. Response
randomness is fixed independently per
episode/tool before any agent acts. The same measurement cannot be repeated.
The first result can therefore change which second measurement is useful.
These are deliberately constructed tool responses, **not computed financial
ICs or simulated investment performance**.

The actor receives the prior, tool definitions and acquired responses. It never
receives the hidden candidate, unrevealed responses, an episode seed, or the
terminal label. Randomly permute candidate IDs, query IDs and bit meanings;
presentation order is determined by those permutations, not independently
randomized. Describe the meanings in the tool interface. Do not encode the
correct answer in an ID, position, expression name or formatting convention.
Reserve disjoint combinations of candidate permutation, query permutation and
bit flips for training, feasibility and final evaluation, with independent
hidden-hypothesis/tool-noise seeds. There are 24 * 6 * 8 = 1,152 presentation
combinations, but these are relabelings of four hypotheses, not 1,152 distinct
mechanisms. Hash every actor-visible mapping, order and bit-meaning field to
check split disjointness. Exact split sizes and seed manifests remain unchosen
until the pre-run protocol. Matched intervention pairs remain one episode.

The question is precise: **does correctly linked trajectory RL improve final
selection and choose the appropriate second query from newly revealed evidence
on unseen ID/order permutations, beyond its untrained parent and matched permutation
controls?** This tests conditional decision learning in a closed task. Even a
positive result would not establish broad research ability or compositional
factor discovery.

Use the already available Qwen backbone with a fresh adapter, rather than
continuing a stopped financial or curriculum checkpoint. Use the same fresh
zero-effect LoRA initialization for all runs, with no optimal-action SFT teacher.
Retain the corresponding untrained backbone policy as the parent. At each decision,
normalize the model's logits over explicitly enumerated legal action tokens;
verify their single-token mappings with the actual tokenizer first. Then
train and sample from that same distribution. This new action interface removes
format repair as a source of reward improvement. It must be implemented and
checked as a new sampling law, not represented as the old full-vocabulary setup.
Reward is one for correct final selection and zero otherwise; every policy makes
exactly two queries, and the common additive cost is zero. Two correct-RL seeds
and two reward-permuted controls start from the same parent bytes and receive
equal update/sample budgets. Record all episodes,
true/assigned rewards, action probabilities and checkpoint identities.

## Controls and prospective allocation rules

Before any LLM training, enumerate the finite belief states on CPU. Solve the
Bayes-optimal two-query policy and the strongest fixed two-query schedule whose
optimal final selector uses **both observed responses**. Optimize over all three
possible distinct-query pairs; random mixtures cannot exceed their maximum.
This separates adaptive acquisition from merely reading evidence at selection.
Include no-query posterior selection, random
queries with that selector, and a small numerical controller receiving exactly
the actor's information. The exact solver is a reference ceiling for the declared
finite task, not a trainable competitor the LLM is expected to beat. An LLM gain
over a weak script would be insufficient.

The eventual protocol should adopt the following allocation rules before runs:

1. Proceed only if exact enumeration shows an adaptive advantage of at least
   .10 in expected correct-selection reward over the strongest fixed schedule,
   and the advantage requires different second queries for different first
   responses. This is an engineering task-quality threshold, not significance.
   If absent, reject this proposed task; do not report an LLM learning failure.
2. First evaluate the untrained parent on the frozen feasibility bank. If it is
   already within .01 expected reward of the oracle, stop: there is little
   learning headroom. Otherwise freeze one RL budget with no development-driven
   extension or best-checkpoint selection. Evaluate each greedy policy on a reserved bank by
   enumerating its two first responses and four response paths, weighting its
   terminal choices by exact likelihoods over all four hidden states. At most
   seven decision calls per policy/presentation remove tool-noise Monte Carlo
   error for that bank, but not training or presentation-transfer uncertainty.
   Retain both RL seeds separately.
3. Evaluate an outcome-scrambled condition using the same episode and policy:
   after each query supply an independent fair-bit response (the uniform-prior marginal),
   independent of that episode's hidden candidate. Evaluate the complete policy
   tree under this changed channel. Also include paired first-response flips
   for which enumeration says the optimal second query changes. Merely changing
   the action string is not success; score whether its change is appropriate.
   Uniform-prior scrambling implies exactly .25 expected success for every
   policy; this is a boundary check, not an additional behavioral discovery.
4. Continue toward any broader agent study only if **both** correct-RL seeds
   improve over their untrained parent and matched controls, capture at least half the
   exact adaptive-minus-fixed reward gap, and make the oracle-prescribed second
   query change on at least 90% of the **entire** reserved presentation bank.
   A pair passes only when the policy queries coarse first and queries the
   appropriate branch on both possible first responses; wrong first queries
   count as failures, with no "applicable case" filtering. Half-gap capture means
   `V(policy) >= V(fixed) + .5 * (V(oracle) - V(fixed))`, anticipated to be .72.
   Report the numerical controller even if it wins.
   Failure ends this version without extra epochs or a replacement test bank.
   These are prospective compute-allocation rules, not a causal proof or an
   arbitrary claim of statistical significance. Presentation-bank sizes and
   training budgets must be frozen in the actual protocol.

The intervention deliberately breaks feedback linkage, so its failure mode is
part of the task definition; it is not an on-distribution financial deployment
test. Successful permutation transfer could still be learning a small decision
algorithm. That narrow result is more informative than calling a fixed research
script an adaptive agent.

## Resources and decision boundary

Use only the existing local CPU, Qwen weights and GPU. CPU enumeration and the
small-controller reference come first. A future implementation should impose a
four-GPU-hour ceiling for four bounded RL runs and frozen
evaluation together, then determine an affordable fixed trajectory count from
an unscored throughput check. This is a resource ceiling, not a measured runtime
estimate. If it cannot support the declared comparisons, reduce the scope before
registration or do not start; an incomplete run is not a failed learning result.

No 2025-or-later market outcome is needed, and no existing financial evaluation
is relabeled as untouched. Bigger same-test sampling is justified only if the
question is the conditional mean of the five existing policies. It is not the
recommended next investment for demonstrating learned evidence-dependent
research. A successful mechanism study would justify asking a separate question
about informative real financial evidence later; it would not reopen the failed
financial gate automatically.
