# Reproducing the matched-prefix revision study

This separate implementation follows the [matched-prefix protocol](astra-matched-prefix-plan-v1.md).
Its tests use artificial saved banks, fake providers and fake financial tasks.
Passing those tests does not mean that the hosted study has run or produced a
financial finding. Completed v1 and pool evidence remains unchanged.

## Inspect a completed public study without scoring

From its matching published checkout, with the ordinary package installed:

```powershell
python scripts/replay_published_astra_revision.py
```

The [public replay guide](replay-astra-revision-evidence.md) describes the
process guards and required artifacts. The wrapper requires a complete 200-slot
bank and result, checks their exact retained byte mirrors, and invokes saved
arithmetic replay. It refuses incomplete or missing evidence. It does not call
the CLI, construct financial tasks, read the market archive, import training or
financial-scoring modules, or recompute market scores. It does not require the
original scoring runtime. Reported model and financial call counts describe
the historical study; the replay itself makes zero such calls.

The lower-level API is
`replay_revision_study(source_root=..., report_path=None)`. An explicit report
must exactly match the retained `COMPLETE.json` bytes. Verification returns
`SAVED_REVISION_VERIFIED`, input/output hashes, complete denominators, historical
call counts and explicit zero replay-operation counts. It rebuilds each saved
adjudication, cache key, direction and selector before checking Q/G arithmetic.
It verifies the saved financial evidence's consistency, not its market values
against raw observations. It also cannot independently attest the hosted
service's hidden context, model identity or generation independence.

## Two publication gates before execution

Only the root research operator executes these stages after source review.
Do not run them merely to inspect existing evidence. Commands below assume the
repository root; `--source-root PATH` can precede the subcommand. Preparation
requires the pinned runtime, the existing raw archive's exact SHA-256, and the
existing CLI executable/version identity. It hashes the archive without loading
market arrays. No installation, network fetch or actor call occurs in prepare.

```powershell
python -m alpha_research_rl.astra_revision_study prepare
python -m alpha_research_rl.astra_revision_study publication-files --stage preparation
```

Preparation exclusively creates `artifacts/astra-matched-prefix-v1/`: a sealed
contract, ten exact task mirrors, ten historical states, twenty exact prompts
and 120 deterministic cheap packets. It binds the new source/author tests/guide,
the publication verifier, original frozen sources/plans, input files, runtime,
data identity and CLI identity. Old assessment and pool files are bound only as
opaque bytes at this stage. Historical states use the original withheld arm's
first two proposals and saved feedback. No old future outcome is parsed or joined.

Publish and anonymously verify every path returned by `publication_files`.
The root's helper checks each required local working-tree file against
anonymous bytes at that public commit and writes a new stage-tagged receipt:

```powershell
python scripts/verify_astra_revision_publication.py --stage preparation --commit FULL_40_CHARACTER_COMMIT
```

Its default receipt is
`.local/astra-matched-prefix-v1/publication-preparation.json`. The executor also
checks the corresponding local committed bytes. A receipt is root-supplied
evidence of anonymous retrieval, not a cryptographic proof of when publication
occurred. Its path/hash map excludes the receipt itself and later-stage files;
there are exactly two publication gates, with no recursive receipt publication.

## Collect one paired batch per invocation

The fixed order is 2020-H1 through 2024-H2, repetition 1 through 4 within each
state. Immediately before each invocation, the root reads current account quota.
Substitute that actual percentage, UTC timestamp and its provenance below:

```powershell
python -m alpha_research_rl.astra_revision_study collect-pair --task 2020-H1 --repetition 1 --receipt .local/astra-matched-prefix-v1/publication-preparation.json --quota-remaining 80 --quota-checked-utc ACTUAL_UTC_TIMESTAMP --quota-provenance "Root's current account-limit observation"
```

The example percentage is a placeholder, not a saved quota observation. A known
remaining percentage must be strictly above 5 and the observation at most 60
seconds old, not in the future, at setup and at each dispatch. Unknown/stale
quota returns `WAIT_QUOTA` without an actor call. A completed setup followed by
such a wait remains recorded and counted; a later invocation needs fresh quota.
At or below 5, the version becomes `INCOMPLETE`. Expiry after one paired call
has launched also terminates the version and retains the launched result;
there is no replacement call. Explicit operator cancellation uses:

```powershell
python -m alpha_research_rl.astra_revision_study stop --reason "Concrete operator reason"
```

Each invocation makes at most two separately invoked, fresh ephemeral provider calls
using frozen Astra/ultra/default-tier flags and a neutral empty working
directory. It retains full private streams under the one contract-bound
`.local/astra-matched-prefix-v1/` tree. Public evidence retains the responses,
prompt bytes and hashes, safe provider summaries, reported token fields,
dispatch times, quota observations and durable start/completion records.
Reasoning tokens remain separate from output tokens. Source hashes identify
the requested provider contract; they do not attest hidden hosted behavior.

Historical feedback is reused by exact task/AST identity when available;
otherwise only `FinancialTask.feedback_score` runs. Task construction and its
two original-probe checks are counted separately. Structural dependency lag is
limited to 60 for every generator without changing the frozen DSL. Invalid,
over-limit, unusable and duplicate proposals keep their charged slots. There
is no repair, retry, redraw or search for a replacement. Each invocation also
records the predeclared copy, temporal edit and seeded grammar packet for its
state/repetition. The four repetitions do not form a best-of-four selector.

After forty successful paired batches (80 hosted calls plus 120 cheap slots):

```powershell
python -m alpha_research_rl.astra_revision_study freeze
python -m alpha_research_rl.astra_revision_study publication-files --stage submissions
```

Freeze reconstructs all 200 slots, directions and historical choices and writes
exact mirrors to execution `SUBMISSIONS.json` and
`results/astra_matched_prefix_v1_submissions.json`. It still neither parses nor
joins old future outcomes. Publish the returned Gate 2 path map, then verify:

```powershell
python scripts/verify_astra_revision_publication.py --stage submissions --commit FULL_40_CHARACTER_COMMIT
```

## Assess the fixed bank once, then use saved replay

Only after validating Gate 2 may the driver replay the old pool, join its
outcomes and plan new unique future assessments:

```powershell
python -m alpha_research_rl.astra_revision_study assess --receipt .local/astra-matched-prefix-v1/publication-submissions.json --max-jobs 200
```

Exact task/AST/fixed-direction cache matches reuse the original evaluated
spelling and outcome provenance. They are never reevaluated for verification.
At most 200 new unique evaluations run. A lower `--max-jobs` explicitly creates
a clean completed prefix; another explicit invocation can continue it under
the same receipt and frozen identities. An exclusive execution claim prevents
simultaneous invocations. Every new job has durable `STARTED` before task setup
or evaluation and `COMPLETED` only after outcome validation. Any ambiguous
start, interruption, integrity error or failed write permanently blocks this
version. There is no automatic retry, overwrite or recovery by deleting files.

The final result is `results/astra_matched_prefix_v1.json`, an exact mirror of
`artifacts/astra-matched-prefix-v1/execution/COMPLETE.json`. It contains all
200 ordered resolved rows, unique-key provenance, setup/call/duplicate counts,
provider usage and `analysis`. Completed execution is replay-only. Inspect the
report and public export before publishing; do not publish the private stream
directory or market archive.

The primary endpoint is truthful-minus-masked candidate Q (oriented future IC,
or -1 for a failed candidate); the secondary is fixed-selector improvement G
over the historical prefix winner. Copy reuses baseline Q and has G=0. Terminal
cost is .03, baseline cost .02, and incremental cost .01. Every generator has
40 charged slots, with all ten states and five years retained. Conditional
generation MCSE uses within-state variation across four hosted draws; it is not
market-period uncertainty. These are development-data comparisons. Common
probes can reveal some masked feedback indirectly, and repeated calls need not
be independent. Passing the numerical allocation rule authorizes no automatic
new study and is not proof of general alpha or profitability.

## Exact bytes and failure boundaries

The plan, guide, mirrored task JSON, prompts and public ledgers are evidence.
Use the matching checkout and preserve exact bytes; the repository disables Git
text conversion for frozen prompt files. Computed arithmetic alone uses the
registered finite 1e-12 tolerance. Retained evidence, types, fixed costs, source
and file identities are exact. Saved replay needs public JSON/text and source
bytes only; preparation and execution additionally enforce the pinned local
runtime and raw archive identity. Synthetic tests cover the two gates, full
population, cache reuse, interrupted calls, quota expiry, write failures and
portable replay without reading real market data or invoking a model.
