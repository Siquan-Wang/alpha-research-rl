# Saved synthetic trajectory replay: review

Reviewed 2026-10-01 from `base-v1.json`, `sft-v1.json`, `rloo-v1.json`, the
synthetic generator, environment, split, evaluator, original evaluation writer
and current actor serializer. This is an
[internal AI-assisted review](README.md). It runs no model, trains no policy,
creates no new sampled trajectory and reopens no stopped experiment.

## Independent saved-action reconstruction

An independent CPU loop replayed all **18 episodes and 144 saved actions**.
For every action it checked strict text-to-action parsing against the recorded
EOS flag, status/reason, zero intermediate reward and termination exactly at the
last saved action. Reconstructed costs sum to the recorded total spending;
selected IDs and terminal rewards match every episode. The maximum absolute
terminal-reward discrepancy was **zero**.

The reconstruction uses the current `make_training_env` configuration: 300
synthetic calendar days, 16 assets, horizon five, budget ten, generation enabled,
and initial expressions `returns`, `ts_mean(returns,5)` and
`ts_std(returns,20)`. Its half-open fit/feedback/assessment intervals are
`[0,115)`, `[120,205)` and `[210,295)`. Feedback labels finish by row 209,
before assessment starts at row 210. The current environment gives the actor
acquired feedback evidence and fixes orientation from that feedback. Assessment
contributes terminal reward only; it is not a field of the actor observation.

## What is recorded and what is reconstructed

The old reports directly retain completion text, parsed action, an EOS boolean,
status/reason, task seed/regime and final reward/spending/selected IDs. They do
**not** retain original observations, prompt/completion token IDs, step costs,
or per-action feedback scores. EOS and the 64-token limit cannot independently
be authenticated without original token IDs. The replay checks consistency
with the saved EOS flag, not the model's historical token stream.

Before/after observations, individual costs and numeric feedback are therefore
**source-matched reconstructions**, even when all retained fields match exactly.
The old manifest has no Git revision and records package source hash
`701992ddc61c59d691f93a746f47c6b779b55aab893b243c16a24fd55bc8f736`, which
differs from the current whole package. The replay author recovered that exact
digest from commit `99eda9525831e9ec01e857ca2f5546f5e7b97760`: hash sorted
package-relative Python filenames followed by each exact Git blob's bytes.
This review did not repeat the Git recovery; it independently checked current
files against the reported historical pins. Seven replay dependencies match
historical bytes; the relevant training factory/constants and actor
parser/serializer/system-prompt definitions match historical AST hashes despite
unrelated whole-module drift. This strengthens reconstruction of defaults
omitted from per-run manifests. It does not recover unlogged runtime prompts.
Later fixes, richer logs and FP32 sampling checks must not be retroactively
attributed to the original BF16 run.

The full environment state is also distinct from actor input. The current
`compact_observation` omits `done` and full `history`, retaining only the last
three entries as `recent_actions`. Its output can be shown as a current
serializer reconstruction, not an original prompt: the system-prompt source
definition is pinned, but the assembled prompt, chat template and tokenization
used for each action are not authenticated here. Task seed/regime,
split metadata and terminal assessment reward belong in the reviewer view,
outside the reconstructed actor payload. A matching replay does not certify
the complete historical information boundary.

## Packaged replay safeguards

Initially reviewed `trajectory_replay.py` SHA256
`efa6aecde5109ff361b5098109a758684bdaba4ef7f39f3e0d4a49a3e89371fc`.
It pins the three original report byte hashes and canonical parsed bodies,
requires exact task/configuration identities, verifies
historical dependency/AST pins, and fails on changed outcomes, missing or
trailing actions, source drift or nonfinite data. Historical Git recovery is
explicitly a one-time author assessment, not a runtime operation.

Review identified that a successful CLI invocation could overwrite an original
report if given that same output path. The author added resolved-path collision
rejection for all three inputs and regression tests. Report identity pins also
reject self-consistent altered text or summary content borrowing old metadata.
The initial 26 tests passed independently on Windows/Python 3.12, including a
fresh process that forbids Torch/Transformers imports and still replays all
144 actions. Ruff passed. Subsequent public CI exposed a portability issue,
documented below. New model inference is outside this source review.

## Public CI portability failure and correction

The public Linux/Python 3.11.16 run failed: **5 failed, 374 passed, 5 skipped,
7 errors**. Its saved log identifies the training-factory AST fingerprint,
before any replay outcome comparison. Python 3.12 adds an empty `type_params`
field to function definitions. This reviewer independently removed only that
empty field from the local factory AST: the old hash `ecd882...b12b` became
`aae903...3b4d`, exactly the hash reported by the failing Python 3.11 job.
The initial local tests therefore did not establish cross-version portability.

Reviewed corrected source SHA256
`5329993cfcadccd9564668daf808a633c8c5cd59601d2d95b61c0a196b7c07f6`.
The new fingerprint serializes AST node types, ordered fields and typed literal
representations. It normalizes only an absent versus exactly empty
`type_params` list on function, async-function and class definitions. Nonempty
type parameters, other empty fields, decorators, annotations, defaults and
function bodies remain significant. The author recomputed all five definition
pins from the original commit blobs; raw source-file and original report
identities were not relaxed.

The Linux environment also installed NumPy 2.4.6 / SciPy 1.17.1, whereas the
original run used 2.5.3 / 1.18.1. The revised contract records original/current
versions and aggregate/per-package match flags. Version differences are allowed
only if **every retained outcome still matches exactly**; no rounding or
numerical tolerance was introduced. The output explicitly states that equal
retained outcomes cannot authenticate unlogged historical feedback values
across numeric libraries. This is reconstruction portability, not a claim that
model generation or every intermediate historical value is reproducible.

Independent local validation on Windows/Python 3.12 passed **31 replay tests
plus 9 explorer tests**, and Ruff passed. Tests simulate missing/empty Python
3.11/3.12 AST fields, reject nonempty parameters and ordinary code edits,
disclose artificial dependency-version drift, and reject a `1e-12` perturbation
to an actual replay calculation. The updated workflow includes Linux Python
3.11 and 3.12 jobs. At this review update, those new remote CI results are
**pending**; local simulation is not reported as a completed Linux rerun.

## Behavioral claim supported by the traces

Base repeats a fenced JSON completion rejected by the strict parser, spending
ten units for reward -0.01 in each task. Every SFT and RLOO episode executes the
same seven-action sequence: propose `delta(log(volume),1)`, screen IDs 3/0/1/2,
select initial ID 0 (`returns`), and stop after seven units. Neither policy
requests mutation or stability, submits the generated factor, or changes its
selection across the six tasks. SFT and RLOO have identical actions and rewards.

The environment automatically assigns selected-factor orientations
`+1,-1,-1,+1,-1,+1` across the six tasks. That rule can alter the submitted
signal and reward without an adaptive actor decision. The replay illustrates
an actual saved multi-step LLM action sequence and its feedback interface; it
does not demonstrate learned adaptive research or incremental RL benefit.
The separate real-data financial policy remains a one-action contextual
bandit, and the failed sequential feasibility branch remains stopped.
