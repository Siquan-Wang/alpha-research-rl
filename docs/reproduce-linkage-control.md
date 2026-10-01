# Reproduce the reward-linkage control

## CPU reanalysis of the five saved reports

The [registered control plan](reward-linkage-control-plan.md) is an exploratory
follow-up to the original one-step financial proposal study. It was written
after inspecting that study's transfer results. This guide documents the method;
both control evaluations are complete. The [result report](reward-linkage-results-v1.md)
interprets their outcomes separately from this procedure. Comparing the five saved reports needs only CPU
analysis, with no market data, model weights, generation or GPU.

Run from the repository root using the published source version associated with
the reports. The examples use Bash; the module arguments also work in PowerShell.
Keep the original report filenames and bytes, even if moving them to another
directory: the control registry binds the three original filenames and SHA-256s.

For a quick check after `python -m pip install -e .`, run:

```bash
python scripts/replay_published_results.py
```

This recomputes the full five-policy analysis and compares it with the published
JSON, allowing only `1e-12` floating-point tolerance. Report file hashes and
non-numeric values must match exactly. During this process it rejects training
stack imports, network connections, and access to local weights or raw market
data. These diagnostic guards do not form a general-purpose security sandbox.
The same check runs in public CPU CI. It reproduces saved-result arithmetic,
not the original undistributed model weights or training.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[plots]'
export PYTHONUTF8=1
python -m alpha_research_rl.linkage_analysis \
  --sft artifacts/development/financial-sft-transfer-v1.json \
  --rl23 artifacts/development/financial-rloo23-transfer-v1.json \
  --rl29 artifacts/development/financial-rloo29-transfer-v1.json \
  --placebo23 artifacts/development/financial-placebo23-transfer-v1.json \
  --placebo29 artifacts/development/financial-placebo29-transfer-v1.json \
  --output artifacts/development/financial-linkage-analysis-reproduced.json \
  --plot artifacts/development/financial-linkage-analysis-reproduced.png
```

Omit `--plot` and install `-e .` if a figure is unnecessary. Analysis records all
five input byte hashes and validates the unchanged original three-report study,
the joint checkpoint registry, its timing, evaluation contracts, matched tasks,
prompt IDs and sampling seeds. It preserves both seeds, all ten half-years and
all five year summaries, true/exchanged evidence, stochastic/greedy decoding,
strict primary parsing and the secondary reparse of the same completions.
Correct-RL-minus-placebo comparisons separate the failure-penalty contribution
from the all-proposal predictive-IC contribution. Failed proposals' zero IC
contribution is an accounting convention, not a measured zero correlation.
Eight draws do not create eight independent market episodes.

## Training replication requires the original parent

The repository publishes code, manifests and traces, **not trained adapter
weights**. Public access to the base Qwen model does not recover the original
SFT adapter. Exact control replication additionally requires lawful access to
the original SFT, both original RL adapters, original suite freeze and original
three saved transfer reports.

`linkage_training.py` deliberately enforces two parent identities:

| Identity | Required SHA-256 |
| --- | --- |
| `PARENT_FILES_SHA`, combined adapter-file manifest | `d95793e5192be85fe4ceb15109a481c86ad13e804ffc01c56815683b1f21e360` |
| `PARENT_DIGEST`, loaded trainable parameter digest | `2de3acf5ae1f6dee2b5b335f083e2c2b5e76f224a1f1de7eb2b151d709a01c53` |

The file check runs before actor loading; the parameter check runs before
optimization. Retraining SFT from the same recipe does not guarantee either
identity. A different parent requires a separately registered study with its
own identifiers, source, hashes, controls and evaluation declaration. Do not
change these constants or edit manifests to make a new parent pass as the
original experiment.

For the model revision, free local inputs and pinned training environment, use
[the original reproduction guide](reproduce-financial-study.md). Its original
training commands describe the procedure; they do not supply the missing
original adapter. Reuse a lawful cached French49 ZIP with SHA-256
`8f394fe34bea54d41b9aafed410425ee8f8e252ede3c71a7c1cd20bab83040de`
and the pinned local Qwen3-0.6B revision
`c1899de289a04d12100db370d81485cdf75e47ca`. The official French download is
revised upstream. If a new download has a different hash, stop exact input
replication; do not replace the registered snapshot hash. Raw market arrays and
weights are not redistributed, and no paid resource is needed or provisioned.

Publish the control plan and implementation source **before control training**,
and retain that source through evaluation. Preserve all original run reports,
adapters, transfer reports and timestamps. The control's entry manifest captures
plan/source/parent hashes before updates. A new publication or registry cannot
retroactively register the original comparison before its results were seen.

## Train the two controls once

On an existing compatible local CUDA host, use the pinned training packages in
the original guide: PyTorch 2.8.0, Transformers 4.57.6, PEFT 0.18.1 and Accelerate
1.15.0. Keep the full resolved environment and numerical manifests. Run the two
seeds sequentially in fresh directories, from the unchanged original SFT parent:

```bash
export PYTHONUTF8=1
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_DATASETS_OFFLINE=1
python -m alpha_research_rl.linkage_training \
  --input data/raw/french49-v1/49_Industry_Portfolios_daily_CSV.zip \
  --model models/Qwen3-0.6B \
  --adapter models/runs/financial-sft-v1/adapter \
  --seed 23 --output models/runs/financial-placebo23-v1
python -m alpha_research_rl.linkage_training \
  --input data/raw/french49-v1/49_Industry_Portfolios_daily_CSV.zip \
  --model models/Qwen3-0.6B \
  --adapter models/runs/financial-sft-v1/adapter \
  --seed 29 --output models/runs/financial-placebo29-v1
```

Each seed completes all 16 registered training groups, one half-year per year
from 2002–2017 (H1 in even years, H2 in odd years), in its seed-dependent order.
There are four fresh on-policy completions per group. A uniform permutation
from RNG seed `700000 + seed` assigns that group's own four true rewards to its
completions. Identity permutations, repeated rewards and invalid completions
are retained. Original RL trajectories are not replayed.

The completion-only leave-one-out gradient uses these assigned rewards. The
actor uses FP32, disables TF32 and inherited generation defaults, and samples
full softmax at temperature 1, top-p 1, top-k 0, with at most 64 completion
tokens. AdamW uses learning rate `1e-5`, betas `(0.9, 0.999)`, no weight decay,
gradient clipping at 1, and no KL or entropy term. The exploration diagnostic
is logged but cannot stop these controls. Constant assigned rewards produce
exactly zero advantages and skip the optimizer step, including its moments.
Thus 16 groups does not imply 16 optimizer updates. Retain true rewards,
permutations, assigned rewards, completion IDs, gradients and digest changes.

## Check both saved adapters before scoring

The following public example performs the same FP32 save/reload check on the
training task 2002 H1, independently for each control. It loads models and uses
local hardware; it is not part of CPU saved-report reanalysis. Save this block
as a temporary local Python script and run it once. Do not overwrite prior
checks or train additional variants after seeing transfer outcomes.

```python
import gc
from pathlib import Path

import torch

from alpha_research_rl.artifacts import write_json
from alpha_research_rl.financial_policy import ProposalActor, load_pinned_panel
from alpha_research_rl.financial_tasks import make_task
from alpha_research_rl.llm import adapter_digest, completion_log_prob

task = make_task(load_pinned_panel(
    "data/raw/french49-v1/49_Industry_Portfolios_daily_CSV.zip"), 2002, 1)
for seed in (23, 29):
    run = Path(f"models/runs/financial-placebo{seed}-v1")
    output, restored_path = run / "roundtrip.json", run / "roundtrip-adapter"
    if output.exists() or restored_path.exists():
        raise FileExistsError("Preserve the existing roundtrip evidence")
    actor = ProposalActor("models/Qwen3-0.6B", str(run / "adapter"), trainable=True)
    prompt = actor.prompt_ids(task.observation())
    target = actor.tokenizer.encode(
        '{"action":"propose","expression":"delay(returns,1)"}',
        add_special_tokens=False) + [actor.tokenizer.eos_token_id]
    with torch.no_grad():
        before_logp = float(completion_log_prob(actor.model, prompt, target))
    before_digest = adapter_digest(actor.model)
    actor.save(str(restored_path))
    del actor
    gc.collect()
    torch.cuda.empty_cache()
    restored = ProposalActor("models/Qwen3-0.6B", str(restored_path), trainable=True)
    with torch.no_grad():
        after_logp = float(completion_log_prob(restored.model, prompt, target))
    result = {
        "adapter_before": before_digest, "adapter_after": adapter_digest(restored.model),
        "logp_before": before_logp, "logp_after": after_logp,
        "absolute_logp_difference": abs(after_logp - before_logp), "precision": "float32",
        "task": task.public_manifest, "completion_ids": target,
    }
    write_json(output, result)
    if result["adapter_before"] != result["adapter_after"] or result["absolute_logp_difference"] > 1e-5:
        raise AssertionError("Financial FP32 adapter did not roundtrip")
    del restored
    gc.collect()
    torch.cuda.empty_cache()
```

This is a check of one fixed completion's likelihood and parameter identity,
not proof of numerical identity for every possible generation or across hardware.

## Freeze all five identities before control transfer

The original paths below are the actual study paths, including
`financial-rloo23-v1` and `financial-rloo29-v1`. Preserve the original three-way
freeze. The new registry binds all five adapters, the original three report
byte hashes and the canonical JSON hash of the original freeze. It must be
written after training and roundtrip checks, **before either control transfer
evaluation starts**. Save this public Python example locally and run it once:

```python
import hashlib
import json
from pathlib import Path

from alpha_research_rl.artifacts import write_json
from alpha_research_rl.financial_evaluation import evaluation_contract, freeze_checkpoints

target = Path("artifacts/development/financial-linkage-suite-freeze-v1.json")
if target.exists():
    raise FileExistsError("Never replace a control freeze")
original = json.loads(Path("artifacts/development/financial-suite-freeze-v1.json").read_bytes())
labels = ["financial-sft-v1", "financial-rloo23-v1", "financial-rloo29-v1",
          "financial-placebo23-v1", "financial-placebo29-v1"]
for seed in (23, 29):
    run = Path(f"models/runs/financial-placebo{seed}-v1")
    report = json.loads((run / "training-report.json").read_bytes())
    check = json.loads((run / "roundtrip.json").read_bytes())
    assert len(report["groups"]) == 16
    assert not report["stopped_at_exploration_gate"]
    assert check["adapter_before"] == check["adapter_after"] == report["adapter_after"]
    assert check["absolute_logp_difference"] <= 1e-5
registry = freeze_checkpoints({
    label: Path("models/runs") / label / "adapter" for label in labels}, draws=8)
registry["study"] = "financial-reward-linkage-control-v1"
registry["original_frozen_suite_sha256"] = hashlib.sha256(
    json.dumps(original, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
registry["original_reports"] = {}
contract = evaluation_contract("models/Qwen3-0.6B")
for label, name in zip(labels[:3], ["sft", "rloo23", "rloo29"], strict=True):
    assert registry["checkpoints"][label] == original["checkpoints"][label]
    path = Path(f"artifacts/development/financial-{name}-transfer-v1.json")
    raw = path.read_bytes()
    report = json.loads(raw)
    assert report["manifest"]["config"]["evaluation_contract"] == contract
    registry["original_reports"][label] = {
        "file": path.name, "sha256": hashlib.sha256(raw).hexdigest()}
write_json(target, registry)
```

Keep training reports and roundtrip files alongside the registry. The public
[training evidence export](../results/financial_linkage_training_v1.json)
retains their hashes and traces. Do not rewrite original report bytes, the
original freeze or its timestamp to force compatibility. Analysis checks that
the extension preserves the original fields and predates control scoring.

## Score only the two new controls, then reanalyze

```bash
python -m alpha_research_rl.financial_evaluation \
  --adapter models/runs/financial-placebo23-v1/adapter \
  --label financial-placebo23-v1 --split transfer --draws 8 \
  --freeze-manifest artifacts/development/financial-linkage-suite-freeze-v1.json \
  --output artifacts/development/financial-placebo23-transfer-v1.json
python -m alpha_research_rl.financial_evaluation \
  --adapter models/runs/financial-placebo29-v1/adapter \
  --label financial-placebo29-v1 --split transfer --draws 8 \
  --freeze-manifest artifacts/development/financial-linkage-suite-freeze-v1.json \
  --output artifacts/development/financial-placebo29-transfer-v1.json
```

These commands use the pinned model and ZIP defaults specified above. Reuse the
original three reports unchanged. Each control records ten 2020–2024 half-years,
true and exchanged actor evidence, eight stochastic draws and one greedy draw
per condition: 180 new completions per checkpoint, 360 across controls. With
the original 540 draws, the five-report analysis retains 900 completions.
The strict parser is primary; secondary parsing does not generate extra draws.
Orientation and reward use true task data in both evidence conditions.

Run the CPU analysis command at the start of this guide after both reports exist.
Preserve both seeds and negative task/year differences. Transfer is chronological
development evaluation already inspected in the original study, not a newly
untouched holdout. Two training seeds and five dependent market years provide a
descriptive mechanism control; they do not establish significance, profitability,
novel alpha discovery or a learned sequential research agent. Do not select a
preferred seed, add retries or tune new checkpoints from this comparison.
