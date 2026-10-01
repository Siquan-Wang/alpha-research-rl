# Sealed-confirmation outer-runner and saved-replay review v1

2026-10-01. **PASS within the scope below.** This internal AI reviewer authored
the confirmation core and separately reviewed the runner's source and actual
saved replay. This is not an independent audit of the core or external peer
review. No canonical panel was generated in this review.

## Source review and resolved findings

The review checked preparation, publication binding, target materialization,
failure retention and replay. The final runner:

- Rejects a failed preparation namespace, including a complete-looking contract
  accompanied by failure evidence.
- Checks the actual loaded runner/core file bytes against the bound source map.
- Parses captured receipt, report and event bytes; hashes those same bytes and
  rechecks consumed evidence before replay returns.
- Requires the exact sealed execution STARTED schema and type-exact canonical
  panel STARTED identities. Boolean or floating aliases for an integer index
  cannot pass that identity check.
- Validates evidence leaf paths with the public-root and no-symlink checks.
- Finishes both correct searches and durably seals complete prediction vectors
  before invoking the one-use target materializer. Full preceding search
  transcripts are bound by their canonical hashes and the event chain; the
  protocol now describes this precisely.
- Blocks any second execution when the execution directory exists. Partial or
  failed evidence cannot become a complete replay. Replay reconstructs the
  exact ordered 512 null and 128 planted panels, including all six arms.

## One actual guarded saved replay

The runner was loaded first. A local Python harness then instrumented the single
call to `replay(root)`. It replaced `feature_bits`, `generate_inputs`,
`hashlib.shake_256`, runner preparation/execution/write helpers and filesystem
mutation functions with raising guards. Import checks rejected model/market
modules; Python audit hooks rejected network/process events, write-mode opens,
filesystem mutations and reads outside the explicit public-evidence allowlist.

The one call ran from **13:43:51.013533 to 13:44:05.469553 UTC**, taking
**14.455824 seconds**, and returned `SAVED_SYNTHETIC_CONFIRMATION_VERIFIED` for
**all 640 panels**. There were **zero prohibited-operation attempts**, zero
imports during replay and 2,586 read-open events. All 1,291 allowlisted files
had identical hashes before and after the call. The returned verification
record reported zero new panel generations, model calls, market scores and
writes.

| Bound item | SHA-256 |
|---|---|
| Prepared contract | `12fcd6791ddc2197b4e20350dd80415d5532668ffedf2b66ab0d144d7e6a6ede` |
| Completed result | `ec6d9076d70f50d436c3d69a9ec126d23489f2ce4f98bbf4e25064e6d9c7306d` |
| Runner | `dbe8a73d1ccd31a65fcfab53e3f30102ea1a4be35db96e695eee69759c6e8292` |
| Confirmation core | `d5b91b30cf97a25eb52af6580e4a894652b6400cbcd046324a15975f66b6cbf2` |
| Protocol | `151f0e6946a8d0353ab61ffaf23de09f77168a66b8597036b281f8df82cac143` |
| Local instrumentation proof | `dd6aa91535197104f0da0bb4df5f3fa86660ac7098a6abe655e075787b2f32f0` |

The detailed proof is retained locally as
`.local/sealed-confirmation-guarded-replay.json`; it is not a required public
replay input. Frozen source, protocol, tests, contract and result were unchanged.
The reviewer did not repeat the existing test suite or the canonical run.

## Limits

These are local Python execution checks, not an adversarial security sandbox.
Module loading preceded the guards; before/after hashing and proof-file writing
occurred outside the replay call. Saved-array reconstruction checks retained
traces, seals, arithmetic and complete population. It does not independently
regenerate the pseudorandom bank, attest unrecorded historical access, prove
ideal-bit independence or establish real-market inference or model capability.
