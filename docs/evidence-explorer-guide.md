# View and rebuild the evidence explorer

[`evidence-explorer.html`](evidence-explorer.html) is a self-contained record of
the completed one-step financial proposal experiment. It includes the full
registered comparison, RL–SFT failure/IC decomposition and every saved draw.
It runs no agent, model inference, market scoring or external request.

## Open it locally

Download the HTML file or use a local repository checkout, then double-click
`docs/evidence-explorer.html` to open it in a browser. No Python environment,
model weights or market-data download is required to view the file.
GitHub's normal `.html` file view shows source; it is not an interactive HTML
preview. The downloaded file contains its scripts, styles and evidence data.

Alternatively, run this from the repository root and open the loopback URL:

```bash
python -m http.server 8765 --bind 127.0.0.1
```

Open [the local explorer](http://127.0.0.1:8765/docs/evidence-explorer.html).
Keep that terminal running while viewing; stop it with Ctrl+C when finished.

## What is included

There are **540 retained records**: three checkpoints × ten half-years × two
evidence conditions × (eight stochastic draws + one greedy draw). The registered
primary policy comparison uses all 240 true-evidence stochastic draws, 80 per
checkpoint. Draws are Monte Carlo samples, not independent market periods.

The first displayed record is SFT, 2020 H1, true evidence, stochastic draw zero.
Nothing is selected for its reward. Checkpoint, task, evidence, decoding and draw
controls expose the whole archive, including ten failed proposals. The overview
includes uniform-grid, feedback-greedy and fixed lag-1 references. Both RL seeds,
every signed task/year difference and the separate failed sequential CPU gate
remain visible. This is descriptive development evidence, not a final holdout,
profitability result or learned full research agent.

The observed-probe panel comes from the actual saved prompt tokens. Submitted
expression feedback and later assessment are separately labeled evaluator
outputs; they were not additional probes observed by the actor. Generated text
is displayed verbatim as text, including malformed output. Strict JSON is the
registered primary parser; the secondary fence-tolerant analysis remains in the
saved JSON reports. The page contains aggregate scoring metrics and public
completion/prompt text, without raw market arrays, weights or machine paths.

## Exact rebuild command

Activate the repository's Python environment and run from its root:

```bash
python -m alpha_research_rl.evidence_explorer \
  --sft artifacts/development/financial-sft-transfer-v1.json \
  --rl23 artifacts/development/financial-rloo23-transfer-v1.json \
  --rl29 artifacts/development/financial-rloo29-transfer-v1.json \
  --analysis results/financial_proposal_paired_v1.json \
  --gate artifacts/development/sequential-grid-gate-v1.json \
  --tokenizer models/Qwen3-0.6B \
  --output docs/evidence-explorer.html
```

The builder validates the three reports and recomputes paired statistics from
their retained outcomes. It rejects missing draws and inconsistent saved
aggregates. Passing `--tokenizer` requires installed Transformers and the cached
tokenizer files; their hashes must match the recorded evaluation. Loading uses
`local_files_only=True`, without loading model weights. Omit that flag to build
without decoded actor prompts; the page then explicitly marks the observed
probes unavailable. `--gate` is also optional. No new generation or numerical
market scoring occurs in either mode.

## Unchanged input identities

These inputs remained unchanged while building the explorer and adjusting its
narrow-screen controls. The HTML also displays these SHA256 hashes, tokenizer
hashes and its builder source hash. Regenerating the presentation does not
replace the recorded financial results.

| Saved input | SHA256 |
|---|---|
| `financial-sft-transfer-v1.json` | `a1de37b17e113cbde41c42f7baa39869756dd95974748f16e89ec68545959eb1` |
| `financial-rloo23-transfer-v1.json` | `25bd93004bf47f088ad701fa4e2856f0843b040b468c6d21e6c98565daec6c85` |
| `financial-rloo29-transfer-v1.json` | `ddae0c86b9d38c7706efaea0635771c4480e4503a5da4e3464ef5275abd66c73` |
| `financial_proposal_paired_v1.json` | `b16ce069aaab127f3cb11dc7b71d627f35b8a7f4d10303cd7cd8a51959fccc44` |
| `sequential-grid-gate-v1.json` | `488424123a6a70273e93107d036a9283fba156bfe9e036f77a7fba53e881043c` |
