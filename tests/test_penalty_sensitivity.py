import copy

import pytest

from alpha_research_rl.penalty_sensitivity import sensitivity


def fixture():
    def cell(valid, ic):
        return {"valid_fraction": valid, "all_proposal_ic_contribution": ic,
                "mean_reward": ic - .01 - (1 - valid), "n_samples": 10,
                "valid_samples": round(valid * 10)}
    return {"study": "financial-proposal-v1-paired-analysis", "integrity": {"validated": True},
            "roles": {"sft": "sft", "rl_seed23": "rl23", "rl_seed29": "rl29"},
            "overall": {"metrics": {"strict": {"stochastic": {"policies": {
                "sft": {"true": cell(.8, .02)}, "rl23": {"true": cell(.9, .03)},
                "rl29": {"true": cell(.9, .01)}}}}},
                "references": {"uniform_grid": cell(1., .02)}}}


def test_positive_primary_gain_can_mask_negative_zero_penalty_gain():
    result = sensitivity(fixture())
    # RL29 improves validity but worsens the all-proposal IC contribution.
    row = result["rl_vs_sft"]["rl29"]
    assert row["zero_penalty_gain"] == pytest.approx(-.01)
    assert row["registered_penalty_one_gain"] == pytest.approx(.09)
    assert row["uniform_grid_crossing_penalty"] is None
    assert result["rl_vs_sft"]["rl23"]["uniform_grid_crossing_penalty"] == pytest.approx(.1)


def test_equal_validity_removes_penalty_dependence_and_does_not_mutate_source():
    report = fixture()
    report["overall"]["metrics"]["strict"]["stochastic"]["policies"]["sft"]["true"].update(
        valid_fraction=.9, valid_samples=9, mean_reward=-.09)
    before = copy.deepcopy(report)
    result = sensitivity(report)
    assert report == before
    assert {round(v, 10) for v in result["rl_vs_sft"]["rl23"]["rl_minus_sft_by_penalty"].values()} == {.01}


def test_reject_changed_primary_reward_or_unvalidated_analysis():
    report = fixture()
    report["overall"]["references"]["uniform_grid"]["mean_reward"] = .99
    with pytest.raises(ValueError, match="registered primary"):
        sensitivity(report)
    report = fixture()
    report["integrity"]["validated"] = False
    with pytest.raises(ValueError, match="validated"):
        sensitivity(report)
