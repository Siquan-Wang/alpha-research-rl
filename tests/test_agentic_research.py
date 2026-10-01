"""Research-budget, feedback-mask and submission-freeze invariants."""

import copy
import json

import pytest

from alpha_research_rl.agentic_research import ARMS, ResearchEpisode, digest, validate_packet


def metrics(value=0.02, usable=True):
    return {"mean_ic": value, "coverage": 1.0, "ic_std": 0.1,
            "n_dates": 100, "n_signal_dates": 100, "usable": usable}


def initial():
    overall = {key: value for key, value in metrics().items() if key != "usable"}
    return {"supported_features": ["returns"], "max_lookback": 60, "horizon_sessions": 5,
            "proposal_cost": 0.01, "probe_evidence": [
                {"expression": expression, "feedback": copy.deepcopy(overall), "feedback_usable": True,
                 "windows": [copy.deepcopy(overall) for _ in range(3)]}
                for expression in ("ts_mean(returns,5)", "ts_mean(returns,20)")]}


def packet(expression):
    return json.dumps({"action": "propose", "expression": expression,
                       "hypothesis": "A public economic justification.", "revision": "No new evidence yet."})


def test_same_initial_prompt_all_arms_and_strict_candidate_feedback_masks():
    sessions = {arm: ResearchEpisode(arm, initial(), lambda _: metrics(0.87654321)) for arm in ARMS}
    assert len({session.prompt() for session in sessions.values()}) == 1
    for session in sessions.values():
        session.submit(packet("returns"))
    assert sessions["full_feedback"].observation()["history"][0]["visible_feedback"]["feedback"]["mean_ic"] == 0.87654321
    assert sessions["validity_only"].observation()["history"][0]["visible_feedback"] == {
        "attempt_recorded": True, "grammar_valid": True, "canonical_duplicate": False,
    }
    full_fields = sessions["full_feedback"].observation()["history"][0]["visible_feedback"]
    full_fields.pop("feedback")
    assert full_fields == sessions["validity_only"].observation()["history"][0]["visible_feedback"]
    assert sessions["withheld_feedback"].observation()["history"][0]["visible_feedback"] == {"attempt_recorded": True}
    for arm in ("validity_only", "withheld_feedback"):
        assert "0.87654321" not in sessions[arm].prompt()
        assert "usable" not in json.dumps(sessions[arm].observation()["history"])


def test_grammar_control_is_invariant_to_data_scoreability_and_future_values():
    low = ResearchEpisode("validity_only", initial(), lambda _: metrics(None, usable=False))
    high = ResearchEpisode("validity_only", initial(), lambda _: metrics(0.8))
    low.submit(packet("div(returns,0)"))
    high.submit(packet("div(returns,0)"))
    assert low.prompt() == high.prompt()
    assert low.records[0]["visible_feedback"]["grammar_valid"] is True


@pytest.mark.parametrize("raw", ["not JSON", packet("volume")])
def test_full_feedback_does_not_add_syntax_error_detail_to_validity_control(raw):
    full = ResearchEpisode("full_feedback", initial(), lambda _: metrics())
    control = ResearchEpisode("validity_only", initial(), lambda _: metrics())
    full_record, control_record = full.submit(raw), control.submit(raw)
    assert full_record["failure_code"] is not None
    assert full_record["failure_code"] == control_record["failure_code"]
    full_visible = full_record["visible_feedback"]
    assert full_visible.pop("feedback") is None
    assert full_visible == control_record["visible_feedback"]


def test_every_invalid_duplicate_attempt_consumes_budget_and_no_extra_tool_call():
    calls = []

    def feedback(expression):
        calls.append(expression)
        return metrics(-0.3)

    session = ResearchEpisode("full_feedback", initial(), feedback)
    actions = [packet("returns"), packet("(returns)"), "not JSON", packet("volume"),
               packet("__import__('os').system('bad')"), packet("delay(returns,1)")]
    for action in actions:
        session.submit(action)
    assert calls == ["returns", "delay(returns,1)"]
    assert [record["attempt"] for record in session.records] == list(range(1, 7))
    assert session.records[1]["canonical_duplicate"] is True
    assert session.records[2]["failure_code"] == "invalid_json_packet"
    assert session.records[3]["failure_code"] == session.records[4]["failure_code"] == "invalid_expression"
    frozen = session.freeze()
    assert frozen["attempt_count"] == 6 and frozen["search_cost"] == 0.06
    assert frozen["selection"] == {"attempt": 1, "expression": "returns", "feedback_ic": -0.3, "orientation": -1}
    assert frozen["future_assessment_calls"] == 0
    assert frozen["body_sha256"] == digest({key: value for key, value in frozen.items() if key != "body_sha256"})
    with pytest.raises(ValueError, match="exhausted"):
        session.submit(packet("returns"))
    with pytest.raises(ValueError, match="exhausted"):
        session.prompt()


def test_selector_uses_feedback_magnitude_and_earliest_tie_for_every_arm():
    values = [0.1, -0.5, 0.5, None, 0.2, 0.05]
    selections = []
    for arm in ARMS:
        scores = iter(values)

        def feedback(_, scores=scores):
            value = next(scores)
            return metrics(value, usable=value is not None)

        session = ResearchEpisode(arm, initial(), feedback)
        for lookback in range(1, 7):
            session.submit(packet(f"delay(returns,{lookback})"))
        selections.append(session.freeze()["selection"])
    assert selections == [{"attempt": 2, "expression": "delay(returns,2)",
                           "feedback_ic": -0.5, "orientation": -1}] * 3


def test_incomplete_search_cannot_be_published_as_complete_and_allinvalid_is_retained():
    session = ResearchEpisode("full_feedback", initial(), lambda _: pytest.fail("invalid packet reached evaluator"))
    session.submit("invalid")
    with pytest.raises(ValueError, match="incomplete"):
        session.freeze()
    for _ in range(5):
        session.submit("invalid")
    frozen = session.freeze()
    assert frozen["selection"] is None
    assert len(frozen["records"]) == 6
    assert frozen["search_cost"] == 0.06


def test_observation_and_frozen_payloads_are_defensive_copies():
    observation = initial()
    session = ResearchEpisode("full_feedback", observation, lambda _: metrics())
    observation["probe_evidence"][0]["feedback"]["mean_ic"] = 0.9
    assert session.observation()["initial_evidence"]["probe_evidence"][0]["feedback"]["mean_ic"] == 0.02
    record = session.submit(packet("returns"))
    record["feedback"]["mean_ic"] = 0.8
    returned = session.observation()
    returned["history"][0]["visible_feedback"]["feedback"]["mean_ic"] = 0.7
    assert session.records[0]["feedback"]["mean_ic"] == 0.02
    for _ in range(5):
        session.submit(packet("returns"))
    frozen = session.freeze()
    frozen["records"][0]["feedback"]["mean_ic"] = 0.6
    assert session.freeze()["records"][0]["feedback"]["mean_ic"] == 0.02


def test_oversized_response_is_retained_but_bounded_in_subsequent_prompt():
    session = ResearchEpisode("withheld_feedback", initial(), lambda _: pytest.fail("invalid reached feedback"))
    raw = "x" * 50000
    session.submit(raw)
    assert session.checkpoint()["records"][0]["raw_response"] == raw
    history = session.observation()["history"][0]
    assert len(history["raw_response"]) == 20000
    assert history["raw_response_truncated"] is True
    assert len(history["raw_response_sha256"]) == 64
    assert len(session.prompt()) < 25000


def test_initial_metrics_cannot_smuggle_fields_overwritten_during_validation():
    evidence = initial()
    evidence["probe_evidence"][0]["feedback"]["usable"] = {"future_ic": 0.9}
    with pytest.raises(ValueError, match="unexpected fields"):
        ResearchEpisode("full_feedback", evidence, lambda _: metrics())


@pytest.mark.parametrize("raw", [
    '{"action":"propose","expression":"returns","hypothesis":"x","revision":"x","extra":1}',
    '{"action":"propose","expression":"returns","expression":"volume","hypothesis":"x","revision":"x"}',
    '{"action":"propose","expression":"returns","hypothesis":NaN,"revision":"x"}',
    '```json\n{}\n```', '[]', '{}', 'null', '"returns"',
])
def test_invalid_or_ambiguous_json_is_not_repaired(raw):
    assert validate_packet(raw)[2] == "invalid_json_packet"


@pytest.mark.parametrize("change", [
    {"assessment": {"mean_ic": 0.9}}, {"supported_features": ["returns", "volume"]},
    {"horizon_sessions": 10}, {"probe_evidence": []},
])
def test_initial_observation_cannot_silently_accept_hidden_or_changed_fields(change):
    with pytest.raises(ValueError):
        ResearchEpisode("full_feedback", initial() | change, lambda _: metrics())


@pytest.mark.parametrize("change", [
    {"mean_ic": float("nan")}, {"mean_ic": True}, {"usable": 1}, {"n_dates": 101},
    {"n_signal_dates": 100.0}, {"coverage": 1.1}, {"future_ic": 0.99},
])
def test_feedback_tool_failure_is_not_silently_cast_or_used(change):
    session = ResearchEpisode("full_feedback", initial(), lambda _: metrics() | change)
    with pytest.raises(ValueError):
        session.submit(packet("returns"))
    assert session.failed and len(session.records) == 1
    assert session.checkpoint()["records"][0]["raw_response"] == packet("returns")
    assert session.checkpoint()["records"][0]["cost"] == 0.01
    with pytest.raises(ValueError, match="failed"):
        session.prompt()
    with pytest.raises(ValueError, match="failed"):
        session.submit(packet("returns"))
    with pytest.raises(ValueError, match="failed"):
        session.freeze()
