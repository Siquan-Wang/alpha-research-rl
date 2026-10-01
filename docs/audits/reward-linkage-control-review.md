# Reward-linkage control: independent source review

Reviewed 2026-10-01 before inspecting any control training or evaluation
outcomes. **No blocking inconsistency remains** between the control trainer and
the [frozen plan](../reward-linkage-control-plan.md). This review used source,
artificial CPU tests and file hashes. It did not run GPU training, regenerate
market outcomes or independently certify future execution.

Reviewed trainer SHA256:
`b1d69303e48ed751a533b3c889b3b5e839cade00cb3d9b7440e3c5f9ae11e85c`.
Reviewed plan SHA256:
`c5f504e9c13c77bea5892ed3e03dfeee3e733144979bde5faf47286405604e6d`.

## Training law and control flow

The implementation uses the original deterministic 16-task schedule for each
seed and generates four fresh samples from the control's current actor before
each update. It does not replay original trajectories. The dedicated NumPy
generator is seeded with `700000+seed` and consumes exactly one `permutation(4)`
per group, including constant groups. Assignment is exactly
`assigned[i]=true[permutation[i]]`. Identity permutations, repeated reward values
and failure penalties remain eligible without conditional retries.

True evaluator outcomes remain attached to their own completions. The separate
assigned vector feeds the four-sample leave-one-out loss; full completion
log-probabilities are recomputed before the update. The trainer uses the existing
FP32 actor and sampling contract, AdamW at `1e-5` with zero weight decay, gradient
clipping at one, no entropy/KL term and no quality-gate stop. It attempts all
16 groups and logs actual optimizer-step counts.

The shared leave-one-out helper centers rewards before summation, so a constant
group has exact zero advantages. The optimizer is not stepped in that case:
existing Adam momentum cannot advance parameters merely because a constant
group was encountered. Zero-advantage groups still retain their permutations,
sample traces, gradients and unchanged parameter digests.

For a fixed sampled group and fixed score-function gradients, each uniformly
permuted assigned reward has expectation equal to the group mean. Thus each
advantage has expectation zero and the expected **pre-clipping policy gradient**
is zero over permutations. The test suite exhaustively checks all 24 assignments
on an artificial group containing repeated rewards and an invalid penalty.
This does not imply zero realized gradients, zero expected clipped gradients,
zero Adam drift or unchanged evaluation behavior. It is a reward-linkage control,
not syntax-only training or a no-update baseline.

## Parent and entry-manifest provenance

Independently hashed the intended `financial-sft-v1` adapter's current weights
and configuration. Its entire checkpoint entry equals the original frozen
entry, with combined SHA256
`d95793e5192be85fe4ceb15109a481c86ad13e804ffc01c56815683b1f21e360`.
The trainer also checks the initialized trainable-parameter digest against the
recorded SFT final digest.

The initial source enforced only the parameter digest while recording file
hashes. Review identified that the parameter digest alone cannot bind adapter
configuration changes such as scaling. Before launch, the author added an exact
combined-file-hash guard and the plan's SHA256 to the entry manifest. These
changes were reread and the five trainer CPU tests were rerun successfully.

The entry manifest is written before the first sample and includes parent
files, expected parameter digest, plan/trainer hashes, package/source provenance,
task order, permutation seed, optimizer and actor settings. Every group records
the true/assigned rewards, permutation, advantages, complete samples, likelihoods,
gradient norm and parameter-digest chain. Existing run manifests prevent silent
overwrite. Reload checks and the joint five-checkpoint freeze remain execution
requirements, not achievements established by this source review.

## Five-report analysis review

Also reviewed `linkage_analysis.py` before any control outputs were inspected.
It first validates the original three reports without relabeling them. The new
registry must preserve their checkpoint identities, bind original report file
hashes and the original suite hash, and precede control evaluation. Each report
retains its genuine applicable freeze and timestamp; no retroactive five-model
freeze is invented for the old evaluations.

The controls must match the original task manifests, prompt tokens, draw/seed
schedule, actor/runtime contract, scorer/tokenizer fingerprints and references.
The validator requires consistent outcomes for the same formula and task across
all five checkpoints. Aggregation keeps the two correct-minus-placebo pairs,
every half-year/year, true/exchanged effects, failure accounting and conditional
IC denominators. It does not select a favorable seed or discard failures.

The 52 combined linkage-analysis/original-analysis artificial tests passed in an
independent run; Ruff passed for the reviewed analysis source/tests. The five
trainer tests also passed after the provenance guards were added. These are
checks of implementation and artificial edge cases. Actual training traces,
reloads, registry contents and real report integrity still require their own
execution evidence. No significance, clean pretraining separation, general
causal financial advantage or sequential-agent capability is certified here.
