"""Draw paper-sized figures from two already published, byte-pinned reports."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/figures"
COLORS = ["#e1e5e9", "#327c98", "#d28b39"]


def read_pinned(name, digest):
    raw = (ROOT / "results" / name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError(f"Published input changed: {name}")
    return json.loads(raw)


def save(fig, name):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / name
    fig.savefig(path, dpi=240, facecolor="white")
    plt.close(fig)
    return {"path": path.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def matched_figure(report):
    generators = ["truthful", "masked", "copy", "window_edit", "grammar_draw"]
    labels = ["Truthful Astra", "Masked Astra", "Copy", "Window edit", "Seeded grammar"]
    rows = [report["analysis"]["generators"][key] for key in generators]
    if any(row["candidate"]["denominator"] != 40 for row in rows):
        raise ValueError("The paper figure must retain all forty slots per generator")
    q = [row["candidate"]["mean_Q"] for row in rows]
    g = [row["mean_G"] for row in rows]
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 4.1))
    fig.subplots_adjust(left=.205, right=.98, top=.88, bottom=.115, hspace=.73)
    fig.suptitle("Matched-prefix revisions: different outcomes, same 200 slots",
                 x=.02, ha="left", y=.995, fontsize=10, fontweight="bold")
    panels = [("A   New-candidate quality Q (failure = -1)", q, (-.068, .004),
               [-.06, -.04, -.02, 0], .0012),
              ("B   Change in selected assessment score G", g, (-.0034, .0007),
               [-.003, -.002, -.001, 0], .00007)]
    for ax, (title, values, limits, ticks, offset) in zip(axes, panels, strict=True):
        ax.set_title(title, loc="left", fontsize=9.3, pad=7)
        ax.axvline(0, color="#75818b", linewidth=.8)
        for row, value in enumerate(values):
            color = "#327c98" if row < 2 else "#718390"
            ax.plot([0, value], [row, row], color=color, linewidth=1.6)
            ax.scatter([value], [row], color=color, s=23, zorder=3)
            ax.text(value - offset, row, f"{value:+.6f}", ha="right", va="center", fontsize=8.3)
        ax.set_yticks(range(5), labels)
        ax.set_ylim(4.55, -.55)
        ax.set_xlim(*limits)
        ax.set_xticks(ticks)
        ax.tick_params(axis="both", length=0, pad=5, labelsize=8.5)
        ax.grid(axis="x", color="#e4e9ec", linewidth=.6)
        ax.set_axisbelow(True)
        for spine in ax.spines.values():
            spine.set_visible(False)
    fig.text(.02, .018, "Grammar: 38/40 usable; others: 40/40. All mean G - 0.01 < 0; continuation gate failed.",
             fontsize=8.2, color="#465765")
    return save(fig, "research-note-matched-prefix-v1.png")


def credit_figure(report):
    expected = ["financial-rloo23-v1", "financial-rloo29-v1",
                "financial-placebo23-v1", "financial-placebo29-v1"]
    if [run["run_id"] for run in report["runs"]] != expected:
        raise ValueError("Expected all four saved runs in their published order")
    categories, steps = [], []
    for run in report["runs"]:
        if [group["group"] for group in run["groups"]] != list(range(16)):
            raise ValueError("Expected every saved group")
        row = []
        for group in run["groups"]:
            advantages = group["advantages"]
            if any(value != 0 for value in advantages["V"]):
                row.append(2)
            elif any(value != 0 for value in advantages["R"]):
                row.append(1)
            else:
                if any(value != 0 for value in advantages["C"]):
                    raise ValueError("Unclassified nonzero IC coefficient")
                row.append(0)
        categories.append(row)
        steps.append(sum(group["optimizer_step"] for group in run["groups"]))
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    fig.subplots_adjust(left=.205, right=.91, top=.72, bottom=.34)
    ax.imshow(categories, cmap=ListedColormap(COLORS), vmin=0, vmax=2, aspect="auto")
    ax.set_xticks(range(16), range(1, 17))
    ax.set_yticks(range(4), ["Correct / seed 23", "Correct / seed 29",
                           "Permuted / seed 23", "Permuted / seed 29"])
    ax.set_xlabel("Training group (one-based)", labelpad=5, fontsize=8.5)
    ax.tick_params(length=0, pad=5, labelsize=8.4)
    ax.set_xticks([x - .5 for x in range(17)], minor=True)
    ax.set_yticks([x - .5 for x in range(5)], minor=True)
    ax.grid(which="minor", color="white", linewidth=1.8)
    ax.tick_params(which="minor", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    for row, values in enumerate(categories):
        for col, category in enumerate(values):
            ax.text(col, row, ["0", "C", "V"][category], ha="center", va="center",
                    fontsize=8.6, color="#253b48" if category == 0 else "white")
        ax.text(15.85, row, f"{steps[row]} steps", ha="left", va="center", fontsize=8.2)
    fig.suptitle("Direct validity contrast was absent in most recorded RLOO updates",
                 x=.02, ha="left", y=.98, fontsize=10, fontweight="bold")
    fig.legend(handles=[Patch(color=COLORS[1], label="C: IC only"),
                        Patch(color=COLORS[2], label="V: validity term present"),
                        Patch(color=COLORS[0], label="0: all zero")],
               loc="upper left", bbox_to_anchor=(.02, .92), frameon=False,
               ncol=3, fontsize=8.5, handlelength=1)
    fig.text(.02, .025,
             "All 64 groups / 63 steps. Controls use assigned reward channels. IC is training-assessment information.\n"
             "Coefficient presence does not identify gradient size, Adam attribution or financial learning.",
             fontsize=8, color="#465765", linespacing=1.5)
    return save(fig, "research-note-reward-credit-v1.png")


def main():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    matched = read_pinned("astra_matched_prefix_v1.json",
                          "89162112ddad384ed8917a8b1198ce94044abc90ff15e1680bfe88b66eb43c37")
    credit = read_pinned("reward_credit_v1.json",
                         "59d31578928894581208c8928fd38690b839d0c12264c38e64779ffc19957cb7")
    print(json.dumps({"figures": [matched_figure(matched), credit_figure(credit)],
                      "matplotlib_version": matplotlib.__version__, "new_evaluations": 0}))


if __name__ == "__main__":
    main()
