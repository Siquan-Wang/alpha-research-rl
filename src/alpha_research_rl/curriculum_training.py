"""Constructed feedback curriculum: diagnose action conditioning, not financial alpha."""

import argparse
import ast
import hashlib
import json
from pathlib import Path

import numpy as np

from .artifacts import json_safe, run_manifest, write_json
from .llm import LocalActor, adapter_digest, completion_log_prob
from .training import seed_everything


def canonical_action(action):
    result = dict(action)
    if isinstance(result.get("expression"), str):
        try:
            result["expression"] = ast.dump(ast.parse(result["expression"].strip(), mode="eval"))
        except (SyntaxError, ValueError):
            pass
    return result


def dataset_digest(dataset):
    encoded = json.dumps(json_safe(dataset), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode()).hexdigest()


def train_curriculum(model_path, initial_adapter, output, epochs=2, seed=47):
    import torch

    from .curriculum import build_curriculum

    if isinstance(epochs, bool) or not isinstance(epochs, int) or epochs < 1:
        raise ValueError("epochs must be a positive integer")
    seed_everything(seed)
    data = build_curriculum("train")
    write_json(Path(output) / "constructed-training-data.json", data)
    manifest = run_manifest({"study": "constructed-feedback-curriculum-v2", "seed": seed,
                "epochs": epochs, "learning_rate": 1e-4, "grad_clip": 1.0,
                "adamw_weight_decay": 0.01, "adamw_betas": [0.9, 0.999],
                "dataset_sha256": dataset_digest(data), "dataset_metadata": data["metadata"],
                "claim": "constructed feedback conditioning, not financial research performance"})
    actor = LocalActor(model_path, initial_adapter, trainable=True)
    manifest["actor"] = actor.provenance
    initial_digest = adapter_digest(actor.model)
    examples = []
    for example in data["examples"]:
        prompt = actor.prompt_ids(example["observation"])
        target = actor.tokenizer.encode(json.dumps(example["action"], separators=(",", ":")),
                                        add_special_tokens=False) + [actor.tokenizer.eos_token_id]
        if len(prompt) > 4096:
            raise ValueError("Curriculum prompt exceeds the same inference limit")
        examples.append((prompt, target, example["family"], example["task_id"]))
    optimizer = torch.optim.AdamW([p for p in actor.model.parameters() if p.requires_grad], lr=1e-4)
    logs = []
    for epoch in range(epochs):
        for step, index in enumerate(np.random.default_rng(seed+epoch).permutation(len(examples))):
            prompt, target, family, task_id = examples[index]
            optimizer.zero_grad(set_to_none=True)
            loss = -completion_log_prob(actor.model, prompt, target) / len(target)
            loss.backward()
            gradient = float(torch.nn.utils.clip_grad_norm_(actor.model.parameters(), 1.0))
            optimizer.step()
            row = {"epoch": epoch, "step": step, "task_id": task_id, "family": family,
                   "loss_per_completion_token": float(loss.detach()), "preclip_grad_norm": gradient}
            logs.append(row)
            if step % 32 == 0:
                print(json.dumps({"phase": "curriculum-sft", **row}), flush=True)
        actor.save(str(Path(output) / f"epoch-{epoch+1}"))
        write_json(Path(output) / "progress.json", {"updates": logs})
    actor.save(str(Path(output) / "adapter"))
    report = {"manifest": manifest, "adapter_before": initial_digest,
              "adapter_after": adapter_digest(actor.model), "n_examples": len(examples), "updates": logs}
    write_json(Path(output) / "training-report.json", report)
    return report


def evaluate_curriculum(model_path, adapter, output, label):
    from .curriculum import build_counterfactual_pairs, build_curriculum

    seed_everything(53)
    data = build_curriculum("dev")
    pairs = build_counterfactual_pairs()
    write_json(Path(output).with_suffix(".constructed-data.json"), {"dataset": data, "pairs": pairs})
    manifest = run_manifest({"study": "constructed-feedback-curriculum-v2", "actor": label,
                "dataset_sha256": dataset_digest(data), "dataset_metadata": data["metadata"],
                "greedy": True, "max_action_tokens": 64,
                "claim": "controlled action conditioning probe, not financial research performance"})
    actor = LocalActor(model_path, adapter)
    manifest["actor_provenance"] = actor.provenance
    rows = []
    for pair in pairs:
        sides = []
        for side in ("left", "right"):
            example = pair[side]
            sample = actor.sample(example["observation"])
            try:
                json_object_valid = sample.terminated and isinstance(json.loads(sample.text), dict)
            except (ValueError, TypeError):
                json_object_valid = False
            sides.append({"side": side, "expected": example["action"], "predicted": sample.action,
                          "text": sample.text, "terminated": sample.terminated,
                          "json_object_valid": json_object_valid,
                          "category": example["provenance"].get("category", "unknown"),
                          "correct": canonical_action(sample.action) == canonical_action(example["action"])})
        rows.append({"pair_id": pair["pair_id"], "task_id": pair["task_id"], "family": pair["family"],
                     "sides": sides, "both_correct": all(side["correct"] for side in sides),
                     "action_changed": canonical_action(sides[0]["predicted"]) !=
                         canonical_action(sides[1]["predicted"])})
        print(json.dumps({"actor": label, "pair_id": pair["pair_id"],
                          "both_correct": rows[-1]["both_correct"]}), flush=True)
    summary = {"n_pairs": len(rows), "n_examples": sum(len(row["sides"]) for row in rows),
               "both_correct_rate": float(np.mean([row["both_correct"] for row in rows])),
               "action_changed_rate": float(np.mean([row["action_changed"] for row in rows])),
               "example_accuracy": float(np.mean([s["correct"] for row in rows for s in row["sides"]])),
               "terminated_rate": float(np.mean([s["terminated"] for row in rows for s in row["sides"]]))}
    summary["json_object_valid_rate"] = float(np.mean([
        side["json_object_valid"] for row in rows for side in row["sides"]]))
    summary["by_family"] = {
        family: {"pairs": sum(row["family"] == family for row in rows),
                 "both_correct_rate": float(np.mean([row["both_correct"] for row in rows
                                                       if row["family"] == family]))}
        for family in sorted({row["family"] for row in rows})}
    summary["by_category"] = {
        category: {"examples": sum(side["category"] == category for row in rows for side in row["sides"]),
                   "accuracy": float(np.mean([side["correct"] for row in rows for side in row["sides"]
                                                if side["category"] == category]))}
        for category in sorted({side["category"] for row in rows for side in row["sides"]})}
    report = {"manifest": manifest, "summary": summary, "pairs": rows}
    write_json(output, report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["train", "evaluate"])
    parser.add_argument("--model", default="models/Qwen3-0.6B")
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--label", default="curriculum-v2")
    parser.add_argument("--epochs", type=int, default=2)
    args = parser.parse_args()
    if args.phase == "train":
        train_curriculum(args.model, args.adapter, args.output, args.epochs)
    else:
        evaluate_curriculum(args.model, args.adapter, args.output, args.label)
