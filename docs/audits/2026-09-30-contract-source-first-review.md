# Source-first research contract review

Reviewer: research/protocol subagent. Date: 2026-09-30. Reviewed `AGENTS.md` and `docs/IMPLEMENTATION_CONTRACT.md` before any numerical result or proposed performance conclusion. This is a contract/design review, not an implementation audit or independent reproduction.

## Findings and integration requirements

| ID | Finding | Status at review |
| --- | --- | --- |
| R01 | Fixed screen/stability/select actions test candidate selection, not generation; controllers are not LLM post-training. | Root acknowledged selection scaffold only and plans validated proposal/mutation plus actual SFT/RL. Documentation distinguishes stages; implementation pending. |
| R02 | Official industry data contain returns, not stock prices/volume. Fabricated volume or stock-alpha framing would invalidate provenance. | Root plans returns/wealth-only adapter with explicit feature availability. Downloader bytes/parser still require verification. |
| R03 | An interval gap alone does not establish label purging. Every t+h realization must remain in its own partition. | Required edge assertions/tests; not yet code-reviewed. |
| R04 | Nonfinite/low-coverage scores, unspecified sign fallback, changing valid-date masks, and assessment-derived combination weights can alter the objective or leak labels. | Freeze reward eligibility, acquired-feedback orientation, masking, ranks, and costs. Recommended successful screen before selection. Implementation pending review. |
| R05 | Assessment reward is training data whenever used by the optimizer. Initial smoke outputs cannot become untouched holdouts retrospectively. | Contract already correct; protocol adds explicit cross-episode freeze manifest and post-result revision rules. |
| R06 | Overlapping forward targets and market episodes are dependent; reward optimization is not statistical error control. | Protocol requires overlap reporting and time-aware descriptive uncertainty or preregistered inference. |
| R07 | Invalid/duplicate proposals, repeated terminal steps, semantic aliases, and hidden debug outputs can game or leak reward. | Contract charges invalid attempts; implementation must verify all paths and observation/info isolation. |
| R08 | A tiny parameter update establishes machinery only. A positive learning claim needs saved changed actor weights and frozen base/SFT/RL comparisons. | Protocol specifies trajectory/logprob/reward/optimizer/checkpoint evidence; training implementation pending. |
| R09 | Public availability does not imply permission to relicense market data. Revised source histories are not point-in-time vintages. | Downloader-only policy and snapshot provenance specified in `docs/data-sources.md`. |

## Source verification

Official Ken French library/details pages were accessible and disclose copyright, daily industry coverage, annual SIC assignment, and retrospective revisions. The official daily ZIP link was identified, but the web reader could not render binary bytes; this review has not certified the actual download, table parsing, or SHA256.

Qlib's official README currently marks its official dataset temporarily disabled. Binance's official dataset terms dated 2026-08-26 require noncommercial CC BY-NC-SA treatment and govern derived outputs; repository MIT wording must not be used as blanket data permission. Exact primary URLs and dates are recorded in `docs/data-sources.md`.

## Resolution boundaries

No code, Git state, external publication, private material, paid resource, numerical experiment, or model weights were modified by this review. Findings marked pending require root integration and a later source-first implementation audit. Documentation is not proof that code satisfies these requirements.
