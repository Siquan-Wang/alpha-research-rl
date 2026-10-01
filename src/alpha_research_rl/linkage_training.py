"""Prospectively specified reward-permutation placebo, with fresh own-policy draws."""

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from .artifacts import run_manifest, write_json
from .financial_evaluation import checkpoint_manifest
from .financial_policy import ProposalActor, evaluate_sample, expression_key, load_pinned_panel, sample_record
from .financial_training import selected_rl_tasks
from .llm import adapter_digest, completion_log_prob
from .training import leave_one_out_advantages, seed_everything

PARENT_DIGEST = "2de3acf5ae1f6dee2b5b335f083e2c2b5e76f224a1f1de7eb2b151d709a01c53"
PARENT_FILES_SHA = "d95793e5192be85fe4ceb15109a481c86ad13e804ffc01c56815683b1f21e360"
STUDY = "financial-reward-linkage-control-v1"


def permute_rewards(rewards, rng):
    """One uniform permutation, including identity, for every four-draw group."""
    values = np.asarray(rewards, dtype=float)
    if values.shape != (4,) or not np.isfinite(values).all():
        raise ValueError("Expected four finite true rewards")
    permutation = np.asarray(rng.permutation(4), dtype=int)
    assigned = values[permutation]
    return permutation, assigned, leave_one_out_advantages(assigned)


def train_placebo(panel, model_path, adapter, output, seed=23):
    import torch

    if seed not in (23, 29):
        raise ValueError("Registered control seeds are 23 and 29")
    output = Path(output)
    if (output / "run-manifest.json").exists():
        raise FileExistsError("Preserve existing run; do not overwrite or retry silently")
    parent_files = checkpoint_manifest(adapter)
    if parent_files["combined_sha256"] != PARENT_FILES_SHA:
        raise ValueError("Parent adapter weights/config files differ from the frozen SFT checkpoint")
    plan = Path(__file__).resolve().parents[2] / "docs" / "reward-linkage-control-plan.md"
    seed_everything(seed)
    tasks = selected_rl_tasks(panel, seed)
    rng = np.random.default_rng(700000 + seed)
    manifest = run_manifest({
        "study": STUDY, "phase": "reward_permutation_rloo", "seed": seed,
        "permutation_seed": 700000 + seed, "permutation_rule": "assigned[i]=true[p[i]]; uniform all24",
        "max_groups": 16, "group_size": 4, "learning_rate": 1e-5,
        "adamw_betas": [0.9, 0.999], "weight_decay": 0.0, "grad_clip": 1.0,
        "kl_penalty": 0.0, "entropy_bonus": 0.0, "max_completion_tokens": 64,
        "quality_gate": None, "task_order": [task.public_manifest for task in tasks],
        "snapshot_sha256": panel.metadata["raw_sha256"], "parent_checkpoint": parent_files,
        "required_parent_parameter_digest": PARENT_DIGEST,
        "plan_sha256": hashlib.sha256(plan.read_bytes()).hexdigest(),
        "trainer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    })
    actor = ProposalActor(model_path, adapter, trainable=True)
    manifest["actor"] = actor.provenance
    before = adapter_digest(actor.model)
    if before != PARENT_DIGEST:
        raise ValueError("Initialized adapter does not match the frozen financial SFT parent")
    write_json(output / "run-manifest.json", {"manifest": manifest, "adapter_before": before})
    optimizer = torch.optim.AdamW([p for p in actor.model.parameters() if p.requires_grad],
                                 lr=1e-5, betas=(0.9, 0.999), weight_decay=0.0)
    groups = []
    for index, task in enumerate(tasks):
        group_before = adapter_digest(actor.model)
        observation = task.observation()
        samples = [actor.sample(observation, stochastic=True, max_tokens=64) for _ in range(4)]
        outcomes = [evaluate_sample(task, sample) for sample in samples]
        true_rewards = [outcome["reward"] for outcome in outcomes]
        permutation, assigned, advantages = permute_rewards(true_rewards, rng)
        optimizer.zero_grad(set_to_none=True)
        logps = []
        for sample, advantage in zip(samples, advantages):
            logp = completion_log_prob(actor.model, sample.prompt_ids, sample.completion_ids)
            logps.append(float(logp.detach()))
            (-logp * float(advantage) / 4).backward()
        norm = float(torch.nn.utils.clip_grad_norm_(actor.model.parameters(), 1.0))
        if not math.isfinite(norm) or not all(math.isfinite(value) for value in logps):
            raise FloatingPointError("Nonfinite likelihood or gradient; do not advance checkpoint")
        updated = bool(np.any(advantages != 0))
        if updated:
            optimizer.step()
        eligible = [outcome for outcome in outcomes if outcome["status"] == "ok"]
        unique = {expression_key(outcome["expression"]) for outcome in eligible}
        ic_range = float(np.ptp([outcome["oriented_future_ic"] for outcome in eligible])) if eligible else 0.0
        row = {"group": index, "task": task.public_manifest, "observation": observation,
               "true_rewards": true_rewards, "permutation": permutation.tolist(),
               "assigned_rewards": assigned.tolist(), "advantages": advantages.tolist(),
               "preclip_grad_norm": norm, "optimizer_step": updated,
               "legal_unique_asts": len(unique), "usable_future_ic_range": ic_range,
               "quality_exploration": len(unique) >= 2 and ic_range > 1e-4,
               "adapter_before": group_before, "adapter_after": adapter_digest(actor.model),
               "samples": [{**sample_record(sample, outcome), "recomputed_preupdate_completion_logp": logp}
                           for sample, outcome, logp in zip(samples, outcomes, logps)]}
        groups.append(row)
        write_json(output / "progress.json", {"manifest": manifest, "groups": groups})
        print(json.dumps({"phase": "reward-permutation", "seed": seed, "group": index,
                          "true_rewards": true_rewards, "permutation": row["permutation"],
                          "optimizer_step": updated}), flush=True)
    actor.save(str(output / "adapter"))
    report = {"manifest": manifest, "adapter_before": before,
              "adapter_after": adapter_digest(actor.model), "groups": groups,
              "stopped_at_exploration_gate": False,
              "optimizer_steps": sum(group["optimizer_step"] for group in groups)}
    write_json(output / "training-report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/raw/french49-v1/49_Industry_Portfolios_daily_CSV.zip")
    parser.add_argument("--model", default="models/Qwen3-0.6B")
    parser.add_argument("--adapter", default="models/runs/financial-sft-v1/adapter")
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", type=int, choices=(23, 29), required=True)
    args = parser.parse_args()
    train_placebo(load_pinned_panel(args.input), args.model, args.adapter, args.output, args.seed)


if __name__ == "__main__":
    main()
