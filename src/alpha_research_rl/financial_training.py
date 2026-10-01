"""Registered feedback-teacher SFT and real-reward RLOO proposal learning."""

import argparse
import json
import math
from pathlib import Path

import numpy as np

from .artifacts import run_manifest, write_json
from .financial_policy import ProposalActor, evaluate_sample, expression_key, load_pinned_panel, sample_record
from .financial_tasks import feedback_teacher, list_tasks
from .llm import adapter_digest, completion_log_prob
from .training import leave_one_out_advantages, seed_everything


def financial_sft(panel, model_path, output, seed=61):
    import torch

    seed_everything(seed)
    tasks = list_tasks(panel, "train")
    examples = []
    for task in tasks:
        expression = feedback_teacher(task)
        if expression is None:
            raise ValueError("No eligible feedback teacher formula; do not silently remove a task")
        examples.append({"observation": task.observation(),
                         "action": {"action": "propose", "expression": expression},
                         "task": task.public_manifest})
    write_json(Path(output) / "training-examples.json", examples)
    manifest = run_manifest({"study": "financial-proposal-v1", "phase": "sft", "seed": seed,
                "epochs": 3, "learning_rate": 1e-4, "adamw_weight_decay": 0.01,
                "adamw_betas": [0.9, 0.999], "grad_clip": 1.0,
                "teacher": "privileged 12-grid feedback-only argmax absolute IC",
                "teacher_information_exceeds_actor_probes": True,
                "task_manifests": [task.public_manifest for task in tasks],
                "snapshot_sha256": panel.metadata["raw_sha256"]})
    actor = ProposalActor(model_path, trainable=True)
    manifest["actor"] = actor.provenance
    before = adapter_digest(actor.model)
    write_json(Path(output) / "run-manifest.json", {"manifest": manifest, "adapter_before": before})
    encoded = [(actor.prompt_ids(example["observation"]),
                actor.tokenizer.encode(json.dumps(example["action"], separators=(",", ":")),
                                       add_special_tokens=False) + [actor.tokenizer.eos_token_id])
               for example in examples]
    write_json(Path(output) / "encoded-training-examples.json", [
        {"task_id": example["task"]["task_id"], "prompt_ids": prompt, "target_ids": target}
        for example, (prompt, target) in zip(examples, encoded)])
    optimizer = torch.optim.AdamW([p for p in actor.model.parameters() if p.requires_grad], lr=1e-4)
    logs = []
    for epoch in range(3):
        for step, index in enumerate(np.random.default_rng(seed+epoch).permutation(len(encoded))):
            prompt, target = encoded[index]
            optimizer.zero_grad(set_to_none=True)
            loss = -completion_log_prob(actor.model, prompt, target) / len(target)
            loss.backward()
            norm = float(torch.nn.utils.clip_grad_norm_(actor.model.parameters(), 1.0))
            if not math.isfinite(norm) or not math.isfinite(float(loss.detach())):
                raise FloatingPointError("Nonfinite SFT gradient/loss; checkpoint must not be advanced")
            optimizer.step()
            logs.append({"epoch": epoch, "step": step, "task_id": examples[index]["task"]["task_id"],
                         "loss_per_token": float(loss.detach()), "preclip_grad_norm": norm})
            if step % 16 == 0:
                print(json.dumps({"phase": "financial-sft", **logs[-1]}), flush=True)
    actor.save(str(Path(output) / "adapter"))
    report = {"manifest": manifest, "adapter_before": before, "adapter_after": adapter_digest(actor.model),
              "updates": logs, "trainable_parameters": sum(p.numel() for p in actor.model.parameters()
                                                            if p.requires_grad)}
    write_json(Path(output) / "training-report.json", report)
    return report


def selected_rl_tasks(panel, seed):
    tasks = [task for task in list_tasks(panel, "train")
             if task.half == (1 if task.year % 2 == 0 else 2)]
    if len(tasks) != 16:
        raise ValueError("Registered RL task schedule requires one half-year per year, 2002-2017")
    return [tasks[index] for index in np.random.default_rng(seed).permutation(len(tasks))]


def financial_rloo(panel, model_path, adapter, output, seed=23):
    import torch

    if seed not in (23, 29):
        raise ValueError("This registered study permits RL seeds 23 and 29")
    seed_everything(seed)
    tasks = selected_rl_tasks(panel, seed)
    manifest = run_manifest({"study": "financial-proposal-v1", "phase": "rloo", "seed": seed,
                "max_groups": 16, "group_size": 4, "learning_rate": 1e-5, "grad_clip": 1.0,
                "weight_decay": 0.0, "kl_penalty": 0.0, "entropy_bonus": 0.0,
                "max_completion_tokens": 64, "task_order": [task.public_manifest for task in tasks],
                "quality_gate": "After 8 groups stop if none has >=2 legal distinct ASTs and valid IC range>1e-4",
                "snapshot_sha256": panel.metadata["raw_sha256"]})
    actor = ProposalActor(model_path, adapter, trainable=True)
    manifest["actor"] = actor.provenance
    before = adapter_digest(actor.model)
    write_json(Path(output) / "run-manifest.json", {"manifest": manifest, "adapter_before": before})
    optimizer = torch.optim.AdamW([p for p in actor.model.parameters() if p.requires_grad],
                                 lr=1e-5, weight_decay=0.0)
    groups = []
    stopped_at_gate = False
    for index, task in enumerate(tasks):
        samples, outcomes = [], []
        group_before = adapter_digest(actor.model)
        for _ in range(4):
            sample = actor.sample(task.observation(), stochastic=True, max_tokens=64)
            samples.append(sample)
            outcomes.append(evaluate_sample(task, sample))
        rewards = [outcome["reward"] for outcome in outcomes]
        advantages = leave_one_out_advantages(rewards)
        optimizer.zero_grad(set_to_none=True)
        logps = []
        for sample, advantage in zip(samples, advantages):
            logp = completion_log_prob(actor.model, sample.prompt_ids, sample.completion_ids)
            logps.append(float(logp.detach()))
            (-logp * float(advantage) / 4).backward()
        norm = float(torch.nn.utils.clip_grad_norm_(actor.model.parameters(), 1.0))
        if not math.isfinite(norm) or not all(math.isfinite(value) for value in logps):
            raise FloatingPointError("Nonfinite RL gradient/likelihood; do not advance checkpoint")
        updated = bool(np.any(advantages != 0))
        if updated:
            optimizer.step()
        eligible = [outcome for outcome in outcomes if outcome["status"] == "ok"]
        unique = {expression_key(outcome["expression"]) for outcome in eligible}
        ic_range = float(np.ptp([outcome["oriented_future_ic"] for outcome in eligible])) if eligible else 0.0
        row = {"group": index, "task": task.public_manifest, "rewards": rewards,
               "advantages": advantages.tolist(), "preclip_grad_norm": norm, "optimizer_step": updated,
               "legal_unique_asts": len(unique), "usable_future_ic_range": ic_range,
               "quality_exploration": len(unique) >= 2 and ic_range > 1e-4,
               "adapter_before": group_before, "adapter_after": adapter_digest(actor.model),
               "samples": [{**sample_record(sample, outcome), "recomputed_preupdate_completion_logp": logp}
                           for sample, outcome, logp in zip(samples, outcomes, logps)]}
        groups.append(row)
        print(json.dumps({"phase": "financial-rloo", "seed": seed, "group": index,
                          "rewards": rewards, "quality_exploration": row["quality_exploration"]}), flush=True)
        write_json(Path(output) / "progress.json", {"manifest": manifest, "groups": groups})
        if index == 7 and not any(group["quality_exploration"] for group in groups):
            stopped_at_gate = True
            break
    actor.save(str(Path(output) / "adapter"))
    report = {"manifest": manifest, "adapter_before": before, "adapter_after": adapter_digest(actor.model),
              "groups": groups, "stopped_at_exploration_gate": stopped_at_gate}
    write_json(Path(output) / "training-report.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["sft", "rloo"])
    parser.add_argument("--input", default="data/raw/french49-v1/49_Industry_Portfolios_daily_CSV.zip")
    parser.add_argument("--model", default="models/Qwen3-0.6B")
    parser.add_argument("--adapter")
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", type=int, default=23)
    args = parser.parse_args()
    panel = load_pinned_panel(args.input)
    if args.phase == "sft":
        financial_sft(panel, args.model, args.output)
    else:
        if not args.adapter:
            parser.error("rloo requires --adapter")
        financial_rloo(panel, args.model, args.adapter, args.output, args.seed)
