# How the revision texts use visible evidence

**Secondary interpretation after coding; no current future results inspected.**
This note explains observable patterns in the 80 final responses. It uses only
the [restricted prompt/response export](../../artifacts/astra-revision-grounding-v1/inputs.json)
and [frozen coding](../../results/astra_revision_grounding_v1.json). It changes
neither that coding nor the experiment. The examples below were selected for
explanatory value after all packets were reviewed, not as a representative sample
or an additional prospective endpoint.

The strongest supported account is that the public rationales translate supplied
scores into comparisons, formula edits and explicit uncertainty statements.
That is observable evidence use in the text. It does not identify the hidden
process that generated the formula or establish that the proposed edit helps.

## Four useful distinctions for the research report

**A historical selection calculation is different from a new prediction.**
In `2020-H2/truthful/2`, the actor proposes the unchanged 20-session probe. Its
revision says the historical IC of 0.046759 exceeds the two prefix values
0.030196 and 0.042878, so “it would win the specified historical selector.”
All three are positive and usable, and the proposed probe becomes selectable
under the instructions. The deduction follows from visible facts. The response
also records the negative last historical window and uncertainty about later
persistence. This is a correct use of the selection rule, not evidence of a
newly discovered signal or a favorable future outcome. Source: input
`/records/9`, decoded `revision`; its prompt's 20-session probe feedback,
`candidate_feedback`, and selector instruction.

**Combining successful-looking components is a hypothesis, not an evaluated
combination.** In `2021-H2/truthful/1`, the text combines the baseline subtraction
from the prefix with IC 0.07287858 and volatility scaling from the other prefix
with IC 0.05808266. The submitted expression actually applies that scaling to
the spread, and the response explicitly says the combination is untested.
The corresponding masked response instead submits the directly observed
five-session mean, citing its probe evidence and the missing candidate reports.
These packets illustrate two stated revision strategies from the same start;
they do not prove that the feedback package caused this particular difference
or that composition is superior. Sources: `/records/24` and `/records/28`,
decoded `expression`/`revision`, with their respective prompt fields.

**Knowing which prefix scored better does not reveal why it worked.**
In `2024-H1/truthful/2`, the actor retains the skipped-week reversal with
historical IC 0.07018 rather than the alternative at 0.03721, then changes its
volatility denominator. The text calls the blended denominator an untested
hypothesis and notes that no candidate-level chronological breakdown was
supplied. That distinction is accurate: the candidate bundles have aggregate
metrics; the common initial probes have window summaries. A plausible
stabilization story cannot substitute for measurements of the proposed
denominator. Source: `/records/65`, decoded `hypothesis`/`revision`,
`candidate_feedback`, and the two probe records.

**Masking candidate reports still leaves meaningful numerical evidence.**
All 40 masked responses explicitly acknowledge missing candidate feedback in
their revisions. They can nevertheless cite the common probes and apply the
supplied sign rule. For example, `2024-H2/masked/2` submits the raw five-session
mean and explains that the broker orients its negative historical IC toward
reversal. No unavailable candidate measurement is needed for that deduction.
The separate known 2023-H1 sign-flip alias also makes some masked candidate
information inferable, whether or not a response chooses to report it. Source:
`/records/77`, decoded `hypothesis`/`revision`, the five-session probe and broker
instruction; the alias limit is specified in the frozen protocol.

## Why the response patterns deserve restraint

A simple secondary count across all 80 exact expression strings finds **8/40
truthful and 17/40 masked** responses that submit one of the two initial probes
verbatim. This is a literal match count, not semantic equivalence, novelty or
performance. Such a submission is allowed and consumes its attempt. In 2023-H2,
all four responses in each condition choose the same 20-session probe, despite
their different access to candidate metrics. More displayed information does
not guarantee a different formula. Conversely, different strings can describe
the same algebraic score, as the two spellings of the baseline-adjusted reversal
in 2023-H1 demonstrate. Neither count is an effect estimate.

The [audit report](astra-revision-grounding-results-v1.md) retains five
ambiguities rather than manufacturing a clean/failed binary. They concern an
undefined comparative persistence claim, two interpretations of window variation
as regime sensitivity, and two formula-description ambiguities. Historical
variation supports caution; it does not by itself identify a regime mechanism.
A terse formula summary can admit both a correct and an incorrect operation
order. Preserving those alternatives is more defensible than guessing intent.

## What this audit contributes—and cannot settle

The coding supplies inspectable evidence that the visible texts usually match
their supplied numbers, source availability and expression structure. It also
shows repeated acknowledgement that proposed combinations remain unmeasured.
The useful scientific distinction is **textual consistency versus predictive
usefulness**: the latter must come from the separate frozen Q/G assessment and
its cheap controls, irrespective of how plausible the prose sounds.

The review does not test hidden reasoning, causal reliance on a cited number,
actual absence of unobserved tool use, long-horizon agency, originality or Astra
weight learning. A model can provide a coherent rationale after choosing a
formula by some other route. The prompt explicitly asks for evidence references
and uncertainty, so those behaviors are also instruction following; they are not
a surprise mechanism discovery. No rationale score enters selection or allocation.

These are internal AI judgments from the protocol author, with no independent
human semantic calibration. The validator checks quote/hash/reference integrity,
not correctness or exhaustiveness of interpretation. Claim segmentation and
verbosity affect counts; zero coded fabricated reports is not a certified zero
error rate. Earlier v1/pool outcomes were already known and the market periods
are reused development data. The operational blinding claim is only that no
current-study outcome artifact was consulted before coding or for this note.
It is not a guarantee of ignorance of every previously evaluated formula.
