# A five-minute technical walkthrough

**Question:** can a language model use historical financial evidence to produce
better factor proposals, and can reward-based training improve that behavior?
This repository separates working orchestration, actual parameter learning and
predictive usefulness. The first two have execution evidence; useful financial
improvement remains unproven.

Completed-evidence baseline: public `main` at `5640368`. The matched-prefix
follow-up below has a reviewed protocol and a prepared execution contract;
public-byte verification must still precede collection. It has no result yet.

## Read these in order

1. **The functioning loop and its negative result:**
   [Astra feedback study](astra-agent-results-v1.md), then one episode in the
   [decision explorer](astra-explorer.html). A bounded expression is generated,
   historically evaluated, masked and returned to the next decision. All pools
   and selections were published before their later-period assessments.
2. **Diagnose that failure without replacing it:**
   [frozen-pool diagnosis](astra-pool-diagnosis-results-v1.md). All 180 original
   slots map to 132 task/AST/direction keys: 24 reused outcomes and 108 new CPU
   evaluations, with zero new model calls. This is a separate post-hoc study.
3. **Inspect actual learning:** [Qwen financial training and results](financial-proposal-results-v1.md)
   and [reward-linkage controls](reward-linkage-results-v1.md). Parameter-update
   evidence and reward improvement answer different questions.
4. **Check the evidence boundary:** [saved Astra replay](replay-astra-evidence.md)
   and [pool reproduction](reproduce-astra-pool-diagnosis.md). Replay checks
   public records and arithmetic without regenerating proposals or recomputing
   market scores. It is not independent economic replication.

## Keep the five components separate

| Component | What actually happens | Boundary |
|---|---|---|
| GenAI generation | A language model emits a bounded factor expression and action text; an AST interpreter executes the allowed operators. | Different expressions need not be different economic signals. |
| Multistep agency | Astra makes six successive proposals using its permitted history, under three feedback conditions. | The common deterministic final selector is not an extra model decision; useful adaptation is an empirical question. |
| Actual weight RL | Local Qwen3-0.6B LoRA receives SFT and REINFORCE updates with a leave-one-out baseline. | The financial episode is one proposal—a contextual bandit. Hosted Astra inference does not update Astra weights. |
| Numerical forecasting | A separate [walk-forward ridge baseline](results-v1.md#historical-industry-return-baseline) maps numerical features to future returns. | Formula generation is not a financial foundation model or a new numerical forecasting architecture. |
| Next controlled revision | Identical two-proposal starts, displayed versus masked candidate metrics, and cheap references. | Protocol review is complete; no follow-up result is reported here. |

## Six questions worth pressing on

**1. What worked, and what failed?**

The hosted workflow completed 180 decisions and 30 selected assessments.
Full feedback's mean historically oriented future IC was **−0.033823**, and full minus validity-only
was **−0.006364**. All 30 outcomes were usable, so invalidity does not explain
that deficit. The pool diagnosis found full-arm hindsight IC **+0.015711**, but
the historical winner, literal first proposal and minimum-AST rule all had
negative mean IC. Full-arm oracle utility is still **−0.044289** after the fixed
abstract cost .06. An oracle proves realized headroom, not an available strategy.
Full feedback had a lower pool ceiling and a smaller selection gap than either
control; “the selector alone caused the failure” is unsupported.

**2. Did RL learn prediction, or merely improve the reported reward?**

The original financial study records **96 SFT updates and 31 RL optimizer
steps** across two seeds, with changing adapter digests and saved-model checks.
Its all-attempt identity is `mean reward = −1.01 + usable fraction + IC contribution`.
RL gains over SFT were **+.031458 / +.026180**; **+.025** in each comes from
two fewer failures among 80 attempts. That decomposition is outcome accounting,
not an identified gradient mechanism. Correct reward linkage beats fresh
on-policy reward-permutation controls by **+.023032 / +.018368**, but predictive
contribution differences are **+.010532 / −.006632**. Both signs must remain in
the conclusion. All five stochastic financial checkpoints still lose to the uniform formula grid
on registered utility; greedy behavior is identical across checkpoints.

**3. How are leakage and repeated development use handled?**

The financial contract uses a five-session target, purged temporal boundaries
and direction fixed from historical feedback. Frozen candidates and selectors
prevent substitution after assessment. These safeguards do not make repeatedly
examined **2020–2024** periods an untouched holdout. The pool diagnosis was
designed after the original selected results and keeps its own namespace and
publication gate. Revised industry-portfolio data and unaudited model pretraining
also limit historical forecasting claims. Training assessment rewards are
training data, never held-out evidence.

**4. Why insist on cheap controls?**

A useful generated proposal must justify more than syntactic variation or
accurate citations of old scores. The uniform-grid comparison already challenges
the trained policies. In the pending revision study, copying the prefix winner,
making one scheduled window edit and taking one seeded grammar draw provide
cheap alternatives at the same attempted-proposal budget. Copies retain their
future quality Q, while their incremental selected gain G is zero. Post-hoc
first/minimum-AST pool results diagnose selection within an existing generated
bank; they do not prove that generation needed an LLM.

**5. How much uncertainty do the repetitions resolve?**

Ten dependent half-years and five calendar years are not 80 or 180 independent
markets. Labels overlap, local RL runs share an SFT parent, and hosted v1 has
only one trajectory per condition and period. Equal call budgets also do not
imply equal token budgets. The follow-up's four continuations estimate limited
conditional generation variation; interpreting its Monte Carlo SE requires an
unverified independent-draw assumption. No significance, general feedback-harm,
profitability or external peer-review claim follows from these records.

**6. What is the next falsifiable decision?**

The [matched-prefix protocol](astra-matched-prefix-plan-v1.md) asks whether
displayed candidate metrics improve a fresh formula from the same starting
state. Its budget is **80 hosted calls plus 120 cheap slots**, with no repair or
resampling. Primary Q is historically oriented future IC, or −1 for failure;
secondary G is the gain after the common historical selector relative to the
prefix winner. All 200 slots and choices must freeze and pass public-byte
verification before cached future outcomes are joined or new ones evaluated.

The allocation rule requires truthful feedback to beat masking and every cheap
reference on Q, predictive contribution and G, with mean G above the abstract
incremental cost .01. Failure stops this version; success does not automatically
authorize another study. Infrastructure failure or the user quota reserve leaves
partial evidence without a complete-study headline. Neither outcome changes the completed
negative result, establishes long-horizon research skill, or supplies a fresh
market holdout.
