# Inspect the Astra research experiment

The explorer requires the complete submission bank and its subsequent
assessment artifact. It renders saved evidence; it does not generate proposals,
read market data or score additional candidates. Building it first runs the
[structural and arithmetic replay](replay-astra-evidence.md). A failed replay
prevents page creation.
The builder captures the three input files once, verifies temporary snapshots
of those exact bytes, and embeds those same captured bytes. Later changes to
the original file paths cannot silently change the displayed evidence.

```powershell
python -m alpha_research_rl.astra_explorer `
  --contract artifacts/astra-agent-v1/contract.json `
  --submissions results/astra_agent_v1_submissions.json `
  --assessment results/astra_agent_v1_assessment.json `
  --source-root . `
  --output astra-explorer.html
```

Use a new output path. The command refuses to replace an existing file. The
resulting HTML is self-contained and uses no remote scripts, fonts, model calls
or data requests. Model text is escaped in the embedded JSON and displayed with
`textContent` rather than interpreted as markup.

Choose a period and proposal number to compare the three conditions side by
side. Every condition starts with the same two historical financial probes;
the controls are not entirely deprived of financial information. Only the
feedback on newly proposed formulas differs. The visible-feedback panel shows
what the broker returned after that proposal. The history disclosure contains
prior response text, its full-text hash and truncation flag, and permitted
feedback. Prefixes use the broker's Python Unicode-character limit, not a
JavaScript UTF-16 substring limit. This is not a claim to reproduce hidden
host context or the model's reasoning.

The separate selector disclosure contains the saved historical metrics used
by the common final selector. These metrics are hidden from the control actors
but available to the selector. The final selection is determined after all six
proposals, even when the reader is inspecting an earlier proposal. Its future
assessment was computed only after all 30 candidate pools were publicly frozen;
that assessment is never actor-visible evidence.

All 180 proposal records, all ten paired period differences, all five year
averages and all three contrasts remain accessible. Invalid, duplicate or
unscorable records are not dropped. The all-period denominator is retained in
the utility decomposition. Token fields are displayed separately, and missing
reports are not treated as zero. Summed call durations are not elapsed wall
time under concurrency.

The builder verifies saved structure and arithmetic, not the correctness of
market calculations or private raw streams. The periods were already
development data, with one trajectory per condition and period. Public model
hypotheses and revision notes are explanations offered by the actor, not causal
evidence that a feedback mechanism worked. Interpretation must follow the
[frozen research protocol](astra-agent-research-plan-v1.md).

## Static result figure

The [SVG](figures/astra-feedback-v1.svg) and [PNG](figures/astra-feedback-v1.png)
show all three mean oriented assessment ICs and the primary contrast in every
period. They retain the large negative 2024-H1 difference and the 2024-H2 tie.
These are descriptive values, with one trajectory per arm/period and no
uncertainty intervals; the common search cost cancels from the differences.

With the optional plotting dependencies installed, generate new files:

```powershell
python scripts/plot_astra_results.py --output-stem astra-feedback-copy
```

The script requires the complete public saved-evidence replay before plotting
and refuses either existing output. It writes SVG and PNG without a model,
market-data load or financial evaluation. The published PNG was visually
inspected for readable labels and complete period coverage.
