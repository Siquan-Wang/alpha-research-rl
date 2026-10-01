"""Independent small-state exact arithmetic and boundary review; no canonical bank."""

import copy
import importlib.util
import itertools
import json
from collections import Counter
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest
from test_sealed_confirmation_fixture import complete_artificial
from test_sealed_confirmation_fixture import fake_root as fake_root  # noqa: PLC0414 -- pytest fixture export
from test_sealed_confirmation_fixture import runner as fixture_runner

from alpha_research_rl import sealed_confirmation as confirmation


@pytest.mark.parametrize("success_states", [1, 2, 3])
def test_exact_tails_against_enumerated_four_way_innovations(success_states):
    # Enumerate equiprobable innovations instead of reusing binomial coefficients
    # or the production tail recurrence, including strict upper-tail endpoints.
    for n in range(6):
        counts = Counter(sum(value < success_states for value in draws)
                         for draws in itertools.product(range(4), repeat=n))
        for k in range(n + 2):
            expected = Fraction(sum(count for matches, count in counts.items() if matches >= k), 4**n)
            assert confirmation.binomial_tail(n, k, Fraction(success_states, 4)) == expected


@pytest.mark.parametrize("probability", [Fraction(0), Fraction(1)])
def test_degenerate_binomial_endpoints(probability):
    for n in range(6):
        success_count = n if probability else 0
        for k in range(n + 2):
            assert confirmation.binomial_tail(n, k, probability) == int(k <= success_count)


def test_fitted_sign_null_rejection_rate_is_exactly_twice_fixed_sign():
    for n in range(11):
        labels_bank = tuple(itertools.product((-1, 1), repeat=n))
        fixed_rejects = fitted_rejects = 0
        for labels in labels_bank:
            fixed = confirmation.confirmation_statistic((1,) * n, labels)
            orientation = 1 if sum(labels) >= 0 else -1
            fitted = confirmation.confirmation_statistic((orientation,) * n, labels)
            fixed_rejects += fixed["reject"]
            fitted_rejects += fitted["reject"]
        assert fitted_rejects == 2 * fixed_rejects
        threshold = confirmation.rejection_threshold(n)
        if threshold is None:
            assert fixed_rejects == 0
        else:
            assert threshold > n / 2
            assert confirmation.binomial_tail(n, threshold) == Fraction(fixed_rejects, len(labels_bank))


def test_abstention_conditions_on_frozen_mask_and_retains_original_population():
    counts = Counter()
    for labels in itertools.product((-1, 1), repeat=3):
        result = confirmation.confirmation_statistic([1, 0, -1], labels)
        assert result["n_predictions"] == 3
        assert result["M"] == 2
        counts[result["K"]] += 1
    assert counts == {0: 2, 1: 4, 2: 2}
    all_abstained = confirmation.confirmation_statistic([0, 0], [-1, 1])
    assert (all_abstained["M"], all_abstained["K"], all_abstained["p_numerator"],
            all_abstained["p_denominator"], all_abstained["reject"], all_abstained["accuracy"]) == (
                0, 0, 1, 1, False, None)
    # Abstaining does not make malformed target data silently acceptable.
    with pytest.raises(confirmation.ConfirmationInputError):
        confirmation.confirmation_statistic([0], [0])


def test_threshold_equality_uses_exact_inclusive_comparison():
    assert confirmation.confirmation_statistic([1] * 5, [1] * 5, Fraction(1, 32))["reject"]
    assert not confirmation.confirmation_statistic([1] * 5, [1] * 5, Fraction(1, 33))["reject"]
    assert confirmation.rejection_threshold(5, Fraction(1, 32)) == 5
    assert confirmation.rejection_threshold(5, Fraction(1, 33)) is None


@pytest.mark.parametrize("predictions,labels", [
    ([True], [1]), ([1.0], [1]), ([2], [1]), ([1], [True]),
    ([1], [-1.0]), ([1], [0]), ([1], [2]), ([1, 1], [1]),
])
def test_malformed_signs_or_shape_are_errors_not_nonrejections(predictions, labels):
    with pytest.raises(confirmation.ConfirmationInputError):
        confirmation.confirmation_statistic(predictions, labels)


def prediction(identifier, values):
    return confirmation.freeze_prediction(identifier, values, {"fixture": "independent-review"})


def test_all_required_predictions_and_defensive_copies_precede_reveal():
    values = [1, -1]
    provenance = {"trace": [{"attempt": 1}]}
    first = confirmation.freeze_prediction("fixed", values, provenance)
    batch = confirmation.ConfirmationBatch(["fixed", "adaptive", "oracle"])
    batch.add(first)
    values[0] = -1
    provenance["trace"][0]["attempt"] = 999
    public_copy = first.as_dict()
    public_copy["predictions"][0] = -1
    public_copy["provenance"]["trace"][0]["attempt"] = 888
    assert first.as_dict()["predictions"] == [1, -1]
    assert first.as_dict()["provenance"] == {"trace": [{"attempt": 1}]}
    batch.add(prediction("adaptive", [-1, 1]))
    with pytest.raises(confirmation.ConfirmationProtocolError, match="every expected"):
        batch.seal()
    assert batch.state == "OPEN"
    batch.add(prediction("oracle", [1, 1]))
    seal = batch.seal()
    assert batch.state == "SEALED"
    with pytest.raises(confirmation.ConfirmationProtocolError):
        batch.add(prediction("fixed", [-1, -1]))
    result = batch.reveal([1, -1])
    assert result["seal_sha256"] == seal
    assert result["status"] == "VALID_SEALED_CONFIRMATION"
    assert [row["confirmation"]["K"] for row in result["results"]] == [2, 0, 1]
    assert all(row["naive_diagnostic"] is None for row in result["results"])
    with pytest.raises(confirmation.ConfirmationProtocolError):
        batch.reveal([-1, 1])


def test_replacing_frozen_prediction_rehashes_but_stale_digest_is_rejected():
    original = prediction("fixed", [1, -1])
    changed = replace(original, predictions=(-1, 1))
    assert original.sha256 != changed.sha256
    # This simulates corrupted saved identity, not a promise of hostile-Python isolation.
    object.__setattr__(changed, "sha256", original.sha256)
    batch = confirmation.ConfirmationBatch(["fixed"])
    with pytest.raises(confirmation.ConfirmationInputError, match="content/hash"):
        batch.add(changed)


@pytest.mark.parametrize("seal_before_reveal,labels", [(False, [1]), (True, [0]), (True, [1, -1])])
def test_any_failed_reveal_permanently_consumes_batch(seal_before_reveal, labels):
    batch = confirmation.ConfirmationBatch(["fixed"])
    batch.add(prediction("fixed", [1]))
    if seal_before_reveal:
        batch.seal()
    with pytest.raises((confirmation.ConfirmationInputError, confirmation.ConfirmationProtocolError)):
        batch.reveal(labels)
    assert batch.state == "FAILED"
    with pytest.raises(confirmation.ConfirmationProtocolError, match="retries"):
        batch.reveal([1])


def test_arithmetic_exception_after_partial_internal_results_does_not_return_valid_report(monkeypatch):
    batch = confirmation.ConfirmationBatch(["fixed", "adaptive"])
    for identifier in ("fixed", "adaptive"):
        batch.add(prediction(identifier, [1]))
    batch.seal()
    real_statistic = confirmation.confirmation_statistic
    calls = 0

    def broken_statistic(*args):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise ArithmeticError("injected arithmetic failure")
        return real_statistic(*args)

    monkeypatch.setattr(confirmation, "confirmation_statistic", broken_statistic)
    with pytest.raises(ArithmeticError):
        batch.reveal([1])
    assert batch.state == "FAILED"
    with pytest.raises(confirmation.ConfirmationProtocolError):
        batch.reveal([1])


def test_declared_access_taints_all_results_even_if_naive_test_does_not_reject():
    batch = confirmation.ConfirmationBatch(["fixed", "adaptive"])
    batch.record_confirmation_access("fixed", 1)
    for identifier in ("fixed", "adaptive"):
        batch.add(prediction(identifier, [1]))
    batch.seal()
    report = batch.reveal([-1])
    assert report["status"] == "PROTOCOL_INVALID"
    assert all(row["confirmation"] is None for row in report["results"])
    assert all(row["naive_diagnostic"]["reject"] is False for row in report["results"])


@pytest.mark.parametrize("identifier,attempt", [("misspelled", 1), ("fixed", True), ("fixed", 0)])
def test_malformed_declared_access_cannot_be_erased_by_catching_input_error(identifier, attempt):
    batch = confirmation.ConfirmationBatch(["fixed"])
    with pytest.raises(confirmation.ConfirmationInputError):
        batch.record_confirmation_access(identifier, attempt)
    assert batch.state == "FAILED"
    with pytest.raises(confirmation.ConfirmationProtocolError):
        batch.add(prediction("fixed", [1]))


@pytest.fixture
def runner():
    path = Path(__file__).resolve().parents[1] / "scripts" / "check_sealed_confirmation.py"
    spec = importlib.util.spec_from_file_location("sealed_confirmation_independent_review", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def small_inputs():
    # Eight explicit artificial rows. No canonical SHAKE namespace or bank seed.
    features = [list(bits) + [1, -1, 1] for bits in itertools.product((-1, 1), repeat=3)]
    search_labels = [row[0] * row[1] for row in features]
    confirmation_features = list(reversed(copy.deepcopy(features)))
    return features, search_labels, confirmation_features


def run_small_panel(runner, labels):
    features, search_labels, confirmation_features = small_inputs()
    events = []
    materializations = 0

    def save(event, body):
        events.append((event, copy.deepcopy(body)))

    def reveal():
        nonlocal materializations
        materializations += 1
        assert [event for event, _ in events] == [
            "INPUT_OWNER", "SEARCH_COMPLETED", "SEARCH_COMPLETED", "PREDICTIONS_SEALED",
        ]
        outer_seal = events[-1][1]
        assert [row["prediction_id"] for row in outer_seal["predictions"]] == [
            "fixed_correct", "adaptive_correct", "oracle",
        ]
        assert all(len(row["predictions"]) == 8 for row in outer_seal["predictions"])
        assert outer_seal["orientation_fault_base"]["predictions"] == [1] * 8
        assert outer_seal["predictions"][2]["predictions"] == [
            row[0] * row[1] for row in confirmation_features]
        assert all(len(body["trace"]["attempts"]) == 32 for event, body in events
                   if event == "SEARCH_COMPLETED")
        return list(labels)

    result = runner.execute_panel("artificial-review-only", "null", features, search_labels,
                                  confirmation_features, reveal, save)
    assert materializations == 1
    return result, events


def test_complete_predictions_are_sealed_before_reveal_and_label_changes_preserve_prior_trace(runner):
    _, _, features = small_inputs()
    labels = [row[0] * row[1] for row in features]
    first, first_events = run_small_panel(runner, labels)
    second, second_events = run_small_panel(runner, [-value for value in labels])
    assert first_events[:4] == second_events[:4]
    assert first_events[4][0] == second_events[4][0] == "CONFIRMATION_LABELS_MATERIALIZED"
    assert first_events[4] != second_events[4]
    assert first["outcomes"]["oracle"]["statistic"]["K"] == 8
    assert second["outcomes"]["oracle"]["statistic"]["K"] == 0


def test_fault_controls_keep_all_attempts_and_pointwise_contain_sign_only_rejection(runner):
    result, events = run_small_panel(runner, [1] * 8)
    outcomes = result["outcomes"]
    for arm in ("fixed_leak", "adaptive_leak", "orientation_only_leak"):
        assert outcomes[arm]["protocol_status"] == "PROTOCOL_INVALID"
        assert outcomes[arm]["statistic"]["reject"]
    assert outcomes["orientation_only_leak"]["attempt_count"] == 1
    assert outcomes["orientation_only_leak"]["duplicate_attempts"] == 0
    assert outcomes["fixed_leak"]["attempt_count"] == outcomes["adaptive_leak"]["attempt_count"] == 32
    seals = [body for event, body in events if event == "FAULT_SEALED"]
    for seal in seals:
        trace = seal["trace"]
        masks = [row["mask"] for row in trace["attempts"]]
        assert trace["duplicate_attempts"] == len(masks) - len(set(masks))
        assert seal["recorded_confirmation_accesses"] == len(masks)
    for event, body in events:
        if event == "FAULT_REVEAL":
            assert all(row["confirmation"] is None for row in body["results"])


def test_failed_durable_seal_never_calls_target_owner(runner):
    features, labels, future_features = small_inputs()
    owner_calls = 0

    def write(event, _body):
        if event == "PREDICTIONS_SEALED":
            raise OSError("injected durable seal write failure")

    def owner():
        nonlocal owner_calls
        owner_calls += 1
        return [1] * 8

    with pytest.raises(OSError, match="durable seal"):
        runner.execute_panel("artificial-review-only", "null", features, labels, future_features, owner, write)
    assert owner_calls == 0


def test_failed_target_materialization_cannot_become_a_nonrejecting_outcome(runner):
    features, labels, future_features = small_inputs()
    events = []

    def owner():
        raise ArithmeticError("injected target-owner failure")

    with pytest.raises(ArithmeticError, match="target-owner"):
        runner.execute_panel("artificial-review-only", "null", features, labels, future_features,
                             owner, lambda event, body: events.append(event))
    assert events[-1] == "PREDICTIONS_SEALED"
    assert "CORRECT_REVEAL" not in events


def test_target_owner_has_no_confirmation_noise_until_called_and_failure_consumes_owner(runner, monkeypatch):
    components = []

    def fake_bits(namespace, _law, _index, component, count):
        assert namespace == "independent-review-artificial"
        components.append(component)
        if component == "confirmation_noise":
            raise ArithmeticError("injected innovation failure")
        return [0] * count

    monkeypatch.setattr(runner, "feature_bits", fake_bits)
    _, _, _, owner = runner.generate_inputs("null", 0, namespace="independent-review-artificial", rows=8)
    assert components == ["search_features", "confirmation_features", "search_noise"]
    with pytest.raises(ArithmeticError):
        owner()
    with pytest.raises(ValueError, match="already attempted"):
        owner()
    assert components.count("confirmation_noise") == 1


def prepared_artificial_root(runner, tmp_path, monkeypatch):
    # A metadata-only fixture retaining reviewed module bytes, but no canonical
    # seed stream or outcome. The actual generator is never called by these tests.
    monkeypatch.setattr(runner, "STUDY", "independent-review-artificial")
    bound_sources = ("scripts/check_sealed_confirmation.py", "src/alpha_research_rl/sealed_confirmation.py")
    monkeypatch.setattr(runner, "SOURCE_PATHS", (*bound_sources, "review-only-source.txt"))
    monkeypatch.setattr(runner, "_thresholds_json", lambda: '{"artificial_metadata_only":true}')
    repository = Path(__file__).resolve().parents[1]
    for relative in bound_sources:
        copied = tmp_path / relative
        copied.parent.mkdir(parents=True, exist_ok=True)
        copied.write_bytes((repository / relative).read_bytes())
    (tmp_path / "review-only-source.txt").write_bytes(b"original artificial source")
    (tmp_path / "results").mkdir()
    runner.prepare(tmp_path)
    receipt = {
        "schema": "sealed-confirmation-publication-v1", "study": runner.STUDY,
        "commit": "a" * 40, "public_repository_url": "https://github.com/Siquan-Wang/alpha-research-rl",
        "verified_utc": "2000-01-01T00:00:00+00:00", "paths_sha256": runner.publication_files(tmp_path),
    }
    path = tmp_path / "artificial-receipt.json"
    path.write_bytes(json.dumps(receipt).encode("utf-8"))
    return path, receipt


def test_incomplete_publication_receipt_never_reaches_even_artificial_generation(runner, tmp_path, monkeypatch):
    receipt_path, receipt = prepared_artificial_root(runner, tmp_path, monkeypatch)
    receipt["paths_sha256"].pop("review-only-source.txt")
    receipt_path.write_bytes(json.dumps(receipt).encode("utf-8"))
    calls = []
    monkeypatch.setattr(runner, "generate_inputs", lambda *args, **kwargs: calls.append((args, kwargs)))
    with pytest.raises(ValueError, match="file map"):
        runner.run(tmp_path, receipt_path)
    assert calls == []
    assert not (tmp_path / runner.EXECUTION).exists()


def test_failed_generation_preserves_started_evidence_and_blocks_rerun_and_replay(runner, tmp_path, monkeypatch):
    receipt_path, _ = prepared_artificial_root(runner, tmp_path, monkeypatch)
    calls = 0

    def failed_generator(*_args, **kwargs):
        nonlocal calls
        calls += 1
        assert kwargs["namespace"] == "independent-review-artificial"
        raise ArithmeticError("no panel or labels generated")

    monkeypatch.setattr(runner, "generate_inputs", failed_generator)
    with pytest.raises(ArithmeticError):
        runner.run(tmp_path, receipt_path)
    execution = tmp_path / runner.EXECUTION
    failure = runner.read_json(execution / "FAILED.json")
    assert failure["rerun_permitted"] is False
    assert failure["error_type"] == "ArithmeticError"
    ledger = runner._events(execution / "panels" / "null-0000" / "events.jsonl")
    assert len(ledger) == 1 and ledger[0]["event"] == "STARTED"
    assert not (tmp_path / runner.RESULT).exists()
    with pytest.raises(ValueError, match="replay only"):
        runner.run(tmp_path, receipt_path)
    with pytest.raises(ValueError, match="failed or active"):
        runner.replay(tmp_path)
    assert calls == 1


def test_saved_event_chain_rejects_reordered_time_even_with_resealed_hashes(runner, tmp_path):
    path = tmp_path / "artificial-events.jsonl"
    first = runner.sealed({"index": 0, "previous_body_sha256": None, "event": "PREDICTIONS_SEALED",
                           "created_utc": "2000-01-01T00:00:01+00:00", "body": {"artificial": True}})
    second = runner.sealed({"index": 1, "previous_body_sha256": first["body_sha256"],
                            "event": "CONFIRMATION_LABELS_MATERIALIZED",
                            "created_utc": "2000-01-01T00:00:00+00:00", "body": {"artificial": True}})
    path.write_bytes((runner.canonical(first) + "\n" + runner.canonical(second) + "\n").encode("ascii"))
    with pytest.raises(ValueError, match="chronology"):
        runner._events(path)


@pytest.mark.parametrize("mutation", ["statistic_integer_as_float", "early_label_event"])
def test_complete_artificial_replay_requires_exact_retained_evidence_and_label_order(fake_root, monkeypatch,
                                                                                   mutation):
    complete_artificial(fake_root, monkeypatch)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("saved replay must not generate any synthetic panel")

    monkeypatch.setattr(fixture_runner, "generate_inputs", forbidden)
    monkeypatch.setattr(fixture_runner, "feature_bits", forbidden)
    assert fixture_runner.replay(fake_root)["panels"] == 2
    if mutation == "statistic_integer_as_float":
        report_path = fake_root / fixture_runner.RESULT
        report = fixture_runner.read_json(report_path)
        statistic = report["panels"][0]["outcomes"]["fixed_correct"]["statistic"]
        statistic["K"] = float(statistic["K"])
        report.pop("body_sha256")
        raw = (fixture_runner.canonical(fixture_runner.sealed(report)) + "\n").encode("ascii")
        report_path.write_bytes(raw)
        (fake_root / fixture_runner.EXECUTION / "COMPLETE.json").write_bytes(raw)
        expected_error = "complete saved report differs"
    else:
        ledger = fake_root / fixture_runner.EXECUTION / "panels/null-0091/events.jsonl"
        events = fixture_runner._events(ledger)
        seal_index = next(i for i, event in enumerate(events) if event["event"] == "PREDICTIONS_SEALED")
        label_index = next(i for i, event in enumerate(events)
                           if event["event"] == "CONFIRMATION_LABELS_MATERIALIZED")
        # Preserve event timestamps/order and rebuild every hash, but make the
        # declaration of label availability precede the prediction seal.
        for key in ("event", "body"):
            events[seal_index][key], events[label_index][key] = events[label_index][key], events[seal_index][key]
        previous = None
        rewritten = []
        for event in events:
            event.pop("body_sha256")
            event["previous_body_sha256"] = previous
            event = fixture_runner.sealed(event)
            previous = event["body_sha256"]
            rewritten.append(event)
        ledger.write_bytes(b"".join((fixture_runner.canonical(event) + "\n").encode("ascii")
                                   for event in rewritten))
        expected_error = "recomputation"
    with pytest.raises(ValueError, match=expected_error):
        fixture_runner.replay(fake_root)


def test_saved_evidence_leaf_symlink_is_rejected_when_platform_permits(fake_root, monkeypatch):
    probe = fake_root / "artificial-link-capability"
    try:
        probe.symlink_to(fake_root / "docs/sealed-confirmation-plan-v1.md")
    except OSError as error:
        pytest.skip(f"platform does not permit test symlinks: {error.winerror if hasattr(error, 'winerror') else error}")
    assert probe.resolve().is_relative_to(fake_root.resolve())
    probe.unlink()
    complete_artificial(fake_root, monkeypatch)
    leaf = fake_root / fixture_runner.EXECUTION / "panels/null-0091/COMPLETED.json"
    retained = fake_root / "artificial-retained-completion.json"
    assert leaf.resolve().is_relative_to(fake_root.resolve())
    leaf.rename(retained)
    leaf.symlink_to(retained)
    with pytest.raises(ValueError, match="symlink"):
        fixture_runner.replay(fake_root)
