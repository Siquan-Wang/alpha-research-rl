# Research protocol: sequential quantitative research and local LLM post-training

Status: prospective protocol and source-first review, written before experiment results. This document does not register a sealed study, establish alpha, or certify the implementation. A study becomes frozen only when its exact machine-readable manifest and checkpoint hashes are saved before its final scores are computed.

## Research question and staged scope

The intended question is whether local LLM reinforcement post-training improves a bounded sequential research policy's ability to acquire evidence, generate or refine causal expressions, and submit a small predictive factor pool under a fixed evaluation budget.

1. **Numerical infrastructure:** deterministic synthetic signal, null, and decay panels validate labels, causality, scoring, action accounting, and observation boundaries. These results are software and simulator evidence.
2. **Selection scaffold:** a fixed candidate library with screen, stability, select, and stop actions tests evidence acquisition and selection. A scripted controller, bandit, or non-LLM learned policy is not LLM post-training. A fixed candidate selector is not alpha generation.
3. **Market development baseline:** a downloader-only adapter for the official 49-industry daily return panel provides an industry-portfolio return-ranking task. Its numerical outputs are historical market evidence about this restricted task; they are not stock-level alpha, trading profit, or executable strategy returns.
4. **Actual LLM study:** add validated expression proposal/mutation actions, collect training-partition trajectories, perform local open-weight SFT and reward-dependent parameter updates, and compare frozen base, SFT-only, and RL policies. Existing/free hardware and software only. Stage 4 remains outstanding until weights change and actual saved checkpoints are evaluated.

The scientific unit is a research policy, not the best expression selected after viewing all reported outcomes. Expression generation and selection must be reported separately when only one is implemented.

## Two levels of separation

Every episode has chronological **fit**, **feedback**, and **assessment** intervals. Fit may train a predetermined downstream combiner, feedback supports research actions, and assessment supplies terminal reward on training episodes. Any assessment used for gradient updates is training data, even if absent from the prompt.

Across episodes, a study has **training**, **development**, and **final** partitions. Only training episodes produce optimization rewards. Development episodes support architecture, hyperparameter, grammar, cost, and checkpoint selection. Final episodes are run once after freeze; their outputs never enter gradients, reward normalization, prompts, factor databases, candidate templates, checkpoint selection, or further experiment design.

All initial smoke results are development results. Merely naming the last chronological slice `assessment`, `test`, or `holdout` does not make it untouched. If results have been viewed and then used to revise the system, that period belongs to development. A successor study must select a new final period or report the reuse as exploratory.

Historical public data may occur in LLM pretraining. Record model release and available cutoff information; avoid a claim that historical holdouts are contamination-free. A later prospective period is stronger evidence, but no period is guaranteed unseen without verified provenance.

## Freeze manifest

Before final evaluation, save a versioned study manifest containing:

- Data source, retrieval UTC time, raw SHA256, parser version, chosen table, ordered assets, valid dates, missing-data policy, and all snapshot revisions.
- Exact train/development/final boundaries, every episode's intervals and label horizon, seed lists, regime proportions, and known overlap between episodes.
- Candidate seed library and generator rules; DSL operators, cumulative lookback limit, feature availability, complexity limits, proposal quota, deduplication rules, action budget, and selection limit.
- Observation schema, fixed feedback stability subwindows, orientation rule, aggregation formula, coverage thresholds, reward cost, invalid-action handling, and stopping rule.
- LLM identity/revision/license, tokenizer revision, prompt and parsing policy, sampling settings, SFT/RL configuration, optimizer, seed, compute budget, checkpoint-selection rule, and exact selected checkpoint hash.
- Baselines, ablations, primary metric, diagnostic metrics, inferential method if any, and a finite number of final runs.

Date ranges and seed counts are not frozen by this prose. Choose them after basic parsing and development smoke runs, before any final scoring. Data schema validation can inspect a raw file without computing policy scores, but access in this shared local workspace is a governance boundary, not a security-enforced blind evaluation.

## Timing, labels, and purging

`returns[t]` represents the return ending at date t. A signal computed using inputs through t predicts `close[t+h] / close[t] - 1`; for the industry adapter, `close` means a cumulative wealth index. The target horizon counts observed trading rows, not calendar days. This is a forecasting alignment and makes no assertion about achievable execution at the same closing value.

A raw data partition ending at B may use a label at t only if `t+h < B`. The implementation represents already-purged **signal-date** intervals `[a,b)`, whose label realizations can extend into the excluded tail before the next partition starts. Thus `b+h <= next_partition_start` is the correct half-open boundary check, and `assessment_stop+h <= panel_length` preserves the final labels. Do not incorrectly require `t+h < b` when b already excludes the purged signal dates. Add horizon-1 and multi-day edge fixtures to prevent an off-by-one failure.

Backward feature history from earlier periods is allowed. Feature evaluation may not center windows, interpolate from future values, backfill from future values, standardize using future rows, or use assessment statistics for clipping, normalization, orientation, filtering, or pool construction. Compute the maximum cumulative lookback of nested expressions, rather than assuming every individual operator's 60-row bound also bounds the whole expression.

## Predictive score and reward design

The primary predictive statistic is mean daily cross-sectional Spearman IC on a prespecified set of usable dates. Report the full daily IC series locally, number of eligible and scored dates, usable asset counts, missingness, and coverage with every mean. A constant or insufficient-coverage factor is unscorable; its scalar terminal predictive reward must be a predetermined finite value, never NaN or an opportunity to choose convenient dates.

Before a selected factor enters a pool, determine its sign from its acquired feedback screen only. A recommended initial rule is to require a successful screen before selection, use +1 for a positive feedback mean and -1 for a negative mean, and reject zero/nonfinite/insufficient feedback. If implementation chooses a different fallback, freeze and disclose it. Never choose or flip signs on assessment.

Orient each selected factor, compute same-day centered cross-sectional ranks with a fixed tie rule and missing-value mask, and average them with equal weights. Fix whether the final pool is re-ranked before Spearman scoring. Report this precisely; do not fit pool weights on assessment. Do not assess different candidates on selectively chosen incomparable dates without accounting for the difference.

The scaffold terminal objective is `assessment_mean_ic - cost_per_attempt * charged_attempts`. Freeze cost before training and report predictive IC and cost separately. Empty submission has predictive score zero; incurred costs still count. Immediate stopping may be optimal under a weak/no-signal task or large cost: report abstention instead of forcing participation to produce a positive headline. Do not tune cost after final results.

Every non-stop attempt consumes budget, including malformed, duplicate, unsupported, out-of-range, and unsuccessful proposals. Freeze whether stop itself is free. Terminal transitions occur once; repeated stop/step calls cannot produce additional reward. Beyond the declared terminal reward to the training optimizer, no hidden metric, assessment vector, or assessment-derived diagnostic may leak via `info`, exceptions, serialized observations, action masks, caches, or logs supplied back to the acting policy. A final runner may report its sealed score to the human after completion, but may not resume research actions from that feedback.

Proposal/mutation actions use the same causal validated DSL, with no arbitrary generated-code execution. Syntactic canonicalization and duplicate counting must use rules fixed in advance. Semantic similarity/diversity rewards may use fit/feedback data only for action-visible decisions. Diversity is a diagnostic or separately declared auxiliary objective, not a guarantee of financial validity or statistical error control.

## Baselines and comparisons

On identical tasks and candidate initializations compare immediate stop, fixed economic expressions, uniform random actions, deterministic feedback-greedy selection, a stability-aware heuristic, a lightweight learned non-LLM policy, the frozen base LLM, SFT-only LLM, and SFT+RL LLM where available. Unsupported baselines are explicitly marked unrun.

Use matched proposal/evaluation budgets and record actual calls, valid expressions, unique expressions, latency, generated tokens, and peak memory. Permitting one policy extra screens or uncounted retries invalidates a search-efficiency comparison. Shuffle candidate order with logged seeds and hold out expression families in a separate development diagnostic to detect memorized candidate-position strategies. A best-of-many oracle that uses assessment is an upper-bound diagnostic and never a deployable baseline.

Primary comparisons use paired task outcomes and frozen checkpoints. Publish null and negative results, invalid/duplicate rates, empty pools, pool size, spending, sign choices, and feedback-to-assessment degradation. Separate SFT benefits, RL incremental benefits, candidate-library quality, and search-budget benefits through ablations. Increased training reward alone is not improved generalization.

## Evidence required for an LLM RL claim

A real RL run must log trajectories sampled from a specified behavior checkpoint, token log-probabilities for generated actions, environment-derived rewards, advantage/baseline construction, optimizer steps, and changed trainable parameters. Tool responses and prompt tokens are context, not sampled actor actions, and must be masked from the actor loss. If an off-policy update is used, specify its correction rather than presenting it as on-policy GRPO/PPO.

Store base/SFT/RL checkpoint identifiers and hashes; demonstrate save/reload consistency and evaluate all policies through the same action parser. A controller update, hand-written candidate adjustment, SFT on reward-ranked traces, inference-time reranking, or an optimizer running on a constant/detached loss is not evidence of reinforcement post-training of an LLM.

A one-batch tiny-model run establishes machinery only. It cannot establish research-policy improvement, financial transfer, or meaningful learning without a frozen comparison on distinct tasks. Under limited free compute, reduce model/task sizes and label the study a pilot rather than substitute an untrained controller for the requested LLM experiment.

## Dependence and uncertainty

Five-day targets overlap in time; industries co-move; rolling episodes can share market rows and candidates. Do not count industries, adjacent days, or overlapping episodes as independent replications. Report date spans and overlap explicitly.

For a descriptive pilot, report paired effects and uncertainty limits without significance claims. A later inferential study can preregister a date-block bootstrap or time-series robust analysis of paired daily-IC differences, with a block/lag rule accounting for the horizon and longer dependence. Resample common dates jointly across policies and industries, preserve temporal blocks, and report sensitivity. Such procedures do not repair adaptive holdout reuse or guarantee false-discovery control after unrestricted search.

Synthetic null tasks check reward exploitation and simulator overfitting; their null does not establish a market-wide financial null. Arbitrary daily return shuffling may destroy dependence and is not automatically a valid financial significance test. Mark permutation controls exploratory unless their null and exchangeability assumptions are justified.

## Source-first contract review

The implementation contract already draws the essential distinction between training assessment and frozen evaluation, bans unrestricted expression execution, and charges invalid attempts. Before final-study registration the following require explicit implementation and documentation:

| Risk | Required correction or evidence |
| --- | --- |
| Fixed candidates mistaken for discovery | Label scaffold selection-only; add bounded proposal/mutation before claiming generated factors. |
| Industry returns mistaken for equity OHLCV | Use returns/wealth metadata and supported fields; reject volume expressions; report industry-level scope. |
| Boundary gap mistaken for purge | Check each label's realization date inside its own partition. |
| Missingness or orientation games | Freeze eligibility, coverage, sign fallback, rank combination, and finite unscorable rewards. |
| Hidden terminal score reused | Separate optimizer episodes from final runner; verify observation/log boundaries and checkpoint freeze. |
| Repeated/canonical proposals gain free evidence | Charge all attempts; freeze syntax and semantic deduplication; report counts. |
| Reward or small-step success mistaken for alpha | Compare frozen base/SFT/RL with paired outcomes; preserve nulls and abstention. |
| Overlapping tasks mistaken for sample size | Report overlap and use time-aware uncertainty; refrain from unsupported error-control claims. |

## Primary literature and attribution

These papers motivate design choices; their reported results are not reproduced by this prototype. Do not copy third-party code without checking its license and recording attribution.

- [RD-Agent-Quant](https://arxiv.org/abs/2505.15155): research/development/feedback loops and factor-model co-optimization motivate the sequential environment. Its market claims do not transfer to our data or policies.
- [AlphaGen](https://arxiv.org/abs/2306.12964): collection-aware formulaic factor RL motivates pool-level reward; its generator is distinct from a pretrained LLM post-training study. [Original code](https://github.com/ICT-FinD-Lab/alphagen).
- [AlphaAgentEvo](https://openreview.net/pdf?id=lNmZrawUMu): multi-turn evolution and agentic RL motivate trajectory-level evaluation and feedback use. The published paper is accessible; forum access may require browser verification.
- [AlphaDiverse](https://arxiv.org/abs/2609.29014): local planner/realizer SFT followed by joint GRPO and inner/outer evaluation motivate exploration diagnostics and freezing. This is a recent preprint, not a replicated baseline.
- [QuantEvolver](https://arxiv.org/abs/2605.15412): executable quantitative feedback converted into parameter updates motivates separating true post-training from prompt accumulation. [Original code](https://github.com/QuantLLM/QuantEvolver) describes a framework rather than bundled market data or paper-specific reproduction assets.
