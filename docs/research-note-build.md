# Research note: reading, building and review

[Read the seven-page PDF](../output/pdf/alpha-research-note-v1.pdf) or its
[Markdown source](research-note-v1.md). The note connects the original hosted
proposal study, post-hoc pool diagnosis, prospective matched-prefix follow-up,
separate local weight training, reward-linkage controls and saved reward-credit
analysis. It adds no experiment, financial observation or statistical claim.

## Build from existing public results

With the optional `plots` and `paper` dependencies available:

```bash
python scripts/plot_research_note.py
python scripts/build_research_note.py
```

For a new environment, `python -m pip install -e ".[plots,paper]"` installs those
dependencies. The publication build used already available packages; no package,
model, data or paid service was acquired for the note.

The plot script checks the exact SHA-256 bytes of
`results/astra_matched_prefix_v1.json` and `results/reward_credit_v1.json`, then
draws paper-sized PNGs. It does not import the financial evaluator, replay
historical studies or run a model. The original full-size figures remain
unchanged. The matched-prefix plot keeps forty attempts per generator, including
the two unusable grammar proposals. The reward-credit plot keeps every group
and applies the saved assigned reward channels for controls.

The PDF builder supports the limited Markdown used by this note, embeds the
ReportLab-bundled Vera fonts for prose and uses standard Courier for equations.
It is not a general Markdown converter. Evidence links resolve to Git commit
`21bf13e4888c24f2f05f1ff21708a175bcb155c5`, so the cited reports remain the
publication-era versions. Formatting the note does not rerun their evidence.

## Publication checks and limits

The [build and inspection record](../artifacts/research-note-v1/build-and-qa.json)
records source, figure and PDF digests and installed renderer versions. Two
internal review lanes examined different concerns:

- [Evidence review](audits/research-note-evidence-review-v1.md): exact values,
  denominator and population definitions, source provenance and inference limits.
- [Reader review](audits/research-note-reader-review-v1.md): intervention clarity,
  counterfactuals, narrative and potential overclaims.

Reviewer participation in earlier work is disclosed. These are internal
AI-assisted reviews, not external peer review or independent economic replication.
The coordinator rendered all seven final pages to PNG with Poppler and inspected
text, tables, both figures, captions, equation blocks and page boundaries. Text,
page dimensions and link annotations were also inspected programmatically.
This establishes the observed layout, not formal PDF accessibility conformance.

The publication build used ReportLab 4.4.9 and Matplotlib 3.11.2. Poppler emitted
two display-font warnings for Symbol and ArialUnicode; the note uses embedded
Vera prose fonts and Courier equations. All final pages were inspected without
observed missing glyphs or clipped content. Different renderer/font versions can
change PDF bytes or pagination; a digest match is an artifact identity check,
not a requirement that arbitrary environments produce identical bytes.

The note retains development-data reuse, limited seeds, revised histories,
unmeasured pretraining exposure and unavailable component-gradient evidence.
Its negative results do not establish that feedback is generally harmful or
that language-model factor research cannot work.
