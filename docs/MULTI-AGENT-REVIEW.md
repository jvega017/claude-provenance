# Multi-Agent Review

Multi-Agent Review is the WarrantOS operating pattern for important artefacts.
The point is not to have more agents for its own sake. The point is to keep
generation, verification, adversarial review, and release judgement separate
enough that one fluent draft cannot silently carry unsupported claims or
inadmissible process context into publication.

The current `claude-provenance` repo supports this pattern through hooks,
CLI checks, ledger output, and CBOM reports. It does not yet provide a full
agent orchestrator.

## Review Roles

| Role | Job | Current repo support |
| --- | --- | --- |
| Writer | Draft or revise the artefact. | Outside this repo. |
| Provenance checker | Extract claims, bind sources, verify support where requested. | Hook, CLI, verifier, ledger. |
| Context reviewer | Classify workflow context and check prose-boundary leakage. | CBOM and Prose Boundary Gate in the current working tree. |
| Adversarial reviewer | Look for unsupported, misleading, stale, or overclaimed material. | Human or separate agent using exported reports. |
| Release owner | Decide whether the artefact can ship. | Human process, informed by ledger and CBOM. |

The separation can be human, model-based, or mixed. The important invariant is
that the same pass that creates the draft should not be the only pass that
declares it safe.

## Recommended Local Workflow

1. Draft the artefact.
2. Run the provenance check in report mode during drafting.
3. Run verification on cited claims when the document becomes consequential.
4. Prepare context input for CBOM if the artefact was shaped by feedback,
   prior drafts, tool traces, style instructions, or operator notes.
5. Run the CBOM and Prose Boundary Gate.
6. Have a separate reviewer inspect the claim report, CBOM, and final prose.
7. Release only after open unsupported claims, contradicted claims, and
   inadmissible process leakage have been resolved or explicitly waived.

Example commands:

```text
python cli/provenance_cli.py --ci final.md
python cli/provenance_cli.py --verify --json final.md
python cli/provenance_cli.py --cbom --context context.json --ci final.md
```

Use `--ci` when a blocked boundary or unsupported claim should fail the run.
Use `--json` when another tool or reviewer needs structured evidence.

## BriefLock as Review Gate

BriefLock is the name for the release gate that sits over this workflow. A
BriefLock profile may require:

- no unsupported load-bearing claims;
- no contradicted verified claims;
- CBOM generated for the artefact;
- Prose Boundary Gate passing for final prose;
- reviewer sign-off or documented waiver.

In this repo, those requirements are currently assembled from CLI outputs and
human process. A future product version could make them a first-class release
manifest.

## Reviewer Checklist

For claim provenance:

- Are all load-bearing factual claims sourced?
- Do cited sources actually support the claims?
- Are unsupported claims marked as `[CITE NEEDED]` only when that is acceptable
  for the artefact stage?
- Are `unverifiable`, `not_addressed`, and `error` verdicts resolved or
  explicitly carried as risk?

For context admissibility:

- Did feedback become a requirement rather than final-prose narration?
- Did style instructions shape prose without being announced?
- Were tool traces and operator notes kept out of reader-facing text?
- Was private reasoning excluded?
- Does the CBOM match the context actually used?

For product claims:

- Does the artefact avoid benchmark overclaims?
- Does it distinguish implemented behaviour from roadmap intent?
- Does it state limits plainly?

## Limits

Multi-Agent Review reduces single-pass failure modes. It does not guarantee
truth, legal compliance, policy approval, or publication readiness. The final
release decision remains a human governance decision.
