"""Synthetic exact-byte, namespace and completeness checks; no tokenizers/models."""

import copy
import hashlib
import json
from itertools import permutations

import pytest

from alpha_research_rl.presentation_integrity import (
    INPUT_SCHEMA,
    PresentationInputError,
    check_presentations,
    load_input,
    main,
)

NS_A, NS_B = "a" * 64, "b" * 64


def record(identifier, split="train", prompt="Prompt\n", tokens=None, namespace=NS_A):
    row = {"id": identifier, "split": split, "prompt": prompt}
    if tokens is not None:
        row["tokenization"] = {"namespace_sha256": namespace, "token_ids": tokens}
    return row


def save_input(path, rows):
    path.write_bytes(json.dumps({"schema": INPUT_SCHEMA, "records": rows}, ensure_ascii=True).encode("utf-8"))
    return path


def test_complete_groups_keep_within_split_aliases_and_minimal_cross_split_witnesses():
    rows = [record("z", "test"), record("c"), record("a"), record("d", prompt="Other")]
    before = copy.deepcopy(rows)
    result = check_presentations(rows)
    assert rows == before
    assert result["status"] == "CONFLICT_FOUND"
    assert result["counts"]["records"] == 4
    assert result["counts"]["prompt_groups"] == 2
    assert result["counts"]["prompt_duplicate_groups"] == 1
    assert result["counts"]["prompt_duplicate_excess_records"] == 2
    assert result["counts"]["prompt_cross_split_groups"] == 1
    collision, = result["cross_split_collisions"]
    assert collision == {
        "kind": "prompt_bytes", "namespace_sha256": None,
        "fingerprint": hashlib.sha256(b"Prompt\n").hexdigest(),
        "record_ids": ["a", "c", "z"], "splits": ["test", "train"],
        "witness_record_ids": ["a", "z"],
    }
    retained = check_presentations([record("a"), record("b")])
    assert retained["status"] == "NO_OBSERVED_EXACT_CONFLICT"
    assert retained["counts"]["prompt_duplicate_excess_records"] == 1
    assert retained["token_evidence"]["global_comparison"] == "UNCHECKED"


def test_record_order_does_not_change_report_bytes_or_population_hash():
    rows = [record("c", "test", "tokenizer collapses this", [7, 2]),
            record("a", "train", "and this", [7, 2]),
            record("b", "test", "and this", [7, 2]), record("d", prompt="untokenized")]
    expected = json.dumps(check_presentations(rows), ensure_ascii=True)
    for ordered in permutations(rows):
        assert json.dumps(check_presentations(list(ordered)), ensure_ascii=True) == expected


def test_exact_whitespace_unicode_newlines_and_identifiers_are_not_normalized():
    prompts = ["A\n", "A\r\n", " A\n", "A\n ", "\u00e9", "e\u0301"]
    result = check_presentations([record(str(i), "train" if i % 2 else "test", p)
                                  for i, p in enumerate(prompts)])
    assert result["counts"]["prompt_groups"] == 6
    assert result["cross_split_collisions"] == []
    assert {g["byte_length"] for g in result["prompt_groups"]} == {2, 3}
    spaces = check_presentations([record("a", "train"), record(" a ", " train ")])
    collision, = spaces["cross_split_collisions"]
    assert collision["record_ids"] == [" a ", "a"]
    assert collision["splits"] == [" train ", "train"]


def test_same_namespace_token_collision_can_exist_without_prompt_collision():
    result = check_presentations([record("a", "train", "X", [4, 0]),
                                  record("b", "test", " X", [4, 0])])
    assert result["counts"]["prompt_cross_split_groups"] == 0
    assert result["counts"]["token_cross_split_groups"] == 1
    collision, = result["cross_split_collisions"]
    assert collision["kind"] == "token_ids" and collision["namespace_sha256"] == NS_A
    assert collision["witness_record_ids"] == ["a", "b"]
    assert result["token_evidence"]["coverage"] == "COMPLETE"
    assert result["token_evidence"]["global_comparison"] == "COMPLETE_SINGLE_NAMESPACE"


def test_token_namespaces_are_incomparable_and_cannot_hide_prompt_collisions():
    rows = [record("a", "train", "X", [1], NS_A), record("b", "test", "Y", [1], NS_B)]
    result = check_presentations(rows)
    assert result["cross_split_collisions"] == []
    assert result["counts"]["token_groups"] == 2
    assert result["token_evidence"]["global_comparison"] == "INCOMPARABLE_NAMESPACES"
    rows[1]["prompt"] = "X"
    # Different namespaces may also encode the same prompt differently.
    rows[1]["tokenization"]["token_ids"] = [99, 2]
    changed = check_presentations(rows)
    assert changed["counts"]["prompt_cross_split_groups"] == 1
    assert changed["counts"]["token_cross_split_groups"] == 0


def test_partial_and_dropped_token_evidence_never_claim_complete_check():
    rows = [record("a", "train", "X", [9]), record("b", "test", "Y", [9]),
            record("c", "train", "Z")]
    partial = check_presentations(rows)
    assert partial["status"] == "CONFLICT_FOUND"
    assert partial["counts"]["tokenized_records"] == 2
    assert partial["counts"]["missing_token_records"] == 1
    assert partial["token_evidence"]["coverage"] == "PARTIAL"
    assert partial["token_evidence"]["global_comparison"] == "UNCHECKED"
    assert partial["token_evidence"]["missing_record_ids"] == ["c"]
    assert partial["token_evidence"]["observed_within_namespace_cross_split_groups"] == 1
    stripped = [{k: v for k, v in row.items() if k != "tokenization"} for row in rows]
    absent = check_presentations(stripped)
    assert absent["status"] == "NO_OBSERVED_EXACT_CONFLICT"
    assert absent["token_evidence"]["coverage"] == "ABSENT"
    assert absent["token_evidence"]["global_comparison"] == "UNCHECKED"
    assert absent["population_sha256"] != partial["population_sha256"]


def test_inconsistent_tokens_for_same_prompt_namespace_rejected_even_within_split():
    with pytest.raises(PresentationInputError, match="conflicting token"):
        check_presentations([record("a", tokens=[1]), record("b", tokens=[2])])


def test_report_omits_prompt_and_token_contents_and_does_not_claim_population_completeness():
    result = check_presentations([record("only", prompt="SYNTHETIC_TEXT_NOT_FOR_REPORT", tokens=[876543210])])
    serialized = json.dumps(result)
    assert "SYNTHETIC_TEXT_NOT_FOR_REPORT" not in serialized
    assert "876543210" not in serialized
    assert result["counts"]["records"] == 1
    assert "Only the supplied population" in result["limitations"][0]
    assert "semantic" in result["limitations"][1]
    # The checker cannot detect an omitted row without an independent manifest.
    assert result["status"] == "NO_OBSERVED_EXACT_CONFLICT"


@pytest.mark.parametrize("rows", [
    None, [], {}, [record("a"), record("a")], [{"id": "a", "split": "train"}],
    [record("a") | {"extra": 1}], [record(1)], [record(" ")], [record("a", "\n")],
    [record("a", prompt="\t\r\n")], [record("a", prompt=1.0)],
    [record("a") | {"token_ids": [1]}], [record("a") | {"tokenization": None}],
    [record("a") | {"tokenization": {"namespace_sha256": NS_A}}],
    [record("a") | {"tokenization": {"token_ids": [1]}}],
    [record("a", tokens=[])], [record("a", tokens=[True])], [record("a", tokens=[-1])],
    [record("a", tokens=[1.0])], [record("a", tokens=[float("nan")])],
    [record("a", tokens=[float("inf")])], [record("a", tokens="1")],
    [record("a", tokens=[1], namespace="")], [record("a", tokens=[1], namespace="A" * 64)],
    [record("a", tokens=[1], namespace=True)],
])
def test_malformed_records_and_partial_token_metadata_rejected(rows):
    with pytest.raises(PresentationInputError):
        check_presentations(rows)


@pytest.mark.parametrize("field", ["id", "split", "prompt"])
def test_unencodable_surrogates_are_input_errors(field):
    with pytest.raises(PresentationInputError, match="strict UTF-8"):
        check_presentations([record("a") | {field: "bad\ud800"}])


def test_input_round_trip_preserves_decoded_crlf_and_unicode(tmp_path):
    rows = [record("a", prompt="\u6c49\U0001f600\r\n"), record("b", "test", "\u6c49\U0001f600\n")]
    path = save_input(tmp_path / "in.json", rows)
    assert load_input(path) == rows
    assert check_presentations(load_input(path))["counts"]["prompt_groups"] == 2


@pytest.mark.parametrize("raw", [
    b'{"schema":"actor-visible-presentations-v1","schema":"actor-visible-presentations-v1","records":[]}',
    b'{"schema":"actor-visible-presentations-v1","records":[{"id":"a","id":"b"}]}',
    b'{"schema":"actor-visible-presentations-v1","records":NaN}',
    b'{"schema":"actor-visible-presentations-v1","records":Infinity}',
    b'{"schema":"actor-visible-presentations-v1","records":1e999}', b'\xff', b'{}',
    b'{"schema":"wrong","records":[]}',
])
def test_ambiguous_nonfinite_or_bad_utf8_input_rejected(tmp_path, raw):
    path = tmp_path / "in.json"
    path.write_bytes(raw)
    with pytest.raises(PresentationInputError):
        load_input(path)


def test_cli_writes_conflict_report_and_returns_distinct_exit_code(tmp_path, capsys):
    source = save_input(tmp_path / "in.json", [record("a"), record("b", "test")])
    output = tmp_path / "out.json"
    assert main(["--input", str(source), "--output", str(output)]) == 1
    written = output.read_bytes()
    assert b"\r\n" not in written and written.endswith(b"\n")
    assert json.loads(written)["status"] == "CONFLICT_FOUND"
    assert main(["--input", str(source), "--output", str(output)]) == 2
    assert output.read_bytes() == written
    assert "already exists" in capsys.readouterr().err
    original = source.read_bytes()
    assert main(["--input", str(source), "--output", str(source.parent / "." / source.name)]) == 2
    assert source.read_bytes() == original


def test_cli_no_conflict_stdout_and_malformed_input_never_creates_report(tmp_path, capsys):
    source = save_input(tmp_path / "in.json", [record("a"), record("b", "test", "Different")])
    assert main(["--input", str(source)]) == 0
    assert json.loads(capsys.readouterr().out)["token_evidence"]["global_comparison"] == "UNCHECKED"
    source.write_bytes(b'{"schema":"actor-visible-presentations-v1","records":[]}')
    output = tmp_path / "out.json"
    assert main(["--input", str(source), "--output", str(output)]) == 2
    assert not output.exists()
    assert "presentation-integrity:" in capsys.readouterr().err
