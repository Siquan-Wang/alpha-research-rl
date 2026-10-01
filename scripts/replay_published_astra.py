"""Check all published Astra traces, saved arithmetic, and offline page content.

Execution guards prohibit model/private-data access, subprocesses and network.
They are checks of this replay process, not an adversarial security sandbox.
"""

from __future__ import annotations

import json
import os
import platform
import re
import sys
from pathlib import Path

from replay_published_results import NoTrainingImports


def compare_explorer_payload(rebuilt, embedded):
    """Retained evidence is exact; only computed verification arithmetic has tolerance."""
    from alpha_research_rl.astra_replay import _computed, _exact

    fields = {"verification", "submissions", "assessment", "permitted_histories"}
    if type(rebuilt) is not dict or type(embedded) is not dict or set(rebuilt) != fields or set(embedded) != fields:
        raise AssertionError("Unexpected explorer payload fields")
    for name in fields - {"verification"}:
        _exact(rebuilt[name], embedded[name], "explorer retained " + name)
    _computed(rebuilt["verification"], embedded["verification"], "explorer verification arithmetic")


def main():
    root = Path(__file__).resolve().parents[1]
    forbidden = [root / name for name in ("models", "data/raw", "data/cache", ".local")]
    # Windows' stdlib platform detection may run `cmd /c ver`. Prime this
    # ordinary host-metadata cache before prohibiting every replay subprocess.
    platform.uname()

    def audit(event, args):
        if event in ("socket.connect", "subprocess.Popen", "os.system"):
            raise RuntimeError("Public Astra replay must not start a process or connect to a network")
        if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0])).resolve()
            if any(path == directory or directory in path.parents for directory in forbidden):
                raise RuntimeError("Public Astra replay must not access weights, raw data or private runs")

    sys.meta_path.insert(0, NoTrainingImports())
    sys.addaudithook(audit)
    from alpha_research_rl.agentic_research import digest
    from alpha_research_rl.astra_explorer import build_payload, render
    from alpha_research_rl.astra_replay import _computed, replay_study
    from alpha_research_rl.astra_trace_diagnostics import diagnose_traces

    contract = root / "artifacts/astra-agent-v1/contract.json"
    submissions = root / "results/astra_agent_v1_submissions.json"
    assessment = root / "results/astra_agent_v1_assessment.json"
    replay = replay_study(contract, submissions, source_root=root, assessment_path=assessment)
    saved_replay = json.loads((root / "results/astra_agent_v1_assessment_replay.json").read_bytes())
    _computed(replay, saved_replay, "published assessment replay")

    rebuilt = diagnose_traces(contract, submissions, source_root=root)
    saved = json.loads((root / "results/astra_agent_v1_trace_diagnostics.json").read_bytes())
    # Each object must authenticate itself. Small cross-Python float differences
    # can change its digest; compare the computed bodies after verifying both.
    for report in (rebuilt, saved):
        if report.pop("body_sha256") != digest(report):
            raise AssertionError("Trace bookkeeping body digest differs")
    _computed(rebuilt, saved, "published trace bookkeeping")

    html = (root / "docs/astra-explorer.html").read_text(encoding="utf-8")
    matches = re.findall(r'<script id="astra-data" type="application/json">(.*?)</script>', html, re.DOTALL)
    if len(matches) != 1:
        raise AssertionError("Explorer must contain exactly one evidence payload")
    embedded = json.loads(matches[0])
    compare_explorer_payload(build_payload(contract, submissions, assessment, source_root=root), embedded)
    if render(embedded) != html:
        raise AssertionError("Explorer static page differs from the published renderer")
    print(json.dumps({"status": "matches_published_astra_evidence", "decisions": 180,
                      "episodes": 30, "saved_assessments": 30, "all_trace_bookkeeping_matches": True,
                      "explorer_payload_and_template_match": True, "arithmetic_absolute_tolerance": 1e-12,
                      "types_keys_order_and_source_hashes_exact": True, "market_scores_recomputed": False,
                      "training_imports_private_data_replay_subprocesses_and_network_disallowed": True,
                      "stdlib_platform_detection_precedes_execution_guards": True}))


if __name__ == "__main__":
    main()
