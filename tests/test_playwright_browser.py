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

from verify_real_browser_playwright import run_real_browser_verification


class TestPlaywrightBrowserAcceptance(unittest.TestCase):
    @unittest.skipUnless(HAS_PLAYWRIGHT, "Playwright is not installed or available in this environment")
    def test_full_browser_butterfly_edit_workflow(self):
        """
        Executes end-to-end browser automation:
        - Opens portal in Google Chrome
        - Selects S3_E4_S10 via Tab 7
        - Proposes 1994 photograph clue via Butterfly modal
        - Evaluates season-wide ripple
        - Approves and verifies DOM and disk sync
        - Rolls back and verifies byte-exact baseline restoration
        """
        out_dir = REPO_ROOT / "test_reports" / "browser_acceptance"
        results = run_real_browser_verification(output_dir=out_dir)
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
