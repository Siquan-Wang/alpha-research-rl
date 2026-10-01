# Local LLM development study v1

Written before base/SFT/RL development comparisons.

Base: Qwen/Qwen3-0.6B, Apache-2.0 model card, revision
`c1899de289a04d12100db370d81485cdf75e47ca`. Downloaded weights remain local.
Training: local BF16 Transformers/PEFT on one existing 24-GiB-class CUDA GPU.
LoRA rank 8, alpha 16, q/k/v/o attention projections, no dropout.

The actor emits JSON actions autoregressively. It can propose new bounded DSL
expressions, screen them, acquire temporal diagnostics, select, or stop. No
unrestricted Python execution. A scripted feedback-only teacher supplies SFT
actions; it never sees terminal assessment rewards when choosing actions.

- SFT: 12 tasks, seeds 1000–1011, alternating signal/null/decay, one epoch,
  AdamW lr 0.0002, completion-only cross entropy.
- RL smoke: initially four groups of four whole independent rollouts per task,
  seeds 2000 onward, same alternating regimes. Full-softmax temperature 1.
  One fresh on-policy update per group, lr 0.00001, gradient clipping 1.
  Reward is terminal assessment IC minus research cost. The baseline for one
  trajectory is the mean reward of its *other* group members. Loss sums all
  sampled completion log probabilities across its actions. No replay, PPO
  clipping, or KL term: label this REINFORCE with a leave-one-out baseline,
  not GRPO or production-scale post-training.
- Development comparison: six tasks, seeds 11000–11005, alternating the same
  three regimes; same budget 10, initial factors, observation formatter, parser,
  greedy decoding and 64-token action cap for base, SFT and RL. Truncated actions
  are invalid and still charged. These tasks are development data, never a final
  financial holdout. Reusing them to debug invalid behavior is disclosed.

Save task/model revisions, gradient norms, losses, reward groups, decoded action
traces, trainable parameter counts and before/after adapter hashes. Verify saved
adapter likelihood and weights survive reload. A changed parameter hash proves
an update occurred, not that RL improves generalization. Report failed/null
comparisons without changing the headline to suggest otherwise.

Synthetic generators deliberately expose simple past-observable patterns. Good
results here do not establish financial alpha, strategy returns, financial text
reasoning, or general discovery. The real industry-return baseline is a separate
numerical research artifact; transferring an LLM policy to it is a later study.
