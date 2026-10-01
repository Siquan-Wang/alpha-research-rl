# Exact information-acquisition opportunity gate, version 1

Scope adopted on 2026-10-01: CPU-only mathematical validation of a proposed
closed-catalog task. This document fixes the kernel and decision rule before
producing its result artifact. It does not register an empirical discovery:
the parameters were chosen to create an adaptive-query opportunity, and the
anticipated values below were calculated by hand before implementation.
No language model, market data, training, generation, paid resource or external
API enters the calculation. It does not reopen either stopped study.

## Chosen finite task

The hidden successful candidate H is uniform over H0, H1, H2 and H3. Three binary
tool responses are conditionally independent given H, with this exact kernel:

| P(response = 1 given H) | H0 | H1 | H2 | H3 |
|---|---:|---:|---:|---:|
| Coarse | 9/10 | 9/10 | 1/10 | 1/10 |
| Left | 9/10 | 1/10 | 1/2 | 1/2 |
| Right | 1/2 | 1/2 | 9/10 | 1/10 |

Every admissible research policy requests exactly two distinct tools and then
selects one candidate. It sees only requested responses. The second query may
depend on the first response. Selection may depend on both responses. A correct
selection earns one, an incorrect selection earns zero, and the common additive
cost is zero. There is no stop action, repeat query, repair, invalid-action
penalty or hidden third query. Candidate generation and formula novelty are
outside scope.

The full outcome space has 4 * 2^3 = 32 hidden-state/three-bit outcomes. A solver
may enumerate these outcomes internally, but a policy decision must use only
its own observation history. This separation is essential: observing all three
bits or the hidden candidate would solve a different task.

## Exact comparisons

Use rational arithmetic, with no random seed or Monte Carlo approximation.
Enumerate all three first-query choices and every map from the first response
to one of the two remaining queries: 3 * 2^2 = 12 deterministic query plans.
For each response path, choose the candidate with largest posterior mass; ties
use the lowest canonical candidate index solely for deterministic display.
This terminal selector uses both acquired responses.

Compare the maximum adaptive-plan value with the maximum value of all three
fixed distinct-query pairs, each also using that Bayes-optimal terminal selector.
A fixed plan may respond to evidence when selecting its final candidate; only
its query schedule is fixed. Random mixtures cannot beat the best deterministic
fixed pair because expected reward is linear in the mixture. Also report every
fixed pair, the uniform mixture over those three pairs and the no-query prior
selector. The last has expected reward 1/4 and is a descriptive reference with
a different query count, not the primary comparator.

The hand calculation anticipates adaptive value 81/100, best fixed-pair value
63/100, remaining fixed-pair value 45/100, uniform fixed-pair value 57/100, and
an adaptive-minus-fixed gap of 18/100. These are design predictions to check,
not already executed experimental observations.

## Pass rule and verification

The gate passes only if the exact adaptive-minus-best-fixed difference is at
least 1/10 **and** an optimal adaptive plan uses different second queries for
the two possible first responses. Report both requirements and every plan,
not only the winner. If either fails, stop this proposed version and retain the
failure; do not adjust the kernel or threshold in the same result artifact.
This is an engineering opportunity check, not a significance test.

Tests must independently compute policy returns by enumerating all 32 outcomes
and executing each plan with only its allowed observations; compare against the
solver's belief/path calculation. Also test an all-fair-bit kernel (zero query
advantage), candidate/query relabelings and response-bit reversals, probability
validation, distinct-query enforcement and total probability one. No third bit
may enter the terminal decision when it was not queried.

Save exact numerator/denominator values alongside display decimals, kernel,
budget, every plan/pair, gate booleans and source/plan hashes. Verify the source
and tests before executing the result-producing CLI. A positive gate establishes
only that this constructed task contains exploitable adaptive information. It
does not show that a language policy can learn it or justify GPU training by
itself. Model initialization, teachers, optimization budgets, seed banks,
presentation splits and later evaluation criteria remain **unadopted** until a
separate pre-run protocol is reviewed.
