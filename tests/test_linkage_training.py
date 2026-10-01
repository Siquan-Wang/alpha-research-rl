"""Placebo assignment law and real CPU optimizer/rollout control flow."""

import itertools
import json
from types import SimpleNamespace

import numpy as np
import pytest

from alpha_research_rl import linkage_training as lt
from alpha_research_rl.llm import ActionSample, adapter_digest


def test_permutation_law_preserves_failures_and_has_zero_mean_score_gradient():
    rewards = np.array([-1.01, .02, .02, -.04])
    scores = np.array([[1., 2.], [-3., 1.], [0., -4.], [2., 0.]])
    gradients = []
    permutations = list(itertools.permutations(range(4)))
    for p in permutations:
        rng = SimpleNamespace(permutation=lambda n, p=p: p)
        permutation, assigned, advantages = lt.permute_rewards(rewards, rng)
        np.testing.assert_array_equal(assigned, rewards[list(p)])
        np.testing.assert_array_equal(np.sort(assigned), np.sort(rewards))
        np.testing.assert_allclose(advantages, assigned - (assigned.sum() - assigned) / 3, atol=1e-15)
        gradients.append(-(advantages[:, None] * scores).mean(axis=0))
        assert tuple(permutation) == p
    np.testing.assert_allclose(np.mean(gradients, axis=0), 0, atol=1e-15)
    assert permutations[0] == (0, 1, 2, 3)  # Identity remains eligible.


def test_permutation_generator_is_independent_and_consumes_constant_groups():
    np.random.seed(123)
    expected = np.random.random(4)
    np.random.seed(123)
    rng = np.random.default_rng(700023)
    reference = np.random.default_rng(700023)
    for _ in range(16):
        permutation, assigned, advantages = lt.permute_rewards([.03] * 4, rng)
        np.testing.assert_array_equal(permutation, reference.permutation(4))
        np.testing.assert_array_equal(advantages, np.zeros(4))
        np.testing.assert_array_equal(assigned, [.03] * 4)
    np.testing.assert_array_equal(np.random.random(4), expected)


@pytest.mark.parametrize("constant", [True, False])
def test_actual_trainer_logs_fresh_groups_parent_and_exact_assignment(monkeypatch, tmp_path, constant):
    torch = pytest.importorskip("torch")

    class Model(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.transitions = torch.nn.Parameter(torch.zeros(6, 6))

        @property
        def device(self):
            return self.transitions.device

        def forward(self, input_ids, use_cache=False):
            return SimpleNamespace(logits=self.transitions[input_ids])

    initial_digest = adapter_digest(Model())
    instances = []

    class Actor:
        def __init__(self, *args, **kwargs):
            self.model = Model()
            self.provenance = {"fixture": True}
            self.calls = []
            instances.append(self)

        def sample(self, observation, stochastic, max_tokens):
            assert (tmp_path / "run-manifest.json").is_file()
            assert stochastic and max_tokens == 64
            self.calls.append(adapter_digest(self.model))
            token = 2 + len(self.calls) % 2
            action = {"action": "propose", "expression": "returns" if token == 2 else "delay(returns,1)"}
            return ActionSample([1], [token], json.dumps(action), action, True)

        def save(self, destination):
            pass

    class Task:
        def __init__(self, index):
            self.public_manifest = {"task_id": str(index)}

        def observation(self):
            return {"task": self.public_manifest["task_id"]}

        def evaluate(self, expression):
            value = .04 if constant or expression == "returns" else -.02
            return {"status": "ok", "expression": expression, "oriented_future_ic": value,
                    "reward": value - .01}

    monkeypatch.setattr(lt, "ProposalActor", Actor)
    monkeypatch.setattr(lt, "PARENT_DIGEST", initial_digest)
    monkeypatch.setattr(lt, "checkpoint_manifest", lambda path: {"combined_sha256": lt.PARENT_FILES_SHA})
    monkeypatch.setattr(lt, "selected_rl_tasks", lambda panel, seed: [Task(i) for i in range(16)])
    report = lt.train_placebo(SimpleNamespace(metadata={"raw_sha256": "fixture"}),
                              "unused", "unused", tmp_path, 23)
    actor = instances[0]
    assert len(actor.calls) == 64 and len(report["groups"]) == 16
    assert not report["stopped_at_exploration_gate"]
    rng = np.random.default_rng(700023)
    previous = initial_digest
    for index, group in enumerate(report["groups"]):
        assert group["adapter_before"] == previous
        assert actor.calls[index * 4:index * 4 + 4] == [previous] * 4
        previous = group["adapter_after"]
        np.testing.assert_array_equal(group["permutation"], rng.permutation(4))
        assert group["assigned_rewards"] == [group["true_rewards"][i] for i in group["permutation"]]
        assert group["true_rewards"] == [sample["outcome"]["reward"] for sample in group["samples"]]
        assert group["optimizer_step"] is (not constant)
    assert (report["adapter_before"] == report["adapter_after"]) is constant
    assert report["optimizer_steps"] == (0 if constant else 16)
    with pytest.raises(FileExistsError):
        lt.train_placebo(SimpleNamespace(), "unused", "unused", tmp_path, 23)


def test_invalid_reward_vector_is_rejected():
    for values in ([1, 2, 3], [1, 2, 3, np.nan]):
        with pytest.raises(ValueError):
            lt.permute_rewards(values, np.random.default_rng(23))
