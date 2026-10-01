# Matched-prefix results: independent saved-number review

2026-10-01. **No numerical or evidence-integrity discrepancy found. The registered allocation rule fails: 5 of 13 strict conditions pass.** This is internal AI-assisted review, not external peer review. The reviewer previously advised the question and reviewed the protocol, implementation and historical collection. The calculations here were independently reconstructed before receiving root's result interpretation, without importing the study's analysis/replay helpers.

The reviewed complete report is [`results/astra_matched_prefix_v1.json`](../../results/astra_matched_prefix_v1.json), SHA-256 `89162112ddad384ed8917a8b1198ce94044abc90ff15e1680bfe88b66eb43c37`. Its retained `COMPLETE.json` is byte-identical. The submissions and contract hashes remain `672d93cd8faababc71a7b3b5ff3823da840061479798f0ec1f2b6eef1cc9577d` and `9f531a0cc6bffc81d010f54b49a4a717703bfef81197d75ddac890373da9b574`. No partial result was inspected. No model, market loader, evaluator, network or Git operation was invoked; only saved public records and source were read. Local audit calculations wrote a helper and its summary under ignored `.local/`.

## Independent reconstruction

Standard-library calculations used 50-digit Decimal aggregation of the saved floating-point values. They reconstructed raw-outcome direction and Q, each of the 200 branch choices and Q/G/cost identities, all 50 state-by-generator cells, ten states, five years, four contrasts and both validity/predictive decompositions. All repeated values, hosted sample standard deviations, conditional MCSE and 13 unrounded allocation booleans match. Across 4,570 floating comparisons, the maximum absolute difference was `5.55e-17`; structure, identities, integer counts and booleans were exact. Float comparison tolerance was `1e-12`, not a change to scores or selection.

The audit independently rebuilt the first-occurrence key/job order from both fixed prefixes and the 200 frozen slots. There are **133 required task/AST/direction keys: 34 exact prior-cache reuses and 99 new completed evaluations**. All 133 raw outcomes have status `ok`. Candidate slots use 123 distinct keys; the additional ten keys supply prefix evidence. The 200 candidate slots comprise 119 linked to newly evaluated keys, 79 linked to prior-cache keys and two historically unusable candidates. Repetition and reuse never shrink a denominator or create a new evaluator call.

All 99 STARTED/COMPLETED pairs match their planned jobs, raw outcomes, saved Q and ordered hash/timestamp chains; there are no ambiguous job directories or retries. The report records ten assessment task constructions and 20 initial-probe checks separately. All 786 files in the saved Gate 2 publication map match their recorded byte hashes. Its verification timestamp is `12:21:45.963655 UTC`; the assessment request is `12:33:46.038837 UTC`, and the final job completed at `12:34:35.188085 UTC`. These are checks of the retained receipt and local bytes, not a new independent network attestation. The later text-audit publication is a separate milestone, not a replacement Gate 2 timestamp.

Historical admission, directions and winners were rechecked from saved feedback: each branch selects among its two fixed prefixes and **one** new candidate. It never chooses the best of four repetitions using future Q. Copy uses exactly the baseline key, retains its nonzero Q and has G zero. Selected future validity never revises admission.

## What the numbers support

Every generator has 40 charged attempts. Candidate Q includes the fixed −1 failure value; G is the selected-factor Q minus the common prefix baseline Q. Costs here are abstract proposal costs, not trading costs.

| Generator | Valid candidates | Mean candidate Q | Mean selected Q | Mean G | Mean G − .01 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Truthful | 40/40 | −0.019742528 | −0.022428458 | −0.001098212 | −0.011098212 |
| Masked | 40/40 | −0.012992932 | −0.023925378 | −0.002595132 | −0.012595132 |
| Copy | 40/40 | −0.021330247 | −0.021330247 | 0 | −0.010000000 |
| Window edit | 40/40 | −0.018146684 | −0.021284212 | +0.000046034 | −0.009953966 |
| Grammar draw | 38/40 | −0.058293946 | −0.023385345 | −0.002055098 | −0.012055098 |

The primary truthful-minus-masked Q contrast is **−0.0067495965923**, entirely predictive rather than a validity difference. The secondary G contrast is **+0.0014969201696**, but truthful G itself is negative: this is a smaller loss relative to the prefix than masked, not positive incremental value. The simple window edit exceeds truthful in both Q and G. All five mean incremental net gains are negative.

The following four rows account for 12 of the 13 strict inequalities. Each displayed contrast must be positive; the actual comparisons use full precision.

| Truthful minus comparator | Candidate Q | Predictive contribution q | G |
| --- | ---: | ---: | ---: |
| Masked | −0.006749597 (fail) | −0.006749597 (fail) | +0.001496920 (pass) |
| Copy | +0.001587718 (pass) | +0.001587718 (pass) | −0.001098212 (fail) |
| Window edit | −0.001595845 (fail) | −0.001595845 (fail) | −0.001144246 (fail) |
| Grammar draw | +0.038551418 (pass) | −0.011448582 (fail) | +0.000956887 (pass) |

The thirteenth condition, truthful mean G `> .01`, also fails (`−.0010982116248`). The apparent truthful Q advantage over grammar decomposes as **+.05 validity − .011448582 predictive contribution**. It is not evidence of superior valid-formula predictive quality. Grammar's conditional-valid mean is −.008730470 over 38 candidates; this different denominator does not replace its registered all-40 mean.

The two failures are the already documented historical constant-zero grammar formulas at `2021-H2/grammar_draw/1` and `/3`. Both retain Q −1 without a future call. Their historical rejection leaves selected baseline Q `−.0441952878712` and G zero. All 200 selected factors are valid; candidate failure and selected-factor failure are distinct.

## All periods and conditional variability

The following paired contrasts retain every period. Ten dependent market states are not 80 independent markets; four continuations estimate conditional generation variation within a state.

| State | Truthful − masked Q | Truthful − masked G |
| --- | ---: | ---: |
| 2020-H1 | +0.005626027 | 0 |
| 2020-H2 | −0.016012789 | −0.001614760 |
| 2021-H1 | −0.022423535 | 0 |
| 2021-H2 | −0.017333517 | +0.007582545 |
| 2022-H1 | −0.013634090 | +0.005928727 |
| 2022-H2 | −0.008068923 | 0 |
| 2023-H1 | −0.001122235 | 0 |
| 2023-H2 | 0 | 0 |
| 2024-H1 | +0.025146714 | −0.001930629 |
| 2024-H2 | −0.019673620 | +0.005003318 |

| Year, equal half-year average | Q contrast | G contrast |
| --- | ---: | ---: |
| 2020 | −0.005193381 | −0.000807380 |
| 2021 | −0.019878526 | +0.003791273 |
| 2022 | −0.010851506 | +0.002964364 |
| 2023 | −0.000561117 | 0 |
| 2024 | +0.002736547 | +0.001536345 |

The prespecified primary conditional generation MCSE is **.0021274762822**, independently obtained from `sqrt(sum_t(s_truth,t²/4 + s_mask,t²/4))/10`. It is an unpaired variance formula: matching repetition numbers does not establish common random numbers. It assumes independent fresh provider draws conditional on fixed states, an unverified assumption. Nine of the 20 hosted state/condition cells have zero observed Q sample variance; four identical observed values do not prove a deterministic policy or no rare failures. This MCSE does not measure market-sampling, training, prompt-selection or provider-drift uncertainty and supplies no significance or confidence guarantee.

## Decision and scope

The evidence does not support additional allocation under this version's rule. Preserve the failed gate and stop this version without extra draws or tuned prompts. The result is specific to this fixed one-step prompt, supplied historical metrics, controls and reused development periods; it does not establish that numerical feedback is generally harmful or that hosted research agents cannot work. The masked condition retains common probes and potentially inferable information, rather than being an information-free control. No profitability, untouched-holdout, broad causal, long-horizon discovery or Astra weight-training claim follows.

The local independent helper SHA-256 is `d382a23e033c73b3c3087d595e86b412e0c51a9a631209fefbf3f037abc364a1`. This review supplements the [historical collection audit](astra-revision-collection-review-v1.md); it does not silently convert that earlier future-unexposed audit into an outcome review.
