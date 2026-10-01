# Matched-prefix explorer: independent implementation review

2026-10-01. **No blocking finding in the reviewed renderer and synthetic tests.**
This is internal AI-assisted review, not external peer review. The reviewer
advised the underlying study and reviewed its driver, but did not author this
renderer. No partial real collection, complete real result, market array or
model response was read for this review. Actual completed-result rendering and
browser visual checks remain separate root operations.

## Evidence and execution boundary

The CLI requires an inactive execution directory with `COMPLETE.json`, validates
the frozen contract/submissions, and captures public source/evidence bytes. It
copies those bytes and required directory structure into a temporary snapshot,
then calls saved-driver replay on that snapshot. It embeds the captured report
bytes only when their SHA-256 matches the replay result. The author test mutates
the original report after capture and verifies that the embedded report remains
the validated snapshot. Missing completion, an active lock, rejected replay or
a mismatched verified hash produces no HTML output.

The snapshot replay authenticates complete population, source/input identities,
all outcome provenance and numerical consistency. It does not establish market
accuracy independently of the original evaluator. No provider, market loader,
financial scorer or network operation is invoked along this renderer path.
The output uses exclusive creation and rejects evidence/source destinations.

`render(payload)` is a formatting helper whose precondition is a trusted
`build_payload` result. Its self-consistent hashes and verification label alone
are not independent authentication of an arbitrary caller-created dictionary.
The public CLI enforces the snapshot/replay path; the synthetic fixtures
explicitly use verifier doubles and are not research evidence.

## Presentation and scientific interpretation

The page retains five generator summaries with 40 slots each, four truthful
contrasts, all 50 state-by-generator cells, 25 year-by-generator cells and every
one of the 200 attempted slots. Failed and negative outcomes are not filtered.
Null conditional-valid means display as unavailable, distinct from a numerical
zero. All four Q/G values remain available for each state and generator.

Each row uses its own historical branch selection: two prefix candidates plus
one new candidate, explicitly labeled attempt 3. Four repetitions are not
pooled into a best-of-four selector. Candidate Q, selected Q, baseline Q, G and
incremental cost remain distinct. Copy keeps baseline Q and zero G. Candidate
and selected validity decompositions, unrounded allocation comparisons and the
full raw report are available. The MCSE description retains its unverified
independence assumption and does not claim market-period uncertainty.

The displayed original formula comes from its proposal packet; the actual
evaluated spelling and cache source remain in separate provenance records.
Exact actor prompts come from the verified historical contract and frozen
prompt constructor. Diagnostic baseline/future values are not described as
actor-visible context. The page preserves the development-data, masked-probe,
no-profitability, no weight-training and no automatic-next-study limitations.

All variable text is inserted through `textContent`. Embedded JSON escapes
markup delimiters and handles Unicode/surrogate content without creating extra
script elements. There are no remote script/font dependencies or dynamic
network requests. Long public explanations receive an explicit preview marker,
while complete text remains in retained rows. This is source/DOM validation,
not an actual browser-layout or adversarial-host attestation.

## Independent checks and identities

Independently ran the author's 11 tests plus two additional presentation cases:
**13 passed in 2.88 seconds**, with targeted Ruff clean. Node DOM execution ran;
there were no skips. The two added cases establish that:

- An entirely invalid truthful generator still displays 40 failed attempts,
  mean Q −1, conditional-valid IC unavailable with count zero, valid selected
  baseline Q .12, G zero and net gain −.01. All 200 slots remain present.
- A whitespace alias remains the literal proposed expression in both detail
  and all-slot tables, while the original evaluated spelling remains unchanged
  in cache provenance.

All data for those tests were constructed artificial fixtures. No real study
was prepared, resumed, assessed, rendered or changed by this review.

| File | Reviewed SHA-256 |
| --- | --- |
| `src/alpha_research_rl/astra_revision_explorer.py` | `4a8206ca62702cb541ae167f1476503a459da3426e40127f294589f319461bf2` |
| `scripts/render_astra_revision_explorer.py` | `4f884d62c8d7af3988bf28380fd74c0831188e7359904fb69ae29df6476e0e77` |
| `tests/test_astra_revision_explorer.py` | `54b98926be9be9982447fd95d98724f5c9966cc22bcbcb9cc11e426d6d74bc45` |
| `tests/test_astra_revision_explorer_review.py` | `b7c210a29ac1f02e42376f3fb67555b394d77f131f2d0f7b1249bd22271bdaa1` |

## Supplement: required public saved-report and HTML replay

The subsequent renderer change extracts `payload_from_verified_records` as a
pure packaging helper. Its callers remain responsible for authenticating the
contract and report against saved replay. The normal builder retains its
immutable temporary-snapshot path; the new public wrapper verifies the saved
study once and then constructs the same presentation from captured, hash-bound
contract/report bytes. This helper is not a standalone evidence authenticator.

The public script's `main` now requires `verify_published_revision_explorer`.
Missing HTML is an error; the retained report-only Python API cannot silently
substitute for that CLI route. The wrapper checks the complete 200-slot,
10-state, four-repetition population, exact historical call accounting and
saved-replay identities before comparing the page. It requires exactly one
embedded payload, exact report and reconstructed prompt content, matching
renderer bytes, and the entire deterministic HTML template. Only real outer
CRLF/LF presentation line endings may normalize; JSON-escaped evidence and
prompt newlines remain exact. Captured inputs, page and renderer are checked
again for changes during verification. The execution-file count includes
completed setup-only WAIT records rather than assuming exactly 40 setups.

The guarded route prohibits new model/scorer imports, private model/data reads,
network access and subprocess execution after stdlib platform detection. These
are process-local checks, not an adversarial sandbox or code-object attestation.
The frozen saved driver **does write disposable public-evidence snapshots**.
Only the subsequent in-memory presentation reconstruction performs no writes;
the combined replay must not be described as a zero-write operation.

No blocking delta finding was identified. Independently reran the 13 relevant
HTML/payload/template/source-change/guard-route tests: **13 passed, 95
deselected in 2.57 seconds**. They use artificial evidence. The author separately
reported the earlier 118 affected synthetic tests passing, then a further
complete artificial-bank integration test passing in 57.74 seconds. That added
test invokes the actual frozen saved driver in a guarded child, removes the
artificial archive, forbids data/runtime lookups and compares against the normal
snapshot builder; its source was reviewed, but its run is author-reported here.
No extra reviewer test was needed. No actual partial collection, future outcome
report or completed real page was read or replayed for this supplement; actual
post-assessment integration remains root's responsibility.

| Current file | Reviewed SHA-256 |
| --- | --- |
| `src/alpha_research_rl/astra_revision_explorer.py` | `3dfb34a58dc934c7a585b3b675dcbed6aaa3b86010fec84f64086bfccc33e568` |
| `scripts/replay_published_astra_revision.py` | `ff661273ec1887e9e1eefcd6bbfe6a261167ddae25d24cb1ba6acf2c0aca28df` |
| `tests/test_public_astra_revision_replay_script.py` | `b7752a048e263395e5434721e4ef19990eacaf52de47b89b86ffc88c0eff7272` |

The earlier identity table and 13-test result document the original renderer
review, rather than claiming that its old source hash is the current revision.
