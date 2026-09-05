# Improvement roadmap, 2026-07-23

Supersedes `IMPROVEMENT-ROADMAP-2026-06-11.md`. Ordered by what makes every
other claim believable. Each item names its measurement artefact so progress
is checkable, and the effort notes assume one maintainer working with
LLM-agent assistance.

Numbers quoted here come from `eval/run_eval.py` against
`eval/corpus/seed.jsonl` (47 items) and `eval/corpus/grader.jsonl` (60
items), and from `eval/measure_precision.py` (3,421 sentences). All are
small, hand-built corpora; treat every figure as corpus-dependent.

## Tier 1: credibility

1. **Labelled precision corpus for the claim detector.** The current
   false-positive figure (5.1% of ordinary-prose sentences fire a trigger,
   `eval/measure_precision.py`) is a proxy on unlabelled text. Hand-label
   roughly 200 sentences drawn from real policy documents and ordinary prose
   as claim or not-claim, then report true detector precision and recall.
   This number decides whether enforce mode is usable. LLM-assisted
   labelling is acceptable at solo scale provided the method is disclosed in
   `eval/README.md`.
2. **Grader corpus expansion at honest scale.** The 0.90 grader accuracy
   rests on 60 hand-built items. Harvest 150 to 200 items from real public
   documents (annual reports, ABS releases, Hansard), single careful
   annotation with an LLM cross-check, method disclosed. Re-measure and
   publish whatever the number turns out to be.
3. **Fix the two pre-existing CI failures**: the hermetic suite calls
   `claude --print`, and one Windows job trips on bash syntax. A
   verification tool with a red CI badge undermines itself.

## Tier 2: capability

4. **Measure the LLM graders.** The local-LLM and Anthropic grader paths
   exist in `provenance/grade.py` and have never been scored against the
   grader corpus. Run `eval/run_eval.py` against an Ollama instance and
   publish the result. This gates the v0.12.0 release story.
5. **Paraphrase-level contradictions.** Four of the sixteen gold-contradicted
   corpus items carry no comparable number and no lexical antonym, so the
   heuristic grader cannot reach them by design. They are the acceptance
   tests for the LLM grader prompt.
6. **Decide the `verified` verdict name.** The heuristic's `verified`
   verdict means token-consistency with the source. At 0.93 precision on
   the current corpus the word is defensible, and it still promises more
   than the method delivers. A v0.12.0 version bump is the window for a
   breaking rename if one is wanted.

## Tier 3: positioning and distribution

7. **Agent-report verification recipe.** An agent's status report ("CI is
   green", "573 tests pass", "release VALID") is a document full of
   checkable claims, and operators mostly accept it on faith. Document a
   recipe (or add a mode) that runs the existing gate over agent handoffs
   so each claim needs a source the operator can open. No competing linter
   covers this.
8. **Enforce the dogfood claim in CI.** The README states the repo's docs
   scan slop-free and tells-clean. Add a CI job that runs `warrantos slop`
   and `warrantos tells` over `docs/` and `README.md` with `--fail-over 0`
   so the claim is enforced rather than asserted. The claim was briefly
   false on 2026-07-23 (one em-dash tell in the README) and was caught by
   hand rather than by CI, which is the argument for the job.
9. **Ship v0.12.0.** The README points to capability that lives on main
   and is absent from PyPI. Scope: local-LLM opt-in, the contradiction
   detector, corrected docs. Tag it, publish it, and update the version
   badge in the same commit.
