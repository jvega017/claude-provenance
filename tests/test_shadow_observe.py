#!/usr/bin/env python3
"""Tests for tools/warrantos-shadow-observe.py (Path X4-B).

The observer is read-only and must never modify any production
artefact. These tests cover:

- find_latest_brief returns the most recent file by mtime
- find_latest_brief returns None when the directory is missing or empty
- observe_one writes a one-line JSON summary to the log
- the shadow log row carries the explicit "NOT enforced" note
- a missing brief writes a no_brief_found row rather than raising
"""

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

# Add tools/ to sys.path so we can import the observer module.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

# Import the module under test as a plain module. The file name uses
# a hyphen so importlib is the cleanest path.
import importlib.util

_SPEC = importlib.util.spec_from_file_location(
    "warrantos_shadow_observe",
    _TOOLS_DIR / "warrantos-shadow-observe.py",
)
warrantos_shadow_observe = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(warrantos_shadow_observe)


class TestFindLatestBrief(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_returns_most_recent_md(self):
        first = self.tmp / "older.md"
        first.write_text("# Older\n", encoding="utf-8")
        time.sleep(0.05)
        second = self.tmp / "newer.md"
        second.write_text("# Newer\n", encoding="utf-8")

        result = warrantos_shadow_observe.find_latest_brief(self.tmp)
        self.assertEqual(result, second)

    def test_missing_directory_returns_none(self):
        result = warrantos_shadow_observe.find_latest_brief(
            self.tmp / "absent"
        )
        self.assertIsNone(result)

    def test_empty_directory_returns_none(self):
        result = warrantos_shadow_observe.find_latest_brief(self.tmp)
        self.assertIsNone(result)


class TestObserveOne(unittest.TestCase):
    """observe_one runs the harness in observation mode and logs one row."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.brief = self.tmp / "brief.md"
        self.brief.write_text(
            "# Morning brief\n\nNeutral paragraph. No claims fired.\n",
            encoding="utf-8",
        )
        self.log = self.tmp / "shadow.log"

    def tearDown(self):
        self._tmp.cleanup()

    def test_observed_row_written(self):
        rc = warrantos_shadow_observe.observe_one(
            self.brief, "brief-light", False, self.log
        )
        self.assertEqual(rc, 0)
        self.assertTrue(self.log.is_file())
        lines = self.log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        row = json.loads(lines[0])
        self.assertEqual(row["shadow_status"], "observed")
        self.assertEqual(row["profile"], "brief-light")
        self.assertIn("verdict", row)
        self.assertIn("NOT enforced", row["note"])

    def test_multiple_runs_append(self):
        warrantos_shadow_observe.observe_one(
            self.brief, "brief-light", False, self.log
        )
        warrantos_shadow_observe.observe_one(
            self.brief, "brief-light", False, self.log
        )
        lines = self.log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)


class TestMain(unittest.TestCase):
    """The main entrypoint never raises and always returns 0."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.log = self.tmp / "shadow.log"

    def tearDown(self):
        self._tmp.cleanup()

    def test_no_brief_writes_status_row(self):
        rc = warrantos_shadow_observe.main(
            ["--brief-dir", str(self.tmp / "absent"), "--log", str(self.log)]
        )
        self.assertEqual(rc, 0)
        self.assertTrue(self.log.is_file())
        row = json.loads(self.log.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(row["shadow_status"], "no_brief_found")

    def test_main_with_real_brief(self):
        brief = self.tmp / "brief.md"
        brief.write_text("# Brief\n\nNeutral content.\n", encoding="utf-8")
        rc = warrantos_shadow_observe.main(
            [
                "--brief-dir", str(self.tmp),
                "--log", str(self.log),
                "--profile", "brief-light",
            ]
        )
        self.assertEqual(rc, 0)
        row = json.loads(self.log.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(row["shadow_status"], "observed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
