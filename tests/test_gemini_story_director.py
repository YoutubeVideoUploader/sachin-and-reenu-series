#!/usr/bin/env python3
"""
Unit and Integration Tests for Gemini AI Story & Shot Director (5-Tab Architecture)
"""

import sys
import json
import unittest
import tempfile
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from gemini_story_director import GeminiStoryDirector
from portal_backend_bridge import create_server
import urllib.request
import threading
import time


class TestGeminiStoryDirector(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sandbox = Path(self.temp_dir.name)
        
        # Copy canonical files
        shutil.copy2(REPO_ROOT / "season_3_shot_outline.json", self.sandbox / "season_3_shot_outline.json")
        shutil.copy2(REPO_ROOT / "story_state.json", self.sandbox / "story_state.json")
        shutil.copy2(REPO_ROOT / "current_episode_shots.json", self.sandbox / "current_episode_shots.json")
        shutil.copy2(REPO_ROOT / "portal.html", self.sandbox / "portal.html")
        shutil.copytree(SCRIPTS_DIR, self.sandbox / "scripts")

        self.director = GeminiStoryDirector(workspace_root=self.sandbox)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_evaluate_shot_continuity_detection(self):
        """Verify director detects physical location fracture when characters jump into a car."""
        # Episode 3 Shot 1 is outside homestay. If user says Sachin climbs into a car:
        eval_res = self.director.evaluate_shot_change(3, 1, "Sachin jumps into the car and slams the door")
        self.assertTrue(eval_res["success"])
        self.assertEqual(eval_res["episode_number"], 3)
        self.assertEqual(eval_res["shot_number"], 1)
        self.assertIn("Car Interior", eval_res["proposed_shot"]["location"])
        
        # Shot 2 is in homestay hallway -> Location fracture must be flagged!
        self.assertTrue(eval_res["has_inconsistency"])
        self.assertIn("Physical Location Fracture", eval_res["inconsistency_details"])
        self.assertEqual(eval_res["recommendation"], "EPISODE_STEER_RECOMMENDED")

    def test_02_apply_episode_wise_change_preserves_shot_10_and_rest_of_season(self):
        """Verify Episode-Wise change reconciles intermediate shots and keeps other episodes untouched."""
        proposed = {
            "episode_number": 3,
            "shot_number": 1,
            "speaker": "Sachin",
            "action": "Medium Shot (MS), Pixar 3D: Sachin nervously steps inside the car.",
            "dialogue_malayalam": "സച്ചിൻ: 'നമുക്ക് വേഗം വണ്ടി സ്റ്റാർട്ട് ചെയ്യാം.'",
            "location": "Car Interior / Mountain Road",
            "persistent_props": ["Keys"]
        }
        
        orig_data = self.director.load_outline()
        ep4_orig_action = orig_data["episodes"][3]["shots"][0]["action"] # Ep 4 Shot 1

        res = self.director.apply_episode_wise_change(3, 1, proposed)
        self.assertTrue(res["success"])
        self.assertEqual(res["scope"], "EPISODE_WISE")

        # Verify Shot 1 is updated
        updated_data = self.director.load_outline()
        ep3_shots = updated_data["episodes"][2]["shots"]
        self.assertEqual(ep3_shots[0]["location"], "Car Interior / Mountain Road")

        # Verify Shot 2 is realigned
        self.assertIn("Reacting to the events at Car Interior", ep3_shots[1]["action"])

        # Verify Episode 4 is completely untouched
        self.assertEqual(updated_data["episodes"][3]["shots"][0]["action"], ep4_orig_action)

    def test_03_apply_season_wise_change_freezes_preceding_shots(self):
        """Verify Season-Wise change strictly freezes 1 to K-1 shots and cascades downstream."""
        orig_data = self.director.load_outline()
        ep3_shot1_orig = dict(orig_data["episodes"][2]["shots"][0])

        proposed = {
            "episode_number": 3,
            "shot_number": 5,
            "speaker": "Amal",
            "action": "Amal discovers an ancient map showing the tea factory underground tunnel.",
            "dialogue_malayalam": "അമൽ: 'ഇവിടെ ഒരു രഹസ്യ തുരങ്കം ഉണ്ട്!'",
            "location": "Homestay Secret Tunnel",
            "persistent_props": ["Flashlight"]
        }

        res = self.director.apply_season_wise_change(3, 5, proposed)
        self.assertTrue(res["success"])
        self.assertEqual(res["scope"], "SEASON_WISE")

        updated_data = self.director.load_outline()
        ep3_shots = updated_data["episodes"][2]["shots"]
        
        # Verify shots 1..4 are STRICTLY FROZEN
        self.assertEqual(ep3_shots[0]["action"], ep3_shot1_orig["action"])
        self.assertEqual(ep3_shots[0]["speaker"], ep3_shot1_orig["speaker"])

        # Verify shot 5 is updated
        self.assertEqual(ep3_shots[4]["location"], "Homestay Secret Tunnel")

    def test_04_portal_html_contains_director_mode_selector_and_buttons(self):
        """Verify portal.html has 3-mode selector, dynamic options, evaluation card, and dual healing buttons."""
        portal_text = (self.sandbox / "portal.html").read_text(encoding="utf-8")
        
        self.assertIn("directorModeShotBtn", portal_text)
        self.assertIn("directorModeEpBtn", portal_text)
        self.assertIn("directorModeSeasonBtn", portal_text)
        self.assertIn("directorEvaluationContainer", portal_text)
        self.assertIn("applyEpisodeWiseDirectorChange", portal_text)
        self.assertIn("applySeasonWiseDirectorChange", portal_text)
        self.assertIn("setDirectorScopeMode", portal_text)
        self.assertIn("evaluateDirectorShotChange", portal_text)


if __name__ == "__main__":
    unittest.main()
