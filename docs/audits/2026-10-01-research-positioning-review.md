# Independent research-positioning review

Reviewed 2026-10-01 UTC. Scope: contribution claims, prior-method distinctions,
and the evidence required for stronger conclusions. This is a documentary
review, not an independent rerun of training, market scoring or external systems.
No experiment, model call, paid service or Git mutation was performed.

The review read the README, financial results and training audit, sampler audit,
constructed-curriculum result, sequential-gate result, and reward-linkage plan.
The resulting [positioning document](../research-positioning.md) distinguishes
the environment, the trained single-action financial actor, unestablished
sequential competence and the separate numerical forecasting task.

Resolved reporting risks:

- Reward gains are reported with failure-count contributions and the failed
  uniform-grid comparison; the residual is not called causal financial learning.
- Development years, shared training history and dependent periods are explicit.
- Both failed branches remain stopped. Suggested future questions require new
  protocols and do not authorize continuation or tuning against inspected data.
- The paper-level comparisons avoid claiming RL formula search or LLM alpha
  selection as new. No common-benchmark superiority is asserted.

Primary-source verification checked [RD-Agent-Quant](https://arxiv.org/abs/2505.15155v2)
and its [official repository](https://github.com/microsoft/RD-Agent),
[Alpha-R1](https://arxiv.org/abs/2512.23515v2) and its
[training notes](https://github.com/FinStep-AI/Alpha-R1/blob/main/training/README.md),
and [AlphaGen's official repository](https://github.com/ICT-FinD-Lab/alphagen).
The comparison preserves two versioning details: RD-Agent currently includes
fine-tuning scenarios, and AlphaGen includes later LLM/HARLA extensions. It does
not infer absence of those capabilities from the original quant/symbolic methods.
Alpha-R1's reference reward implementation is not treated as an independently
reproduced full training pipeline. The existing AlphaAgentEvo OpenReview link
returned a browser challenge, so no new detailed claim about it was added.

No blocking contradiction was found in the conservative completed-study
positioning. Reward-permutation control outcomes were not used in this review;
they require their own saved-result analysis and cannot retroactively make the
original comparison preregistered for that mechanism question.
