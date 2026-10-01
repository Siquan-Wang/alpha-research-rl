# Installed-package reproduction review

2026-10-01. No packaging defect was found in the tested source snapshot. A built
wheel installed into a fresh target reproduced the complete five-policy,
900-draw saved-result analysis and the 18-episode, 144-action synthetic replay.
Both checks imported the installed package rather than the editable checkout.

This is an **installed-package boundary test on the current Windows host**,
not an independent-machine replication. Existing CPU dependencies were reused;
they were not freshly downloaded or installed. The separate Linux Python
3.11/3.12 CI matrix and root's public-download check remain separate evidence.

## Tested artifact and isolation

| Item | Observed identity |
| --- | --- |
| Python | 3.12.14, Windows |
| Build backend | setuptools 78.1.0; pip 25.0.1 |
| Wheel | `alpha_research_rl-0.1.0-py3-none-any.whl` |
| Wheel SHA-256 | `3e9dcdbdeaccdbae777b08dd5b522f15ee8595487e94e8f9f16f1e490ba2b4ef` |
| Installed package source digest | `5674fc57522a9514cbaacc14c1568b8d4edb862bb358951326972202ac3c89dd` |
| Existing CPU packages | NumPy 2.5.3, pandas 3.0.6, SciPy 1.18.1 |
| Wheel base requirements | `numpy>=1.26`, `pandas>=2.1`, `scipy>=1.11` |

A copy of the package's 36 Python files, `pyproject.toml`, README and license
was made under ignored `.local/packaging-review/`. Build outputs, installation,
copied public input reports and logs stayed there. Every wheel Python source
file matched its captured source-snapshot byte hash. Required replay source
files, including `training.py` and `llm.py` for the pinned definitions, were
present. The wheel included the declared console entry point and no model
weights, raw market archives or saved-report data.

The isolated worker used `python -I`, put the fresh target first on `sys.path`,
and removed editable-package import hooks. All 17 loaded
`alpha_research_rl` modules and the selected distribution metadata resolved
inside that target. Model-library imports (`torch`, `transformers`, `peft`,
`accelerate`, `huggingface_hub`) were prohibited and none were loaded. A Python
audit hook blocked socket operations except the local hostname query needed by
the numerical runtime, and limited audited file access to review resources,
the existing Python environments and the null device. No raw data, local model,
private workspace input or network access was needed for either replay.
This is a Python-level check, not an operating-system-wide security sandbox.

The original editable environment was not reinstalled or replaced. A separate
check still resolved its source package from `src/` and retained its editable
distribution metadata after the target installation.

## Results and preservation checks

- **Five-policy saved-result analysis:** the installed `linkage_analysis` CLI
  read the five original public transfer-report byte streams, retaining all 900
  draws. Its entire parsed JSON output equaled the published
  `results/financial_linkage_paired_v1.json`, including identities, statistics,
  task/year tables and both matched-seed comparisons. It loaded no market data
  and generated no new proposals or scores.
- **Synthetic trajectory replay:** the installed `trajectory_replay` CLI
  verified all 18 episodes and 144 actions. All recorded outcome checks were
  exact and the maximum terminal-reward difference was zero. Replay-core byte
  pins and the portable AST fingerprints passed from installed `.py` files.
  Reconstructed observations remain reconstructions; installation does not
  authenticate the missing original prompt or completion tokens.
- **Console entry point:** wheel metadata declared
  `alpha-research = alpha_research_rl.cli:main`. The loaded entry point's help
  passed inside the isolated worker. The actual generated Windows launcher
  also ran `--help` from the scratch directory; verbose import records showed
  the package and CLI loaded from the installed target.
- **Fresh benchmark path:** the installed CLI selected
  `.local/synthetic-benchmark.json` by default. A stub replaced benchmark
  computation so this check introduced no new benchmark study. A second call
  rejected the existing path before invoking that stub and preserved its
  bytes. This verifies CLI dispatch/default/overwrite protection, not the
  benchmark's numerical performance.
- **Input preservation:** all nine copied public inputs—three synthetic reports,
  five transfer reports and the published paired analysis—retained their
  original byte hashes after the checks.

## Commands and reproducibility boundary

The build and target-install commands used existing tools without an index or
build isolation, from the copied source directory:

```bash
python -m pip wheel . --no-deps --no-build-isolation --no-index \
  --no-cache-dir --wheel-dir ../wheels
python -m pip install --no-index --no-deps --no-cache-dir \
  --target ../target ../wheels/alpha_research_rl-0.1.0-py3-none-any.whl
```

The replay worker ran in isolated mode, explicitly inserted the installed target,
and invoked these installed modules with the public saved inputs:

```bash
python -m alpha_research_rl.linkage_analysis \
  --sft inputs/financial-sft-transfer-v1.json \
  --rl23 inputs/financial-rloo23-transfer-v1.json \
  --rl29 inputs/financial-rloo29-transfer-v1.json \
  --placebo23 inputs/financial-placebo23-transfer-v1.json \
  --placebo29 inputs/financial-placebo29-transfer-v1.json \
  --output outputs/linkage-analysis.json
python -m alpha_research_rl.trajectory_replay \
  --base inputs/base-v1.json --sft inputs/sft-v1.json --rloo inputs/rloo-v1.json \
  --output outputs/trajectory-replay.json
```

These latter commands describe module arguments, not a claim that plain
`python -m` automatically chooses the target. A reproduction must assert the
imported module locations or use a genuinely separate environment containing
the built wheel. Here, dependencies came from the existing environment while
all project modules came from the new target.

The first build attempt hit the host's unwritable default pip cache. Disabling
the cache resolved that tool-environment issue; no package source change was
needed. The source digest above identifies the tested snapshot, so subsequent
source additions require a newly identified wheel. Wheel ZIP timestamps can
also change its byte digest on rebuilding the same sources.

This check supports offline installed-code reanalysis of public evidence. It
does not load adapters or prove retraining reproducibility,
establish numerical identity on another platform, or expand any financial or
sequential-learning result claim. See the
[linkage reproduction boundary](../reproduce-linkage-control.md) for exact
original-parent requirements.
