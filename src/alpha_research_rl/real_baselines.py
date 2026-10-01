"""Frozen numerical industry-return baselines; development assessment only.

Run: python -m alpha_research_rl.real_baselines --input <official.zip> --output <summary.json>
The output contains aggregates only, never raw returns, model weights or predictions.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .data import MarketPanel
from .dsl import evaluate_expression
from .evaluation import forward_returns, score_factor
from .french import load_french49

HORIZON = 5
RIDGE_ALPHA = 1.0
BOOTSTRAP_SEED = 1729
BOOTSTRAP_BLOCK = 20
BOOTSTRAP_REPLICATES = 2000
EXPECTED_RAW_SHA256 = "8f394fe34bea54d41b9aafed410425ee8f8e252ede3c71a7c1cd20bab83040de"
FEATURE_EXPRESSIONS = (
    "returns", "delay(returns,1)", "delay(returns,2)", "delay(returns,5)",
    "ts_mean(returns,5)", "ts_std(returns,5)",
    "ts_mean(returns,20)", "ts_std(returns,20)",
    "ts_mean(returns,60)", "ts_std(returns,60)",
)
COMPARATORS = {"momentum20": "ts_mean(returns,20)", "reversal20": "neg(ts_mean(returns,20))"}


def build_features(panel: MarketPanel) -> np.ndarray:
    """Ten fixed, causal features; [date, industry, feature]."""
    return np.stack([evaluate_expression(expression, panel) for expression in FEATURE_EXPRESSIONS], axis=-1)


@dataclass
class RidgeModel:
    mean: np.ndarray
    scale: np.ndarray
    coefficients: np.ndarray
    intercept: float
    n_training_samples: int

    def predict(self, features: np.ndarray) -> np.ndarray:
        if features.ndim != 3 or features.shape[-1] != len(self.coefficients):
            raise ValueError("features must be a matching [time,asset,feature] cube")
        result = np.full(features.shape[:2], np.nan)
        eligible = np.isfinite(features).all(axis=-1)
        standardized = (features[eligible] - self.mean) / self.scale
        result[eligible] = self.intercept + standardized @ self.coefficients
        return result


def fit_ridge(features: np.ndarray, labels: np.ndarray, start: int, stop: int,
              alpha: float = RIDGE_ALPHA) -> RidgeModel:
    """Fit only start:stop complete-case samples; summed squared-error penalty.

    All feature scaling, target centering and coefficients use training samples.
    Callers supply label-purged signal bounds. The intercept is unpenalized.
    """
    if features.ndim != 3 or labels.shape != features.shape[:2] or features.shape[-1] < 1:
        raise ValueError("feature cube and labels have incompatible shapes")
    if not 0 <= start < stop <= len(features) or not np.isfinite(alpha) or alpha <= 0:
        raise ValueError("invalid fit interval or alpha")
    train_x, train_y = features[start:stop], labels[start:stop]
    eligible = np.isfinite(train_x).all(axis=-1) & np.isfinite(train_y)
    x, y = train_x[eligible], train_y[eligible]
    if len(y) < 2:
        raise ValueError("not enough complete training samples")
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale == 0] = 1.0
    standardized = (x - mean) / scale
    target_mean = float(y.mean())
    coefficients = np.linalg.solve(standardized.T @ standardized + alpha * np.eye(x.shape[1]),
                                   standardized.T @ (y - target_mean))
    return RidgeModel(mean, scale, coefficients, target_mean, len(y))


def calendar_split(dates: np.ndarray, year: int, horizon: int = HORIZON) -> dict:
    """Five prior calendar years fit; purge labels reaching next period."""
    if type(year) is not int or type(horizon) is not int or horizon < 1:
        raise ValueError("year and positive horizon must be integers")
    dates = np.asarray(dates, dtype="datetime64[D]")
    if dates.ndim != 1 or np.isnat(dates).any() or (np.diff(dates) <= np.timedelta64(0, "D")).any():
        raise ValueError("dates must be unique and increasing")
    fit_start_date = np.datetime64(f"{year - 5:04d}-01-01")
    assessment_start_date = np.datetime64(f"{year:04d}-01-01")
    assessment_end_date = np.datetime64(f"{year + 1:04d}-01-01")
    fit_start = int(np.searchsorted(dates, fit_start_date))
    assessment_start = int(np.searchsorted(dates, assessment_start_date))
    assessment_end = int(np.searchsorted(dates, assessment_end_date))
    fit_stop = assessment_start - horizon
    assessment_stop = assessment_end - horizon
    if not 0 <= fit_start < fit_stop < assessment_start < assessment_stop <= len(dates):
        raise ValueError("insufficient dates for five-year fit and purged assessment year")
    if len(dates) == 0 or dates[0] > fit_start_date + np.timedelta64(7, "D"):
        raise ValueError("panel does not cover the five-year training interval")
    if dates[-1] < assessment_end_date - np.timedelta64(7, "D"):
        raise ValueError("panel does not cover the assessment year")
    return {"year": year, "fit": (fit_start, fit_stop), "assessment": (assessment_start, assessment_stop),
            "fit_label_boundary": assessment_start, "assessment_label_boundary": assessment_end,
            "horizon": horizon}


def block_bootstrap_mean_ci(blocks: list[np.ndarray], block_length: int = BOOTSTRAP_BLOCK,
                           n_bootstrap: int = BOOTSTRAP_REPLICATES, seed: int = BOOTSTRAP_SEED) -> dict:
    """Circular moving blocks sampled within original yearly time blocks."""
    if type(block_length) is not int or block_length < 1 or type(n_bootstrap) is not int or n_bootstrap < 2:
        raise ValueError("positive integer block length and at least two replicates required")
    blocks = [np.asarray(block, dtype=float) for block in blocks]
    if not blocks or any(block.ndim != 1 or not len(block) or not np.isfinite(block).all() for block in blocks):
        raise ValueError("bootstrap requires nonempty finite one-dimensional yearly IC arrays")
    rng = np.random.default_rng(seed)
    bootstrap_sums = np.zeros(n_bootstrap)
    total = sum(len(block) for block in blocks)
    for block in blocks:
        n = len(block)
        starts = rng.integers(0, n, size=(n_bootstrap, int(np.ceil(n / block_length))))
        indices = (starts[..., None] + np.arange(block_length)) % n
        bootstrap_sums += block[indices.reshape(n_bootstrap, -1)[:, :n]].sum(axis=1)
    replicates = bootstrap_sums / total
    interval = np.quantile(replicates, [0.025, 0.975])
    return {"method": "circular moving blocks separately within calendar-year assessment blocks",
            "block_length": block_length, "replicates": n_bootstrap, "seed": seed,
            "confidence_level": 0.95, "lower": float(interval[0]), "upper": float(interval[1]),
            "n_dates": total}


def _public_metrics(metrics: dict) -> dict:
    return {key: value if not isinstance(value, float) or np.isfinite(value) else None
            for key, value in metrics.items() if key != "daily_ic"}


def run_fixed_baselines(panel: MarketPanel, years: tuple[int, ...] = (2020, 2021, 2022, 2023, 2024),
                        bootstrap_replicates: int = BOOTSTRAP_REPLICATES) -> dict:
    """Evaluate the prewritten development plan; return public aggregates only."""
    if not years or len(set(years)) != len(years) or tuple(sorted(years)) != years:
        raise ValueError("assessment years must be nonempty, unique and ordered")
    features = build_features(panel)
    labels = forward_returns(panel, HORIZON)
    comparator_values = {name: evaluate_expression(expression, panel) for name, expression in COMPARATORS.items()}
    annual = []
    per_method = {name: [] for name in ("ridge", *COMPARATORS)}
    paired_cells = dict.fromkeys(per_method, 0.0)
    total_cells = dict.fromkeys(per_method, 0)
    for year in years:
        split = calendar_split(panel.dates, year)
        fit_start, fit_stop = split["fit"]
        start, stop = split["assessment"]
        model = fit_ridge(features, labels, fit_start, fit_stop)
        predictions = {"ridge": model.predict(features[start:stop]),
                       **{name: values[start:stop] for name, values in comparator_values.items()}}
        year_result = {
            "year": year, "fit_signal_dates": [str(panel.dates[fit_start].astype("datetime64[D]")),
                                                str(panel.dates[fit_stop - 1].astype("datetime64[D]"))],
            "assessment_signal_dates": [str(panel.dates[start].astype("datetime64[D]")),
                                         str(panel.dates[stop - 1].astype("datetime64[D]"))],
            "fit_indices_half_open": [fit_start, fit_stop], "assessment_indices_half_open": [start, stop],
            "training_samples": model.n_training_samples, "scores": {},
        }
        for name, values in predictions.items():
            metrics = score_factor(values, labels[start:stop], 0, stop - start)
            year_result["scores"][name] = _public_metrics(metrics)
            daily = np.array([ic for ic in metrics["daily_ic"] if ic is not None])
            if not len(daily):
                raise ValueError(f"no valid daily IC for {name} in {year}")
            if len(daily) != stop - start:
                raise ValueError("bootstrap requires consecutive complete IC dates; do not compress missing dates")
            per_method[name].append(daily)
            cells = (stop - start) * len(panel.assets)
            paired_cells[name] += metrics["coverage"] * cells
            total_cells[name] += cells
        annual.append(year_result)
    pooled = {}
    for name, blocks in per_method.items():
        daily = np.concatenate(blocks)
        pooled[name] = {"mean_ic": float(daily.mean()), "ic_std": float(daily.std(ddof=1)),
                        "n_dates": len(daily), "coverage": paired_cells[name] / total_cells[name],
                        "mean_ic_block_bootstrap_ci": block_bootstrap_mean_ci(
                            blocks, n_bootstrap=bootstrap_replicates)}
    safe_keys = ("source", "source_url", "details_url", "raw_file", "raw_sha256", "raw_bytes",
                 "archive_member", "parser_version", "selected_table", "retained_date_range",
                 "price_semantics", "supported_features", "source_missing_cells", "retained_missing_cells",
                 "wealth_base_date", "wealth_base_value", "first_retained_return", "vintage", "attribution")
    return {"study": "french49-fixed-baselines-development-v1", "status": "development only",
            "provenance": {key: panel.metadata[key] for key in safe_keys if key in panel.metadata},
            "synthetic": panel.metadata.get("synthetic"), "assets": list(panel.assets),
            "horizon_sessions": HORIZON, "ridge_alpha": RIDGE_ALPHA,
            "feature_expressions": list(FEATURE_EXPRESSIONS), "fixed_comparators": COMPARATORS,
            "training_protocol": "pooled industry samples; prior five calendar years; train-only scaling; "
            "purged labels; fixed alpha; no adaptive feedback", "yearly": annual, "pooled": pooled,
            "limitations": ["descriptive industry-portfolio forecasting; no stock-level alpha claim",
                            "no transaction costs, execution, portfolio returns, Sharpe or PnL",
                            "bootstrap describes short-range dependence; no guaranteed error control",
                            "development inspection; not final holdout or evidence of LLM post-training"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    panel = load_french49(args.input, start="2000-01-01", end="2024-12-31")
    if panel.metadata["raw_sha256"] != EXPECTED_RAW_SHA256:
        raise ValueError("snapshot hash differs from the prewritten development plan")
    results = run_fixed_baselines(panel)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": args.output.name, "pooled": results["pooled"]}, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
