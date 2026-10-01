"""Package and verify the exact five financial adapters, without loading a model.

Network access occurs only in the explicit ``fetch`` command. Extraction uses
an exact member allowlist and checks all bytes before writing new directories.
"""

import argparse
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path

LABELS = (
    "financial-sft-v1", "financial-rloo23-v1", "financial-rloo29-v1",
    "financial-placebo23-v1", "financial-placebo29-v1",
)
ADAPTER_FILES = ("adapter_config.json", "adapter_model.safetensors")
EXTRA_FILES = ("LICENSE", "MODEL_CARD.md", "NOTICE")
BASE_REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"
ASSET_NAME = "financial-adapters-v1.zip"
RELEASE_URL = "https://github.com/Siquan-Wang/alpha-research-rl/releases/download/v0.1.0/" + ASSET_NAME
MAX_ARCHIVE_BYTES = 60_000_000
NOTICE = (
    "Financial proposal adapters v1\n"
    "Base model: Qwen/Qwen3-0.6B, revision " + BASE_REVISION + "\n"
    "Copyright 2024 Alibaba Cloud. Base license: Apache-2.0.\n"
    "Modifications: new LoRA adapter tensors trained by AlphaResearch-RL; "
    "copyright 2026 AlphaResearch-RL contributors, Apache-2.0.\n"
    "The base model itself is not modified or included. "
    "No affiliation or endorsement is implied.\n"
    "Adapter/config bytes are unchanged from their recorded checkpoint freeze.\n"
)


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def expected_adapter_files(freeze: dict) -> dict[str, dict]:
    """Resolve only the literal published policy labels and two safe filenames."""
    checkpoints = freeze.get("checkpoints", {})
    if set(checkpoints) != set(LABELS):
        raise ValueError("Expected the five published financial checkpoints")
    result = {}
    for label in LABELS:
        entries = checkpoints[label]["files"]
        if len(entries) != 2 or {entry["file"] for entry in entries} != set(ADAPTER_FILES):
            raise ValueError("Unexpected adapter file inventory")
        for entry in entries:
            result[f"{label}/adapter/{entry['file']}"] = {
                "sha256": entry["sha256"], "bytes": entry["bytes"],
            }
    return result


def build_archive(root: Path, output: Path, manifest_path: Path) -> dict:
    root = root.resolve()
    freeze_path = root / "artifacts/development/financial-linkage-suite-freeze-v1.json"
    inventory = expected_adapter_files(read_json(freeze_path))
    contents = {}
    for member, identity in inventory.items():
        label, _, filename = member.split("/")
        data = (root / "models/runs" / label / "adapter" / filename).read_bytes()
        if len(data) != identity["bytes"] or sha256(data) != identity["sha256"]:
            raise ValueError(f"Frozen adapter identity mismatch: {member}")
        contents[member] = data
    contents["LICENSE"] = (root / "models/Qwen3-0.6B/LICENSE").read_bytes()
    contents["MODEL_CARD.md"] = (root / "docs/financial-adapters-model-card.md").read_bytes()
    contents["NOTICE"] = NOTICE.encode("utf-8")
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(contents.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    archive_bytes = payload.getvalue()
    if len(archive_bytes) > MAX_ARCHIVE_BYTES:
        raise ValueError("Unexpected release size")
    result = {
        "schema_version": 1,
        "asset": {"name": ASSET_NAME, "url": RELEASE_URL,
                  "bytes": len(archive_bytes), "sha256": sha256(archive_bytes)},
        "base_model": {"id": "Qwen/Qwen3-0.6B", "revision": BASE_REVISION},
        "license": "Apache-2.0",
        "freeze_sha256": sha256(freeze_path.read_bytes()),
        "builder_sha256": sha256(Path(__file__).read_bytes()),
        "members": {name: {"bytes": len(data), "sha256": sha256(data)}
                    for name, data in sorted(contents.items())},
    }
    # Review the complete archive before any output is written.
    verify_archive(archive_bytes, result, read_json(freeze_path))
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and output.read_bytes() != archive_bytes:
        raise ValueError("Refusing to overwrite a different release archive")
    if not output.exists():
        with output.open("xb") as handle:
            handle.write(archive_bytes)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    rendered = (json.dumps(result, indent=2, ensure_ascii=True) + "\n").encode()
    if manifest_path.exists() and manifest_path.read_bytes() != rendered:
        raise ValueError("Refusing to overwrite a different release manifest")
    if not manifest_path.exists():
        with manifest_path.open("xb") as handle:
            handle.write(rendered)
    return result


def verify_archive(payload: bytes, manifest: dict, freeze: dict) -> dict[str, bytes]:
    if manifest.get("schema_version") != 1:
        raise ValueError("Unsupported release manifest")
    if manifest.get("base_model") != {"id": "Qwen/Qwen3-0.6B", "revision": BASE_REVISION}:
        raise ValueError("Unexpected base model identity")
    if len(payload) != manifest["asset"]["bytes"] or sha256(payload) != manifest["asset"]["sha256"]:
        raise ValueError("Release archive byte identity mismatch")
    if len(payload) > MAX_ARCHIVE_BYTES:
        raise ValueError("Release exceeds allowed size")
    expected = expected_adapter_files(freeze)
    allowed = set(expected) | set(EXTRA_FILES)
    if set(manifest["members"]) != allowed:
        raise ValueError("Release manifest member inventory mismatch")
    if sum(entry["bytes"] for entry in manifest["members"].values()) > MAX_ARCHIVE_BYTES:
        raise ValueError("Uncompressed release exceeds allowed size")
    contents = {}
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = archive.namelist()
        if len(names) != len(allowed) or set(names) != allowed:
            raise ValueError("Archive contains missing, duplicate or unexpected members")
        for name in names:
            info = archive.getinfo(name)
            identity = manifest["members"][name]
            if info.file_size != identity["bytes"] or info.file_size > MAX_ARCHIVE_BYTES:
                raise ValueError(f"Unexpected member size: {name}")
            if name in expected and identity != expected[name]:
                raise ValueError(f"Manifest disagrees with checkpoint freeze: {name}")
            data = archive.read(info)
            if sha256(data) != identity["sha256"]:
                raise ValueError(f"Member hash mismatch: {name}")
            contents[name] = data
    return contents


def extract_verified(payload: bytes, manifest: dict, freeze: dict, destination: Path) -> None:
    contents = verify_archive(payload, manifest, freeze)
    destination = destination.resolve()
    if destination.exists():
        raise ValueError("Choose a new destination; existing paths are never overwritten")
    destination.mkdir(parents=True, exist_ok=False)
    # No extractall: only the validated literal paths above are written.
    for member, data in contents.items():
        target = destination / member
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write(data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify", "fetch"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--archive", type=Path, default=Path(".local/release") / ASSET_NAME)
    parser.add_argument("--manifest", type=Path,
                        default=Path("artifacts/releases/financial-adapters-v1.manifest.json"))
    parser.add_argument("--destination", type=Path, default=Path("models/published-financial-v1"))
    args = parser.parse_args()
    if args.command == "build":
        result = build_archive(args.root, args.archive, args.manifest)
        print(json.dumps({"status": "built", "asset": result["asset"]}))
        return
    manifest = read_json(args.manifest)
    freeze_path = args.root / "artifacts/development/financial-linkage-suite-freeze-v1.json"
    if sha256(freeze_path.read_bytes()) != manifest["freeze_sha256"]:
        raise ValueError("Freeze document byte identity mismatch")
    freeze = read_json(freeze_path)
    if args.command == "fetch":
        if args.destination.exists():
            raise ValueError("Choose a new destination before downloading")
        if manifest["asset"]["url"] != RELEASE_URL:
            raise ValueError("Unrecognized release URL")
        with urllib.request.urlopen(RELEASE_URL, timeout=120) as response:
            payload = response.read(MAX_ARCHIVE_BYTES + 1)
        extract_verified(payload, manifest, freeze, args.destination)
        print(json.dumps({"status": "verified_and_extracted", "checkpoints": len(LABELS)}))
    else:
        contents = verify_archive(args.archive.read_bytes(), manifest, freeze)
        print(json.dumps({"status": "verified", "members": len(contents), "checkpoints": len(LABELS)}))


if __name__ == "__main__":
    main()
