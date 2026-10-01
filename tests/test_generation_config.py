"""Effective Hugging Face sampler law checked on tiny random CPU GPT-2."""

import copy
from types import SimpleNamespace

import pytest

from alpha_research_rl.llm import LocalActor

torch = pytest.importorskip("torch")
transformers = pytest.importorskip("transformers")


def tiny_actor():
    model = transformers.GPT2LMHeadModel(transformers.GPT2Config(
        vocab_size=8, n_positions=32, n_embd=8, n_layer=1, n_head=1,
        bos_token_id=0, eos_token_id=7, pad_token_id=7,
    )).eval()
    # Match the local model's non-global defaults, including a saved version
    # that causes Transformers to merge model defaults unless disabled.
    model.generation_config = transformers.GenerationConfig(
        do_sample=True, temperature=.6, top_k=20, top_p=.95,
        bos_token_id=0, eos_token_id=7, pad_token_id=7,
    )
    model.generation_config.transformers_version = "4.57.6"
    actor = object.__new__(LocalActor)
    actor.model = model
    actor.tokenizer = SimpleNamespace(decode=lambda tokens, skip_special_tokens: '{"action":"stop"}')
    actor.prompt_ids = lambda observation: [1, 2]
    actor.greedy_config = transformers.GenerationConfig(do_sample=False, eos_token_id=7, pad_token_id=7)
    actor.sampling_config = transformers.GenerationConfig(
        do_sample=True, temperature=1., top_k=0, top_p=1., eos_token_id=7, pad_token_id=7,
    )
    return actor


@pytest.mark.parametrize("stochastic", [False, True])
def test_local_actor_effective_config_is_not_overridden_by_model_defaults(monkeypatch, stochastic):
    actor = tiny_actor()
    prepared = []
    original = actor.model._prepare_generation_config

    def capture(generation_config, use_model_defaults=None, **kwargs):
        config, model_kwargs = original(generation_config, use_model_defaults, **kwargs)
        prepared.append(copy.deepcopy(config))
        return config, model_kwargs

    monkeypatch.setattr(actor.model, "_prepare_generation_config", capture)
    actor.sample({}, stochastic=stochastic, max_tokens=1)
    assert prepared[-1].do_sample is stochastic
    if stochastic:
        assert prepared[-1].temperature == 1.
        assert prepared[-1].top_k == 0
        assert prepared[-1].top_p == 1.


def test_actual_stochastic_generation_scores_equal_raw_full_softmax_logits(monkeypatch):
    actor = tiny_actor()
    captured = []
    original = actor.model.generate

    def scored_generate(*args, **kwargs):
        output = original(*args, **kwargs, return_dict_in_generate=True, output_scores=True)
        captured.append(output)
        return output.sequences

    monkeypatch.setattr(actor.model, "generate", scored_generate)
    with torch.no_grad():
        raw = actor.model(input_ids=torch.tensor([[1, 2]])).logits[:, -1].float()
    actor.sample({}, stochastic=True, max_tokens=1)
    scores = captured[0].scores[0].float()
    assert torch.isfinite(scores).all()
    # Temperature or top-p inherited from the model changes these scores;
    # equality verifies the actual generation law, beyond inspecting config.
    torch.testing.assert_close(scores, raw, rtol=1e-5, atol=1e-6)
    torch.testing.assert_close(scores.log_softmax(-1), raw.log_softmax(-1), rtol=1e-5, atol=1e-6)
