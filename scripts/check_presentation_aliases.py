"""Exhaustive synthetic alias/split regression; never invoke a policy or solver.

This is an engineering fixture, not a training/holdout experiment. The reference
partition is derived from integer matrices, independently of the public checker.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

BASE = ((9, 9, 1, 1), (9, 1, 5, 5), (5, 5, 9, 1))
SPLITS = ("train", "validation", "test")
INSTRUCTIONS = (
    "Choose two distinct diagnostic queries, one at a time, then select one candidate.\n"
    "Only acquired responses may inform later choices. The likelihood table is public.\n"
    "Observation:\n"
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def render_prompt(matrix):
    """A complete fixed initial observation; no transform ID or unrevealed bit."""
    observation = {
        "candidate_ids": ["C0", "C1", "C2", "C3"],
        "prior": {"numerators": [1, 1, 1, 1], "denominator": 4},
        "query_ids": ["Q0", "Q1", "Q2"],
        "response_one_likelihood": {"numerators": matrix, "denominator": 10},
        "response_alphabet": [0, 1], "query_budget": 2,
        "phase": "first_query", "acquired_history": [],
        "legal_query_ids": ["Q0", "Q1", "Q2"],
        "response_assumption": "conditionally independent given hidden candidate",
        "reward_rule": "one if selected candidate is hidden candidate, otherwise zero",
    }
    return INSTRUCTIONS + canonical(observation) + "\n"


def transformations():
    """24 candidate orders x 6 query orders x 8 displayed-response complements."""
    rows = []
    for candidates in itertools.permutations(range(4)):
        for queries in itertools.permutations(range(3)):
            for flips in itertools.product((0, 1), repeat=3):
                matrix = tuple(tuple(10 - BASE[q][c] if flips[i] else BASE[q][c]
                                     for c in candidates) for i, q in enumerate(queries))
                identity = ("p" + "".join(map(str, candidates)) + "-q" + "".join(map(str, queries))
                            + "-b" + "".join(map(str, flips)))
                rows.append({"id": identity, "matrix": matrix, "prompt": render_prompt(matrix)})
    return rows


def prepare_banks():
    """Preserve every raw row; deterministic assignment without random split search."""
    rows = transformations()
    by_matrix, by_prompt = defaultdict(list), defaultdict(list)
    for row in rows:
        by_matrix[row["matrix"]].append(row["id"])
        by_prompt[row["prompt"].encode("utf-8")].append(row["id"])
    if len(rows) != 1152 or len({r["id"] for r in rows}) != 1152:
        raise AssertionError("Incomplete raw transformation enumeration")
    if len(by_matrix) != 144 or set(map(len, by_matrix.values())) != {8}:
        raise AssertionError("Independent matrix partition is not 144 groups of eight")
    matrix_partition = {frozenset(ids) for ids in by_matrix.values()}
    prompt_partition = {frozenset(ids) for ids in by_prompt.values()}
    if matrix_partition != prompt_partition:
        raise AssertionError("Prompt serialization changed the independent matrix partition")
    group_split = {raw: SPLITS[index % len(SPLITS)] for index, raw in enumerate(sorted(by_prompt))}
    naive = [{"id": row["id"], "split": SPLITS[index % len(SPLITS)], "prompt": row["prompt"]}
             for index, row in enumerate(rows)]
    grouped = [{"id": row["id"], "split": group_split[row["prompt"].encode("utf-8")],
                "prompt": row["prompt"]} for row in rows]
    for bank in (naive, grouped):
        if Counter(row["split"] for row in bank) != Counter({name: 384 for name in SPLITS}):
            raise AssertionError("Every declared fixture split must retain 384 rows")
    if [(r["id"], r["prompt"]) for r in naive] != [(r["id"], r["prompt"]) for r in grouped]:
        raise AssertionError("Group assignment lost, changed or reordered a raw alias")
    return rows, naive, grouped


def expected_groups(records):
    """Reference byte equality, using only stdlib and the supplied exhaustive rows."""
    groups = defaultdict(list)
    for row in records:
        groups[row["prompt"].encode("utf-8")].append(row)
    return {raw: {"ids": sorted(r["id"] for r in rows), "splits": sorted({r["split"] for r in rows})}
            for raw, rows in groups.items()}


def move_one_alias(records):
    """Change only the first raw row's split; preserve its seven group aliases."""
    changed = [dict(row) for row in records]
    first = changed[0]
    before = first["split"]
    first["split"] = SPLITS[(SPLITS.index(before) + 1) % len(SPLITS)]
    return changed, {"record_id": first["id"], "original_split": before,
                     "changed_split": first["split"], "expected_cross_split_groups": 1,
                     "expected_equal_cross_split_pairs": 7}


def exact_cross_split_pairs(records):
    """Count unordered byte-equal cross-split pairs without pairwise enumeration."""
    groups = defaultdict(Counter)
    for row in records:
        groups[row["prompt"].encode("utf-8")][row["split"]] += 1
    return sum((sum(counts.values()) ** 2 - sum(n ** 2 for n in counts.values())) // 2
               for counts in groups.values())


def validate_checker_report(records, report):
    """Cross-check public outputs against a separately built exact-byte partition."""
    reference = expected_groups(records)
    conflicts = {sha(raw): value for raw, value in reference.items() if len(value["splits"]) > 1}
    expected_counts = {
        "records": 1152, "splits": 3, "prompt_groups": 144,
        "prompt_duplicate_groups": 144, "prompt_duplicate_excess_records": 1008,
        "prompt_cross_split_groups": len(conflicts), "tokenized_records": 0,
        "missing_token_records": 1152, "token_namespaces": 0, "token_groups": 0,
        "token_cross_split_groups": 0,
    }
    for name, value in expected_counts.items():
        if type(report["counts"].get(name)) is not int or report["counts"][name] != value:
            raise AssertionError("Checker count differs: " + name)
    expected_status = "CONFLICT_FOUND" if conflicts else "NO_OBSERVED_EXACT_CONFLICT"
    if report["status"] != expected_status:
        raise AssertionError("Checker status differs from independent byte equality")
    expected = {sha(raw): {"record_ids": value["ids"], "splits": value["splits"], "byte_length": len(raw)}
                for raw, value in reference.items()}
    if len(expected) != len(reference):
        raise AssertionError("Unexpected fingerprint collision in reference groups")
    observed = {}
    for group in report["prompt_groups"]:
        identity = group["prompt_sha256"]
        if identity in observed:
            raise AssertionError("Repeated checker prompt group")
        observed[identity] = {k: group[k] for k in ("record_ids", "splits", "byte_length")}
    if observed != expected:
        raise AssertionError("Checker partition lost or changed exhaustive row membership")
    collisions = report["cross_split_collisions"]
    if len(collisions) != len(conflicts):
        raise AssertionError("Checker collision population differs")
    covered = set()
    split_by_id = {row["id"]: row["split"] for row in records}
    for collision in collisions:
        fingerprint = collision["fingerprint"]
        if collision["kind"] != "prompt_bytes" or collision["namespace_sha256"] is not None:
            raise AssertionError("Unexpected token claim in a prompt-only fixture")
        if fingerprint in covered or fingerprint not in conflicts:
            raise AssertionError("Repeated or unexplained collision")
        covered.add(fingerprint)
        ref = conflicts[fingerprint]
        if collision["record_ids"] != ref["ids"] or collision["splits"] != ref["splits"]:
            raise AssertionError("Collision membership differs")
        witness = collision["witness_record_ids"]
        if (len(witness) != 2 or any(row_id not in ref["ids"] for row_id in witness)
                or split_by_id[witness[0]] == split_by_id[witness[1]]):
            raise AssertionError("Collision witness does not cross splits")
    evidence = report["token_evidence"]
    if evidence["coverage"] != "ABSENT" or evidence["global_comparison"] != "UNCHECKED":
        raise AssertionError("Missing token evidence must remain UNCHECKED")
    return len(conflicts)


def build_report():
    # The independent construction above does not import the old presentation
    # renderer, solver, tokenizer, model or market modules.
    from alpha_research_rl import presentation_integrity

    rows, naive, grouped = prepare_banks()
    moved, moved_identity = move_one_alias(grouped)
    naive_report = presentation_integrity.check_presentations(naive)
    grouped_report = presentation_integrity.check_presentations(grouped)
    moved_report = presentation_integrity.check_presentations(moved)
    naive_collisions = validate_checker_report(naive, naive_report)
    repaired_collisions = validate_checker_report(grouped, grouped_report)
    moved_collisions = validate_checker_report(moved, moved_report)
    if not naive_collisions or repaired_collisions:
        raise AssertionError("Registered naive/grouped contrast did not reproduce")
    if moved_collisions != 1 or exact_cross_split_pairs(moved) != 7:
        raise AssertionError("Moving one alias must create exactly one group and seven equal cross-split pairs")
    return {
        "schema": "synthetic-presentation-alias-regression-v1", "status": "PASS_ENGINEERING_REGRESSION",
        "scope": "Exhaustive synthetic serialization and split regression; no policy or solver run.",
        "population": {"raw_rows": 1152, "unique_visible_matrices": 144,
                       "unique_initial_prompts": 144, "aliases_per_group": 8,
                       "declared_splits": list(SPLITS), "records_per_split_before_single_alias_fault": 384},
        "construction": {"probability_numerators": BASE, "probability_denominator": 10,
                         "enumeration": "candidate lexicographic permutations; query permutations; displayed bit flips",
                         "naive_assignment": "zero-based raw enumeration index modulo 3",
                         "group_assignment": "zero-based lexicographic exact UTF-8 prompt group index modulo 3",
                         "reference_partition": "exact integer tuple matrices, checked against complete prompt bytes",
                         "all_raw_ids_preserved": True, "all_prompt_bytes_preserved": True},
        "reference_rows_sha256": sha(canonical([
            {"id": r["id"], "matrix": r["matrix"], "prompt_sha256": sha(r["prompt"].encode("utf-8"))}
            for r in rows]).encode("utf-8")),
        "source_sha256": {"scripts/check_presentation_aliases.py": sha(Path(__file__).read_bytes()),
                          "src/alpha_research_rl/presentation_integrity.py":
                              sha(Path(presentation_integrity.__file__).read_bytes())},
        "naive_split": naive_report, "grouped_split": grouped_report,
        "single_moved_alias": {"fault": moved_identity, "checker_report": moved_report},
        "independent_equal_cross_split_pair_counts": {"naive_split": exact_cross_split_pairs(naive),
                                                      "grouped_split": exact_cross_split_pairs(grouped),
                                                      "single_moved_alias": exact_cross_split_pairs(moved)},
        "limits": ["Split names are fixture labels; no model was trained or evaluated.",
                   "Only exact visible prompt bytes were checked; token equality is UNCHECKED.",
                   "No duplicate across splits does not establish semantic disjointness or generalization.",
                   "The 144 presentations relabel one constructed mechanism, not 144 independent mechanisms.",
                   "Exhaustive scope is asserted by this fixture, not inferred by the generic checker."],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New JSON path; existing outputs are refused.")
    args = parser.parse_args(argv)
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError("Output already exists: " + str(args.output))
    report = build_report()
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(report, sort_keys=True, ensure_ascii=True, allow_nan=False, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "raw_rows": 1152, "visible_groups": 144,
                      "naive_cross_split_groups": report["naive_split"]["counts"]["prompt_cross_split_groups"],
                      "grouped_cross_split_groups": 0, "single_moved_alias_cross_split_groups": 1,
                      "token_comparison": "UNCHECKED"}, sort_keys=True))


if __name__ == "__main__":
    main()
