"""Analyze the two pinned public RLOO training reports without model or market access."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from alpha_research_rl.reward_credit import SOURCES, RewardCreditError, analyze_saved_reports


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--financial", type=Path, default=ROOT / SOURCES["financial"][0])
    parser.add_argument("--linkage", type=Path, default=ROOT / SOURCES["linkage"][0])
    parser.add_argument("--output", type=Path, required=True,
                        help="New JSON file; never overwrite. Successful exit is required to accept it.")
    args = parser.parse_args(argv)
    try:
        if args.output.resolve() in {args.financial.resolve(), args.linkage.resolve()}:
            raise RewardCreditError("Output collides with an input")
        if args.output.exists():
            raise FileExistsError("Output already exists")
        report = analyze_saved_reports(args.financial, args.linkage, source_root=ROOT)
        raw = (json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")
        with args.output.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except (OSError, RewardCreditError) as exc:
        print(f"Reward-credit analysis failed: {exc}. Any output from a failed write is not complete evidence.",
              file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "population": report["population"]}, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
