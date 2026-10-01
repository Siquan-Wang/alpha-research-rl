# Sealed-confirmation implementation review

2026-10-01. **Pre-run implementation review passed; no unresolved blocker in
the reviewed contract. No canonical panel bank was generated or run by this
reviewer.** The source and tests identified below are ready for root's final
integration and publication gate. This is not a report of calibration outcomes.

The reviewer participated in the statistical design critique, but authored
neither the core nor the runner. This is internal AI-assisted independent
implementation review, not independent protocol authorship or external human
peer review. Existing financial studies, models and market scores were untouched.

## Core finding and resolution

Source-first review identified a recoverable error in the original
`record_confirmation_access` operation: malformed event metadata raised an error
while leaving the batch open and untainted. A caller that caught that error could
subsequently obtain a valid report, despite declaring a confirmation access.
This is different from correcting an `add` argument before touching any labels.

The implementation author repaired the boundary. A declared access operation
first enters `FAILED`; only a successfully validated access from `OPEN` restores
the open state, with an irreversible recorded taint. A malformed or post-seal
access remains failed. Three independent regression cases verify that catching
the metadata error cannot restore a valid execution. This is fail-closed API
behavior, not interception of unrecorded access or hostile-Python isolation.

No unresolved core-contract blocker remains in the reviewed source.

## Independent small-state checks

The reviewer created
[`tests/test_sealed_confirmation_review.py`](../../tests/test_sealed_confirmation_review.py).
The first core-only run completed **26 tests in 0.06 seconds; Ruff passed**.
These original artificial cases cover:

- Exact tail probabilities against enumeration of four-way equiprobable
  innovations for probabilities 1/4, 1/2 and 3/4; degenerate probabilities 0 and 1.
- Every fair-label vector for lengths 0 through 10, independently confirming
  that selecting the sign after seeing labels doubles the fixed-sign rejection
  frequency, including sample sizes where neither rule can reject.
- Frozen abstention masks, retained total prediction counts, unavailable accuracy
  at zero support, strict integer signs, malformed labels and exact inclusive
  threshold comparisons.
- Requiring every expected predictor, defensive copies of vectors/provenance,
  canonical content identities, rejecting a stale forged digest, and reveal once.
- Premature reveal, malformed reveal and an injected arithmetic exception after
  partial internal computation: all consume the batch permanently, without
  returning a partial valid report or converting failure to non-rejection.
- A correctly recorded leak invalidates every batch result even when its naive
  calculation does not reject.

These tests use no canonical seeds or panel subsets. The core contains no label
generator, features, search algorithm or RNG. Its label argument first arrives
at `reveal`; its arithmetic cannot establish the caller's independence assumptions.

## Runner lifecycle and saved-evidence checks

The completed independent suite subsequently passed **36 tests in 0.48 seconds**.
Additional checks used eight handcrafted rows and explicitly artificial
metadata/namespaces. A two-panel completed lifecycle fixture was supplied by the
runner author; the reviewer independently added its tampering tests rather than
claiming independent authorship of that fixture. None of these fixtures was
presented as a completed 640-panel run.

- The first label-owner call observes both full 32-attempt correct-search
  traces, the fixed/adaptive/oracle prediction vectors and the constant fault
  base already sealed. Reversing confirmation labels preserves the entire
  pre-reveal trace and seal while changing the subsequent oracle outcome.
- Failure to write the durable seal leaves the target owner uncalled. Target
  materialization/innovation failure propagates as an error; a failed owner
  cannot be called again. Confirmation noise is absent before owner invocation.
- All three faulty arms remain protocol-invalid. Their requests are retained
  at 32, 32 and one respectively, including duplicates. On the constructed
  example, selection-plus-orientation rejection includes the sign-only rejection.
- An incomplete publication file map never reaches generation. An injected
  generator failure after the first durable STARTED record preserves FAILED
  evidence and blocks both rerun and completed replay. No synthetic panel is
  generated in this failure test.
- A rebuilt hash chain cannot conceal reverse chronology. Fully saved artificial
  replay succeeds with every stream generator forbidden, but rejects both a
  retained integer K changed to the same-valued float and labels moved before
  the prediction-seal event, even after the relevant hashes/mirrors are rebuilt.

Root separately identified that a complete contract file could survive a failed
preparation write while `PREPARE_FAILED` was ignored. The reviewer inspected the
repair: preparation-directory membership rejects that marker and other unexpected
members. The final runner also binds loaded runner/core source bytes, parses
receipts/contracts from captured buffers, validates exact STARTED fields, and
rechecks captured saved bytes and source identities before returning replay
success. These observations do not claim interception of concurrent or hostile
external activity.

After the final runner edits, the two affected completed-replay cases passed
again: **2 passed, 1 skipped, 34 deselected in 0.38 seconds; Ruff passed**. The
new optional leaf-symlink case was skipped because this Windows host did not
permit the fixture symlink. Leaf-path rejection was reviewed in source but is
not claimed as executed here. Earlier tests are not added to these overlapping
reruns as if they were separate cases. The final review file contains 37 cases.

## Independent pre-outcome arithmetic

The reviewer separately calculated binomial masses with integer coefficients
and powers, without using the production recurrence, loading the root's saved
reference, or generating a panel. The results agree with the proposed constants:

| Quantity | Independently checked value |
| --- | ---: |
| Smallest rejecting K among 256 fair labels | 142 |
| Actual discrete null rejection probability pi0 | 0.04565604346614261 |
| Upper null count U among 512 panels | 37 |
| P(null count > 37) | 0.002649919285411411 |
| P(null count > 36) | 0.004584924522854112 |
| Lower planted-oracle count L among 128 panels | 128 |
| P(at least one oracle miss among 128 panels) | 4.6290403895747995e-10 |
| Sign-only fault's naive null rejection probability | 0.09131208693228522 |
| P(sign-only count > 37 among 512 panels) | 0.9255870391647933 |

The null boundary probabilities bracket the allocated tail budget 1/300.
The oracle's single-panel miss probability, approximately 3.6164378e-12, differs
from the 128-panel failure probability above. Decimal displays are descriptive;
the comparisons were exact rational arithmetic.

Using pi0 for the count envelope requires the canonical nonabstaining M=256
vectors. Generic helper support for abstention must not silently change that
population. The finalized plan states this distinction and the three single-tail
checks, with total ideal-law false-alarm allowance .01. It does not claim a
two-sided calibration or equivalence test. The sign-only fault can miss the
empirical upper threshold with positive probability; structural invalidity does
not depend on that event.

## Interpretation and remaining scope

The [guide](../sealed-confirmation.md) correctly derives the five-sign 1/32
versus 2/32 example and separates the conditional-fair-label null from overlapping
financial returns. No narrative blocker was found in that scope. A planted oracle
checks that the evaluator can reject for a known direction; it does not show that
either search procedure learned that direction.

Passing the synthetic calibration family cannot validate undisclosed label
access, omitted records, arbitrary generators, reused market ICs, p-values for
the previous studies, GenAI advantage or alpha. SHAKE reproducibility is not an
independent proof of random-stream independence. Saved replay recomputes from
retained arrays; it does not independently attest their pseudorandom origin.
Canonical publication and execution remain root's responsibility, outside these
artificial pre-run tests.

Final reviewed identities:

| File | SHA-256 |
| --- | --- |
| `src/alpha_research_rl/sealed_confirmation.py` | `d5b91b30cf97a25eb52af6580e4a894652b6400cbcd046324a15975f66b6cbf2` |
| `scripts/check_sealed_confirmation.py` | `dbe8a73d1ccd31a65fcfab53e3f30102ea1a4be35db96e695eee69759c6e8292` |
| `tests/test_sealed_confirmation_review.py` | `8f52ffe5699c956a22a3a7d7e0cfe169786c62ae6bb29ea346fd621a5e965928` |
| `docs/sealed-confirmation-plan-v1.md` | `151f0e6946a8d0353ab61ffaf23de09f77168a66b8597036b281f8df82cac143` |
