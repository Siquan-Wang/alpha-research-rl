"""Load the five downloaded adapters and compare their trained tensor digests.

Requires the cached pinned base and the documented CUDA training stack. This
performs no generation, market scoring, backpropagation or optimizer updates.
"""

import argparse
import gc
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from alpha_research_rl.adapter_release import BASE_REVISION, LABELS
from alpha_research_rl.financial_evaluation import checkpoint_manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapters", type=Path, default=Path("models/published-financial-v1"))
    parser.add_argument("--model", type=Path, default=Path("models/Qwen3-0.6B"))
    parser.add_argument("--output", type=Path, default=Path(".local/adapter-load-verification.json"))
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Choose a fresh output; verification never overwrites a file")

    def read(path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    source = read(args.model / "source-manifest.json")
    if source["model_id"] != "Qwen/Qwen3-0.6B" or source["revision"] != BASE_REVISION:
        raise ValueError("Expected the recorded pinned base source manifest")
    original = read("results/financial_training_v1.json")["runs"]
    controls = read("results/financial_linkage_training_v1.json")["runs"]
    expected = {label: run["training-report.json"]["adapter_after"] for label, run in original.items()}
    expected.update({label: run["training_report"]["adapter_after"] for label, run in controls.items()})
    freeze = read("artifacts/development/financial-linkage-suite-freeze-v1.json")
    # Verify the whole downloaded suite before loading any model.
    for label in LABELS:
        if checkpoint_manifest(args.adapters / label / "adapter") != freeze["checkpoints"][label]:
            raise ValueError("Downloaded checkpoint differs from original freeze: " + label)

    import peft
    import torch
    import transformers

    from alpha_research_rl.financial_policy import ProposalActor
    from alpha_research_rl.llm import adapter_digest

    records = []
    for label in LABELS:
        actor = ProposalActor(str(args.model), str(args.adapters / label / "adapter"), trainable=True)
        # trainable=True exposes the exact named LoRA tensors to adapter_digest;
        # no optimizer is created and no parameter-changing operation is called.
        actual = adapter_digest(actor.model)
        if actual != expected[label]:
            raise ValueError("Loaded parameter digest differs: " + label)
        count = sum(parameter.numel() for parameter in actor.model.parameters() if parameter.requires_grad)
        if count != 2_293_760:
            raise ValueError("Unexpected number of trainable adapter parameters")
        records.append({"checkpoint": label, "parameter_digest": actual,
                        "expected_parameter_digest": expected[label],
                        "trainable_parameters": count, "matches_original": True})
        print(json.dumps(records[-1]), flush=True)
        del actor
        gc.collect()
        torch.cuda.empty_cache()
    result = {
        "checked_utc": datetime.now(UTC).isoformat(),
        "scope": "Actual loading of downloaded adapter bytes; no generation, training or market scoring",
        "base_model": {"id": source["model_id"], "revision": source["revision"]},
        "runtime": {"torch": torch.__version__, "transformers": transformers.__version__,
                    "peft": peft.__version__, "gpu": torch.cuda.get_device_name(0), "precision": "float32"},
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "release_manifest_sha256": hashlib.sha256(
            Path("artifacts/releases/financial-adapters-v1.manifest.json").read_bytes()).hexdigest(),
        "checkpoints": records,
        "limitations": ["This verifies loading and parameter identity, not new generation or financial results",
                        "Other hardware and kernels may generate different stochastic completions"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
