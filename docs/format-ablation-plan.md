# Frozen format-tolerance development ablation

Written before running any GPU evaluation with the new parser.

Motivation: the initial base-model strict evaluation produced 60 invalid actions
because its complete JSON objects were wrapped in Markdown fences. The strict
evaluation remains unchanged and remains an observed result. This additional
controlled ablation asks whether the apparent improvement after SFT/RL can be
explained by output formatting rather than better sequential research choices.
This design follows inspection of development behavior; it is not a preregistered
final test and cannot supply untouched-holdout evidence.

The original `llm.parse_action`, model prompts, training losses, rewards and
strict evaluator remain unchanged. A separate parser accepts one terminated
completion in either of two forms: a whole JSON object, or one whole block
beginning exactly with lowercase ` ```json ` followed by a newline and ending
with a newline plus ` ``` `. Outer whitespace and CRLF newlines are permitted.
No explanatory prose, trailing text, second JSON object, unlabeled fence,
alternate fence tag, or truncated completion is accepted. The body must decode
to a dictionary. The same JSON decoding semantics as the existing strict parser
are retained; this is a container-format ablation, not a replacement action
schema. JSON formatting acceptance and environment action validity are logged
separately. Malformed or unsupported research actions still consume budget.

Apply this exact parser to base, SFT, and RL checkpoints. Use the six existing
development tasks from `llm_evaluation.TASKS`: seeds 11000–11005, cycling signal,
null and decay synthetic regimes. Keep seed 31, greedy decoding, 64 generated
tokens per action, the existing three initial factors, generation-enabled
environment, budget 10, and the existing chronological split/reward identical.
Require EOS termination before accepting either format; preserve raw completion,
termination flag, parsed action, accepted format/failure, environment status,
selected IDs, action history, budget spent and terminal reward. Every action
also records what the unchanged strict parser would receive for that completion.

Models/adapter weights are loaded locally. There is no optimizer, gradient,
retraining, prompt revision, output repair beyond the single whole fence, or
actor-specific parser setting. Test the parser and rollout mechanics with CPU
fake actors first. Root explicitly schedules GPU evaluation to avoid interfering
with concurrent training. The runner emits a separate report per checkpoint;
compare those reports with the original strict reports, retaining both.

Report mean terminal reward, invalid/duplicate actions, accepted proposals,
format acceptance counts, and environment research-action counts. Format-only
acceptance does not establish research quality, and matching or exceeding SFT/RL
after fence tolerance would weaken a format-confounded research-learning claim.
Trajectories may diverge after the first recovered action because observations
change; this is a controlled parser-policy interaction ablation, not a claim
that one can replay complete strict trajectories into identical observations.
All tasks are synthetic development data; no market-alpha or final-generalization
claim follows from any result.
