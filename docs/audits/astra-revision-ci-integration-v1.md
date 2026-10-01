# Matched-prefix saved replay: CPU CI integration

This is an internal AI configuration review by an implementation contributor,
not external peer review or independent validation of the financial findings.
It changes no frozen study source, protocol, input, response, selector or result.

The root confirmed that the actual complete result and
`docs/astra-revision-explorer.html` existed before the workflow was edited.
One unconditional step was added after the pool replay in the ordinary `tests`
job of [CPU checks](../../.github/workflows/tests.yml):

```yaml
- name: Replay the complete matched-prefix revision bank and offline explorer
  run: python scripts/replay_published_astra_revision.py
```

An availability-only byte check matched result SHA-256
`89162112ddad384ed8917a8b1198ce94044abc90ff15e1680bfe88b66eb43c37`
and HTML SHA-256
`8bb1ff7013c8c7906f9223daca87287296103f8643e41216037d2bbf39d9b772`.
This check does not replace guarded replay.

The existing Ubuntu matrix runs this step under Python 3.11 and 3.12. The
existing `pip install -e '.[dev]'` supplies the package and ordinary numerical
dependencies. No training extra, provider login, model weights, market archive,
new package, workflow permission or secret is added. Each replay starts in a
fresh Python process, avoiding state inherited from pytest or other replays.

The [public entrypoint](../../scripts/replay_published_astra_revision.py)
requires the complete 200-slot saved bank and exact report/HTML identities. It
reconstructs the page in memory, including all twenty prompt contexts, and
rejects missing HTML or an altered payload, renderer identity or template.
There is no existence-based skip or `continue-on-error`. Its saved replay
does not revalidate the installed scoring runtime, so the normal CPU matrix
does not need the original pinned scoring environment.

The existing guards prohibit model/training and financial scorer imports,
network and subprocess activity after platform initialization, and reads from
private/model/raw-data directories. Frozen replay makes disposable temporary
copies of public evidence; the ordinary runner's temporary directory supports
this. The integration does not claim zero filesystem writes. It does not alter
these guards. Existing Git attributes preserve bound source/evidence/prompt
bytes; only surrounding HTML presentation line endings may normalize.

Validation here is a read-only compatibility inspection and a narrow workflow
edit. Root owns the actual guarded replay and subsequent publication/remote CI
checks; this note does not claim those runs passed. No model invocation,
financial scoring or duplicate full test run was performed for this integration.
