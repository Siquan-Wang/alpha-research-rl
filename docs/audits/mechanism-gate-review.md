# Exact mechanism opportunity gate: source-first review

Reviewed on 2026-10-01 before root's result-producing CLI. This is an
[internal AI-assisted review](README.md), not external peer review or evidence
of learned language-model behavior. No source or test changes were made by
this reviewer, and no model, market data or GPU was used.

## Reviewed contract and source

The [adopted plan](../mechanism-gate-plan-v1.md) defines four equally likely
hidden candidates, three conditionally independent binary measurements, exactly
two distinct queries and one final selection. It discloses the anticipated
hand-calculated values before execution. It is a constructed mathematical
check, not a preregistered empirical discovery or a reopened financial study.

Inspected `mechanism_gate.py` and all its tests before executing the tests:

- `evaluate_plan` multiplies the prior by only the first and chosen second
  response likelihoods. The unqueried channel is marginalized, not exposed.
  Each leaf maximizes the four joint hidden-state masses for that observed
  history; the value sums the selected joint masses over all four paths.
  Displayed posteriors divide by the path mass. Zero-probability histories are
  represented explicitly without dividing by zero.
- `solve` retains all 12 deterministic query schedules and all three unordered
  fixed pairs. The fixed-pair selector uses **both responses**, so its comparison
  with the adaptive optimum isolates query choice rather than a deliberately
  weakened final selector. Reversing a fixed pair's order preserves its value.
- All inference uses `Fraction`. Binary floating-point input probabilities are
  rejected; display decimals are derived only after exact calculation. The gate
  uses the exact 1/10 threshold and checks response-dependent second querying.
  The no-query 1/4 reference has a different query count and is not the primary
  equal-budget comparator.
- Reports retain all schedules, branch/leaf probabilities, terminal choices,
  exact rational values, kernel, budget and source/plan byte hashes. The CLI
  rejects existing output paths and creates its output exclusively.

An aggregate score alone would not establish the observation boundary. The
independent reference enumerates all 32 hidden-state/three-bit worlds, groups
them by the two responses actually acquired by each plan, constructs the
history-only selector, and executes that selector in a second pass. Every plan's
value, posterior and choice agrees with the solver. Separate tests hold queried
histories fixed while varying the unqueried bit, and replace an entire unqueried
channel for a fixed plan without changing its selector or value.

## Executed validation and conclusion

The reviewer independently ran **26 focused tests: all passed**, and Ruff passed.
Tests also check all-fair-bit channels, candidate/query relabelings, bit reversals,
unreachable paths, malformed probabilities/priors, repeated queries, exact report
serialization and refusal to overwrite evidence. They confirm the disclosed
values: adaptive 81/100; fixed pairs 63/100, 63/100 and 45/100; uniform fixed pair
57/100; no query 1/4; adaptive-minus-best-fixed 18/100. The unique optimal schedule
queries coarse first, right after response 0, and left after response 1.

No blocking source or arithmetic finding remains. The source is suitable for
root's fresh-path result-producing run. A passing gate establishes that this
chosen finite channel rewards adaptive measurement choice. It does not establish
that an LLM has learned it, that an RL update helps, that permutations are new
mechanisms, or that generated factors have financial value. Later model budgets,
initializations, presentation banks and evaluation rules remain outside this
adopted CPU contract.

Verified byte identities at review:

| File | SHA256 |
|---|---|
| `src/alpha_research_rl/mechanism_gate.py` | `b62e94101168d29ac7d0b9d1ee1af7ea733fa5780a9ce7fb44d86d08ed702803` |
| `tests/test_mechanism_gate.py` | `20c2cc0224ad4d4ebc32be7bf2f1c09d4fedc45b0583b4b9ae56089156889ca0` |
| `docs/mechanism-gate-plan-v1.md` | `b0a1ec898affb741a015f8c75e778bc30eb84ac287dbd50f070f9063436d0401` |
