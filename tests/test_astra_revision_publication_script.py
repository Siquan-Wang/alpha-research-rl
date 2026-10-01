"""Fake public retrieval exercises the actual receipt boundary without network."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/verify_astra_revision_publication.py"
SPEC = importlib.util.spec_from_file_location("revision_publication_script", SCRIPT)
publication = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publication)


def setup(tmp_path):
    raw = b"PUBLIC SYNTHETIC EVIDENCE\n"
    (tmp_path / "evidence.json").write_bytes(raw)
    wanted = {"evidence.json": hashlib.sha256(raw).hexdigest()}
    receipt = tmp_path / ".local" / publication.STUDY / "receipt.json"
    commit = "a" * 40
    calls = []

    def fetch(url):
        calls.append(url)
        return json.dumps({"sha": commit}).encode() if "/commits/" in url else raw

    kwargs = {"root": tmp_path, "stage": "preparation", "commit": commit, "receipt_path": receipt,
              "expected": wanted, "fetch": fetch}
    return kwargs, calls


def test_complete_exact_map_exclusive_receipt_and_no_authentication_arguments(tmp_path):
    kwargs, calls = setup(tmp_path)
    receipt = publication.verify_publication(**kwargs)
    assert len(calls) == 2 and all(url.startswith("https://") for url in calls)
    assert receipt["paths_sha256"] == kwargs["expected"]
    assert receipt["body_sha256"] == publication.digest({k: v for k, v in receipt.items() if k != "body_sha256"})
    assert json.loads(kwargs["receipt_path"].read_bytes()) == receipt
    with pytest.raises(ValueError, match="new path"):
        publication.verify_publication(**kwargs)
    assert len(calls) == 2


@pytest.mark.parametrize("failure", ["local", "remote", "commit", "concurrent_edit"])
def test_mismatch_writes_no_gate_receipt(tmp_path, failure):
    kwargs, _ = setup(tmp_path)
    original = kwargs["fetch"]

    def bad_fetch(url):
        raw = original(url)
        if "/commits/" in url:
            return b'{"sha":"bad"}' if failure == "commit" else raw
        if failure == "concurrent_edit":
            (tmp_path / "evidence.json").write_bytes(b"CHANGED")
        return b"DIFFERENT" if failure == "remote" else raw

    kwargs["fetch"] = bad_fetch
    if failure == "local":
        (tmp_path / "evidence.json").write_bytes(b"CHANGED BEFORE RETRIEVAL")
    with pytest.raises(ValueError):
        publication.verify_publication(**kwargs)
    assert not kwargs["receipt_path"].exists()


@pytest.mark.parametrize("path", [".local/secret", "../outside", "/absolute", "C:/private", "a\\b",
                                  "a//b", "a/./b", ".git/config", "a/../b", "", ".LOCAL/secret",
                                  "nested/.Git/config", ".VENV/file", ".local./file", ".local /file"])
def test_unsafe_or_private_expected_paths_are_rejected_before_retrieval(tmp_path, path):
    kwargs, calls = setup(tmp_path)
    kwargs["expected"] = {path: "b" * 64}
    with pytest.raises(ValueError):
        publication.verify_publication(**kwargs)
    assert not calls and not kwargs["receipt_path"].exists()


def test_resolved_alias_into_private_directory_is_rejected(tmp_path):
    kwargs, calls = setup(tmp_path)
    private = tmp_path / ".local" / "fixture"
    private.mkdir(parents=True)
    raw = b"PRIVATE SYNTHETIC FIXTURE"
    (private / "value").write_bytes(raw)
    alias = tmp_path / "public-looking"
    try:
        alias.symlink_to(private, target_is_directory=True)
    except OSError:
        pytest.skip("Directory symlinks unavailable on this host")
    kwargs["expected"] = {"public-looking/value": hashlib.sha256(raw).hexdigest()}
    with pytest.raises(ValueError, match="private directory"):
        publication.verify_publication(**kwargs)
    assert not calls and not kwargs["receipt_path"].exists()


def test_network_failure_never_creates_a_partial_success_receipt(tmp_path):
    kwargs, _ = setup(tmp_path)

    def failed(_):
        raise OSError("SYNTHETIC network unavailable")

    kwargs["fetch"] = failed
    with pytest.raises(OSError):
        publication.verify_publication(**kwargs)
    assert not kwargs["receipt_path"].exists()
