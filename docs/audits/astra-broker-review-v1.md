# Astra research broker: source-first review and transport evidence

Reviewed on 2026-10-01 before financial actor collection. This is an
[internal AI-assisted review](README.md), not external peer review. The reviewer
did not author `agentic_research.py` or the financial task/scorer, and read their
source before running the broker tests. The reviewer did author `codex_actor.py`;
its fake-subprocess tests are author checks, not an independent provider review.
Root separately executed the nonfinancial transport smoke described below. This
reviewer made no model call and ran no market-data experiment.

## Broker findings

The reviewed [protocol](../astra-agent-research-plan-v1.md) is implemented by the
broker's explicit observation whitelist and common six-attempt selector:

- All arms receive identical instructions and initial probe evidence. Their
  subsequent histories contain only their own raw responses, response hashes,
  attempt counts, and permitted feedback. The broker accepts a feedback-only
  callable; no assessment function or task object is passed to an actor.
- `full_feedback` now adds only `feedback` to the exact validity-only fields.
  That payload contains quantitative scores, support and usability, as declared
  by the primary contrast. Private `failure_code` values are not exposed in
  either arm. `withheld_feedback` exposes only the attempt acknowledgment.
- Grammar checks use the fixed synthetic panel, independently of market
  usability. An undefined or constant factor can remain grammar-valid. JSON
  fences, duplicate keys, unexpected fields, nonfinite packet values and invalid
  DSL are rejected without repair. Invalid and duplicate completed proposals
  still consume a slot; duplicate ASTs reuse cached private feedback.
- The common selector ranks only unique feedback-usable proposals by absolute
  feedback IC, breaks exact ties by earliest attempt, and fixes sign using that
  same feedback. No eligible proposal produces a null selection. A complete
  freeze requires exactly six attempts and includes every response and cost.
- Initial evidence, visible histories, returned records and freezes are copied.
  Oversized raw responses remain fully retained while their prompt replay is
  bounded and explicitly flagged. A propagated feedback exception marks the
  episode failed and prevents continuation or a completed freeze.

No unresolved blocker was found in the broker's masking, charging, caching or
selection rules. This does not certify all study orchestration or publication
behavior; those have a separate review.

## Findings and resolutions

1. **Exact primary-mask regression coverage.** Earlier tests checked the full
   arm's numeric value without requiring that its remaining fields exactly
   equal the validity arm. An accidental syntax-error field could therefore
   alter the primary information contrast without failing that assertion.
   Root added checks for valid quantitative feedback, invalid JSON, and invalid
   DSL: removing only `feedback` from the full response must yield exactly the
   control response. The retained private failure codes are also checked.
   **Resolved.** The reviewer inspected the changes and ran all 29 broker tests:
   all passed in 0.67 seconds.

2. **Task/arm names in CLI working directory.** The initially reviewed
   `astra_study._run_arm` passed each arm's artifact directory as CLI `cwd`.
   That directory contains both task and arm names. Since the native CLI can
   expose working-directory context independently of stdin, this creates a
   avoidable side channel around the prompt's omission of period/arm labels.
   The proposed repair is one fixed neutral working directory for every actor,
   while retaining separate exclusive artifact directories for each attempt.
   Root and the orchestration author were notified before collection. The author
   changed the driver to one registered `actor-context` directory for every
   task/arm and kept distinct artifact directories. The contract checks this
   fixed relative context, and `_run_arm` receives it separately from its output
   path. **Resolved.** The reviewer inspected that data flow and independently
   ran the targeted two-round fake-provider test: all six calls used the same
   neutral directory; the test passed in 0.90 seconds. This removes the explicit
   task/arm path side channel, without claiming removal of all native host context.

## Financial integration boundary

The collector uses the frozen `load_pinned_panel`, capped at 2024-12-31 and
checked against the registered raw-source hash. `FinancialTask` creates separate
feedback and assessment prefixes and purges the five-session label boundary.
Its initial evidence and `feedback_score` use only the preceding half-year's
visible prefix, visible labels and feedback interval. The observation omits
task dates and source identities. The private task object does hold future
arrays, as the protocol explicitly discloses; their existence is not an
assessment score or actor observation.

Source inspection of the existing future-perturbation and boundary tests
supports that separation. This reviewer did not run a historical assessment or
reuse an old outcome to select a formula. The separately gated study driver is
responsible for publishing all submissions before selected-formula assessment.
The old financial evaluation source and saved original reports were not edited.

## Actual nonfinancial provider smoke

Root's single structured smoke used abstract independent, finite-variance,
zero-conditional-mean returns, requested a placebo expression and explicitly
forbade tools. It supplied no empirical feedback or market observations.
The reviewer inspected the supplied prompt, saved final message, event stream
and public summary, then independently verified the sizes and SHA256 hashes of
all six retained prompt/schema/request/event/stderr/response artifacts.

The saved event sequence is exactly `thread.started`, `turn.started`, one
completed `agent_message`, and `turn.completed`. Event text and final-response
bytes agree exactly. Exit status was zero; one provider attempt ran with no
provider retry. Elapsed time was 15.375 seconds. Reported usage was 15,282 input
tokens, 395 output tokens, and 317 reasoning-output tokens; cached input and
cache-write counts were zero. Despite the nonzero reasoning count, there was
no separate reasoning-text item and no tool event in the retained stream, so
the strict parser needed no widening.

This establishes a functioning structured transport path for the requested
`gpt-6-astra` / `ultra` / default service configuration and CLI contract 0.159.2.
It does not attest server weights, hidden context, total internal computation,
unreported execution, native service retries, financial skill or throughput for
the planned study. Public evidence below contains no machine path or thread ID.

| Saved smoke artifact | SHA256 |
| --- | --- |
| Prompt | `14bab1b1d861bf327885851a612520a1a9aa311c9d40c5aa740a9acff70c8798` |
| Response schema | `418ae402d9ca3b9ae234806365c7f97151d7f657d8d8f4c01f9d89f93e6d8aa0` |
| Request metadata | `4823382dfaa80474f826140f406356f876e6ef6ebe4ffb7b60a3bf9e9d802af2` |
| Event stream | `ef21a9b30520a434513a214d7f49ab4dbe961c72c0dd367f404b5b72df56ba05` |
| Stderr | `5ccbc9981cc5b110c889fd270d1398e887415a7ddc0f33b8f3ffa2b9ac0e8b9b` |
| Final response | `c2cdb3b1d6cd050d46d27c92e3f79d50a2419688154cf1b854b439f563543f59` |
| Public-safe result summary | `e286158cc4a28aba84cfeaf2e5b09416f0b66749bbe5dcea7be1a7bafbe5231c` |

Provider author checks separately passed 54 fake-subprocess tests and targeted
Ruff. They cover exclusive attempts, complete byte retention, exact CLI flags,
no-shell execution, strict lifecycle/tool-event rejection, malformed final
packets passed to the broker, timeout/cancellation, and validated usage recovery
from failed streams without converting a failed attempt into success.

Reviewed broker source hash:
`3c51c8ceaf2aba9510cbb92027d9aad67097f84aa0e7a61f30ab15e8a637edce`.
Reviewed broker-test hash:
`349fa75b8aa2da63ddb4ac733761fb7bac95489b5732788e9069247bd238066d`.
