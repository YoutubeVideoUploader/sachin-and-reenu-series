#!/usr/bin/env python3
"""
Playwright Browser Acceptance Test for Sachin & Reenu Studio
Automates the full 10-step browser lifecycle test in an isolated disposable sandbox.
"""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

import json
import subprocess


class TestPlaywrightBrowserAcceptance(unittest.TestCase):
    @unittest.skipUnless(HAS_PLAYWRIGHT, "Playwright is not installed or available in this environment")
    def test_full_browser_butterfly_edit_workflow(self):
        """
        Executes end-to-end browser automation in an isolated process:
        - Opens portal in Google Chrome
        - Selects S3_E4_S10 via Tab 7
        - Proposes 1994 photograph clue via Butterfly modal
        - Evaluates season-wide ripple
        - Approves and verifies DOM and disk sync
        - Rolls back and verifies byte-exact baseline restoration
        """
        script_path = SCRIPTS_DIR / "verify_real_browser_playwright.py"
        res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, cwd=str(REPO_ROOT))
        self.assertEqual(res.returncode, 0, f"Browser test process failed: {res.stderr}\n{res.stdout}")

        summary_file = REPO_ROOT / "test_reports" / "browser_acceptance" / "playwright_browser_test_summary.json"
        self.assertTrue(summary_file.exists(), "Summary report must be generated")
        with open(summary_file, "r", encoding="utf-8") as f:
            results = json.load(f)

        self.assertEqual(results.get("status"), "SUCCESS", f"Browser test failed: {results.get('error')}")
        self.assertIn("baseline_restored", results.get("screenshots", {}))
        
        hashes = results.get("file_hashes", {})
        baseline = hashes.get("baseline", {})
        restored = hashes.get("restored", {})
        committed = hashes.get("committed", {})

        self.assertNotEqual(baseline["season_3_shot_outline.json"], committed["season_3_shot_outline.json"])
        self.assertEqual(baseline["season_3_shot_outline.json"], restored["season_3_shot_outline.json"])
        self.assertEqual(baseline["story_state.json"], restored["story_state.json"])


if __name__ == "__main__":
    unittest.main()
