"""Exact opportunity gate for a constructed four-candidate, two-query task.

The channel was designed using prior hand calculations. This is mathematical
validation of a closed catalog, not a held-out finding or a learned policy.
Only standard-library rational arithmetic enters the solver.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Mapping, Sequence
from fractions import Fraction
from itertools import combinations, product
from pathlib import Path

DEFAULT_CHANNELS = {
    "coarse": (Fraction(9, 10), Fraction(9, 10), Fraction(1, 10), Fraction(1, 10)),
    "left": (Fraction(9, 10), Fraction(1, 10), Fraction(1, 2), Fraction(1, 2)),
    "right": (Fraction(1, 2), Fraction(1, 2), Fraction(9, 10), Fraction(1, 10)),
}
DEFAULT_PRIOR = (Fraction(1, 4),) * 4
GAP_THRESHOLD = Fraction(1, 10)
DEFAULT_PLAN = Path(__file__).resolve().parents[2] / "docs" / "mechanism-gate-plan-v1.md"


def _probability(value: object) -> Fraction:
    """Accept exact rationals or decimal text; deliberately reject binary floats."""
    if isinstance(value, bool) or not isinstance(value, (Fraction, int, str)):
        raise ValueError("probabilities must be Fraction, integer, or rational/decimal text")  # noqa: TRY004
    try:
        probability = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError("invalid rational probability") from exc
    if not 0 <= probability <= 1:
        raise ValueError("probability outside [0, 1]")
    return probability


def validate_problem(
    channels: Mapping[str, Sequence[object]], prior: Sequence[object] = DEFAULT_PRIOR,
) -> tuple[dict[str, tuple[Fraction, ...]], tuple[Fraction, ...]]:
    """Validate exactly three binary tools and four hidden candidates."""
    if not isinstance(channels, Mapping) or len(channels) != 3:
        raise ValueError("exactly three tools are required")
    clean = {}
    for name, probabilities in channels.items():
        if not isinstance(name, str) or not name:
            raise ValueError("tool names must be nonempty strings")
        if not isinstance(probabilities, Sequence) or isinstance(probabilities, (str, bytes)):
            raise ValueError("each tool needs a four-element probability sequence")  # noqa: TRY004
        if len(probabilities) != 4:
            raise ValueError("each tool needs four hidden-candidate probabilities")
        clean[name] = tuple(_probability(p) for p in probabilities)
    if not isinstance(prior, Sequence) or isinstance(prior, (str, bytes)) or len(prior) != 4:
        raise ValueError("prior needs four probabilities")
    clean_prior = tuple(_probability(p) for p in prior)
    if sum(clean_prior) != 1:
        raise ValueError("prior probabilities must sum exactly to one")
    return clean, clean_prior


def evaluate_plan(
    channels: Mapping[str, Sequence[object]],
    plan: Sequence[str],
    prior: Sequence[object] = DEFAULT_PRIOR,
) -> dict:
    """Evaluate (first tool, second after 0, second after 1) using acquired bits only.

    Conditional independence permits marginalizing the unqueried tool entirely.
    Each terminal decision maximizes the joint mass of H and its two observed
    responses; dividing by path probability gives the displayed posterior.
    """
    channels, prior = validate_problem(channels, prior)
    if not isinstance(plan, Sequence) or isinstance(plan, (str, bytes)) or len(plan) != 3:
        raise ValueError("plan must contain first, second-after-0, second-after-1 tools")
    if any(not isinstance(tool, str) or tool not in channels for tool in plan):
        raise ValueError("plan contains an unknown tool")
    first, second_zero, second_one = plan
    if first in (second_zero, second_one):
        raise ValueError("each path must query two distinct tools")
    branches = []
    value = Fraction(0)
    for bit in (0, 1):
        first_mass = tuple(
            p * (q if bit else 1 - q) for p, q in zip(prior, channels[first])
        )
        branch_probability = sum(first_mass)
        second = (second_zero, second_one)[bit]
        leaves = []
        for next_bit in (0, 1):
            mass = tuple(
                p * (q if next_bit else 1 - q) for p, q in zip(first_mass, channels[second])
            )
            path_probability = sum(mass)
            # Lowest canonical index breaks ties, including unreachable paths.
            selected = max(range(4), key=mass.__getitem__)
            correct_mass = mass[selected]
            value += correct_mass
            leaves.append({
                "response": next_bit,
                "path_probability": path_probability,
                "conditional_response_probability": (
                    path_probability / branch_probability if branch_probability else None
                ),
                "posterior": tuple(p / path_probability for p in mass) if path_probability else None,
                "selected_candidate": selected,
                "correct_joint_mass": correct_mass,
            })
        branches.append({
            "response": bit,
            "probability": branch_probability,
            "posterior": tuple(p / branch_probability for p in first_mass) if branch_probability else None,
            "second_query": second,
            "leaves": leaves,
        })
    return {
        "plan": tuple(plan), "value": value,
        "response_dependent_second_query": second_zero != second_one,
        "tree": {"first_query": first, "branches": branches},
    }


def solve(
    channels: Mapping[str, Sequence[object]] | None = None,
    prior: Sequence[object] = DEFAULT_PRIOR,
) -> dict:
    """Enumerate all 12 adaptive schedules and all 3 fixed unordered pairs."""
    channels, prior = validate_problem(DEFAULT_CHANNELS if channels is None else channels, prior)
    names = tuple(channels)
    plans = []
    for first in names:
        remaining = tuple(name for name in names if name != first)
        for second_zero, second_one in product(remaining, repeat=2):
            plans.append(evaluate_plan(channels, (first, second_zero, second_one), prior))
    fixed_pairs = []
    for first, second in combinations(names, 2):
        fixed_pairs.append({"pair": (first, second), **evaluate_plan(channels, (first, second, second), prior)})
    best_adaptive = max(plan["value"] for plan in plans)
    best_fixed = max(pair["value"] for pair in fixed_pairs)
    optimal_plans = [plan["plan"] for plan in plans if plan["value"] == best_adaptive]
    adaptive_dependence = any(
        plan["value"] == best_adaptive and plan["response_dependent_second_query"] for plan in plans
    )
    gap = best_adaptive - best_fixed
    return {
        "kernel": channels, "prior": prior,
        "budget": {"queries": 2, "distinct": True, "terminal_selections": 1, "common_cost": 0},
        "plans": plans, "fixed_pairs": fixed_pairs, "optimal_plans": optimal_plans,
        "best_adaptive": best_adaptive, "best_fixed": best_fixed,
        "uniform_random_fixed_pair": sum(pair["value"] for pair in fixed_pairs) / len(fixed_pairs),
        "no_query": max(prior), "adaptive_minus_best_fixed": gap,
        "gate": {
            "threshold": GAP_THRESHOLD, "gap_requirement": gap >= GAP_THRESHOLD,
            "optimal_second_query_depends_on_response": adaptive_dependence,
            "passed": gap >= GAP_THRESHOLD and adaptive_dependence,
        },
    }


def _json_value(value: object) -> object:
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator, "decimal": float(value)}
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    return value


def build_report(plan_path: Path = DEFAULT_PLAN) -> dict:
    """Attach byte identities and the disclosed pre-implementation expectations."""
    return _json_value({
        "study": "exact-hierarchical-query-mechanism-gate-v1",
        "scope": "Constructed closed-catalog mathematical opportunity gate; no held-out discovery.",
        "no_llm_trained": True, "no_market_data": True,
        "prior_hand_calculation_disclosed": True,
        "anticipated_values": {
            "best_adaptive": Fraction(81, 100), "best_fixed": Fraction(63, 100),
            "remaining_fixed_pair": Fraction(45, 100), "uniform_random_fixed_pair": Fraction(57, 100),
            "no_query": Fraction(1, 4), "adaptive_minus_best_fixed": Fraction(18, 100),
        },
        "provenance": {
            "source_file": "src/alpha_research_rl/mechanism_gate.py",
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "plan_file": plan_path.name,
            "plan_sha256": hashlib.sha256(plan_path.read_bytes()).hexdigest(),
        },
        "calculation": solve(),
        "limitation": "A pass establishes constructed adaptive information only; no learned-policy claim or GPU authorization.",
    })


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    parser.add_argument("--output", type=Path, help="new JSON file; existing paths are never overwritten")
    args = parser.parse_args(argv)
    if args.output is not None and args.output.exists():
        parser.error("output already exists; evidence cannot be overwritten")
    payload = json.dumps(build_report(args.plan), indent=2, allow_nan=False) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        # Exclusive creation also prevents an overwrite if a path appears after validation.
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)


if __name__ == "__main__":
    main()
