import ast
import copy
import json
from collections import Counter

import numpy as np
import pytest

from alpha_research_rl.curriculum import (
    DEV_SEEDS,
    TRAIN_SEEDS,
    build_counterfactual_pairs,
    build_curriculum,
    curriculum_action,
)
from alpha_research_rl.data import MarketPanel, make_synthetic_panel
from alpha_research_rl.dsl import evaluate_expression


def test_deterministic_balanced_train_and_separate_dev():
    train, dev = build_curriculum(), build_curriculum("dev")
    assert train == build_curriculum()
    assert len(train["examples"]) == 192 and len(dev["examples"]) == 48
    assert train["metadata"]["category_counts"] == {"control": 64, "selection": 64, "generation": 64}
    assert set(TRAIN_SEEDS).isdisjoint(DEV_SEEDS)
    assert set(train["metadata"]["families"]).isdisjoint(dev["metadata"]["families"])
    assert {e["task_id"] for e in train["examples"]}.isdisjoint(e["task_id"] for e in dev["examples"])
    train["examples"][0]["observation"]["candidates"][0]["expression"] = "modified"
    assert build_curriculum()["examples"][0]["observation"]["candidates"][0]["expression"] != "modified"


def test_select_and_mutation_ids_balanced_and_both_signs_present():
    examples = build_curriculum()["examples"]
    for name in ("select", "mutate"):
        relevant = [e for e in examples if e["action"]["action"] == name]
        assert Counter(e["action"]["candidate"] for e in relevant) == {0: 8, 1: 8, 2: 8, 3: 8}
        for candidate in range(4):
            signs = {e["observation"]["orientation"][str(candidate)] for e in relevant
                     if e["action"]["candidate"] == candidate}
            assert signs == {-1, 1}


@pytest.mark.parametrize("split", ["train", "dev"])
def test_every_fixture_budget_evidence_history_and_provenance_coherent(split):
    for example in build_curriculum(split)["examples"]:
        obs, action = example["observation"], example["action"]
        json.dumps(example, allow_nan=False)
        assert obs["spent_budget"] == sum(row["cost"] for row in obs["history"])
        assert obs["budget"] + obs["spent_budget"] == obs["initial_budget"]
        assert obs["budget"] > 0 and not obs["done"]
        ids = {candidate["id"] for candidate in obs["candidates"]}
        assert ids == set(range(4))
        assert set(obs["provenance"]) == {str(i) for i in ids}
        for key, evidence in obs["evidence"].items():
            screen = evidence["screen"]
            assert int(key) in ids and screen["n_dates"] == 80 and screen["coverage"] == 1
            assert obs["orientation"][key] == (-1 if screen["mean_ic"] < 0 else 1)
            assert any(row["action"] == "screen" and row["candidate"] == int(key) for row in obs["history"])
        for candidate in obs["selected"]:
            assert str(candidate) in obs["evidence"]
            assert any(row["action"] == "select" and row["candidate"] == candidate for row in obs["history"])
        assert action == curriculum_action(obs)
        assert "assessment" not in obs and "family" not in obs and "task_id" not in obs
        assert example["provenance"]["no_assessment_used"]
        if action["action"] in ("select", "stability", "mutate"):
            assert str(action["candidate"]) in obs["evidence"]


def _without_visible_scores(obs):
    result = copy.deepcopy(obs)
    for evidence in result["evidence"].values():
        evidence["screen"]["mean_ic"] = 0
    return result


def test_twenty_four_heldout_pairs_change_only_visible_scores_and_change_action():
    pairs = build_counterfactual_pairs()
    assert len(pairs) == 24 and len({p["pair_id"] for p in pairs}) == 24
    for pair in pairs:
        left, right = pair["left"], pair["right"]
        assert left["task_id"] == right["task_id"] == pair["task_id"]
        assert left["family"] == right["family"] == pair["family"]
        assert _without_visible_scores(left["observation"]) == _without_visible_scores(right["observation"])
        assert left["action"] != right["action"]
        assert left["provenance"]["seed"] in DEV_SEEDS
        assert left["provenance"]["seed"] not in TRAIN_SEEDS


def test_teacher_cannot_use_task_family_or_dataset_bookkeeping():
    example = build_curriculum()["examples"][4]
    obs = example["observation"]
    assert curriculum_action(obs) == example["action"]
    example["task_id"] = "changed"
    example["family"] = "changed"
    example["provenance"] = {}
    assert curriculum_action(obs) == example["action"]


def test_proposals_and_mutations_are_new_safe_supported_expressions():
    panel = make_synthetic_panel(seed=7, n_dates=100, n_assets=8)
    expressions = set()
    for split in ("train", "dev"):
        for example in build_curriculum(split)["examples"]:
            action = example["action"]
            if action["action"] not in ("propose", "mutate"):
                continue
            obs = example["observation"]
            restricted = MarketPanel(panel.close, panel.volume, panel.returns, panel.dates, panel.assets,
                                     {"supported_features": obs["supported_features"]})
            expression = action["expression"]
            values = evaluate_expression(expression, restricted)
            assert values.shape == panel.close.shape
            key = ast.dump(ast.parse(expression, mode="eval"))
            assert key not in {ast.dump(ast.parse(c["expression"], mode="eval")) for c in obs["candidates"]}
            expressions.add(expression)
            parent = action.get("candidate")
            if parent is not None:
                assert obs["candidates"][parent]["expression"] in expression
    assert len(expressions) > 8


def test_score_sign_reversal_preserves_expression_decision():
    example = next(e for e in build_curriculum()["examples"] if e["action"]["action"] == "mutate")
    obs = copy.deepcopy(example["observation"])
    for key, evidence in obs["evidence"].items():
        evidence["screen"]["mean_ic"] *= -1
        obs["orientation"][key] *= -1
    assert curriculum_action(obs) == example["action"]


def test_candidate_permutation_preserves_selected_parent_and_generated_expression():
    mapping = {0: 2, 1: 0, 2: 3, 3: 1}
    examples = [e for e in build_curriculum()["examples"]
                if e["action"]["action"] in ("select", "mutate", "propose")]
    for example in examples:
        obs = copy.deepcopy(example["observation"])
        for candidate in obs["candidates"]:
            candidate["id"] = mapping[candidate["id"]]
        obs["candidates"].sort(key=lambda c: c["id"])
        for key in ("evidence", "orientation", "provenance"):
            obs[key] = {str(mapping[int(i)]): value for i, value in obs[key].items()}
        for record in obs["history"]:
            if record["candidate"] is not None:
                record["candidate"] = mapping[record["candidate"]]
        expected = copy.deepcopy(example["action"])
        if "candidate" in expected:
            expected["candidate"] = mapping[expected["candidate"]]
        assert curriculum_action(obs) == expected


def test_threshold_and_budget_rules_are_explicit():
    example = next(e for e in build_curriculum()["examples"] if e["action"]["action"] == "select")
    obs = copy.deepcopy(example["observation"])
    for evidence in obs["evidence"].values():
        evidence["screen"]["mean_ic"] = .01
    obs["evidence"]["2"]["screen"]["mean_ic"] = .04
    assert curriculum_action(obs) == {"action": "select", "candidate": 2}
    obs["evidence"]["2"]["screen"]["mean_ic"] = np.nextafter(.04, 0)
    assert curriculum_action(obs) == {"action": "stop"}
    obs["budget"] = 1
    obs["evidence"]["2"]["screen"]["mean_ic"] = .9
    assert curriculum_action(obs) == {"action": "stop"}


def test_invalid_partition_rejected():
    with pytest.raises(ValueError):
        build_curriculum("test")


def test_root_counterfactual_evaluator_counts_constant_actor_failures(monkeypatch, tmp_path):
    from types import SimpleNamespace

    from alpha_research_rl import curriculum_training

    class ConstantActor:
        def __init__(self, *args):
            self.provenance = {"kind": "cpu_test_fixture"}

        def sample(self, observation):
            return SimpleNamespace(action={"action": "stop"}, text='{"action":"stop"}', terminated=True)

    monkeypatch.setattr(curriculum_training, "LocalActor", ConstantActor)
    monkeypatch.setattr(curriculum_training, "seed_everything", lambda seed: None)
    report = curriculum_training.evaluate_curriculum("unused", "unused", tmp_path / "report.json", "constant-test")
    summary = report["summary"]
    assert summary["n_pairs"] == 24 and summary["n_examples"] == 48
    assert summary["both_correct_rate"] == 0
    assert summary["action_changed_rate"] == 0
    assert summary["example_accuracy"] == pytest.approx(6 / 48)
    assert summary["terminated_rate"] == 1
