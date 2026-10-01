# Sealed-confirmation saved-results review

2026-10-01. **Independent saved-array reconstruction passed for all 640 panels;
no discrepancy or unresolved result-integrity blocker was found.** The three
prespecified calibration checks pass. This is a result for the new synthetic
interface, not evidence about the earlier financial studies.

The reviewer participated in the design critique and authored independent
pre-run tests, but authored neither the core nor the runner. The calculation
below used a separate standard-library implementation over saved arrays and
events. It imported no project evaluator, generator, runner or summary function,
generated no new panel, and performed no model, market, network or Git operation.
The review preceded inspection of root's narrative draft. Machine-readable
reported results were visible; this is independent arithmetic, not an
outcome-blinded review or external human peer review.

## Population and reconstruction

The input was the complete
[`sealed_confirmation_v1.json`](../../results/sealed_confirmation_v1.json), its
[execution records](../../artifacts/sealed-confirmation-v1/execution/), and the
[frozen contract](../../artifacts/sealed-confirmation-v1/contract.json).
All 512 null and 128 planted panel IDs appeared exactly once, in the declared
order. Every panel had 256 search rows and 256 confirmation rows, each with six
integer-sign features. Confirmation labels were strict integer signs; all six
prediction vectors had M=256, without abstentions or omitted rows.

The separate calculation encoded feature rows as six-bit sign patterns and
derived parity signs from the parity of the selected negative-feature bits.
It reconstructed each fixed/adaptive search request from the saved features and
appropriate labels, including every alignment, direction, incumbent update,
earliest tie, selected identity and duplicate. It independently rebuilt every
prediction/provenance digest and batch seal. For each resulting prediction it
counted K directly and calculated the reduced rational tail using integer
binomial coefficients, without the core's recurrence.

Exactly **8,960 events, 3,840 arm results, 640 label-materialization events and
82,560 charged feedback requests** were checked. There were 1,920 legitimate
confirmation results and 1,920 protocol-invalid fault results. Every public
panel, its COMPLETED event, its separate completion file and its evidence-map
hash agreed with the reconstruction. The public result was byte-identical to
the retained COMPLETE file.

All reported arm aggregates also matched: rejection counts, exact and displayed
accuracies, signed scores, selected-mask counts, orientation counts, charged
attempts and duplicate counts. This verification retained all 32 fixed requests,
32 adaptive requests and the one-request orientation control; repeats were not
removed or turned into extra independent observations.

## Verified outcomes and decision

| Arm | Null rejections / 512 | Planted rejections / 128 | Planted mean accuracy | Interpretation of statistic |
| --- | ---: | ---: | ---: | --- |
| Fixed correct | 23 | 128 | 0.751434 | Legitimate confirmation |
| Adaptive correct | 21 | 72 | 0.637939 | Legitimate confirmation |
| Oracle | 15 | 128 | 0.751434 | Legitimate confirmation |
| Fixed selection/orientation leak | 480 | 128 | 0.751434 | Invalid naive diagnostic |
| Adaptive selection/orientation leak | 294 | 92 | 0.652588 | Invalid naive diagnostic |
| Orientation-only leak | 39 | 10 | 0.524750 | Invalid naive diagnostic |

Only three entries determine the frozen calibration decision:

- Fixed-correct null: **23 <= 37**, pass.
- Adaptive-correct null: **21 <= 37**, pass.
- Planted oracle: **128 >= 128**, pass.

The exact rejecting threshold is K>=142. The retained pi0 and pi1 fractions agree
with independently calculated binomial tails. The stored null boundary
certificates bracket the allocated 1/300 tail budget, and the oracle lower-tail
certificate equals `1 - pi1^128`. These are the same constants independently
checked before outcomes in the
[pre-run review](sealed-confirmation-review-v1.md). They were not fitted to the
observed counts. This is the declared three-check, single-tail acceptance rule,
not an equivalence test or an estimate that the Type I error equals .05.

All three invalid null controls happen to exceed 37. That observation remains
descriptive: none was used as a validation gate or treated as valid inference.
The orientation-only count of 39 is compatible with an occasionally missed
finite-panel diagnostic; its prespecified ideal-law probability of exceeding
37 is approximately .925587, not one. Each panel also satisfies the predicted
pointwise containment: when the orientation-only calculation rejects, both
selection-plus-orientation calculations reject.

## Timing, seals and publication provenance

Every recorded sequence has the same fourteen-event lifecycle. Both correct
search traces, the fixed/adaptive/oracle vectors and the positive constant base
are contained in PREDICTIONS_SEALED before CONFIRMATION_LABELS_MATERIALIZED.
Reconstruction matched those seals exactly. Each intentional leak has its own
recorded pre-seal accesses and only a `naive_diagnostic`; its valid-confirmation
field remains null. A high apparent accuracy or small naive p-value never changes
that protocol-invalid status.

All event indices, previous-event digests, body digests and timestamps were
checked, including chronology between panels. The retained publication receipt
records exact-byte verification of seven files at
**2026-10-01 13:40:23.540538 UTC**, commit
`00c17f400bda3f25b995db3b8e35150110fe5b97`. Local bytes match every receipt entry:
the six bound plan/source/test files and the contract. Execution STARTED is
**13:40:37.622332 UTC**; the first panel starts at **13:40:37.628233 UTC** and the
last completes at **13:40:59.067740 UTC**. Thus the recorded execution follows the
retained public verification. The reviewer did not repeat the external network
fetch or independently attest the host clock.

| Identity | Value |
| --- | --- |
| Public result size | 2,780,007 bytes |
| Public result file SHA-256 | `ec6d9076d70f50d436c3d69a9ec126d23489f2ce4f98bbf4e25064e6d9c7306d` |
| Result canonical body SHA-256 | `12896c81add67315d60020a3aeac0c2595f8ade6b88684f5ea216844093506a3` |
| Contract file SHA-256 | `12fcd6791ddc2197b4e20350dd80415d5532668ffedf2b66ab0d144d7e6a6ede` |

## What the result supports

The finite execution is consistent with the reviewed sealing interface and its
known conditional-null arithmetic. The positive oracle prevents an evaluator
that simply never rejects from passing this validation. Fixed search selected
the planted mask 3 in all 128 planted panels; the prescribed adaptive procedure
selected it in 69. Its weaker observed power is descriptive of this particular
local-mutation schedule and fixed library, not a general finding that adaptation
is inferior. The planted mask is deliberately available in the fixed bank.
Adaptive-correct's 72 rejections must not be relabeled as 69 true discoveries plus
three false discoveries merely by matching mask IDs.

The binomial law requires independent fair confirmation labels conditional on
the search information, confirmation features and frozen choices. Deterministic
SHAKE streams make this finite bank reproducible; neither saved arrays nor this
review prove independence of a pseudorandom generator. The reviewer deliberately
did not regenerate the streams. Seals and access records support the declared
execution but cannot establish the absence of undisclosed external label access.

The configurations share panels, so six arms do not create six times as many
independent panels. Passing the finite family is not a new theorem, universal
calibration guarantee, GenAI result, discovery of alpha, or permission to attach
these p-values to overlapping financial ICs. No earlier result, frozen study or
failure gate is revised by this check.
