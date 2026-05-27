#!/usr/bin/env python3
"""warrantos: integration CLI for the WarrantOS provenance and admissibility stack.

This is the Day-4 scaffold. It parses arguments, loads the draft and the
optional context input file, classifies each context item through Layer 1
(with source_agent threading per SPEC-L1-S005), and prints a structured
summary. Day 5 will wire the full pipeline (Layer 2 persistence, Layer 7
G1 + G2 gates, CBOM v0.2 assembly, override-aware consolidated verdict,
reader-facing footer).

Usage
-----

    python cli/warrantos_cli.py check DRAFT.md [--context CONTEXT.json]
        [--profile final-prose|paper-full|brief-light|audit|...]
        [--run-id RUN_ID]
        [--db PATH_TO_LEDGER.db]
        [--json] [--ci] [--verify]

The context file format is a JSON list of objects::

    [
        {"id": "ctx_001", "text": "...", "source_agent": "policy-red-team"},
        {"id": "ctx_002", "text": "..."}
    ]

source_agent is optional but recommended: when present and the value is
in REVIEW_ROLE_REGISTRY, Layer 1 forces the classification to
review_finding ahead of the rule-based decision tree (SPEC-L1-S005).

Stdlib only. Python 3.8 compatible.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import List, Optional

# Make the repository root importable when running this file directly.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from provenance.context_admissibility import ContextItem, classify_context  # noqa: E402


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="warrantos",
        description=(
            "WarrantOS integration CLI. Day-4 scaffold: classifies context "
            "and emits a structured summary. The full pipeline (Layer 2 "
            "persistence, Layer 7 G1+G2 gates, CBOM v0.2, consolidated "
            "verdict, reader-facing override footer) lands in Day 5."
        ),
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    check = sub.add_parser(
        "check",
        help="Run the WarrantOS check pipeline over a draft artefact.",
        description=(
            "Run the WarrantOS check pipeline over a draft artefact. "
            "Day-4 scaffold prints classified context only; the gates "
            "and CBOM are Day 5."
        ),
    )
    check.add_argument("draft", help="Path to the draft Markdown file.")
    check.add_argument(
        "--context",
        default=None,
        help="Path to a JSON file with context items (see module docstring).",
    )
    check.add_argument(
        "--profile",
        default="final-prose",
        choices=(
            "final-prose",
            "brief-light",
            "paper-full",
            "audit",
            "methodology",
            "consultation_report",
            "changelog",
        ),
        help="Layer 7 G1 boundary profile (default: final-prose).",
    )
    check.add_argument(
        "--run-id",
        default=None,
        help="Stable run identifier. Generated when absent.",
    )
    check.add_argument(
        "--db",
        default=str(Path(".warrant") / "provenance.db"),
        help="Path to the ledger database (created if absent). Day 5 uses this.",
    )
    check.add_argument(
        "--json",
        action="store_true",
        help="Emit the summary as JSON instead of text.",
    )
    check.add_argument(
        "--ci",
        action="store_true",
        help=(
            "Exit non-zero on a HOLD or BLOCK verdict. Day 4 always exits 0 "
            "because the consolidated verdict is Day 5."
        ),
    )
    check.add_argument(
        "--verify",
        action="store_true",
        help=(
            "Run the out-of-band claim verifier where available. Day 4 "
            "scaffold parses the flag but does not act on it."
        ),
    )

    return parser


# ---------------------------------------------------------------------------
# Input loading
# ---------------------------------------------------------------------------

def load_draft(path: str) -> str:
    """Read the draft Markdown file."""
    return Path(path).read_text(encoding="utf-8")


def load_context(path: Optional[str]) -> List[dict]:
    """Load the optional JSON context file.

    Returns an empty list when path is None or the file does not exist.
    """
    if not path:
        return []
    p = Path(path)
    if not p.is_file():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("context file must be a JSON list of items")
    return data


# ---------------------------------------------------------------------------
# Pipeline (Day-4 partial: Layer 1 only)
# ---------------------------------------------------------------------------

def classify_all(items: List[dict]) -> List[ContextItem]:
    """Run Layer 1 over every context item, threading source_agent."""
    result = []
    for raw in items:
        if not isinstance(raw, dict):
            continue
        context_id = str(raw.get("id") or raw.get("context_id") or "ctx_" + uuid.uuid4().hex[:8])
        text = str(raw.get("text") or "")
        source_agent = raw.get("source_agent")
        item = classify_context(context_id, text, source_agent=source_agent)
        result.append(item)
    return result


def summarise(items: List[ContextItem], draft_chars: int, run_id: str) -> dict:
    """Build the Day-4 structured summary."""
    by_type: dict = {}
    by_bucket: dict = {}
    for item in items:
        by_type[item.context_type] = by_type.get(item.context_type, 0) + 1
        by_bucket[item.ledger_bucket] = by_bucket.get(item.ledger_bucket, 0) + 1

    return {
        "run_id": run_id,
        "stage": "day-4-scaffold",
        "draft_chars": draft_chars,
        "context_items": len(items),
        "by_context_type": by_type,
        "by_ledger_bucket": by_bucket,
        "next_stage_note": (
            "Day 5 wires Layer 2 persistence, Layer 7 G1+G2, CBOM v0.2 "
            "assembly with actor_identity and classification_overrides, "
            "and the consolidated verdict (PASS/HOLD/BLOCK/NOT_ASSESSABLE)."
        ),
    }


def format_text_summary(summary: dict) -> str:
    """Render the JSON summary as a short stdout block."""
    lines = []
    lines.append("warrantos check (Day-4 scaffold)")
    lines.append("  run id:        %s" % summary["run_id"])
    lines.append("  draft chars:   %d" % summary["draft_chars"])
    lines.append("  context items: %d" % summary["context_items"])
    if summary["by_context_type"]:
        lines.append("  by context_type:")
        for k in sorted(summary["by_context_type"]):
            lines.append("    %-22s %d" % (k, summary["by_context_type"][k]))
    if summary["by_ledger_bucket"]:
        lines.append("  by ledger_bucket:")
        for k in sorted(summary["by_ledger_bucket"]):
            lines.append("    %-22s %d" % (k, summary["by_ledger_bucket"][k]))
    lines.append("")
    lines.append("note: " + summary["next_stage_note"])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command != "check":
        parser.print_help()
        return 0

    run_id = args.run_id or "run_" + uuid.uuid4().hex[:12]

    try:
        draft = load_draft(args.draft)
    except FileNotFoundError:
        sys.stderr.write("warrantos: draft file not found: %s\n" % args.draft)
        return 2

    try:
        context_items_raw = load_context(args.context)
    except (ValueError, json.JSONDecodeError) as exc:
        sys.stderr.write("warrantos: context file invalid: %s\n" % exc)
        return 2

    classified = classify_all(context_items_raw)
    summary = summarise(classified, draft_chars=len(draft), run_id=run_id)

    if args.json:
        sys.stdout.write(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(format_text_summary(summary) + "\n")

    # Day-4 scaffold always exits 0. Day 5 wires the consolidated verdict.
    return 0


if __name__ == "__main__":
    sys.exit(main())
