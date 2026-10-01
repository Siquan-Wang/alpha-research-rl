# Reliability replay portability: independent boundary review

2026-10-01. This internal AI-assisted review inspected the bounded comparator
correction and its tests without editing the implementation. It is separate
from the [original reliability mathematical review](reliability-analysis-review.md)
and the [retained-diagnostics review](retained-diagnostics-review.md).

The retained public CI log shows Linux Python 3.11 passed 424 tests (five
skipped) and the full 900-record financial analysis replay, then failed the
reliability loader's earlier `rebuilt == saved_analysis` check. That log locates
the failure, but does not isolate its upstream arithmetic cause. Python 3.12
success was reported by root; this reviewer did not run that public job.

The final correction replaces only that complete-analysis comparison. It checks
identical container/scalar types before recursing, exact dictionary keys and
list lengths/order, and exact non-floating values. Thus `True`, `1` and `1.0`
cannot substitute for one another. Computed floating values must both be finite
and agree within absolute and relative tolerance `1e-12`. Identity metadata
subtrees (`study`, `status`, `roles`, `integrity`, `source_reports`, `limitations`)
remain exact, including any floating values beneath them. Input report bytes
still must match their declared SHA-256 before analysis. No scorer, original
outcome, pairing, covariance, denominator or weighting formula changed.

The reviewer independently ran all 28 focused reliability tests and Ruff on
the source and test file: both passed. An additional mutation check against the
actual published five-report analysis accepted a `1e-14` computed-reward drift
and produced an identical reliability diagnostic. It rejected all ten separate
mutations: a `1e-8` score change, NaN, infinity, integer-count-to-float substitution,
changed count, boolean-to-integer substitution, source-byte hash, checkpoint
role identity, list order and task-list length. The focused tests also reject
a tiny metadata-float change and preserve source-byte checks and input files.

The final source SHA is
`267d633b5b732885558984afed323257cf045904e8286c5e3928f89d3e55e355`.
The retained reliability JSON records that source identity. Its complete
canonical JSON excluding only `analysis_source_sha256` has SHA
`d868eb31ab5ea78e9afdef446c9d71cd3d6fcdfd4dc18d3721ae3a00e730c792`
both before and after regeneration. The diagnostic body, source-analysis
identity and five input-report identities therefore remained unchanged.

A fresh current-host public diagnostic replay passed all 12 reliability
contrasts, 60 year omissions, 900 diversity records and 12 constructed query
plans under the existing training-import/network/raw-data/weights guards.
The exact canonical-JSON mechanism-gate comparison was untouched. These are
Windows-host validation results, not a new Linux cross-version pass: root must
rerun the public Python 3.11/3.12 jobs before making that claim.

No blocking issue remained in the reviewed fix. This portability repair adds
no new market evidence or learned-policy result, and does not change the
statistical limitations of eight draws on the existing fixed episodes.
