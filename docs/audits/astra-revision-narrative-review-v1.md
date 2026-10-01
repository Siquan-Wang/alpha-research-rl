# Matched-prefix result narrative review

Reviewed on 2026-10-01 after root explicitly released the completed outcomes.
The earlier grounding plan, coding and interpretation were left unchanged.
This is an internal AI review of the result narrative. The reviewer authored
the protocol and grounding audit, but not root's result draft; it is not
independent protocol review or external peer review.

## Reviewed evidence and scope

- [Result draft](../astra-matched-prefix-results-v1.md), reviewed bytes SHA-256
  `d45e5769d05f27167e33fbc255f61112c0d2cb0482c51211e604b958ea7eb54d`.
- [Complete saved result](../../results/astra_matched_prefix_v1.json), SHA-256
  `89162112ddad384ed8917a8b1198ce94044abc90ff15e1680bfe88b66eb43c37`.
- [Frozen score and stopping rules](../astra-matched-prefix-plan-v1.md#scores-denominators-and-fixed-primary-analysis)
  and the previously frozen grounding evidence.

This review checks inferential claims, grounding linkage and interpretation of
the tradeoffs. It does not independently repeat the complete execution-ledger
audit, remote-publication verification or financial scoring. Only saved JSON
was used for the numerical checks; no model, market-data or Git operation ran.

## Actionable findings sent to root

**1. Make the title name the manipulated condition.** The reviewed title,
“accurate explanations did not improve proposal quality,” makes explanation
accuracy sound like the tested intervention. The study manipulated access to
the candidate-feedback package. Accuracy was an ancillary reviewer's coding,
with five retained ambiguities and no randomized explanation-quality condition.
The body already states these boundaries carefully. Suggested replacement:
**“Matched-prefix results: displayed feedback did not improve candidate Q on
fixed development states.”** This preserves the negative primary comparison
without attributing its mechanism to explanation accuracy.

**2. State the stage and nature of the two grammar failures.** Both expressions
are syntactically valid and eligible, but identically zero:
`sub(ts_mean(returns,5),ts_mean(returns,5))` and
`neg(sub(ts_mean(returns,10),ts_mean(returns,10)))`. Their historical records have
`n_dates=0`, null mean IC, `historically_usable=false`, no selector admission and
no candidate outcome key. They receive Q = −1 and G = 0 before any candidate
future evaluation. Add this distinction to the grammar-decomposition paragraph
so the +.05 validity contribution is not mistaken for syntax repair or failure
on a future test. Keep both attempted slots and the original generator unchanged.

These are narrative corrections, not requests for rescoring or new experiments.
Their initial disposition is **sent to root**; the hash above identifies the
pre-correction draft, rather than silently treating a later edit as reviewed.

## Scoped checks with no further blocker

The five-generator table, 40-slot denominators, selection counts, grammar
decomposition and five-pass/eight-fail gate account agree with the saved result.
Separate standard-library sums over the saved rows reproduce the primary
Q difference `−0.006749596592294661`, secondary G difference
`+.0014969201695758517`, and specified conditional MCSE
`.002127476282207234`. This is a focused arithmetic check, not a second complete
ledger reconstruction.

The draft correctly retains the tradeoff: truthful feedback has lower candidate
Q but higher G than masking; truthful G remains negative, below copying and
the scheduled window edit, and below the .01 incremental-cost threshold.
It does not equate more historical selections with prediction improvement.
It also preserves the negative predictive component of the favorable penalized
comparison against grammar, without replacing the all-attempt endpoint by
grammar's conditional-valid mean.

The grounding section distinguishes accurate citation from hidden reasoning
and future usefulness, discloses the reviewer's prior knowledge/authorship, and
keeps the after-collection audit outside the primary endpoint. The uncertainty
section appropriately limits MCSE to conditional generation under an unverified
independence assumption, retains reused dependent development periods, and
avoids significance, profitability, fresh-holdout and Astra-weight-RL claims.
No additional inferential or numerical blocker was found within this scope.

## Resolution: both findings closed

The corrected draft was reread on 2026-10-01. Its title now names **displayed
feedback**, and the grammar paragraph explicitly identifies syntactically valid,
eligible zero-valued expressions with unusable historical feedback (`n_dates=0`),
rather than failed future assessments. Both requested corrections are resolved.
**No open narrative blocker remains within the scope of this review.**

The final correction-verified draft SHA-256 is
`995879688e2bd13e995bc3fab4d8674f826722e8a7775ae07d6c11ba758dc7b6`.
The earlier draft hash and findings above preserve review history. This hash
identifies the reviewed text snapshot; later audit-link additions may change
the publication bytes without being part of this snapshot.
