# First development results

These small experiments verify mechanisms and expose failure modes. They do not
establish a new research result, improved financial alpha, or profitable trading.

## Local LLM training and behavior

Qwen3-0.6B LoRA SFT used 84 action examples from 12 synthetic tasks. The first
RL run used four groups of four trajectories. Two groups had identical rewards
and no update; two had nonzero gradients and updated the adapter. Adapter hashes
changed, and a saved/reloaded checkpoint reproduced both the parameter hash and
a reference action log probability exactly (absolute difference 0).

| Actor | Mean development reward, 6 tasks | Invalid actions | Accepted proposals |
| --- | ---: | ---: | ---: |
| Base, strict JSON | -0.01000 | 60 | 0 |
| SFT | 0.03283 | 0 | 6 |
| SFT + RLOO | 0.03283 | 0 | 6 |

Base emitted valid-looking JSON inside Markdown fences, which the original parser
rejected. This makes the base/SFT gap an interface confound. **SFT and RL chose
identical actions on all six tasks**, including always selecting initial candidate
0. The proposed expression was also identical. This is evidence of a narrow
learned action script, not adaptive discovery. A format-robust comparison and
counterfactual evidence tests are the next diagnostics.

The reward is assessment rank IC minus research cost, not a portfolio return.
Training/development seeds are distinct, but all tasks share deliberately simple
synthetic generators. Six tasks provide no persuasive generalization estimate.

Full recorded evidence: [training logs and checkpoint checks](../results/llm_training_development_v1.json),
[base](../artifacts/development/base-v1.json), [SFT](../artifacts/development/sft-v1.json),
[RLOO](../artifacts/development/rloo-v1.json). The v1 manifest/trace limitations
are preserved in the evidence file; later code improves their completeness.

## Historical industry-return baseline

The separate numerical baseline uses the pinned official 49-industry return
snapshot, prior-five-year ridge fits, and purged annual development periods
2020–2024. It is not an LLM-trained market strategy.

| Fixed method | Mean daily IC | Within-year block-bootstrap 95% interval |
| --- | ---: | ---: |
| Ridge | 0.01759 | [-0.01134, 0.04917] |
| Momentum20 | 0.01215 | [-0.01256, 0.03893] |
| Reversal20 | -0.01215 | [-0.03893, 0.01256] |

All intervals cross zero. These intervals describe a limited development sample
with short-range dependence assumptions, not guaranteed error control. The study
does not evaluate P&L, transaction costs or stock-level generalization. See the
[prewritten protocol](real-baseline-plan.md) and [aggregate results](../results/french49_fixed_baselines_development_v1.json).

## Validation

179 tests and Ruff passed at this milestone. Tests include causal perturbations,
label support at split boundaries, invalid/duplicate proposal charging, restricted
source features, reward eligibility, completion-only token likelihoods and actual
SFT/RLOO update directions on an independent small model. Independent review found
and corrected issues; it does not substitute for a larger empirical study.
