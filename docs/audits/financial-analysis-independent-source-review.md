# Independent financial-analysis source review

Reviewer: data/evaluation agent. Scope: `financial_analysis.py`, its tests, and
`docs/financial-analysis-plan.md`. Review occurred before any actual transfer
outputs were available or inspected. No market outcomes, GPU work, or changes
to the seven frozen scorer-contract source files were used.

## Verified findings

- The 18 original artificial-fixture tests passed independently.
- Fixed proposal-slot counts make the pooled reward calculations equivalent to
  equal weighting of the ten half-years and of two halves within each year.
- Failure-penalty and all-proposal predictive-contribution decomposition is
  algebraically correct. All-invalid cells preserve -1.01 reward and null
  conditional IC. Conditional usable IC remains a secondary metric.
- The analysis preserves both RL roles, every signed task/year effect, exchanged
  evidence effects and grounding interactions. Across-seed min/max is explicitly
  descriptive rather than a confidence interval or best-seed selection.
- Prompt-token matching, per-slot RNG schedules, EOS/schema validation, strict
  versus same-completion fence reparsing, frozen checkpoint identities and
  relevant prompt/scoring contracts are checked. Saved display summaries are
  ignored in favor of individual outcomes.

## Finding requiring resolution

P2: task chronology fields were compared across checkpoints but were not
validated against their named half-year or the post-2024 exclusion. Successful
outcomes' `n_signal_dates` was also not tied to the task's purged signal bounds.
An original artificial-suite fixture still returned `integrity.validated=true`
after every checkpoint's task assessment dates were changed to January–June
2025 and every valid feedback/assessment result was changed to one valid day
out of one signal day. This did not involve real transfer results.

The finding was sent to the analysis owner before edits and is resolved. The
owner added checks for raw/purged bounds, exact five-session purging, adjacent
feedback/assessment blocks, preceding/current calendar half-year containment,
endpoint ordering/coverage, the post-2024 cap and period lengths. Supplied
feedback/assessment metrics must now match the task's purged signal lengths.
Full artificial task manifests and shared-invalid-date, boundary/purge and
fabricated-short-support rejection tests were added.

The reviewer independently read the revised source and ran all 25 analysis tests
and Ruff: both passed. No unresolved blocking finding remains in the reviewed
source and tests. The seven frozen scorer-contract files were not edited.

## Limits

The reviewer verified source and artificial tests, not actual checkpoint training
lineage or decoded tokenizer contents. Report analysis remains a descriptive
development comparison and does not establish financial independence, alpha,
profitability or final-holdout generalization.
