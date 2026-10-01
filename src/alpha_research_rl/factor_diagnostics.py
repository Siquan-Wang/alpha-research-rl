"""Feedback-only rank equivalence diagnostics for saved financial proposals.

No assessment target is constructed or read. Correlation uses two causal factor
arrays on the original purged feedback signal dates. Only aggregates are emitted.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

from .artifacts import write_json
from .data import MarketPanel
from .dsl import evaluate_expression
from .evaluation import score_factor
from .financial_policy import expression_key, load_pinned_panel
from .financial_tasks import HARD_CAP, HORIZON, TEACHER_GRID, _halfyear_bounds, _prefix_panel

RANK_EQUIVALENCE_TOLERANCE = 1e-10


class FeedbackRankAnalyzer:
    """Per-task caches contain feedback arrays only and are never serialized."""

    def __init__(self, visible_panel: MarketPanel, feedback: tuple[int, int]):
        start, stop = feedback
        if not 0 <= start < stop <= len(visible_panel.dates):
            raise ValueError("invalid feedback signal interval")
        if visible_panel.dates[-1].astype("datetime64[D]") > HARD_CAP:
            raise ValueError("feedback panel exceeds 2024-12-31 cap")
        self._visible = visible_panel
        self._feedback = feedback
        self._values_cache: dict[str, np.ndarray] = {}
        self._pair_cache: dict[tuple[str, str], dict] = {}

    @classmethod
    def from_panel(cls, panel: MarketPanel, year: int, half: int) -> FeedbackRankAnalyzer:
        """Reconstruct just the preceding half-year, without any forward labels."""
        dates = panel.dates.astype("datetime64[D]")
        if dates[-1] > HARD_CAP:
            raise ValueError("financial diagnostic panel must be capped at 2024-12-31")
        _halfyear_bounds(year, half)  # Validate the task descriptor without scoring its assessment.
        previous = (year - 1, 2) if half == 1 else (year, 1)
        first, end = _halfyear_bounds(*previous)
        if dates[0] > first + np.timedelta64(7, "D") or dates[-1] < end - np.timedelta64(7, "D"):
            raise ValueError("panel does not cover the task's feedback half-year")
        start, boundary = int(np.searchsorted(dates, first)), int(np.searchsorted(dates, end))
        return cls(_prefix_panel(panel, boundary), (start, boundary - HORIZON))

    @classmethod
    def from_task(cls, task) -> FeedbackRankAnalyzer:
        """Trusted analysis only: use the task's fixed historical prefix/bounds."""
        return cls(task._visible, task._feedback)

    def _values(self, expression: str) -> np.ndarray:
        key = expression_key(expression)
        if key is None:
            raise ValueError("invalid expression")
        if key not in self._values_cache:
            self._values_cache[key] = evaluate_expression(expression, self._visible)
        return self._values_cache[key]

    def pair_similarity(self, expression: str, reference: str) -> dict:
        """abs(mean daily Spearman), retaining signed mean and support separately."""
        key = expression_key(expression), expression_key(reference)
        if key in self._pair_cache:
            return dict(self._pair_cache[key])
        length = self._feedback[1] - self._feedback[0]
        result = {"expression": expression, "reference": reference, "status": "unscorable",
                  "reason": "invalid_or_unsupported_expression", "mean_daily_spearman": None,
                  "absolute_mean_daily_spearman": None, "daily_spearman_std": None,
                  "paired_cell_coverage": 0.0, "n_valid_dates": 0, "n_signal_dates": length,
                  "required_valid_dates": max(min(20, length), math.ceil(0.8 * length)),
                  "near_exact_rank_equivalent": False, "tolerance": RANK_EQUIVALENCE_TOLERANCE}
        try:
            values, teacher_values = self._values(expression), self._values(reference)
            # score_factor is a generic daily finite-pair Spearman routine. Here
            # its second array is another factor, never a forward-return target.
            metrics = score_factor(values, teacher_values, *self._feedback)
            result.update(paired_cell_coverage=metrics["coverage"], n_valid_dates=metrics["n_dates"])
            if np.isfinite(metrics["mean_ic"]):
                result["mean_daily_spearman"] = metrics["mean_ic"]
                result["absolute_mean_daily_spearman"] = abs(metrics["mean_ic"])
                result["daily_spearman_std"] = metrics["ic_std"]
            adequate = (result["absolute_mean_daily_spearman"] is not None
                        and result["paired_cell_coverage"] >= 0.8
                        and result["n_valid_dates"] >= result["required_valid_dates"])
            if adequate:
                result.update(status="ok", reason=None,
                              near_exact_rank_equivalent=result["absolute_mean_daily_spearman"]
                              >= 1.0 - RANK_EQUIVALENCE_TOLERANCE)
            else:
                result["reason"] = "insufficient_nonconstant_paired_support"
        except (ValueError, TypeError, ArithmeticError, RecursionError):
            pass
        self._pair_cache[key] = result
        return dict(result)

    def diagnose(self, expression: str, references: tuple[str, ...] = TEACHER_GRID) -> dict:
        comparisons = [self.pair_similarity(expression, reference) for reference in references]
        usable = [row for row in comparisons if row["status"] == "ok"]
        nearest = max(usable, key=lambda row: row["absolute_mean_daily_spearman"]) if usable else None
        return {"expression": expression, "canonical_ast": expression_key(expression),
                "status": "ok" if nearest else "unscorable", "nearest_teacher": nearest,
                "teacher_comparisons": comparisons,
                "interpretation": "feedback rank similarity; sign and monotone aliases are not independent alpha"}


def diagnose_report(report: dict, panel: MarketPanel) -> dict:
    """Analyze every unique valid saved proposal from both declared parsers."""
    episodes = []
    analyzers: dict[tuple[int, int], FeedbackRankAnalyzer] = {}
    for episode in report["episodes"]:
        manifest = episode["task"]
        descriptor = manifest["year"], manifest["half"]
        if descriptor not in analyzers:
            analyzers[descriptor] = FeedbackRankAnalyzer.from_panel(panel, *descriptor)
        analyzer = analyzers[descriptor]
        if "feedback_bounds_half_open" in manifest and list(analyzer._feedback) != manifest["feedback_bounds_half_open"]:
            raise ValueError("saved task's feedback bounds differ from pinned reconstruction")
        occurrences = Counter()
        expressions = {}
        for record in episode["records"]:
            for parser in ("strict", "fence_tolerant_secondary"):
                outcome = record[parser]
                if outcome["status"] != "ok" or not isinstance(outcome["expression"], str):
                    continue
                expression = outcome["expression"]
                key = expression_key(expression)
                expressions[key] = expression
                occurrences[(key, parser, record["condition"], record["decoding"])] += 1
        diagnostics = []
        for key, expression in expressions.items():
            diagnostic = analyzer.diagnose(expression)
            counts = [{"parser": parser, "condition": condition, "decoding": decoding, "count": count}
                      for (candidate, parser, condition, decoding), count in occurrences.items() if candidate == key]
            diagnostics.append({**diagnostic, "saved_proposal_counts": counts})
        episodes.append({"task": manifest, "unique_valid_expression_diagnostics": diagnostics})
    rows = [row for episode in episodes for row in episode["unique_valid_expression_diagnostics"]]
    supported = [row for row in rows if row["status"] == "ok"]
    source_hash = panel.metadata.get("raw_sha256")
    report_hash = report.get("manifest", {}).get("config", {}).get("snapshot_sha256")
    if report_hash is not None and report_hash != source_hash:
        raise ValueError("saved evaluation and diagnostic panel snapshots differ")
    return {"study": "financial-feedback-rank-alias-diagnostics-v1", "snapshot_sha256": source_hash,
            "references": list(TEACHER_GRID), "similarity_definition": "abs(mean daily cross-sectional Spearman)",
            "rank_equivalence_tolerance": RANK_EQUIVALENCE_TOLERANCE,
            "support": {"paired_cell_coverage": 0.8, "valid_date_fraction": 0.8, "min_valid_dates": 20},
            "episodes": episodes,
            "summary": {"n_tasks": len(episodes), "unique_task_expression_pairs": len(rows),
                        "supported_task_expression_pairs": len(supported),
                        "near_exact_rank_equivalent_pairs": sum(row["nearest_teacher"]["near_exact_rank_equivalent"]
                                                                for row in supported)},
            "limitations": ["feedback only; no future assessment labels constructed or read",
                            "unique task-expression counts are descriptive, not independent observations",
                            "nearest-reference search over 12 fixed formulas, not a novelty bonus",
                            "high rank similarity does not establish future alpha or profitability",
                            "no raw factor arrays, daily correlations or post-2024 values published"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputreport", required=True, type=Path)
    parser.add_argument("--panel", default="data/raw/french49-v1/49_Industry_Portfolios_daily_CSV.zip")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    panel = load_pinned_panel(args.panel)
    report = json.loads(args.inputreport.read_text(encoding="utf-8"))
    diagnostics = diagnose_report(report, panel)
    diagnostics["input_report"] = args.inputreport.name
    write_json(args.output, diagnostics)
    print(diagnostics["summary"], flush=True)


if __name__ == "__main__":
    main()
