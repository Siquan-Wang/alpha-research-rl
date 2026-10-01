# Saved reward-credit accounting: independent implementation review

2026-10-01. **No remaining implementation blocker for the bounded saved-only
analysis.** This disposition follows source review and the final 30 artificial
tests below; it is not a verification of the actual four-run output.

The reviewer participated in selecting this post-hoc question and supplied design
criticism, but did not author the new accounting implementation or plan. This is
an internal AI implementation review, not external peer review. The review uses
source inspection and artificial records only; root owns the actual analysis of
the four published training runs. Existing model, market and study artifacts are
unchanged.

## Source-grounded scope

The original `financial_training.py` and `linkage_training.py` apply raw
leave-one-out advantages to each saved completion log-probability, divide by
four, then clip the aggregate parameter gradient before AdamW. There is no
advantage whitening or clipping before this scalar surrogate. The control uses
`assigned[i] = true[p[i]]`; sample and likelihood order stays fixed.

Consequently, the proposed reward/advantage/surrogate identities describe the
recorded sampled objective. They do not recover its expectation, parameter
gradient components, clipping effects or optimizer updates. The IC component is
training-assessment information, not a heldout prediction-quality measurement.
The existing evaluation-reward decomposition remains valid regardless of how
often training groups contain a validity contrast.

## Pre-implementation specification review

The plan's conditional nonidentifiability construction is sound, including its
explicit noncollinearity condition. An invalid sample's zero IC contribution can
exceed a valid sample's negative IC; component signs therefore do not justify
training on an isolated component. All-valid groups have zero direct validity
coefficient, which does not preclude improved validity through other updates or
shared parameters.

The reviewer requested exact fixed reward/training metadata, separate arithmetic
tolerances, finite nonpositive saved log-probabilities, and explicit training-data
terminology. All were incorporated before the final source review.

## Findings and resolution

1. **Impossible update hidden by numerical tolerance.** The author identified,
   and this reviewer independently reproduced, acceptance of exactly constant
   rewards with forged logged advantages `[1e-14, -1e-14, 0, 0]`, a changed digest
   and `optimizer_step=True`. The targeted rejection test initially failed
   (one failure, 0.06 seconds). The frozen centered implementation produces exact
   zeros for constant rewards. The new checker now requires exact logged zeros
   in this case. A separate passing test preserves an actual update for
   nonconstant IC variation below 1e-12: tolerance does not become a new stopping
   or display rule.
2. **Retained copies are not arithmetic estimates.** The reviewer required exact
   numeric equality between sample outcomes and group rewards, and between
   indexed true rewards and assigned rewards. These are copying/indexing
   identities; a tolerance could disagree about whether the recorded reward
   vector was constant. The author repaired both checks. Two final tests reject
   a one-ULP change while allowing numeric int/float equality and rejecting bool.
   The computed reward, advantage and surrogate identities retain the fixed
   1e-12 absolute/relative tolerance.

These findings concern the new checker. No evidence of corrupt original training
records was inferred, and no historical file was repaired.

## Independent artificial validation

`python -m pytest tests/test_reward_credit_review.py -q -p no:cacheprovider
--basetemp=.local/credit-review-final` completed **30 passed in 0.05 seconds**.
Ruff on the reviewer test file passed. The tests do not import the author fixture,
read the actual training exports, call the scorer or load a model.

The direct other-three `Fraction` oracle differs from the implementation's
centered summation. For a mixed group and permutation `(2,0,3,1)`, it verifies
the full advantage vectors, coefficient L1 values and exact scalar expectations
`L_V=7/12`, `L_C=-1/2`, `L_R=1/12`, keeping likelihoods in sample order. An
incorrect joint permutation of likelihoods produces a different objective.

Further cases cover all-valid IC variation with zero validity coefficient;
all-valid and all-failed constant groups; and a mixed group whose V and C
coefficients cancel completely despite both having nonzero magnitude. The
cancellation case retains a negative cross term of `-8/3`, zero total
coefficient and no update. Cases also reject malformed/inverse permutations,
Boolean tokens/indices/orientations, invalid status/reason combinations, failed
samples carrying IC, nonfinite or positive likelihoods, changed task/group
identity, unchanged digests for recorded updates and even a subnormal nonzero
norm for a skipped group.

Source review separately checked fixed four-run roles and ordered 16-by-4
populations, task and SFT-parent matching, digest chains, input-byte pins checked
before parsing the same captured buffers, duplicate-key rejection, and exclusive
CLI output. The pure in-memory API explicitly does not attest published byte
identity. Original metadata outside the consumed validation scope is not
independently reconstructed. The author's complete artificial-bank/CLI tests
are separate from this reviewer's 30-case count.

## Reviewed identities and limits

| File | SHA-256 |
| --- | --- |
| `src/alpha_research_rl/reward_credit.py` | `b03e21e845b63b727509d3101a0bd4f585318bf5079b4c95a9273d493b72c44c` |
| `scripts/analyze_reward_credit.py` | `035007cf70a695bffca79626a606f025da845362cc501b22b665a96352303606` |
| `tests/test_reward_credit.py` | `32dee270279d68bb665b9c668c285f87f298d7b5cbff7911e91cb73676bd1a91` |
| `tests/test_reward_credit_review.py` | `09d55b8142827d075ab745ea9456cf7c427c57b481abeccdd448eabbbf6912cc` |
| `docs/reward-credit-plan-v1.md` | `8bad73a35841156be263a7f869360e8f6ec14cc720158883bb1a9154bdf53b7c` |

This checks a deliberately small accounting interface. It does not establish
economic learning, causal reward-channel effects, generalization, independence
of training groups or validity of the original market measurements. Root still
owns the complete saved-record analysis and its publication. No model, market,
gradient, training, checkpoint-selection or Git operation occurred in this lane.

## Post-run read-only inspection

After root's single analysis completed, this reviewer inspected the saved
report's metadata, all four group/sample container counts, run summaries, and
root's separately written arithmetic-checker source. The reviewer did **not**
execute either analysis or checker, recompute the full training bank, or repeat
the earlier tests. Root's execution record reports exit 0 between
2026-10-01T15:08:12.0994327Z and 15:08:12.2794228Z.

The inspected [result](../../results/reward_credit_v1.json) is 340,901 bytes with
SHA-256 `59d31578928894581208c8928fd38690b839d0c12264c38e64779ffc19957cb7`.
Its source-byte pins, analysis/CLI/test/plan identities, four ordered run roles,
16 groups per run and four sample rows per group match the reviewed contract.
It retains all 64 groups and 256 attempts, including the skipped group. Its
reported operation fields are zero new model calls, zero market scores and no
recomputed gradients.

| Saved run | Usable attempts / 64 | Mixed-validity groups / 16 | Recorded updates / 16 |
| --- | ---: | ---: | ---: |
| Correct, seed 23 | 63 | 1 | 16 |
| Correct, seed 29 | 64 | 0 | 15 |
| Permuted, seed 23 | 64 | 0 | 16 |
| Permuted, seed 29 | 63 | 1 | 16 |

The denominators must stay explicit: **62 of 64 groups** have zero direct
validity coefficients; **61 of 63 recorded optimizer-step groups** do so.
One all-valid constant-reward group was skipped. This is compatible with the
previous finding that most evaluated reward improvement came from fewer failed
proposals. It neither identifies the learning pathway that improved validity
nor establishes useful financial learning from the remaining coefficients.

Root's independent checker, retained locally with SHA-256
`83cc4b1fd2402476dfbe487f0f2569d9d4c8550c92f90d70fc21493dd08b4179`, uses
60-digit `Decimal`, direct other-three means, the logged permutation and
unaltered likelihood order, with no project imports. Source inspection confirms
that it compares every group's component vectors, coefficient magnitudes,
cross term and surrogate, then the retained run aggregates. Root reports 3,752
numeric comparisons passed with maximum absolute discrepancy about 2.93e-16.
That execution result is root's evidence; this reviewer verified the checker's
method and report consistency, not a second execution. The checker is an
independent arithmetic cross-check, not a replacement for the implementation's
strict schema, exact-copy and input-identity checks.

No further blocker was found within this read-only scope. L1 masses, negative
cross terms, sign opposition and differently signed surrogate sums must still
remain coefficient accounting. They cannot rank the runs' learning quality,
allocate gradient/Adam shares or turn training-assessment IC into heldout
evidence. The upcoming narrative and figure remain separate review items.

## Final narrative and publication inspection

The follow-up read-only scan covered the result narrative, related README,
walkthrough, site-index and iteration-log passages, both public JSON records,
the plot source, the rendered PNG and the public independent-inspection source.
No analysis, inspector, plotting command, test or model was executed for this
scan. **No publication blocker was found.**

The narrative preserves both denominators, distinguishes 31 original RL steps
from the four-run accounting population, and makes no gradient-share, useful
learning or significance claim. Its mixed-group task identities, zero-based
indices, rounded coefficient scales and invalid-sample example agree with the
saved report. The figure's one-based positions agree with those records; the
two V-present cells and one all-zero cell remain visible and its text is readable.
Its category rule gives V presence priority, including in the cancellation edge
case exercised by artificial tests. The stopped financial research branches
remain stopped. All nine local links in the new results document resolve.

The public inspector's source following `getcontext().prec` matches the executed
copy; only preceding standard-library imports were reordered/formatted. The
public source hash is
`cb7e4f78fde5ede5c130addd7aad721eeb911e8459b345fd2525525819827a21`, distinct from
the executed-source hash recorded above. The public inspection record discloses
that difference accurately and does not claim another arithmetic execution.
Its suggested invocation uses isolated startup and no optimization flags, which
is relevant because its checks use assertions. It remains a complementary
arithmetic inspector, not the strict evidence parser.

The reviewed results narrative has SHA-256
`7ba0ec07c5b921cdcf93ed18beb4464ead0510f3b3c8511c5a01ee97475edea0`;
the plot source has
`4c16afe1f16fb509ddbbd1b263f494bfd519b7cbc88fc0841893f7bd1888fe5c`;
the visually inspected PNG has
`1386358a7c432a68280b492311f3bfdef9e637bdf68996eb4622dd8e523ccf8f`.
Public execution and inspection records preserve the actual result hash and
distinguish the analysis invocation from the independent arithmetic check.
