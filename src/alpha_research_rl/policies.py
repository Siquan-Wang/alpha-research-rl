"""Transparent non-learning controls. These are not LLM or RL results."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Protocol

import numpy as np


class Policy(Protocol):
    def act(self, observation: dict[str, Any]) -> dict[str, Any]: ...


def candidate_library() -> list[str]:
    """Predeclared causal templates; fixed-pool experiments test selection only."""
    return [
        "returns",
        "ts_mean(returns, 3)",
        "ts_mean(returns, 5)",
        "ts_mean(returns, 10)",
        "ts_mean(returns, 20)",
        "ts_std(returns, 5)",
        "ts_std(returns, 20)",
        "sub(ts_mean(returns, 3), ts_mean(returns, 20))",
        "div(ts_mean(returns, 5), ts_std(returns, 20))",
        "mul(returns, div(volume, ts_mean(volume, 20)))",
        "div(volume, ts_mean(volume, 5))",
        "delta(log(volume), 5)",
    ]


def _screened(obs: dict) -> dict[int, dict]:
    result = {}
    for key, evidence in obs.get("evidence", {}).items():
        score = evidence.get("screen")
        if score and score.get("mean_ic") is not None and math.isfinite(score["mean_ic"]):
            result[int(key)] = score
    return result


def _remaining_candidates(obs: dict) -> list[int]:
    return [c["id"] for c in obs["candidates"] if "screen" not in obs.get("evidence", {}).get(str(c["id"]), {})]


@dataclass
class StopPolicy:
    def act(self, observation: dict) -> dict:
        return {"action": "stop"}


@dataclass
class ScreenThenSelect:
    """Spend a fixed fraction of the budget screening; retain best oriented IC."""

    screen_fraction: float = 0.65
    max_selected: int = 3

    def act(self, observation: dict) -> dict:
        obs = observation
        screened = _screened(obs)
        remaining = _remaining_candidates(obs)
        target = max(1, min(len(obs["candidates"]), int(obs["initial_budget"] * self.screen_fraction)))
        if remaining and len(screened) < target and obs["budget"] > self.max_selected:
            return {"action": "screen", "candidate": remaining[0]}
        ranked = sorted(screened, key=lambda k: (-abs(screened[k]["mean_ic"]), k))
        for idx in ranked:
            if idx not in obs["selected"] and len(obs["selected"]) < self.max_selected and obs["budget"] >= 1:
                return {"action": "select", "candidate": idx}
        return {"action": "stop"}


@dataclass
class RandomSearch:
    """Random candidate coverage with the same screen/select cost schedule."""

    seed: int = 0
    screen_fraction: float = 0.65
    max_selected: int = 3
    _rng: np.random.Generator = field(init=False, repr=False)

    def __post_init__(self):
        self._rng = np.random.default_rng(self.seed)

    def act(self, observation: dict) -> dict:
        action = ScreenThenSelect(self.screen_fraction, self.max_selected).act(observation)
        if action["action"] == "screen":
            action["candidate"] = int(self._rng.choice(_remaining_candidates(observation)))
        return action


@dataclass
class StabilityAware:
    """A specified diagnostic heuristic, not a statistically calibrated policy."""

    screens: int = 4
    max_selected: int = 2

    def act(self, observation: dict) -> dict:
        obs = observation
        screened = _screened(obs)
        remaining = _remaining_candidates(obs)
        if remaining and len(screened) < self.screens and obs["budget"] > 3:
            return {"action": "screen", "candidate": remaining[0]}
        ranked = sorted(screened, key=lambda k: (-abs(screened[k]["mean_ic"]), k))
        for idx in ranked[: self.max_selected]:
            evidence = obs["evidence"][str(idx)]
            if "stability" not in evidence and obs["budget"] >= 3:
                return {"action": "stability", "candidate": idx}
        scores = {}
        for idx in ranked:
            evidence = obs["evidence"][str(idx)]
            windows = evidence.get("stability", {}).get("windows", [])
            orientation = 1 if screened[idx]["mean_ic"] >= 0 else -1
            valid = [orientation * w["mean_ic"] for w in windows if w.get("mean_ic") is not None]
            scores[idx] = min(valid) if valid else abs(screened[idx]["mean_ic"]) * 0.5
        for idx in sorted(scores, key=lambda k: (-scores[k], k)):
            if scores[idx] > 0 and idx not in obs["selected"] and len(obs["selected"]) < self.max_selected:
                return {"action": "select", "candidate": idx}
        return {"action": "stop"}


def build_policy(name: str, seed: int = 0) -> Policy:
    factories = {
        "stop": StopPolicy,
        "fixed": ScreenThenSelect,
        "random": lambda: RandomSearch(seed=seed),
        "stability": StabilityAware,
    }
    try:
        return factories[name]()
    except KeyError as exc:
        raise ValueError(f"Unknown policy {name!r}; choose {list(factories)}") from exc
