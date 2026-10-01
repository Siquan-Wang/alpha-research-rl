# Sealed confirmation: standalone interface-validation protocol v1

2026-10-01. Adopted for implementation and review; the canonical outcome bank has not been generated. Publication of the completed protocol, source, tests and prepared contract must precede its single run. This validates a **new finite synthetic interface**, not `FinancialTask`, real-market p-values, Astra, GenAI superiority or reinforcement learning. It does not extend any completed financial study.

## Question and fixed population

Does the interface keep confirmation targets unavailable until every legitimate predictor is frozen, preserve its exact null rejection law after feedback-driven selection, and retain power for a known direction? Explicit leaking controls test structural detection. Their naive statistical rejection rates are diagnostics, not calibrated inference or additional pass criteria.

Use six binary features and two disjoint sets of 256 rows per panel, called **search** and **confirmation**. Rows have no nominal market assets, chronology or overlapping-return interpretation. In the ideal generative law all feature bits and target-noise innovations are independent. A feature bit 0 maps to −1 and 1 to +1.

The complete fixed bank comprises 512 null panels, `null-0000` through `null-0511`, and 128 planted panels, `planted-0000` through `planted-0127`. Each panel is shared by all configurations; matched arms are not additional independent panels. There is no feasibility bank, seed substitution or data-dependent budget extension.

Exactly four SHAKE256 streams per panel use ASCII input
`sealed-confirmation-v1|731|{law}|{index:04d}|{component}`.
The law is `null` or `planted`; components are `search_features`, `confirmation_features`, `search_noise`, `confirmation_noise`. Consume bytes from least-significant to most-significant bit and flatten row, then feature. Request exactly the required whole bytes. No shared mutable RNG state is used.

Null labels are independent noise bits mapped to ±1. For planted labels define `H=x[0]*x[1]`. Read two noise bits as `u=bit0+2*bit1`; set `Y=H` for `u=0,1,2`, otherwise `Y=-H`. Thus `Pr(Y=H|X)=3/4`. The laws concern ideal independent bits. Domain-separated pseudorandom streams provide reproducibility, not proof of independence.

## Candidates and search contracts

The finite library contains masks 0 through 63. `phi_m(x)` is the product of features selected by mask m; empty mask 0 gives constant +1. A chosen predictor has one mask and orientation ±1. This is a fixed 128-direction class, not a factor-discovery claim.

One feedback request returns exact integer alignment `A=sum(phi_m(X_i)*Y_i)` and denominator 256. Orientation is +1 for `A>=0`, otherwise −1. Ranking uses `abs(A)`; an exact tie preserves the earliest attempted candidate.

- **Fixed search:** request masks 0 through 31 in that order, exactly 32 attempts.
- **Adaptive search:** first request mask 0. At attempt `r=2,...,32`, request `incumbent_mask XOR (1 << ((r-2) mod 6))`. Update the incumbent by the same absolute-alignment/earliest-tie rule. Record all 32 requests, including repeated masks; no skipped duplicates, uncharged neighbor queries, retries or replacement proposals.

The search implementation receives only its algorithm identifier and a feedback callable. Neither seeds/RNGs, confirmation targets nor a confirmation-owner object are search arguments or callback payloads. The correct callback owns search features/labels only. Library descriptions and integer responses contain no confirmation information. This is an auditable argument/access boundary, not a claim that Python or the filesystem prevents adversarial introspection.

## Per-panel seal before target materialization

The canonical runner first writes a durable panel STARTED record. It generates search features/labels and confirmation features, but **does not yet generate confirmation noise or targets**. Both correct searches finish. From their selected masks/orientations and confirmation features, construct their entire 256-element prediction vectors.

Also construct the planted oracle vector H (mask 3, positive orientation) and the positive constant base vector for the orientation-only fault. Before the first confirmation target is materialized, durably write the full search transcripts followed by one seal record binding:

1. Both preceding complete 32-attempt correct-search transcripts and selected identities, using their exact canonical hashes and the append-only event hash chain.
2. Both complete correct-search confirmation prediction vectors, the full H oracle vector and the positive constant base vector.
3. Canonical provenance and vector hashes, the confirmation batch's seal identity, and the preceding event identity.

The legitimate batch expects exactly the fixed, adaptive and oracle predictor IDs. All must be added before it seals; equal vector lengths and unique IDs are mandatory. The constant base is bound in the same outer durable seal, without creating a fourth calibration arm. Only after that write succeeds may the runner call the confirmation-label materializer. The same targets are then used for every configuration of this panel. Target hashes and any saved target values enter records only after sealing.

The interface permits one reveal for each batch and rejects later mutation or repeated reveal. A mutable input vector/provenance supplied to freezing must not mutate the frozen copy. The runner stores enough synthetic features, labels, vectors, traces and event identities for later saved-evidence reconstruction; these are new artificial bits, never market data.

## Explicit leaking controls

After legitimate sealing/reveal, run the following intentionally invalid configurations against the same confirmation data:

- **Fixed selection plus orientation fault:** the 32-mask fixed search obtains its feedback from confirmation labels before its predictor is frozen.
- **Adaptive selection plus orientation fault:** the 32-attempt adaptive search obtains confirmation feedback before its predictor is frozen.
- **Orientation-only fault:** exactly **one** recorded request for constant mask 0, followed by choosing its sign from confirmation alignment. There is no candidate search, 32-request padding or equal-search-budget claim for this diagnostic.

Every leaking feedback access is recorded before the corresponding faulty batch's seal. Its report must be `PROTOCOL_INVALID`; any computed one-candidate tail is labeled `naive_diagnostic`, with no valid confirmation result. The first two faults combine selection and orientation dependence. The orientation-only control isolates the fitted-sign defect. Deliberately invalid controls do not become valid because their realized rejection count happens to be small.

Structural tests change confirmation targets while preserving search inputs and check that correct pre-reveal transcripts, vectors and seals remain identical. Test materialization/write order and failure retention explicitly. Such tests and access witnesses supplement, rather than prove, the null calibration claim.

## Exact statistic, thresholds and calibration family

For predictions and labels in ±1, K is the number correct and M the number of nonzero predictions. All canonical library predictions are nonzero, so M=256. A general helper may accept zero abstentions: M=0 means p=1, reject=false and accuracy unavailable. It does not drop a panel. Malformed values, mismatched lengths, source/identity errors or exceptions are failures, not abstentions or non-rejections.

A correct null predictor is frozen independently of confirmation labels, conditional on search information and confirmation features. Therefore `K ~ Binomial(256,1/2)`. Use the one-sided exact tail
`p(K)=sum_{j=K}^{256} C(256,j)/2^256`.
The fixed threshold is `alpha=1/20`; reject iff
`20*sum_{j=K}^{256} C(256,j) <= 2^256`.
Use inclusive comparison and exact integer/rational arithmetic, without rounded p-values or normal approximations. This is per-panel Type I error for one frozen selected predictor, not FDR control over a research portfolio.

Let `k_star` be the smallest rejecting K and `pi0=p(k_star)`. Null discreteness means pi0 need not equal .05. For each correct search algorithm the 512-panel rejection count has ideal law `Binomial(512,pi0)`. Their matched counts may be dependent.

The positive oracle has `K ~ Binomial(256,3/4)` and exact rejection power
`pi1=sum_{j=k_star}^{256} C(256,j)*3^j/4^256`.
Its 128-panel planted rejection count has law `Binomial(128,pi1)`. Its expected signed score is .5. Another fixed signed vector S has conditional expected signed score `.5*mean(S*H)`; correlated alternatives are not intrinsically false discoveries because their mask differs from 3.

The calibration family contains exactly three checks, total false-alarm allowance `delta=1/100`, Bonferroni allocation `1/300` to each:

1. Correct fixed-search null rejection count `<= U`.
2. Correct adaptive-search null rejection count `<= U`.
3. Planted-oracle rejection count `>= L`.

U is the smallest integer with `Pr(Binomial(512,pi0)>U) <= 1/300`.
L is the largest integer with `Pr(Binomial(128,pi1)<L) <= 1/300`.
The prepare step computes and saves exact pi0/pi1, k_star, U/L and boundary-tail certificates **without generating any panel**. Lossless large integers may use explicitly tagged hexadecimal strings. Display decimals never determine decisions. The union bound does not require independence between the three checks. Its ideal-law guarantee concerns this family, not arbitrary real-world inference or successful detection of every fault.

The orientation-only invalid control has exact naive null rejection rate `2*pi0`, because opposite one-sided tails are disjoint. Its probability of exceeding U across 512 panels is `Pr(Binomial(512,2*pi0)>U)`. Each selection-plus-orientation fault retains at least the constant candidate, so its naive null rejection probability is at least `2*pi0`; the same detection probability is a lower bound, not its exact power. Save these deterministic expectations before outcomes. Observed fault exceedances are **descriptive only** and never alter the validation pass/fail decision.

## Preparation, publication and one-run accounting

`prepare` computes only protocol/seed identities, exact thresholds and source hashes. It must not invoke feature/noise generation, construct simulated labels or inspect any candidate canonical panel. Its fresh contract binds this plan, runner, core, author/reviewer tests, complete panel order and a single canonical execution/result directory. Preparation uses exclusive creation and never overwrites an existing artifact.

After review, root publishes those exact files and the prepared contract, anonymously retrieves their GitHub bytes, and saves a receipt with actual commit, UTC time and complete path/SHA map. The runner checks receipt schema, local byte identities and time before any panel begins. The receipt is not part of its own required publication map, avoiding recursive self-reference. The runner validates the retained evidence of publication; it does not itself claim to independently repeat root's network verification.

The canonical run is null indices 0..511, then planted indices 0..127. It creates an exclusive run lock and durable STARTED record before work, then ordered per-panel STARTED, PREDICTIONS_SEALED and COMPLETED evidence. Record the one materialization event, legitimate confirmations, all three faulty transcripts/reports, duplicate counts and exact statistic denominators. Do not pool configurations as independent panels.

Each panel uses one append-only JSONL ledger, with flush/fsync on every event, and one immutable completion record. The flattened outcome records retain `protocol_status` and `statistic_role` beside their arithmetic; invalid controls always use `naive_diagnostic`. Complete synthetic feature/target arrays are stored once per panel rather than repeated per arm.

A preparation/run error writes FAILED evidence where possible and preserves all prior records. An ambiguous STARTED record, partial file, killed process or failure blocks canonical execution permanently. There is **no resume, rerun, replacement panel or overwrite** for v1. A complete report is emitted only after all 640 panels and population/integrity checks succeed. Completed output is replay-only. A rerun required by a concrete bug would need a separately named version retaining the original evidence.

The report separately records structural conformance, all three calibration booleans, and descriptive fault rejection/detection counts. An overall validation pass requires structurally correct legitimate sealing, structural invalidation of all intentional leaks, exact complete population and all three calibration checks. It does not require stochastic fault-count exceedances. Search power and selected masks on the planted bank are descriptive, not extra gates.

Saved-only replay checks the source/contract/publication identities, exact population, event order and hashes, all search decisions, prediction vectors, seals, outcomes and final report from the retained arrays. It must not call a feature/noise generator, load markets, invoke a model or write replacement evidence. This checks arithmetic and recorded access ordering; it does not independently attest that a saved array came from SHAKE256, that hidden label access was impossible, or that an unlogged process event did not occur.

## Pre-run tests and limits

Before the one actual run, use handcrafted small panels and a distinctly named artificial test-only stream namespace. Never run any canonical null/planted seed as an informal smoke test. Tests include small exhaustive binomial/two-sign enumeration, exact threshold boundaries, mutable-copy protection, all-required-predictors sealing, reveal-once behavior, label perturbation, write-before-materialize ordering, error-to-FAILED behavior, all 32 attempts/duplicates, source/publication tampering, and exclusive output preservation. A fake tiny driver population must be clearly test-only, never labeled a complete 640-panel result.

This is a CPU-only engineering regression with fixed hypotheses and known laws. No hosted/local model, GPU, network generation, purchases, financial scoring, prior study edits or new real-market periods are used. Runtime is not yet measured. Passing does not establish novel adaptive-inference theory, GenAI advantage, alpha, realistic chronological dependence or a new RL result.
