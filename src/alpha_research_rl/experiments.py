"""Development experiments; do not label these runs untouched final tests."""

from __future__ import annotations

import copy
from pathlib import Path

import numpy as np

from .artifacts import run_manifest, write_json
from .data import make_synthetic_panel
from .environment import ResearchEnvironment
from .policies import build_policy, candidate_library
from .protocol import make_chronological_split


def run_episode(env, policy) -> dict:
    obs = env.reset()
    trajectory = []
    done = False
    reward = 0.0
    for _ in range(obs["initial_budget"] + 1):
        action = policy.act(copy.deepcopy(obs))
        before = copy.deepcopy(obs)
        obs, reward, done, info = env.step(action)
        trajectory.append({"observation": before, "action": action, "reward": reward,
                           "done": done, "status": info["status"], "reason": info["reason"]})
        if done:
            break
    if not done:
        raise RuntimeError("Environment failed to terminate within its action budget")
    return {
        "terminal_reward": reward,
        "spent_budget": obs["spent_budget"],
        "selected": obs["selected"],
        "trajectory": trajectory,
    }


def run_synthetic_benchmark(output: str | Path, seeds: list[int], budget: int = 12) -> dict:
    config = {
        "study": "development-smoke-v1", "data": "synthetic", "seeds": seeds,
        "regimes": ["signal", "null", "decay"], "budget": budget,
        "policies": ["stop", "fixed", "random", "stability"],
        "candidates": candidate_library(), "horizon": 5, "n_dates": 600, "n_assets": 32,
        "claim": "fixed-pool research-policy development only; no financial alpha or LLM training claim",
    }
    runs = []
    for regime in config["regimes"]:
        for seed in seeds:
            panel = make_synthetic_panel(seed=seed, n_dates=config["n_dates"], n_assets=config["n_assets"], regime=regime)
            split = make_chronological_split(len(panel.dates), horizon=config["horizon"])
            for policy_name in config["policies"]:
                env = ResearchEnvironment(panel, split, config["candidates"], budget=budget)
                result = run_episode(env, build_policy(policy_name, seed))
                result.update(regime=regime, seed=seed, policy=policy_name)
                runs.append(result)
    summary = []
    for regime in config["regimes"]:
        for policy in config["policies"]:
            group = [r for r in runs if r["regime"] == regime and r["policy"] == policy]
            values = [r["terminal_reward"] for r in group]
            summary.append({
                "regime": regime, "policy": policy, "n_seeds": len(group),
                "mean_reward": float(np.mean(values)),
                "std_across_synthetic_seeds": float(np.std(values, ddof=1)) if len(values) > 1 else None,
                "mean_budget_used": float(np.mean([r["spent_budget"] for r in group])),
            })
    report = {"manifest": run_manifest(config), "summary": summary, "runs": runs}
    write_json(output, report)
    return report
