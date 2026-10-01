"""CPU-only, training-period opportunity gate for acquiring late feedback.

The full-feature ridge policy is privileged: it sees every candidate's late
evidence. This gate measures an opportunity before any sequential policy run;
it does not establish that an agent can acquire or use that information.
"""

from __future__ import annotations

import argparse
import hashlib
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .artifacts import run_manifest, write_json
from .financial_tasks import EXPECTED_RAW_SHA256, FORMULA_GRID

RIDGE_ALPHA = 10.0
ROW_WEIGHT = 1.0 / 16
COST = .01
FAILURE_REWARD = -1.01
MIN_GAIN = .002
FOLDS = ((2002, 2009, 2010, 2013), (2002, 2013, 2014, 2017))
CHEAP_SCALARS = ("cheap_abs_ic", "cheap_orientation", "cheap_ic_std", "cheap_coverage",
                 "cheap_valid_fraction", "cheap_usable")
LATE_SCALARS = ("oriented_late_ic", "late_ic_std", "late_coverage", "late_valid_fraction", "late_usable")
CHEAP_FEATURES = (*CHEAP_SCALARS, *(f"{name}_missing" for name in CHEAP_SCALARS),
                  *(f"candidate_{index}" for index in range(16)))
FULL_FEATURES = (*CHEAP_FEATURES, *LATE_SCALARS, *(f"{name}_missing" for name in LATE_SCALARS))
METHODS = ("cheap_ridge", "all_late_ridge", "fixed_lag1", "cheap_abs_ic", "uniform_grid", "future_oracle")


def _number(value):
    if value is None:
        return None
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.number)):
        raise TypeError("metric must be numeric or missing")
    return float(value) if np.isfinite(value) else None


def _fraction(metrics):
    count, length = _number(metrics.get("n_dates")), _number(metrics.get("n_signal_dates"))
    return count / length if count is not None and length is not None and length > 0 else None


def _usable_value(metrics):
    value = metrics.get("usable")
    if value is None:
        return None
    if type(value) is not bool:
        raise ValueError("usable must be a boolean or missing")
    return float(value)


def _encode(values):
    return [0.0 if value is None else float(value) for value in values] + [
        float(value is None) for value in values]


def candidate_features(row: dict, include_late: bool = False) -> np.ndarray:
    """Declared 28/38 features; assessment and target fields are never read."""
    candidate = row["candidate_id"]
    if type(candidate) is not int or candidate not in range(16):
        raise ValueError("candidate_id must be an integer in 0..15")
    cheap = row["cheap"]
    mean = _number(cheap.get("mean_ic"))
    orientation = None if mean is None else (-1.0 if mean < 0 else 1.0)
    values = [None if mean is None else abs(mean), orientation, _number(cheap.get("ic_std")),
              _number(cheap.get("coverage")), _fraction(cheap), _usable_value(cheap)]
    features = _encode(values) + [float(candidate == index) for index in range(16)]
    if include_late:
        late = row["late"]
        late_mean = _number(late.get("mean_ic"))
        values = [None if late_mean is None or orientation is None else orientation * late_mean,
                  _number(late.get("ic_std")), _number(late.get("coverage")), _fraction(late),
                  _usable_value(late)]
        features.extend(_encode(values))
    return np.asarray(features, dtype=float)


@dataclass(frozen=True)
class WeightedRidge:
    mean: np.ndarray
    scale: np.ndarray
    coefficients: np.ndarray
    intercept: float
    n_training_rows: int

    def predict(self, features: np.ndarray) -> np.ndarray:
        features = np.asarray(features, dtype=float)
        if features.ndim != 2 or features.shape[1] != len(self.mean) or not np.isfinite(features).all():
            raise ValueError("prediction features must be finite and match fitted dimensions")
        return self.intercept + ((features - self.mean) / self.scale) @ self.coefficients

    def public_state(self) -> dict:
        return {"mean": self.mean.tolist(), "scale": self.scale.tolist(),
                "coefficients": self.coefficients.tolist(), "intercept": self.intercept,
                "n_training_rows": self.n_training_rows}


def fit_weighted_ridge(features: np.ndarray, targets: np.ndarray) -> WeightedRidge:
    """Minimize sum(row_weight * residual**2) + 10*||w||²; free intercept.

    Row weights stay 1/16, so each complete task has total weight one. They are
    never renormalized to make a growing number of tasks total weight one.
    """
    features, targets = np.asarray(features, dtype=float), np.asarray(targets, dtype=float)
    if (features.ndim != 2 or not len(features) or not features.shape[1]
            or targets.shape != (len(features),) or not np.isfinite(features).all()
            or not np.isfinite(targets).all()):
        raise ValueError("ridge requires nonempty finite features and matching targets")
    mean = np.mean(features, axis=0)
    scale = np.sqrt(np.mean((features - mean) ** 2, axis=0))
    scale[scale == 0] = 1.0
    standardized = (features - mean) / scale
    intercept = float(np.mean(targets))
    coefficients = np.linalg.solve(ROW_WEIGHT * standardized.T @ standardized
                                   + RIDGE_ALPHA * np.eye(features.shape[1]),
                                   ROW_WEIGHT * standardized.T @ (targets - intercept))
    return WeightedRidge(mean, scale, coefficients, intercept, len(features))


def _check_metrics(metrics):
    mean, coverage = _number(metrics.get("mean_ic")), _number(metrics.get("coverage"))
    count, length = metrics.get("n_dates"), metrics.get("n_signal_dates")
    if (type(count) is not int or type(length) is not int or length <= 0
            or not 0 <= count <= length or coverage is None or not 0 <= coverage <= 1
            or (mean is not None and not -1 <= mean <= 1)):
        raise ValueError("invalid metric counts, coverage or IC")
    usable = (mean is not None and coverage >= .8
              and count >= max(min(20, length), math.ceil(.8 * length)))
    if type(metrics.get("usable")) is not bool or metrics["usable"] != usable:
        raise ValueError("usable annotation disagrees with finite IC/support")
    return usable


def target_reward(row: dict) -> float:
    cheap_usable = _check_metrics(row["cheap"])
    assessment_usable = _check_metrics(row["assessment"])
    if not cheap_usable or not assessment_usable:
        return FAILURE_REWARD
    orientation = -1 if row["cheap"]["mean_ic"] < 0 else 1
    return orientation * row["assessment"]["mean_ic"] - COST


def _task_rows(rows):
    grouped = {}
    for row in rows:
        year, half, candidate = row["year"], row["half"], row["candidate_id"]
        if (type(year) is not int or year not in range(2002, 2018) or type(half) is not int
                or half not in (1, 2) or type(candidate) is not int or candidate not in range(16)):
            raise ValueError("gate accepts only the declared 2002–2017 training task/candidate grid")
        if row["task_id"] != f"{year}-H{half}" or row["expression"] != FORMULA_GRID[candidate]:
            raise ValueError("task/candidate identity does not match frozen grid")
        task = grouped.setdefault((year, half), {})
        if candidate in task:
            raise ValueError("duplicate task/candidate row")
        _check_metrics(row["late"])
        reward = target_reward(row)
        if "target_reward" in row and (not np.isfinite(row["target_reward"])
                                       or not math.isclose(row["target_reward"], reward, abs_tol=1e-12)):
            raise ValueError("target_reward annotation differs from cheap-oriented assessment reward")
        mean = _number(row["cheap"].get("mean_ic"))
        orientation = None if mean is None else (-1 if mean < 0 else 1)
        if "orientation" in row and row["orientation"] != orientation:
            raise ValueError("orientation annotation differs from cheap mean IC")
        task[candidate] = row
    expected = {(year, half) for year in range(2002, 2018) for half in (1, 2)}
    if set(grouped) != expected or any(set(task) != set(range(16)) for task in grouped.values()):
        raise ValueError("gate requires all32 training half-years and all16 candidate rows per task")
    return {key: [grouped[key][candidate] for candidate in range(16)] for key in sorted(grouped)}


def choose_candidate(rows: list[dict], scores: np.ndarray) -> int | None:
    """Only cheap-usable candidates; exact prediction ties use grid order."""
    scores = np.asarray(scores, dtype=float)
    if (len(rows) != 16 or [row["candidate_id"] for row in rows] != list(range(16))
            or scores.shape != (16,) or not np.isfinite(scores).all()):
        raise ValueError("candidate scores must be 16 finite values")
    eligible = [index for index, row in enumerate(rows) if row["cheap"]["usable"]]
    return max(eligible, key=lambda index: scores[index]) if eligible else None


def _selected(rows, candidate):
    reward = FAILURE_REWARD if candidate is None else target_reward(rows[candidate])
    failed = candidate is None or not (rows[candidate]["cheap"]["usable"]
                                       and rows[candidate]["assessment"]["usable"])
    return {"candidate_id": candidate,
            "expression": None if candidate is None else rows[candidate]["expression"],
            "reward": reward, "failure": failed, "failure_fraction": float(failed),
            "valid_ic_contribution": 0.0 if failed else reward + COST}


def _aggregate(tasks):
    means = {method: float(np.mean([task["choices"][method]["reward"] for task in tasks]))
             for method in METHODS}
    return {"n_tasks": len(tasks), "mean_reward": means,
            "failure_counts": {method: sum(task["choices"][method]["failure_fraction"] for task in tasks)
                               for method in METHODS},
            "failure_counts_definition": "failed tasks; uniform-grid value is expected failed tasks",
            "valid_fraction": {method: float(np.mean([1 - task["choices"][method]["failure_fraction"]
                                                       for task in tasks])) for method in METHODS},
            "valid_ic_contribution": {method: float(np.mean([task["choices"][method]["valid_ic_contribution"]
                                                              for task in tasks])) for method in METHODS},
            "all_late_minus_cheap": means["all_late_ridge"] - means["cheap_ridge"],
            "all_late_minus_fixed_lag1": means["all_late_ridge"] - means["fixed_lag1"]}


def run_opportunity_gate(rows: list[dict]) -> dict:
    """Two registered forward folds; no feasibility/transfer rows accepted."""
    grouped = _task_rows(rows)
    fold_reports, all_evaluated = [], []
    lag1 = FORMULA_GRID.index("delay(returns,1)")
    for index, (fit_first, fit_last, eval_first, eval_last) in enumerate(FOLDS):
        training = [row for key, task in grouped.items() if fit_first <= key[0] <= fit_last for row in task]
        targets = np.asarray([target_reward(row) for row in training])
        models = {name: fit_weighted_ridge(np.vstack([candidate_features(row, late) for row in training]), targets)
                  for name, late in (("cheap_ridge", False), ("all_late_ridge", True))}
        evaluated = []
        for (year, half), task in grouped.items():
            if not eval_first <= year <= eval_last:
                continue
            choices = {}
            for name, late in (("cheap_ridge", False), ("all_late_ridge", True)):
                scores = models[name].predict(np.vstack([candidate_features(row, late) for row in task]))
                choices[name] = _selected(task, choose_candidate(task, scores))
            cheap_scores = np.asarray([abs(row["cheap"]["mean_ic"])
                                       if row["cheap"]["mean_ic"] is not None else 0.0 for row in task])
            choices["cheap_abs_ic"] = _selected(task, choose_candidate(task, cheap_scores))
            choices["fixed_lag1"] = _selected(task, lag1)
            uniform = [_selected(task, candidate) for candidate in range(16)]
            choices["uniform_grid"] = {"candidate_id": None, "expression": None,
                                       "reward": float(np.mean([outcome["reward"] for outcome in uniform])),
                                       "failure_fraction": float(np.mean([outcome["failure_fraction"]
                                                                          for outcome in uniform])),
                                       "valid_ic_contribution": float(np.mean([outcome["valid_ic_contribution"]
                                                                              for outcome in uniform]))}
            oracle = max(range(16), key=lambda candidate: target_reward(task[candidate]))
            choices["future_oracle"] = _selected(task, oracle)
            evaluated.append({"task_id": f"{year}-H{half}", "year": year, "half": half, "choices": choices,
                              "all_late_minus_cheap": choices["all_late_ridge"]["reward"]
                              - choices["cheap_ridge"]["reward"],
                              "all_late_minus_fixed_lag1": choices["all_late_ridge"]["reward"]
                              - choices["fixed_lag1"]["reward"]})
        fold_reports.append({"fold": index + 1, "training_years": [fit_first, fit_last],
                             "evaluation_years": [eval_first, eval_last],
                             "models": {name: model.public_state() for name, model in models.items()},
                             "tasks": evaluated, **_aggregate(evaluated)})
        all_evaluated.extend(evaluated)
    pooled = _aggregate(all_evaluated)
    conditions = {"pooled_late_minus_cheap_gt_002": pooled["all_late_minus_cheap"] > MIN_GAIN,
                  "late_minus_cheap_positive_both_folds": all(fold["all_late_minus_cheap"] > 0
                                                              for fold in fold_reports),
                  "pooled_late_minus_fixed_lag1_positive": pooled["all_late_minus_fixed_lag1"] > 0}
    return {"study": "sequential-financial-opportunity-gate-v1", "gate_passed": all(conditions.values()),
            "conditions": conditions,
            "config": {"alpha": RIDGE_ALPHA, "row_weight": ROW_WEIGHT, "unpenalized_intercept": True,
                       "standardization": "training-only weighted population mean/std; zero std -> 1",
                       "missing": "impute scalar zero with separate flag before standardization",
                       "cheap_features": list(CHEAP_FEATURES), "full_features": list(FULL_FEATURES),
                       "candidate_grid": list(FORMULA_GRID), "task_weighting": "equal half-years; retain failures",
                       "target": "cheap-oriented assessment IC-.01 if cheap and assessment usable; else -1.01"},
            "folds": fold_reports, "pooled": pooled,
            "yearly": [{"year": year, **_aggregate([task for task in all_evaluated if task["year"] == year])}
                       for year in range(2010, 2018)],
            "limitations": ["training-period opportunity gate, not chronological transfer evidence",
                            "all-late ridge has privileged free access to every candidate's late evidence",
                            "future oracle is diagnostic only and never enters the gate",
                            "late failure does not change a selected candidate's target reward",
                            "no significance, agent adaptation, profitability or novel-factor claim"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/raw/french49-v1/49_Industry_Portfolios_daily_CSV.zip")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    sources = ("sequential_gate.py", "sequential_financial.py", "financial_tasks.py", "financial_policy.py",
               "data.py", "dsl.py", "evaluation.py", "french.py", "real_baselines.py")
    manifest = run_manifest({
        "study": "sequential-financial-opportunity-gate-v1", "cpu_only": True,
        "snapshot_sha256": EXPECTED_RAW_SHA256, "raw_file": Path(args.input).name,
        "alpha": RIDGE_ALPHA, "row_weight": ROW_WEIGHT, "unpenalized_intercept": True,
        "folds": [list(fold) for fold in FOLDS], "candidate_grid": list(FORMULA_GRID),
        "cheap_features": list(CHEAP_FEATURES), "full_features": list(FULL_FEATURES),
        "minimum_pooled_late_minus_cheap_exclusive": MIN_GAIN,
        "require_positive_each_fold": True, "require_positive_pooled_vs_fixed_lag1": True,
        "source_files_sha256": {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                                for name in sources},
        "manifest_capture": "entry before panel loading, task construction or scoring",
    })
    sidecar = args.output.with_suffix(".manifest.json")
    write_json(sidecar, manifest)
    from .financial_policy import load_pinned_panel
    from .sequential_financial import list_sequential_tasks
    panel = load_pinned_panel(args.input)
    tasks = list_sequential_tasks(panel, "train")
    manifest["config"]["task_manifests"] = [task.public_manifest for task in tasks]
    write_json(sidecar, manifest)
    rows = [row for task in tasks for row in task.diagnostic_rows()]
    report = run_opportunity_gate(rows)
    report["snapshot_sha256"] = panel.metadata["raw_sha256"]
    report["manifest"] = manifest
    write_json(args.output, report)
    print({"gate_passed": report["gate_passed"], "conditions": report["conditions"]}, flush=True)


if __name__ == "__main__":
    main()
