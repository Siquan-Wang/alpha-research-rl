# Initial implementation contract

This is a new research prototype; no alpha or LLM improvement has been demonstrated.

## Scope

First establish numerical correctness and leakage boundaries with deterministic synthetic panels, then public historical-data adapters, then local open-weight LLM SFT/RL. Do not call synthetic results financial evidence or scripted policies LLM agents.

## Package boundaries

Root owns packaging, CLI, policies, experiment runners, training code, README and CHECKPOINT.
Data agent owns `data.py`, `dsl.py`, `evaluation.py`, and matching tests.
Environment agent owns `environment.py`, `protocol.py`, and matching tests.
Research reviewer owns docs/protocol and data-source research only, initially no source edits.

## Data/evaluation interface

- `MarketPanel`: dataclass `close`, `volume`, `returns` float arrays [time, asset], `dates` array [time], `assets` tuple[str,...], `metadata` dict. Validate shapes/chronological dates. Return `returns[t]` is close[t]/close[t-1]-1.
- `make_synthetic_panel(seed=0, n_dates=600, n_assets=32, regime='signal') -> MarketPanel`. Regimes include `signal`, `null`, `decay`; all metadata marks synthetic. Avoid leaking latent signal columns into observation.
- `load_panel_csv(path) -> MarketPanel`: long CSV date,asset,close,volume, with explicit missing/duplicate checks and no silent forward filling.
- `evaluate_expression(expression: str, panel: MarketPanel) -> ndarray[T,N]`. Bounded AST grammar: close, volume, returns; add/sub/mul/div/neg/abs/log; delay(x,k), delta(x,k), ts_mean(x,k), ts_std(x,k), rank(x), zscore(x). Only positive integer lookbacks <=60, causal operations, depth/node caps. No eval/exec.
- `forward_returns(panel,horizon=5)`: close[t+h]/close[t]-1; last h rows NaN.
- `score_factor(values, labels, start, stop) -> dict`: daily Spearman IC, mean_ic, n_dates, coverage, ic_std; handle insufficient assets/constants explicitly. `start:stop` is half-open signal-date interval, caller purges label boundary. No PnL claims.

## Protocol/environment interface

- `ResearchSplit`: half-open `fit`, `feedback`, `assessment` date index tuples, `horizon`; validates order and horizon gap. Assessment is training reward only for training tasks and is never in observations.
- `ResearchEnvironment(panel, split, candidates: list[str], budget=12)`: finite action dicts `{"action":"screen"|"stability"|"select"|"stop", "candidate": int}`; stop may omit candidate.
- `reset() -> dict`, `step(action) -> (observation, reward, done, info)`; observation includes budget, candidate expressions, acquired evidence, selected IDs/history only. No hidden assessment scores/panel/labels in observation or info.
- Screen exposes feedback mean IC; stability exposes predetermined feedback subwindow metrics; select adds candidate to submitted pool, max 3. All non-stop attempts consume budget, including invalid/duplicate actions. Prevent free reward exploitation.
- Reward is zero until done, then assessment score of equally weighted, feedback-oriented, cross-sectionally ranked selected factors minus fixed spent-budget cost. Never choose factor orientation on assessment. Empty pool => zero predictive score, costs still charged. Agent cannot access assessment except terminal training reward; final holdout used only by separate frozen evaluation.
- Root's policies implement `act(observation)->dict` and consume only observations, not environment internals.

## Initial study

For implementation smoke runs, all periods are development, not final untouched tests. Register a frozen study later with separated training seeds/tasks, development seeds/tasks, and sealed held-out tasks/periods. Include null tasks, chronological purging, and matched search budgets. Do not regard overlapping episodes as independent financial evidence.
