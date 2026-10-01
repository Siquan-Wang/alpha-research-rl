"""Plot saved frozen-pool outcomes after their public-evidence replay succeeds."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from alpha_research_rl.astra_pool_diagnosis import replay_pool_diagnosis


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-stem", type=Path, required=True)
    args = parser.parse_args()
    outputs = [args.output_stem.with_suffix(suffix) for suffix in (".svg", ".png")]
    if any(path.exists() for path in outputs):
        raise FileExistsError("Figure outputs must be new paths")
    root = Path(__file__).resolve().parents[1]
    report_path = root / "results/astra_pool_diagnosis_v1.json"
    verified = replay_pool_diagnosis(root / "artifacts/astra-pool-diagnosis-v1/contract.json",
                                     root / "artifacts/astra-pool-diagnosis-v1/execution",
                                     source_root=root, report_path=report_path)
    raw = report_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != verified["report_sha256"]:
        raise ValueError("Report changed after saved replay")
    report = json.loads(raw)
    if report["slot_validity"]["all"]["valid_count"] != 180:
        raise ValueError("This bank-specific IC figure requires all 180 slots valid")

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MultipleLocator

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "svg.hashsalt": "astra-pool-diagnosis-v1", "axes.spines.top": False,
                         "axes.spines.right": False, "axes.spines.left": False,
                         "axes.spines.bottom": False})
    fig, (left, right) = plt.subplots(1, 2, figsize=(13, 7), gridspec_kw={"width_ratios": [1, 1.4]})
    fig.patch.set_facecolor("white")
    fig.suptitle("Frozen pools: where the historical selector missed headroom", x=.055, y=.965,
                 ha="left", fontsize=18, fontweight="bold", color="#182c3c")
    fig.text(.055, .905, "POST-HOC  ·  180 fixed slots  ·  132 unique keys  ·  108 new + 24 reused evaluations",
             color="#526673", fontsize=11)
    arms = ("full_feedback", "validity_only", "withheld_feedback")
    names = ("Full feedback", "Validity only", "Withheld feedback")
    styles = (("original", "Historical best", "#245b76", "o"),
              ("first", "First proposal", "#4f929a", "s"),
              ("minimum_ast", "Smallest AST", "#88959c", "^"),
              ("oracle", "Hindsight maximum", "#b7812b", "D"))
    for index, (selector, label, color, marker) in enumerate(styles):
        values = [report["arm_summaries"][arm]["selectors"][selector]["predictive_contribution_q"] for arm in arms]
        y = [i + (index - 1.5) * .14 for i in range(3)]
        left.scatter(values, y, s=48, marker=marker, label=label, edgecolors=color,
                     facecolors="none" if selector == "oracle" else color, zorder=3)
        for value, pos in zip(values, y, strict=True):
            left.text(value + .0013, pos, f"{value:+.4f}", va="center", fontsize=8.5, color=color)
    left.set_yticks(range(3), names)
    left.set_ylim(2.5, -.5)
    left.set_xlim(-.042, .047)
    left.set_title("Mean oriented future IC by fixed selector", loc="left", fontsize=11, pad=16)
    left.set_xlabel("Mean IC across ten periods")
    left.xaxis.set_major_locator(MultipleLocator(.02))
    left.legend(frameon=False, loc="lower left", bbox_to_anchor=(-.22, -.30), ncol=2, fontsize=8.5)

    rows = [row for row in report["selector_rows"] if row["arm"] == "full_feedback"]
    selected = [row["selectors"]["original"]["diagnosis"]["oriented_future_ic"] for row in rows]
    ceiling = [row["selectors"]["oracle"]["diagnosis"]["oriented_future_ic"] for row in rows]
    for i, (s, o) in enumerate(zip(selected, ceiling, strict=True)):
        right.plot([s, o], [i, i], color="#cbd5da", linewidth=2, zorder=1)
    right.scatter(selected, range(10), s=42, color="#245b76", label="Historical best", zorder=3)
    right.scatter(ceiling, range(10), s=45, marker="D", facecolors="none", edgecolors="#b7812b",
                  label="Hindsight maximum", zorder=3)
    right.set_yticks(range(10), [row["task_id"] for row in rows])
    right.invert_yaxis()
    right.set_xlim(-.09, .115)
    right.set_title("Full-feedback pool: every period retained", loc="left", fontsize=11, pad=16)
    right.set_xlabel("Oriented future IC")
    right.xaxis.set_major_locator(MultipleLocator(.05))
    right.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, -.24), fontsize=8.5)
    for axis in (left, right):
        axis.axvline(0, color="#738793", linewidth=.8, zorder=0)
        axis.set_axisbelow(True)
        axis.grid(axis="x", color="#e5eaee", linewidth=.7)
        axis.tick_params(axis="both", length=0)
    fig.text(.055, .047, "The hindsight maximum is unattainable without future information. All three tested feasible rules remain negative on average.\n"
             "Each choice retains abstract search cost 0.06; this is not a monetary trading cost. Previously examined 2020–2024 data; no uncertainty intervals.",
             fontsize=8.6, color="#526673", va="bottom")
    fig.subplots_adjust(left=.15, right=.97, bottom=.25, top=.8, wspace=.53)
    for output in outputs:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("xb") as stream:
            fig.savefig(stream, format=output.suffix[1:], dpi=180,
                        metadata={"Date": None} if output.suffix == ".svg" else {})
    plt.close(fig)
    print("Saved SVG and PNG from the replay-verified complete pool diagnosis.")


if __name__ == "__main__":
    main()
