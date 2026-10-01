"""Tiny synthetic public-evidence fixtures; no actors, market files, or 60 disk rounds."""

import copy
import hashlib
import json
import math
from pathlib import Path

import pytest

from alpha_research_rl import astra_replay as replay
from alpha_research_rl.agentic_research import (
    ACTOR_INSTRUCTIONS,
    ARMS,
    ResearchEpisode,
    canonical_json,
    digest,
)
from alpha_research_rl.codex_actor import CLI_VERSION_CONTRACT, RESPONSE_SCHEMA

ROOT = Path(__file__).resolve().parents[1]
STAMP = "2026-10-01T00:00:00+00:00"


def seal(value):
    body = {key: item for key, item in value.items() if key != "body_sha256"}
    return {**body, "body_sha256": digest(body)}


def metrics(value=0.1):
    return {"mean_ic": value, "coverage": 1.0, "ic_std": 0.2, "n_dates": 100, "n_signal_dates": 100}


def initial():
    return {"supported_features": ["returns"], "max_lookback": 60, "horizon_sessions": 5, "proposal_cost": 0.01,
            "probe_evidence": [{"expression": expression, "feedback": metrics(), "feedback_usable": True,
                                "windows": [metrics(), metrics(), metrics()]}
                               for expression in ("ts_mean(returns,5)", "ts_mean(returns,20)")]}


def packet(expression):
    return json.dumps({"action": "propose", "expression": expression,
                       "hypothesis": "Synthetic fixture only.", "revision": "No market data."})


def transport(prompt, raw, attempt, *, missing=False, partial=False):
    usage = None if missing else {"input_tokens": 100, "output_tokens": 20, "reasoning_output_tokens": 5,
                                 "cached_input_tokens": 0, "cache_write_input_tokens": 0}
    if partial:
        usage.pop("reasoning_output_tokens")
    artifacts = {name: {"sha256": "a" * 64, "bytes": 1} for name in (
        "prompt.txt", "schema.json", "request.json", "events.jsonl", "stderr.log", "response.json",
    )}
    for name, text in (("prompt.txt", prompt), ("response.json", raw)):
        artifacts[name] = {"sha256": hashlib.sha256(text.encode()).hexdigest(), "bytes": len(text.encode())}
    return {"success": True, "status": "succeeded", "error": None, "event_error": None, "returncode": 0,
            "elapsed_seconds": float(attempt), "started_at_utc": STAMP, "ended_at_utc": STAMP,
            "model_requested": "gpt-6-astra", "reasoning_effort_requested": "ultra", "service_tier_requested": "default",
            "model_attested_by_events": False, "cli_version_contract": CLI_VERSION_CONTRACT,
            "response_only_stream_valid": True, "tool_event_claim": "No tool events observed in retained stream.",
            "usage": usage, "reported_usage_records": [] if missing else [{"line_1based": 4, "usage": usage}],
            "usage_source": "unavailable_or_ambiguous" if missing else "validated_completed_stream",
            "attempts_started": 1, "automatic_retries": 0,
            "provider_retry_scope": "No provider retry; native CLI/service retries are not attested.", "artifacts": artifacts}


@pytest.fixture(scope="module")
def synthetic():
    episodes = []
    for task, arm in replay.PAIRS:
        episode = ResearchEpisode(arm, initial(), lambda expression: {
            **metrics(-0.4 if expression == "neg(returns)" else 0.1), "usable": True,
        })
        raws = [packet("returns"), packet("(returns)"), "invalid JSON", packet("volume"),
                packet("neg(returns)"), packet("delay(returns,1)")]
        if (task, arm) == ("2020-H1", "withheld_feedback"):
            raws = ["invalid JSON"] * 6
        summaries = []
        for attempt, raw in enumerate(raws, start=1):
            summaries.append(transport(episode.prompt(), raw, attempt,
                                       missing=task == "2020-H1" and arm == "validity_only" and attempt == 1,
                                       partial=task == "2020-H1" and arm == "withheld_feedback" and attempt == 1))
            episode.submit(raw)
        episodes.append({"task_id": task, "arm": arm, "submission": episode.freeze(), "transport_summaries": summaries})
    prompt_hash = hashlib.sha256(ResearchEpisode(ARMS[0], initial(), lambda _: None).prompt().encode()).hexdigest()
    plan = "docs/astra-agent-research-plan-v1.md"
    contract = seal({
        "study": "astra-agent-research-v1", "created_utc": STAMP, "task_order": list(replay.TASK_IDS),
        "arms": list(ARMS), "attempts_per_episode": 6,
        "round_order": [[task, attempt] for task in replay.TASK_IDS for attempt in range(1, 7)],
        "data": {"path": "data/never-open-this.zip",
                 "sha256": "8f394fe34bea54d41b9aafed410425ee8f8e252ede3c71a7c1cd20bab83040de"},
        "plan": {"path": plan, "sha256": hashlib.sha256((ROOT / plan).read_bytes()).hexdigest()},
        "source_sha256": {f"src/alpha_research_rl/{name}": hashlib.sha256(
            (ROOT / "src/alpha_research_rl" / name).read_bytes()).hexdigest() for name in replay.SOURCE_NAMES},
        "task_manifest_sha256": dict.fromkeys(replay.TASK_IDS, "b" * 64),
        "model_settings": replay.MODEL_SETTINGS.copy(),
        "interface": {"actor_instructions_sha256": hashlib.sha256(ACTOR_INSTRUCTIONS.encode()).hexdigest(),
                      "response_schema_sha256": digest(RESPONSE_SCHEMA), "cli_version_contract": CLI_VERSION_CONTRACT},
        "runtime_versions": dict.fromkeys(("python", "numpy", "pandas", "scipy"), "synthetic-version"),
        "cli_identity": {"executable_name": "codex.exe", "sha256": "c" * 64, "version": "codex-cli 0.159.2"},
        "actor_context_relative_to_study": "actor-context",
        "initial_prompt_sha256": dict.fromkeys(replay.TASK_IDS, prompt_hash), "assessment_score_calls": 0,
        "quota_stop_remaining_percent": 5,
        "assessment_gate": "all 30 six-attempt episodes frozen; separate assess command",
    })
    submissions = {"study": "astra-agent-research-v1", "stage": "all-submissions-frozen", "frozen_utc": STAMP,
                   "contract_sha256": "", "episode_count": 30, "completed_response_count": 180,
                   "assessment_score_calls": 0, "episodes": episodes, "round_sha256": dict.fromkeys(replay.ROUNDS, "d" * 64)}
    return contract, submissions


def assessment_fixture(episodes, submissions_hash):
    rows = []
    for item in episodes:
        selection = item["submission"]["selection"]
        if selection is None:
            outcome = {"status": "invalid", "reason": "all_proposals_invalid_or_unusable", "reward": -1.06,
                       "cost": 0.06, "oriented_future_ic": None, "assessment_evaluator_called": False}
        else:
            value = {ARMS[0]: 0.2, ARMS[1]: 0.1, ARMS[2]: -0.05}[item["arm"]]
            valid = (item["task_id"], item["arm"]) != ("2020-H2", "full_feedback")
            future = metrics(value) if valid else {**metrics(None), "n_dates": 0, "coverage": 0.0}
            feedback = item["submission"]["records"][selection["attempt"] - 1]["feedback"]
            ic = value * selection["orientation"] if valid else None
            outcome = {"expression": selection["expression"], "reward": ic - 0.06 if valid else -1.06,
                       "cost": 0.06, "status": "ok" if valid else "unscorable",
                       "reason": None if valid else "insufficient_assessment_support", "anchor_reuse": False,
                       "orientation": selection["orientation"],
                       "feedback": {k: v for k, v in feedback.items() if k != "usable"}, "assessment": future,
                       "oriented_future_ic": ic, "zero_feedback_tie": False,
                       "one_proposal_reward": ic - 0.01 if valid else -1.01, "assessment_evaluator_called": True}
        rows.append({"task_id": item["task_id"], "arm": item["arm"], "outcome": outcome})
    lookup = {(row["task_id"], row["arm"]): row["outcome"] for row in rows}
    paired = [{"task_id": task, **{name: lookup[task, left]["reward"] - lookup[task, right]["reward"]
                                    for name, left, right in replay.CONTRASTS}} for task in replay.TASK_IDS]
    arms = {}
    for arm in ARMS:
        outcomes = [lookup[task, arm] for task in replay.TASK_IDS]
        valid = [row for row in outcomes if row["status"] == "ok"]
        p = len(valid) / 10
        q = sum(row["oriented_future_ic"] for row in valid) / 10
        arms[arm] = {"task_count": 10, "valid_assessment_count": len(valid), "validity_fraction_p": p,
                     "predictive_contribution_q": q, "mean_utility": sum(row["reward"] for row in outcomes) / 10,
                     "conditional_valid_mean_ic": q / p if p else None}
    contrasts = {name: {"mean_utility_difference": sum(row[name] for row in paired) / 10,
                        "validity_contribution": arms[left]["validity_fraction_p"] - arms[right]["validity_fraction_p"],
                        "predictive_contribution": arms[left]["predictive_contribution_q"] -
                        arms[right]["predictive_contribution_q"]} for name, left, right in replay.CONTRASTS}
    years = [{"year": year, **{name: sum(row[name] for row in paired if row["task_id"].startswith(str(year))) / 2
                               for name, _, _ in replay.CONTRASTS}} for year in range(2020, 2025)]
    return seal({"study": "astra-agent-research-v1", "stage": "development-assessment-complete", "episode_count": 30,
                 "paired_task_count": 10, "results": rows, "paired": paired,
                 "primary_mean_full_minus_validity": contrasts["full_minus_validity"]["mean_utility_difference"],
                 "arm_summaries": arms, "contrasts": contrasts, "year_averages": years,
                 "submissions_sha256": submissions_hash,
                 "interpretation": "descriptive development; no untouched holdout or profitability claim"})


def write_fixture(tmp_path, synthetic, *, mutate=None, assess=False, mutate_assessment=None):
    contract, submissions = copy.deepcopy(synthetic)
    if mutate:
        mutate(contract, submissions)
    contract_path, submissions_path = tmp_path / "contract.json", tmp_path / "submissions.json"
    contract_path.write_text(canonical_json(seal(contract)), encoding="utf-8")
    submissions["contract_sha256"] = hashlib.sha256(contract_path.read_bytes()).hexdigest()
    submissions_path.write_text(canonical_json(seal(submissions)), encoding="utf-8")
    assessment_path = None
    if assess:
        assessment = assessment_fixture(submissions["episodes"], hashlib.sha256(submissions_path.read_bytes()).hexdigest())
        if mutate_assessment:
            mutate_assessment(assessment)
        assessment_path = tmp_path / "assessment.json"
        assessment_path.write_text(canonical_json(seal(assessment)), encoding="utf-8")
    return contract_path, submissions_path, assessment_path


def invoke(paths):
    return replay.replay_study(paths[0], paths[1], source_root=ROOT, assessment_path=paths[2])


def test_complete_structural_and_arithmetic_replay_needs_no_actor_or_market_file(tmp_path, synthetic, monkeypatch):
    import subprocess

    monkeypatch.setattr(subprocess, "Popen", lambda *_, **__: pytest.fail("no process may start"))
    result = invoke(write_fixture(tmp_path, synthetic, assess=True))
    assert result["status"] == "STRUCTURALLY_VERIFIED" and result["attempt_count"] == 180
    assert result["selected_episode_count"] == 29
    assert result["financial_scores_recomputed"] is False and result["market_data_reads"] == 0
    assert result["assessment"]["status"] == "SAVED_ARITHMETIC_VERIFIED"
    full = result["usage_by_arm"]["full_feedback"]
    assert full["token_fields"]["output_tokens"]["complete_sum"] == 1200
    assert full["token_fields"]["reasoning_output_tokens"]["complete_sum"] == 300
    assert full["elapsed_seconds"] == {"total": 210.0, "minimum": 1.0, "maximum": 6.0}
    assert result["usage_by_arm"]["validity_only"]["missing_usage_decisions"] == 1
    missing = result["usage_by_arm"]["validity_only"]["token_fields"]["input_tokens"]
    assert missing == {"reported_sum": 5900, "reported_decisions": 59, "missing_decisions": 1, "complete_sum": None}
    partial = result["usage_by_arm"]["withheld_feedback"]["token_fields"]["reasoning_output_tokens"]
    assert partial["missing_decisions"] == 1 and partial["complete_sum"] is None


@pytest.mark.parametrize("field,value", [
    ("attempt", True), ("cost", 0.02), ("prompt_sha256", "e" * 64), ("canonical_duplicate", True),
    ("canonical_ast", "changed"), ("visible_feedback", {"attempt_recorded": True}),
    ("failure_code", "invented"), ("packet", {}),
])
def test_resealed_attempt_tampering_cannot_hide_mask_cost_or_identity_drift(tmp_path, synthetic, field, value):
    def mutate(_, submissions):
        saved = submissions["episodes"][0]["submission"]
        saved["records"][0][field] = value
        saved.update(seal(saved))

    with pytest.raises(ValueError):
        invoke(write_fixture(tmp_path, synthetic, mutate=mutate))


@pytest.mark.parametrize("mutation", [
    lambda rows: rows.pop(), lambda rows: rows.__setitem__(1, copy.deepcopy(rows[0])),
    lambda rows: rows[0]["transport_summaries"].pop(),
    lambda rows: rows[0]["transport_summaries"][0].update(success=False),
    lambda rows: rows[0]["transport_summaries"][0].update(returncode=False),
    lambda rows: rows[0]["transport_summaries"][0].update(elapsed_seconds=True),
    lambda rows: rows[0]["transport_summaries"][0]["usage"].update(input_tokens=True),
    lambda rows: rows[0]["submission"]["records"].pop(),
    lambda rows: rows[0]["submission"]["selection"].update(attempt=1),
])
def test_fixed_denominator_successful_transport_and_selector_are_required(tmp_path, synthetic, mutation):
    with pytest.raises(ValueError):
        invoke(write_fixture(tmp_path, synthetic, mutate=lambda _, s: mutation(s["episodes"])))


@pytest.mark.parametrize("mutation", [
    lambda c: c["source_sha256"].update({"src/alpha_research_rl/dsl.py": "0" * 64}),
    lambda c: c["plan"].update(sha256="0" * 64),
    lambda c: c["plan"].update(path="../private.md"),
    lambda c: c["data"].update(path="../private.zip"),
    lambda c: c["initial_prompt_sha256"].update({"2020-H1": "0" * 64}),
    lambda c: c.update(attempts_per_episode=6.0),
])
def test_contract_identity_and_paths_fail_closed_before_data_access(tmp_path, synthetic, mutation):
    with pytest.raises(ValueError):
        invoke(write_fixture(tmp_path, synthetic, mutate=lambda c, _: mutation(c)))


@pytest.mark.parametrize("mutation", [
    lambda a: a.update(submissions_sha256="0" * 64),
    lambda a: a["results"][0]["outcome"].update(orientation=1),
    lambda a: a["results"][0]["outcome"].update(reward=0.2),
    lambda a: a["results"][0]["outcome"].update(cost=0.01),
    lambda a: a["results"][0]["outcome"].update(status="unknown"),
    lambda a: a["results"][0]["outcome"].update(assessment_evaluator_called=1),
    lambda a: a["results"][0]["outcome"]["assessment"].update(coverage=0.1),
    lambda a: a["results"].pop(),
    lambda a: a["paired"][1].update(full_minus_validity=0.7),
    lambda a: a["arm_summaries"]["full_feedback"].update(predictive_contribution_q=0.7),
    lambda a: a["contrasts"]["validity_minus_withheld"].update(validity_contribution=0.7),
    lambda a: a["year_averages"][4].update(full_minus_withheld=0.7),
    lambda a: a["year_averages"][4].update(year=2024.0),
    lambda a: a.update(primary_mean_full_minus_validity=1),
])
def test_optional_assessment_checks_every_row_and_all_aggregates(tmp_path, synthetic, mutation):
    with pytest.raises(ValueError):
        invoke(write_fixture(tmp_path, synthetic, assess=True, mutate_assessment=mutation))


def test_only_computed_float_arithmetic_has_small_absolute_tolerance(tmp_path, synthetic):
    def rounding(assessment):
        value = assessment["primary_mean_full_minus_validity"]
        assessment["primary_mean_full_minus_validity"] = math.nextafter(value, math.inf)

    assert invoke(write_fixture(tmp_path, synthetic, assess=True, mutate_assessment=rounding))["assessment"]


def test_cli_refuses_existing_output_and_input_collision_before_replay(tmp_path, synthetic, monkeypatch):
    paths = write_fixture(tmp_path, synthetic)
    monkeypatch.setattr(replay, "replay_study", lambda *_, **__: pytest.fail("must reject before replay"))
    arguments = ["--contract", str(paths[0]), "--submissions", str(paths[1]), "--source-root", str(ROOT)]
    for destination in (paths[0], paths[1]):
        with pytest.raises(SystemExit) as error:
            replay.main(arguments + ["--output", str(destination)])
        assert error.value.code == 2
    output = tmp_path / "retained.json"
    output.write_bytes(b"retained")
    with pytest.raises(SystemExit):
        replay.main(arguments + ["--output", str(output)])
    assert output.read_bytes() == b"retained"


def test_cli_creates_one_fresh_report(tmp_path, synthetic):
    paths = write_fixture(tmp_path, synthetic)
    output = tmp_path / "replay.json"
    replay.main(["--contract", str(paths[0]), "--submissions", str(paths[1]),
                 "--source-root", str(ROOT), "--output", str(output)])
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "STRUCTURALLY_VERIFIED"
