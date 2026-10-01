# Reproduce the financial proposal diagnostic

This is the bounded **one-step return-formula study** in
[the registered plan](next-research-study.md), separate from the sequential
synthetic environment and constructed curriculum. These commands describe the
study procedure; they do not assert that RL improves financial prediction.
Run from the repository root, using the source version and dependency manifests
attached to the study. Keep that source unchanged from training through transfer
evaluation. Evaluation verifies the relevant prompt, tokenizer, scorer and source
hashes, not just a checkpoint label.

## Fresh environment and pinned inputs

The examples use Bash, Python 3.12 and an existing compatible NVIDIA CUDA host.
On Windows, activate `.venv\Scripts\Activate.ps1` and translate shell environment
assignments; the Python modules and arguments are identical. CPU correctness
tests need no model download or GPU. Full model training uses local hardware;
this procedure does not provision a paid service.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128
python -m pip install -e '.[dev,plots]' transformers==4.57.6 peft==0.18.1 accelerate==1.15.0
export PYTHONUTF8=1
mkdir -p artifacts/development
python -m pip freeze > artifacts/development/financial-environment.txt
```

For CPU tests only, use the PyTorch `/whl/cpu` index instead. The public CI
`training-math` job uses that index and these four pinned training packages on
Python 3.12. Other resolved packages and hardware can affect numerical replay;
preserve the full environment and run manifests rather than claiming bitwise
reproducibility across machines.

Download the historical model revision explicitly. The convenience
`model_setup` CLI resolves the revision available at download time, so it alone
does not reproduce the revision below.

```bash
python - <<'PY'
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download
from alpha_research_rl.artifacts import write_json

model_id = "Qwen/Qwen3-0.6B"
revision = "c1899de289a04d12100db370d81485cdf75e47ca"
destination = Path("models/Qwen3-0.6B")
info = HfApi(token=False).model_info(model_id, revision=revision)
license_name = (info.card_data or {}).get("license")
assert info.sha == revision and license_name == "apache-2.0"
snapshot_download(repo_id=model_id, revision=revision, local_dir=destination,
                  token=False, allow_patterns=["*.json", "*.safetensors", "*.txt",
                  "*.model", "LICENSE*", "README.md"])
write_json(destination / "source-manifest.json", {
    "model_id": model_id, "revision": revision, "model_card_license": license_name,
    "source": f"https://huggingface.co/{model_id}/tree/{revision}",
    "weights_published_in_repository": False,
})
PY
```

Obtain the official French 49-industry daily ZIP through the repository's
immutable downloader. It checks the archive and writes a provenance sidecar;
it refuses to overwrite an existing snapshot.

```bash
python - <<'PY'
from alpha_research_rl.french import download_french49

manifest = download_french49("data/raw/french49-v1")
expected = "8f394fe34bea54d41b9aafed410425ee8f8e252ede3c71a7c1cd20bab83040de"
if manifest["raw_sha256"] != expected:
    raise SystemExit("Source snapshot changed: stop exact-study reproduction.")
PY
```

The official URL is a changing upstream snapshot. If it no longer serves this
hash, exact input replay requires an independently retained lawful copy with
that hash. Do not change the registered hash to make a new download pass;
register a new study version instead. Raw ZIPs, converted panels and model
weights remain local and gitignored. No permission to redistribute French data
is assumed. The loader exposes industry-portfolio returns, with no volume or
individual-stock universe, and caps this study at 2024-12-31.

After both downloads, keep model access offline:

```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
python -m ruff check src tests
python -m pytest -q -p no:cacheprovider
python -m alpha_research_rl.financial_tasks \
  --input data/raw/french49-v1/49_Industry_Portfolios_daily_CSV.zip \
  --output artifacts/development/financial-preflight.json
python -m alpha_research_rl.sampling_probe \
  --output artifacts/development/financial-sampling-preflight.json
```

The preflight computes training-only opportunity diagnostics. The sampling
probe must pass before RL: processed logits must equal raw cached logits, with
finite cached/full-forward log probabilities and maximum token discrepancy at
most 0.25. Financial actors use FP32, disable TF32 and model-default generation
merging, and sample at temperature 1, top-p 1, top-k 0.

## Train once, inspect feasibility, then run both RL seeds

Defaults below use the pinned model and ZIP paths above. Choose fresh output
directories rather than overwriting a completed experiment.

```bash
python -m alpha_research_rl.financial_training sft \
  --output models/runs/financial-sft-v1
python -m alpha_research_rl.financial_evaluation \
  --adapter models/runs/financial-sft-v1/adapter --label sft \
  --split feasibility --draws 8 \
  --output artifacts/development/financial-sft-feasibility.json
python -m alpha_research_rl.financial_training rloo \
  --adapter models/runs/financial-sft-v1/adapter --seed 23 \
  --output models/runs/financial-rloo-seed23-v1
python -m alpha_research_rl.financial_training rloo \
  --adapter models/runs/financial-sft-v1/adapter --seed 29 \
  --output models/runs/financial-rloo-seed29-v1
```

SFT starts from the pinned base model, uses fixed seed 61 and three epochs over
32 training half-years (2002–2017), totaling 96 updates. The CLI's `--seed`
argument applies to the `rloo` phase; do not use it to claim a different SFT seed.
The privileged teacher chooses from 12 formulas using feedback only. Its access
exceeds the actor's two probe summaries and is recorded in the manifest.

Feasibility covers 2018–2019 and is a behavior diagnostic, not the transfer
comparison. Each RL run starts independently from the same SFT adapter. It uses
four fresh proposals per group and 16 fixed training episodes: H1 in even years,
H2 in odd years, one episode per year from 2002 through 2017, with seed-dependent
order. After eight groups, a run stops if no group contains at least two legal
distinct canonical ASTs with usable future-IC range greater than `1e-4`.
Invalid-versus-valid reward spread alone does not pass. Retain stopped runs and
their saved adapters; report every completed seed. Do not keep training to
improve a later transfer score or choose the better seed.

## Freeze all checkpoints before transfer

Eight stochastic draws per task and condition are the registered default.
Four are allowed only if selected and frozen before the first transfer score;
use the same count in every subsequent command and disclose the reduction.
The commands below select eight.

```bash
python - <<'PY'
from pathlib import Path
from alpha_research_rl.artifacts import write_json
from alpha_research_rl.financial_evaluation import freeze_checkpoints

path = Path("artifacts/development/financial-suite-freeze.json")
if path.exists():
    raise SystemExit("Freeze already exists; preserve it rather than overwrite.")
suite = freeze_checkpoints({
    "sft": "models/runs/financial-sft-v1/adapter",
    "rl23": "models/runs/financial-rloo-seed23-v1/adapter",
    "rl29": "models/runs/financial-rloo-seed29-v1/adapter",
}, draws=8)
write_json(path, suite)
PY
python -m alpha_research_rl.financial_evaluation \
  --adapter models/runs/financial-sft-v1/adapter --label sft \
  --split transfer --draws 8 \
  --freeze-manifest artifacts/development/financial-suite-freeze.json \
  --output artifacts/development/financial-sft-transfer.json
python -m alpha_research_rl.financial_evaluation \
  --adapter models/runs/financial-rloo-seed23-v1/adapter --label rl23 \
  --split transfer --draws 8 \
  --freeze-manifest artifacts/development/financial-suite-freeze.json \
  --output artifacts/development/financial-rl23-transfer.json
python -m alpha_research_rl.financial_evaluation \
  --adapter models/runs/financial-rloo-seed29-v1/adapter --label rl29 \
  --split transfer --draws 8 \
  --freeze-manifest artifacts/development/financial-suite-freeze.json \
  --output artifacts/development/financial-rl29-transfer.json
```

Transfer covers ten half-years from 2020 H1 through 2024 H2. It remains
chronological **development evaluation**, not an untouched final holdout.
Every checkpoint receives matched tasks, true and exchanged probe evidence,
common sampling seeds, eight stochastic draws and one greedy diagnostic per
condition. Exchanged evidence requires newly generated completions. Orientation
and scoring use the true data for both conditions. Strict JSON is primary;
the secondary fence-tolerant parser reuses the same completions. All invalid or
unscorable proposals receive `-1.01`; valid reward is oriented future IC minus
`0.01`. Average all draws, including failures, without best-of-N selection.

## Analyze saved reports

```bash
python -m alpha_research_rl.financial_analysis \
  --sft artifacts/development/financial-sft-transfer.json \
  --rl23 artifacts/development/financial-rl23-transfer.json \
  --rl29 artifacts/development/financial-rl29-transfer.json \
  --output artifacts/development/financial-paired-analysis.json \
  --plot artifacts/development/financial-paired-year.png
```

Analysis reads saved reports only. It requires the same freeze, evaluation
contract, matched tasks and sampling seeds; it does not generate more proposals.
For an additional feedback-only alias diagnostic, compare each checkpoint's
valid saved proposals with the 12 teacher formulas:

```bash
for label in sft rl23 rl29; do
  python -m alpha_research_rl.factor_diagnostics \
    --inputreport "artifacts/development/financial-${label}-transfer.json" \
    --output "artifacts/development/financial-${label}-factor-diagnostics.json"
done
```

This diagnostic reconstructs only each task's historical prefix and constructs
no forward-return labels. It reports signed daily rank similarity, its absolute
mean, finite-pair coverage and nonconstant-date support. Near-unit similarity
on the eligible pairs is an alias diagnostic, not independent alpha evidence.

Preserve the ten task-level and five year-level paired differences, both RL
seeds, validity, expression frequencies, true/exchanged effects, and greedy
diagnostics. Five temporally dependent years and two training seeds support a
small descriptive comparison, not a profitability or significance claim.
Review provenance and remove machine-local paths before exporting public
aggregate results; retain original local run reports for audit.

## Exploratory penalty sensitivity

This optional **post-hoc** diagnostic reuses the validated paired analysis.
It varies the invalid-penalty accounting coefficient lambda over fixed saved
proposals. The registered primary lambda remains 1; do not choose a penalty,
checkpoint or new training configuration from this plot. Failed proposals have
no measured IC, so assigning them zero predictive contribution is a surrogate
convention, not a measured zero return correlation.

```bash
python -m alpha_research_rl.penalty_sensitivity \
  --analysis artifacts/development/financial-paired-analysis.json \
  --output artifacts/development/financial-penalty-sensitivity.json \
  --plot artifacts/development/financial-penalty-sensitivity.png
```

The command runs no generation, training or market scoring. The published
artifact is [`financial_penalty_sensitivity_v1.json`](../results/financial_penalty_sensitivity_v1.json);
it remains separate from the registered comparison.

## Separate sequential opportunity gate

After publishing [the sequential study plan](next-sequential-study.md), run its
training-only CPU opportunity gate:

```bash
python -m alpha_research_rl.sequential_gate \
  --input data/raw/french49-v1/49_Industry_Portfolios_daily_CSV.zip \
  --output artifacts/development/sequential-grid-gate-v1.json
```

This uses the fixed 16-formula grid and the two registered forward folds within
2002–2017. It compares a cheap-only ridge selector with a privileged selector
that observes every late check. Its entry manifest and all task boundary
manifests are saved before candidate scoring. Retain every comparator and failed
gate; a pass allocates further work and does not establish a learned sequential
agent, GenAI improvement or transfer performance.
