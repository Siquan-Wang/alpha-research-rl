# Bounded expression proposal and mutation

`ResearchEnvironment(..., allow_generation=True, max_candidates=64)` enables
proposal actions. Generation is disabled by default, so existing fixed-pool
policies retain their candidate, evidence, and history schema. The candidate
limit is an integer from 1 through 64, includes initial candidates, and is fixed
before an episode starts. Initial candidates may be empty in generation mode.

Accepted action forms are:

```json
{"action": "propose", "expression": "ts_mean(returns, 5)"}
{"action": "mutate", "candidate": 0, "expression": "delta(returns, 3)"}
```

Mutation proposes a replacement expression derived by the policy and records
the existing parent candidate. It appends a new candidate, preserving the
original expression. The environment does not assert that the mutation is
semantically related to its parent. No additional fields are accepted, and
mutation requires a valid integer parent ID (booleans are invalid).

Both action types cost two budget units, including invalid, disabled, and
duplicate attempts. An attempt with one unit left consumes that unit, acquires
nothing, and finishes the episode. Unknown actions cost one unit. Valid stop
remains free and terminal; stepping after termination is forbidden.

Validation uses the existing bounded DSL interpreter on the feedback-visible
panel prefix. It does not execute generated Python, inspect assessment rows,
or compute screening scores. The DSL limits expression length, AST size/depth,
lookbacks, names, and operators. Undefined numerical operations yield missing
values; a syntactically valid constant or all-missing expression can be proposed
but cannot be selected without usable screening evidence.

Duplicate detection compares canonical Python ASTs with positions omitted,
including every initial and generated expression. Whitespace and redundant
parentheses are duplicates. Algebraically equivalent expressions with different
ASTs are not deduplicated. Expression validation precedes duplicate detection;
the candidate-count limit is checked first. Invalid expressions return only a
fixed reason code, never raw exception strings.

Accepted expressions receive consecutive stable IDs and appear in the normal
`candidates` list. Proposal supplies no evidence or orientation. Policies must
spend a separate screening unit. Selection requires finite feedback mean IC,
paired-cell coverage of at least 0.8, and at least
`max(ceil(0.8 * block_length), min(20, block_length))` dates with defined IC.
This excludes constant cross sections from qualifying as valid dates even when
every cell is finite. The maximum selected pool remains three.

Only generation-enabled observations add these public fields:

```json
{
  "generation": {"enabled": true, "max_candidates": 64,
                 "proposal_cost": 2, "mutation_cost": 2},
  "provenance": {"0": {"kind": "initial", "parent": null},
                 "1": {"kind": "mutate", "parent": 0}},
  "supported_features": ["close", "volume", "returns"]
}
```

`supported_features` also appears for fixed-pool sources that explicitly restrict
feature availability. Only this safe schema is carried into the visible panel;
arbitrary panel metadata is excluded. For example, return-only portfolio data
cannot acquire a volume expression through proposal or screening.

Generation history records action, new candidate ID (null on failure), bounded
attempted expression, parent ID, charged cost, status, and reason. Existing
screen/stability/select/stop records retain their fields. Reset discards generated
candidates and restores the initial pool, budget, and empty evidence/history.

Terminal training reward still uses equally weighted feedback-oriented ranks
on a common finite asset universe. The same paired-cell coverage and valid-date
count requirements apply to assessment; failing either yields zero predictive
score, and spent-budget cost remains charged.
Assessment metrics never appear in observations or info. This API enables a
policy to propose factors; its existence is not evidence that an LLM policy has
been trained or improved, nor that synthetic factors predict financial markets.
