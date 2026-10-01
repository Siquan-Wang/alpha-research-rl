"""Independent artificial arithmetic and corruption checks; no published-bank run."""

from __future__ import annotations

import math
from copy import deepcopy
from fractions import Fraction

import pytest

from alpha_research_rl import reward_credit as credit


def exact_loo(values):
    """Direct other-three formula, independent of the implementation's centering."""
    return [value - sum(values[:i] + values[i + 1:]) / 3 for i, value in enumerate(values)]


def artificial_group(ics=(None, -.3, .1, .2), permutation=None):
    task = {"task_id": "artificial-training-only"}
    samples = []
    for i, ic in enumerate(ics):
        expression = f"delay(returns,{i + 1})"
        metric = {"mean_ic": .25, "coverage": 1.0, "ic_std": .1,
                  "n_dates": 100, "n_signal_dates": 100}
        ok = ic is not None
        outcome = {"expression": expression if ok else None,
                   "reward": float(ic) - .01 if ok else -1.01,
                   "cost": .01, "status": "ok" if ok else "invalid",
                   "reason": None if ok else "invalid_json_action",
                   "anchor_reuse": False, "orientation": 1 if ok else None,
                   "feedback": metric if ok else None,
                   "assessment": {**metric, "mean_ic": float(ic)} if ok else None,
                   "oriented_future_ic": float(ic) if ok else None, "zero_feedback_tie": False}
        samples.append({"text": '{"action":"propose","expression":"' + expression + '"}' if ok else "bad",
                        "action": {"action": "propose", "expression": expression} if ok else None,
                        "terminated": True, "completion_ids": [10 + i, 99], "prompt_ids": [1, 2],
                        "outcome": outcome, "recomputed_preupdate_completion_logp": -float(2**i)})
    rewards = [sample["outcome"]["reward"] for sample in samples]
    p = [0, 1, 2, 3] if permutation is None else list(permutation)
    assigned = [rewards[i] for i in p]
    advantages = [float(v) for v in exact_loo([Fraction(str(v)) for v in assigned])]
    updated = any(v != 0 for v in advantages)
    usable = [float(ic) for ic in ics if ic is not None]
    group = {"group": 0, "task": task, "samples": samples, "advantages": advantages,
             "optimizer_step": updated, "preclip_grad_norm": .75 if updated else 0.0,
             "adapter_before": "1" * 64, "adapter_after": ("2" if updated else "1") * 64,
             "legal_unique_asts": len(usable),
             "usable_future_ic_range": max(usable) - min(usable) if usable else 0.0,
             "quality_exploration": len(usable) > 1 and max(usable) - min(usable) > 1e-4}
    if permutation is None:
        group["rewards"] = rewards
    else:
        group.update(observation={}, true_rewards=rewards, permutation=p, assigned_rewards=assigned)
    return group, task


def inspect(group, task):
    return credit._group(group, 0, task, "permutation" in group)


def test_permuted_mixed_group_matches_fraction_oracle_and_preserves_logp_order():
    group, task = artificial_group(permutation=(2, 0, 3, 1))
    row = inspect(group, task)
    v = [Fraction(1, 3), Fraction(-1), Fraction(1, 3), Fraction(1, 3)]
    c = [Fraction(2, 15), Fraction(0), Fraction(4, 15), Fraction(-2, 5)]
    a = [Fraction(7, 15), Fraction(-1), Fraction(3, 5), Fraction(-1, 15)]
    for channel, expected in (("V", v), ("C", c), ("R", a)):
        assert row["advantages"][channel] == pytest.approx([float(x) for x in expected], abs=1e-14)
        assert row["coefficient_l1"][channel] == pytest.approx(float(sum(abs(x) for x in expected)))
    assert [r["preupdate_logp"] for r in row["samples"]] == [-1., -2., -4., -8.]
    assert row["assigned_components"]["V"] == [1, 0, 1, 1]
    assert row["surrogate"]["V"] == pytest.approx(float(Fraction(7, 12)))
    assert row["surrogate"]["C"] == pytest.approx(-.5)
    assert row["surrogate"]["R"] == pytest.approx(float(Fraction(1, 12)))
    # Permuting likelihoods too is a different, incorrect objective.
    wrong = -sum(float(x) * y for x, y in zip(a, [-4., -1., -8., -2.])) / 4
    assert abs(row["surrogate"]["R"] - wrong) > 1


def test_constant_reward_can_hide_nonzero_opposing_component_coefficients():
    group, task = artificial_group(ics=(None, -1., -1., -1.))
    row = inspect(group, task)
    assert row["constant_assigned_reward"] is True
    assert row["optimizer_step"] is False
    assert row["active_validity_credit"] is True
    assert row["advantages"]["R"] == [0.] * 4
    assert row["advantages"]["V"] == pytest.approx([-1., 1 / 3, 1 / 3, 1 / 3])
    assert row["advantages"]["C"] == pytest.approx([1., -1 / 3, -1 / 3, -1 / 3])
    assert row["coefficient_squared"]["cross_2VC"] == pytest.approx(-8 / 3)
    assert row["coefficient_squared"]["R"] == 0
    assert row["surrogate"]["R"] == 0
    assert row["surrogate"]["V"] == pytest.approx(-row["surrogate"]["C"])


@pytest.mark.parametrize("ics", [(None,) * 4, (-.1,) * 4])
def test_constant_groups_retained_with_zero_loss_and_no_validity_contrast(ics):
    group, task = artificial_group(ics=ics)
    row = inspect(group, task)
    assert len(row["samples"]) == 4
    assert row["active_validity_credit"] is False
    assert row["optimizer_step"] is False
    for channel in ("R", "V", "C"):
        assert row["advantages"][channel] == [0.] * 4
        assert row["surrogate"][channel] == 0


@pytest.mark.parametrize("field,value", [
    ("cost", math.nextafter(.01, math.inf)), ("cost", True),
    ("oriented_future_ic", float("nan")), ("oriented_future_ic", 1.01),
    ("orientation", True), ("orientation", -1), ("status", "success"),
    ("reason", "invalid_expression"),
])
def test_success_metadata_corruption_is_rejected(field, value):
    group, task = artificial_group()
    group["samples"][1]["outcome"][field] = value
    with pytest.raises(credit.RewardCreditError):
        inspect(group, task)


@pytest.mark.parametrize("value", [True, float("inf"), float("nan"), .00001])
def test_likelihood_is_finite_nonpositive_number_not_boolean(value):
    group, task = artificial_group()
    group["samples"][2]["recomputed_preupdate_completion_logp"] = value
    with pytest.raises(credit.RewardCreditError):
        inspect(group, task)


@pytest.mark.parametrize("permutation", [[True, 0, 2, 3], [0, 0, 2, 3], [0, 1, 2, 4], [0, 1, 2]])
def test_malformed_permutation_cannot_reduce_or_relabel_population(permutation):
    group, task = artificial_group(permutation=(2, 0, 3, 1))
    group["permutation"] = permutation
    with pytest.raises(credit.RewardCreditError):
        inspect(group, task)


def test_inverse_permutation_is_not_accepted_as_saved_assignment():
    group, task = artificial_group(permutation=(2, 0, 3, 1))
    group["permutation"] = [1, 3, 0, 2]
    with pytest.raises(credit.RewardCreditError):
        inspect(group, task)


def test_failed_sample_cannot_keep_oriented_ic_even_with_penalty_reward():
    group, task = artificial_group()
    group["samples"][0]["outcome"]["oriented_future_ic"] = 0.
    with pytest.raises(credit.RewardCreditError):
        inspect(group, task)


def test_group_order_and_token_identity_types_are_exact():
    original, task = artificial_group()
    for mutation in ("bool_group", "reordered_group", "bool_token", "different_task"):
        group = deepcopy(original)
        if mutation == "bool_group":
            group["group"] = False
        elif mutation == "reordered_group":
            group["group"] = 1
        elif mutation == "bool_token":
            group["samples"][0]["completion_ids"] = [True]
        else:
            group["task"] = {"task_id": "different"}
        with pytest.raises(credit.RewardCreditError):
            inspect(group, task)


def test_all_valid_varying_ic_has_no_direct_validity_coefficient():
    group, task = artificial_group(ics=(-.3, -.1, .1, .3))
    row = inspect(group, task)
    assert row["advantages"]["V"] == [0.] * 4
    assert row["advantages"]["R"] == pytest.approx(row["advantages"]["C"])
    assert row["optimizer_step"] is True


def test_sub_tolerance_ic_variation_does_not_relabel_an_actual_update_as_skip():
    group, task = artificial_group(ics=(0., 0., 0., 1e-13))
    row = inspect(group, task)
    assert 0 < max(abs(a) for a in row["recorded_advantages"]) < 1e-12
    assert row["optimizer_step"] is True
    assert row["zero_advantage_channels"]["C"] is False


def test_recorded_update_requires_changed_parameter_digest():
    group, task = artificial_group()
    group["adapter_after"] = group["adapter_before"]
    with pytest.raises(credit.RewardCreditError):
        inspect(group, task)


def test_skipped_group_requires_exact_zero_norm_even_below_tolerance():
    group, task = artificial_group(ics=(None,) * 4)
    group["preclip_grad_norm"] = math.nextafter(0., math.inf)
    with pytest.raises(credit.RewardCreditError):
        inspect(group, task)


def test_constant_reward_cannot_forge_tiny_balanced_logged_advantages_to_claim_update():
    group, task = artificial_group(ics=(-.1,) * 4)
    group.update(advantages=[1e-14, -1e-14, 0., 0.], optimizer_step=True,
                 adapter_after="2" * 64, preclip_grad_norm=.75)
    with pytest.raises(credit.RewardCreditError):
        inspect(group, task)


@pytest.mark.parametrize("field", ["true_rewards", "assigned_rewards"])
def test_retained_reward_copies_are_exact_even_one_ulp_apart(field):
    group, task = artificial_group(permutation=(2, 0, 3, 1))
    group[field][0] = math.nextafter(group[field][0], math.inf)
    with pytest.raises(credit.RewardCreditError):
        inspect(group, task)
