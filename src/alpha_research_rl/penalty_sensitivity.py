"""Post-hoc invalid-penalty sensitivity of saved financial proposal outcomes.

The registered primary penalty remains one. This diagnostic neither chooses a
penalty nor generates new actions. Zero predictive contribution for a failure is
an accounting convention, never a measured zero IC.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from .artifacts import write_json

PENALTIES = (0.0, .01, .05, .1, .25, .5, 1.0)


def sensitivity(report: dict) -> dict:
    if report.get("study") != "financial-proposal-v1-paired-analysis" or not report["integrity"]["validated"]:
        raise ValueError("requires a validated paired financial proposal analysis")
    primary = report["overall"]["metrics"]["strict"]["stochastic"]
    cells = {label: row["true"] for label, row in primary["policies"].items()}
    cells.update(report["overall"]["references"])
    lines = {}
    for label, row in cells.items():
        valid = row["valid_fraction"]
        contribution = row["all_proposal_ic_contribution"]
        if not all(math.isfinite(v) for v in (valid, contribution)) or not 0 <= valid <= 1:
            raise ValueError("invalid saved metrics")
        intercept = contribution - .01
        slope = -(1 - valid)
        if not math.isclose(intercept + slope, row["mean_reward"], abs_tol=1e-10):
            raise ValueError("penalty one must reproduce the registered primary reward")
        lines[label] = {"intercept": intercept, "slope": slope,
                        "valid_fraction": valid, "n_samples": row["n_samples"],
                        "valid_samples": row["valid_samples"],
                        "mean_reward_by_penalty": {str(p): intercept + p * slope for p in PENALTIES}}
    sft = report["roles"]["sft"]
    comparisons = {}
    for role in ("rl_seed23", "rl_seed29"):
        label = report["roles"][role]
        delta_intercept = lines[label]["intercept"] - lines[sft]["intercept"]
        delta_slope = lines[label]["slope"] - lines[sft]["slope"]
        uniform = lines["uniform_grid"]
        denominator = lines[label]["slope"] - uniform["slope"]
        crossing = ((uniform["intercept"] - lines[label]["intercept"]) / denominator
                    if denominator != 0 else None)
        comparisons[label] = {
            "rl_minus_sft_by_penalty": {str(p): delta_intercept + p * delta_slope for p in PENALTIES},
            "registered_penalty_one_gain": delta_intercept + delta_slope,
            "zero_penalty_gain": delta_intercept,
            "validity_component_at_registered_penalty": delta_slope,
            "uniform_grid_crossing_penalty": crossing if crossing is not None and 0 <= crossing <= 1 else None,
        }
    return {"study": "financial-proposal-post-hoc-penalty-sensitivity-v1",
            "status": "exploratory analysis designed after inspecting transfer results",
            "registered_primary_penalty": 1.0, "cost": .01,
            "formula": "mean_reward(lambda)=valid_IC_sum/N - .01 - lambda*(1-valid_fraction)",
            "scope": "strict JSON, stochastic policy, true evidence; fixed saved proposals",
            "penalties": list(PENALTIES), "policy_lines": lines, "rl_vs_sft": comparisons,
            "limitations": ["No penalty selection or replacement of the registered primary result",
                            "Failed proposals have no measured IC; zero contribution is a surrogate",
                            "Changing a penalty changes the objective, not the model or its actions",
                            "All-proposal IC contribution can change with the successful subset",
                            "No new samples, market periods, uncertainty or significance claims"]}


def plot_sensitivity(report: dict, destination: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    points = (0, 1)
    rl_labels = tuple(report["rl_vs_sft"])
    colors = {rl_labels[0]: "tab:blue", rl_labels[1]: "tab:orange",
              "uniform_grid": "black", "training_best_fixed": "tab:purple"}
    for label, line in report["policy_lines"].items():
        if label == "feedback_greedy_grid":
            continue  # Extra-information reference remains in the JSON.
        axes[0].plot(points, [line["intercept"] + p * line["slope"] for p in points],
                     label=label, color=colors.get(label, ".5"))
    for label, row in report["rl_vs_sft"].items():
        axes[1].plot(points, [row["zero_penalty_gain"], row["registered_penalty_one_gain"]],
                     label=label, color=colors[label])
    for axis in axes:
        axis.axvline(1, color=".45", linestyle=":", linewidth=1)
        axis.axhline(0, color=".65", linewidth=.7)
        axis.set_xlabel("Invalid penalty lambda (primary = 1)")
        axis.grid(alpha=.15)
        axis.legend(fontsize=7, frameon=False)
    axes[0].set(title="Reward sensitivity: higher is better", ylabel="Mean surrogate reward")
    axes[1].set(title="RL minus SFT on the same proposals", ylabel="Mean reward difference")
    fig.suptitle("Exploratory post-hoc sensitivity; primary result unchanged\n"
                 "Failures have no measured IC; lambda = 0 is an accounting convention", fontsize=10)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destination, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plot", type=Path)
    args = parser.parse_args()
    report = sensitivity(json.loads(args.analysis.read_text(encoding="utf-8")))
    report["source_analysis"] = {"file": args.analysis.name,
                                 "sha256": hashlib.sha256(args.analysis.read_bytes()).hexdigest()}
    write_json(args.output, report)
    if args.plot:
        plot_sensitivity(report, args.plot)
    print(json.dumps(report["rl_vs_sft"]))


if __name__ == "__main__":
    main()
