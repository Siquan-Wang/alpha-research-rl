# Replay the public matched-prefix revision evidence

This entrypoint verifies the complete saved evidence for `astra-matched-prefix-v1`.
It does not generate a proposal, launch a model, reconstruct a market panel, or
compute a new financial score. It is separate from collection and assessment.

Run from a matching repository checkout with the ordinary package dependencies
already installed:

```powershell
python scripts/replay_published_astra_revision.py
```

For a fresh environment, install the ordinary package before replay with
`python -m pip install -e .`. The `train` extra, local model weights, market ZIP,
private actor logs, and a provider login are not needed. Package installation is
a separate setup step and may access the configured package index; the replay
command itself prohibits network access.

The command has no alternate data-directory argument and does not skip absent
artifacts. Run the matching published source and evidence together. A missing,
partial, failed, active, or changed study exits unsuccessfully. Before a complete
result has been published, this is the expected behavior.

## Required evidence

The fixed inputs are:

- `artifacts/astra-matched-prefix-v1/contract.json`, its bound source/input files,
  and the complete public `execution` ledger;
- `results/astra_matched_prefix_v1_submissions.json`, containing all 200 frozen
  slots and their historical choices;
- `results/astra_matched_prefix_v1.json`, containing the complete saved outcomes,
  all 200 resolved rows, and the analysis;
- the original v1 and pool evidence referenced by the bound revision contract.

The public submissions and result must exactly match the internal execution
`SUBMISSIONS.json` and `COMPLETE.json` bytes. The wrapper checks their status,
schema, study identity, fixed population, row ordering, historical call counts,
and exact SHA-256 hashes reported by `replay_revision_study`. It requires the
collection request, preparation receipt, assessment request, submissions receipt,
and assessment plan. The saved replay checks the bound evidence and ledgers,
reconstructs the branch outcomes and analysis, and rejects inconsistent records.
It reads saved public JSON; it does not verify a cache entry by rescoring it.

Success prints one JSON summary. `historical_hosted_calls: 80` describes the
completed experiment, while `replay_model_calls: 0` and
`replay_financial_scores: 0` describe this command. The fixed denominator is 200
slots: 80 hosted continuations and 120 cheap references across ten states and four
repetitions. Invalid and duplicate attempts remain in that denominator. Actual
new historical feedback and future calls can be lower than 200 through reuse or
ineligibility; each must be an integer between zero and 200. At completion,
`unique_future_keys = reused_future_keys + new_future_calls`. Unique keys also
include reused prefix factors, so they need not be bounded by the 200 new slots.

The wrapper requires the replay to report zero new model calls, zero financial
scores, zero raw-market-data reads, and no revalidation of the originally
installed scoring runtime. The returned contract, submissions, and report hashes
must equal the actual public file bytes, which are checked again after replay.

## Process checks and limits

The entrypoint rejects financial scorer/loader and training-library imports,
including forbidden modules that were already imported. Python audit hooks block
network events, subprocess launches, and opens under the repository's `models`,
`data/raw`, `data/cache`, and `.local` directories. Standard-library platform
detection runs first because Windows may use a subprocess to identify its
platform; this does not launch a model or read market data. Synthetic tests check
the subsequent guard behavior in fresh child interpreters.

These are checks on this trusted Python replay process, not an adversarial
operating-system sandbox. They do not attest the hosted model's actual identity,
the service's internal actions, the original installed binaries, or a trusted
wall-clock timestamp. Saved publication receipts are checked as recorded evidence;
this command does not re-fetch GitHub. Exact hashes establish agreement with the
checked-out evidence, not an independent external signature of that evidence.

Replay is also not independent economic replication. All ten market states are
development periods, four continuations per state do not create four independent
markets, and inference is not Astra weight training. Interpret Q, selector gain G,
failure penalties, and the conditional-generation variability under the separate
[matched-prefix protocol](astra-matched-prefix-plan-v1.md).

## Validation scope

The entrypoint tests use artificial file trees and injected saved-replay callbacks
to check routing, missing evidence, exact accounting and byte boundaries, failure
propagation, and active process guards. They import the real driver only to check
that importing it does not load a financial scorer or training dependency. This
does not claim that a complete real revision study has been collected, scored,
or successfully replayed. Root integrates the command into public CI after the
actual complete evidence exists.

```powershell
python -m pytest -q tests/test_public_astra_revision_replay_script.py -p no:cacheprovider --basetemp .local/revision-replay-tests
```

Use a fresh, short test directory for each run. The tests invoke harmless child
Python processes to exercise the guards; they make no provider or market calls.
