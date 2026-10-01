"""Plot all saved training groups' reward-credit categories; no model execution."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Output stem for SVG and PNG")
    args = parser.parse_args()
    report = json.loads(args.input.read_text(encoding="utf-8"))
    if (report.get("study") != "financial-rloo-reward-credit-v1"
            or report.get("status") != "verified_saved_reward_credit"
            or report.get("input_bytes_verified") is not True):
        raise ValueError("First complete the saved reward-credit analysis")
    runs = report["runs"]
    expected = ["financial-rloo23-v1", "financial-rloo29-v1",
                "financial-placebo23-v1", "financial-placebo29-v1"]
    if [run["run_id"] for run in runs] != expected:
        raise ValueError("The figure requires all four runs in registered order")
    categories = []
    update_counts = []
    for run in runs:
        groups = run["groups"]
        if [group["group"] for group in groups] != list(range(16)):
            raise ValueError("The figure requires every ordered group")
        row = []
        for group in groups:
            total = group["advantages"]["R"]
            validity = group["advantages"]["V"]
            ic = group["advantages"]["C"]
            if not all(len(v) == 4 for v in (total, validity, ic)):
                raise ValueError("Expected four coefficients per channel")
            if any(value != 0.0 for value in validity):
                row.append(2)
            elif any(value != 0.0 for value in total):
                row.append(1)
            elif any(value != 0.0 for value in ic):
                raise ValueError("Unexpected zero-total category with IC contrast")
            else:
                row.append(0)
        categories.append(row)
        update_counts.append(sum(group["optimizer_step"] for group in groups))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch

    colors = ["#e1e5e9", "#327c98", "#d28b39"]
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "svg.fonttype": "none"})
    fig, ax = plt.subplots(figsize=(13.2, 4.9))
    fig.subplots_adjust(left=.17, right=.91, top=.73, bottom=.34)
    ax.imshow(categories, cmap=ListedColormap(colors), vmin=0, vmax=2, aspect="auto")
    ax.set_xticks(range(16), range(1, 17))
    ax.set_yticks(range(4), ["Correct linkage · 23", "Correct linkage · 29",
                           "Permuted reward · 23", "Permuted reward · 29"])
    ax.set_xlabel("Training group (one-based; task order differs by seed)", labelpad=11)
    ax.tick_params(length=0, pad=8)
    ax.set_xticks([x - .5 for x in range(17)], minor=True)
    ax.set_yticks([x - .5 for x in range(5)], minor=True)
    ax.grid(which="minor", color="white", linewidth=3)
    ax.tick_params(which="minor", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for row, values in enumerate(categories):
        for col, category in enumerate(values):
            ax.text(col, row, ["0", "C", "V"][category], ha="center", va="center",
                    color="#253b48" if category == 0 else "white", fontweight="bold")
        ax.text(16.0, row, f"{update_counts[row]} steps", ha="left", va="center", fontsize=10)
    fig.suptitle("Which reward terms supplied the recorded RLOO coefficients?",
                 x=.02, ha="left", y=.96, fontsize=18, fontweight="bold")
    fig.legend(handles=[Patch(color=colors[1], label="C: IC coefficients only"),
                        Patch(color=colors[2], label="V: validity coefficients present"),
                        Patch(color=colors[0], label="0: all coefficients zero")],
               loc="upper left", bbox_to_anchor=(.02, .88), frameon=False, ncol=3)
    fig.text(.02, .07,
             f"All 64 saved groups retained; {sum(update_counts)} recorded optimizer steps. "
             "IC is training-assessment information.\n"
             "Control coefficients follow their logged reward assignments, not the completion's own IC.\n"
             "Coefficient presence does not identify gradient size, Adam attribution or financial learning.",
             fontsize=10, color="#465765", linespacing=1.5)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for suffix in (".svg", ".png"):
        fig.savefig(args.output.with_suffix(suffix), dpi=170, facecolor="white")
    svg_path = args.output.with_suffix(".svg")
    svg_path.write_text("\n".join(line.rstrip() for line in
                                svg_path.read_text(encoding="utf-8").splitlines()) + "\n",
                        encoding="utf-8")
    plt.close(fig)
    print(json.dumps({"groups": 64, "optimizer_steps": sum(update_counts),
                      "output_stem": args.output.as_posix()}))


if __name__ == "__main__":
    main()
