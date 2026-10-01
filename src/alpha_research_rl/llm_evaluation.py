"""Identical development tasks and decoding for base/SFT/RL actor comparisons."""

import argparse
import json
from pathlib import Path

import numpy as np

from .artifacts import run_manifest, write_json
from .llm import LocalActor, adapter_digest, completion_log_prob
from .training import make_training_env, seed_everything

TASKS = [{"seed": 11000 + index, "regime": ["signal", "null", "decay"][index % 3]}
         for index in range(6)]


def evaluate_actor(model_path, adapter, output, label):
    seed_everything(31)
    actor = LocalActor(model_path, adapter)
    episodes = []
    for task in TASKS:
        env = make_training_env(**task)
        observation = env.reset()
        actions = []
        for _ in range(observation["initial_budget"] + 1):
            sample = actor.sample(observation, stochastic=False)
            observation, reward, done, info = env.step(sample.action)
            actions.append({"action": sample.action, "text": sample.text,
                            "terminated": sample.terminated, **info})
            if done:
                break
        if not done:
            raise RuntimeError("evaluation episode failed to terminate")
        episode = {**task, "reward": reward, "spent_budget": observation["spent_budget"],
                   "selected": observation["selected"], "actions": actions}
        episodes.append(episode)
        print(json.dumps({"actor": label, **task, "reward": reward,
                          "n_actions": len(actions)}), flush=True)
    summary = {"mean_reward": float(np.mean([episode["reward"] for episode in episodes])),
               "n_episodes": len(episodes),
               "invalid_actions": sum(action["status"] == "invalid"
                                      for episode in episodes for action in episode["actions"]),
               "duplicate_actions": sum(action["status"] == "duplicate"
                                        for episode in episodes for action in episode["actions"]),
               "accepted_proposals": sum(action["action"].get("action") in {"propose", "mutate"}
                                          and action["status"] == "ok"
                                          for episode in episodes for action in episode["actions"])}
    report = {"manifest": run_manifest({"label": label, "tasks": TASKS, "decoding": "greedy",
               "data": "synthetic development only", "max_action_tokens": 64, "budget": 10,
               "not_final_holdout": True}), "summary": summary, "episodes": episodes}
    write_json(output, report)
    return report


def check_adapter_roundtrip(model_path, adapter, output):
    """Evidence that saved parameters and masked action likelihood survive reload."""
    import gc

    import torch
    actor = LocalActor(model_path, adapter, trainable=True)
    observation = make_training_env(9000, "signal").reset()
    prompt = actor.prompt_ids(observation)
    target = actor.tokenizer.encode('{"action":"stop"}', add_special_tokens=False) \
        + [actor.tokenizer.eos_token_id]
    with torch.no_grad():
        logp_before = float(completion_log_prob(actor.model, prompt, target))
    digest_before = adapter_digest(actor.model)
    saved = str(Path(output).parent / "roundtrip-adapter")
    actor.save(saved)
    del actor
    gc.collect()
    torch.cuda.empty_cache()
    restored = LocalActor(model_path, saved, trainable=True)
    with torch.no_grad():
        logp_after = float(completion_log_prob(restored.model, prompt, target))
    result = {"adapter_digest_before": digest_before, "adapter_digest_after": adapter_digest(restored.model),
              "completion_logp_before": logp_before, "completion_logp_after": logp_after,
              "absolute_logp_difference": abs(logp_after - logp_before)}
    if result["adapter_digest_before"] != result["adapter_digest_after"] or abs(logp_after-logp_before) > 1e-4:
        raise AssertionError("Adapter did not preserve weights/likelihood after save/reload")
    write_json(output, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/Qwen3-0.6B")
    parser.add_argument("--adapter")
    parser.add_argument("--output", required=True)
    parser.add_argument("--label", default="base")
    parser.add_argument("--roundtrip", action="store_true")
    args = parser.parse_args()
    if args.roundtrip:
        print(check_adapter_roundtrip(args.model, args.adapter, args.output))
    else:
        evaluate_actor(args.model, args.adapter, args.output, args.label)
