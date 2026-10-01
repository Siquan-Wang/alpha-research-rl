"""A finite-budget research process with feedback-only observations.

The assessment is exposed exactly once, as terminal *training* reward. This
environment must not be used to optimize a reported final holdout.
"""

import ast
import copy
import math
from collections.abc import Mapping
from itertools import pairwise
from numbers import Integral

import numpy as np

from .data import MarketPanel
from .dsl import MAX_LENGTH, evaluate_expression
from .evaluation import forward_returns, score_factor
from .protocol import ResearchSplit


def _finite_number(value):
    value = float(value)
    return value if math.isfinite(value) else None


def _metrics(scores):
    return {"mean_ic": _finite_number(scores["mean_ic"]),
            "n_dates": int(scores["n_dates"]),
            "coverage": _finite_number(scores["coverage"]),
            "ic_std": _finite_number(scores["ic_std"])}


def _rank_eligible(values, eligible):
    """Average-tie centered ranks, using only this date's eligible asset set."""
    result = np.full(values.shape, np.nan, dtype=float)
    for t in range(values.shape[0]):
        indices = np.flatnonzero(eligible[t])
        if len(indices) < 2:
            continue
        row = values[t, indices]
        order = np.argsort(row, kind="stable")
        sorted_values = row[order]
        ranks = np.empty(len(indices), dtype=float)
        left = 0
        while left < len(indices):
            right = left + 1
            while right < len(indices) and sorted_values[right] == sorted_values[left]:
                right += 1
            ranks[order[left:right]] = (left + right - 1) / 2
            left = right
        result[t, indices] = ranks / (len(indices) - 1) - 0.5
    return result


def combine_ranked_factors(factors, orientations):
    """Equal-weight causal ranks on assets finite for every submitted factor.

    Eligibility depends only on current factor values, never future labels.
    Complete-case eligibility preserves equal weights with missing observations.
    """
    if not factors or len(factors) != len(orientations):
        raise ValueError("factors and orientations must have matching nonzero lengths")
    arrays = [np.asarray(factor, dtype=float) for factor in factors]
    if any(array.ndim != 2 or array.shape != arrays[0].shape for array in arrays):
        raise ValueError("factor shapes must match")
    if any(orientation not in (-1, 1) for orientation in orientations):
        raise ValueError("orientations must be -1 or 1")
    eligible = np.logical_and.reduce([np.isfinite(array) for array in arrays])
    ranked = [_rank_eligible(array * orientation, eligible)
              for array, orientation in zip(arrays, orientations)]
    return np.mean(np.stack(ranked), axis=0)


class ResearchEnvironment:
    SCREEN_COST = 1
    STABILITY_COST = 2
    SELECT_COST = 1
    PROPOSAL_COST = 2
    MUTATION_COST = 2
    MAX_SELECTED = 3
    MIN_ASSESSMENT_COVERAGE = 0.8
    MIN_VALID_DATE_FRACTION = 0.8
    MIN_VALID_DATES = 20

    def __init__(self, panel: MarketPanel, split: ResearchSplit,
                 candidates: list[str], budget: int = 12,
                 budget_cost: float = 0.001, allow_generation: bool = False,
                 max_candidates: int = 64):
        if isinstance(budget, bool) or not isinstance(budget, Integral) or budget < 1:
            raise ValueError("budget must be a positive integer")
        if not math.isfinite(budget_cost) or budget_cost < 0:
            raise ValueError("budget_cost must be finite and nonnegative")
        if not isinstance(candidates, (list, tuple)) or any(not isinstance(x, str) for x in candidates):
            raise ValueError("candidates must be a sequence of expressions")
        if not isinstance(allow_generation, bool):
            raise TypeError("allow_generation must be a boolean")
        if isinstance(max_candidates, bool) or not isinstance(max_candidates, Integral) or not 1 <= max_candidates <= 64:
            raise ValueError("max_candidates must be an integer between 1 and 64")
        if allow_generation and len(candidates) > max_candidates:
            raise ValueError("initial candidates exceed max_candidates")
        split.validate_for_panel(len(panel.dates))
        self._panel = panel
        self._split = split
        self._initial_candidates = tuple(candidates)
        self._allow_generation = allow_generation
        self._max_candidates = int(max_candidates)
        self._initial_budget = int(budget)
        self._budget_cost = float(budget_cost)
        configured_features = panel.metadata.get("supported_features", ("close", "volume", "returns"))
        if not isinstance(configured_features, (list, tuple, set, frozenset)):
            raise TypeError("supported_features must be a collection of feature names")
        self._supported_features = [name for name in ("close", "volume", "returns") if name in configured_features]
        self._explicit_features = "supported_features" in panel.metadata
        # No hidden prices or errors can affect acquisition of visible evidence.
        visible_stop = split.feedback[1] + split.horizon
        self._visible_panel = MarketPanel(
            close=panel.close[:visible_stop].copy(),
            volume=panel.volume[:visible_stop].copy(),
            returns=panel.returns[:visible_stop].copy(),
            dates=panel.dates[:visible_stop].copy(), assets=tuple(panel.assets),
            metadata={"supported_features": self._supported_features.copy()})
        self._visible_labels = forward_returns(self._visible_panel, split.horizon)
        self.reset()

    def reset(self) -> dict:
        self._candidates = list(self._initial_candidates)
        self._provenance = {str(i): {"kind": "initial", "parent": None}
                            for i in range(len(self._candidates))}
        self._budget = self._initial_budget
        self._done = False
        self._evidence = {}
        self._orientation = {}
        self._selected = []
        self._history = []
        self._visible_values = {}
        self._screened_expressions = set()
        self._stability_expressions = set()
        return self._observation()

    def _observation(self):
        observation = {
            "budget": self._budget, "initial_budget": self._initial_budget,
            "spent_budget": self._initial_budget - self._budget, "done": self._done,
            "candidates": [{"id": i, "expression": expression}
                           for i, expression in enumerate(self._candidates)],
            "evidence": self._evidence, "selected": self._selected,
            "orientation": self._orientation, "history": self._history}
        if self._allow_generation:
            observation["generation"] = {"enabled": True, "max_candidates": self._max_candidates,
                                         "proposal_cost": self.PROPOSAL_COST, "mutation_cost": self.MUTATION_COST}
            observation["provenance"] = self._provenance
        if self._allow_generation or self._explicit_features:
            observation["supported_features"] = self._supported_features
        return copy.deepcopy(observation)

    def _usable_scores(self, scores, block_length):
        mean_ic = scores["mean_ic"]
        coverage = scores["coverage"]
        required_dates = max(math.ceil(self.MIN_VALID_DATE_FRACTION * block_length),
                             min(self.MIN_VALID_DATES, block_length))
        return (mean_ic is not None and math.isfinite(mean_ic)
                and coverage is not None and coverage >= self.MIN_ASSESSMENT_COVERAGE
                and scores["n_dates"] >= required_dates)

    @staticmethod
    def _expression_key(expression):
        try:
            return ast.dump(ast.parse(expression.strip(), mode="eval"), include_attributes=False)
        except (SyntaxError, ValueError, RecursionError):
            return expression.strip()

    def _key(self, candidate):
        return self._expression_key(self._candidates[candidate])

    def _propose(self, name, expression, parent):
        if not self._allow_generation:
            return "invalid", "generation_disabled", None
        if not isinstance(expression, str) or not expression.strip() or len(expression) > MAX_LENGTH:
            return "invalid", "invalid_expression", None
        if len(self._candidates) >= self._max_candidates:
            return "invalid", "candidate_limit", None
        expression = expression.strip()
        try:
            # The DSL validates AST depth/size, names and lookbacks before
            # interpreting anything. This panel contains no assessment rows.
            values = evaluate_expression(expression, self._visible_panel)
        except (ValueError, TypeError, ArithmeticError, RecursionError):
            return "invalid", "invalid_expression", None
        key = self._expression_key(expression)
        if any(key == self._key(i) for i in range(len(self._candidates))):
            return "duplicate", "duplicate_expression", None
        candidate = len(self._candidates)
        self._candidates.append(expression)
        self._visible_values[candidate] = values
        self._provenance[str(candidate)] = {"kind": name, "parent": parent}
        return "ok", None, candidate

    def _values(self, candidate):
        if candidate not in self._visible_values:
            self._visible_values[candidate] = evaluate_expression(
                self._candidates[candidate], self._visible_panel)
        return self._visible_values[candidate]

    def _acquire(self, action, candidate):
        key = self._key(candidate)
        entry = self._evidence.setdefault(str(candidate), {})
        if action == "select":
            if "screen" not in entry:
                return "invalid", "screen_required"
            if not self._usable_scores(entry["screen"], self._split.feedback[1] - self._split.feedback[0]):
                return "invalid", "usable_screen_required"
            if candidate in self._selected:
                return "duplicate", "already_selected"
            if len(self._selected) >= self.MAX_SELECTED:
                return "invalid", "selection_limit"
            self._selected.append(candidate)
            return "ok", None
        acquired = self._screened_expressions if action == "screen" else self._stability_expressions
        if key in acquired:
            return "duplicate", "already_acquired"
        try:
            values = self._values(candidate)
            start, stop = self._split.feedback
            if action == "screen":
                evidence = _metrics(score_factor(values, self._visible_labels, start, stop))
                entry["screen"] = evidence
                mean_ic = evidence["mean_ic"]
                self._orientation[str(candidate)] = -1 if mean_ic is not None and mean_ic < 0 else 1
            else:
                edges = np.linspace(start, stop, min(3, stop - start) + 1, dtype=int)
                windows = [{"start": int(left), "stop": int(right),
                            **_metrics(score_factor(values, self._visible_labels, int(left), int(right)))}
                           for left, right in pairwise(edges)]
                entry["stability"] = {"windows": windows}
            acquired.add(key)
            return "ok", None
        except (ValueError, TypeError, ArithmeticError, RecursionError):
            # Do not expose raw exception strings, arrays, or hidden evaluation errors.
            return "invalid", "invalid_expression"

    def _terminal_reward(self):
        predictive_score = 0.0
        if self._selected:
            try:
                factors = [evaluate_expression(self._candidates[i], self._panel) for i in self._selected]
                composite = combine_ranked_factors(factors, [self._orientation[str(i)] for i in self._selected])
                result = score_factor(composite, forward_returns(self._panel, self._split.horizon),
                                      *self._split.assessment)
                score = float(result["mean_ic"])
                if self._usable_scores(result, self._split.assessment[1] - self._split.assessment[0]):
                    predictive_score = score
            except (ValueError, TypeError, ArithmeticError, RecursionError):
                pass
        return predictive_score - self._budget_cost * (self._initial_budget - self._budget)

    def step(self, action):
        if self._done:
            raise RuntimeError("episode already finished; reset before stepping")
        valid_mapping = isinstance(action, Mapping)
        name = action.get("action") if valid_mapping else None
        candidate = action.get("candidate") if valid_mapping else None
        generating = isinstance(name, str) and name in ("propose", "mutate")
        allowed_fields = {"action", "expression"} if name == "propose" else (
            {"action", "candidate", "expression"} if name == "mutate" else {"action", "candidate"})
        valid_shape = valid_mapping and set(action).issubset(allowed_fields)
        is_stop = valid_shape and name == "stop"
        requested_cost = {"screen": self.SCREEN_COST, "stability": self.STABILITY_COST,
                          "select": self.SELECT_COST, "propose": self.PROPOSAL_COST,
                          "mutate": self.MUTATION_COST}.get(name, 1) if isinstance(name, str) else 1
        cost = 0 if is_stop else min(requested_cost, self._budget)
        self._budget -= cost
        status, reason = "ok", None
        candidate_valid = (not isinstance(candidate, bool) and isinstance(candidate, Integral)
                           and 0 <= candidate < len(self._candidates))
        parent = int(candidate) if generating and candidate_valid else None
        proposed = None
        if not is_stop:
            if not valid_shape or name not in ("screen", "stability", "select", "propose", "mutate"):
                status, reason = "invalid", "invalid_action"
            elif name != "propose" and not candidate_valid:
                status, reason = "invalid", "invalid_candidate"
            elif cost < requested_cost:
                status, reason = "invalid", "insufficient_budget"
            elif generating:
                status, reason, proposed = self._propose(name, action.get("expression"), parent)
            else:
                status, reason = self._acquire(name, int(candidate))
        record = {"action": name if isinstance(name, str) and name in (
                      "screen", "stability", "select", "stop", "propose", "mutate") else "invalid",
                  "candidate": proposed if generating else (int(candidate) if candidate_valid else None),
                  "cost": cost, "status": status, "reason": reason}
        if generating:
            expression = action.get("expression")
            record["expression"] = expression.strip() if isinstance(expression, str) and len(expression) <= MAX_LENGTH else None
            record["parent"] = parent
        self._history.append(record)
        self._done = is_stop or self._budget == 0
        reward = self._terminal_reward() if self._done else 0.0
        return self._observation(), reward, self._done, {"status": status, "reason": reason}
