# Replay public Astra research evidence

The replay command checks saved evidence using CPU only. It needs the normal
repository dependencies, public contract, completed submissions, and the source
checkout whose bytes match the contract. It does not require a Codex login,
download data, start a model, read market arrays, or calculate financial scores.

Run from the matching repository checkout after a complete submission file is
available:

```powershell
python -m alpha_research_rl.astra_replay `
  --contract artifacts/astra-agent-v1/contract.json `
  --submissions results/astra_agent_v1_submissions.json `
  --source-root . `
  --output astra-submission-replay.json
```

Use the installed Python command for your environment, such as
`.venv\Scripts\python.exe` on Windows. Output must be a new file. Existing
outputs and collisions with the supplied evidence/source inputs are rejected.
An incomplete collection is not accepted as a smaller completed study.

The verifier requires all ten registered development periods, all three arms,
six records and six successful provider summaries per episode. It reconstructs
each exact actor prompt from the frozen instructions and permitted history,
checks its hash and the provider's prompt/response byte identities, and replays
the broker using the saved feedback. It compares every attempt, feedback mask,
cost, canonical AST, duplicate decision, selector and episode digest exactly.
It also checks the public source/plan byte identities and the loaded broker,
DSL, data and provider modules against those identities.

The result reports `STRUCTURALLY_VERIFIED` separately from
`financial_scores_recomputed: false`. Saved feedback is accepted as evidence;
the verifier does not independently establish that its market calculation was
correct. Raw private CLI streams, private task manifests, round-file contents,
publication timing, server identity and hidden host context are not revalidated.
Their published hash references are checked for structure, not independently
recovered. Check out the original frozen source revision if a later code edit
causes a byte-identity failure.

Usage is summarized separately for every reported token field. Each field has
its reported sum, number of reported decisions and number missing; a complete
sum is null when any decision lacks that field. Missing usage is not zero.
Reasoning tokens are never added to output tokens because their containment is
not established here. Elapsed-time sums, minima and maxima summarize recorded
per-call durations; the sum is not the study's concurrent wall-clock duration.

If a completed assessment artifact is available, add its actual path:

```powershell
python -m alpha_research_rl.astra_replay `
  --contract artifacts/astra-agent-v1/contract.json `
  --submissions results/astra_agent_v1_submissions.json `
  --assessment results/astra_agent_v1_assessment.json `
  --source-root . `
  --output astra-assessment-replay.json
```

This optional pass checks the exact submissions-file hash, all 30 selected
outcomes, feedback-fixed orientations, support/status consistency and the
six-attempt cost. It reconstructs all ten paired differences, three contrasts,
five year averages and the validity/predictive utility decomposition. Computed
floating-point arithmetic uses absolute tolerance `1e-12`; metadata, scalar
types, keys and broker-record replay remain exact. Success is labeled
`SAVED_ARITHMETIC_VERIFIED`, never a fresh market evaluation.

The Python API is `replay_study(contract_path, submissions_path,
source_root=..., assessment_path=None)`. It returns a JSON-compatible summary
and raises on inconsistent evidence. Tests use small synthetic in-memory
episodes; their outcomes are not experimental results.

The repository's CPU CI also runs `python scripts/replay_published_astra.py`
against the actual published bank. It checks all 180 decisions, the 30 saved
assessments, complete trace bookkeeping, and the explorer's embedded evidence
and page template. Recomputed floats use absolute tolerance `1e-12`; scalar
types, keys, order and source identities remain exact. Each bookkeeping digest
is validated before comparing numerical bodies. Process-level guards reject
training imports, raw/private data access, replay subprocesses and network
connections. Standard-library host-platform detection runs first because on
Windows it may invoke the OS version command. The guards are execution checks
rather than an adversarial security sandbox.
