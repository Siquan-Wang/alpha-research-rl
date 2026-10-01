"""Original downloader/parser for official French 49-industry daily returns.

Raw snapshots are local inputs, not licensed for redistribution by this package.
The adapter exposes cumulative wealth and returns; trading volume is unavailable.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import urllib.error
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

import numpy as np

from .data import MarketPanel, _close_returns

SOURCE_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/49_Industry_Portfolios_daily_CSV.zip"
DETAILS_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_49_ind_port.html"
PARSER_VERSION = "french49-daily-v1"
TABLE_NAME = "Average Value Weighted Returns -- Daily"
ASSETS = (
    "Agric", "Food", "Soda", "Beer", "Smoke", "Toys", "Fun", "Books", "Hshld", "Clths",
    "Hlth", "MedEq", "Drugs", "Chems", "Rubbr", "Txtls", "BldMt", "Cnstr", "Steel", "FabPr",
    "Mach", "ElcEq", "Autos", "Aero", "Ships", "Guns", "Gold", "Mines", "Coal", "Oil",
    "Util", "Telcm", "PerSv", "BusSv", "Hardw", "Softw", "Chips", "LabEq", "Paper", "Boxes",
    "Trans", "Whlsl", "Rtail", "Meals", "Banks", "Insur", "RlEst", "Fin", "Other",
)
MAX_DOWNLOAD_BYTES = 64 * 1024 * 1024
MAX_MEMBER_BYTES = 256 * 1024 * 1024
MISSING_SENTINELS = (-99.99, -999.0)


def _csv_member(archive: zipfile.ZipFile) -> zipfile.ZipInfo:
    members = archive.infolist()
    for member in members:
        path = PurePosixPath(member.filename.replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts or ":" in member.filename:
            raise ValueError("unsafe ZIP member path")
        if member.file_size > MAX_MEMBER_BYTES or member.flag_bits & 1:
            raise ValueError("oversized or encrypted ZIP member")
    csv_members = [member for member in members if member.filename.lower().endswith(".csv")]
    if len(csv_members) != 1:
        raise ValueError("expected exactly one CSV archive member")
    member = csv_members[0]
    if PurePosixPath(member.filename).name.lower() != "49_industry_portfolios_daily.csv":
        raise ValueError("unsupported archive member name")
    return member


def download_french49(destination: str | Path) -> dict:
    """Download a new immutable local ZIP snapshot and provenance JSON.

    destination may name a ZIP file or directory. Existing snapshots are never
    overwritten. Three bounded attempts, 30-second timeout and 64-MiB limit.
    Archive paths are inspected without extracting files. Returned manifest
    includes raw_path and manifest_path for callers; raw data stay gitignored.
    """
    destination = Path(destination)
    raw_path = destination if destination.suffix.lower() == ".zip" else destination / Path(SOURCE_URL).name
    manifest_path = raw_path.with_suffix(".manifest.json")
    if raw_path.exists() or manifest_path.exists():
        raise FileExistsError("snapshot exists; choose a new destination to preserve provenance")
    payload = None
    status = None
    final_url = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "AlphaResearch-RL/0.1"})
            with urllib.request.urlopen(request, timeout=30) as response:
                status = response.status
                final_url = response.geturl()
                if status != 200:
                    raise ValueError(f"unexpected HTTP status {status}")
                payload = response.read(MAX_DOWNLOAD_BYTES + 1)
                if len(payload) > MAX_DOWNLOAD_BYTES:
                    raise ValueError("download exceeds size limit")
            break
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        member = _csv_member(archive)
        # Reading checks CRC before accepting the snapshot; no extraction occurs.
        archive.read(member)
        archive_members = [entry.filename for entry in archive.infolist()]
    manifest = {
        "source_url": SOURCE_URL, "details_url": DETAILS_URL, "response_status": status,
        "response_url": final_url, "retrieved_utc": datetime.now(UTC).isoformat(),
        "raw_file": raw_path.name, "raw_bytes": len(payload),
        "raw_sha256": hashlib.sha256(payload).hexdigest(), "archive_members": archive_members,
        "archive_member": member.filename, "selected_table": TABLE_NAME, "parser_version": PARSER_VERSION,
        "attribution": "Kenneth R. French Data Library; copyright Eugene F. Fama and Kenneth R. French",
        "redistribution": "No blanket redistribution license verified; raw and converted panels stay local",
        "terms_review_date": "2026-09-30", "raw_path": str(raw_path.resolve()),
        "manifest_path": str(manifest_path.resolve()),
    }
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with raw_path.open("xb") as stream:
        stream.write(payload)
    with manifest_path.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, indent=2)
        stream.write("\n")
    return manifest


def _read_source(path: Path) -> tuple[str, dict]:
    payload = path.read_bytes()
    provenance = {"raw_file": path.name, "raw_bytes": len(payload),
                  "raw_sha256": hashlib.sha256(payload).hexdigest()}
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            member = _csv_member(archive)
            text = archive.read(member).decode("utf-8-sig")
            provenance["archive_member"] = member.filename
        manifest_path = path.with_suffix(".manifest.json")
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("raw_sha256") != provenance["raw_sha256"]:
                raise ValueError("snapshot hash differs from download manifest")
            provenance["download_manifest"] = manifest
    elif path.suffix.lower() == ".csv":
        text = payload.decode("utf-8-sig")
        provenance["archive_member"] = None
    else:
        raise ValueError("source must be an official CSV or ZIP snapshot")
    return text, provenance


def load_french49(path: str | Path, start: str | None = None, end: str | None = None) -> MarketPanel:
    """Load only the daily value-weighted section; start/end dates are inclusive.

    The selected segment must be complete across all 49 portfolios. Missing
    source returns are identified across the entire table and cause an explicit
    error if retained. No interpolation, dropped interior dates or missing-return
    bridges occur. Wealth starts at 100 on the first retained date, whose return
    is explicitly unavailable; subsequent rows retain the original source return.
    """
    text, provenance = _read_source(Path(path))
    rows = list(csv.reader(io.StringIO(text)))
    section_indices = [i for i, row in enumerate(rows)
                       if len(row) == 1 and " ".join(row[0].split()).casefold() == TABLE_NAME.casefold()]
    if len(section_indices) != 1:
        raise ValueError("daily value-weighted table must occur exactly once")
    cursor = section_indices[0] + 1
    while cursor < len(rows) and not any(cell.strip() for cell in rows[cursor]):
        cursor += 1
    if cursor >= len(rows) or tuple(cell.strip() for cell in rows[cursor]) != ("", *ASSETS):
        raise ValueError("unsupported 49-industry column names/order")
    dates, observations = [], []
    for row in rows[cursor + 1:]:
        if not any(cell.strip() for cell in row):
            break
        if len(row) != 50 or not re.fullmatch(r"\d{8}", row[0].strip()):
            raise ValueError("unsupported daily value-weighted row layout")
        token = row[0].strip()
        try:
            date = np.datetime64(f"{token[:4]}-{token[4:6]}-{token[6:]}", "D")
            values = np.array([float(value.strip()) for value in row[1:]])
        except (ValueError, OverflowError) as exc:
            raise ValueError("invalid daily date or return cell") from exc
        if not np.isfinite(values).all():
            raise ValueError("nonfinite source return cell; only documented missing sentinels are supported")
        missing = np.isin(values, MISSING_SENTINELS)
        if ((values[~missing] <= -100) | (values[~missing] > 10000)).any():
            raise ValueError("source percent return outside supported bounds")
        values[missing] = np.nan
        dates.append(date)
        observations.append(values / 100.0)
    if not dates:
        raise ValueError("daily value-weighted table is empty")
    dates = np.array(dates)
    source_returns = np.array(observations)
    if (np.diff(dates) <= np.timedelta64(0, "D")).any():
        raise ValueError("source dates must be unique and strictly chronological")
    first = np.datetime64(start, "D") if start is not None else dates[0]
    last = np.datetime64(end, "D") if end is not None else dates[-1]
    if np.isnat(first) or np.isnat(last) or first > last:
        raise ValueError("invalid inclusive date range")
    retained = (dates >= first) & (dates <= last)
    if retained.sum() < 2:
        raise ValueError("selected range must contain at least two source dates")
    selected_returns = source_returns[retained]
    missing_count = int(np.isnan(source_returns).sum())
    retained_missing = int(np.isnan(selected_returns).sum())
    if retained_missing:
        raise ValueError(f"selected range contains {retained_missing} missing return cells; "
                         "choose an explicit complete segment; missing returns cannot be bridged")
    wealth = np.full(selected_returns.shape, 100.0)
    with np.errstate(over="ignore", invalid="ignore"):
        wealth[1:] = 100.0 * np.cumprod(1.0 + selected_returns[1:], axis=0)
    if not np.isfinite(wealth).all() or (wealth <= 0).any():
        raise ValueError("wealth compounding overflow/underflow; choose a shorter range")
    metadata = {
        **provenance, "synthetic": False, "source": "Kenneth R. French Data Library",
        "source_url": SOURCE_URL, "details_url": DETAILS_URL, "parser_version": PARSER_VERSION,
        "selected_table": TABLE_NAME, "source_units": "percent returns",
        "conversion": "fraction=percent/100; W[0]=100; W[t]=W[t-1]*(1+r[t]) for t>=1",
        "price_semantics": "cumulative_wealth_index", "supported_features": ["close", "returns"],
        "volume_semantics": "unavailable; all NaN; volume expressions disabled",
        "wealth_base_date": str(dates[retained][0]), "wealth_base_value": 100.0,
        "first_retained_return": "unavailable in recomputed returns; source first-day return discarded",
        "retained_date_range": [str(dates[retained][0]), str(dates[retained][-1])],
        "source_date_range": [str(dates[0]), str(dates[-1])],
        "excluded_outside_range_dates": int((~retained).sum()), "dropped_interior_dates": 0,
        "missing_sentinels_percent": list(MISSING_SENTINELS), "source_missing_cells": missing_count,
        "retained_missing_cells": retained_missing, "ordered_assets": list(ASSETS),
        "vintage": "revised upstream historical snapshot; not historical point-in-time data",
        "limitations": "industry-portfolio return ranking; no stock-level execution, volume or PnL claims",
        "attribution": "Kenneth R. French Data Library; copyright Eugene F. Fama and Kenneth R. French",
    }
    return MarketPanel(wealth, np.full_like(wealth, np.nan), _close_returns(wealth),
                       dates[retained], ASSETS, metadata)
