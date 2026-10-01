import sys

import pytest

from alpha_research_rl.cli import main


def test_benchmark_refuses_existing_evidence_before_running(tmp_path, monkeypatch):
    from alpha_research_rl import experiments

    original = tmp_path / "saved-evidence.json"
    original.write_bytes(b"preserved published evidence\r\n")
    monkeypatch.setattr(sys, "argv", ["alpha-research", "benchmark", "--output", str(original)])

    def unexpected_run(*args, **kwargs):
        pytest.fail("existing evidence must be protected before expensive work starts")

    monkeypatch.setattr(experiments, "run_synthetic_benchmark", unexpected_run)
    with pytest.raises(FileExistsError, match="existing benchmark evidence is preserved"):
        main()
    assert original.read_bytes() == b"preserved published evidence\r\n"
