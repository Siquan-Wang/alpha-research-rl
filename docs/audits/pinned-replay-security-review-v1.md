# Commit-pinned replay: implementation boundary review

2026-10-01. Internal AI review, independent of launcher implementation. The
reviewer participated in the design and earlier saved-evidence audits; this is
not external peer review or an adversarial security assessment.

**Current review result:** no remaining blocker in this lane after the Windows
compatibility follow-up below. The revised independent suite has 78 passes and
two Windows symlink-permission skips; Ruff passes. A separately executed,
author-written artificial nested-path integration test also passes. That one
fixture creates its own temporary artificial Git repository. This reviewer has
not run either registered historical recipe, installed anything, called a model,
scored market data or generated a synthetic seed panel.

## Source-first finding and resolution

The original `_process.drain` handled reader errors but performed log
flush/fsync/close in an unguarded `finally` block. A stderr persistence exception
could kill that thread without entering the parent's error list; a successful
stdout stream and process exit could consequently be returned as success.

`test_failed_stderr_persistence_cannot_be_reported_as_success` reproduced this:
the fake stderr flush raised, pytest reported an unhandled thread exception,
and `_process` did not raise. The author now records flush/fsync/close failures,
preserves captured output and closes the pipe before the parent validates the
error list. The same regression passes. This is an observed error-propagation
repair, not a hypothetical claim that all operating-system persistence failures
are handled transactionally.

A related final-write boundary was made explicit: failure after writing
`COMPLETE.json` can leave complete-looking bytes alongside `FAILED.json`.
The function raises, retains both, and rejects reuse of the directory. **FAILED
dominates COMPLETE.** An inspector must require successful launcher completion,
no FAILED marker and a valid complete proof; the existence of COMPLETE alone is
insufficient. The independent injected-final-write test verifies this policy.
The tool does not claim atomic crash recovery or hostile-filesystem isolation.

## Independent checks

The independent security tests import only the launcher's definitions. Git
responses and child processes are replaced by handwritten artificial protocols;
those tests execute no actual commit or historical verifier. The separately
executed integration fixture is distinguished in the follow-up below.

- Complete tree manifests preserve UTF-8 names, modes and exact ordering rules;
  duplicates, case/NFC aliases, file/directory prefixes, traversal, drive/UNC
  forms, Windows forbidden names, control characters, links/gitlinks and tracked
  bytecode are rejected. File-count and listing limits fail without a partial
  returned manifest.
- All inherited Git-variable case variants are removed, including repository,
  alternate-object and configuration injection. The actual `_git` argv builder
  is intercepted and checked for no-replace/no-lazy-fetch, the exact repository
  and exact-root `safe.directory`, bounded time and raw batch input.
- Independent Git-blob hashes bind empty, arbitrary-byte, NUL and mixed-CRLF
  bodies. Concatenated packets are consumed exactly. Wrong object/type/size,
  truncation, changed content and missing framing fail. Oversized content is
  rejected before a body read.
- Artificial extraction requests each unique object once but charges every
  materialized file against total bytes. Literal export-substitution text and
  CRLF/NUL bytes survive unchanged; no attribute-processing operation is called.
  Every path/mode/size/blob ID/SHA-256 is checked against independent fixture
  values. A subsequent byte change fails tree verification.
- The output must be a fresh direct child of the designated replay area.
  Successful and failed directories cannot be reused. A missing local object
  stops before any child. Wrong summary, changed tree and interruption retain
  STARTED, manifests and available logs, record failure and never start a second
  child. The successful artificial path also retains a complete origin-bearing
  proof and preserves every file on a refused second invocation.
- Fake process timeout and stdout overflow kill the single fake process, retain
  the captured bounded bytes and fail. Reader-log persistence and final
  completion persistence failures are separately injected.

The symlink test attempts an actual temporary directory symlink and was skipped
because this Windows host denies its creation. Source inspection covers the
symlink/reparse-ancestor check, but this run does not establish its runtime
behavior for Windows junctions, Unix symlinks or malicious concurrent changes.

## Scope and remaining gate

The public CLI exposes two fixed recipes. Its internal child mode is a **trusted
parent-to-child capsule interface**, not a safe API for untrusted user-written
manifests or bootstrap copies. The static bootstrap and installed runtime are
trusted; Python instrumentation is not an OS sandbox. The separate reviewer
covers exact summary types/digests and fresh-process import-contamination tests.
This audit does not relabel those checks as its own independent executions.

Raw object materialization avoids Git checkout/export transformations. Root
separately verified the two local recipe commits and report/HTML identities;
this lane did not repeat those object reads. Matched-prefix requires existing
NumPy/SciPy imports and legitimately writes disposable evidence snapshots in
scratch; this must not be described as a stdlib-only or zero-scratch-write
reproduction. No original training, collection, assessment or random-stream
generation is authorized by a saved replay.

Validation command: existing repository Python, `pytest
tests/test_pinned_replay_security.py -q -p no:cacheprovider`, with a unique
repository-local basetemp. Initial run: **68 passed, 1 skipped in 0.26 seconds**.
`ruff check tests/test_pinned_replay_security.py` passed. Earlier failing output
was diagnostic evidence before the repair, not a remaining failing test.

Initial pre-compatibility review identities:

- Launcher: `77eaa93fefa7e6c0b4350e2a23ccbc26de49e6e3a3a594c0f0e91ddd1697accb`.
- Independent tests: `7b7f521492fd8e6c3a56605625d024117f60d0b3a0fac9828e97c4544b130a70`.

The final source change after the last independent run only clarified the
trusted child-interface docstring; this reviewer checked that change and both
final file identities. Root owns combined testing and the two actual recipe
checks. These artificial results do not claim historical runtime compatibility,
reproduce the original binary environment, or establish security containment.

## Windows compatibility follow-up: retained failure, bounded repair

Root's first real matched-prefix replay on the initial source failed with
`WinError 206`. The saved record reports stage `child`, exit code 1 and
`retry_permitted: false`, from 14:20:49.809626 to 14:20:58.276863 UTC on
2026-10-01. The unchanged historical snapshot copier attempted a directory
beneath the long capsule-owned scratch path. Read-only calculation from its
retained tree manifest finds a longest suffix of 132 UTF-16 units and a complete
projected snapshot filename of 270 units. The earlier artificial suite did not
cover this real Windows path geometry. No successful real replay was reported.

The repair changes only the new launcher: allocate one exclusive short scratch
directory at repository-relative `.local/p/<16-lowercase-hex>`. Its OWNER binds
capsule, recipe, commit and exact scratch reference. STARTED, request, child
proof, COMPLETE and FAILED carry the same reference. Both parent and child check
ownership and reparse ancestors. Read/write guards allow only that allocation,
not its containing `.local` tree; sealed replay still forbids scratch writes.

Before child execution, Windows preflight checks both all extracted targets and
snapshot projections, reserving a 32-unit temporary-directory component. Full
file paths are limited to 259 UTF-16 units and parents to 247; an excessively
long checkout/output fails without changing OS settings or frozen source.
Allocation and capsules are not reused or automatically removed. The unchanged
verifier may still clean its own `TemporaryDirectory` children, so retaining the
allocated scratch does not promise retention of every disposable snapshot.

The follow-up independent cases cover allocation collision, cross-capsule,
recipe and commit mismatches, malformed references, owner corruption, retained
scratch on success/failure, separate file/parent boundaries, astral characters
occupying two UTF-16 units, and the reserved snapshot component. The two skipped
cases attempt real temporary symlinks for output and scratch ancestors; Windows
permission prevented creation. **78 passed, 2 skipped in 0.37 seconds**, with
Ruff clean.

The author-written
`test_real_nested_snapshot_uses_owned_short_scratch` was independently executed:
**1 passed in 0.84 seconds**. It builds a tiny artificial local Git repository,
uses artificial package stubs and a fresh bootstrap, and actually writes/reads
the long `jobs/001-<64 hex>/COMPLETED.json` geometry inside a temporary snapshot.
Saved fixture evidence records **255 file units and 240 parent units**. It also
checks cleanup of that temporary child, retention of the owned scratch and
agreement of all scratch references. It does not import a real study's evidence
or recompute a scientific outcome.

The first real failed capsule remains unchanged. This reviewer checked its
FAILED bytes, SHA-256
`4fd52250b55bf5edc9fdfa3cc0dc6db5bf3ccaa77adbf83f407fa46ab0ef8e5e`, and stderr
bytes, SHA-256
`204ca05c13e8c729e35af2d99ae36cf9f8ed93db8d000302ee772301c1c7a687`, before and
after these tests. Raw stderr is retained locally rather than reproduced here.
Any root-authorized subsequent real check is a finite new attempt in a new
capsule after this repair; it is not a silent retry or a rerun of model
collection, financial assessment or the canonical synthetic bank.

Revised held launcher SHA-256:
`dce34a515e51e3544a6a6aac23d769ebb76eedec4c12b2dd2898835ec6ec4ed0`.
Revised independent test SHA-256:
`09c0ffce027a5fa668eadb9d44a80ac70c332e857b300e9463ebc4d4ac7c70ab`.
Root retains ownership of combined testing, finite actual recipe invocations and
publication. The successful artificial geometry check is not itself a claim
that either real historical recipe has completed.

## Later root-run results: read-only publication inspection

Root subsequently completed both actual saved replays using the unchanged
`dce34a…4ed0` launcher. This reviewer inspected the 14 prepared public files in
[`artifacts/pinned-saved-replay-v1`](../../artifacts/pinned-saved-replay-v1/integration.json)
with a separate standard-library JSON/hash check. **This was a publication
consistency inspection, not another evidence replay or an independent Git
tree/blob comparison.** Root's separate all-blob inspection is attributed to
root in the [integration audit](pinned-replay-integration-v1.md).

Both public COMPLETE, STARTED, child-proof and tree-manifest files exactly match
their retained capsule counterparts; exported scratch-owner bytes also match
the allocated OWNER files. The inspection recomputed manifest SHA-256 values,
file counts, byte totals and origin-to-manifest hash mappings, checked identical
recipe/commit/runtime/scratch references across the records, and confirmed
successful exit/status, timestamp order and absence of FAILED in each successful
capsule. Each retained stdout JSON equals its public child summary; both stderr
files are empty.

| Record inspected | Tracked files / bytes in manifest | Project origins | Reported monotonic elapsed | Recorded dependencies |
| --- | --- | --- | --- | --- |
| Matched-prefix | 1,251 / 56,802,037 | 12 | 13.047 seconds | NumPy 2.5.3, SciPy 1.18.1 |
| Sealed confirmation | 2,560 / 99,747,310 | 3 | 30.938 seconds | None; standard-library route |

The expected result hashes and matched-prefix HTML hash are unchanged. The
integration record correctly accounts for **three actual attempts: one initial
failure and two successful saved replays**. The public initial bootstrap still
hashes to `77eaa…accb`; its FAILED record exactly matches the retained failed
capsule and the earlier failure hash above. The private stderr hash is also
unchanged, and raw stderr is absent from the prepared public failure directory.

A stale draft sentence in the reproduction guide initially said the corrected
replay was pending and sealed confirmation unattempted. This reviewer reported
it; the guide author replaced it with both completed outcomes while retaining
the initial failure. The corrected opening and chronology were checked. No
remaining numerical transcription or claim-boundary blocker was found in the
guide or root integration audit. The successful records establish observed
compatibility on the recorded runtime, not new statistical evidence, model
identity attestation, original binary-environment reproduction, or a sandbox.

After this reviewer's earlier nested-fixture execution, the author changed only
that artificial test's placement: it now allocates a fresh short repository-local
temporary test root independently of pytest's potentially long basetemp. Its
cleanup verifies exact parent ownership and no reparse ancestors before removing
only its own artificial repository. The revised author-test SHA-256 is
`d2529aec49df65e15cd9679e2ff4f748f4bef2f8bf2af807faeaa1a8ce28e903`.
This reviewer inspected that change but did not rerun it; root's separate
targeted result is reported in the integration audit. The real launcher and
real failed/successful capsules were unchanged by this test-only refinement.

**Disposition:** no remaining publication-consistency blocker in this lane.
All actual recipe executions, full Git-object checks and publication remain
root's work; this section must not be represented as an independent replay.
