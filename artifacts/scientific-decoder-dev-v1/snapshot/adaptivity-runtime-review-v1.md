# Adaptivity runtime qualification: source review

2026-10-01. Internal Astra Ultra review of root's artificial PySR smoke and the installed SymbolicRegression source. I did not start a fit, install a package, open benchmark gold, call a model/oracle, or alter the runtime. The numerical fit was run by root; my actual-result participation is read-only inspection. This is not an independent reproduction or scientific benchmark result.

## Smoke evidence and precise counter meaning

The retained result reports PySR 2.6.0, Julia 1.13.1, 64 artificial polynomial rows, a 10,000 requested backend count and a maximum reported count of 10,081. The raw logger has 101 count records and ends with 9,925, 9,971 and 10,081, matching the result. A polynomial candidate has recorded training loss approximately 6.51e-32. These observations establish that this configured fit and logger worked once; they do not establish strength on NewtonBench or full cost accounting.

The result records **start** `2026-10-01T16:18:21.937859+00:00` and 21.266 elapsed seconds. It does not contain an independently recorded completion timestamp; approximately 16:18:43.2 UTC is inferred from those fields.

Source identities inspected:

| Relative file | SHA256 |
| --- | --- |
| `.local/pysr_runtime_smoke_v1.py` | `2c53f8a8632c0ce582467b0d96963b9fba62b29cda94bc2458b8b02386ce7050` |
| `.local/pysr-runtime-smoke-v1/result.json` | `932e1e19c004b11a06887636bc865b314a063894c171a244ece135efc7342a26` |
| `.local/pysr-runtime-smoke-v1/backend-counter.log` | `d02b7c304b13485c965a3e814f90874b070ab28aeb14cc229cb823049d8946dd` |
| `Logging.jl` | `61c86a03b5ae7c5dca28ca001e9f5e35308c53865cfc428a2f8ce317c8ffefb7` |
| `SymbolicRegression.jl` | `bc80d97bd5a4ec5f93a5627dd9f91a9d992f7fca2c77ce3795a8b1fca1bcfeea` |
| `ConstantOptimization.jl` | `6f80e48282e2f2d1c6b5834b35c7e1b06d1d1420c1a3acf6ada0dbc68c2ade0c` |
| `SearchUtils.jl` | `06d1ba163ed540c307dfe075ba8dbe6a7e84b71122cf1f68fee59f9f7f9a1f25` |

The Julia filenames refer to `.local/julia-depot/packages/SymbolicRegression/PPgnc/src/`.

**The count is a backend-reported, assimilated-search-state proxy, not the number of all computations actually performed.** Four specific source findings matter:

1. **Logger coverage:** `Logging.jl:113` emits `sum(sum, state.num_evals)`. With `log_interval=1`, the callback at `SymbolicRegression.jl:1268` reports every normally completed main-loop assimilation, including the final one before the early-stop check. Thus 10,081 is an observed final accumulated state count for this successful smoke. It is not a separately instrumented total. An exception before the callback need not have a terminal report.
2. **Initialization is not fully retained:** `_initialize_search!` constructs populations and returns their `population_size` count, but `_warmup_search!` extracts `(in_pop, _, _, _, ...)`, discarding that count before replacing the worker output with a search-cycle result. Dummy/prototype construction also evaluates population members outside the ordinary accumulated cycle count. A count of zero would not imply zero numerical work.
3. **Constant optimization has omissions:** `ConstantOptimization.jl:210–237` evaluates `baseline=f(x0)` before assigning `num_evals=result.f_calls*eval_fraction`. It adds optimizer restart function-call counts and a final improved-member evaluation, but not that external baseline. The source itself leaves Hessian-call coverage as a TODO. This confirms partial accounting and does not justify a claim that every derivative/function evaluation is included. `dataset_fraction` makes batch evaluations fractional; without batching the marked unit is a full-dataset evaluation, not one data row or a FLOP.
4. **Already executed work may be unassimilated at stop:** the main loop stores the current cycle count at line 1149, then dispatches the next cycle before logging and checking `max_evals`/timeout. `SearchUtils.jl:321–339` executes that dispatch immediately in serial mode. A ready next-cycle result can therefore exist in `worker_output` when stopping occurs, without its count reaching `state.num_evals`. Multiple populations can have such pending results. This is more than the visible 81-count overshoot; the saved log does not recover the omitted work.

Timeout is likewise soft and narrower than the full call. The timeout clock starts at `SymbolicRegression.jl:1069`, after initialization and warmup; checks occur at the main-loop stopping boundary. A synchronous cycle/constant optimization may continue past it. Python's 21.266-second measurement covers model construction/fit/closing the logger after the script's imports and logger setup, not process startup or every import/precompile cost.

**Recommended contract:** retain the smoke unchanged, name this field `reported_backend_num_evals` or equivalent, record its stopping threshold and observed overshoot, and record full process/fit elapsed time separately. A parent process deadline is required for a hard wall-time boundary. Common backend-count allowances can be a practical search-budget proxy; they must not be described as equal actual objective work, FLOPs or exact total cost. Do not patch the installed package or retroactively “correct” 10,081 with an unverified adjustment.

For a production evidence collector, require a nonempty finite nondecreasing count sequence and distinguish the last report from its maximum. The current one-off smoke allows an empty sequence and would still write a result with a null maximum; that is a qualification limitation, not a defect in the retained successful evidence. A broken logger must fail an accounting qualification rather than silently pass it.

## Exponent boundary

`constraints={"^":(-1,1)}` restricts exponent-tree complexity, not its type. A variable leaf also has complexity one. The completed smoke has no power operator and therefore does not qualify power semantics. If the adapter allows only literal powers, it must inspect the exponent AST and accept only a finite numeric literal or a permitted unary-signed numeric literal; booleans and variables remain invalid. Filtering exported candidates is distinct from preventing those structures inside the search grammar and should be labelled accordingly. The implementation author acknowledged this requirement.

## Safe-expression and broker contract

Reviewed `.local/adaptivity_adapter_contract.py` at SHA256 `c79610ef27bfa70cc8ec153e8848e8345bf299ee49225287317dc00096bc8fb8`. This is source inspection, with no independent test execution in my lane.

The interpreter walks a validated mathematical AST rather than executing generated Python. It limits text length, AST nodes/depth, admitted operators and one-argument functions; rejects booleans, attributes, keyword calls and nonfinite constants; and allows only literal or unary-signed literal power exponents. Overflow, real-domain failures and complex power results become invalid predictions. This verifies the intended narrow grammar boundary, not its coverage of all benchmark laws or equality with every PySR operator's semantics.

I found a numerical-reporting gap in the first helper: target `[1,0]` and prediction `[1,1e-200]` lose a nonzero residual on squaring; target `[1e308,0]` and prediction `[1e308,1e-100]` lose it during scaling. Both could report exact relative error zero without a flag. The reviewed revision checks raw differences against scaled/squared residuals, flags lost components and sets an unrepresentable positive relative error to null. Utility may legitimately round to one; the diagnostic now distinguishes that from demonstrated exact equality. Aggregate target underflow and relative-error overflow also remain explicit.

The scalar broker charges malformed and duplicate submissions, enforces finite positive-width bounds and a strict point schema, returns defensive copies, and permanently fails after a callback exception. Duplicates currently consume another callback; this is explicit requery behavior, not a cache. Its freeze method can seal a partial budget and therefore does not certify a complete study. Raw-request length, multi-query packet accounting, full-bank completeness and the native-float conversion of trusted NumPy scalar outputs remain integration duties. The primitive explicitly makes no claim of resisting arbitrary caller introspection.

## Pinned scalar worker: additional source gate

Root then requested review of `.local/newton_scalar_worker_v1.py`. The initial inspected worker binds a manifest/commit, validates request types, passes `noise_level=0.0` and `system="vanilla_equation"`, supplies a disabled symbolic-evaluator stub, blocks selected API imports/network/subprocess operations, uses fresh output creation, and records staged failures without exporting source/exception text. It intentionally does not enforce study-specific compact bounds or data-reveal timing; those remain driver responsibilities. I did not import vendor modules or query the worker.

Two concrete fixes were sent to root and the author before import qualification:

- Hashing `.py` files followed by normal `importlib` does not prove those are the bytes executed: existing unbound bytecode can be read despite `dont_write_bytecode=True`. Every imported vendor module also needs an allowlisted source origin. A narrowly scoped source-only loader or bytecode rejection plus import-origin checks is required before claiming pinned imported-source provenance.
- The first `run()` maps every `WorkerError` to a nonfinite/nonscalar-output code. That would mislabel a deliberately blocked evaluator or operation occurring inside the scalar callback. Preserve fixed safe codes for those integrity failures; do not emit arbitrary exception strings.

Both findings are resolved in independently hash-checked worker SHA256 `4f9a23e93a11e71a5064ab3902cff926b9417e33de384768854a60a57fee3152`. The cache inventory rejects bytecode/cache paths, unlisted files and redirected paths. Imported vendor modules must resolve to a manifest-listed `.py` file with matching bytes; both the selected core and laws modules must be present. This check runs before the first callback and again after the run, alongside a second cache check. Synthetic namespace packages and the disabled evaluator stub are explicitly distinguished from file-backed vendor modules. Fixed safe integrity-error codes are preserved; arbitrary exception text remains excluded. Root reports 39 artificial fixtures passing after these repairs; I did not rerun them.

The worker records zero attempted queries for pre-import failures, an explicit ambiguous count for unexpected outer interruption during the run, and actual attempted rows for ordinary row failures. Remaining rows stay `not_attempted`. Fresh exclusive output writing and stage/error records retain failure evidence. Source review finds no remaining blocker to root's fresh-process **import-only qualification with zero target calls**. That is not clearance for the hosted development gate, a hostile-host sandbox, or exact computation accounting. Installed third-party dependencies and ordinary trusted-host behavior remain outside the vendor-source hash claim.

## Staged driver and delayed scoring review

I reviewed the first draft and the repaired driver at SHA256 `77aafc70ac4bd800a9e964cb305bb5a2376f7427c1d5fc80467566b9a49a0c34`. The initial source lacked an exclusive durable pair claim before starting threads, could leave a sibling outcome unrecorded when another future raised, normalized prompt newlines on reading, and did not require the exact bound-file population or complete pair identities. These findings were sent directly to root; the inspected revision adds the exclusive claim, validates both prompt byte strings before claiming/launching, collects both futures, rechecks the pinned coordinate bytes and exact binding members, pins the explicit actor executable, and checks the two-condition/eight-pair schedule. This is source inspection, not an execution or evidence replay.

The claim expressly does not guarantee parent liveness or termination of already launched native processes. A lost parent may leave work running; the retained claim blocks a replacement pair. No parent-death cancellation or adversarial process-isolation claim is justified. Public-byte publication gates are root-operated external evidence rather than an automatic property of this local driver.

Additional metadata corrections were sent before freeze: require exact integer task/repetition fields and exact Boolean success (Python equality otherwise equates `True`, `1` and `1.0`); require successful status `succeeded` and consistent retained provider evidence; and compare the final frozen calls exactly to the validated pair population. Only `succeeded`, not `complete`, is the frozen provider's success status. These are narrow evidence-integrity checks, not additional scientific conditions. All are present in the final source identities below. The frozen-call comparison uses canonical JSON, retaining distinctions between Boolean, integer and floating-point representations.

The initial scoring source also collapsed the secondary pointwise mean to zero whenever any prediction failed. This contradicts the agreed equal-point diagnostic: malformed packet/grammar means all zeros, whereas a valid expression with isolated numerical failures retains finite-position utilities and assigns zero to failed positions, over all 256 targets. Primary all-point failure must remain zero, accompanied by the finite-prediction fraction. This concrete correction was sent to root before any confirmation targets or score calls and is repaired. The final scorer derives finite-prediction coverage from the scalar helper's validity status and normalizes numerical failure to `invalid_candidate`, so partial secondary support cannot pass the primary validity gate. Exact-zero target counts and floating-point limitations remain visible. Neither metric is symbolic equivalence or whole-law recovery.

## Final scoped disposition

Final files independently read and hashed:

| Relative file | SHA256 |
| --- | --- |
| `.local/adaptivity_adapter_contract.py` | `c79610ef27bfa70cc8ec153e8848e8345bf299ee49225287317dc00096bc8fb8` |
| `.local/newton_scalar_worker_v1.py` | `4f9a23e93a11e71a5064ab3902cff926b9417e33de384768854a60a57fee3152` |
| `.local/run_adaptivity_decoder_dev_v1.py` | `ac4c60030af29819966280a170bfcb22c3246573e4565ff29dffeb32fdc35b8d` |
| `.local/score_adaptivity_decoder_dev_v1.py` | `fb9c85c36d815978ae3dd32e2f3a0fbc4015cf5954ca46bd2299621aa8ef5669` |

**No remaining identified source blocker within this review's scope.** This is readiness for completing the prelaunch gate, not evidence that a scientific run has launched or passed. Root reports separate fresh-process import-only qualifications for both selected domains at approximately 16:37:11 UTC, with zero queries and no API use; these are root-supplied observations, not my execution or independent replay. Root reports 39 helper/worker artificial fixtures passing, and the separate renderer/driver reviewer reports 36 fixtures passing. Scorer regressions and the remaining bounded lifecycle checks are being completed by their owners; no unchanged tests were duplicated in this lane. In particular, sibling-future exception retention and mixed finite/failed pointwise scoring were source-reviewed here, not independently executed here.

The final driver uses a conservative launch reserve above 7% with quota evidence at most 60 seconds old. Source and reviewed protocol bytes must be frozen after pending wording is resolved; root's public-byte gates must precede their corresponding scientific stages. All 16 complete transport slots must freeze before any confirmation targets. Study-specific bounds, scheduled population, publication ordering and the shared-host access boundary are obligations of this composed protocol, not guarantees supplied by the scalar primitive alone. There is no extra scientific attempt, new seed, model call, gold-law inspection or numerical target evaluation in this review.
