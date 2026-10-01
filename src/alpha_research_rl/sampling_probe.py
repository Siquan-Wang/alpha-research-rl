"""Measure actual cached-generation versus full-forward token likelihood numerics."""

import argparse

from .artifacts import run_manifest, write_json
from .financial_policy import ProposalActor, load_pinned_panel
from .financial_tasks import make_task
from .training import seed_everything


def check_sampling(model_path, panel_path, output, adapter=None):
    import torch

    seed_everything(71)
    manifest = run_manifest({"probe": "real-model cached sampling and full-forward likelihood",
                            "seed": 71, "max_new_tokens": 24})
    actor = ProposalActor(model_path, adapter)
    task = make_task(load_pinned_panel(panel_path), 2002, 1)
    prompt = actor.prompt_ids(task.observation())
    inputs = torch.tensor([prompt], device=actor.model.device)
    with torch.no_grad():
        generated = actor.model.generate(
            input_ids=inputs, attention_mask=torch.ones_like(inputs),
            generation_config=actor.sampling_config, use_model_defaults=False,
            do_sample=True, temperature=1.0, top_p=1.0, top_k=0,
            max_new_tokens=24, return_dict_in_generate=True, output_scores=True, output_logits=True,
        )
        completion = generated.sequences[0, len(prompt):]
        processed = torch.stack(generated.scores)[:, 0].float()
        raw_cached = torch.stack(generated.logits)[:, 0].float()
        logits = actor.model(input_ids=generated.sequences, use_cache=False).logits
        full = logits[0, len(prompt)-1:-1].float()
        score_lp = processed.log_softmax(-1).gather(1, completion[:, None]).squeeze(1)
        full_lp = full.log_softmax(-1).gather(1, completion[:, None]).squeeze(1)
    processing_difference = float((processed-raw_cached).abs().max())
    discrepancy = (score_lp-full_lp).abs()
    report = {"manifest": manifest, "actor": actor.provenance,
              "task": task.public_manifest, "prompt_ids": prompt,
              "completion_ids": completion.tolist(), "completion_tokens": len(completion),
              "processed_vs_raw_cached_max_logit_difference": processing_difference,
              "generation_logps": score_lp.tolist(), "full_forward_logps": full_lp.tolist(),
              "max_token_logp_difference": float(discrepancy.max()),
              "mean_token_logp_difference": float(discrepancy.mean()),
              "absolute_sequence_logp_difference": abs(float(score_lp.sum()-full_lp.sum())),
              "interpretation": "Processed/raw equality tests the full-softmax sampler; cached/full discrepancy measures finite-precision kernels, not a changed temperature or truncation law."}
    write_json(output, report)
    if processing_difference != 0.0:
        raise AssertionError("A logits processor changed the intended untruncated sampling distribution")
    if not torch.isfinite(discrepancy).all() or float(discrepancy.max()) > 0.25:
        raise AssertionError("Large cached/full numerical discrepancy requires investigation before RL")
    return {key: value for key, value in report.items() if key in {
        "completion_tokens", "processed_vs_raw_cached_max_logit_difference", "max_token_logp_difference",
        "mean_token_logp_difference", "absolute_sequence_logp_difference"}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/Qwen3-0.6B")
    parser.add_argument("--input", default="data/raw/french49-v1/49_Industry_Portfolios_daily_CSV.zip")
    parser.add_argument("--adapter")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(check_sampling(args.model, args.input, args.output, args.adapter))
