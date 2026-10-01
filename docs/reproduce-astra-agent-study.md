# Astra agent study: execution and evidence boundaries

The [prospective protocol](astra-agent-research-plan-v1.md) governs this separately
versioned development experiment. The existing financial scorer and cached data
are reused; the agent proposes formulas through the native Codex CLI. The
three feedback conditions have matched proposal counts and the same selector.

## Validation without inference

The broker, provider and orchestrator tests use artificial panels, fake tasks
and fake subprocesses. They need neither a model login nor downloaded market
data and do not launch actual Codex inference:

```bash
python -m pytest -q -p no:cacheprovider tests/test_agentic_research.py tests/test_codex_actor.py tests/test_astra_study.py
```

These tests verify the interface, information masks, budget, durable failure
records and assessment gate. They do not reproduce a hosted model's decisions.

## Recorded execution workflow

The commands below describe the original study workflow, not an instruction to
replace a published contract in a fresh clone. Output creation is exclusive.
Once a contract or attempted round exists, rerunning it is forbidden. A new
independent model experiment needs a separately versioned protocol and output
namespace; it cannot overwrite this study or claim deterministic regeneration.

The original host has the frozen cached data and an existing authenticated
Codex CLI. `prepare` checks its version, records runtime package versions and
hashes the resolved executable, plan, sources, data and task manifests. It computes the common
historical probes, makes no model request and performs no future assessment:

```bash
python -m alpha_research_rl.astra_study prepare --study-dir .local/astra-agent-v1 --data data/raw/french49-v1/49_Industry_Portfolios_daily_CSV.zip --plan docs/astra-agent-research-plan-v1.md
```

Publish the plan, implementation and `artifacts/astra-agent-v1/contract.json`
before collecting. Check the actual remote commit, then supply its complete
40-character hash. The program verifies local Git blob bytes against that
commit; the operator separately verifies remote visibility.

Check the shared allowance before **each** three-arm round. Supply the current
remaining percentage; the example placeholder is intentionally not a quota
claim. Unknown quota means wait and recheck. At the user's stop threshold,
preserve the incomplete study without launching another round.

A confirmed remaining percentage at or below 5 blocks collection and records
a terminal incomplete marker. To stop earlier with a closing reserve, use the
explicit `stop` command with the actual reading and a reason; do not use it for
a temporarily unavailable quota reading:

```bash
python -m alpha_research_rl.astra_study stop --study-dir .local/astra-agent-v1 --reason "User quota stop with closing reserve" --quota-remaining-percent CURRENT_REMAINING_PERCENT
```

```bash
python -m alpha_research_rl.astra_study collect-round --study-dir .local/astra-agent-v1 --task 2020-H1 --attempt 1 --contract-commit FULL_PUBLISHED_COMMIT --quota-remaining-percent CURRENT_REMAINING_PERCENT
```

One command launches at most three fresh Astra decisions. Calls request ultra
reasoning and the default service tier. Every decision receives the permitted
history through stdin and uses the same neutral working directory. Continue
only in the protocol's fixed task/attempt order. There is no automatic study
loop or provider retry. Infrastructure or protocol failures stop the fixed
study; completed malformed packets instead consume their proposal slot.

After all 60 rounds have completed, freeze all 30 pools and selections:

```bash
python -m alpha_research_rl.astra_study freeze --study-dir .local/astra-agent-v1
```

Publish `results/astra_agent_v1_submissions.json`, verify that remote commit,
then run the separate assessment command:

```bash
python -m alpha_research_rl.astra_study assess --study-dir .local/astra-agent-v1 --published-commit FULL_SUBMISSION_PUBLICATION_COMMIT
```

Assessment evaluates only each frozen selection, with `.06` total abstract
search cost and the registered invalid penalty. A null selection produces a
retained outcome without calling the market evaluator. There is no substitute
candidate selected after viewing future scores.

## What is retained and what can be claimed

Private task-local evidence includes exact prompts, responses, event streams,
process status, usage reports, failed attempts and hashes. Public exports contain
the permitted observations, decisions, selector inputs, outcomes and sanitized
transport metadata, with hashes binding them to retained evidence. Market arrays,
machine/account identifiers, credentials and hidden reasoning are not published.

The recorded CLI configuration is not a backend-weight attestation. Shared
filesystem execution is not an adversarial read-access sandbox. Hosted model
sampling and hidden context need not reproduce exactly. Existing 2020–2024
periods are development data, and this study measures inference-time adaptation;
it neither trains Astra weights nor establishes profitable alpha.
