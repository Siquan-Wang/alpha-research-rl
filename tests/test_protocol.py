import pytest

from alpha_research_rl.protocol import ResearchSplit, make_chronological_split


def test_half_open_chronological_purging():
    split = make_chronological_split(200, horizon=5)
    assert split.fit == (0, 75)
    assert split.feedback == (80, 135)
    assert split.assessment == (140, 195)
    for before, after in ((split.fit, split.feedback), (split.feedback, split.assessment)):
        assert before[1] - 1 + split.horizon < after[0]
    split.validate_for_panel(200)
    assert split.to_dict()["fit"] == [0, 75]


@pytest.mark.parametrize("fit,feedback,assessment,horizon", [
    ((0, 10), (12, 20), (25, 30), 5),
    ((0, 10), (15, 20), (24, 30), 5),
    ((0, 0), (15, 20), (25, 30), 5),
    ((-1, 10), (15, 20), (25, 30), 5),
    ((0, 10), (15, 20), (25, 30), 0),
    ((0, True), (15, 20), (25, 30), 5),
    ((0, 10), (15, 20), (25, 30), True),
])
def test_invalid_split_is_rejected(fit, feedback, assessment, horizon):
    with pytest.raises(ValueError):
        ResearchSplit(fit, feedback, assessment, horizon)


def test_assessment_label_end_must_exist():
    split = ResearchSplit((0, 10), (15, 20), (25, 30), 5)
    split.validate_for_panel(35)
    with pytest.raises(ValueError):
        split.validate_for_panel(34)


@pytest.mark.parametrize("n,h,f,g", [(10, 5, .4, .3), (100, 5, .7, .3), (100, 5, -.1, .3)])
def test_factory_rejects_empty_or_invalid_blocks(n, h, f, g):
    with pytest.raises(ValueError):
        make_chronological_split(n, h, f, g)
