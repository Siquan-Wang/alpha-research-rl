"""Plot a complete replay-verified matched-prefix study, including every state."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

GENERATORS = ("truthful", "masked", "copy", "window_edit", "grammar_draw")
NAMES = ("Truthful feedback", "Masked feedback", "Copy baseline", "One window edit", "One grammar draw")
COLORS = ("#245b76", "#b7812b", "#637d89", "#637d89", "#637d89")


def plot_analysis(analysis, output_stem, *, evidence_label):
    """Render supplied verified analysis; synthetic callers must identify their fixture."""
    outputs = [Path(output_stem).with_suffix(suffix) for suffix in (".svg", ".png")]
    if any(path.exists() for path in outputs):
        raise FileExistsError("Figure outputs must be new paths")
    expected_states = [f"{year}-H{half}" for year in range(2020, 2025) for half in (1, 2)]
    if (analysis["slot_count"] != 200 or analysis["state_count"] != 10
            or [row["task_id"] for row in analysis["states"]] != expected_states
            or set(analysis["generators"]) != set(GENERATORS)):
        raise ValueError("The complete fixed 200-slot, ten-state analysis is required")
    if any(analysis["generators"][name]["candidate"]["denominator"] != 40 for name in GENERATORS):
        raise ValueError("All forty slots per generator must remain")
    if any(len(state["repeated_values"][name][field]) != 4
           for state in analysis["states"] for name in GENERATORS for field in ("candidate_Q", "G")):
        raise ValueError("Every state/generator needs all four repetitions")

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "svg.hashsalt": "astra-matched-prefix-v1", "axes.spines.top": False,
                         "axes.spines.right": False, "axes.spines.left": False,
                         "axes.spines.bottom": False})
    fig, axes = plt.subplots(2, 2, figsize=(13, 10), gridspec_kw={"height_ratios": [1, 1.8]})
    fig.patch.set_facecolor("white")
    fig.suptitle("Matched starts: proposal quality and gains after selection", x=.045, y=.975,
                 ha="left", fontsize=18, fontweight="bold", color="#182c3c")
    fig.text(.045, .933, evidence_label, fontsize=10, color="#526673")
    fig.text(.045, .905, "80 hosted calls + 120 cheap-reference slots  ·  40 slots per generator  ·  Ten fixed development states",
             fontsize=10, color="#526673")
    for axis, field, title in ((axes[0, 0], "Q", "Primary: mean proposal quality Q"),
                               (axes[0, 1], "G", "Secondary: mean selected-score gain G")):
        values = [analysis["generators"][name]["candidate"]["mean_Q"] if field == "Q"
                  else analysis["generators"][name]["mean_G"] for name in GENERATORS]
        axis.scatter(values, range(5), c=COLORS, s=55, zorder=3)
        for i, (name, value) in enumerate(zip(GENERATORS, values, strict=True)):
            invalid = analysis["generators"][name]["candidate"]["invalid_count"]
            label = f"{value:+.4f}" + (f"  ({invalid}/40 penalized)" if field == "Q" else "")
            axis.annotate(label, (value, i), xytext=(7, 0), textcoords="offset points",
                          va="center", fontsize=9, color=COLORS[i])
        axis.set_yticks(range(5), NAMES)
        axis.set_ylim(4.6, -.6)
        low, high = min(0., *values), max(.01 if field == "G" else 0., *values)
        span = max(high - low, .01)
        axis.set_xlim(low - .12 * span, high + .85 * span)
        axis.set_title(title, loc="left", fontsize=11, pad=12)
        axis.set_xlabel("Oriented future IC; invalid/unusable = −1" if field == "Q"
                        else "Selected Q minus unchanged prefix-baseline Q")
        if field == "G":
            axis.axvline(.01, color="#919da5", linewidth=.8, linestyle="--", zorder=0)
            axis.text(.01, 1.03, "+.01 incremental cost", transform=axis.get_xaxis_transform(),
                      ha="center", fontsize=8, color="#637682")

    for axis, field, title in ((axes[1, 0], "candidate_Q", "All ten states: four proposals per condition"),
                               (axes[1, 1], "G", "All ten states: gains after historical selection")):
        for condition, offset, color in zip(GENERATORS[:2], (-.16, .16), COLORS[:2], strict=True):
            for i, state in enumerate(analysis["states"]):
                values = state["repeated_values"][condition][field]
                positions = [i + offset + (r - 1.5) * .035 for r in range(4)]
                axis.scatter(values, positions, color=color, alpha=.55, s=20, zorder=2,
                             label=("Truthful: four draws" if condition == "truthful" else "Masked: four draws")
                             if i == 0 else None)
                mean = state["generators"][condition]["candidate"]["mean_Q"] if field == "candidate_Q" \
                    else state["generators"][condition]["mean_G"]
                axis.scatter([mean], [i + offset], marker="D", facecolors="none", edgecolors=color,
                             s=48, linewidths=1.1, zorder=3)
        axis.set_yticks(range(10), expected_states)
        axis.set_ylim(9.6, -.6)
        axis.set_title(title, loc="left", fontsize=10.5, pad=14)
        axis.set_xlabel("Proposal Q; all failures retained" if field == "candidate_Q" else "Selected-score gain G")
        axis.margins(x=.13)
        axis.legend(frameon=False, loc="upper left", bbox_to_anchor=(-.03, -.14), fontsize=8.5, ncol=2)
    for axis in axes.flat:
        axis.axvline(0, color="#738793", linewidth=.8, zorder=0)
        axis.set_axisbelow(True)
        axis.grid(axis="x", color="#e5eaee", linewidth=.7)
        axis.tick_params(axis="both", length=0)
    primary = analysis["primary_truthful_minus_masked_Q"]
    secondary = analysis["secondary_truthful_minus_masked_G"]
    mcse = analysis["conditional_generation_mc_se"]
    fig.text(.045, .027, f"Truthful − masked: mean Q {primary:+.6f}; mean G {secondary:+.6f}. "
             f"Conditional generation MCSE for mean Q contrast: {mcse:.6f}.\n"
             "Dots retain all four proposals; open diamonds are cell means. MCSE assumes independent provider draws; this is unverified.\n"
             "Dependent 2020–2024 development states; no fresh holdout or market confidence interval. Abstract attempt cost is not a monetary trading cost.",
             fontsize=8.3, color="#526673", va="bottom")
    fig.subplots_adjust(left=.16, right=.96, top=.82, bottom=.20, hspace=.63, wspace=.65)
    for output in outputs:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("xb") as stream:
            fig.savefig(stream, format=output.suffix[1:], dpi=180,
                        metadata={"Date": None} if output.suffix == ".svg" else {})
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-stem", type=Path, required=True)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    report_path = root / "results/astra_matched_prefix_v1.json"
    from alpha_research_rl.astra_revision_study import replay_revision_study

    verification = replay_revision_study(source_root=root, report_path=report_path)
    raw = report_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != verification["report_sha256"]:
        raise ValueError("Report changed after saved replay")
    report = json.loads(raw)
    plot_analysis(report["analysis"], args.output_stem,
                  evidence_label="COMPLETE MATCHED-PREFIX STUDY  ·  Frozen collection before outcome joins  ·  No Astra weight training")
    print("Saved SVG and PNG from the replay-verified complete matched-prefix study.")


if __name__ == "__main__":
    main()
