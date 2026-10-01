# Constructed-feedback curriculum v2 results

The predefined 80% both-sides-correct gate **failed**. The trained adapter passed
8/24 pairs (33.3%), versus 0/24 for its SFT-v1 parent. Curriculum training stops
here; this registered study includes no extra epochs, checkpoint selection, or
RL continuation after the failed gate. This is controlled action-conditioning evidence, not a financial or
factor-discovery result.

## Frozen training and evaluation

Training continued the SFT-v1 adapter for the registered two epochs: 192 explicit
constructed-feedback examples, 384 updates, seed 47, AdamW learning rate 1e-4,
weight decay 0.01, gradient clipping 1, and completion-token-normalized loss.
Train families and seeds 5000–5031 were disjoint from development families and
seeds 6000–6011 before candidate permutations. No hidden assessment target was
present in this dataset. Mean per-token training loss was 0.246644 in epoch one
and 0.098828 in epoch two; these training losses do not establish transfer.

The final registered adapter digest changed from
`46e89788c8bc2a8cef11ba401f8729ea94df2c103598319772b2919bf2047148` to
`de61809e546eaaa68052309ecf21e23b0f6841db1560584281977faaeb23e185`.
The exact retained training dataset SHA256 is
`4e6e3d6b49f69275d244e52aec3d28ec58b74776419cfa82e4c77ebf2bbe4537`.

Each actor was evaluated once, greedily, on the same 24 held-out pairs / 48 sides,
with a 64-token action cap and seed 53. The development dataset SHA256 was
`a1fe071ed154334fbc3040fb036e732a5fb3ff48fb689caf7170531b5a950f40`
for both evaluations. A pair changes only visible feedback scores. Action accuracy
requires the exact action/ID and canonical AST where an expression is present.

The two aggregate package source hashes differ because independent financial
modules and a sampling probe were added between evaluation starts. Root confirmed
that the actor, curriculum, and evaluator source were unchanged across both
corrected evaluations. The individual manifests retain the hashes; the mismatch
must not be represented as identical entire-repository snapshots.

## Results

| Metric | SFT-v1 parent | Curriculum-v2 |
| --- | ---: | ---: |
| Both sides correct | 0/24 (0.0%) | 8/24 (33.3%) |
| Correct individual actions | 0/48 (0.0%) | 30/48 (62.5%) |
| Predicted action changes within pair | 0/24 (0.0%) | 12/24 (50.0%) |
| Selection/stop actions correct | 0/24 (0.0%) | 20/24 (83.3%) |
| Generation actions correct | 0/24 (0.0%) | 10/24 (41.7%) |
| Selection pairs both correct | 0/12 (0.0%) | 8/12 (66.7%) |
| Generation pairs both correct | 0/12 (0.0%) | 0/12 (0.0%) |
| EOS terminated | 48/48 (100%) | 48/48 (100%) |
| Terminated JSON objects | 48/48 (100%) | 48/48 (100%) |

By held-out family, curriculum-v2 passed 3/12 mixed-composition pairs and 5/12
restricted-return pairs. The 80% threshold would require at least 20/24 pairs;
the observed eight pass neither that overall gate nor an 80% category-specific
gate. These 24 pairs share twelve underlying constructed tasks, so their sides
and categories are not independent replications or a significance test.

The parent emits `screen` on all 48 sides, despite the fixtures already containing
four screened candidates. The new adapter emits 14 selects, ten stops, and 24
mutations. All six required stop actions are correct. Four of eighteen required
selects become stop; every one of those errors has target candidate ID 0. All
fourteen required selects for other IDs are correct. The association is observed;
the artifacts do not establish why the model treats candidate 0 differently.

Every one of the twelve moderate-strength generation cases should propose, but
the adapter mutates instead. It also mutates in all twelve high-strength cases,
of which ten have the expected expression. Thus it learned to compose some new
parent expressions but did not learn the feedback-dependent propose/mutate branch.
The sole changed generation pair changes to an incorrect expression; changed
strings therefore must not be counted as successful evidence use.

A separate CPU check with the actual bounded DSL found 21/24 generated expressions
legal for the fixture's supported features. The three illegal expressions are
`dev:1:generation` right and `dev:3:generation` left/right; they use an expression
where a temporal function requires a literal integer lookback. JSON validity is
therefore distinct from executable-expression validity. Eight distinct canonical
ASTs were emitted, including invalid forms. No market data or assessment outcome
exists for these fixtures, so neither legality nor exact-target novelty measures
useful factor discovery.

## Every pair inspected

Each row below represents one selection pair and one generation pair: all 24.
SFT-v1 passed neither pair in every row.

| Task index | Held-out family | Selection both correct | Selection action changed | Generation both correct | Generation action changed |
| --- | --- | --- | --- | --- | --- |
| 0 | mixed composition | No | Yes | No | No |
| 1 | mixed composition | Yes | Yes | No | Yes, incorrect expression |
| 2 | mixed composition | Yes | Yes | No | No |
| 3 | mixed composition | No | Yes | No | No |
| 4 | mixed composition | No | Yes | No | No |
| 5 | mixed composition | Yes | Yes | No | No |
| 6 | restricted returns | Yes | Yes | No | No |
| 7 | restricted returns | Yes | Yes | No | No |
| 8 | restricted returns | No | No | No | No |
| 9 | restricted returns | Yes | Yes | No | No |
| 10 | restricted returns | Yes | Yes | No | No |
| 11 | restricted returns | Yes | Yes | No | No |

## Sampler correction and precision limits

The first baseline attempt was mislabeled greedy because Transformers merged
Qwen-specific sampling defaults into a fresh `GenerationConfig`. Its original
output, constructed data, and supersession note are preserved under the ignored
run's diagnostics directory. That attempt is excluded from the table above.
Both reported evaluations were rerun after root fixed `use_model_defaults=False`
and passed explicit sampler kwargs. Three tiny CPU GPT-2 regression tests verify
effective greedy/full-softmax configurations and raw-versus-processed generation
score equality. Neither training example generation nor the 384 teacher-forced
SFT updates used the affected sampler.

Curriculum training and the corrected greedy evaluations retain BF16 model
precision. The separately saved Qwen sampling-law probe measured processed/raw
cached logits equal, but cached-generation versus full-forward recomputation had
maximum token log-probability difference 0.464909 and sequence difference 0.487569.
This is a finite-precision execution difference, not the configuration-merge bug.
It limits exact-likelihood claims about the earlier BF16 RL implementation.
Curriculum-v2 performs SFT only and makes no REINFORCE or exact policy-gradient
claim. These measured greedy results apply to the recorded BF16 execution;
they are not a precision-invariant guarantee.

## Artifacts and decision

- `results/curriculum_training_v2.json`: public-safe training report, added frozen
  evaluation summaries, and explicit failed-gate/stop decision; no weights.
- `artifacts/development/sft-curriculum-probe-v2.json`: corrected parent outputs.
- `artifacts/development/trained-curriculum-probe-v2.json`: corrected trained
  outputs, expected actions, and all pair judgments.
- Corresponding `.constructed-data.json` files: exact controlled development
  fixtures. The ignored run retains exact constructed training data.
- `docs/audits/2026-10-01-generation-config-merge.md` and
  `tests/test_generation_config.py`: sampler finding and CPU regressions.

The supported result is partial held-out selection/stop conditioning alongside
failed generation-branch transfer and a residual candidate-ID error. The gate
fails, so this run ends as a documented mixed result. It does not justify more
training on inspected development pairs, RL scaling of this curriculum, financial
performance claims, or claiming that a full sequential research policy was learned.
