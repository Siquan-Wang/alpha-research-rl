"""Independent supplied-evidence boundaries; no models, tokenizers or market data."""

import copy
import itertools
import json

import pytest

from alpha_research_rl import presentation_integrity as integrity


def record(identifier, split, prompt, namespace=None, tokens=None):
    result = {"id": identifier, "split": split, "prompt": prompt}
    if namespace is not None:
        result["tokenization"] = {"namespace_sha256": namespace, "token_ids": tokens}
    return result


def direct_partition(rows, kind):
    """Independent all-pairs equality relation, with no production fingerprints."""
    groups = set()
    for left in rows:
        if kind == "token_ids" and "tokenization" not in left:
            continue
        members = []
        for right in rows:
            if kind == "prompt_bytes":
                equal = left["prompt"].encode("utf-8") == right["prompt"].encode("utf-8")
            else:
                equal = (
                    "tokenization" in right
                    and left["tokenization"]["namespace_sha256"]
                    == right["tokenization"]["namespace_sha256"]
                    and left["tokenization"]["token_ids"] == right["tokenization"]["token_ids"]
                )
            if equal:
                members.append(right["id"])
        groups.add(frozenset(members))
    return groups


def test_mixed_evidence_partitions_witnesses_and_permutation_invariance():
    # The byte collision bridges namespaces; a separate token collision shares
    # a namespace despite different bytes. One row has no token evidence.
    rows = [
        record("a", "train", "same", "a" * 64, [1]),
        record("b", "test", "same", "b" * 64, [7]),
        record("c", "train", "different", "b" * 64, [7]),
        record("d", "test", "line\r\nend", "a" * 64, [2]),
        record("e", "test", "line\nend"),
    ]
    original = copy.deepcopy(rows)
    expected = integrity.check_presentations(rows)
    for order in itertools.permutations(rows):
        assert integrity.check_presentations(list(order)) == expected
    assert rows == original
    for key, kind in (("prompt_groups", "prompt_bytes"), ("token_groups", "token_ids")):
        assert {frozenset(group["record_ids"]) for group in expected[key]} == direct_partition(rows, kind)
    assert {(entry["kind"], tuple(entry["record_ids"])) for entry in expected["cross_split_collisions"]} == {
        ("prompt_bytes", ("a", "b")), ("token_ids", ("b", "c")),
    }
    by_id = {row["id"]: row for row in rows}
    for collision in expected["cross_split_collisions"]:
        left, right = (by_id[key] for key in collision["witness_record_ids"])
        assert left["split"] != right["split"]
        assert {left["id"], right["id"]} <= set(collision["record_ids"])
    assert expected["token_evidence"]["coverage"] == "PARTIAL"
    assert expected["token_evidence"]["global_comparison"] == "UNCHECKED"


@pytest.mark.parametrize("left,right", [
    ("a\r\nb", "a\nb"),
    ("\u00e9", "e\u0301"),
    (" action", "action"),
    ("action ", "action"),
    ("A", "a"),
    ("x\x00y", "xy"),
])
def test_literal_utf8_boundary_survives_json_roundtrip(tmp_path, left, right):
    rows = [record("a", "train", left), record("b", "test", right)]
    path = tmp_path / "input.json"
    path.write_bytes(json.dumps({"schema": integrity.INPUT_SCHEMA, "records": rows},
                               ensure_ascii=False).encode("utf-8"))
    loaded = integrity.load_input(path)
    assert loaded == rows
    report = integrity.check_presentations(loaded)
    assert report["counts"]["prompt_groups"] == 2
    assert not report["cross_split_collisions"]
    assert report["token_evidence"]["global_comparison"] == "UNCHECKED"


def test_forced_digest_collision_cannot_merge_unequal_evidence(monkeypatch):
    # Hashes identify evidence in reports; they must not define equality.
    monkeypatch.setattr(integrity, "_sha", lambda _: "0" * 64)
    rows = [record("a", "train", "one", "a" * 64, [1]),
            record("b", "test", "two", "a" * 64, [2])]
    report = integrity.check_presentations(rows)
    assert report["counts"]["prompt_groups"] == 2
    assert report["counts"]["token_groups"] == 2
    assert report["cross_split_collisions"] == []


def test_namespace_difference_is_not_a_global_token_disjointness_claim():
    rows = [record("a", "train", "one", "a" * 64, [1]),
            record("b", "test", "two", "b" * 64, [1])]
    report = integrity.check_presentations(rows)
    assert report["cross_split_collisions"] == []
    assert report["token_evidence"]["coverage"] == "COMPLETE"
    assert report["token_evidence"]["global_comparison"] == "INCOMPARABLE_NAMESPACES"
    rows[1]["prompt"] = "one"
    report = integrity.check_presentations(rows)
    assert report["counts"]["prompt_cross_split_groups"] == 1
    assert report["status"] == "CONFLICT_FOUND"


@pytest.mark.parametrize("second_split", ["train", "test"])
def test_inconsistent_encoding_is_not_silently_reclassified_as_a_clean_pair(second_split):
    rows = [record("a", "train", "same", "a" * 64, [1]),
            record("b", second_split, "same", "a" * 64, [2])]
    with pytest.raises(integrity.PresentationInputError, match="conflicting token sequences"):
        integrity.check_presentations(rows)


def test_single_alias_move_reports_exactly_one_group_and_seven_equal_cross_pairs():
    rows = [record(f"a{index}", "train", "visible-a") for index in range(8)]
    rows.extend(record(f"b{index}", "test", "visible-b") for index in range(8))
    before = integrity.check_presentations(rows)
    assert before["cross_split_collisions"] == []
    changed = copy.deepcopy(rows)
    changed[0]["split"] = "test"
    report = integrity.check_presentations(changed)
    assert report["counts"]["records"] == 16
    assert report["counts"]["prompt_groups"] == 2
    assert report["counts"]["prompt_cross_split_groups"] == 1
    assert report["cross_split_collisions"][0]["record_ids"] == [f"a{index}" for index in range(8)]
    violating_pairs = [(left["id"], right["id"]) for left, right in itertools.combinations(changed, 2)
                       if left["prompt"].encode() == right["prompt"].encode()
                       and left["split"] != right["split"]]
    assert violating_pairs == [("a0", f"a{index}") for index in range(1, 8)]
    changed[0]["split"] = "train"
    assert changed == rows
    assert integrity.check_presentations(changed) == before
