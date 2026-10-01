# Independent implementation and training review

Reviewer: research/protocol subagent. Review order: source and tests before performance reports. Files reviewed: `data.py`, `dsl.py`, `evaluation.py`, `environment.py`, `protocol.py`, `policies.py`, `experiments.py`, then `french.py`, `llm.py`, and `training.py` as they became available. The reviewer made no implementation edits or Git changes. Source is under active integration; line references below identify the reviewed version and may shift.

## Concrete findings and resolutions

| ID / severity | Finding and consequence | Resolution / remaining work |
| --- | --- | --- |
| I01 / P1 | Earlier `ResearchEnvironment._terminal_reward` checked paired-cell coverage only. Constant cross-sections counted as full coverage but disappeared from the IC mean. A legal 64x4 panel gave assessment IC ~1 on only 1 of 38 dates, coverage 1, and terminal reward .998. Screening accepted only 1 of 8 dates as well. | Fixed during review: `_usable_scores` (`environment.py:157`) requires finite mean, coverage >=.8, and `n_dates >= max(ceil(.8*span), min(20,span))` for both selection and terminal reward. Independent recheck rejects selection and returns -.002 costs only. New tests cover poor screen support and poor terminal support after a usable screen. |
| I02 / P2 | Earlier environment visible prefix used `metadata={}`, bypassing DSL supported-feature checks. A no-volume panel accepted volume proposals/screens although full-panel terminal evaluation rejected them. | Fixed during review: constructor copies only normalized `supported_features`, excludes arbitrary metadata, and reports the safe feature schema to the actor. Independent check returns invalid-expression for both volume screen and proposal. Dedicated metadata-isolation test added. |
| I03 / P1 operational | Earlier `run_episode` used nonexistent `env.initial_budget` and would fail before a rollout. | Root changed the bound to the observation's `initial_budget`. Independent stop-policy rollout completed. This was an integration failure, not leakage. |
| I04 / P2 provenance | Earlier generic `load_panel_csv` hardcoded `synthetic=False` although its disclaimer said authenticity was unverified; the roundtrip test imported generated synthetic data through that path. | Fixed by data agent: generic CSV now reports `synthetic=None`, `data_kind=unverified`. Verified-source French adapter has separate source provenance. |
| I05 / P2 auditability | Initial RLOO logs retained decoded text and prompt hashes but not raw completion token IDs or action log probabilities. Decoding with special-token removal is not reversible, limiting exact likelihood reproduction. Original manifests were emitted at run end rather than before execution. | Partly resolved prospectively: current code retains completion IDs/counts, group adapter digests and exact task seeds/templates/settings and creates its manifest before training. Public v1 report joins the pinned model revision and actual save/reload evidence. Historical v1 token/provenance limits remain explicitly disclosed; current richer logging cannot be retroactively attributed to that run. Per-action likelihood scalars/effective full config would further improve reproduction. |
| I06 / P2 numerical | The original direct LOO subtraction could give tiny nonzero advantages for identical floating rewards (e.g. .1 repeated three times), falsely marking an optimizer step when the mathematical advantage is zero. | Fixed prospectively: subtract the first reward before computing LOO. This is algebraically unchanged and makes identical values exactly zero. Four constant-value/group-size fixtures and an actual-trainer constant-reward fixture pass. Independently checked v1 groups 0/2 already had exact-zero advantages, gradients and no optimizer step; that actual run is not invalidated by this hardening. |

### I01 reproduction

Construct 64 dates and four assets with zero returns except dates 13,14,23,24, whose returns are `[.01,.02,.03,.04]`. Set wealth to `100*cumprod(1+returns)` and recomputed first-row returns to NaN. Use `ResearchSplit(fit=(0,10), feedback=(12,20), assessment=(22,60), horizon=1)` and candidate `returns`. Before correction, screen/select/stop gave .998. After correction selection returns `usable_screen_required`, and terminal reward is -.002. The existing sparse-NaN fixture alone did not detect this failure because constant dates had finite paired cells.

## Findings that were checked and did not become bugs

- Chronological bounds are already-purged signal intervals. `before.stop+h <= after.start` and `assessment.stop+h <= n_dates` correctly keep the final realized target before the next raw partition or panel end. The reviewer corrected an earlier prose ambiguity in the protocol; the split arithmetic itself was sound.
- DSL interpretation uses bounded AST validation and direct array operations, with no generated `eval`/`exec`. Lookbacks are causal; negative/zero/noninteger/future indexing and code-access constructs are rejected. Future-perturbation tests cover representative expressions.
- Visible feedback is computed on a copied prefix ending before assessment. Proposal/mutation validation also uses that prefix. New generation tests preserve observation/status equality when assessment values change.
- Rank combination uses same-day complete-case factor eligibility, average ties, predetermined feedback orientation, and equal entry weights. It does not choose orientations or weights on assessment. Invalid, duplicate, and insufficient-budget attempts are charged; terminal reward is paid once.
- Fixed candidate experiments remain explicitly development selection scaffolds. Newly enabled proposal/mutation records parent provenance and validates expressions before addition. Syntax deduplication is not semantic factor deduplication: aliases such as positive monotone transforms can still duplicate ranked signals and implicitly change pool weights. Do not describe structural diversity as independent economic diversity.
- Mean IC, missingness and scored-date counts have distinct meanings. The new support gate prevents the demonstrated extreme exploit; it is an objective eligibility rule, not statistical error control.

## Independent RLOO math review

For one task and one behavior checkpoint, let K independently sampled whole trajectories have terminal rewards R_i. The code computes `A_i = R_i - sum(R_j for j != i)/(K-1)`. The baseline excludes the current rollout; no reward-standard-deviation normalization is applied. The loss is `-(1/K) * sum_i A_i * sum_actions log pi(action_completion | exact_observation_prompt)`. Advantages are external numbers and do not backpropagate through the environment.

`completion_log_prob` (`llm.py:41`) scores logits from `prompt_length-1` through the penultimate input position against every completion token, including sampled EOS. Prompt tokens receive no direct target loss. Summing backward calls over actions/trajectories before a single optimizer step is algebraically equivalent to differentiating the trajectory-sum objective.

The model remains in eval mode with zero LoRA dropout. The reviewed local Qwen generation config contains temperature .6, top-k20, top-p.95 defaults, but stochastic `sample` overrides these to temperature 1, top-k 0, top-p 1. No additional nontrivial processor was visible in that config. Thus the source uses the same untruncated softmax for sampling and recomputed likelihoods. Record the effective config for other models rather than assuming all downloaded configs have identical defaults.

All rollouts in a group complete before an optimizer update, and a fresh group is sampled afterward. There is no replay or multiple on-policy epochs on old actions. This is basic grouped REINFORCE with a leave-one-out baseline; it is neither PPO nor GRPO. Gradient clipping and AdamW make the actual finite optimizer step differ from the raw unbiased score-function estimator, as usual. Groups with identical rewards have exactly zero advantages after the I06 correction and correctly skip the optimizer step.

SFT targets come from the scripted teacher acting on observations. Although `run_episode` records terminal training reward, example construction reads only each pre-action observation and chosen action. The teacher does not consult assessment data or rewards. The teacher's proposal is deliberately informed by the synthetic generator; it is not an independently discovered market hypothesis. SFT and RL task seeds are distinct in the reviewed code; later development seeds must stay disjoint.

No source-level likelihood-shift, baseline-sign, action-token masking, or on-policy reuse bug was found in this review. This conclusion is narrower than proof that a completed GPU run changed weights or improved behavior.

## Executed checks and evidence boundary

- Original five-module suite: 97 passed before findings were corrected.
- After environment corrections and generation additions: `python -m pytest tests/test_data.py tests/test_dsl.py tests/test_evaluation.py tests/test_protocol.py tests/test_environment.py -q -p no:cacheprovider --basetemp .pytest-protocol-review-20261001-recheck`: **123 passed**.
- Independent in-memory reproduction confirms I01 rejection and costs-only reward; separate restricted-feature probes confirm I02 rejection. Stop-policy runner confirms I03 correction.
- Training and real-baseline suites independently re-run after source review: `python -m pytest tests/test_training.py tests/test_real_baselines.py -q -p no:cacheprovider --basetemp .pytest-protocol-review-training-20261001`: **39 passed**, including actual-trainer toy reward-direction and constant-reward checks.
- No market performance result, training success claim, checkpoint-comparison outcome, or proposed final score was used to form the source-first judgment. Market aggregates and completed GPU artifacts were inspected only afterward, as recorded below.

For a defensible parameter-update claim, retain finite loss, nonzero gradient norm, changed adapter tensors/digest, saved checkpoint, and save/reload action-likelihood agreement. Compare base/SFT/RL through the same parser and greedy evaluation settings on disjoint development tasks. Record failed/invalid actions, support rejection, spending, empty pools and null tasks. Six development tasks are a machinery pilot, not statistical evidence of generalization, market alpha, or method novelty.

## Historical-market baseline review

The separate `real_baselines.py` and `docs/real-baseline-plan.md` use ten fixed return-only features and fixed alpha 1 ridge with prior-five-calendar-year fits. Source review found train-only feature scaling and target centering, no assessment-dependent orientation/hyperparameter choice, causal feature calculations, correct h5 purging, and fixed momentum/reversal comparators. The annual walk-forward baseline is a numerical market benchmark, not the LLM research policy's market-transfer result.

The bootstrap refuses missing daily-IC compression and samples circular 20-session blocks separately within each original year. It conditions on the specific five assessment years and captures limited within-year dependence; it does not estimate uncertainty over arbitrary future regimes or guarantee error control. Pooled industry/date training samples are not claimed independent statistical replicates. Comparison superiority would require paired differences, not separate intervals alone; no such superiority claim is supported here.

The output's provenance safelist excludes raw local paths, raw returns, predictions, coefficients and per-date IC. The source snapshot is pinned to `8f394fe34bea54d41b9aafed410425ee8f8e252ede3c71a7c1cd20bab83040de`, and the CLI retains only 2000-2024 before computing features/labels. Reviewer inspected aggregate results after source review: ridge mean IC .01759 over 1,233 dates, bootstrap interval [-.01134,.04917], consistent with an inconclusive development result. There is no evidence of positive financial alpha from this interval.

No unresolved P1 issue was found after the demonstrated fixes. Public prototype publication can describe the implementation, actual v1 parameter updates, and inconclusive development results. Remaining I05 gaps are explicitly P2 historical auditability limits; newer logging and software tests must not be presented as evidence that was captured in v1.

## Actual saved-checkpoint evidence reviewed

The public `results/llm_training_development_v1.json` SFT/RLOO sections exactly equal the original local `models/runs/{sft-v1,rloo-v1}/training-report.json` files. The reviewer checked equality programmatically, without altering either report. SFT has 84 examples/updates and 2,293,760 trainable parameters, finite losses/gradient norms, and changed adapter digests. RLOO has four groups of four trajectories, exactly two reward-varying groups with optimizer steps and nonzero preclip gradient norms .00548927 and .48108071. Its constant groups 0/2 have exact-zero advantages, zero gradients, and no step.

The reviewer independently loaded both saved `adapter_model.safetensors` checkpoints on CPU, mapped persisted LoRA keys to their live `default` adapter names, and recomputed the tensor-byte digest used by the implementation. Both digests match the corresponding original reports:

- SFT: `46e89788c8bc2a8cef11ba401f8729ea94df2c103598319772b2919bf2047148`.
- RLOO: `1433212171684a7cd581dbf80f3e89685b36ac175e16c87d4e3c8576fdb13bc9`.

All 224 saved trainable tensors differ between SFT and RLOO; the independently calculated aggregate Frobenius parameter delta is .0237611731. This establishes an actual saved LLM-adapter change, rather than only a controller update or orchestration claim. The source and reward-varying gradient logs support attributing that change to the declared RLOO optimizer path.

The original roundtrip report matches the public copy: same post-training tensor digest before/after reload and identical probe completion log probability (-17.62581443786621; absolute difference 0). The reviewer inspected this recorded GPU check and independently checked persisted tensor identity; the reviewer did not redundantly rerun the full GPU model reload.

The six development comparisons report base mean reward -.01 with 60 invalid actions, SFT .0328327566, and RLOO .0328327566. SFT and RLOO greedy behavior/rewards are identical, so no incremental RL benefit is demonstrated. Base-format failure under the original strict JSON parser confounds any research-quality interpretation of the base-to-SFT gap. The public artifact preserves that limitation and the small synthetic-task scope. Future format-robust comparisons are new development experiments, not corrections to the original measured result.
