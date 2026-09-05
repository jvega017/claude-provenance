# WarrantOS: CI for claims

Every citation-trigger in an AI-assisted document ships with a source, a `[CITE NEEDED]` tag, or a logged BLOCK. No warrant, no ship.

[![ci](https://github.com/jvega017/warrantos/actions/workflows/ci.yml/badge.svg)](https://github.com/jvega017/warrantos/actions/workflows/ci.yml)
[![layers: 20B / 0P](https://img.shields.io/badge/layers-20B%20%2F%200P-brightgreen)](docs/STATUS.md)
![version: 0.11.0](https://img.shields.io/badge/version-0.11.0-brightgreen)
![python: 3.11--3.13](https://img.shields.io/badge/python-3.11--3.13-blue)
![deps: stdlib only](https://img.shields.io/badge/deps-stdlib%20only-green)

In plain words: 20 layers built, 0 partial. B = built, P = partial; per-layer detail in [`docs/STATUS.md`](docs/STATUS.md).

WarrantOS is a command-line gate for AI-assisted writing. Before a document ships, it checks every citation-triggering claim for a source, scans for chat residue and machine-writing tells, and writes the result to a tamper-evident audit ledger. It is for people who ship AI-assisted prose that others rely on: policy and research teams, communications staff, and operators of AI agents who need to verify what their agents wrote, including agent status reports and handoffs, rather than take it on faith.

## Ten seconds

```text
$ warrantos demo
WarrantOS honest demo
---------------------
Checking a synthetic AI-style draft that deliberately contains
unsupported factual claims and conversational scaffold residue.
Expect a BLOCK verdict.

warrantos check
  run id:        run_6e466f721f8a
  profile:       final-prose
  claims detected: 6
  claims supported: 0
  claims unsupported: 6
  boundary: blocked (7 violations)
  overrides on record: 0

VERDICT: BLOCK
  - BLOCK: boundary violation [assistant_opener severity=high] line 9: Certainly!
  - BLOCK: boundary violation [hedge_provenance severity=medium] line 15: Based on the information provided
  - BLOCK: boundary violation [scaffold_placeholder severity=high] line 17: [TODO: add the figures from the evaluation once the team sen
  - BLOCK: boundary violation [assistant_closer severity=high] line 19: I hope this helps
```

Real output, trimmed. The full run lists all seven violations and the paths of the audit artefacts it wrote.

## Install

```bash
pipx install warrantos      # isolated CLI install
uvx warrantos demo          # zero-install trial run
pip install warrantos       # plain pip works too
```

## Check and verify

`warrantos check` is the core gate: point it at a draft and it returns one verdict, `PASS`, `HOLD`, `BLOCK`, or `NOT_ASSESSABLE`.

```bash
warrantos check draft.md --context context.json --actor-identity actor.json --profile final-prose
```

It detects citation-trigger patterns (years, percentages, magnitudes, statutes, attribution, causal language, superlatives) and checks each for a nearby source or an explicit `[CITE NEEDED]`, then scans for chat-scaffold residue that leaked into the draft. Every miss goes on the record in an append-only ledger.

Detection is free and local. Add `--verify` to check whether a cited source actually supports the claim:

```bash
ANTHROPIC_API_KEY=... warrantos check draft.md --context context.json --verify
```

**Coming in v0.12.0 (unreleased, on main, not yet on PyPI):** verify with a local LLM instead, no API key needed.

```bash
ollama pull llama3.2 && ollama serve       # ~2.0 GB, listens on localhost:11434
warrantos check draft.md --context context.json --verify --no-fetch
```

Supported local servers: Ollama, LM Studio, llama.cpp, vLLM. Full guide in [`docs/NO-API-KEY.md`](docs/NO-API-KEY.md).

## Lint for AI slop and tells

```bash
warrantos slop docs/ README.md         # scan for scaffold residue and unsourced claims
warrantos tells docs/                  # scan for machine-writing tells, same flags
```

`slop` catches chat residue that shipped by accident: assistant openers and sign-offs, identity disclaimers, delivery framing, stray TODO placeholders, and factual sentences with no source in reach. One rule module, [`context_admissibility`](warrantos/provenance/context_admissibility.py), backs both `slop` and `check`, so a finding in one always traces to the same rule as a violation in the other.

`tells` goes one layer deeper: prose that is residue-free but still reads machine-written (contrastive negation, stacked hedges, em-dash punctuation, filler phrases, formulaic paragraph openers). It is opinionated where `slop` is objective, so it scores separately; philosophy and limits are in [`docs/TELLS.md`](docs/TELLS.md).

Both take `--json`, `--badge`, and `--fail-over N` for CI; fenced code is skipped unless you pass `--include-fences`. This repository holds itself to both: the docs scan slop-free and tells-clean.

## Audit trail

Every checked run can be sealed into a portable `.warrant` bundle:

```bash
warrantos attest final.md --run-dir .warrant/runs/<id> --out final.warrant
warrantos verify-external final.warrant --prose final.md   # exits non-zero on any failure
```

A third party verifies the bundle offline: no ledger access, no network call, fail-closed. A zero-backend browser verifier ([`web/verify.html`](web/verify.html)) covers readers who have only the file. Full detail in [`docs/VERIFICATION.md`](docs/VERIFICATION.md); the ISO/IEC 42001 and NIST AI RMF control mapping is in [`docs/COMPLIANCE.md`](docs/COMPLIANCE.md).

## Gate your agent

```bash
pip install "warrantos[mcp]"
warrantos-mcp                # stdio MCP server for Claude Code / Claude Desktop
```

The Claude Code Stop hook (`warrantos-verify-hook`) checks what the model wrote before the turn ends: stdlib only, no network, never breaks the session. The same gate covers an agent's own status reports and handoffs, so an operator can check what the agent claims against what it can source, rather than trust the summary on its face. Wiring in [`docs/MCP-CONFIG.md`](docs/MCP-CONFIG.md); hook source in [`warrantos/hooks/`](warrantos/hooks/).

## Measured, not promised

- **Grader accuracy**, 60-item labelled grader corpus ([`eval/corpus/grader.jsonl`](eval/corpus/grader.jsonl), harness [`eval/run_eval.py`](eval/run_eval.py)): 0.90 overall accuracy. It now catches anchored numeric and directional contradictions, 11 of 16 gold-contradicted items, with zero false "contradicted" calls on that corpus. The remaining 4 of 16 are paraphrase-level contradictions the heuristic cannot reach; those need an LLM-backed grader.
- **False-positive proxy**, 3,421 sentences of installed-package documentation ([`eval/measure_precision.py`](eval/measure_precision.py)): 5.1% of sentences fire at least one citation trigger. Treat this as a proxy upper bound only; the corpus is underpowered and the script says so plainly.
- **Unsupported-claim detection**, 47-item seed corpus ([`eval/run_eval.py`](eval/run_eval.py)): axis-1 precision 0.9545, recall 1.0000.

Every figure above is from a small, hand-built corpus. Numbers are corpus-dependent: run the harness on your own text before relying on any of them. Methodology and caveats in [`eval/README.md`](eval/README.md).

## What this does not do

WarrantOS does not detect truth, and does not try to. The claim detector is a heuristic: expect false positives and false negatives. Offline verification checks token overlap, not meaning, so a correctly sourced claim can still mislead. What the tool guarantees is narrower: an unsourced or unchecked claim becomes expensive instead of invisible, and the miss goes on the record. It does not replace human review. Full list in [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md).

## Where to go deeper

| Doc | What it covers |
|---|---|
| [`docs/QUICKSTART.md`](docs/QUICKSTART.md) | Five-minute tour with each output line explained |
| [`docs/SPEC.md`](docs/SPEC.md) | The normative specification |
| [`docs/FULL-OVERVIEW.md`](docs/FULL-OVERVIEW.md) | Full narrative, tooling map, release history |

Also known as: `claude-provenance` (GitHub, legacy plugin name); `warrantos` on PyPI and the CLI.

## Licence

MIT. Built by Juan Vega, Prometheus Policy Lab, in a personal capacity. Not associated with, funded by, or endorsed by any employer or government.
