# Research-validation tooling: exact presentation split integrity

**Status, 2026-10-01:** the narrow static-validator iteration described below is
implemented and reviewed. The core checker passed the bounded review recorded
below; root then executed the full alias-bank regression. Its
[result and reproduction guide](presentation-integrity.md) records all 1,152
rows, both split constructions and the single-alias fault. A broader fault-diagnosis benchmark and any hosted
agent experiment are **not adopted**. Hosted-call budget: **zero**. This design
does not reopen the failed financial studies or the deferred query-policy study.

The useful contribution is a reusable check for a demonstrated evaluation-design
failure: different transformation IDs can expose exactly the same input to an
actor in different splits. A complete deterministic check should solve this
problem. That is the desired outcome, not a reason to hide information, impose
artificial tool prices, or manufacture harder cases for an LLM.

## Why this gap, rather than another broad benchmark

The repository already has concrete validation work in the other proposed fault
families. Their provenance must not be confused with actual compromised results.

| Failure class | Existing evidence and checks | Decision for this iteration |
| --- | --- | --- |
| Temporal leakage and fabricated support | An [independent artificial-fixture audit](audits/financial-analysis-independent-source-review.md) found that mutually consistent checkpoint metadata could still violate the named half-year, date cap and purged support. Absolute chronology/support checks and 25 artificial tests subsequently passed, before actual analysis. | Preserve the existing regression suite; do not describe the artificial finding as observed financial leakage. |
| Effective sampling-law mismatch | A [documented generation-config merge](audits/2026-10-01-generation-config-merge.md) made an intended greedy curriculum baseline stochastic. The affected output was superseded; explicit settings and [tiny random CPU-model checks](../tests/test_generation_config.py) cover effective configuration and full-softmax scores. | Reuse those checks. A finite-logit toy would not replace the actual library-boundary regression or numerical-equivalence checks. |
| All-attempt metric interpretation | The [financial analysis](financial-proposal-results-v1.md#primary-reward-and-validity-results) already preserves every attempt and decomposes mean reward as `-1.01 + valid_fraction + all_attempt_IC_contribution`. Conditional usable IC has a different denominator. | No new metric implementation. The risk of misinterpretation is real, but the published decomposition is not a discovered denominator bug. |
| Actor-visible split aliases | A [static audit](audits/next-mechanism-design-review.md) found 1,152 raw transformations but only 144 distinct visible kernels, with eight aliases each. Raw-ID split separation therefore does not imply visible-input separation. | Implement a reusable exact-input checker and an independently constructed alias regression. |

Broader ML-engineering and replication benchmarks already exist:
[MLE-bench](https://openai.com/index/mle-bench/) covers 75 ML-engineering
competitions, while [PaperBench](https://openai.com/index/paperbench/) evaluates
research-paper replication through detailed rubrics. This small tool is not a
replacement or a comparable capability benchmark. Its contribution is a precise,
reusable contract check with executable counterexamples; no novelty claim rests
on using deterministic rather than model-based grading.

## Input boundary and proposed API

The implementation owner will expose `check_presentations(records) -> dict` in
`src/alpha_research_rl/presentation_integrity.py`. The command-line envelope is
`{"schema":"actor-visible-presentations-v1","records":[...]}`. Each record has
exactly `id`, `split`, and `prompt`, all nonblank strings, with an optional complete
`tokenization` object containing:

- `namespace_sha256`: a lowercase SHA-256 identity for the caller's tokenizer,
  template and encoding configuration;
- `token_ids`: a nonempty ordered list of exact nonnegative integers. Booleans
  are not integers for this contract. Empty lists and incomplete optional objects
  are errors; absent token metadata is explicitly unchecked.

IDs must be unique. The input is a finite, declared bank of complete rendered
text prompts at one stated decision boundary, not fragments, hidden simulator
states, raw transformation IDs, or a model's responses. The caller is responsible
for supplying the actual surface it intends to compare. If it supplies only an
initial prompt, the result concerns that initial surface; it says nothing about
later tool messages or other host-provided context.

Byte identity means the literal UTF-8 encoding of `prompt`. There is no trimming,
newline conversion, Unicode normalization, JSON reformatting inside the prompt,
or removal of instructions. CRLF and LF, or composed and decomposed Unicode,
remain distinct unless separately supplied token evidence makes them collide.
Neither split labels nor tokenizer namespaces may hide a byte collision.

Token identity means exact sequence equality **within the same namespace**.
Different namespaces are incomparable, not evidence that their inputs differ.
The checker consumes saved sequences; it does not load a tokenizer or attest
that these sequences were actually sent to a model. A namespace is a caller
declaration, not an independently verified fingerprint. Identical prompt bytes
with conflicting sequences in the same deterministic namespace are inconsistent
evidence and must not quietly become two clean groups.

Reports must distinguish byte coverage from token coverage, including the number
of supplied sequences and each namespace's coverage. Absent or partial token
metadata, or multiple incomparable namespaces, cannot support an unqualified
claim of global token disjointness. A byte-only pass is allowed and must say it
is byte-only. Structural errors are errors, not a successful empty report.

## Detection, evidence and recovery boundaries

The checker groups literal equal prompts and, separately, equal token sequences
within namespaces. It returns deterministic, ID-sorted group membership, split
membership and cross-split witnesses. Hashes are compact evidence identities;
group equality must be established from the actual bytes/sequences, not by
trusting a supplied hash. Default reports omit raw prompts and token arrays.

A finding identifies the affected IDs and the equality relation that violates
split separation. Duplicates entirely within a split are counted but do not
violate cross-split separation. A record cannot be silently discarded to improve
the result. Total input records, covered records and groups remain visible.

The checker does not automatically repair a research split. For an unpublished
synthetic fixture, assigning each connected component of established equality
relations to one split is a valid recovery demonstration. Preserve every ID and
every prompt/token byte; only split metadata changes. Recheck the recovered bank
with an independent comparator. There can be several valid assignments: matching
one privileged reference patch is not the recovery oracle. Grouping does not
guarantee desired split sizes, and deleting duplicates or relabeling a used
evaluation set as fresh holdout is not an acceptable repair.

## Smallest useful regression bank

`scripts/check_presentation_aliases.py` will reconstruct only the old synthetic
presentation family: all 24 column permutations, six row permutations and eight
row-wise bit flips of the integer kernel with entries 9, 1 and 5 over denominator
10. Canonical labels and fixed literal formatting produce 1,152 prompt records.
This is a known mathematical regression target, not a newly preregistered
discovery or an execution of the query policy.

The required regression is:

1. **Raw-ID split fault:** assign rows by enumeration index modulo three. Raw IDs
   remain unique, but the reference comparator must exhibit cross-split prompt
   aliases. Do not hard-code an unverified number of conflicting groups.
2. **Recovery/clean bank:** sort complete visible-prompt groups and assign group
   index modulo three. Retain all 1,152 records, 144 groups of eight, and 384 rows
   in each illustrative split; independently verify no cross-split equality.
   This repairs synthetic metadata, not an existing study's training/test history.
3. **Single-fault isolation:** in a small regression derived from the clean bank,
   move one member of one eight-member group to another split, preserving IDs and
   prompt bytes. Exactly that group must be flagged. Its one-versus-seven split
   creates seven discordant equal pairs.

Small boundary fixtures supplement this bank: within-split duplicates, genuinely
different literal bytes, different text with equal supplied tokens, partial token
coverage, incomparable namespaces, conflicting same-namespace evidence, malformed
or duplicate IDs, and CRLF/Unicode preservation. Token fixtures are explicitly
artificial. They do not claim compatibility with an actual tokenizer.

The independent regression oracle should compare rendered bytes directly without
calling the production grouping helper. It separately enumerates the integer
matrices, confirms the 144/eight multiplicity, and verifies that canonical
rendering preserves this partition. A direct partition comparison plus exact
cross-split witness checks is sufficient; an optional pairwise reference would
use 663,552 unordered comparisons. Expected counts alone are insufficient: a
checker that returns the right count but the wrong members must fail. Recovery
also requires record-by-record preservation and absence of new violations.

## Strong cheap checks, costs and stop rule

The relevant baseline is complete deterministic validation over the entire bank,
using hash-indexed equality plus exact comparisons or sorting. The independently
constructed partition is the correctness reference. A raw-ID check is included only
to exhibit the original failure, not as a competitive baseline. An adaptive
diagnoser has no privileged accuracy role when the complete finite inputs and
equality rules are available cheaply.

Acceptance requires exact witness/group agreement, clean-bank preservation,
rejection of malformed evidence, and explicit incomplete-token coverage. Record
input bytes/counts, comparisons where available, elapsed CPU/wall time and peak
memory if measured. Do not convert these into invented financial or abstract
tool costs. Model inference, market-data reads, financial evaluations and training
updates remain zero. Test runtimes are observed engineering measurements, not
statistical repetitions or capability scores.

If the complete deterministic method solves this family, publish the validator,
synthetic regression and limitations, and stop. Do not launch hosted diagnosis
calls to prove that a language model can repeat the equality check. A later agent
benchmark would need a separately justified, naturally occurring residual task
that strong static and deterministic diagnostic baselines fail under fair access
and costs, plus independent semantic repair oracles. Obfuscating files or charging
artificially high prices for complete checks would not establish that need.

## What passing establishes

Passing establishes absence of the declared exact cross-split collisions in the
supplied finite text bank, with separately qualified token coverage. It does not
establish semantic novelty, distribution shift, absence of training/pretraining
contamination, hidden-context equality, dataset independence, actual model use,
financial predictive value, or general research ability. In particular, 144
unique presentations still describe one constructed mechanism.

The design author previously authored the matched-prefix protocol and parts of
the orchestration; that participation is not an external peer review of this
project.

## Subsequent core implementation review

At 2026-10-01 12:59 UTC, this design author reviewed the core checker's source,
written by a different agent, and ran the new
[`test_presentation_integrity_review.py`](../tests/test_presentation_integrity_review.py):
**12 passed in 0.07 seconds; Ruff passed.** This is independent implementation
review within the project, not independent review of this author's design or
external human peer review. No unresolved core-contract blocker was found.

The tests independently construct pairwise equality partitions and witnesses,
check 120 permutations of a mixed-evidence population, preserve six literal
UTF-8 distinctions through JSON loading, and force all report digests to collide
without merging unequal inputs. They also test incomplete/incomparable token
evidence, inconsistent encoding rejection, and a single moved alias producing
exactly one conflicting group and seven equal cross-split pairs. Recovery retains
every record and restores the clean report. No model, tokenizer or market operation
was performed. These checks do not execute the separate 1,152-row regression.

Reviewed source SHA-256:
`92906a097436087aa4212af838f83d572851d32ad854dae539543fdd0ff7af5b`.
Independent test-file SHA-256:
`ade8d5a743a2428159054bfc5b471c2cd6c9e08a7edad0a85613bc18dc59d73b`.
