# Reading and reconstructing the decoder development gate

This guide accompanies the adopted four-law, 16-call **joint decoder-and-representation feasibility gate**. It is not the larger adaptive-acquisition study, a weight-training run, or an official NewtonBench leaderboard result. At guide preparation, the source/import/artificial checks and input coordinates exist; no target or hosted outcome has been examined for this gate. Execution status and results belong in separate dated records.

The [full prospective protocol](../artifacts/scientific-decoder-dev-v1/snapshot/adaptivity-decoder-dev-plan-v1.md), [preflight byte manifest](../artifacts/scientific-decoder-dev-v1/preflight-manifest.json), and [preflight validation record](../artifacts/scientific-decoder-dev-v1/snapshot/adaptivity-preflight-validation-v1.json) identify the adopted specification and checked preparation. The [reviewed source snapshot](../artifacts/scientific-decoder-dev-v1/snapshot/) contains their supporting files. These links are relative to this guide's public location, `docs/scientific-decoder-dev-plan-v1.md`; the working `.local` copy is not their navigation context.

## Use the reviewed snapshot, not relocated scripts

Use the publication's exact repository commit and byte manifest for the reviewed plan, driver, scorer, prompt renderer, expression helper, numerical worker, provider source, metadata, coordinates, source audit and artificial tests. The snapshot also retains the runtime review, two import-only qualification records, coordinate-freezing script and pinned source-cache manifest. Verify those identities before reconstructing an environment. A current checkout may contain later code; matching a filename is not sufficient.

The scripts were reviewed in their original repository-relative layout. Their `__file__` paths locate sibling modules, the source cache and the repository's `src` directory. **Do not run copies directly from the snapshot directory.** Start from the exact publication commit, which supplies the bound `src/alpha_research_rl/codex_actor.py`, and reconstruct the snapshot files at their original `.local` paths in a separate working copy. Snapshot basenames and subdirectories mirror those `.local` paths, including:

```text
repository/
  src/alpha_research_rl/codex_actor.py
  .local/
    run_adaptivity_decoder_dev_v1.py
    score_adaptivity_decoder_dev_v1.py
    adaptivity_adapter_contract.py
    adaptivity_dev_prompts_v1.py
    newton_scalar_worker_v1.py
    adaptivity-decoder-dev-plan-v1.md
    adaptivity-metadata-order-v1.json
    newton-adapter-metadata-v1.json
    newton-source-determinism-audit-v1.json
    adaptivity-dev-coordinates-v1.json
    newtonbench-source-912a4ba/
      manifest.json
      [only the pinned source files named in that manifest]
```

Preserve exact file bytes, including line endings, the snapshot's artificial-test files and source records, and all 13 pinned vendor files plus their manifest. The worker rejects changed or unlisted vendor files, bytecode caches and unexpected import origins. Its source cache refers to NewtonBench commit `912a4ba5f4356ddd06acc16e44460ca30be4abc2`; retain the included MIT license and upstream attribution. No task substitution, regeneration of the frozen coordinate bank, source-path patching or import of a current alternate benchmark package is part of reconstructing this version.

The reviewed local numerical runtime uses NumPy 2.5.3 and SciPy 1.18.1; retain the published Python/runtime record as well. These version records are not a hermetic dependency or binary identity claim. The driver currently names the repository's Windows `.venv/Scripts/python.exe`. Porting that launch path to another platform is a separate compatibility change, not a byte-identical original execution. The helper has no model requirement; PySR is not used in this development gate.

## Distinguish inspection, tests and scientific execution

Reading saved JSON, source hashes and transcripts does not call a model or oracle. The specifically identified artificial tests use hand-built data and stub actors/workers; their passing establishes only those tested boundaries. They do not establish representability of the four hidden laws or successful hosted inference.

The actual stage commands have different effects:

- `freeze` creates a fresh execution binding and records the local executable identity. It is preparation, not a scientific result.
- `training` evaluates 256 fixed training targets. It is an oracle operation.
- `prompts` renders and freezes eight law/condition records, some byte-identical, from saved training values.
- `pair` invokes two hosted Astra responses and consumes the user's existing subscription allowance. Eight fixed pairs exhaust the 16-call cap.
- `freeze-responses` verifies and records all 16 successful transport packets before confirmation.
- The separate scoring script evaluates the fixed confirmation targets and saved formulas. **It is not a saved-only replay command.** Do not launch it merely to inspect a published result.

The plan requires source/contract publication before training targets, grouped prompt publication before hosted calls, and complete response freezing before confirmation. A recreated local environment cannot reproduce historical publication timestamps or server state. Fresh execution would create new evidence; it must not overwrite or be reported as the original run. Existing output/start markers intentionally prevent retrying ambiguous or completed calls.

The original executable path, neutral temporary working directory, authentication and quota are host-specific. Public records need not expose private absolute paths or credentials. A new machine's bindings must be separate records; do not edit published hashes to make local paths appear identical. The provider requests Astra/ultra/default and records observable events/usage. That is neither model-weight attestation nor equal token compute across the two conditions.

At closure, no saved-only numerical replay entrypoint is promised. Inspect the published records directly until an explicit replay path is provided. A successful future gate would support only this bounded joint feasibility result; a failure cannot distinguish grammar, finite-data and model limitations, and does not justify repairing this version after outcomes. Neither outcome allocates the main acquisition bank.
