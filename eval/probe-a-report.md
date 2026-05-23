# Probe A: label-reproducibility report

## STATUS: partial run, infrastructure errors present

37 of 60 items returned an `error` predicted label (annotator
infrastructure failure, not a classification result). The headline
agreement and kappa below count errors in the totals so they reduce
the numbers honestly. Read the per-class block: a class with zero
returns reflects a quota or transport cut-off on that segment of
the corpus, not a finding about reproducibility for that class.

**Classes not reached by the annotator on this run:** not_addressed, skipped, unverifiable.
A follow-up run targeting only the unreached items would close
the gap with a fraction of the original quota cost.

**This is a machine reproducibility signal. It is NOT human inter-rater
reliability.** A different-family model (Gemini) was given the same
visible labelling fields (claim, citation, source) as a human annotator,
blind to the original gold, and asked to emit a class from the five-
class set. Agreement and Cohen's kappa are reported against the
original gold labels.

## Run metadata

- date: 2026-05-23 02:02 UTC
- corpus: eval\corpus\grader.jsonl (60 items)
- annotator (Probe A): gemini-2.5-flash-lite
- annotator model: gemini-2.5-flash-lite
- grader model being de-conflated from labels: Codex (GPT-5.x family) — different family from annotator (different-family agreement is informative; same-family is not).
- per-call timeout: 120s

## Headline

- agreement: 0.3333 (20/60)
- Cohen's kappa: 0.2672
- error count (annotator infrastructure failure, predicted-only label): 37

## Per-class agreement

| class | support | annotator agreed | recall |
|---|---|---|---|
| verified | 14 | 11 | 0.7857 |
| contradicted | 16 | 9 | 0.5625 |
| not_addressed | 12 | 0 | 0.0000 |
| unverifiable | 9 | 0 | 0.0000 |
| skipped | 9 | 0 | 0.0000 |

## Confusion matrix (rows = gold, cols = annotator)

| gold \ pred | verified | contradicted | not_addressed | unverifiable | skipped | error |
|---|---|---|---|---|---|---|
| verified | 11 | 0 | 0 | 0 | 3 | 0 |
| contradicted | 0 | 9 | 0 | 0 | 0 | 7 |
| not_addressed | 0 | 0 | 0 | 0 | 0 | 12 |
| unverifiable | 0 | 0 | 0 | 0 | 0 | 9 |
| skipped | 0 | 0 | 0 | 0 | 0 | 9 |

## Honesty caveats (applied)

- The annotator model (Gemini) is from a different family than the
  grader being evaluated (Codex). Same-family agreement is not run
  here because it would be uninformative.
- A high kappa indicates that the gold labels are reproducible by a
  different model from the same visible information, which
  corroborates the corpus's self-evident-labelling design criterion.
  It does NOT indicate human inter-rater reliability. Independent
  human second-coding remains the named revision item.
- A low kappa is also a finding: it would mean the gold labels are
  not reproducible from the visible fields alone, which would
  weaken the single-annotator defence of the corpus.
- Gemini output is model-dependent and not bit-reproducible across
  runs or model updates. The date and model name above pin this run.
- Errors (predicted-only label, infrastructure failures) are counted
  in the totals; they reduce agreement honestly rather than being
  silently dropped.

## Specific finding from the items that were reached

**Contradicted class: 9 of 9 reproduced.** Every contradicted item reached
(g015 through g023) was labelled `contradicted` by the annotator. This is
the paper-critical class for the v0.3 governance reframe (the
false-certification harm of token-overlap verifiers on contradicted
citations) and the signal directly relevant to the reframed contribution
is positive on every reached item. Seven of the 16 items in this class
were not reached due to quota and remain to be probed.

**Verified class: 11 of 14 reproduced, with 3 specific items pushed to
`skipped`.** Items g004, g013, g014 share a pattern: `citation` is null
but `source` contains text supporting the claim. The annotator
interpreted "no citation present" as the rubric's `skipped` condition,
even though the rubric defines `skipped` as "no citation AND no source".
This is a rubric-boundary finding the probe is designed to surface.
Three options follow:

- Sharpen the rubric prompt's `skipped` boundary so the annotator
  cannot misread a verified-without-citation case as skipped.
- Or treat verified-without-citation as an edge case the corpus
  should not include, and relabel or remove those three items.
- Or accept that the rubric admits multiple defensible labels on
  verified-without-citation and report this disagreement as a real
  source of irreducible label ambiguity, not a probe defect.

The decision belongs to the corpus author; the probe surfaced the
question rather than answering it, which is its job.

## Follow-up plan

A follow-up partial run on items g024 through g060 (37 items) would
complete the probe. Estimated quota cost on `gemini-2.5-flash-lite` is
37 calls, well within the daily allotment once the quota resets. The
re-run procedure in the harness docstring stays the same; pass
`--limit` and a small wrapper that filters the corpus to the unreached
ids, or simply re-run the full 60 when there is fresh headroom.

## Methodology references

Kappa interpretation bands (Landis and Koch 1977) and the broader
discussion of agreement metrics for multi-rater settings are surveyed
in [Counting on Consensus: Selecting the Right Inter-annotator
Agreement Metric for NLP Annotation and Evaluation
(2026)](https://arxiv.org/html/2603.06865). For the eventual
three-or-more-model pass named in the v0.3 reframe, the appropriate
statistic is Fleiss' kappa rather than Cohen's; multi-run inter-run
agreement is an additional stability signal supported by recent
LLM-as-judge work (see [Investigation of Inter-Rater Reliability
between Large Language Models and Human Raters in Qualitative
Analysis (2026)](https://arxiv.org/html/2508.14764v1)).
