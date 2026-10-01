"""Native actor transport tests using fake subprocesses only; no model inference."""

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

import alpha_research_rl.codex_actor as actor

TEXT = '{"action":"propose","expression":"returns","hypothesis":"momentum","revision":"initial"}'
USAGE = {"input_tokens": 100, "cached_input_tokens": 0, "cache_write_input_tokens": 0,
         "output_tokens": 20, "reasoning_output_tokens": 5}


def events(text=TEXT, usage=USAGE):
    return [
        {"type": "thread.started", "thread_id": "test-thread"},
        {"type": "turn.started"},
        {"type": "item.completed", "item": {"id": "item_0", "type": "agent_message", "text": text}},
        {"type": "turn.completed", "usage": usage},
    ]


def jsonl(rows):
    return ("\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n").encode("utf-8")


def fake_process(monkeypatch, *, raw=None, final=TEXT, returncode=0, failure=None, write_response=True):
    state = {"calls": [], "communicate": [], "kills": 0}

    class FakeProcess:
        def __init__(self, command, **kwargs):
            state["calls"].append((command, kwargs))
            self.returncode = None
            self.command = command
            self.stdout = kwargs["stdout"]
            self.stderr = kwargs["stderr"]
            self.first = True

        def communicate(self, input=None, timeout=None):
            state["communicate"].append((input, timeout))
            if self.first:
                self.first = False
                self.stdout.write(jsonl(events()) if raw is None else raw)
                self.stderr.write(b"retained diagnostic bytes\n")
                if write_response:
                    path = Path(self.command[self.command.index("--output-last-message") + 1])
                    path.write_bytes(final.encode("utf-8") if isinstance(final, str) else final)
                if failure is not None:
                    raise failure
                self.returncode = returncode
            else:
                self.returncode = -9
            return None, None

        def kill(self):
            state["kills"] += 1

    monkeypatch.setattr(actor.subprocess, "Popen", FakeProcess)
    return state


def run(tmp_path, **kwargs):
    return actor.run_actor("Full frozen observed history. \u03bb", tmp_path / "attempt", cwd=tmp_path,
                           executable="fake-codex.exe", **kwargs)


def test_one_exact_array_command_preserves_all_evidence_before_parse(tmp_path, monkeypatch):
    state = fake_process(monkeypatch)
    result = run(tmp_path)
    assert result.success and result.status == "succeeded" and result.error is None
    assert result.final_text == TEXT and result.usage == USAGE and result.returncode == 0
    assert len(state["calls"]) == 1 and state["kills"] == 0
    command, kwargs = state["calls"][0]
    assert command == [
        "fake-codex.exe", "exec", "--ignore-user-config", "--strict-config", "--model", "gpt-6-astra",
        "-c", 'model_reasoning_effort="ultra"', "-c", 'service_tier="default"',
        "--sandbox", "read-only", "--ephemeral", "--skip-git-repo-check",
        "--output-schema", str((tmp_path / "attempt" / "schema.json").resolve()),
        "--output-last-message", str((tmp_path / "attempt" / "response.json").resolve()), "--json", "-",
    ]
    assert kwargs["shell"] is False and kwargs["stdin"] == subprocess.PIPE
    assert kwargs["cwd"] == str(tmp_path.resolve())
    assert "env" not in kwargs  # No credential/environment copying into request metadata.
    assert state["communicate"] == [("Full frozen observed history. \u03bb".encode(), 600)]
    paths = {key: Path(value) for key, value in result.artifact_paths.items()}
    assert paths["prompt"].read_bytes() == state["communicate"][0][0]
    assert paths["events"].read_bytes() == jsonl(events())
    assert paths["stderr"].read_bytes() == b"retained diagnostic bytes\n"
    assert paths["response"].read_text(encoding="utf-8") == TEXT
    schema = json.loads(paths["schema"].read_text(encoding="utf-8"))
    assert set(schema["properties"]) == {"action", "expression", "hypothesis", "revision"}
    assert set(schema["required"]) == set(schema["properties"])
    assert schema["properties"]["action"]["enum"] == ["propose"]
    assert schema["additionalProperties"] is False
    summary = json.loads(paths["result"].read_text(encoding="utf-8"))
    assert summary == result.public_summary
    assert summary["automatic_retries"] == 0 and summary["attempts_started"] == 1
    assert summary["model_attested_by_events"] is False
    assert summary["cli_version_contract"] == "0.159.2"
    assert datetime.fromisoformat(summary["started_at_utc"]) <= datetime.fromisoformat(summary["ended_at_utc"])
    assert summary["response_only_stream_valid"] is True
    for filename, metadata in summary["artifacts"].items():
        raw = (tmp_path / "attempt" / filename).read_bytes()
        assert metadata == {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    public_text = json.dumps(summary, allow_nan=False)
    assert str(tmp_path) not in public_text and TEXT not in public_text
    assert "retained diagnostic bytes" not in public_text


def test_parser_checks_run_only_after_both_streams_are_closed(tmp_path, monkeypatch):
    state = fake_process(monkeypatch)
    original = actor.parse_response_events

    def checking_parser(raw, final):
        _, kwargs = state["calls"][0]
        assert kwargs["stdout"].closed and kwargs["stderr"].closed
        assert (tmp_path / "attempt" / "events.jsonl").read_bytes() == raw
        return original(raw, final)

    monkeypatch.setattr(actor, "parse_response_events", checking_parser)
    assert run(tmp_path).success


@pytest.mark.parametrize("text", ["not JSON", "", '{"action":"wrong"}', "  JSON with trailing whitespace\n"])
def test_completed_malformed_packet_is_left_to_broker(tmp_path, monkeypatch, text):
    fake_process(monkeypatch, raw=jsonl(events(text)), final=text)
    result = run(tmp_path)
    assert result.success and result.final_text == text


@pytest.mark.parametrize("item_type", ["command_execution", "mcp_tool_call", "web_search", "reasoning", "unknown"])
def test_every_non_agent_message_item_fails_closed(tmp_path, monkeypatch, item_type):
    rows = events()
    rows[2]["item"]["type"] = item_type
    raw = jsonl(rows)
    state = fake_process(monkeypatch, raw=raw)
    result = run(tmp_path)
    assert not result.success and result.final_text is None
    assert result.error == "forbidden_or_invalid_response_item"
    assert result.usage == USAGE and result.public_summary["usage_source"] == "failed_stream_report"
    assert Path(result.artifact_paths["events"]).read_bytes() == raw
    assert len(state["calls"]) == 1


@pytest.mark.parametrize("mutation", [
    lambda rows: rows[:3],
    lambda rows: rows + [rows[-1]],
    lambda rows: rows[:3] + [rows[2], rows[-1]],
    lambda rows: [rows[1], rows[0], rows[2], rows[3]],
    lambda rows: rows[:3] + [{"type": "turn.failed", "error": {"message": "failure"}}],
    lambda rows: rows[:2] + [{"type": "item.started", "item": {"type": "command_execution"}}] + rows[2:],
    lambda rows: rows[:2] + [{"type": "error", "message": "error"}] + rows[2:],
    lambda rows: rows[:2] + [{"type": "item.completed", "item": {**rows[2]["item"], "model": "unknown"}}] + rows[3:],
])
def test_incoherent_lifecycle_unknown_fields_and_tool_events_fail(tmp_path, monkeypatch, mutation):
    raw = jsonl(mutation(events()))
    fake_process(monkeypatch, raw=raw)
    result = run(tmp_path)
    assert not result.success and result.error
    assert result.public_summary["response_only_stream_valid"] is False
    assert Path(result.artifact_paths["events"]).read_bytes() == raw


@pytest.mark.parametrize("raw", [
    jsonl(events()) + b"{broken}\n", b"\xff\xfe", jsonl(events()) + b"\n",
    jsonl(events()).replace(b'"type": "turn.started"', b'"type":"turn.started","type":"turn.started"'),
    b"[]\n" * 4,
])
def test_malformed_duplicate_nonutf8_or_trailing_event_is_retained(tmp_path, monkeypatch, raw):
    fake_process(monkeypatch, raw=raw)
    result = run(tmp_path)
    assert not result.success
    assert Path(result.artifact_paths["events"]).read_bytes() == raw
    assert Path(result.artifact_paths["result"]).is_file()


@pytest.mark.parametrize("usage", [
    {"input_tokens": True, "output_tokens": 1}, {"input_tokens": -1, "output_tokens": 1},
    {"input_tokens": 1.0, "output_tokens": 1}, {"input_tokens": "1", "output_tokens": 1},
    {"input_tokens": 1, "output_tokens": float("nan")},
    {"input_tokens": 1, "output_tokens": float("inf")},
    {"input_tokens": 1}, {"input_tokens": 1, "output_tokens": 1, "unknown": 1}, None,
])
def test_invalid_reported_usage_fails_without_coercion(tmp_path, monkeypatch, usage):
    fake_process(monkeypatch, raw=jsonl(events(usage=usage)))
    assert not run(tmp_path).success


def test_absent_usage_is_explicitly_unavailable(tmp_path, monkeypatch):
    rows = events()
    rows[-1] = {"type": "turn.completed"}
    fake_process(monkeypatch, raw=jsonl(rows))
    result = run(tmp_path)
    assert result.success and result.usage is None


def test_multiple_completion_usage_reports_are_retained_without_choosing_one(tmp_path, monkeypatch):
    rows = events()
    rows.append({"type": "turn.completed", "usage": {"input_tokens": 7, "output_tokens": 2}})
    fake_process(monkeypatch, raw=jsonl(rows))
    result = run(tmp_path)
    assert not result.success and result.usage is None
    assert result.public_summary["reported_usage_records"] == [
        {"line_1based": 4, "usage": USAGE},
        {"line_1based": 5, "usage": {"input_tokens": 7, "output_tokens": 2}},
    ]
    assert result.public_summary["usage_source"] == "unavailable_or_ambiguous"


def test_usage_is_retained_despite_a_trailing_malformed_event(tmp_path, monkeypatch):
    fake_process(monkeypatch, raw=jsonl(events()) + b"broken tail\n")
    result = run(tmp_path)
    assert not result.success and result.usage == USAGE
    assert result.public_summary["response_only_stream_valid"] is False
    assert result.public_summary["usage_source"] == "failed_stream_report"


def test_distinct_attempts_each_start_a_fresh_process_with_the_entire_supplied_history(tmp_path, monkeypatch):
    state = fake_process(monkeypatch)
    for index, history in enumerate(("arm one full history", "arm two full history")):
        result = actor.run_actor(history, tmp_path / str(index), cwd=tmp_path, executable="fake-codex.exe")
        assert result.success
    assert len(state["calls"]) == 2
    assert [call[0] for call in state["communicate"]] == [b"arm one full history", b"arm two full history"]
    assert all(command[1] == "exec" and "--ephemeral" in command and "resume" not in command
               for command, _ in state["calls"])


@pytest.mark.parametrize("final,write_response", [("changed", True), (TEXT + "\n", True), (b"\xff", True), (TEXT, False)])
def test_missing_or_nonidentical_last_message_fails(tmp_path, monkeypatch, final, write_response):
    fake_process(monkeypatch, final=final, write_response=write_response)
    result = run(tmp_path)
    assert not result.success and result.final_text is None


def test_invalid_surrogate_response_is_a_recorded_transport_failure(tmp_path, monkeypatch):
    fake_process(monkeypatch, raw=jsonl(events("\ud800")), final=b"invalid")
    result = run(tmp_path)
    assert result.error == "invalid_response_unicode"
    assert Path(result.artifact_paths["result"]).is_file()


def test_nonzero_exit_cannot_be_repaired_by_a_completed_final_message(tmp_path, monkeypatch):
    state = fake_process(monkeypatch, returncode=9)
    result = run(tmp_path)
    assert not result.success and result.error == "nonzero_exit" and result.final_text is None
    assert result.usage == USAGE and len(state["calls"]) == 1


@pytest.mark.parametrize("failure,status,error", [
    (subprocess.TimeoutExpired("fake", 2), "timed_out", "process_timeout"),
    (KeyboardInterrupt(), "cancelled", "process_cancelled"),
])
def test_timeout_or_cancellation_kills_drains_and_never_retries(tmp_path, monkeypatch, failure, status, error):
    raw = jsonl(events()[:2])
    state = fake_process(monkeypatch, raw=raw, failure=failure, write_response=False)
    result = run(tmp_path, timeout_seconds=2)
    assert not result.success and result.status == status and result.error == error
    assert len(state["calls"]) == 1 and state["kills"] == 1
    assert len(state["communicate"]) == 2
    assert state["communicate"][1] == (None, 5)
    assert Path(result.artifact_paths["events"]).read_bytes() == raw
    assert Path(result.artifact_paths["stderr"]).read_bytes() == b"retained diagnostic bytes\n"
    assert Path(result.artifact_paths["exception"]).is_file()


def test_launch_failure_preserves_request_and_no_exception_text_is_published(tmp_path, monkeypatch):
    def fail(*_, **__):
        raise FileNotFoundError("private diagnostic detail")

    monkeypatch.setattr(actor.subprocess, "Popen", fail)
    result = run(tmp_path)
    assert not result.success and result.status == "launch_failed"
    assert result.public_summary["attempts_started"] == 0
    assert "private diagnostic detail" not in json.dumps(result.public_summary)
    assert "private diagnostic detail" in Path(result.artifact_paths["exception"]).read_text(encoding="utf-8")
    assert Path(result.artifact_paths["request"]).is_file()


def test_cancellation_during_launch_is_retained_with_no_process(tmp_path, monkeypatch):
    def cancel(*_, **__):
        raise KeyboardInterrupt

    monkeypatch.setattr(actor.subprocess, "Popen", cancel)
    result = run(tmp_path)
    assert result.status == "cancelled" and result.error == "process_cancelled"
    assert result.returncode is None and result.public_summary["attempts_started"] == 0
    assert Path(result.artifact_paths["exception"]).is_file()


def test_missing_executable_is_recorded_without_a_launch(tmp_path, monkeypatch):
    monkeypatch.setattr(actor.shutil, "which", lambda _: None)
    monkeypatch.setattr(actor.subprocess, "Popen", lambda *_, **__: pytest.fail("must not execute"))
    result = actor.run_actor("observed history", tmp_path / "missing", cwd=tmp_path)
    assert result.error == "codex_executable_not_found" and result.status == "launch_failed"
    assert result.public_summary["attempts_started"] == 0


def test_existing_attempt_directory_cannot_be_overwritten_or_reused(tmp_path, monkeypatch):
    destination = tmp_path / "attempt"
    destination.mkdir()
    marker = destination / "retained.txt"
    marker.write_text("prior attempt", encoding="utf-8")
    monkeypatch.setattr(actor.subprocess, "Popen", lambda *_, **__: pytest.fail("must not execute"))
    with pytest.raises(FileExistsError):
        run(tmp_path)
    assert marker.read_text(encoding="utf-8") == "prior attempt"


@pytest.mark.parametrize("prompt,timeout", [(None, 1), ("", 1), ("x", True), ("x", 0), ("x", float("nan"))])
def test_invalid_arguments_do_not_start_a_process_or_create_an_attempt(tmp_path, monkeypatch, prompt, timeout):
    monkeypatch.setattr(actor.subprocess, "Popen", lambda *_, **__: pytest.fail("must not execute"))
    with pytest.raises(ValueError):
        actor.run_actor(prompt, tmp_path / "attempt", timeout_seconds=timeout, cwd=tmp_path)
    assert not (tmp_path / "attempt").exists()
