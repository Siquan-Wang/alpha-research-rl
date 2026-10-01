# Check what the actor actually sees across splits

A different task ID does not guarantee a different model input. In the
repository's constructed query task, 1,152 raw permutations collapse to only
144 distinct visible likelihood tables, with eight aliases each. That fact
was previously recorded in a [design audit](audits/next-mechanism-design-review.md).
The new checker makes exact presentation collisions an executable validation
step. It requires no model, tokenizer download or market data.

This is research-engineering validation. It neither trains a policy nor
evaluates Astra on the constructed task. The existing financial experiments
and their stopped allocation rules are unchanged.

## Use the final rendered input

Supply one record per presentation. `prompt` must be the complete final text
that the caller actually presents to its actor, after rendering and any
preprocessing. Include all actor-visible instructions, tool definitions and
action mappings in that serialization; an earlier template or a selected
observation field is insufficient. The checker cannot independently attest
what a hosted service received or added internally.

```json
{
  "schema": "actor-visible-presentations-v1",
  "records": [
    {"id": "case-a", "split": "train", "prompt": "Choose between A and B."},
    {"id": "case-b", "split": "validation", "prompt": "Choose between A and B."}
  ]
}
```

These two records have different IDs but identical visible input. The checker
reports a cross-split collision. It preserves whitespace, newlines and Unicode
in the supplied text rather than silently normalizing them.

Run the standard-library-only interface from an installed checkout:

```bash
python -m alpha_research_rl.presentation_integrity \
  --input presentations.json --output NEW_REPORT.json
```

The output must be a new path. Conflicts produce a failing exit status even
when a diagnostic report is written; malformed evidence is rejected separately.
Reports contain hashes, counts and record-ID witnesses rather than copying
raw prompts. They are still local artifacts whose identifiers may matter to
their owner; this command performs no publication or network operation.

For an in-memory caller:

```python
from alpha_research_rl.presentation_integrity import check_presentations

report = check_presentations(records)
```

The caller remains responsible for an expected population manifest. Checking
the records supplied to this function cannot establish that omitted records
never existed. Within-split duplicate groups remain reported and are not
automatically errors: planned repeated calls may deliberately share an input.
They do not create additional independent task mechanisms.

## Optional token evidence has a separate scope

A record may include `tokenization`, containing a nonempty `token_ids` list
and `namespace_sha256`. The latter is the caller's explicit fingerprint for
the tokenizer and serialization/template context. The checker compares token
sequences only inside the same supplied namespace. It does not tokenize text,
verify a tokenizer installation, or establish that these were the actual
tokens sent to a provider.

| Evidence | What can be checked | What remains unresolved |
|---|---|---|
| Complete supplied prompt text | Exact UTF-8 input collisions across declared splits | Different strings can still have the same semantics or later preprocessing |
| Supplied token IDs in one namespace | Equal recorded token sequences despite different text | Accuracy and completeness of the supplied tokenization record |
| Missing token IDs | Prompt-level checks only; token scope is unchecked | Token-level overlap |
| Multiple tokenization namespaces | Collisions inside each comparison domain | Cross-namespace equivalence and any hidden context |

Partial token coverage must not become a clean token-level result for the whole
bank. Likewise, distinct hashes do not establish statistical independence,
unseen mechanisms, absence of pretraining exposure or a valid evaluation split.

## A deterministic regression with known aliases

The accompanying synthetic regression enumerates every candidate permutation,
query permutation and response-bit flip of the already published four-state
kernel. It independently groups exact integer likelihood matrices and fully
rendered prompts, then checks that those partitions agree.

It compares a naive assignment by raw enumeration index with assignment by
complete visible-presentation group. Both retain all 1,152 records. The latter
keeps all eight aliases together; it changes split membership, not the task
mechanism or the number of unique inputs. No actor is trained or evaluated,
and the terms train/validation/test are labels in a regression fixture.

The expected 1,152-to-144 collapse is known in advance. Reproducing it is an
engineering regression check, not a new empirical discovery. A deterministic
exact checker is the appropriate baseline; this task provides no reason to
spend additional hosted calls on an LLM judge.

The actual exhaustive regression completed on 2026-10-01:

| Split construction | Records retained | Cross-split equal-input groups | Equal cross-split record pairs |
|---|---:|---:|---:|
| Raw enumeration index modulo three | 1,152 | 144 | 2,952 |
| Whole visible-input groups | 1,152 | 0 | 0 |
| Move one alias out of its correct group | 1,152 | 1 | 7 |

The first two banks each retain 384 records per illustrative split. Moving one
alias produces split sizes 383, 384 and 385; the remaining seven aliases stay
in their original group. The full group membership and collision witnesses
match a separately constructed matrix/byte reference. No tokenizer was invoked,
so every token-level comparison remains **UNCHECKED**.

The [saved result](../results/presentation_alias_regression_v1.json) has SHA256
`1a11f533c306f3c46f6de7e077c566d3f903c8b694cb9826547217827d706ace`.
It also records the exact checker and fixture source hashes. Reproduce into a
new path with:

```bash
python scripts/check_presentation_aliases.py --output NEW_REPORT.json
```

Root ran the combined author, independent reviewer and regression suites:
**72 tests passed in .28 seconds; Ruff passed.** A subsequently added test
that compares the published artifact with a complete deterministic rebuild
passed separately on both the author and root runs. The normal regression CLI
completed successfully afterward. The [source review](audits/presentation-integrity-review-v1.md)
covers literal-byte preservation, incomplete token evidence, namespace bounds,
deterministic witnesses and forced hash-collision behavior. Passing this finite
regression is not proof that arbitrary datasets are free from leakage.

The [design record](research-validation-benchmark-design.md) explains why the
broader agent benchmark was not adopted. Existing temporal, sampling-law and
all-attempt metric tests are preserved rather than replaced by this checker.
