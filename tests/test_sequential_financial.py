import json

import numpy as np
import pytest

from alpha_research_rl.data import MarketPanel, make_synthetic_panel
from alpha_research_rl.financial_tasks import INVALID_REWARD
from alpha_research_rl.sequential_financial import SequentialFinancialEnvironment, make_sequential_task


@pytest.fixture(scope="module")
def panel():
    return make_synthetic_panel(seed=82, n_dates=1200, n_assets=8)


def altered_panel(panel, boundary, flatten=False):
    close = panel.close.copy()
    if flatten:
        close[boundary:] = close[boundary - 1]
    else:
        close[boundary:] *= np.linspace(1.2, 2, len(close) - boundary)[:, None]
    returns = np.full_like(close, np.nan)
    returns[1:] = close[1:] / close[:-1] - 1
    return MarketPanel(close, panel.volume, returns, panel.dates, panel.assets)


def test_cheap_and_late_have_separate_label_purges(panel):
    manifest = make_sequential_task(panel, 2002, 1).public_manifest
    left, right = manifest["raw_feedback_bounds_half_open"]
    middle = left + 2 * (right - left) // 3
    assert manifest["cheap_bounds_half_open"] == [left, middle - 5]
    assert manifest["late_bounds_half_open"] == [middle, right - 5]
    for phase in ("cheap", "late", "assessment"):
        assert manifest[phase + "_bounds_half_open"][1] - 1 + 5 < manifest[phase + "_label_boundary"]


def test_late_perturbation_preserves_cheap_scores_and_orientation(panel):
    task = make_sequential_task(panel, 2002, 1)
    boundary = task.public_manifest["cheap_label_boundary"]
    changed = make_sequential_task(altered_panel(panel, boundary), 2002, 1)
    assert task.cheap_rows() == changed.cheap_rows()
    assert task.orientation(0) == changed.orientation(0)


def test_assessment_perturbation_preserves_all_controller_observations(panel):
    task = make_sequential_task(panel, 2002, 1)
    changed = make_sequential_task(altered_panel(panel, task.public_manifest["late_label_boundary"]), 2002, 1)
    env_a, env_b = SequentialFinancialEnvironment(task), SequentialFinancialEnvironment(changed)
    assert env_a.reset() == env_b.reset()
    for candidate in (0, 1):
        obs_a, reward_a, done_a, info_a = env_a.step({"action": "check", "candidate": candidate})
        obs_b, reward_b, done_b, info_b = env_b.step({"action": "check", "candidate": candidate})
        assert obs_a == obs_b and reward_a == reward_b == 0
        assert done_a == done_b is False and info_a == info_b


def test_exactly_two_checks_and_selection_of_unchecked_candidate(panel):
    task = make_sequential_task(panel, 2002, 1)
    env = SequentialFinancialEnvironment(task)
    observation = env.reset()
    assert observation["late_evidence"] == {}
    assert "year" not in observation and "task_id" not in observation
    assert "assessment" not in json.dumps(observation)
    for candidate in (0, 1):
        observation, reward, done, _ = env.step({"action": "check", "candidate": candidate})
        assert not done and reward == 0
        assert set(observation["late_evidence"]) == {str(index) for index in range(candidate + 1)}
    assert observation["phase"] == "select"
    final, reward, done, info = env.step({"action": "select", "candidate": 2})
    assert done and final["selected"] == 2 and info == {"status": "ok", "reason": None}
    assert reward == task.terminal_result(2)["reward"]
    assert len(final["history"]) == 3 and final["budget"] == 0
    assert "assessment" not in info
    with pytest.raises(RuntimeError):
        env.step({"action": "select", "candidate": 0})


@pytest.mark.parametrize("action", [{"action": "stop"}, {"action": "select", "candidate": 0},
    {"action": "check", "candidate": True}, {"action": "check", "candidate": 99},
    {"action": "check", "candidate": 0, "extra": 1}, {"action": ["check"], "candidate": 0}, None])
def test_invalid_actions_terminate_immediately_without_free_retries(panel, action):
    env = SequentialFinancialEnvironment(make_sequential_task(panel, 2002, 1))
    observation, reward, done, info = env.step(action)
    assert done and reward == INVALID_REWARD and info["status"] == "invalid"
    assert len(observation["history"]) == 1
    assert observation["fixed_total_cost"] == 0.01
    with pytest.raises(RuntimeError):
        env.step({"action": "check", "candidate": 1})


def test_duplicate_id_fails_but_duplicate_formula_slots_are_charged_and_logged(panel):
    task = make_sequential_task(panel, 2002, 1, ("returns", "returns", "ts_mean(returns,5)"))
    env = SequentialFinancialEnvironment(task)
    env.step({"action": "check", "candidate": 0})
    observation, reward, done, info = env.step({"action": "check", "candidate": 0})
    assert done and reward == INVALID_REWARD and info["status"] == "duplicate"
    env.reset()
    env.step({"action": "check", "candidate": 0})
    observation, reward, done, info = env.step({"action": "check", "candidate": 1})
    assert not done and reward == 0 and info["status"] == "ok"
    assert observation["history"][-1]["redundant_formula_evidence"] is True


def test_late_failure_does_not_change_orientation_or_fail_usable_future_selection(panel):
    task = make_sequential_task(panel, 2002, 1)
    start, stop = task.public_manifest["late_bounds_half_open"]
    close = panel.close.copy()
    close[start:stop] = close[start - 1]
    returns = np.full_like(close, np.nan)
    returns[1:] = close[1:] / close[:-1] - 1
    changed = make_sequential_task(MarketPanel(close, panel.volume, returns, panel.dates, panel.assets), 2002, 1)
    assert changed.cheap_rows() == task.cheap_rows()
    assert changed.late_score(0)["usable"] is False
    assert changed.terminal_result(0)["status"] == "ok"
    assert changed.orientation(0) == task.orientation(0)
    env = SequentialFinancialEnvironment(changed)
    env.step({"action": "check", "candidate": 0})
    env.step({"action": "check", "candidate": 1})
    _, reward, done, _ = env.step({"action": "select", "candidate": 0})
    assert done and reward == changed.terminal_result(0)["reward"]


def test_return_only_constant_and_explicit_invalid_bank_slots_fail_cheap_selection(panel):
    task = make_sequential_task(panel, 2002, 1, ("returns", "volume", "close", "1", None))
    assert all(task.cheap_score(i)["usable"] is False for i in range(1, 5))
    for index in range(1, 5):
        env = SequentialFinancialEnvironment(task)
        env.step({"action": "check", "candidate": 0})
        env.step({"action": "check", "candidate": 1})
        _, reward, done, info = env.step({"action": "select", "candidate": index})
        assert done and reward == INVALID_REWARD and info["reason"] == "unusable_cheap_selection"


def test_diagnostic_rows_are_training_only_and_never_in_observation(panel):
    task = make_sequential_task(panel, 2002, 1)
    rows = task.diagnostic_rows()
    assert len(rows) == 16 and rows[0]["candidate_id"] == 0
    assert "target_reward" in rows[0] and "assessment" in rows[0]
    assert "target_reward" not in json.dumps(SequentialFinancialEnvironment(task).reset())
    shifted = MarketPanel(panel.close, panel.volume, panel.returns,
                          panel.dates + np.timedelta64(16 * 365, "D"), panel.assets)
    with pytest.raises(ValueError, match="training tasks"):
        make_sequential_task(shifted, 2018, 1).diagnostic_rows()


def test_observation_copy_cannot_change_task_or_acquired_evidence(panel):
    env = SequentialFinancialEnvironment(make_sequential_task(panel, 2002, 1))
    observation, _, _, _ = env.step({"action": "check", "candidate": 0})
    observation["late_evidence"]["0"]["mean_ic"] = 99
    observation["candidates"][0]["cheap"]["mean_ic"] = 99
    fresh = env.observation()
    assert fresh["late_evidence"]["0"]["mean_ic"] != 99
    assert fresh["candidates"][0]["cheap"]["mean_ic"] != 99


def test_sign_aliases_share_cheap_fixed_oriented_rewards(panel):
    task = make_sequential_task(panel, 2002, 1, ("returns", "mul(returns,-1)"))
    assert task.cheap_score(0)["mean_ic"] != 0
    assert task.orientation(0) == -task.orientation(1)
    assert task.late_score(0)["oriented_mean_ic"] == pytest.approx(task.late_score(1)["oriented_mean_ic"])
    assert task.terminal_result(0)["reward"] == pytest.approx(task.terminal_result(1)["reward"])


def test_diagnostic_rows_match_gate_feature_and_target_contract(panel):
    from alpha_research_rl.sequential_gate import candidate_features, target_reward

    rows = make_sequential_task(panel, 2002, 1).diagnostic_rows()
    for row in rows:
        assert candidate_features(row).shape == (28,)
        assert candidate_features(row, include_late=True).shape == (38,)
        assert target_reward(row) == pytest.approx(row["target_reward"])
        for phase in ("cheap", "late", "assessment"):
            assert type(row[phase]["usable"]) is bool
            assert type(row[phase]["n_dates"]) is int
            assert type(row[phase]["n_signal_dates"]) is int


def test_panel_hard_cap_rejects_2025_rows_before_scoring(panel):
    shifted = MarketPanel(panel.close, panel.volume, panel.returns,
                          panel.dates + np.timedelta64(25 * 365, "D"), panel.assets)
    with pytest.raises(ValueError, match="capped"):
        make_sequential_task(shifted, 2024, 1)
