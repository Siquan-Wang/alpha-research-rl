"""Independent combinatorial expectations and wrapper-contract regressions."""

import copy
import importlib.util
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check_presentation_aliases.py"
spec = importlib.util.spec_from_file_location("alias_regression", SCRIPT)
alias = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alias)


def test_every_raw_transformation_and_reference_partition():
    rows = alias.transformations()
    # Separate indexed NumPy-free construction; no checker grouping helper.
    expected = {}
    for c, q, bits in itertools.product(itertools.permutations((0, 1, 2, 3)),
                                      itertools.permutations((0, 1, 2)), itertools.product((0, 1), repeat=3)):
        raw_id = f"p{''.join(map(str, c))}-q{''.join(map(str, q))}-b{''.join(map(str, bits))}"
        table = []
        for i in range(3):
            selected = [((9, 9, 1, 1), (9, 1, 5, 5), (5, 5, 9, 1))[q[i]][j] for j in c]
            table.append(tuple(abs(10 * bits[i] - value) for value in selected))
        expected[raw_id] = tuple(table)
    assert {r["id"]: r["matrix"] for r in rows} == expected
    assert len(rows) == 1152
    assert Counter(Counter(expected.values()).values()) == {8: 144}


def test_initial_observation_contains_only_visible_semantics():
    rows = alias.transformations()
    for row in rows:
        assert row["id"] not in row["prompt"]
        assert row["prompt"].startswith(alias.INSTRUCTIONS) and row["prompt"].endswith("\n")
        obs = json.loads(row["prompt"][len(alias.INSTRUCTIONS):])
        assert set(obs) == {"candidate_ids", "prior", "query_ids", "response_one_likelihood", "response_alphabet",
                            "query_budget", "phase", "acquired_history", "legal_query_ids", "response_assumption",
                            "reward_rule"}
        assert obs["acquired_history"] == [] and obs["phase"] == "first_query"
        assert obs["response_one_likelihood"]["numerators"] == [list(r) for r in row["matrix"]]
        assert not any(x in row["prompt"] for x in ("coarse", "left-pair", "right-pair", "transform_id", "seed"))
    assert len({r["prompt"] for r in rows}) == 144


def test_whole_group_assignment_retains_every_alias_and_nonempty_splits():
    rows, naive, fixed = alias.prepare_banks()
    assert [(r["id"], r["prompt"]) for r in naive] == [(r["id"], r["prompt"]) for r in fixed]
    assert [r["id"] for r in rows] == [r["id"] for r in fixed]
    for bank in (naive, fixed):
        assert Counter(r["split"] for r in bank) == {"train": 384, "validation": 384, "test": 384}
        assert all(set(r) == {"id", "split", "prompt"} for r in bank)
    components = defaultdict(set)
    for row in fixed:
        components[row["prompt"]].add(row["split"])
    assert len(components) == 144 and all(len(s) == 1 for s in components.values())
    naive_components = defaultdict(set)
    for row in naive:
        naive_components[row["prompt"]].add(row["split"])
    assert sum(len(s) > 1 for s in naive_components.values()) > 0


def test_missing_or_aliased_raw_enumeration_fails_closed(monkeypatch):
    complete = alias.transformations()
    monkeypatch.setattr(alias, "transformations", lambda: complete[:-1])
    with pytest.raises(AssertionError, match="Incomplete raw"):
        alias.prepare_banks()
    monkeypatch.setattr(alias, "transformations", lambda: complete[:-1] + [complete[0]])
    with pytest.raises(AssertionError, match="Incomplete raw"):
        alias.prepare_banks()


def test_leaking_ids_in_prompt_breaks_independent_partition(monkeypatch):
    render = alias.render_prompt
    next_id = itertools.count()
    monkeypatch.setattr(alias, "render_prompt", lambda matrix: render(matrix) + f"raw-row-{next(next_id)}")
    with pytest.raises(AssertionError, match="Prompt serialization"):
        alias.prepare_banks()


def test_public_checker_matches_independent_reference():
    report = alias.build_report()
    assert report["status"] == "PASS_ENGINEERING_REGRESSION"
    assert report["population"]["raw_rows"] == 1152
    assert report["naive_split"]["status"] == "CONFLICT_FOUND"
    assert report["grouped_split"]["status"] == "NO_OBSERVED_EXACT_CONFLICT"
    assert report["grouped_split"]["token_evidence"]["global_comparison"] == "UNCHECKED"
    assert report["single_moved_alias"]["checker_report"]["counts"]["prompt_cross_split_groups"] == 1
    assert report["independent_equal_cross_split_pair_counts"]["single_moved_alias"] == 7


def test_published_artifact_matches_complete_deterministic_rebuild():
    artifact = SCRIPT.parents[1] / "results/presentation_alias_regression_v1.json"
    # Missing published evidence is a failure, never an optional CI skip.
    published = json.loads(artifact.read_text(encoding="utf-8"))
    rebuilt = json.loads(json.dumps(alias.build_report(), allow_nan=False))
    # JSON normalizes tuples to lists; canonical strings still distinguish
    # booleans from integer counts and preserve every ordered member/witness.
    assert alias.canonical(published) == alias.canonical(rebuilt)


def test_one_moved_alias_changes_only_one_split_and_seven_cross_split_pairs():
    _, _, clean = alias.prepare_banks()
    moved, fault = alias.move_one_alias(clean)
    assert [(r["id"], r["prompt"]) for r in moved] == [(r["id"], r["prompt"]) for r in clean]
    assert sum(a != b for a, b in zip(clean, moved, strict=True)) == 1
    assert fault["record_id"] == clean[0]["id"]
    counts = Counter(r["split"] for r in moved)
    assert sorted(counts.values()) == [383, 384, 385]
    group = [r for r in moved if r["prompt"] == clean[0]["prompt"]]
    assert sorted(Counter(r["split"] for r in group).values()) == [1, 7]
    assert sum(a["split"] != b["split"] for a, b in itertools.combinations(group, 2)) == 7
    assert alias.exact_cross_split_pairs(clean) == 0
    assert alias.exact_cross_split_pairs(moved) == 7


@pytest.mark.parametrize("mutation", ["dropped_member", "count_bool", "same_split_witness", "token_claim"])
def test_checker_output_cannot_replace_independent_expectations(mutation):
    from alpha_research_rl.presentation_integrity import check_presentations

    _, naive, _ = alias.prepare_banks()
    report = copy.deepcopy(check_presentations(naive))
    if mutation == "dropped_member":
        report["prompt_groups"][0]["record_ids"].pop()
    elif mutation == "count_bool":
        report["counts"]["tokenized_records"] = False
    elif mutation == "same_split_witness":
        collision = report["cross_split_collisions"][0]
        collision["witness_record_ids"] = [collision["record_ids"][0]] * 2
    else:
        report["token_evidence"]["global_comparison"] = "COMPLETE_SINGLE_NAMESPACE"
    with pytest.raises(AssertionError):
        alias.validate_checker_report(naive, report)


def test_existing_output_refused_before_report_build(tmp_path, monkeypatch):
    destination = tmp_path / "existing.json"
    destination.write_bytes(b"original")
    monkeypatch.setattr(alias, "build_report", lambda: pytest.fail("existing destination triggered regression"))
    with pytest.raises(FileExistsError):
        alias.main(["--output", str(destination)])
    assert destination.read_bytes() == b"original"


def test_exclusive_output_survives_race_without_overwrite(tmp_path, monkeypatch):
    destination = tmp_path / "race.json"
    def race():
        destination.write_bytes(b"concurrent original")
        return {"status": "SYNTHETIC"}
    monkeypatch.setattr(alias, "build_report", race)
    with pytest.raises(FileExistsError):
        alias.main(["--output", str(destination)])
    assert destination.read_bytes() == b"concurrent original"
