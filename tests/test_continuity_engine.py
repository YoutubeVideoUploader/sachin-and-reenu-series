import unittest
import sys
from pathlib import Path

# Add scripts directory to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from universal_continuity_engine import (
    compile_single_shot_prompt,
    UniversalSceneTracker,
    MASTER_STYLE,
    DNA_SACHIN,
    DNA_REENU,
    DNA_AMAL
)

class TestUniversalContinuityEngine(unittest.TestCase):

    def test_mathematical_proportions_and_anti_fat_guards(self):
        """Verify Pixar 1:6.5 proportions and strict anti-fat guards in character DNA."""
        for dna, name, expected_ratio in [
            (DNA_SACHIN, "Sachin", "1:6.5"),
            (DNA_REENU, "Reenu", "1:6.2"),
            (DNA_AMAL, "Amal", "1:6.5")
        ]:
            self.assertIn(expected_ratio, dna, f"{name} must enforce {expected_ratio} head-to-body proportion")
            self.assertIn("PROHIBIT OVERWEIGHT", dna, f"{name} must contain PROHIBIT OVERWEIGHT")
            self.assertIn("PROHIBIT CHUBBY", dna, f"{name} must contain PROHIBIT CHUBBY")
            self.assertIn("PROHIBIT FAT BODY", dna, f"{name} must contain PROHIBIT FAT BODY")

    def test_immutable_malayalam_dialogue(self):
        """User Malayalam dialogue must be preserved byte-for-byte with zero hallucination."""
        tracker = UniversalSceneTracker()
        sacred_dialogue = "വണ്ടി എന്താ പെട്ടെന്ന് നിന്നത്? എന്തെങ്കിലും പ്രശ്നമുണ്ടോ?"

        shot = compile_single_shot_prompt(
            shot_num=1,
            speaker="Sachin",
            dialogue_malayalam=sacred_dialogue,
            action="Sachin leans forward anxiously looking at the stalled engine dashboard.",
            location="Mountain road car interior",
            persistent_props=["Car dashboard", "Car keys"],
            scene_tracker=tracker
        )

        prompt_dialogue = shot["json_prompt"]["dialogue"]["line"]
        self.assertEqual(prompt_dialogue, sacred_dialogue, "Dialogue line must match input exactly")
        self.assertEqual(shot["dialogue_malayalam"], sacred_dialogue, "Top-level dialogue must match input exactly")
        self.assertEqual(shot["character"], "Sachin")

    def test_vehicle_role_invariance(self):
        """Vehicle roles must lock Amal as driver, Sachin as front passenger, Reenu as rear passenger."""
        tracker = UniversalSceneTracker()
        shot = compile_single_shot_prompt(
            shot_num=2,
            speaker="Amal",
            dialogue_malayalam="എനിക്ക് ഒന്നും മനസ്സിലാകുന്നില്ലടാ, പെട്ടെന്ന് ഓഫ് ആയിപ്പോയി.",
            action="Amal desperately turns the ignition key in the car.",
            location="Mountain road car interior",
            persistent_props=["Car steering wheel", "Car keys"],
            scene_tracker=tracker
        )

        spatial = shot["json_prompt"]["sequence_continuity"]["spatial_blocking"]
        self.assertIn("Amal", spatial)
        self.assertIn("Driver seat", spatial["Amal"], "Amal must be locked to Driver seat")

        # Now Sachin speaks in the same vehicle scene
        shot2 = compile_single_shot_prompt(
            shot_num=3,
            speaker="Sachin",
            dialogue_malayalam="പുറത്ത് ഭയങ്കര മൂടൽമഞ്ഞാണ്, ഒന്നും കാണാൻ പറ്റുന്നില്ല.",
            action="Sachin peers through the misty front windshield.",
            location="Mountain road car interior",
            persistent_props=["Car steering wheel", "Car keys"],
            scene_tracker=tracker
        )
        spatial2 = shot2["json_prompt"]["sequence_continuity"]["spatial_blocking"]
        self.assertIn("Amal", spatial2)
        self.assertIn("Driver seat", spatial2["Amal"], "Amal must remain Driver across consecutive shots")

    def test_lip_sync_and_bgm_prohibition(self):
        """Spoken dialogue must mandate animated lips and strictly prohibit BGM in audio directive."""
        tracker = UniversalSceneTracker()
        shot = compile_single_shot_prompt(
            shot_num=4,
            speaker="Reenu",
            dialogue_malayalam="സച്ചിൻ... ആ ജനലിൽ എന്തോ ഒന്ന് കണ്ടു!",
            action="Reenu points trembling toward the fog-covered car window.",
            location="Mountain road car interior",
            persistent_props=["Car keys"],
            scene_tracker=tracker
        )

        audio_directive = shot["json_prompt"]["audio_directive"]
        self.assertIn("ABSOLUTELY NO BACKGROUND MUSIC", audio_directive)
        self.assertIn("CHARACTER DIALOGUE SPOKEN BY REENU", audio_directive)
        self.assertIn("Character Dialogue (Reenu Speaking)", shot["json_prompt"]["perspective"])

if __name__ == "__main__":
    unittest.main()
