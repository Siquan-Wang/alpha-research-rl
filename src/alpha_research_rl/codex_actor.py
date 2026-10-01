"""One response-only native Codex CLI attempt, with complete local transport evidence.

Uses the user's existing CLI login without inspecting credentials. There is no
retry, API-key handling, subprocess shell, model loader, or tool-result broker.
Only the narrow event sequence observed in the transport smoke is accepted.
Packet/DSL validity belongs to agentic_research, even for malformed final text.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

MODEL = "gpt-6-astra"
REASONING_EFFORT = "ultra"
SERVICE_TIER = "default"
CLI_VERSION_CONTRACT = "0.159.2"
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["propose"]},
        "expression": {"type": "string"},
        "hypothesis": {"type": "string"},
        "revision": {"type": "string"},
    },
    "required": ["action", "expression", "hypothesis", "revision"],
    "additionalProperties": False,
}
USAGE_KEYS = frozenset({
    "input_tokens", "cached_input_tokens", "cache_write_input_tokens", "output_tokens", "reasoning_output_tokens",
})


@dataclass(frozen=True)
class ActorResult:
    success: bool
    status: str
    error: str | None
    final_text: str | None
    usage: dict[str, int] | None
    returncode: int | None
    artifact_paths: dict[str, str]
    public_summary: dict


class TransportError(ValueError):
    """A stable, publication-safe error code; raw evidence stays in local files."""


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise TransportError("duplicate_event_field")
        result[key] = value
    return result


def _reject_constant(_: str):
    raise TransportError("nonfinite_event_value")


def _validated_usage(value: object) -> dict[str, int]:
    if (not isinstance(value, dict) or not {"input_tokens", "output_tokens"} <= set(value)
            or not set(value) <= USAGE_KEYS
            or any(type(count) is not int or count < 0 for count in value.values())):
        raise TransportError("invalid_usage")
    return dict(value)


def _reported_usage_records(raw: bytes) -> list[dict]:
    """Retain valid numeric usage reports even when the response stream fails.

    These reports never establish lifecycle success. Multiple completion reports
    remain separate rather than selecting one or guessing whether they overlap.
    """
    reports = []
    for number, line in enumerate(raw.splitlines(), start=1):
        try:
            event = json.loads(line.decode("utf-8"), object_pairs_hook=_unique_object,
                               parse_constant=_reject_constant)
            if isinstance(event, dict) and event.get("type") == "turn.completed" and "usage" in event:
                reports.append({"line_1based": number, "usage": _validated_usage(event["usage"])})
        except (UnicodeError, ValueError, TypeError, RecursionError):
            continue
    return reports


def parse_response_events(raw: bytes, final_bytes: bytes) -> tuple[str, dict[str, int] | None]:
    """Accept exactly one cold-start, tool-free completed assistant response.

    Success describes only the retained event stream. It does not prove absence
    of unreported execution/context or attest the server's actual model name.
    """
    try:
        lines = raw.decode("utf-8").splitlines()
        events = [json.loads(line, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
                  for line in lines]
    except TransportError:
        raise
    except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
        raise TransportError("malformed_event_stream") from exc
    if len(events) != 4 or any(not isinstance(event, dict) for event in events):
        raise TransportError("unexpected_event_count_or_shape")
    started, turn, message, completed = events
    if (set(started) != {"type", "thread_id"} or started["type"] != "thread.started"
            or not isinstance(started["thread_id"], str) or not started["thread_id"]):
        raise TransportError("invalid_thread_start")
    if turn != {"type": "turn.started"}:
        raise TransportError("invalid_turn_start")
    if set(message) != {"type", "item"} or message["type"] != "item.completed":
        raise TransportError("unexpected_response_event")
    item = message["item"]
    if (not isinstance(item, dict) or set(item) != {"id", "type", "text"}
            or item.get("type") != "agent_message" or not isinstance(item.get("id"), str)
            or not item["id"] or not isinstance(item.get("text"), str)):
        raise TransportError("forbidden_or_invalid_response_item")
    if (set(completed) not in ({"type"}, {"type", "usage"})
            or completed.get("type") != "turn.completed"):
        raise TransportError("invalid_turn_completion")
    usage = completed.get("usage")
    if "usage" in completed:
        usage = _validated_usage(usage)
    # Preserve the exact final text: neither whitespace normalization nor JSON
    # repair may turn an incoherent transport into a completed policy attempt.
    try:
        event_text = item["text"].encode("utf-8")
    except UnicodeError as exc:
        raise TransportError("invalid_response_unicode") from exc
    if event_text != final_bytes:
        raise TransportError("last_message_mismatch")
    return item["text"], usage


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stop_process(process) -> dict | None:
    """Kill and drain the single CLI process; never start a replacement attempt."""
    try:
        process.kill()
        process.communicate(timeout=5)
    except Exception as exc:  # noqa: BLE001 - cleanup failures are retained, never retried or treated as success.
        return {"type": type(exc).__name__, "message": str(exc)}
    return None


def run_actor(
    prompt: str, output_dir: str | Path, *, timeout_seconds: float = 600,
    cwd: str | Path | None = None, executable: str | None = None,
) -> ActorResult:
    """Execute one isolated response attempt and retain evidence on every outcome.

    An existing output directory is always rejected. Caller argument errors
    raise before execution; transport/model-process failures return success=False.
    The returned final text is available only for a coherent successful transport.
    This function never reads auth files, environment secrets, or API keys.
    """
    if not isinstance(prompt, str) or not prompt:
        raise ValueError("prompt must be nonempty text")
    if (type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0):
        raise ValueError("timeout_seconds must be finite and positive")
    if executable is not None and (not isinstance(executable, str) or not executable):
        raise ValueError("executable must be a nonempty path or command name")
    prompt_bytes = prompt.encode("utf-8")
    working_directory = Path.cwd().resolve() if cwd is None else Path(cwd).resolve()
    if not working_directory.is_dir():
        raise ValueError("cwd must be an existing directory")
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=False)
    paths = {name: output / filename for name, filename in {
        "prompt": "prompt.txt", "schema": "schema.json", "request": "request.json",
        "events": "events.jsonl", "stderr": "stderr.log", "response": "response.json",
        "exception": "exception.json", "result": "result.json",
    }.items()}
    paths["prompt"].write_bytes(prompt_bytes)
    _write_json(paths["schema"], RESPONSE_SCHEMA)
    resolved_executable = executable if executable is not None else shutil.which("codex")
    command = None if resolved_executable is None else [
        resolved_executable, "exec", "--ignore-user-config", "--strict-config", "--model", MODEL,
        "-c", 'model_reasoning_effort="ultra"', "-c", 'service_tier="default"',
        "--sandbox", "read-only", "--ephemeral", "--skip-git-repo-check",
        "--output-schema", str(paths["schema"]), "--output-last-message", str(paths["response"]), "--json", "-",
    ]
    _write_json(paths["request"], {
        "argv": command, "cwd": str(working_directory), "timeout_seconds": timeout_seconds,
        "prompt_sha256": _sha256(paths["prompt"]), "schema_sha256": _sha256(paths["schema"]),
        "scope": "One response-only research decision; no tools permitted; no retry.",
        "model_requested": MODEL, "reasoning_effort_requested": REASONING_EFFORT,
        "service_tier_requested": SERVICE_TIER, "shell": False,
    })
    started_at = time.monotonic()
    started_at_utc = datetime.now(UTC).isoformat()
    status, error, exception = "failed", None, None
    returncode = None
    process = None
    with paths["events"].open("wb") as stdout, paths["stderr"].open("wb") as stderr:
        if command is None:
            status, error = "launch_failed", "codex_executable_not_found"
        else:
            try:
                process = subprocess.Popen(
                    command, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                    cwd=str(working_directory), shell=False,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
                )
                process.communicate(input=prompt_bytes, timeout=timeout_seconds)
                returncode = process.returncode
            except subprocess.TimeoutExpired as exc:
                status, error = "timed_out", "process_timeout"
                exception = {"type": type(exc).__name__, "cleanup_error": _stop_process(process)}
                returncode = process.returncode
            except KeyboardInterrupt:
                status, error = "cancelled", "process_cancelled"
                exception = {"type": "KeyboardInterrupt",
                             "cleanup_error": _stop_process(process) if process is not None else None}
                returncode = process.returncode if process is not None else None
            except Exception as exc:  # noqa: BLE001 - preserve failed-attempt evidence before returning failure.
                status, error = "launch_failed" if process is None else "failed", "process_exception"
                exception = {"type": type(exc).__name__, "message": str(exc)}
                if process is not None:
                    exception["cleanup_error"] = _stop_process(process)
                    returncode = process.returncode
    # All process streams are closed on disk before inspecting any event or text.
    final_text, usage, event_error = None, None, None
    usage_records = []
    try:
        raw_events = paths["events"].read_bytes()
        usage_records = _reported_usage_records(raw_events)
        if not paths["response"].is_file():
            raise TransportError("missing_last_message")
        final_text, usage = parse_response_events(raw_events, paths["response"].read_bytes())
    except (TransportError, OSError) as exc:
        event_error = str(exc) if isinstance(exc, TransportError) else "artifact_read_failure"
    if event_error is not None and len(usage_records) == 1:
        usage = dict(usage_records[0]["usage"])
    if error is None:
        error = "nonzero_exit" if returncode != 0 else event_error
        status = "succeeded" if error is None else "failed"
    success = error is None
    if exception is not None:
        _write_json(paths["exception"], exception)
    artifacts = {path.name: {"sha256": _sha256(path), "bytes": path.stat().st_size}
                 for path in paths.values() if path.is_file()}
    public_summary = {
        "success": success, "status": status, "error": error, "event_error": event_error,
        "returncode": returncode, "elapsed_seconds": time.monotonic() - started_at,
        "started_at_utc": started_at_utc, "ended_at_utc": datetime.now(UTC).isoformat(),
        "model_requested": MODEL, "reasoning_effort_requested": REASONING_EFFORT,
        "service_tier_requested": SERVICE_TIER, "model_attested_by_events": False,
        "cli_version_contract": CLI_VERSION_CONTRACT,
        "response_only_stream_valid": event_error is None,
        "tool_event_claim": "No tool events observed in retained stream." if event_error is None
        else "Response-only stream was not established.",
        "usage": usage, "reported_usage_records": usage_records,
        "usage_source": ("validated_completed_stream" if event_error is None else "failed_stream_report")
        if usage is not None else "unavailable_or_ambiguous",
        "attempts_started": int(process is not None), "automatic_retries": 0,
        "provider_retry_scope": "No provider retry; native CLI/service retries are not attested.",
        "artifacts": artifacts,
    }
    _write_json(paths["result"], public_summary)
    return ActorResult(
        success=success, status=status, error=error, final_text=final_text if success else None,
        usage=usage, returncode=returncode, artifact_paths={key: str(path) for key, path in paths.items()},
        public_summary=public_summary,
    )
