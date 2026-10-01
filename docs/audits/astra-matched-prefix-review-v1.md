# Matched-prefix Astra study: protocol and implementation review

2026-10-01. **No unresolved blocker in the reviewed protocol and implementation.**
Actual preparation, both publication gates and execution remain separate root
operations; this review does not claim they have occurred. This is an internal
AI-assisted review, not external peer review. The reviewer proposed the earlier
research direction and the Q/G endpoint distinction, but did not author this
study's new protocol or implementation. Independence applies to reviewing those
artifacts, not to originating the research question.

## Scientific boundary and saved-prefix checks

The new question is whether displaying historical candidate feedback improves
one fresh proposal from an otherwise identical state. It is not a repeat of
the unmatched original trajectories, an isolated manipulation of IC alone,
or a test of Astra weight training. The primary score Q concerns the candidate;
secondary G concerns its effect through the fixed historical selector. The
current draft correctly retains `Q(copy)=Q(b)`, `G(copy)=0`, and incremental
net gain `G−.01`. It does not assign a fabricated zero Q or invalidity penalty
to a duplicate copy.

Independently read the original saved submissions and task metadata, without
constructing financial tasks or evaluating market arrays. The twenty fixed
prefix records are historically usable and distinct within each state. Their
largest structural lag is 24; each state's historical winner has lag at most
19. The lag definition counts maximum earlier-row offset: lag 60 allows the
current row plus sixty earlier rows, not a sixty-observation window. It is
conservative and does not simplify algebraic cancellations.

Independently derived the complete cheap expression schedule directly from the
protocol, then compared it with the new pure core's outputs:

| Generator | Slots | Maximum realized lag | Maximum AST nodes |
|---|---:|---:|---:|
| Copy | 40 | 19 | 27 |
| One window edit | 40 | 39 | 27 |
| Grammar draw | 40 | 20 | 20 |

All 120 generated expressions passed the common eligibility filter. The exact
expression schedules matched. For the review's canonical forty-row object
with keys `task,r,copy,window_edit,grammar_draw`, SHA-256 was
`f347345f7a3f07e4f6727f31739432a69d398be3f3d4efa2abe174f2072c13a4`.
This is an independent comparison artifact description, not a replacement for
the eventual preparation contract or a financial score.

The forty grammar draws have template counts `4,6,4,3,9,2,10,2` for indices
0 through 7. They are not empirically balanced. Sign variants often share the
same feedback-oriented signal and do not establish economic diversity.

One concrete information limitation was identified and resolved in the draft:
2023-H1 prefix attempt 1 is `neg(ts_mean(returns,5))`, whose feedback is
recoverable from the common probe by sign transformation. The author added
that masking removes the displayed package, not all inferable information.
The state remains in the fixed denominator. No favorable-state replacement
or stronger treatment-isolation claim is justified.

## Reviewed draft and partial source

The protocol makes all five generators subject to the same structural/grammar
rules and all 200 attempts part of the result denominator. Historical rejection
keeps G at zero against the valid prefix; future failure cannot retroactively
exclude a historically admitted proposal. Reuse changes computation counts,
not replication counts. Four fresh calls per fixed condition/state are not
four independent markets or attested shared-seed pairs. The MCSE formula is
conditional on an explicitly unverified independent-draw assumption.

The revised draft requires two publication gates, byte-only early binding of
old outcomes, no future joins during collection, complete-bank freezing before
new assessment, zero automatic retries, durable incomplete evidence, and a
fresh recorded quota observation before each two-call batch. Shared host
context remains a disclosed limitation rather than a claimed access sandbox.

The initial `astra_revision_core.py` helpers were checked for dependency-lag
composition, literal one-edit/one-draw controls, exact historical ties, duplicate
handling and truthful/masked observation construction. Actual saved-state
checks confirmed that the observations differ only in `candidate_feedback`.
No source blocker was found in those reviewed helpers. Their grammar validation
uses the existing artificial fixture, not market scoring.

The final literal instruction block was independently extracted from the plan,
then all twenty complete prompts were rebuilt directly from original task and
prefix records. Every byte matched `core.prompt`; there were twenty unique
state/condition prompts. The instruction SHA-256 is
`e081aff6c12200787714ae113a48451b073727bcf52ff0ff582b73920415db23`.

The subsequent analysis code was reviewed for all-attempt Q and selected-Q
decompositions, Q/G/cost arithmetic, all four truthful comparisons, strict
200-slot ordering, equal state weights, all ten states/five years, and the
conditional-generation MCSE. No mathematical blocker was found. Added and ran
one independent test in `tests/test_astra_revision_study_review.py`: large
common shifts in market-state levels must change score levels without changing
the within-state treatment contrast or conditional generation error. Both
fixtures retain 200 slots, have primary and secondary contrasts .05, and match
the hand-derived MCSE `sqrt(10*(1/1500+1/1875)/4)/10`. The test and targeted Ruff
check passed. This tests the scalar-analysis boundary, not evidence provenance.

The durable driver/replay must reconstruct every adjudication and cache-derived
Q before analysis, including the common baseline across branches and
`Q(copy)=Q(b)`. The pure analysis function's arithmetic validation alone does
not authenticate these facts. This required implementation boundary has been
sent to its author.

## Incremental durable-driver review

The preparation/collection path binds old assessment, pool-result and ledger
bytes without parsing their future fields. Its structural replay of the old
study omits the assessment argument. State construction and feedback caches use
only original historical proposals and task metadata. Complete submissions
are rebuilt from all forty two-call batches and all 200 adjudications.

The assessment caller verifies the full-bank publication gate before invoking
the old pool's full arithmetic replay or joining its cached outcomes. New jobs
use fixed task/AST/direction identities, and the frozen scorer-output validator
rechecks historical metrics, support, signs, expression identity and failure
forms. Report assembly derives Q from validated outcomes, resolves one baseline
per state, explicitly requires copy key/Q equality, and then calls the scalar
analysis. This closes the earlier pure-analysis provenance boundary in the
reviewed source.

Concrete implementation findings were sent to the author before execution:

- A copied original-contract hash omitted one character; corrected to the
  actual saved-byte identity before preparation.
- A preparation failure marker was initially ignored by contract validation;
  a permanent-INCOMPLETE check was added.
- Pre-dispatch setup failures could previously leave a batch retryable;
  durable setup-command records and terminal failure handling were added.
- Quota could expire between checking and dispatch; individual dispatch
  timestamps/checks were added. Setup also checks quota at its exact saved
  start time before creating a command directory. Independently ran the new
  regressions for expiry before setup, during setup and between dispatches.
- A key first seen through a prefix retained a null first-new-slot identity;
  subsequent new-slot use now records that identity.
- Extra fields in saved quality objects and a partially failed submission
  freeze were identified as schema/failure-retention edges. Source now checks
  exact quality keys and permanently marks attempted freeze-write failures.

The final replay path was inspected: it validates the saved Gate 2 receipt
before parsing the old future cache, then reconstructs the complete job plan,
every outcome and all 200 rows. Retained provenance, statuses, historical
metrics and costs remain exact; only reconstructed floating arithmetic uses
the existing finite `1e-12` tolerance. Replay does not invoke the task loader,
runtime-version check, provider, raw-market reader or financial evaluator.

Added a second independent test using the author's artificial fixture. After
all 200 synthetic slots freeze, a resealed Gate 2 receipt missing the submission
file is rejected before `_cache_and_plan` is entered. After restoring the valid
receipt, a `KeyboardInterrupt` in the first fake future job preserves STARTED,
omits COMPLETED, records permanent INCOMPLETE and prevents both assessment
continuation and replay; the attempted future-call count stays one. The two
independent tests passed in 38.53 seconds, and targeted Ruff passed. No real
provider, market array or financial score was used.

Also independently ran six author regressions for the three quota boundaries,
ambiguous STARTED evidence, exclusive execution/operator-stop persistence, and
partial submission-freeze failure: **6 passed in 30.78 seconds**. Waiting after
a completed setup preserves its setup/probe counts; expiry between dispatches
retains the already launched call and permanently stops without replacement.
Explicit stop reasons are now durable. Completed assessment rejects another
execution before requiring the raw archive or original scoring environment.

Independently ran the author's core tests together with the additional
statistical test: **19 passed**. These checks do not execute real providers or
financial tasks. The author subsequently reported **57 passing tests** across
18 core, 13 driver, the two independent reviewer and 24 lag-review cases, with
Ruff clean. This full combined run was author-run; it is distinct from the
independent executions listed above. Two unused test imports and guide wording
were cleaned up after that run; no tested runtime logic changed.

The completed reproduction guide was checked against CLI/API signatures,
publication maps, cache timing, exact evidence versus arithmetic tolerance,
fixed costs and failure states. Its initial claim of independent calls was
corrected to separately invoked fresh calls; independence remains explicitly
unverified. It now distinguishes the helper's anonymous-versus-working-tree
byte check from the executor's local committed-blob verification.

Final reviewed SHA-256 identities:

| File | SHA-256 |
| --- | --- |
| `docs/astra-matched-prefix-plan-v1.md` | `a0f5a5ede6f098c5a1c632ceb5ab6eae6ac449fcbf025ce72c94a2be0073f271` |
| `src/alpha_research_rl/astra_revision_core.py` | `74c6f6b36406234b4ea5a004d6566356f6d5b47fa347e9e5ec1f68a2f538e0f5` |
| `src/alpha_research_rl/astra_revision_study.py` | `9bad4259a85d37c2f94b337e5d179cc6ca11bd58200e37dac9ead8618723a227` |
| `tests/test_astra_revision_core.py` | `9b5ad04f0c7b2f006f5d42819ddcde71071ee5b87a4a1b344fd164d8513b80c2` |
| `tests/test_astra_revision_study.py` | `383ae89b9ac024f13c906579fabbf42842e0a5b9f0d86c927ceb23979c9f8ae9` |
| `tests/test_astra_revision_study_review.py` | `cd0eefea8fc16d993215ea132d61d66d85e9806e03555fe6e2e653633556ab47` |
| `docs/reproduce-astra-revision-study.md` | `7cc657cee30ec32d722b663852b63bac775cd025832cbdddcf5c1a3e39ad40db` |

No actual model response, new historical market score, future score, prepared
contract or executed-study outcome was produced by this review. The review
supports proceeding to the root's separately verified preparation/publication
steps, with all previously stated scientific and provider-boundary limitations
unchanged. The root's repository-wide integrated test run, actual preparation
freeze and public publication checks were still pending when this review closed.
