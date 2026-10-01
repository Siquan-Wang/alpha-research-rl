"""Synthetic public-HTML integrity checks; no market arrays or scoring."""

import copy
import hashlib
import json
from pathlib import Path

import pytest
from test_astra_pool_diagnosis import Harness
from test_public_astra_pool_replay_script import api as api  # noqa: PLC0414 - pytest fixture re-export
from test_public_astra_pool_replay_script import saved as saved  # noqa: PLC0414 - pytest fixture re-export

from alpha_research_rl import astra_pool_explorer as explorer


@pytest.fixture
def page(api, saved):
    root, _, report, _, _, verified = saved
    raw = report.read_bytes()
    payload = {"schema": "astra-pool-explorer-payload-v1", "verification": verified,
               "report_sha256": hashlib.sha256(raw).hexdigest(), "report_bytes": len(raw),
               "report_json": raw.decode("utf-8"), "captured_execution_file_count": 219,
               "renderer_sha256": hashlib.sha256(Path(explorer.__file__).read_bytes()).hexdigest()}
    html_path = root / api["EXPLORER_PATH"]
    html_path.parent.mkdir(parents=True)
    html_path.write_bytes(explorer.render(payload).encode("utf-8"))
    return root, html_path, payload


@pytest.mark.parametrize("crlf", [False, True])
def test_rebuilds_expected_paths_and_accepts_only_outer_line_ending_difference(api, page, crlf):
    root, path, payload = page
    if crlf:
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    calls = []

    def build(*args, **kwargs):
        calls.append((args, kwargs))
        return payload

    result = api["verify_published_pool_explorer"](root, build=build)
    contract = root / api["CONTRACT_PATH"]
    assert calls == [((contract, contract.parent / "execution", root / api["REPORT_PATH"]), {"source_root": root})]
    assert result["explorer_payload_and_template_match"] is True
    assert result["explorer_report_bytes_exact"] is True
    assert result["explorer_html_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize("kind", ["report-bytes", "renderer-hash", "integer-type", "extra-metadata", "verification"])
def test_changed_envelope_is_rejected_even_when_rendered_with_current_template(api, page, kind):
    root, path, expected = page
    changed = copy.deepcopy(expected)
    if kind == "report-bytes":
        changed["report_json"] += "\r\n"  # Semantically equal JSON still differs from captured bytes.
    elif kind == "renderer-hash":
        changed["renderer_sha256"] = "0" * 64
    elif kind == "integer-type":
        changed["captured_execution_file_count"] = 219.0
    elif kind == "extra-metadata":
        changed["unaudited"] = True
    else:
        changed["verification"]["raw_market_data_reads"] = False
    path.write_bytes(explorer.render(changed).encode("utf-8"))
    with pytest.raises(ValueError, match="embedded report and metadata"):
        api["verify_published_pool_explorer"](root, build=lambda *_a, **_k: expected)


@pytest.mark.parametrize("kind", ["template", "script", "duplicate-json-key"])
def test_changed_full_html_is_rejected_even_with_semantically_matching_payload(api, page, kind):
    root, path, expected = page
    html = path.read_bytes().decode("utf-8")
    if kind == "template":
        html = html.replace("unattainable hindsight oracle", "feasible live trading policy")
    elif kind == "script":
        html = html.replace("'use strict';", "'use strict';alert('tampered');")
    else:
        html = html.replace('"schema":"astra-pool-explorer-payload-v1",',
                            '"schema":"astra-pool-explorer-payload-v1",'
                            '"schema":"astra-pool-explorer-payload-v1",', 1)
    path.write_bytes(html.encode("utf-8"))
    with pytest.raises(AssertionError, match="full HTML"):
        api["verify_published_pool_explorer"](root, build=lambda *_a, **_k: expected)


@pytest.mark.parametrize("kind", ["missing-page", "missing-envelope", "duplicate-envelope"])
def test_required_page_and_single_envelope_cannot_be_silently_skipped(api, page, kind):
    root, path, expected = page
    if kind == "missing-page":
        path.unlink()
    elif kind == "missing-envelope":
        path.write_text("<html>no evidence</html>", encoding="utf-8")
    else:
        html = explorer.render(expected)
        path.write_bytes((html + '<script id="pool-data" type="application/json">{}</script>').encode("utf-8"))
    with pytest.raises((FileNotFoundError, AssertionError)):
        api["verify_published_pool_explorer"](
            root, build=lambda *_a, **_k: pytest.fail("missing evidence cannot reach builder"))


def test_main_always_runs_report_then_explorer_under_guards(api, page, monkeypatch, capsys):
    root, _, payload = page
    calls = []
    namespace = api["main"].__globals__
    monkeypatch.setitem(namespace, "__file__", str(root / "scripts/replay_published_astra_pool.py"))
    monkeypatch.setitem(namespace, "install_guards", lambda actual: calls.append(("guards", actual)))
    hashes = {"contract_sha256": payload["verification"]["contract_sha256"],
              "report_sha256": payload["report_sha256"]}

    def report(actual):
        calls.append(("report", actual))
        return {"status": "matches_published_astra_pool_evidence", **hashes}

    def html(actual):
        calls.append(("html", actual))
        return {"explorer_payload_and_template_match": True, **hashes}

    monkeypatch.setitem(namespace, "verify_published_pool", report)
    monkeypatch.setitem(namespace, "verify_published_pool_explorer", html)
    api["main"]()
    assert calls == [("guards", root), ("report", root), ("html", root)]
    assert json.loads(capsys.readouterr().out)["explorer_payload_and_template_match"] is True
    monkeypatch.setitem(namespace, "verify_published_pool_explorer", lambda _: {**hashes, "report_sha256": "0" * 64})
    with pytest.raises(AssertionError, match="different evidence"):
        api["main"]()
    monkeypatch.setitem(namespace, "verify_published_pool_explorer", lambda _: (_ for _ in ()).throw(FileNotFoundError()))
    with pytest.raises(FileNotFoundError):
        api["main"]()


def test_full_synthetic_saved_bank_is_replayed_then_page_rebuilt(api, tmp_path, monkeypatch):
    harness = Harness(tmp_path, monkeypatch)
    harness.prepare()
    harness.publish()
    harness.execute()
    report_path = harness.root / api["REPORT_PATH"]
    report_path.parent.mkdir(parents=True)
    report_path.write_bytes((harness.execution / "COMPLETE.json").read_bytes())
    payload = explorer.build_payload(harness.contract_path, harness.execution, report_path, source_root=harness.root)
    html_path = harness.root / api["EXPLORER_PATH"]
    html_path.write_bytes(explorer.render(payload).encode("utf-8"))
    harness.data.unlink()
    from alpha_research_rl import astra_pool_diagnosis as diagnosis

    monkeypatch.setattr(diagnosis, "_data_bytes", lambda *_: pytest.fail("no raw data"))
    monkeypatch.setattr(diagnosis, "_load_tasks", lambda *_: pytest.fail("no market scoring"))
    monkeypatch.setattr(diagnosis, "_versions", lambda: pytest.fail("no scoring environment"))
    report = api["verify_published_pool"](harness.root)
    page = api["verify_published_pool_explorer"](harness.root)
    assert report["report_sha256"] == page["report_sha256"] == payload["report_sha256"]
    assert page["explorer_payload_and_template_match"] is True
    assert len(harness.calls) == 108  # Only synthetic fixture construction called its fake evaluator.
