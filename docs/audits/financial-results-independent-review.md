# Independent saved-results and reporting review

Reviewed 2026-10-01 by the data/evaluation agent, independently of the results
document's author. Scope: the three saved transfer reports, paired analysis JSON,
saved historical-rank diagnostics, results document, README, and post-hoc penalty
sensitivity source/tests/JSON/plots. No model generation, new market scoring,
checkpoint selection, GPU work, or frozen scorer edits were performed.

## Findings from retained outcomes

Direct arithmetic on all 80 strict/stochastic true-evidence attempts per policy
reproduces mean rewards -0.051585615 (SFT), -0.020128011 (RL 23), and -0.025405592
(RL 29). Usable counts are 77, 79, and 79. RL-minus-SFT gains are +0.031457603
and +0.026180023; exactly +0.025 of each comes from two fewer failures. The
remaining all-attempt IC-contribution changes are +0.006457603 and +0.001180023.
These remainders need not identify improved quality on a fixed usable subset.

Both sampled RL policies remain below the uniform-grid reward (-0.015410821).
Against training-frozen lag-1 (-0.020188993), RL 23 differs by only +0.000060981
and RL 29 by -0.005216599. Correct-minus-exchanged reward is -0.001737036 for
RL 23 and +0.001071094 for RL 29. Positive relative grounding interactions do
not remove that opposite-sign result.

Every greedy completion under both conditions is `ts_mean(returns,60)`, with
identical mean reward +0.005006598 for all three policies. Strict and narrow-fence
outcomes agree on every retained completion. Exact paired prompt tokens,
condition/decoding/draw identities, and RNG seeds match across checkpoints.

Re-running saved-report `analyze_reports` reproduces every corresponding field
of the paired JSON exactly, including its integrity checks. Direct yearly
arithmetic retains seed 23's negative 2020 difference and all other signed
periods. Historical-diagnostic joins reproduce 75/77, 76/79, and 77/79 near-exact
teacher matches among usable primary draws, plus 33/35, 32/35, and 34/36 among
unique task-expression pairs across conditions/decodings. The non-equivalent
saved rank similarities lie between approximately .829 and .877. This review
does not independently recompute those correlations from market arrays.

## Narrative and exploratory sensitivity

`docs/financial-proposal-results-v1.md` and the reviewed README accurately
separate actual updates, sampled reward gains, formula validity, mixed feedback
effects, identical greedy behavior, and the one-action versus sequential study.
They retain negative/null findings and development/dependence qualifications.
No blocking numerical discrepancy or alpha, profitability, significance, or
learned-sequential-agent overclaim was found.

`penalty_sensitivity.py` operates only on saved aggregates. It changes no action,
checkpoint, orientation, scorer, or registered primary penalty. Its identity
is `IC_sum/N - .01 - lambda*(1-valid_fraction)`. Lambda one reproduces the
primary reward; lambda zero is explicitly an accounting convention for failures,
not an observed zero IC. Regeneration matches the saved sensitivity fields
exactly; its input-analysis SHA256 matches the paired JSON. The uniform-grid
crossings .622624753 and .200418310 and zero-penalty gains are correct.
Both plots were visually inspected: signed effects, both seeds, zero lines,
and the primary/post-hoc distinction remain visible.

The sensitivity module assumes an already validated paired report; its flag is
not independent authentication. That assumption is satisfied by the reviewed
saved input and its separately re-run validation. This exploratory diagnostic
cannot select a replacement primary objective or justify new policy behavior.

## Validation and limits

All 28 existing financial-analysis and penalty-sensitivity tests passed; Ruff
passed for sensitivity source/tests. An additional in-memory artificial
all-invalid probe confirmed the sensitivity line remains `-.01-lambda`, with
no invented measured IC and no source mutation. No module changes were needed.

This audit verifies saved evidence and reporting, not a fresh raw-calendar,
training, or economic replication. Ten dependent half-years, five years, two RL
seeds, a shared SFT parent, overlapping labels, and eight draws per task leave
substantial uncertainty. The defensible result is a modest sampled-behavior
change dominated by validity improvement, with no demonstrated useful alpha or
consistent feedback advantage.
