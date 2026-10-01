# Replay two historical studies without changing the current checkout

**Both fixed recipes completed successfully on the recorded Windows/Python runtime after a short-scratch correction.** The first actual matched-prefix attempt failed on a Windows path-length limit and remains retained. The corrected launcher subsequently verified matched-prefix and sealed-confirmation evidence without repeating either experiment. Existing direct replay commands and CI routing are unchanged.

The launcher reconstructs a fixed historical source/evidence tree from local Git objects, then starts a fresh interpreter whose project imports must come from that tree. This avoids accidentally combining an old report with today's editable `alpha_research_rl` package. It verifies saved evidence; it does not repeat model collection, training, market assessment or synthetic panel generation.

## Requirements and commands

Use an existing Python 3.11+ interpreter, a local Git build supporting both `--no-replace-objects` and `--no-lazy-fetch`, and the complete local objects for the selected commit. Root verified those flags on Git 2.52. The tool does not fetch missing objects, clone a repository, install dependencies or fall back to another commit. Missing or incompatible prerequisites are errors.

From the repository root, choose exactly one recipe and a **new** output directory under `.local/pinned-replay-runs/`:

```powershell
python scripts/replay_pinned_study.py --recipe matched-prefix-v1 --output .local/pinned-replay-runs/revision-check-001
python scripts/replay_pinned_study.py --recipe sealed-confirmation-v1 --output .local/pinned-replay-runs/sealed-check-001
```

Each command starts one saved replay, with no automatic retry. Use the project's existing `.\.venv\Scripts\python.exe` in place of `python` when appropriate. The chosen launcher interpreter is also the child interpreter; environment installation is not part of either command. On other platforms, use the corresponding existing Python executable and the same arguments.

The recipe IDs, commits, entrypoints and expected results are fixed in source. There is no arbitrary command, revision, report path or alternative study-directory option. An existing output directory is refused, including after failure. A later deliberate saved replay needs a new directory; it still does not create another experimental replication.

## Windows path boundary and retained failure

The original actual attempt, `root-matched-20261001-v1`, started at `2026-10-01T14:20:49.809626+00:00` and was marked failed at `14:20:58.276863+00:00`. Exact historical extraction completed, but the child exited 1 with Windows error 206 while the frozen verifier created a nested temporary copy of public evidence. It produced no completion summary. The capsule and failure records remain intact. No original experiment, model call or market assessment was repeated.

The approved correction gives each invocation a fresh, exclusive repository-owned scratch directory at `.local/p/<16-hex-character-id>`, instead of placing scratch below the long capsule name. Its repository-relative reference must agree across STARTED, the child request/proof and COMPLETE or FAILED; an `OWNER.json` binds it to the capsule and recipe. The allocated directory and owner record remain after success or failure, although the historical verifier normally removes its own temporary subdirectories. It is not a caller-supplied arbitrary path, and existing scratch is never reused. On Windows, preflight checks UTF-16 path lengths for the extracted tree and historical temporary snapshots, with a fixed 32-character temporary-name allowance; excessively long repository roots fail clearly before child replay. This does not change OS settings, use extended-path aliases, modify frozen code or claim support for every Windows path layout.

After correction and review, root made a separately recorded matched-prefix saved replay in a new output directory, followed by the first sealed-confirmation launcher replay. Both completed. The prior failure was not deleted, relabeled as success or resumed. Its [exact failure record](../artifacts/pinned-saved-replay-v1/initial-failure/FAILED.json), [original launcher](../artifacts/pinned-saved-replay-v1/initial-failure/bootstrap.py) and [explanation](../artifacts/pinned-saved-replay-v1/initial-failure/evidence-summary.json) are retained. This was an engineering compatibility repair, not a new scientific experiment or an automatic retry.

| Recipe | Exact commit | Retained result SHA-256 | Additional requirement |
| --- | --- | --- | --- |
| `matched-prefix-v1` | `7e0f7b35618ace986de6ce0cfa1a6231e7716080` | `89162112ddad384ed8917a8b1198ce94044abc90ff15e1680bfe88b66eb43c37` | Required HTML SHA-256 `8bb1ff7013c8c7906f9223daca87287296103f8643e41216037d2bbf39d9b772` |
| `sealed-confirmation-v1` | `58dc66ed2a4af7add8ee79f54337e278d9bd7d13` | `ec6d9076d70f50d436c3d69a9ec126d23489f2ce4f98bbf4e25064e6d9c7306d` | No HTML verifier or HTML claim |

The matched-prefix result is `results/astra_matched_prefix_v1.json`; its page is `docs/astra-revision-explorer.html`. The sealed result is `results/sealed_confirmation_v1.json`. The launcher preserves Git blob bytes directly; it does not run checkout filters, apply newline conversion, copy the current working package or alter the current branch.

## Recorded actual replays

Both successful attempts used launcher SHA-256 `dce34a515e51e3544a6a6aac23d769ebb76eedec4c12b2dd2898835ec6ec4ed0` on Windows 11 / CPython 3.12.14. These timings describe this host, not a performance benchmark or cross-platform verification.

| Saved replay | UTC interval, 2026-10-01 | Elapsed | Extracted tree | Recorded project imports |
| --- | --- | --- | --- | --- |
| [Matched-prefix completion](../artifacts/pinned-saved-replay-v1/matched-prefix-v1/COMPLETE.json) | 14:34:02–14:34:15 | 13.047 s | 1,251 files; 56,802,037 bytes | 12 |
| [Sealed-confirmation completion](../artifacts/pinned-saved-replay-v1/sealed-confirmation-v1/COMPLETE.json) | 14:34:42–14:35:13 | 30.938 s | 2,560 files; 99,747,310 bytes | 3 |

The retained [integration record](../artifacts/pinned-saved-replay-v1/integration.json) accounts for **three actual attempts: one initial failure and two verified saved replays**. Matched-prefix imported existing NumPy 2.5.3 and SciPy 1.18.1; sealed confirmation imported neither. The associated [matched-prefix proof](../artifacts/pinned-saved-replay-v1/matched-prefix-v1/child-proof.json) and [sealed proof](../artifacts/pinned-saved-replay-v1/sealed-confirmation-v1/child-proof.json) record relative source/dependency origins and zero observed prohibited operations. The independent contract review checked these saved records without launching another replay. Root separately checked every extracted file against its local Git blob.

## What successful completion establishes

Success requires the launcher invocation to finish successfully, child exit zero, no `FAILED.json`, and the exact recipe's completion fields, hashes and full denominators. A missing file, incomplete summary, wrong scalar type, failed child or changed evidence is not a skipped success. `COMPLETE.json` records the recipe, commit, actual child summary, extracted-tree/bootstrap identities, imported source origins and runtime. Standard output and error are retained separately.

A late write/flush failure can leave complete-looking `COMPLETE.json` bytes before failure handling writes `FAILED.json`; **the failure marker takes precedence**. File presence alone is never sufficient. Failed or interrupted attempts retain available records and cannot resume in place. An ambiguous finalization is incomplete even if a JSON body looks well formed. These are process-level checks and best-effort durable records, not a guarantee against every hardware failure or hostile concurrent filesystem change.

For matched-prefix, the unchanged historical wrapper verifies all **200 slots**, **10 states**, four repetitions, the recorded 80 hosted and 120 cheap attempts, 98 historical new feedback calls, and **133 unique future keys** comprising 99 historical new evaluations and 34 reused keys. It also reconstructs the mandatory HTML's embedded report, prompts and template. Replay makes zero model calls or financial evaluations and reads no raw market data. Its historical counts are not operations performed by the launcher.

For sealed confirmation, the unchanged historical replay checks all **640 saved panels**, their transcripts, prediction seals and arithmetic, with zero new panel generations, model calls or market scores. It checks saved arrays rather than generating their SHAKE256 streams. Its replay-function write count is zero; that does not mean the outer launcher wrote no files.

The launcher creates an extracted tree, manifests and logs. The matched-prefix verifier also creates disposable public-evidence snapshots in launcher-owned scratch space. Neither recipe is a zero-disk-space operation. The extracted historical files must remain unchanged; temporary work and retained launch records are separate from those files.

## Dependencies and isolation limits

The child uses isolated startup, without processing user-site settings, inherited `PYTHONPATH`, `.pth` or `sitecustomize`. Historical project modules must resolve inside the extracted tree; a missing historical module must fail rather than import the current package. Existing third-party directories are added explicitly only for the recipe that needs them. Their imported package versions and relative origins are recorded. This isolates project source; it does not recreate an old operating system or native-library environment.

- **Matched-prefix:** its historical dummy grammar validation imports NumPy and SciPy. These must already be compatible with the chosen Python. No Torch, Transformers, PEFT, model weights, provider login or market ZIP is required. The original scoring-runtime binaries are deliberately not revalidated; current numerical-library identities are reported. This is not a standard-library-only replay.
- **Sealed confirmation:** its runner/core use the Python standard library. No third-party package directory is needed.
- **Both:** local Git reads and one child Python process are operational prerequisites. During replay, guarded network/provider/scoring operations are prohibited. Windows standard-library platform detection occurs before replay guards and may use a local OS-version subprocess. These checks concern trusted replay code, not a hostile-code sandbox or attestation of all native-library behavior.

The launcher does not re-fetch publication receipts or prove their wall-clock times. Exact historical hashes establish agreement with retained evidence. They do not attest hosted model identity, prove unobserved access was absent, rescore financial factors, restore a fresh holdout or increase statistical confidence through repeated replays.

The two-recipe restriction applies to the public entrypoint. The retained `bootstrap.py --_child` mode is an internal interface for a trusted launcher-created capsule, also used by artificial tests; it is not a public service for running untrusted user-supplied capsules. Do not infer an arbitrary-code security guarantee from the process guards or request hash.

See the [matched-prefix evidence guide](replay-astra-revision-evidence.md), [sealed-confirmation replay guide](reproduce-sealed-confirmation.md) and the new [launcher contract review](audits/pinned-replay-contract-review-v1.md) for the narrower original contracts and validation scope. A compatibility failure belongs in a new launcher diagnostic; it is not permission to edit frozen study evidence or relax its identities.
