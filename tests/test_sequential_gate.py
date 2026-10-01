"""Original artificial candidate tables; no model or market-data downloads."""

import copy
import json
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from alpha_research_rl.sequential_gate import (
    CHEAP_FEATURES,
    FORMULA_GRID,
    FULL_FEATURES,
    candidate_features,
    choose_candidate,
    fit_weighted_ridge,
    run_opportunity_gate,
    target_reward,
)


def metrics(mean, usable=True):
    return {"mean_ic": mean, "ic_std": .1, "coverage": 1.0,
            "n_dates": 40 if usable else 0, "n_signal_dates": 40, "usable": usable}


def artificial_rows():
    rows = []
    for year in range(2002, 2018):
        for half in (1, 2):
            best = ((year - 2002) * 2 + half - 1) % 16
            for candidate, expression in enumerate(FORMULA_GRID):
                good = candidate == best
                rows.append({"task_id": f"{year}-H{half}", "year": year, "half": half,
                             "candidate_id": candidate, "expression": expression,
                             "cheap": metrics(.02), "late": metrics(.06 if good else 0),
                             "assessment": metrics(.06 if good else 0)})
    return rows


def test_feature_contract_sign_missing_flags_and_no_assessment_access():
    row = artificial_rows()[7]
    row["cheap"] = metrics(-.2)
    row["late"] = metrics(-.3)
    # Assessment fields and task identity do not belong in either vector.
    row["assessment"] = object()
    row["year"] = 9999
    cheap, full = candidate_features(row), candidate_features(row, True)
    assert len(CHEAP_FEATURES) == len(cheap) == 28
    assert len(FULL_FEATURES) == len(full) == 38
    np.testing.assert_array_equal(cheap[:12], [.2, -1, .1, 1, 1, 1, 0, 0, 0, 0, 0, 0])
    np.testing.assert_array_equal(cheap[12:], np.eye(16)[7])
    np.testing.assert_array_equal(full[:28], cheap)
    np.testing.assert_array_equal(full[28:], [.3, .1, 1, 1, 1, 0, 0, 0, 0, 0])
    row["cheap"] = metrics(None, False)
    row["cheap"]["ic_std"] = float("nan")
    full = candidate_features(row, True)
    np.testing.assert_array_equal(full[:12], [0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0])
    assert full[28] == 0 and full[33] == 1  # Late IC lacks a cheap orientation.
    assert full[37] == 0  # Late usability remains an observed scalar.


def test_weighted_ridge_matches_closed_form_and_free_intercept():
    x = np.asarray([-1.] * 8 + [1.] * 8)
    features = np.column_stack([x, np.full(16, 7.)])
    targets = 3 + 2 * x
    model = fit_weighted_ridge(features, targets)
    np.testing.assert_allclose(model.mean, [0, 7])
    np.testing.assert_allclose(model.scale, [1, 1])
    np.testing.assert_allclose(model.coefficients, [2/11, 0], atol=1e-14)
    assert model.intercept == 3
    # Twice as many tasks doubles the data weight, not the penalty or global
    # normalization. This distinguishes mean-per-task from mean-per-dataset.
    doubled = fit_weighted_ridge(np.tile(features, (2, 1)), np.tile(targets, 2))
    assert doubled.coefficients[0] == pytest.approx(1/3)


def test_ridge_validation_features_cannot_change_training_normalization():
    train = np.asarray([[1., 4.], [2., 4.], [3., 4.]])
    targets = np.asarray([.1, .2, .3])
    model = fit_weighted_ridge(train, targets)
    before = copy.deepcopy(model.public_state())
    model.predict(np.asarray([[1e6, -1e8], [-1e6, 1e8]]))
    assert model.public_state() == before
    np.testing.assert_allclose(model.mean, [2, 4])
    assert model.scale[0] == pytest.approx(np.sqrt(2/3))
    with pytest.raises(ValueError, match="finite"):
        fit_weighted_ridge(np.asarray([[np.inf]]), np.asarray([0.]))


def test_late_failure_never_changes_target_or_cheap_orientation():
    row = artificial_rows()[0]
    row["cheap"] = metrics(-.2)
    row["assessment"] = metrics(.3)
    before = target_reward(row)
    row["late"] = metrics(None, False)
    assert before == pytest.approx(-.31) and target_reward(row) == before
    row["cheap"] = metrics(0)
    assert target_reward(row) == pytest.approx(.29)  # Zero cheap IC declares +1.
    row["assessment"] = metrics(None, False)
    assert target_reward(row) == -1.01


def test_selector_excludes_cheap_failures_with_grid_order_ties():
    task = artificial_rows()[:16]
    scores = np.zeros(16)
    task[0]["cheap"] = metrics(None, False)
    scores[0] = 100
    assert choose_candidate(task, scores) == 1
    for row in task:
        row["cheap"] = metrics(None, False)
    assert choose_candidate(task, scores) is None


def test_forward_folds_gate_and_equal_task_year_denominators():
    report = run_opportunity_gate(artificial_rows())
    assert report["gate_passed"] is True and all(report["conditions"].values())
    assert [fold["models"]["cheap_ridge"]["n_training_rows"] for fold in report["folds"]] == [256, 384]
    assert [fold["n_tasks"] for fold in report["folds"]] == [8, 8]
    assert report["pooled"]["n_tasks"] == 16
    assert [row["year"] for row in report["yearly"]] == list(range(2010, 2018))
    assert all(row["n_tasks"] == 2 for row in report["yearly"])
    tasks = [row for fold in report["folds"] for row in fold["tasks"]]
    assert len({row["task_id"] for row in tasks}) == 16
    assert report["pooled"]["mean_reward"]["all_late_ridge"] == pytest.approx(.05)
    assert report["pooled"]["mean_reward"]["uniform_grid"] == pytest.approx(-.00625)
    assert report["pooled"]["mean_reward"]["fixed_lag1"] == pytest.approx(-.00625)
    for method, mean in report["pooled"]["mean_reward"].items():
        assert mean == pytest.approx(np.mean([row["choices"][method]["reward"] for row in tasks]))
        assert mean == pytest.approx(-1.01 + report["pooled"]["valid_fraction"][method]
                                    + report["pooled"]["valid_ic_contribution"][method])
    json.dumps(report, allow_nan=False)


def test_future_fold_features_and_rewards_do_not_change_either_fit():
    rows = artificial_rows()
    original = run_opportunity_gate(rows)
    changed = copy.deepcopy(rows)
    for row in changed:
        if row["year"] >= 2014:
            row["late"] = metrics(-.7)
            row["assessment"] = metrics(-.4)
            row["cheap"] = metrics(-.9)
    altered = run_opportunity_gate(changed)
    for before, after in zip(original["folds"], altered["folds"]):
        assert before["models"] == after["models"]
    assert original["folds"][0]["tasks"] == altered["folds"][0]["tasks"]
    assert original["folds"][1]["tasks"] != altered["folds"][1]["tasks"]


def test_positive_pooled_gain_cannot_hide_a_negative_first_fold():
    rows = artificial_rows()
    for row in rows:
        if 2010 <= row["year"] <= 2013:
            # Late evidence reverses its relationship to the target in fold1's
            # evaluation. Fold2 still has enough positive training signal.
            best = ((row["year"] - 2002) * 2 + row["half"] - 1) % 16
            row["assessment"] = metrics(-.03 if row["candidate_id"] == best else .02)
    report = run_opportunity_gate(rows)
    assert report["pooled"]["all_late_minus_cheap"] > .002
    assert report["folds"][0]["all_late_minus_cheap"] < 0
    assert report["folds"][1]["all_late_minus_cheap"] > 0
    assert report["conditions"]["late_minus_cheap_positive_both_folds"] is False
    assert report["gate_passed"] is False


def test_small_predictable_improvement_does_not_pass_compute_allocation_threshold():
    rows = artificial_rows()
    for row in rows:
        if row["year"] >= 2010 and row["assessment"]["mean_ic"] > 0:
            row["assessment"]["mean_ic"] = .001
    report = run_opportunity_gate(rows)
    assert 0 < report["pooled"]["all_late_minus_cheap"] < .002
    assert report["conditions"]["pooled_late_minus_cheap_gt_002"] is False
    assert report["gate_passed"] is False


def test_no_information_gain_and_all_unusable_tasks_fail_gate_without_dropping():
    rows = artificial_rows()
    for row in rows:
        row["assessment"] = metrics(.03)
        row["late"] = metrics(None, False)
    report = run_opportunity_gate(rows)
    assert report["gate_passed"] is False
    assert report["pooled"]["all_late_minus_cheap"] == 0
    for row in rows:
        if row["year"] >= 2010:
            row["cheap"] = metrics(None, False)
    failed = run_opportunity_gate(rows)
    assert failed["pooled"]["n_tasks"] == 16 and failed["gate_passed"] is False
    assert set(failed["pooled"]["mean_reward"].values()) == {-1.01}
    assert set(failed["pooled"]["failure_counts"].values()) == {16}
    assert all(task["choices"]["fixed_lag1"]["candidate_id"] == 1
               for fold in failed["folds"] for task in fold["tasks"])


def test_cli_writes_entry_manifest_and_all_task_bounds_before_scoring(monkeypatch, tmp_path):
    import alpha_research_rl.financial_policy as policy
    import alpha_research_rl.sequential_financial as financial
    import alpha_research_rl.sequential_gate as gate

    output = tmp_path / "artificial-gate.json"
    sidecar = output.with_suffix(".manifest.json")
    rows = artificial_rows()
    panel = SimpleNamespace(metadata={"raw_sha256": gate.EXPECTED_RAW_SHA256})
    boundaries = [{"task_id": rows[index]["task_id"], "cheap_bounds_half_open": [0, 40],
                   "late_bounds_half_open": [45, 85], "assessment_bounds_half_open": [90, 130]}
                  for index in range(0, len(rows), 16)]

    def load_without_real_data(path):
        assert path == "artificial.zip"
        entry = json.loads(sidecar.read_text())
        assert entry["created_utc"] and len(entry["source_sha256"]) == 64
        assert entry["config"]["snapshot_sha256"] == gate.EXPECTED_RAW_SHA256
        assert "task_manifests" not in entry["config"]
        return panel

    class Task:
        def __init__(self, index):
            self.index = index
            self.public_manifest = boundaries[index]

        def diagnostic_rows(self):
            captured = json.loads(sidecar.read_text())
            assert captured["config"]["task_manifests"] == boundaries
            assert len(captured["config"]["source_files_sha256"]) == 9
            return rows[self.index*16:(self.index+1)*16]

    monkeypatch.setattr(policy, "load_pinned_panel", load_without_real_data)
    monkeypatch.setattr(financial, "list_sequential_tasks", lambda panel, split: [Task(index) for index in range(32)])
    monkeypatch.setattr(sys, "argv", ["gate", "--input", "artificial.zip", "--output", str(output)])
    gate.main()
    report = json.loads(output.read_text())
    assert report["manifest"] == json.loads(sidecar.read_text())
    assert report["manifest"]["config"]["task_manifests"] == boundaries


@pytest.mark.parametrize("kind", ["holdout", "duplicate", "missing", "target"])
def test_rejects_holdout_or_incomplete_or_inconsistent_candidate_tables(kind):
    rows = artificial_rows()
    if kind == "holdout":
        rows[0]["year"] = 2018
    elif kind == "duplicate":
        rows.append(copy.deepcopy(rows[0]))
    elif kind == "missing":
        rows.pop()
    else:
        rows[0]["target_reward"] = .99
    with pytest.raises(ValueError):
        run_opportunity_gate(rows)
