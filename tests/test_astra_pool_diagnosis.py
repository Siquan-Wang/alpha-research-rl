"""Complete synthetic pool with the production population; no market/model/Git calls."""

import ast
import copy
import hashlib
import json
import math

import pytest
from test_astra_replay import ROOT, initial, metrics, packet, seal, synthetic, transport

from alpha_research_rl import astra_pool_diagnosis as pool
from alpha_research_rl.agentic_research import ARMS, ResearchEpisode, canonical_json
from alpha_research_rl.astra_replay import CONTRASTS, SOURCE_NAMES, TASK_IDS


def expression_index(expression):
    return ast.parse(expression.strip(), mode="eval").body.args[1].value - 1


def historical(task_index, index):
    magnitude = 0.05 * (index + 1)
    if index == 5:
        magnitude = 0.8
    elif index == 11:
        magnitude = 0.7
    elif index >= 12:
        magnitude = 0.9 + (index - 12) * 0.01 if task_index in (0, 2, 3, 4) else 0.3
    negative = task_index == 0 and 6 <= index <= 12 or task_index == 1 and 6 <= index <= 11
    return {**metrics(-magnitude if negative else magnitude), "usable": True}


def raw_outcome(task_index, expression):
    index = expression_index(expression)
    feedback = {key: value for key, value in historical(task_index, index).items() if key != "usable"}
    orientation = -1 if feedback["mean_ic"] < 0 else 1
    future = metrics(((index % 7) - 3) * 0.03 + task_index * 0.001)
    ic = orientation * future["mean_ic"]
    return {"expression": expression, "reward": ic - 0.01, "cost": 0.01, "status": "ok", "reason": None,
            "anchor_reuse": False, "orientation": orientation, "feedback": feedback, "assessment": future,
            "oriented_future_ic": ic, "zero_feedback_tie": feedback["mean_ic"] == 0}


def financial_manifest(task):
    return {"task_id": task, "split": "transfer", "year": int(task[:4]), "half": int(task[-1]),
            "horizon_sessions": 5, "diagnostic_windows": "synthetic fixture only",
            "feedback_bounds_half_open": [0, 100], "assessment_bounds_half_open": [105, 205],
            "raw_feedback_bounds_half_open": [0, 105], "raw_assessment_bounds_half_open": [105, 210],
            "feedback_label_boundary": 105, "assessment_label_boundary": 210,
            **{f"{period}_{field}": ["2020-01-01", "2020-06-01"]
               for period in ("feedback", "assessment") for field in ("signal_dates", "label_support_dates")}}


def assessment(episodes, submissions_hash):
    rows = []
    for item in episodes:
        selection = item["submission"]["selection"]
        raw = raw_outcome(TASK_IDS.index(item["task_id"]), selection["expression"])
        outcome = {**raw, "reward": raw["reward"] - 0.05, "cost": 0.06,
                   "one_proposal_reward": raw["reward"], "assessment_evaluator_called": True}
        rows.append({"task_id": item["task_id"], "arm": item["arm"], "outcome": outcome})
    lookup = {(r["task_id"], r["arm"]): r["outcome"] for r in rows}
    paired = [{"task_id": task, **{name: lookup[task, left]["reward"] - lookup[task, right]["reward"]
                                   for name, left, right in CONTRASTS}} for task in TASK_IDS]
    arms = {}
    for arm in ARMS:
        values = [lookup[task, arm] for task in TASK_IDS]
        q = math.fsum(v["oriented_future_ic"] for v in values) / 10
        arms[arm] = {"task_count": 10, "valid_assessment_count": 10, "validity_fraction_p": 1.0,
                     "predictive_contribution_q": q, "mean_utility": math.fsum(v["reward"] for v in values) / 10,
                     "conditional_valid_mean_ic": q}
    contrasts = {name: {"mean_utility_difference": math.fsum(row[name] for row in paired) / 10,
                        "validity_contribution": 0.0,
                        "predictive_contribution": arms[left]["predictive_contribution_q"]
                        - arms[right]["predictive_contribution_q"]} for name, left, right in CONTRASTS}
    years = [{"year": year, **{name: math.fsum(row[name] for row in paired if row["task_id"].startswith(str(year))) / 2
                              for name, _, _ in CONTRASTS}} for year in range(2020, 2025)]
    return seal({"study": "astra-agent-research-v1", "stage": "development-assessment-complete", "episode_count": 30,
                 "paired_task_count": 10, "results": rows, "paired": paired,
                 "primary_mean_full_minus_validity": contrasts["full_minus_validity"]["mean_utility_difference"],
                 "arm_summaries": arms, "contrasts": contrasts, "year_averages": years,
                 "submissions_sha256": submissions_hash,
                 "interpretation": "descriptive development; no untouched holdout or profitability claim"})


class FakeTask:
    def __init__(self, harness, task):
        self.harness, self.task = harness, task

    @property
    def public_manifest(self):
        return financial_manifest(self.task)

    def observation(self):
        return initial()

    def evaluate(self, expression):
        h = self.harness
        job = h.contract["pending_jobs"][len(h.calls)]
        assert (job["task_id"], job["expression"]) == (self.task, expression)
        started = h.execution / "jobs" / pool._job_name(job) / "STARTED.json"
        assert started.exists()  # A durable start precedes every fake evaluator call.
        h.calls.append((self.task, expression))
        if h.interrupt:
            raise KeyboardInterrupt("synthetic interruption")
        raw = raw_outcome(TASK_IDS.index(self.task), expression)
        return h.transform(raw, len(h.calls)) if h.transform else raw


class Harness:
    def __init__(self, tmp_path, monkeypatch):
        self.root = tmp_path / "source"
        self.root.mkdir()
        for relative in ({f"src/alpha_research_rl/{name}" for name in SOURCE_NAMES}
                         | set(pool.IMPLEMENTATION_PATHS) | {pool.PLAN_PATH, "docs/astra-agent-research-plan-v1.md"}):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / relative).read_bytes())
        self.data = self.root / "synthetic.zip"
        self.data.write_bytes(b"synthetic bytes only, never market arrays")
        self.tasks_dir = self.root / "original-tasks"
        self.tasks_dir.mkdir()
        contract, bank = copy.deepcopy(synthetic.__wrapped__())
        contract["data"]["path"] = "synthetic.zip"
        contract["runtime_versions"] = pool._versions()
        monkeypatch.setattr(pool, "RUNTIME", contract["runtime_versions"])
        self.task_raw = {}
        for task in TASK_IDS:
            value = seal({"task_id": task, "interpretation": "previously examined chronological DEVELOPMENT",
                          "financial_manifest": financial_manifest(task), "initial_observation": initial()})
            raw = (canonical_json(value) + "\n").encode()
            (self.tasks_dir / (task + ".json")).write_bytes(raw)
            contract["task_manifest_sha256"][task] = hashlib.sha256(raw).hexdigest()
            self.task_raw[task] = raw
        episodes = []
        for task_index, (task, count) in enumerate(zip(TASK_IDS, pool.POPULATION["keys_by_task"], strict=True)):
            indices = list(range(count)) + [5, *range(5)][:18 - count]
            for arm_index, arm in enumerate(ARMS):
                episode = ResearchEpisode(arm, initial(), lambda expression, ti=task_index:
                                          historical(ti, expression_index(expression)))
                summaries = []
                for attempt, index in enumerate(indices[arm_index * 6:arm_index * 6 + 6], start=1):
                    raw = packet(f"delay(returns,{index + 1})")
                    summaries.append(transport(episode.prompt(), raw, attempt))
                    episode.submit(raw)
                episodes.append({"task_id": task, "arm": arm, "submission": episode.freeze(),
                                 "transport_summaries": summaries})
        bank["episodes"] = episodes
        self.paths = {name: self.root / (name + ".json") for name in ("contract", "submissions", "assessment")}
        self.paths["contract"].write_text(canonical_json(seal(contract)), encoding="utf-8")
        bank["contract_sha256"] = hashlib.sha256(self.paths["contract"].read_bytes()).hexdigest()
        self.paths["submissions"].write_text(canonical_json(seal(bank)), encoding="utf-8")
        result = assessment(episodes, hashlib.sha256(self.paths["submissions"].read_bytes()).hexdigest())
        self.paths["assessment"].write_text(canonical_json(result), encoding="utf-8")
        monkeypatch.setattr(pool, "INPUT_HASHES", {name: hashlib.sha256(path.read_bytes()).hexdigest()
                                                  for name, path in self.paths.items()})

        def fake_data_bytes(path, expected):
            assert path == self.data and expected == contract["data"]["sha256"]
            raw = path.read_bytes()
            if raw != b"synthetic bytes only, never market arrays":
                raise ValueError("synthetic raw byte identity mismatch")
            return raw

        monkeypatch.setattr(pool, "_data_bytes", fake_data_bytes)
        self.output = self.root / pool.PUBLIC_DIRECTORY
        self.contract_path = self.output / "contract.json"
        self.execution = self.output / "execution"
        self.receipt = self.root / "publication.json"
        self.calls, self.load_calls, self.publication_calls = [], [], []
        self.transform, self.interrupt = None, False
        self.contract = None

    def prepare(self):
        self.contract = pool.prepare_pool_diagnosis(
            self.paths["contract"], self.paths["submissions"], self.paths["assessment"], self.tasks_dir,
            source_root=self.root,
        )
        return self.contract

    def publish(self):
        hashes = pool.publication_files(self.contract_path, source_root=self.root)
        self.receipt.write_text(canonical_json(seal({
            "schema": "astra-pool-publication-receipt-v1", "study": pool.STUDY, "commit": "a" * 40,
            "verified_utc": "2020-01-01T00:00:00+00:00",
            "verification_method": "root-verified unauthenticated public retrieval",
            "public_repository_url": "https://github.com/synthetic/fixture", "paths_sha256": hashes,
        })), encoding="utf-8")

    def loader(self, path):
        self.load_calls.append(path.name)
        assert path.read_bytes() == self.data.read_bytes()
        return {task: FakeTask(self, task) for task in TASK_IDS}

    def publisher(self, root, commit, bound):
        assert root == self.root and commit == "a" * 40
        assert all((root / name).read_bytes() == raw for name, raw in bound.items())
        self.publication_calls.append(commit)
        return {"commit": commit, "local_committed_bytes_verified": True}

    def execute(self, **kwargs):
        return pool.execute_pool_diagnosis(self.contract_path, self.receipt, source_root=self.root,
                                           execution_dir=self.execution, published_commit="a" * 40,
                                           task_loader=self.loader, publication_verifier=self.publisher, **kwargs)

    def replay(self):
        return pool.replay_pool_diagnosis(self.contract_path, self.execution, source_root=self.root)


@pytest.fixture
def harness(tmp_path, monkeypatch):
    return Harness(tmp_path, monkeypatch)


def test_prepare_is_manifest_only_exact_population_and_byte_mirrors(harness, monkeypatch):
    monkeypatch.setattr(pool, "_load_tasks", lambda *_: pytest.fail("prepare cannot construct tasks"))
    result = harness.prepare()
    assert result["population"] == pool.POPULATION
    assert len(result["slots"]) == 180 and len(result["keys"]) == 132
    assert len(result["pending_jobs"]) == 108
    assert sum(len(key["reuse_sources"]) for key in result["keys"]) == 30
    assert result["new_evaluator_calls"] == 0 and harness.calls == []
    for task in TASK_IDS:
        assert (harness.output / "tasks" / (task + ".json")).read_bytes() == harness.task_raw[task]
    with pytest.raises(ValueError, match="already exists"):
        harness.prepare()


def test_complete_execution_and_portable_saved_replay_without_data_or_loader(harness, monkeypatch):
    harness.prepare()
    harness.publish()
    result = harness.execute()
    assert len(harness.calls) == 108 and len(set(harness.calls)) == 108 and len(harness.load_calls) == 1
    assert result["status"] == "COMPLETE_POST_HOC"
    assert len(result["slot_results"]) == 180 and len(result["key_results"]) == 132
    assert len(result["selector_rows"]) == 30 and len(result["paired"]) == 10 and len(result["year_averages"]) == 5
    assert result["call_accounting"]["new_evaluator_calls_completed"] == 108
    assert result["slot_validity"]["all"]["denominator"] == 180
    assert result["unique_key_validity"]["denominator"] == 132
    assert any(abs(row["delta_R"]) > 0 for row in result["contrasts"].values())
    for contrast in result["contrasts"].values():
        assert contrast["delta_S"] == pytest.approx(contrast["delta_O"] - contrast["delta_R"], abs=1e-12)
    monkeypatch.setattr(pool, "_data_bytes", lambda *_: pytest.fail("replay cannot read raw data"))
    monkeypatch.setattr(pool, "_versions", lambda: pytest.fail("replay cannot require installed scoring versions"))
    monkeypatch.setattr(pool, "_load_tasks", lambda *_: pytest.fail("replay cannot construct tasks"))
    harness.data.unlink()
    assert harness.replay()["status"] == "SAVED_ARITHMETIC_VERIFIED"
    with pytest.raises(ValueError, match="replay only"):
        harness.execute()
    assert len(harness.calls) == 108


def test_clean_prefix_continues_without_a_second_call_to_any_key(harness):
    harness.prepare()
    harness.publish()
    partial = harness.execute(max_jobs=2)
    assert partial["status"] == "CLEAN_COMPLETED_PREFIX" and partial["completed_new_jobs"] == 2
    assert not (harness.execution / "COMPLETE.json").exists()
    with pytest.raises(ValueError, match="incomplete"):
        harness.replay()
    result = harness.execute()
    assert result["status"] == "COMPLETE_POST_HOC" and len(harness.calls) == len(set(harness.calls)) == 108


@pytest.mark.parametrize("status", ["invalid", "unscorable"])
def test_future_failures_preserve_full_slot_denominators(harness, status):
    harness.prepare()
    harness.publish()

    def fail(raw, call):
        if call == 1:
            raw.update(status=status, reason="invalid_expression" if status == "invalid"
                       else "insufficient_assessment_support", assessment=None if status == "invalid"
                       else {**metrics(None), "ic_std": None, "coverage": 0.0, "n_dates": 0},
                       reward=-1.01, oriented_future_ic=None)
        return raw

    harness.transform = fail
    result = harness.execute()
    assert result["slot_validity"]["all"]["denominator"] == 180
    failed_slots = [row for row in result["slot_results"] if not row["diagnosis"]["valid"]]
    assert failed_slots and all(row["diagnosis"]["utility"] == -1.06 for row in failed_slots)
    assert result["unique_key_validity"]["invalid_count"] == 1
    assert harness.replay()["status"] == "SAVED_ARITHMETIC_VERIFIED"


@pytest.mark.parametrize("field,value", [("orientation", -1), ("feedback", None), ("reward", float("nan"))])
def test_integrity_failure_retains_raw_stops_and_cannot_resume(harness, field, value):
    harness.prepare()
    harness.publish()
    harness.transform = lambda raw, _: {**raw, field: value}
    with pytest.raises(ValueError):
        harness.execute()
    assert len(harness.calls) == 1
    failed = json.loads((harness.execution / "INCOMPLETE.json").read_text())
    assert failed["raw_return_available"] is True
    with pytest.raises(ValueError, match="INCOMPLETE"):
        harness.execute()
    assert len(harness.calls) == 1


def test_ambiguous_interruption_blocks_and_exclusive_lock_prevents_concurrent_start(harness):
    harness.prepare()
    harness.publish()
    harness.execution.mkdir()
    lock = harness.execution / ".execution-lock"
    lock.mkdir()
    with pytest.raises(FileExistsError):
        harness.execute()
    assert harness.calls == harness.load_calls == []
    lock.rmdir()
    harness.interrupt = True
    with pytest.raises(KeyboardInterrupt):
        harness.execute()
    assert len(harness.calls) == 1 and (harness.execution / "INCOMPLETE.json").exists()
    with pytest.raises(ValueError, match="INCOMPLETE"):
        harness.execute()
    assert len(harness.calls) == 1


def test_interruption_after_durable_completion_recovers_by_validation_without_rescore(harness, monkeypatch):
    harness.prepare()
    harness.publish()
    original_write = pool._write

    def interrupt_after_completion(path, value):
        original_write(path, value)
        if path.name == "COMPLETED.json":
            raise KeyboardInterrupt("synthetic after completed file")

    monkeypatch.setattr(pool, "_write", interrupt_after_completion)
    with pytest.raises(KeyboardInterrupt):
        harness.execute()
    assert len(harness.calls) == 1 and not (harness.execution / "INCOMPLETE.json").exists()
    monkeypatch.setattr(pool, "_write", original_write)
    result = harness.execute(max_jobs=1)
    assert result["completed_new_jobs"] == 2 and len(set(harness.calls)) == 2


@pytest.mark.parametrize("kind", ["future-receipt", "missing-public-path", "changed-data", "changed-source"])
def test_all_gates_fail_before_task_loading_or_evaluation(harness, kind):
    harness.prepare()
    harness.publish()
    if kind in ("future-receipt", "missing-public-path"):
        value = json.loads(harness.receipt.read_text())
        if kind == "future-receipt":
            value["verified_utc"] = "2999-01-01T00:00:00+00:00"
        else:
            value["paths_sha256"].pop(next(iter(value["paths_sha256"])))
        harness.receipt.write_text(canonical_json(seal(value)), encoding="utf-8")
    elif kind == "changed-data":
        harness.data.write_bytes(b"changed synthetic input")
    else:
        path = harness.root / "src/alpha_research_rl/financial_tasks.py"
        path.write_bytes(path.read_bytes() + b"\n# synthetic tampering\n")
    with pytest.raises(ValueError):
        harness.execute()
    assert harness.calls == harness.load_calls == []


def test_changed_task_file_blocks_prepare_before_any_output(harness):
    path = harness.tasks_dir / "2020-H1.json"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="task bytes"):
        harness.prepare()
    assert not harness.output.exists() and harness.calls == []


def test_bound_directory_and_corrupt_completed_prefix_cannot_be_bypassed(harness):
    harness.prepare()
    harness.publish()
    with pytest.raises(ValueError, match="directory differs"):
        pool.execute_pool_diagnosis(harness.contract_path, harness.receipt, source_root=harness.root,
                                    execution_dir=harness.root / "replacement", published_commit="a" * 40,
                                    task_loader=harness.loader, publication_verifier=harness.publisher)
    harness.execute(max_jobs=1)
    result_path = next((harness.execution / "jobs").glob("*/COMPLETED.json"))
    value = json.loads(result_path.read_text())
    value["raw_outcome"]["reward"] += 0.1
    result_path.write_text(canonical_json(seal(value)), encoding="utf-8")
    with pytest.raises(ValueError):
        harness.execute()
    assert len(harness.calls) == 1 and (harness.execution / "INCOMPLETE.json").exists()


def test_production_data_hash_checker_rejects_wrong_bytes(tmp_path):
    # This test has no Harness monkeypatch; it exercises the real byte hash boundary.
    path = tmp_path / "synthetic.dat"
    path.write_bytes(b"synthetic")
    assert pool._data_bytes(path, hashlib.sha256(b"synthetic").hexdigest()) == b"synthetic"
    with pytest.raises(ValueError, match="byte identity"):
        pool._data_bytes(path, "0" * 64)
