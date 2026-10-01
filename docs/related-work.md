# Related work and positioning

The [focused design comparison](agentic-research-design-context.md) examines
feedback identification, generator/selector controls and reproduction limits
in accessible primary sources. It distinguishes verified methods from an
OpenReview access limitation and from unadopted experiments in this repository.

These are research references, not claims that this project originated their
ideas. The implementation here was written for this repository; no unlicensed
source or proprietary trading data is incorporated.

| Work | Relevant contribution | Boundary for this project |
| --- | --- | --- |
| [Microsoft RD-Agent](https://github.com/microsoft/RD-Agent) | Automated proposal, coding, feedback and quantitative R&D loops | An agent loop alone is not evidence of LLM gradient training |
| [Qlib](https://github.com/microsoft/qlib) | Financial ML data, models, training and evaluation infrastructure | Data availability and permissions must be verified separately |
| [AlphaGen](https://github.com/ICT-FinD-Lab/alphagen) | RL construction of formulaic alpha expressions | Symbolic RL is relevant prior art; it is distinct from post-training a pretrained LLM |
| [QuantEvolver](https://github.com/QuantLLM/QuantEvolver) | Evolutionary quantitative research and reinforcement fine-tuning interfaces | Public scaffolding does not automatically reproduce the complete reported pipeline |
| [Alpha-R1](https://github.com/FinStep-AI/Alpha-R1) | LLM RL for adaptive alpha selection | Adaptive alpha selection with LLM RL is existing work, not a novelty claim here |
| [AlphaAgentEvo](https://openreview.net/pdf?id=lNmZrawUMu) | RL of a tool-interacting alpha researcher | Tool-based alpha-research policy learning has direct prior art |
| [Kronos](https://github.com/shiyu-coder/Kronos) | Generative numerical financial time-series modeling | A numerical forecasting backbone would be a separate extension, with its own training study |
| [Qwen3](https://huggingface.co/Qwen/Qwen3-0.6B) | Open causal language-model backbone | Model license/revision recorded separately from this repository's code |

The practical aim is a small, reproducible, auditable study of **what a research
policy learns under a finite experimental budget**, including failures. The
strongest possible contribution would be supported empirical findings about
sequential evidence acquisition and robust generalization. That remains to be
established. Reproducibility and careful protocol design are engineering strengths,
not proof of research novelty.
