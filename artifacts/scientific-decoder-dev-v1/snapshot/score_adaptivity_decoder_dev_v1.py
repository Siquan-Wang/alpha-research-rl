"""One post-freeze numerical evaluation of the complete four-law decoder bank."""
from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime

from adaptivity_adapter_contract import ContractError, SafeExpression, signed_utility
from newton_scalar_worker_v1 import strict_json
from run_adaptivity_decoder_dev_v1 import COORDS, RUN, digest, read, validate_pair, verify, worker, write_new


def stable_mean(values):
    scale = max(map(abs, values))
    return 0.0 if scale == 0 else (math.fsum(v / scale for v in values) / len(values)) * scale


def score_vector(predictions, truth, invalid_reason=None):
    if invalid_reason == "packet_or_grammar_invalid":
        return {"U": 0.0, "pointwise_mean_U": 0.0, "status": "invalid_candidate",
                "reason": invalid_reason, "relative_squared_error": None,
                "native_magnitude_rmsle": None, "numerical_limits": [],
                "finite_prediction_count": 0, "finite_prediction_fraction": 0.0,
                "zero_target_count": sum(v == 0 for v in truth)}
    primary = signed_utility(predictions, truth)
    secondary = [signed_utility([p], [y]) for p, y in zip(predictions, truth, strict=True)]
    finite_count = sum(s["status"] != "invalid_prediction" for s in secondary)
    if finite_count != len(truth) and invalid_reason is None:
        invalid_reason = "nonfinite_or_domain_prediction"
    rmsle = (math.sqrt(math.fsum((math.log1p(abs(p)) - math.log1p(abs(y))) ** 2
                              for p, y in zip(predictions, truth, strict=True)) / len(truth))
             if finite_count == len(truth) else None)
    return {**primary, "status": "invalid_candidate" if invalid_reason else primary["status"],
            "reason": invalid_reason,
            "pointwise_mean_U": math.fsum(s["U"] for s in secondary) / len(secondary),
            "native_magnitude_rmsle": rmsle,
            "finite_prediction_count": finite_count, "finite_prediction_fraction": finite_count / len(truth),
            "numerical_limits": sorted({s["numerical_limit"] for s in [primary, *secondary]
                                        if s["numerical_limit"]}),
            "zero_target_count": sum(v == 0 for v in truth)}


def main():
    verify()
    if (RUN / "scores.json").exists():
        raise ValueError("score artifact already exists; no re-evaluation")
    frozen_raw = (RUN / "responses-frozen.json").read_bytes()
    frozen_sha = hashlib.sha256(frozen_raw).hexdigest()
    frozen = strict_json(frozen_raw)
    if len(frozen["calls"]) != 16:
        raise ValueError("incomplete response bank")
    expected = {(t, r, c) for t in range(4) for r in range(2) for c in ("prior", "data")}
    observed = {(v["task"], v["repetition"], v["condition"]) for v in frozen["calls"]}
    if expected != observed:
        raise ValueError("response bank identity")
    paired_calls = []
    for index in range(8):
        group = read(RUN / f"pair-{index}.json")
        validate_pair(index, group)
        paired_calls.extend(group["calls"])
    if json.dumps(frozen["calls"], sort_keys=True) != json.dumps(paired_calls, sort_keys=True):
        raise ValueError("frozen calls differ from validated pair evidence")
    training_values = {}
    training_ledger = read(RUN / "training.json")
    if type(training_ledger) is not list or len(training_ledger) != 4:
        raise ValueError("training ledger must contain exactly four tasks")
    for index, item in enumerate(training_ledger):
        if (type(item) is not dict or type(item.get("task")) is not int
                or item["task"] != index or item.get("output") != f"t{index}-train-output.json"):
            raise ValueError("training ledger identity")
        if digest(RUN / item["output"]) != item["sha256"]:
            raise ValueError("training evidence changed")
        output = read(RUN / item["output"])
        records = output.get("records")
        if (output.get("status") != "COMPLETE" or output.get("row_count") != 64
                or output.get("attempted_count") != 64 or type(records) is not list or len(records) != 64
                or any(type(r) is not dict or type(r.get("index")) is not int or r["index"] != j
                       or r.get("status") != "ok" or type(r.get("value")) not in (int, float)
                       or not math.isfinite(r["value"]) for j, r in enumerate(records))):
            raise ValueError("training output must contain 64 ordered finite responses")
        training_values[index] = [r["value"] for r in records]
    response_bytes = {}
    for call in frozen["calls"]:
        if not call["success"]:
            raise ValueError("incomplete response")
        for name in ("response", "result"):
            if digest(RUN / call["directory"] / (name + ".json")) != call[name + "_sha256"]:
                raise ValueError("frozen response bytes changed")
        raw = (RUN / call["directory"] / "response.json").read_bytes()
        if hashlib.sha256(raw).hexdigest() != call["response_sha256"]:
            raise ValueError("response changed during read")
        response_bytes[call["directory"]] = raw
    if any((RUN / f"t{index}-test{suffix}").exists() for index in range(4)
           for suffix in ("-request.json", "-output.json", "-stdout.log", "-stderr.log")):
        raise ValueError("prior confirmation attempt exists; no target re-evaluation")
    tasks = read(COORDS)["tasks"]
    targets = []
    for index in range(4):
        output = worker(index, "test")
        targets.append([r["value"] for r in read(output)["records"]])
    rows = []
    prediction_evaluations = 0
    for call in frozen["calls"]:
        index = call["task"]
        reason, predictions, packet = None, [], None
        try:
            packet = strict_json(response_bytes[call["directory"]])
            if (type(packet) is not dict or set(packet) != {"action", "expression", "hypothesis", "revision"}
                    or any(type(v) is not str for v in packet.values()) or packet["action"] != "propose"):
                raise ValueError("invalid_packet")
            formula = SafeExpression(packet["expression"], [f"x{i}" for i in range(len(tasks[index]["specification"]["variables"]))])
        except (ValueError, TypeError, OverflowError, RecursionError):
            formula, reason = None, "packet_or_grammar_invalid"
        if formula is not None:
            for coordinate in tasks[index]["coordinates"]["test"]["x"]:
                prediction_evaluations += 1
                try:
                    predictions.append(formula.evaluate(coordinate))
                except ContractError:
                    predictions.append(None)
                    reason = "nonfinite_or_domain_prediction"
        rows.append({"task": index, "repetition": call["repetition"], "condition": call["condition"],
                     "expression": packet.get("expression") if type(packet) is dict else None,
                     "predictions": predictions,
                     "score": score_vector(predictions, targets[index], reason)})
    references, by_law = [], []
    for index in range(4):
        mean = stable_mean(training_values[index])
        for name, constant in (("zero", 0.0), ("observed_mean", mean)):
            predictions = [constant] * 256
            references.append({"task": index, "condition": name, "constant": constant,
                               "score": score_vector(predictions, targets[index])})
        means = {c: math.fsum(r["score"]["U"] for r in rows if r["task"] == index and r["condition"] == c) / 2
                 for c in ("prior", "data")}
        means.update({c + "_pointwise": math.fsum(r["score"]["pointwise_mean_U"] for r in rows
                     if r["task"] == index and r["condition"] == c) / 2 for c in ("prior", "data")})
        by_law.append({"task": index, "canonical_law_id": tasks[index]["canonical_law_id"],
                       "domain_id": tasks[index]["domain_id"], **means,
                       "data_minus_prior": means["data"] - means["prior"],
                       "data_minus_prior_pointwise": means["data_pointwise"] - means["prior_pointwise"]})
    means = {c: math.fsum(v[c] for v in by_law) / 4 for c in ("prior", "data")}
    means.update({c: math.fsum(v["score"]["U"] for v in references if v["condition"] == c) / 4
                  for c in ("zero", "observed_mean")})
    means.update({c + "_pointwise": math.fsum(v[c + "_pointwise"] for v in by_law) / 4
                  for c in ("prior", "data")})
    means.update({c + "_pointwise": math.fsum(v["score"]["pointwise_mean_U"] for v in references
                  if v["condition"] == c) / 4 for c in ("zero", "observed_mean")})
    by_domain = []
    for domain in dict.fromkeys(t["domain_id"] for t in tasks):
        members = [v for v in by_law if v["domain_id"] == domain]
        by_domain.append({"domain_id": domain, "laws": len(members), **{
            field: math.fsum(v[field] for v in members) / len(members)
            for field in ("prior", "data", "data_minus_prior", "prior_pointwise", "data_pointwise",
                          "data_minus_prior_pointwise")}})
    gates = {
        "all_candidates_valid": all(r["score"]["status"] != "invalid_candidate" for r in rows),
        "dense_mean_at_least_0_80": means["data"] >= 0.80,
        "dense_minus_prior_at_least_0_15": means["data"] - means["prior"] >= 0.15,
        "dense_minus_zero_at_least_0_10": means["data"] - means["zero"] >= 0.10,
        "dense_minus_observed_mean_at_least_0_10": means["data"] - means["observed_mean"] >= 0.10,
        "positive_on_at_least_three_laws": sum(v["data_minus_prior"] > 0 for v in by_law) >= 3,
        "prior_below_0_90": means["prior"] < 0.90,
    }
    record = {"schema": "adaptivity-decoder-dev-results-v1", "scored_at_utc": datetime.now(UTC).isoformat(),
              "responses_freeze_sha256": frozen_sha,
              "scope": "Development predictive utility, not adaptivity, symbolic equivalence, alpha or weight learning",
              "rows": rows, "references": references, "by_law": by_law, "by_domain": by_domain, "means": means,
              "gates": gates, "all_gates_pass": all(gates.values()),
              "actual_hosted_prediction_evaluations": prediction_evaluations,
              "deterministic_reference_predictions": 2048,
              "confirmation_target_evaluations": 1024, "hosted_calls": 16}
    verify()
    if digest(RUN / "responses-frozen.json") != frozen_sha:
        raise ValueError("frozen bank changed after target generation")
    for call in frozen["calls"]:
        if digest(RUN / call["directory"] / "response.json") != call["response_sha256"]:
            raise ValueError("response changed after target generation")
    write_new(RUN / "scores.json", record)
    print({"means": means, "gates": gates, "result_sha256": digest(RUN / "scores.json")})


if __name__ == "__main__":
    main()
