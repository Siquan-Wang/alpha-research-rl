"""Controlled whole-fenced-JSON tolerance, separate from the strict evaluator."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass

import numpy as np

from .artifacts import run_manifest, write_json
from .llm import LocalActor, parse_action
from .llm_evaluation import TASKS
from .training import make_training_env, seed_everything

PARSER_VERSION = "whole-json-or-single-json-fence-v1"
_FENCE = re.compile(r"```json\r?\n(?P<body>[\s\S]*?)\r?\n```")


@dataclass(frozen=True)
class ParsedCompletion:
    action: dict
    accepted_format: str | None
    failure: str | None


def parse_completion(text: str, terminated: bool) -> ParsedCompletion:
    """Accept only a terminated whole JSON object or single whole json fence.

    This does not repair or validate the research action schema. Environment
    validation still determines whether an accepted dictionary is a valid action.
    JSON decoding matches the original strict parser, which remains unchanged.
    """
    if not terminated:
        return ParsedCompletion({"action": "invalid"}, None, "unterminated_completion")
    if not isinstance(text, str):
        return ParsedCompletion({"action": "invalid"}, None, "non_text_completion")
    stripped = text.strip()
    fenced = _FENCE.fullmatch(stripped)
    body = fenced.group("body") if fenced else stripped
    accepted_format = "json_fence" if fenced else "strict_json"
    try:
        decoded = json.loads(body)
    except (ValueError, TypeError, RecursionError):
        return ParsedCompletion({"action": "invalid"}, None,
                                "invalid_json_body" if fenced else "unsupported_or_invalid_format")
    if not isinstance(decoded, dict):
        return ParsedCompletion({"action": "invalid"}, None, "non_object_json")
    # Delegate the object interpretation to the untouched strict action parser.
    return ParsedCompletion(parse_action(body), accepted_format, None)


def evaluate_actor_episodes(actor, tasks=None) -> tuple[list[dict], dict]:
    """Pure rollout mechanics, injectable actor for CPU-only invariant tests."""
    tasks = TASKS if tasks is None else tasks
    episodes = []
    for task in tasks:
        env = make_training_env(**task)
        observation = env.reset()
        actions = []
        done = False
        for _ in range(observation["initial_budget"] + 1):
            sample = actor.sample(observation, stochastic=False, max_tokens=64)
            parsed = parse_completion(sample.text, sample.terminated)
            # strict acceptance diagnoses the raw container only, without stripping
            # fences; its action remains exactly LocalActor's original action.
            strict_accepted = parsed.accepted_format == "strict_json"
            strict_action = parse_action(sample.text) if sample.terminated else {"action": "invalid"}
            observation, reward, done, info = env.step(parsed.action)
            actions.append({"action": parsed.action, "text": sample.text,
                            "terminated": sample.terminated, "accepted_format": parsed.accepted_format,
                            "parse_failure": parsed.failure, "strict_format_accepted": strict_accepted,
                            "strict_action": strict_action, **info})
            if done:
                break
        if not done:
            raise RuntimeError("format-ablation episode failed to terminate")
        episode = {**task, "reward": reward, "spent_budget": observation["spent_budget"],
                   "selected": observation["selected"], "history": observation["history"], "actions": actions}
        episodes.append(episode)
    all_actions = [action for episode in episodes for action in episode["actions"]]
    formats = Counter(action["accepted_format"] for action in all_actions if action["accepted_format"])
    failures = Counter(action["parse_failure"] for action in all_actions if action["parse_failure"])
    def action_name(action):
        name = action["action"].get("action", "missing")
        return name if isinstance(name, str) else "non_string_action"

    attempted = Counter(action_name(action) for action in all_actions)
    successful = Counter(action_name(action) for action in all_actions
                         if action["status"] == "ok")
    summary = {
        "mean_reward": float(np.mean([episode["reward"] for episode in episodes])) if episodes else None,
        "n_episodes": len(episodes), "n_actions": len(all_actions),
        "invalid_actions": sum(action["status"] == "invalid" for action in all_actions),
        "duplicate_actions": sum(action["status"] == "duplicate" for action in all_actions),
        "accepted_proposals": sum(action_name(action) in {"propose", "mutate"}
                                  and action["status"] == "ok" for action in all_actions),
        "format_acceptance": dict(formats), "parse_failures": dict(failures),
        "strict_format_accepted": sum(action["strict_format_accepted"] for action in all_actions),
        "attempted_action_counts": dict(attempted), "successful_action_counts": dict(successful),
    }
    return episodes, summary


def evaluate_actor(model_path: str, adapter: str | None, output: str, label: str) -> dict:
    """Run the identical greedy format ablation for any locally loaded checkpoint."""
    manifest = run_manifest({
        "label": label, "tasks": TASKS, "decoding": "greedy", "seed": 31,
        "data": "synthetic development only", "max_action_tokens": 64, "budget": 10,
        "parser_version": PARSER_VERSION, "requires_termination": True,
        "accepted_formats": ["whole JSON object", "one whole lowercase json Markdown fence"],
        "ablation": "container formatting tolerance; original strict evaluator unchanged",
        "not_final_holdout": True, "training": False, "manifest_capture": "entry before model load",
    })
    seed_everything(31)
    actor = LocalActor(model_path, adapter)
    episodes, summary = evaluate_actor_episodes(actor)
    for episode in episodes:
        print(json.dumps({"actor": label, "seed": episode["seed"], "regime": episode["regime"],
                          "reward": episode["reward"], "n_actions": len(episode["actions"])}), flush=True)
    report = {"manifest": manifest, "summary": summary, "episodes": episodes}
    write_json(output, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="models/Qwen3-0.6B")
    parser.add_argument("--adapter")
    parser.add_argument("--output", required=True)
    parser.add_argument("--label", default="base")
    args = parser.parse_args()
    evaluate_actor(args.model, args.adapter, args.output, args.label)


if __name__ == "__main__":
    main()
