"""Verify complete published matched-prefix evidence without models or market data.

Run in a matching checkout with the ordinary package installed. The process
guards check this replay; they are not an adversarial security sandbox.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import sys
from pathlib import Path

from replay_published_results import NoTrainingImports

STUDY = "astra-matched-prefix-v1"
PUBLIC_DIRECTORY = "artifacts/astra-matched-prefix-v1"
CONTRACT_PATH = PUBLIC_DIRECTORY + "/contract.json"
EXECUTION_DIRECTORY = PUBLIC_DIRECTORY + "/execution"
SUBMISSIONS_PATH = "results/astra_matched_prefix_v1_submissions.json"
REPORT_PATH = "results/astra_matched_prefix_v1.json"
SCORING_MODULES = {
    "alpha_research_rl.financial_tasks", "alpha_research_rl.financial_policy",
    "alpha_research_rl.evaluation", "alpha_research_rl.french", "alpha_research_rl.astra_study",
}
EXPECTED_POPULATION = {"states": 10, "hosted_calls": 80, "cheap_slots": 120,
                       "new_slots": 200, "repetitions": 4}
EXPECTED_REPLAY_COUNTS = {"state_count": 10, "slot_count": 200, "hosted_calls": 80,
                          "cheap_slots": 120, "repetitions": 4, "new_model_calls": 0,
                          "new_financial_scores": 0, "raw_market_data_reads": 0}
SLOT_ORDER = tuple((f"{year}-H{half}", generator, repetition)
                   for year in range(2020, 2025) for half in (1, 2)
                   for generator in ("truthful", "masked", "copy", "window_edit", "grammar_draw")
                   for repetition in range(1, 5))
REQUIRED_EXECUTION_FILES = (
    "collection-request.json", "preparation-receipt.json", "SUBMISSIONS.json",
    "assessment-request.json", "submissions-receipt.json", "assessment-plan.json", "COMPLETE.json",
)


class NoScoringImports(NoTrainingImports):
    def find_spec(self, fullname, path=None, target=None):
        if any(fullname == name or fullname.startswith(name + ".") for name in SCORING_MODULES):
            raise ImportError(f"Saved revision replay must not import a financial scorer/loader: {fullname}")
        return super().find_spec(fullname, path, target)


def install_guards(root):
    """Install irreversible process-local checks; test these in a fresh interpreter."""
    # Windows platform detection can run `cmd /c ver`; finish it before the
    # replay phase prohibits all subprocesses. This does not invoke a provider.
    platform.uname()
    root = Path(root).resolve()
    guard = NoScoringImports()
    for name in tuple(sys.modules):
        guard.find_spec(name)
    forbidden = [(root / name).resolve() for name in ("models", "data/raw", "data/cache", ".local")]

    def audit(event, args):
        if event.startswith("socket.") or event in {
            "subprocess.Popen", "os.system", "os.posix_spawn", "os.exec", "os.fork",
            "os.startfile", "os.startfile/2",
        }:
            raise RuntimeError("Public revision replay must not start a process or use a network")
        if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0])).resolve()
            if any(path == directory or directory in path.parents for directory in forbidden):
                raise RuntimeError("Public revision replay must not access weights, raw data or private runs")

    sys.meta_path.insert(0, guard)
    sys.addaudithook(audit)


def _object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate JSON object key: " + key)
        value[key] = item
    return value


def _nonfinite(value):
    raise ValueError("Nonfinite JSON value: " + value)


def _float(value):
    result = float(value)
    if not math.isfinite(result):
        _nonfinite(value)
    return result


def _json(raw, label):
    value = json.loads(raw, object_pairs_hook=_object, parse_constant=_nonfinite, parse_float=_float)
    if type(value) is not dict:
        raise AssertionError(label + " must be a JSON object")
    return value


def _public_file(root, relative):
    path = root / relative
    # Fixed paths cannot redirect the replay into an external/private tree.
    if path.resolve() != path or any(part.is_symlink() for part in (path, *path.parents) if part != root):
        raise AssertionError("Published evidence cannot be redirected: " + relative)
    if not path.is_file():
        raise FileNotFoundError("Missing published revision artifact: " + relative)
    return path


def _counts(value, expected, label):
    if type(value) is not dict:
        raise AssertionError("Invalid " + label + " object")
    for key, count in expected.items():
        if type(value.get(key)) is not int or value[key] != count:
            raise AssertionError(f"Unexpected {label}.{key}; required exact integer {count}")


def _bounded_count(value, key, maximum=None):
    count = value.get(key)
    if type(count) is not int or count < 0 or (maximum is not None and count > maximum):
        raise AssertionError("Invalid historical call_accounting." + key)
    return count


def verify_published_revision(root, *, replay=None):
    """An injected replay supports artificial tests; the CLI always uses the saved replay."""
    root = Path(root).resolve()
    paths = {name: _public_file(root, relative) for name, relative in (
        ("contract", CONTRACT_PATH), ("submissions", SUBMISSIONS_PATH), ("report", REPORT_PATH),
    )}
    raw = {name: path.read_bytes() for name, path in paths.items()}
    contract = _json(raw["contract"], "contract")
    submissions = _json(raw["submissions"], "submissions")
    report = _json(raw["report"], "report")
    if contract.get("execution_directory") != EXECUTION_DIRECTORY:
        raise AssertionError("Execution directory must equal the fixed public contract directory")
    directory = root / EXECUTION_DIRECTORY
    if (directory / "INCOMPLETE.json").exists() or (directory / ".execution-lock").exists():
        raise AssertionError("Published revision must be complete and inactive")
    required = {name: _public_file(root, EXECUTION_DIRECTORY + "/" + name)
                for name in REQUIRED_EXECUTION_FILES}
    mirrors = {"submissions": required["SUBMISSIONS.json"], "report": required["COMPLETE.json"]}
    for name, path in mirrors.items():
        if path.read_bytes() != raw[name]:
            raise AssertionError("Public " + name + " must exactly mirror its completed execution evidence")
    for value, schema, status, label in (
        (submissions, "astra-revision-submissions-v1", "ALL_200_SLOTS_FROZEN_NO_JOINED_FUTURE_OUTCOMES",
         "submissions"),
        (report, "astra-revision-result-v1", "COMPLETE_MATCHED_PREFIX_DEVELOPMENT", "report"),
    ):
        if value.get("schema") != schema or value.get("study") != STUDY or value.get("status") != status:
            raise AssertionError("Unexpected complete " + label + " identity/status")
    _counts(report.get("population"), EXPECTED_POPULATION, "population")
    counts = report.get("call_accounting")
    _counts(counts, {"hosted_calls": 80, "cheap_slots": 120, "new_slots": 200,
                     "automatic_retries": 0}, "call_accounting")
    feedback = _bounded_count(counts, "new_feedback_calls", 200)
    future = _bounded_count(counts, "new_future_calls", 200)
    _counts(counts, {"completed_new_future_calls": future}, "call_accounting")
    reused = _bounded_count(counts, "reused_future_keys")
    unique = _bounded_count(counts, "unique_future_keys")
    if unique != reused + future:
        raise AssertionError("Historical unique keys must equal reused keys plus completed new future calls")
    rows = report.get("rows")
    if type(rows) is not list or len(rows) != 200:
        raise AssertionError("All 200 ordered report rows are required")
    for row, expected in zip(rows, SLOT_ORDER, strict=True):
        if (type(row) is not dict or type(row.get("repetition")) is not int
                or (row.get("task_id"), row.get("generator"), row.get("repetition")) != expected):
            raise AssertionError("Report row identity/order differs from the fixed 200-slot population")
    _counts(report.get("analysis"), {"state_count": 10, "slot_count": 200}, "analysis")

    if replay is None:
        from alpha_research_rl.astra_revision_study import replay_revision_study

        replay = replay_revision_study
    verified = replay(source_root=root, report_path=paths["report"])
    if (type(verified) is not dict or verified.get("schema") != "astra-revision-replay-v1"
            or verified.get("study") != STUDY or verified.get("status") != "SAVED_REVISION_VERIFIED"):
        raise AssertionError("Saved revision replay did not verify the registered complete study")
    _counts(verified, EXPECTED_REPLAY_COUNTS, "replay")
    _counts(verified, {"new_future_calls": future, "completed_new_future_calls": future,
                       "reused_future_keys": reused, "unique_future_keys": unique}, "replay historical accounting")
    if verified.get("installed_runtime_revalidated") is not False:
        raise AssertionError("Saved revision replay must not require the original installed scoring runtime")
    for name, path in paths.items():
        if (verified.get(name + "_sha256") != hashlib.sha256(raw[name]).hexdigest()
                or path.read_bytes() != raw[name]):
            raise AssertionError("Verified " + name + " bytes differ from the published input")
    for name, path in mirrors.items():
        if path.read_bytes() != raw[name]:
            raise AssertionError("Completed " + name + " bytes changed during replay")
    return {
        "status": "matches_published_astra_revision_evidence", "states": 10, "slots": 200,
        "repetitions": 4, "historical_hosted_calls": 80, "historical_cheap_slots": 120,
        "historical_new_feedback_calls": feedback, "historical_new_future_calls": future,
        "reused_future_keys": reused, "unique_future_keys": unique, "replay_model_calls": 0,
        "replay_financial_scores": 0, "market_scores_recomputed": False, "raw_market_data_read": False,
        "installed_scoring_runtime_revalidated": False,
        **{name + "_sha256": verified[name + "_sha256"] for name in paths},
    }


def main():
    root = Path(__file__).resolve().parents[1]
    install_guards(root)
    summary = verify_published_revision(root)
    summary.update(training_and_financial_imports_private_data_subprocesses_and_network_disallowed=True,
                   stdlib_platform_detection_precedes_execution_guards=True,
                   guards_are_not_an_adversarial_sandbox=True)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, AssertionError, RuntimeError, ImportError) as error:
        raise SystemExit("Public Astra revision replay failed: " + str(error)) from error
