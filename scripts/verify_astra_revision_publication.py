"""Verify exact public bytes at either matched-prefix gate; never run the study."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from urllib.parse import quote
from urllib.request import Request, urlopen

from alpha_research_rl.agentic_research import canonical_json, digest

REPOSITORY = "Siquan-Wang/alpha-research-rl"
STUDY = "astra-matched-prefix-v1"
STAGES = ("preparation", "submissions")
PRIVATE_COMPONENTS = {".local", ".git", ".venv"}


def _get(url):
    request = Request(url, headers={"User-Agent": "AlphaResearch-RL-public-verification"})
    with urlopen(request, timeout=30) as response:
        return response.read()


def verify_publication(*, root, stage, commit, receipt_path, expected, fetch=_get):
    """Write one exclusive receipt after the entire required map matches anonymously.

    ``expected`` must come from the study driver's public-file reconstruction.
    The driver independently validates its exact map and committed blobs at the
    next gate. This helper alone never authorizes execution or claims a sandbox.
    """
    root, receipt_path = Path(root).resolve(), Path(receipt_path).resolve()
    if stage not in STAGES or not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise ValueError("An exact stage and full lowercase commit hash are required")
    if not receipt_path.is_relative_to(root / ".local" / STUDY) or receipt_path.exists():
        raise ValueError("Receipt must be a new path inside this study's local directory")
    if not isinstance(expected, dict) or not expected:
        raise ValueError("The reconstructed complete public file map is required")
    captured = {}
    for relative, wanted in expected.items():
        if not isinstance(relative, str):
            raise TypeError("Invalid public path")
        parts = PurePosixPath(relative).parts
        if (not parts or PurePosixPath(relative).is_absolute() or "\\" in relative or ":" in relative
                or PurePosixPath(relative).as_posix() != relative
                or any(part in {".", ".."} or part != part.rstrip(" .")
                       or part.casefold() in PRIVATE_COMPONENTS for part in parts)):
            raise ValueError("Unsafe or private public path")
        if not isinstance(wanted, str) or re.fullmatch(r"[0-9a-f]{64}", wanted) is None:
            raise ValueError("Invalid public SHA256")
        local = (root / relative).resolve()
        if not local.is_relative_to(root):
            raise ValueError("Public path escapes repository")
        if any(part.casefold() in PRIVATE_COMPONENTS for part in local.relative_to(root).parts):
            raise ValueError("Resolved public path enters a private directory")
        raw = local.read_bytes()
        if hashlib.sha256(raw).hexdigest() != wanted:
            raise ValueError("Local bytes differ: " + relative)
        captured[relative] = raw
    remote_commit = json.loads(fetch(f"https://api.github.com/repos/{REPOSITORY}/commits/{commit}"))
    if remote_commit.get("sha") != commit:
        raise ValueError("Public commit identity differs")

    def verify_file(item):
        relative, raw = item
        url = f"https://raw.githubusercontent.com/{REPOSITORY}/{commit}/" + quote(relative, safe="/")
        downloaded = fetch(url)
        if downloaded != raw:
            raise ValueError("Public bytes differ: " + relative)
        return relative, hashlib.sha256(downloaded).hexdigest()

    with ThreadPoolExecutor(max_workers=3) as pool:
        verified = dict(pool.map(verify_file, captured.items()))
    # Detect local edits during remote retrieval instead of blessing a stale snapshot.
    if any((root / relative).read_bytes() != raw for relative, raw in captured.items()):
        raise ValueError("Local public bytes changed during verification")
    body = {"schema": "astra-matched-prefix-publication-receipt-v1", "study": STUDY,
            "stage": stage, "commit": commit, "verified_utc": datetime.now(UTC).isoformat(),
            "verification_method": "root-verified unauthenticated public retrieval",
            "public_repository_url": f"https://github.com/{REPOSITORY}", "paths_sha256": verified}
    receipt = {**body, "body_sha256": digest(body)}
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    with receipt_path.open("xb") as stream:
        stream.write((canonical_json(receipt) + "\n").encode("utf-8"))
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=STAGES, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    receipt_path = args.receipt or root / ".local" / STUDY / f"publication-{args.stage}.json"
    from alpha_research_rl.astra_revision_study import publication_files

    expected = publication_files(source_root=root, stage=args.stage)
    receipt = verify_publication(root=root, stage=args.stage, commit=args.commit,
                                 receipt_path=receipt_path, expected=expected)
    print(json.dumps({"public_commit": receipt["commit"], "stage": args.stage,
                      "verified_files": len(receipt["paths_sha256"]),
                      "verified_utc": receipt["verified_utc"], "authentication_used": False}))


if __name__ == "__main__":
    main()
