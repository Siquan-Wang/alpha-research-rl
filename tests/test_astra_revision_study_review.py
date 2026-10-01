"""Independent arithmetic and synthetic failure checks; no real scoring or models."""

import math

import pytest

from alpha_research_rl import astra_revision_core as core


def resolved_scalar_fixture(*, shift_states):
    """Exercise the numerical boundary, not the driver's evidence authentication."""
    rows = []
    for task, generator, repetition in core.SLOT_ORDER:
        index = core.TASK_IDS.index(task)
        offset = -0.25 + 0.06 * index if shift_states else 0.0
        baseline = 0.02 + offset
        levels = {
            "truthful": 0.10 + (-0.03, -0.01, 0.01, 0.03)[repetition - 1],
            "masked": 0.05 + (-0.02, 0.02, -0.02, 0.02)[repetition - 1],
            "copy": 0.02,
            "window_edit": 0.03,
            "grammar_draw": -0.10,
        }
        duplicate = generator == "copy"
        adjudication = {
            "packet_valid": True, "grammar_valid": True,
            "within_dependency_limit": True, "eligible": True,
            "historically_usable": True, "canonical_duplicate_with_prefix": duplicate,
            "admitted_to_selector": not duplicate, "selected_new": not duplicate,
            "failure_code": None,
        }
        scores = core.resolve_branch(adjudication, core.quality(True, levels[generator] + offset),
                                     core.quality(True, baseline))
        rows.append({"task_id": task, "generator": generator, "repetition": repetition,
                     "adjudication": adjudication, **scores})
    return rows


def test_market_level_offsets_do_not_become_generation_uncertainty():
    base = core.analyze(resolved_scalar_fixture(shift_states=False))
    shifted = core.analyze(resolved_scalar_fixture(shift_states=True))
    # Per-state hosted sample variances are 1/1500 and 1/1875. Sum ten
    # copies of (s_truth^2/4 + s_mask^2/4), then divide its root by ten.
    expected_mc_se = math.sqrt(10 * (1 / 1500 + 1 / 1875) / 4) / 10
    for result in (base, shifted):
        assert result["slot_count"] == 200
        assert result["primary_truthful_minus_masked_Q"] == pytest.approx(0.05, abs=1e-14)
        assert result["secondary_truthful_minus_masked_G"] == pytest.approx(0.05, abs=1e-14)
        assert result["conditional_generation_mc_se"] == pytest.approx(expected_mc_se, abs=1e-14)
        assert len(result["states"]) == 10 and len(result["years"]) == 5
        assert all(summary["candidate"]["denominator"] == 40
                   for summary in result["generators"].values())
    assert shifted["generators"]["truthful"]["candidate"]["mean_Q"] == pytest.approx(0.12)
    assert base["generators"]["truthful"]["candidate"]["mean_Q"] == pytest.approx(0.10)
    for original, changed in zip(base["states"], shifted["states"], strict=True):
        assert original["task_id"] == changed["task_id"]
        assert changed["contrasts"]["truthful_minus_masked"]["Q_difference"] == pytest.approx(0.05)
        assert changed["generators"]["copy"]["mean_G"] == 0


def test_all_slot_freeze_does_not_bypass_publication_or_retry_failed_score(tmp_path, monkeypatch):
    """A full bank is necessary but insufficient; a started failed job is terminal."""
    from test_astra_revision_study import RevisionHarness

    from alpha_research_rl import astra_pool_diagnosis as pool
    from alpha_research_rl import astra_revision_study as study
    from alpha_research_rl.agentic_research import canonical_json

    harness = RevisionHarness(tmp_path, monkeypatch)
    bank = harness.complete_collection()
    assert len(bank["slots"]) == 200 and len(harness.actor_calls) == 80
    assert harness.future_calls == []
    receipt_path = harness.receipt("submissions")
    correct_receipt = receipt_path.read_bytes()
    incomplete_receipt = pool._read(correct_receipt)
    incomplete_receipt.pop("body_sha256")
    incomplete_receipt["paths_sha256"].pop(study.SUBMISSIONS_PATH)
    receipt_path.write_text(canonical_json(pool._sealed(incomplete_receipt)) + "\n", encoding="utf-8")
    with monkeypatch.context() as blocked:
        blocked.setattr(study, "_cache_and_plan", lambda *_args, **_kwargs:
                        pytest.fail("future cache parsed before a complete Gate 2 proof"))
        with pytest.raises(ValueError, match="publication hashes"):
            harness.assess(max_jobs=1)
    assert harness.future_calls == [] and not harness.second_gate_verified
    assert not (harness.execution / "assessment-request.json").exists()
    assert not (harness.execution / "INCOMPLETE.json").exists()

    receipt_path.write_bytes(correct_receipt)
    harness.future_failure = True
    with pytest.raises(KeyboardInterrupt, match="synthetic future interruption"):
        harness.assess(max_jobs=1)
    assert harness.second_gate_verified and len(harness.future_calls) == 1
    first_job = harness.execution / "assessment-jobs" / "001"
    assert (first_job / "STARTED.json").is_file()
    assert not (first_job / "COMPLETED.json").exists()
    assert (harness.execution / "INCOMPLETE.json").is_file()
    assert not (harness.root / study.RESULT_PATH).exists()
    for action in (harness.assess, lambda: study.replay_revision_study(source_root=harness.root)):
        with pytest.raises(ValueError, match="INCOMPLETE"):
            action()
    assert len(harness.future_calls) == 1 and len(harness.actor_calls) == 80
