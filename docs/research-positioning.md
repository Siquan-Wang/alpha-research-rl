# Research positioning and contribution boundaries

Reviewed 2026-10-01 UTC. AlphaResearch-RL is a small, inspectable study of
language-model training and evaluation for factor research. Its strongest
contribution so far is an implemented experimental system and a set of bounded
empirical findings, including failed gates. It has not established a new learning
algorithm, profitable alpha, or a useful learned sequential financial researcher.

## What the evidence supports

| Component | Demonstrated evidence | Claim boundary |
| --- | --- | --- |
| Research environment | Bounded expressions, explicit action costs, evidence observations, invalid/duplicate handling, and preserved action traces | An environment that permits sequential decisions does not establish a policy that makes useful ones. |
| Generative model and actual RL | Local Qwen3-0.6B LoRA; the financial study records 96 SFT updates and 31 actual RLOO optimizer steps across two seeds, with digest and saved-reload checks | This is pretrained-LLM post-training. Its financial episode contains one proposal, so it is a contextual bandit, not demonstrated multistep agency. |
| Financial evaluation | Frozen checkpoints, purged chronology, true/exchanged evidence, fixed/grid references, all-attempt validity accounting, and individual saved outcomes | Ten dependent 2020–2024 half-years are development transfer evidence. They are not an untouched final test or 80 independent market replications. |
| Numerical forecasting | A separate walk-forward ridge baseline maps numerical features to future returns | The language model emits formulas. It is not a numerical market foundation model, and LoRA training does not demonstrate financial tokenization or a new forecasting architecture. |
| Research judgment | The constructed curriculum and sequential CPU gate failed their declared criteria and stopped | Preserving negative results demonstrates experimental discipline; failure alone does not establish a general research discovery. |

The [financial results](financial-proposal-results-v1.md) show sampled reward
gains of +0.031458 and +0.026180 over the shared SFT parent. In each run, +0.025
comes from two fewer failed proposals among 80 attempts. Both policies remain
below the uniform formula-grid expectation under the registered reward. All
three greedy policies emit the same formula, feedback effects are inconsistent,
and most usable proposals reproduce teacher formulas or their historical rank
behavior. The residual IC contribution is outcome accounting, not a causal
separation of syntax learning and financial learning.

These records support discussion of policy-gradient implementation, sampling
contracts, leakage prevention, diagnostics and negative-result interpretation.
For example, the [sampler audit](audits/2026-10-01-generation-config-merge.md)
documents a model-default override that made a purported greedy run stochastic;
the [policy audit](audits/2026-10-01-financial-policy-review.md) separates that
bug from finite-precision likelihood disagreement. These are concrete engineering
findings. They do not substitute for prediction quality or scale evidence.

## Relevant prior methods

The following comparison uses official repositories and primary papers checked
on the review date. It compares problem formulations, not benchmark performance;
this project has not reproduced these systems on a common dataset or budget.

| Prior work | Verified methodological overlap | Distinction in this repository |
| --- | --- | --- |
| [RD-Agent-Quant paper](https://arxiv.org/abs/2505.15155v2) and [RD-Agent repository](https://github.com/microsoft/RD-Agent) | Research hypotheses, generated implementations, experiment feedback, factor/model co-optimization and a bandit scheduler already form an automated research loop. | The present study asks what a small, locally post-trained actor changes under an explicit scoring contract. It neither originates research loops nor matches RD-Agent's broader capabilities. The current RD-Agent repository also has fine-tuning scenarios; this comparison concerns its quant formulation. |
| [Alpha-R1 paper](https://arxiv.org/abs/2512.23515v2) and [training documentation](https://github.com/FinStep-AI/Alpha-R1/blob/main/training/README.md) | Qwen3-8B is trained with GRPO to screen candidate factors using semantic profiles and market context, with portfolio-return rewards. The public training reward is described as a simplified reference implementation. | LLM RL for alpha selection is existing work. Here Qwen3-0.6B proposes one bounded expression using numeric probe summaries; RLOO optimizes oriented IC with failure penalties. Different actions, information and rewards prevent direct score comparisons. |
| [AlphaGen repository](https://github.com/ICT-FinD-Lab/alphagen) | The original KDD 2023 work learns formulaic alpha collections through RL; the repository exposes maskable-PPO/LSTM components and now also contains LLM generation and HARLA extensions. | The current experiment updates a pretrained language-model adapter and evaluates individual proposals, without demonstrating a synergistic factor collection. Neither RL expression search nor adding an LLM constitutes novelty here. |

The [wider reference list](related-work.md) supplies context. A smaller model,
free local execution, or more visible logs can make this project useful to
inspect; those properties alone are not evidence of methodological novelty.

## Missing evidence and falsifiable next questions

The existing [reward-linkage control plan](reward-linkage-control-plan.md) is a
separate exploratory follow-up, declared after the original outcomes. It tests
correct reward assignment against two on-policy reward-permutation controls.
This positioning review uses no outcome from that follow-up. If correctly linked
RL does not consistently beat its matched controls, attributing the original
gains to correct reward linkage remains unsupported. A favorable result would
establish only sensitivity within this small pipeline, not financial alpha or
sequential competence.

The [sequential acquisition branch](sequential-gate-results-v1.md) remains
**stopped**: the privileged selector harmed one chronological fold and failed
the registered overall gate. The [constructed curriculum](curriculum-results-v2.md)
also remains stopped. Neither result authorizes extra epochs, a generated
candidate bank, controller training or tuning against inspected evaluation years.

Any later project addressing the following questions needs a new, versioned
protocol with a finite budget, untouched assessment outcomes, and its own stop
rule. These are evidence requirements, not experiments initiated by this review:

- **Useful evidence acquisition:** does acquiring a specified additional
  observation improve downstream utility over matched no-check and fixed-check
  controls, after its cost, consistently across frozen chronological folds?
  Failure of that criterion should stop the new study before LLM scaling.
- **Useful learned generation:** does the policy beat frozen formula-library
  and random-generation references at equal attempted-proposal budgets, retain
  the effect with invalid attempts counted, and produce factors that add
  predictive value beyond teacher-equivalent ranks? Different strings are
  insufficient.
- **Numerical modeling, if pursued separately:** does a frozen numerical model
  improve a declared forecast loss and calibration or ranking metric over ridge
  and other prespecified baselines across forward periods? This requires its own
  data representation, training and ablations; adding a language-model tool call
  cannot supply that evidence.

Robust financial claims additionally need defensible data-vintage and universe
handling, appropriate uncertainty for dependent periods, and explicit trading
and cost assumptions if claiming returns. The current data are revised industry
portfolio histories; pretraining exposure is unaudited and no executable P&L is
measured. The strongest present portfolio signal is therefore careful ML
experimentation and implementation, with financial usefulness still unproven.
