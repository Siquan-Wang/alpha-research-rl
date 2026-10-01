"""Saved-evidence integrity and HTML injection checks on original artificial data."""

import copy
import json
import re
from html.parser import HTMLParser

import pytest
from test_financial_analysis import reports as original_reports

from alpha_research_rl.evidence_explorer import local_prompt_decoder, prepare_payload, render_html
from alpha_research_rl.financial_analysis import analyze_reports


@pytest.fixture
def reports(tmp_path):
    return original_reports.__wrapped__(tmp_path)


def analysis_for(reports):
    return analyze_reports(reports, "sft", ("rl23", "rl29"))


def test_complete_archive_counts_order_and_registered_metrics(reports):
    payload = prepare_payload(reports, analysis_for(reports), [])
    assert payload["counts"] == {"checkpoints": 3, "tasks": 10, "records": 540,
                                 "stochastic_draws_per_task_condition": 8}
    assert payload["checkpoints"] == ["sft", "rl23", "rl29"]
    assert [task["task_id"] for task in payload["tasks"]] == [f"{year}-H{half}" for year in range(2020, 2025)
                                                            for half in (1, 2)]
    first = payload["records"][0]
    assert (first["checkpoint"], first["task_id"], first["condition"], first["decoding"], first["draw"]) == (
        "sft", "2020-H1", "true", "stochastic", 0)
    assert first["status"] == "invalid" and first["reward"] == -1.01
    assert first["prompt_tokens"] == 4 and first["completion_tokens"] == 2
    assert "prompt_ids" not in first and "completion_ids" not in first
    cell = payload["overall"]["metrics"]["stochastic"]
    assert cell["policies"]["sft"]["true"]["valid_fraction"] == .875
    # Independent artificial fixture: 70 successes, ten failures; equal-weight
    # task ICs average .005. No failed record disappears from the denominator.
    expected = .875 * (.005 - .01) + .125 * -1.01
    assert cell["policies"]["sft"]["true"]["mean_reward"] == pytest.approx(expected)
    delta = cell["rl_vs_sft"]["rl23"]["true"]
    assert delta["reward_delta"] == pytest.approx(delta["failure_penalty_component_delta"]
                                               + delta["all_proposal_ic_contribution_delta"])


def test_saved_aggregate_mismatch_cannot_be_published(reports):
    analysis = analysis_for(reports)
    analysis["overall"]["metrics"]["strict"]["stochastic"]["policies"]["sft"]["true"]["mean_reward"] += .1
    with pytest.raises(ValueError, match="saved analysis differs"):
        prepare_payload(reports, analysis, [])


def test_missing_retained_draw_cannot_be_published(reports):
    analysis = analysis_for(reports)
    reports["rl23"]["episodes"][0]["records"].pop()
    with pytest.raises(ValueError, match="missing proposal slots"):
        prepare_payload(reports, analysis, [])


def test_whitelist_omits_raw_arrays_tokens_weights_and_machine_paths(reports):
    for report in reports.values():
        report["raw_market_array"] = [["RAW_SENTINEL"]]
        report["manifest"]["local_path"] = "C:\\Users\\PRIVATE_SENTINEL\\model"
        for episode in report["episodes"]:
            for record in episode["records"]:
                record["weights"] = {"WEIGHT_SENTINEL": [1, 2, 3]}
    payload = prepare_payload(reports, analysis_for(reports), [{"file": "C:\\machine\\public.json", "sha256": "a"*64}])
    serialized = json.dumps(payload)
    for sentinel in ("RAW_SENTINEL", "PRIVATE_SENTINEL", "WEIGHT_SENTINEL", "prompt_ids", "completion_ids"):
        assert sentinel not in serialized
    assert payload["sources"] == [{"file": "public.json", "sha256": "a"*64}]


def test_actor_probes_are_decoded_prompt_evidence_not_scorer_feedback(reports):
    observation = {"probe_evidence": [{"expression": expression,
                    "feedback": {"mean_ic": mean, "coverage": 1, "n_dates": 100,
                                 "n_signal_dates": 100, "ic_std": .05},
                    "feedback_usable": True, "windows": []}
                   for expression, mean in (("ts_mean(returns,5)", .777), ("ts_mean(returns,20)", -.222))]}
    decoded = "<|im_start|>system\nFixture<|im_end|>\n<|im_start|>user\n" + json.dumps(observation) + "<|im_end|>"
    calls = []

    def decoder(tokens):
        calls.append(tokens)
        return decoded

    payload = prepare_payload(reports, analysis_for(reports), [], decoder=decoder)
    assert len(calls) == len(payload["prompts"]) == 20  # One per task/evidence condition, shared by checkpoints/draws.
    actual = payload["prompts"]["2020-H1/true"]["observation"]
    assert [probe["feedback"]["mean_ic"] for probe in actual["probe_evidence"]] == [.777, -.222]
    valid = next(record for record in payload["records"] if record["status"] == "ok")
    assert valid["scorer_feedback"]["mean_ic"] == .1
    assert payload["prompts"][valid["prompt_key"]]["exact_prompt"] == decoded


def test_generated_script_closure_remains_inert_exact_text(reports):
    attack = '</script><img src=x onerror="alert(1)">'
    record = reports["sft"]["episodes"][0]["records"][0]
    record["text"], record["action"] = attack, {"action": "invalid"}
    payload = prepare_payload(reports, analysis_for(reports), [], decoder=lambda tokens: attack)
    html = render_html(payload)
    assert attack not in html and "\\u003c/script>" in html
    assert "innerHTML" not in html and "textContent" in html
    embedded = re.search(r'<script id="evidence-data" type="application/json">(.*?)</script>', html, re.DOTALL).group(1)
    restored = json.loads(embedded)
    assert restored["records"][0]["text"] == attack
    assert restored["prompts"]["2020-H1/true"]["exact_prompt"] == attack

    class SecurityParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.scripts = self.images = self.external = 0

        def handle_starttag(self, tag, attrs):
            self.scripts += tag == "script"
            self.images += tag == "img"
            self.external += any(key in {"src", "href"} for key, value in attrs)

    parser = SecurityParser()
    parser.feed(html)
    assert (parser.scripts, parser.images, parser.external) == (2, 0, 0)
    # The input archive is not modified during compaction or rendering.
    again = prepare_payload(copy.deepcopy(reports), analysis_for(reports), [])
    assert again["records"][0]["text"] == attack


def test_wrong_tokenizer_cannot_mislabel_decoded_actor_observation(tmp_path):
    (tmp_path / "tokenizer.json").write_text("different tokenizer", encoding="utf-8")
    with pytest.raises(ValueError, match="differs from the recorded"):
        local_prompt_decoder(tmp_path, {"tokenizer.json": "a"*64})
    with pytest.raises(ValueError, match="unsafe tokenizer"):
        local_prompt_decoder(tmp_path, {"../tokenizer.json": "a"*64})
