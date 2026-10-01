# Astra feedback study v1: no observed improvement on the registered comparison

The complete three-arm development experiment did **not show a benefit from
full quantitative feedback** on its primary comparison. Full feedback minus
validity-only mean utility was **-0.00636387**.
All 30 final assessments were valid, so the difference is entirely in predictive
IC; invalid-output penalties and the common search cost do not explain it.
Every arm's average future IC was negative before subtracting search cost.

This is a descriptive result for ten previously examined 2020–2024 half-years,
with one generated trajectory per condition and period. It does not establish
that feedback is generally harmful, that Astra cannot conduct research, or
that the project has found profitable alpha.

## What actually ran

The [prospective protocol](astra-agent-research-plan-v1.md) fixed three conditions,
six proposals per episode and a common final selector. The actual actor was the
native Codex CLI requesting `gpt-6-astra`, `ultra` and the default service tier.
Sixty three-arm rounds completed: **180 model decisions and 30 episodes**.
The broker evaluated bounded return-based formulas on historical French49
industry-portfolio feedback. Native shell/web tool events were forbidden by
the experiment and none were observed in the retained response streams.

All three conditions received the same two initial financial probes. Full
feedback then received quantitative metrics for its new proposals; validity
only received grammar and duplicate flags; withheld feedback received attempt
acknowledgments. Every condition's final selector privately used usable
historical scores and chose the greatest absolute IC, breaking ties by the
earliest attempt. Orientation was fixed from historical feedback. This tests
the additional information available during proposal generation, not whether
any part of the pipeline uses financial feedback.

All 180 proposals were grammar-valid and usable on feedback, with zero repeated
canonical ASTs **within an episode**. There were 95 distinct canonical ASTs
across the entire bank. Different ASTs can still produce the same ranked
financial signal; these counts are not discoveries of 95 independent alphas.
No observed validity repair occurred in this collection.

The separate [post-hoc trace diagnostics](astra-trace-diagnostics.md) reproduce
these counts, all ten periods' historical comparisons and missingness rules
from the captured submission bytes, without reading any assessment artifact or
calculating new market scores. Per-condition global AST counts are 51 (full),
43 (validity only) and 41 (withheld); these sets overlap and are not independent
signal counts. The [machine-readable report](../results/astra_agent_v1_trace_diagnostics.json)
retains every episode and charged proposal.

## Publication preceded assessment

- Plan, source and contract: public commit
  [`63394d7`](https://github.com/Siquan-Wang/alpha-research-rl/commit/63394d7d9eb5a10e9dc80b559b88773292868e02), verified before collection.
- All pools and selections frozen: `2026-10-01T09:03:42.501498+00:00`;
  [complete submissions](../results/astra_agent_v1_submissions.json), SHA256
  `89b9cd42d4d248393c2c3c2b9f29714fb9ba023b511d9b3741196d99a321def7`.
- Candidate publication: [`b204714`](https://github.com/Siquan-Wang/alpha-research-rl/commit/b204714539c1ebdf38511631120a1119ce68a3d0).
  Root re-downloaded all 15 bound public files without authentication and checked
  exact bytes at `2026-10-01T09:07:06.866866+00:00`.
- The separate assessment request was recorded at `2026-10-01T09:07:54.001336+00:00`.
  It evaluated only the 30 frozen selections, once each. No later candidate
  substitution, orientation flip, or unselected-candidate future scoring was used.

The [saved assessment](../results/astra_agent_v1_assessment.json) and
[replay result](../results/astra_agent_v1_assessment_replay.json) preserve the
complete arithmetic. Replay passed `STRUCTURALLY_VERIFIED` and
`SAVED_ARITHMETIC_VERIFIED`; this verifies saved structure and arithmetic,
not a fresh recomputation of market scores or an external attestation of private
execution timestamps.

## All conditions and contrasts

| Condition | Valid final outcomes | Mean oriented future IC | Mean utility |
| --- | ---: | ---: | ---: |
| Full quantitative feedback | 10/10 | -0.03382312 | -0.09382312 |
| Validity only | 10/10 | -0.02745926 | -0.08745926 |
| Withheld new feedback | 10/10 | -0.02871876 | -0.08871876 |

For a valid outcome, utility is oriented future IC minus **0.06 abstract search
cost**. An invalid/unscorable outcome would retain −1.06. This is not portfolio
return, Sharpe ratio or transaction cost. With p the valid fraction and q the
sum of valid oriented IC divided by all ten periods, mean utility is
`−1.06 + p + q`. Here p = 1 for every condition.

| Contrast | Mean utility difference | Validity contribution | Predictive contribution |
| --- | ---: | ---: | ---: |
| Full − validity (primary) | -0.00636387 | +0.00000000 | -0.00636387 |
| Full − withheld | -0.00510436 | +0.00000000 | -0.00510436 |
| Validity − withheld | +0.00125950 | +0.00000000 | +0.00125950 |

The primary comparison has 4 positive, 5 negative and 1 tied
period differences. The 2024-H1 loss is particularly large; all periods remain
in the headline. The mixture of signs and single trajectory per arm prohibit
a strong general harm or benefit claim.

| Development period | Full − validity | Full − withheld | Validity − withheld |
| --- | ---: | ---: | ---: |
| 2020-H1 | -0.00968350 | -0.00968350 | +0.00000000 |
| 2020-H2 | -0.00624737 | +0.01863483 | +0.02488220 |
| 2021-H1 | -0.00731279 | -0.00731279 | +0.00000000 |
| 2021-H2 | +0.00777335 | +0.00777335 | +0.00000000 |
| 2022-H1 | +0.02371491 | +0.02371491 | +0.00000000 |
| 2022-H2 | +0.01320808 | +0.01320808 | +0.00000000 |
| 2023-H1 | +0.00726693 | -0.03246064 | -0.03972757 |
| 2023-H2 | -0.01748862 | -0.01748862 | +0.00000000 |
| 2024-H1 | -0.07486966 | -0.04758189 | +0.02728777 |
| 2024-H2 | +0.00000000 | +0.00015265 | +0.00015265 |

| Year average | Full − validity | Full − withheld | Validity − withheld |
| --- | ---: | ---: | ---: |
| 2020 | -0.00796543 | +0.00447567 | +0.01244110 |
| 2021 | +0.00023028 | +0.00023028 | +0.00000000 |
| 2022 | +0.01846149 | +0.01846149 | +0.00000000 |
| 2023 | -0.00511084 | -0.02497463 | -0.01986379 |
| 2024 | -0.03743483 | -0.02371462 | +0.01372021 |

## What the traces demonstrate, and what they do not

The project records an actual generative research loop: the model emits a
formula, a public hypothesis and a revision note; the broker validates it,
returns the assigned evidence, and supplies the permitted history to the next
decision. The [explorer](astra-explorer.html) exposes all 180 decisions with
actor-visible feedback, selector-only evidence and future assessment separated.
Its [rebuild guide](astra-explorer-guide.md) explains verification and limits.

Some full-feedback revision notes refer accurately to earlier saved scores.
That supports observable feedback-referenced behavior, not proof that those
scores causally determined the proposal. Historical best-so-far improvement is
partly built into selecting a maximum and is not future improvement. For example,
in 2022-H2 none of the five later full-feedback proposals exceeded its first
proposal's historical score, so the frozen selector retained attempt 1.

In 2024-H2, full feedback selected a ranked version of the validity arm's
formula. Their saved future ICs are identical despite different ASTs. This is
a concrete reason to separate syntactic exploration from signal diversity.

Supplied initial prompt bytes matched across conditions in all ten periods,
but first formulas differed in six periods. Reported initial input-token counts
also differ by 12 in one triplet. The experiment does not attest identical
hidden host context or reproducible hosted sampling. Fresh ephemeral calls
were not necessarily cache-cold.

## Complete reported usage

Each condition has 60 decisions and no missing usage reports. Fields are shown
separately; reasoning tokens are not added to output tokens. Summed per-call
seconds are not the concurrent collection's wall-clock duration or a price.

| Condition | Input tokens | Cached input tokens | Output tokens | Reasoning tokens | Sum of call seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Full quantitative feedback | 987,445 | 426,496 | 27,052 | 20,181 | 1070.176 |
| Validity only | 979,666 | 489,216 | 30,006 | 23,590 | 1164.815 |
| Withheld new feedback | 977,813 | 514,304 | 28,781 | 22,417 | 1129.652 |

Equal proposal budgets do not imply equal token or computation budgets. No
additional paid API, model purchase or paid data feed was used for this study.

## Scope and next question

The financial panel contains revised industry portfolios, not point-in-time
individual equities. The periods overlap earlier development work; they cannot
be relabeled as an untouched holdout. Ten dependent periods and five year
averages are not 180 independent market replications. One trajectory per cell
cannot estimate generation Monte Carlo uncertainty. The recorded CLI settings
and response-only streams do not attest backend weights or create an
adversarial filesystem read boundary.

This study uses **Astra inference-time adaptation, not Astra weight RL**. The
completed local Qwen post-training experiments remain separate evidence. The
new result establishes a functioning, inspectable research workflow and a
negative registered comparison. Future work should distinguish evidence-responsive
behavior from reliable predictive improvement and quantify repeated-generation
variation. It must preserve this completed bank and its negative result.

Internal AI reviews are [execution/replay evidence](audits/astra-evidence-review-v1.md),
[source-first result interpretation](audits/astra-results-review-v1.md), and
[explorer integrity](audits/astra-explorer-review-v1.md). Review authorship and
limits are disclosed in each record; these are not external peer reviews.
