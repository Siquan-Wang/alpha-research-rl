# Astra pool explorer: independent implementation review

2026-10-01. Internal AI-assisted review, not external peer review. This reviewer
authored the pool protocol and earlier public replay wrapper, but did not author
the explorer, its twelve tests, or its guide. Independence here concerns the
explorer implementation, not the study design. The separate pool-results audit
covers numerical reconstruction; this review does not duplicate it.

**No blocking source, evidence-retention or injection finding.** One wording
precision was sent to the author before publication: the oracle guarantees
`O−S >= 0`, not a strictly positive gap. The initial template's “An oracle gap
is guaranteed” should say that the oracle is at least as good as original
selection by construction. The author made that correction in both source and
guide, and this reviewer checked the resulting text. The finding is resolved.

## Evidence boundary

`build_payload` verifies the source/input/task contract, requires the bound
complete execution tree and exactly the expected job directories, and captures
the report and execution records. It copies those bytes into a temporary tree
with the same relative paths and runs saved-record replay there. The embedded
`report_json` comes from that capture and its SHA-256 must equal replay's
verified report hash. There is no later reread of the original report for the
page content. A concurrent change that makes the capture internally inconsistent
fails replay; later changes to the original files cannot change the captured
HTML evidence.

The snapshot is a consistency mechanism, not a signed archive or an adversarial
filesystem sandbox. Loaded Python code and the host remain trusted. The guide
appropriately tells readers to regenerate a copied HTML artifact from public
evidence; a displayed hash alone cannot authenticate an edited page.

The builder follows the saved-replay path, not task construction or scoring.
Its temporary tree contains public JSON/source/plan evidence, not market arrays.
The browser code has no network or scoring operation. This review ran an actual
saved-report build in a fresh Python process with the existing public-replay
guards prohibiting financial/model imports, network calls, subprocesses, and
reads of raw data, cached data, model weights and private runs. Platform detection
preceded the subprocess guard, as required on Windows. The build succeeded:

- Saved snapshot status: `SAVED_ARITHMETIC_VERIFIED`.
- 180 retained slots, 30 pools, 132 keys and 219 captured execution files.
- Embedded report SHA-256:
  `ed50f86cbe876585b9de81c0960ca0a0a9d9c588345e82001ef5706141f0df2c`.
- No market score was recomputed and no model call was made.

These process-local guards are checks of the exercised path, not proof of
adversarial isolation or package-binary identity.

## Display and tests

The serialized envelope escapes `<`, `>` and `&`, uses ASCII JSON escapes, and
retains the exact decoded report text. Dynamic values enter text nodes through
`textContent`, including formulas, statuses, raw evidence and provenance.
No expression is interpreted as HTML or executable code. Null metrics display
as unavailable rather than zero; failed candidates retain status and penalty.

The page retains all twelve arm/selector summaries, thirty task/arm control
states, six candidates per state, all 180 slots, thirty period rows, fifteen
year/arm rows, all contrasts and the allocation rule. Selector flags use stable
slot IDs. Original expression spellings and cached evaluation expressions remain
separate fields; canonical AST identity is not described as economic novelty.
The oracle, reused development periods, six-attempt cost and valid-only
denominators are explicitly labeled.

Independently reran the author's **12 tests**, all passing. They cover immutable
capture, tampering and missing records, nulls and future failures, hostile text,
all controls/slots, selector flags, and output collision refusal. Added one
nonredundant synthetic boundary test in
`tests/test_astra_pool_explorer_review.py`: a whitespace alias must remain the
displayed original expression while the exact cached evaluation expression,
key provenance and selector metadata remain unchanged. This deliberately
modified renderer fixture is not asserted to be a verified financial report.
The additional test passed, and targeted Ruff checks passed.

The first added-test invocation exceeded Windows' path-length allowance inside
a long pytest temporary directory. A shorter repository-local base directory
passed; the frozen diagnosis implementation was unchanged. The successful
commands used `-p no:cacheprovider` and `.local/exalias-2` for the additional test.

No browser visual inspection was performed by this reviewer. The root's browser
checks and any later wrapper integration are separate validation work.

## Reviewed identities

Initial explorer source:
`eefece011f81e7174a83b9cbbf76f22e2b3c3bf3140484bbfc23238c6949e7e7`.
Author tests:
`d11304811b1cc0e3e2edb0ccd824dbf51d5b7b7f434e6781d7fd8b9fca562e07`.
Additional alias test:
`2a82b7d8a83063300c7e1f343540dfbc8c1df4461d4c9cb38da5c00126361942`.
This is the root's post-test EOF-only cleanup, removing one surplus final blank
line from the tested `064bc4e6d63968727974fd4526c27af400b51b76d461854674a35f10a9df4ea8`
file. No test semantics changed or additional test execution is claimed.
After the wording-only correction, the reviewed renderer SHA-256 is
`5c12e67d1d9c2a2daea243b1286c0ce2038a1ebe574dbf0d61f0c6f29d9128e1`;
guide SHA-256 is
`ceece6a403d72c9d9f669ed57957eb08d99d0d8dd015bc379a17e956df02d156`.
The root must regenerate the HTML for this renderer identity; no financial
scoring is required. The checks described above precede this prose-only change.

The guide's subsequent public-CI paragraph was also checked against
`verify_published_pool_explorer`: it rebuilds the verified payload, compares
the complete embedded envelope, and compares the full template with only outer
CRLF normalization. The recorded guide hash above already includes that
paragraph. This source check is separate from the author's wrapper regression
suite; it adds no scoring or browser-QA claim.
