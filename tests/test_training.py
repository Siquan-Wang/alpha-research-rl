"""Numerical training checks using an original six-token bigram actor on CPU."""

import json
import math
from types import SimpleNamespace

import numpy as np
import pytest

from alpha_research_rl.llm import ActionSample, completion_log_prob, parse_action
from alpha_research_rl.training import leave_one_out_advantages

torch = pytest.importorskip("torch")


class ToyBigram(torch.nn.Module):
    """A tiny causal model; row i predicts the token following token i."""

    def __init__(self, zero=False):
        super().__init__()
        values = torch.zeros((6, 6)) if zero else torch.arange(36).reshape(6, 6).float() / 13
        self.transitions = torch.nn.Parameter(values)

    @property
    def device(self):
        return self.transitions.device

    def forward(self, input_ids, use_cache=False):
        assert not use_cache
        return SimpleNamespace(logits=self.transitions[input_ids])


def test_completion_logprob_matches_independent_conditional_probability():
    model = ToyBigram()
    prompt, completion = [0, 1, 2], [3, 4, 5]
    # Independently sum elementary log conditional probabilities, using each
    # previous token's transition row rather than a shifted CE implementation.
    expected = 0.0
    previous = prompt[-1]
    for target in completion:
        logits = model.transitions[previous].detach().tolist()
        expected += logits[target] - math.log(sum(math.exp(value) for value in logits))
        previous = target
    actual = completion_log_prob(model, prompt, completion)
    assert actual.item() == pytest.approx(expected, abs=1e-6)


def test_prompt_masking_and_next_token_alignment_have_exact_gradient_support():
    model = ToyBigram()
    completion_log_prob(model, [0, 1, 2], [3, 4]).backward()
    gradients = model.transitions.grad
    assert torch.count_nonzero(gradients[0]).item() == 0
    assert torch.count_nonzero(gradients[1]).item() == 0
    assert torch.count_nonzero(gradients[4]).item() == 0
    assert gradients[2, 3].item() > 0 and gradients[3, 4].item() > 0
    assert gradients[2, 4].item() < 0 and gradients[3, 3].item() < 0
    # Prompt tokens excluded from loss: changing an earlier prompt-only row
    # cannot affect this model's completion probability.
    before = completion_log_prob(model, [0, 1, 2], [3, 4]).item()
    with torch.no_grad():
        model.transitions[0] = torch.tensor([10., -10., 20., -20., 30., -30.])
    assert completion_log_prob(model, [0, 1, 2], [3, 4]).item() == before


def test_completion_probability_includes_eos_and_sums_instead_of_averaging():
    model = ToyBigram(zero=True)
    one = completion_log_prob(model, [1], [2])
    with_eos = completion_log_prob(model, [1], [2, 5])
    assert one.item() == pytest.approx(-math.log(6))
    assert with_eos.item() == pytest.approx(-2 * math.log(6))


@pytest.mark.parametrize("prompt,completion", [([], [1]), ([1], []), ([], [])])
def test_empty_sequences_rejected(prompt, completion):
    with pytest.raises(ValueError):
        completion_log_prob(ToyBigram(), prompt, completion)


def test_leave_one_out_uses_only_other_trajectory_rewards():
    # Each expected baseline is the arithmetic mean of the other two rewards.
    rewards = [3., 1., -2.]
    advantages = leave_one_out_advantages(rewards)
    np.testing.assert_allclose(advantages, [3.5, .5, -4.])
    changed = leave_one_out_advantages([9., 1., -2.])
    assert changed[0] - advantages[0] == pytest.approx(6)
    assert changed[1] - advantages[1] == pytest.approx(-3)
    assert advantages.sum() == pytest.approx(0)


@pytest.mark.parametrize("reward,size", [(.1, 3), (-.01, 7), (1e8 + .1, 5), (0, 4)])
def test_identical_rewards_have_exactly_zero_advantages(reward, size):
    np.testing.assert_array_equal(leave_one_out_advantages([reward] * size), np.zeros(size))


@pytest.mark.parametrize("rewards", [[], [1], [[1, 2], [3, 4]], [1, float("nan")], [1, float("inf")]])
def test_invalid_baseline_inputs_rejected(rewards):
    with pytest.raises(ValueError):
        leave_one_out_advantages(rewards)


@pytest.mark.parametrize("text", ["", "{", "{\"action\":'stop'}", "[]", "null", "true", "3",
                                    "```json\n{\"action\":\"stop\"}\n```",
                                    "{\"action\":\"stop\"} trailing"])
def test_malformed_or_nonobject_actions_fail_closed(text):
    assert parse_action(text) == {"action": "invalid"}


def test_action_parser_preserves_fields_for_environment_validation():
    text = ' {"action":"mutate","candidate":0,"expression":"ts_mean(returns,3)"} '
    assert parse_action(text) == {"action": "mutate", "candidate": 0, "expression": "ts_mean(returns,3)"}
    # JSON syntax parsing is not environment validation: these attempts must
    # reach the environment and be charged, rather than silently re-sampled.
    assert parse_action('{"action":"screen","candidate":true}') == {"action": "screen", "candidate": True}


def run_toy_rloo(monkeypatch, tmp_path, constant_reward=None, group_size=2):
    from alpha_research_rl import training

    instances = []

    class ToyActor:
        def __init__(self, *args, **kwargs):
            self.model = ToyBigram(zero=True)
            self.sample_number = 0
            self.before = self.model.transitions.detach().clone()
            instances.append(self)

        def sample(self, observation, stochastic=False):
            assert stochastic
            token = 2 + self.sample_number % 2
            self.sample_number += 1
            action = {"action": "select", "candidate": token}
            return ActionSample([1], [token], json.dumps(action), action, True)

        def save(self, destination):
            self.saved_destination = destination

    class ToyEnvironment:
        def reset(self):
            return {"initial_budget": 1}

        def step(self, action):
            reward = constant_reward if constant_reward is not None else (.8 if action["candidate"] == 2 else -.2)
            return {"done": True}, reward, True, {"status": "ok"}

    monkeypatch.setattr(training, "LocalActor", ToyActor)
    monkeypatch.setattr(training, "make_training_env", lambda *args: ToyEnvironment())
    report = training.train_rloo("unused-local-model", "unused-adapter", str(tmp_path),
                                 groups=1, group_size=group_size)
    return instances[0], report


def test_actual_rloo_trainer_increases_rewarded_and_decreases_penalized_action(monkeypatch, tmp_path):
    actor, report = run_toy_rloo(monkeypatch, tmp_path)
    row = report["groups"][0]
    np.testing.assert_allclose(row["advantages"], [1., -1.])
    assert row["optimizer_step"] and row["preclip_grad_norm"] > 0
    before_logprob = -math.log(6)
    assert completion_log_prob(actor.model, [1], [2]).item() > before_logprob
    assert completion_log_prob(actor.model, [1], [3]).item() < before_logprob
    assert report["adapter_before"] != report["adapter_after"]
    assert actor.saved_destination.endswith("adapter")
    assert (tmp_path / "training-report.json").is_file()


def test_actual_rloo_constant_reward_group_skips_update(monkeypatch, tmp_path):
    actor, report = run_toy_rloo(monkeypatch, tmp_path, constant_reward=.1, group_size=3)
    row = report["groups"][0]
    assert row["optimizer_step"] is False
    np.testing.assert_array_equal(row["advantages"], [0., 0., 0.])
    torch.testing.assert_close(actor.model.transitions, actor.before, rtol=0, atol=0)
    assert report["adapter_before"] == report["adapter_after"]


def test_actual_sft_trainer_learns_completion_and_eos_without_prompt_loss(monkeypatch, tmp_path):
    from alpha_research_rl import training

    instances = []

    class ToyActor:
        def __init__(self, *args, **kwargs):
            self.model = ToyBigram(zero=True)
            self.before = self.model.transitions.detach().clone()
            self.tokenizer = SimpleNamespace(eos_token_id=5, encode=lambda text, add_special_tokens: [2])
            instances.append(self)

        def prompt_ids(self, observation):
            return [0, 1]

        def save(self, destination):
            self.saved_destination = destination

    monkeypatch.setattr(training, "LocalActor", ToyActor)
    monkeypatch.setattr(training, "make_training_env", lambda *args: None)
    monkeypatch.setattr(training, "run_episode", lambda *args: {
        "trajectory": [{"observation": {}, "action": {"action": "stop"}}]})
    report = training.train_sft("unused-local-model", str(tmp_path), episodes=1, epochs=1)
    actor = instances[0]
    assert report["n_examples"] == 1 and len(report["updates"]) == 1
    assert report["updates"][0]["loss_per_completion_token"] == pytest.approx(math.log(6))
    assert completion_log_prob(actor.model, [0, 1], [2, 5]).item() > -2 * math.log(6)
    assert actor.model.transitions[1, 2].item() > 0
    assert actor.model.transitions[2, 5].item() > 0
    torch.testing.assert_close(actor.model.transitions[0], actor.before[0], rtol=0, atol=0)
    assert report["adapter_before"] != report["adapter_after"]
