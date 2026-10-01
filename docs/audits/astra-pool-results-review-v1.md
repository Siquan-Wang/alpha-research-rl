# Astra frozen-pool diagnosis: independent saved-results review

Date: 2026-10-01. **Status: PASS for saved evidence, bookkeeping and arithmetic;
no publication-blocking discrepancy found.** This review made no model call,
market-data read or new financial evaluation. It formed its interpretation
from the saved records before reading a root-authored results discussion.

## Scope and authorship

The reviewer authored the earlier Astra v1 orchestration, independently
critiqued the next-study design, and reviewed the new diagnosis implementation
before execution. The reviewer did not author the pool diagnosis implementation
or its protocol. This is an internal independent arithmetic reconstruction,
not external peer review or a second computation of market IC from raw data.

The earlier implementation/preparation audit is
[astra-pool-diagnosis-review-v1.md](astra-pool-diagnosis-review-v1.md). The
present review concerns the actual completed evidence under the separate
post-hoc [diagnosis protocol](../astra-pool-diagnosis-plan-v1.md). Original v1
still has its original 30 selected assessment calls; the 108 additional calls
belong solely to this diagnosis.

## Evidence identities and execution order

| Artifact | SHA256 |
|---|---|
| Frozen diagnosis contract | `612b426cd843fa44956ccdbb3cc12692c8cada53590f781eef2bf3d00af81979` |
| Complete public result, 575,962 bytes | `ed50f86cbe876585b9de81c0960ca0a0a9d9c588345e82001ef5706141f0df2c` |
| Complete result body | `532cd3e053a26e3a3f72a019f9d69aa25dc2b3eaa988094b805be0f51f46442d` |
| Execution request body | `1bbd577495e3193dceceef7d653f6162289fd0d666c3ddc16c68714dc10fccba` |
| Publication receipt file | `8acd3e05a499ab141ee4ca0951cdbe211452a35483bd283c18dc258f22438027` |

The public result is byte-identical to the execution directory's COMPLETE
record. All 32 files named in the retained publication receipt match their
local bytes, including the three immutable v1 inputs, ten task mirrors,
original/new sources, plans and frozen contract. The task mirrors also match
the original v1 task-manifest hashes. The receipt and execution request agree
on publication commit `8afcf868301bd5daab0999bdfa4f2f2125187479`.

The saved order is:

| Event | UTC |
|---|---|
| Root's recorded public retrieval verification | 2026-10-01 10:11:42.099795 |
| First job STARTED | 2026-10-01 10:12:12.067207 |
| Last job COMPLETED | 2026-10-01 10:12:45.910050 |

For all 108 jobs, the reviewer checked the sealed STARTED and COMPLETED body
hashes, exact frozen job identity, contract identity, STARTED-file hash in the
completion, and byte-hash chain to the preceding completed record. Every
previous completion precedes or equals the next start, and every start
precedes or equals its completion. The first start follows the receipt time.
The directory contains exactly 108 expected job subdirectories, each with one
STARTED and one COMPLETED file, and only the request, receipt and COMPLETE
files at the execution root: 219 execution files in total. There are no
failure, ambiguous-start, duplicate-job or residual-lock records in this
completed directory.

This independently checks the retained ordering and local byte consistency.
It does not independently repeat root's remote retrieval, query Git, attest
the host clock, or prove that an unlogged action was impossible. The receipt
remains evidence of root's stated public verification rather than an
independent network audit by this reviewer.

## Reconstruction method and coverage

A separate script used only Python's standard library: JSON with duplicate
key rejection, SHA256, AST parsing, timestamp parsing, `math.fsum` and
`statistics.fmean`. It did not import the package's diagnosis analysis,
replay, market loader or evaluator. The already-reviewed prepared tables were
bound by their unchanged contract hash; selectors were additionally selected
again from their frozen feedback/AST fields during this reconstruction.

The script rebuilt each new key from its original COMPLETED raw outcome and
each reused key from the original v1 selected assessment row. For all 24
reused keys, it checked every contributing selected-row reference and complete
unmodified outcome, preserving the source expression spelling and original
cost/reward. Reconstruction of a one-call raw outcome from a v1 six-call
outcome is explicit: restore `.01` cost and the retained one-proposal reward,
then separately derive the diagnosis's `.06` cost. No cached value is treated
as a new evaluation.

For all 132 distinct keys it verified the full observed `ok` schema, exact
historical feedback and direction, zero-feedback flag, probe-reuse flag from
the two original probe ASTs, exact fixed cost, and well-formed usable feedback
and assessment metrics against their frozen task-window lengths. Each signed
future IC equals raw assessment IC times the **historical feedback-fixed
direction**, with one-call reward `IC-.01` and diagnosis utility `IC-.06`.
All 132 observed keys are valid; no exceptional-case interpretation or
invalid-result repair was needed for the real run. Failure behavior was
tested synthetically in the earlier implementation review.

The reconstruction checked:

- All 108 new outcomes, 24 reused keys, 132 key records and provenance, and
  all 180 slot mappings and costs; repeated keys retain every original slot.
- All 30 original/first/minimum-AST selections and all 30 oracle selections,
  including earliest-attempt ties and nonnegative `R=O-S`.
- Each of the 30 selector rows, all ten paired task rows, all five year rows,
  three arm summaries, and all three pairwise arm contrasts at every level.
- Full-denominator validity/predictive decomposition, conditional-valid
  counts, all-slot and unique-key validity, and the frozen allocation flags.
- Reproduction of all 30 original v1 selected utilities and exact call
  accounting: 108 started/completed, 24 reused keys, 132 keys, 180 slots,
  zero recorded model calls, new formulas and automatic retries.

Retained raw values, identities, cost fields and provenance compare exactly.
Only derived arithmetic uses the declared absolute/relative tolerance of
`1e-12`. The independent script made **4,227 arithmetic comparisons**, with
maximum absolute difference **6.245004513516506e-17**, consistent with different
floating-point summation order. These comparisons are not additional market
evaluations or independent observations. The retained review-script SHA256 is
`55af284d1861d3580f7867f3d1430f2ed4cb0217fb98d0130cd3bc9e5a601f8e`.

## Results from the reconstructed records

Each entry below is mean oriented assessment IC across **all ten tasks**.
Every selected outcome is valid, so these values equal the conditional-valid
means in this particular run. Subtract `.06` to obtain the registered mean
utility for any column, including the first-proposal rule.

| Arm | Original feedback selector | Literal first | Minimum AST | Hindsight oracle |
|---|---:|---:|---:|---:|
| Full feedback | -0.033823125 | -0.016354513 | -0.026670190 | 0.015711202 |
| Validity only | -0.027459260 | -0.024907958 | -0.007375240 | 0.024479567 |
| Withheld feedback | -0.028718764 | -0.017843582 | -0.012255223 | 0.029464473 |

All nine feasible selector/arm means are negative. Both fixed cheap selectors
improve on the original feedback selector within each arm in this realized
bank, but neither produces positive mean IC. The first-proposal diagnostic
still pays the full six-proposal cost; this study did not evaluate stopping
after one call or a one-call-cost alternative. The cheap rules were frozen
before the missing outcomes, but chosen after v1 selected outcomes were
already known. They are post-hoc descriptive controls, not untouched-holdout
validation of a newly selected rule.

All 180 slots and all 132 unique keys are valid. Each selector has 10/10
valid tasks per arm, each yearly selector has 2/2, and each arm has 60/60 valid
slots. Thus every arm-contrast validity contribution is exactly zero; all
observed contrast differences are in predictive IC. These remain different
denominators: 180 candidate slots, 132 distinct bookkeeping keys and ten
paired time tasks do not represent 180 or 132 independent trials.

The original-selector disadvantage for full feedback is reproduced, with a
descriptive decomposition into realized ceiling and selection gap:

| Contrast | Delta S | Delta O | Delta R | Identity |
|---|---:|---:|---:|---|
| Full minus validity | -0.006363865 | -0.008768364 | -0.002404499 | Delta S = Delta O - Delta R |
| Full minus withheld | -0.005104361 | -0.013753271 | -0.008648910 | Delta S = Delta O - Delta R |
| Validity minus withheld | 0.001259504 | -0.004984906 | -0.006244411 | Delta S = Delta O - Delta R |

The mean selection gaps are 0.049534327, 0.051938827 and 0.058183237 for full,
validity-only and withheld feedback respectively. Full feedback has a lower
realized oracle ceiling than both controls and a slightly smaller gap to its
own ceiling. Consequently its worse original selected outcome cannot be
described as simply a uniquely worse selector. These quantities are an
algebraic decomposition of sampled pools, not identified causal contributions
of generation and selection.

For completeness, the primary full-minus-validity decomposition retains its
signed variation by year:

| Year | Delta S | Delta O | Delta R |
|---|---:|---:|---:|
| 2020 | -0.007965431 | 0.002974474 | 0.010939905 |
| 2021 | 0.000230283 | -0.023862840 | -0.024093123 |
| 2022 | 0.018461494 | -0.039637943 | -0.058099437 |
| 2023 | -0.005110840 | 0.011562092 | 0.016672933 |
| 2024 | -0.037434831 | 0.005122395 | 0.042557226 |

Each year equally averages its two half-years. All ten individual task rows
were verified, including five full-feedback pools whose best oriented IC is
still negative. No year, task or failed slot was removed to obtain a mean.

## Allocation interpretation and claim boundary

For the registered full-feedback decision, mean oracle oriented IC is
**0.015711202473390015**, while mean oracle fixed-cost utility is
**-0.04428879752660998**. Every pool contains a valid original selected
candidate with IC greater than -1, so its oracle is a valid candidate and
`O+.06` can be read as ordinary oriented IC for this bank.

The positive-IC selection-only no-go flag is therefore **false**: an ideal
hindsight choice would achieve positive mean IC. The positive fixed-cost
utility no-go flag is **true**: no rule choosing one member from each of
these frozen six-candidate full-feedback pools, at their fixed directions
and cost, can exceed that negative mean oracle utility. This is an exact
finite-pool bound, not a significance test or statement about economic
profitability. The `.06` penalty is an abstract benchmark cost, not dollars,
transaction costs or a measured inference bill.

Positive hindsight headroom does **not** show that its winners can be
predicted from available feedback. The oracle reads assessment outcomes to
choose a different winner for each task, is unattainable as an ex ante rule,
and is not a strategy result. It cannot authorize another model call,
selector training, sign reversal, retuned threshold or expanded search.
The retained `automatic_next_experiment_authorized` flag is correctly false.

This bound excludes abstention, pooling all eighteen candidates, other
trajectories, generators or dates, and changing the prescribed cost. Nor does
the result establish whether an LLM was needed to generate the pool, whether
AST-distinct candidates represent distinct economic signals, or whether a
new chronological validation study would succeed. The run uses previously
examined 2020-2024 development periods and one sampled trajectory per
arm/task. It supports no fresh-holdout, statistical-significance, general
causal, factor-originality, profitability, or Astra weight-training claim.

## Subsequent narrative and figure check

After completing the source-first reconstruction and interpretation above,
the reviewer read `docs/astra-pool-diagnosis-results-v1.md`, inspected its saved
plot script and viewed the generated PNG. The arm means, pairwise
decompositions, ten full-feedback task rows, yearly primary contrasts and
allocation decisions agree with the independently reconstructed values at
their displayed precision. The figure shows all three arms and all ten
full-feedback periods, labels hindsight as unattainable, and identifies the
post-hoc period/cost limits. No concrete numerical transcription or claim
boundary issue was found. The only narrative edit by this reviewer added a
link to this independent results audit; no figure or scorer was regenerated.

No unresolved arithmetic or bookkeeping discrepancy was found. Remaining
limitations are evidence limits: the reviewer did not recompute market
metrics, independently authenticate publication/host time, or establish the
absence of activity outside the retained execution records. The completed
diagnosis should stop at its fixed analysis and audit boundary; any next
research experiment remains a separate explicit decision.
