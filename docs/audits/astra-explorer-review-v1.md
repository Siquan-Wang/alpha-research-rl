# Astra evidence explorer: source-first review

Reviewed on 2026-10-01. This is an [internal AI-assisted review](README.md),
not external peer review. The reviewer did not author `astra_explorer.py`, its
original tests, or its guide. The reviewer authored `astra_replay.py`, so the
replay verifier itself is not independently audited by this review. Source
inspection preceded the additional renderer regression cases.

Scope: the explorer's evidence binding, complete record display, observation
boundaries, model-text rendering, and scientific claims. All new checks use
synthetic submissions and saved synthetic feedback. No model, network, market
data, real study outcome, browser, or assessment calculation was used. Root's
separate browser checks are not attributed to this reviewer.

## Findings and resolutions

1. **Verified bytes could differ from displayed bytes.** `build_payload` first
   called the path-based replay verifier, then independently reread submissions
   and assessment. Two regressions changed the original input immediately after
   successful replay. The builder embedded either 29 episodes instead of the
   verified 30, or an altered primary contrast, under the original verification
   result. **Repair requested:** capture each input's bytes once, validate exact
   temporary snapshots of those bytes, and decode the display payload from the
   same captured bytes. A second original-path hash alone does not address races
   within a verifier that performs multiple reads. **Resolved:** root captures
   all three public JSON inputs once, verifies byte-identical temporary copies,
   and constructs the display objects from those captured bytes. The reviewer
   inspected that data flow; both mutation regressions now pass.

2. **JSON-valid lone surrogates could prevent page creation.** A model-authored
   JSON string can contain escaped unpaired surrogate code points. Rendering
   with `ensure_ascii=False` produced a Python string that could not be written
   as UTF-8. A regression combines both surrogate values with mixed-case script
   closing text; the page must remain writable, keep exactly its two intended
   script blocks, and round-trip the data. **Repair requested:** ASCII-escaped
   JSON plus the existing HTML-delimiter escaping. **Resolved:** root changed
   serialization to `ensure_ascii=True`. The encoding, inert-script, and exact
   JSON round-trip assertions all pass.

3. **The history disclosure did not reproduce the recorded observation.** The
   displayed projection omitted `raw_response_sha256` and
   `raw_response_truncated`. Its JavaScript slice also counts UTF-16 code units,
   while the broker's 20,000-character limit counts Python Unicode code points.
   The regression compares the executed renderer's history with the actual
   broker observation for long ASCII text and a non-BMP character at the
   truncation boundary. **Repair requested:** precompute the broker-exact
   projection in Python, or explicitly label and document a partial projection.
   **Resolved:** root computes all six prior-history projections in Python,
   preserving the full response hash, code-point truncation and explicit flag.
   The UI consumes those projections. Both executed JavaScript cases exactly
   match the broker's observation, and the guide now explains this boundary.

The first four regression cases failed against the original renderer, as
expected: two input mutation cases, surrogate serialization, and long-ASCII
history. The Unicode truncation case extends the same history finding. These
are renderer issues; no protocol, frozen source, selector, or evaluator change
is requested. No unresolved blocker remains in the reviewed renderer scope.

## Other inspected boundaries

- The builder requires the full replay verifier before creating output. The
  verifier requires all 30 episodes and six decisions each, exact task/arm
  identities, complete transport summaries, matching record masks and prompt
  hashes, frozen selection consistency, and the saved assessment arithmetic.
  The immutable input binding added for finding 1 ties that result to the page.
- The renderer iterates every recorded proposal, including invalid, duplicate,
  and unusable records. It retains all ten paired periods, all five year
  averages, and all three contrasts. Missing token reports remain explicitly
  incomplete; reasoning tokens are not added to output counts.
- Current-proposal feedback is labeled as delivered after that proposal.
  Prior permitted history, private selector evidence, and final future
  assessment are separate disclosures. The final selection is identified as
  occurring after all six proposals even when an earlier attempt is selected.
- Model text is assigned through `textContent`. Embedded JSON escapes `<`, `>`,
  and `&`; there is no dynamic HTML sink, executable model text, remote asset,
  or data request in the reviewed template. Finding 2 concerns encoding and
  availability, not a demonstrated script-execution escape.
- The guide and page identify these periods as development data, preserve the
  fixed outcome denominator and abstract search cost, and avoid claims of
  profitable alpha, market generalization, causal attribution from public
  explanations, authenticated hidden reasoning, or Astra weight training.
  Backend identity and hidden host context remain unverified. Replay checks
  saved structure and arithmetic; it cannot itself prove market-score accuracy
  or the chronology of public publication and assessment.

## Validation record

Additional tests are retained in `tests/test_astra_explorer_review.py`.
The history check executes the trusted inline renderer with Node and a minimal
test DOM; it is not a visual browser or accessibility review. That check skips
explicitly if Node is unavailable. It ran successfully in this review.

After source inspection of root's repairs, the reviewer independently ran:

```text
python -m pytest tests/test_astra_explorer.py tests/test_astra_explorer_review.py -q -p no:cacheprovider
8 passed in 1.21s
python -m ruff check src/alpha_research_rl/astra_explorer.py tests/test_astra_explorer.py tests/test_astra_explorer_review.py
All checks passed!
```

The eight cases comprise the three original publication checks and five
additional regressions. They verify the stated repairs using synthetic
fixtures, without claiming real-data rescoring or browser visual validation.

| Reviewed file | SHA256 |
| --- | --- |
| `src/alpha_research_rl/astra_explorer.py` | `91709537b65cf470f496db080932ede37e96e202e5506256a50bb5834ac0c468` |
| `tests/test_astra_explorer.py` | `9485b00fb4d885b9f7edd5c1a29797b994155f2c415b3308d0f1547ab261d1ef` |
| `tests/test_astra_explorer_review.py` | `14dbac6ca7b0f7fbe2752bff9f6228e89fb6a9b740ac0ab8b5b21e1206f366b7` |
| `docs/astra-explorer-guide.md` | `fa42130fec2e71ce2cb35dfb187de7e083d85c43247baa404af3de56bba6f0fa` |

## Root follow-up: public CI must compare retained evidence exactly

This addendum is authored by root, not an additional independent review. The
review above concerned the renderer and retains its original reviewed hashes.
The guide subsequently gained a static-figure section; the renderer and its
eight reviewed tests did not change.

During the separate pool-diagnosis review, a reviewer identified arithmetic
tolerance being applied too broadly to retained report evidence. Root checked
the new public Astra CI wrapper and found the same class of issue in its HTML
payload comparison: a one-ULP edit to a copied metric could fall within the
numerical tolerance even though the embedded evidence no longer matched its
input exactly. No such change was present in the published page.

The wrapper now compares the complete embedded submissions, assessment and
permitted histories exactly. Only newly calculated verification arithmetic
retains the `1e-12` absolute tolerance. Five focused tests reject one-ULP
changes in each evidence section, unexpected sections and Boolean/int metadata
substitution, while allowing a computed elapsed-time rounding difference.
All five passed in 0.60 seconds. The full actual-bank wrapper also passed,
including its unchanged template and all 180/30 saved records; Ruff passed.
This strengthens the checker without altering a model response, market score,
study conclusion or the published HTML.
