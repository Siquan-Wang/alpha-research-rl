"""Synthetic-only two-gate collection/assessment; no actual provider or market data."""

import copy
import hashlib
import json
import threading
from datetime import timedelta
from types import SimpleNamespace

import pytest
from test_astra_pool_diagnosis import ROOT, Harness, financial_manifest, metrics
from test_astra_replay import initial, transport

from alpha_research_rl import astra_pool_diagnosis as pool
from alpha_research_rl import astra_revision_core as core
from alpha_research_rl import astra_revision_study as study
from alpha_research_rl.agentic_research import canonical_json


class FakeTask:
    def __init__(self, harness, task_id):
        self.harness, self.task_id = harness, task_id

    @property
    def public_manifest(self):
        return financial_manifest(self.task_id)

    def observation(self):
        return initial()

    def feedback_score(self, expression):
        self.harness.feedback_calls.append((self.task_id, expression))
        if self.harness.feedback_failure:
            raise RuntimeError("synthetic historical failure")
        return {**metrics(-0.6 if "45" in expression else 0.5), "usable": True}

    def evaluate(self, expression):
        h = self.harness
        assert h.second_gate_verified and (h.root / study.SUBMISSIONS_PATH).is_file()
        frozen = json.loads((h.root / study.SUBMISSIONS_PATH).read_bytes())
        assert len(frozen["slots"]) == 200
        key = core.validate_proposal(canonical_json({"action": "propose", "expression": expression,
                                                   "hypothesis": "", "revision": ""}))["canonical_ast"]
        feedback = next(slot["adjudication"]["feedback"] for slot in frozen["slots"]
                        if slot["task_id"] == self.task_id and slot["adjudication"]["canonical_ast"] == key)
        h.future_calls.append((self.task_id, expression))
        if h.future_failure:
            raise KeyboardInterrupt("synthetic future interruption")
        direction = -1 if feedback["mean_ic"] < 0 else 1
        future = metrics(-0.2 if "45" in expression else 0.08)
        value = direction * future["mean_ic"]
        raw = {"expression": expression, "reward": value - 0.01, "cost": 0.01, "status": "ok", "reason": None,
               "anchor_reuse": expression.replace(" ", "") in {"ts_mean(returns,5)", "ts_mean(returns,20)"},
               "orientation": direction, "feedback": {name: value for name, value in feedback.items() if name != "usable"},
               "assessment": future, "oriented_future_ic": value, "zero_feedback_tie": feedback["mean_ic"] == 0}
        return h.future_transform(raw) if h.future_transform else raw


class RevisionHarness:
    def __init__(self, tmp_path, monkeypatch):
        old = Harness(tmp_path, monkeypatch)
        old.prepare()
        old.publish()
        old.execute()  # This constructs only the previous artificial saved cache.
        self.root, self.data = old.root, old.data
        old_result = self.root / "old-pool-result.json"
        old_result.write_bytes((old.execution / "COMPLETE.json").read_bytes())
        self.inputs = {"v1_contract": old.paths["contract"], "v1_submissions": old.paths["submissions"],
                       "v1_assessment": old.paths["assessment"], "pool_contract": old.contract_path,
                       "pool_result": old_result}
        monkeypatch.setattr(study, "INPUT_PATHS", {name: path.relative_to(self.root).as_posix()
                                                   for name, path in self.inputs.items()})
        monkeypatch.setattr(study, "INPUT_HASHES", {name: hashlib.sha256(path.read_bytes()).hexdigest()
                                                    for name, path in self.inputs.items()})
        monkeypatch.setattr(study, "RUNTIME", pool._versions())
        for relative in (*study.AUTHOR_PATHS, study.PLAN_PATH):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / relative).read_bytes())
        self.contract = None
        self.actor_calls, self.feedback_calls, self.future_calls, self.task_calls = [], [], [], []
        self.actor_failure = self.feedback_failure = self.future_failure = False
        self.future_transform = None
        self.second_gate_verified = False
        self.lock = threading.Lock()
        self.cli = {"path": "synthetic-codex-never-executed", "identity": {
            "executable_name": "codex.exe", "version": "codex-cli 0.159.2", "sha256": "c" * 64}}

    @property
    def execution(self):
        return self.root / study.PUBLIC_DIRECTORY / "execution"

    def prepare(self):
        self.contract = study.prepare_revision_study(source_root=self.root, executable_probe=lambda: self.cli)
        return self.contract

    def receipt(self, stage):
        value = {"schema": "astra-matched-prefix-publication-receipt-v1", "study": core.STUDY, "stage": stage,
                 "commit": "a" * 40, "verified_utc": pool._now(),
                 "verification_method": "root-verified unauthenticated public retrieval",
                 "public_repository_url": "https://github.com/synthetic/fixture",
                 "paths_sha256": study.publication_files(source_root=self.root, stage=stage)}
        path = self.root / study.TRANSPORT_DIRECTORY / ("publication-" + stage + ".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(canonical_json(pool._sealed(value)) + "\n", encoding="utf-8")
        return path

    def publisher(self, root, commit, bound):
        assert root == self.root and commit == "a" * 40
        assert all((root / relative).read_bytes() == raw for relative, raw in bound.items())
        if study.SUBMISSIONS_PATH in bound:
            self.second_gate_verified = True
        return {"commit": commit, "local_committed_bytes_verified": True}

    def loader(self, data_path, task):
        assert data_path == self.data
        self.task_calls.append(task)
        return FakeTask(self, task)

    def actor(self, prompt, output, **kwargs):
        assert kwargs == {"timeout_seconds": 600, "cwd": self.root / study.TRANSPORT_DIRECTORY / "actor-context",
                          "executable": self.cli["path"]}
        with self.lock:
            self.actor_calls.append(prompt)
        if self.actor_failure and json.loads(prompt.split("\nOBSERVATION:\n", 1)[1])["candidate_feedback"] == [None, None]:
            raise RuntimeError("synthetic failed transport")
        raw = canonical_json({"action": "propose", "expression": "delay(returns,46)" if
                              json.loads(prompt.split("\nOBSERVATION:\n", 1)[1])["candidate_feedback"] == [None, None]
                              else "delay(returns,45)", "hypothesis": "synthetic", "revision": "synthetic"})
        output.mkdir(parents=True, exist_ok=False)
        summary = transport(prompt, raw, 1)
        now = pool._now()
        summary.update(started_at_utc=now, ended_at_utc=now)
        files = {"prompt.txt": prompt.encode(), "response.json": raw.encode(), "schema.json": b"{}",
                 "request.json": b"{}", "events.jsonl": b"synthetic no actual CLI events", "stderr.log": b""}
        for name, content in files.items():
            (output / name).write_bytes(content)
            summary["artifacts"][name] = study._identity(content)
        return SimpleNamespace(success=True, status="succeeded", error=None, returncode=0, final_text=raw,
                               usage=summary["usage"], artifact_paths={}, public_summary=summary)

    def collect(self, task="2020-H1", repetition=1, **kwargs):
        return study.collect_pair(task, repetition, source_root=self.root,
                                  publication_receipt_path=self.root / study.TRANSPORT_DIRECTORY / "publication-preparation.json",
                                  quota={"remaining_percent": 50.0, "checked_utc": pool._now(), "provenance": "synthetic test"},
                                  task_loader=self.loader, actor_runner=self.actor, executable_probe=lambda: self.cli,
                                  publication_verifier=self.publisher, **kwargs)

    def complete_collection(self):
        self.prepare()
        self.receipt("preparation")
        for task, repetition in core.ROUND_ORDER:
            self.collect(task, repetition)
        return study.freeze_revision_study(source_root=self.root)

    def assess(self, **kwargs):
        return study.assess_revision_study(source_root=self.root,
                                          publication_receipt_path=self.root / study.TRANSPORT_DIRECTORY / "publication-submissions.json",
                                          task_loader=self.loader, publication_verifier=self.publisher, **kwargs)


@pytest.fixture
def harness(tmp_path, monkeypatch):
    return RevisionHarness(tmp_path, monkeypatch)


def test_prepare_only_binds_future_bytes_and_freezes_all_prompts_controls(harness, monkeypatch):
    opaque = {path.read_bytes() for name, path in harness.inputs.items()
              if name in {"v1_assessment", "pool_contract", "pool_result"}}
    original = pool._read

    def guard(raw):
        assert raw not in opaque, "future-valued prior artifacts must not be parsed"
        return original(raw)

    monkeypatch.setattr(pool, "_read", guard)
    monkeypatch.setattr(pool, "replay_pool_diagnosis", lambda *_a, **_k: pytest.fail("no old financial arithmetic replay"))
    contract = harness.prepare()
    assert contract["old_future_outcomes_parsed"] is False
    assert len(contract["states"]) == 10 and len(contract["cheap_packets"]) == 120
    assert len([name for name in contract["mirror_files"] if name.endswith(".txt")]) == 20
    assert harness.actor_calls == harness.feedback_calls == harness.future_calls == harness.task_calls == []
    assert all(len(value) == 64 for value in study.publication_files(source_root=harness.root, stage="preparation").values())
    with pytest.raises(ValueError, match="already exists"):
        harness.prepare()


def test_one_pair_is_bounded_and_next_pair_has_identical_prompts(harness):
    harness.prepare()
    harness.receipt("preparation")
    first = harness.collect()
    assert first["accounting"]["hosted_calls"] == 2 and len(first["slots"]) == 5
    second = harness.collect(repetition=2)
    assert len(harness.actor_calls) == 4 and sorted(harness.actor_calls[:2]) == sorted(harness.actor_calls[2:])
    assert sum(item["accounting"]["new_feedback_calls"] for item in (first, second)) == len(harness.feedback_calls)
    assert harness.future_calls == [] and len(harness.task_calls) == 2
    with pytest.raises(ValueError, match="next fixed batch"):
        harness.collect(repetition=2)
    assert len(harness.actor_calls) == 4
    with pytest.raises(ValueError, match="entire"):
        study.freeze_revision_study(source_root=harness.root)


@pytest.mark.parametrize("failure", ["actor", "feedback", "setup"])
def test_launched_results_retained_and_failures_are_permanent(harness, failure):
    harness.prepare()
    harness.receipt("preparation")
    if failure == "actor":
        harness.actor_failure = True
    elif failure == "feedback":
        harness.feedback_failure = True
    else:
        harness.cli["identity"]["sha256"] = "d" * 64
    with pytest.raises((ValueError, RuntimeError)):
        harness.collect()
    assert (harness.execution / "INCOMPLETE.json").exists()
    assert len(harness.actor_calls) == (0 if failure == "setup" else 2)
    before = len(harness.actor_calls)
    with pytest.raises(ValueError, match="INCOMPLETE"):
        harness.collect()
    assert len(harness.actor_calls) == before and harness.future_calls == []
    if failure == "actor":
        assert list((harness.root / study.TRANSPORT_DIRECTORY / "batches").glob("*/truthful/actor-result.json"))


def test_quota_unknown_stale_and_threshold_do_not_launch(harness):
    harness.prepare()
    receipt = harness.receipt("preparation")
    for percent, stamp in ((None, None), (50.0, (pool._utc(pool._now()) - timedelta(seconds=61)).isoformat())):
        result = study.collect_pair("2020-H1", 1, source_root=harness.root, publication_receipt_path=receipt,
                                    quota={"remaining_percent": percent, "checked_utc": stamp, "provenance": "synthetic"})
        assert result["status"] == "WAIT_QUOTA"
    assert not harness.execution.exists()
    result = study.collect_pair("2020-H1", 1, source_root=harness.root, publication_receipt_path=receipt,
                                quota={"remaining_percent": 5.0, "checked_utc": pool._now(), "provenance": "synthetic"})
    assert result["status"] == "INCOMPLETE" and harness.actor_calls == harness.task_calls == []


def test_quota_expiring_during_setup_retains_setup_counts_and_allows_explicit_fresh_dispatch(harness, monkeypatch):
    harness.prepare()
    harness.receipt("preparation")
    clock = [pool._utc(pool._now())]
    monkeypatch.setattr(pool, "_now", lambda: clock[0].isoformat())
    loader = harness.loader

    def slow_loader(*args):
        result = loader(*args)
        clock[0] += timedelta(seconds=61)
        return result

    harness.loader = slow_loader
    waited = harness.collect()
    assert waited == {"status": "WAIT_QUOTA", "new_calls": 0}
    assert harness.actor_calls == [] and len(harness.task_calls) == 1
    assert not (harness.execution / "INCOMPLETE.json").exists()
    first = json.loads((harness.execution / "setup-commands/001/COMPLETED.json").read_bytes())
    assert first["status"] == "WAIT_QUOTA" and first["initial_probe_checks"] == 2
    harness.loader = loader
    harness.collect()
    contract, _, history, bound = study._verified_contract(harness.root)
    completed, slots, _, captured, request = study._collection_prefix(harness.root, contract, history, bound)
    setups = study._setup_prefix(harness.execution, request, captured)
    assert len(completed) == 1 and len(slots) == 5 and len(setups) == 2
    assert len(harness.actor_calls) == 2 and len(harness.task_calls) == 2


def test_quota_expiring_before_setup_performs_no_setup_and_remains_waitable(harness, monkeypatch):
    harness.prepare()
    harness.receipt("preparation")
    clock = [pool._utc(pool._now())]
    monkeypatch.setattr(pool, "_now", lambda: clock[0].isoformat())
    publisher = harness.publisher

    def slow_gate(*args):
        result = publisher(*args)
        clock[0] += timedelta(seconds=61)
        return result

    harness.publisher = slow_gate
    assert harness.collect() == {"status": "WAIT_QUOTA", "new_calls": 0}
    assert not list((harness.execution / "setup-commands").iterdir())
    assert harness.task_calls == harness.actor_calls == []
    harness.publisher = publisher
    harness.collect()
    assert len(harness.actor_calls) == 2 and len(harness.task_calls) == 1


def test_quota_expiring_between_dispatches_retains_launched_call_without_replacement(harness, monkeypatch):
    harness.prepare()
    harness.receipt("preparation")
    clock = [pool._utc(pool._now())]
    monkeypatch.setattr(pool, "_now", lambda: clock[0].isoformat())
    write = pool._write

    def expire_after_first_dispatch(path, value):
        result = write(path, value)
        if path.name == "truthful-DISPATCH.json":
            clock[0] += timedelta(seconds=61)
        return result

    monkeypatch.setattr(pool, "_write", expire_after_first_dispatch)
    with pytest.raises(ValueError, match="hosted calls failed"):
        harness.collect()
    assert len(harness.actor_calls) == 1 and harness.feedback_calls == []
    assert list((harness.execution / "batches").glob("*/truthful-RESPONSE.json"))
    assert (harness.execution / "INCOMPLETE.json").exists()
    with pytest.raises(ValueError, match="INCOMPLETE"):
        harness.collect()
    assert len(harness.actor_calls) == 1


def test_ambiguous_started_batch_permanently_blocks_continuation(harness):
    harness.prepare()
    harness.receipt("preparation")
    harness.collect()
    completion = next((harness.execution / "batches").glob("*/COMPLETED.json"))
    completion.unlink()  # Artificial lost completion after durable STARTED.
    with pytest.raises(ValueError, match="ambiguous"):
        harness.collect(repetition=2)
    assert len(harness.actor_calls) == 2 and (harness.execution / "INCOMPLETE.json").exists()


def test_explicit_stop_reason_is_durable_and_execution_claim_is_exclusive(harness):
    harness.prepare()
    harness.receipt("preparation")
    harness.execution.mkdir()
    lock = harness.execution / ".execution-lock"
    lock.mkdir()
    with pytest.raises(FileExistsError):
        harness.collect()
    assert harness.actor_calls == harness.task_calls == []
    lock.rmdir()
    result = study.stop_revision_study(source_root=harness.root, reason="Synthetic operator stop.")
    retained = json.loads((harness.execution / "INCOMPLETE.json").read_bytes())
    assert result["reason"] == retained["reason"] == "Synthetic operator stop."
    assert retained["stage"] == "explicit-root-stop" and retained["automatic_retries"] == 0


def test_partial_freeze_write_is_retained_and_permanently_marked_incomplete(harness, monkeypatch):
    harness.prepare()
    harness.receipt("preparation")
    harness.collect()
    # Isolate the two-file commit boundary; complete-population validation is
    # independently exercised by the full-bank test below.
    artificial_bank = pool._sealed({"synthetic_write_boundary_fixture": True})
    monkeypatch.setattr(study, "_submission_body", lambda *_: artificial_bank)
    write = pool._write

    def fail_public_mirror(path, value):
        if path == harness.root / study.SUBMISSIONS_PATH:
            raise OSError("Synthetic disk failure after retained bank write")
        return write(path, value)

    monkeypatch.setattr(pool, "_write", fail_public_mirror)
    with pytest.raises(OSError, match="disk failure"):
        study.freeze_revision_study(source_root=harness.root)
    assert json.loads((harness.execution / "SUBMISSIONS.json").read_bytes()) == artificial_bank
    assert not (harness.root / study.SUBMISSIONS_PATH).exists()
    marker = json.loads((harness.execution / "INCOMPLETE.json").read_bytes())
    assert marker["stage"] == "submission-freeze-write-failure" and marker["error_type"] == "OSError"
    with pytest.raises(ValueError, match="INCOMPLETE"):
        study.freeze_revision_study(source_root=harness.root)


def test_complete_bank_gate_cache_no_rescore_and_portable_replay(harness, monkeypatch):
    frozen = harness.complete_collection()
    assert len(frozen["slots"]) == 200 and len(harness.actor_calls) == 80
    assert frozen["accounting"]["task_constructions"] == 40
    assert frozen["accounting"]["new_feedback_calls"] == len(harness.feedback_calls)
    assert harness.future_calls == []
    with pytest.raises(FileNotFoundError):
        harness.assess()
    assert harness.future_calls == [] and not harness.second_gate_verified
    harness.receipt("submissions")
    partial = harness.assess(max_jobs=1)
    assert partial["status"] == "CLEAN_COMPLETED_ASSESSMENT_PREFIX" and len(harness.future_calls) == 1
    result = harness.assess()
    assert result["status"] == "COMPLETE_MATCHED_PREFIX_DEVELOPMENT"
    assert len(harness.future_calls) == len(set(harness.future_calls))
    assert len(result["rows"]) == 200 and len(result["analysis"]["states"]) == 10
    assert all(row["candidate_Q"] == row["baseline_Q"] and row["G"] == 0.0
               for row in result["rows"] if row["generator"] == "copy")
    assert result["call_accounting"]["unique_future_keys"] == (
        result["call_accounting"]["reused_future_keys"] + result["call_accounting"]["new_future_calls"])
    harness.data.unlink()
    monkeypatch.setattr(pool, "_data_bytes", lambda *_: pytest.fail("saved replay cannot read raw data"))
    monkeypatch.setattr(pool, "_versions", lambda: pytest.fail("saved replay cannot require scoring runtime"))
    monkeypatch.setattr(study, "_load_task", lambda *_: pytest.fail("saved replay cannot construct tasks"))
    verified = study.replay_revision_study(source_root=harness.root)
    assert verified["status"] == "SAVED_REVISION_VERIFIED" and verified["new_financial_scores"] == 0
    assert verified["report_sha256"] == hashlib.sha256((harness.root / study.RESULT_PATH).read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        harness.assess()
    # A resealed one-ULP retained historical change is never aggregate tolerance.
    changed = copy.deepcopy(result)
    changed["rows"][0]["adjudication"]["feedback"]["mean_ic"] += 1e-15
    changed.pop("body_sha256")
    raw = (canonical_json(pool._sealed(changed)) + "\n").encode()
    (harness.execution / "COMPLETE.json").write_bytes(raw)
    (harness.root / study.RESULT_PATH).write_bytes(raw)
    with pytest.raises(ValueError, match="retained slot"):
        study.replay_revision_study(source_root=harness.root)
