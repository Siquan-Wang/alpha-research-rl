# Astra v1 retained-evidence and saved-arithmetic review

Review date: 2026-10-01. Status: **PASS within the scope below; no publication
blocker found.** The completed development bank does not demonstrate a benefit
from additional feedback. This review reports the negative primary contrast.

## Reviewer scope and independence

This Astra review lane authored `astra_study.py` earlier. It did **not** author
`astra_replay.py`, its tests, the provider, or the broker. The present work is an
independent review of the replay implementation and a separately written check
of retained evidence and arithmetic, not an independent implementation review
of the reviewer's own orchestrator and not external peer review.

Only saved artifacts and source were read. No actor, tokenizer, model, market
data loader, financial evaluator, network request, or Git operation was run in
this review. No frozen source, protocol, contract, submission, or outcome was
changed. Raw transport locations, thread identifiers, and stderr contents are
not reproduced here. The raw stderr files were hashed, not interpreted as
research evidence.

## Frozen identities and ordering

| Artifact | SHA256 of file bytes |
|---|---|
| `artifacts/astra-agent-v1/contract.json` | `63848687bb44ea7d835b0a2d6ebe88d95dd7ed7257c8ca27dd216a6c37d8b17a` |
| `results/astra_agent_v1_submissions.json` | `89b9cd42d4d248393c2c3c2b9f29714fb9ba023b511d9b3741196d99a321def7` |
| `results/astra_agent_v1_assessment.json` | `30aafbc089f6017c99c6d23c14fca077ffcdf59e9cbf0599d28560c4446ff2a0` |
| Reviewed `src/alpha_research_rl/astra_replay.py` | `245afe1891e811dc81fcd9419b7f68818500b14272e178ee39008d2a36e89ef0` |
| Reviewed `tests/test_astra_replay.py` | `025c163152847effaf893b79068234219af0725b9986facfa8089e598b5c8dcd` |

The 663,206-byte public submission bank matches its local frozen copy exactly.
The public contract and assessment also match their local copies. Both public
replay and the separate checks accept the body digests. The assessment body
digest is `aca23cdd5b05d699d4b91e2f1e02db0a208cb4c5b430ccab4c715f20f523beef`.

Recorded first/last actor times are 07:56:08.806130 and 09:02:52.694557 UTC.
The bank froze at 09:03:42.501498 UTC. All 60 round requests identify the same
source/contract commit, `63394d7d9eb5a10e9dc80b559b88773292868e02`.
Root's retained remote-byte verification record identifies submission commit
`b204714539c1ebdf38511631120a1119ce68a3d0` at 09:07:06.866866 UTC; the assessment
request names that commit and was recorded at 09:07:54.001336 UTC. Thus the
saved publication record precedes the saved assessment request. This reviewer
did not independently fetch the remote or attest wall-clock integrity.

## Actual transport, prompts, masks, and selections

A separate standard-library check, without importing the orchestrator, verified:

- All 10 private task-manifest byte hashes against the contract and identical
  initial evidence across the three arms for each task.
- All 60 round hashes against the bank and all 2,040 recorded round-tree file
  hashes. The 1,080 provider artifact hashes/sizes are a subset of these files,
  not additional distinct artifacts.
- All 180 public transport summaries against their local actor/provider records,
  six provider artifact hashes/sizes per response, raw final-response bytes,
  event final text, and reported usage. Every retained stream has exactly
  `thread.started`, `turn.started`, `item.completed` containing an agent message,
  and `turn.completed`: 720 events in total. **No tool event was observed in
  these retained streams.**
- Every exact prompt reconstructed directly from frozen instructions, initial
  evidence, attempt budget, prior raw responses and permitted feedback. Its
  UTF-8 bytes match both saved prompt copies and the public prompt digest.
  Full feedback contains acknowledgement, grammar validity, duplicate status,
  and financial/support feedback; validity-only contains the first three;
  withheld contains acknowledgement only. Internal failure metadata is not
  introduced into actor-visible feedback. Each history contains only its own
  earlier responses and permitted observations.
- Every request uses the frozen CLI options requesting `gpt-6-astra`, `ultra`,
  default service tier, read-only execution and an ephemeral process, with a
  600-second timeout and the same neutral working directory. Recorded launch
  rotations match the plan. Every round ends before the next round begins;
  every call falls within its recorded round and before the freeze. Recorded
  remaining quota readings are 93–96%, all above the 5% threshold. These are
  root-reported readings, not an independent account/quota audit.
- All 180 proposals are grammar-valid, feedback-usable, and unique by canonical
  AST within their six-attempt episode. Each of the 30 frozen selectors chooses
  the largest absolute saved feedback IC, with earliest-attempt tie handling
  and the matching sign orientation. Each episode has six charged attempts,
  cost 0.06, and a recorded zero pre-freeze assessment-call count.

Targeted searches of the public bank found zero Windows home-path, email,
credential-prefix, or thread-ID-key matches. Exact schema checks also restrict
published transport fields. These checks are bounded publication hygiene, not
a universal absence-of-sensitive-content guarantee.

## Replay implementation and validation

The public replay independently returned `STRUCTURALLY_VERIFIED` for all 30
episodes and 180 responses, exactly matching root's saved structural report.
It checks the frozen contract, twelve source files, protocol bytes, loaded
broker/provider/data/DSL module identities, fixed task/arm order, strict JSON
schemas and types, prompt/response digests, broker transitions, feedback masks,
and selectors. It rejects duplicate JSON keys and non-finite JSON values.

Its tests passed: **41 passed in 2.53 seconds**, using
`python -m pytest tests/test_astra_replay.py -q -p no:cacheprovider` with a
repository-local temporary directory. The artificial cases exercise resealed
tampering, malformed budgets and types, missing/extra rows, transport failure,
source/plan mismatch, path escape, usage missingness, incorrect masks/selectors,
saved outcome arithmetic, and output-overwrite refusal. No extra test was
added because this review found no uncovered implementation defect.

The public replay deliberately does not fetch the private raw artifacts,
recompute financial metrics, validate remote publication, or establish
cross-round chronology. Its report states these limits. The private-artifact
and chronology checks above supplement that narrower public replay; they do
not change what a public user can verify from the public files alone.

## Usage evidence

All 60 responses per arm report each field below. The sums were independently
recomputed from raw completion events and match the public replay.

| Arm | Input tokens | Cached input | Output tokens | Reasoning output |
|---|---:|---:|---:|---:|
| Full feedback | 987,445 | 426,496 | 27,052 | 20,181 |
| Validity only | 979,666 | 489,216 | 30,006 | 23,590 |
| Withheld feedback | 977,813 | 514,304 | 28,781 | 22,417 |

Reported cache-write input is zero for all arms. Token categories are retained
separately; reasoning output is **not added** to output, and cached input is
not added to input. Equal call counts do not imply equal token expenditure or
hidden reasoning compute. Per-call elapsed-time sums are also not study wall
time because the three arms were launched concurrently.

## Saved assessment arithmetic

After root supplied the completed assessment, the replay returned
`SAVED_ARITHMETIC_VERIFIED` for 30 outcomes. A separate arithmetic check matched
all 30 sealed individual files to the report and frozen selections, verified
orientation and saved feedback, and recomputed the 0.01-to-0.06 cost adjustment,
ten paired task rows, five yearly means, all three contrasts, and the validity
and predictive decomposition. It used only saved numbers, with absolute
tolerance `1e-12` for floating-point arithmetic; no market score was recomputed.

| Arm | Valid assessments | Mean oriented assessment IC | Mean utility |
|---|---:|---:|---:|
| Full feedback | 10/10 | -0.033823125 | -0.093823125 |
| Validity only | 10/10 | -0.027459260 | -0.087459260 |
| Withheld feedback | 10/10 | -0.028718764 | -0.088718764 |

The primary mean full-minus-validity contrast is **-0.006363865179299209**.
Full-minus-withheld is -0.005104360743339688; validity-minus-withheld is
+0.0012595044359595214. All validity fractions are one, so every validity
contribution is zero and each contrast equals its predictive contribution.
The primary yearly contrasts for 2020 through 2024 are respectively
-0.007965431, +0.000230283, +0.018461494, -0.005110840, and -0.037434831.
The denominator is ten paired development tasks, not 180 independent trials.

## Claims that remain unsupported

The arithmetic check accepts saved IC values as evidence; it does not verify
them against raw market observations. Hashes establish consistency with these
retained records, not a tamper-proof independent execution log. Zero recorded
pre-freeze assessments cannot certify absence of an unlogged action.

The retained events do not attest the actual backend model identity, absence
of hidden host/provider context, absence of native CLI/service retries, or
absence of all possible tool use outside the retained stream. A shared
read-only working directory is not a read-access sandbox; output-file paths
also exist outside the frozen stdin prompt. Recorded submit order does not
establish backend service order. The neutral directory and response-only
protocol support a bounded workflow claim, not adversarial isolation.

These ten 2020–2024 periods were already development data. There is one actor
trajectory per arm/task, unknown foundation-model historical exposure, shared
initial quantitative probes, unequal reported token use, and no repeated-run
estimate of actor variability. The negative observed contrast is descriptive:
it neither demonstrates a general benefit nor establishes general harm from
feedback. No untouched-holdout, profitability, statistical-significance,
causal-model-mechanism, Astra fine-tuning, RL weight-update, or log-probability
claim follows from this bank.
