# Fixed historical-data development baseline plan

Written before running the baseline on the downloaded French snapshot.

Purpose: verify a real, numerical return-prediction pipeline independently of a
scripted research controller. These are development results; they are neither
final untouched tests nor evidence of improved LLM weights or trading profitability.

Input: official 49-industry daily value-weighted returns, pinned raw snapshot
SHA256 `8f394fe34bea54d41b9aafed410425ee8f8e252ede3c71a7c1cd20bab83040de`.
The runner retains only 2000-01-01 through 2024-12-31. No 2025+ outcome is reported
or used. Industries are portfolios with changing constituents, not 49 stocks.
Close is a cumulative wealth index; no observed trading volume is available.

Prediction target: five-session cumulative forward return at each signal date.
The last five rows of every fit and assessment boundary are purged if their
labels would reach the following period. Assessment stops at year-end; labels
crossing that boundary are excluded. Features are observable at the close of
the signal day; this is a descriptive forecasting study, without execution claims.

Frozen features for the ridge baseline: current realized return, delays 1/2/5,
and trailing means and population standard deviations at 5/20/60 sessions.
One shared cross-industry linear model is fit per year. Training rows are the
prior five calendar years; standardization uses those eligible training
date-asset samples only. Training target is mean-centered; no label or feature
from the assessment year affects fitting, imputation, scaling, hyperparameters,
feature choice, or orientation. Incomplete feature/label samples are excluded;
constant training features use scale one. Ridge alpha is fixed at 1.0 with an
unpenalized intercept and squared-error sum convention. No adaptive feedback
or hyperparameter selection is performed in this baseline.

Fixed non-trained comparators: 20-session momentum and its reversal (negative
20-session mean return). Their orientations remain fixed even if observed IC is
negative. No best-of-comparator result is selected as a performance estimate.

Development assessment time blocks: calendar years 2020, 2021, 2022, 2023, 2024.
Report each separately, plus concatenated daily Spearman IC. At least three
paired finite assets and nonconstant cross-sections are required. Report
coverage and the count of valid IC dates. No transaction cost, turnover,
portfolio return, Sharpe, or PnL estimate is inferred.

Uncertainty: fixed circular moving-block bootstrap of concatenated daily IC,
block length 20 sessions, 2,000 replicates, seed 1729, percentile 95% interval
for mean IC. Blocks are resampled separately within each calendar assessment
year to avoid bridging purged gaps; original per-year valid sample lengths are
preserved. This addresses some short-range dependence, but is not a proof of
error control, task independence, robustness to long regimes, or generalization
to stocks. Correlated methods and repeated development inspection also limit
inference. No multiplicity adjustment or significance claim is made.

Public output contains aggregate summaries, relative/source file identifiers,
snapshot hash, feature specification, chronological boundaries and provenance.
Raw returns, wealth panels, predictions, weights, and per-date IC series remain
local; no dataset redistribution license is implied. Observing these results
does not authorize tuning on a later final holdout.
