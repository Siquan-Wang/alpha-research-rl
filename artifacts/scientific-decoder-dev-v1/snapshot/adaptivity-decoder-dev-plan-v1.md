# Astra scientific-discovery decoder development gate, v1

2026-10-01. **Adopted for the 16-call development gate only, conditional on the publication/staging requirements and fresh-quota checks below.** The adoption closes preparation before benchmark targets or hosted responses are observed. A possible larger adaptivity-value pilot remains private design advice, with no main bank or adaptive-query experiment allocated. No development score may choose a new prompt, grammar, task, range, seed, or response.

## 1. Question and limits

Can the combination of one fixed fresh hosted Astra terminal-inference procedure and a fixed expression representation use a declared 64-measurement dataset better than its public-task prior and trivial predictors, on four development laws? This is a **joint decoder-and-representation feasibility gate**, not the adaptive-query experiment. Failure cannot distinguish inadequate representation, an insufficient finite dataset, and model inference limitations. It has no planner, no weight update, no symbolic-accuracy judge, and no claim of contamination-free discovery. The reference dataset is space-filling, not chosen using the true law and not guaranteed maximally informative.

Use NewtonBench's **vanilla_equation** scalar observation interface. Its simple-system trajectories are excluded from this version. An expression predicts the same scalar output that a valid experiment observes; it does not receive hidden intermediate labels. This is an explicitly adapted numeric evaluation, not an official leaderboard reproduction. The upstream commit is `912a4ba5f4356ddd06acc16e44460ca30be4abc2`; the reviewed worker verifies its source cache and import origins, uses the selected explicit versions, and requests noise_level=0.0. Root's import-only qualification passed without target queries or hosted/API-module calls. This establishes the checked import route, not successful evaluation at every proposed input. No unlicensed AutoSciLab code is adopted.

## 2. Fixed domain allocation and law identities

Root already computed, without outcomes, the following order. Canonical domain IDs are sorted by the tuple `(SHA256(UTF8("adaptivity-value-v1:domain:" + domain_id)), domain_id)` using the lowercase hexadecimal digest:

1. `m8_sound_speed`
2. `m10_be_distribution`
3. `m1_coulomb_force`
4. `m7_malus_law`
5. `m6_underdamped_harmonic`
6. `m5_radioactive_decay`
7. `m3_fourier_law`
8. `m2_magnetic_force`
9. `m9_hooke_law`
10. `m11_heat_transfer`
11. `m0_gravity`
12. `m4_snell_law`

The first two domains are development domains. The next six are reserved for the proposed main-bank rule, with no main measurements or model calls at this stage. Remaining domains are unallocated. Do not replace `m10_be_distribution` because its representation or fitting is difficult. Observed difficulty belongs to the fixed joint feasibility result; it does not justify selecting a different domain.

Within each development domain select one medium and one hard law. Among public version IDs `v0,v1,v2`, choose the first by `(SHA256(UTF8("adaptivity-value-v1:law:" + domain_id + ":" + difficulty + ":" + version_id)), version_id)`. The saved metadata-only order is [adaptivity-metadata-order-v1.json](adaptivity-metadata-order-v1.json), SHA-256 `7defbfbc0fe602a59bade3941e0442cb5b0cbd6b40976a06f4e216fa6fa4fb4c`. It fixes these four tasks, in order:

| Task index | Canonical law ID |
|---|---|
| 0 | `m8_sound_speed:medium:v0` |
| 1 | `m8_sound_speed:hard:v1` |
| 2 | `m10_be_distribution:medium:v2` |
| 3 | `m10_be_distribution:hard:v0` |

`canonical_law_id` is exactly `domain_id + ":" + difficulty + ":" + selected_version`. IDs and difficulty stay in the custodian record, not actor prompts. No gold formula or outcome was used in this ordering.

Root initially proposed runtime default/10 to runtime default×10 for all positive coordinates. **Before any outputs or contract freeze**, newly extracted public m10 guidance recommended omega scale at least 1e8 and exploration across orders of magnitude to avoid flat regimes. Root therefore replaced the proposed m10 box `[1e7,1e9] × [100,10000]` with `[1e8,1e16] × [10,10000]`; m8 retains the default-centered rule. This is a recorded metadata-based design revision, not outcome-based resampling. Both domains use log10-coordinate sampling in unconverted raw benchmark units.

No common official finite-bounds registry was established. These supports are adapted measurement domains, not upstream finite bounds or a claim that every combination is physically realistic. In particular, the adiabatic-index box is broader than ordinary gas values; the public schema only requires positivity. The revised m10 range is a prospectively chosen finite extent, not a guarantee of whole-function coverage. After freeze no outcome-based tightening, resampling or favorable replacement is permitted.

| Domain | Actor input | Public input | Frozen interval | Unit label |
|---|---|---|---|---|
| sound speed | x0 | gamma, adiabatic index | [.14,14] | dimensionless |
| sound speed | x1 | T, temperature | [29.315,2931.5] | Kelvin |
| sound speed | x2 | M, molar mass | [.002897,.2897] | kg/mol |
| Bose–Einstein distribution | x0 | omega, angular frequency | [1e8,1e16] | angular frequency in benchmark input units |
| Bose–Einstein distribution | x1 | T, temperature | [10,10000] | temperature in benchmark input units |

The map from a unit-cube coordinate u is `10**(log10(lower)+u*(log10(upper)-log10(lower)))`, with no output rescaling. Both versions within a domain use the same box. Public schema/default evidence is retained in `.local/newton-adapter-metadata-v1.json` (SHA-256 `df3b5f05bbb3c9e4d259577aa180a4a2178fcda768ede1b2315ac1511d309028`). The main domains' bounds are not selected from development success. Extreme-range oracle and expression behavior must be documented before running: an exponential can overflow even when an algebraically equivalent physical response has a finite limit. No alternative oracle arithmetic or redraw may be introduced after seeing a failure.

## 3. Dataset construction and information boundary

Root has now generated and frozen **coordinates only, without oracle outputs**, in `.local/adaptivity-dev-coordinates-v1.json`, SHA-256 `1555c66e856f1451dbf151bb1aafe48474cae2fe1885f9cf37762d966e26211d`, at `2026-10-01T16:26:47.456615+00:00`. The manifest reports zero training targets, confirmation targets and hosted calls. The construction is `scipy.stats.qmc.Sobol(d, scramble=True, bits=30, rng=numpy.random.default_rng(seed), optimization=None)` in the frozen transformed unit cube, followed by `random_base2(m=6)` for 64 training coordinates or `random_base2(m=8)` for 256 confirmation coordinates; installed versions are NumPy 2.5.3 and SciPy 1.18.1. The root generator uses the default bits/optimization values corresponding to those shown explicitly here. The seed is the unsigned big-endian integer represented by the first eight bytes of `SHA256(UTF8("astra-adaptivity-decoder-dev-v1|" + canonical_law_id + "|" + split))`, with split exactly `train` or `test`. Each split uses a fresh generator; no search over scrambles. These saved coordinates, rather than regenerated draws, are the prelaunch inputs.

Coordinate-support, duplicate and cross-split checks have passed without evaluating targets; preserve their inputs and validation outcome. There are exactly 64 training and 256 confirmation coordinates per law, with no target-conditioned rejection sampling or new seed search.

The source-only closure audit `.local/newton-source-determinism-audit-v1.json`, SHA-256 `fc66899332a83fe6adeb49a2c9b985cc524f0536c159039c3dec7993f55bdc88`, reports `SOURCE_CONDITIONAL_CLEAR` for all four selected functions. It found no reachable RNG, unknown external call/name, state mutation or dynamic import in the selected closure. Supplying explicit versions excludes the selector's random-choice branch. The reviewed m10 NumPy error-policy contexts have fixed configuration. Together with noise_level=0.0, this supports deterministic target evaluation **conditional on pinned source, unmodified modules and the fixed numeric runtime**. The audit did not execute a law, disclose formulas, or prove totality, numerical finiteness or representability. There is no noise averaging or alternative random replicate in this version.

Then materialize the 64 training responses once per law. Simulator exceptions or nonfinite training targets stop the development run as incomplete, preserving every attempted point. The prior-only prompt receives no training response. The reference-data prompt receives all 64 exact input/output pairs; no selected subset, rounding chosen from outcomes, fitted parameters, candidate functions or withheld scores.

**Confirmation targets are not materialized before all 16 final packets are durably frozen.** The coordinate file may exist only in the custodian/evaluator record. Actor inputs contain neither test coordinates nor outputs, file paths, task/version/difficulty IDs, condition labels, repetition IDs, seeds, or other models' responses. The exact common public problem metadata and variable mapping are identical between a law's two conditions; only the observation list differs. Each condition's two calls use no prior conversational state. No model may inspect repository files or call tools. Shared-host restrictions and absence of observed tool events are not an adversarial sandbox or evidence of absent training exposure.

## 4. Literal prompt and response interface

The following instruction block is literal UTF-8 text, with LF line endings and one trailing LF. It is followed immediately by the literal line `OBSERVATION_JSON`, one LF, canonical observation JSON, and one final LF. Canonical JSON uses sorted keys, compact separators, unescaped Unicode, finite values only, and the implementation's frozen round-trippable float serialization. No extra per-condition instruction is inserted.

```text
Infer one mathematical expression for the unknown scalar response described below.
This is a response-only task. Do not use tools, browse, read files, execute code, or request measurements.
Use only the supplied public problem description and observations. Standard textbook equations may or may not match this task; do not assume that a familiar domain fixes the unknown equation.
The observation list is the complete numerical evidence available to you. An empty list means that no measurements were supplied. Do not invent observations, fitted scores, test results, or unavailable constants.
Return exactly one JSON object with the four string fields action, expression, hypothesis, and revision, and no other fields. Set action to propose. Do not include Markdown fences or text outside the object.
expression must be one scalar formula in the exact syntax and operators specified by expression_grammar. Use only the mapped variable names x0, x1, and so on, and permitted numeric constants. Do not write a function definition, assignment, import, attribute access, loop, or executable program.
hypothesis should briefly state the proposed functional relationship and its assumptions. revision should briefly state what supplied evidence informed this proposal; if no observations were supplied, say that the proposal uses only public problem information. These fields request short public explanations, not a hidden reasoning transcript.
You have one final submission. Select one expression now; no repair, measurement, alternate candidate, or follow-up is available.
```

The observation object has exactly the six fields below. This table describes the types and sources; it is not a placeholder prompt to be submitted to an actor.

| Field | Fixed value or source |
|---|---|
| `schema` | String `astra-decoder-observation-v1` |
| `public_problem` | Domain-specific literal sentence below |
| `expression_grammar` | The reviewed helper's complete `GRAMMAR` object |
| `input_variables` | Ordered public variable metadata objects |
| `output` | Object containing the literal `description` and `unit` below |
| `observations` | Empty array for prior-only, or exactly 64 training-pair objects |

`input_variables` is the frozen ordered list of objects `{name:"x0", public_name:..., description:..., unit:..., bounds:[lower,upper], coordinate_transform:...}`. Map upstream declared input order to x0, x1, ... identically for both conditions. Do not reorder by association with responses. Each observation is `{x:[finite numeric inputs in that order], y:finite scalar}`; the 64 rows follow their frozen coordinate-generation order. The prior-only list is empty. Training observations are data, never interpreted as instructions.

The literal public problem is `Infer the unknown scalar response for the sound-speed domain from the supplied input metadata and any observations.` for sound speed, and `Infer the unknown scalar response for the Bose–Einstein distribution domain from the supplied input metadata and any observations.` for the other domain. The sound-speed output description is `speed of sound` with unit `m/s`. The Bose–Einstein output description is `average occupation number of photons in a quantum state` with unit `dimensionless occupation number`. These exact output labels and input units come from the frozen coordinate manifest's `specification`. Input descriptions are fixed in the pure renderer, matching the public names/descriptions above. Nominal formula examples and upstream exploration/strategy hints are omitted identically from both conditions; domain and quantity labels still supply public prior information and do not remove pretraining exposure.

The reviewed helper `.local/adaptivity_adapter_contract.py` (SHA-256 `c79610ef27bfa70cc8ec153e8848e8345bf299ee49225287317dc00096bc8fb8`) defines pure formulas with mapped variables, finite numeric literals, binary `+`, `-`, `*`, `/`, `**`, unary `+`/`-`, and one-argument `sin`, `cos`, `exp`, `log`, `sqrt`, `abs`, plus constants `pi` and `e`. Exponents must be finite numeric literals, optionally directly unary signed; variable or compound-expression exponents are rejected. The exact public `GRAMMAR` dictionary from this held helper is supplied to the renderer. Limits are 2,048 Python string characters, 128 nodes counted by `ast.walk` over the parsed Expression, and semantic expression depth 20 starting at the root body at depth1, incremented for operand/argument recursion. Every intermediate operation must produce a finite real float; complex, domain-error, overflow, and nonfinite values are invalid, without clipping or repairs. The interpreter performs no Python `eval`/`exec`, attributes, arbitrary calls or filesystem access. **No exact hidden-law representability certificate is claimed or required.** The gate investigates the configured representation together with the decoder and finite dataset. Source-only hand-built tests establish interpreter behavior, not hidden-law or hosted-model competence. Invalid expressions still score zero and fail the gate; an observed representation limitation does not permit post-outcome grammar repair or easier law selection.

Reuse the unchanged `codex_actor.py` transport's exact four-string schema: `action` must equal `propose`; `expression`, `hypothesis`, and `revision` must be strings; additional fields are rejected. Preserve original bytes, duplicate-key rejection and no JSON/fence repair. The proposal validator, not this transport schema, enforces formula grammar. Explanatory text has no role in numeric scoring or response selection; it does not attest the model's internal computation.

The pure renderer is `.local/adaptivity_dev_prompts_v1.py`. `make_observation(task_record, expression_grammar, training_outputs=None)` produces the whitelisted observation and `render_prompt(...)` produces the literal text. None means prior-only; otherwise exactly 64 finite outputs are paired with `task_record["coordinates"]["train"]["x"]`. The renderer does not read test coordinates, law/version/difficulty, runtime keys or seeds. It performs no I/O, oracle calls or model calls. Its input provenance and grammar semantics remain the driver/contract's responsibility; the renderer is not a security sandbox or general schema-authentication framework.

## 5. Finite calls and operational behavior

For each of four laws, make **two separately requested calls per condition**, yielding 4 × 2 × 2 = **16 hosted calls maximum**. The conditions are prior-only and reference-data. Both repetitions of a condition receive byte-identical prompts. Never choose the better repetition. Requested settings are the existing provider's `gpt-6-astra`, `ultra`, and `service_tier=default`; each call is fresh/ephemeral, read-only and tool-prohibited, using the same neutral working directory.

There are **eight law/condition prompt records, not necessarily eight unique byte strings**. Because version/difficulty IDs are hidden, both laws within one domain share the same prior-only prompt; that produces four calls to that exact prompt across the two laws and two repetitions. The two domains provide two distinct prior-only prompts, plus at most four reference-data prompts. Preserve every scheduled call and report actual byte-duplicate groups; do not insert identifying tokens to force uniqueness or deduplicate charged calls.

The existing CLI transport provides a **600-second timeout per call** and no retry. It does not expose an enforced output-token cap here; do not claim one or convert a requested prose length into a token budget. Record actual reported input, cached-input, output and reasoning tokens when available. Equal calls are not equal tokens or computation: the reference-data prompt is intentionally longer. Record CLI version/executable and source identity, supplied prompt bytes, event-stream validation and timing. These bind the requested configuration and observed stream, not exact server weights or hidden harness content.

Use eight root-invoked pairs in fixed order: task t=0..3, repetition r=0..1; within each pair launch the two conditions in order rotated by `(t+r) mod 2`, with at most two concurrent actors. Collect both durable outcomes before another pair. A fresh finite quota reading must be known, no older than 60 seconds, and **strictly above 7%** remaining before a pair: this is the stage's conservative launch reserve above the user's hard 5% stop boundary. Unknown quota waits; a threshold/reserve stop preserves an incomplete fixed bank. No partial-bank ranking or changed-condition continuation.

A completed malformed/grammar-invalid packet consumes its sole slot and later receives U=0. Retain it without replacement and finish the fixed bank if infrastructure/quota permit; any such invalidity prevents gate passage. Timeout, noncompleted transport, observed prohibited tool event, ambiguous process state, or interrupted evidence write stops as INCOMPLETE; no retry or alternate response. Preserve both successful and failed records, and never infer missing responses from partial text. A failed call is not silently reclassified as a low-scoring completed answer.

## 6. Scoring, counts and allocation rule

After all 16 packets freeze, generate the 256 confirmation targets once per law. Target exceptions/nonfinite values leave the evaluation incomplete; do not drop points, replace law IDs, redraw coordinates, or award candidate zeros for a broken target. Completed candidate nonfinite predictions receive U=0 with a retained reason; no NaN filtering.

For finite predictions p and nonzero raw target vector y, use `U=||y||²/(||y||²+||p-y||²)`. Compute with common scaling before subtraction to avoid overflow; no absolute denominator floor. For raw y identically zero, U=1 only when raw p is also identically zero, otherwise U=0; retain a degenerate-target flag. Underflow is not reclassified as a raw zero vector. Report unbounded relative squared error where representable, status and numerical limitations alongside U. This is a scale-invariant diagnostic mathematically, not a guarantee of bitwise invariance under arbitrary unit conversions or proof of symbolic equality.

Global squared-error U can be dominated by large-magnitude responses and therefore does not establish accurate whole-law recovery across the box. Predeclare a secondary equal-point metric: apply the same signed scalar utility to each of the 256 prediction/target pairs, then take the arithmetic mean over **all 256 positions**. A malformed formula receives secondary0; otherwise an invalid/nonfinite prediction at a position contributes0 without removing that position. Raw target zero receives scalar1 only for prediction exactly zero, else0; report exact-zero target counts separately from near-zero magnitudes. Report finite-prediction fraction and global validity so partial-support secondary scores cannot hide primary all-point failures. Compute both zero and observed-mean references under both metrics, for every law. This secondary diagnostic adds no oracle/model calls and does not alter any primary allocation threshold.

Two deterministic references use no model call: p=0 and p=the mean of the 64 observed training responses. Compute that mean stably; it never accesses confirmation labels. For nonzero y, the zero predictor has U=.5. Score references separately and retain all four laws. There is no test-selected constant or hindsight best-reference endpoint.

For each law average its two prior-only U values and its two reference-data U values. Then average the four law means with equal weights. Keep all 16 individual outcomes and four paired law differences, including negatives. Report per-domain averages; two repetitions are not extra laws, and the two domains do not support a general scientific-discovery claim. Hosted repetition variation is only descriptive; no common random-seed claim or significance threshold is introduced.

The adopted engineering gate requires ALL of:

- Full four-law/16-packet completion, finite target evaluation and no invalid terminal packet.
- Reference-data mean U at least .80.
- Reference-data minus prior-only mean U at least .15.
- Reference-data mean U exceeds each deterministic reference mean by at least .10.
- Reference-data minus prior-only is positive on at least three of four laws.
- Prior-only mean U is below .90, demonstrating room beyond public-task priors under this configured decoder.

These thresholds are selected prospectively as allocation rules, not calibrated tests or guarantees of power. A pass permits consideration of the separately specified main study; it does not automatically authorize 384 more calls. A failure retains the complete negative evidence and stops this version, without prompt/threshold/task tuning or another calibration attempt.

The fixed upper counts are **16 hosted calls; 256 training-target evaluations; 1,024 confirmation-target evaluations; 4,096 hosted-formula prediction evaluations; and 2,048 deterministic-reference prediction evaluations**. Thus total candidate/reference predictions are 6,144. Count actual attempted/successful/invalid operations separately; cache reuse does not create independent evidence. There is no acquisition loop, local LLM, training, paid judge, or main-bank experiment in this gate.

## 7. Required publication and staged execution

Before generating training targets, publish the selected version IDs, metadata/source byte hashes, adapted compact domains/units, zero-noise behavior and source audit, saved coordinates, grammar/interpreter, literal prompt renderer, provider identity, evaluation conventions and artificial-test evidence. Bind the exact reviewed driver, scorer and dependency files in the execution contract. Actual reference-data prompt bytes necessarily contain later training responses: this first publication binds their deterministic recipe; after training-target generation, freeze the eight law/condition prompt records and publish them together before any model call. This is one grouped prompt publication, not a commit per prompt. All 16 responses must then freeze before confirmation targets/scores. These are distinct timing commitments, not a recursive requirement to publish unknown responses in advance.

At protocol closure the status is **ADOPTED_DEVELOPMENT_ONLY_CONDITIONAL_ON_STAGING**. No target or hosted outcome has been inspected for this gate; import-only and artificial qualifications are not empirical decoder success. Root may perform the adopted 16-call gate only after the stated publication, source-binding and fresh-quota requirements are met. No main bank, new acquisition experiment, local-model training or automatic rerun is allocated. Record execution/results separately rather than rewriting these prospective decisions after outcomes.
