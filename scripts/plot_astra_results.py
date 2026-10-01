"""Plot verified saved Astra v1 outcomes without financial or model execution."""

from __future__ import annotations

import argparse
from pathlib import Path

from alpha_research_rl.astra_explorer import build_payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-stem", type=Path, required=True)
    args = parser.parse_args()
    outputs = [args.output_stem.with_suffix(suffix) for suffix in (".svg", ".png")]
    if any(path.exists() for path in outputs):
        raise FileExistsError("Figure outputs must be new paths")
    root = Path(__file__).resolve().parents[1]
    saved = build_payload(root / "artifacts/astra-agent-v1/contract.json",
                          root / "results/astra_agent_v1_submissions.json",
                          root / "results/astra_agent_v1_assessment.json", source_root=root)["assessment"]
    # Plotting is optional; a public saved-evidence replay needs no plotting stack.
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MultipleLocator

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "svg.hashsalt": "astra-agent-v1", "axes.spines.top": False,
                         "axes.spines.right": False, "axes.spines.left": False,
                         "axes.spines.bottom": False, "axes.titleweight": "bold"})
    arms = ("full_feedback", "validity_only", "withheld_feedback")
    names = ("Full feedback", "Validity only", "Withheld feedback")
    # All outcomes are usable in the frozen v1 bank; q therefore equals mean IC.
    if any(saved["arm_summaries"][arm]["validity_fraction_p"] != 1.0 for arm in arms):
        raise ValueError("This bank-specific figure requires all 30 selected assessments to be valid")
    means = [saved["arm_summaries"][arm]["predictive_contribution_q"] for arm in arms]
    periods = [row["task_id"] for row in saved["paired"]]
    paired = [row["full_minus_validity"] for row in saved["paired"]]
    average = saved["primary_mean_full_minus_validity"]
    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 6.5), gridspec_kw={"width_ratios": [1, 1.6]})
    fig.patch.set_facecolor("#ffffff")
    fig.suptitle("Astra feedback study: no observed improvement", x=.07, y=.97,
                 ha="left", fontsize=19, fontweight="bold", color="#182c3c")
    fig.text(.07, .905, "180 proposals  ·  30 pools published before assessment  ·  all 30 outcomes valid",
             color="#526673", fontsize=11)
    left.barh(names, means, color=("#245b76", "#7995a3", "#b5c5cc"), height=.55)
    left.invert_yaxis()
    left.set_title("Every arm has negative mean future IC", loc="left", fontsize=11, pad=16)
    left.set_xlim(-.043, .003)
    left.axvline(0, color="#738793", linewidth=.8)
    left.set_xlabel("Mean oriented future IC")
    left.xaxis.set_major_locator(MultipleLocator(.02))
    for i, value in enumerate(means):
        left.text(value - .0006, i, f"{value:.4f}", va="center", ha="right", fontsize=9)
    left.tick_params(axis="both", length=0)
    right.barh(periods, paired, color=["#28788b" if value > 1e-12 else "#a66044" for value in paired], height=.65)
    right.invert_yaxis()
    right.set_title(f"Full − validity by period  |  overall mean {average:+.4f}", loc="left", fontsize=11, pad=16)
    right.axvline(0, color="#738793", linewidth=.8)
    right.axvline(average, color="#182c3c", linestyle="--", linewidth=1, label="Ten-period mean")
    right.set_xlim(-.097, .046)
    right.set_xlabel("Difference in oriented future IC")
    right.xaxis.set_major_locator(MultipleLocator(.04))
    right.tick_params(axis="both", length=0)
    for i, value in enumerate(paired):
        label = "0.0000" if abs(value) < .00005 else f"{value:+.4f}"
        right.text(value + (.002 if value >= 0 else -.002), i, label, va="center",
                   ha="right" if value < 0 else "left", fontsize=9)
    right.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, -.24), fontsize=9)
    for axis in (left, right):
        axis.set_axisbelow(True)
        axis.grid(axis="x", color="#e5eaee", linewidth=.7)
    fig.text(.07, .06, "Previously examined 2020–2024 development periods; one trajectory per arm and period.\n"
             "Descriptive values, with no uncertainty intervals. The common 0.06 search cost cancels in differences.",
             fontsize=9, color="#526673", va="bottom")
    fig.subplots_adjust(left=.15, right=.97, bottom=.23, top=.8, wspace=.6)
    for output in outputs:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("xb") as stream:
            fig.savefig(stream, format=output.suffix[1:], dpi=180,
                        metadata={"Date": None} if output.suffix == ".svg" else {})
    plt.close(fig)
    print("Saved SVG and PNG from the replay-verified complete v1 assessment.")


if __name__ == "__main__":
    main()
