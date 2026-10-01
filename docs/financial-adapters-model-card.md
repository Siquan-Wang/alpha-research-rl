# Financial proposal adapters v1

Five research LoRA adapters for the pinned
[Qwen3-0.6B base](https://huggingface.co/Qwen/Qwen3-0.6B/tree/c1899de289a04d12100db370d81485cdf75e47ca).
They contain the exact parameter and configuration bytes frozen for the published
financial studies. The release distributes adapters, not the base model.

## Checkpoints and training

| Adapter | Parent | Actual optimizer updates | Purpose |
|---|---|---:|---|
| `financial-sft-v1` | Pinned Qwen3-0.6B | 96 SFT | Learn the bounded formula JSON interface from feedback-selected teacher formulas |
| `financial-rloo23-v1` | Financial SFT | 16 RLOO | Correct financial reward assignment, seed 23 |
| `financial-rloo29-v1` | Financial SFT | 15 RLOO | Correct financial reward assignment, seed 29; one constant-reward group skipped |
| `financial-placebo23-v1` | Financial SFT | 16 permutation-control updates | Fresh on-policy samples with within-group reward permutation, seed 23 |
| `financial-placebo29-v1` | Financial SFT | 16 permutation-control updates | Fresh on-policy samples with within-group reward permutation, seed 29 |

All adapters use rank 8, alpha 16, zero LoRA dropout, and attention q/k/v/o
projections: 2,293,760 trainable parameters. Training and financial evaluation
used FP32 with TF32 disabled on an existing RTX 5090 Laptop GPU. The original
runtime was Python 3.12.14, PyTorch 2.8.0+cu128, Transformers 4.57.6 and PEFT
0.18.1. Base revision: `c1899de289a04d12100db370d81485cdf75e47ca`.

Training used 2002–2017 half-years from revised French49 industry-portfolio
return histories. SFT's teacher searched a fixed feedback formula grid; the
actor saw only two probe summaries. RL used later-period training IC rewards.
Neither the release nor the repository redistributes the downloaded raw market
panel. The original six-task synthetic pilot and failed curriculum adapters
are different models and are not included in this release.

## Intended use and measured limits

Use these checkpoints to reproduce the recorded proposal-policy experiments,
inspect training effects and study evaluation methodology. Each financial
episode produces one bounded factor expression. These models have not
demonstrated a useful learned multistep financial researcher.

Across ten 2020–2024 development half-years, both correctly linked RL runs had
higher sampled reward than SFT and their matched permutation controls. Much of
the SFT difference came from fewer invalid formulas; correct-versus-permuted
predictive IC contributions had opposite signs across the two seeds. All five
sampled policies remained below the uniform formula-grid reference. All five
greedy policies emitted the same formula. These findings do not establish
profitable alpha, independent factor discovery or an untouched final test.
See the complete [original results](https://github.com/Siquan-Wang/alpha-research-rl/blob/main/docs/financial-proposal-results-v1.md) and
[control results](https://github.com/Siquan-Wang/alpha-research-rl/blob/main/docs/reward-linkage-results-v1.md).

The data are revised industry histories rather than a point-in-time stock
universe. The base model's pretraining exposure is unaudited. The small number
of dependent periods, two training seeds and exploratory timing of the control
limit generalization. The model generates invalid actions in some samples;
use the repository's restricted parser and evaluator rather than executing
generated code. No trading system, transaction-cost model or P&L was evaluated.

## License and modification notice

The base model is provided by the Qwen team / Alibaba Cloud under
[Apache-2.0](https://huggingface.co/Qwen/Qwen3-0.6B/blob/c1899de289a04d12100db370d81485cdf75e47ca/LICENSE).
Copyright 2024 Alibaba Cloud. This release includes an unchanged copy of that
license. The newly trained adapter tensors and their configurations are
AlphaResearch-RL modifications, copyright 2026 AlphaResearch-RL contributors,
distributed under Apache-2.0. The frozen base parameters are not modified or
redistributed in this archive. No Qwen affiliation or endorsement is implied.
Repository source code remains under its separate MIT license.

## File identity and use

Each `<checkpoint>/adapter/` directory contains only `adapter_config.json` and
`adapter_model.safetensors`; no pickle, optimizer state, tokenizer copy or raw
data is included. The archive also contains this model card, the Apache license
and a modification notice. Every adapter byte hash must match
`artifacts/development/financial-linkage-suite-freeze-v1.json` before packaging
and again before extraction. The release manifest additionally pins the archive
hash, size, individual members and builder source.

The configuration's original relative base path is deliberately preserved for
hash identity. Supply the pinned base model explicitly when loading, as the
repository's `ProposalActor` does. Never replace the SFT parent with a newly
trained adapter and treat its descendants as reproductions of these runs.
Different hardware or library kernels may still change stochastic generation;
published saved draws remain the authoritative observations for these results.
