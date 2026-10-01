"""Durability and chronology gates use fake tasks/providers, never market/model calls."""

import copy
import hashlib
import json
from types import SimpleNamespace

import pytest

from alpha_research_rl import astra_study as study
from alpha_research_rl.agentic_research import ARMS


def metrics(value=0.02):
    return {"mean_ic": value, "coverage": 1.0, "ic_std": 0.1,
            "n_dates": 100, "n_signal_dates": 100, "usable": True}


def initial():
    overall = {key: value for key, value in metrics().items() if key != "usable"}
    return {"supported_features": ["returns"], "max_lookback": 60, "horizon_sessions": 5,
            "proposal_cost": 0.01, "probe_evidence": [
                {"expression": expression, "feedback": copy.deepcopy(overall), "feedback_usable": True,
                 "windows": [copy.deepcopy(overall) for _ in range(3)]}
                for expression in ("ts_mean(returns,5)", "ts_mean(returns,20)")]}


class FakeTask:
    def __init__(self, task_id, harness):
        self.task_id = task_id
        self.harness = harness

    @property
    def public_manifest(self):
        return {"task_id": self.task_id, "synthetic_fixture": True,
                "year": int(self.task_id[:4]), "half": int(self.task_id[-1])}

    def observation(self):
        return initial()

    def feedback_score(self, expression):
        self.harness.feedback_calls.append((self.task_id, expression))
        if self.harness.broker_failure:
            raise RuntimeError("injected feedback failure")
        return metrics(0.02 + self.harness.feedback_drift)

    def evaluate(self, expression):
        self.harness.assessment_calls.append((self.task_id, expression))
        if len(self.harness.assessment_calls) == self.harness.fail_assessment_at:
            raise RuntimeError("injected assessment failure")
        index = study.TASK_IDS.index(self.task_id)
        ic = 0.1 + index / 1000
        unscorable = self.harness.unscorable
        if self.harness.mixed_assessment:
            arm = (int(expression.rsplit(",", 1)[1][:-1]) - 1) // 10
            unscorable = index in ({1, 6}, {2}, {0, 3, 4})[arm]
            ic = (0.2 if index % 2 == 0 else -0.1) if arm == 0 else (0.05 if arm == 1 else -0.02)
        if unscorable:
            return {"status": "unscorable", "reason": "insufficient_assessment_support",
                    "orientation": 1, "oriented_future_ic": None, "reward": -1.01, "cost": 0.01}
        return {"status": "ok", "orientation": 1, "oriented_future_ic": ic,
                "reward": ic - 0.01, "cost": 0.01}


class FakeProvider:
    def __init__(self, *, failure_arm=None, exception_arm=None, invalid=False, crlf=False,
                 different_by_arm=False):
        self.calls = []
        self.working_directories = []
        self.failure_arm = failure_arm
        self.exception_arm = exception_arm
        self.invalid = invalid
        self.crlf = crlf
        self.different_by_arm = different_by_arm

    def __call__(self, prompt, output_dir, *, timeout_seconds, cwd, executable):
        assert timeout_seconds == 600
        assert executable.endswith("fake-codex.exe")
        assert (output_dir.parent / "prompt.txt").read_bytes().decode("utf-8") == prompt
        assert cwd.name == "actor-context"
        self.working_directories.append(cwd)
        arm = output_dir.parent.name
        self.calls.append((arm, prompt))
        if arm == self.exception_arm:
            raise RuntimeError("injected provider exception")
        observation = json.loads(prompt.split("\nObservation:\n", 1)[1])
        attempt = observation["budget"]["used_attempts"] + 1
        lookback = attempt + (10 * ARMS.index(arm) if self.different_by_arm else 0)
        packet = {"action": "propose", "expression": f"delay(returns,{lookback})",
                  "hypothesis": "Synthetic test only.", "revision": "No real evidence used."}
        raw = "invalid completed packet" if self.invalid else json.dumps(packet, indent=2)
        if self.crlf:
            raw = raw.replace("\n", "\r\n")
        output_dir.mkdir(parents=True, exist_ok=False)
        (output_dir / "events.jsonl").write_bytes(b'{"synthetic_transport":true}\n')
        (output_dir / "response.txt").write_bytes(raw.encode())
        success = arm != self.failure_arm
        usage = {"input_tokens": 10, "output_tokens": 5}
        return SimpleNamespace(success=success, error=None if success else "synthetic_transport_failure",
                               final_text=raw if success else None, usage=usage,
                               artifact_paths={"events": str(output_dir / "events.jsonl")},
                               public_summary={"synthetic_provider": True, "success": success, "usage": usage})


class Harness:
    def __init__(self, root):
        self.root = root
        self.directory = root / ".local" / "study"
        self.data = root / "data" / "fake.dat"
        self.plan = root / "docs" / "plan.md"
        self.feedback_calls = []
        self.assessment_calls = []
        self.feedback_drift = 0
        self.broker_failure = False
        self.fail_assessment_at = None
        self.unscorable = False
        self.mixed_assessment = False
        self.publication_calls = []
        for name in study.SOURCE_FILES:
            path = root / "src" / "alpha_research_rl" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"synthetic source fixture: {name}", encoding="utf-8")
        self.data.parent.mkdir(parents=True)
        self.data.write_bytes(b"synthetic data identity; no market values")
        self.plan.parent.mkdir(parents=True)
        self.plan.write_text("synthetic protocol fixture\n", encoding="utf-8")
        self.executable = root / "fake-codex.exe"
        self.executable.write_bytes(b"not an executable; never invoked")

    def probe(self):
        return {"path": str(self.executable), "identity": {"executable_name": self.executable.name,
                "sha256": hashlib.sha256(self.executable.read_bytes()).hexdigest(),
                "version": "codex-cli 0.159.2"}}

    def tasks(self, data_path, ids):
        assert data_path.resolve() == self.data.resolve()
        return tuple(FakeTask(task_id, self) for task_id in ids)

    def publication(self, root, commit, paths):
        assert root == self.root and commit == "a" * 40
        assert all(path.exists() for path in paths)
        assert self.root / study.PUBLIC_CONTRACT in paths
        assert all(".local" not in str(path.relative_to(root)) for path in paths)
        self.publication_calls.append(paths)
        return {"synthetic_publication_check": True, "commit": commit}

    def prepare(self):
        return study.prepare_study(self.directory, self.data, self.plan, root=self.root,
                                   task_loader=self.tasks, executable_probe=self.probe)

    def collect(self, task_id=study.TASK_IDS[0], attempt=1, provider=None, remaining=99):
        return study.collect_round(self.directory, task_id, attempt, root=self.root,
                                   contract_commit="a" * 40, quota_remaining_percent=remaining,
                                   task_loader=self.tasks, actor_runner=provider or FakeProvider(),
                                   publication_verifier=self.publication, executable_probe=self.probe)

    def complete(self, provider=None):
        provider = provider or FakeProvider()
        for task_id, attempt in study.ROUND_ORDER:
            assert self.collect(task_id, attempt, provider)["status"] == "COMPLETE"
        return provider

    def freeze(self):
        return study.freeze_study(self.directory, root=self.root, task_loader=self.tasks)

    def assess(self):
        return study.assess_study(self.directory, root=self.root, published_commit="a" * 40,
                                  task_loader=self.tasks, publication_verifier=self.publication)


@pytest.fixture
def harness(tmp_path):
    return Harness(tmp_path)


def test_prepare_freezes_exact_development_bank_and_public_mirror_without_assessment(harness):
    contract = harness.prepare()
    assert contract["task_order"] == list(study.TASK_IDS)
    assert contract["round_order"] == [list(item) for item in study.ROUND_ORDER]
    assert contract["assessment_score_calls"] == 0
    assert len(contract["task_manifest_sha256"]) == 10
    assert contract["data"]["sha256"] == hashlib.sha256(harness.data.read_bytes()).hexdigest()
    assert (harness.directory / "contract.json").read_bytes() == (
        harness.root / study.PUBLIC_CONTRACT).read_bytes()
    assert str(harness.root) not in json.dumps(contract)
    assert harness.assessment_calls == []
    with pytest.raises(FileExistsError):
        harness.prepare()


def test_one_round_exactly_three_calls_rotates_and_refuses_repeats_or_wrong_order(harness):
    harness.prepare()
    provider = FakeProvider()
    assert harness.collect(provider=provider)["status"] == "COMPLETE"
    assert len(provider.calls) == 3
    assert harness.assessment_calls == []
    with pytest.raises(ValueError, match="next registered"):
        harness.collect(provider=provider)
    with pytest.raises(ValueError, match="next registered"):
        harness.collect(study.TASK_IDS[1], 1, provider)
    assert len(provider.calls) == 3
    harness.collect(attempt=2, provider=provider)
    request = json.loads((harness.directory / "rounds" / "2020-H1" / "02" / "request.json").read_text())
    assert request["launch_order"] == [ARMS[1], ARMS[2], ARMS[0]]
    assert len(provider.calls) == 6
    assert set(provider.working_directories) == {harness.directory / "actor-context"}


@pytest.mark.parametrize("remaining", [None, -1, True, float("nan"), 101])
def test_unverified_or_exhausted_quota_starts_nothing_and_preserves_prior_work(harness, remaining):
    harness.prepare()
    provider = FakeProvider()
    with pytest.raises(ValueError, match="quota"):
        harness.collect(provider=provider, remaining=remaining)
    assert provider.calls == []
    assert not (harness.directory / "INCOMPLETE.json").exists()


@pytest.mark.parametrize("remaining", [0, 4.9, 5])
def test_confirmed_quota_stop_marks_incomplete_and_retains_completed_round(harness, remaining):
    harness.prepare()
    provider = FakeProvider()
    harness.collect(provider=provider)
    first = harness.directory / "rounds/2020-H1/01/round.json"
    before = first.read_bytes()
    with pytest.raises(ValueError, match="quota stop"):
        harness.collect(attempt=2, provider=provider, remaining=remaining)
    assert len(provider.calls) == 3 and first.read_bytes() == before
    assert (harness.directory / "INCOMPLETE.json").is_file()
    with pytest.raises(ValueError, match="INCOMPLETE"):
        harness.freeze()


@pytest.mark.parametrize("changed", ["source", "data", "plan", "executable"])
def test_changed_identity_stops_before_actor(harness, changed):
    harness.prepare()
    path = {"source": harness.root / "src/alpha_research_rl/agentic_research.py",
            "data": harness.data, "plan": harness.plan, "executable": harness.executable}[changed]
    path.write_bytes(path.read_bytes() + b"changed")
    provider = FakeProvider()
    with pytest.raises(ValueError, match="changed"):
        harness.collect(provider=provider)
    assert provider.calls == []


@pytest.mark.parametrize("failure", ["returned", "raised", "broker"])
def test_failure_is_durable_and_all_launched_siblings_are_retained_without_retry(harness, failure):
    harness.prepare()
    provider = FakeProvider(failure_arm=ARMS[0] if failure == "returned" else None,
                            exception_arm=ARMS[0] if failure == "raised" else None)
    harness.broker_failure = failure == "broker"
    report = harness.collect(provider=provider)
    assert report["status"] == "INCOMPLETE"
    assert len(provider.calls) == 3
    assert (harness.directory / "INCOMPLETE.json").is_file()
    for arm in ARMS:
        path = harness.directory / "rounds/2020-H1/01/arms" / arm
        assert (path / "prompt.txt").is_file() and (path / "checkpoint.json").is_file()
    if failure != "broker":
        assert report["arms"][ARMS[1]] == report["arms"][ARMS[2]] == "COMPLETE"
    else:
        checkpoint = json.loads((harness.directory / "rounds/2020-H1/01/arms" /
                                 ARMS[0] / "checkpoint.json").read_text())
        assert checkpoint["failed"] and checkpoint["attempt_count"] == 1
        assert checkpoint["records"][0]["cost"] == .01
    with pytest.raises(ValueError, match="INCOMPLETE"):
        harness.collect(attempt=2, provider=provider)
    with pytest.raises(ValueError, match="INCOMPLETE"):
        harness.freeze()
    assert len(provider.calls) == 3 and harness.assessment_calls == []


def test_replay_detects_changed_feedback_before_new_actor(harness):
    harness.prepare()
    provider = FakeProvider()
    harness.collect(provider=provider)
    harness.feedback_drift = 0.01
    with pytest.raises(ValueError, match="feedback replay"):
        harness.collect(attempt=2, provider=provider)
    assert len(provider.calls) == 3
    assert harness.assessment_calls == []


def test_collection_interruption_preserves_request_and_marks_no_retry(harness, monkeypatch):
    harness.prepare()

    class InterruptedExecutor:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            raise KeyboardInterrupt

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(study, "ThreadPoolExecutor", InterruptedExecutor)
    with pytest.raises(KeyboardInterrupt):
        harness.collect()
    assert (harness.directory / "rounds/2020-H1/01/request.json").exists()
    failure = json.loads((harness.directory / "INCOMPLETE.json").read_text())
    assert failure["stage"] == "collection-interrupted" and failure["retries"] == 0


def test_tampered_transport_evidence_blocks_new_actor(harness):
    harness.prepare()
    provider = FakeProvider()
    harness.collect(provider=provider)
    path = harness.directory / "rounds/2020-H1/01/arms" / ARMS[0] / "provider/events.jsonl"
    path.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="durable hashes"):
        harness.collect(attempt=2, provider=provider)
    assert len(provider.calls) == 3


def test_incomplete_bank_cannot_freeze_or_assess(harness):
    harness.prepare()
    harness.collect()
    with pytest.raises(ValueError, match="all 60"):
        harness.freeze()
    with pytest.raises(FileNotFoundError):
        harness.assess()
    assert harness.assessment_calls == []


def test_all_180_crlf_responses_freeze_before_only_30_selected_assessments(harness):
    harness.prepare()
    provider = harness.complete(FakeProvider(crlf=True, different_by_arm=True))
    assert len(provider.calls) == 180 and harness.assessment_calls == []
    frozen = harness.freeze()
    assert frozen["episode_count"] == 30 and frozen["completed_response_count"] == 180
    assert len(frozen["episodes"]) == 30 and len(frozen["round_sha256"]) == 60
    assert harness.assessment_calls == []
    assert (harness.directory / "submissions.json").read_bytes() == (
        harness.root / study.PUBLIC_SUBMISSIONS).read_bytes()
    harness.mixed_assessment = True
    report = harness.assess()
    assert len(harness.assessment_calls) == 30 and len(provider.calls) == 180
    assert [expression for _, expression in harness.assessment_calls] == [
        "delay(returns,1)", "delay(returns,11)", "delay(returns,21)"] * 10
    assert report["episode_count"] == 30 and report["paired_task_count"] == 10
    assert len(report["paired"]) == 10 and len(report["year_averages"]) == 5
    assert len(report["contrasts"]) == 3
    assert report["primary_mean_full_minus_validity"] == pytest.approx(-.105)
    assert report["results"][0]["outcome"]["reward"] == pytest.approx(.14)
    for arm, count, q in zip(ARMS, (8, 9, 7), (.04, .045, -.014), strict=True):
        assert report["arm_summaries"][arm]["valid_assessment_count"] == count
        assert report["arm_summaries"][arm]["predictive_contribution_q"] == pytest.approx(q)
    expected = {"full_minus_validity": (-.105, -.1, -.005),
                "full_minus_withheld": (.154, .1, .054),
                "validity_minus_withheld": (.259, .2, .059)}
    for name, (total, validity, predictive) in expected.items():
        assert report["contrasts"][name]["mean_utility_difference"] == pytest.approx(total)
        assert report["contrasts"][name]["validity_contribution"] == pytest.approx(validity)
        assert report["contrasts"][name]["predictive_contribution"] == pytest.approx(predictive)
    assert [row["full_minus_validity"] for row in report["year_averages"]] == pytest.approx(
        [-.45, .525, 0, -.6, 0])
    with pytest.raises(FileExistsError):
        harness.assess()
    assert len(harness.assessment_calls) == 30


def test_null_selections_still_have_30_outcomes_no_evaluator_and_fixed_penalty(harness):
    harness.prepare()
    harness.complete(FakeProvider(invalid=True))
    harness.freeze()
    report = harness.assess()
    assert harness.assessment_calls == []
    assert len(report["results"]) == 30
    assert all(row["outcome"]["reward"] == -1.06 for row in report["results"])
    assert all(row["conditional_valid_mean_ic"] is None for row in report["arm_summaries"].values())


def test_unscorable_selection_gets_registered_penalty_without_an_alternate_candidate(harness):
    harness.prepare()
    harness.complete()
    harness.freeze()
    harness.unscorable = True
    report = harness.assess()
    assert len(harness.assessment_calls) == 30
    assert all(row["outcome"]["reward"] == pytest.approx(-1.06) for row in report["results"])
    assert all(expression == "delay(returns,1)" for _, expression in harness.assessment_calls)


def test_assessment_exception_retains_prior_outcomes_and_blocks_retries(harness):
    harness.prepare()
    harness.complete()
    harness.freeze()
    harness.fail_assessment_at = 4
    with pytest.raises(RuntimeError, match="injected assessment"):
        harness.assess()
    output = harness.directory / "assessment"
    failure = json.loads((output / "failure.json").read_text())
    assert failure["completed_outcome_count"] == 3
    assert len(list(output.glob("2020-H1-*.json"))) == 3
    assert not (output / "results.json").exists()
    with pytest.raises(ValueError, match="INCOMPLETE"):
        harness.assess()
    assert len(harness.assessment_calls) == 4


def test_rehashed_incomplete_freeze_is_rejected_before_assessment(harness):
    harness.prepare()
    harness.complete()
    frozen = harness.freeze()
    frozen["episodes"] = frozen["episodes"][:-1]
    frozen["body_sha256"] = study.digest({key: value for key, value in frozen.items() if key != "body_sha256"})
    data = study.canonical_json(frozen) + "\n"
    for path in (harness.directory / "submissions.json", harness.root / study.PUBLIC_SUBMISSIONS):
        path.write_text(data, encoding="utf-8")
    with pytest.raises(ValueError, match="differ from"):
        harness.assess()
    assert harness.assessment_calls == []


def test_task_loader_order_is_verified(harness):
    with pytest.raises(ValueError, match="task order"):
        study.prepare_study(harness.directory, harness.data, harness.plan, root=harness.root,
                            task_loader=lambda path, ids: reversed(harness.tasks(path, ids)),
                            executable_probe=harness.probe)
    assert (harness.directory / "INCOMPLETE.json").exists()
