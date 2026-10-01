# Financial training evidence audit — 2026-10-01

The saved records support **96 SFT updates and 31 actual RL optimizer steps**
from a common SFT parent. No blocking inconsistency was found. This audit
examines training evidence only; no transfer output was opened and no GPU
inference or training was performed.

## Evidence checked

Read the original training reports, entry manifests and reload checks under
`models/runs/financial-sft-v1`, `financial-rloo23-v1` and
`financial-rloo29-v1`. Independently recomputed counts, leave-one-out
advantages, quality-gate predicates, task order, reward/feedback orientation,
parameter-digest chains and public-export hashes. Each original JSON object and
its byte-level SHA256 match the corresponding entry in
[`results/financial_training_v1.json`](../../results/financial_training_v1.json).
The export contains no host username or absolute Windows path.

| Run | Training seed | Updates | Proposal groups | Proposals | Valid proposals | Quality groups |
|---|---:|---:|---:|---:|---:|---:|
| Financial SFT | 61 | 96 | — | — | — | — |
| RLOO seed 23 | 23 | 16 | 16 | 64 | 63 | 16 |
| RLOO seed 29 | 29 | 15 | 16 | 64 | 64 | 15 |

SFT has three complete epochs of 32 distinct training tasks and 2,293,760
trainable parameters. Both RL initial digests equal the SFT final digest:
`2de3acf5ae1f6dee2b5b335f083e2c2b5e76f224a1f1de7eb2b151d709a01c53`.
Every RL group continues the preceding digest chain; every recorded optimizer
step changes that digest. The seed-29 last group has identical rewards, exact
zero advantages, zero gradient norm, no optimizer step and an unchanged digest.

For all 32 groups, the independent calculation
`A_i = r_i - sum(r_j for j != i)/3` agrees with saved advantages within
`1.11e-16`. Current code minimizes the four-sample mean of
`-A_i * completion_log_probability`, clips gradients at one, and applies
AdamW at `1e-5` with zero weight decay. It recomputes each completion's full
autoregressive likelihood, including EOS and excluding prompt tokens, before
one update; there is no replay, KL or entropy term.

Both seeds follow their deterministic random permutation of the same 16
episodes: H1 in even years and H2 in odd years, 2002–2017. Every logged boundary
purges five signal rows before the next half-year. Both runs pass the
predeclared eight-group gate using legal distinct ASTs with valid future-IC
range greater than `1e-4`, so completing 16 groups matches the plan. Syntax
failure spread alone is not counted as quality exploration. These later-period
ICs enter gradient updates and are **training rewards**, not holdout evidence.

## Prompt, sampler and reload evidence

Using only the local tokenizer, reconstructed all 32 actual SFT prompt/target
token traces and all 128 sampled RL prompt traces exactly. SFT targets include
EOS. Actual actor observations contain supported fields, lookback/horizon/cost
constants and the two probe evidence bundles; they contain no assessment
metrics, task identifier or year. The SFT teacher's additional 12-formula
feedback access remains explicitly privileged.

All three manifests declare the pinned Qwen3-0.6B revision
`c1899de289a04d12100db370d81485cdf75e47ca`, the registered French snapshot hash,
FP32, disabled TF32 and disabled model-default merging. The sampler declares
temperature 1, top-p 1 and top-k 0. Saved roundtrip records have identical
before/after parameter digests and completion log probabilities, with absolute
log-probability difference zero, for each final adapter. Their digests match the
training-report final digests. This checks the retained records; it is not a
new independent reload execution or a universal numerical-equivalence claim.

## Provenance limits and interpretation

The seven current relevant files (`financial_training.py`, `financial_policy.py`,
`financial_tasks.py`, `llm.py`, `training.py`, `dsl.py`, `evaluation.py`) are
byte-identical to Git revision `1bab1207636f3250eaedf705808f63eea6a07ff3`,
which all three run manifests identify. Root's execution record reports no
edits to those files between SFT and RL. Whole-package source hashes differ
between SFT, RL and this audit because additional modules were introduced.
The entry manifests contain package hashes, not per-file source snapshots;
Git/current equality and the execution record therefore do not constitute a
cryptographic reconstruction of every file present during each run.

The quality gate is an engineering check, not evidence of useful adaptation.
`ts_mean(returns,60)` and `ts_std(returns,20)` account for 102 of the 128 training
proposals; legal AST diversity can still conceal rank aliases or a concentrated
learned prior. Both RL seeds share one parent and historical episodes. Parameter
updates, valid outputs, exact saved reload checks and training reward variation
do not establish out-of-period IC improvement, financial alpha or profitability.
Those questions require the separately frozen matched evaluation.
