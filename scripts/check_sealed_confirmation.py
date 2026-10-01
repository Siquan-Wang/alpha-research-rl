"""One-run synthetic sealed-confirmation interface validation; no market or model calls."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import re
from collections import Counter
from datetime import UTC, datetime
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

import alpha_research_rl.sealed_confirmation as confirmation_core
from alpha_research_rl.sealed_confirmation import (
    ConfirmationBatch,
    binomial_tail,
    freeze_prediction,
)

STUDY = "sealed-confirmation-v1"
DIRECTORY = "artifacts/sealed-confirmation-v1"
CONTRACT = DIRECTORY + "/contract.json"
EXECUTION = DIRECTORY + "/execution"
RESULT = "results/sealed_confirmation_v1.json"
SOURCE_PATHS = (
    "docs/sealed-confirmation-plan-v1.md",
    "scripts/check_sealed_confirmation.py",
    "src/alpha_research_rl/sealed_confirmation.py",
    "tests/test_sealed_confirmation.py",
    "tests/test_sealed_confirmation_fixture.py",
    "tests/test_sealed_confirmation_review.py",
)
ARMS = ("fixed_correct", "adaptive_correct", "oracle", "fixed_leak", "adaptive_leak", "orientation_only_leak")
PANELS = tuple((law, index) for law, n in (("null", 512), ("planted", 128)) for index in range(n))
N_ROWS = 256
N_FEATURES = 6
ATTEMPTS = 32


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def bytes_sha(raw):
    return hashlib.sha256(raw).hexdigest()


def sealed(body):
    return {**body, "body_sha256": digest(body)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _pairs(pairs):
    result = {}
    for name, value in pairs:
        require(name not in result, "duplicate JSON field")
        result[name] = value
    return result


def parse_json(raw):
    value = json.loads(raw, object_pairs_hook=_pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
    if isinstance(value, dict) and "body_sha256" in value:
        require(value["body_sha256"] == digest({k: v for k, v in value.items() if k != "body_sha256"}),
                "saved body hash differs")
    return value


def read_json(path):
    return parse_json(Path(path).read_bytes())


def now():
    return datetime.now(UTC).isoformat()


def utc(value):
    parsed = datetime.fromisoformat(value)
    require(parsed.tzinfo is not None and parsed.utcoffset() is not None, "timezone is required")
    return parsed


def write_once(path, body):
    with Path(path).open("xb") as stream:
        stream.write((canonical(body) + "\n").encode("ascii"))
        stream.flush()
        os.fsync(stream.fileno())


def safe_path(root, relative):
    require(type(relative) is str and relative and "\\" not in relative, "invalid relative public path")
    path = Path(relative)
    require(not path.is_absolute() and not any(p in {".", ".."} for p in path.parts), "unsafe public path")
    target = root / path
    require(target.resolve().is_relative_to(root.resolve()), "public path escapes root")
    for part in (target, *target.parents):
        if part == root.parent:
            break
        require(not part.is_symlink(), "public evidence cannot be a symlink")
    return target


def rational(value):
    """Lossless representation even for envelope integers beyond JSON digit limits."""
    return {"encoding": "unsigned-base16-rational", "numerator_hex": format(value.numerator, "x"),
            "denominator_hex": format(value.denominator, "x"), "display_decimal": float(value)}


def _integer_weights(n, p):
    # Direct binomial coefficients, separate from the core's recurrence.
    a, b = p.numerator, p.denominator - p.numerator
    return [math.comb(n, k) * a ** k * b ** (n - k) for k in range(n + 1)], p.denominator ** n


def exact_thresholds():
    """Deterministic arithmetic only. Never call a feature/noise generator."""
    fair = [math.comb(256, k) for k in range(257)]
    k_star = next(k for k in range(257) if 20 * sum(fair[k:]) <= 2 ** 256)
    pi0 = Fraction(sum(fair[k_star:]), 2 ** 256)
    pi1 = Fraction(sum(math.comb(256, k) * 3 ** k for k in range(k_star, 257)), 4 ** 256)
    require(pi0 == binomial_tail(256, k_star) and pi1 == binomial_tail(256, k_star, Fraction(3, 4)),
            "independent direct weights differ from core tails")
    weights0, denominator0 = _integer_weights(512, pi0)
    remaining = denominator0
    for upper, weight in enumerate(weights0):
        remaining -= weight
        if 300 * remaining <= denominator0:
            break
    weights1, denominator1 = _integer_weights(128, pi1)
    lower = max(k for k in range(129) if 300 * sum(weights1[:k]) <= denominator1)
    orientation = 2 * pi0
    weights_fault, denominator_fault = _integer_weights(512, orientation)
    return {
        "alpha": {"numerator": 1, "denominator": 20}, "calibration_family_size": 3,
        "family_allowance": {"numerator": 1, "denominator": 100},
        "per_check_allowance": {"numerator": 1, "denominator": 300},
        "M": 256, "K_reject_at_least": k_star, "pi0": rational(pi0), "pi1": rational(pi1),
        "null_panels": 512, "null_upper_inclusive": upper,
        "null_exceedance_at_upper": rational(Fraction(remaining, denominator0)),
        "null_exceedance_at_previous": rational(Fraction(sum(weights0[upper:]), denominator0)),
        "planted_panels": 128, "oracle_lower_inclusive": lower,
        "oracle_single_panel_miss": rational(1 - pi1),
        "oracle_count_below_lower": rational(Fraction(sum(weights1[:lower]), denominator1)),
        "orientation_only_naive_rate": rational(orientation),
        "orientation_only_count_exceeds_upper": rational(Fraction(sum(weights_fault[upper + 1:]), denominator_fault)),
        "selection_fault_detection_lower_bound_uses_same_tail": True,
        "fault_exceedances_are_validation_gates": False,
    }


def feature_bits(namespace, law, index, component, count):
    """Explicit namespace; tests must use a distinct artificial namespace."""
    require(type(namespace) is str and namespace and "|" not in namespace, "invalid stream namespace")
    require(law in {"null", "planted"} and type(index) is int and index >= 0, "invalid stream identity")
    require(component in {"search_features", "confirmation_features", "search_noise", "confirmation_noise"},
            "invalid component")
    label = f"{namespace}|731|{law}|{index:04d}|{component}".encode("ascii")
    raw = hashlib.shake_256(label).digest((count + 7) // 8)
    return [(raw[i // 8] >> (i % 8)) & 1 for i in range(count)]


def generate_inputs(law, index, *, namespace, rows=N_ROWS):
    """Generate pre-seal inputs; return a one-use deferred confirmation owner."""
    def features(component):
        bits = feature_bits(namespace, law, index, component, rows * N_FEATURES)
        return [[2 * bits[i * N_FEATURES + j] - 1 for j in range(N_FEATURES)] for i in range(rows)]

    def labels(x, component):
        bits = feature_bits(namespace, law, index, component, rows if law == "null" else rows * 2)
        if law == "null":
            return [2 * b - 1 for b in bits]
        return [row[0] * row[1] * (-1 if bits[2*i] + 2*bits[2*i+1] == 3 else 1)
                for i, row in enumerate(x)]

    search_x = features("search_features")
    confirmation_x = features("confirmation_features")
    search_y = labels(search_x, "search_noise")
    consumed = False

    def load_confirmation_labels():
        nonlocal consumed
        require(not consumed, "confirmation target materialization already attempted")
        consumed = True
        return labels(confirmation_x, "confirmation_noise")

    return search_x, search_y, confirmation_x, load_confirmation_labels


def _features(values):
    require(type(values) is list and values, "features must be a nonempty row list")
    require(all(type(row) in (list, tuple) and len(row) == 6
                and all(type(x) is int and x in (-1, 1) for x in row) for row in values), "invalid feature rows")
    return tuple(tuple(row) for row in values)


def _labels(values, n):
    require(type(values) in (list, tuple) and len(values) == n
            and all(type(x) is int and x in (-1, 1) for x in values), "invalid target labels")
    return tuple(values)


def predict(mask, orientation, features):
    require(type(mask) is int and 0 <= mask < 64 and type(orientation) is int and orientation in (-1, 1),
            "invalid predictor")
    return tuple(orientation * math.prod(row[j] for j in range(6) if mask & (1 << j)) for row in features)


def search(algorithm, feedback):
    """No seeds, feature/target owner or confirmation batch enters this callable."""
    require(algorithm in {"fixed", "adaptive"}, "unknown search algorithm")
    attempts, seen, incumbent = [], set(), None
    denominator = None
    for r in range(1, ATTEMPTS + 1):
        mask = r - 1 if algorithm == "fixed" else (0 if r == 1 else incumbent["mask"] ^ (1 << ((r - 2) % 6)))
        value = feedback(mask)
        require(type(value) is dict and set(value) == {"alignment", "denominator"}, "malformed feedback")
        a, n = value["alignment"], value["denominator"]
        require(type(a) is int and type(n) is int and n > 0 and abs(a) <= n and (a + n) % 2 == 0,
                "feedback is not an exact sign alignment")
        if denominator is None:
            denominator = n
        require(n == denominator, "feedback denominator changed")
        item = {"attempt": r, "mask": mask, "orientation": 1 if a >= 0 else -1,
                "alignment": a, "denominator": n, "duplicate": mask in seen}
        if incumbent is None or abs(a) > abs(incumbent["alignment"]):
            incumbent = dict(item)
        item["incumbent_attempt"] = incumbent["attempt"]
        attempts.append(item)
        seen.add(mask)
    return {"algorithm": algorithm, "attempts": attempts, "selected": incumbent,
            "attempt_count": len(attempts), "unique_masks": len(seen), "duplicate_attempts": len(attempts) - len(seen)}


def execute_panel(panel_id, law, search_features, search_labels, confirmation_features,
                  load_confirmation_labels, write_event):
    """Small panel helper: handcrafted arrays are permitted; this is not a bank run."""
    require(law in {"null", "planted"}, "unknown panel law")
    sx, cx = _features(search_features), _features(confirmation_features)
    require(len(sx) == len(cx), "search/confirmation row counts differ")
    sy = _labels(search_labels, len(sx))
    write_event("INPUT_OWNER", {"panel_id": panel_id, "law": law, "n_rows": len(sx),
                               "search_features": [list(r) for r in sx], "search_labels": list(sy),
                               "confirmation_features": [list(r) for r in cx]})
    searches, predictions = {}, {}
    good = ConfirmationBatch(list(ARMS[:3]))

    def correct_feedback(mask):
        return {"alignment": sum(a*b for a, b in zip(predict(mask, 1, sx), sy, strict=True)),
                "denominator": len(sy)}

    for arm, algorithm in (("fixed_correct", "fixed"), ("adaptive_correct", "adaptive")):
        found = search(algorithm, correct_feedback)
        searches[arm] = found
        choice = found["selected"]
        predictions[arm] = freeze_prediction(arm, predict(choice["mask"], choice["orientation"], cx),
                                            {"mask": choice["mask"], "orientation": choice["orientation"],
                                             "search_trace_sha256": digest(found), "target_role_used": "search"})
        good.add(predictions[arm])
        write_event("SEARCH_COMPLETED", {"arm": arm, "target_role": "search", "trace": found})
    predictions["oracle"] = freeze_prediction("oracle", predict(3, 1, cx),
                                               {"mask": 3, "orientation": 1, "target_role_used": "none"})
    good.add(predictions["oracle"])
    constant_base = freeze_prediction("constant_positive_base", predict(0, 1, cx),
                                       {"mask": 0, "orientation": 1, "target_role_used": "none"})
    seal_id = good.seal()
    write_event("PREDICTIONS_SEALED", {"batch_seal_sha256": seal_id,
                                      "predictions": [predictions[a].as_dict() for a in ARMS[:3]],
                                      "orientation_fault_base": constant_base.as_dict(),
                                      "correct_search_trace_hashes": {a: digest(v) for a, v in searches.items()}})
    # The durable callback must return before this owner is invoked.
    labels = _labels(load_confirmation_labels(), len(cx))
    write_event("CONFIRMATION_LABELS_MATERIALIZED", {"labels": list(labels), "labels_sha256": digest(list(labels))})
    good_report = good.reveal(labels)
    write_event("CORRECT_REVEAL", good_report)
    outcomes = {}
    for result in good_report["results"]:
        arm = result["prediction_id"]
        outcomes[arm] = {"protocol_status": good_report["status"], "statistic": result["confirmation"],
                         "statistic_role": "confirmation",
                         "frozen_prediction_sha256": result["frozen_prediction_sha256"],
                         "selected": searches[arm]["selected"] if arm in searches else {"mask": 3, "orientation": 1},
                         "attempt_count": 32 if arm in searches else 0,
                         "duplicate_attempts": searches[arm]["duplicate_attempts"] if arm in searches else 0}
    for arm, algorithm in (("fixed_leak", "fixed"), ("adaptive_leak", "adaptive"), ("orientation_only_leak", None)):
        faulty = ConfirmationBatch([arm])
        accesses = []

        def leak_feedback(mask, *, batch=faulty, arm_id=arm, access_log=accesses):
            batch.record_confirmation_access(arm_id, len(access_log) + 1)
            access_log.append(mask)
            return {"alignment": sum(a*b for a, b in zip(predict(mask, 1, cx), labels, strict=True)),
                    "denominator": len(labels)}

        if algorithm is None:
            value = leak_feedback(0)
            selected = {"attempt": 1, "mask": 0, "orientation": 1 if value["alignment"] >= 0 else -1,
                        **value, "duplicate": False}
            trace = {"algorithm": "orientation_only", "attempts": [selected], "selected": selected,
                     "attempt_count": 1, "unique_masks": 1, "duplicate_attempts": 0}
        else:
            trace = search(algorithm, leak_feedback)
            selected = trace["selected"]
        frozen = freeze_prediction(arm, predict(selected["mask"], selected["orientation"], cx),
                                   {"mask": selected["mask"], "orientation": selected["orientation"],
                                    "search_trace_sha256": digest(trace), "target_role_used": "confirmation"})
        faulty.add(frozen)
        fault_seal = faulty.seal()
        write_event("FAULT_SEALED", {"arm": arm, "trace": trace, "frozen_prediction": frozen.as_dict(),
                                     "batch_seal_sha256": fault_seal, "recorded_confirmation_accesses": len(accesses)})
        invalid = faulty.reveal(labels)
        require(invalid["status"] == "PROTOCOL_INVALID", "leaking control obtained a valid confirmation")
        write_event("FAULT_REVEAL", invalid)
        result = invalid["results"][0]
        outcomes[arm] = {"protocol_status": invalid["status"], "statistic": result["naive_diagnostic"],
                         "statistic_role": "naive_diagnostic",
                         "frozen_prediction_sha256": result["frozen_prediction_sha256"], "selected": selected,
                         "attempt_count": trace["attempt_count"], "duplicate_attempts": trace["duplicate_attempts"]}
    for arm in ARMS:
        require(outcomes[arm]["statistic"]["M"] == len(cx), "canonical parity predictions must not abstain")
    if outcomes["orientation_only_leak"]["statistic"]["reject"]:
        require(all(outcomes[a]["statistic"]["reject"] for a in ("fixed_leak", "adaptive_leak")),
                "selection leak failed to retain its constant-sign reference")
    return {"panel_id": panel_id, "law": law, "n_rows": len(cx), "outcomes": outcomes}


@lru_cache(maxsize=1)
def _thresholds_json():
    # Cache only immutable text, never a mutable prepared contract or any panel.
    return canonical(exact_thresholds())


def _source_map(root):
    result = {p: bytes_sha(safe_path(root, p).read_bytes()) for p in SOURCE_PATHS}
    for relative, loaded in (("scripts/check_sealed_confirmation.py", __file__),
                             ("src/alpha_research_rl/sealed_confirmation.py", confirmation_core.__file__)):
        require(bytes_sha(Path(loaded).read_bytes()) == result[relative],
                "loaded runner/core source differs from the bound source root")
    return result


def _contract_body(root):
    return {
        "schema": "sealed-confirmation-contract-v1", "study": STUDY, "status": "PREPARED_NO_PANELS_GENERATED",
        "source_sha256": _source_map(root), "execution_directory": EXECUTION, "result_path": RESULT,
        "panel_order": [{"panel_id": f"{law}-{i:04d}", "law": law, "index": i} for law, i in PANELS],
        "population": {"null_panels": sum(law == "null" for law, _ in PANELS),
                       "planted_panels": sum(law == "planted" for law, _ in PANELS), "total_panels": len(PANELS),
                       "search_rows": N_ROWS, "confirmation_rows": N_ROWS, "features": N_FEATURES},
        "library": {"masks": list(range(64)), "orientations": [-1, 1], "oracle_mask": 3},
        "attempts": {"fixed_correct": 32, "adaptive_correct": 32, "oracle": 0,
                     "fixed_leak": 32, "adaptive_leak": 32, "orientation_only_leak": 1},
        "stream": {"namespace": STUDY, "master_id": 731, "algorithm": "SHAKE256",
                   "components": ["search_features", "confirmation_features", "search_noise", "confirmation_noise"],
                   "bits": "least-significant first; row then feature; sign=2*bit-1"},
        "thresholds": json.loads(_thresholds_json()), "canonical_panel_generations": 0,
        "new_market_scores": 0, "new_model_calls": 0,
    }


def prepare(source_root):
    """Exclusive metadata/threshold preparation; canonical panel generation is absent."""
    root = Path(source_root).resolve()
    directory = safe_path(root, DIRECTORY)
    require(not directory.exists(), "preparation directory already exists; no overwrite")
    contract = sealed(_contract_body(root))
    directory.mkdir(parents=True, exist_ok=False)
    try:
        write_once(directory / "contract.json", contract)
    except BaseException as error:
        write_once(directory / "PREPARE_FAILED.json", sealed({"stage": "prepare", "error_type": type(error).__name__}))
        raise
    return contract


def _verified_contract_bytes(root):
    directory = safe_path(root, DIRECTORY)
    require({p.name for p in directory.iterdir()} <= {"contract.json", "execution"},
            "failed or unexpected preparation namespace member")
    if (directory / "execution").exists() or (directory / "execution").is_symlink():
        require(safe_path(root, EXECUTION).is_dir(), "execution namespace must be a directory")
    path = safe_path(root, CONTRACT)
    raw = path.read_bytes()
    contract = parse_json(raw)
    require(canonical(contract) == canonical(sealed(_contract_body(root))), "contract/source/protocol differs")
    return contract, raw


def _verified_contract(root):
    return _verified_contract_bytes(root)[0]


def publication_files(source_root):
    """Exactly six reviewed source/plan/test files and the prepared contract."""
    root = Path(source_root).resolve()
    contract, raw = _verified_contract_bytes(root)
    return {**contract["source_sha256"], CONTRACT: bytes_sha(raw)}


def _receipt(root, path, expected_files=None):
    raw = Path(path).read_bytes()
    value = parse_json(raw)
    require(type(value) is dict and set(value) == {"schema", "study", "commit", "public_repository_url",
                                                  "verified_utc", "paths_sha256"}, "receipt schema differs")
    require(value["schema"] == "sealed-confirmation-publication-v1" and value["study"] == STUDY,
            "receipt study differs")
    require(type(value["commit"]) is str and re.fullmatch(r"[0-9a-f]{40}", value["commit"]), "invalid commit")
    require(value["public_repository_url"] == "https://github.com/Siquan-Wang/alpha-research-rl", "repository differs")
    require(value["paths_sha256"] == (publication_files(root) if expected_files is None else expected_files),
            "publication file map differs")
    require(utc(value["verified_utc"]) <= utc(now()), "publication receipt is from the future")
    return value, raw


class EventWriter:
    """Durable ordered JSONL with a separate immutable COMPLETED record."""

    def __init__(self, path):
        self.path = Path(path)
        self.stream = self.path.open("xb")
        self.index = 0
        self.previous = None

    def __call__(self, event, body):
        record = sealed({"index": self.index, "previous_body_sha256": self.previous,
                         "event": event, "created_utc": now(), "body": body})
        self.stream.write((canonical(record) + "\n").encode("ascii"))
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.previous = record["body_sha256"]
        self.index += 1
        return record

    def close(self):
        self.stream.close()


def _events_bytes(raw):
    require(raw.endswith(b"\n"), "partial event record")
    records, previous, previous_time = [], None, None
    for index, line in enumerate(raw.splitlines()):
        record = json.loads(line, object_pairs_hook=_pairs)
        require(type(record) is dict and set(record) == {"index", "previous_body_sha256", "event", "created_utc",
                                                       "body", "body_sha256"}, "event fields differ")
        require(type(record["index"]) is int and record["index"] == index
                and record["previous_body_sha256"] == previous, "event order/hash chain differs")
        require(record["body_sha256"] == digest({k: v for k, v in record.items() if k != "body_sha256"}),
                "event body hash differs")
        timestamp = utc(record["created_utc"])
        require(previous_time is None or timestamp >= previous_time, "event chronology reversed")
        records.append(record)
        previous, previous_time = record["body_sha256"], timestamp
    require(records, "empty event ledger")
    return records


def _events(path):
    return _events_bytes(Path(path).read_bytes())


def _panel_counts(row):
    require(set(row["outcomes"]) == set(ARMS), "panel arm membership differs")
    for arm in ARMS:
        outcome = row["outcomes"][arm]
        valid = arm in ARMS[:3]
        require(outcome["protocol_status"] == ("VALID_SEALED_CONFIRMATION" if valid else "PROTOCOL_INVALID"),
                "wrong arm protocol status")
        require(outcome["statistic_role"] == ("confirmation" if valid else "naive_diagnostic"), "wrong statistic role")
        require(type(outcome["statistic"]["reject"]) is bool and outcome["statistic"]["M"] == N_ROWS
                and outcome["statistic"]["n_predictions"] == N_ROWS, "canonical confirmation denominator differs")
        expected = 0 if arm == "oracle" else (1 if arm == "orientation_only_leak" else 32)
        require(type(outcome["attempt_count"]) is int and outcome["attempt_count"] == expected,
                "charged attempt count differs")


def summarize(rows, thresholds):
    require([(r["law"], r["panel_id"]) for r in rows] == [(law, f"{law}-{i:04d}") for law, i in PANELS],
            "complete ordered 512+128 population is required")
    for row in rows:
        require(row["n_rows"] == N_ROWS, "canonical panel row count differs")
        _panel_counts(row)
    by_law = {}
    for law in ("null", "planted"):
        group = [r for r in rows if r["law"] == law]
        by_law[law] = {}
        for arm in ARMS:
            outcomes = [r["outcomes"][arm] for r in group]
            accuracy = Fraction(sum(x["statistic"]["K"] for x in outcomes), len(group) * N_ROWS)
            by_law[law][arm] = {
                "panels": len(group), "rejections": sum(x["statistic"]["reject"] for x in outcomes),
                "protocol_status": outcomes[0]["protocol_status"], "statistic_role": outcomes[0]["statistic_role"],
                "mean_accuracy": float(accuracy), "accuracy_exact": rational(accuracy),
                "mean_signed_score": float(2 * accuracy - 1),
                "selected_mask_counts": dict(sorted(Counter(str(x["selected"]["mask"]) for x in outcomes).items())),
                "orientation_counts": {str(s): sum(x["selected"]["orientation"] == s for x in outcomes) for s in (-1, 1)},
                "charged_attempts": sum(x["attempt_count"] for x in outcomes),
                "duplicate_attempts": sum(x["duplicate_attempts"] for x in outcomes),
            }
    upper, lower = thresholds["null_upper_inclusive"], thresholds["oracle_lower_inclusive"]
    calibration = {
        "fixed_correct_null": {"count": by_law["null"]["fixed_correct"]["rejections"], "n": by_law["null"]["fixed_correct"]["panels"],
                               "comparison": "<=", "threshold": upper},
        "adaptive_correct_null": {"count": by_law["null"]["adaptive_correct"]["rejections"], "n": by_law["null"]["adaptive_correct"]["panels"],
                                  "comparison": "<=", "threshold": upper},
        "oracle_planted": {"count": by_law["planted"]["oracle"]["rejections"], "n": by_law["planted"]["oracle"]["panels"],
                           "comparison": ">=", "threshold": lower},
    }
    for item in calibration.values():
        item["pass"] = item["count"] <= item["threshold"] if item["comparison"] == "<=" else item["count"] >= item["threshold"]
    fault_statistics = {arm: {"null_rejections": by_law["null"][arm]["rejections"], "n": by_law["null"][arm]["panels"],
                              "exceeds_correct_null_upper": by_law["null"][arm]["rejections"] > upper,
                              "protocol_status": "PROTOCOL_INVALID", "used_as_validation_gate": False}
                        for arm in ARMS[3:]}
    return {"panel_count": len(rows), "by_law": by_law, "calibration": calibration,
            "structural_conformance": True, "fault_statistics": fault_statistics,
            "validation_pass": all(item["pass"] for item in calibration.values()),
            "fault_statistical_detection_is_not_gating": True}


def _report(contract, contract_raw, receipt, rows, evidence):
    return sealed({"schema": "sealed-confirmation-result-v1", "study": STUDY,
                   "status": "COMPLETE_INTERFACE_VALIDATION", "contract_sha256": bytes_sha(contract_raw),
                   "publication": receipt, "source_sha256": contract["source_sha256"],
                   "population": contract["population"], "thresholds": contract["thresholds"],
                   "panels": rows, "panel_evidence": evidence, "analysis": summarize(rows, contract["thresholds"]),
                   "execution": {"panel_generations": len(rows), "confirmation_target_materializations": len(rows),
                                 "new_model_calls": 0, "new_market_scores": 0, "automatic_retries": 0},
                   "limits": ["New synthetic interface only; not FinancialTask or real-market inference.",
                              "Ideal independent-bit laws; deterministic streams do not prove independence.",
                              "Recorded API access is not an adversarial sandbox or model attestation.",
                              "Fault p-values are naive diagnostics, never valid confirmation.",
                              "No GenAI, training, alpha, chronological-market or new statistical-theory claim."]})


def run(source_root, publication_receipt_path):
    """The single canonical run. Any existing execution directory forbids a rerun."""
    root = Path(source_root).resolve()
    execution, result_path = safe_path(root, EXECUTION), safe_path(root, RESULT)
    require(not execution.exists() and not result_path.exists(), "canonical execution/result already exists; replay only")
    contract, contract_raw = _verified_contract_bytes(root)
    expected_files = {**contract["source_sha256"], CONTRACT: bytes_sha(contract_raw)}
    receipt, receipt_raw = _receipt(root, publication_receipt_path, expected_files)
    require(safe_path(root, CONTRACT).read_bytes() == contract_raw, "contract changed before execution")
    require(result_path.parent.is_dir(), "result parent directory must exist")
    execution.mkdir(exist_ok=False)
    current_panel, writer = None, None
    try:
        write_once(execution / "STARTED.json", sealed({"study": STUDY, "created_utc": now(),
                   "contract_sha256": bytes_sha(contract_raw), "publication_receipt_sha256": bytes_sha(receipt_raw)}))
        with (execution / "publication-receipt.json").open("xb") as stream:
            stream.write(receipt_raw)
            stream.flush()
            os.fsync(stream.fileno())
        write_once(execution / ".RUNNING", {"study": STUDY})
        parent = execution / "panels"
        parent.mkdir()
        rows, evidence = [], []
        for law, index in PANELS:
            require(_source_map(root) == contract["source_sha256"]
                    and safe_path(root, CONTRACT).read_bytes() == contract_raw,
                    "source or contract changed during canonical execution")
            current_panel = f"{law}-{index:04d}"
            directory = parent / current_panel
            directory.mkdir()
            writer = EventWriter(directory / "events.jsonl")
            writer("STARTED", {"panel_id": current_panel, "law": law, "index": index,
                               "contract_sha256": bytes_sha(contract_raw), "stream_namespace": STUDY})
            inputs = generate_inputs(law, index, namespace=STUDY, rows=N_ROWS)
            require(len(inputs[0]) == len(inputs[1]) == len(inputs[2]) == N_ROWS, "canonical generated rows differ")
            panel = execute_panel(current_panel, law, *inputs, writer)
            _panel_counts(panel)
            ending = writer("COMPLETED", panel)
            writer.close()
            writer = None
            write_once(directory / "COMPLETED.json", sealed({"panel": panel, "last_event_body_sha256": ending["body_sha256"],
                       "events_sha256": bytes_sha((directory / "events.jsonl").read_bytes())}))
            rows.append(panel)
            evidence.append({"panel_id": current_panel,
                             "events_sha256": bytes_sha((directory / "events.jsonl").read_bytes()),
                             "completed_sha256": bytes_sha((directory / "COMPLETED.json").read_bytes())})
        require(_source_map(root) == contract["source_sha256"]
                and safe_path(root, CONTRACT).read_bytes() == contract_raw, "source or contract changed")
        report = _report(contract, contract_raw, receipt, rows, evidence)
        write_once(execution / "COMPLETE.json", report)
        write_once(result_path, report)
        (execution / ".RUNNING").unlink()
        return report
    except BaseException as error:
        if writer is not None:
            writer.close()
        if not (execution / "FAILED.json").exists():
            write_once(execution / "FAILED.json", sealed({"study": STUDY, "created_utc": now(),
                       "panel_id": current_panel, "error_type": type(error).__name__, "rerun_permitted": False}))
        raise


def replay(source_root, report_path=None):
    """Recompute from saved arrays/traces only; never invoke any stream generator."""
    root = Path(source_root).resolve()
    execution = safe_path(root, EXECUTION)
    require(not (execution / "FAILED.json").exists() and not (execution / ".RUNNING").exists(),
            "failed or active canonical execution is not a complete report")
    require({p.name for p in execution.iterdir()} == {"STARTED.json", "publication-receipt.json", "panels", "COMPLETE.json"},
            "completed execution membership differs")
    contract, contract_raw = _verified_contract_bytes(root)
    captured = {safe_path(root, CONTRACT): bytes_sha(contract_raw)}

    def capture(path):
        path = safe_path(root, Path(path).relative_to(root).as_posix())
        raw = path.read_bytes()
        captured[path] = bytes_sha(raw)
        return raw

    receipt_path = safe_path(root, EXECUTION + "/publication-receipt.json")
    receipt, receipt_raw = _receipt(root, receipt_path,
                                    {**contract["source_sha256"], CONTRACT: bytes_sha(contract_raw)})
    captured[execution / "publication-receipt.json"] = bytes_sha(receipt_raw)
    started = parse_json(capture(execution / "STARTED.json"))
    require(type(started) is dict and set(started) == {"study", "created_utc", "contract_sha256",
                                                     "publication_receipt_sha256", "body_sha256"},
            "execution start schema differs")
    require(started["study"] == STUDY and started["contract_sha256"] == bytes_sha(contract_raw)
            and started["publication_receipt_sha256"] == bytes_sha(receipt_raw), "execution start binding differs")
    require(utc(started["created_utc"]) >= utc(receipt["verified_utc"]), "execution preceded publication")
    selected = safe_path(root, RESULT) if report_path is None else Path(report_path).resolve()
    require(selected == safe_path(root, RESULT).resolve(), "replay must use the bound public report")
    report_raw = capture(selected)
    require(report_raw == capture(execution / "COMPLETE.json"), "public and retained reports differ")
    report = parse_json(report_raw)
    panel_parent = execution / "panels"
    require(sorted(p.name for p in panel_parent.iterdir()) == sorted(f"{law}-{i:04d}" for law, i in PANELS),
            "panel population differs")
    rows, evidence = [], []
    previous_time = utc(started["created_utc"])
    for law, index in PANELS:
        panel_id = f"{law}-{index:04d}"
        directory = safe_path(root, EXECUTION + "/panels/" + panel_id)
        require({p.name for p in directory.iterdir()} == {"events.jsonl", "COMPLETED.json"}, "panel membership differs")
        events_raw = capture(directory / "events.jsonl")
        events = _events_bytes(events_raw)
        require(events[0]["event"] == "STARTED" and events[-1]["event"] == "COMPLETED", "panel lifecycle differs")
        require(canonical(events[0]["body"]) == canonical({"panel_id": panel_id, "law": law, "index": index,
                                       "contract_sha256": bytes_sha(contract_raw), "stream_namespace": STUDY}),
                "panel start identity differs")
        require(utc(events[0]["created_utc"]) >= previous_time, "panel chronology reversed")
        previous_time = utc(events[-1]["created_utc"])
        owners = [e["body"] for e in events if e["event"] == "INPUT_OWNER"]
        label_events = [e["body"] for e in events if e["event"] == "CONFIRMATION_LABELS_MATERIALIZED"]
        require(len(owners) == len(label_events) == 1, "owner/target event population differs")
        owner, saved_labels = owners[0], label_events[0]
        require(owner["n_rows"] == N_ROWS and saved_labels["labels_sha256"] == digest(saved_labels["labels"]),
                "saved owner row/target identity differs")
        rebuilt_events = []
        panel = execute_panel(panel_id, law, owner["search_features"], owner["search_labels"],
                              owner["confirmation_features"], lambda saved=saved_labels: copy.deepcopy(saved["labels"]),
                              lambda event, body, sink=rebuilt_events: sink.append((event, copy.deepcopy(body))))
        require(canonical(rebuilt_events) == canonical([(e["event"], e["body"]) for e in events[1:-1]]),
                "saved input/search/seal/reveal evidence differs from recomputation")
        require(canonical(panel) == canonical(events[-1]["body"]), "saved panel outcome differs")
        completion_raw = capture(directory / "COMPLETED.json")
        completion = parse_json(completion_raw)
        expected = sealed({"panel": panel, "last_event_body_sha256": events[-1]["body_sha256"],
                           "events_sha256": bytes_sha(events_raw)})
        require(canonical(completion) == canonical(expected), "completed panel binding differs")
        rows.append(panel)
        evidence.append({"panel_id": panel_id, "events_sha256": expected["events_sha256"],
                         "completed_sha256": bytes_sha(completion_raw)})
    rebuilt = _report(contract, contract_raw, receipt, rows, evidence)
    require(canonical(rebuilt) == canonical(report), "complete saved report differs")
    require(_source_map(root) == contract["source_sha256"]
            and all(bytes_sha(path.read_bytes()) == expected for path, expected in captured.items()),
            "source or saved evidence changed during replay")
    return {"status": "SAVED_SYNTHETIC_CONFIRMATION_VERIFIED", "panels": len(rows),
            "report_sha256": bytes_sha(report_raw), "new_panel_generations": 0,
            "new_model_calls": 0, "new_market_scores": 0, "writes": 0,
            "scope": "Saved-array recomputation; not an independent PRNG or hidden-access attestation."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("prepare")
    commands.add_parser("publication-files")
    execute = commands.add_parser("run")
    execute.add_argument("--publication-receipt", type=Path, required=True)
    commands.add_parser("replay")
    args = parser.parse_args(argv)
    if args.command == "prepare":
        value = prepare(args.root)
        summary = {"status": value["status"], "body_sha256": value["body_sha256"],
                   "K_reject_at_least": value["thresholds"]["K_reject_at_least"],
                   "null_upper": value["thresholds"]["null_upper_inclusive"],
                   "oracle_lower": value["thresholds"]["oracle_lower_inclusive"], "panel_generations": 0}
    elif args.command == "publication-files":
        summary = publication_files(args.root)
    elif args.command == "run":
        value = run(args.root, args.publication_receipt)
        summary = {"status": value["status"], "validation_pass": value["analysis"]["validation_pass"],
                   "calibration": value["analysis"]["calibration"]}
    else:
        summary = replay(args.root)
    print(json.dumps(summary, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
