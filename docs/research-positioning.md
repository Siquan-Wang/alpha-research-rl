# Research positioning and contribution boundaries

Updated after the completed matched-prefix study on 2026-10-01 UTC. AlphaResearch-RL
studies language-model generation, feedback use and post-training for factor
research. The actual Astra research loop and the separate local Qwen training
experiments have both run. Its strongest contribution is an inspectable
experimental system with bounded empirical findings, including negative results
and failed gates. It has not established a new learning algorithm, profitable
alpha, or a useful learned sequential financial researcher.

## What the evidence supports

| Component | Demonstrated evidence | Claim boundary |
| --- | --- | --- |
| Actual agentic research | Astra generated 180 proposals in 30 six-decision episodes; full, validity-only and withheld feedback were compared under a common selector, after every pool was publicly frozen | Full minus validity mean future IC was −0.006364. The loop is real inference-time research, with no observed mean future-IC benefit on this bank; no Astra weight update is claimed. |
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

The subsequent [reward-linkage controls](reward-linkage-results-v1.md) preserve
both original seeds and add two matched on-policy reward-permutation controls.
Correct linkage exceeds those controls on the penalized reward, but the
predictive-IC contributions change in opposite directions across seeds. That
limits the claim to reward sensitivity in this pipeline.

The [Astra result](astra-agent-results-v1.md) removes the small local model as
the sole research actor. All 180 proposals were valid and all thirty selected
assessments were usable, yet each condition's mean oriented future IC was
negative. The full-feedback arm's −0.006364 difference therefore cannot be
explained by fewer invalid outputs. This separates the question of successful
tool orchestration from useful predictive research. A single trajectory per
condition and period cannot establish a general effect of feedback.

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
| [RD-Agent-Quant paper](https://arxiv.org/abs/2505.15155v2) and [RD-Agent repository](https://github.com/microsoft/RD-Agent) | Research hypotheses, generated implementations, experiment feedback, factor/model co-optimization and a bandit scheduler already form an automated research loop. | The present studies separately test feedback during strong-model proposal generation and small-model post-training under fixed budgets. They neither originate research loops nor match RD-Agent's broader capabilities. The repository also has fine-tuning scenarios; this comparison concerns its quant formulation. |
| [Alpha-R1 paper](https://arxiv.org/abs/2512.23515v2) and [training documentation](https://github.com/FinStep-AI/Alpha-R1/blob/main/training/README.md) | Qwen3-8B is trained with GRPO to screen candidate factors using semantic profiles and market context, with portfolio-return rewards. The public training reward is described as a simplified reference implementation. | LLM RL for alpha selection is existing work. Here Qwen3-0.6B proposes one bounded expression using numeric probe summaries; RLOO optimizes oriented IC with failure penalties. Different actions, information and rewards prevent direct score comparisons. |
| [AlphaGen repository](https://github.com/ICT-FinD-Lab/alphagen) | The original KDD 2023 work learns formulaic alpha collections through RL; the repository exposes maskable-PPO/LSTM components and now also contains LLM generation and HARLA extensions. | The current experiment updates a pretrained language-model adapter and evaluates individual proposals, without demonstrating a synergistic factor collection. Neither RL expression search nor adding an LLM constitutes novelty here. |

The [wider reference list](related-work.md) supplies context. A smaller model,
free local execution, or more visible logs can make this project useful to
inspect; those properties alone are not evidence of methodological novelty.

## Missing evidence and falsifiable next questions

The [separate pool diagnosis](astra-pool-diagnosis-results-v1.md) has now scored
the remaining frozen candidates after publishing its finite population and
rules. Full feedback's hindsight mean IC is +0.015711, but the original,
first-proposal and minimum-AST selectors all remain negative. Its realized
pool ceiling trails both controls, while its selection gap is slightly smaller.
This narrows the explanation of the original deficit, without identifying a
causal generation effect or a deployable selector. The original v1 result is
unchanged.

The original result lacks repeated hosted generations within each condition
and period. The separate [matched-prefix study](astra-matched-prefix-overview.md)
completed four fresh one-proposal calls per condition and state against
copying, scheduled window edits and seeded grammar draws: 80 hosted calls and
120 cheap slots, with both publication gates satisfied before outcome joins.
Truthful minus masked Q was −.006750. Truthful G was −.001098, below copying
and window edits, so the registered allocation gate failed and this version
stopped. The [result report](astra-matched-prefix-results-v1.md) preserves all
comparisons. Four continuations quantify limited conditional generation
variation, not independent market histories or long-horizon adaptation.
The separate rationale audit recorded mostly supported public factual claims;
accurate citations of old scores did not establish predictive benefit.

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
