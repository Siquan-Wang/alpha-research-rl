"""Plot the actual saved synthetic confirmation regression after guarded replay."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


def load_verified(root):
    spec = importlib.util.spec_from_file_location("sealed_plot_replay", root / "scripts/check_sealed_confirmation.py")
    driver = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = driver
    spec.loader.exec_module(driver)
    proof = driver.replay(root)
    raw = (root / "results/sealed_confirmation_v1.json").read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != proof["report_sha256"]:
        raise ValueError("report changed after saved-evidence replay")
    return json.loads(raw), proof


def plot(report, proof, prefix):
    outputs = [prefix.with_suffix(".svg"), prefix.with_suffix(".png")]
    if any(path.exists() for path in outputs):
        raise FileExistsError("figure output already exists; select a new prefix")
    analysis = report["analysis"]
    null, planted = analysis["by_law"]["null"], analysis["by_law"]["planted"]
    thresholds = report["thresholds"]
    teal, orange, ink, faint = "#216b75", "#b76132", "#213747", "#d8e1e8"
    names = ["fixed_correct", "adaptive_correct", "orientation_only_leak", "fixed_leak", "adaptive_leak"]
    labels = ["Fixed\nsearch", "Adaptive\nsearch", "Fitted sign\nonly", "Fixed search\n+ fitted sign", "Adaptive search\n+ fitted sign"]
    values = [null[arm]["rejections"] for arm in names]
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.1), gridspec_kw={"width_ratios": [1.8, 1]})
    fig.set_facecolor("#ffffff")
    for ax in axes:
        ax.set_axisbelow(True)
        ax.grid(axis="y", color=faint, linewidth=.7)
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color(faint)
        ax.tick_params(colors=ink, labelsize=9)
    colors = [teal, teal, orange, orange, orange]
    bars = axes[0].bar(range(5), values, color=colors, width=.64, edgecolor=colors)
    for bar in bars[2:]:
        bar.set_hatch("///")
        bar.set_edgecolor("#fff4eb")
    axes[0].set_xticks(range(5), labels)
    axes[0].set_ylim(0, 512 * 1.13)
    axes[0].set_ylabel("Null-panel rejections / 512", color=ink)
    axes[0].set_title("A  Correct confirmation and deliberately invalid controls", loc="left", fontsize=11, pad=18)
    upper = thresholds["null_upper_inclusive"]
    axes[0].axhline(upper, color=ink, linestyle="--", linewidth=1)
    axes[0].text(.02, .94, f"Correct-arm upper check: {upper}/512", transform=axes[0].transAxes,
                 color=ink, fontsize=9, va="top")
    for bar, value in zip(bars, values, strict=True):
        axes[0].text(bar.get_x() + bar.get_width()/2, max(value + 9, upper + 12), str(value),
                     ha="center", color=ink, fontsize=11)
    pnames = ["fixed_correct", "adaptive_correct", "oracle"]
    pvalues = [planted[arm]["rejections"] for arm in pnames]
    pbars = axes[1].bar(range(3), pvalues, color=[teal, teal, ink], width=.6)
    axes[1].set_xticks(range(3), ["Fixed\nsearch", "Adaptive\nsearch", "Known\noracle"])
    axes[1].set_ylim(0, 150)
    axes[1].set_yticks([0, 32, 64, 96, 128])
    axes[1].set_ylabel("Planted-panel rejections / 128", color=ink)
    axes[1].set_title("B  Power check and descriptive search outcomes", loc="left", fontsize=11, pad=18)
    axes[1].axhline(thresholds["oracle_lower_inclusive"], color=ink, linestyle="--", linewidth=1)
    for bar, value in zip(pbars, pvalues, strict=True):
        axes[1].text(bar.get_x()+bar.get_width()/2, value+3, str(value), ha="center", color=ink, fontsize=11)
    state = "passed" if analysis["validation_pass"] else "failed"
    fig.suptitle(f"Sealed confirmation: the frozen synthetic validation {state}", x=.07, y=.98,
                 ha="left", color=ink, fontsize=17, fontweight="bold")
    fig.text(.07, .91, "640 prespecified panels · six binary features · no model calls or market data", color=ink, fontsize=10)
    fig.legend(handles=[Patch(facecolor=teal, label="Valid recorded confirmation protocol"),
                        Patch(facecolor=orange, edgecolor="#fff4eb", hatch="///", label="Protocol invalid; naive diagnostics")],
               loc="lower left", bbox_to_anchor=(.065, .13), frameon=False, ncol=2, fontsize=9)
    fig.text(.07, .105, "Only two correct-null upper checks and the planted-oracle lower check determine calibration success.",
             color=ink, fontsize=9)
    fig.text(.07, .078, "Fault exceedances and search power are descriptive. Known synthetic laws do not validate financial IC or hidden label access.",
             color=ink, fontsize=9)
    fig.text(.07, .036, "Saved report SHA256: " + proof["report_sha256"], color="#687d8a", fontsize=7.3, family="monospace")
    fig.subplots_adjust(left=.07, right=.975, bottom=.27, top=.82, wspace=.3)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    for path in outputs:
        with path.open("xb") as handle:
            fig.savefig(handle, format=path.suffix[1:], dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-prefix", type=Path, required=True)
    args = parser.parse_args()
    report, proof = load_verified(args.root.resolve())
    outputs = plot(report, proof, args.output_prefix)
    print(json.dumps({"report_sha256": proof["report_sha256"], "outputs": [str(p) for p in outputs]}))


if __name__ == "__main__":
    main()
