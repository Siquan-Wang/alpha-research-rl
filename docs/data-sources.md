# Public data sources and provenance policy

Verification date: 2026-09-30. Availability and terms can change. This is a source-selection record, not a claim that an adapter or a completed market experiment exists. Use existing/free resources only; do not substitute paid APIs, purchased datasets, or private workspace files.

## Recommended first numerical market task

Use daily value-weighted returns of the official 49 industry portfolios for a cross-sectional industry-portfolio return-ranking task. This low-friction choice avoids an account, API key, and stock-level corporate-action/universe assembly. It cannot establish stock-level alpha or executable profitability.

Primary links:

- [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html).
- [49 industry portfolio construction and coverage](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_49_ind_port.html).
- [Official daily CSV ZIP](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/49_Industry_Portfolios_daily_CSV.zip).

The details page currently lists daily coverage from July 1, 1926 through August 31, 2026 and describes annual end-of-June industry assignment using SIC codes. It carries Fama/French copyright. The library states that histories are reconstructed monthly and can change; it also documents the FIZ-to-CIZ source transition beginning January 2025. Therefore freeze one download and describe it as revised historical data, not a historical point-in-time vintage. [Official details](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_49_ind_port.html), [official library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html).

The official pages offer public downloads, but no blanket redistribution license was verified. Repository policy is **downloader-only**: do not commit raw CSV/ZIP, converted return panels, or wealth-index panels. Commit original downloader/parser code, attribution, source URLs, a provenance/hash manifest, and compact original experiment summaries. Free access is not a verified grant to relicense downloaded data under the code license. This conservative publication rule is a project decision, not a claim that the source explicitly bans every use.

The HTML pages and their official download link were verified. The web reader could not render the binary ZIP; a successful local download, archive inspection, numeric parsing, and recorded SHA256 remain required before calling the data usable.

## Adapter requirements

These are proposed implementation requirements, to be reconciled with the actual parser rather than presumed completed:

1. Download the official URL to an ignored local data directory; log response status, retrieval UTC time, raw file name, size, SHA256, and local manifest path. Bound retries, inspect ZIP entries, reject unsafe paths, and preserve the raw snapshot.
2. Select the daily value-weighted return table explicitly. Do not concatenate value-weighted and equal-weighted sections or monthly/annual tables. Validate exact headers, increasing unique daily dates, expected asset count/order, and numeric cells. Record table name and parser version.
3. Convert source percent returns to fractions once. Convert documented missing sentinels such as -99.99/-999 to missing before scaling and compounding. Validate bounds and report missing counts. No silent interpolation, backfill, or future-assisted repair. Reject unsupported or ambiguous layouts rather than guessing.
4. The data provide portfolio returns, not individual-stock closing prices or trading volume. A schema may store `close` as a derived cumulative wealth index for compatibility, but metadata must say `price_semantics=cumulative_wealth_index`, `synthetic=false`, and list available features. Disable volume expressions and represent absent volume as unsupported/missing; never fabricate observed volume.
5. For a complete segment, choose a common arbitrary initial wealth and compound `W[t]=W[t-1]*(1+r[t])`. The first retained row cannot both be an initial wealth and preserve an unknown prior-period return. Either prepend a correctly dated prior observation/base row or explicitly mark the first recomputed return missing. Missing-return segments must not be bridged silently by inventing returns.
6. Prefer causal return transformations and rolling ratios; arbitrary wealth-index level rankings depend on their initialization and are not economic price signals. Define whether cumulative wealth begins at the source start or a frozen common base date; record it and avoid level-based candidates in the first return-only task.
7. Compare recomputed one-day and compounded h-day labels with the original return series on hand-checked rows. Validate feature support before an episode begins. Keep downloaded and converted data outside public Git history.

Industry portfolios are correlated aggregates with changing constituents. A source-defined stable list of 49 industry series is not a fixed list of 49 stocks. The series do not provide stock memberships, tradeable vehicle costs, bid/ask execution, or portfolio-level turnover needed for a realistic trading backtest. These are task limitations rather than synthetic-data caveats: the returns themselves are historical market data.

## Alternatives checked

| Source | Access and fields | Decision |
| --- | --- | --- |
| [Binance official public-data archive](https://github.com/binance/binance-public-data) | Public daily/monthly spot/futures archives, OHLCV klines, checksums; spot timestamp units change from 2025. | Possible separate noncommercial crypto benchmark, not a stock substitute. Review dataset terms and historical universe before use. |
| [Qlib official repository](https://github.com/microsoft/qlib) | Official README currently says its official dataset is temporarily disabled and points to community data. | Do not make disabled official data a required reproducibility dependency; a community mirror needs separate provenance and permission checks. |
| Original synthetic generator | Entirely generated locally with explicit seeds/regimes. | Public fixtures and numerical/simulator studies are allowed; never count their results as financial evidence. |

Binance's current [Vision Dataset Terms](https://raw.githubusercontent.com/binance/binance-public-data/master/TERMS_AND_CONDITIONS.md), version 1.0 dated August 26, 2026, grant free access under CC BY-NC-SA 4.0 for specified noncommercial use. They expressly govern derived indicators and models and require attribution/share-alike for redistributed derivatives. The repository's MIT wording is not an unrestricted dataset license. Keep any eventual crypto-derived artifacts separately attributed/licensed; downloader-only is the default until output obligations are checked. This source is not necessary for the initial industry benchmark.

The Binance [official README](https://github.com/binance/binance-public-data) documents per-archive checksum files and later archive corrections. Its example URL structure is `https://data.binance.vision/data/spot/monthly/klines/{SYMBOL}/{INTERVAL}/{SYMBOL}-{INTERVAL}-{YYYY-MM}.zip`; existence of every chosen symbol/month still requires verification. Do not build a historical universe by querying only today's active symbols: that introduces survivorship bias. A multiasset crypto panel needs frozen as-of inclusion criteria, listings/delistings, quote-currency policy, UTC bars, and missingness handling.

## Minimum provenance manifest

Each experiment references a manifest containing source and details URLs, retrieval time, raw SHA256/bytes, archive member, selected table, source return units, conversion formula, ordered assets, retained date range, dropped dates, missing sentinels/counts, wealth-index initialization, supported features, parser revision, and terms/attribution review date. Any new download is a new snapshot even when its filename is unchanged.

Publish commands and hashes sufficient to identify the intended snapshot, while explaining that revised upstream data may prevent byte-identical reconstruction later. Do not promise permanently available files or redistribute restricted snapshots merely to repair upstream reproducibility.
