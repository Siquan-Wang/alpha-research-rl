"""Signal-date-aligned forward labels and descriptive cross-sectional IC."""

from __future__ import annotations

import numpy as np
from scipy.stats import rankdata

from .data import MarketPanel


def forward_returns(panel: MarketPanel, horizon: int = 5) -> np.ndarray:
    """close[t+h]/close[t]-1; the last h signal rows have unavailable labels."""
    if isinstance(horizon, bool) or not isinstance(horizon, int) or horizon < 1:
        raise ValueError("horizon must be a positive integer")
    labels = np.full(panel.close.shape, np.nan)
    if horizon < len(panel.close):
        with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
            labels[:-horizon] = panel.close[horizon:] / panel.close[:-horizon] - 1.0
    labels[~np.isfinite(labels)] = np.nan
    return labels


def score_factor(values: np.ndarray, labels: np.ndarray, start: int, stop: int) -> dict:
    """Summarize daily Spearman IC over half-open signal rows start:stop.

    At least three finite paired assets and nonconstant ranks are required.
    n_dates counts valid IC days; coverage measures finite paired cells before
    constant/asset-count exclusion. daily_ic uses None for undefined days.
    ic_std is the sample standard deviation (zero for one valid day).
    Empty/no-valid intervals have mean_ic and ic_std NaN, never an invented zero.
    These are descriptive statistics, not independent-sample error bars or PnL.
    Caller must purge labels that would cross its evaluation boundary.
    """
    values, labels = np.asarray(values, dtype=float), np.asarray(labels, dtype=float)
    if values.ndim != 2 or labels.shape != values.shape or values.shape[1] < 1:
        raise ValueError("values and labels must be matching [time,asset] matrices")
    if any(isinstance(i, bool) or not isinstance(i, (int, np.integer)) for i in (start, stop)):
        raise ValueError("start and stop must be integer indices")
    if not 0 <= start <= stop <= len(values):
        raise ValueError("invalid half-open score interval")
    daily_ic: list[float | None] = []
    paired_count = 0
    for x, y in zip(values[start:stop], labels[start:stop], strict=True):
        mask = np.isfinite(x) & np.isfinite(y)
        paired_count += int(mask.sum())
        ic = None
        if mask.sum() >= 3:
            rx, ry = rankdata(x[mask]), rankdata(y[mask])
            rx, ry = rx - rx.mean(), ry - ry.mean()
            denominator = np.linalg.norm(rx) * np.linalg.norm(ry)
            if denominator > 0:
                ic = float(np.clip(np.dot(rx, ry) / denominator, -1, 1))
        daily_ic.append(ic)
    valid = np.array([ic for ic in daily_ic if ic is not None], dtype=float)
    total_cells = (stop - start) * values.shape[1]
    return {
        "mean_ic": float(valid.mean()) if len(valid) else float("nan"),
        "n_dates": len(valid),
        "coverage": paired_count / total_cells if total_cells else 0.0,
        "ic_std": float(valid.std(ddof=1)) if len(valid) > 1 else 0.0 if len(valid) else float("nan"),
        "daily_ic": daily_ic,
        "n_signal_dates": int(stop - start),
    }
