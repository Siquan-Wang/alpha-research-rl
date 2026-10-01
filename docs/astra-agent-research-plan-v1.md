# Astra agent research: development protocol v1

**Status: prospective protocol; no financial actor run or new assessment result
is reported here.** Root must publish this protocol and the implementation/input
manifest before collection. This is a separately versioned study. The earlier
failed sequential gate remains stopped and the local-Qwen mechanism preflight
is deferred. Existing free resources and the user's authenticated Codex allowance
are used; no paid API, purchase, or agent-initiated quota reset is permitted.

## Question, arms, and fixed budget

Does additional historical financial feedback improve an actual Astra agent's
six-proposal candidate pool, when all arms use the same final selector?

The bank is all ten consecutive half-years **2020H1 through 2024H2**, with three
arms per period: `full_feedback`, `validity_only`, and `withheld_feedback`.
Each episode has **six attempted proposals and six fresh CLI decisions**: 30
episodes and 180 decisions if complete. K=6 is a bounded engineering budget
allowing five feedback-informed revisions; it is not a power calculation or a
budget selected from financial outcomes. Each decision proposes one expression.
There is no extra model selection call, free replacement, early success stop,
or actor-generated Python execution.

The primary contrast is **full_feedback minus validity_only**. It measures the
availability of quantitative and data-support feedback beyond grammar feedback,
not the isolated effect of the IC number. Secondary contrasts are full minus
withheld and validity-only minus withheld. All three are reported. Six calls
match proposal opportunities, not tokens, latency, or hidden reasoning compute.

## Data and information boundary

Use the existing cached French 49-industry return panel, raw-source SHA256
`8f394fe34bea54d41b9aafed410425ee8f8e252ede3c71a7c1cd20bab83040de`, with the
study panel capped at 2024-12-31. No 2025-or-later sample enters an actor or
scorer. The downloaded upstream archive can contain later rows; its physical
existence is not a claim that those rows were studied.

Use the unchanged `financial_tasks.py` task factory and evaluator: each target
half-year's immediately preceding half-year supplies feedback; the target
half-year supplies assessment. Five-session forward-return labels must remain
inside their respective half-year, with the existing five-session boundary
purge. Factor calculation is causal and uses only the corresponding prefix.
The manifest retains exact raw, signal, and label-support boundaries.

Every arm starts with identical `ts_mean(returns,5)` and
`ts_mean(returns,20)` evidence: aggregate feedback IC, IC standard deviation,
coverage, date counts, usability, and the same three chronological window
summaries. These two common probes are free setup for all arms and are not
eligible for selection unless proposed in a charged slot. Re-proposing a probe
consumes one attempt. Thus withheld means **subsequent candidate feedback is
withheld**, not that the actor has no initial quantitative information.

The actor receives only the frozen instructions, initial evidence, attempt
budget, and its own permitted history. Task dates, source identifiers, other
arms, earlier project findings, and assessment results are omitted. The broker
accepts a feedback-only callable. Root may hold task objects with assessment
arrays internally; the enforceable workflow claim is no assessment scoring or
disclosure before the submission freeze, not that such arrays cannot exist.

These are reused **development periods**, already examined in earlier work.
They are not a new untouched holdout. Foundation-model exposure to historical
financial material is unknown. Read-only execution on a shared filesystem is
not an adversarial read-access sandbox. Actor instructions forbid tools,
shell/files, web, retrieval, delegation, and cross-agent contact; the retained
event stream must contain no tool events. This cannot certify absence of
unreported provider context or historical pretraining exposure.

## Actor interface and feedback masks

The exact prompt is `ACTOR_INSTRUCTIONS` plus the canonical serialized
observation in the frozen `agentic_research.py`. All arms use identical
instructions; their permitted histories implement the intervention. The output
is one JSON object with exactly `action`, `expression`, `hypothesis`, and
`revision`, all strings, with `action="propose"`. The latter two are brief
public justification/decision summaries, each at most 1,200 characters, not
requests for hidden chain-of-thought. An explanation is not proof that the
stated evidence caused a revision.

Use the existing return-only bounded DSL: supported functions and operators,
integer windows 1–60, finite constants bounded by 1e6, expression length 2,048,
128 AST nodes, and depth 16. Do not repair fenced JSON, extract substrings,
rewrite whitespace in expressions, or execute generated code. Ordinary JSON
whitespace remains governed by the parser. Reject duplicate JSON keys,
nonfinite JSON values, extra fields, and packets over 20,000 characters.
Malformed completed packets and invalid DSL are charged attempts.

Grammar validation uses only the frozen deterministic 61-by-3 synthetic dummy
panel, not market observations. Missing/constant factor output on that fixture
does not itself make a legal expression invalid. Canonical duplication means
identical validated AST; it does not establish economic or rank equivalence.

| Arm | Exact additional response after every completed attempt |
| --- | --- |
| `withheld_feedback` | `{"attempt_recorded":true}` only, including invalid, duplicate, or unusable proposals. |
| `validity_only` | The acknowledgment plus `grammar_valid` and `canonical_duplicate`; no market-dependent usability, support, error, or metric. |
| `full_feedback` | The validity-only fields plus `feedback`; feedback is null when unavailable, otherwise exactly `mean_ic`, `coverage`, `ic_std`, `n_dates`, `n_signal_dates`, and `usable`. |

Failure codes remain in the retained records but are not actor-visible in any
arm. This keeps syntax-error specificity equal between full and validity-only.
The broker privately computes feedback for each unique grammar-valid proposal
in every arm so selection has the same information. Duplicates reuse cached
feedback and consume a slot. Deterministic integrity replay may recompute
previously recorded feedback; it grants no new proposal or actor observation.
No timing, evaluator exception, private ranking,
or hidden-arm metric is added to actor observations. Each new call receives
the initial evidence and its own complete prior records, except that replay
of an oversized raw response is capped at 20,000 characters with its full hash
and a truncation flag. The full raw response is retained outside the prompt.

## Provider, schedule, and failure rule

Use a new ephemeral Codex CLI process for each decision, authenticated through
the existing ChatGPT login. Freeze the resolved executable/version and exact
argument vector. The adopted argument template is:

```text
codex exec --ignore-user-config --strict-config --model gpt-6-astra
  -c model_reasoning_effort="ultra" -c service_tier="default"
  --sandbox read-only --ephemeral --skip-git-repo-check
  --output-schema SCHEMA --output-last-message RESPONSE --json -
```

The prompt is passed through stdin, with `shell=False`. The inspected CLI is
0.159.2; its resolved executable/version must also be recorded at collection.
Every process uses the same neutral working directory, `study_dir/actor-context`,
bound in the contract. Do not use a task-, date-, or arm-named working directory:
CLI host context could otherwise reveal those identifiers. Evidence/output
directories remain separate from this common working directory.
Use the provider's 600-second timeout. No sampling seed or exact server checkpoint is available
to freeze; record requested settings, CLI version, UTC timing, elapsed time,
exit status, and reported usage. Missing usage is unknown, not zero. Requested
`gpt-6-astra`/`ultra` and reported reasoning-token counts do not attest server
weights or total internal computation. The separate nonfinancial CLI smoke
established a functioning response/capture path, not financial capability.
The structured-packet calibration completed at 07:34 UTC on 2026-10-01 with
exit status zero and the same four accepted event types. Reported usage was
15,282 input, 395 output, and 317 reasoning-output tokens; elapsed time was
15.375 seconds. Its retained event SHA256 is
`ef21a9b30520a434513a214d7f49ab4dbe961c72c0dd367f404b5b72df56ba05`.
No broader event allowlist is inferred from this single calibration.
The neutral directory, ephemeral execution, and ignored user configuration do
not establish the absence of host/system or ancestor-directory context; its complete contents are neither attested nor
published. The supplied actor prompt and visible event stream are auditable.

Process periods chronologically. For zero-based period index `t` and attempt
index `j`, submit one three-arm batch in `ARMS` order rotated by `(t+j) mod 3`;
allow at most three concurrent calls. Finish and record that batch before the
next attempt. This rotates launch order without conditioning on results.
Worker/service scheduling can change actual start or completion order; record
observed timing. Contexts, prompts, and records remain separate for every task/arm.

Before **every batch**, root checks the account allowance and the user's stop
rule of approximately 5% remaining. Do not launch when remaining allowance is
at or below 5%, the allowance cannot be verified, or root determines the batch
would breach the available reserve. Unknown allowance pauses new launches for
a recheck; it is not itself a failed model attempt or final study failure.
Root can stop conservatively around 6–7% to preserve checkpoint headroom.
Retain already-started calls; initiate no replacement. This is a bounded operational guard, not a guarantee that delayed
provider usage reporting prevents every threshold overshoot.

There are **zero orchestration/provider-wrapper infrastructure retries**; native
CLI or service-internal retries are not attested. Require exit status zero, exact
agreement between the saved final-response bytes and event text, and exactly:
`thread.started`, `turn.started`, one `item.completed` of type `agent_message`,
then `turn.completed`. The provider's frozen parser also checks exact event
schemas and finite nonnegative integer usage fields when present. Tool,
unknown, error, duplicate, missing, malformed, or ambiguous partial events are
infrastructure/protocol failures. A timeout, cancellation, failure to preserve
evidence, or feedback-evaluator exception also stops collection. Persist raw
streams and partial checkpoints before reporting failure. Distinguish a
completed but malformed policy packet, which consumes its slot, from a failed
transport, which cannot be silently converted into a fresh candidate draw.

Any such failure, or a quota stop before all rounds complete, makes the
**whole fixed-bank study INCOMPLETE**. Root records a terminal reserve/quota stop
through the stop command; a verified reading at or below 5% also invokes that
stop before a new collection call. A completed bank needs no further actor call.
Do not replace a task, discard a triplet, shrink the denominator, compare
unequal prefixes, or run assessment for a full-study headline. Already-started
calls remain logged. Any repaired continuation requires an explicitly new
version; it cannot overwrite this attempt.

## Common selector, freeze, and assessment

After six charged attempts, choose the unique feedback-usable proposal with
greatest absolute mean feedback IC; exact ties select the earliest attempt.
Feedback usability follows the unchanged scorer: finite mean IC, coverage at
least .8, and valid dates at least `max(min(20,L),ceil(.8*L))`, where `L` is the
purged signal-interval length. Fix orientation to -1 for negative feedback IC
and +1 otherwise, including zero. Do not rank, orient, or break ties using
assessment. If no eligible proposal exists, freeze a null selection.

**Complete, persist, hash, and publish all 30 candidate pools and selections
before the first assessment call.** The planned public contract is
`artifacts/astra-agent-v1/contract.json`; the completed submission freeze is
`results/astra_agent_v1_submissions.json`. The submission freeze binds each task/arm,
six responses and costs, private selector inputs, actor-visible histories,
selected expression/orientation, and transport/request identities. The prior
implementation/input freeze binds this plan, actor prompt/schema, provider,
broker, collection driver, chronological scorer and dependencies, exact task
bank, package versions, data hash, and scheduling rule. Root must verify these
identities before assessment. A revised plan or changed contract is a new
version, not an unlogged adjustment.

Then score only the frozen selected expression for each episode with the
existing task evaluator. Verify the feedback-derived orientation against the
freeze. No alternative candidate is substituted when assessment is unusable.
The assessment IC is mean daily cross-industry Spearman IC with the existing
support rule. Charge `.01` for each of six attempts, including invalid and
duplicate proposals: utility is **oriented assessment IC − .06** when valid,
and **−1.06** for null selection or an invalid/unscorable assessment. Adapt the
existing one-proposal scorer's `.01` cost to the registered `.06` total; do not
charge both. These are abstract search-utility units, not trading costs.

## Mandatory reporting and limits

Retain all 180 attempted decision records and all 30 episode outcomes when
complete. Publish all ten paired period differences and all five two-period
year averages for every contrast, including negative values. Report arithmetic
means with equal period weight; each year contains two periods. Show selected
expressions, feedback IC/orientation, future IC/status, per-attempt validity,
duplication and feedback usability, and all observed token/time usage. Public
exports must remove machine/account identifiers without hiding failures; retain
the raw task-local streams and an explicit export/hash mapping. Do not publish
market arrays, credentials, or hidden reasoning.

For each arm, let `p` be the fraction of selected episodes valid on assessment
and `q` be the sum of their oriented ICs divided by **all ten periods**. Then
mean utility is `-1.06 + p + q`. Report each contrast's validity contribution
`Δp` and predictive contribution `Δq`; conditional valid-only IC is a separate
descriptive statistic with its denominator, never a replacement estimand.
One trajectory per arm/period does not estimate generation Monte Carlo error.
The 180 calls are not independent market replications; the ten chronological
periods are dependent and share data across adjacent feedback/assessment roles.
Do not attach an independence-based significance or general causal claim.

No new formula-grid or random-pool comparator is adopted in v1. Earlier grid
results, if mentioned, are context with different budgets and selection rules.
The primary comparator is the same actual Astra agent with the validity mask.
The result can support a limited development comparison of feedback-guided
candidate generation under this selector. It does not demonstrate originality,
profitable alpha, untouched-market generalization, learned Astra weights, or
reinforcement learning. A future outcome-trained controller would be a separate
hybrid study; training an external controller is not Astra weight training.
No controller architecture, training budget, or future RL run is adopted here.
