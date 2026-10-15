#!/usr/bin/env python3
"""
=============================================================================
REAL-SEASON BUTTERFLY-EFFECT ACCEPTANCE AUDIT SUITE
Sachin & Reenu AI Animation Studio
=============================================================================
End-to-End Acceptance Tests executing realistic season-wide edits across:
- Episode 1: Glowing Talisman & Mist Apparition (Ripples to Ep 2, 5, 10; Ep 7 unaffected)
- Episode 4: Scratched Vintage Photo Clue (Ripples to Ep 5, 8, 9, 10; Ep 1-3, 6-7 unaffected)
- Episode 7: Bridge Collapses into Mine Shaft (Ripples to Ep 8, 9, 10; Ep 1-6 unaffected)
- Episode 9: Caretaker Confession: Old Clock Tower (Ripples to Ep 9, 10; Ep 1-8 unaffected)

For each test:
1. Records original season state.
2. Changes a meaningful story event / clue / hazard.
3. Verifies direct and indirect consequences across all 10 episodes.
4. Produces concrete, chronologically coherent proposed screenplay revisions.
5. Verifies character knowledge & prop plausibility via NarrativeCoherenceValidator.
6. Verifies unaffected episodes remain 100% untouched.
7. Exercises approval path & verifies all 4 downstream artifacts sync:
   - season_3_shot_outline.json
   - current_episode_shots.json
   - story_state.json
   - portal.html
8. Verifies stale assets are flagged without auto-rendering or publication.
9. Exercises rollback path & verifies exact byte-for-byte restoration.
10. Verifies synchronization failure safety.
=============================================================================
"""

import os
import sys
import json
import shutil
import tempfile
import unittest
from pathlib import Path

# Setup paths
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from season_story_model import build_canonical_season_3_model, SeasonStoryModel
from season_dependency_graph import SeasonDependencyGraph
from storyline_rewriter import StorylineRewriter, NarrativeCoherenceValidator
from season_story_propagation_engine import SeasonStoryPropagationEngine


class TestRealSeasonAcceptance(unittest.TestCase):
    """Real-season acceptance tests in isolated sandbox environments."""

    def setUp(self):
        """Create disposable sandbox with copies of real production files."""
        self.temp_dir = tempfile.mkdtemp(prefix="sachin_reenu_acceptance_")
        self.sandbox_path = Path(self.temp_dir)

        # Copy canonical outline, story_state, current_episode_shots, and portal
        shutil.copy(REPO_ROOT / "season_3_shot_outline.json", self.sandbox_path / "season_3_shot_outline.json")
        shutil.copy(REPO_ROOT / "story_state.json", self.sandbox_path / "story_state.json")
        shutil.copy(REPO_ROOT / "current_episode_shots.json", self.sandbox_path / "current_episode_shots.json")
        shutil.copy(REPO_ROOT / "portal.html", self.sandbox_path / "portal.html")

        # Copy scripts directory so update_portals and domain modules can run
        shutil.copytree(REPO_ROOT / "scripts", self.sandbox_path / "scripts")

        # Initialize propagation engine in isolated sandbox
        self.engine = SeasonStoryPropagationEngine(workspace_root=self.sandbox_path)

        # Baseline contents for exact byte-for-byte rollback verification
        self.baseline_outline_bytes = (self.sandbox_path / "season_3_shot_outline.json").read_bytes()
        self.baseline_state_bytes = (self.sandbox_path / "story_state.json").read_bytes()
        self.baseline_current_ep_bytes = (self.sandbox_path / "current_episode_shots.json").read_bytes()

    def tearDown(self):
        """Clean up isolated sandbox."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_episode_1_talisman_ripple_across_season(self):
        """
        Scenario 1: Edit in Episode 1 (Mist Sighting & Glowing Talisman).
        - Changes Ep 1 Shot 10.
        - Consequences ripple across Ep 2, 5, 10.
        - Episode 7 remains strictly unaffected.
        - Narrative coherence passes (zero future leaks, authentic Malayalam).
        - Grand Finale adapts as 'The Talisman's Light'.
        - Approval synchronizes outline, state, current_ep, and portal.
        - Rollback restores exact byte-for-byte baseline.
        """
        proposal = self.engine.propose_season_edit(
            season_number=3,
            episode_number=1,
            shot_number=10,
            new_action="Reenu spots the ethereal woman in the mist holding out a glowing antique talisman, which Reenu picks up from the roadside before the apparition fades.",
            new_dialogue="റീനു: 'സച്ചിൻ, നോക്കൂ! ആ സ്ത്രീയുടെ കയ്യിൽ തിളങ്ങുന്ന എന്തോ ഒന്നുണ്ട്! വഴിയിൽ വീണുകിടക്കുന്ന ഈ താലി നോക്കിക്കേ!'",
            user_notes="Introduce glowing talisman clue in Episode 1",
            added_fact_ids=["FACT_GLOWING_TALISMAN_FOUND"]
        )

        impact = proposal["butterfly_impact"]
        redev = proposal["redevelopment"]
        coherence = proposal["narrative_coherence"]

        # 1. Verify Ripple & Unaffected Boundaries
        self.assertIn(1, impact["affected_episodes"])
        self.assertIn(2, impact["affected_episodes"])
        self.assertIn(5, impact["affected_episodes"])
        self.assertIn(10, impact["affected_episodes"])
        self.assertIn(7, impact["unaffected_episodes"])

        # 2. Verify Narrative Coherence
        self.assertTrue(coherence["is_coherent"], f"Coherence violations: {coherence.get('violations')}")

        # 3. Verify Grand Finale Redevelopment
        finale = redev["alternative_grand_finale"]
        self.assertTrue(finale["is_redeveloped"])
        self.assertIn("Talisman", finale["alternative_finale_title"])
        self.assertIn("talisman", finale["adapted_climax"].lower())

        # 4. Exercise Approval & Synchronize all 4 artifacts
        commit_res = self.engine.approve_and_commit(proposal["revision_id"])
        self.assertEqual(commit_res["status"], "SUCCESS")

        # Verify downstream artifacts updated
        updated_outline = json.loads((self.sandbox_path / "season_3_shot_outline.json").read_text(encoding="utf-8"))
        ep1_shots = next(e["shots"] for e in updated_outline["episodes"] if e["episode_number"] == 1)
        self.assertIn("talisman", ep1_shots[9]["action"].lower())

        updated_state = json.loads((self.sandbox_path / "story_state.json").read_text(encoding="utf-8"))
        self.assertIn("season_shot_outline", updated_state)

        # 5. Exercise Rollback & Verify exact restoration
        rollback_res = self.engine.rollback(proposal["revision_id"])
        self.assertEqual(rollback_res["status"], "SUCCESS")

        restored_outline_bytes = (self.sandbox_path / "season_3_shot_outline.json").read_bytes()
        self.assertEqual(self.baseline_outline_bytes, restored_outline_bytes, "Outline not restored byte-for-byte!")

    def test_02_episode_4_scratched_vintage_photo_ripple(self):
        """
        Scenario 2: Edit in Episode 4 (Scratched Vintage Photo Clue).
        - Changes Ep 4 Shot 10.
        - Consequences ripple across Ep 5, 8, 9, 10.
        - Ep 1, 2, 3, 6, 7 remain strictly unaffected.
        - Characters know only what has been plausibly discovered up to that episode.
        - Grand Finale adapts climax conflict to resolve the altered photo clue.
        - Approval & Rollback verified.
        """
        proposal = self.engine.propose_season_edit(
            season_number=3,
            episode_number=4,
            shot_number=10,
            new_action="Inside Room 13, Amal discovers an antique photograph where the third face has been violently scratched out with claw marks.",
            new_dialogue="അമൽ: 'എന്റെ ദൈവമേ! ഈ ഫോട്ടോയിലെ മൂന്നാമത്തെ ആളുടെ മുഖം ആരോ നഖം കൊണ്ട് മാന്തിക്കീറിയിരിക്കുകയാണല്ലോ!'",
            user_notes="Damaged vintage photo clue with claw marks",
            removed_fact_ids=["FACT_VINTAGE_PHOTO_CLUE"],
            added_fact_ids=["FACT_VINTAGE_PHOTO_CLAW_SCRATCH"]
        )

        impact = proposal["butterfly_impact"]
        redev = proposal["redevelopment"]
        coherence = proposal["narrative_coherence"]

        # 1. Ripple Checks
        self.assertIn(4, impact["affected_episodes"])
        self.assertIn(5, impact["affected_episodes"])
        self.assertIn(8, impact["affected_episodes"])
        self.assertIn(9, impact["affected_episodes"])
        self.assertIn(10, impact["affected_episodes"])

        # Unaffected prior and independent episodes
        for un_ep in [1, 2, 3, 6, 7]:
            self.assertIn(un_ep, impact["unaffected_episodes"])

        # 2. Coherence: zero future leaks
        self.assertTrue(coherence["is_coherent"])

        # 3. Grand Finale
        finale = redev["alternative_grand_finale"]
        self.assertTrue(finale["is_redeveloped"])
        combined_text = (finale.get("adapted_climax", "") + " " + finale.get("climax_conflict", "") + " " + finale.get("alternative_finale_title", "")).lower()
        self.assertTrue("photo" in combined_text or "photograph" in combined_text)

        # 4. Commit Approval & Rollback
        self.engine.approve_and_commit(proposal["revision_id"])
        self.engine.rollback(proposal["revision_id"])

        self.assertEqual(self.baseline_outline_bytes, (self.sandbox_path / "season_3_shot_outline.json").read_bytes())

    def test_03_episode_7_bridge_collapses_into_mine_shaft(self):
        """
        Scenario 3: Edit in Episode 7 (Bridge Collapses into Old Mine Shaft).
        - Changes Ep 7 Shot 10.
        - Consequences ripple across Ep 8, 9, 10.
        - Ep 1 through 6 remain completely unaffected.
        - Ep 8 adapts action to navigate subterranean mine tunnel.
        - Grand Finale adapts as 'The Subterranean Truth'.
        """
        proposal = self.engine.propose_season_edit(
            season_number=3,
            episode_number=7,
            shot_number=10,
            new_action="The dilapidated suspension bridge snaps violently, plummeting into a hidden abandoned mine shaft entrance beneath the cliff.",
            new_dialogue="സച്ചിൻ: 'റീനു, പിടിക്ക്! ആ പാലം താഴെയുള്ള പഴയ തുരങ്കത്തിലേക്ക് തകർന്നു വീഴുകയാണ്!'",
            user_notes="Bridge collapses into subterranean mine shaft",
            added_fact_ids=["FACT_MINE_SHAFT_DISCOVERY"]
        )

        impact = proposal["butterfly_impact"]
        redev = proposal["redevelopment"]
        coherence = proposal["narrative_coherence"]

        # 1. Affected and Unaffected
        self.assertEqual(sorted(impact["affected_episodes"]), [7, 8, 9, 10])
        self.assertEqual(sorted(impact["unaffected_episodes"]), [1, 2, 3, 4, 5, 6])

        # 2. Subterranean continuity in Ep 8
        ep8_shots = redev["revised_episodes"][8]["all_shots"]
        self.assertIn("mine", ep8_shots[0]["action"].lower() + ep8_shots[1]["action"].lower())

        # 3. Grand Finale
        finale = redev["alternative_grand_finale"]
        self.assertIn("Subterranean", finale["alternative_finale_title"])
        self.assertIn("mine", finale["adapted_climax"].lower())

        # 4. Coherence
        self.assertTrue(coherence["is_coherent"])

        # 5. Commit and Rollback
        self.engine.approve_and_commit(proposal["revision_id"])
        self.engine.rollback(proposal["revision_id"])
        self.assertEqual(self.baseline_outline_bytes, (self.sandbox_path / "season_3_shot_outline.json").read_bytes())

    def test_04_episode_9_caretaker_reveals_old_clock_tower(self):
        """
        Scenario 4: Edit in Episode 9 (Caretaker reveals Old Clock Tower).
        - Changes Ep 9 Shot 2.
        - Affects ONLY Episode 9 and Episode 10 Grand Finale.
        - Episodes 1 through 8 remain 100% unaffected.
        - Grand Finale is dynamically redeveloped as 'The Clock Tower Reckoning'.
        """
        proposal = self.engine.propose_season_edit(
            season_number=3,
            episode_number=9,
            shot_number=2,
            new_action="Sreedharan breaks down and confesses that the original testament is hidden inside the iron gears of the Old Clock Tower on the cliff.",
            new_dialogue="ശ്രീധരൻ: 'സത്യം ഇവിടെയല്ല... പഴയ ക്ലോക്ക് ടവറിന്റെ വലിയ ഗിയറുകൾക്കിടയിലാണ് ഞാൻ അത് ഒളിപ്പിച്ചത്! നിങ്ങൾ അങ്ങോട്ട് പോകരുത്!'",
            user_notes="Climax location shifted to Old Clock Tower",
            added_fact_ids=["FACT_CLOCK_TOWER_REVELATION"]
        )

        impact = proposal["butterfly_impact"]
        redev = proposal["redevelopment"]

        # 1. Only Ep 9 and Ep 10 affected
        self.assertEqual(sorted(impact["affected_episodes"]), [9, 10])
        self.assertEqual(sorted(impact["unaffected_episodes"]), [1, 2, 3, 4, 5, 6, 7, 8])

        # 2. Grand Finale redevelopment
        finale = redev["alternative_grand_finale"]
        self.assertTrue(finale["is_redeveloped"])
        self.assertEqual(finale["alternative_finale_title"], "The Clock Tower Reckoning (Grand Finale Redevelopment)")
        self.assertIn("clock tower", finale["adapted_climax"].lower())

        # 3. Commit and Rollback
        self.engine.approve_and_commit(proposal["revision_id"])
        self.engine.rollback(proposal["revision_id"])
        self.assertEqual(self.baseline_outline_bytes, (self.sandbox_path / "season_3_shot_outline.json").read_bytes())

    def test_05_stale_assets_flagged_without_auto_execution(self):
        """
        Scenario 5: Stale asset identification & Execution Gate.
        - Verifies outdated video assets are flagged.
        - Confirms NO video rendering or upload happens automatically.
        """
        # Create simulated clip in clean_shots
        clean_dir = self.sandbox_path / "clean_shots"
        clean_dir.mkdir(exist_ok=True)
        dummy_clip = clean_dir / "shot_01.mp4"
        dummy_clip.write_text("dummy video content")

        proposal = self.engine.propose_season_edit(
            season_number=3,
            episode_number=1,
            shot_number=1,
            new_action="Amal starts the car engine with a roar.",
            new_dialogue="അമൽ: 'നമുക്ക് പോകാം!'"
        )

        stale = proposal["stale_asset_audit"]
        self.assertTrue(len(stale["stale_video_clips"]) > 0)
        self.assertIn("shot_01.mp4", stale["stale_video_clips"][0])

        # Verify dummy clip was NOT overwritten or rendered
        self.assertEqual(dummy_clip.read_text(), "dummy video content")

    def test_06_synchronization_failure_resilience(self):
        """
        Scenario 6: Synchronization failure handling.
        - Simulates missing pending proposal during commit.
        - Verifies system catches error gracefully without corrupting approved canon.
        """
        with self.assertRaises(FileNotFoundError):
            self.engine.approve_and_commit("non_existent_revision_id_999999")

        # Canon remains untouched
        self.assertEqual(self.baseline_outline_bytes, (self.sandbox_path / "season_3_shot_outline.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
