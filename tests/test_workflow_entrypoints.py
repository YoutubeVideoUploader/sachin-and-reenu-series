#!/usr/bin/env python3
"""
=============================================================================
WORKFLOW ENTRY POINTS INTEGRATION TEST SUITE
Sachin & Reenu AI Animation Studio
=============================================================================
Tests and validates that all real editing entry points route through the
canonical Season-Wide Butterfly-Effect Story Propagation Engine:
1. scripts/push_corrected_shot.py (CLI entry point for episode/shot updates)
2. scripts/universal_continuity_engine.py (Programmatic API entry point)
3. scripts/story_and_prompt_engine.py (Showrunner reharmonize entry point)
4. scripts/update_portals.py (Synchronization to all workspace portal.html files)
=============================================================================
"""

import os
import sys
import json
import shutil
import tempfile
import unittest
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from season_story_propagation_engine import SeasonStoryPropagationEngine
from universal_continuity_engine import edit_episode_event_with_propagation
from story_and_prompt_engine import reharmonize_outline_from_pivot


class TestWorkflowEntryPoints(unittest.TestCase):
    """Verifies that all editing entry points unify around the same engine."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="sachin_reenu_entrypoints_")
        self.sandbox_path = Path(self.temp_dir)

        shutil.copy(REPO_ROOT / "season_3_shot_outline.json", self.sandbox_path / "season_3_shot_outline.json")
        shutil.copy(REPO_ROOT / "story_state.json", self.sandbox_path / "story_state.json")
        shutil.copy(REPO_ROOT / "current_episode_shots.json", self.sandbox_path / "current_episode_shots.json")
        shutil.copy(REPO_ROOT / "portal.html", self.sandbox_path / "portal.html")
        shutil.copytree(REPO_ROOT / "scripts", self.sandbox_path / "scripts")

        self.baseline_outline = (self.sandbox_path / "season_3_shot_outline.json").read_bytes()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_push_corrected_shot_cli_generates_propagation_report(self):
        """
        Tests scripts/push_corrected_shot.py CLI invokes season propagation engine,
        generates the 11-point Change-Impact report, and supports --approve and --rollback.
        """
        cli_script = self.sandbox_path / "scripts" / "push_corrected_shot.py"

        # 1. Propose edit via CLI
        cmd_prop = [
            sys.executable, str(cli_script),
            "--season", "3",
            "--episode", "4",
            "--shot", "10",
            "--action", "Amal drops the vintage photo into the crevice.",
            "--dialogue", "അമൽ: 'അയ്യോ സച്ചിൻ! ഫോട്ടോ താഴെ വീണു!'",
            "--notes", "CLI test dropped photo"
        ]
        res_prop = subprocess.run(cmd_prop, cwd=str(self.sandbox_path), capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(res_prop.returncode, 0, f"CLI error: {res_prop.stderr}")
        self.assertIn("SEASON-WIDE CHANGE-IMPACT REPORT", res_prop.stdout)
        self.assertIn("Directly Affected Episodes", res_prop.stdout)
        self.assertIn("Grand Finale (Episode 10) Re-assessment", res_prop.stdout)

        # Extract revision ID
        rev_id = None
        for line in res_prop.stdout.splitlines():
            if "Revision `" in line:
                rev_id = line.split("Revision `")[1].split("`")[0]
                break
        self.assertIsNotNone(rev_id, "Could not extract revision ID from CLI output")

        # 2. Approve via CLI
        cmd_app = [
            sys.executable, str(cli_script),
            "--approve", rev_id
        ]
        res_app = subprocess.run(cmd_app, cwd=str(self.sandbox_path), capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(res_app.returncode, 0, f"Approve error: {res_app.stderr}")
        self.assertIn("Successfully approved", res_app.stdout)

        # Verify outline was updated
        updated_outline = (self.sandbox_path / "season_3_shot_outline.json").read_bytes()
        self.assertNotEqual(self.baseline_outline, updated_outline)

        # 3. Rollback via CLI
        cmd_roll = [
            sys.executable, str(cli_script),
            "--rollback", rev_id
        ]
        res_roll = subprocess.run(cmd_roll, cwd=str(self.sandbox_path), capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(res_roll.returncode, 0, f"Rollback error: {res_roll.stderr}")
        self.assertIn("Successfully rolled back", res_roll.stdout)

        # Verify exact baseline restoration
        restored_outline = (self.sandbox_path / "season_3_shot_outline.json").read_bytes()
        self.assertEqual(self.baseline_outline, restored_outline)

    def test_02_universal_continuity_engine_api_routes_to_propagation(self):
        """
        Tests universal_continuity_engine.edit_episode_event_with_propagation()
        programmatic API routes to SeasonStoryPropagationEngine.
        """
        report = edit_episode_event_with_propagation(
            season_number=3,
            episode_number=9,
            shot_number=2,
            new_action="Sreedharan reveals the secret is inside the Clock Tower.",
            new_dialogue="ശ്രീധരൻ: 'ആ സത്യം ക്ലോക്ക് ടവറിലാണ്!'",
            user_notes="Programmatic API propagation test",
            workspace_root=self.sandbox_path
        )

        self.assertIn("revision_id", report)
        self.assertIn("butterfly_impact", report)
        self.assertIn(10, report["butterfly_impact"]["affected_episodes"])
        self.assertTrue(report["butterfly_impact"]["grand_finale_evaluation"]["is_affected"])
        self.assertTrue(report["narrative_coherence"]["is_coherent"])

    def test_03_story_and_prompt_engine_reharmonize_routes_to_propagation(self):
        """
        Tests story_and_prompt_engine.reharmonize_outline_from_pivot()
        routes through SeasonStoryPropagationEngine without bypassing season safety.
        """
        res = reharmonize_outline_from_pivot(
            season_number=3,
            pivot_ep=7,
            pivot_shot=10,
            new_action="The suspension bridge collapses into the deep gorge.",
            new_dialogue="സച്ചിൻ: 'പാലം താഴേക്ക് വീഴുകയാണ്!'",
            workspace_root=self.sandbox_path,
            auto_commit=False
        )

        self.assertTrue(res["success"])
        self.assertIn("revision_id", res)
        self.assertIn("report", res)
        self.assertIn(10, res["report"]["butterfly_impact"]["affected_episodes"])

    def test_04_portal_sync_propagates_to_html(self):
        """
        Tests that scripts/update_portals.py injects episode and season outline data
        into portal.html.
        """
        portal_file = self.sandbox_path / "portal.html"
        self.assertTrue(portal_file.exists())

        # Run update_portals.py
        up_script = self.sandbox_path / "scripts" / "update_portals.py"
        run_res = subprocess.run([sys.executable, str(up_script)], cwd=str(self.sandbox_path), capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(run_res.returncode, 0, f"update_portals error: {run_res.stderr}")

        # Check that portal.html contains episodeData and seasonShotOutlineData
        portal_text = portal_file.read_text(encoding="utf-8")
        self.assertIn("let episodeData =", portal_text)
        self.assertIn("let seasonShotOutlineData =", portal_text)


if __name__ == "__main__":
    unittest.main()
