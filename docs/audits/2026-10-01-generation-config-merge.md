# Generation-config merge finding

During the first curriculum baseline evaluation, Transformers 4.57.6 warned that
model defaults replaced intended configuration values with `do_sample=True`,
`temperature=0.6`, `top_k=20`, and `top_p=0.95`. The supplied fresh greedy
`GenerationConfig` had default-valued fields; `_prepare_generation_config` fills
these from model defaults when `use_model_defaults` is unset and the saved model
version is at least 4.50. This makes a manifest marked greedy inaccurate. A fresh
stochastic config can similarly lose temperature 1/top-p 1, breaking the declared
full-softmax likelihood contract.

The affected baseline output and its constructed data are preserved, with an
explicit supersession note, under the ignored curriculum run's `diagnostics`
directory. They must not be used as the planned greedy comparison. No financial
RL had run after this configuration refactor. The earlier v1 direct sampler kwargs
protected its specified values; the 384 curriculum SFT updates are teacher forced
and unaffected by sampling.

The corrected actor passes `use_model_defaults=False` and explicit sampler kwargs.
`tests/test_generation_config.py` uses a tiny random CPU GPT-2 with the same model
defaults to inspect the effective greedy/stochastic configuration and compare
actual stochastic generation scores against raw next-token full-softmax logits.
Corrected curriculum evaluations follow those CPU checks. No model download or
financial interpretation is involved in the regression fixture.
