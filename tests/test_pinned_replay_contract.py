"""Independent artificial completion/import-boundary checks; no historical replay."""

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("pinned_contract_launcher", ROOT / "scripts/replay_pinned_study.py")
launcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launcher)

REVISION = "matched-prefix-v1"
SEALED = "sealed-confirmation-v1"


def complete_summary(name):
    recipe = launcher.RECIPES[name]
    summary = copy.deepcopy(recipe["expected_summary"])
    if name == REVISION:
        summary.update(historical_new_feedback_calls=98,
                       contract_sha256="9f531a0cc6bffc81d010f54b49a4a717703bfef81197d75ddac890373da9b574",
                       submissions_sha256="672d93cd8faababc71a7b3b5ff3823da840061479798f0ec1f2b6eef1cc9577d",
                       renderer_sha256="3dfb34a58dc934c7a585b3b675dcbed6aaa3b86010fec84f64086bfccc33e568")
    return recipe, summary


def test_registry_binds_the_two_adopted_results_and_real_denominators():
    assert set(launcher.RECIPES) == {REVISION, SEALED}
    revision, sealed = launcher.RECIPES[REVISION], launcher.RECIPES[SEALED]
    assert revision["commit"] == "7e0f7b35618ace986de6ce0cfa1a6231e7716080"
    assert revision["report_sha256"] == "89162112ddad384ed8917a8b1198ce94044abc90ff15e1680bfe88b66eb43c37"
    assert revision["html_sha256"] == "8bb1ff7013c8c7906f9223daca87287296103f8643e41216037d2bbf39d9b772"
    assert sealed["commit"] == "58dc66ed2a4af7add8ee79f54337e278d9bd7d13"
    assert sealed["report_sha256"] == "ec6d9076d70f50d436c3d69a9ec126d23489f2ce4f98bbf4e25064e6d9c7306d"
    assert "html_path" not in sealed and "html_sha256" not in sealed
    # Independent literals prevent a self-consistent registry/template mistake.
    expected = {"states": 10, "slots": 200, "repetitions": 4,
                "historical_hosted_calls": 80, "historical_cheap_slots": 120,
                "historical_new_feedback_calls": 98,
                "historical_new_future_calls": 99, "reused_future_keys": 34,
                "unique_future_keys": 133, "captured_execution_file_count": 685,
                "replay_model_calls": 0, "replay_financial_scores": 0}
    for key, value in expected.items():
        assert type(revision["expected_summary"][key]) is int
        assert revision["expected_summary"][key] == value
    for key, value in {"panels": 640, "new_panel_generations": 0, "new_model_calls": 0,
                       "new_market_scores": 0, "writes": 0}.items():
        assert type(sealed["expected_summary"][key]) is int
        assert sealed["expected_summary"][key] == value


@pytest.mark.parametrize("name", [REVISION, SEALED])
def test_complete_summary_accepts_only_its_own_recipe(name):
    recipe, summary = complete_summary(name)
    launcher.validate_summary(recipe, summary)
    other = launcher.RECIPES[SEALED if name == REVISION else REVISION]
    with pytest.raises(launcher.ReplayError):
        launcher.validate_summary(other, summary)


@pytest.mark.parametrize("name", [REVISION, SEALED])
def test_every_summary_field_is_required_and_unknown_fields_are_rejected(name):
    recipe, good = complete_summary(name)
    for field in good:
        bad = {key: value for key, value in good.items() if key != field}
        with pytest.raises(launcher.ReplayError):
            launcher.validate_summary(recipe, bad)
    with pytest.raises(launcher.ReplayError):
        launcher.validate_summary(recipe, {**good, "partial_success": True})


@pytest.mark.parametrize("name", [REVISION, SEALED])
def test_numerically_equal_float_or_boolean_cannot_replace_an_exact_count(name):
    recipe, good = complete_summary(name)
    for field, value in good.items():
        if type(value) is int:
            with pytest.raises(launcher.ReplayError):
                launcher.validate_summary(recipe, {**good, field: float(value)})
            if value in (0, 1):
                with pytest.raises(launcher.ReplayError):
                    launcher.validate_summary(recipe, {**good, field: bool(value)})
            with pytest.raises(launcher.ReplayError):
                launcher.validate_summary(recipe, {**good, field: value + 1})


def test_equal_integer_values_cannot_replace_boolean_safety_assertions():
    recipe, good = complete_summary(REVISION)
    flags = {key: value for key, value in good.items() if type(value) is bool}
    assert flags["market_scores_recomputed"] is False
    assert flags["explorer_payload_and_template_match"] is True
    for field, value in flags.items():
        with pytest.raises(launcher.ReplayError):
            launcher.validate_summary(recipe, {**good, field: int(value)})
        with pytest.raises(launcher.ReplayError):
            launcher.validate_summary(recipe, {**good, field: not value})


@pytest.mark.parametrize("name", [REVISION, SEALED])
def test_report_and_required_html_hashes_are_exact_not_just_well_formed(name):
    recipe, good = complete_summary(name)
    for field in ("report_sha256", "explorer_html_sha256"):
        if field not in good:
            continue
        for replacement in ("0"*64, good[field].upper(), good[field][:-1], None):
            with pytest.raises(launcher.ReplayError):
                launcher.validate_summary(recipe, {**good, field: replacement})


@pytest.mark.parametrize("field", ["contract_sha256", "submissions_sha256", "renderer_sha256"])
def test_historical_summary_digest_fields_reject_malformed_values(field):
    recipe, good = complete_summary(REVISION)
    for replacement in ("0"*64, "A"*64, "g"*64, "a"*63, 0, None, "a"*64+"\n"):
        with pytest.raises(launcher.ReplayError):
            launcher.validate_summary(recipe, {**good, field: replacement})


def test_feedback_count_is_exact_historical_accounting_not_a_plausible_range():
    recipe, good = complete_summary(REVISION)
    for value in (-1, 0, 17, 97, 99, 200, 201, False, 98.0):
        with pytest.raises(launcher.ReplayError):
            launcher.validate_summary(recipe, {**good, "historical_new_feedback_calls": value})
    launcher.validate_summary(recipe, {**good, "historical_new_feedback_calls": 98})


def test_historical_missing_package_cannot_fall_through_to_installed_package(tmp_path, monkeypatch):
    tree, site = tmp_path / "tree", tmp_path / "site"
    (tree / "src").mkdir(parents=True)
    package = site / "alpha_research_rl"
    package.mkdir(parents=True)
    marker = tmp_path / "external-imported"
    (package / "__init__.py").write_text(f"open({str(marker)!r}, 'w').write('unexpected')\n", encoding="utf-8")
    monkeypatch.setattr(sys, "path", [str(site), *sys.path])
    finder = launcher.HistoricalFinder(tree, "revision")
    with pytest.raises(launcher.ReplayError, match="historical module missing"):
        finder.find_spec("alpha_research_rl")
    assert not marker.exists()


def test_package_extended_path_cannot_execute_an_external_missing_child(tmp_path):
    tree, external = tmp_path / "tree", tmp_path / "external"
    historic = tree / "src/alpha_research_rl"
    historic.mkdir(parents=True)
    external.mkdir()
    (historic / "__init__.py").write_text("", encoding="utf-8")
    marker = tmp_path / "external-child-imported"
    (external / "new_child.py").write_text(f"open({str(marker)!r}, 'w').write('unexpected')\n", encoding="utf-8")
    finder = launcher.HistoricalFinder(tree, "revision")
    with pytest.raises(launcher.ReplayError, match="escaped tree"):
        finder.find_spec("alpha_research_rl.new_child", [str(historic), str(external)])
    assert not marker.exists()


def test_missing_historical_helper_cannot_use_a_current_scripts_directory(tmp_path, monkeypatch):
    tree, current = tmp_path / "tree", tmp_path / "current-scripts"
    (tree / "scripts").mkdir(parents=True)
    current.mkdir()
    (current / "replay_published_results.py").write_text("raise AssertionError('current helper executed')\n", encoding="utf-8")
    monkeypatch.setattr(sys, "path", [str(current), *sys.path])
    with pytest.raises(launcher.ReplayError, match="historical module missing"):
        launcher.HistoricalFinder(tree, "revision").find_spec("replay_published_results")


def artificial_capsule(base, *, missing=None):
    """Materialized tiny fake tree; no Git, real report or historical execution."""
    output = base / ".local/pinned-replay-runs/artificial-capsule"
    tree, dependency, poisoned = (output / "tree", base / "existing-test-dependencies",
                                  base / "poisoned-pythonpath")
    for directory in (tree, dependency, poisoned):
        directory.mkdir(parents=True)
    scratch_relative = ".local/p/0123456789abcdef"
    scratch = launcher.allocate_scratch(base, output, scratch_relative,
                                         "artificial-import-contract", "f"*40)
    marker = scratch / "outside-code-executed"
    attack = f"from pathlib import Path\nPath({str(marker)!r}).write_text('unexpected')\n"
    (poisoned / "sitecustomize.py").write_text(attack, encoding="utf-8")
    (dependency / "sitecustomize.py").write_text(attack, encoding="utf-8")
    (dependency / "trigger.pth").write_text(f"import pathlib; pathlib.Path({str(marker)!r}).write_text('pth')\n",
                                            encoding="utf-8")
    outside = dependency / "alpha_research_rl"
    outside.mkdir()
    (outside / "__init__.py").write_text(attack + "FROM_HISTORICAL = False\n", encoding="utf-8")
    (dependency / "replay_published_results.py").write_text(attack, encoding="utf-8")
    for package in ("numpy", "scipy"):
        path = dependency / package
        path.mkdir()
        (path / "__init__.py").write_text("__version__ = 'artificial-fixture-only'\n", encoding="utf-8")
    recipe = copy.deepcopy(launcher.RECIPES[REVISION])
    recipe["commit"] = "f"*40
    report_raw, html_raw = b'{"artificial_fixture":true}\n', b"<!doctype html><p>Artificial fixture</p>\n"
    recipe["report_sha256"] = hashlib.sha256(report_raw).hexdigest()
    recipe["html_sha256"] = hashlib.sha256(html_raw).hexdigest()
    summary = copy.deepcopy(recipe["expected_summary"])
    summary.update(report_sha256=recipe["report_sha256"], explorer_html_sha256=recipe["html_sha256"],
                   contract_sha256=hashlib.sha256(b"artificial-contract").hexdigest(),
                   submissions_sha256=hashlib.sha256(b"artificial-submissions").hexdigest(),
                   renderer_sha256=hashlib.sha256(b"artificial-renderer").hexdigest())
    recipe["expected_summary"] = summary
    files = {
        "src/alpha_research_rl/__init__.py": b"FROM_HISTORICAL = True\n",
        "src/alpha_research_rl/fixture_support.py": b"VALUE = 'historical-fixture'\n",
        "scripts/replay_published_results.py": b"VALUE = 'historical-helper'\n",
        recipe["report_path"]: report_raw,
        recipe["html_path"]: html_raw,
        "scripts/replay_published_astra_revision.py": (
            "import json\nimport alpha_research_rl\nfrom alpha_research_rl import fixture_support\n"
            "import replay_published_results\nimport numpy\nimport scipy\n"
            "assert alpha_research_rl.FROM_HISTORICAL is True\n"
            "assert fixture_support.VALUE == 'historical-fixture'\n"
            "assert replay_published_results.VALUE == 'historical-helper'\n"
            f"SUMMARY = {summary!r}\ndef main():\n    print(json.dumps(SUMMARY, sort_keys=True))\n"
        ).encode(),
    }
    if missing == "package":
        files.pop("src/alpha_research_rl/__init__.py")
    elif missing == "helper":
        files.pop("scripts/replay_published_results.py")
    entries = []
    for relative, raw in sorted(files.items()):
        target = tree / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        oid = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        entries.append({"path": relative, "mode": "100644", "oid": oid, "size": len(raw),
                        "sha256": hashlib.sha256(raw).hexdigest()})
    manifest = {"schema": "pinned-tree-manifest-v1", "recipe": "artificial-import-contract",
                "commit": recipe["commit"], "tree_oid": "e"*40,
                "total_bytes": sum(len(raw) for raw in files.values()), "files": entries}
    manifest_raw = (launcher.canonical(manifest)+"\n").encode("ascii")
    (output / "tree-manifest.json").write_bytes(manifest_raw)
    (output / "STARTED.json").write_text(launcher.canonical({"recipe": manifest["recipe"],
                                                             "commit": recipe["commit"],
                                                             "scratch_relative": scratch_relative}), encoding="ascii")
    request = {"schema": "pinned-replay-request-v1", "recipe_id": manifest["recipe"], "recipe": recipe,
               "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(), "dependency_dirs": [str(dependency)],
               "scratch_relative": scratch_relative}
    request_raw = (launcher.canonical(request)+"\n").encode("ascii")
    (output / "child-request.json").write_bytes(request_raw)
    (output / "bootstrap.py").write_bytes((ROOT / "scripts/replay_pinned_study.py").read_bytes())
    env = dict(os.environ)
    env["PYTHONPATH"] = str(poisoned)
    env["PYTHONUSERBASE"] = str(dependency)
    return output, marker, summary, env, hashlib.sha256(request_raw).hexdigest()


def launch_artificial_capsule(fixture):
    output, _, _, env, request_hash = fixture
    return subprocess.run([sys.executable, "-I", "-S", "-B", str(output / "bootstrap.py"), "--_child",
                           str(output / "child-request.json"), request_hash],
                          cwd=output / "tree", env=env, capture_output=True, text=True,
                          encoding="utf-8", timeout=30, check=False)


def test_real_child_route_ignores_pythonpath_pth_and_startup_customization(tmp_path):
    fixture = artificial_capsule(tmp_path)
    output, marker, expected, _, _ = fixture
    before = {p.relative_to(output / "tree"): p.read_bytes() for p in (output / "tree").rglob("*") if p.is_file()}
    result = launch_artificial_capsule(fixture)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == expected
    assert not marker.exists()
    proof = json.loads((output / "child-proof.json").read_bytes())
    assert proof["runtime"]["third_party_versions"] == {"numpy": "artificial-fixture-only", "scipy": "artificial-fixture-only"}
    assert proof["runtime"]["third_party_origins"] == {
        package: {"dependency_directory_index": 0, "relative_path": package + "/__init__.py"}
        for package in ("numpy", "scipy")}
    assert proof["import_origins"]["alpha_research_rl"]["path"] == "src/alpha_research_rl/__init__.py"
    assert proof["import_origins"]["alpha_research_rl.fixture_support"]["path"] == "src/alpha_research_rl/fixture_support.py"
    assert proof["prohibited_operations"] == []
    request = json.loads((output / "child-request.json").read_bytes())
    started = json.loads((output / "STARTED.json").read_bytes())
    owner = json.loads((tmp_path / request["scratch_relative"] / "OWNER.json").read_bytes())
    assert proof["scratch_relative"] == started["scratch_relative"] == request["scratch_relative"]
    assert owner == {"schema": "pinned-scratch-owner-v1", "capsule_relative": output.relative_to(tmp_path).as_posix(),
                     "recipe": request["recipe_id"], "commit": request["recipe"]["commit"],
                     "scratch_relative": request["scratch_relative"]}
    after = {p.relative_to(output / "tree"): p.read_bytes() for p in (output / "tree").rglob("*") if p.is_file()}
    assert before == after


@pytest.mark.parametrize("missing", ["package", "helper"])
def test_real_child_missing_historical_code_never_executes_installed_fallback(tmp_path, missing):
    fixture = artificial_capsule(tmp_path, missing=missing)
    output, marker, _, _, _ = fixture
    result = launch_artificial_capsule(fixture)
    assert result.returncode != 0
    assert "historical module missing" in result.stderr
    assert not marker.exists()
    assert not (output / "child-proof.json").exists()


def test_real_child_rejects_scratch_reference_disagreement_before_import(tmp_path):
    fixture = artificial_capsule(tmp_path)
    output, marker, _, _, _ = fixture
    started = json.loads((output / "STARTED.json").read_bytes())
    started["scratch_relative"] = ".local/p/fedcba9876543210"
    (output / "STARTED.json").write_text(launcher.canonical(started), encoding="ascii")
    completed = launch_artificial_capsule(fixture)
    assert completed.returncode != 0
    assert "capsule start differs" in completed.stderr
    assert not marker.exists()
    assert not (output / "child-proof.json").exists()


def test_parent_proof_requires_manifest_bound_origins_and_typed_runtime(tmp_path):
    fixture = artificial_capsule(tmp_path)
    output, _, _, _, _ = fixture
    completed = launch_artificial_capsule(fixture)
    assert completed.returncode == 0, completed.stderr
    good = json.loads((output / "child-proof.json").read_bytes())
    manifest = json.loads((output / "tree-manifest.json").read_bytes())
    recipe = json.loads((output / "child-request.json").read_bytes())["recipe"]
    launcher.validate_child_proof(recipe, good, manifest)
    mutations = []
    for field, replacement in (("import_origins", None), ("import_origins", {}),
                                ("runtime", None), ("scratch_writes_permitted", 1),
                                ("scratch_writes_permitted", False), ("prohibited_operations", {}),
                                ("prohibited_operations", ["caught forbidden action"]), ("guard_scope", "unchecked"),
                                ("scratch_relative", None), ("scratch_relative", ".local/p/0123456789ABCDEF"),
                                ("scratch_relative", ".local/p/../0123456789abcdef")):
        bad = copy.deepcopy(good)
        bad[field] = replacement
        mutations.append(bad)
    bad = copy.deepcopy(good)
    bad["import_origins"]["alpha_research_rl"]["sha256"] = "0"*64
    mutations.append(bad)
    bad = copy.deepcopy(good)
    bad["import_origins"]["alpha_research_rl"] = copy.deepcopy(bad["import_origins"]["pinned_revision_entrypoint"])
    mutations.append(bad)
    bad = copy.deepcopy(good)
    bad["import_origins"]["alpha_research_rl.extra"] = copy.deepcopy(bad["import_origins"]["alpha_research_rl.fixture_support"])
    mutations.append(bad)
    for field, replacement in (("python", ""), ("implementation", 3),
                                ("platform", {"system": "fake"}), ("third_party_versions", {"numpy": 1}),
                                ("third_party_versions", {}), ("third_party_origins", {})):
        bad = copy.deepcopy(good)
        bad["runtime"][field] = replacement
        mutations.append(bad)
    for field, replacement in (("dependency_directory_index", False), ("dependency_directory_index", -1),
                                ("relative_path", "../numpy/__init__.py"), ("relative_path", "scipy/__init__.py")):
        bad = copy.deepcopy(good)
        bad["runtime"]["third_party_origins"]["numpy"][field] = replacement
        mutations.append(bad)
    for bad in mutations:
        with pytest.raises(launcher.ReplayError):
            launcher.validate_child_proof(recipe, bad, manifest)
