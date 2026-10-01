# Offline explorer for the post-hoc Astra pool diagnosis

This separate view displays the completed [frozen-pool diagnosis](astra-pool-diagnosis-plan-v1.md). It keeps all 180 original proposal slots, all ten development periods, all three conditions, and all four selection rules. The oracle is an **unattainable hindsight oracle**: it chooses using future outcomes and is at least as good as original selection by construction. This guarantees only a nonnegative gap, not a strictly positive one. A positive gap does not demonstrate that a feasible selector can find those candidates.

Build a new self-contained HTML file after the diagnosis has completed:

```powershell
.venv\Scripts\python.exe -m alpha_research_rl.astra_pool_explorer `
  --contract artifacts/astra-pool-diagnosis-v1/contract.json `
  --execution-dir artifacts/astra-pool-diagnosis-v1/execution `
  --report results/astra_pool_diagnosis_v1.json `
  --source-root . `
  --output docs/astra-pool-explorer.html
```

The output must be a new path outside the execution directory. The builder refuses incomplete or ambiguous execution evidence, unexpected job files, changed bound sources or inputs, and a report that differs byte-for-byte from retained `COMPLETE.json`. See the [saved replay guide](reproduce-astra-pool-diagnosis.md) for the complete evidence requirements.

The builder captures the bound public files, completed execution records, and report bytes. It recreates their relative paths in a temporary directory and runs saved-record replay on that immutable snapshot. Only those verified report bytes enter the page. This prevents a later change to the original file from changing the rendered evidence. The page includes the exact captured JSON text, its SHA-256, the replay result, and the renderer source hash. A copied HTML file is a presentation artifact, not a digital signature; regenerate it from the public evidence to verify it independently.

`python scripts/replay_published_astra_pool.py` verifies both the published complete report and `docs/astra-pool-explorer.html`. It rebuilds the payload through saved snapshot replay, checks embedded report text and all metadata exactly, and compares the full page with the renderer. Only outer HTML line endings may differ; the report bytes encoded inside the JSON remain exact. A missing page or changed payload, template, or script fails verification. The existing Python `verify_published_pool` function remains available for report-only checks.

The page opens without a server, login, package runtime, or network connection. Building it needs the project's Python dependencies but does not require the pinned scoring runtime, raw market archive, Codex login, model access, or financial evaluation. It neither verifies package binaries nor reconstructs hidden model context. All imported financial-task construction and scoring remain outside saved replay.

Use the period and condition controls to inspect six charged candidates at a time. Each row shows the original expression, historical feedback IC, the direction fixed by that feedback, future oriented IC and status, fixed-cost utility, AST-node count, and selector flags. Details retain the key and cache provenance, including the expression actually evaluated. Nulls display as `unavailable`; invalid or unscorable candidates remain in their original slots at utility −1.06. The first-proposal and minimum-AST rules do not skip a candidate because its future outcome failed.

The summary includes all twelve condition/selector combinations, every period, every year, all three pairwise contrasts, validity denominators, and the saved allocation rule. All selectors retain the original cost of 0.06. Conditional IC means carry their valid-only denominator. The identity ΔS = ΔO − ΔR describes arithmetic; it is not a causal attribution of generation versus selection. AST differences do not establish distinct economic signals.

The diagnosis was designed after the original selected outcomes were known and uses previously examined 2020–2024 development periods, with one realized trajectory per condition and period. Neither oracle headroom nor any displayed positive value establishes fresh holdout performance, profitable alpha, factor originality, learned selection, or Astra weight training.

Renderer tests use synthetic evidence only. They exercise complete snapshot replay without market-data/runtime access, read/verify/embed races, missing and tampered records, exact report bytes, inert hostile text and lone surrogates, all 30 control states, all 180 slots, selector flags, nulls, failure penalties, and output collision refusal. The tiny Node DOM tests check behavior and data retention; they do not substitute for browser visual inspection.
