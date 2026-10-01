"""Metadata-only coordinate freeze; never imports an oracle or a hosted actor."""
from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import scipy
from scipy.stats import qmc

ROOT = Path(__file__).resolve().parent
DEST = ROOT / "adaptivity-dev-coordinates-v1.json"
if DEST.exists():
    raise SystemExit("refuse to overwrite frozen coordinates")
selection = ROOT / "adaptivity-metadata-order-v1.json"
metadata = ROOT / "newton-adapter-metadata-v1.json"
order = json.loads(selection.read_text(encoding="utf-8"))
specifications = {
    "m8_sound_speed": {
        "variables": ["gamma", "T", "M"],
        "runtime_keys": ["adiabatic_index", "temperature", "molar_mass"],
        "bounds": [[0.14, 14.0], [29.315, 2931.5], [0.002897, 0.2897]],
        "units": ["dimensionless", "Kelvin", "kg/mol"],
        "output": "speed of sound", "output_unit": "m/s",
        "support_reason": "One decade either side of each public runtime default; adapted positive support.",
    },
    "m10_be_distribution": {
        "variables": ["omega", "T"], "runtime_keys": ["omega", "temperature"],
        "bounds": [[1e8, 1e16], [10.0, 10000.0]],
        "units": ["angular frequency in benchmark input units", "temperature in benchmark input units"],
        "output": "average occupation number of photons in a quantum state",
        "output_unit": "dimensionless occupation number",
        "support_reason": "Pre-outcome revision honoring public recommended lower scales and multi-order exploration; upper bounds are adapter choices.",
    },
}
tasks = []
for domain in order["domains"]:
    if domain["allocation"] != "development":
        continue
    spec = specifications[domain["domain_id"]]
    for law in domain["laws"]:
        rows = {}
        for split, power in (("train", 6), ("test", 8)):
            seed_text = "astra-adaptivity-decoder-dev-v1|" + law["canonical_law_id"] + "|" + split
            seed = int.from_bytes(hashlib.sha256(seed_text.encode("utf-8")).digest()[:8], "big")
            unit = qmc.Sobol(d=len(spec["bounds"]), scramble=True, rng=np.random.default_rng(seed)).random_base2(m=power)
            values = [[float(10.0 ** (math.log10(lo) + float(u) * (math.log10(hi) - math.log10(lo))))
                       for u, (lo, hi) in zip(row, spec["bounds"])] for row in unit]
            if len({tuple(row) for row in values}) != len(values):
                raise ValueError("duplicate coordinates; no redraw allowed")
            if any(not math.isfinite(x) or not lo <= x <= hi
                   for row in values for x, (lo, hi) in zip(row, spec["bounds"])):
                raise ValueError("mapped support failure; no redraw allowed")
            rows[split] = {"seed": seed, "seed_text": seed_text, "unit": unit.tolist(), "x": values}
        if {tuple(row) for row in rows["train"]["x"]} & {tuple(row) for row in rows["test"]["x"]}:
            raise ValueError("train/test overlap; no redraw allowed")
        tasks.append({"domain_id": domain["domain_id"], "difficulty": law["difficulty"],
                      "law_version": law["selected_version"], "canonical_law_id": law["canonical_law_id"],
                      "specification": spec, "coordinates": rows})
assert len(tasks) == 4
record = {
    "schema": "adaptivity-dev-coordinates-v1", "created_at_utc": datetime.now(UTC).isoformat(),
    "scope": "Metadata-only coordinates; no oracle or model invocation; test coordinates never enter actor inputs",
    "upstream_commit": order["upstream_commit"],
    "selection_sha256": hashlib.sha256(selection.read_bytes()).hexdigest(),
    "metadata_sha256": hashlib.sha256(metadata.read_bytes()).hexdigest(),
    "numpy": np.__version__, "scipy": scipy.__version__,
    "generator": "qmc.Sobol(scramble=True,rng=np.random.default_rng(seed)).random_base2(m)",
    "noise_level": 0.0, "coordinate_transform": "log10 all dimensions",
    "training_target_count": 0, "confirmation_target_count": 0, "hosted_calls": 0,
    "tasks": tasks,
}
DEST.write_text(json.dumps(record, indent=2, ensure_ascii=True, allow_nan=False) + "\n", encoding="utf-8")
print(json.dumps({"path": DEST.name, "sha256": hashlib.sha256(DEST.read_bytes()).hexdigest(),
                  "tasks": len(tasks), "train_coordinates": 256, "test_coordinates": 1024,
                  "oracle_queries": 0, "hosted_calls": 0}))
