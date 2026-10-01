# Post-hoc Astra trace bookkeeping

This CPU-only report describes the frozen 180 proposal records using their
saved historical feedback. It is a **post-hoc descriptive analysis**, not a
new preregistered endpoint, market evaluation, or evidence of learned Astra
weights. It does not read the assessment artifact, market arrays, private CLI
streams, or model credentials; it does not invoke a model or network service.
No future candidate is scored.

Run from the source checkout matching the public contract:

```powershell
python -m alpha_research_rl.astra_trace_diagnostics `
  --contract artifacts/astra-agent-v1/contract.json `
  --submissions results/astra_agent_v1_submissions.json `
  --source-root . `
  --output astra-trace-diagnostics.json
```

Use the Python interpreter installed for the repository, such as
`.venv\Scripts\python.exe` on Windows. The output must be a new path. Existing
outputs and collisions with evidence or source inputs are rejected. There is
no assessment argument. The Python API is
`diagnose_traces(contract_path, submissions_path, source_root=...)`.

The builder captures contract and submissions bytes once and writes exact
temporary copies for the existing [structural replay](replay-astra-evidence.md).
Only after successful replay does it analyze the same captured objects. It
never rereads the original inputs to form the analysis. The gate requires all
ten periods, all three arms, six charged attempts each, matching source/plan
bytes, prompt identities, masks, duplicate flags, selection rules, and sealed
records. Missing episodes are a failure, not a smaller completed study.

## Counts and their denominators

`all` and `by_arm` retain the 180 and 60 charged-attempt denominators. Every one
of the ten entries in `periods` contains all three arms and all 18 attempts for
that period. Counts distinguish:

- Grammar-valid and grammar-invalid completed proposals.
- Feedback-usable records, feedback-unusable records, and unavailable feedback.
  A usable repeated AST still counts as a usable charged record; its cached
  score does not represent a new financial evaluation.
- Within-episode duplicate AST records and unique proposals eligible for the
  common selector. Eligibility requires usable feedback and no previous
  occurrence of that AST within the episode.
- The union of distinct canonical AST strings within the reported scope, and
  the sum of unique AST counts across episodes. These quantities differ when
  the same AST occurs in several episodes or arms. Per-arm union sizes must
  not be summed to claim the bank-wide union size.
- Selected attempts 1 through 6 and an explicit `unavailable` selection count.

AST identity is exactly the broker's recorded Python AST identity. This report
does not reorder arithmetic, remove rank-preserving transformations, infer
functional equivalence, or cluster financial signals. Different ASTs may
produce identical or closely related signals. AST counts are not counts of
novel financial ideas or independent tests.

The two common initial probes occur once per period: `common_initial_probe_count`
is 20. Their repeated presentation across 30 episodes produces 60
`initial_probe_entries_across_episodes`. Those entries are shared observations,
not 60 independently generated probes, and are not charged proposals.

## First proposal and supplied prompt identity

For each period the report retains each arm's first charged expression, its
grammar status, canonical AST, and supplied prompt SHA256. It separately reports
exact expression-string equality and canonical-AST equality across all three
arms and each pair. There is no whitespace normalization of expression strings.
For example, `returns` and `(returns)` differ as strings but share a canonical
AST. A comparison involving an invalid first proposal is `null`, not a match
or a difference. Aggregate matches, differences, and unavailable counts retain
all ten periods.

Identical supplied prompts are checked independently of formula matching.
The replay gate already requires the common first prompt for all three arms
within each period. Its hash says nothing about unobserved host context,
server weights, randomness, or the amount of hidden computation. Formula
agreement under the same supplied prompt is descriptive, not evidence that
all actor contexts were identical.

## Saved historical comparisons

Every episode includes the selected proposal's absolute saved historical IC,
the best usable common initial probe's absolute IC, and the first charged
eligible proposal's absolute IC. The first eligible proposal can occur after
attempt 1 when earlier proposals were invalid or unusable. The benchmark from
initial probes uses the overall saved probe feedback, not the three window
scores; an unusable probe is excluded even if its recorded IC is large. Probe
ties retain the first listed probe. Zero remains a valid value.

The report computes the selected absolute IC minus each of those two
benchmarks. A missing selection or benchmark yields `null`. Summary fields
state the full episode denominator, available and unavailable counts, and the
mean/minimum/maximum among available values. They do not silently convert
missing comparisons to zero or drop episodes from the declared denominator.

These are comparisons of **in-sample historical maxima**. The selector already
maximizes absolute historical IC over its usable proposed pool, so its value
cannot be smaller than the first eligible proposal's value. A positive
difference alone does not establish feedback adaptation, useful exploration,
out-of-sample improvement, profitability, or causal benefit. The common initial
probes and actor-generated pool also have different construction and sizes.
No model-text causal classifier or additional hypothesis test is applied.

## Resource reports and reproducibility

Every known token field is retained separately, including input, cached input,
cache-write input, output, and reasoning output. Each has a reported sum,
reported/missing decision counts, and a `complete_sum` that is null if any
decision lacks the field. Missing usage is not zero. Reasoning tokens are never
added to output tokens, and cached input is not interpreted as an additional
independent token budget. Elapsed sums, minima and maxima describe saved
per-call durations; the sum is not concurrent study wall-clock duration.

The report identifies the exact input bytes, diagnostics/replay module bytes,
and frozen source/plan identities. Its canonical body digest binds all saved
counts and metadata. It adds no generation timestamp, so identical input and
source bytes produce identical report content. Status
`POST_HOC_TRACE_BOOKKEEPING` is separate from the embedded replay result
`STRUCTURALLY_VERIFIED`; `financial_scores_recomputed` and
`assessment_artifact_read` remain false.

Saved feedback is accepted as evidence. Neither bookkeeping nor replay
independently verifies its market calculation, original private streams,
publication timing, or hidden actor context. The author checks use synthetic
fixtures only; their counts and feedback values are not experimental results.
