# Presentation-integrity implementation review

Reviewed 2026-10-01 at approximately 12:59 UTC. The reviewer authored the
[narrow design note](../research-validation-benchmark-design.md), but did not
author `presentation_integrity.py`. This is internal AI-assisted, source-first
implementation review, not independent design review or external human peer
review. No model, tokenizer, market-data, financial-scoring or Git operation was
performed in this review.

**Disposition: no unresolved blocker within the supplied-evidence contract.**
Source inspection confirms direct UTF-8-byte/tuple equality, unconditional byte
comparison across namespaces, deterministic grouping and witnesses, explicit
missing/incomparable token evidence, and rejection of inconsistent same-prompt,
same-namespace encoding. Literal whitespace and Unicode are preserved. The CLI
strictly loads JSON, creates output exclusively and distinguishes conflicts from
input/file errors.

## Independently executed checks

The reviewer created and ran
[`tests/test_presentation_integrity_review.py`](../../tests/test_presentation_integrity_review.py):
**12 passed in 0.07 seconds; Ruff passed.** The tests cover:

- Independently constructed all-pairs equality partitions, exact cross-split
  groups/witnesses, unchanged input records and 120 input-order permutations.
- Equal bytes across different namespaces, and different bytes with equal tokens
  inside one namespace; missing and incomparable evidence remains qualified.
- CRLF versus LF, composed versus decomposed Unicode, leading/trailing spaces,
  letter case and embedded NUL, all preserved through JSON loading.
- Forced collisions of every generated digest without falsely merging unequal
  prompts or token sequences. Actual equality does not depend on a digest match.
- Contradictory tokens for the same prompt/namespace, within and across splits.
- Moving one of eight aliases to another split: exactly one conflicting group
  and seven equal cross-split pairs. Restoring the assignment preserves all
  records and reproduces the clean report.

These are original artificial fixtures with supplied artificial token IDs.
The reviewer did not execute the separate 1,152-row alias artifact generator.
Its expected 144 groups of eight are a previously known mathematical regression
target, not a new empirical finding from these twelve tests.

## Identities and limits

| Reviewed file | SHA-256 |
| --- | --- |
| `src/alpha_research_rl/presentation_integrity.py` | `92906a097436087aa4212af838f83d572851d32ad854dae539543fdd0ff7af5b` |
| `tests/test_presentation_integrity_review.py` | `ade8d5a743a2428159054bfc5b471c2cd6c9e08a7edad0a85613bc18dc59d73b` |

The checker can establish exact conflicts only for supplied records. A caller
can omit records, provide incomplete prompts, or misdeclare a tokenizer namespace;
this tool does not attest those inputs. Namespace separation does not establish
token disjointness, and byte-only evidence does not establish token coverage.
Equal inputs within a split are retained and counted, not independent tasks.

No absence-of-leakage, semantic novelty, held-out generalization, pretraining
contamination, hidden-host-context, financial value or agent capability claim
follows from a clean report. Complete deterministic validation is sufficient for
this declared task; this review supplies no reason to spend hosted-model calls.
