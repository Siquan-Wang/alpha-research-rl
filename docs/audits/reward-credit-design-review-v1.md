# Reward-credit accounting: design and interpretation review

2026-10-01. Internal AI-assisted design review. This reviewer proposed the
saved-training question and authored the plan, so this is **not an independent
review of that plan**. Another agent authors the implementation; root and a
separate reviewer inspect it. The reviewer also participated in earlier project
designs/audits. No external peer review or new experiment is claimed.

The useful missing distinction is narrow: evaluation utility gains from fewer
failures do not establish how much direct validity credit training received.
The four published runs preserve enough information to reconstruct all 64
groups' reward channels, leave-one-out coefficients and sampled scalar
surrogates. Their per-sample score-gradient vectors and intermediate optimizer
states are not saved. Consequently, full gradient/update attribution is not an
identifiable extension of this analysis.

Source-first checks before the full-bank calculation:

- Read the training functions and public export structure, plus first-record
  schemas; did not calculate the complete population. The original trainer
  centers reward values on the first sample before leave-one-out subtraction,
  uses four unnormalized completion sequence log-probabilities, clips the total
  gradient at one and uses AdamW. The control trainer assigns all four rewards
  through its saved permutation before computing advantages.
- Independently read the two export byte hashes: original training
  `5cb85943a209183492df813cb63f372f05c9257bba254382957d41183a69cf17`,
  control training
  `e9143fb33680317cc8312410b7b078a849a9d26d7824e7770f29b7230fd3c80d`.
  The enclosed report hashes remain historical provenance, not hashes newly
  recoverable by JSON reserialization.
- Verified the algebraic scope: R=-1.01+V+C, common-permutation channel
  assignment, linearity of the leave-one-out map, and scalar surrogate
  additivity. The constant cost cancels. The squared coefficient decomposition
  requires its signed cross term; L1 coefficients and scalar losses do not
  determine gradient percentages.
- The plan includes a constructive nonidentifiability argument. When validity
  coefficients have a component orthogonal to total coefficients, varying the
  unobserved score gradients along that component preserves the entire total
  gradient but changes its proposed attribution. The construction is conditional
  on noncollinearity; actual groups must not be assumed to satisfy it. An exactly
  zero validity vector instead proves an exactly zero direct validity term for
  that recorded group, without proving pure financial skill.

Known summary counts suggest few mixed-validity groups; those prior results
motivated this post-hoc question. They are not hidden from the analysts and
should not be advertised as a surprising preregistered finding. The eventual
report must verify, rather than simply copy, the all-group counts and every
identity. Keep all original/control seeds, failed attempts and skipped groups.

The source/plan boundary is appropriate for a compact saved-JSON analysis:
no model or market imports, no new gradients, exact inputs, fixed finite
tolerance and failure on inconsistency. It does not warrant a new publication
gate, a general analysis framework or more model calls. Full implementation
review, artificial tests and the actual saved-result calculation are pending
at the time of this note.

Independent plan review requested three precision fixes, now included: training
assessment IC is explicitly training data; saved sequence log-probabilities must
be nonpositive; and frozen numeric settings use exact comparisons rather than
the 1e-12 reconstructed-arithmetic tolerance. These clarify the existing scope
and do not use new full-bank outcomes.

Before the first actual analysis, implementation review clarified two exact
evidence invariants. Outcome-to-group rewards and permutation-indexed assigned
rewards are retained copies, so they require exact numeric equality rather than
reconstruction tolerance. Exactly constant assigned rewards require exactly zero
logged advantages, preventing tiny tolerated noise from inventing an optimizer
step. Truly nonconstant tiny variation remains distinct. The plan now states
both explicitly; the arithmetic tolerance and population are unchanged. Root
reports the combined 64 artificial tests and Ruff passing; this design reviewer
did not run the full saved bank. These are pre-analysis wording clarifications,
not changes made after viewing the new result.

## Completed saved-result interpretation review

Root completed one saved-only analysis. This reviewer subsequently read the
result's population, all four run summaries, the two mixed-validity groups and
the skipped group, and verified the file SHA-256:
`59d31578928894581208c8928fd38690b839d0c12264c38e64779ffc19957cb7`.
The source and plan remain unchanged. This was read-only interpretation review:
no replay, model/gradient computation, market scoring or repeat of root's
independent arithmetic reconstruction.

| Role/seed | Groups / attempts | Usable attempts | Groups with nonzero validity credit | Actual updates |
| --- | ---: | ---: | ---: | ---: |
| Correct 23 | 16 / 64 | 63 | 1 | 16 |
| Correct 29 | 16 / 64 | 64 | 0 | 15 |
| Placebo 23 | 16 / 64 | 64 | 0 | 16 |
| Placebo 29 | 16 / 64 | 63 | 1 | 16 |

All 64 groups and 256 attempts are present. Exactly 62 groups have zero direct
validity-credit vectors, including the one constant/skipped correct-29 group;
thus **61 of 63 actual updates** have zero direct validity coefficients under
the registered decomposition. This resolves the narrow interpretive question:
evaluation gains mostly attributed to failure avoidance do not imply most
training groups had failure-penalty contrasts.

The two exceptions are correct-23 group 8 (`2004-H1`) and placebo-29 group 10
(`2011-H2`). Each has validity-coefficient L1 size 2; their IC-coefficient L1
sizes are respectively about .124143 and .174385. Their signed squared cross
terms have opposite signs (about −.106159 and +.159944), with respectively two
and one per-sample sign oppositions. These are descriptions of coefficients,
not gradient size, optimizer impact or learning shares. In particular, counting
61 zero-validity updates does not imply that the two remaining updates were
unimportant. Their recorded total norms cannot reveal component norms.

The failed sample in correct-23 group 8 receives C=0 while its valid peers have
negative training IC. Consequently its IC advantage is positive even though
its validity advantage is negative. This saved example makes the validity-gated
definition concrete: C is not a pure skill channel, and no zero-validity-credit
claim should be converted into a claim of financial learning. Placebo channel
credit is evaluated after its saved permutation and must not be described as
correct reward assignment to each formula.

Root separately reports a 60-digit Decimal reconstruction using direct sums of
the other three rewards, without project imports: 3,752 checked values across
all groups, maximum absolute discrepancy approximately 2.93e−16. That arithmetic
verification belongs to root's review, not this reviewer's work. The result also
records both pinned inputs and the final plan/implementation hashes, zero new
model/market calls and no recomputed gradients.

No interpretation blocker was found. The result supports a precise distinction
between **training credit** and **evaluation reward accounting**, while leaving
the original negative financial findings and gradient/update nonidentifiability
unchanged. It supplies no new sample, significance claim or reason to reopen a
stopped experiment.
