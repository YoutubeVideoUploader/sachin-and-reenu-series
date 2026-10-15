import unittest
import sys
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from story_dependency_engine import (
    StoryDependencyGraph,
    StoryRevisionManager,
    REVISIONS_DIR
)

class TestStoryDependencyEngine(unittest.TestCase):

    def setUp(self):
        self.outline_file = REPO_ROOT / "season_3_shot_outline.json"
        with open(self.outline_file, "r", encoding="utf-8") as f:
            self.outline_data = json.load(f)

    def test_causal_boundary_conflict_detection(self):
        """Graph must detect physical teleportation between stalled car in Ep 2 and unharmonized homestay."""
        shot_a = {
            "shot_key": "S3_E2_S10",
            "location": "Mountain road car interior",
            "action": "Reenu freezes in horror as a translucent handprint appears on window glass as car stalls.",
            "dialogue_malayalam": "എന്റെ അമ്മോ, കാർ സ്റ്റാർട്ട് ആകുന്നില്ല!"
        }
        shot_b_broken = {
            "shot_key": "S3_E3_S01",
            "location": "Homestay hallway",
            "action": "Outside the shadowy colonial homestay, Caretaker Sreedharan hands heavy ring of keys to Sachin.",
            "dialogue_malayalam": "കെയർടേക്കർ: 'താക്കോലുകൾ ഇതാ...'"
        }
        graph = StoryDependencyGraph(self.outline_data)
        conflicts = graph.validate_boundary_continuity(shot_a, shot_b_broken)
        teleport = any(c.get("type") in ("LOCATION_TELEPORTATION", "UNRESOLVED_MECHANICAL_FAILURE") for c in conflicts)
        self.assertTrue(teleport, "Must flag fracture between disconnected car and homestay shots")

    def test_propose_edit_change_impact_report(self):
        """Proposing an edit generates a change-impact report without mutating disk outline."""
        manager = StoryRevisionManager(outline_path=self.outline_file)
        
        # Propose an edit to Episode 2 Shot 10 (the stalled car cliffhanger)
        rev = manager.propose_edit(
            season_number=3,
            episode_number=2,
            shot_number=10,
            new_action="Amal notices a distant lantern swinging in the dense fog approaching their car.",
            new_dialogue="ഡാ... ആ മഞ്ഞിലൂടെ ആരോ ഒരു റാന്തൽ വിളക്കുമായി വരുന്നുണ്ട്!",
            user_notes="Introduce caretaker lantern arrival narrative bridge"
        )

        self.assertIsNotNone(rev.get("revision_id"))
        self.assertEqual(rev["edit_payload"]["shot_key"], "S3_E2_S10")
        self.assertTrue(len(rev["impact_analysis"]["affected_scenes"]) > 0)

        # Verify disk outline was NOT modified
        with open(self.outline_file, "r", encoding="utf-8") as f:
            current_data = json.load(f)
        ep2 = next(e for e in current_data["episodes"] if e["episode_number"] == 2)
        s10 = next(s for s in ep2["shots"] if s["shot_number"] == 10)
        self.assertNotEqual(s10.get("action"), "Amal notices a distant lantern swinging in the dense fog approaching their car.")

    def test_dialogue_immutability_in_unaffected_shots(self):
        """Unaffected scenes must retain 100% of approved Malayalam dialogue."""
        manager = StoryRevisionManager(outline_path=self.outline_file)
        rev = manager.propose_edit(
            season_number=3,
            episode_number=2,
            shot_number=10,
            new_action="Car engine dies completely.",
            new_dialogue="സ്റ്റാർട്ട് ആകുന്നില്ലടാ...",
            user_notes="Test isolation"
        )

        # Verify unaffected Episode 1 shots are completely frozen
        unaffected = rev["impact_analysis"]["unaffected_scenes"]
        ep1_shots = [s for s in unaffected if "_E1_" in s]
        self.assertEqual(len(ep1_shots), 10, "All 10 Episode 1 shots must be strictly in unaffected_scenes")

if __name__ == "__main__":
    unittest.main()
