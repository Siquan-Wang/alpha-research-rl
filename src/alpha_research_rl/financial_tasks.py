"""One-shot return-formula diagnostic with chronological financial task blocks.

This contextual-bandit study is separate from the sequential ResearchEnvironment.
Agent observations contain only two actually computed historical probe results;
future metrics are reserved for explicit training rewards or frozen evaluation.
"""

from __future__ import annotations

import argparse
import ast
import copy
import math
from collections import Counter
from dataclasses import dataclass, field
from itertools import pairwise
from pathlib import Path

import numpy as np

from .artifacts import write_json
from .data import MarketPanel
from .dsl import evaluate_expression
from .evaluation import forward_returns, score_factor
from .french import load_french49

HORIZON = 5
PROPOSAL_COST = 0.01
INVALID_REWARD = -1.0 - PROPOSAL_COST
HARD_CAP = np.datetime64("2024-12-31", "D")
EXPECTED_RAW_SHA256 = "8f394fe34bea54d41b9aafed410425ee8f8e252ede3c71a7c1cd20bab83040de"
PROBES = ("ts_mean(returns,5)", "ts_mean(returns,20)")
FORMULA_GRID = (
    "returns", "delay(returns,1)", "delay(returns,5)", "ts_mean(returns,3)",
    "ts_mean(returns,5)", "ts_mean(returns,10)", "ts_mean(returns,20)",
    "ts_mean(returns,40)", "ts_mean(returns,60)", "ts_std(returns,5)",
    "ts_std(returns,20)", "sub(ts_mean(returns,5),ts_mean(returns,20))",
    "sub(ts_mean(returns,10),ts_mean(returns,40))",
    "div(ts_mean(returns,5),ts_std(returns,20))",
    "div(ts_mean(returns,20),ts_std(returns,20))", "mul(returns,ts_mean(returns,5))",
)
TEACHER_GRID = FORMULA_GRID[:12]
GRID = FORMULA_GRID
teacher_grid = TEACHER_GRID
SPLIT_YEARS = {"train": range(2002, 2018), "feasibility": range(2018, 2020), "transfer": range(2020, 2025)}


def task_periods(split: str) -> tuple[tuple[int, int], ...]:
    if split not in SPLIT_YEARS:
        raise ValueError("split must be train, feasibility or transfer")
    return tuple((year, half) for year in SPLIT_YEARS[split] for half in (1, 2))


def _halfyear_bounds(year: int, half: int) -> tuple[np.datetime64, np.datetime64]:
    if type(year) is not int or type(half) is not int or half not in (1, 2):
        raise ValueError("year must be an integer and half must be 1 or 2")
    start = np.datetime64(f"{year:04d}-{'01' if half == 1 else '07'}-01", "D")
    stop = np.datetime64(f"{year:04d}-07-01", "D") if half == 1 else np.datetime64(f"{year + 1:04d}-01-01", "D")
    return start, stop


def _metrics(values: np.ndarray, labels: np.ndarray, start: int, stop: int) -> dict:
    raw = score_factor(values, labels, start, stop)
    return {name: float(raw[name]) if np.isfinite(raw[name]) else None
            for name in ("mean_ic", "coverage", "ic_std")} | {
        "n_dates": raw["n_dates"], "n_signal_dates": stop - start,
    }


def _usable(metrics: dict) -> bool:
    length = metrics["n_signal_dates"]
    required = max(min(20, length), math.ceil(0.8 * length))
    return (metrics["mean_ic"] is not None and metrics["coverage"] >= 0.8
            and metrics["n_dates"] >= required)


def _expression_key(expression: str) -> str:
    return ast.dump(ast.parse(expression.strip(), mode="eval"), include_attributes=False)


def _prefix_panel(panel: MarketPanel, stop: int) -> MarketPanel:
    arrays = [array[:stop].copy() for array in (panel.close, panel.volume, panel.returns)]
    for array in arrays:
        array.flags.writeable = False
    dates = panel.dates[:stop].copy()
    dates.flags.writeable = False
    return MarketPanel(*arrays, dates, panel.assets, {"supported_features": ["returns"]})


@dataclass(frozen=True)
class FinancialTask:
    """Frozen half-year task; observation is a fresh copy without period identity.

    Python objects do not constitute an adversarial sandbox. Actor callers must
    receive only observation; internal future metrics never enter that payload.
    """

    _panel: MarketPanel = field(repr=False)
    year: int
    half: int
    _feedback: tuple[int, int] = field(init=False, repr=False)
    _assessment: tuple[int, int] = field(init=False, repr=False)
    _feedback_boundary: int = field(init=False, repr=False)
    _assessment_boundary: int = field(init=False, repr=False)
    _visible: MarketPanel = field(init=False, repr=False)
    _future: MarketPanel = field(init=False, repr=False)
    _visible_labels: np.ndarray = field(init=False, repr=False)
    _future_labels: np.ndarray = field(init=False, repr=False)
    _observation: dict = field(init=False, repr=False)

    def __post_init__(self) -> None:
        dates = self._panel.dates.astype("datetime64[D]")
        if dates[-1] > HARD_CAP:
            raise ValueError("financial study panel must be capped at 2024-12-31")
        assessment_start, assessment_end = _halfyear_bounds(self.year, self.half)
        previous_year, previous_half = (self.year - 1, 2) if self.half == 1 else (self.year, 1)
        feedback_start, feedback_end = _halfyear_bounds(previous_year, previous_half)
        if dates[0] > feedback_start + np.timedelta64(7, "D") or dates[-1] < assessment_end - np.timedelta64(7, "D"):
            raise ValueError("panel does not cover complete feedback and assessment half-years")
        feedback_left = int(np.searchsorted(dates, feedback_start))
        feedback_boundary = int(np.searchsorted(dates, feedback_end))
        assessment_left = int(np.searchsorted(dates, assessment_start))
        assessment_boundary = int(np.searchsorted(dates, assessment_end))
        feedback = (feedback_left, feedback_boundary - HORIZON)
        assessment = (assessment_left, assessment_boundary - HORIZON)
        if not 0 <= feedback[0] < feedback[1] < assessment[0] < assessment[1] < assessment_boundary:
            raise ValueError("insufficient rows after purging five-session labels")
        visible = _prefix_panel(self._panel, feedback_boundary)
        future = _prefix_panel(self._panel, assessment_boundary)
        object.__setattr__(self, "_feedback", feedback)
        object.__setattr__(self, "_assessment", assessment)
        object.__setattr__(self, "_feedback_boundary", feedback_boundary)
        object.__setattr__(self, "_assessment_boundary", assessment_boundary)
        object.__setattr__(self, "_visible", visible)
        object.__setattr__(self, "_future", future)
        object.__setattr__(self, "_visible_labels", forward_returns(visible, HORIZON))
        object.__setattr__(self, "_future_labels", forward_returns(future, HORIZON))
        evidence = []
        left, right = feedback
        edges = np.linspace(left, right, 4, dtype=int)
        for expression in PROBES:
            values = evaluate_expression(expression, visible)
            overall = _metrics(values, self._visible_labels, left, right)
            windows = [_metrics(values, self._visible_labels, int(a), int(b))
                       for a, b in pairwise(edges)]
            evidence.append({"expression": expression, "feedback": overall,
                             "feedback_usable": _usable(overall), "windows": windows})
        object.__setattr__(self, "_observation", {
            "supported_features": ["returns"], "max_lookback": 60, "horizon_sessions": HORIZON,
            "proposal_cost": PROPOSAL_COST, "probe_evidence": evidence,
        })

    def observation(self) -> dict:
        return copy.deepcopy(self._observation)

    @property
    def public_manifest(self) -> dict:
        def dates(interval):
            return [str(self._future.dates[index].astype("datetime64[D]"))
                    for index in (interval[0], interval[1] - 1)]

        split = next((name for name, years in SPLIT_YEARS.items() if self.year in years), "unspecified")
        return {"task_id": f"{self.year}-H{self.half}", "split": split,
                "year": self.year, "half": self.half, "feedback_signal_dates": dates(self._feedback),
                "assessment_signal_dates": dates(self._assessment), "horizon_sessions": HORIZON,
                "feedback_bounds_half_open": list(self._feedback),
                "assessment_bounds_half_open": list(self._assessment),
                "raw_feedback_bounds_half_open": [self._feedback[0], self._feedback_boundary],
                "raw_assessment_bounds_half_open": [self._assessment[0], self._assessment_boundary],
                "feedback_label_support_dates": dates(tuple(index + HORIZON for index in self._feedback)),
                "assessment_label_support_dates": dates(tuple(index + HORIZON for index in self._assessment)),
                "feedback_label_boundary": self._feedback_boundary,
                "assessment_label_boundary": self._assessment_boundary,
                "diagnostic_windows": "three contiguous signal windows; labels overlap internal edges"}

    def feedback_grid(self, expressions: tuple[str, ...] = FORMULA_GRID) -> list[dict]:
        """Offline training-teacher diagnostics; never merged into observation."""
        scores = []
        for expression in expressions:
            metrics = self.feedback_score(expression)
            scores.append({"expression": expression, "feedback": metrics, "usable": metrics["usable"]})
        return scores

    def feedback_score(self, expression: str) -> dict:
        """Visible-prefix-only teacher score; assessment is never consulted."""
        try:
            values = evaluate_expression(expression, self._visible)
            metrics = _metrics(values, self._visible_labels, *self._feedback)
            return metrics | {"usable": _usable(metrics)}
        except (ValueError, TypeError, ArithmeticError, RecursionError):
            return {"mean_ic": None, "n_dates": 0, "coverage": 0.0, "ic_std": None,
                    "n_signal_dates": self._feedback[1] - self._feedback[0], "usable": False}

    def evaluate(self, expression: str) -> dict:
        """Internal terminal training/evaluation outcome, never an observation."""
        result = {"expression": expression if isinstance(expression, str) else None,
                  "reward": INVALID_REWARD, "cost": PROPOSAL_COST, "status": "invalid",
                  "reason": "invalid_expression", "anchor_reuse": False, "orientation": None,
                  "feedback": None, "assessment": None, "oriented_future_ic": None,
                  "zero_feedback_tie": False}
        try:
            values = evaluate_expression(expression, self._visible)
            key = _expression_key(expression)
            result["anchor_reuse"] = any(key == _expression_key(probe) for probe in PROBES)
            feedback = _metrics(values, self._visible_labels, *self._feedback)
            result["feedback"] = feedback
            if not _usable(feedback):
                result["status"], result["reason"] = "unscorable", "insufficient_feedback_support"
                return result
            orientation = -1 if feedback["mean_ic"] < 0 else 1
            result["orientation"] = orientation
            result["zero_feedback_tie"] = feedback["mean_ic"] == 0
            future_values = evaluate_expression(expression, self._future)
            assessment = _metrics(future_values, self._future_labels, *self._assessment)
            result["assessment"] = assessment
            if not _usable(assessment):
                result["status"], result["reason"] = "unscorable", "insufficient_assessment_support"
                return result
            oriented_ic = assessment["mean_ic"] * orientation
            result.update(status="ok", reason=None, oriented_future_ic=oriented_ic,
                          reward=oriented_ic - PROPOSAL_COST)
        except (ValueError, TypeError, ArithmeticError, RecursionError):
            pass
        return result


def make_task(panel: MarketPanel, year: int, half: int) -> FinancialTask:
    return FinancialTask(panel, year, half)


def list_tasks(panel: MarketPanel, split: str = "train") -> list[FinancialTask]:
    return [make_task(panel, year, half) for year, half in task_periods(split)]


def feedback_teacher(task: FinancialTask, expressions: tuple[str, ...] = TEACHER_GRID) -> str | None:
    """Argmax absolute feedback IC only; ties use frozen grid order."""
    scores = [entry for entry in task.feedback_grid(expressions) if entry["usable"]]
    if not scores:
        return None
    return max(scores, key=lambda entry: abs(entry["feedback"]["mean_ic"]))["expression"]


def run_training_preflight(panel: MarketPanel) -> dict:
    """Training-only finite-grid feasibility; future oracle is unattainable.

    Never evaluates feasibility/transfer periods. Future oracle fixes orientation
    on feedback, then maximizes terminal reward using training future outcomes.
    Report contains aggregate scores only, not per-date returns or IC arrays.
    """
    tasks = list_tasks(panel, "train")
    formula_results = {expression: [] for expression in FORMULA_GRID}
    paired = []
    teacher_counts = Counter()
    probe_counts = Counter()
    probe_window_disagreements = 0
    for task in tasks:
        results = [task.evaluate(expression) for expression in FORMULA_GRID]
        for expression, result in zip(FORMULA_GRID, results, strict=True):
            formula_results[expression].append(result)
        greedy_expression = feedback_teacher(task, FORMULA_GRID)
        greedy = next((result for result in results if result["expression"] == greedy_expression), None)
        oracle = max(results, key=lambda result: result["reward"])
        teacher_label = feedback_teacher(task)
        teacher_counts[teacher_label if teacher_label is not None else "unscorable"] += 1
        probes = task.observation()["probe_evidence"]
        probe_winner = max(range(2), key=lambda i: abs(probes[i]["feedback"]["mean_ic"]))
        probe_counts[probes[probe_winner]["expression"]] += 1
        window_winners = [max(range(2), key=lambda i: abs(probes[i]["windows"][window]["mean_ic"] or 0))
                          for window in range(3)]
        probe_window_disagreements += any(winner != probe_winner for winner in window_winners)
        greedy_reward = greedy["reward"] if greedy else INVALID_REWARD
        paired.append({"year": task.year, "half": task.half, "feedback_greedy_expression": greedy_expression,
                       "feedback_greedy_reward": greedy_reward,
                       "future_oracle_expression": oracle["expression"], "future_oracle_reward": oracle["reward"],
                       "oracle_minus_greedy_reward": oracle["reward"] - greedy_reward,
                       "feedback_greedy_oriented_ic": greedy["oriented_future_ic"] if greedy else None,
                       "future_oracle_oriented_ic": oracle["oriented_future_ic"], "teacher_expression": teacher_label})

    def aggregate(rows):
        valid = [row for row in rows if row["status"] == "ok"]
        return {"mean_reward": float(np.mean([row["reward"] for row in rows])), "n_tasks": len(rows),
                "valid_tasks": len(valid), "invalid_or_unscorable_tasks": len(rows) - len(valid),
                "mean_oriented_future_ic_valid_tasks": float(np.mean([row["oriented_future_ic"] for row in valid]))
                if valid else None,
                "mean_raw_future_ic_valid_tasks": float(np.mean([row["assessment"]["mean_ic"] for row in valid]))
                if valid else None}

    provenance_keys = ("raw_file", "raw_sha256", "source_url", "details_url", "parser_version",
                       "selected_table", "retained_date_range", "attribution")
    aggregates = {expression: aggregate(rows) for expression, rows in formula_results.items()}
    uniform_reward = float(np.mean([row["mean_reward"] for row in aggregates.values()]))
    best_fixed_expression = max(FORMULA_GRID, key=lambda expression: aggregates[expression]["mean_reward"])
    return {"study": "financial-one-shot-return-formula-training-preflight-v1",
            "status": "training-only future-oracle feasibility; not achievable policy performance",
            "data_synthetic": panel.metadata.get("synthetic"),
            "provenance": {key: panel.metadata[key] for key in provenance_keys if key in panel.metadata},
            "horizon_sessions": HORIZON, "proposal_cost": PROPOSAL_COST, "invalid_reward": INVALID_REWARD,
            "formula_grid": list(FORMULA_GRID), "teacher_grid": list(TEACHER_GRID),
            "teacher_label_counts": dict(teacher_counts),
            "teacher_usable_tasks": len(tasks) - teacher_counts["unscorable"],
            "probe_absolute_feedback_winner_counts": dict(probe_counts),
            "probe_window_winner_disagreement_tasks": probe_window_disagreements,
            "formula_aggregates": aggregates,
            "paired_task_aggregates": paired,
            "summary": {"n_tasks": len(tasks),
                        "feedback_greedy_mean_reward": float(np.mean([row["feedback_greedy_reward"] for row in paired])),
                        "future_oracle_mean_reward": float(np.mean([row["future_oracle_reward"] for row in paired])),
                        "uniform_grid_expected_reward": uniform_reward,
                        "training_best_fixed_expression": best_fixed_expression,
                        "training_best_fixed_mean_reward": aggregates[best_fixed_expression]["mean_reward"],
                        "oracle_minus_greedy_mean_reward": float(np.mean([row["oracle_minus_greedy_reward"] for row in paired]))},
            "limitations": ["future oracle uses training future labels; unattainable upper-bound diagnostic",
                            "half-year task metrics are dependent; no significance claim",
                            "one-shot contextual-bandit proposal, not sequential agent research",
                            "no feasibility/transfer future metrics or post-2024 labels computed",
                            "no raw data redistribution or profitability claim"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    panel = load_french49(args.input, start="2000-01-01", end="2024-12-31")
    if panel.metadata["raw_sha256"] != EXPECTED_RAW_SHA256:
        raise ValueError("snapshot hash differs from the frozen financial study plan")
    report = run_training_preflight(panel)
    write_json(args.output, report)
    print(report["summary"], flush=True)


if __name__ == "__main__":
    main()
