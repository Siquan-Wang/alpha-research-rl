import json
from itertools import pairwise

import numpy as np
import pytest

from alpha_research_rl.data import MarketPanel, make_synthetic_panel
from alpha_research_rl.dsl import evaluate_expression
from alpha_research_rl.environment import ResearchEnvironment, combine_ranked_factors
from alpha_research_rl.evaluation import forward_returns, score_factor
from alpha_research_rl.protocol import ResearchSplit, make_chronological_split


@pytest.fixture
def panel():
    return make_synthetic_panel(seed=123, n_dates=180, n_assets=12)


@pytest.fixture
def split():
    return make_chronological_split(180, horizon=3)


def make_env(panel, split, budget=12, candidates=None):
    return ResearchEnvironment(panel, split, candidates or ["returns", "volume", "close", "neg(returns)"], budget)


def assert_json_safe(observation):
    json.dumps(observation, allow_nan=False)
    assert not ({"assessment", "panel", "labels", "daily_ic"} & observation.keys())


def test_reset_replays_deterministically_and_copies_observations(panel, split):
    env = make_env(panel, split)
    initial = env.reset()
    first = env.step({"action": "screen", "candidate": 0})
    first[0]["evidence"]["0"]["screen"]["mean_ic"] = 999
    assert env.reset() == initial
    repeated = env.step({"action": "screen", "candidate": 0})
    assert repeated[0]["evidence"]["0"]["screen"]["mean_ic"] != 999
    assert repeated[1] == 0
    assert_json_safe(repeated[0])


def test_future_assessment_perturbation_cannot_change_visible_evidence(panel, split):
    close, volume, returns = panel.close.copy(), panel.volume.copy(), panel.returns.copy()
    start = split.assessment[0]
    close[start:] *= np.exp(np.random.default_rng(77).normal(0, .3, close[start:].shape))
    volume[start:] *= 13
    returns[1:] = close[1:] / close[:-1] - 1
    changed = MarketPanel(close=close, volume=volume, returns=returns,
                          dates=panel.dates.copy(), assets=panel.assets, metadata={"secret": "hidden"})
    env_a, env_b = make_env(panel, split), make_env(changed, split)
    assert env_a.reset() == env_b.reset()
    actions = [{"action": "screen", "candidate": 0},
               {"action": "stability", "candidate": 0},
               {"action": "screen", "candidate": 1},
               {"action": "select", "candidate": 0},
               {"action": "screen", "candidate": 500},
               {"action": "screen", "candidate": 0}]
    for action in actions:
        assert env_a.step(action) == env_b.step(action)
    obs_a, reward_a, done_a, info_a = env_a.step({"action": "stop"})
    obs_b, reward_b, done_b, info_b = env_b.step({"action": "stop"})
    assert obs_a == obs_b and info_a == info_b and done_a and done_b
    assert reward_a != pytest.approx(reward_b)
    assert_json_safe(obs_a)
    assert set(info_a) == {"status", "reason"}


@pytest.mark.parametrize("action", [None, [], {}, {"action": []},
    {"action": "bogus", "candidate": 0}, {"action": "select", "candidate": 0},
    {"action": "screen", "candidate": True}, {"action": "screen", "candidate": []},
    {"action": "screen", "candidate": -1}, {"action": "screen", "candidate": 99},
    {"action": "stop", "unexpected": "secret"}])
def test_every_invalid_nonstop_attempt_consumes_budget(panel, split, action):
    env = make_env(panel, split, budget=1)
    obs, reward, done, info = env.step(action)
    assert obs["budget"] == 0 and done
    assert reward == pytest.approx(-.001)
    assert info["status"] == "invalid"
    assert_json_safe(obs)
    with pytest.raises(RuntimeError):
        env.step({"action": "stop"})


def test_duplicates_and_insufficient_stability_budget_are_charged(panel, split):
    env = make_env(panel, split, budget=3, candidates=["returns", " returns "])
    assert env.step({"action": "screen", "candidate": 0})[0]["budget"] == 2
    duplicate = env.step({"action": "screen", "candidate": 1})
    assert duplicate[0]["budget"] == 1 and duplicate[3]["status"] == "duplicate"
    obs, reward, done, info = env.step({"action": "stability", "candidate": 0})
    assert done and obs["budget"] == 0 and "stability" not in obs["evidence"]["0"]
    assert info["reason"] == "insufficient_budget"
    assert reward == pytest.approx(-.003)


def test_stability_cost_and_feedback_subwindows(panel, split):
    env = make_env(panel, split)
    obs, reward, done, _info = env.step({"action": "stability", "candidate": 0})
    assert obs["spent_budget"] == 2 and reward == 0 and not done
    windows = obs["evidence"]["0"]["stability"]["windows"]
    assert windows[0]["start"] == split.feedback[0]
    assert windows[-1]["stop"] == split.feedback[1]
    assert all(a["stop"] == b["start"] for a, b in pairwise(windows))
    assert all(w["stop"] <= split.assessment[0] - split.horizon for w in windows)
    assert_json_safe(obs)


def test_selection_requires_usable_screen_and_maximum_three(panel, split):
    env = make_env(panel, split, budget=20)
    assert env.step({"action": "select", "candidate": 0})[3]["reason"] == "screen_required"
    for candidate in range(4):
        env.step({"action": "screen", "candidate": candidate})
        result = env.step({"action": "select", "candidate": candidate})
    assert result[0]["selected"] == [0, 1, 2]
    assert result[3]["reason"] == "selection_limit"
    env = make_env(panel, split, candidates=["sub(close, close)"])
    screen = env.step({"action": "screen", "candidate": 0})
    assert screen[0]["evidence"]["0"]["screen"]["mean_ic"] is None
    assert env.step({"action": "select", "candidate": 0})[3]["reason"] == "usable_screen_required"


def test_invalid_expression_message_never_exposes_content(panel, split):
    env = make_env(panel, split, candidates=["__import__('secret_hidden_assessment')"])
    observation, reward, _done, info = env.step({"action": "screen", "candidate": 0})
    assert info == {"status": "invalid", "reason": "invalid_expression"}
    assert observation["history"][-1]["reason"] == "invalid_expression"
    assert reward == 0


def test_terminal_reward_uses_feedback_orientation_and_is_paid_once(panel, split):
    env = make_env(panel, split, candidates=["returns"])
    observation = env.step({"action": "screen", "candidate": 0})[0]
    orientation = observation["orientation"]["0"]
    feedback_ic = observation["evidence"]["0"]["screen"]["mean_ic"]
    assert orientation == (-1 if feedback_ic < 0 else 1)
    env.step({"action": "select", "candidate": 0})
    observation, reward, done, _info = env.step({"action": "stop"})
    factor = evaluate_expression("returns", panel)
    composite = combine_ranked_factors([factor], [orientation])
    expected = score_factor(composite, forward_returns(panel, split.horizon), *split.assessment)
    assert reward == pytest.approx(expected["mean_ic"] - .002)
    assert done and observation["orientation"]["0"] == orientation
    with pytest.raises(RuntimeError):
        env.step({"action": "stop"})


def test_automatic_budget_finish_and_empty_pool_cost(panel, split):
    env = make_env(panel, split, budget=1)
    _, reward, done, _ = env.step({"action": "screen", "candidate": 0})
    assert done and reward == pytest.approx(-.001)
    env = make_env(panel, split)
    assert env.step({"action": "stop"})[1:3] == (0, True)


def test_common_asset_universe_for_rank_combination():
    a = np.array([[1., 2., 3., 100.], [1., 1., 3., np.nan]])
    b = np.array([[3., 2., 1., np.nan], [1., 2., 2., 4.]])
    result = combine_ranked_factors([a, b], [1, 1])
    np.testing.assert_allclose(result[0, :3], [0, 0, 0])
    assert np.isnan(result[0, 3]) and np.isnan(result[1, 3])
    np.testing.assert_allclose(result[1, :3], [-.375, 0, .375])


def test_missing_asset_and_future_date_do_not_change_current_ranks():
    a = np.array([[1., 2., 3., np.nan], [10., 20., 30., 40.]])
    b = np.array([[3., 2., 1., 1000.], [40., 30., 20., 10.]])
    first = combine_ranked_factors([a, b], [1, -1])[0]
    b[0, 3] = -1000
    a[1] *= -13
    np.testing.assert_allclose(combine_ranked_factors([a, b], [1, -1])[0], first)


def test_sparse_assessment_cannot_gain_positive_reward(panel, split, monkeypatch):
    import alpha_research_rl.environment as module

    original = module.evaluate_expression

    def sparse(expression, evaluated_panel):
        values = original(expression, evaluated_panel)
        if len(evaluated_panel.dates) == len(panel.dates):
            values[split.assessment[0]:, :6] = np.nan
        return values

    monkeypatch.setattr(module, "evaluate_expression", sparse)
    env = make_env(panel, split, candidates=["returns"])
    env.step({"action": "screen", "candidate": 0})
    env.step({"action": "select", "candidate": 0})
    _, reward, done, info = env.step({"action": "stop"})
    assert done and reward == pytest.approx(-.002)
    assert set(info) == {"status", "reason"}


def generation_env(panel, split, budget=16, max_candidates=64):
    return ResearchEnvironment(panel, split, ["returns"], budget=budget,
                               allow_generation=True, max_candidates=max_candidates)


def test_proposal_is_new_factor_without_free_evidence_and_reset_removes_it(panel, split):
    env = generation_env(panel, split)
    initial = env.reset()
    obs, reward, done, info = env.step({"action": "propose", "expression": "ts_mean(returns, 5)"})
    assert info["status"] == "ok" and reward == 0 and not done
    assert obs["spent_budget"] == 2
    assert obs["candidates"][-1] == {"id": 1, "expression": "ts_mean(returns, 5)"}
    assert obs["provenance"]["1"] == {"kind": "propose", "parent": None}
    assert "1" not in obs["evidence"] and "1" not in obs["orientation"]
    assert env.step({"action": "select", "candidate": 1})[3]["reason"] == "screen_required"
    obs = env.step({"action": "screen", "candidate": 1})[0]
    values = evaluate_expression("ts_mean(returns, 5)", panel)
    expected = score_factor(values, forward_returns(panel, split.horizon), *split.feedback)
    assert obs["evidence"]["1"]["screen"]["mean_ic"] == pytest.approx(expected["mean_ic"])
    assert env.step({"action": "select", "candidate": 1})[0]["selected"] == [1]
    assert_json_safe(obs)
    assert env.reset() == initial


def test_mutation_tracks_parent_without_changing_original(panel, split):
    env = generation_env(panel, split)
    action = {"action": "mutate", "candidate": 0, "expression": "ts_mean(returns, 3)"}
    obs, reward, done, info = env.step(action)
    assert info["status"] == "ok" and reward == 0 and not done
    assert obs["candidates"][0]["expression"] == "returns"
    assert obs["provenance"]["1"] == {"kind": "mutate", "parent": 0}
    assert obs["history"][-1]["candidate"] == 1 and obs["history"][-1]["parent"] == 0
    obs = env.step({"action": "mutate", "candidate": 1, "expression": "delta(returns, 3)"})[0]
    assert obs["provenance"]["2"]["parent"] == 1


@pytest.mark.parametrize("action,reason", [
    ({"action": "propose", "expression": " (returns) "}, "duplicate_expression"),
    ({"action": "propose", "expression": "__import__('os').system('echo forbidden')"}, "invalid_expression"),
    ({"action": "propose", "expression": "delay(returns, -1)"}, "invalid_expression"),
    ({"action": "propose", "expression": "ts_mean(returns, 61)"}, "invalid_expression"),
    ({"action": "propose", "expression": "returns[0]"}, "invalid_expression"),
    ({"action": "propose", "expression": "returns", "assessment": True}, "invalid_action"),
    ({"action": "propose", "expression": "returns", "candidate": 0}, "invalid_action"),
    ({"action": "propose"}, "invalid_expression"),
    ({"action": "propose", "expression": []}, "invalid_expression"),
    ({"action": "propose", "expression": "x" * 2049}, "invalid_expression"),
    ({"action": "mutate", "candidate": [], "expression": "volume"}, "invalid_candidate"),
    ({"action": "mutate", "candidate": True, "expression": "volume"}, "invalid_candidate"),
    ({"action": "mutate", "candidate": 99, "expression": "volume"}, "invalid_candidate"),
])
def test_generation_invalid_and_duplicate_attempts_cost_two(panel, split, action, reason):
    env = generation_env(panel, split, budget=2)
    obs, reward, done, info = env.step(action)
    assert done and obs["budget"] == 0 and reward == pytest.approx(-.002)
    assert len(obs["candidates"]) == 1 and info["reason"] == reason
    assert_json_safe(obs)


def test_generation_bounds_and_insufficient_budget(panel, split):
    env = generation_env(panel, split, max_candidates=2)
    env.step({"action": "propose", "expression": "volume"})
    result = env.step({"action": "propose", "expression": "close"})
    assert result[3]["reason"] == "candidate_limit" and result[0]["spent_budget"] == 4
    assert len(result[0]["candidates"]) == 2
    env = generation_env(panel, split, budget=1)
    obs, reward, done, info = env.step({"action": "propose", "expression": "volume"})
    assert done and reward == pytest.approx(-.001) and len(obs["candidates"]) == 1
    assert info["reason"] == "insufficient_budget"


def test_generation_is_opt_in_and_existing_policy_compatible(panel, split):
    from alpha_research_rl.policies import ScreenThenSelect

    fixed = make_env(panel, split)
    assert "generation" not in fixed.reset() and "provenance" not in fixed.reset()
    obs, _, _, info = fixed.step({"action": "propose", "expression": "ts_mean(returns, 5)"})
    assert info["reason"] == "generation_disabled" and obs["spent_budget"] == 2
    env = generation_env(panel, split)
    env.step({"action": "propose", "expression": "ts_mean(returns, 5)"})
    policy = ScreenThenSelect()
    obs = env._observation()
    while not obs["done"]:
        obs, _, _, _ = env.step(policy.act(obs))
    assert all(i in (0, 1) for i in obs["selected"])


def test_generation_future_assessment_invariance_including_errors(panel, split):
    close = panel.close.copy()
    start = split.assessment[0]
    close[start:] *= np.exp(np.random.default_rng(171).normal(0, .5, close[start:].shape))
    returns = panel.returns.copy()
    returns[1:] = close[1:] / close[:-1] - 1
    changed = MarketPanel(close=close, volume=panel.volume.copy(), returns=returns,
                          dates=panel.dates.copy(), assets=panel.assets, metadata={})
    env_a, env_b = generation_env(panel, split), generation_env(changed, split)
    actions = [
        {"action": "propose", "expression": "ts_mean(returns, 3)"},
        {"action": "mutate", "candidate": 1, "expression": "mul(returns, volume)"},
        {"action": "screen", "candidate": 2},
        {"action": "select", "candidate": 2},
        {"action": "propose", "expression": "close.real"},
        {"action": "propose", "expression": "(returns)"},
    ]
    for action in actions:
        assert env_a.step(action) == env_b.step(action)
    obs_a, _, done_a, info_a = env_a.step({"action": "stop"})
    obs_b, _, done_b, info_b = env_b.step({"action": "stop"})
    assert obs_a == obs_b and done_a and done_b and info_a == info_b


@pytest.mark.parametrize("max_candidates", [0, -1, True, 65, 1.5])
def test_generation_candidate_limit_must_be_bounded(panel, split, max_candidates):
    with pytest.raises(ValueError):
        generation_env(panel, split, max_candidates=max_candidates)


def test_mostly_constant_dates_cannot_pass_screen_or_terminal_gate():
    returns = np.zeros((64, 4))
    returns[[13, 14, 23, 24]] = [.01, .02, .03, .04]
    close = 100 * np.cumprod(1 + returns, axis=0)
    returns[0] = np.nan
    panel = MarketPanel(close, np.ones_like(close), returns,
                        np.arange("2020-01-01", "2020-03-05", dtype="datetime64[D]"),
                        tuple("abcd"), {})
    split = ResearchSplit((0, 10), (12, 20), (22, 60), 1)
    env = ResearchEnvironment(panel, split, ["returns"])
    obs = env.step({"action": "screen", "candidate": 0})[0]
    screen = obs["evidence"]["0"]["screen"]
    assert screen["coverage"] == 1 and screen["n_dates"] == 1
    assert env.step({"action": "select", "candidate": 0})[3]["reason"] == "usable_screen_required"
    # Independently exercise terminal rejection even if a pool had been selected.
    env._selected = [0]
    _, reward, _, _ = env.step({"action": "stop"})
    assert reward == pytest.approx(-.002)


def test_terminal_constant_dates_rejected_after_usable_screen():
    returns = np.zeros((64, 4))
    returns[12:21] = [.01, .02, .03, .04]
    returns[[23, 24]] = [.01, .02, .03, .04]
    close = 100 * np.cumprod(1 + returns, axis=0)
    returns[0] = np.nan
    panel = MarketPanel(close, np.ones_like(close), returns,
                        np.arange("2020-01-01", "2020-03-05", dtype="datetime64[D]"),
                        tuple("abcd"), {})
    split = ResearchSplit((0, 10), (12, 20), (22, 60), 1)
    env = ResearchEnvironment(panel, split, ["returns"])
    env.step({"action": "screen", "candidate": 0})
    assert env.step({"action": "select", "candidate": 0})[3]["status"] == "ok"
    assert env.step({"action": "stop"})[1] == pytest.approx(-.002)


def test_supported_features_preserved_without_disclosing_metadata(panel, split):
    restricted = MarketPanel(panel.close.copy(), panel.volume.copy(), panel.returns.copy(),
                             panel.dates.copy(), panel.assets,
                             {"supported_features": ["close", "returns"], "hidden_assessment": 999})
    env = ResearchEnvironment(restricted, split, ["volume"], allow_generation=True)
    obs = env.reset()
    assert obs["supported_features"] == ["close", "returns"]
    assert "hidden_assessment" not in json.dumps(obs)
    assert env.step({"action": "screen", "candidate": 0})[3]["reason"] == "invalid_expression"
    obs, _, _, info = env.step({"action": "propose", "expression": "mul(volume, returns)"})
    assert info["reason"] == "invalid_expression" and len(obs["candidates"]) == 1
    assert env.step({"action": "propose", "expression": "ts_mean(returns, 5)"})[3]["status"] == "ok"
