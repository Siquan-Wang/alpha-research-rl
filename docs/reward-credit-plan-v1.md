# Saved training reward-credit accounting v1

2026-10-01. **Post-hoc analysis of already published training records.** Training
and evaluation outcomes are already known. This is not a prospective scientific
test, another RL run, or a new publication-gate experiment. Root runs the bounded
analysis only after source/tests and this plan are reviewed. Existing records,
study conclusions and stopped branches remain unchanged.

## Question and fixed population

Evaluation reward gains dominated by failure avoidance do not establish that
training updates received predominantly failure-penalty credit. Determine which
recorded groups had direct validity-credit coefficients, and reconstruct the
additive sampled training surrogate without claiming parameter-update attribution.

Use only these two exact public byte streams:

| Input | SHA-256 |
| --- | --- |
| `results/financial_training_v1.json` | `5cb85943a209183492df813cb63f372f05c9257bba254382957d41183a69cf17` |
| `results/financial_linkage_training_v1.json` | `e9143fb33680317cc8312410b7b078a849a9d26d7824e7770f29b7230fd3c80d` |

Preserve exactly four runs, in this order: `correct23`, `correct29`, `placebo23`,
`placebo29`, corresponding to `financial-rloo23-v1`, `financial-rloo29-v1`,
`financial-placebo23-v1`, `financial-placebo29-v1`. Each has 16 ordered groups of
four attempted samples: **64 groups / 256 attempts**. Keep failed proposals,
duplicates, identity permutations and constant/skipped groups. The SFT entry in
the first export supplies parent provenance; it is not a fifth RL run and its
96 supervised updates are outside this decomposition. No condition is chosen
because of its result. Keep the two seeds separate; pooled counts are accounting,
not independent learning replications.

The original reports live under `training-report.json`; control reports use
`training_report`. Embedded historical file hashes are recorded provenance:
the two enclosing export-byte pins are checked directly. Do not claim to recover
an original file-byte hash by reserializing an embedded JSON object.

## Exact decomposition

For sample i, define V_i=1 when saved outcome status is `ok`, otherwise V_i=0.
Define C_i as the saved oriented future IC for `ok`, otherwise C_i=0. Zero here
is an accounting convention for failed attempts, not an observed IC.
These later-period assessments were used as training rewards and are **training
data**, not held-out predictive-quality evidence.

```text
R_i = -1.01 + V_i + C_i
assigned_X[i] = true_X[p[i]],  X in {R,V,C}
A_i(X) = assigned_X[i] - sum(assigned_X[j] for j != i)/3
A(R) = A(V) + A(C)
L_X = -sum(A_i(X) * saved_preupdate_completion_logp_i)/4
L_R = L_V + L_C
```

Correct-linkage runs use the identity p=(0,1,2,3). Placebo runs use the actual
logged permutation, including identities. Apply that same permutation to **all
three reward channels**. Sample identities, completion log-probabilities and
tokens remain in their recorded order. These controls received assigned rewards,
so decomposing their unpermuted channels would describe the wrong objective.

The constant -1.01 cancels under leave-one-out centering. Numerically reconstruct
each advantage vector by first subtracting its first channel value, as the
historical trainer did, then using `math.fsum` for sums. Constant input channels
therefore produce exact zeros. Match logged total advantages within the fixed
tolerance below; preserve their raw values separately. Use the saved recomputed
pre-update **sequence** log-probability, with no length normalization or new
likelihood calculation. This is a scalar sampled surrogate, not the objective's
expectation or evidence of its improvement over training.

RLOO is established policy-gradient methodology; see
[Ahmadian et al., §2.3](https://arxiv.org/html/2402.14740v2#S2.SS3).
The present identities are elementary linearity/accounting, not a new algorithm
or reproduction of that paper.

## Validation before reporting

Use standard-library JSON/arithmetic only. Reject duplicate JSON keys, nonfinite
numbers and Boolean substitutes for numeric fields. Counts, seeds, group indices,
token IDs, permutations and orientations are exact integers; flags are exact
Booleans. Required consumed fields, roles, lengths and order must match. Preserve
unused historical metadata in the input, without importing its training runtime.

- Verify the four run roles/phases/seeds and their 16×4 population; group indices
  are exactly 0..15, and group task manifests equal their declared task order.
  Paired correct/placebo runs for each seed must share task order and SFT parent
  digest. Validate common frozen reward/training settings used by these equations.
- Fixed numeric settings are exact metadata, not tolerance-based comparisons:
  cost .01, group size 4, maximum groups 16, learning rate 1e-5, gradient clip 1,
  weight decay/KL/entropy coefficients 0 and maximum completion length 64.
  Required integer/Boolean types remain exact; numeric settings reject Boolean
  substitutes. Do not accept a changed cost or configuration within 1e-12.
- Every saved outcome has cost .01. `ok` requires finite IC in [-1,1], an exact
  ±1 orientation, no failure reason, and oriented IC consistent with saved
  assessment mean IC and orientation. Its reward must be C−.01. A failed status
  must be one of the recorded `invalid`/`unscorable` alternatives, have no
  reported oriented IC and reward −1.01. Retain its status/reason; do not reparse,
  repair, re-evaluate or infer an unavailable score.
- Check all four true rewards against outcomes and all assigned rewards against
  the permutation. Each permutation contains each integer 0..3 exactly once.
  These outcome-to-group copies and `true[p[i]]`-to-assigned copies require
  **exact numeric equality**, not an arithmetic tolerance (numeric int/float
  values are accepted, Boolean substitutes are not).
  Correct-run rewards are their assigned rewards. Validate finite nonpositive
  saved sequence log-probabilities and finite nonnegative aggregate pre-clipping
  norms.
- Verify reconstructed A_R against logged advantages and A_V+A_C, each vector's
  zero sum, surrogate additivity, and the squared identity below. Verify digest
  chains and update/skip records. `optimizer_step` must agree with the historical
  **exact** nonzero test on logged advantages; zero/nonzero display conventions
  must not change a recorded update. A skip has unchanged digest and zero logged
  gradient norm; an actual recorded update has a changed digest.
  Exactly constant assigned rewards require every logged advantage to be exactly
  zero. A tolerated tiny nonzero coefficient cannot invent an update on that
  group; genuinely nonconstant sub-tolerance reward variation is not rounded
  into a constant group.

Reconstructed arithmetic equalities use finite `math.isclose` with **absolute
and relative tolerances both 1e-12**, and report maximum residuals. Fixed settings,
direct reward copies, strings, hashes, roles,
Booleans, integer identities, list order and population are exact. Numeric
reward/metric fields may be exact int or float but never bool. No tolerance is
enlarged after results. Any malformed field or failed identity stops analysis;
there is no successful reduced-denominator report.

## Outputs and coefficient-scale diagnostics

The complete report binds exact input hashes and current analysis module, CLI,
author tests and this plan's source hashes; hashes do not form a self-referential
cycle. Public CLI output is created exclusively at a new path after validation.
It has no automatic retry, source overwrite, partial-success or missing-file
skip. Pure artificial-fixture helpers cannot claim the published byte pins were
checked; the saved-file entrypoint must check them before parsing.

For every run/group preserve source indices, task ID, sample status/reason,
true and assigned R/V/C, p, saved log-probabilities, logged/reconstructed total
advantages, component advantages, L_R/L_V/L_C, update flag, digest identities
and the **logged total** pre-clipping gradient norm. Retain the original evidence
through its pinned input link; do not duplicate all prompt/token arrays merely
for this table.

For X in {R,V,C}, record `sum(abs(A_X))` and `sum(A_X**2)`, plus
`cross = 2*sum(A_V*A_C)`. Check:

```text
sum(A_R**2) = sum(A_V**2) + sum(A_C**2) + cross
```

Record coefficient sign opposition where one of A_V/A_C is strictly positive
and the other strictly negative. Use their signs, not a possibly underflowing
product. Keep zero cases in the denominator and report their count separately.
Record exact constant-channel/zero-component flags and raw values, without
rounding small IC variation away. Summarize each run over all 16 groups/64
attempts, with update-only counts clearly secondary. Raw component L1 and square
sums are **coefficient scale** diagnostics. Do not turn them into gradient shares,
Adam-update shares, causal percentages, a new reward choice or performance tests.
Cross terms may be negative; none may be discarded to produce positive shares.

## What cannot be identified

Let a=A_R, v=A_V, c=A_C and g_i be the unrecorded score gradient of completion i.
The total loss gradient is −sum(a_i*g_i)/4. Saved log-probabilities specify values,
not these derivatives; a total gradient norm supplies even less information.

For a≠0 with v not proportional to a, choose
`d = v - (v·a)/(a·a) * a`. Then a·d=0 but v·d=||d||²>0. Replacing unknown g_i by
`g_i + t*d_i*u` for any direction u leaves the entire total gradient—and hence
its norm—unchanged, while changing the validity component and oppositely changing
the IC component. Equal function values at the recorded parameter point can have
different local derivatives. This is a mathematical nonidentifiability example,
not an intervention on the actual model or a claim that every mixed group meets
the noncollinearity condition. Component attribution is therefore unavailable
from these logs; clipping and Adam history do not repair it.

If v is exactly zero, its direct loss-gradient term is exactly zero conditional
on the recorded group. Still, C itself is validity-gated; prior updates, SFT,
shared parameters and out-of-sample behavior remain relevant and unmeasured by
this decomposition. Neither zero validity credit nor nonzero IC credit proves
economic learning. Degenerate collinear/zero-total cases must not be described
by the noncollinear construction without its assumptions.

## Termination and claim boundary

Perform one complete saved-only analysis and an independent arithmetic review.
No new model execution, backward pass, optimizer step, market-data loading,
financial scoring, sample generation, checkpoint selection or training follows.
The scientific studies retain their original conclusions. This post-hoc
accounting may clarify them; it supplies no significance claim, new independent
replication or evidence that RL learned a useful financial researcher. There is
no required positive result and no extension if the interpretation is unchanged.
