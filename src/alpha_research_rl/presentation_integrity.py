"""Exact presentation collisions in a supplied population; standard library only.

Records contain exactly ``id``, ``split`` and final actor-visible ``prompt``
strings, optionally ``tokenization`` with ``namespace_sha256`` and nonempty
``token_ids``. Required strings must be nonblank and encode as strict UTF-8.
Their whitespace, newline spelling and Unicode representation are preserved.
The namespace is a caller-supplied fingerprint of tokenizer, template and all
tokenization settings; this module cannot attest that provenance.

No semantic equivalence, hidden context or population completeness is checked.
The CLI reads only its supplied JSON file and optionally creates a new report.
Exit codes: 0 no observed exact cross-split collision, 1 collision found,
2 malformed input or file error. Missing token evidence remains UNCHECKED.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

INPUT_SCHEMA = "actor-visible-presentations-v1"
REPORT_SCHEMA = "presentation-integrity-report-v1"
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class PresentationInputError(ValueError):
    """The supplied evidence does not satisfy the explicit record contract."""


def _keys(value, required, optional=()):
    if type(value) is not dict or not set(required) <= value.keys() <= set(required) | set(optional):
        raise PresentationInputError("object has missing or unexpected fields")


def _text(value, name):
    if type(value) is not str or not value.strip():
        raise PresentationInputError(f"{name} must be a nonblank string")
    try:
        return value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise PresentationInputError(f"{name} must encode as strict UTF-8") from exc


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                      separators=(",", ":")).encode("ascii")


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _validated(records):
    if type(records) is not list or not records:
        raise PresentationInputError("records must be a nonempty list")
    clean, seen, token_evidence = [], set(), {}
    for row in records:
        _keys(row, {"id", "split", "prompt"}, {"tokenization"})
        _text(row["id"], "id")
        _text(row["split"], "split")
        prompt_bytes = _text(row["prompt"], "prompt")
        if row["id"] in seen:
            raise PresentationInputError("duplicate record id")
        seen.add(row["id"])
        copied = {key: row[key] for key in ("id", "split", "prompt")}
        if "tokenization" in row:
            tokenization = row["tokenization"]
            _keys(tokenization, {"namespace_sha256", "token_ids"})
            namespace, ids = tokenization["namespace_sha256"], tokenization["token_ids"]
            if type(namespace) is not str or _SHA256.fullmatch(namespace) is None:
                raise PresentationInputError("namespace_sha256 must be 64 lowercase hexadecimal characters")
            if type(ids) is not list or not ids or any(type(item) is not int or item < 0 for item in ids):
                raise PresentationInputError("token_ids must be a nonempty list of nonnegative exact integers")
            key = (namespace, prompt_bytes)
            ids_tuple = tuple(ids)
            if key in token_evidence and token_evidence[key] != ids_tuple:
                raise PresentationInputError("identical prompt in one namespace has conflicting token sequences")
            token_evidence[key] = ids_tuple
            copied["tokenization"] = {"namespace_sha256": namespace, "token_ids": list(ids)}
        clean.append(copied)
    return sorted(clean, key=lambda row: row["id"])


def _members(rows):
    return {"record_ids": [row["id"] for row in rows], "splits": sorted({row["split"] for row in rows})}


def _collision(kind, fingerprint, namespace, rows):
    first = rows[0]
    second = next(row for row in rows if row["split"] != first["split"])
    return {"kind": kind, "fingerprint": fingerprint, "namespace_sha256": namespace,
            **_members(rows), "witness_record_ids": [first["id"], second["id"]]}


def check_presentations(records: list[dict]) -> dict:
    """Return deterministic groups and witnesses without prompts or token arrays.

    Equality is tested on complete bytes/tuples, not on hashes alone. Token IDs
    are comparable only inside their supplied namespace. An identical prompt
    with inconsistent tokens in the same namespace is malformed evidence.
    Identical records within a split are retained, counted and permitted.
    """
    rows = _validated(records)
    by_prompt, by_tokens, by_split, by_namespace = (defaultdict(list) for _ in range(4))
    missing = []
    for row in rows:
        by_prompt[row["prompt"].encode("utf-8")].append(row)
        by_split[row["split"]].append(row)
        if "tokenization" not in row:
            missing.append(row["id"])
            continue
        tokens = row["tokenization"]
        namespace = tokens["namespace_sha256"]
        by_tokens[(namespace, tuple(tokens["token_ids"]))].append(row)
        by_namespace[namespace].append(row)

    prompt_groups, token_groups, collisions = [], [], []
    for prompt_bytes, members in by_prompt.items():
        fingerprint = _sha(prompt_bytes)
        group = {"prompt_sha256": fingerprint, "byte_length": len(prompt_bytes), **_members(members)}
        prompt_groups.append(group)
        if len(group["splits"]) > 1:
            collisions.append(_collision("prompt_bytes", fingerprint, None, members))
    for (namespace, token_ids), members in by_tokens.items():
        fingerprint = _sha(_canonical(list(token_ids)))
        group = {"namespace_sha256": namespace, "token_sha256": fingerprint,
                 "token_count": len(token_ids), **_members(members)}
        token_groups.append(group)
        if len(group["splits"]) > 1:
            collisions.append(_collision("token_ids", fingerprint, namespace, members))
    prompt_groups.sort(key=lambda group: (group["prompt_sha256"], group["record_ids"]))
    token_groups.sort(key=lambda group: (group["namespace_sha256"], group["token_sha256"], group["record_ids"]))
    collisions.sort(key=lambda row: (row["kind"], row["namespace_sha256"] or "",
                                     row["fingerprint"], row["record_ids"]))
    prompt_conflicts = sum(row["kind"] == "prompt_bytes" for row in collisions)
    token_conflicts = sum(row["kind"] == "token_ids" for row in collisions)
    tokenized = len(rows) - len(missing)
    coverage = "COMPLETE" if not missing else "PARTIAL" if tokenized else "ABSENT"
    comparison = ("UNCHECKED" if missing else "INCOMPARABLE_NAMESPACES" if len(by_namespace) > 1
                  else "COMPLETE_SINGLE_NAMESPACE")
    return {
        "schema": REPORT_SCHEMA,
        "status": "CONFLICT_FOUND" if collisions else "NO_OBSERVED_EXACT_CONFLICT",
        "scope": "EXACT_PROVIDED_PROMPT_BYTES_AND_SAME_NAMESPACE_SUPPLIED_TOKEN_IDS",
        "population_sha256": _sha(_canonical(rows)),
        "counts": {
            "records": len(rows), "splits": len(by_split), "prompt_groups": len(prompt_groups),
            "prompt_duplicate_groups": sum(len(group["record_ids"]) > 1 for group in prompt_groups),
            "prompt_duplicate_excess_records": len(rows) - len(prompt_groups),
            "prompt_cross_split_groups": prompt_conflicts, "tokenized_records": tokenized,
            "missing_token_records": len(missing), "token_namespaces": len(by_namespace),
            "token_groups": len(token_groups),
            "token_duplicate_groups": sum(len(group["record_ids"]) > 1 for group in token_groups),
            "token_duplicate_excess_records": tokenized - len(token_groups),
            "token_cross_split_groups": token_conflicts,
        },
        "splits": [{"split": split, "record_count": len(members),
                    "tokenized_record_count": sum("tokenization" in row for row in members)}
                   for split, members in sorted(by_split.items())],
        "prompt_groups": prompt_groups,
        "token_groups": token_groups,
        "cross_split_collisions": collisions,
        "token_evidence": {
            "coverage": coverage, "global_comparison": comparison,
            "missing_record_ids": missing,
            "observed_within_namespace_cross_split_groups": token_conflicts,
            "namespaces": [{"namespace_sha256": namespace, "record_count": len(members),
                            "splits": sorted({row["split"] for row in members}),
                            "cross_split_groups": sum(group["namespace_sha256"] == namespace
                                                      and len(group["splits"]) > 1 for group in token_groups)}
                           for namespace, members in sorted(by_namespace.items())],
        },
        "limitations": [
            "Only the supplied population is checked; omitted records cannot be detected without a manifest.",
            "Exact differences do not establish semantic difference or independent mechanisms.",
            "Prompt completeness, hidden host context and tokenizer/template provenance are not attested.",
            "Token IDs are compared only within each caller-supplied namespace; missing evidence is UNCHECKED.",
            "Within-split duplicates are reported and retained, not rejected or counted as independent tasks.",
            "Cross-split collisions are evidence findings; this tool does not repair or reassign splits.",
        ],
    }


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PresentationInputError("duplicate JSON object key")
        result[key] = value
    return result


def _nonfinite(_value):
    raise PresentationInputError("nonfinite JSON numbers are forbidden")


def _float(value):
    parsed = float(value)
    if not math.isfinite(parsed):
        _nonfinite(value)
    return parsed


def load_input(path: str | Path) -> list[dict]:
    """Read the exact UTF-8 JSON input; JSON string CR/LF escapes are preserved."""
    try:
        value = json.loads(Path(path).read_bytes().decode("utf-8", errors="strict"),
                           object_pairs_hook=_object, parse_constant=_nonfinite, parse_float=_float)
    except (UnicodeError, ValueError) as exc:
        raise PresentationInputError("input must be unambiguous finite UTF-8 JSON") from exc
    _keys(value, {"schema", "records"})
    if value["schema"] != INPUT_SCHEMA:
        raise PresentationInputError("unsupported input schema")
    return _validated(value["records"])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="supplied evidence JSON")
    parser.add_argument("--output", type=Path, help="new report file; omit to write JSON to stdout")
    args = parser.parse_args(argv)
    try:
        if args.output is not None:
            if args.output.resolve() == args.input.resolve():
                raise PresentationInputError("input/output collision")
            if args.output.exists():
                raise PresentationInputError("output already exists")
        report = check_presentations(load_input(args.input))
        serialized = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
        if args.output is None:
            sys.stdout.write(serialized)
        else:
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(serialized)
        return 1 if report["status"] == "CONFLICT_FOUND" else 0
    except (PresentationInputError, OSError) as exc:
        print(f"presentation-integrity: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
