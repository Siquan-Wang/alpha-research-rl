# Newton scalar adapter contract — source-only readiness

2026-10-01. Internal implementation review, pinned upstream commit
`912a4ba5f4356ddd06acc16e44460ca30be4abc2`. No benchmark module was imported,
no law was evaluated, no hosted/local model ran, and no package was installed by
this lane. Runtime source was fetched under MIT; law files were parsed only for
import names and difficulty/version registry keys. Their bodies were not shown
to the model. Public prompt examples were viewed and contain ordinary physical
formula hints; this is public prior exposure, not a claim of blind discovery.

## Decision and exact scope

The first prospective gate can use **vanilla_equation scalar observations**.
The trusted import route is small enough to implement and independently review;
its execution/dependency behavior remains unverified until root's isolated smoke.
This adapter is a different numerical evaluation from the upstream symbolic
LLM judge and its auxiliary magnitude-only RMSLE. It does not invoke either.

The original trajectory proposal is excluded. For example, gravity simple-system
runtime allocates `int(duration/time_step)` steps but returns the first 20; its
formatting/observation/budget semantics would need a separate protocol. None of
that is evidence against the present scalar setting.

Root fixed domain SHA ordering before outputs: dev `m8_sound_speed`,
`m10_be_distribution`; main `m1_coulomb_force`, `m7_malus_law`,
`m6_underdamped_harmonic`, `m5_radioactive_decay`, `m3_fourier_law`,
`m2_magnetic_force`. Reserve domains are not replacements for failed readiness.
All 12 registries contain `v0,v1,v2` under each of easy/medium/hard. The study
uses prospective medium/hard version selection; this source review did not pick
versions based on their formulas or behavior.

## Metadata and source custody

`.local/newton-adapter-metadata-v1.json` has exact public parameter/signature
strings, version keys and pinned file hashes for all 12 domains. Its final SHA256
is `df3b5f05bbb3c9e4d259577aa180a4a2178fcda768ede1b2315ac1511d309028`.

| Domain | Actor input order | Official experiment keywords | Public constraints/defaults | Observable |
|---|---|---|---|---|
| sound speed | `gamma,T,M` | `adiabatic_index,temperature,molar_mass` | all positive; T Kelvin, M kg/mol; defaults 1.4,293.15,.02897 | speed of sound v; m/s physical interpretation |
| Bose–Einstein | `omega,T` | `omega,temperature` | both positive; vanilla public prompt recommends frequency scale at least 1e8 and temperature scale at least 1e1; defaults 1e8,1000 | mean photon occupation n; dimensionless physical interpretation |

Source references are immutable: sound
[public interface](https://github.com/HKUST-KnowComp/NewtonBench/blob/912a4ba5f4356ddd06acc16e44460ca30be4abc2/modules/m8_sound_speed/prompts.py#L10-L62),
[scalar branch](https://github.com/HKUST-KnowComp/NewtonBench/blob/912a4ba5f4356ddd06acc16e44460ca30be4abc2/modules/m8_sound_speed/core.py#L70-L86);
occupation [public interface](https://github.com/HKUST-KnowComp/NewtonBench/blob/912a4ba5f4356ddd06acc16e44460ca30be4abc2/modules/m10_be_distribution/prompts.py#L10-L78),
[scalar branch](https://github.com/HKUST-KnowComp/NewtonBench/blob/912a4ba5f4356ddd06acc16e44460ca30be4abc2/modules/m10_be_distribution/core.py#L60-L75).
Neither dev interface exposes E or chemical potential. Do not invent these as
independent inputs. No common finite upper/lower box registry was found. Study
boxes and coordinate transforms are **adapted evaluation choices**, now separately
frozen by root before outcomes, not official Newton bounds. Public semantic
labels/units do not prove each alternative law's physical dimensional consistency.

Exact dev source cache: `.local/newtonbench-source-912a4ba/`, 13 files including
MIT LICENSE, both cores/laws/types/prompts, m8 physics, common types/physics_base,
and noise. Manifest SHA256
`87c7d18f6987461b403c3f87b95873cc4f8fa7b19caf32ca52964ee87d9f9010`.
Only trusted root/custodian code may read law source. Actor input must contain
rendered public metadata/allowed observations, not cache paths, source, version
IDs or benchmark filenames. The current filesystem arrangement is ordinary
process/API separation, not a hostile-process security sandbox.

The dev numerical transitive imports are stdlib + NumPy, and SciPy for m10's
imported integration helper even though vanilla does not integrate. Pandas is
only a later m11 core issue outside this dev worker. `utils/noise.py` SHA256
`f239b80240ea33bd61ab08c5bf64d9d8edf11250708cba023d2d94cc1f0f6c67` returns
the raw value immediately at noise zero, before RNG use or precision flooring.
Explicit version selection avoids randomized version selection.

## Trusted worker, not an actor tool

`.local/newton_scalar_worker_v1.py` owns a fixed dev-only interface:

```json
{"domain":"m8_sound_speed","difficulty":"medium","law_version":"v1","rows":[[1.4,300.0,0.03]],"noise0":0}
```

This is a **schema illustration**, not an adopted smoke task/version/query.
Root supplies the frozen version and coordinates. Exact five keys; medium/hard;
v0/v1/v2; 1–1024 rows; every input finite and positive with exact dimension.
All rows validate before source verification/import. Study-specific compact
bounds, row denominators and train/confirmation timing remain caller duties.

The worker hashes the fixed cache before and after use, creates only trusted
namespace packages, and replaces `modules.common.evaluation` with a function
that always raises. Thus importing a core does not transitively import the
upstream LLM evaluation/API module. It blocks model/API client imports and
network/process audit events; it never calls the symbolic evaluator, generated
Python, PySR, or a downloader. It passes every required scalar keyword explicitly.
Cache verification also rejects bytecode/cache directories and all unlisted
files: `dont_write_bytecode` alone would not prevent reading stale bytecode.
Every loaded vendor `modules`/`utils` source origin is checked against the exact
manifest before the first oracle call and again afterward. These checks close
ordinary source-identity mistakes, not malicious concurrent filesystem races.

Output keeps one indexed row record per requested row. A nonfinite/non-scalar
result or exception marks that row failed and leaves later rows unattempted;
there is no automatic retry. Exceptions are reduced to stable codes and no
traceback/law source is exported. Library stdout/stderr are suppressed, with
only a presence boolean retained. Stage and failure class distinguish request,
source verification, import, oracle execution and post-run integrity failures.
Pre-run failures record zero attempts; unexpected interruption during the outer
run boundary records unknown attempts, not a fabricated zero. Root must require
exit 0 **and** COMPLETE; output persistence failure can leave partial bytes.
All output paths are exclusive. No claim is made that rerunning a failed request
is scientifically authorized merely because this low-level CLI accepts a new
path; the prospective study ledger owns retry prohibition.

Later root-only command, **not run by this lane**:

```powershell
.\.venv\Scripts\python.exe -I -B .local/newton_scalar_worker_v1.py --request <FROZEN_REQUEST.json> --output <NEW_OUTPUT.json>
```

The existing numerical environment supplies NumPy/SciPy. Missing dependencies
must produce a pre-run failure rather than automatic installation/fallback.
No real task measurement may happen until source/protocol review authorizes it.

## Artificial safe-expression, metric and budget contracts

`.local/adaptivity_adapter_contract.py` is stdlib only. `SafeExpression(source,
variables).evaluate(point)` interprets a bounded AST: +,-,*,/,**, unary +/-;
single-argument sin/cos/exp/log/sqrt/abs; pi/e; finite numeric literals. Power
requires a numeric literal optionally unary signed; a PySR complexity constraint
alone does not enforce this. Limits are 2048 characters, 128 complete AST nodes,
and depth 20. No eval/exec, attributes, subscripts, assignments, unknown names,
arbitrary calls, keywords, clipping or repair. Numerical-domain/overflow/nonfinite
output is invalid. These tests prove semantics only, not that every hidden law
is representable by this grammar or learnable from the declared observations.

`signed_utility(prediction, truth)` uses common-scaled
`U=||y||²/(||y||²+||p-y||²)`. No absolute unit floor. Raw all-zero truth is an
explicit degenerate case: U=1 iff raw predictions all zero, else U=0. An invalid
prediction returns U=0 without dropping coordinates. Dimension/truth corruption
raises rather than becoming a candidate failure. Relative squared error is
reported only when representable; nonzero components lost at scaling/squaring,
relative underflow, and overflow have explicit flags. U can round to one when
positive error is unrepresentably small; this is not exact equivalence.

`ScalarBroker(bounds,budget,oracle).submit(raw_json)` accepts only `{"x":[...]}`.
Every attempted submission consumes budget, including malformed/duplicate keys,
nonfinite/bool/out-of-bounds points. Duplicate coordinates consume another oracle
call and are flagged. Returned records/trace are defensive copies. An oracle
exception permanently fails the broker; frozen/failed/exhausted brokers reject
new calls. `freeze()` can intentionally freeze a partial budget, so the outer
driver must check required completeness. The driver also owns raw-response-size
caps. Callback owners/seeds/confirmation closures must never be supplied to the
search policy; Python introspection resistance is not claimed.

## Observed validation and remaining gate

One artificial fixture invocation completed: **35 tests passed in 0.09 seconds**.
It covered syntax/exponent rejection, signed utility at common scales 1e-200,
1e-20,1,1e20,1e200, zero-predictor .5/sign-flip .2, exact-zero/nonfinite inputs,
residual/target underflow reporting, charged invalid/duplicate attempts, frozen
and interrupted lifecycle, and worker keyword/error-tail behavior with injected
callbacks only. No pinned Newton import or actual output was generated.

Root requested the final worker main-stage failure ledger after that test run;
the critic then identified stale-bytecode/origin checks and safe error-code
classification. Those worker repairs are present, with four additional focused
artificial cases added (39 cases expected). This lane did not repeat the test
run; root owns the final affected-suite execution. Held helper SHA256 is
`c79610ef27bfa70cc8ec153e8848e8345bf299ee49225287317dc00096bc8fb8`;
worker `4f9a23e93a11e71a5064ab3902cff926b9417e33de384768854a60a57fee3152`;
tests `327d693f27ba4cbaa0b1fa730afba09ff42e164bf29dadf3c4acc05c32254cf2`.
Independent critic review and root's later isolated smoke remain required before
operational readiness. This is interface groundwork, not a completed benchmark
pilot, scientific finding, or claim that adaptive acquisition beats cheap baselines.
