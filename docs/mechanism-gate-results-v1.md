# Constructed adaptive-query opportunity: exact result

The [adopted plan](mechanism-gate-plan-v1.md) was published at commit `3defd2c`
before the result-producing CLI ran on 2026-10-01 UTC. Its bytes remain unchanged.
The kernel was deliberately designed to create a query opportunity; the values
below were anticipated by hand. This is an exact mathematical check, not a
held-out empirical finding or a trained-model result.

| Query policy | Exact expected correct-selection reward |
| --- | ---: |
| Best response-dependent two-query plan | 81/100 |
| Best fixed two-query pair, with optimal evidence-dependent final selection | 63/100 |
| Uniform mixture of the three fixed pairs, with the same final selector | 57/100 |
| No-query prior selection, a different-budget reference | 1/4 |
| Adaptive minus best fixed | 9/50 |

The optimal adaptive plan first requests the coarse query. After response zero
it requests the right-pair query; after response one it requests the left-pair
query. It then selects from the posterior based on its two observed responses.
The coarse/left and coarse/right fixed pairs each attain 63/100; left/right
attains 45/100. Fixed schedules also use both responses for their final choices.

The adopted gate passes: the exact gap 9/50 exceeds the 1/10 task-quality
threshold, and the optimal second query changes with the first response.
All twelve possible query plans, three fixed pairs, response-path probabilities,
posteriors, selected candidates and source/plan hashes are retained in the
[complete rational-arithmetic report](../results/mechanism_gate_v1.json).
Display decimals do not enter the solver.

Twenty-six focused tests passed. A separate full 32-outcome calculation executes
each policy using only its acquired observations and agrees with the solver.
Tests cover unqueried-response invariance, replacement of an unqueried channel,
uninformative channels, relabelings, impossible paths, probability validation
and preservation of existing outputs. The
[separate source review](audits/mechanism-gate-review.md) checked the information
boundary and the strongest fixed comparator before the result-producing run.

To reproduce from a checkout containing the plan, use a fresh path:

```bash
python -m alpha_research_rl.mechanism_gate \
  --plan docs/mechanism-gate-plan-v1.md \
  --output .local/mechanism-gate-reproduction.json
```

The destination directory must already exist; an existing output is rejected.
`python scripts/replay_published_diagnostics.py` instead compares the complete
gate report and its source/plan hashes against the published JSON without
writing an output. It also reproduces the earlier financial diagnostics.

This pass establishes a useful property of a deliberately constructed task.
It does not establish learned adaptive behavior, financial value or novel
formulas. No new language-model training or generation occurred. The
[next-study advice](research-next-steps.md) still needs a separately frozen
learning protocol, including its action law, presentation banks, budgets and
control runs. The stopped financial gate and curriculum remain stopped.
