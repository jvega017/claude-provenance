# CONTRACT: grader precision/recall evaluation (frozen)

This file is the single interface contract for the grader-evaluation work.
Three agents code against it independently. Do not deviate. If something is
underspecified, choose the option that preserves backward compatibility and
the stdlib-only / no-network-by-default invariants.

Status: FROZEN. The corpus and this contract are authored. Agents implement
only the harness (A), tests (B), and README (C) against what is written here.

---

## 1. Hard invariants (all agents)

- Do NOT modify `hooks/provenance_check.py`. Do NOT modify any file under
  `provenance/`. Do NOT modify `eval/corpus/seed.jsonl`. Do NOT modify
  `eval/corpus/grader.jsonl`. Do NOT modify this contract file.
- Standard library only. Python 3.8 compatible. No third-party imports.
- Australian English in all prose and comments. No em dashes. No exclamation
  marks. Sentence case headings.
- Backward compatibility is absolute: every existing test in
  `tests/test_eval.py` must still pass unchanged, and every existing public
  function and CLI behaviour of `eval/run_eval.py` must be preserved.
- The blocking hook stays pure stdlib with zero network I/O. None of this work
  touches the hook. All of it is out of band, inside `eval/` and
  `tests/test_eval.py`.

## 2. File ownership (disjoint)

- Agent A owns `eval/run_eval.py` only.
- Agent B owns `tests/test_eval.py` only.
- Agent C owns `eval/README.md` only.

No agent edits another agent's file. No new files.

## 3. The grader corpus (already authored, do not edit)

Path: `eval/corpus/grader.jsonl`. 60 items, ids `g001`..`g060`. One JSON
object per line:

```json
{
  "id": "g001",
  "claim": "<the sentence asserting a fact>",
  "citation": "<URL or APA token>" | null,
  "source": "<inline synthetic source text>" | null,
  "gold": "verified | contradicted | not_addressed | unverifiable | skipped",
  "note": "<one-line reason the label is self-evident>"
}
```

Gold class counts: verified 14 (g001-g014), contradicted 16 (g015-g030),
not_addressed 12 (g031-g042), unverifiable 9 (g043-g051), skipped 9
(g052-g060).

Methodological note (carry into README): sources are synthetic and
self-contained. There is no network fetch for the grader corpus. The grader
is called directly with the inline source. This isolates grader reasoning
from fetch reliability, which is a separate axis and must not contaminate
the measurement.

`gold` is one of FIVE classes: `verified | contradicted | not_addressed |
unverifiable | skipped`. `error` is never a gold label: it is a grader
infrastructure-failure outcome, not a labelable property of a claim plus
source. `error` may appear only as a PREDICTED label and only as a column in
the confusion matrix.

## 4. Grading semantics

For each grader-corpus item, the predicted label is:

```
pred = grader.grade(item["claim"], src, cit).verdict
```

where `src = item["source"]` mapped to Python `None` when JSON null, and
`cit = item["citation"]` mapped to Python `None` when JSON null. JSON null
maps to Python `None`. A non-null `source`/`citation` is always a non-empty
string.

The harness MUST call `grader.grade(...)` directly. It MUST NOT call
`provenance.verify.verify_text` or `provenance.verify.fetch_text` for the
grader corpus. No network fetch for source retrieval. The only network call
permitted anywhere in this path is the one inside `LLMGrader.grade`, and only
when `ANTHROPIC_API_KEY` is set.

Grader selection:

- `--grader heuristic` (default): `HeuristicGrader()` from
  `provenance.grade`. Fully deterministic, no network.
- `--grader llm`: `LLMGrader()` from `provenance.grade`, but only if
  `ANTHROPIC_API_KEY` is set in the environment. If it is not set, print one
  line containing the exact substring `LLM grader unavailable` then fall back
  to `HeuristicGrader()` for that run and still exit 0. Never raise. Never
  exit non-zero for a missing key.
- `--grader both`: always run `HeuristicGrader()`; additionally run
  `LLMGrader()` only if `ANTHROPIC_API_KEY` is set (else print the
  `LLM grader unavailable` notice and run heuristic only).

## 5. New public functions in `eval/run_eval.py` (exact names)

Tests import these by name. Signatures are frozen.

```python
def load_grader_corpus(path) -> list:
    """Parse eval/corpus/grader.jsonl. SystemExit(1) on missing file,
    malformed JSON, empty file, missing required field (id, claim, gold),
    gold not in the 5-class set, duplicate id, or citation/source not
    (str or None)."""

def grade_grader_corpus(items, grader) -> list:
    """Return list of (id, gold, pred) tuples. pred is the
    Verdict.verdict string from grader.grade(claim, source, citation)."""

def compute_grader_metrics(results) -> dict:
    """results is the list from grade_grader_corpus. Returns a dict:
       {
         "per_class": { cls: {"tp":int,"fp":int,"fn":int,
                              "precision":float,"recall":float,
                              "f1":float,"support":int} for cls in 5 gold classes },
         "macro": {"precision":float,"recall":float,"f1":float},
         "accuracy": float,
         "confusion": { (gold,pred): int },   # pred may be 'error'
         "n": int
       }
    One-vs-rest per class: TP gold==c and pred==c; FP gold!=c and pred==c;
    FN gold==c and pred!=c. precision/recall/f1 = 0.0 when denominator 0.
    macro = unweighted mean over the 5 gold classes. accuracy = exact-match
    correct / n. All values computed at runtime; nothing hard-coded."""

def print_grader_report(metrics, grader_label, n_items) -> None:
    """Print the grader report to stdout. Markers in section 6 are mandatory."""
```

`main()` must, with no CLI args, still produce the existing seed report
exactly as before AND THEN append the grader report(s). Existing functions
(`load_corpus`, `_evaluate_item`, `_compute_axis1_metrics`,
`_compute_axis1_confusion`, `_compute_axis2_counts`, `print_report`,
`_load_hook`) keep their names and behaviour.

## 6. Stdout markers (exact case-sensitive substrings)

Preserved from the existing report (must still appear):
`claude-provenance v0 evaluation report`, `AXIS 1`, `AXIS 2`, `precision`,
`recall`, `F1`.

New, required in the grader report:

- `GRADER EVALUATION`
- `Grader: ` followed by `HeuristicGrader` or `LLMGrader(model=...)`
- `per-class precision / recall / F1`
- `macro-avg`
- `overall accuracy`
- `confusion matrix (rows = gold, cols = predicted)`
- A caveat block containing all three substrings:
  `not a benchmark`, `synthetic, self-contained sources`,
  `corpus-dependent`

For `--grader both` print two grader blocks, each with its own `Grader: `
line; the heuristic block first.

## 7. CLI (argparse in `run_eval.py`)

Keep existing `--corpus` (default seed.jsonl). Add:

- `--grader-corpus PATH` default `str(_REPO_ROOT / "eval" / "corpus" / "grader.jsonl")`
- `--grader {heuristic,llm,both}` default `heuristic`

## 8. Exit codes (frozen)

- `0` on success, including when metrics are low and including when `--grader
  llm` was requested but no API key is present (that path prints the
  `LLM grader unavailable` notice and falls back; it is not an error).
- `1` only if a corpus file (seed or grader) is missing or malformed.

## 9. Test isolation (Agent B, hard requirement)

The v0.2.0 build had a `sys.modules` isolation leak: a module loaded via
`importlib` under a name that collided across test modules caused
full-suite-only failures that per-file runs did not show. Agent B must:

- Load `run_eval` via `importlib` under a unique spec name and, if it inserts
  anything into `sys.modules`, remove it in `tearDown`.
- Not assert specific accuracy numbers (corpus-dependent). Assert structure:
  harness exits 0 with the grader corpus; every per-class and macro metric in
  `[0,1]`; each confusion-matrix row sums to that class's support;
  `load_grader_corpus` rejects a malformed temp corpus with SystemExit(1);
  the corpus contains at least one `contradicted` gold item (the structural
  blindness is actually exercised); ids are unique; all gold values in the
  5-class set.
- All tests offline, deterministic, no sleeps, no network, stdlib unittest
  only. Must pass under the FULL suite, not only per-file.

## 10. Honesty guardrails (Agent C, hard requirement)

The README must state plainly, without softening:

1. The corpus is hand-built and small. It is not an external validated
   benchmark. Numbers are corpus-dependent. Do not quote them as general
   accuracy.
2. Sources are synthetic and self-contained. This measures grader reasoning
   given a source, not end-to-end fetch reliability. Fetch reliability is a
   separate, unmeasured axis.
3. The offline `HeuristicGrader` cannot emit `contradicted`: token overlap
   has no model of negation. On the `contradicted` gold block the heuristic
   is expected to mislabel items as `verified` or `not_addressed`. This is a
   measured structural finding, not a defect introduced by the corpus.
4. Any `LLMGrader` numbers depend on the model and are not reproducible
   bit-for-bit. The associated paper, *From Citation to Epistemic
   Governance*, stays described as in preparation. Do not claim stars,
   adoption, or benchmark status the project does not hold.
