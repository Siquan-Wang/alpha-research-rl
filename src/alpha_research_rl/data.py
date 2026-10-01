"""Validated market panels and explicitly synthetic, causal development tasks."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


def _close_returns(close: np.ndarray) -> np.ndarray:
    result = np.full(close.shape, np.nan, dtype=float)
    with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
        result[1:] = close[1:] / close[:-1] - 1.0
    return result


@dataclass
class MarketPanel:
    """Rows are chronological dates; returns[t] realizes close[t-1] to close[t].

    NaN observations are permitted for in-memory panels, never silently imputed.
    Infinite values, nonpositive observed prices and negative volume are rejected.
    """

    close: np.ndarray
    volume: np.ndarray
    returns: np.ndarray
    dates: np.ndarray
    assets: tuple[str, ...]
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.close = np.asarray(self.close, dtype=float)
        self.volume = np.asarray(self.volume, dtype=float)
        self.returns = np.asarray(self.returns, dtype=float)
        original_dates = np.asarray(self.dates)
        self.dates = np.asarray(self.dates, dtype="datetime64[ns]")
        if (
            original_dates.dtype.kind == "M"
            and not np.isnat(original_dates).any()
            and not np.array_equal(self.dates.astype(original_dates.dtype), original_dates)
        ):
            raise ValueError("dates are outside supported nanosecond range")
        self.assets = tuple(self.assets)
        if self.close.ndim != 2 or min(self.close.shape) < 1:
            raise ValueError("close must be a nonempty [time, asset] matrix")
        if self.volume.shape != self.close.shape or self.returns.shape != self.close.shape:
            raise ValueError("close, volume and returns must have identical shapes")
        if self.dates.shape != (self.close.shape[0],):
            raise ValueError("dates must have one entry per time row")
        if np.isnat(self.dates).any() or (np.diff(self.dates) <= np.timedelta64(0, "ns")).any():
            raise ValueError("dates must be valid, unique and strictly chronological")
        if len(self.assets) != self.close.shape[1] or len(set(self.assets)) != len(self.assets):
            raise ValueError("assets must uniquely identify every column")
        if any(not isinstance(asset, str) or not asset.strip() for asset in self.assets):
            raise ValueError("asset identifiers must be nonempty strings")
        if any(np.isinf(array).any() for array in (self.close, self.volume, self.returns)):
            raise ValueError("panel arrays cannot contain infinity")
        if (self.close[np.isfinite(self.close)] <= 0).any():
            raise ValueError("observed close prices must be positive")
        if (self.volume[np.isfinite(self.volume)] < 0).any():
            raise ValueError("observed volumes must be nonnegative")
        if not np.allclose(self.returns, _close_returns(self.close), rtol=1e-9, atol=1e-12, equal_nan=True):
            raise ValueError("returns must equal close[t]/close[t-1]-1 with an all-NaN first row")
        if not isinstance(self.metadata, dict):
            raise TypeError("metadata must be a dictionary")


def make_synthetic_panel(
    seed: int = 0, n_dates: int = 600, n_assets: int = 32, regime: str = "signal"
) -> MarketPanel:
    """Produce causal development data; this is not a financial market model.

    At t>=2 the conditional mean of return[t] is determined by the observed
    return[t-1] and log(volume[t-1]/volume[t-2]), standardized across assets.
    Independent Gaussian noise realizes return[t]; contemporaneous volume is
    drawn afterwards. Null uses zero coefficients. Decay coefficients decline
    linearly from one to zero over the supplied panel. No latent feature is exposed.
    """
    if regime not in {"signal", "null", "decay"}:
        raise ValueError("regime must be signal, null or decay")
    if isinstance(n_dates, bool) or not isinstance(n_dates, int) or n_dates < 3:
        raise ValueError("n_dates must be an integer >=3")
    if isinstance(n_assets, bool) or not isinstance(n_assets, int) or n_assets < 3:
        raise ValueError("n_assets must be an integer >=3")
    rng = np.random.default_rng(seed)
    close = np.empty((n_dates, n_assets))
    volume = np.empty_like(close)
    returns = np.full_like(close, np.nan)
    close[0] = 100.0
    volume[0] = rng.lognormal(mean=12.0, sigma=0.4, size=n_assets)

    def standardize(x: np.ndarray) -> np.ndarray:
        scale = x.std()
        return (x - x.mean()) / scale if scale > 0 else np.zeros_like(x)

    for t in range(1, n_dates):
        strength = 0.0 if regime == "null" else 1.0
        if regime == "decay":
            strength *= 1.0 - t / (n_dates - 1)
        conditional_mean = np.zeros(n_assets)
        if t >= 2:
            conditional_mean = strength * (
                0.004 * standardize(returns[t - 1])
                + 0.006 * standardize(np.log(volume[t - 1] / volume[t - 2]))
            )
        returns[t] = np.clip(conditional_mean + rng.normal(0, 0.01, n_assets), -0.15, 0.15)
        close[t] = close[t - 1] * (1.0 + returns[t])
        volume[t] = rng.lognormal(mean=12.0, sigma=0.4, size=n_assets)
    return MarketPanel(
        close=close,
        volume=volume,
        returns=_close_returns(close),
        dates=np.datetime64("2000-01-03") + np.arange(n_dates).astype("timedelta64[D]"),
        assets=tuple(f"SYN{i:03d}" for i in range(n_assets)),
        metadata={
            "synthetic": True,
            "generator": "causal-observed-v1",
            "seed": int(seed),
            "regime": regime,
            "signal_equation": "E[return[t]|past] = strength[t] * (0.004*zcs(return[t-1]) + "
            "0.006*zcs(log(volume[t-1]/volume[t-2]))) for t>=2; independent N(0,0.01^2) noise",
            "strength": "zero" if regime == "null" else "linear 1 to 0" if regime == "decay" else "one",
            "return_clip": [-0.15, 0.15],
            "calendar": "consecutive synthetic calendar days, not exchange sessions",
            "purpose": "implementation and development only; no financial evidence",
        },
    )


def load_panel_csv(path: str | Path) -> MarketPanel:
    """Read strict rectangular long CSV: date,asset,close,volume.

    Input row order is immaterial; output dates and asset identifiers are sorted.
    Prices/volumes must be finite and all date-asset cells must be present exactly once.
    """
    path = Path(path)
    cells: dict[tuple[np.datetime64, str], tuple[float, float]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or len(reader.fieldnames) != 4 or set(reader.fieldnames) != {
            "date", "asset", "close", "volume"
        }:
            raise ValueError("CSV header must contain exactly date,asset,close,volume")
        for row_number, row in enumerate(reader, start=2):
            try:
                if None in row or any(value is None or not value.strip() for value in row.values()):
                    raise ValueError("missing or extra field")
                date_text = row["date"].strip()
                if date_text.lower() == "nat":
                    raise ValueError("invalid date")
                parsed_date = np.datetime64(date_text)
                date = parsed_date.astype("datetime64[ns]")
                if date.astype(parsed_date.dtype) != parsed_date:
                    raise ValueError("date is outside supported nanosecond range")
                asset = row["asset"].strip()
                price, volume = float(row["close"]), float(row["volume"])
                if np.isnat(date) or not np.isfinite(price) or price <= 0:
                    raise ValueError("invalid date or close")
                if not np.isfinite(volume) or volume < 0:
                    raise ValueError("invalid volume")
                key = (date, asset)
                if key in cells:
                    raise ValueError("duplicate date-asset cell")
                cells[key] = (price, volume)
            except (ValueError, TypeError, OverflowError) as exc:
                raise ValueError(f"Invalid CSV row {row_number}: {exc}") from exc
    if not cells:
        raise ValueError("CSV contains no observations")
    dates = np.array(sorted({key[0] for key in cells}), dtype="datetime64[ns]")
    assets = tuple(sorted({key[1] for key in cells}))
    if len(cells) != len(dates) * len(assets):
        raise ValueError("CSV has missing date-asset cells; forward filling is forbidden")
    close = np.array([[cells[(date, asset)][0] for asset in assets] for date in dates])
    volume = np.array([[cells[(date, asset)][1] for asset in assets] for date in dates])
    return MarketPanel(close, volume, _close_returns(close), dates, assets, {
        "synthetic": None, "data_kind": "unverified", "source": "user-supplied CSV", "source_file": path.name,
        "provenance": "Importer does not establish source license or market authenticity",
    })
