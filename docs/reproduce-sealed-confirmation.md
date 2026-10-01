# Replay the sealed-confirmation evidence

This is a **saved-evidence replay of a completed synthetic interface validation**. It does not run another simulation bank, query a model, load market data or extend a financial study. The [plan](sealed-confirmation-plan-v1.md), [explanation](sealed-confirmation.md) and [result JSON](../results/sealed_confirmation_v1.json) describe its scope.

## Run from a complete checkout

Use Python 3.11 or later and a checkout containing the result **and all retained panel ledgers** under `artifacts/sealed-confirmation-v1/execution/`. The earlier pre-run publication commit contains the preparation evidence, not the later completed bank. Preserve the repository's exact bytes; formatting a bound source, test or plan file intentionally invalidates replay.

Only the Python standard library and this checkout's source are needed. No package installation, model download, credentials or internet access is required by this replay command. From the repository root, on PowerShell:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) "src")
python scripts/check_sealed_confirmation.py replay
```

Use an existing Python 3.11+ executable in place of `python` if necessary; for this project's existing Windows environment it is `.\.venv\Scripts\python.exe`. On a POSIX shell:

```sh
PYTHONPATH=src python3 scripts/check_sealed_confirmation.py replay
```

The command reads the recorded arrays and traces, reconstructs the six arms' decisions and arithmetic, and prints a compact verification object. Expected fields include:

```json
{
  "status": "SAVED_SYNTHETIC_CONFIRMATION_VERIFIED",
  "panels": 640,
  "report_sha256": "ec6d9076d70f50d436c3d69a9ec126d23489f2ce4f98bbf4e25064e6d9c7306d",
  "new_panel_generations": 0,
  "new_model_calls": 0,
  "new_market_scores": 0,
  "writes": 0
}
```

The output also includes a scope statement. Missing evidence is an error, never a skipped validation. Replay checks the contract and loaded runner/core identities, publication receipt, complete ordered 512-null/128-planted population, event chronology and hash chains, full attempt histories and frozen predictions, outcome roles, exact statistic denominators and final report. It compares the public result with the retained execution copy and rechecks consumed file hashes before returning. It invokes no feature/noise generator; the runner itself makes no network or model calls. This is a reviewed code path, not an operating-system sandbox.

## Recorded identities

The pre-run receipt records anonymous byte verification at commit `00c17f400bda3f25b995db3b8e35150110fe5b97`, at `2026-10-01T13:40:23.540538+00:00`. Replay validates that retained receipt and its bindings; it does not repeat the network verification.

| File | SHA-256 |
| --- | --- |
| `docs/sealed-confirmation-plan-v1.md` | `151f0e6946a8d0353ab61ffaf23de09f77168a66b8597036b281f8df82cac143` |
| `scripts/check_sealed_confirmation.py` | `dbe8a73d1ccd31a65fcfab53e3f30102ea1a4be35db96e695eee69759c6e8292` |
| `src/alpha_research_rl/sealed_confirmation.py` | `d5b91b30cf97a25eb52af6580e4a894652b6400cbcd046324a15975f66b6cbf2` |
| `tests/test_sealed_confirmation.py` | `25163dffb511b03b63ff86c1787a6f6671d64d5ad2fca8cb1a65d2fa98f426c7` |
| `tests/test_sealed_confirmation_fixture.py` | `155de17541c53c055705d5f6a71f3a3e2faf4532876ca901d4cab655265ba4de` |
| `tests/test_sealed_confirmation_review.py` | `8f52ffe5699c956a22a3a7d7e0cfe169786c62ae6bb29ea346fd621a5e965928` |
| `artifacts/sealed-confirmation-v1/contract.json` | `12fcd6791ddc2197b4e20350dd80415d5532668ffedf2b66ab0d144d7e6a6ede` |
| `artifacts/sealed-confirmation-v1/execution/publication-receipt.json` | `22ee58695ef24e955b23b1af502dba5f19f420939612cb4695ea364a264a9210` |
| `results/sealed_confirmation_v1.json` | `ec6d9076d70f50d436c3d69a9ec126d23489f2ce4f98bbf4e25064e6d9c7306d` |

The contract binds the six source/plan/test files. The result binds each panel's JSONL ledger and completion record; those hashes are not duplicated in this guide. The receipt does not hash itself, avoiding a recursive publication requirement.

## Why `prepare` and `run` refuse an existing version

`prepare` requires a fresh preparation directory. `run` requires the bound execution directory and public result to be absent, then claims that directory before the first panel. Any completed, failed or interrupted execution blocks another run. Failure evidence is retained; it cannot silently become a non-rejection, replacement panel or clean retry. Therefore refusal on this completed checkout is intended behavior. Do not delete evidence or change the canonical destination to bypass it.

Replay is the supported operation for this version. Deterministically regenerating known artificial bits would be a different verification activity, not an independent statistical replication: identical seeds do not supply new panels. A corrected generator or fresh outcome bank would require a separately named, prospectively specified version retaining this one. No such run is part of these instructions.

## What the completed checks mean

The correct fixed and adaptive searches rejected on **23/512** and **21/512** null panels, within their predeclared upper limit of 37. The planted oracle rejected on **128/128**, meeting its lower limit of 128. Those three checks passed in this finite synthetic bank.

The orientation-only, fixed-selection and adaptive-selection faults produced **39/512**, **480/512** and **294/512** naive null rejections. All three remain `PROTOCOL_INVALID`; their statistical exceedances were descriptive, not required pass conditions. The fixed search's planted result of **128/128** versus the adaptive search's **72/128** describes these particular algorithms. The fixed search explicitly includes the planted mask; neither algorithm learned through model training.

The exact calibration argument assumes independent fair confirmation signs under the null, conditional on all search information and frozen choices. Replaying arrays verifies recorded arithmetic and access order; it cannot establish that law for financial returns, prove pseudorandom independence, attest hidden access, or establish that saved arrays originated from the declared generator. This adds reproducible engineering evidence for a new interface, with no new market, GenAI-superiority, profitability or reinforcement-learning claim.
