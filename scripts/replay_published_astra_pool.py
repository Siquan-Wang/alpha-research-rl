"""Verify the published frozen-pool diagnosis and offline HTML using saved evidence only.

Run after ``python -m pip install -e .``. These Python execution guards are
checks of this replay process, not an adversarial security sandbox.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import sys
from pathlib import Path, PurePosixPath

from replay_published_results import NoTrainingImports

CONTRACT_PATH = "artifacts/astra-pool-diagnosis-v1/contract.json"
REPORT_PATH = "results/astra_pool_diagnosis_v1.json"
EXPLORER_PATH = "docs/astra-pool-explorer.html"
STUDY = "astra-frozen-pool-diagnosis-v1"
SCORING_MODULES = {
    "alpha_research_rl.financial_tasks", "alpha_research_rl.financial_policy",
    "alpha_research_rl.evaluation", "alpha_research_rl.french", "alpha_research_rl.astra_study",
}
EXPECTED_ACCOUNTING = {
    "new_evaluator_calls_started": 108, "new_evaluator_calls_completed": 108,
    "reused_key_count": 24, "total_key_count": 132, "total_slot_count": 180,
    "model_calls": 0, "new_formulas": 0, "automatic_retries": 0,
}
EXPECTED_POPULATION = {
    "slot_count": 180, "episode_count": 30, "key_count": 132,
    "reuse_key_count": 24, "pending_job_count": 108,
}


class NoScoringImports(NoTrainingImports):
    def find_spec(self, fullname, path=None, target=None):
        if any(fullname == name or fullname.startswith(name + ".") for name in SCORING_MODULES):
            raise ImportError(f"Saved pool replay must not import a financial scorer/loader: {fullname}")
        return super().find_spec(fullname, path, target)


def install_guards(root):
    """Install irreversible process-local guards; tests use a fresh interpreter."""
    # On Windows platform detection can invoke `cmd /c ver`; finish it before
    # prohibiting every replay subprocess, just as the original Astra verifier does.
    platform.uname()
    guard = NoScoringImports()
    for name in tuple(sys.modules):
        guard.find_spec(name)  # A cached forbidden module must not bypass the finder.
    forbidden = [(root / name).resolve() for name in ("models", "data/raw", "data/cache", ".local")]

    def audit(event, args):
        if event in {"socket.__new__", "socket.connect", "socket.getaddrinfo", "socket.sendto",
                     "subprocess.Popen", "os.system", "os.posix_spawn", "os.exec", "os.fork"}:
            raise RuntimeError("Public pool replay must not start a process or use a network")
        if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0])).resolve()
            if any(path == directory or directory in path.parents for directory in forbidden):
                raise RuntimeError("Public pool replay must not access weights, raw data or private runs")

    sys.meta_path.insert(0, guard)
    sys.addaudithook(audit)


def _require_files(paths, root):
    missing = [path.relative_to(root).as_posix() for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing published pool artifacts: " + ", ".join(missing))


def _counts(value, expected, label):
    if type(value) is not dict:
        raise AssertionError(f"Invalid {label} object")
    for key, count in expected.items():
        if type(value.get(key)) is not int or value[key] != count:
            raise AssertionError(f"Unexpected {label}.{key}; required exact integer {count}")


def verify_published_pool(root, *, replay=None):
    """The injectable callback supports synthetic interface tests, never CLI substitution."""
    root = Path(root).resolve()
    contract_path, report_path = root / CONTRACT_PATH, root / REPORT_PATH
    _require_files((contract_path, report_path), root)
    contract_raw = contract_path.read_bytes()
    contract = json.loads(contract_raw)
    relative = contract.get("execution_directory")
    if (type(relative) is not str or "\\" in relative or ":" in relative
            or PurePosixPath(relative).is_absolute() or ".." in PurePosixPath(relative).parts):
        raise AssertionError("Invalid public execution directory")
    directory = (root / relative).resolve()
    if not directory.is_relative_to(root) or directory != contract_path.parent / "execution":
        raise AssertionError("Execution directory must be the contract's bound public execution directory")
    _require_files((directory / "COMPLETE.json", directory / "request.json",
                    directory / "publication-receipt.json"), root)

    if replay is None:
        from alpha_research_rl.astra_pool_diagnosis import replay_pool_diagnosis

        replay = replay_pool_diagnosis
    verified = replay(contract_path, directory, source_root=root, report_path=report_path)
    report_raw = report_path.read_bytes()
    report = json.loads(report_raw)
    if report.get("status") != "COMPLETE_POST_HOC" or report.get("study") != STUDY:
        raise AssertionError("Published pool report must be COMPLETE_POST_HOC for the registered study")
    if verified.get("status") != "SAVED_ARITHMETIC_VERIFIED" or verified.get("study") != STUDY:
        raise AssertionError("Saved pool replay did not verify the registered study")
    _counts(report.get("call_accounting"), EXPECTED_ACCOUNTING, "call_accounting")
    _counts(report.get("population"), EXPECTED_POPULATION, "report population")
    _counts(verified.get("population"), EXPECTED_POPULATION, "replay population")
    _counts(verified, {"completed_new_jobs": 108, "model_calls": 0,
                       "new_financial_scores": 0, "raw_market_data_reads": 0}, "replay")
    if (verified.get("contract_sha256") != hashlib.sha256(contract_raw).hexdigest()
            or verified.get("report_sha256") != hashlib.sha256(report_raw).hexdigest()):
        raise AssertionError("Verified input hashes differ from the published files")
    return {"status": "matches_published_astra_pool_evidence", "historical_new_evaluations": 108,
            "reused_keys": 24, "keys": 132, "slots": 180, "episodes": 30, "model_calls": 0,
            "market_scores_recomputed": False, "raw_market_data_read": False,
            "arithmetic_absolute_tolerance": 1e-12, "arithmetic_relative_tolerance": 1e-12,
            "retained_evidence_types_and_hashes_exact": True,
            "contract_sha256": verified["contract_sha256"], "report_sha256": verified["report_sha256"]}


def verify_published_pool_explorer(root, *, build=None, renderer=None):
    """Rebuild saved-only evidence and require the exact published payload and template."""
    from alpha_research_rl.astra_pool_diagnosis import _exact
    from alpha_research_rl.astra_pool_explorer import build_payload, render

    root = Path(root).resolve()
    contract_path, report_path, html_path = root / CONTRACT_PATH, root / REPORT_PATH, root / EXPLORER_PATH
    _require_files((contract_path, report_path, html_path), root)
    # Capture once: the compared page cannot change between extracting its evidence
    # envelope and verifying its full template. The builder snapshots all report inputs.
    html_raw = html_path.read_bytes()
    html = html_raw.decode("utf-8")
    matches = re.findall(r'<script id="pool-data" type="application/json">(.*?)</script>', html, re.DOTALL)
    if len(matches) != 1:
        raise AssertionError("Pool explorer must contain exactly one evidence payload")
    embedded = json.loads(matches[0])
    rebuilt = (build or build_payload)(contract_path, contract_path.parent / "execution", report_path,
                                      source_root=root)
    _exact(embedded, rebuilt, "pool explorer embedded report and metadata")
    # JSON report newlines are escaped inside the envelope. This normalization
    # permits checkout line endings only in the surrounding presentation text.
    expected_html = (renderer or render)(rebuilt)
    if html.replace("\r\n", "\n") != expected_html.replace("\r\n", "\n"):
        raise AssertionError("Pool explorer full HTML differs from the published renderer")
    return {"explorer_payload_and_template_match": True, "explorer_report_bytes_exact": True,
            "explorer_html_sha256": hashlib.sha256(html_raw).hexdigest(),
            "contract_sha256": rebuilt["verification"]["contract_sha256"],
            "report_sha256": rebuilt["report_sha256"]}


def main():
    root = Path(__file__).resolve().parents[1]
    install_guards(root)
    summary = verify_published_pool(root)
    explorer = verify_published_pool_explorer(root)
    if any(summary[name] != explorer[name] for name in ("contract_sha256", "report_sha256")):
        raise AssertionError("Pool report and explorer were verified against different evidence")
    summary.update(explorer)
    summary.update(training_and_financial_imports_private_data_subprocesses_and_network_disallowed=True,
                   stdlib_platform_detection_precedes_execution_guards=True,
                   guards_are_not_an_adversarial_sandbox=True)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, AssertionError, RuntimeError, ImportError) as error:
        raise SystemExit("Public Astra pool replay failed: " + str(error)) from error
