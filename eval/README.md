# eval: evaluation harness for claude-provenance

## What this is

This directory contains a small, hand-built seed corpus and an evaluation
harness for the claude-provenance v0 heuristic detector.

**This is not an external validated benchmark.** The corpus was constructed
manually to cover the claim types the heuristic is designed to catch, to
confirm that the false-negative the v0 design closed stays closed, and to
give a regression baseline. Reported numbers are entirely corpus-dependent
and reflect the design choices embedded in the corpus labels. Do not quote
precision, recall or F1 from this harness as general accuracy figures.

## Corpus: eval/corpus/seed.jsonl

35 items. Each line is a JSON object:

```json
{
  "id":   "<unique id>",
  "text": "<one short paragraph>",
  "gold": [
    {
      "claim":  "<substring asserting a fact>",
      "axis1":  "supported | unsupported | tagged",
      "axis2":  "verified | unverifiable | skipped | na"
    }
  ]
}
```

Items with an empty `gold` array are non-claim sentences included to confirm
the heuristic does not fire on them.

### Axis-1 labels (v0 heuristic)

| Label | Meaning |
|---|---|
| `supported` | The claim sentence itself carries a citation (URL, APA, Source: note, markdown link, or footnote), or the immediately following sentence is a citation-lead line. |
| `unsupported` | A claim trigger fires but no adjacent citation is present. |
| `tagged` | The claim carries an explicit `[CITE NEEDED]` marker. |

### Axis-2 labels (offline verify_text)

| Label | Meaning |
|---|---|
| `unverifiable` | A citation is present but source text cannot be fetched (offline). |
| `skipped` | No citation is present; nothing to verify. |
| `verified` | Source text was fetched and salient tokens matched (not reachable offline). |
| `na` | Axis-2 verdict not applicable for this gold entry. |

### Coverage in the seed corpus

The corpus explicitly covers:

- **Supported claims** -- inline URL, APA (Author, Year), `Source:` note,
  adjacent citation-lead line (next sentence is the source)
- **Unsupported claims** -- each trigger type: year, percentage, magnitude,
  statute, attribution
- **Tagged claims** -- explicit `[CITE NEEDED]` across mixed trigger types
- **v0 false-negative case** -- a source two or more sentences away from the
  claim; the corpus labels the claim `unsupported`, confirming the v0
  bleeding-citation bug stays closed
- **Non-claim sentences** -- plain text with no factual trigger; gold is empty
- **APA citation with multi-word author** -- exercises a known regex limitation
  where `(Productivity Commission, 2021)` does not match the single-token APA
  pattern; correctly labelled `supported` (gold) even though the heuristic
  predicts `unsupported` (a genuine false positive)

## Running the evaluation

From the repo root:

```
python eval/run_eval.py
```

Use a custom corpus:

```
python eval/run_eval.py --corpus path/to/custom.jsonl
```

The harness exits 0 on success and prints a metrics table. It exits 1 only if
the corpus file is missing or malformed.

## How to extend the seed corpus

1. Add lines to `eval/corpus/seed.jsonl`. Each line must be valid JSON with
   the schema above.
2. Choose texts that are self-evidently labelled: a reviewer reading the text
   must be able to agree the gold axis-1 label without external knowledge.
3. Cover edge cases you care about: non-English Unicode, footnote references
   (`[^1]`), markdown links, multi-claim sentences, very long claims.
4. After adding items, re-run `python eval/run_eval.py` and inspect the
   confusion table. Large drops in precision or recall warrant investigation.
5. Run `python -m unittest tests.test_eval -v` to confirm the harness
   invariants still hold.

## Test suite

`tests/test_eval.py` verifies:

- The harness runs on the seed corpus and exits 0.
- Every reported metric is within `[0, 1]`.
- The corpus parses as JSONL and all axis-1/axis-2 values are from the allowed
  set.
- The v0 false-negative item (`c10`) is labelled `unsupported`.

The test suite does **not** assert specific accuracy numbers because those
numbers are corpus-dependent and will change as the corpus grows.

---

## Grader evaluation

This section documents the second evaluation layer: a precision/recall
assessment of the grader classes in `provenance/grade.py` against a dedicated
grader corpus.

### Corpus: eval/corpus/grader.jsonl

60 items, ids `g001` to `g060`. Each line is a JSON object:

```json
{
  "id":       "g001",
  "claim":    "<the sentence asserting a fact>",
  "citation": "<URL or APA token>" | null,
  "source":   "<inline synthetic source text>" | null,
  "gold":     "verified | contradicted | not_addressed | unverifiable | skipped",
  "note":     "<one-line reason the label is self-evident>"
}
```

The gold label is always one of five classes. The label `error` is never a
gold value; it can appear only as a predicted label in the confusion matrix,
representing a grader infrastructure failure.

#### Class balance

| Gold class | Count | Item ids |
|---|---|---|
| `verified` | 14 | g001-g014 |
| `contradicted` | 16 | g015-g030 |
| `not_addressed` | 12 | g031-g042 |
| `unverifiable` | 9 | g043-g051 |
| `skipped` | 9 | g052-g060 |
| **Total** | **60** | g001-g060 |

### Methodology

Sources in the grader corpus are synthetic and self-contained. There is no
network fetch for any grader corpus item. The harness calls `grader.grade()`
directly with the inline `source` text (or Python `None` when the JSON value
is null). This design isolates the measurement to grader reasoning given a
source. Fetch reliability is a separate, unmeasured axis and must not
contaminate results from this corpus.

### Running the grader evaluation

The grader evaluation runs automatically after the seed report when you invoke
the harness with no additional arguments:

```
python eval/run_eval.py
```

This appends the default heuristic grader report to stdout immediately after
the existing seed report.

Additional CLI options:

```
python eval/run_eval.py --grader-corpus PATH
```

Override the default path to the grader corpus (default:
`eval/corpus/grader.jsonl` relative to the repo root).

```
python eval/run_eval.py --grader heuristic
```

Run the `HeuristicGrader` only. This is the default and requires no API key.

```
python eval/run_eval.py --grader llm
```

Run the `LLMGrader`. This path is active only when the environment variable
`ANTHROPIC_API_KEY` is set. If the key is absent, the harness prints a line
containing `LLM grader unavailable`, falls back to `HeuristicGrader` for the
run, and exits 0. It never raises and never exits non-zero for a missing key.

```
python eval/run_eval.py --grader both
```

Run `HeuristicGrader` unconditionally, then run `LLMGrader` only if
`ANTHROPIC_API_KEY` is set. If the key is absent the `LLM grader unavailable`
notice is printed and only the heuristic block is produced. Two separate grader
blocks are printed when both graders are active, heuristic first.

### What is measured

For each run the harness reports:

- **Per-class precision, recall, and F1** using one-vs-rest counting across
  the five gold classes (`verified`, `contradicted`, `not_addressed`,
  `unverifiable`, `skipped`). For each class: TP is items where gold equals
  the class and predicted equals the class; FP is items where gold differs but
  predicted equals the class; FN is items where gold equals the class but
  predicted differs. Precision, recall, and F1 are set to 0.0 when the
  denominator is zero.
- **Macro-average precision, recall, and F1**, computed as the unweighted mean
  over the five gold classes.
- **Overall accuracy**, the fraction of items where the predicted label exactly
  matches the gold label.
- **Confusion matrix** with rows representing the five gold classes and columns
  representing all six possible predicted labels (the five gold classes plus
  `error`). Each cell counts the number of items with that gold/predicted
  combination.

All values are computed at runtime from the corpus. No figures are hard-coded.

### Structural finding: contradiction-blindness is analytic, and its governance cost

The offline `HeuristicGrader` operates by token overlap only. With a source
present, its code path can return only `verified` or `not_addressed`: the
verdict `contradicted` is not in its output alphabet. Its zero score on the
`contradicted` block is therefore an analytic property of the algorithm, true
by construction, not an empirical discovery. That token-overlap and lexical
matching have no model of negation is established prior work in natural
language inference (for example McCoy, Pavlick and Linzen 2019, the HANS
diagnostic; He, Zha and Wang 2019 on negation-as-contradiction dataset cues).
This harness does not claim to discover that.

The contribution this block supports is a governance one. On the 16-item
`contradicted` gold block (g015-g030) the heuristic does not merely fail to
flag contradiction: it returns a confident `verified` on the majority of
items, because a contradicting source still contains nearly all of the
claim's salient tokens (the polarity is carried by short verbs the tokeniser
does not retain). A token-overlap citation verifier, deployed as a provenance
control, therefore silently converts contradicted citations into supported
ones. The reportable quantity is this false-certification count, not a
precision or recall figure against a label the grader cannot emit.

Scope, stated plainly. Sources here are synthetic and supplied inline with no
fetch, so this measures reasoning over a given claim-source pair, a natural
language inference setting, not end-to-end citation verification. Retrieval,
source ambiguity and multi-document evidence are out of scope for this corpus
and are named limitations, not results. Only a grader that can reason about
opposition (the optional `LLMGrader`, or the evaluation-only `CodexGrader`)
can emit `contradicted` at all.

### Honesty guardrails

The following constraints apply to how results from this harness are
interpreted and communicated. They are stated without softening.

1. The grader corpus is hand-built and small. It is not an external validated
   benchmark. Numbers produced by this harness are corpus-dependent. Do not
   quote them as general accuracy figures for the grader or for the
   claude-provenance plugin.

2. Sources are synthetic and self-contained. This measures grader reasoning
   given a source, not end-to-end fetch reliability. Fetch reliability is a
   separate, unmeasured axis.

3. The offline `HeuristicGrader` cannot emit `contradicted`: with a source
   present its code path returns only `verified` or `not_addressed`. Its zero
   on the `contradicted` block is analytic, true by construction, not a
   measured finding and not a defect introduced by the corpus. The polarity
   word in those items is a short verb below the grader's salient-token length
   cutoff, so the corpus and the tokeniser interact. Report this plainly: do
   not present the zero as an experimental result.

4. Any `LLMGrader` or `CodexGrader` numbers depend on the model version in use
   and are not reproducible bit-for-bit across runs or model updates. The
   associated paper, *From Citation to Epistemic Governance*, is in
   preparation. Do not claim stars, adoption, or benchmark status the project
   does not hold.

5. Prior art and claim scope. The blindness of lexical or token-overlap
   matching to negation is established in the natural language inference
   literature (McCoy, Pavlick and Linzen 2019; He, Zha and Wang 2019), and
   automatic citation-verification benchmarks already exist (for example ALCE,
   Gao et al. 2023; Liu, Zhang and Liang 2023). The contribution anchored to
   this harness is the governance framing, that deployed token-overlap
   provenance tooling false-certifies contradicted citations, not the
   rediscovery of negation-blindness. A single cross-model run (one
   alternative vendor) supports only the narrow claim that the recovery is not
   idiosyncratic to one vendor. A claim that recovery is general across models
   would require at least three version-pinned models spanning training
   lineages, including one small or open model, and is not made here.

### How to extend the grader corpus

1. Add lines to `eval/corpus/grader.jsonl`. Each line must be valid JSON
   matching the schema above.
2. Apply the same self-evident-labelling discipline used in the seed corpus:
   a reviewer reading only the `claim`, `citation`, and `source` fields must
   be able to agree the `gold` label without any external knowledge.
3. For `verified` and `contradicted` items, include an inline `source` so the
   grader receives the evidence directly. For `unverifiable` items, include a
   `citation` but leave `source` null. For `skipped` items, leave both null.
   For `not_addressed` items, include a `source` whose content is genuinely
   unrelated to the claim's factual assertion.
4. Write a `note` that makes the label self-evident in one line.
5. Assign the next sequential id in the `g001`-`g999` range.
6. After adding items, re-run `python eval/run_eval.py` and review the updated
   confusion matrix. A large change in any per-class metric warrants checking
   whether the new items inadvertently favour or disfavour the grader being
   measured.

---

## Addendum: the Codex cross-model backend (`--grader codex`)

The shipped `LLMGrader` calls the Anthropic Messages API directly and
therefore requires `ANTHROPIC_API_KEY`. To measure the headline question
without provisioning a key, the harness adds a third grader backend,
`CodexGrader`, selected with `python eval/run_eval.py --grader codex`.

What it is. `CodexGrader` drives the local Codex CLI (`codex exec`) as a
separate, read-only, ephemeral subprocess. It is fed the exact same system
prompt, claim, source, and citation that `LLMGrader` uses, and is constrained
to the same JSON verdict schema via `--output-schema`. The no-source classes
(`unverifiable`, `skipped`) are decided deterministically, identical to
`HeuristicGrader`, so no Codex call is spent on them and the comparison is on
identical ground. It is never auto-selected by `get_grader()`, is never
reachable from the hook, and is not run in CI.

Why it strengthens the result. Because the prompt, inputs, and verdict
schema are held constant and only the model changes, a Codex run is a clean
same-task different-model comparison. If a different vendor's model recovers
the `contradicted` class that the token-overlap heuristic gets zero on, the
finding is shown to be structural to token overlap and general across models,
not an artefact of one provider.

Honesty caveats (in addition to the four guardrails above).

1. Codex output is model-dependent and not bit-reproducible. The model is
   whatever the local Codex CLI is configured and authenticated to use; the
   harness labels the grader `codex-cli` and does not assert a fixed model.
2. This requires the Codex CLI installed and authenticated. If it is absent
   or unauthenticated, every source-bearing item returns verdict `error`;
   the harness still exits 0 and the confusion matrix shows the `error`
   column. An all-`error` run is a tooling failure, not a finding, and must
   be reported as such.
3. The Codex run measures the finding's generality, not the exact shipped
   `LLMGrader`. The keyed Anthropic run remains the only measurement of the
   artefact exactly as published, and stays optional.
4. `CodexGrader.grade()` never raises: any failure (binary missing, non-zero
   exit, timeout, schema or JSON failure) maps to verdict `error`.

Reproducing the clean run. The default per-call timeout is 120 seconds.
On slower machines a small number of source-bearing calls can exceed this
and return verdict `error` (an infrastructure outcome, not a
misclassification). Set `PROVENANCE_CODEX_TIMEOUT=300` to reproduce a run
with no timeout-induced `error` items. The `error` count must always be
reported explicitly with any result: a clean confusion matrix is only
trustworthy if the `error` column is stated and zero.
