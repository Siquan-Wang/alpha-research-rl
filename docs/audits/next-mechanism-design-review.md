# Independent design review: next evidence-acquisition mechanism

Reviewed 2026-10-01 by the data/evaluation agent, separately from the design
author. This is an internal AI-assisted source-first feasibility critique of
`research-next-steps.md` and the adopted CPU-only `mechanism-gate-plan-v1.md`.
The reviewer ran no solver, model, training, generation, or scoring experiment
and edited neither design document nor implementation source.

**Disposition:** the exact CPU opportunity gate is well specified and useful.
It does not authorize or validate the later LLM study. No unresolved blocker
remains for the adopted mathematical gate. A separate frozen LLM protocol is
still required before any training.

## Is there an identifiable adaptive opportunity?

Yes, in this deliberately constructed finite task. With a uniform four-state
prior, the coarse response points to a pair with posterior mass .9. Querying
that pair's .9-accurate inner tool gives anticipated success .9 times .9 = .81.
A fixed coarse-plus-inner schedule, using both responses and an optimal final
selector, gives .5 times .81 plus .5 times .45 = .63. Querying both inner tools
gives .45, and a uniform mixture of the three fixed pairs gives .57. These are
by-hand design predictions, not executed results. The registered solver must
confirm the full adaptive maximum by comparing all twelve query plans, not
merely compare one good adaptive script with a weak static script.

The CPU plan meets that requirement, specifies conditional independence of
tool bits given the hidden state, uses exact rational arithmetic, and demands
independent 32-world plan execution tests. Its >=.10 opportunity gap and
different-second-query requirements are concrete stop/go rules. The static
selector is allowed to use both acquired responses, making it the relevant
same-budget comparator. The no-query .25 reference is correctly labeled as
having a different query count.

## Findings resolved before closing this review

The original fair-bit scrambling criterion was not diagnostic of learning:
with independent fair responses and a uniform hidden candidate, every policy
has exactly .25 expected success. The revised design labels this as a boundary
check, rather than treating disappearance of a reward gain as additional
behavioral evidence. Enumerating each frozen greedy policy's four response
paths also removes avoidable tool-noise Monte Carlo error for the fixed
presentation bank; this does not remove training or transfer uncertainty.

Five further specification findings were sent to the author and incorporated:

- Half-gap capture now explicitly means
  `V(policy) >= V(fixed) + .5*(V(oracle)-V(fixed))`, anticipated to be .72.
- Appropriate branch changes use the entire reserved presentation bank.
  Wrong first queries count as failures; there is no selected subset of
  favorable "applicable" cases. A passing pair requires coarse first and the
  correct inner query on both first-response branches.
- Training/feasibility/final banks must have disjoint complete actor-visible
  presentation configurations, not just different random seeds or hidden-state
  draws. Mapping, order and bit meanings are hashed. Display order is determined
  by the declared permutations, so the stated 24*6*8=1,152 count is consistent.
- The actual tokenizer must verify single-token legal actions; sampling and
  likelihood training must use the same normalized legal-action distribution.
- A frozen feasibility-bank parent-ceiling check stops before RL if the
  untrained parent is already within .01 expected reward of the oracle.

The reviewer checked the revised text for all five changes. The four-GPU-hour
ceiling is stated as a limit, not a measured runtime promise. Failure is to stop
the version, without extra epochs or a replacement evaluation bank.

## What a later positive result would mean

A fixed-ID query script cannot exceed the properly optimized static ceiling
by merely improving its terminal selector. Reward above that ceiling together
with the full-bank branch criterion would demonstrate response-dependent
acquisition in this task. Matched correct-reward versus permutation-control
training and the unchanged parent would help identify the effect of updates.

However, a Bayes-adaptive policy is itself a short conditional algorithm.
The test cannot prove the absence of memorization of that algorithm. Held-out
presentation combinations test use of relabeled meanings within one known
mechanism, not unseen hypotheses, new likelihood structures, compositional
factor discovery, or general research intelligence. The revised design states
this narrow interpretation. All four hidden states recur by construction.

The later protocol still must freeze presentation-bank sizes/hashes, exact
training tasks and reward-permutation grouping, optimization/sample budgets,
checkpoints, numerical-controller training/information limits, action mappings,
and affordable evaluation counts before results are inspected. The prospective
thresholds in the advice document are not a substitute for that registration.
The CPU gate's positive result alone would not establish that the LLM can learn,
nor automatically justify spending the full compute ceiling.

This new synthetic closed-catalog study does not reopen the failed financial
sequential gate or stopped curriculum, relabel development history as holdout,
or provide evidence of novel alpha or profitability.

## Bounded local tokenizer interface check

At root's request the reviewer subsequently performed a tokenizer-only CPU
check using the existing local Qwen3-0.6B revision
`c1899de289a04d12100db370d81485cdf75e47ca`, with `HF_HUB_OFFLINE=1`,
`local_files_only=True`, and `trust_remote_code=False`. The tokenizer-file
SHA256 map matched the existing frozen financial tokenizer contract. No model
weights, forward pass, generation, GPU operation, training or market scoring
was used. The ignored detailed record is
`.local/mechanism-token-interface-check.json`.

Exactly eight candidate forms were checked: raw `A/B/C/D` have distinct IDs
`32/33/34/35`; leading-space ` A/ B/ C/ D` have distinct IDs
`362/425/356/422`. Each form is one token, decodes exactly to its original
string, and is neither a special token nor an EOS token. Three explicit chat
prefixes used the actual tokenizer template with thinking disabled: query and
selection prefixes ending in `Action:\n`, and a selection prefix ending in
`Action: `. Both newline prefixes preserve the prefix IDs when either form
is appended, with suffix IDs equal to the isolated form IDs. The trailing-space
prefix plus a raw letter instead resegments its final space. Consequently,
retokenizing a full prefix-plus-action string can change conditioning tokens;
it must not silently replace a policy's actual prefix/action token sequence.

For a legal action set L, a constrained next-token law at temperature T>0 is
`pi(a)=exp(logit[token(a)]/T)/sum_{b in L} exp(logit[token(b)]/T)`.
Sampling and logged/training probabilities must use the same mask and T.
Positive temperature does not change the legal greedy argmax, but changes
stochastic probabilities and gradients. Further top-k/top-p filtering changes
the law unless explicitly included. Normalizing complete multi-token action
sequence scores is a different choice distribution; full-vocabulary factors,
EOS and length normalization may matter. Only the same-prefix, one-token,
same-temperature special case reduces to this constrained distribution.

This establishes compatibility of the checked token forms and prefixes only.
It does not validate model probabilities, sampling, log-probability roundtrips,
gradients, numerical precision, or a future policy implementation. No training
or evaluation budget was chosen.

An additional static combinatorial check, requested by the design author,
enumerated only presentation matrices: 24 candidate-column permutations times
6 query-row permutations times 8 response-bit flips. Using the exact integer
kernel entries 9/1/5 (denominator 10), the 1,152 raw transformations produce
only **144 distinct visible 3-by-4 kernels**, with exactly eight aliases per
kernel. No hidden outcomes, returns, policy values or model calls were computed.
If displayed labels and formatting are canonical, those aliases give identical
initial actor observations, so splitting raw transformation IDs would leak
identical presentations across banks. All aliases must share a split, with
group identity checked against the complete initial actor-visible prompt and
its tokenization. The reviewer sent this finding to the author; it does not
choose presentation-bank sizes or training budgets.
