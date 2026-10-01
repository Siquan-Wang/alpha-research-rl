# Reproduce the separate Astra frozen-pool diagnosis

This is an explicitly **post-hoc** analysis of the already generated v1
candidate pools. Its [protocol](astra-pool-diagnosis-plan-v1.md) is separate
from the immutable v1 study. It permits zero model calls and at most 108 new
CPU evaluations of previously frozen candidates. The original v1 assessment
remains its 30 selected calls. No original artifact is overwritten.

There are three phases: prepare immutable evidence, execute after public
verification, and replay saved arithmetic. Only the execute phase imports the
market loader and evaluator. The preparation and execution runtime must match
the versions recorded in the new protocol. Saved replay does not require those
installed scoring versions or the raw market ZIP; it uses the usual repository
dependencies and the matching public source checkout.

## Prepare without additional scoring

From the repository root, using its installed Python interpreter:

```powershell
python -m alpha_research_rl.astra_pool_diagnosis prepare `
  --v1-contract artifacts/astra-agent-v1/contract.json `
  --submissions results/astra_agent_v1_submissions.json `
  --assessment results/astra_agent_v1_assessment.json `
  --task-manifest-dir .local/astra-agent-v1/tasks `
  --source-root .
```

The original task directory is an input, not a location to reconstruct or
overwrite. Preparation checks its ten sealed files against the original
contract and mirrors their exact bytes into
`artifacts/astra-pool-diagnosis-v1/tasks/`. It creates the new
`artifacts/astra-pool-diagnosis-v1/contract.json` only after validating the
complete bank, assessment, runtime, raw ZIP hash, source and plan identities.
The ZIP path is read from the original contract. Hashing its bytes does not
construct financial tasks or evaluate any candidate.

The output directory must be new. Production preparation enforces the exact
v1 input hashes and the registered population: 180 slots, 132 keys, 24 reused
keys, 108 pending jobs, 167 positive and 13 negative slot orientations. It also
binds all selector choices, task lengths, execution order, and one permitted
execution directory. Synthetic tests replace only test input identities and
the byte-checking/task/publication dependencies; they are not new studies.

## Public gate and bounded execution

Publish the new plan, implementation, tests, this guide, prepared contract and
ten task mirrors with the unchanged original evidence and frozen dependencies.
Root verifies the public commit and exact bytes through unauthenticated public
retrieval. The module does not replace this check with a claim that a local Git
commit is public.

`publication_files(contract_path, source_root=...)` returns the precise
relative-path/SHA256 map that the receipt must cover. Root saves a JSON object
with these fields:

- `schema`: `astra-pool-publication-receipt-v1`.
- `study`: `astra-frozen-pool-diagnosis-v1`.
- `commit`: the full 40-character lowercase public commit ID.
- `verified_utc`: UTC ISO timestamp of the completed public byte check.
- `verification_method`: `root-verified unauthenticated public retrieval`.
- `public_repository_url`: the HTTPS GitHub repository URL, without a trailing slash.
- `paths_sha256`: the exact map returned by `publication_files`.
- `body_sha256`: the existing broker `digest` of all the preceding fields.

The receipt is root's retained verification statement. Execution independently
checks the corresponding local Git blobs against captured bytes and rejects
missing paths, changed files, an incorrect commit, or a future-dated receipt
before constructing tasks. The receipt itself follows preparation/publication
and is not recursively included in the prepared contract.

```powershell
python -m alpha_research_rl.astra_pool_diagnosis execute `
  --contract artifacts/astra-pool-diagnosis-v1/contract.json `
  --publication-receipt .local/astra-pool-diagnosis-v1/publication.json `
  --published-commit FULL_PUBLIC_COMMIT_ID `
  --execution-dir artifacts/astra-pool-diagnosis-v1/execution `
  --max-jobs 108 `
  --source-root .
```

Only root executes the real diagnosis after independent review and publication.
The bounded command caches constructed tasks, evaluates keys in the frozen
order, and aborts on its first integrity or execution failure. `max_jobs` may
be a smaller positive number to stop at a fully completed prefix. A subsequent
explicit invocation resumes at the first unstarted key; it never repeats an
existing evaluation. The execution directory is contract-bound, so a second
directory cannot bypass this state.

Each call has an exclusive, flushed STARTED record before the evaluator and
a sealed COMPLETED record only after full outcome validation. The start binds
the prior completed file hash. An exclusive study lock prevents concurrent
execution. An interrupted STARTED record, a failed or corrupt job, unexplained
files, or an INCOMPLETE marker blocks further scoring under this version.
Do not delete a lock or change directories to bypass that condition. If an
interruption occurs after a complete valid job record was durably written,
the wrapper can establish a clean prefix by artifact validation, without
calling the evaluator again. Completed diagnoses refuse execute and allow
saved replay only.

Historical feedback must match the saved five-field bundle exactly, including
types, support, direction, zero tie and probe identity. New assessment-side
invalid or unscorable results keep utility -1.06. Historical drift, a malformed
result or an uncaught exception is an incomplete run, not a penalized candidate.
The failing raw return is retained when available; earlier records remain.

## Complete output and saved replay

Only after all 132 keys and all 180 slots are accounted for does execution
create `execution/COMPLETE.json`. Root may mirror those exact bytes to the
protocol's public result path `results/astra_pool_diagnosis_v1.json` after
review. A partial prefix returns counts and retains evidence, without a
full-bank report. The complete output includes every original slot, unmodified
reuse source outcome, evaluated expression spelling, new job reference,
selector result, and the fixed task/year/arm summaries.

```powershell
python -m alpha_research_rl.astra_pool_diagnosis replay `
  --contract artifacts/astra-pool-diagnosis-v1/contract.json `
  --execution-dir artifacts/astra-pool-diagnosis-v1/execution `
  --report results/astra_pool_diagnosis_v1.json `
  --source-root . `
  --output astra-pool-saved-replay.json
```

The optional `--report` checks that the public result is byte-identical to the
retained complete report. Replay output must be a new path. Saved replay checks
the original public evidence, job hash chain, record bodies, exact retained
feedback/provenance, complete accounting and recomputed aggregate arithmetic.
Only derived finite arithmetic receives 1e-12 absolute/relative tolerance;
saved identities, metadata, scalar types and feedback remain exact. Replay
does not open the ZIP, check installed scoring versions, construct tasks,
import the financial loader/evaluator, access a network or rescore anything.

The Python APIs are `prepare_pool_diagnosis`, `publication_files`,
`execute_pool_diagnosis`, and `replay_pool_diagnosis`. Explicit task-loader and
local-publication-verifier dependencies in the execute API support artificial
tests; the command-line interface uses the frozen real loader and Git checker.

## Interpretation

All candidates retain cost .06, including duplicate cache references and
first/minimum-AST selector comparisons. Distinct ASTs are syntax identities,
not independent economic signals. Source expressions are never rewritten to
pretend that an alias was the spelling actually evaluated.

The original selector is `S`, the maximum future utility within each fixed
six-slot pool is the unattainable hindsight ceiling `O`, and `R=O-S`. Reports
verify all three contrasts through `Delta S = Delta O - Delta R`, retain every
task and year, and expose validity denominators through `mean(u)=-1.06+p+q`.
No positive oracle gap proves that a feasible selector could identify the
better candidate; it is guaranteed by construction. `Delta O` is not a causal
generation contribution.

The full-feedback ceiling determines only whether selection among these exact
pools and directions can reach positive mean IC or fixed-cost utility. A
positive ceiling authorizes no automatic follow-up experiment. The report
does not establish factor originality, profitability, a fresh holdout, a need
for an LLM generator, general causal effects, or Astra weight training. The
first/minimum-AST rules were chosen after the original selected outcomes were
known. This remains a diagnosis of one realized trajectory per arm and reused
2020–2024 development periods.
