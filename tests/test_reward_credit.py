"""Artificial records only: no historical bank analysis, model or market calls."""

import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import pytest

from alpha_research_rl import reward_credit as rc


def _digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _sample(ic, i):
    metric = lambda mean: {"mean_ic": mean, "coverage": 1.0, "ic_std": 0.2,
                           "n_dates": 30, "n_signal_dates": 30}
    expression = f"delay(returns,{i + 1})" if ic is not None else "unsupported(returns)"
    outcome = {"expression": expression, "reward": ic - 0.01 if ic is not None else -1.01,
               "cost": 0.01, "status": "ok" if ic is not None else "invalid",
               "reason": None if ic is not None else "invalid_expression", "anchor_reuse": False,
               "orientation": 1 if ic is not None else None,
               "feedback": metric(0.1) if ic is not None else None,
               "assessment": metric(ic) if ic is not None else None,
               "oriented_future_ic": ic, "zero_feedback_tie": False}
    return {"text": "artificial", "action": {"action": "propose", "expression": expression},
            "terminated": True, "completion_ids": [i + 1, 100], "prompt_ids": [2, 3],
            "outcome": outcome, "recomputed_preupdate_completion_logp": -float(i + 1)}


def _reference_loo(values):
    # Independent direct means; fixtures use tolerances for binary floating point.
    if all(x == values[0] for x in values):
        return [0.0] * 4
    return [value - math.fsum(values[:i] + values[i + 1:]) / 3 for i, value in enumerate(values)]


def synthetic_documents():
    parent = _digest("synthetic SFT")
    financial = {"study": "financial-proposal-v1", "role": "artificial training record",
                 "runs": {"financial-sft-v1": {"training-report.json": {"adapter_after": parent}}},
                 "limitations": []}
    linkage = {"study": "financial-reward-linkage-control-v1", "freeze": {}, "scope": "artificial", "runs": {}}
    patterns = ([0.03, 0.06, 0.12, 0.21], [None, -0.4, None, 0.2], [None] * 4, [0.1] * 4)
    for run_id, role, seed in rc.RUNS:
        placebo = role == "placebo"
        tasks = [{"task_id": name, "year": int(name[:4]), "half": int(name[-1]), "split": "train"}
                 for name in rc.TASK_ORDER[seed]]
        config = {"study": "financial-reward-linkage-control-v1" if placebo else "financial-proposal-v1",
                  "phase": "reward_permutation_rloo" if placebo else "rloo", "seed": seed,
                  "max_groups": 16, "group_size": 4, "learning_rate": 1e-5, "grad_clip": 1.0,
                  "weight_decay": 0.0, "kl_penalty": 0.0, "entropy_bonus": 0.0, "max_completion_tokens": 64,
                  "task_order": tasks}
        if placebo:
            config.update(permutation_seed=700000 + seed, permutation_rule="assigned[i]=true[p[i]]; uniform all24",
                          adamw_betas=[0.9, 0.999], quality_gate=None, required_parent_parameter_digest=parent)
        groups, before = [], parent
        for index, task in enumerate(tasks):
            samples = [_sample(ic, i) for i, ic in enumerate(patterns[index % 4])]
            true = [s["outcome"]["reward"] for s in samples]
            permutation = [2, 0, 3, 1] if placebo else [0, 1, 2, 3]
            assigned = [true[i] for i in permutation]
            advantages = _reference_loo(assigned)
            update = any(x != 0 for x in advantages)
            after = _digest(f"{run_id}:{index}") if update else before
            group = {"group": index, "task": copy.deepcopy(task), "advantages": advantages,
                     "preclip_grad_norm": 0.25 if update else 0.0, "optimizer_step": update,
                     "legal_unique_asts": sum(ic is not None for ic in patterns[index % 4]),
                     "usable_future_ic_range": 0.1 if update else 0.0, "quality_exploration": update,
                     "adapter_before": before, "adapter_after": after, "samples": samples}
            if placebo:
                group.update(observation={}, true_rewards=true, assigned_rewards=assigned, permutation=permutation)
            else:
                group["rewards"] = true
            groups.append(group)
            before = after
        manifest = {"config": config}
        report = {"manifest": manifest, "adapter_before": parent, "adapter_after": before,
                  "groups": groups, "stopped_at_exploration_gate": False}
        if placebo:
            report["optimizer_steps"] = 8
            linkage["runs"][run_id] = {"training_report": report}
        else:
            financial["runs"][run_id] = {
                "training-report.json": report, "run-manifest.json": {"manifest": manifest, "adapter_before": parent},
                "counts": {"sft_updates": 0, "rl_groups": 16, "rl_updates": 8, "quality_exploration_groups": 8}}
    return financial, linkage


def test_complete_population_arithmetic_and_no_mutation():
    documents = synthetic_documents()
    original = copy.deepcopy(documents)
    report = rc.analyze_training_reports(*documents)
    assert documents == original
    assert report["population"] == {"runs": 4, "groups_per_run": 16, "samples_per_group": 4, "groups": 64, "samples": 256}
    assert report["input_bytes_verified"] is False
    assert [row["run_id"] for row in report["runs"]] == [r[0] for r in rc.RUNS]
    for run in report["runs"]:
        summary = run["summary"]
        assert (summary["groups"], summary["samples"], summary["usable_samples"]) == (16, 64, 40)
        assert (summary["active_validity_groups"], summary["optimizer_step_groups"], summary["constant_reward_groups"]) == (4, 8, 8)
        assert summary["all_usable_groups"] == 8
        assert summary["all_failed_groups"] == 4
        assert max(summary["maximum_residuals"].values()) < 1e-12
    first = report["runs"][0]["groups"][0]
    assert first["advantages"]["C"] == pytest.approx([-0.1, -0.06, 0.02, 0.14])
    assert first["advantages"]["V"] == [0.0] * 4
    assert first["surrogate"]["C"] == pytest.approx(0.1)
    assert first["surrogate"]["R"] == pytest.approx(first["surrogate"]["C"])
    assert first["surrogate"]["V"] == 0


def test_recorded_control_assignment_not_inverse_or_reordered_logps():
    report = rc.analyze_training_reports(*synthetic_documents())
    row = report["runs"][2]["groups"][1]
    assert row["permutation"] == [2, 0, 3, 1]
    assert row["true_components"]["V"] == [0, 1, 0, 1]
    assert row["assigned_components"]["V"] == [0, 0, 1, 1]
    assert row["assigned_components"]["C"] == [0.0, 0.0, 0.2, -0.4]
    assert [s["preupdate_logp"] for s in row["samples"]] == [-1, -2, -3, -4]
    for channel in rc.CHANNELS:
        expected = -sum(a * logp for a, logp in zip(row["advantages"][channel], [-1, -2, -3, -4])) / 4
        assert row["surrogate"][channel] == pytest.approx(expected)


def test_tiny_credit_is_preserved_and_constant_centering_is_exact():
    assert rc.loo([-1.01] * 4) == [0.0] * 4
    tiny = rc.loo([0.0, 1e-200, 2e-200, 3e-200])
    assert all(x != 0 for x in tiny)
    assert tiny[0] < 0 < tiny[-1]
    assert sum(tiny) == pytest.approx(0, abs=1e-210)


def _first(financial):
    return financial["runs"]["financial-rloo23-v1"]["training-report.json"]


@pytest.mark.parametrize("mutation", [
    lambda f, l: _first(f)["groups"].pop(),
    lambda f, l: _first(f)["groups"][0]["samples"].pop(),
    lambda f, l: _first(f)["groups"][0].update(group=True),
    lambda f, l: _first(f)["groups"][1].update(group=0),
    lambda f, l: _first(f)["groups"].reverse(),
    lambda f, l: _first(f)["manifest"]["config"].update(seed=True),
    lambda f, l: _first(f)["manifest"]["config"].update(group_size=4.0),
    lambda f, l: _first(f)["manifest"]["config"].update(learning_rate=math.nextafter(1e-5, 1)),
    lambda f, l: _first(f)["manifest"]["config"].update(kl_penalty=False),
    lambda f, l: _first(f)["groups"][0]["samples"][0]["outcome"].update(cost=math.nextafter(0.01, 1)),
    lambda f, l: _first(f)["groups"][0]["samples"][0].update(recomputed_preupdate_completion_logp=0.1),
    lambda f, l: _first(f)["groups"][0]["samples"][0].update(recomputed_preupdate_completion_logp=float("nan")),
    lambda f, l: _first(f)["groups"][0]["samples"][0]["completion_ids"].append(True),
    lambda f, l: _first(f)["groups"][0]["samples"][0]["outcome"].update(orientation=True),
    lambda f, l: _first(f)["groups"][0]["samples"][0]["outcome"].update(oriented_future_ic=0.7),
    lambda f, l: _first(f)["groups"][1]["samples"][0]["outcome"].update(oriented_future_ic=0),
    lambda f, l: _first(f)["groups"][0]["advantages"].__setitem__(0, 2.0),
    lambda f, l: _first(f)["groups"][2].update(optimizer_step=True),
    lambda f, l: _first(f)["groups"][2].update(preclip_grad_norm=1e-20),
    lambda f, l: _first(f)["groups"][0].update(adapter_after=_first(f)["groups"][0]["adapter_before"]),
    lambda f, l: f["runs"]["financial-sft-v1"]["training-report.json"].update(adapter_after="f" * 64),
    lambda f, l: l["runs"]["financial-placebo23-v1"]["training_report"]["groups"][0].update(permutation=[0, 0, 2, 3]),
    lambda f, l: l["runs"]["financial-placebo23-v1"]["training_report"]["groups"][0].update(permutation=[True, 0, 2, 3]),
    lambda f, l: l["runs"]["financial-placebo23-v1"]["training_report"]["groups"][0]["assigned_rewards"].reverse(),
])
def test_inconsistent_evidence_never_produces_reduced_population(mutation):
    documents = synthetic_documents()
    mutation(*documents)
    with pytest.raises(rc.RewardCreditError):
        rc.analyze_training_reports(*documents)


def test_full_paired_task_metadata_must_agree():
    financial, linkage = synthetic_documents()
    report = linkage["runs"]["financial-placebo23-v1"]["training_report"]
    report["manifest"]["config"]["task_order"][0]["extra"] = "changed"
    report["groups"][0]["task"]["extra"] = "changed"
    with pytest.raises(rc.RewardCreditError, match="Paired full task"):
        rc.analyze_training_reports(financial, linkage)


@pytest.mark.parametrize("raw", [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}', b'\xff'])
def test_json_loader_rejects_ambiguous_or_nonfinite_evidence(raw):
    with pytest.raises(rc.RewardCreditError):
        rc._load(raw)


def test_exact_byte_binding_before_parse_and_retained_source_identity(tmp_path, monkeypatch):
    documents = synthetic_documents()
    paths = []
    source_map = {}
    for key, document in zip(("financial", "linkage"), documents):
        raw = json.dumps(document).encode()
        path = tmp_path / f"{key}.json"
        path.write_bytes(raw)
        paths.append(path)
        source_map[key] = (f"synthetic/{key}.json", hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(rc, "SOURCES", source_map)
    for relative in rc.IMPLEMENTATION_PATHS:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(Path(rc.__file__).read_bytes() if relative == rc.IMPLEMENTATION_PATHS[0] else b"synthetic identity")
    report = rc.analyze_saved_reports(*paths, source_root=tmp_path)
    assert report["input_bytes_verified"] is True
    assert len(report["implementation_sha256"]) == 4
    assert report["sources"]["financial"]["sha256"] == source_map["financial"][1]
    paths[0].write_bytes(paths[0].read_bytes() + b"\n")
    with pytest.raises(rc.RewardCreditError, match="source bytes"):
        rc.analyze_saved_reports(*paths, source_root=tmp_path)


def _cli():
    path = Path(__file__).resolve().parents[1] / "scripts/analyze_reward_credit.py"
    spec = importlib.util.spec_from_file_location("reward_credit_cli_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_exclusive_output_and_failed_durability_is_not_success(tmp_path, monkeypatch, capsys):
    cli = _cli()
    calls = []
    def analyze(*args, **kwargs):
        calls.append(1)
        return {"status": "synthetic", "population": {"groups": 64}}
    monkeypatch.setattr(cli, "analyze_saved_reports", analyze)
    output = tmp_path / "new.json"
    assert cli.main(["--output", str(output)]) == 0
    first = output.read_bytes()
    assert cli.main(["--output", str(output)]) == 2
    assert output.read_bytes() == first and calls == [1]
    assert cli.main(["--financial", str(output), "--output", str(output)]) == 2
    monkeypatch.setattr(cli.os, "fsync", lambda _: (_ for _ in ()).throw(OSError("synthetic fsync failure")))
    failed = tmp_path / "failed.json"
    assert cli.main(["--output", str(failed)]) == 2
    assert failed.exists()
    assert "not complete evidence" in capsys.readouterr().err
