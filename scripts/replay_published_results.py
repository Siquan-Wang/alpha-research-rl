"""Recompute the published five-policy comparison without training dependencies.

Run after `python -m pip install -e .`. This is an execution check of saved
evidence, not a security sandbox or a reproduction of the undistributed weights.
"""

from __future__ import annotations

import hashlib
import importlib.abc
import json
import math
import os
import sys
from pathlib import Path


class NoTrainingImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in {"torch", "transformers", "peft", "accelerate"}:
            raise ImportError(f"Saved-evidence replay must not import {fullname}")


def same(left, right, location="root"):
    if isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            raise AssertionError(f"Object keys differ: {location}")
        for key in left:
            same(left[key], right[key], f"{location}.{key}")
    elif isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            raise AssertionError(f"List lengths differ: {location}")
        for index, (a, b) in enumerate(zip(left, right, strict=True)):
            same(a, b, f"{location}[{index}]")
    elif type(left) in (int, float) and type(right) in (int, float):
        if not math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12):
            raise AssertionError(f"Numbers differ: {location}")
    elif type(left) is not type(right) or left != right:
        raise AssertionError(f"Values differ: {location}")


def main():
    root = Path(__file__).resolve().parents[1]
    forbidden = [(root / "models").resolve(), (root / "data" / "raw").resolve()]

    def audit(event, args):
        if event == "socket.connect":
            raise RuntimeError("Saved-evidence replay must not connect to a network")
        if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0])).resolve()
            if any(path == directory or directory in path.parents for directory in forbidden):
                raise RuntimeError("Saved-evidence replay must not access weights or raw market data")

    sys.meta_path.insert(0, NoTrainingImports())
    sys.addaudithook(audit)
    from alpha_research_rl.linkage_analysis import ORIGINALS, ROLES, analyze_linkage

    reports, sources = {}, {}
    names = ("sft", "rloo23", "rloo29", "placebo23", "placebo29")
    for label, name in zip(ROLES.values(), names, strict=True):
        path = root / "artifacts" / "development" / f"financial-{name}-transfer-v1.json"
        raw = path.read_bytes()
        reports[label] = json.loads(raw)
        sources[label] = {"file": path.name, "sha256": hashlib.sha256(raw).hexdigest()}
    reproduced = analyze_linkage(reports, {label: sources[label] for label in ORIGINALS})
    reproduced["source_reports"] = sources
    published = json.loads((root / "results" / "financial_linkage_paired_v1.json").read_bytes())
    same(reproduced, published)
    count = sum(len(episode["records"]) for report in reports.values() for episode in report["episodes"])
    print(json.dumps({"status": "matches_published_analysis", "checkpoints": len(reports),
                      "retained_records": count, "float_tolerance": 1e-12,
                      "report_byte_hashes_match": True,
                      "training_imports_raw_data_weights_and_network_disallowed": True}))


if __name__ == "__main__":
    main()
