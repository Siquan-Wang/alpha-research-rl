# Implemented methodology and limits

This document describes the local prototype's method, not a performance claim. Results and completion status belong in versioned run artifacts and `CHECKPOINT.md`. See [research protocol](research-protocol.md), [source provenance](data-sources.md), and [independent implementation audit](audits/2026-10-01-implementation-review.md).

## Research process

A policy interacts with a finite-budget environment by proposing or mutating causal expressions, screening feedback IC, examining predetermined feedback subwindows, selecting up to three entries, and stopping. Generation is opt-in; fixed-pool baselines test only evidence acquisition/selection. Generated expressions run through a bounded AST interpreter, not arbitrary Python execution.

Close/wealth, volume where available, and realized returns are transformed using arithmetic, positive delays, rolling summaries, and same-day ranks/standardization. Each temporal operator has a maximum lookback of 60, expression depth 16, node count128, and length2048. These are per-operator and expression resource limits; they do not imply a 60-day maximum cumulative nested history. Dataset-supported fields are checked and exposed as safe schema information.

Each episode has fit, feedback and assessment signal intervals. Fit is reserved for possible downstream estimation; the current equal-weight pool does not fit a separate model there. Feedback labels realize before assessment starts. The policy sees acquired feedback evidence and research history, while terminal training reward uses assessment. Assessment is therefore training data for RL episodes even though its arrays and scores are absent from action prompts.

Selection fixes each factor's sign from feedback. The pool averages oriented centered cross-sectional ranks on assets finite for every selected factor; final evaluation uses Spearman IC of that composite. Positive monotone aliases can still represent equivalent ranked signals: syntactic uniqueness is not economic diversity, and repeated aliases can effectively alter pool weights.

Screen/selection cost one budget unit; stability and proposal/mutation cost two. Invalid and duplicate attempts are charged, stop is free, and terminal reward occurs once. The objective is eligible assessment mean daily IC minus .001 per spent unit. Both screening eligibility and assessment reward require paired-cell coverage >=.8 and valid IC dates >=`max(ceil(.8*block_length),min(20,block_length))`. Low-support submissions receive zero predictive score and still pay costs. The sign of exact zero feedback uses +1 in the current implementation.

## Local actor and SFT

The initial actor is a locally cached Qwen3-0.6B causal language model, model-source revision `c1899de289a04d12100db370d81485cdf75e47ca`, with rank8 LoRA on attention q/k/v/o projections, alpha16, and dropout0. Computation uses the available local CUDA GPU; model requests use local files. The JSON action prompt disables the model's optional thinking mode. Exact action likelihood includes completion tokens only; prompts and environment responses are context.

SFT is supervised behavior cloning of a scripted teacher that proposes a known synthetic-signal expression, screens available candidates, selects from feedback, and stops. Target strings are compact JSON plus EOS. The objective is negative completion log probability divided by completion length; AdamW uses learning rate2e-4, gradient clipping1, and no action-prompt target loss.

The reviewed default pilot creates12 synthetic episodes with training seeds1000 through1011 across signal/null/decay regimes, 300 dates,16 assets, horizon5 and budget10. The teacher contains knowledge of the simulator and is not evidence that an LLM independently discovered a financial factor. Neither teacher action choice nor SFT target construction uses assessment scores.

## Reward-dependent parameter updates

The RL trainer implements grouped REINFORCE with a leave-one-out reward baseline, following the general score-function approach associated with [REINFORCE](https://doi.org/10.1007/BF00992696) and the LLM leave-one-out approach discussed in [Back to Basics](https://arxiv.org/abs/2402.14740). It is not PPO/GRPO and does not reproduce those papers' experiments.

For K>=2 trajectories sampled independently from the same current actor on one task:

`A_i = R_i - (sum_j R_j - R_i)/(K-1)`

`L = -(1/K) * sum_i A_i * sum_actions sum_completion_tokens log pi(token | exact_prompt, earlier_tokens)`

Each reward is the environment's terminal objective. Tool outputs and prompts are excluded from sampled-action likelihood. Sampling uses temperature1, top-p1 and top-k0 so raw-model likelihood matches the untruncated sampling distribution for the reviewed model configuration. The actor stays in eval mode with dropout disabled while gradients remain enabled during likelihood recomputation.

The trainer accumulates gradients over the whole group, clips norm at1, and makes one AdamW step with learning rate1e-5 and weight decay0. It samples a fresh group after each update, without replay or extra epochs. The implementation first subtracts the first reward before computing the algebraically identical LOO expression to make constant rewards exactly zero despite floating-point summation. If all rewards are equal, the update is skipped. Earlier affected pilot artifacts must remain labeled superseded. No KL regularizer, value model, reward model, clipping ratio, or standard-deviation-normalized advantage is implemented.

The default tiny pilot uses four groups of four trajectories, seeds2000 through2003 and rotating signal/null/decay regimes. This is an implementation-scale study. It may produce no useful policy improvement, and cheaper stopping on null tasks is a legitimate consequence of the cost objective. A changed adapter proves parameter learning occurred; it does not prove improved reasoning or financial performance.

## Evaluation and scientific limits

Planned first local comparison uses base, SFT and SFT+RL checkpoints with identical greedy decoding, action parser, initial candidates and budget10 on disjoint synthetic seeds11000 through11005, with two tasks each for signal/null/decay. This remains development evaluation: six tasks cannot support broad generalization or significance claims, and later adjustments consume these tasks as development evidence. Actual completed runs must record their settings instead of relying on defaults in this prose.

The separate public-data baseline uses the official 49-industry return source through a downloader-only adapter. Ten causal return features feed a shared ridge model with alpha1, train-only scaling and previous-five-calendar-year fits, evaluated on2020-2024 with five-session target purging. Momentum20 and reversal20 have fixed orientations. The descriptive interval uses2000 circular-bootstrap replicates of20-session blocks separately within each assessment year and conditions on those specific years. It is an industry-portfolio ranking task. Wealth indices are derived from returns, volume is unavailable, and current revised histories are not historical point-in-time vintages. Neither that adapter nor synthetic actor training establishes stock alpha, executable PnL, profitability, market transfer of the RL actor, or statistical error control.

Report predictive IC separately from budget penalty and include valid-date support, coverage, abstention, spending, selected expressions, invalid/duplicate actions, and feedback-to-assessment change. Overlapping horizons, correlated industries and reused market episodes are dependent. A future sealed study must freeze data/checkpoints/protocol before scoring, use a later untouched partition, and preregister any time-aware uncertainty analysis.

The evidence chain for actual local LLM RL is: sampled token trajectories -> environment rewards -> correct completion likelihood -> reward-dependent gradient -> changed trainable adapter -> saved/reloaded checkpoint -> matched development comparison. None of these arrows establishes alpha by itself. Log null results and preserve failures.
