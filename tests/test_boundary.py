#!/usr/bin/env python3
"""Tests for the reusable prose-boundary gate."""

import unittest

from provenance.boundary import check_boundary


class TestBoundaryProfiles(unittest.TestCase):

    def test_final_prose_blocks_original_process_leakage_examples(self):
        text = "\n".join([
            "Based on your feedback, this version is more commercial.",
            "Build policy-r6-1716-2026-05-23.",
            "[archive only] LinkedIn: draft hook.",
        ])

        result = check_boundary(text, profile="final-prose")

        self.assertEqual(result.verdict, "blocked")
        self.assertGreaterEqual(len(result.violations), 4)
        self.assertEqual(result.violations[0].line_number, 1)
        self.assertTrue(any(v.rule_id == "archive_only" for v in result.violations))
        self.assertTrue(any(v.rule_id == "build_label" for v in result.violations))

    def test_audit_profile_allows_process_language(self):
        result = check_boundary(
            "Based on your feedback, this version records the review history.",
            profile="audit",
        )

        self.assertEqual(result.verdict, "pass")
        self.assertEqual(result.violations, [])

    def test_paper_full_blocks_process_narration_but_not_word_build_in_normal_use(self):
        result = check_boundary(
            "This version incorporates review feedback. Institutions build capability over time.",
            profile="paper-full",
        )

        self.assertEqual(result.verdict, "blocked")
        self.assertTrue(any(v.rule_id == "version_narration" for v in result.violations))
        self.assertFalse(any(v.rule_id == "build_label" for v in result.violations))


if __name__ == "__main__":
    unittest.main()

