"""Independent adversarial review fixtures; no market arrays or real evaluator."""

import ast
import builtins
import copy
import json
import math

import pytest
from test_astra_pool_diagnosis import Harness

from alpha_research_rl import astra_pool_diagnosis as diagnosis


def _fixture(expression="returns"):
    history = {"mean_ic": -0.2, "coverage": 1.0, "ic_std": 0.1,
               "n_dates": 100, "n_signal_dates": 100}
    future = {"mean_ic": -0.25, "coverage": 1.0, "ic_std": 0.2,
              "n_dates": 100, "n_signal_dates": 100}
    key = {"evaluation_expression": expression, "orientation": -1,
           "canonical_ast": ast.dump(ast.parse(expression, mode="eval"), include_attributes=False),
           "feedback": copy.deepcopy(history)}
    task = {"financial_manifest": {"feedback_bounds_half_open": [0, 100],
                                    "assessment_bounds_half_open": [105, 205]}}
    raw = {"expression": expression, "reward": 0.24, "cost": 0.01, "status": "ok",
           "reason": None, "anchor_reuse": False, "orientation": -1,
           "feedback": copy.deepcopy(history), "assessment": future,
           "oriented_future_ic": 0.25, "zero_feedback_tie": False}
    return key, task, raw


def test_negative_historical_direction_is_preserved_not_chosen_from_future():
    key, task, raw = _fixture()
    result = diagnosis._outcome(raw, key, task)
    assert result == {"status": "ok", "valid": True, "oriented_future_ic": 0.25,
                      "utility": 0.19, "cost": 0.06}
    raw["assessment"]["mean_ic"] = 0.25
    raw.update(oriented_future_ic=-0.25, reward=-0.26)
    assert diagnosis._outcome(raw, key, task)["utility"] == -0.31


@pytest.mark.parametrize("source", ["new_raw", "cached_v1"])
def test_fixed_cost_metadata_does_not_receive_arithmetic_tolerance(source):
    key, task, raw = _fixture()
    if source == "new_raw":
        raw["cost"] = math.nextafter(0.01, math.inf)
        with pytest.raises(ValueError):
            diagnosis._outcome(raw, key, task)
    else:
        raw.update(cost=math.nextafter(0.06, math.inf), reward=0.19,
                   one_proposal_reward=0.24, assessment_evaluator_called=True)
        with pytest.raises(ValueError):
            diagnosis._raw_from_v1(raw)


@pytest.mark.parametrize("field,value", [
    ("mean_ic", math.nextafter(-0.2, -math.inf)),
    ("coverage", 0.999),
    ("ic_std", 0.11),
    ("n_dates", 99),
    ("n_signal_dates", 101),
    ("n_dates", True),
])
def test_historical_drift_is_rejected_even_when_reward_still_looks_consistent(field, value):
    key, task, raw = _fixture()
    raw["feedback"][field] = value
    with pytest.raises(ValueError):
        diagnosis._outcome(raw, key, task)


@pytest.mark.parametrize("field,value", [("orientation", 1), ("orientation", True),
                                          ("zero_feedback_tie", True)])
def test_historical_direction_and_tie_metadata_are_exact(field, value):
    key, task, raw = _fixture()
    raw[field] = value
    with pytest.raises(ValueError):
        diagnosis._outcome(raw, key, task)


def test_future_failure_is_penalized_but_missing_history_is_not_a_financial_failure():
    key, task, raw = _fixture()
    raw.update(status="invalid", reason="invalid_expression", assessment=None,
               oriented_future_ic=None, reward=-1.01)
    result = diagnosis._outcome(raw, key, task)
    assert result["valid"] is False
    assert result["utility"] == -1.06
    raw["feedback"] = None
    with pytest.raises(ValueError):
        diagnosis._outcome(raw, key, task)


def test_unscorable_support_cannot_be_relabelled_as_a_caught_invalid_exception():
    key, task, raw = _fixture()
    raw["assessment"].update(mean_ic=None, ic_std=None, n_dates=0)
    raw.update(status="unscorable", reason="insufficient_assessment_support",
               oriented_future_ic=None, reward=-1.01)
    assert diagnosis._outcome(raw, key, task)["utility"] == -1.06
    raw.update(status="invalid", reason="invalid_expression")
    with pytest.raises(ValueError):
        diagnosis._outcome(raw, key, task)


@pytest.mark.parametrize("count,mean,spread", [
    (0, 0.0, None), (0, None, 0.0), (0, 0.0, 0.0),
    (100, None, 0.1), (100, 0.1, None), (100, None, None),
])
def test_metric_nullness_must_match_number_of_valid_dates(count, mean, spread):
    metric = {"mean_ic": mean, "coverage": 1.0, "ic_std": spread,
              "n_dates": count, "n_signal_dates": 100}
    with pytest.raises(ValueError):
        diagnosis._metric(metric, 100)


def _alias_tables(conflict=False):
    key, task, raw = _fixture()
    episodes, rows = [], []
    for arm, expression in zip(("full_feedback", "validity_only"), ("returns", "(returns)"), strict=True):
        feedback = {**key["feedback"], "usable": True}
        episodes.append({"task_id": "2020-H1", "arm": arm, "submission": {
            "records": [{"attempt": 1, "canonical_ast": key["canonical_ast"],
                         "feedback": feedback, "canonical_duplicate": False,
                         "packet": {"expression": expression}}],
            "selection": {"attempt": 1}}})
        outcome = copy.deepcopy(raw)
        outcome.update(expression=expression, cost=0.06, reward=0.19,
                       one_proposal_reward=0.24, assessment_evaluator_called=True)
        if conflict and arm == "validity_only":
            # Below arithmetic tolerance, but exact duplicated cache evidence must agree.
            outcome["assessment"]["mean_ic"] = math.nextafter(-0.25, -math.inf)
        rows.append({"task_id": "2020-H1", "arm": arm, "outcome": outcome})
    return {"episodes": episodes}, {"results": rows}, {"2020-H1": task}


def test_cache_aliases_keep_each_evaluated_spelling_without_new_jobs():
    slots, keys, _, jobs = diagnosis._tables(*_alias_tables())
    assert len(keys) == 1
    assert jobs == []
    assert [slot["expression"] for slot in slots] == ["returns", "(returns)"]
    assert keys[0]["evaluation_expression"] == "returns"
    assert [source["outcome"]["expression"] for source in keys[0]["reuse_sources"]] == [
        "returns", "(returns)"]


def test_conflicting_alias_cache_is_not_accepted_with_arithmetic_tolerance():
    with pytest.raises(ValueError, match="conflicting cache reuse"):
        diagnosis._tables(*_alias_tables(conflict=True))


def test_nonzero_signed_selection_decomposition_keeps_invalid_tasks():
    # Hand calculation: full S=-.10, validity S=-.07; full O=.24,
    # validity O=.19. Hence delta S=-.03 = delta O(.05)-delta R(.08).
    def outcome(ic):
        return {"valid": ic is not None, "oriented_future_ic": ic,
                "utility": -1.06 if ic is None else ic - 0.06}

    rows = []
    for index, task in enumerate(diagnosis.TASK_IDS):
        for arm in diagnosis.ARMS:
            if arm == "full_feedback":
                original, oracle = outcome(None if index < 2 else 0.2), outcome(0.3)
            elif arm == "validity_only":
                original, oracle = outcome(None if index < 1 else 0.1), outcome(0.25)
            else:
                original, oracle = outcome(-0.05), outcome(0.05)
            selectors = {"original": {"diagnosis": original}, "first": {"diagnosis": original},
                         "minimum_ast": {"diagnosis": outcome(None)}, "oracle": {"diagnosis": oracle}}
            rows.append({"task_id": task, "arm": arm, "selectors": selectors,
                         "selection_gap_R": oracle["utility"] - original["utility"],
                         "first_minus_original": 0.0,
                         "minimum_ast_minus_original": -1.06 - original["utility"]})
    summaries = diagnosis._arm_summaries(rows)
    full = summaries["full_feedback"]["selectors"]["original"]
    assert full["denominator"] == 10
    assert full["valid_count"] == full["conditional_valid_count"] == 8
    assert full["invalid_count"] == 2
    assert full["mean_utility"] == pytest.approx(-0.1)
    assert full["predictive_contribution_q"] == pytest.approx(0.16)
    assert full["conditional_valid_mean_ic"] == pytest.approx(0.2)
    failed = summaries["full_feedback"]["selectors"]["minimum_ast"]
    assert failed["denominator"] == failed["invalid_count"] == 10
    assert failed["conditional_valid_count"] == 0
    assert failed["conditional_valid_mean_ic"] is None
    contrast = diagnosis._contrasts(summaries)["full_minus_validity"]
    assert contrast["delta_S"] == pytest.approx(-0.03)
    assert contrast["delta_O"] == pytest.approx(0.05)
    assert contrast["delta_R"] == pytest.approx(0.08)
    assert contrast["selectors"]["original"]["validity_contribution"] == pytest.approx(-0.1)
    assert contrast["selectors"]["original"]["predictive_contribution"] == pytest.approx(0.07)
    for year in range(2020, 2025):
        yearly = diagnosis._arm_summaries([row for row in rows if row["task_id"].startswith(str(year))])
        assert yearly["full_feedback"]["selectors"]["original"]["denominator"] == 2
        expected = -0.55 if year == 2020 else 0.1
        assert diagnosis._contrasts(yearly)["full_minus_validity"]["delta_S"] == pytest.approx(expected)


def test_first_is_literal_and_minimum_ast_ignores_ineligible_slots_not_future_outcomes():
    key, task, raw = _fixture("delay(returns,1)")
    records = []
    for attempt, expression in enumerate((None, "returns", "(returns)", "delay(returns,1)",
                                        "ts_mean(returns,2)", "neg(returns)"), start=1):
        feedback = {**key["feedback"], "usable": True}
        if attempt == 4:
            feedback["mean_ic"] = -0.3
        if attempt == 6:
            feedback.update(mean_ic=None, ic_std=None, n_dates=0, usable=False)
        records.append({"attempt": attempt,
                        "canonical_ast": None if expression is None else ast.dump(
                            ast.parse(expression, mode="eval"), include_attributes=False),
                        "feedback": None if expression is None else feedback,
                        "canonical_duplicate": attempt == 3,
                        "packet": None if expression is None else {"expression": expression}})
    raw["feedback"]["mean_ic"] = -0.3
    raw.update(cost=0.06, reward=0.19, one_proposal_reward=0.24, assessment_evaluator_called=True)
    bank = {"episodes": [{"task_id": "2020-H1", "arm": "full_feedback", "submission": {
        "records": records, "selection": {"attempt": 4}}}]}
    assessment = {"results": [{"task_id": "2020-H1", "arm": "full_feedback", "outcome": raw}]}
    slots, keys, selectors, jobs = diagnosis._tables(bank, assessment, {"2020-H1": task})
    assert len(slots) == 6
    assert slots[0]["orientation"] is slots[5]["orientation"] is None
    assert len(keys) == 3 and len(jobs) == 2
    assert selectors == [{"task_id": "2020-H1", "arm": "full_feedback",
                          "original": "2020-H1/full_feedback/4", "first": "2020-H1/full_feedback/1",
                          "minimum_ast": "2020-H1/full_feedback/2"}]


def test_public_replay_does_not_tolerate_changes_to_retained_evidence(tmp_path, monkeypatch):
    harness = Harness(tmp_path, monkeypatch)
    harness.prepare()
    harness.publish()
    report = harness.execute()
    target = harness.execution / "COMPLETE.json"
    original_bytes = target.read_bytes()
    reused = next(i for i, row in enumerate(report["key_results"]) if row["key"]["reuse_sources"])
    new = next(i for i, row in enumerate(report["key_results"]) if not row["key"]["reuse_sources"])
    locations = {
        "slot feedback": ("slot_results", 0, "feedback", "mean_ic"),
        "key feedback": ("key_results", new, "key", "feedback", "mean_ic"),
        "new raw history": ("key_results", new, "raw_evaluator_outcome", "feedback", "mean_ic"),
        "new raw future": ("key_results", new, "raw_evaluator_outcome", "assessment", "mean_ic"),
        "cached source outcome": ("key_results", reused, "provenance", "source_outcomes", 0,
                                  "outcome", "feedback", "mean_ic"),
        "slot fixed diagnosis cost": ("slot_results", 0, "diagnosis", "cost"),
        "selector fixed diagnosis cost": ("selector_rows", 0, "selectors", "original", "diagnosis", "cost"),
    }
    accepted = []
    for label, path in locations.items():
        altered = copy.deepcopy(report)
        parent = altered
        for step in path[:-1]:
            parent = parent[step]
        parent[path[-1]] = math.nextafter(parent[path[-1]], math.inf)
        altered.pop("body_sha256")
        target.write_text(diagnosis.canonical_json(diagnosis._sealed(altered)), encoding="utf-8")
        try:
            harness.replay()
        except ValueError:
            pass
        else:
            accepted.append(label)
        finally:
            target.write_bytes(original_bytes)
    assert accepted == [], f"Exact retained evidence accepted one-ULP changes: {accepted}"

    # Computed aggregate arithmetic retains its declared tolerance.
    altered = copy.deepcopy(report)
    values = altered["arm_summaries"]["full_feedback"]["selectors"]["original"]
    values["mean_utility"] = math.nextafter(values["mean_utility"], math.inf)
    altered.pop("body_sha256")
    target.write_text(diagnosis.canonical_json(diagnosis._sealed(altered)), encoding="utf-8")
    try:
        assert harness.replay()["status"] == "SAVED_ARITHMETIC_VERIFIED"
    finally:
        target.write_bytes(original_bytes)

    public = harness.root / "public-result.json"
    public.write_bytes(original_bytes + b"\n")
    with pytest.raises(ValueError, match="bytes differ"):
        diagnosis.replay_pool_diagnosis(harness.contract_path, harness.execution,
                                       source_root=harness.root, report_path=public)
    public.write_bytes(original_bytes)
    assert diagnosis.replay_pool_diagnosis(harness.contract_path, harness.execution,
                                          source_root=harness.root, report_path=public)["status"] == (
                                              "SAVED_ARITHMETIC_VERIFIED")


def test_saved_replay_needs_no_zip_versions_loader_or_financial_import(tmp_path, monkeypatch):
    harness = Harness(tmp_path, monkeypatch)
    harness.prepare()
    harness.publish()
    harness.execute()
    harness.data.unlink()

    def forbidden(*_args, **_kwargs):
        pytest.fail("saved replay invoked an execution-only dependency")

    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.rsplit(".", 1)[-1] in {"financial_policy", "financial_tasks"}:
            forbidden()
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(diagnosis, "_data_bytes", forbidden)
    monkeypatch.setattr(diagnosis, "_versions", forbidden)
    monkeypatch.setattr(diagnosis, "_load_tasks", forbidden)
    monkeypatch.setattr(builtins, "__import__", guarded_import)
    result = harness.replay()
    assert result["raw_market_data_reads"] == 0
    assert result["new_financial_scores"] == 0
    assert result["installed_runtime_revalidated"] is False
    assert len(harness.calls) == 108


def test_serial_job_chronology_cannot_be_resealed_backwards(tmp_path, monkeypatch):
    harness = Harness(tmp_path, monkeypatch)
    harness.prepare()
    harness.publish()
    harness.execute(max_jobs=2)
    directories = sorted((harness.execution / "jobs").iterdir())
    second_start_path = directories[1] / "STARTED.json"
    second = json.loads(second_start_path.read_bytes())
    # Meets the publication bound, but predates the prior durable completion.
    second["started_utc"] = json.loads(harness.receipt.read_bytes())["verified_utc"]
    second.pop("body_sha256")
    second_start_path.write_text(diagnosis.canonical_json(diagnosis._sealed(second)), encoding="utf-8")
    completed_path = directories[1] / "COMPLETED.json"
    completed = json.loads(completed_path.read_bytes())
    completed["started_sha256"] = diagnosis._sha(second_start_path.read_bytes())
    completed.pop("body_sha256")
    completed_path.write_text(diagnosis.canonical_json(diagnosis._sealed(completed)), encoding="utf-8")
    with pytest.raises(ValueError, match="prior completion"):
        harness.execute(max_jobs=1)
    assert len(harness.calls) == 2
    assert (harness.execution / "INCOMPLETE.json").exists()
