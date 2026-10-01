# Source-first financial proposal-policy review, 2026-10-01

Status: in progress. This independent review reads implementation and tests before
the training-only financial preflight results. It does not run GPU training,
modify implementation, or certify outcomes that have not been inspected.

Scope: `financial_tasks.py`, its tests, the registered
`docs/next-research-study.md` protocol, the actor sampling boundary in `llm.py`,
and the installed Transformers 4.57.6 generation implementation. The root-owned
financial trainer is reviewed separately when its source is available.

## Early critical finding: generation configuration inheritance

The recently introduced standalone `GenerationConfig` objects were passed to
`model.generate` without `use_model_defaults=False`. Installed Transformers
`generation/utils.py::_prepare_generation_config` replaces values equal to the
library defaults with model-specific defaults when the model configuration
version is at least 4.50 and `use_model_defaults` is unspecified.

The cached Qwen generation configuration declares version 4.51.0, sampling true,
temperature .6, top-p .95 and top-k 20. Thus the new stochastic configuration's
temperature 1 and top-p 1 can become .6 and .95. Its explicit top-k 0 differs from
the library default and is retained. More subtly, the new greedy configuration's
`do_sample=False` equals the library default and can become true. In that case a
call described as greedy is actually sampled.

This would invalidate the claimed untruncated sampling law and its raw-logit
policy-gradient recomputation. It can also invalidate a greedy behavior label.
The earlier v1 implementation passed `do_sample`, temperature, top-p and top-k as
direct generation keyword arguments; the library applies those after merging,
so this particular issue does not retrospectively indict that implementation.
Specific old artifacts must be attributed to the source actually loaded by their
process, not inferred from the current working tree.

Required resolution before financial RL: pass `use_model_defaults=False` for
both branches, retain explicit generation-law arguments, test the prepared
configuration against the Qwen defaults, and compare actual generated-token
scores with recomputed completion likelihood on the local actor. SFT weights do
not depend on decoding settings; behavior probes generated through an affected
call must be rerun or labeled unverified. Root was notified before financial RL.

Resolution observed in source: `LocalActor.sample` now disables model-default
merging and supplies explicit sampler keywords. The separate environment agent
added three CPU regression checks in `tests/test_generation_config.py`: effective
greedy mode, effective untruncated stochastic configuration, and actual generated
next-token scores versus raw full-softmax logits under conflicting model
defaults. This reviewer inspected those tests; their reported pass is a CPU
mechanism check, not a multi-token Qwen/BF16 likelihood-equality result. See the
separate [generation-config audit](2026-10-01-generation-config-merge.md).

## Task/evaluator findings before viewing results

| Check | Source-first judgment |
| --- | --- |
| Hard date cap | Constructor rejects a panel containing any post-2024 date; CLI loads through 2024-12-31. |
| Pinned snapshot | Initial preflight CLI omitted the hash check. Data owner added an explicit expected-SHA256 check before the first preflight output. Root's trainer must independently enforce the same pin. |
| Half-year chronology | Feedback is the immediately preceding half-year. Both signal intervals stop five rows before their raw period boundaries. The final included signal's label is strictly inside its own period. |
| Future isolation | Probe evidence, teacher scores and orientation use a copied prefix ending before assessment. Tests perturb future values and check invariance. |
| Teacher asymmetry | Teacher ranks 12 formula feedback scores while actor sees two probes. This is declared privileged-teacher distillation, not an equal-information optimality target. Teacher does not call future evaluation. |
| Input fields | Prefix panels expose only `returns`; existing DSL metadata checks reject wealth/close and unavailable volume. |
| Finite support | Feedback and assessment both require .8 cell coverage and the frozen valid-date threshold. Constant or unsupported formulas receive the strict failure penalty. |
| Orientation | Sign is chosen from feedback; assessment never chooses or flips it. Negation aliases have the same oriented outcome, as expected. |
| Fixed objective | Usable reward is oriented future IC minus .01; all failures receive -1.01. Failed calls do not save research cost. |
| Metadata boundary | Actor observation contains probe metrics and schema, without dates, task identity, source paths or assessment fields. Manifest remains separate. |
| Opportunity check | All 32 tasks are training periods. The grid oracle uses training assessment only and retains feedback-fixed orientation. It is labeled unattainable. |
| Reference reporting | Uniform-grid expected reward and probe winner diagnostics were initially missing, then added before preflight output. |

No fatal task/evaluator leakage was found in this source reading. The tests are
relevant boundary tests, not proof of valid real-data performance. Test execution
reported by the implementation owner is distinct from this review's inspection.

The Python object includes hidden arrays and is not an adversarial sandbox. The
safe call boundary is passing only `task.observation()` to the actor. The trainer
must not serialize the task object or public date manifest into the prompt.

## Statistical and interpretation requirements

The primary expected reward includes the failure penalty. A rise can come
entirely from fewer invalid or unscorable proposals. Report valid proportions,
failure reasons, cost, and predictive scores alongside it. A conditional mean IC
over successful proposals uses a policy-dependent subset and cannot replace the
all-proposal comparison.

Shared evaluation random seeds across checkpoints and evidence conditions are a
common-random-number coupling for paired Monte Carlo comparisons. Reseeding for
every task/draw prevents variable completion lengths from shifting later draws.
Those repeated draws are not independent market replications. Two RL seeds also
share one SFT parent and the same historical tasks; they estimate limited RL
optimization variability, not data-generating or full-training uncertainty.

The evidence intervention must generate new completions from the exchanged
same-episode probe bundles. Reusing the original formulas would force identical
scores because the evaluator deliberately retains true data. Do not shuffle
evidence across dates, and do not let an exchanged probe orientation replace the
generated formula's actual feedback orientation. This intervention tests
evidence correspondence, not a calibrated financial null hypothesis.

An assessment-selected grid maximum is a hindsight diagnostic. Even on training
data, its gap above a fixed formula can result partly from noisy maxima. It does
not establish that the two observable probe summaries contain enough information
for an adaptive policy to realize that gap. A positive transfer result without
an evidence effect can still be an improved unconditional proposal prior.

## Financial trainer source review

The first financial-policy/training source revision has the correct substantive
boundaries: `ProposalActor` receives only the observation; the strict shape
requires exactly action/propose and a string expression; EOS is required;
feedback-teacher construction never requests assessment. The same-episode
intervention exchanges complete non-expression bundles and leaves expression
labels fixed. The evaluator subsequently uses actual feedback/data.

RLOO samples four fresh completions from one current actor on one task before
performing an update. Its leave-one-out advantages and loss divide by four;
completion log probabilities include EOS and exclude prompt loss. There is one
optimizer step per fresh group, no replay, no step for exactly constant rewards,
weight decay zero and finite-gradient checks. The selected half-years and
eight-group quality gate match the protocol. A quality group requires different
legal ASTs and a usable future-IC spread, so invalid-versus-valid penalties alone
cannot pass it. No substantive policy-gradient error was identified here.

Two provenance changes were requested before the first financial run:

1. The initial SFT version only wrote its manifest after all 96 updates, and RL
   first persisted it after one update. Persist the manifest, actor identity and
   starting adapter digest before any optimizer step or sampled training action.
   Save encoded SFT prompt and target tokens as well as readable examples.
2. A value named `behavior_completion_logp` is recomputed from the unchanged actor
   before update, rather than captured from generation. Name it accurately and
   measure the actual local model's generation/recomputation discrepancy before
   claiming exact numerical agreement. Cached autoregressive and full-sequence
   BF16 passes can differ numerically even when the intended probability law is
   the same.

Resolution observed before the financial run: both trainer phases now persist
`run-manifest.json` with the initial adapter digest before the first update or
rollout. SFT also writes its exact encoded prompt/target pairs. This closes the
start-of-run provenance gap. Local-model generation/recomputation numerical
agreement remains a separate pending measurement.

The requested local-model measurement subsequently found a substantive numerical
discrepancy before financial training. In
`artifacts/development/qwen-sampling-law-v1.json`, processed versus raw cached
logits match exactly, while cached-generation versus full-forward recomputed log
probabilities differ by up to .464909 per token and .487569 over a 21-token
completion. Thus the untruncated softmax **configuration** is correct, but exact
numerical equivalence of the likelihood computations is not supported in that
BF16 check. This is a different issue from model-default merging.

Root changed only the separate financial `ProposalActor` to float32 with CUDA
and cuDNN TF32 disabled and requested a same-prompt/same-seed repeat before
financial SFT/RL. This reviewer inspected that constructor change and amended the
financial protocol before training. The failed BF16 check stays in the evidence
record. Earlier BF16 experiments still demonstrate parameter updates where those
were verified, but must not be described as having measured exact
cached-generation/full-forward likelihood equality. The float32 repeat retained
the same 21-token completion and measured zero processed/raw cached-logit
difference, maximum token log-probability difference `2.6226e-5`, and sequence
difference `2.0981e-5`. Those values were inspected from
`artifacts/development/qwen-sampling-law-fp32-v2.json`. This resolves the observed
large numerical mismatch for that probe, with a finite numerical tolerance; it
does not prove equality on all future prompts or trained adapters.

The evaluator owner was also warned that the shared `adapter_digest` hashes only
parameters with `requires_grad=True`. Frozen evaluation adapters would therefore
produce an empty-set digest through that helper. Evaluation checkpoint identity
must use adapter-file hashes or a LoRA tensor hash independent of gradient flags.

## Training-only preflight interpretation

Only after the code judgment above, this reviewer inspected
`artifacts/development/financial-training-grid-v1.json`. Its source hash matches
the frozen input and its scored half-years end in 2017. All 16 formulas are usable
on all 32 training episodes, so failure penalties do not explain the comparisons.

| Reference | Mean reward | Mean oriented future IC |
| --- | ---: | ---: |
| Feedback-greedy over 16 formulas | -0.031795 | -0.021795 |
| Exact uniform average over the grid | -0.010452 | -0.000452 |
| Training-selected fixed `delay(returns,1)` | -0.000201 | 0.009799 |
| Per-episode future-best grid oracle | 0.047283 | 0.057283 |

The simple feedback ranking is worse than uniform on these training periods.
The oracle gap is not evidence that the two probes make its hindsight advantage
predictable. The first-12 SFT teacher supplies nine target formulas, with
`ts_std(returns,20)` in 15 of 32 cases, `ts_mean(returns,60)` in six, and the
remaining cases distributed across seven labels. This gives syntax diversity but
does not validate the teacher's future utility. The reported 16-grid greedy
performance must not be mislabeled as the first-12 teacher's exact performance.

The probe with larger absolute whole-feedback IC is mean-20 on 20 tasks and
mean-5 on 12; 25 tasks have at least one subwindow with a different winner. This
shows observable variation and instability, not that its mapping to future
formula performance can be learned with 32 episodes.

The strongest immediate extra comparison is to freeze the **training-selected
fixed formula** `delay(returns,1)` before transfer scoring and evaluate it with
the same feedback orientation, support guards and fixed cost. Root accepted this
addition before transfer evaluation. It cheaply distinguishes a useful formula
prior from improvement over an especially weak feedback heuristic. It is not
chosen from the later reported comparison.

## Remaining audit work

Verify the trainer provenance fixes and the separate financial evaluation source,
including checkpoint identities, sample coupling, frozen comparison boundaries,
and aggregation before marking this review complete. No financial RL result has
been inspected or asserted at this stage.
