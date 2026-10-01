"""Publication boundaries for the Astra evidence view; no model or market calls."""

import json
from html.parser import HTMLParser

import pytest

from alpha_research_rl import astra_explorer as explorer


def test_model_text_cannot_escape_embedded_json():
    class Scripts(HTMLParser):
        def __init__(self):
            super().__init__()
            self.script_ids = []
            self.inside_data = False
            self.data = []

        def handle_starttag(self, tag, attrs):
            if tag == "script":
                self.script_ids.append(dict(attrs).get("id"))
                self.inside_data = dict(attrs).get("id") == "astra-data"

        def handle_endtag(self, tag):
            if tag == "script":
                self.inside_data = False

        def handle_data(self, data):
            if self.inside_data:
                self.data.append(data)

    payload = {"public_model_text": '</script><script>alert("model")</script>&\u2028\u2029'}
    parsed = Scripts()
    parsed.feed(explorer.render(payload))
    assert parsed.script_ids == ["astra-data", None]
    assert json.loads("".join(parsed.data)) == payload


def test_failed_evidence_verification_produces_no_page(tmp_path, monkeypatch):
    def reject(*args, **kwargs):
        raise ValueError("incomplete or inconsistent fixed bank")

    monkeypatch.setattr(explorer, "replay_study", reject)
    output = tmp_path / "evidence.html"
    inputs = [tmp_path / name for name in ("contract.json", "submissions.json", "assessment.json")]
    for path in inputs:
        path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="fixed bank"):
        explorer.main(["--contract", str(inputs[0]), "--submissions", str(inputs[1]),
                       "--assessment", str(inputs[2]), "--output", str(output)])
    assert not output.exists()


def test_existing_evidence_is_not_replaced(tmp_path):
    output = tmp_path / "evidence.html"
    output.write_text("preserve existing artifact", encoding="utf-8")
    with pytest.raises(SystemExit):
        explorer.main(["--contract", "missing.json", "--submissions", "missing.json",
                       "--assessment", "missing.json", "--output", str(output)])
    assert output.read_text(encoding="utf-8") == "preserve existing artifact"
