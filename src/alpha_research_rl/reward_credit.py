"""Saved RLOO reward-credit accounting; no model, gradient or market evaluation."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

STUDY = "financial-rloo-reward-credit-v1"
TOLERANCE = 1e-12
CHANNELS = ("R", "V", "C")
SOURCES = {
    "financial": ("results/financial_training_v1.json",
                  "5cb85943a209183492df813cb63f372f05c9257bba254382957d41183a69cf17"),
    "linkage": ("results/financial_linkage_training_v1.json",
                "e9143fb33680317cc8312410b7b078a849a9d26d7824e7770f29b7230fd3c80d"),
}
IMPLEMENTATION_PATHS = (
    "src/alpha_research_rl/reward_credit.py", "scripts/analyze_reward_credit.py",
    "tests/test_reward_credit.py", "docs/reward-credit-plan-v1.md",
)
TASK_ORDER = {
    23: ("2005-H2", "2008-H1", "2007-H2", "2016-H1", "2012-H1", "2013-H2", "2010-H1", "2009-H2",
         "2004-H1", "2017-H2", "2011-H2", "2015-H2", "2014-H1", "2002-H1", "2003-H2", "2006-H1"),
    29: ("2005-H2", "2002-H1", "2014-H1", "2007-H2", "2013-H2", "2016-H1", "2009-H2", "2012-H1",
         "2008-H1", "2015-H2", "2011-H2", "2010-H1", "2017-H2", "2004-H1", "2006-H1", "2003-H2"),
}
RUNS = (("financial-rloo23-v1", "correct", 23), ("financial-rloo29-v1", "correct", 29),
        ("financial-placebo23-v1", "placebo", 23), ("financial-placebo29-v1", "placebo", 29))
GROUP_KEYS = {"group", "task", "advantages", "preclip_grad_norm", "optimizer_step", "legal_unique_asts",
              "usable_future_ic_range", "quality_exploration", "adapter_before", "adapter_after", "samples"}
SAMPLE_KEYS = {"text", "action", "terminated", "completion_ids", "outcome", "prompt_ids",
               "recomputed_preupdate_completion_logp"}
OUTCOME_KEYS = {"expression", "reward", "cost", "status", "reason", "anchor_reuse", "orientation",
                "feedback", "assessment", "oriented_future_ic", "zero_feedback_tie"}


class RewardCreditError(ValueError):
    """Malformed or inconsistent retained evidence; never an analyzed zero."""


def _require(condition, message):
    if not condition:
        raise RewardCreditError(message)


def _keys(value, keys, where):
    _require(type(value) is dict and set(value) == set(keys), f"{where}: unexpected object keys")


def _number(value, where, low=-math.inf, high=math.inf):
    _require(type(value) in (int, float) and math.isfinite(value) and low <= value <= high,
             f"{where}: finite numeric value required")
    return value


def _integer(value, where, low=0, high=2**63 - 1):
    _require(type(value) is int and low <= value <= high, f"{where}: integer required")
    return value


def _boolean(value, where):
    _require(type(value) is bool, f"{where}: boolean required")
    return value


def _text(value, where):
    _require(type(value) is str and bool(value.strip()), f"{where}: nonempty string required")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise RewardCreditError(f"{where}: invalid Unicode") from exc
    return value


def _sha(value, where):
    _require(type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value),
             f"{where}: SHA-256 required")
    return value


def _json_value(value):
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        _number(value, "JSON number")
    elif type(value) is str:
        try:
            value.encode("utf-8")
        except UnicodeError as exc:
            raise RewardCreditError("Invalid Unicode in evidence") from exc
    elif type(value) is list:
        for item in value:
            _json_value(item)
    elif type(value) is dict and all(type(key) is str for key in value):
        for key, item in value.items():
            _json_value(key)
            _json_value(item)
    else:
        raise RewardCreditError("Evidence must contain only finite JSON values")


def _exact(left, right, where):
    _require(type(left) is type(right) and json.dumps(left, sort_keys=True, allow_nan=False)
             == json.dumps(right, sort_keys=True, allow_nan=False), f"{where}: exact metadata mismatch")


def _close(left, right, where):
    _number(left, where)
    _number(right, where)
    _require(math.isclose(left, right, rel_tol=TOLERANCE, abs_tol=TOLERANCE), f"{where}: arithmetic mismatch")


def _vector(value, where):
    _require(type(value) is list and len(value) == 4, f"{where}: exactly four values required")
    return [_number(x, where) for x in value]


def loo(values):
    """Centered four-sample LOO: constants are exactly zero; no whitening."""
    values = _vector(values, "LOO values")
    centered = [value - values[0] for value in values]
    total = math.fsum(centered)
    return [value - (total - value) / 3 for value in centered]


def _metric(metric, where):
    if metric is None:
        return
    _keys(metric, {"mean_ic", "coverage", "ic_std", "n_dates", "n_signal_dates"}, where)
    length = _integer(metric["n_signal_dates"], where, 1)
    count = _integer(metric["n_dates"], where, 0, length)
    _number(metric["coverage"], where, 0, 1)
    for field, low, high in (("mean_ic", -1, 1), ("ic_std", 0, math.inf)):
        if count == 0:
            _require(metric[field] is None, f"{where}: empty support must have null moments")
        else:
            _number(metric[field], where, low, high)


def _sample(sample, index):
    _keys(sample, SAMPLE_KEYS, "sample")
    _require(type(sample["text"]) is str, "Sample text must be a string")
    _boolean(sample["terminated"], "termination")
    for field in ("prompt_ids", "completion_ids"):
        _require(type(sample[field]) is list and bool(sample[field]), f"{field}: nonempty list required")
        for token in sample[field]:
            _integer(token, field)
    logp = _number(sample["recomputed_preupdate_completion_logp"], "completion logp", high=0)
    outcome = sample["outcome"]
    _keys(outcome, OUTCOME_KEYS, "outcome")
    _exact(outcome["cost"], 0.01, "proposal cost")
    for field in ("anchor_reuse", "zero_feedback_tie"):
        _boolean(outcome[field], field)
    _require(outcome["expression"] is None or type(outcome["expression"]) is str, "Expression type")
    _require(outcome["status"] in ("ok", "invalid", "unscorable"), "Unknown outcome status")
    for field in ("feedback", "assessment"):
        _metric(outcome[field], field)
    orientation = outcome["orientation"]
    _require(orientation is None or type(orientation) is int and orientation in (-1, 1), "Orientation type")
    valid = int(outcome["status"] == "ok")
    if valid:
        _require(outcome["reason"] is None and orientation is not None, "Successful outcome metadata")
        _require(sample["terminated"] is True, "Successful outcome must be terminated")
        _keys(sample["action"], {"action", "expression"}, "successful action")
        _exact(sample["action"], {"action": "propose", "expression": outcome["expression"]}, "action/outcome")
        _text(outcome["expression"], "successful expression")
        credit = _number(outcome["oriented_future_ic"], "successful IC", -1, 1)
        _require(outcome["feedback"] is not None and outcome["assessment"] is not None, "Missing metrics")
        _number(outcome["feedback"]["mean_ic"], "feedback IC", -1, 1)
        _number(outcome["assessment"]["mean_ic"], "assessment IC", -1, 1)
        _exact(orientation, -1 if outcome["feedback"]["mean_ic"] < 0 else 1, "fixed orientation")
        _exact(outcome["zero_feedback_tie"], outcome["feedback"]["mean_ic"] == 0, "feedback tie")
        _close(credit, orientation * outcome["assessment"]["mean_ic"], "oriented IC")
        expected_reward = credit - 0.01
    else:
        allowed = {"invalid": {"invalid_expression", "invalid_json_action", "nonterminated_completion"},
                   "unscorable": {"insufficient_feedback_support", "insufficient_assessment_support"}}
        _require(outcome["reason"] in allowed[outcome["status"]], "Failure reason/status mismatch")
        _require(outcome["oriented_future_ic"] is None, "Failed outcome must not carry IC")
        credit, expected_reward = 0.0, -1.01
    reward = _number(outcome["reward"], "reward", -1.01, 0.99)
    _close(reward, expected_reward, "outcome reward")
    return {"sample": index, "status": outcome["status"], "reason": outcome["reason"],
            "expression": outcome["expression"], "completion_tokens": len(sample["completion_ids"]),
            "preupdate_logp": logp,
            "reward_identity_residual": abs(reward - (-1.01 + valid + credit)),
            "oriented_ic_residual": abs(credit - orientation * outcome["assessment"]["mean_ic"])
            if valid else None}, (reward, valid, credit)


def _group(group, index, task, placebo):
    extras = {"observation", "true_rewards", "permutation", "assigned_rewards"} if placebo else {"rewards"}
    _keys(group, GROUP_KEYS | extras, "group")
    _exact(group["group"], index, "group order")
    _exact(group["task"], task, "task order/identity")
    _require(type(group["samples"]) is list and len(group["samples"]) == 4, "Four samples per group required")
    records, components = zip(*(_sample(sample, i) for i, sample in enumerate(group["samples"])))
    true = {channel: [row[i] for row in components] for i, channel in enumerate(CHANNELS)}
    recorded_rewards = _vector(group["true_rewards" if placebo else "rewards"], "group rewards")
    for actual, expected in zip(recorded_rewards, true["R"]):
        _require(actual == expected, "sample/group rewards: copied numeric evidence differs")
    permutation = group["permutation"] if placebo else [0, 1, 2, 3]
    _require(type(permutation) is list and len(permutation) == 4 and
             all(type(i) is int for i in permutation) and sorted(permutation) == [0, 1, 2, 3], "Permutation")
    assigned = {channel: [values[i] for i in permutation] for channel, values in true.items()}
    if placebo:
        for actual, expected in zip(_vector(group["assigned_rewards"], "assigned rewards"), assigned["R"]):
            _require(actual == expected, "reward assignment: copied numeric evidence differs")
        _require(type(group["observation"]) is dict, "Observation must be an object")
    advantages = {channel: loo(values) for channel, values in assigned.items()}
    recorded = _vector(group["advantages"], "recorded advantages")
    if all(value == assigned["R"][0] for value in assigned["R"]):
        _require(all(value == 0 for value in recorded), "Constant rewards require exact zero logged advantages")
    for i in range(4):
        _close(recorded[i], advantages["R"][i], "recorded LOO")
        _close(advantages["R"][i], advantages["V"][i] + advantages["C"][i], "LOO decomposition")
    zero_sums = {channel: math.fsum(values) for channel, values in advantages.items()}
    for value in zero_sums.values():
        _close(value, 0, "zero-sum advantages")
    optimizer = _boolean(group["optimizer_step"], "optimizer step")
    _exact(optimizer, any(value != 0 for value in recorded), "historical exact optimizer-step rule")
    _integer(group["legal_unique_asts"], "AST count", 0, 4)
    _number(group["usable_future_ic_range"], "IC range", 0, 2)
    _boolean(group["quality_exploration"], "quality exploration")
    norm = _number(group["preclip_grad_norm"], "total preclip norm", 0)
    for field in ("adapter_before", "adapter_after"):
        _sha(group[field], field)
    if not optimizer:
        _exact(group["adapter_before"], group["adapter_after"], "skipped update adapter")
        _close(norm, 0, "skipped gradient norm")
        _require(norm == 0, "Skipped group must have exact zero recorded gradient norm")
    else:
        _require(group["adapter_before"] != group["adapter_after"], "Recorded update must change adapter")
    l1 = {channel: math.fsum(abs(a) for a in values) for channel, values in advantages.items()}
    squared = {channel: math.fsum(a * a for a in values) for channel, values in advantages.items()}
    squared["cross_2VC"] = 2 * math.fsum(v * c for v, c in zip(advantages["V"], advantages["C"]))
    squared["identity_residual"] = squared["R"] - math.fsum((squared["V"], squared["C"], squared["cross_2VC"]))
    _close(squared["R"], math.fsum((squared["V"], squared["C"], squared["cross_2VC"])),
           "squared coefficient identity")
    logps = [row["preupdate_logp"] for row in records]
    surrogate = {channel: -math.fsum(a * logp for a, logp in zip(values, logps)) / 4
                 for channel, values in advantages.items()}
    surrogate["identity_residual"] = surrogate["R"] - math.fsum((surrogate["V"], surrogate["C"]))
    _close(surrogate["R"], math.fsum((surrogate["V"], surrogate["C"])), "surrogate identity")
    opposition = {}
    for channel in ("R", "V"):
        pairs = list(zip(advantages[channel], advantages["C"]))
        opposition[f"{channel}_versus_C_strict"] = sum((a < 0 < c) or (c < 0 < a) for a, c in pairs)
        opposition[f"{channel}_versus_C_zero_cases"] = sum(a == 0 or c == 0 for a, c in pairs)
    return {"group": index, "task_id": task["task_id"], "samples": list(records),
            "permutation": list(permutation), "true_components": true, "assigned_components": assigned,
            "advantages": advantages, "recorded_advantages": list(recorded),
            "coefficient_l1": l1, "coefficient_squared": squared, "surrogate": surrogate,
            "sign_opposition": opposition, "optimizer_step": optimizer,
            "adapter_before": group["adapter_before"], "adapter_after": group["adapter_after"],
            "logged_total_preclip_grad_norm": norm,
            "constant_assigned_reward": all(x == assigned["R"][0] for x in assigned["R"]),
            "active_validity_credit": len(set(true["V"])) > 1,
            "constant_assigned_channels": {c: all(x == assigned[c][0] for x in assigned[c]) for c in CHANNELS},
            "zero_advantage_channels": {c: all(x == 0 for x in advantages[c]) for c in CHANNELS},
            "residuals": {"max_logged_advantage": max(abs(a - b) for a, b in zip(recorded, advantages["R"])),
                          "max_reward_identity": max(row["reward_identity_residual"] for row in records),
                          "max_oriented_ic": max((row["oriented_ic_residual"] for row in records
                                                  if row["oriented_ic_residual"] is not None), default=0.0),
                          "max_sample_group_reward": max(abs(a - b) for a, b in zip(recorded_rewards, true["R"])),
                          "max_assigned_reward": max(abs(a - b) for a, b in zip(group["assigned_rewards"], assigned["R"]))
                          if placebo else 0.0,
                          "max_advantage_additivity": max(abs(r - v - c) for r, v, c in
                                                           zip(advantages["R"], advantages["V"], advantages["C"])),
                          "max_advantage_zero_sum": max(abs(v) for v in zero_sums.values()),
                          "squared_identity": abs(squared["identity_residual"]),
                          "surrogate_identity": abs(surrogate["identity_residual"])}}


def _run(entry, run_id, role, seed):
    placebo = role == "placebo"
    report = entry["training_report" if placebo else "training-report.json"]
    _keys(report, {"manifest", "adapter_before", "adapter_after", "groups", "stopped_at_exploration_gate"}
          | ({"optimizer_steps"} if placebo else set()), run_id)
    manifest = report["manifest"]
    _require(type(manifest) is dict and type(manifest.get("config")) is dict, "Training manifest/config")
    config = manifest["config"]
    expected = {"study": "financial-reward-linkage-control-v1" if placebo else "financial-proposal-v1",
                "phase": "reward_permutation_rloo" if placebo else "rloo", "seed": seed,
                "max_groups": 16, "group_size": 4, "learning_rate": 1e-5, "grad_clip": 1.0,
                "weight_decay": 0.0, "kl_penalty": 0.0, "entropy_bonus": 0.0, "max_completion_tokens": 64}
    if placebo:
        expected.update(permutation_seed=700000 + seed, permutation_rule="assigned[i]=true[p[i]]; uniform all24",
                        adamw_betas=[0.9, 0.999], quality_gate=None)
    for key, value in expected.items():
        if type(value) is float:
            _require(_number(config.get(key), key) == value, f"{run_id} config {key}: exact setting mismatch")
        else:
            _exact(config.get(key), value, f"{run_id} config {key}")
    _exact(report["stopped_at_exploration_gate"], False, "Complete registered population")
    tasks = config.get("task_order")
    _require(type(tasks) is list and len(tasks) == 16, "Sixteen declared tasks required")
    for task, task_id in zip(tasks, TASK_ORDER[seed]):
        _require(type(task) is dict, "Task manifest object required")
        _exact(task.get("task_id"), task_id, "Registered task order")
        _exact(task.get("split"), "train", "Training-only task")
        _exact(task.get("year"), int(task_id[:4]), "Task year")
        _exact(task.get("half"), int(task_id[-1]), "Task half")
    groups = report["groups"]
    _require(type(groups) is list and len(groups) == 16, "Sixteen complete ordered groups required")
    previous = _sha(report["adapter_before"], "initial adapter")
    rows = []
    for index, group in enumerate(groups):
        rows.append(_group(group, index, tasks[index], placebo))
        _exact(group["adapter_before"], previous, "Adapter update chain")
        previous = group["adapter_after"]
    _exact(report["adapter_after"], previous, "Final adapter")
    summary = {
        "groups": 16, "samples": 64,
        "usable_samples": sum(sum(row["true_components"]["V"]) for row in rows),
        "active_validity_groups": sum(row["active_validity_credit"] for row in rows),
        "all_usable_groups": sum(all(row["true_components"]["V"]) for row in rows),
        "all_failed_groups": sum(not any(row["true_components"]["V"]) for row in rows),
        "optimizer_step_groups": sum(row["optimizer_step"] for row in rows),
        "constant_reward_groups": sum(row["constant_assigned_reward"] for row in rows),
        "ic_credit_groups_strict": sum(any(a != 0 for a in row["advantages"]["C"]) for row in rows),
        "coefficient_l1_sums": {c: math.fsum(row["coefficient_l1"][c] for row in rows) for c in CHANNELS},
        "coefficient_squared_sums": {c: math.fsum(row["coefficient_squared"][c] for row in rows)
                                     for c in (*CHANNELS, "cross_2VC")},
        "surrogate_sums": {c: math.fsum(row["surrogate"][c] for row in rows) for c in CHANNELS},
        "sign_opposition": {key: sum(row["sign_opposition"][key] for row in rows)
                            for key in rows[0]["sign_opposition"]},
        "maximum_residuals": {key: max(row["residuals"][key] for row in rows) for key in rows[0]["residuals"]},
    }
    if placebo:
        _exact(report["optimizer_steps"], summary["optimizer_step_groups"], "Recorded optimizer count")
    else:
        _keys(entry["counts"], {"sft_updates", "rl_groups", "rl_updates", "quality_exploration_groups"}, "Counts")
        _exact(entry["counts"], {"sft_updates": 0, "rl_groups": 16,
                                "rl_updates": summary["optimizer_step_groups"],
                                "quality_exploration_groups": sum(g["quality_exploration"] for g in groups)}, "Counts")
        _exact(entry["run-manifest.json"], {"manifest": manifest, "adapter_before": report["adapter_before"]},
               "Original run manifest")
    return {"run_id": run_id, "role": role, "seed": seed, "groups": rows, "summary": summary,
            "adapter_before": report["adapter_before"], "adapter_after": report["adapter_after"]}


def analyze_training_reports(financial, linkage):
    """Pure structural/arithmetic analysis. Input byte identities are NOT attested here."""
    try:
        for document in (financial, linkage):
            _json_value(document)
        _keys(financial, {"study", "role", "runs", "limitations"}, "Financial document")
        _keys(linkage, {"study", "freeze", "scope", "runs"}, "Linkage document")
        _exact(financial["study"], "financial-proposal-v1", "Financial study")
        _exact(linkage["study"], "financial-reward-linkage-control-v1", "Linkage study")
        _keys(financial["runs"], {"financial-sft-v1", RUNS[0][0], RUNS[1][0]}, "Original run set")
        _keys(linkage["runs"], {RUNS[2][0], RUNS[3][0]}, "Control run set")
        runs = [_run((financial if role == "correct" else linkage)["runs"][run_id], run_id, role, seed)
                for run_id, role, seed in RUNS]
        sft_parent = _sha(financial["runs"]["financial-sft-v1"]["training-report.json"]["adapter_after"], "SFT parent")
        for first, second in ((runs[0], runs[2]), (runs[1], runs[3])):
            correct_report = financial["runs"][first["run_id"]]["training-report.json"]
            placebo_report = linkage["runs"][second["run_id"]]["training_report"]
            _exact(correct_report["manifest"]["config"]["task_order"],
                   placebo_report["manifest"]["config"]["task_order"], "Paired full task schedule")
            _exact(first["adapter_before"], second["adapter_before"], "Paired SFT parent")
            _exact(first["adapter_before"], sft_parent, "Saved SFT parent")
            _exact(placebo_report["manifest"]["config"].get("required_parent_parameter_digest"),
                   sft_parent, "Required control parent")
        report = {"schema_version": 1, "study": STUDY, "status": "validated_supplied_training_records",
                  "input_bytes_verified": False,
                  "population": {"runs": 4, "groups_per_run": 16, "samples_per_group": 4, "groups": 64, "samples": 256},
                  "method": {"reward_identity": "R=-1.01+V+C",
                             "C_definition": "V times training-assessment oriented IC; zero for failure is accounting",
                             "assignment": "assigned_X[i]=true_X[permutation[i]]; sample/logp order unchanged",
                             "loo": "center=x-x[0]; A_i=center_i-(sum(center)-center_i)/3",
                             "surrogate": "L_X=-sum(A_X[i]*logged_preupdate_logp[i])/4",
                             "arithmetic_absolute_tolerance": TOLERANCE, "arithmetic_relative_tolerance": TOLERANCE,
                             "optimizer_rule": "any(recorded_advantage != 0), exact historical rule",
                             "sign_rule": "strict opposite signs by direct comparisons; zero cases retained"},
                  "limitations": [
                      "Coefficient magnitudes are not gradient norms, causal shares, or Adam-update attribution.",
                      "Surrogate scalars are sampled objective accounting, not loss reduction or a cross-run ranking.",
                      "C is validity-gated; zero validity advantage does not isolate pure financial learning.",
                      "Saved total gradient norms omit component gradient vectors and their inner products.",
                      "Own-policy control trajectories differ; no counterfactual learning or transfer effect is identified.",
                  ], "runs": runs,
                  "execution": {"new_model_calls": 0, "new_market_scores": 0, "gradients_recomputed": False}}
        _json_value(report)
        return report
    except (KeyError, TypeError, OverflowError, RecursionError) as exc:
        raise RewardCreditError("Malformed training evidence") from exc


def _load(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(RewardCreditError("Nonfinite JSON")))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RewardCreditError("Invalid UTF-8 JSON input") from exc


def analyze_saved_reports(financial_path, linkage_path, *, source_root=None):
    """Verify both exact published buffers, then analyze those same captured bytes."""
    root = Path(source_root).resolve() if source_root is not None else Path(__file__).resolve().parents[2]
    documents, identities = {}, {}
    for key, path in (("financial", financial_path), ("linkage", linkage_path)):
        raw = Path(path).read_bytes()
        relative, expected = SOURCES[key]
        digest = hashlib.sha256(raw).hexdigest()
        _exact(digest, expected, f"{key} source bytes")
        documents[key] = _load(raw)
        identities[key] = {"path": relative, "sha256": digest, "bytes": len(raw)}
    implementation = {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in IMPLEMENTATION_PATHS}
    _exact(implementation[IMPLEMENTATION_PATHS[0]], hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "Loaded analysis source")
    report = analyze_training_reports(documents["financial"], documents["linkage"])
    report.update(status="verified_saved_reward_credit", input_bytes_verified=True,
                  sources=identities, implementation_sha256=implementation)
    return report
