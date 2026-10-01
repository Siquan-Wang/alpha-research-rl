# Research note: quant-ML reader review

2026-10-01. **Final prose review cleared; no remaining reader/claim blocker.**
The reviewed manuscript identity and resolved findings appear below. PDF layout,
rendered figures and publication are root's separate checks.

This is an internal AI reader review, not external peer review. The reviewer
participated in earlier study design, implementation and audits, including the
matched-prefix protocol and reward-credit review, and therefore is not an
independent judge of the entire research program. The reviewer does not author
the synthesis note or PDF. This lane reads source records and prose only; it
performs no new experiment, inference, training, market evaluation or replay.

## Coherent question and proposed structure

The central question should be whether supplied historical feedback improves a
bounded financial-research decision beyond cheap alternatives. A suitable scope
is an empirical development case study of language-model factor proposals;
neither a new forecasting architecture nor a general benchmark of financial
agents is established. The opening should say what the models generate, what
feedback reaches them, what decision is scored, and what the negative result
changed about subsequent research allocation.

For six to eight pages, a useful reading order is:

1. **Task and measurement.** Returns-only factor DSL, historical orientation,
   later-period cross-sectional rank IC, all-attempt penalties and the reused
   2020–2024 development periods. Define usable, Q and G before presenting
   their values; distinguish the abstract research charge from trading costs.
2. **Sequential hosted behavior.** Six proposals per episode, three feedback
   conditions, the same deterministic selector, 180 calls and 30 selected
   outcomes. Explain the primary contrast and its negative result. Agency is
   the observed history-conditioned proposal sequence; useful adaptation remains
   the tested question.
3. **Why diagnose the pool?** The separately declared post-hoc diagnosis found
   hindsight headroom, but no positive mean IC from the three tested feasible
   selectors. Full feedback had a lower ceiling and smaller selection gap than
   the controls. This motivates a common starting state; it does not identify
   selection as the sole failure or authorize an oracle strategy.
4. **Matched-prefix revision.** Same two-candidate starts, displayed versus
   masked candidate metrics, four separate continuations and three cheap
   generators. Explain why proposal Q and selected gain G answer different
   questions, then report the failed allocation gate with all denominators.
5. **Separate actual post-training evidence.** Qwen SFT/RLOO updates exist, but
   the financial policy is a one-action contextual bandit. Evaluation validity
   gains and within-group reward coefficients are different facts; neither
   establishes useful prediction. Reward-permutation controls have their own
   trajectories and remain exploratory follow-up evidence.
6. **Limits and decisions.** What stopped, what remains unmeasured, and what
   independently inspectable artifacts support each claim. Put hashes, commands
   and most audit details in an evidence map or appendix rather than recounting
   engineering iterations in the main text.

The research sequence itself was adaptive. Individual prospective freezes and
later post-hoc analyses must not be presented as one preregistered program. A
small study-to-question table is more useful than a list of every implemented
tool or every passing test. The hosted proposal studies should carry the main
narrative, with actual local weight training as a clearly separate path.

## Main interpretation traps to prevent

- **Generation versus discovery.** A model emits formula structure and rationale;
  syntactic variety, coherent explanations or supported score citations do not
  establish economically distinct signals or useful alpha.
- **Agency versus learning.** Six history-conditioned proposals are actual
  inference-time interaction. They do not show learned query acquisition,
  long-horizon competence or Astra weight updates. The final selector is
  deterministic, not an additional actor decision.
- **Controlled information versus total ignorance.** Masking removes the
  displayed candidate-metric package; shared probes and formulas still permit
  legitimate mathematical inference. Do not rename this intervention a clean
  scalar-IC effect or claim the masked actor has no relevant information.
- **Different outcomes versus contradictory results.** Truthful feedback had
  worse candidate Q but better G relative to masking; its absolute G stayed
  negative and below copying/window edits. This is compatible because the
  historical selector can retain a prefix candidate. Each repetition is a
  separate branch, not four candidates followed by a best-of-four selection.
- **Validity versus prediction.** The truthful-versus-grammar Q advantage
  contains a positive failure-avoidance component and negative IC contribution.
  The two grammar failures were valid eligible expressions with unusable
  historical signals, not malformed syntax or failed future assessments.
  Conditional usable IC must not replace the all-slot endpoint.
- **Oracle versus policy.** The post-hoc best-in-pool ceiling uses future outcomes.
  It is neither deployable nor proof a learnable selector exists, and differences
  between arm ceilings are not a causal generation-effect decomposition.
- **Counts versus uncertainty.** Ten dependent half-years are not 180 or 80
  independent markets. Four continuations describe conditional generation
  variation; provider-draw independence is unverified. Neither the MCSE nor the
  thirteen point inequalities constitutes a significance test or fresh holdout.
- **Training signal versus update attribution.** The original 31 RL updates and
  the four-run total of 63 updates have different populations. Zero direct V
  coefficients in 61 of 63 updates does not contradict validity-driven evaluated
  reward gains, nor identify gradient, clipping or Adam contributions. C uses
  training-assessment information and is itself validity-gated.
- **Evidence integrity versus economic replication.** Byte-pinned saved replay,
  sampling-law checks and synthetic confirmation checks support particular
  implementation claims. They do not create an unseen market, prove model
  pretraining was clean, or calibrate the overlapping financial ICs.

No pre-draft scope blocker was found. The proposed note would be valuable if its reader could
identify the critical counterfactual and resulting stop decision for each main
study without consulting an audit log. These recommendations preceded the draft.

## Draft review and resolved findings

The first reviewed manuscript had SHA-256
`cbcb1c843b0be5cb7f448f99306b7d5b2ee610fbbb6b77ce0d34f7ccfeb932a1`.
The reader review cross-checked its claims against the existing original Astra,
pool, matched-prefix, financial proposal, reward-linkage, diversity, reliability
and reward-credit reports. This was a prose/source comparison, not another
arithmetic run over saved outcomes.

Three substantive clarity findings were sent directly to the manuscript author:

1. **Define the actual information intervention.** Truthful/masked labels alone
   did not tell the reader what both conditions still knew. Section 4 now states
   that numerical initial probes, prefix formulas and structural statuses are
   shared, while candidate metric/support bundles are masked. It preserves
   legitimate inference from visible information rather than implying the
   control knows nothing about candidates.
2. **Explain the decision rule instead of listing passed checks.** The draft
   reported five of thirteen inequalities without saying what continuation
   required. It now gives Q, all-attempt IC-contribution and G superiority over
   masking and each cheap comparator, plus mean G above the abstract .01 cost.
   It explicitly calls this resource allocation, not significance testing.
3. **Identify where the positive reward evidence came from.** The abstract's
   opening referred to higher training reward, whereas the reported gains were
   evaluation utility. It now says higher evaluated reward and distinguishes
   correctly linked RL versus SFT from IC-contribution comparisons against
   permutation controls.

The author also replaced ambiguous "private" selector wording with an
actor-hidden deterministic selector, specified that the window edit acts on the
historical prefix winner, and spelled out the Kenneth R. French Data Library
attribution. These changes resolve the reader ambiguities without changing an
endpoint, result or frozen study. A suggested short qualitative response example
was optional; the author omitted it to avoid introducing a separate text-audit
method and selected-example caveat within the page budget. Its omission is not a
claim blocker.

## Final reader judgment

The revised [manuscript](../research-note-v1.md), approximately 2,581 words, has
SHA-256 `ed3882b51ac0f66d97fd10bfe374cadf2e342209abd50eaa2b3c93e784c5dd0a`.
The reviewer reread the changed abstract, task attribution, selector definition,
matched-prefix intervention and allocation paragraph before clearing it.

The note now supports a coherent quant-ML discussion: the original feedback
comparison motivates a post-hoc pool diagnosis; that diagnosis motivates a
common-start revision comparison; cheap controls determine whether to continue.
The distinct local training path establishes actual parameter updates while
showing why evaluated validity gains are not a training-gradient explanation.
It does not organize its contribution around audit counts or CI activity.

The core interpretations are consistent with their linked reports:

- Q scores the new candidate; G scores the selected branch relative to the
  prefix baseline. Relative G can improve while candidate Q worsens, and neither
  hosted arm beats copying/window edits on absolute G. Four continuations are
  separate branches, with no hidden best-of-four selection.
- Copy has zero G, not zero Q. Grammar's two unusable historical signals remain
  in forty-slot Q denominators; the positive validity component and negative
  IC-contribution contrast both remain visible.
- Oracle headroom is explicitly unavailable to a feasible historical selector.
  The pool-versus-selection identity is not described as a causal attribution.
- The original 31 RL steps, two additional permutation-control runs and 63-step
  saved accounting have explicit populations. Reward-linkage controls follow
  their own policy trajectories. Coefficient and surrogate statistics do not
  identify component gradients, Adam shares or useful financial learning.
- Generation MCSE, market uncertainty and training variation remain distinct.
  The reused development periods, limited repetitions, post-hoc follow-ups,
  revised histories and unaudited pretraining exposure are disclosed.

Primary-source spot checks support the short prior-method descriptions:
[R&D-Agent-Quant](https://arxiv.org/abs/2505.15155) describes hypothesis,
implementation and feedback stages with bandit scheduling;
[AlphaGen's official repository](https://github.com/ICT-FinD-Lab/alphagen)
identifies formulaic factor generation by RL; and
[Ahmadian et al.](https://arxiv.org/abs/2402.14740) treats REINFORCE-style LLM
post-training. This was a bounded attribution check, not a literature review or
independent validation of their empirical performance. The note makes no
cross-benchmark ranking or algorithm-novelty claim.

The final prose shows observable GenAI and multistep behavior without relabeling
hosted inference as Astra weight training. It presents a useful, inspectable
negative development case study, not an economically useful agent, a general
feedback-effect estimate, an independent market replication or external peer
review. The figure paths were intentionally being supplied by root during this
review. PDF pagination, figure rendering and link delivery are outside this
prose clearance; no new experimental execution occurred in this lane.
