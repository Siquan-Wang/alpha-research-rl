"""Immutable embedded evidence must not inherit floating-point replay tolerance."""

import copy
import math
import runpy
from pathlib import Path

import pytest


@pytest.fixture
def compare(monkeypatch):
    scripts = Path(__file__).resolve().parents[1] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    return runpy.run_path(str(scripts / "replay_published_astra.py"))["compare_explorer_payload"]


def payload():
    return {"verification": {"elapsed_seconds": 1.0, "count": 1},
            "submissions": {"historical_ic": 0.1}, "assessment": {"future_ic": 0.1},
            "permitted_histories": [{"visible_ic": 0.1}]}


@pytest.mark.parametrize("section", ["submissions", "assessment", "permitted_histories"])
def test_retained_one_ulp_drift_is_rejected(compare, section):
    original = payload()
    changed = copy.deepcopy(original)
    target = changed[section][0] if section == "permitted_histories" else changed[section]
    key = next(iter(target))
    target[key] = math.nextafter(target[key], math.inf)
    with pytest.raises(ValueError, match="exact replay"):
        compare(original, changed)


def test_only_computed_verification_has_float_tolerance(compare):
    original = payload()
    changed = copy.deepcopy(original)
    changed["verification"]["elapsed_seconds"] = math.nextafter(1.0, math.inf)
    compare(original, changed)
    changed["verification"]["count"] = True
    with pytest.raises(ValueError, match="metadata"):
        compare(original, changed)


def test_extra_embedded_section_is_rejected(compare):
    original = payload()
    with pytest.raises(AssertionError, match="fields"):
        compare(original, {**original, "unverified": "data"})
