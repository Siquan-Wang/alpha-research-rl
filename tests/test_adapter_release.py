import copy
import io
import json
import zipfile

import pytest

from alpha_research_rl.adapter_release import (
    LABELS,
    build_archive,
    extract_verified,
    sha256,
    verify_archive,
)


@pytest.fixture
def release(tmp_path):
    root = tmp_path / "repo"
    checkpoints = {}
    for label in LABELS:
        folder = root / "models/runs" / label / "adapter"
        folder.mkdir(parents=True)
        entries = []
        for name, value in (("adapter_config.json", b'{"r":8}\r\n'),
                            ("adapter_model.safetensors", ("fixture-" + label).encode())):
            (folder / name).write_bytes(value)
            entries.append({"file": name, "bytes": len(value), "sha256": sha256(value)})
        # Accidental packaging of the whole adapter directory would leak this.
        (folder / "unpublished-notes.txt").write_text("DO NOT PACKAGE", encoding="utf-8")
        checkpoints[label] = {"files": entries}
    freeze = {"checkpoints": checkpoints}
    freeze_path = root / "artifacts/development/financial-linkage-suite-freeze-v1.json"
    freeze_path.parent.mkdir(parents=True)
    freeze_path.write_text(json.dumps(freeze), encoding="utf-8")
    license_path = root / "models/Qwen3-0.6B/LICENSE"
    license_path.parent.mkdir(parents=True)
    license_path.write_bytes(b"Fixture license")
    card = root / "docs/financial-adapters-model-card.md"
    card.parent.mkdir()
    card.write_bytes(b"Fixture model card")
    output = tmp_path / "release.zip"
    manifest_path = tmp_path / "manifest.json"
    manifest = build_archive(root, output, manifest_path)
    return root, output, manifest_path, manifest, freeze


def test_exact_deterministic_bytes_and_allowlist(release, tmp_path):
    root, output, manifest_path, manifest, freeze = release
    original = output.read_bytes()
    assert build_archive(root, output, manifest_path) == manifest
    assert output.read_bytes() == original
    contents = verify_archive(original, manifest, freeze)
    assert len(contents) == 13
    assert not any("notes" in name or "tokenizer" in name for name in contents)
    destination = tmp_path / "verified"
    extract_verified(original, manifest, freeze, destination)
    for name, data in contents.items():
        assert (destination / name).read_bytes() == data


def test_corrupt_download_writes_nothing(release, tmp_path):
    _, output, _, manifest, freeze = release
    payload = bytearray(output.read_bytes())
    payload[-1] ^= 1
    destination = tmp_path / "rejected"
    with pytest.raises(ValueError, match="archive byte identity"):
        extract_verified(bytes(payload), manifest, freeze, destination)
    assert not destination.exists()


def test_freeze_rejects_resigned_member(release):
    _, output, _, manifest, freeze = release
    contents = verify_archive(output.read_bytes(), manifest, freeze)
    name = f"{LABELS[0]}/adapter/adapter_config.json"
    contents[name] = b"{}"
    amended = copy.deepcopy(manifest)
    amended["members"][name] = {"bytes": 2, "sha256": sha256(b"{}")}
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for member, data in contents.items():
            archive.writestr(member, data)
    payload = stream.getvalue()
    amended["asset"].update(bytes=len(payload), sha256=sha256(payload))
    with pytest.raises(ValueError, match="checkpoint freeze"):
        verify_archive(payload, amended, freeze)


@pytest.mark.parametrize("bad_name", ["../escaped", "C:/escaped", "financial-sft-v1/extra"])
def test_reject_extra_and_traversal_members(release, bad_name):
    _, output, _, manifest, freeze = release
    contents = verify_archive(output.read_bytes(), manifest, freeze)
    contents[bad_name] = b"bad"
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for member, data in contents.items():
            archive.writestr(member, data)
    payload = stream.getvalue()
    amended = copy.deepcopy(manifest)
    amended["asset"].update(bytes=len(payload), sha256=sha256(payload))
    with pytest.raises(ValueError, match="unexpected members"):
        verify_archive(payload, amended, freeze)


def test_existing_destination_is_preserved(release, tmp_path):
    _, output, _, manifest, freeze = release
    destination = tmp_path / "existing"
    destination.mkdir()
    marker = destination / "original.txt"
    marker.write_bytes(b"original")
    with pytest.raises(ValueError, match="never overwritten"):
        extract_verified(output.read_bytes(), manifest, freeze, destination)
    assert marker.read_bytes() == b"original"
    assert len(list(destination.iterdir())) == 1


def test_changed_checkpoint_rejected_before_new_release(release, tmp_path):
    root, _, _, _, _ = release
    (root / "models/runs" / LABELS[0] / "adapter/adapter_config.json").write_bytes(b"changed")
    new_output = tmp_path / "new.zip"
    with pytest.raises(ValueError, match="Frozen adapter identity mismatch"):
        build_archive(root, new_output, tmp_path / "new.json")
    assert not new_output.exists()


def test_extracted_layout_preserves_checkpoint_names(release, tmp_path):
    from alpha_research_rl.financial_evaluation import checkpoint_manifest

    _, output, _, manifest, freeze = release
    destination = tmp_path / "matching-layout"
    extract_verified(output.read_bytes(), manifest, freeze, destination)
    for label in LABELS:
        identity = checkpoint_manifest(destination / label / "adapter")
        assert identity["adapter_name"] == label
        assert identity["files"] == freeze["checkpoints"][label]["files"]
