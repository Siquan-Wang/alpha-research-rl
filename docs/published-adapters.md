# Download and use the published financial adapters

The [v0.1.0 release](https://github.com/Siquan-Wang/alpha-research-rl/releases/tag/v0.1.0)
provides the exact five financial LoRA checkpoints, including the original SFT
parent. The approximately 46 MB archive contains ten adapter/configuration
files and three documentation/license files. See the
[model card](financial-adapters-model-card.md) for training and limitations.

## Verified download

From the repository root after `python -m pip install -e .`:

```bash
python -m alpha_research_rl.adapter_release fetch \
  --destination models/published-financial-v1
```

The downloader needs no model or training dependencies. It checks the archive
SHA-256, every member's hash, the exact member allowlist and the five-policy
checkpoint freeze before writing. It refuses existing destination directories.
The archive is fetched from the public GitHub release without credentials.
No inference service, cloud compute or payment is involved.

If downloading the archive manually, verify it without extraction:

```bash
python -m alpha_research_rl.adapter_release verify \
  --archive /path/to/financial-adapters-v1.zip
```

Expected identities are in
[`financial-adapters-v1.manifest.json`](../artifacts/releases/financial-adapters-v1.manifest.json).
Keep the original JSON bytes when checking the freeze hash. Do not relax hash
checks to accept a replaced file.

## Load an actual checkpoint

First install the pinned training stack and download the pinned base model using
[the financial reproduction guide](reproduce-financial-study.md#fresh-environment-and-pinned-inputs).
The base model and tokenizer are not included in this archive. Then:

```python
from alpha_research_rl.financial_policy import ProposalActor

actor = ProposalActor(
    "models/Qwen3-0.6B",
    "models/published-financial-v1/financial-sft-v1/adapter",
    trainable=False,
)
```

Other checkpoint directories are `financial-rloo23-v1`, `financial-rloo29-v1`,
`financial-placebo23-v1` and `financial-placebo29-v1`, each with an `adapter/`
subdirectory. This layout preserves the checkpoint name inferred by the
original evaluator. The original relative
base path in each adapter configuration is preserved; `ProposalActor` receives
the actual local base-model path explicitly. It loads only cached model files.

To check actual loading of all five adapters against the original trained tensor
digests, using that same cached base and CUDA environment:

```bash
python scripts/verify_published_adapter_loads.py
```

This writes a fresh local verification report. It checks the complete checkpoint
file manifests before loading, then compares named LoRA tensor digests and
parameter counts. It performs no generation, market scoring, backward pass or
optimizer update. This check does not establish identical sampled behavior on
another machine.

To rerun an evaluation after independently obtaining the exact market snapshot,
use a fresh result path, the original label and published freeze:

```bash
python -m alpha_research_rl.financial_evaluation \
  --adapter models/published-financial-v1/financial-placebo23-v1/adapter \
  --label financial-placebo23-v1 --split transfer --draws 8 \
  --freeze-manifest artifacts/development/financial-linkage-suite-freeze-v1.json \
  --output artifacts/development/local-placebo23-reproduction.json
```

The original SFT and correctly linked RL policies use
`financial-suite-freeze-v1.json`; the controls use the five-policy extension
shown above. The scorer verifies identities; new runtime/source manifests remain
distinct from the original run. Hardware and kernel differences can change
sampled draws even with identical weights. Never overwrite original reports
with rerun results or claim an exact numerical reproduction without checking.

## What remains separate

Exact model publication removes the missing-checkpoint barrier. It does not
redistribute the French raw data, certify their historical vintage, or turn
development results into an untouched test. The public upstream data file can
change; exact market replay still needs the recorded snapshot hash. CPU
reanalysis with `python scripts/replay_published_results.py` remains available
without any weights or market data.

To rebuild the archive from an original training checkout, run
`python -m alpha_research_rl.adapter_release build`. The builder reads only the
ten allowlisted files with exact freeze hashes, the pinned base license and the
model card. It will not package a whole run directory or overwrite different
release outputs. A new checkpoint or changed release content requires an
explicit new release manifest rather than changing an existing download.
