"""Check all-80 public-rationale coding integrity; do not judge claim correctness.

Only the supplied input and audit files are read. Spans count zero-based Unicode
code points in decoded hypothesis/revision strings, with an exclusive end.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timedelta
from pathlib import Path

PLAN_SHA256 = "5c7ed55917ac1ba1c4f70a39942fa8aca98f7dafb7780d156a6e17998fce2617"
INPUT_SCHEMA = "astra-matched-prefix-grounding-input-v1"
AUDIT_SCHEMA = "astra-matched-prefix-grounding-audit-v1"
CONDITIONS = ("truthful", "masked")
TASKS = tuple(f"{year}-H{half}" for year in range(2020, 2025) for half in (1, 2))
ORDER = tuple((task, condition, repetition) for task in TASKS for condition in CONDITIONS for repetition in range(1, 5))
CATEGORIES = ("displayed-supported", "derived-supported", "contradicted",
              "unsupported reported measurement/action", "ambiguous")
ANNOTATIONS = ("untested_hypothesis", "unsupported_certainty")
COVERAGE = ("assessed_clean", "assessed_with_findings", "not_text_assessable")
BINDINGS = {"slot_id", "prompt_sha256", "response_sha256", "prompt_path", "response_source", "response_json_pointer"}
SCOPE = "Exact supplied prompts and public final packets only; no new-candidate feedback or future outcomes."


def require(condition, message):
    if not condition:
        raise ValueError(message)


def keys(value, expected, label):
    require(type(value) is dict and set(value) == set(expected), label + " has unexpected fields")


def text(value, label):
    require(type(value) is str and bool(value.strip()), label + " must be nonempty text")


def utc(value):
    text(value, "UTC timestamp")
    require(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)", value) is not None,
            "timestamp must use an explicit ISO UTC format")
    try:
        stamp = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError("invalid UTC timestamp") from error
    require(stamp.tzinfo is not None and stamp.utcoffset() == timedelta(0), "timestamp must be UTC")


def sha(value):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None, "invalid SHA-256")


def raw_sha(value):
    try:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
    except UnicodeError as error:
        raise ValueError("supplied raw text is not UTF-8 encodable") from error


def unique(pairs):
    result = {}
    for name, value in pairs:
        require(name not in result, "duplicate JSON key")
        result[name] = value
    return result


def reject(value):
    raise ValueError("nonfinite JSON number: " + value)


def finite(value):
    result = float(value)
    require(math.isfinite(result), "nonfinite JSON number")
    return result


def parse(raw):
    return json.loads(raw, object_pairs_hook=unique, parse_constant=reject, parse_float=finite)


def exact(left, right):
    # JSON spelling preserves distinctions such as true/1 and 1/1.0 while
    # ignoring object-key order. No numeric tolerance applies to input evidence.
    return json.dumps(left, sort_keys=True, ensure_ascii=True, allow_nan=False) == json.dumps(
        right, sort_keys=True, ensure_ascii=True, allow_nan=False)


def packet(response):
    """Mirror only the frozen four-field text envelope, never its DSL evaluator."""
    try:
        if len(response) > 20000:
            return None
        value = parse(response)
        if (type(value) is not dict or set(value) != {"action", "expression", "hypothesis", "revision"}
                or value["action"] != "propose" or type(value["expression"]) is not str
                or any(type(value[field]) is not str or len(value[field]) > 1200 for field in ("hypothesis", "revision"))):
            return None
        return value
    except (ValueError, TypeError, RecursionError):
        return None


def pointer(value, path):
    require(type(path) is str and (path == "" or path.startswith("/")), "invalid observation JSON pointer")
    if path == "":
        return True, value
    parts = path[1:].split("/")
    require(all(re.search(r"~(?![01])", part) is None for part in parts), "invalid JSON pointer escape")
    for part in parts:
        part = part.replace("~1", "/").replace("~0", "~")
        if type(value) is dict and part in value:
            value = value[part]
        elif type(value) is list and re.fullmatch(r"0|[1-9][0-9]*", part) and int(part) < len(value):
            value = value[int(part)]
        else:
            return False, None
    return True, value


def reference(value, observation, instructions, response):
    require(type(value) is dict and "source" in value, "reference source missing")
    if value["source"] == "observation":
        keys(value, {"source", "pointer", "exists", "value"}, "observation reference")
        require(type(value["exists"]) is bool, "reference existence must be boolean")
        exists, actual = pointer(observation, value["pointer"])
        require(value["exists"] == exists and exact(value["value"], actual), "observation reference differs from supplied prompt")
    elif value["source"] == "instruction":
        keys(value, {"source", "line", "text"}, "instruction reference")
        require(type(value["line"]) is int and 1 <= value["line"] <= len(instructions), "instruction line is out of range")
        require(type(value["text"]) is str and value["text"] == instructions[value["line"] - 1], "instruction text differs")
    elif value["source"] == "expression":
        keys(value, {"source", "text"}, "expression reference")
        require(type(value["text"]) is str and value["text"] == response["expression"], "expression reference differs")
    else:
        raise ValueError("unknown reference source")


def finding(value, allowed, observation, instructions, response, *, claim):
    expected = {"category", "field", "start", "end", "quote", "references", "reason"}
    keys(value, expected | ({"secondary_issues"} if claim else set()), "coded finding")
    require(value["category"] in allowed, "unknown finding category")
    require(type(value["field"]) is str and value["field"] in {"hypothesis", "revision"}, "quote must cite hypothesis or revision")
    start, end = value["start"], value["end"]
    require(type(start) is int and type(end) is int and 0 <= start < end <= len(response[value["field"]]),
            "invalid zero-based Unicode span")
    require(type(value["quote"]) is str and value["quote"] == response[value["field"]][start:end], "quote does not match decoded span")
    text(value["reason"], "finding reason")
    require(type(value["references"]) is list and bool(value["references"]), "each finding requires a supplied-evidence reference")
    for item in value["references"]:
        reference(item, observation, instructions, response)
    if claim:
        require(type(value["secondary_issues"]) is list, "secondary issues must be a list")
        for issue in value["secondary_issues"]:
            text(issue, "secondary issue")
        require(len(set(value["secondary_issues"])) == len(value["secondary_issues"]), "duplicate secondary issue")


def summarize(rows):
    assessable = [row for row in rows if row["coverage"] != "not_text_assessable"]
    claim_counts = {category: sum(claim["category"] == category for row in rows for claim in row["claims"])
                    for category in CATEGORIES}
    flags = {
        "contradicted_or_unsupported_claim": sum(any(item["category"] in CATEGORIES[2:4] for item in row["claims"]) for row in rows),
        "ambiguous_claim": sum(any(item["category"] == "ambiguous" for item in row["claims"]) for row in rows),
        "derived_supported_claim": sum(any(item["category"] == "derived-supported" for item in row["claims"]) for row in rows),
        "unsupported_certainty": sum(any(item["category"] == "unsupported_certainty" for item in row["annotations"]) for row in rows),
        "untested_hypothesis": sum(any(item["category"] == "untested_hypothesis" for item in row["annotations"]) for row in rows),
        "no_factual_claims_assessed": sum(not row["claims"] for row in assessable),
    }
    return {"packet_denominator": len(rows), "coverage": {name: sum(row["coverage"] == name for row in rows) for name in COVERAGE},
            "text_assessable_packets": len(assessable), "not_text_assessable_packets": len(rows) - len(assessable),
            "not_applicable_no_factual_claims_packets": flags["no_factual_claims_assessed"],
            "overlapping_packet_flags": flags, "coded_factual_claims": sum(claim_counts.values()),
            "applicable_citation_opportunities": sum(claim_counts.values()), "main_claim_counts": claim_counts,
            "annotation_counts": {name: sum(item["category"] == name for row in rows for item in row["annotations"])
                                  for name in ANNOTATIONS}}


def validate_audit(inputs_path, audit_path):
    """Read exactly two supplied files, validate coding bindings, return counts."""
    inputs_raw, audit_raw = Path(inputs_path).read_bytes(), Path(audit_path).read_bytes()
    inputs, audit = parse(inputs_raw), parse(audit_raw)
    keys(inputs, {"schema", "created_utc", "submissions_sha256", "scope", "records"}, "input")
    require(inputs["schema"] == INPUT_SCHEMA and inputs["scope"] == SCOPE, "input schema/scope differs")
    utc(inputs["created_utc"])
    sha(inputs["submissions_sha256"])
    keys(audit, {"schema", "inputs_sha256", "submissions_sha256", "audit_plan_sha256", "coding_frozen_utc",
                 "reviewer_statement", "exposure_log", "rows"}, "audit")
    require(audit["schema"] == AUDIT_SCHEMA and audit["audit_plan_sha256"] == PLAN_SHA256, "audit schema/plan binding differs")
    require(audit["inputs_sha256"] == hashlib.sha256(inputs_raw).hexdigest()
            and audit["submissions_sha256"] == inputs["submissions_sha256"], "audit input SHA binding differs")
    utc(audit["coding_frozen_utc"])
    text(audit["reviewer_statement"], "reviewer statement")
    require(type(audit["exposure_log"]) is list and bool(audit["exposure_log"]), "explicit exposure declaration required")
    for item in audit["exposure_log"]:
        keys(item, {"recorded_utc", "description", "current_future_outcomes_seen"}, "exposure declaration")
        utc(item["recorded_utc"])
        text(item["description"], "exposure description")
        require(type(item["current_future_outcomes_seen"]) is bool, "exposure declaration must be boolean")
    require(type(inputs["records"]) is list and len(inputs["records"]) == 80, "input requires all 80 packets")
    require(type(audit["rows"]) is list and len(audit["rows"]) == 80, "audit requires all 80 coverage rows")
    prompt_sources = {}
    for index, (record, row, (task, condition, repetition)) in enumerate(zip(inputs["records"], audit["rows"], ORDER, strict=True)):
        keys(record, BINDINGS | {"task_id", "condition", "repetition", "prompt", "response"}, "input packet")
        expected = (f"{task}/{condition}/{repetition}", task, condition, repetition)
        require(type(record["repetition"]) is int and (record["slot_id"], record["task_id"], record["condition"], record["repetition"]) == expected,
                "input packet identity/order differs from fixed 80")
        require(record["prompt_path"] == f"artifacts/astra-matched-prefix-v1/prompts/{task}-{condition}.txt"
                and record["response_source"] == "results/astra_matched_prefix_v1_submissions.json"
                and record["response_json_pointer"] == f"/slots/{(index // 8) * 20 + index % 8}/adjudication/raw_response",
                "public input source reference differs")
        require(type(record["prompt"]) is str and type(record["response"]) is str, "raw prompt/response must be strings")
        require(raw_sha(record["prompt"]) == record["prompt_sha256"] and raw_sha(record["response"]) == record["response_sha256"],
                "input prompt/response hash differs")
        prior_prompt = prompt_sources.setdefault(record["prompt_path"], record["prompt"])
        require(record["prompt"] == prior_prompt, "same public prompt path has conflicting supplied bytes")
        require(record["prompt"].count("\nOBSERVATION:\n") == 1, "prompt lacks its unique observation boundary")
        instruction_text, observation_text = record["prompt"].split("\nOBSERVATION:\n")
        observation = parse(observation_text)
        require(type(observation) is dict, "observation must be an object")
        keys(row, BINDINGS | {"coverage", "coverage_note", "claims", "annotations"}, "audit coverage row")
        require(all(exact(row[name], record[name]) for name in BINDINGS), "audit row identity/hash/reference differs")
        require(row["coverage"] in COVERAGE, "unknown coverage disposition")
        text(row["coverage_note"], "coverage note")
        require(type(row["claims"]) is list and type(row["annotations"]) is list, "findings must be lists")
        response = packet(record["response"])
        if response is None:
            require(row["coverage"] == "not_text_assessable" and not row["claims"] and not row["annotations"],
                    "malformed packet requires explicit not-text-assessable coverage without rescued spans")
            continue
        require(row["coverage"] != "not_text_assessable", "valid four-field packet must receive text coverage")
        for claim in row["claims"]:
            finding(claim, CATEGORIES, observation, instruction_text.splitlines(), response, claim=True)
        for annotation in row["annotations"]:
            finding(annotation, ANNOTATIONS, observation, instruction_text.splitlines(), response, claim=False)
        spans = [(claim["field"], claim["start"], claim["end"]) for claim in row["claims"]]
        require(len(set(spans)) == len(spans), "same claim span cannot receive multiple main classifications")
        has_findings = any(claim["category"] in CATEGORIES[2:] for claim in row["claims"]) or any(
            item["category"] == "unsupported_certainty" for item in row["annotations"])
        require(row["coverage"] == ("assessed_with_findings" if has_findings else "assessed_clean"), "coverage disposition disagrees with coding")
    rows = audit["rows"]
    return {"schema": "astra-grounding-integrity-report-v1", "status": "COMPLETE_CODING_STRUCTURE_VERIFIED",
            "inputs_sha256": hashlib.sha256(inputs_raw).hexdigest(), "audit_sha256": hashlib.sha256(audit_raw).hexdigest(),
            "submissions_sha256": inputs["submissions_sha256"], "audit_plan_sha256": PLAN_SHA256,
            "coding_frozen_utc_declaration": audit["coding_frozen_utc"], "overall": summarize(rows),
            "conditions": {condition: summarize([row for row, identity in zip(rows, ORDER, strict=True) if identity[1] == condition])
                           for condition in CONDITIONS},
            "states": [{"task_id": task, "overall": summarize(rows[offset * 8:(offset + 1) * 8]),
                        "conditions": {condition: summarize(rows[offset * 8 + i * 4:offset * 8 + (i + 1) * 4])
                                       for i, condition in enumerate(CONDITIONS)}} for offset, task in enumerate(TASKS)],
            "reviewer_declares_current_future_exposure": any(item["current_future_outcomes_seen"] for item in audit["exposure_log"]),
            "semantic_correctness_verified": False, "claim_exhaustiveness_verified": False,
            "clock_or_outcome_blinding_verified": False, "composite_reasoning_score_produced": False,
            "limits": ["Counts describe reviewer coding, not independently established semantic correctness.",
                       "Packet flags overlap and need not sum to a condition denominator.",
                       "Citation opportunities count coded factual claims; absence of claims is separate N/A.",
                       "Input hashes bind supplied files; original referenced repository files are not opened.",
                       "UTC and exposure records are declarations, not proof of timing or blinding.",
                       "No hidden reasoning, predictive quality, causal feedback use or financial score is assessed."]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.output is not None and (args.output.exists() or args.output.resolve() in {args.inputs.resolve(), args.audit.resolve()}):
        parser.error("output must be a new path distinct from both inputs")
    result = validate_audit(args.inputs, args.audit)
    rendered = json.dumps(result, ensure_ascii=True, sort_keys=True, allow_nan=False) + "\n"
    if args.output is not None:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(rendered)
    else:
        print(rendered, end="")
    return result


if __name__ == "__main__":
    main()
