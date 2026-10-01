"""Deterministic constructed-feedback teaching fixtures, not market discoveries.

The teacher consumes only the public observation. Task IDs and dataset provenance
are bookkeeping and must never be included in an actor's prompt.
"""

from __future__ import annotations

import copy
import math
from collections import Counter

import numpy as np

VERSION = "constructed-feedback-v2"
SELECT_THRESHOLD = 0.04
MUTATE_THRESHOLD = 0.14
DIAGNOSTIC_STD = 0.15
TRAIN_SEEDS = tuple(range(5000, 5032))
DEV_SEEDS = tuple(range(6000, 6012))
TRAIN_FAMILIES = {
    "return_levels": ("returns", "delay(returns,1)", "ts_mean(returns,5)", "delta(returns,2)"),
    "volume_changes": ("delta(log(volume),1)", "ts_mean(delta(log(volume),1),5)",
                       "div(volume,ts_mean(volume,5))", "volume"),
    "price_transforms": ("delta(log(close),1)", "delta(log(close),5)",
                         "div(close,ts_mean(close,10))", "close"),
    "volatility": ("ts_std(returns,5)", "ts_std(returns,20)", "abs(returns)", "zscore(returns)"),
}
DEV_FAMILIES = {
    "mixed_composition": ("add(returns,delta(log(volume),1))", "mul(returns,div(volume,ts_mean(volume,5)))",
                          "sub(ts_mean(returns,3),ts_mean(returns,20))", "div(ts_mean(returns,5),ts_std(returns,20))"),
    "restricted_returns": ("delta(returns,3)", "ts_mean(returns,10)",
                           "div(returns,ts_std(returns,10))", "rank(returns)"),
}


def _metrics(ic, std=.05):
    return {"mean_ic": float(ic), "n_dates": 80, "coverage": 1., "ic_std": float(std)}


def _record(name, candidate, cost=1, status="ok", reason=None):
    return {"action": name, "candidate": candidate, "cost": cost, "status": status, "reason": reason}


def _screen(obs, candidate, ic, std=.05):
    obs["evidence"][str(candidate)] = {"screen": _metrics(ic, std)}
    obs["orientation"][str(candidate)] = -1 if ic < 0 else 1
    obs["history"].append(_record("screen", candidate))
    _budget(obs)


def _budget(obs):
    obs["spent_budget"] = sum(record["cost"] for record in obs["history"])
    obs["budget"] = obs["initial_budget"] - obs["spent_budget"]


def _task(split, index):
    families = TRAIN_FAMILIES if split == "train" else DEV_FAMILIES
    seeds = TRAIN_SEEDS if split == "train" else DEV_SEEDS
    per_family = len(seeds) // len(families)
    family = list(families)[index // per_family]
    seed = seeds[index]
    permutation = np.random.default_rng(seed).permutation(4)
    expressions = [families[family][int(i)] for i in permutation]
    return seed, family, expressions


def _base(split, index, initial_budget=10):
    seed, family, expressions = _task(split, index)
    features = ["close", "returns"] if family == "restricted_returns" else ["close", "volume", "returns"]
    observation = {
        "budget": initial_budget, "initial_budget": initial_budget, "spent_budget": 0, "done": False,
        "candidates": [{"id": i, "expression": expression} for i, expression in enumerate(expressions)],
        "evidence": {}, "selected": [], "orientation": {}, "history": [],
        "generation": {"enabled": True, "max_candidates": 64, "proposal_cost": 2, "mutation_cost": 2},
        "provenance": {str(i): {"kind": "initial", "parent": None} for i in range(4)},
        "supported_features": features,
    }
    return observation, seed, family


def curriculum_action(observation: dict) -> dict:
    """Predeclared teaching heuristic using public fields alone, never rewards."""
    obs = observation
    if obs["selected"] or obs["budget"] < 2:
        return {"action": "stop"}
    screened = {}
    for key, evidence in obs["evidence"].items():
        screen = evidence.get("screen", {})
        ic = screen.get("mean_ic")
        if (ic is not None and math.isfinite(ic) and screen.get("coverage", 0) >= .8
                and screen.get("n_dates", 0) >= 64):
            screened[int(key)] = screen
    diagnostic = [i for i, screen in screened.items()
                  if screen["ic_std"] > DIAGNOSTIC_STD and "stability" not in obs["evidence"][str(i)]]
    if diagnostic and obs["budget"] >= 2:
        return {"action": "stability", "candidate": min(diagnostic)}
    remaining = [candidate["id"] for candidate in obs["candidates"]
                 if "screen" not in obs["evidence"].get(str(candidate["id"]), {})]
    if remaining and obs["budget"] >= 3:
        return {"action": "screen", "candidate": min(remaining)}
    if not screened:
        return {"action": "stop"}
    best = min(screened, key=lambda i: (-abs(screened[i]["mean_ic"]), i))
    strength = abs(screened[best]["mean_ic"])
    if strength < SELECT_THRESHOLD:
        return {"action": "stop"}
    if obs["budget"] <= 2:
        return {"action": "select", "candidate": best}
    if not obs.get("generation", {}).get("enabled"):
        return {"action": "select", "candidate": best}
    parent = next(candidate["expression"] for candidate in obs["candidates"] if candidate["id"] == best)
    if strength < MUTATE_THRESHOLD:
        return {"action": "propose", "expression": f"ts_mean({parent},3)"}
    return {"action": "mutate", "candidate": best, "expression": f"ts_mean({parent},10)"}


def _example(observation, split, index, category, variant, pair_id=None):
    seed, family, _ = _task(split, index)
    return {
        "observation": observation, "action": curriculum_action(observation),
        "task_id": f"{VERSION}:{split}:{seed}", "family": family,
        "provenance": {"kind": "explicitly_constructed_feedback_curriculum", "seed": seed,
                       "partition": split, "category": category, "variant": variant, "pair_id": pair_id,
                       "not_observed_market_scores": True, "no_assessment_used": True},
    }


def _all_screened(split, index, budget, winner, magnitude):
    obs, _, _ = _base(split, index, budget)
    sign = -1 if (index // 4) % 2 else 1
    for candidate in range(4):
        ic = sign * (magnitude if candidate == winner else .01)
        _screen(obs, candidate, ic)
    return obs


def _control(split, index, variant):
    obs, _, _ = _base(split, index)
    target = index % 4
    kind = (index // 4) % 4
    sign = -1 if variant else 1
    if kind == 0:
        for candidate in range(target):
            _screen(obs, candidate, sign * .01)
    elif kind == 1:
        _screen(obs, target, sign * .1, std=.25)
    elif kind == 2:
        obs["history"] = [_record("invalid", None, status="invalid", reason="invalid_action") for _ in range(9)]
        _budget(obs)
    else:
        _screen(obs, target, sign * .12)
        obs["selected"] = [target]
        obs["history"].append(_record("select", target))
        _budget(obs)
    return _example(obs, split, index, "control", str(variant))


def _selection_pair(split, index, switch_winner=False):
    target = index % 4
    left = _all_screened(split, index, 6, target, .12)
    if switch_winner:
        right = _all_screened(split, index, 6, (target + 1) % 4, .12)
    else:
        right = _all_screened(split, index, 6, target, .02)
    pair_id = f"{split}:{index}:selection"
    return [_example(left, split, index, "selection", "strong", pair_id),
            _example(right, split, index, "selection", "other_winner" if switch_winner else "weak", pair_id)]


def _generation_pair(split, index):
    target = index % 4
    pair_id = f"{split}:{index}:generation"
    return [_example(_all_screened(split, index, 10, target, magnitude), split, index,
                     "generation", variant, pair_id)
            for magnitude, variant in ((.1, "moderate"), (.18, "strong"))]


def build_counterfactual_pairs() -> list[dict]:
    """Twenty-four held-out pairs; each pair changes only visible screen scores."""
    pairs = []
    for index in range(len(DEV_SEEDS)):
        for examples in (_selection_pair("dev", index, switch_winner=index < 6), _generation_pair("dev", index)):
            left, right = examples
            pairs.append({"pair_id": left["provenance"]["pair_id"], "task_id": left["task_id"],
                          "family": left["family"], "left": left, "right": right})
    return pairs


def build_curriculum(split: str = "train") -> dict:
    """Return examples and metadata; every family/task is assigned before permutation."""
    if split not in ("train", "dev"):
        raise ValueError("split must be train or dev")
    if split == "train":
        examples = []
        for index in range(len(TRAIN_SEEDS)):
            examples.extend([_control(split, index, 0), _control(split, index, 1)])
            examples.extend(_selection_pair(split, index))
            examples.extend(_generation_pair(split, index))
    else:
        examples = [example for pair in build_counterfactual_pairs() for example in (pair["left"], pair["right"])]
    metadata = {
        "version": VERSION, "split": split, "data_kind": "explicitly_constructed_feedback_curriculum",
        "no_financial_or_discovery_evidence": True, "teacher_inputs": "public observation only",
        "seeds": list(TRAIN_SEEDS if split == "train" else DEV_SEEDS),
        "families": list(TRAIN_FAMILIES if split == "train" else DEV_FAMILIES),
        "partition_before_permutation": True, "n_examples": len(examples),
        "category_counts": dict(Counter(example["provenance"]["category"] for example in examples)),
        "action_counts": dict(Counter(example["action"]["action"] for example in examples)),
        "select_threshold": SELECT_THRESHOLD, "mutate_threshold": MUTATE_THRESHOLD,
        "diagnostic_std_threshold": DIAGNOSTIC_STD, "declared_feedback_dates": 80,
        "valid_date_requirement": 64, "propose_lookback": 3, "mutate_lookback": 10,
        "actor_prompt_fields": ["observation"],
        "limitations": ["constructed scores have no associated panel or assessment labels",
                        "teacher is a transparent heuristic, not an optimal research policy",
                        "dev generation family/AST transfer is grammar transfer, not discovery"],
    }
    return copy.deepcopy({"examples": examples, "metadata": metadata})
