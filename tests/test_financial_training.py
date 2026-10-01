"""Actual financial trainer's update and quality gate, with original CPU fixtures."""

import json
from types import SimpleNamespace

import pytest

from alpha_research_rl import financial_training
from alpha_research_rl.llm import ActionSample, completion_log_prob

torch = pytest.importorskip("torch")


class ToyModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.transitions = torch.nn.Parameter(torch.zeros(6, 6))

    @property
    def device(self):
        return self.transitions.device

    def forward(self, input_ids, use_cache=False):
        return SimpleNamespace(logits=self.transitions[input_ids])


class ToyTask:
    def __init__(self, year, half, scenario):
        self.year, self.half, self.scenario = year, half, scenario

    @property
    def public_manifest(self):
        return {"task_id": f"{self.year}-H{self.half}", "year": self.year, "half": self.half, "split": "train"}

    def observation(self):
        return {"supported_features": ["returns"], "probe_evidence": []}

    def evaluate(self, expression):
        if expression is None:
            return {"status": "invalid", "expression": None, "oriented_future_ic": None,
                    "reward": -1.01, "reason": "invalid_expression"}
        ic = .04
        if self.scenario == "quality":
            ic = .02 if expression == "returns" else .06
        return {"status": "ok", "expression": expression, "oriented_future_ic": ic,
                "reward": ic - .01, "reason": None}


def run_toy(monkeypatch, tmp_path, scenario):
    instances = []
    tasks = [ToyTask(year, half, scenario) for year in range(2002, 2018) for half in (1, 2)]

    class ToyActor:
        def __init__(self, *args, **kwargs):
            self.model = ToyModel()
            self.before = self.model.transitions.detach().clone()
            self.provenance = {"kind": "original_cpu_fixture"}
            self.sample_number = 0
            instances.append(self)

        def sample(self, observation, stochastic=False, max_tokens=64):
            assert stochastic and max_tokens == 64
            token = 2 + self.sample_number % 2
            self.sample_number += 1
            expression = "returns" if token == 2 or scenario == "constant" else "delay(returns,1)"
            action = {"action": "propose", "expression": expression}
            if scenario == "syntax" and token == 2:
                action = {"action": "invalid"}
            return ActionSample([1], [token], json.dumps(action), action, True)

        def save(self, destination):
            self.saved_destination = destination

    monkeypatch.setattr(financial_training, "ProposalActor", ToyActor)
    monkeypatch.setattr(financial_training, "list_tasks", lambda panel, split: tasks)
    monkeypatch.setattr(financial_training, "seed_everything", lambda seed: None)
    panel = SimpleNamespace(metadata={"raw_sha256": "cpu-fixture"})
    report = financial_training.financial_rloo(panel, "unused", "unused", str(tmp_path), seed=23)
    return instances[0], report


def test_constant_reward_gate_skips_every_update_and_preserves_digest(monkeypatch, tmp_path):
    actor, report = run_toy(monkeypatch, tmp_path, "constant")
    assert len(report["groups"]) == 8 and report["stopped_at_exploration_gate"]
    assert all(not group["optimizer_step"] for group in report["groups"])
    assert all(group["advantages"] == [0., 0., 0., 0.] for group in report["groups"])
    assert all(group["adapter_before"] == group["adapter_after"] for group in report["groups"])
    assert report["adapter_before"] == report["adapter_after"]
    torch.testing.assert_close(actor.model.transitions, actor.before, rtol=0, atol=0)


def test_invalid_vs_valid_reward_spread_alone_fails_quality_gate(monkeypatch, tmp_path):
    _, report = run_toy(monkeypatch, tmp_path, "syntax")
    assert len(report["groups"]) == 8 and report["stopped_at_exploration_gate"]
    assert all(max(group["rewards"]) - min(group["rewards"]) > 1 for group in report["groups"])
    assert all(group["legal_unique_asts"] == 1 for group in report["groups"])
    assert all(not group["quality_exploration"] for group in report["groups"])
    assert any(group["optimizer_step"] for group in report["groups"])


def test_two_legal_asts_with_identical_future_ic_fail_quality_gate(monkeypatch, tmp_path):
    _, report = run_toy(monkeypatch, tmp_path, "equal_ic")
    assert len(report["groups"]) == 8 and report["stopped_at_exploration_gate"]
    assert all(group["legal_unique_asts"] == 2 for group in report["groups"])
    assert all(group["usable_future_ic_range"] == 0 for group in report["groups"])
    assert all(not group["quality_exploration"] and not group["optimizer_step"] for group in report["groups"])


def test_quality_diversity_allows_sixteen_fresh_groups_and_changes_rewarded_probability(monkeypatch, tmp_path):
    actor, report = run_toy(monkeypatch, tmp_path, "quality")
    assert len(report["groups"]) == 16 and not report["stopped_at_exploration_gate"]
    assert actor.sample_number == 64
    assert all(group["quality_exploration"] for group in report["groups"])
    assert len({group["task"]["task_id"] for group in report["groups"]}) == 16
    assert report["adapter_before"] != report["adapter_after"]
    before = -torch.log(torch.tensor(6.)).item()
    assert completion_log_prob(actor.model, [1], [3]).item() > before
    assert completion_log_prob(actor.model, [1], [2]).item() < before
    assert (tmp_path / "run-manifest.json").is_file()
    assert (tmp_path / "training-report.json").is_file()


def test_registered_schedule_is_reproducible_and_contains_only_training_years(monkeypatch):
    tasks = [ToyTask(year, half, "constant") for year in range(2002, 2018) for half in (1, 2)]
    monkeypatch.setattr(financial_training, "list_tasks", lambda panel, split: tasks)
    first = financial_training.selected_rl_tasks(None, 23)
    second = financial_training.selected_rl_tasks(None, 23)
    other = financial_training.selected_rl_tasks(None, 29)
    assert first == second and first != other
    assert {(task.year, task.half) for task in first} == {
        (year, 1 if year % 2 == 0 else 2) for year in range(2002, 2018)}
    assert len(first) == 16 and all(task.year < 2018 for task in first)
    assert {(task.year, task.half) for task in first} == {(task.year, task.half) for task in other}
