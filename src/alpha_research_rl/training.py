"""Small, inspectable local SFT and on-policy REINFORCE with a leave-one-out baseline.

This reference trainer is not PPO/GRPO. It makes one optimizer update per freshly
sampled trajectory group, with a terminal environment reward and no replay.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from .artifacts import run_manifest, write_json
from .data import make_synthetic_panel
from .environment import ResearchEnvironment
from .experiments import run_episode
from .llm import LocalActor, adapter_digest, completion_log_prob
from .policies import StabilityAware
from .protocol import make_chronological_split

INITIAL_FACTORS = ["returns", "ts_mean(returns,5)", "ts_std(returns,20)"]
PROPOSALS = ["delta(log(volume),1)", "sub(ts_mean(returns,3),ts_mean(returns,20))"]


def make_training_env(seed: int, regime: str, budget: int = 10):
    panel = make_synthetic_panel(seed, n_dates=300, n_assets=16, regime=regime)
    return ResearchEnvironment(panel, make_chronological_split(300, horizon=5),
                               INITIAL_FACTORS, budget=budget, allow_generation=True)


class DemonstrationPolicy:
    """Scripted proposal+feedback teacher; no assessment data/reward in action choice."""
    def __init__(self):
        self.fallback = StabilityAware()

    def act(self, observation):
        candidates = observation["candidates"]
        if len(candidates) == len(INITIAL_FACTORS):
            return {"action": "propose", "expression": PROPOSALS[0]}
        evidence = observation["evidence"]
        if observation["budget"] >= 3:
            for identifier in [3, 0, 1, 2]:
                if str(identifier) not in evidence:
                    return {"action": "screen", "candidate": identifier}
        scores = [(int(identifier), entry["screen"]["mean_ic"])
                  for identifier, entry in evidence.items() if "screen" in entry
                  and entry["screen"]["mean_ic"] is not None]
        scores.sort(key=lambda pair: abs(pair[1]), reverse=True)
        if scores and not observation["selected"] and abs(scores[0][1]) > 0.04:
            return {"action": "select", "candidate": scores[0][0]}
        return {"action": "stop"}


def leave_one_out_advantages(rewards: list[float]) -> np.ndarray:
    values = np.asarray(rewards, dtype=float)
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("At least two finite trajectory rewards are required")
    centered = values - values[0]
    return centered - (centered.sum() - centered) / (len(values) - 1)


def seed_everything(seed):
    import random

    import torch
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def train_sft(model_path: str, output: str, seed: int = 17, episodes: int = 12, epochs: int = 1):
    import torch
    seed_everything(seed)
    manifest = run_manifest({"algorithm": "supervised behavior cloning",
        "seed": seed, "episodes": episodes, "epochs": epochs, "train_seeds": list(range(1000, 1000+episodes)),
        "teacher": "scripted proposal and feedback only", "data": "synthetic only",
        "learning_rate": 2e-4, "lora_rank": 8, "initial_factors": INITIAL_FACTORS,
        "proposal_templates": PROPOSALS, "budget": 10, "horizon": 5})
    actor = LocalActor(model_path, trainable=True)
    examples = []
    for index in range(episodes):
        regime = ["signal", "null", "decay"][index % 3]
        trajectory = run_episode(make_training_env(1000 + index, regime), DemonstrationPolicy())["trajectory"]
        for step in trajectory:
            prompt = actor.prompt_ids(step["observation"])
            target = actor.tokenizer.encode(json.dumps(step["action"], separators=(",", ":")),
                                            add_special_tokens=False) + [actor.tokenizer.eos_token_id]
            examples.append((prompt, target))
    before = adapter_digest(actor.model)
    optimizer = torch.optim.AdamW([p for p in actor.model.parameters() if p.requires_grad], lr=2e-4)
    losses = []
    for epoch in range(epochs):
        order = np.random.default_rng(seed + epoch).permutation(len(examples))
        for step, index in enumerate(order):
            optimizer.zero_grad(set_to_none=True)
            prompt, target = examples[index]
            loss = -completion_log_prob(actor.model, prompt, target) / len(target)
            loss.backward()
            grad_norm = float(torch.nn.utils.clip_grad_norm_(actor.model.parameters(), 1.0))
            optimizer.step()
            losses.append({"epoch": epoch, "step": step, "loss_per_completion_token": float(loss.detach()),
                           "preclip_grad_norm": grad_norm})
            if step % 20 == 0:
                print(json.dumps({"phase": "sft", **losses[-1]}), flush=True)
    actor.save(str(Path(output) / "adapter"))
    report = {"manifest": manifest,
              "n_examples": len(examples), "adapter_before": before,
              "adapter_after": adapter_digest(actor.model), "updates": losses,
              "trainable_parameters": sum(p.numel() for p in actor.model.parameters() if p.requires_grad)}
    write_json(Path(output) / "training-report.json", report)
    return report


def train_rloo(model_path: str, adapter: str, output: str, seed: int = 23,
               groups: int = 4, group_size: int = 4):
    import torch
    if group_size < 2:
        raise ValueError("group_size must be at least 2")
    seed_everything(seed)
    manifest = run_manifest({"algorithm": "on-policy REINFORCE with leave-one-out baseline",
        "seed": seed, "groups": groups, "group_size": group_size, "data": "synthetic only",
        "one_update_per_fresh_group": True, "kl_penalty": 0.0, "learning_rate": 1e-5,
        "sampling_temperature": 1.0, "top_p": 1.0, "top_k": 0, "max_action_tokens": 64,
        "train_seeds": list(range(2000, 2000+groups)), "initial_factors": INITIAL_FACTORS,
        "budget": 10, "horizon": 5,
        "claim": "training-path development; not evidence of improved market alpha"})
    actor = LocalActor(model_path, adapter, trainable=True)
    optimizer = torch.optim.AdamW([p for p in actor.model.parameters() if p.requires_grad], lr=1e-5,
                                 weight_decay=0.0)
    before = adapter_digest(actor.model)
    logs = []
    for group in range(groups):
        group_digest_before = adapter_digest(actor.model)
        task_seed = 2000 + group
        regime = ["signal", "null", "decay"][group % 3]
        trajectories, rewards = [], []
        for rollout in range(group_size):
            env = make_training_env(task_seed, regime)
            observation = env.reset()
            samples = []
            for _ in range(observation["initial_budget"] + 1):
                sample = actor.sample(observation, stochastic=True)
                observation, reward, done, info = env.step(sample.action)
                samples.append((sample, info))
                if done:
                    break
            if not done:
                raise RuntimeError("rollout did not terminate")
            trajectories.append(samples)
            rewards.append(reward)
            print(json.dumps({"phase": "rollout", "group": group, "rollout": rollout,
                              "reward": reward, "actions": len(samples)}), flush=True)
        advantages = leave_one_out_advantages(rewards)
        optimizer.zero_grad(set_to_none=True)
        loss_value = 0.0
        for trajectory, advantage in zip(trajectories, advantages):
            for sample, _ in trajectory:
                loss = -completion_log_prob(actor.model, sample.prompt_ids, sample.completion_ids) \
                    * float(advantage) / group_size
                loss.backward()
                loss_value += float(loss.detach())
        grad_norm = float(torch.nn.utils.clip_grad_norm_(actor.model.parameters(), 1.0))
        if np.any(advantages != 0):
            optimizer.step()
        row = {"group": group, "task_seed": task_seed, "regime": regime, "rewards": rewards,
               "advantages": advantages.tolist(), "loss": loss_value, "preclip_grad_norm": grad_norm,
               "optimizer_step": bool(np.any(advantages != 0)),
               "adapter_before": group_digest_before, "adapter_after": adapter_digest(actor.model),
               "trajectories": [[{"text": sample.text, "action": sample.action,
                                   "completion_ids": sample.completion_ids,
                                   "completion_token_count": len(sample.completion_ids),
                                   "terminated": sample.terminated, "status": info["status"],
                                   "prompt_sha256": hashlib.sha256(
                                       str(sample.prompt_ids).encode()).hexdigest()}
                                  for sample, info in trajectory] for trajectory in trajectories]}
        logs.append(row)
        write_json(Path(output) / "progress.json", {"groups": logs})
    actor.save(str(Path(output) / "adapter"))
    report = {"manifest": manifest,
              "adapter_before": before, "adapter_after": adapter_digest(actor.model), "groups": logs}
    write_json(Path(output) / "training-report.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["sft", "rloo"])
    parser.add_argument("--model", default="models/Qwen3-0.6B")
    parser.add_argument("--adapter")
    parser.add_argument("--output", required=True)
    parser.add_argument("--episodes", type=int, default=12)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--groups", type=int, default=4)
    parser.add_argument("--group-size", type=int, default=4)
    args = parser.parse_args()
    if args.phase == "sft":
        train_sft(args.model, args.output, episodes=args.episodes, epochs=args.epochs)
    else:
        if not args.adapter:
            parser.error("rloo requires --adapter")
        train_rloo(args.model, args.adapter, args.output, groups=args.groups, group_size=args.group_size)
