# Actual historical replay integration

2026-10-01 UTC. This is root's engineering integration record, following separate
implementation, contract and failure-handling reviews. Root specified and
integrated the launcher and separately inspected its outputs; this is internal
AI-assisted verification, not external peer review or independent economic
replication. The original studies were not rerun.

## Three attempts, including the failure

| Actual invocation | Historical commit | Outcome | Recorded elapsed |
| --- | --- | --- | --- |
| Initial matched-prefix attempt, 14:20:49–14:20:58 UTC | `7e0f7b3` | Failed with Windows error 206 in a nested temporary snapshot | About 8.47 seconds by recorded timestamps |
| Corrected matched-prefix attempt, 14:34:02–14:34:15 UTC | `7e0f7b3` | All 200 slots and required HTML verified | 13.047 seconds, monotonic |
| First sealed-confirmation attempt, 14:34:42–14:35:13 UTC | `58dc66e` | All 640 saved panels verified | 30.938 seconds, monotonic |

The first source version, SHA-256
`77eaa93fefa7e6c0b4350e2a23ccbc26de49e6e3a3a594c0f0e91ddd1697accb`,
passed artificial checks but had not covered this full temporary-path shape.
The exact [failed record](../../artifacts/pinned-saved-replay-v1/initial-failure/FAILED.json)
and [initial source](../../artifacts/pinned-saved-replay-v1/initial-failure/bootstrap.py)
remain public. The failure was reported, not converted to a skip or overwritten.
Raw stderr stays local because it includes host paths; its hash is retained in
the [failure summary](../../artifacts/pinned-saved-replay-v1/initial-failure/evidence-summary.json).

The corrected launcher allocates a short, exclusive scratch directory inside
the repository, binds its owner and reference throughout the capsule, and checks
Windows UTF-16 path lengths before child execution. It does not change system
settings or historical verifiers. Both successful invocations used source SHA
`dce34a515e51e3544a6a6aac23d769ebb76eedec4c12b2dd2898835ec6ec4ed0`.
They were deliberate new invocations after a reviewed compatibility repair;
the launcher does not automatically retry a failure.

## Saved evidence actually verified

| Recipe | Extracted tracked files / bytes | Verified project-module origins | Saved result |
| --- | --- | --- | --- |
| Matched-prefix | 1,251 / 56,802,037 | 12 | 200 slots, 10 states, 133 future keys, exact report and HTML |
| Sealed confirmation | 2,560 / 99,747,310 | 3 | 640 panels, exact report and saved-array reconstruction |

The [integration record](../../artifacts/pinned-saved-replay-v1/integration.json)
links the attempt accounting and inspection identities. Exact success records:

- [Matched-prefix completion](../../artifacts/pinned-saved-replay-v1/matched-prefix-v1/COMPLETE.json),
  [manifest](../../artifacts/pinned-saved-replay-v1/matched-prefix-v1/tree-manifest.json),
  [child proof](../../artifacts/pinned-saved-replay-v1/matched-prefix-v1/child-proof.json).
- [Sealed completion](../../artifacts/pinned-saved-replay-v1/sealed-confirmation-v1/COMPLETE.json),
  [manifest](../../artifacts/pinned-saved-replay-v1/sealed-confirmation-v1/tree-manifest.json),
  [child proof](../../artifacts/pinned-saved-replay-v1/sealed-confirmation-v1/child-proof.json).

Root's separate standard-library inspection did not import the launcher or run
either verifier again. It compared each complete file set, mode, Git blob ID,
length and SHA-256 against fresh local Git tree metadata; checked the commit's
tree ID; and rehashed every extracted file, imported project source and retained
bootstrap. It also checked STARTED/proof/completion scratch references and the
scratch owner's capsule, recipe and commit. All matched. Both child stderr
files were empty and both invocations exited zero without a failure marker.

The report hashes remain
`89162112ddad384ed8917a8b1198ce94044abc90ff15e1680bfe88b66eb43c37`
and `ec6d9076d70f50d436c3d69a9ec126d23489f2ce4f98bbf4e25064e6d9c7306d`.
Matched-prefix also retained HTML SHA
`8bb1ff7013c8c7906f9223daca87287296103f8643e41216037d2bbf39d9b772`.

## Tests, runtime and limits

Before the initial invocation, root's combined artificial suite passed 96 tests
with one Windows symbolic-link permission skip. After the path correction,
the combined suite passed **109 tests, with two permission skips, in 4.94 seconds**.
A preceding invocation with an excessively long pytest base correctly triggered
the new preflight and failed the deep-path fixture; 108 other tests passed.
The fixture was then made independent of pytest's base directory. Root ran that
changed case under a deliberately long base: **one passed in .73 seconds**.
The launcher source was unchanged by this test-only repair. Ruff passed.

Actual recipes ran on Windows 11 / AMD64 / CPython 3.12.14. Matched-prefix loaded
existing NumPy 2.5.3 and SciPy 1.18.1 with recorded relative source origins;
sealed confirmation loaded neither. Actual whole-recipe compatibility on other
operating systems or Python versions has not been established by these runs.
Artificial CI tests, when completed, are a different scope.

The matched-prefix verifier used disposable public-evidence snapshots. The
sealed verifier reported zero inner replay writes; the outer launcher still
wrote trees and records. Python instrumentation is not a hostile-code sandbox,
and recorded versions do not reconstruct all native binaries. The replays
performed no new model calls, market evaluations or synthetic panel generation.
They preserve prior findings and do not increase the studies' statistical
evidence. Existing CI replay routing and frozen study contracts remain unchanged.
