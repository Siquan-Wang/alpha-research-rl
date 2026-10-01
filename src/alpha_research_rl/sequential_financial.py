"""Causal fixed-bank financial tasks and exactly-two-check action environment.

The train-only privileged row API is separate from actor observations. This
module neither fits a controller nor claims that a language model is trained.
"""

from __future__ import annotations

import copy
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from numbers import Integral

import numpy as np

from .data import MarketPanel
from .dsl import MAX_LENGTH, evaluate_expression
from .evaluation import forward_returns, score_factor
from .financial_policy import expression_key
from .financial_tasks import (
    GRID,
    HARD_CAP,
    HORIZON,
    INVALID_REWARD,
    PROPOSAL_COST,
    _halfyear_bounds,
    _prefix_panel,
    task_periods,
)


def _summary(values, labels, bounds) -> dict:
    start, stop = bounds
    raw = score_factor(values, labels, start, stop)
    mean = float(raw["mean_ic"]) if np.isfinite(raw["mean_ic"]) else None
    std = float(raw["ic_std"]) if np.isfinite(raw["ic_std"]) else None
    length = stop - start
    usable = (mean is not None and raw["coverage"] >= 0.8
              and raw["n_dates"] >= max(min(20, length), math.ceil(0.8 * length)))
    return {"mean_ic": mean, "ic_std": std, "coverage": raw["coverage"], "n_dates": raw["n_dates"],
            "n_signal_dates": length, "usable": bool(usable), "reason": None if usable else "insufficient_support"}


@dataclass(frozen=True)
class SequentialFinancialTask:
    _panel: MarketPanel = field(repr=False)
    year: int
    half: int
    candidates: tuple[str | None, ...] = GRID
    _bounds: dict = field(init=False, repr=False)
    _panels: dict = field(init=False, repr=False)
    _labels: dict = field(init=False, repr=False)
    _score_cache: dict = field(init=False, repr=False)

    def __post_init__(self):
        dates = self._panel.dates.astype("datetime64[D]")
        if dates[-1] > HARD_CAP:
            raise ValueError("sequential panel must be capped at 2024-12-31")
        if not isinstance(self.candidates, (tuple, list)) or not 2 <= len(self.candidates) <= 64:
            raise ValueError("a bank must contain two to 64 candidate slots")
        if any(expression is not None and (not isinstance(expression, str) or len(expression) > MAX_LENGTH)
               for expression in self.candidates):
            raise ValueError("candidate slots must contain bounded expressions or explicit invalid None slots")
        object.__setattr__(self, "candidates", tuple(self.candidates))
        c_start, c_end = _halfyear_bounds(self.year, self.half)
        previous = (self.year - 1, 2) if self.half == 1 else (self.year, 1)
        b_start, b_end = _halfyear_bounds(*previous)
        if dates[0] > b_start + np.timedelta64(7, "D") or dates[-1] < c_end - np.timedelta64(7, "D"):
            raise ValueError("panel does not cover complete evidence and assessment half-years")
        left = int(np.searchsorted(dates, b_start))
        right = int(np.searchsorted(dates, b_end))
        c_left = int(np.searchsorted(dates, c_start))
        c_right = int(np.searchsorted(dates, c_end))
        middle = left + 2 * (right - left) // 3
        bounds = {"cheap": (left, middle - HORIZON), "late": (middle, right - HORIZON),
                  "assessment": (c_left, c_right - HORIZON), "raw_feedback": (left, right),
                  "raw_assessment": (c_left, c_right), "cheap_boundary": middle,
                  "late_boundary": right, "assessment_boundary": c_right}
        if right != c_left or any(bounds[name][1] - bounds[name][0] < 20 for name in ("cheap", "late", "assessment")):
            raise ValueError("not enough independently purged rows for evidence and assessment")
        panels = {"cheap": _prefix_panel(self._panel, middle), "late": _prefix_panel(self._panel, right)}
        object.__setattr__(self, "_bounds", bounds)
        object.__setattr__(self, "_panels", panels)
        object.__setattr__(self, "_labels", {name: forward_returns(panel, HORIZON) for name, panel in panels.items()})
        object.__setattr__(self, "_score_cache", {})

    def _candidate(self, candidate_id):
        if isinstance(candidate_id, bool) or not isinstance(candidate_id, Integral) or not 0 <= candidate_id < len(self.candidates):
            raise ValueError("invalid candidate ID")
        return int(candidate_id)

    def _score(self, phase: str, candidate_id: int) -> dict:
        candidate_id = self._candidate(candidate_id)
        expression = self.candidates[candidate_id]
        key = phase, expression_key(expression) if expression is not None else None
        if key not in self._score_cache:
            length = self._bounds[phase][1] - self._bounds[phase][0]
            result = {"mean_ic": None, "ic_std": None, "coverage": 0.0, "n_dates": 0,
                      "n_signal_dates": length, "usable": False, "reason": "invalid_expression"}
            try:
                if phase not in self._panels:
                    self._panels[phase] = _prefix_panel(self._panel, self._bounds[phase + "_boundary"])
                    self._labels[phase] = forward_returns(self._panels[phase], HORIZON)
                values = evaluate_expression(expression, self._panels[phase])
                result = _summary(values, self._labels[phase], self._bounds[phase])
            except (ValueError, TypeError, ArithmeticError, RecursionError):
                pass
            self._score_cache[key] = result
        return copy.deepcopy(self._score_cache[key])

    def cheap_score(self, candidate_id: int) -> dict:
        return self._score("cheap", candidate_id)

    def orientation(self, candidate_id: int) -> int | None:
        mean = self.cheap_score(candidate_id)["mean_ic"]
        return None if mean is None else -1 if mean < 0 else 1

    def late_score(self, candidate_id: int) -> dict:
        metrics = self._score("late", candidate_id)
        orientation = self.orientation(candidate_id)
        metrics["oriented_mean_ic"] = metrics["mean_ic"] * orientation if metrics["mean_ic"] is not None and orientation else None
        return metrics

    def assessment_score(self, candidate_id: int) -> dict:
        return self._score("assessment", candidate_id)

    def terminal_result(self, candidate_id: int) -> dict:
        """Private scorer; later evidence does not affect sign or eligibility."""
        candidate_id = self._candidate(candidate_id)
        cheap = self.cheap_score(candidate_id)
        future = self.assessment_score(candidate_id)
        orientation = self.orientation(candidate_id)
        valid = cheap["usable"] and future["usable"]
        ic = orientation * future["mean_ic"] if valid else None
        return {"candidate_id": candidate_id, "expression": self.candidates[candidate_id],
                "status": "ok" if valid else "unscorable",
                "reason": None if valid else "unusable_cheap_or_assessment",
                "orientation": orientation, "cheap": cheap, "assessment": future,
                "oriented_future_ic": ic, "cost": PROPOSAL_COST,
                "reward": ic - PROPOSAL_COST if valid else INVALID_REWARD}

    def cheap_rows(self) -> list[dict]:
        return [{"candidate_id": index, "expression": expression, "cheap": self.cheap_score(index),
                 "orientation": self.orientation(index)} for index, expression in enumerate(self.candidates)]

    def diagnostic_rows(self) -> list[dict]:
        """Privileged training-only gate rows; never deliver to the actor."""
        if (self.year, self.half) not in task_periods("train"):
            raise ValueError("privileged grid diagnostic is restricted to 2002-2017 training tasks")
        rows = []
        for index in range(len(self.candidates)):
            result = self.terminal_result(index)
            rows.append({"task_id": f"{self.year}-H{self.half}", "year": self.year, "half": self.half,
                         "candidate_id": index, "expression": self.candidates[index], "cheap": result["cheap"],
                         "orientation": result["orientation"], "late": self.late_score(index),
                         "assessment": result["assessment"], "target_reward": result["reward"],
                         "oriented_future_ic": result["oriented_future_ic"], "status": result["status"]})
        return rows

    @property
    def public_manifest(self) -> dict:
        result = {"task_id": f"{self.year}-H{self.half}", "year": self.year, "half": self.half,
                  "horizon_sessions": HORIZON, "candidate_slots": len(self.candidates), "fixed_cost": PROPOSAL_COST,
                  "common_cheap_screens": len(self.candidates)}
        for phase in ("cheap", "late", "assessment"):
            start, stop = self._bounds[phase]
            result[phase + "_bounds_half_open"] = [start, stop]
            result[phase + "_label_boundary"] = self._bounds[phase + "_boundary"]
            result[phase + "_signal_dates"] = [str(self._panel.dates[i].astype("datetime64[D]")) for i in (start, stop - 1)]
            result[phase + "_label_support_dates"] = [str(self._panel.dates[i + HORIZON].astype("datetime64[D]"))
                                                      for i in (start, stop - 1)]
        result["raw_feedback_bounds_half_open"] = list(self._bounds["raw_feedback"])
        result["raw_assessment_bounds_half_open"] = list(self._bounds["raw_assessment"])
        return result


def make_sequential_task(panel: MarketPanel, year: int, half: int,
                         candidates: tuple[str | None, ...] = GRID) -> SequentialFinancialTask:
    return SequentialFinancialTask(panel, year, half, candidates)


def list_sequential_tasks(panel: MarketPanel, split: str = "train") -> list[SequentialFinancialTask]:
    return [make_sequential_task(panel, year, half) for year, half in task_periods(split)]


class SequentialFinancialEnvironment:
    """Maximum three attempts: check, distinct check, select; any invalid ends."""

    def __init__(self, task: SequentialFinancialTask):
        self._task = task
        self.reset()

    def reset(self) -> dict:
        self._checked = []
        self._late_evidence = {}
        self._history = []
        self._selected = None
        self._done = False
        return self.observation()

    def observation(self) -> dict:
        return copy.deepcopy({"supported_features": ["returns"], "horizon_sessions": HORIZON,
                              "fixed_total_cost": PROPOSAL_COST, "initial_budget": 3,
                              "budget": 0 if self._done else 3 - len(self._history),
                              "phase": "done" if self._done else "check" if len(self._checked) < 2 else "select",
                              "candidates": self._task.cheap_rows(), "checked_ids": self._checked,
                              "late_evidence": self._late_evidence, "selected": self._selected,
                              "history": self._history, "done": self._done})

    def step(self, action) -> tuple[dict, float, bool, dict]:
        if self._done:
            raise RuntimeError("episode finished; reset before stepping")
        phase = "check" if len(self._checked) < 2 else "select"
        shape_ok = isinstance(action, Mapping) and set(action) == {"action", "candidate"}
        candidate = action.get("candidate") if isinstance(action, Mapping) else None
        name = action.get("action") if isinstance(action, Mapping) else None
        status, reason, redundant = "ok", None, False
        try:
            index = self._task._candidate(candidate)
        except ValueError:
            index = None
        if not shape_ok or not isinstance(name, str) or name != phase:
            status, reason = "invalid", "invalid_or_out_of_phase_action"
        elif index is None:
            status, reason = "invalid", "invalid_candidate"
        elif phase == "check" and index in self._checked:
            status, reason = "duplicate", "duplicate_candidate_check"
        elif phase == "select" and not self._task.cheap_score(index)["usable"]:
            status, reason = "invalid", "unusable_cheap_selection"
        reward = 0.0
        if status != "ok":
            self._done, reward = True, INVALID_REWARD
        elif phase == "check":
            key = expression_key(self._task.candidates[index])
            redundant = any(key == expression_key(self._task.candidates[old]) for old in self._checked)
            self._checked.append(index)
            self._late_evidence[str(index)] = self._task.late_score(index)
        else:
            self._selected, self._done = index, True
            reward = self._task.terminal_result(index)["reward"]
        self._history.append({"action": name if isinstance(name, str) else "invalid",
                              "candidate": index, "status": status, "reason": reason,
                              "redundant_formula_evidence": redundant, "slot": len(self._history)})
        return self.observation(), reward, self._done, {"status": status, "reason": reason}
