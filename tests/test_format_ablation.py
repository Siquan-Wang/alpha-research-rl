import json
from types import SimpleNamespace

import pytest

from alpha_research_rl.format_ablation import evaluate_actor_episodes, parse_completion
from alpha_research_rl.llm import parse_action


@pytest.mark.parametrize("text,expected_format", [
    ('{"action":"stop"}', "strict_json"),
    ('  \n {"action":"screen","candidate":0} \n', "strict_json"),
    ('```json\n{"action":"stop"}\n```', "json_fence"),
    (' \n```json\r\n{\r\n"action":"stop"\r\n}\r\n``` \n', "json_fence"),
])
def test_accepts_only_whole_documented_formats(text, expected_format):
    result = parse_completion(text, terminated=True)
    assert result.accepted_format == expected_format
    assert result.failure is None
    assert result.action["action"] in {"stop", "screen"}


@pytest.mark.parametrize("text", [
    'Here is the action: {"action":"stop"}', '{"action":"stop"} trailing',
    '{"action":"stop"}{"action":"stop"}',
    '```json\n{"action":"stop"}\n```\nExplanation',
    'Explanation\n```json\n{"action":"stop"}\n```',
    '```json\n{"action":"stop"}\n```\n```json\n{"action":"stop"}\n```',
    '```\n{"action":"stop"}\n```', '```JSON\n{"action":"stop"}\n```',
    '```python\n{"action":"stop"}\n```', '```json {"action":"stop"}```',
    '```json\n{"action":"stop"}```', '```json\n{"action":"stop"}\n',
    '```json\n{"action":"stop"},\n```', '[{"action":"stop"}]', 'null',
    '```json\n[1,2]\n```', '```json\n{"action":"stop"}\n{"action":"stop"}\n```',
])
def test_rejects_prose_extra_blocks_wrong_fences_or_nonobject_json(text):
    result = parse_completion(text, terminated=True)
    assert result.action == {"action": "invalid"}
    assert result.accepted_format is None
    assert result.failure is not None


@pytest.mark.parametrize("text", ['{"action":"stop"}', '```json\n{"action":"stop"}\n```'])
def test_unterminated_completion_never_accepted_even_if_json_complete(text):
    result = parse_completion(text, terminated=False)
    assert result.failure == "unterminated_completion"
    assert result.accepted_format is None


def test_format_acceptance_does_not_repair_action_schema_or_change_strict_parser():
    text = '```json\n{"action":"invented","extra":1}\n```'
    parsed = parse_completion(text, True)
    assert parsed.accepted_format == "json_fence"
    assert parsed.action == {"action": "invented", "extra": 1}
    assert parse_action(text) == {"action": "invalid"}


class ScriptedActor:
    def __init__(self, fence=False, terminate=True, action="screen"):
        self.fence, self.terminate, self.action = fence, terminate, action
        self.seen = []

    def sample(self, observation, stochastic, max_tokens):
        assert stochastic is False and max_tokens == 64
        self.seen.append(observation)
        if self.action == "invalid":
            action = {"action": "invented"}
        elif not observation["evidence"]:
            action = {"action": "screen", "candidate": 0}
        elif not observation["selected"]:
            action = {"action": "select", "candidate": 0}
        else:
            action = {"action": "stop"}
        text = json.dumps(action)
        if self.fence:
            text = "```json\n" + text + "\n```"
        return SimpleNamespace(text=text, terminated=self.terminate)


def test_identical_research_trajectory_for_json_and_fenced_json():
    tasks = [{"seed": 11000, "regime": "signal"}]
    plain_episodes, plain = evaluate_actor_episodes(ScriptedActor(), tasks)
    fenced_episodes, fenced = evaluate_actor_episodes(ScriptedActor(fence=True), tasks)
    assert plain_episodes[0]["reward"] == fenced_episodes[0]["reward"]
    assert plain_episodes[0]["history"] == fenced_episodes[0]["history"]
    assert plain["successful_action_counts"] == fenced["successful_action_counts"]
    assert plain["format_acceptance"] == {"strict_json": 3}
    assert fenced["format_acceptance"] == {"json_fence": 3}
    assert plain["strict_format_accepted"] == 3 and fenced["strict_format_accepted"] == 0


def test_unterminated_and_schema_invalid_attempts_consume_same_budget():
    tasks = [{"seed": 11000, "regime": "signal"}]
    unfinished_episodes, unfinished = evaluate_actor_episodes(ScriptedActor(fence=True, terminate=False), tasks)
    invalid_episodes, invalid = evaluate_actor_episodes(ScriptedActor(fence=True, action="invalid"), tasks)
    assert unfinished["n_actions"] == invalid["n_actions"] == 10
    assert unfinished["invalid_actions"] == invalid["invalid_actions"] == 10
    assert unfinished_episodes[0]["spent_budget"] == invalid_episodes[0]["spent_budget"] == 10
    assert unfinished_episodes[0]["reward"] == invalid_episodes[0]["reward"] == -0.01
    assert unfinished["parse_failures"] == {"unterminated_completion": 10}
    assert invalid["format_acceptance"] == {"json_fence": 10}


def test_nonstring_action_value_is_logged_without_summary_failure():
    class NonStringActor:
        def sample(self, observation, stochastic, max_tokens):
            return SimpleNamespace(text='{"action":["screen"],"candidate":0}', terminated=True)

    _, summary = evaluate_actor_episodes(NonStringActor(), [{"seed": 11000, "regime": "null"}])
    assert summary["attempted_action_counts"] == {"non_string_action": 10}
    assert summary["invalid_actions"] == 10


def test_run_manifest_is_captured_before_model_loading(monkeypatch, tmp_path):
    import alpha_research_rl.format_ablation as module

    events = []

    def manifest(config):
        events.append("manifest")
        return {"config": config}

    def actor(model_path, adapter):
        events.append("load")
        return ScriptedActor()

    monkeypatch.setattr(module, "run_manifest", manifest)
    monkeypatch.setattr(module, "seed_everything", lambda seed: events.append("seed"))
    monkeypatch.setattr(module, "LocalActor", actor)
    monkeypatch.setattr(module, "TASKS", [{"seed": 11000, "regime": "signal"}])
    report = module.evaluate_actor("mock-model", None, str(tmp_path / "report.json"), "mock")
    assert events == ["manifest", "seed", "load"]
    assert report["manifest"]["config"]["manifest_capture"] == "entry before model load"
