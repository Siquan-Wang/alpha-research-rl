# Astra agent research v1: independent design critique

**Status: prospective development design; no actors or new financial scores
were run for this review.** Reviewed on 2026-10-01 UTC, separately from the
protocol author. This is an [internal AI-assisted review](README.md), not
external peer review. The local-Qwen preflight is deferred and is not evidence
for this experiment.

## Question and adopted scope

The root selected three actual Codex Astra-agent arms: full quantitative
feedback, validity-only feedback, and withheld feedback. Each arm receives six
proposal turns on each of the same ten 2020-2024 development half-years. A common
deterministic selector uses the complete feedback-period evidence for every
arm's final pool. There is no extra model selection turn.

This is a feasible small experiment about **within-episode, feedback-guided
formula proposal** using an existing authenticated Codex allowance. It is not
Astra reinforcement learning, weight adaptation, a probability-level policy
study, or evidence that the agent discovers profitable alpha. The revised
budget is subject to the user's explicit requirement to stop around 5%
remaining allowance. Root controls quota checks and the stop; there is no
authorization here to purchase capacity, reset allowance, or start a paid API.

The matched six-turn design is preferable to comparing six adaptive turns with
one batch-generation call: both conditions have the same number of proposal
opportunities. The common final selector removes model selection skill as an
additional treatment difference. These controls equalize visible decision,
proposal and evaluation budgets, **not hidden reasoning compute**. The later
CLI smoke exposed reported token-usage fields, which should be retained for
each call. Those reports do not reveal model probabilities or establish an
exact backend checkpoint or complete accounting of hidden reasoning compute.

## Required protocol decisions before the first actor

1. **Freeze the estimands.** Full versus validity-only feedback primarily tests
   the incremental effect of quantitative research evidence. Validity-only
   versus withheld feedback tests the effect of validation feedback. Full
   versus withheld is the combined intervention. Register one primary contrast
   or report all three as descriptive development contrasts without choosing a
   winner after results. The ten market periods are paired units, not thirty
   independent markets or 180 independent financial replications.
2. **Specify the observation packets exactly.** Withheld actors should receive
   the same neutral acknowledgment after every attempt, including malformed,
   duplicate or unusable proposals. Validity-only feedback needs an exact
   whitelist: syntax/grammar validity is distinct from scoreability, support
   counts, variation, orientation and quantitative scores. Declare which of
   these it reveals. Full feedback must expose only the registered
   feedback-period metrics. Never accidentally reveal scores through errors,
   status text, ranking, timing annotations or different retry behavior.
3. **Freeze selection and chronology.** Predeclare orientation, feedback score,
   tie breaking, missing-data eligibility, all-invalid fallback, and the
   assessment metric. Select and orient using feedback only. Purge by actual
   label-support dates, not only signal timestamps. Fix the same six-attempt
   cost accounting in every arm. Invalid, duplicate and timeout attempts consume
   budget; do not supply free replacement proposals.
4. **Separate roles and contexts.** Give each task/arm a fresh actor context,
   the same model/effort settings and the frozen actor packet. For native
   collaboration use `fork_turns=none`. For fresh ephemeral CLI calls,
   reconstruct only the permitted visible trajectory in each turn's prompt;
   apply the same stateless protocol to every arm and record that choice.
   Exclude earlier project results, other arms, assessment outcomes, review
   commentary and mutable root instructions. Forbid actor filesystem/network
   reads, arbitrary execution, delegation and cross-agent messages. The root
   broker alone validates the bounded DSL and executes permitted evaluation.
   These are protocol instructions; the actors still possess broader tools.
5. **Freeze execution and stopping.** Record the exact task bank, six-turn
   budget, scheduling order, arm prompts, grammar, broker/selector code and data
   identities before results. Interleave or pre-randomize arm order so one arm
   is not consistently later in a provider session. Record model identifier,
   requested reasoning effort and invocation times; do not invent a sampling
   seed, exact provider weight hash or deterministic replay guarantee. If quota
   ends the run, retain the attempt and report the incomplete fixed bank; do
   not substitute easy periods or rank arms on unequal incomplete coverage.
6. **Freeze submissions before assessment.** Complete and hash all candidate
   pools and deterministic selections before the root inspects any assessment
   metric. Persist every failed or partial trajectory. A failed paired task
   must follow the registered invalidation/fallback rule, never silently vanish
   from the denominator. Do not change prompts or budgets in response to early
   assessment results.

## Broker evidence and containment

### Concrete resolutions communicated by root

Root proposed the following precise v1 choices while the protocol was being
written; they must appear in the final frozen protocol before execution:

- Primary contrast: full minus validity-only. The other two contrasts are
  secondary descriptive development comparisons.
- All arms receive the same two fixed initial probes. Thus "withheld" means
  withholding subsequent candidate feedback, not withholding every piece of
  quantitative information from the agent.
- Validity-only packets contain grammar validity, canonical-duplicate status
  and an attempt acknowledgment. They contain no data-dependent usability,
  coverage or score. Validation uses the frozen DSL on a deterministic 61-by-3
  dummy returns panel. Legal expressions that produce missing values on this
  dummy panel must remain grammar-valid; dummy scoreability is not validation.
- The common selector chooses maximum absolute feedback IC among usable unique
  candidates, breaks ties by first attempt, and fixes orientation from feedback.
  Six proposals incur `.06` cost; the registered all-invalid result is `-1.06`.
  The two common probes' fixed cost treatment must be disclosed separately.
- An incomplete quota-limited bank has no full primary summary. Root retains
  the partial evidence and stops without substituting tasks.

For infrastructure failures, this reviewer recommended at most one exact-input
retry only when a verifiable transport/process failure occurred **before any
assistant content or tool action**. Retain both event streams; the quota stop
overrides a retry. Completed malformed actions, invalid DSL and duplicates are
ordinary charged attempts, not infrastructure retries. A produced or ambiguous
partial candidate followed by failure must not be rerolled. After an exhausted
safe retry, protocol violation or ambiguous partial result, stop before
assessment and retain the incomplete triplet, without replacing a period or
reducing the registered denominator. A uniformly zero-retry policy is also
defensible. The author must select one rule prospectively; ad hoc retries are
not acceptable.

Accept a small strict JSON action schema containing a proposed expression and,
if useful, a short public hypothesis statement. Validate expressions with the
existing bounded AST interpreter. Never execute generated Python. The public
hypothesis statement is an observable explanation, not a record of hidden
reasoning.

For each turn, persist the task/arm identity, ordinal, raw response, parse and
canonical-AST result, duplicate status, charged budget, permitted evaluation
request, exact actor-visible response, wall time/status and prompt digest. Keep
the private-to-actor evaluator record separately from the actor packet. Freeze
the final expression/orientation and record all selector inputs and hashes.
Store records append-only or with exclusive file creation; a late exception
must preserve earlier records. There should be no assessment score in the
actor-visible ledger.

Instruction-level separation on this shared host is not a secure read-access
sandbox. A read-only shell sandbox prevents writes, not reading existing
assessment data or result files. A different working directory alone does not
establish isolation. If a complete tool-event trace is available, audit it for
unregistered evidence access and invalidate the affected comparison according
to the frozen rule. An actor's declaration that it used no tools is insufficient
evidence of tool absence.

### What was established about accessible logs

The reviewer examined the advertised collaboration and Codex app tool schemas,
and ran only `codex exec --help` and `codex --version`. No other conversation
history, credentials, actor inference or network endpoint was read or invoked.

- Native collaboration exposes messages, final outputs, canonical agent names
  and statuses. The advertised API does not provide a full tool-event export.
  The app's `read_thread` provides summaries and potentially truncated outputs;
  this review found no documented mapping from a collaboration name to a
  readable app thread ID. Guessing such IDs or scanning unrelated private
  history is not an acceptable evidence path.
- The installed executable reports `codex-cli 0.159.2`. Its local help confirms
  `exec --json` writes stdout events as JSONL; it also advertises
  `--output-schema`, `--output-last-message`, `--ephemeral`,
  `--ignore-user-config`, and `--sandbox read-only`. This establishes available
  CLI options, not event completeness or model availability.
- The help command warned that it could not find the home directory. Therefore
  executable discovery does not establish working authenticated Astra access
  or which allowance would be consumed. No auth files were inspected, no login
  was changed, and no model was called to resolve that question.

After this initial inspection, root reported a separately authorized
`codex login status` check returning `Logged in using ChatGPT`, without reading
auth-file tokens. Root then completed a new nonfinancial ephemeral Astra smoke
using normal CLI commands and the existing allowance. No financial actor was
run. The reviewer independently parsed only the new smoke's task-local request,
stdout events and saved response; no historical session or credential content
was read.

The request records `gpt-6-astra`, reasoning effort `ultra`, service tier
`default`, read-only sandbox, ephemeral execution, ignored user config, strict
config, an output schema, JSONL events and stdin prompt input. Its event stream
contains exactly:

```text
thread.started
turn.started
item.completed (agent_message)
turn.completed
```

The completed message parses as `{"ready":true}` and matches the separately
saved response. The terminal usage record reports 15,103 input tokens, 15
output tokens, zero cached-input and cache-write tokens, and
`reasoning_output_tokens: 0`. All reported counts are nonnegative integers.
Zero reported reasoning tokens does not prove absence of internal reasoning,
and requested model/effort settings are not a server-side weight attestation.
No tool item is present in this retained stream.

Reviewed SHA256 identities:

| Artifact | SHA256 |
| --- | --- |
| Smoke request metadata | `2892253596324b44a2d75c9cd4c015ecdbfbacc1caf401f609ac6290dda827e2` |
| Smoke JSONL events | `115d300780782f3f3601fa66055245078abb0f269a1de67f8e6c9e106e3f637a` |
| Smoke response | `b342fc286d0216cc212e0d7ba234894e2e7283ddf14f959adf0fe7fd5924308a` |

Root reports exit status zero, consistent with the completed event; process
exit status was not separately persisted in the four reviewed smoke files.
The experimental provider should persist exit status and start/end times along
with stdout, stderr, request metadata and final-response evidence.

The smoke validates a functioning response and capture path for one simple
request. It does **not** establish that every future event will be captured,
that no implicit context was loaded, or that actors cannot read other files.
Each actual run needs a closed event parser: reject tool/unknown/error events,
malformed or incomplete streams, missing or duplicate completions, invalid
usage values and inconsistent final-response evidence. Retain raw streams
before raising. Failure of these checks must stop the study according to the
registered failure rule, rather than trigger a new candidate draw.

Capture each new process's JSONL and stderr directly into task-local files;
there is no need to scan historical sessions. Preserve observed usage when the
CLI supplies it, and treat missing usage as unknown, not zero. Freeze the exact
CLI invocation and actor-context construction after this smoke and before
financial actions. These event records improve auditability over native final
outputs, but they still do not constitute adversarial read-access isolation.

## Interpretation and future assessment

The ten 2020-2024 periods have already informed earlier development. Fresh
actors and hidden prompts cannot turn those market periods into an untouched
holdout. New results remain a paired development study with dependent market
periods and potentially substantial provider variation. Report every
period/arm, validity and duplication rates, selected feedback scores, assessment
ICs and paired contrasts. A higher valid-proposal rate and improved conditional
financial quality are separate outcomes.

A post-2024 interval could become a later unused chronological assessment only
after an exposure audit and separately frozen protocol; this reviewer did not
inspect its availability or outcomes. A repository-unseen historical interval
also does not prove that a provider's pretrained model never encountered it.
Truly calendar-future evidence requires later observations and cannot be
manufactured during this turn. IC is a predictive association metric, not a
transaction-cost-aware trading return or profitability claim.

The proposal is acceptable as the limited, prospectively frozen development
pilot above once the protocol decisions are explicit. It does not support
stronger containment, untouched-holdout, causal market-generalization,
equal-compute, or Astra fine-tuning claims.

## Independent review of the broker state machine

The reviewer subsequently read `agentic_research.py`, its tests and the existing
bounded DSL, and ran CPU tests with synthetic/fake feedback only. No real market
feedback, future assessment, actor inference or model call was made by this
reviewer.

The reviewed implementation accepts only a feedback callable. Initial probe
evidence is constrained to the frozen return-only schema, fixed two expressions
and fixed window count. Quantitative candidate feedback is omitted from both
control prompts; withheld feedback uses the same acknowledgment for every
completed attempt. Grammar checks use the fixed synthetic panel and do not
require finite output values. Selection uses feedback magnitude, earliest
attempt for a tie, and feedback orientation, uniformly across all three arms.
These API properties do not establish that a future caller's feedback closure
contains the correct chronological data; the integration still requires review.

Findings and resolutions:

| Finding | Resolution and observed check |
| --- | --- |
| An evaluator/schema exception originally occurred before the completed response was recorded, allowing the same episode slot to be called again. | The revised code records the raw response, attempt, cost and exception, marks the episode failed, and rejects further prompt, submit and freeze calls. A partial checkpoint remains available. Independently injected failure passes these checks. The orchestration layer must durably save that checkpoint. |
| Nested probe/window `usable` fields could be overwritten for validation but retained in the original actor-visible object, allowing an unvalidated payload through. | Strict five-field nested metric schemas now reject the extra key before merging a synthetic validation flag. Independent sentinel payloads in both overall feedback and a window are rejected. |
| Oversized invalid raw responses could be replayed without bound into later prompts. | Complete raw evidence remains in the record, while observation replay is capped at 20,000 characters and includes full-response SHA256 and a truncation flag. An independent 50,000-character case verifies both retention and bounded replay. |
| An initial duplicate test assumed that leading-space expressions would be repaired. | The author retained the existing DSL's exact acceptance rule and changed the test to the valid AST-equivalent pair `returns` and `(returns)`. Leading-space syntax remains invalid; no new grammar repair was introduced. |

The repaired suite passed **27 tests in 0.67 seconds** with cache disabled and
scratch under ignored `.local/`. Additional independent checks confirmed both
nested-payload rejections, terminal failed-state behavior, oversized replay
hashing, and grammar acceptance of a nested 120-session lag that has all-missing
values on the 61-row dummy fixture. No blocking issue remains in the reviewed
standalone state-machine source. This is not approval of an unreviewed provider,
chronological data binding, orchestration, or final assessment.

| Reviewed source | SHA256 |
| --- | --- |
| `src/alpha_research_rl/agentic_research.py` | `144273c447e001856e1c2137ba2167315e690a8b53bfdd9566ad66e5a534b43f` |
| `tests/test_agentic_research.py` | `c0452f54ebd9956444c263243bbfb8123d55c57195939e19cc25565725d1526e` |
