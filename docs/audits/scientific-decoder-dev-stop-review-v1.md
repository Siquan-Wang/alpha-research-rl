# Scientific decoder development v1: saved stop review

2026-10-01. **The saved evidence supports an incomplete target-generation stage and the prescribed stop. It contains no model-performance result.** The review found no discrepancy in the retained counts, request/source bindings or public evidence copies.

This is an internal Astra Ultra review. I participated in earlier design and source reviews but did not author or execute the worker, driver or scorer. Root supplied the claimed counts; I independently reconstructed them from the saved requests and row records using standard-library JSON, hashing and arithmetic, without importing project code. This was not an outcome-blinded review, a repeated experiment or external peer review. No hidden law bodies were interpreted or printed, and no oracle, provider, scorer, generator, network request or Git operation was run.

## Counts and stopping behavior

| Scheduled task | Planned | Attempted | Finite outputs | Failed | Unattempted |
| --- | ---: | ---: | ---: | ---: | ---: |
| `m8_sound_speed:medium:v0` | 64 | 64 | 64 | 0 | 0 |
| `m8_sound_speed:hard:v1` | 64 | 64 | 64 | 0 | 0 |
| `m10_be_distribution:medium:v2` | 64 | 7 | 6 | 1 | 57 |
| `m10_be_distribution:hard:v0` | 64 | 0 | 0 | 0 | 64 |
| **Total** | **256** | **135** | **134** | **1** | **121** |

All three saved requests contain the exact 64 corresponding training coordinates from the frozen coordinate bank, with matching task/domain/version and zero-noise request. All 192 retained row records have ordered native-integer indices and valid status/value shapes. The first two outputs are COMPLETE. In the third output, rows 0–5 are finite successes, row 6 is failed with null value, and rows 7–63 are explicitly `not_attempted`. The fourth task has no request or output; its 64 unattempted slots are scheduled population, not invented worker records. Thus 192 points were present in requests, but only 135 callbacks were attempted.

The rejection at task 2, zero-based index 6, is `nonfinite_or_nonscalar_output`. Inspection of the bound worker's scalar-return check confirms that this code covers a Boolean, a non-real/nonscalar object, or a value whose float conversion is nonfinite. The raw rejected object is not retained. The evidence therefore does **not** identify a particular NaN, infinity, overflow or hidden-formula cause. The worker subsequently wrote `INCOMPLETE`, `oracle_row_failure` and `stage: finished`; the last field means it finished recording the failure, not that target collection succeeded.

The local run directory contains exactly the binding and three request/output/stdout/stderr sets. All six logs are empty. There is no fourth request, completed training ledger, prompt record, actor directory, response bank, confirmation request or score artifact. Together with the driver stage order and root's execution account, this supports **zero hosted calls, zero confirmation targets and zero model/reference predictions for this version**. The allocation inequalities are unevaluated, not model failures or zero-valued predictive scores.

## Provenance and timing

I independently checked all 11 bound source/metadata identities against the saved binding. Each output's request SHA matches its exact request file. Each output identifies the bound worker, pinned upstream commit and source manifest; its recorded vendor-origin entries agree with the manifest. I did not reinterpret vendor law source. The public binding's projection and private-binding SHA also match the local binding.

The [preflight manifest](../../artifacts/scientific-decoder-dev-v1/preflight-manifest.json) supplies 36 snapshot entries. Those entries plus the public binding, preflight manifest, public guide and unchanged transport reconstruct the exact 40-file map in the [publication receipt](../../artifacts/scientific-decoder-dev-v1/execution/publication-preflight.json). All 40 current local file hashes match that map. This is a saved-byte consistency check, not my own remote fetch. The receipt records anonymous raw-file verification at commit `3d818347f286e15ce673f5814411f7d27261a026`, completed at `2026-10-01T17:01:31.675904+00:00`.

The first request's local modification time is `2026-10-01T17:01:39.1982349Z`; the final incomplete output's is `2026-10-01T17:01:40.0235046Z`. They corroborate root's account that the single training-stage invocation followed successful public verification. They are not independently authenticated event times. Worker rows contain no embedded per-call timestamps, and the receipt is coordinator-produced; this review cannot turn those artifacts into an external chronology attestation or prove the absence of arbitrary activity outside the recorded protocol.

All 13 files in the new public [execution directory](../../artifacts/scientific-decoder-dev-v1/execution/)—three request/output pairs, six logs and the receipt—are byte-identical to the inspected local evidence. The [stop record](../../results/scientific_decoder_dev_v1.json) and accompanying report accurately retain the full denominator, collapsed error-code limit, missing performance outcomes and stopped disposition.

| Evidence | SHA256 |
| --- | --- |
| Stop record | `06950ce985f5fd7f05ba8ecb3fe9966f09cba3c352ce7fec32f54ef7682b2db3` |
| Publication receipt | `87bdf5e73a0aa4563b8743c02a915f325d83153126c335331420cde49f1ed80b` |
| Private binding, public hash only | `a8d37a03164d7492eda85abc2f68a8b2aee0ce705fc41401abe1ba36b6699c72` |
| Bound worker | `4f9a23e93a11e71a5064ab3902cff926b9417e33de384768854a60a57fee3152` |
| Task 0 output | `d78605a2dbf12b20eaf0bafb7649be8aca4164bcf98d891cd9e9aebe8d2ae850` |
| Task 1 output | `7ea7f0df5213e3833629ab3fb929199924f9779650e099f82b554803a99946d1` |
| Task 2 output | `bb33fc7985295b9153b19399f15c542e37cde40cc8026c89a75b6b0d0df28306` |

## Interpretation

The configured oracle and adapted support did not complete the required finite-scalar target collection. Source-conditional determinism and import qualification never established numerical totality over that support. Because the stop preceded every hosted call, these records establish neither success nor failure of Astra inference, expression representability, adaptive acquisition, financial prediction or weight learning. The original version remains stopped with its source, support, coordinates and failed/unattempted slots preserved; this audit supplies no basis to repair or resume it from the observed failure.
