# Astra study v1: independent orchestration review

**Status: source and artificial-test review completed; no blocking finding remains
in the reviewed implementation.**
Reviewed on 2026-10-01 UTC. This reviewer authored the study protocol and
independently reviewed another agent's orchestration implementation. This is
not an independent review of the reviewer's own protocol and is an
[internal AI-assisted review](README.md), not external peer review.

No model inference, market feedback, or financial assessment was run by this
reviewer. The review used source, artificial test fixtures, and the root's
already completed nonfinancial transport-calibration metadata. It does not
establish the correctness of a future actual collection run.

## Source judgment and concrete resolutions

The collecting interface supplies each broker with `task.feedback_score`, not
the assessment evaluator. Preparation computes historical probes and binds the
ten chronological task manifests. Each registered round starts at most three
calls; all sibling results are retained before another round is accepted.
The neutral actor directory is common across all task/arm calls. Actor prompt
construction excludes task manifests, private selector records and assessment
outcomes; this is an application information boundary, not host isolation.

The source requires all 60 rounds, 30 six-attempt episodes and 180 completed
responses before the submission freeze. A separate assessment command checks
the public/local freeze bytes, recorded round hashes, and recomputed broker
states before scoring only the selected expressions. It never replaces an
unscorable selected factor with a different candidate. A null selection gets
its retained invalid outcome without an evaluator call. Feedback orientation
is checked against the frozen selection; the existing one-proposal reward is
validated before subtracting the remaining `.05` search cost. The resulting
total cost is `.06`, and invalid/unscorable utility is `-1.06`.

Findings were sent to the author before any financial actor run:

| Finding | Resolution in the reviewed implementation/protocol |
| --- | --- |
| Text-mode replay normalized CRLF, potentially rejecting a legitimate exact completed response. | Prompt/response replay now decodes UTF-8 bytes without newline normalization. A complete fake CRLF bank exercises the path. |
| The first contract omitted the runtime/interface/executable identities promised by the protocol. | The contract now records Python and numerical-package versions, instruction/schema identities, and CLI executable name/hash/observed version; collection checks these identities before calls. Installed package binary contents are not individually hashed. |
| The initial assessment summary omitted the two secondary means, annual averages and validity/predictive decomposition. | Assessment now retains all three contrasts, all five year averages, `p`/`q` contributions and conditional-valid IC with its valid count. |
| Full feedback exposed a finer syntax-error code than validity-only. | Root removed the actor-visible failure code while retaining it in records; full and validity-only now differ through the financial/support feedback field. |
| Per-task/arm working directories could disclose the condition or period through CLI host context. | Root and the implementation author replaced them with one contract-bound `actor-context` directory. This reduces an avoidable identifier channel, without claiming that ancestor/system context is absent. |

The current source checks plan, source, raw-data and task-manifest identities
before collection and assessment. Prior prompts, responses and feedback
checkpoints must replay exactly. Exclusive file creation and recorded tree
hashes prevent an ordinary rerun from silently replacing a previous round.
An incomplete failed round prevents continuation and scoring; successful
siblings remain part of the retained evidence. Previously computed historical
feedback may be recomputed for integrity replay, without creating an extra
proposal opportunity or revealing new evidence to the actor.

## Operator responsibilities and claim limits

The code's `verify_committed_files` checks exact **local Git blob bytes** at a
specified commit. It does not contact GitHub or prove remote visibility. Root
must separately verify and retain the public commit evidence before collection
and before assessment. Byte-preserving publication matters: newline conversion
must not be bypassed by relaxing this check.

The quota argument is a root-reported observation, not a programmatic account
sensor. Unknown quota must prevent new launches while root rechecks. A terminal
quota stop must be durably recorded and must not become an unlogged resume or a
smaller comparison bank. The final implementation records `INCOMPLETE` for a
verified reading at or below 5% before an unfinished collection, and exposes
an explicit stop command for a conservative reserve stop. Unknown/invalid
quota values start nothing without falsely declaring a completed stop. A bank
with all 60 rounds complete needs no further actor call. A three-call batch can finish after the latest usage
reading; no exact threshold-overshoot guarantee follows from this mechanism.

Provider success is a checked, completed response-only event stream plus exit
status and final-byte agreement. It does not attest an exact backend model,
absence of undisclosed context, complete hidden computation, or service-internal
retries. The strict provider parser is covered by its separate review/tests;
fake orchestration providers deliberately do not invoke a real CLI or emulate
the entire transport. Their success tests therefore establish the state
machine's behavior, not live provider containment.

The reproduction guide matches the separate prepare, collect, freeze and assess
stages. No actual market outcome follows from these source/artificial checks.
The retained question remains a dependent-period development comparison of
feedback-guided candidate generation with a common selector, not Astra weight
training, an untouched holdout, or profitable alpha.

## Final validation

The reviewer independently ran the earlier complete artificial suite: **26
passed in 162.23 seconds**. Following the author's final quota/interruption and
nonzero-summary changes, the reviewer reran the **10 affected tests on the
final source: all passed in 35.53 seconds**, with 17 unchanged cases deselected.
Targeted Ruff checks also passed. These are overlapping checks, not 36 distinct
cases. Root is responsible for the final integrated suite and real execution.

The final complete-bank fixture preserves 180 CRLF responses before making
exactly 30 selected assessments. Its three arms select different expressions,
have valid counts 8/9/7 and all-period IC contributions `.04/.045/-.014`.
Independent hand arithmetic gives the three mean utility contrasts
`-.105`, `+.154`, and `+.259`, and primary annual contrasts
`[-.45, +.525, 0, -.6, 0]`; the returned summaries match those values. This
checks a nonzero decomposition with failures and negative years, rather than
only identical-arm zeros. Other cases retain null/unscorable selections,
partial failures, changed feedback/source/data identities, and blocked early
assessment. All values in this paragraph are **artificial test values**.

| Final reviewed artifact | SHA256 |
| --- | --- |
| `src/alpha_research_rl/astra_study.py` | `832354133f28110c98a6b3a2b8310a88fd47c9ca3d43803ec0e9dbe1fa1dc6b6` |
| `tests/test_astra_study.py` | `0dc850c400b52e1e34eaf4a8197b4d411e3dfdcdb60498e2a95fb10c03c6494a` |
| `docs/astra-agent-research-plan-v1.md` | `485e09bd0de26614b8831c15e16650d779fdcc71a27b3c89a654c2a249d94f2c` |

The actual collection still requires the published contract, separately
verified remote commits, fresh root quota readings and validated provider
streams. This review neither ran those actors nor pre-judged their outcomes.
