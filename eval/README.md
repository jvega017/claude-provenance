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

### Structural finding: the heuristic cannot detect contradiction

The offline `HeuristicGrader` operates by token overlap only. It checks
whether salient tokens from the claim text appear in the source text. Token
overlap has no model of negation and no mechanism for recognising that a
source explicitly contradicts a claim by reversing its direction or replacing
its figures. As a result, `HeuristicGrader` structurally cannot emit the
`contradicted` verdict. The four verdicts it can produce are `verified`,
`not_addressed`, `unverifiable`, and `skipped`.

On the 16-item `contradicted` gold block (g015-g030), the heuristic is
expected to mislabel items as `verified` (when the contradicting source
contains most of the claim's tokens) or `not_addressed` (when token overlap is
low). This is a measured structural property of the grader, not a defect
introduced by the corpus design.

Only the optional `LLMGrader` can reason about whether a source opposes a
claim and therefore produce a `contradicted` verdict.

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

3. The offline `HeuristicGrader` cannot emit `contradicted`: token overlap has
   no model of negation. On the `contradicted` gold block the heuristic is
   expected to mislabel items as `verified` or `not_addressed`. This is a
   measured structural finding, not a defect introduced by the corpus.

4. Any `LLMGrader` numbers depend on the model version in use and are not
   reproducible bit-for-bit across runs or model updates. The associated paper,
   *From Citation to Epistemic Governance*, is in preparation. Do not claim
   stars, adoption, or benchmark status the project does not hold.

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
