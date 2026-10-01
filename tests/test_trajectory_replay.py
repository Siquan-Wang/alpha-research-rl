"""Replay only previously saved public synthetic trajectories; no actor calls."""

import ast
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from alpha_research_rl.trajectory_replay import (
    LABELS,
    ReplayMismatch,
    replay_reports,
    verify_replay_sources,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def original_inputs():
    reports, sources = {}, {}
    for label in LABELS:
        path = ROOT / "artifacts" / "development" / (label + "-v1.json")
        raw = path.read_bytes()
        reports[label] = json.loads(raw)
        sources[label] = {"file": path.name, "sha256": hashlib.sha256(raw).hexdigest()}
    return reports, sources


@pytest.fixture(scope="module")
def replay(original_inputs):
    return replay_reports(*original_inputs)


def test_all_original_episodes_and_outcomes_replay_exactly_without_mutation(original_inputs, replay):
    before = copy.deepcopy(original_inputs)
    assert replay_reports(*original_inputs) == replay
    assert replay["verified"] is True
    assert replay["summary"] == {"n_episodes": 18, "n_steps": 144,
                                  "maximum_terminal_reward_difference": 0., "all_recorded_outcome_checks_exact": True}
    assert original_inputs == before
    assert all(episode["checks"]["terminal_reward_exact"] for episode in replay["episodes"])
    for episode in replay["episodes"]:
        assert episode["split"] == {"fit": [0, 115], "feedback": [120, 205], "assessment": [210, 295], "horizon": 5}
        assert sum(step["cost"] for step in episode["steps"]) == episode["terminal"]["spent_budget"]
        assert episode["steps"][-1]["done"] is True
        assert all(step["done"] is False for step in episode["steps"][:-1])


def test_actual_acquisition_and_compact_actor_views_are_reconstructed_and_nonleaking(replay):
    episode = next(e for e in replay["episodes"] if e["label"] == "sft")
    steps = episode["steps"]
    assert steps[0]["before"]["environment"]["evidence"] == {}
    assert steps[0]["after"]["environment"]["provenance"]["3"] == {"kind": "propose", "parent": None}
    assert steps[1]["before"]["environment"]["evidence"] == {}
    assert set(steps[1]["after"]["environment"]["evidence"]) == {"3"}
    assert "screen" in steps[1]["after"]["environment"]["evidence"]["3"]
    assert steps[5]["after"]["environment"]["selected"] == [0]
    assert [step["cost"] for step in steps] == [2, 1, 1, 1, 1, 1, 0]
    for step in steps:
        for phase in ("before", "after"):
            state = step[phase]
            actor = state["actor_visible"]
            assert state["reconstructed"] is True
            assert "history" not in actor and "done" not in actor
            assert len(actor["recent_actions"]) <= 3
            assert actor["recent_actions"] == state["environment"]["history"][-3:]
            assert json.loads(state["actor_visible_json"]) == actor
            assert not {"seed", "regime", "split", "assessment", "reward", "terminal"} & actor.keys()


def test_original_base_failures_and_identical_sft_rl_behavior_remain_visible(replay):
    base = [e for e in replay["episodes"] if e["label"] == "base"]
    assert all(len(e["steps"]) == 10 and e["terminal"]["reward"] == -.01 for e in base)
    assert all(step["status"] == "invalid" for e in base for step in e["steps"])
    sft = [e for e in replay["episodes"] if e["label"] == "sft"]
    rl = [e for e in replay["episodes"] if e["label"] == "rloo"]
    for left, right in zip(sft, rl, strict=True):
        assert left["steps"] == right["steps"]
        assert left["terminal"] == right["terminal"]
    p = replay["provenance"]
    assert p["reconstruction"] is True and p["original_actor_prompt_authenticated"] is False
    assert p["original_eos_tokens_authenticated"] is False
    assert p["original_action_token_count_authenticated"] is False
    assert p["whole_package_matches_original"] is False


@pytest.mark.parametrize("change", ["status", "reason", "reward", "spend", "selection", "parsed_action",
                                     "saved_eos", "missing_last", "trailing", "task", "source", "dependency", "cost"])
def test_saved_evidence_or_config_mismatch_fails_clearly(original_inputs, change):
    reports, sources = copy.deepcopy(original_inputs)
    r = reports["sft"]
    e = r["episodes"][0]
    a = e["actions"][0]
    if change == "status":
        a["status"] = "invalid"
    elif change == "reason":
        a["reason"] = "invented"
    elif change == "reward":
        e["reward"] += 1e-12
    elif change == "spend":
        e["spent_budget"] += 1
    elif change == "selection":
        e["selected"] = [1]
    elif change == "parsed_action":
        a["action"] = {"action": "stop"}
    elif change == "saved_eos":
        a["terminated"] = False
    elif change == "missing_last":
        e["actions"].pop()
    elif change == "trailing":
        e["actions"].append(copy.deepcopy(e["actions"][-1]))
    elif change == "task":
        e["seed"] += 1
    elif change == "source":
        r["manifest"]["source_sha256"] = "0" * 64
    elif change == "dependency":
        r["manifest"]["packages"]["numpy"] = "different"
    elif change == "cost":
        a["cost"] = 1
    with pytest.raises(ReplayMismatch, match="expected.*actual"):
        replay_reports(reports, sources)


@pytest.mark.parametrize("target", ["environment.py", "training.py"])
def test_runtime_source_or_factory_drift_fails_before_reconstruction(monkeypatch, target):
    original_read = Path.read_bytes

    def altered(self):
        raw = original_read(self)
        if self.name == target:
            return raw + b"\n# artificial source drift\n" if target == "environment.py" else raw.replace(
                b"budget: int = 10", b"budget: int = 11")
        return raw

    monkeypatch.setattr(Path, "read_bytes", altered)
    with pytest.raises(ReplayMismatch, match="source.*mismatch"):
        verify_replay_sources()


def test_canonical_ast_normalizes_only_missing_versus_empty_type_parameters():
    from alpha_research_rl.trajectory_replay import _canonical_ast

    tree = ast.parse("@decorate\nclass C:\n @decorate\n def f(self, x: int = 2) -> int:\n  async def nested(y=3):\n   return y + x\n  return x\n")
    missing, empty = copy.deepcopy(tree), copy.deepcopy(tree)
    for node in ast.walk(missing):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            node._fields = tuple(name for name in node._fields if name != "type_params")
            if hasattr(node, "type_params"):
                del node.type_params
    for node in ast.walk(empty):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if "type_params" not in node._fields:
                node._fields = (*node._fields, "type_params")
            node.type_params = []
    assert _canonical_ast(missing) == _canonical_ast(empty)
    changed = copy.deepcopy(empty)
    changed.body[0].type_params = [ast.Name(id="T", ctx=ast.Load())]
    assert _canonical_ast(changed) != _canonical_ast(empty)
    # Other empty fields are significant, as are decorators/annotations/defaults.
    changed = copy.deepcopy(empty)
    del changed.body[0].decorator_list
    assert _canonical_ast(changed) != _canonical_ast(empty)
    for edit in ("x: float", "x: int = 4", "@different", "return x + 1"):
        raw = ast.unparse(tree)
        old = "x: int" if edit == "x: float" else "x: int=2" if edit == "x: int = 4" else "@decorate" if edit == "@different" else "return x"
        assert _canonical_ast(ast.parse(raw.replace(old, edit))) != _canonical_ast(tree)


@pytest.mark.parametrize("change", ["nonempty_type_params", "body"])
def test_semantic_ast_change_is_rejected_by_pinned_fingerprint(monkeypatch, change):
    original_parse = ast.parse

    def altered(*args, **kwargs):
        tree = original_parse(*args, **kwargs)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "make_training_env":
                if change == "body":
                    node.body.append(ast.Pass())
                else:
                    if "type_params" not in node._fields:
                        node._fields = (*node._fields, "type_params")
                    node.type_params = [ast.Name(id="T", ctx=ast.Load())]
        return tree

    monkeypatch.setattr(ast, "parse", altered)
    with pytest.raises(ReplayMismatch, match="source AST mismatch training.py/make_training_env"):
        verify_replay_sources()


def test_pinned_ast_hashes_match_with_python311_definition_fields(monkeypatch):
    original_parse = ast.parse

    def without_empty_type_params(*args, **kwargs):
        tree = original_parse(*args, **kwargs)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                assert not getattr(node, "type_params", [])
                node._fields = tuple(name for name in node._fields if name != "type_params")
                if hasattr(node, "type_params"):
                    del node.type_params
        return tree

    monkeypatch.setattr(ast, "parse", without_empty_type_params)
    assert verify_replay_sources()["matching_config_parser_serializer_ast_sha256"]


def test_numeric_package_drift_is_disclosed_without_relaxing_outcome_checks(original_inputs, monkeypatch):
    import alpha_research_rl.trajectory_replay as module

    original_version = module.importlib.metadata.version
    monkeypatch.setattr(module.importlib.metadata, "version", lambda name: "artificial-version" if name in ("numpy", "scipy") else original_version(name))
    result = replay_reports(*original_inputs)
    proof = result["provenance"]
    assert proof["numeric_packages_match_original"] is False
    assert proof["numeric_package_matches_original"] == {"numpy": False, "scipy": False}
    assert proof["numeric_packages_current"] == {"numpy": "artificial-version", "scipy": "artificial-version"}
    assert proof["numeric_packages_original"]["base"] == {
        name: original_inputs[0]["base"]["manifest"]["packages"][name] for name in ("numpy", "scipy")}
    assert any("versions differ" in limit for limit in proof["limits"])
    assert result["summary"]["all_recorded_outcome_checks_exact"] is True
    reports, sources = copy.deepcopy(original_inputs)
    reports["sft"]["episodes"][0]["reward"] += 1e-12
    with pytest.raises(ReplayMismatch, match="terminal reward"):
        replay_reports(reports, sources)
    original_step = module.ResearchEnvironment.step

    def numerical_perturbation(self, action):
        observation, reward, done, info = original_step(self, action)
        return observation, reward + 1e-12 if done else reward, done, info

    monkeypatch.setattr(module.ResearchEnvironment, "step", numerical_perturbation)
    # Original reports are unchanged; a real calculation difference must fail.
    with pytest.raises(ReplayMismatch, match="terminal reward"):
        replay_reports(*original_inputs)


def test_cli_preserves_inputs_and_existing_output_on_mismatch(original_inputs, tmp_path, monkeypatch):
    from alpha_research_rl.trajectory_replay import main

    reports, _ = copy.deepcopy(original_inputs)
    reports["base"]["episodes"][0]["reward"] = .5
    argv = ["trajectory_replay"]
    paths = []
    for label in LABELS:
        path = tmp_path / (label + ".json")
        path.write_text(json.dumps(reports[label]), encoding="utf-8")
        paths.append(path)
        argv.extend(["--" + label, str(path)])
    originals = [path.read_bytes() for path in paths]
    output = tmp_path / "replay.json"
    output.write_bytes(b"preserve existing output")
    argv.extend(["--output", str(output)])
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(ReplayMismatch, match="original report byte identity"):
        main()
    assert [path.read_bytes() for path in paths] == originals
    assert output.read_bytes() == b"preserve existing output"


@pytest.mark.parametrize("label", LABELS)
def test_cli_success_case_output_collision_preserves_original_bytes(tmp_path, monkeypatch, label):
    from alpha_research_rl.trajectory_replay import main

    argv = ["trajectory_replay"]
    paths = {}
    for role in LABELS:
        path = tmp_path / (role + ".json")
        path.write_bytes((ROOT / "artifacts/development" / (role + "-v1.json")).read_bytes())
        paths[role] = path
        argv.extend(["--" + role, str(path)])
    originals = {role: path.read_bytes() for role, path in paths.items()}
    # Resolve an alias so the refusal cannot depend on spelling alone.
    argv.extend(["--output", str(tmp_path / "alias" / ".." / paths[label].name)])
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(ReplayMismatch, match="output/input path collision"):
        main()
    assert {role: path.read_bytes() for role, path in paths.items()} == originals


@pytest.mark.parametrize("change", ["equivalent_action_text", "summary", "byte_hash"])
def test_self_consistent_changed_report_cannot_borrow_historical_identity(original_inputs, change):
    reports, sources = copy.deepcopy(original_inputs)
    if change == "equivalent_action_text":
        # This would replay identically, including every saved status and total.
        reports["sft"]["episodes"][0]["actions"][0]["text"] += " "
    elif change == "summary":
        reports["sft"]["summary"]["invented"] = "not original evidence"
    else:
        sources["sft"]["sha256"] = "0" * 64
    with pytest.raises(ReplayMismatch, match="original report (canonical|byte) identity"):
        replay_reports(reports, sources)


def test_fresh_process_import_and_replay_do_not_import_torch_or_transformers():
    script = '''
import importlib.abc,json,sys,hashlib
from pathlib import Path
class Reject(importlib.abc.MetaPathFinder):
 def find_spec(self, fullname, path=None, target=None):
  if fullname.split('.')[0] in ('torch','transformers'):
   raise AssertionError('forbidden import '+fullname)
sys.meta_path.insert(0,Reject())
from alpha_research_rl.trajectory_replay import replay_reports,LABELS
reports={};sources={}
for label in LABELS:
 p=Path('artifacts/development')/(label+'-v1.json');raw=p.read_bytes()
 reports[label]=json.loads(raw);sources[label]={'file':p.name,'sha256':hashlib.sha256(raw).hexdigest()}
r=replay_reports(reports,sources)
assert r['summary']['n_steps']==144
assert 'torch' not in sys.modules and 'transformers' not in sys.modules
print('CPU-only replay verified')
'''
    result = subprocess.run([sys.executable, "-c", script], cwd=ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "CPU-only replay verified"
