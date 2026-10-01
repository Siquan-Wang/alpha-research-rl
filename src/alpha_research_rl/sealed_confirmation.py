"""A small one-shot confirmation boundary and exact binomial arithmetic.

This module has no generator, search procedure, RNG, seed, feature library or
target owner. The caller must generate confirmation targets only after sealing
all chosen predictions. Logged confirmation feedback before sealing invalidates
inference; its arithmetic remains a separately labeled naive diagnostic.
This is an ordinary API boundary, not a hostile-Python sandbox or proof that
unlogged accesses, target generation and independence assumptions are correct.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from fractions import Fraction
from functools import lru_cache

DEFAULT_ALPHA = Fraction(1, 20)


class ConfirmationInputError(ValueError):
    """Malformed supplied evidence, never a statistical non-rejection."""


class ConfirmationProtocolError(RuntimeError):
    """An operation violates the staged one-shot protocol."""


def _integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ConfirmationInputError(f"{name} must be an exact integer >= {minimum}")


def _probability(value, *, alpha=False):
    if type(value) is not Fraction or not 0 <= value <= 1 or (alpha and value in (0, 1)):
        raise ConfirmationInputError("probability must be an exact Fraction in the permitted interval")


@lru_cache(maxsize=16)
def _tails(n, numerator, denominator):
    if numerator in (0, denominator):
        successes = n if numerator else 0
        return tuple(Fraction(int(k <= successes)) for k in range(n + 2))
    other = denominator - numerator
    weights = [other ** n]
    for k in range(n):
        product = weights[-1] * (n - k) * numerator
        divisor = (k + 1) * other
        weight, remainder = divmod(product, divisor)
        if remainder:
            raise ArithmeticError("nonintegral binomial weight")
        weights.append(weight)
    cumulative, denominator_power = 0, denominator ** n
    tails = [Fraction(0)] * (n + 2)
    for k in range(n, -1, -1):
        cumulative += weights[k]
        tails[k] = Fraction(cumulative, denominator_power)
    return tuple(tails)


def binomial_tail(n: int, k: int, p: Fraction = Fraction(1, 2)) -> Fraction:
    """Return exact P[Binomial(n,p) >= k], permitting k=0 and k=n+1."""
    _integer(n, "n")
    _integer(k, "k")
    if k > n + 1:
        raise ConfirmationInputError("k must not exceed n+1")
    _probability(p)
    return _tails(n, p.numerator, p.denominator)[k]


def rejection_threshold(n: int, alpha: Fraction = DEFAULT_ALPHA) -> int | None:
    """Smallest rejecting match count for fair targets; None means no rejection.

    n=0 never rejects, irrespective of the supplied (strictly interior) alpha.
    Comparisons are inclusive and use cross-multiplied integers.
    """
    _integer(n, "n")
    _probability(alpha, alpha=True)
    for k in range(1, n + 1):
        tail = binomial_tail(n, k)
        if tail.numerator * alpha.denominator <= alpha.numerator * tail.denominator:
            return k
    return None


def _signs(values, name, *, zeros):
    allowed = (-1, 0, 1) if zeros else (-1, 1)
    if type(values) not in (list, tuple) or any(type(v) is not int or v not in allowed for v in values):
        raise ConfirmationInputError(f"{name} must be a list or tuple of exact permitted integer signs")
    return tuple(values)


def confirmation_statistic(predictions, labels, alpha: Fraction = DEFAULT_ALPHA) -> dict:
    """Compute arithmetic only; this function does not validate independence/access."""
    _probability(alpha, alpha=True)
    predictions = _signs(predictions, "predictions", zeros=True)
    labels = _signs(labels, "labels", zeros=False)
    if len(predictions) != len(labels):
        raise ConfirmationInputError("prediction and label lengths differ")
    m = sum(value != 0 for value in predictions)
    k = sum(value != 0 and value == label for value, label in zip(predictions, labels))
    tail = binomial_tail(m, k)
    return {
        "n_predictions": len(predictions), "M": m, "K": k,
        "p_numerator": tail.numerator, "p_denominator": tail.denominator,
        "reject": bool(m and tail.numerator * alpha.denominator <= alpha.numerator * tail.denominator),
        "accuracy": {"numerator": k, "denominator": m} if m else None,
    }


def _text(value, name):
    if type(value) is not str or not value.strip():
        raise ConfirmationInputError(f"{name} must be a nonblank string")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ConfirmationInputError(f"{name} must encode as strict UTF-8") from exc


def _json_value(value):
    kind = type(value)
    if kind is dict:
        if any(type(key) is not str for key in value):
            raise ConfirmationInputError("provenance object keys must be strings")
        for key, item in value.items():
            _json_value(key)
            _json_value(item)
    elif kind is list:
        for item in value:
            _json_value(item)
    elif kind is str:
        try:
            value.encode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise ConfirmationInputError("provenance must encode as strict UTF-8") from exc
    elif kind is float:
        if not math.isfinite(value):
            raise ConfirmationInputError("nonfinite provenance value")
    elif kind not in (int, bool, type(None)):
        raise ConfirmationInputError("provenance must contain JSON scalar/container types")


def _canonical(value):
    _json_value(value)
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":"))


def _digest(value):
    return hashlib.sha256(_canonical(value).encode("ascii")).hexdigest()


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ConfirmationInputError("duplicate provenance JSON key")
        result[key] = value
    return result


def _provenance(text):
    if type(text) is not str:
        raise ConfirmationInputError("provenance_json must be a string")
    try:
        value = json.loads(text, object_pairs_hook=_object)
    except (ValueError, RecursionError) as exc:
        raise ConfirmationInputError("malformed provenance JSON") from exc
    if type(value) is not dict or not value:
        raise ConfirmationInputError("provenance must be a nonempty object")
    _json_value(value)
    return value


@dataclass(frozen=True)
class FrozenPrediction:
    """Immutable prediction and canonical, copied provenance; no labels."""

    prediction_id: str
    predictions: tuple[int, ...]
    provenance_json: str
    sha256: str = field(init=False)

    def __post_init__(self):
        _text(self.prediction_id, "prediction_id")
        if type(self.predictions) is not tuple:
            raise ConfirmationInputError("FrozenPrediction predictions must be an immutable tuple")
        _signs(self.predictions, "predictions", zeros=True)
        provenance = _provenance(self.provenance_json)
        object.__setattr__(self, "provenance_json", _canonical(provenance))
        object.__setattr__(self, "sha256", _digest({
            "prediction_id": self.prediction_id, "predictions": list(self.predictions),
            "provenance": provenance,
        }))

    def as_dict(self) -> dict:
        """Return fresh mutable containers without exposing owned state."""
        return {"prediction_id": self.prediction_id, "predictions": list(self.predictions),
                "provenance": _provenance(self.provenance_json), "sha256": self.sha256}


def freeze_prediction(prediction_id: str, predictions, provenance: dict) -> FrozenPrediction:
    if type(provenance) is not dict or not provenance:
        raise ConfirmationInputError("provenance must be a nonempty object")
    return FrozenPrediction(prediction_id, _signs(predictions, "predictions", zeros=True), _canonical(provenance))


def _verified_prediction(prediction):
    if type(prediction) is not FrozenPrediction:
        raise ConfirmationInputError("expected a FrozenPrediction")
    copied = FrozenPrediction(prediction.prediction_id, prediction.predictions, prediction.provenance_json)
    if prediction.sha256 != copied.sha256 or prediction.provenance_json != copied.provenance_json:
        raise ConfirmationInputError("frozen prediction content/hash mismatch")
    return copied


class ConfirmationBatch:
    """Accept every expected prediction, seal once, then consume one reveal.

    Access events are caller-recorded evidence, not an interception mechanism.
    A pre-seal confirmation-feedback event taints the entire batch. Predictions
    in an invalid batch receive only naive diagnostic results. Every reveal
    attempt consumes the batch: malformed labels or other failures enter FAILED
    permanently. Target arrays are never retained by this object.
    """

    def __init__(self, expected_prediction_ids, alpha: Fraction = DEFAULT_ALPHA):
        if type(expected_prediction_ids) not in (list, tuple) or not expected_prediction_ids:
            raise ConfirmationInputError("expected_prediction_ids must be a nonempty list or tuple")
        for identifier in expected_prediction_ids:
            _text(identifier, "expected prediction id")
        if len(set(expected_prediction_ids)) != len(expected_prediction_ids):
            raise ConfirmationInputError("duplicate expected prediction id")
        _probability(alpha, alpha=True)
        self._expected = tuple(expected_prediction_ids)
        self._alpha = alpha
        self._predictions = {}
        self._accesses = []
        self._state = "OPEN"
        self._seal = None

    @property
    def state(self):
        return self._state

    @property
    def seal_sha256(self):
        return self._seal

    def add(self, prediction: FrozenPrediction) -> None:
        if self._state != "OPEN":
            raise ConfirmationProtocolError("predictions cannot be added after seal or reveal attempt")
        copied = _verified_prediction(prediction)
        identifier = copied.prediction_id
        if identifier not in self._expected or identifier in self._predictions:
            raise ConfirmationInputError("unexpected or duplicate prediction id")
        if self._predictions and len(copied.predictions) != len(next(iter(self._predictions.values())).predictions):
            raise ConfirmationInputError("all batch predictions must have the same length")
        self._predictions[identifier] = copied

    def record_confirmation_access(self, prediction_id: str, attempt: int) -> None:
        previous = self._state
        # The access may already have occurred. A malformed witness cannot be
        # discarded and followed by apparently valid inference.
        self._state = "FAILED"
        if previous != "OPEN":
            raise ConfirmationProtocolError("confirmation feedback is permitted only as an explicit pre-seal fault")
        _text(prediction_id, "prediction_id")
        _integer(attempt, "attempt", 1)
        if prediction_id not in self._expected:
            raise ConfirmationInputError("unexpected prediction id in access event")
        self._accesses.append({"event_index": len(self._accesses) + 1,
                               "event": "pre_seal_confirmation_feedback", "prediction_id": prediction_id,
                               "attempt": attempt, "stage": previous})
        self._state = "OPEN"

    def _seal_body(self):
        return {"expected_prediction_ids": list(self._expected),
                "alpha": {"numerator": self._alpha.numerator, "denominator": self._alpha.denominator},
                "predictions": [_verified_prediction(self._predictions[key]).as_dict() for key in self._expected],
                "pre_seal_confirmation_accesses": [dict(row) for row in self._accesses]}

    def seal(self) -> str:
        if self._state != "OPEN":
            raise ConfirmationProtocolError("batch can be sealed only once before reveal")
        if set(self._predictions) != set(self._expected):
            raise ConfirmationProtocolError("every expected prediction is required before seal")
        self._seal = _digest(self._seal_body())
        self._state = "SEALED"
        return self._seal

    def reveal(self, labels) -> dict:
        if self._state in {"REVEALED", "FAILED"}:
            raise ConfirmationProtocolError("reveal was already attempted; retries are forbidden")
        previous = self._state
        self._state = "FAILED"
        if previous != "SEALED":
            raise ConfirmationProtocolError("all predictions must be sealed before reveal")
        # FAILED is assigned before any validation/arithmetic, including unexpected exceptions.
        body = self._seal_body()
        if _digest(body) != self._seal:
            raise ConfirmationInputError("sealed batch changed")
        labels = _signs(labels, "labels", zeros=False)
        invalid = bool(self._accesses)
        results = []
        for identifier in self._expected:
            prediction = self._predictions[identifier]
            statistic = confirmation_statistic(prediction.predictions, labels, self._alpha)
            results.append({"prediction_id": identifier, "frozen_prediction_sha256": prediction.sha256,
                            "confirmation": None if invalid else statistic,
                            "naive_diagnostic": statistic if invalid else None})
        report = {"schema": "sealed-confirmation-batch-v1",
                  "status": "PROTOCOL_INVALID" if invalid else "VALID_SEALED_CONFIRMATION",
                  "seal_sha256": self._seal, "expected_prediction_ids": list(self._expected),
                  "alpha": body["alpha"], "pre_seal_confirmation_accesses": body["pre_seal_confirmation_accesses"],
                  "results": results,
                  "scope": "RECORDED_ACCESS_PROTOCOL_ONLY; GENERATION_AND_INDEPENDENCE_NOT_ATTESTED"}
        self._state = "REVEALED"
        return report
