"""Recompute retained diagnostics and the constructed exact opportunity gate.

No new generation or factor scoring; the saved feedback rank diagnostics are
inputs. Python-level guards are execution checks, not a security sandbox.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

from replay_published_results import NoTrainingImports, same


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parents[1]
    reports_dir = root / "artifacts" / "development"
    forbidden = [(root / "models").resolve(), (root / "data" / "raw").resolve()]

    def audit(event, args):
        if event == "socket.connect":
            raise RuntimeError("Saved-diagnostic replay must not connect to a network")
        if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0])).resolve()
            if any(path == directory or directory in path.parents for directory in forbidden):
                raise RuntimeError("Saved-diagnostic replay must not access weights or raw market data")

    sys.meta_path.insert(0, NoTrainingImports())
    sys.addaudithook(audit)
    from alpha_research_rl import mechanism_gate, proposal_diversity, reliability_analysis

    analysis_path = root / "results" / "financial_linkage_paired_v1.json"
    reports, saved, sources, _, analysis_sha = reliability_analysis.load_inputs(analysis_path, reports_dir)
    reliability = reliability_analysis.analyze_reliability(reports, saved, sources)
    reliability["source_analysis"] = {"file": analysis_path.name, "sha256": analysis_sha}
    reliability["analysis_source_sha256"] = sha(Path(reliability_analysis.__file__))
    same(reliability, json.loads((root / "results" / "financial_reliability_v1.json").read_bytes()))

    diversity_published = json.loads((root / "results" / "financial_proposal_diversity_v1.json").read_bytes())
    diagnostic_sources = diversity_published["source_rank_diagnostics"]
    diagnostics = {}
    for name, source in diagnostic_sources.items():
        if name != source["file"] or not name or any(c in name for c in "/\\:"):
            raise AssertionError("Rank diagnostic must use a safe basename")
        path = reports_dir / name
        if sha(path) != source["sha256"]:
            raise AssertionError("Rank diagnostic source-byte hash differs")
        diagnostics[name] = json.loads(path.read_bytes())
    diversity = proposal_diversity.analyze_diversity(reports, sources, diagnostics, diagnostic_sources)
    diversity["analysis_source_sha256"] = sha(Path(proposal_diversity.__file__))
    same(diversity, diversity_published)
    gate = mechanism_gate.build_report(root / "docs" / "mechanism-gate-plan-v1.md")
    gate_published = json.loads((root / "results" / "mechanism_gate_v1.json").read_bytes())
    if json.dumps(gate, sort_keys=True, allow_nan=False) != json.dumps(
        gate_published, sort_keys=True, allow_nan=False
    ):
        raise AssertionError("Exact mechanism gate report or source/plan byte identities differ")
    print(json.dumps({"status": "matches_published_diagnostics",
                      "reliability_contrasts": len(reliability["comparisons"]),
                      "year_omissions": sum(len(row["leave_one_year_out"]) for row in reliability["comparisons"]),
                      "diversity_records": diversity["integrity"]["n_strict_proposals"], "float_tolerance": 1e-12,
                      "constructed_gate_query_plans": len(gate["calculation"]["plans"]),
                      "constructed_gate_report_matches_exactly": True,
                      "source_byte_hashes_match": True,
                      "training_imports_raw_data_weights_and_network_disallowed": True}))


if __name__ == "__main__":
    main()
