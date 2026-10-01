"""Portable evidence manifests without local paths or user identifiers."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import numpy as np


def json_safe(obj):
    if isinstance(obj, dict):
        return {str(k): json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_safe(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return json_safe(obj.tolist())
    if isinstance(obj, np.generic):
        return json_safe(obj.item())
    if isinstance(obj, float) and not np.isfinite(obj):
        return None
    return obj


def write_json(path: str | Path, value) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_safe(value), indent=2, allow_nan=False) + "\n", encoding="utf-8")


def source_digest() -> str:
    root = Path(__file__).parent
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*.py")):
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def run_manifest(config: dict) -> dict:
    packages = {}
    for package in ["numpy", "pandas", "scipy", "torch", "transformers", "peft"]:
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            pass
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False,
        cwd=Path(__file__).parent,
    )
    return {
        "created_utc": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "platform": platform.system(),
        "packages": packages,
        "git_revision": revision.stdout.strip() if revision.returncode == 0 else None,
        "source_sha256": source_digest(),
        "config": config,
    }
