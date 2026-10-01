# Matched-prefix structural-lag and cheap-control review

Date: 2026-10-01. **Status: PASS for the targeted core checks below; no
concrete structural-boundary or deterministic-control mismatch found.**
This does not clear the durable driver, publication gates or experiment for
execution; those have separate reviews.

## Protocol-author validation, not independent protocol review

This reviewer authored `docs/astra-matched-prefix-plan-v1.md`. The reviewer
did not author `astra_revision_core.py` or its original tests. Accordingly,
this is a source-first check of a separately authored implementation against
the reviewer's protocol, **not an independent review of that protocol** or
external peer review. The separate design reviewer independently inspected
the protocol and fixed states. This lane does not duplicate its Q/G analysis
or the durable state-machine review.

The write scope was this new audit and
`tests/test_astra_revision_lag_review.py`. No frozen source, prior protocol,
bank, score or completed result audit was edited. No model, tokenizer, network,
Git, real market-data loader or financial task/evaluator was used. The only
factor evaluations here used explicitly artificial arrays through the frozen
DSL, without labels or IC scoring.

## Targeted evidence

The separate reviewer suite has **24 passing cases in 0.63 seconds**, and Ruff
reports no findings. The command was `python -m pytest
tests/test_astra_revision_lag_review.py -q -p no:cacheprovider`, with a fresh,
short, ignored repository-local basetemp. These are 24 cases, not 24 model or
market evaluations. No broad repetition of the unchanged author suites was
needed for this bounded task.

Eight grammar-valid forms check negative finite constants, stacked unary
operators, arithmetic with signed constants, a lag-60 delayed term inside a
unary/binary expression, hexadecimal and underscored integer windows, and
nested lag-61 cases. The old DSL accepts integer constants such as `0x3c` and
`6_0`; the new filter correctly computes their value without a stricter
decimal-only grammar. Delayed constants retain their declared structural
lag even when a smaller algebraic/semantic dependency could be inferred.

Seven contrasting window forms—`+60`, `-1`, `60.0`, `True`, `30+30`,
`int(60)` and a variable—are rejected by the original literal-positive-integer
window rule before structural lag is assigned. They retain their raw packet
and receive `invalid_expression`, not the new study-level lag failure. General
negative constants and a syntactically signed *window* are therefore handled
differently exactly as the frozen DSL requires.

Three tests check dependencies through artificial-data perturbation rather
than implementing another copy of the recursive lag calculation:

| Expression | Greatest tested dependency lag | New study eligibility |
|---|---:|---|
| `ts_mean(delay(returns,31),30)` | 60 | Eligible |
| `ts_std(delta(returns,31),30)` | 60 | Eligible |
| `delay(ts_mean(returns,30),32)` | 61 | Ineligible |

At a fixed interior output row, changing the input at the stated boundary
changes that output. Changing the next older input and a future input leaves
it exactly unchanged. All three remain grammar-valid in the unchanged DSL;
only the new study eligibility rejects the 61-lag expression. These finite
checks substantiate the specified `k-1` rolling-window versus `k` delay/delta
boundary without claiming an exhaustive proof over all expressions.

Six additional cases check deterministic control semantics:

- A scheduled edit of a nested temporal formula preserves its negative
  constant, inner window and all other syntax, starts afresh from the baseline,
  and does not mutate the supplied state. If the fixed edit changes lag 60 to
  61, it returns that single over-cap proposal without changing another window
  or searching for a replacement. The registered forty real-state edits were
  separately statically checked before this test; this adversarial artificial
  baseline verifies the no-repair behavior.
- Three hard-coded seed/digest/expression goldens check the raw-byte SHA256
  draw schedule, including a nested delayed mean, a negated branch, and equal
  rolling windows. These are not regenerated from the implementation's
  template choices to create their expected answers.
- The fixed equal-window subtraction is retained, remains grammar/lag
  eligible, and evaluates to zero on every complete artificial window. The
  generator does not redraw it in response to degeneracy. Historical/future
  usability belongs to the later broker, outside this test's scope.
- Copy retains the exact literal alias spelling, including parentheses and
  hexadecimal window notation, in each of four repetitions; it does not
  normalize the source expression into a different string.

The first local test run exposed a reviewer-fixture error: constant artificial
prices were inconsistent with the supplied artificial returns, violating
`MarketPanel`'s existing invariant. The fixture was corrected to compound the
prices consistently and retain its all-NaN first return row. The corresponding
rolling completeness assertion was adjusted accordingly. This was not a core
implementation finding or a change to the frozen data invariant. The final
24-case run above passed after that correction.

## Reviewed identities and remaining scope

| File | SHA256 |
|---|---|
| `src/alpha_research_rl/astra_revision_core.py` | `74c6f6b36406234b4ea5a004d6566356f6d5b47fa347e9e5ec1f68a2f538e0f5` |
| `tests/test_astra_revision_lag_review.py` | `9de485226be383caa1d2375fe77c0f845b6b3d11f524c4899793e9343761843b` |
| `docs/astra-matched-prefix-plan-v1.md` | `a0f5a5ede6f098c5a1c632ceb5ab6eae6ac449fcbf025ce72c94a2be0073f271` |
| Frozen `dsl.py` | `47c311c0d2b4074653789bf1275081a58517822d0f1fc0a6fb811fd796e8ba97` |
| Frozen `data.py` | `21be3b5df887acdfc97d3ebfe2b191c91db2f647f44516d9f5c987e33f39b48c` |

No core source repair was requested by the lag/control review. The internal `dependency_lag`
helper explicitly assumes an already validated AST; the tested public proposal
validator applies the old grammar first. The new restriction is a study-level
structural bound, not a modification of the old scorer, an economic usefulness
test, or a physical memory/read sandbox. Passing these tests does not establish
proposal quality, statistical power, successful provider execution, complete
quota enforcement or correct held-output assessment. Those claims require
their own evidence and must not be inferred from this protocol-author check.

## Supplemental public-receipt helper review and resolved finding

Root subsequently requested source review of
`scripts/verify_astra_revision_publication.py`, authored and edited by root.
The reviewer found and reproduced a concrete Windows path-boundary issue:
with an artificial file under lowercase `.local`, an expected public path
spelled `.LOCAL/fixture.txt` passed the helper's case-sensitive deny list,
resolved to that same local file, and produced a receipt after two fake fetch
responses. No real network or private user data was accessed in the reproducer.
The driver's independent complete-map validation remained a separate gate;
this finding did not demonstrate a bypass of the full execution protocol.

Root repaired the helper to casefold denied directory components, reject
trailing spaces/dots that form Windows aliases, and check resolved relative
components after confirming repository containment. The reviewer inspected
those changes and independently ran the updated fake-fetch helper suite:
**21 passed, 1 skipped in 0.69 seconds**. The directory-symlink regression was
skipped because this Windows host lacks permission to create that symlink;
its rejection branch received source inspection, not a claimed successful
local runtime test. The regression can run on a host supporting the operation.

The helper obtains the required map from the driver's reconstruction, checks
all local hashes, verifies public commit identity and every fetched file, then
rechecks local bytes before exclusively creating the receipt. A mismatch or
fetch error creates no success receipt; `xb` prevents receipt overwrite. The
helper alone does not establish that an arbitrary caller-supplied map is the
complete study map: the CLI constructs it through the driver, and execution
must independently revalidate exact coverage and committed bytes. That is the
intended two-layer boundary, not a security-sandbox claim.

The Windows case issue is resolved in reviewed helper SHA256
`6fc8f8f5887ed798b328823b5f8981fb5f619e7d38710ee26d4061b072f46da7`.
The reviewed helper-test SHA256 is
`cdf3102cb06947df18d0235edd333d40d7b8d4e9659428097d4954f6f52e145e`.
No additional helper defect was found in this bounded review. These 21 passing
cases and one platform skip are separate from the 24 core cases above. No
actual publication fetch, preparation, hosted response or assessment was run.
