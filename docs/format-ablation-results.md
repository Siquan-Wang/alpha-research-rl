# Whole-fenced-JSON development ablation results

All three planned checkpoints were evaluated sequentially offline with identical
six synthetic development tasks, greedy decoding, 64 action tokens, budget 10,
and the same narrow whole-fence parser. No checkpoint was retrained. Original
strict-parser reports remain unchanged. Reports are
`artifacts/development/{base,sft,rloo}-format-v1.json`.

| Checkpoint | Mean terminal reward | Actions | Invalid | Duplicate | Accepted proposals | Format acceptance |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Base | -0.006333 | 44 | 26 | 6 | 0 | 33 whole JSON fences; 11 unterminated |
| SFT v1 | 0.032833 | 42 | 0 | 0 | 6 | 42 strict JSON objects |
| RLOO v1 | 0.032833 | 42 | 0 | 0 | 6 | 42 strict JSON objects |

The base model recovered one valid screen and one valid stop per task, but
selected no factor and proposed none. Its 26 invalid actions comprise 11
unterminated completions and 15 stop dictionaries with unsupported extra
`reason` fields; six additional repeated screens were duplicates. Its reward
improvement from the original strict result (-0.010000) is entirely less spent
budget with an empty selected pool. Fence tolerance therefore recovers some
action validity, not predictive utility.

SFT and RLOO produced exactly the same seven-action trajectory in every task:
propose `delta(log(volume),1)`; screen candidates 3, 0, 1, 2; select candidate 0
(`returns`); stop. The action sequence remained unchanged across signal, null
and decay tasks despite their different feedback. The environment automatically
sets factor orientation from feedback; that built-in behavior is not evidence
that the LLM learned to interpret evidence. These trajectories are consistent
with learning a fixed procedure and do not demonstrate adaptive research choice.

| Seed | Regime | Base reward | SFT reward | RLOO reward |
| --- | --- | ---: | ---: | ---: |
| 11000 | signal | -0.007000 | 0.140716 | 0.140716 |
| 11001 | null | -0.007000 | -0.015097 | -0.015097 |
| 11002 | decay | -0.007000 | -0.029803 | -0.029803 |
| 11003 | signal | -0.007000 | 0.112965 | 0.112965 |
| 11004 | null | -0.005000 | 0.029090 | 0.029090 |
| 11005 | decay | -0.005000 | -0.040875 | -0.040875 |

SFT and RLOO rewards match their original strict reports exactly; the new parser
changed neither trajectory. No greedy RL improvement over SFT was observed.
Accepting fences did not remove the entire base-to-SFT gap, but remaining schema
compliance and learned fixed action order still confound a claim of better
research reasoning. Six inspected development tasks are insufficient for
generalization or significance claims. No market-alpha or PnL inference is made.

Execution used parent commit
`99eda9525831e9ec01e857ca2f5546f5e7b97760` plus the then-uncommitted ablation files.
All three reports record the same package source SHA256
`9484196ff46077bc5bf6198352ec3ba5c657423bfeebd995ee529116e74deba5`.
That original runner captured its manifest after rollout; the global package hash
can include unrelated concurrent source additions and is not itself a snapshot
of loaded Python modules. Root kept model/evaluation/environment core unchanged
during these runs. The subsequent runner now captures provenance at entry before
model loading; that bookkeeping change was CPU-tested without rerunning these
outcomes. No GPU process remains from this ablation.
