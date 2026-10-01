# AlphaResearch-RL working rules

- Work only inside this repository. Never read or publish private interview, resume, employer, credential, or personal workspace files.
- The user authorized autonomous iteration, subagents, and creation/pushing of a public GitHub repository. Use only existing/free resources; no purchases, paid APIs, quota resets, or paid cloud compute.
- Keep data provenance and code attribution explicit. Do not redistribute downloaded market data or model weights without verified permission. Synthetic data must always be labeled synthetic.
- One primary research target: train and evaluate a sequential alpha-research policy. A controller experiment is not evidence of LLM post-training; report these separately.
- Training rewards, development scores, and final chronological evaluation are distinct. An assessment used for gradient updates is training data even if absent from the prompt. Never optimize on a reported final holdout; create a new clearly versioned study if design changes after looking at it.
- Do not promise alpha, profitability, statistical error control, or novel research without evidence. Log null results and failed experiments.
- Use deterministic seed manifests, finite evaluation budgets, and record invalid/duplicate proposals. No unrestricted execution of generated Python; use a validated expression grammar.
- Subagents own disjoint files. Root integrates, runs checks, reviews publication contents, and alone commits/pushes. Keep independent review findings in docs/audits/.
- Checkpoint after meaningful milestones. Record observed results, commands, environment, limitations, and next steps in CHECKPOINT.md. Avoid cosmetic iterations or redundant testing merely to consume usage.
