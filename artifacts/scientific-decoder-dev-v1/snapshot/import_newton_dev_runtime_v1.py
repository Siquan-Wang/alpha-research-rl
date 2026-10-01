"""One trusted-domain import qualification only; never invokes its scalar function."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

base = Path(__file__).resolve().parent
domain = sys.argv[1]
if domain not in {"m8_sound_speed", "m10_be_distribution"}:
    raise ValueError("development domain only")
destination = base / ("newton-import-" + domain + "-v1.json")
if destination.exists():
    raise ValueError("do not overwrite import qualification")
path = base / "newton_scalar_worker_v1.py"
spec = importlib.util.spec_from_file_location("newton_scalar_worker", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
record = {"domain": domain, "started_at_utc": datetime.now(UTC).isoformat(),
          "worker_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "oracle_queries": 0}
try:
    hashes = module.verify_cache()
    scalar = module.load_scalar(domain)
    module.verify_cache()
    origins = module.verify_vendor_origins(hashes, domain)
    record.update(status="IMPORTED_WITHOUT_MEASUREMENT", callable=callable(scalar),
                  imported_project_modules=origins,
                  api_modules_present=sorted(n for n in sys.modules if n.split(".")[0] in {"openai", "anthropic", "requests", "httpx"}))
except BaseException as exc:  # noqa: BLE001 - record stable class only, never source/traceback.
    record.update(status="IMPORT_FAILED", error_class=type(exc).__name__)
with destination.open("x", encoding="utf-8") as file:
    file.write(json.dumps(record, indent=2, sort_keys=True) + "\n")
print(json.dumps(record))
raise SystemExit(0 if record["status"] == "IMPORTED_WITHOUT_MEASUREMENT" else 1)
