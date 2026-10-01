"""Small artificial confirmation cases only; no canonical bank or generator."""

import copy
import json
from dataclasses import FrozenInstanceError, replace
from fractions import Fraction
from itertools import product

import pytest

import alpha_research_rl.sealed_confirmation as core


def frozen(identifier="fixed", values=(1, -1, 0)):
    return core.freeze_prediction(identifier, values, {"selected_attempt": 1, "mask": 3, "orientation": 1})


def batch(ids=("fixed", "adaptive"), values=(1, -1, 0)):
    result = core.ConfirmationBatch(ids)
    for identifier in ids:
        result.add(frozen(identifier, values))
    return result


@pytest.mark.parametrize("n", range(8))
def test_fair_binomial_tails_match_independent_exhaustive_target_bits(n):
    counts = [sum(bits) for bits in product((0, 1), repeat=n)]
    for k in range(n + 2):
        expected = Fraction(sum(count >= k for count in counts), 2 ** n)
        assert core.binomial_tail(n, k) == expected


def test_biased_tail_matches_independent_two_bit_innovation_enumeration():
    for n in range(5):
        # Three of four equiprobable symbols give a success, independently.
        counts = [sum(symbol != 3 for symbol in symbols) for symbols in product(range(4), repeat=n)]
        for k in range(n + 2):
            expected = Fraction(sum(count >= k for count in counts), 4 ** n)
            assert core.binomial_tail(n, k, Fraction(3, 4)) == expected
    for p, point in ((Fraction(0), 0), (Fraction(1), 4)):
        assert [core.binomial_tail(4, k, p) for k in range(6)] == [Fraction(k <= point) for k in range(6)]


def test_inclusive_integer_threshold_and_nonrejecting_zero_trials():
    assert core.rejection_threshold(4) is None
    assert core.rejection_threshold(5) == 5
    assert core.rejection_threshold(0) is None
    at_boundary = core.confirmation_statistic([1] * 5, [1] * 5, Fraction(1, 32))
    assert at_boundary["reject"] is True
    assert core.confirmation_statistic([1] * 5, [1] * 5, Fraction(1, 33))["reject"] is False
    empty = core.confirmation_statistic([], [])
    assert empty == {"n_predictions": 0, "M": 0, "K": 0, "p_numerator": 1,
                     "p_denominator": 1, "reject": False, "accuracy": None}
    zeros = core.confirmation_statistic([0, 0], [-1, 1])
    assert zeros == empty | {"n_predictions": 2}


def test_abstentions_and_joint_sign_flip_preserve_exact_statistic():
    predictions, targets = [1, -1, 0, 1, -1], [1, 1, -1, 1, -1]
    result = core.confirmation_statistic(predictions, targets)
    assert (result["M"], result["K"]) == (4, 3)
    assert Fraction(result["p_numerator"], result["p_denominator"]) == Fraction(5, 16)
    assert result["accuracy"] == {"numerator": 3, "denominator": 4}
    assert core.confirmation_statistic([-v for v in predictions], [-v for v in targets]) == result
    assert core.confirmation_statistic(predictions, [1, 1, 1, 1, -1]) == result


@pytest.mark.parametrize("args", [
    (True, 0), (-1, 0), (1.0, 0), (2, True), (2, -1), (2, 4),
    (2, 1, .5), (2, 1, True), (2, 1, Fraction(-1, 2)), (2, 1, Fraction(3, 2)),
])
def test_exact_tail_rejects_coercions_and_invalid_boundaries(args):
    with pytest.raises(core.ConfirmationInputError):
        core.binomial_tail(*args)


@pytest.mark.parametrize("predictions,labels", [
    ([True], [1]), ([1.0], [1]), ([2], [1]), ([1], [0]), ([1], [False]),
    ([1], [1.0]), ([float("nan")], [1]), ([1], [float("inf")]), ([1], []), ("1", [1]),
])
def test_bad_vectors_are_errors_not_abstentions(predictions, labels):
    with pytest.raises(core.ConfirmationInputError):
        core.confirmation_statistic(predictions, labels)


@pytest.mark.parametrize("alpha", [0.05, True, Fraction(0), Fraction(1), Fraction(-1), None])
def test_alpha_is_exact_and_strictly_interior(alpha):
    with pytest.raises(core.ConfirmationInputError):
        core.rejection_threshold(3, alpha)
    with pytest.raises(core.ConfirmationInputError):
        core.confirmation_statistic([1], [1], alpha)


def test_freeze_copies_mutable_vectors_and_nested_provenance_and_binds_all_contents():
    values = [1, -1]
    provenance = {"trace": [{"attempt": 1, "alignment": 2}], "orientation": 1}
    prediction = core.freeze_prediction(" a ", values, provenance)
    before = prediction.as_dict()
    values[0] = -1
    provenance["trace"][0]["alignment"] = -999
    exposed = prediction.as_dict()
    exposed["predictions"][0] = 0
    exposed["provenance"]["trace"].clear()
    assert prediction.as_dict() == before and prediction.prediction_id == " a "
    with pytest.raises(FrozenInstanceError):
        prediction.predictions = (0, 0)
    replacement = replace(prediction, predictions=(-1, -1))
    assert replacement.sha256 != prediction.sha256
    assert replace(prediction, prediction_id="different").sha256 != prediction.sha256


@pytest.mark.parametrize("provenance", [
    {}, [], {1: "coerced key"}, {"n": float("inf")}, {"n": float("nan")},
    {"value": (1, 2)}, {"value": "\ud800"},
])
def test_frozen_provenance_rejects_ambiguous_or_nonfinite_values(provenance):
    with pytest.raises(core.ConfirmationInputError):
        core.freeze_prediction("a", [1], provenance)


def test_direct_frozen_constructor_rejects_duplicate_json_keys_mutable_vectors_and_surrogates():
    for args in (("a", (1,), '{"x":1,"x":2}'), ("a", [1], '{"x":1}'),
                 ("\ud800", (1,), '{"x":1}'), (" ", (1,), '{"x":1}')):
        with pytest.raises(core.ConfirmationInputError):
            core.FrozenPrediction(*args)


def test_all_expected_predictions_required_before_seal_and_order_does_not_change_identity():
    first = core.ConfirmationBatch(["fixed", "adaptive"])
    first.add(frozen("adaptive"))
    with pytest.raises(core.ConfirmationProtocolError, match="every expected"):
        first.seal()
    assert first.state == "OPEN" and first.seal_sha256 is None
    first.add(frozen("fixed"))
    second = batch()
    assert first.seal() == second.seal()
    assert first.state == "SEALED"
    for operation in (lambda: first.add(frozen("fixed")), first.seal):
        with pytest.raises(core.ConfirmationProtocolError):
            operation()
    report = first.reveal([1, -1, 1])
    assert report["status"] == "VALID_SEALED_CONFIRMATION"
    assert [row["prediction_id"] for row in report["results"]] == ["fixed", "adaptive"]
    assert all(row["confirmation"]["K"] == 2 and row["naive_diagnostic"] is None for row in report["results"])
    assert first.state == "REVEALED"
    json.dumps(report, allow_nan=False)
    with pytest.raises(core.ConfirmationProtocolError, match="retries"):
        first.reveal([-1, 1, -1])


def test_pre_seal_feedback_taints_entire_batch_and_preserves_only_naive_results():
    owner = batch(values=(1,) * 5)
    owner.record_confirmation_access("fixed", 1)
    owner.record_confirmation_access("fixed", 2)
    owner.seal()
    report = owner.reveal([1] * 5)
    assert report["status"] == "PROTOCOL_INVALID"
    assert len(report["pre_seal_confirmation_accesses"]) == 2
    assert [row["event_index"] for row in report["pre_seal_confirmation_accesses"]] == [1, 2]
    assert all(row["confirmation"] is None and row["naive_diagnostic"]["reject"] for row in report["results"])
    clean = batch(values=(1,) * 5)
    assert clean.seal() != report["seal_sha256"]


@pytest.mark.parametrize("labels", [[1], [1, 0, -1], [True, -1, 1], None])
def test_malformed_reveal_permanently_fails_without_retry(labels):
    owner = batch()
    owner.seal()
    with pytest.raises(core.ConfirmationInputError):
        owner.reveal(labels)
    assert owner.state == "FAILED"
    with pytest.raises(core.ConfirmationProtocolError):
        owner.reveal([1, -1, 1])


def test_early_reveal_and_processing_exception_are_permanent_failures(monkeypatch):
    early = batch()
    with pytest.raises(core.ConfirmationProtocolError):
        early.reveal([1, -1, 1])
    assert early.state == "FAILED"
    with pytest.raises(core.ConfirmationProtocolError):
        early.seal()
    owner = batch()
    owner.seal()
    monkeypatch.setattr(core, "confirmation_statistic", lambda *args: (_ for _ in ()).throw(ArithmeticError("fault")))
    with pytest.raises(ArithmeticError, match="fault"):
        owner.reveal([1, -1, 1])
    assert owner.state == "FAILED"


def test_add_defensive_copy_and_stale_hash_rejection():
    forged = frozen()
    object.__setattr__(forged, "predictions", (-1, -1, 0))
    with pytest.raises(core.ConfirmationInputError, match="hash mismatch"):
        core.ConfirmationBatch(["fixed"]).add(forged)
    original = frozen()
    owner = core.ConfirmationBatch(["fixed"])
    owner.add(original)
    object.__setattr__(original, "predictions", (0, 0, 0))
    owner.seal()
    assert owner.reveal([1, -1, 1])["results"][0]["confirmation"]["M"] == 2


def test_label_intervention_cannot_change_pre_reveal_seal_and_targets_are_not_retained():
    a, b = batch(), batch()
    assert a.seal() == b.seal()
    before = copy.deepcopy(a.__dict__)
    result_a = a.reveal([1, -1, 1])
    result_b = b.reveal([-1, 1, -1])
    assert result_a["seal_sha256"] == result_b["seal_sha256"]
    assert result_a["results"][0]["confirmation"]["K"] == 2
    assert result_b["results"][0]["confirmation"]["K"] == 0
    assert a.__dict__ == before | {"_state": "REVEALED"}


def test_batch_identity_lengths_and_access_metadata_are_strict():
    for ids in ([], ["a", "a"], [" "], [True], "a"):
        with pytest.raises(core.ConfirmationInputError):
            core.ConfirmationBatch(ids)
    owner = core.ConfirmationBatch(["fixed", "adaptive"])
    owner.add(frozen())
    for prediction in (frozen(), frozen("other"), frozen("adaptive", (1,))):
        with pytest.raises(core.ConfirmationInputError):
            owner.add(prediction)
    for identifier, attempt in (("other", 1), ("fixed", True), ("fixed", 0)):
        accessed = batch()
        with pytest.raises(core.ConfirmationInputError):
            accessed.record_confirmation_access(identifier, attempt)
        assert accessed.state == "FAILED"
        with pytest.raises(core.ConfirmationProtocolError):
            accessed.seal()
    owner.add(frozen("adaptive"))
    owner.seal()
    with pytest.raises(core.ConfirmationProtocolError):
        owner.record_confirmation_access("fixed", 1)
    assert owner.state == "FAILED"
