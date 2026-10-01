# Independent reward-linkage training and freeze review

Reviewed 2026-10-01 before control transfer outcomes were inspected. This review
uses trainer source, retained training traces, the public training export,
checkpoint file bytes, saved roundtrip records, and the declared five-checkpoint
registry. No model generation, new market scoring, GPU operation, or scorer
edit was performed by the reviewer.

## Training mechanism and retained evidence

`linkage_training.py` samples four fresh completions from its own current actor
for each group, evaluates their true training outcomes, and separately assigns
rewards through one uniform `permutation(4)` call. The dedicated generator is
seeded with `700000 + seed`; it does not control task order or token sampling.
All rewards, including failures, enter the permutation. The source has no
quality-triggered stop and writes the entry manifest before optimization.

For both saved runs, independent reconstruction confirmed every permutation,
`assigned[i] = true[p[i]]`, reward multiset, leave-one-out advantage, original
true-outcome reward, finite pre-update log-probability, EOS/action trace,
optimizer-step flag, and parameter-digest chain. Task manifests, task order,
prompt token IDs, parent digest, and FP32 actor provenance match the corresponding
original correctly linked run. Entry and final manifests agree, and recorded
plan/trainer SHA256 values match the reviewed files.

| Seed | Groups | Optimizer steps | Usable/all | Repeated-reward groups | Permutations preserving reward values |
| --- | ---: | ---: | ---: | ---: | ---: |
| 23 | 16 | 16 | 64/64 | 13 | 3 |
| 29 | 16 | 16 | 63/64 | 15 | 2 |

Neither run drew the identity permutation; that is an observed realization,
not a derangement restriction. Repeated values and unchanged assignments remain
in the evidence. There were no constant-reward groups. Seed 29 has two groups
with approximately `1e-9` gradient norms: repeated identical completions receive
opposite nonzero advantages, nearly cancelling their score gradients. Their
Adam steps are permitted by the declared nonzero-advantage rule; they must not
be interpreted as strong realized financial-learning signals.

The controls share 22/64 and 41/64 completion token sequences with their original
seed counterparts. Initial agreement is expected from the common parent and
sampling seed. Source execution uses fresh current-policy samples throughout;
matching strings do not establish replay, and different strings alone would not
establish useful learning. All 32 recorded optimizer steps changed their adapter
digests. Both controls start at the required SFT digest
`2de3acf5ae1f6dee2b5b335f083e2c2b5e76f224a1f1de7eb2b151d709a01c53`.

## Checkpoint, export, and byte provenance

The five-way registry frozen at `2026-10-01T04:58:36.053875+00:00` preserves all
three original checkpoint dictionaries, binds the actual three original report
file hashes, and reproduces the canonical original-suite SHA256. All five
actual adapter/config file sizes and SHA256 values match the registry.
The public export's two training-report and roundtrip hashes match the retained
local files; its embedded report objects equal those files' parsed contents.
Both root-run roundtrip records have identical before/after adapter digests and
zero completion-log-probability difference. The reviewer did not rerun those
GPU checks.

At commit `94fdc9c`, all seven frozen scorer source blobs matched local and
recorded contract hashes. A subsequent check found the original report blobs
had normalized LF while local frozen bytes used CRLF. Root corrected publication
without changing working files. At `2ddb8cb`, all 34 tracked JSON blobs match
their local bytes, including the paired-analysis source-report bindings and
sensitivity input binding. At `05aa82d`, the new registry and training-export
blobs also match local bytes. Hash validation was not relaxed for line endings.

## Judgment and limits

No blocking mismatch was found in the completed training mechanism or
pre-evaluation registry. These checks establish execution/provenance consistency,
not a financial advantage. Uniform reward permutation has zero expected
pre-clipping score gradient conditional on a fixed sampled group; realized
gradients, clipped gradients, Adam updates, future trajectories, and evaluation
effects need not have zero expectation. The two fresh on-policy controls must
remain distinct from original RL and from syntax-only or no-update baselines.
Their transfer comparison remains exploratory and must retain both seeds and
all failures.
