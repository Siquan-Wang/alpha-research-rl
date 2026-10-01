import copy
import hashlib
import json

import pytest

from alpha_research_rl.financial_evaluation import (
    checkpoint_manifest,
    compare_reports,
    evaluate_task_runner,
    evaluation_contract,
    freeze_checkpoints,
)
from alpha_research_rl.financial_tasks import INVALID_REWARD
from alpha_research_rl.llm import ActionSample, parse_action


class FakeTask:
    def __init__(self):
        self.public_manifest = {"year": 2020, "half": 1, "task_id": "hidden-task"}

    def observation(self):
        return {"supported_features": ["returns"], "probe_evidence": [
            {"expression": "ts_mean(returns,5)", "feedback": {"mean_ic": 0.1}, "windows": [1, 2, 3]},
            {"expression": "ts_mean(returns,20)", "feedback": {"mean_ic": -0.2}, "windows": [4, 5, 6]},
        ]}

    def evaluate(self, expression):
        valid = expression in {"returns", "ts_mean(returns,5)", "ts_mean(returns,20)"}
        ic = 0.1 if expression == "ts_mean(returns,5)" else 0.2
        return {"expression": expression, "status": "ok" if valid else "invalid",
                "reason": None if valid else "invalid_expression", "reward": ic - 0.01 if valid else INVALID_REWARD,
                "oriented_future_ic": ic if valid else None,
                "assessment": {"mean_ic": ic, "coverage": 1} if valid else None}


class FakeActor:
    def __init__(self, fence=False, invalid_every_other=False):
        self.calls = []
        self.fence, self.invalid_every_other = fence, invalid_every_other

    def sample(self, observation, stochastic, max_tokens):
        self.calls.append((copy.deepcopy(observation), stochastic, max_tokens))
        expression = "ts_mean(returns,5)" if observation["probe_evidence"][0]["feedback"]["mean_ic"] > 0 else "ts_mean(returns,20)"
        action = {"action": "propose", "expression": expression}
        if self.invalid_every_other and len(self.calls) % 2 == 0:
            action = {"action": "stop"}
        text = json.dumps(action)
        if self.fence:
            text = "```json\n" + text + "\n```"
        return ActionSample([1, 2], [3, 4], text, parse_action(text), True)


def test_rng_matching_and_swapped_evidence_requires_new_generations():
    seeds = []
    actor = FakeActor()
    report = evaluate_task_runner(actor, [FakeTask()], draws=2, seed_fn=seeds.append, include_references=False)
    assert seeds == [80000, 80001, 80099, 80000, 80001, 80099]
    assert len(actor.calls) == 6
    assert actor.calls[0][0]["probe_evidence"][0]["feedback"]["mean_ic"] == 0.1
    assert actor.calls[3][0]["probe_evidence"][0]["feedback"]["mean_ic"] == -0.2
    assert actor.calls[3][0]["probe_evidence"][0]["windows"] == [4, 5, 6]
    assert actor.calls[3][0]["probe_evidence"][0]["expression"] == "ts_mean(returns,5)"
    records = report["episodes"][0]["records"]
    assert records[0]["strict"]["expression"] != records[3]["strict"]["expression"]
    for observation, _, max_tokens in actor.calls:
        assert "hidden-task" not in json.dumps(observation)
        assert "year" not in observation and "assessment" not in observation
        assert max_tokens == 64
    assert records[0]["prompt_ids"] == [1, 2] and records[0]["completion_ids"] == [3, 4]


def test_invalid_samples_stay_in_reward_denominator_and_ic_is_secondary():
    report = evaluate_task_runner(FakeActor(invalid_every_other=True), [FakeTask()], draws=2,
                                  seed_fn=lambda seed: None, include_references=False)
    metrics = report["summary"]["strict"]["true"]["stochastic"]
    assert metrics["n_samples"] == 2 and metrics["valid_samples"] == 1
    assert metrics["mean_reward"] == pytest.approx((0.09 + INVALID_REWARD) / 2)
    assert metrics["mean_oriented_ic_valid_only"] == 0.1
    assert metrics["valid_fraction"] == 0.5


def test_secondary_fence_reparse_has_no_new_generations_or_best_of_n():
    actor = FakeActor(fence=True)
    report = evaluate_task_runner(actor, [FakeTask()], draws=2, seed_fn=lambda seed: None, include_references=False)
    assert len(actor.calls) == 6
    primary = report["summary"]["strict"]["true"]["stochastic"]
    secondary = report["summary"]["fence_tolerant_secondary"]["true"]["stochastic"]
    assert primary["mean_reward"] == INVALID_REWARD and primary["valid_samples"] == 0
    assert secondary["mean_reward"] == pytest.approx(0.09) and secondary["valid_samples"] == 2
    assert report["episodes"][0]["records"][0]["secondary_accepted_format"] == "json_fence"


def test_checkpoint_identity_uses_files_and_contains_no_absolute_paths(tmp_path):
    adapter = tmp_path / "run" / "adapter"
    adapter.mkdir(parents=True)
    (adapter / "adapter_config.json").write_text('{}', encoding="utf-8")
    (adapter / "adapter_model.safetensors").write_bytes(b"original artificial weight fixture")
    before = checkpoint_manifest(adapter)
    frozen = freeze_checkpoints({"sft": adapter})
    assert frozen["checkpoints"]["sft"] == before
    assert str(tmp_path) not in json.dumps(frozen)
    (adapter / "adapter_model.safetensors").write_bytes(b"changed artificial weight fixture")
    assert checkpoint_manifest(adapter)["combined_sha256"] != before["combined_sha256"]


def test_mean_reward_is_paired_by_task_and_greedy_is_separate():
    task_a, task_b = FakeTask(), FakeTask()
    task_b.public_manifest = {"year": 2021, "half": 1, "task_id": "hidden-other"}
    actor = FakeActor()
    seeds = []
    report = evaluate_task_runner(actor, [task_a, task_b], draws=2, seed_fn=seeds.append, include_references=False)
    assert seeds[6:9] == [80100, 80101, 80199]
    assert report["summary"]["strict"]["true"]["stochastic"]["n_samples"] == 4
    assert report["summary"]["strict"]["true"]["greedy"]["n_samples"] == 2
    assert set(report["yearly"]) == {"2020", "2021"}


def test_paired_comparison_does_not_select_best_checkpoint_and_checks_rng():
    report = evaluate_task_runner(FakeActor(), [FakeTask()], draws=2,
                                  seed_fn=lambda seed: None, include_references=False)
    comparison = compare_reports({"sft": report, "rl23": copy.deepcopy(report), "rl29": copy.deepcopy(report)})
    assert set(comparison["comparisons"]) == {"rl23", "rl29"}
    for compared in comparison["comparisons"].values():
        assert compared["pooled"]["strict"]["stochastic"]["incremental_reward_vs_sft"] == 0
        assert compared["pooled"]["strict"]["stochastic"]["grounding_interaction_reward"] == 0
    altered = copy.deepcopy(report)
    altered["episodes"][0]["records"][0]["seed"] += 1
    with pytest.raises(ValueError, match="RNG"):
        compare_reports({"sft": report, "rl23": altered})


def test_invalid_canonical_asts_excluded_from_valid_frequency_counts():
    class UnsupportedActor(FakeActor):
        def sample(self, observation, stochastic, max_tokens):
            text = '{"action":"propose","expression":"close"}'
            return ActionSample([1], [2], text, parse_action(text), True)

    report = evaluate_task_runner(UnsupportedActor(), [FakeTask()], draws=2,
                                  seed_fn=lambda seed: None, include_references=False)
    frequencies = report["summary"]["strict"]["true"]["stochastic"]["frequencies"]
    assert frequencies["unique_canonical_asts"] == 1
    assert frequencies["valid_only"]["unique_canonical_asts"] == 0
    assert frequencies["valid_only"]["denominator_valid_proposals"] == 0


def test_evaluation_contract_hashes_prompt_tokenizer_and_scoring_files(tmp_path):
    (tmp_path / "tokenizer.json").write_text('{}', encoding="utf-8")
    contract = evaluation_contract(tmp_path)
    assert set(contract["source_files_sha256"]) == {
        "financial_evaluation.py", "financial_policy.py", "financial_tasks.py", "dsl.py",
        "evaluation.py", "llm.py", "format_ablation.py"}
    assert contract["tokenizer_files_sha256"]["tokenizer.json"] == hashlib.sha256(b'{}').hexdigest()
    digest = contract.pop("shared_contract_sha256")
    expected = hashlib.sha256(json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert digest == expected


def test_cpu_references_use_feedback_greedy_and_frozen_lag1_not_future_oracle():
    from alpha_research_rl.financial_evaluation import reference_outcomes
    from alpha_research_rl.financial_tasks import GRID

    class ReferenceTask(FakeTask):
        def feedback_grid(self, expressions):
            return [{"expression": expression, "usable": True,
                     "feedback": {"mean_ic": 0.9 if expression == "ts_mean(returns,20)" else 0.01}}
                    for expression in expressions]

        def evaluate(self, expression):
            ic = 0.8 if expression == "ts_mean(returns,5)" else 0.3 if expression == "delay(returns,1)" else 0.1
            return {"expression": expression, "status": "ok", "reason": None,
                    "reward": ic - 0.01, "oriented_future_ic": ic,
                    "assessment": {"mean_ic": ic, "coverage": 1}}

    references = reference_outcomes(ReferenceTask())
    assert references["feedback_greedy_grid"]["expression"] == "ts_mean(returns,20)"
    assert references["training_best_fixed"]["expression"] == "delay(returns,1)"
    assert references["uniform_grid"]["n_samples"] == len(GRID)
    assert references["uniform_grid"]["mean_reward"] == pytest.approx((14 * 0.1 + 0.8 + 0.3) / 16 - 0.01)


@pytest.mark.parametrize("draws", [0, 9, True, 1.5])
def test_invalid_draw_count_rejected(draws):
    with pytest.raises(ValueError):
        evaluate_task_runner(FakeActor(), [FakeTask()], draws=draws, seed_fn=lambda seed: None)
