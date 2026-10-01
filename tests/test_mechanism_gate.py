"""Independent 32-outcome checks of the exact two-query Bayes solver."""

import json
from collections import defaultdict
from fractions import Fraction
from itertools import permutations, product

import pytest

from alpha_research_rl.mechanism_gate import (
    DEFAULT_CHANNELS,
    DEFAULT_PRIOR,
    build_report,
    evaluate_plan,
    main,
    solve,
    validate_problem,
)


def joint_reference(channels, plan, prior=DEFAULT_PRIOR):
    """Pre-draw all three bits, then expose only the two requested by this policy."""
    names = tuple(channels)
    observed_hidden_mass = defaultdict(lambda: [Fraction(0) for _ in range(4)])
    total = Fraction(0)
    for hidden, bits in product(range(4), product((0, 1), repeat=3)):
        probability = prior[hidden]
        for name, bit in zip(names, bits):
            p_one = channels[name][hidden]
            probability *= p_one if bit else 1 - p_one
        total += probability
        outcomes = dict(zip(names, bits))
        first_bit = outcomes[plan[0]]
        second_tool = plan[1 + first_bit]
        history = (first_bit, second_tool, outcomes[second_tool])
        observed_hidden_mass[history][hidden] += probability
    decisions = {
        history: max(range(4), key=mass.__getitem__) for history, mass in observed_hidden_mass.items()
    }
    # Execute those history-only decisions on full latent outcomes in a second pass.
    reward = Fraction(0)
    for hidden, bits in product(range(4), product((0, 1), repeat=3)):
        probability = prior[hidden]
        for name, bit in zip(names, bits):
            p_one = channels[name][hidden]
            probability *= p_one if bit else 1 - p_one
        outcomes = dict(zip(names, bits))
        first_bit = outcomes[plan[0]]
        second_tool = plan[1 + first_bit]
        if decisions[(first_bit, second_tool, outcomes[second_tool])] == hidden:
            reward += probability
    return reward, total, observed_hidden_mass, decisions


def test_every_plan_matches_independent_all_three_bit_enumeration():
    result = solve()
    assert len(result["plans"]) == 12
    assert len({tuple(row["plan"]) for row in result["plans"]}) == 12
    for row in result["plans"]:
        expected, total, masses, decisions = joint_reference(DEFAULT_CHANNELS, row["plan"])
        assert total == 1
        assert row["value"] == expected
        assert sum(leaf["path_probability"] for branch in row["tree"]["branches"] for leaf in branch["leaves"]) == 1
        for branch in row["tree"]["branches"]:
            for leaf in branch["leaves"]:
                history = (branch["response"], branch["second_query"], leaf["response"])
                mass = masses[history]
                assert leaf["posterior"] == tuple(p / sum(mass) for p in mass)
                assert leaf["selected_candidate"] == decisions[history]


def test_disclosed_hand_predictions_and_strongest_both_response_fixed_selector():
    result = solve()
    assert result["best_adaptive"] == Fraction(81, 100)
    assert sorted(pair["value"] for pair in result["fixed_pairs"]) == [Fraction(45, 100), Fraction(63, 100), Fraction(63, 100)]
    assert result["uniform_random_fixed_pair"] == Fraction(57, 100)
    assert result["no_query"] == Fraction(1, 4)
    assert result["adaptive_minus_best_fixed"] == Fraction(18, 100)
    assert result["optimal_plans"] == [("coarse", "right", "left")]
    assert result["gate"]["passed"]
    # All pair scores independently use both observed bits rather than a weaker selector.
    for pair in result["fixed_pairs"]:
        assert pair["value"] == joint_reference(DEFAULT_CHANNELS, pair["plan"])[0]
        reversed_plan = (pair["pair"][1], pair["pair"][0], pair["pair"][0])
        assert pair["value"] == joint_reference(DEFAULT_CHANNELS, reversed_plan)[0]


def test_no_information_has_no_advantage_even_with_adaptive_schedules():
    channels = {name: (Fraction(1, 2),) * 4 for name in DEFAULT_CHANNELS}
    result = solve(channels)
    assert {row["value"] for row in result["plans"]} == {Fraction(1, 4)}
    assert result["best_fixed"] == result["uniform_random_fixed_pair"] == result["no_query"]
    assert result["adaptive_minus_best_fixed"] == 0
    assert not result["gate"]["passed"]


def test_unqueried_response_cannot_change_terminal_choice_or_posterior():
    for row in solve()["plans"]:
        first, second_zero, second_one = row["plan"]
        groups = defaultdict(list)
        for bits in product((0, 1), repeat=3):
            outcomes = dict(zip(DEFAULT_CHANNELS, bits))
            first_bit = outcomes[first]
            second = (second_zero, second_one)[first_bit]
            second_bit = outcomes[second]
            leaf = row["tree"]["branches"][first_bit]["leaves"][second_bit]
            groups[(first_bit, second, second_bit)].append((leaf["selected_candidate"], leaf["posterior"]))
        assert len(groups) == 4
        # Each observation history has two worlds differing ONLY in the unqueried bit.
        assert all(len(worlds) == 2 and worlds[0] == worlds[1] for worlds in groups.values())
    fixed = ("coarse", "left", "left")
    original = evaluate_plan(DEFAULT_CHANNELS, fixed)
    # Even changing the entire unqueried channel cannot affect this plan's selector.
    for probability in (Fraction(0), Fraction(1)):
        changed = {**DEFAULT_CHANNELS, "right": (probability,) * 4}
        assert evaluate_plan(changed, fixed) == original


def _signature(channels, prior=DEFAULT_PRIOR):
    result = solve(channels, prior)
    return (
        result["best_adaptive"], result["best_fixed"], result["uniform_random_fixed_pair"],
        result["no_query"], sorted(row["value"] for row in result["plans"]), result["gate"],
    )


def test_candidate_query_and_bit_relabelings_preserve_exact_values():
    expected = _signature(DEFAULT_CHANNELS)
    for columns in permutations(range(4)):
        channels = {name: tuple(row[i] for i in columns) for name, row in DEFAULT_CHANNELS.items()}
        assert _signature(channels) == expected
    for order in permutations(DEFAULT_CHANNELS):
        renamed = {f"tool_{i}": DEFAULT_CHANNELS[name] for i, name in enumerate(order)}
        assert _signature(renamed) == expected
    for flips in product((False, True), repeat=3):
        channels = {
            name: tuple(1 - p if flip else p for p in row)
            for (name, row), flip in zip(DEFAULT_CHANNELS.items(), flips)
        }
        assert _signature(channels) == expected


def test_nonuniform_prior_and_unreachable_paths_remain_exact():
    prior = (Fraction(1), Fraction(0), Fraction(0), Fraction(0))
    deterministic = {name: (Fraction(0),) * 4 for name in DEFAULT_CHANNELS}
    result = solve(deterministic, prior)
    assert result["best_adaptive"] == result["best_fixed"] == result["no_query"] == 1
    for row in result["plans"]:
        assert row["value"] == joint_reference(deterministic, row["plan"], prior)[0]
        unreachable = row["tree"]["branches"][1]
        assert unreachable["probability"] == 0
        assert unreachable["posterior"] is None
        assert all(leaf["posterior"] is None for leaf in unreachable["leaves"])


@pytest.mark.parametrize("bad", [True, 0.9, "nan", "1/0", "-1/10", "11/10", None])
def test_invalid_probability_rejected(bad):
    channels = dict(DEFAULT_CHANNELS)
    channels["coarse"] = (bad,) + channels["coarse"][1:]
    with pytest.raises(ValueError):
        solve(channels)


@pytest.mark.parametrize("channels,prior", [
    ({"a": ("1/2",) * 4}, DEFAULT_PRIOR),
    ({"a": ("1/2",) * 3, "b": ("1/2",) * 4, "c": ("1/2",) * 4}, DEFAULT_PRIOR),
    ({"a": "1234", "b": ("1/2",) * 4, "c": ("1/2",) * 4}, DEFAULT_PRIOR),
    (DEFAULT_CHANNELS, ("1/2",) * 4),
    (DEFAULT_CHANNELS, ("1/4",) * 3),
])
def test_invalid_shapes_and_prior_rejected(channels, prior):
    with pytest.raises(ValueError):
        validate_problem(channels, prior)


@pytest.mark.parametrize("plan", [
    ("coarse", "coarse", "left"), ("coarse", "left", "coarse"),
    ("coarse", "left", "unknown"), ("coarse", "left"), "coarse", ([], "left", "right"),
])
def test_repeated_or_invalid_query_schedule_rejected(plan):
    with pytest.raises(ValueError):
        evaluate_plan(DEFAULT_CHANNELS, plan)


def test_report_exact_rationals_disclosure_and_byte_hashes(tmp_path):
    from hashlib import sha256
    from pathlib import Path

    import alpha_research_rl.mechanism_gate as module

    plan_path = tmp_path / "plan.md"
    plan_path.write_bytes(b"declared exact kernel\n")
    report = build_report(plan_path)
    assert report["calculation"]["best_adaptive"] == {"numerator": 81, "denominator": 100, "decimal": 0.81}
    assert report["no_llm_trained"] and report["no_market_data"] and report["prior_hand_calculation_disclosed"]
    assert report["provenance"]["source_sha256"] == sha256(Path(module.__file__).read_bytes()).hexdigest()
    assert report["provenance"]["plan_sha256"] == sha256(plan_path.read_bytes()).hexdigest()
    assert json.loads(json.dumps(report, allow_nan=False)) == report


def test_cli_refuses_to_overwrite_existing_evidence_before_solving(tmp_path, monkeypatch):
    import alpha_research_rl.mechanism_gate as module

    output = tmp_path / "retained.json"
    output.write_bytes(b"retained evidence")
    monkeypatch.setattr(module, "build_report", lambda *_: pytest.fail("must reject before computation"))
    with pytest.raises(SystemExit) as exc:
        main(["--output", str(output)])
    assert exc.value.code == 2
    assert output.read_bytes() == b"retained evidence"
