# Original Astra bank: historical factor-behavior diagnostic v1

2026-10-01. Adopted only as a bounded post-hoc descriptive diagnostic. Root publishes the final plan and implementation before the one actual calculation. The original financial studies, selections, outcomes and stopping decisions stay unchanged. No new model calls, proposals, training, forward-return targets or predictive evaluations are permitted.

## Question and value

The original Astra bank contains 95 distinct canonical ASTs, but that does not quantify different cross-sectional signal behavior. The Qwen rank diagnostics concern another population. This one calculation can complete the original Astra description: how close were all its proposals to twelve fixed reference formulas, and how similar were the six proposals within each episode? Either redundancy or dissimilarity is informative about this finite bank. Neither establishes original economic insight, alpha, or a reason to reopen a failed study. The references were Qwen's teacher grid; they are **not known Astra training teachers**.

## Frozen population and inputs

- Original submissions: `results/astra_agent_v1_submissions.json`, SHA256 `89b9cd42d4d248393c2c3c2b9f29714fb9ba023b511d9b3741196d99a321def7`.
- Original contract: `artifacts/astra-agent-v1/contract.json`, SHA256 `63848687bb44ea7d835b0a2d6ebe88d95dd7ed7257c8ca27dd216a6c37d8b17a`; validate its ten task metadata/probe files and the original structural submission contract without assessment inputs.
- Exactly ten tasks, 2020-H1 through 2024-H2, three original arms, six attempted slots per episode: 30 episodes and 180 slots. No selected-only, valid-only, distinct-AST-only, outcome-based or arm-based filtering. Validate exact task/arm/attempt identities, saved raw expressions, canonical ASTs, and all expected slot counts before calculation. Preserve the saved feedback validity flags as historical metadata, not a filter.
- Pinned 49-industry-portfolio archive: raw SHA256 `8f394fe34bea54d41b9aafed410425ee8f8e252ede3c71a7c1cd20bab83040de`. Use the existing loader cap and each task's causal prefix. No assessment artifact is an input. Record source hashes of the diagnostic, its tests and this plan, plus the actual reused loader/DSL/rank/prefix dependency files and relevant runtime versions.

## Exactly what is calculated

Use `FeedbackRankAnalyzer.from_panel` and its existing pair metric. For each task reconstruct the preceding half-year, retaining the original five-session purge and earlier history needed by causal expressions; assert reconstructed bounds against the sealed task metadata. The latest signal interval is the purged 2024-H1 interval. Never construct `FinancialTask`, call `feedback_score`/`evaluate`, or construct forward-return labels. The second argument of the generic daily rank routine is another factor array, not a return target.

Order jobs by task, arm in original contract order, attempt, then reference index; within each episode use slot pairs `(i,j)` with `i<j` lexicographically. Evaluate expressions **as written**, without applying a future-derived sign or rewriting the program. Retain signed mean daily Spearman, its absolute value, daily standard deviation, paired-cell coverage, valid-date count, required-date count, total signal dates, status and reason.

1. Each of all 180 slots is compared with every formula in the frozen twelve-formula `TEACHER_GRID` order: **2,160 requested comparisons**. Retain all twelve rows. Its nearest supported reference is the largest **absolute value of the mean daily Spearman**, ties resolved by earliest reference index. This is not the mean of absolute daily correlations.
2. Each of all 30 episodes retains all `choose(6,2)=15` pairs: **450 requested within-episode comparisons**. Duplicate or aliased slots remain charged and present.

Use existing support rules unchanged: paired-cell coverage at least 0.8; valid dates at least `max(min(20,L),ceil(0.8*L))`; at least three finite paired assets and nonconstant ranks per valid day. Retain the existing near-exact flag `abs(mean daily Spearman)>=1-1e-10`, only for supported pairs. This is an inherited diagnostic tolerance, not a newly optimized threshold, a mathematical equivalence certificate, or a rule for constructing transitive classes.

Computational caching may share a numerical/support result for a task and canonical-AST pair, but may not remove any requested slot. Bind raw expression and slot provenance independently of the cached body: the existing analyzer cache can retain the first expression spelling. Record requested comparisons (2,610) and unique computed pair count separately. No repeated request is reinterpreted as an independent observation.

## Summaries, failures and interpretation

Preserve every comparison even if invalid or unsupported; similarity is null when undefined, never invented zero. A supported nearest reference can be reported when some references are unsupported, but report its supported-reference count out of twelve. If none are supported, nearest reference is null. Do not replace formulas, change support or retry with alternative expressions. Source/population/provenance mismatches or infrastructure failures stop output completion, rather than becoming factor failures.

For each episode, each arm and the full bank report requested/supported/unsupported counts and mean/median among supported values for (a) each slot's nearest-reference similarity and (b) within-episode similarity; retain the relevant 6/60/180 and 15/150/450 denominators. Report inherited near-exact counts together with supported and total counts, not as a significance test or diversity score. All ten per-period episode summaries remain visible. No inference that the arm with lower similarity is better, no confidence intervals over slots, no threshold search, no clusters and no future-utility join.

Signed correlations distinguish the observed sign relation, while the absolute metric deliberately treats a sign flip as similar behavior. It measures rank resemblance over these historical portfolios, at these dates and pairwise finite supports. Different pair supports and a tolerance do not define an equivalence relation. Low similarity to a small reference set is not proof of novel factors; high similarity does not prove equality on other data. The post-hoc calculation is not a new confirmatory financial result.

## Minimal deliverable and replay

The new standalone wrapper owns this schema; the old analyzer/scorer remains unchanged. Write one exclusive new `results/astra_feedback_diversity_v1.json` with status identifying completed post-hoc historical rank diagnostics, all 180 slot records, all 30 pair lists, input/source/runtime identities and the limits above. Fail if the output already exists. Preserve a partial/failure marker for an interrupted actual calculation; do not overwrite or silently restart the canonical run.

Saved-only replay validates the exact population, schemas, input identities, each comparison's slot/reference ownership, support/status consistency and all summaries using saved aggregates only. It imports no market loader or factor evaluator and claims arithmetic/provenance replay, not independent regeneration of ranks from data. Before the actual calculation use small artificial arrays for sign/monotone aliases, constant/unscorable behavior, missing support, canonical-string cache provenance and exact slot retention. Root alone performs the actual data calculation after review/publication. No new investigation follows automatically from its outcome.
