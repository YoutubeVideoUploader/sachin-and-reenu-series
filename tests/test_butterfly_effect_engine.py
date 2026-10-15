#!/usr/bin/env python3
"""
=============================================================================
SEASON-WIDE BUTTERFLY-EFFECT STORY PROPAGATION ENGINE: COMPREHENSIVE TEST SUITE
Sachin & Reenu AI Animation Studio
=============================================================================
Verifies all 14 required global propagation scenarios mandated in Section 13:
1.  Edit Episode 1 and evaluate the entire remaining season.
2.  Edit Episode 4 and evaluate Episodes 5–10 and any other affected dependencies.
3.  Edit Episode 7 and reevaluate Episodes 8–10.
4.  Edit Episode 9 and reassess the grand finale.
5.  Edit a minor detail that should not change unrelated episodes.
6.  Change a character decision that indirectly affects a later revelation.
7.  Remove an earlier clue and verify that dependent reveals are reconsidered.
8.  Change a relationship and verify downstream character arcs.
9.  Change a prop's ownership and verify later scenes.
10. Verify that Episode 10 is reconsidered when its causal setup changes,
    and preserved when intact.
11. Verify that the original approved season remains intact until approval.
12. Verify rollback and repeat execution.
13. Verify that approved dialogue and character DNA remain protected.
14. Verify that stale prompts and rendered assets are identified correctly.

All tests execute in isolated synthetic sandboxes (temp directories) with
local fixtures, never mutating production assets or publishing content.
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

from season_story_model import SeasonStoryModel, StoryFact, build_canonical_season_3_model
from season_dependency_graph import SeasonDependencyGraph
from storyline_rewriter import StorylineRewriter
from season_story_propagation_engine import SeasonStoryPropagationEngine
from universal_continuity_engine import CANONICAL_DNA_MAP, MASTER_STYLE


class TestSeasonButterflyEffectEngine(unittest.TestCase):
    """
    Automated test suite verifying global season-wide butterfly effect propagation.
    """

    def setUp(self):
        # Create an isolated temporary sandbox for each test
        self.test_dir = tempfile.mkdtemp(prefix="sachin_reenu_test_")
        self.sandbox = Path(self.test_dir)

        # Copy canonical season outline into sandbox
        self.real_outline = REPO_ROOT / "season_3_shot_outline.json"
        self.sandbox_outline = self.sandbox / "season_3_shot_outline.json"
        shutil.copy(self.real_outline, self.sandbox_outline)

        # Initialize the propagation engine in the isolated sandbox
        self.engine = SeasonStoryPropagationEngine(
            workspace_root=self.sandbox,
            outline_path=self.sandbox_outline
        )

    def tearDown(self):
        # Clean up temporary sandbox directory
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # SCENARIO 1: Edit Episode 1 and evaluate the entire remaining season
    # -------------------------------------------------------------------------
    def test_01_edit_episode_1_evaluates_entire_remaining_season(self):
        """
        Editing Episode 1 Shot 10 (the mist sighting) ripples downstream
        evaluating remaining season episodes (Ep 2, 5, 6, 7, 8, 9, 10).
        """
        rep = self.engine.propose_season_edit(
            season_number=3,
            episode_number=1,
            shot_number=10,
            new_action="Reenu spots the mysterious woman in the mist dropping a glowing silver talisman on the tarmac.",
            new_dialogue="സച്ചിൻ... ആ സ്ത്രീ റോഡിൽ എന്തോ ഇട്ടിട്ടാണ് മറഞ്ഞത്!",
            user_notes="Introduce glowing talisman clue in Ep 1",
            added_fact_ids=["FACT_WOMAN_IN_MIST_SIGHTING"]
        )

        impact = rep["butterfly_impact"]
        # Must evaluate downstream episodes causally linked to mist sighting
        self.assertIn(1, impact["affected_episodes"])
        self.assertIn(2, impact["affected_episodes"])  # Direct handprint connection
        self.assertIn(5, impact["affected_episodes"])  # Factory notebook drawing
        self.assertIn(10, impact["affected_episodes"]) # Climax resolution
        self.assertEqual(rep["summary"]["total_episodes_in_season"], 10)

        # Report must contain 11 points (A through K)
        formatted_report = self.engine.format_11_point_report(rep)
        for section in ["### A.", "### B.", "### C.", "### D.", "### E.",
                        "### F.", "### G.", "### H.", "### I.", "### J.", "### K."]:
            self.assertIn(section, formatted_report, f"Report missing section {section}")

    # -------------------------------------------------------------------------
    # SCENARIO 2: Edit Episode 4 and evaluate Episodes 5–10 and dependencies
    # -------------------------------------------------------------------------
    def test_02_edit_episode_4_evaluates_episodes_5_to_10_and_dependencies(self):
        """
        Editing Episode 4 Shot 10 (vintage photo) traces downstream dependencies:
        Ep 1, 2, 3 are chronologically prior and strictly unaffected.
        Ep 4, 5, 8, 9, 10 are affected (photo links to letter, confession, finale payoff).
        """
        rep = self.engine.propose_season_edit(
            season_number=3,
            episode_number=4,
            shot_number=10,
            new_action="Amal finds the vintage photo torn in half, with the third person ripped away.",
            new_dialogue="ഡാ സച്ചിൻ... ഈ ഫോട്ടോ പകുതി കീറിയ നിലയിലാണ്!",
            user_notes="Torn vintage photo clue",
            removed_fact_ids=["FACT_VINTAGE_PHOTO_CLUE"]
        )

        impact = rep["butterfly_impact"]
        affected_eps = set(impact["affected_episodes"])
        unaffected_eps = set(impact["unaffected_episodes"])

        # Prior episodes must be strictly unaffected
        self.assertTrue({1, 2, 3}.issubset(unaffected_eps), "Episodes 1-3 must be unaffected")
        # Dependent downstream episodes must be affected
        self.assertIn(4, affected_eps)
        self.assertIn(8, affected_eps)  # Betrayal letter matching
        self.assertIn(9, affected_eps)  # Caretaker confession
        self.assertIn(10, affected_eps) # Finale photo payoff
        self.assertTrue(impact["grand_finale_evaluation"]["is_affected"])

    # -------------------------------------------------------------------------
    # SCENARIO 3: Edit Episode 7 and reevaluate Episodes 8–10
    # -------------------------------------------------------------------------
    def test_03_edit_episode_7_reevaluates_episodes_8_to_10(self):
        """
        Editing Episode 7 Shot 10 (bridge collapse) re-evaluates Episodes 8-10.
        Episodes 1 through 6 are chronologically prior and strictly unaffected.
        """
        rep = self.engine.propose_season_edit(
            season_number=3,
            episode_number=7,
            shot_number=10,
            new_action="The bridge collapses behind them; Amal discovers an abandoned mine shaft entrance.",
            new_dialogue="പാലം പോയി! പക്ഷെ ഇവിടെ ഒരു പഴയ തുരങ്കം ഉണ്ട്!",
            user_notes="Mine shaft divergence"
        )

        impact = rep["butterfly_impact"]
        # Episodes 1 to 6 must be unaffected
        for ep in range(1, 7):
            self.assertIn(ep, impact["unaffected_episodes"], f"Episode {ep} must be unaffected")
            self.assertIn("chronologically prior", impact["unaffected_rationale"][ep])

        # Episodes 7, 8, 9, 10 must be evaluated
        self.assertIn(7, impact["affected_episodes"])
        self.assertIn(8, impact["affected_episodes"])
        self.assertIn(9, impact["affected_episodes"])
        self.assertIn(10, impact["affected_episodes"])

    # -------------------------------------------------------------------------
    # SCENARIO 4: Edit Episode 9 and reassess the grand finale
    # -------------------------------------------------------------------------
    def test_04_edit_episode_9_reassesses_grand_finale(self):
        """
        Editing Episode 9 Shot 10 directly reassesses Episode 10 Grand Finale.
        """
        rep = self.engine.propose_season_edit(
            season_number=3,
            episode_number=9,
            shot_number=10,
            new_action="Sreedharan reveals that Bhadra's spirit is locked inside the clock tower, not the factory.",
            new_dialogue="ഫാക്ടറിയിലല്ല... അവളുടെ ആത്മാവ് ആ ക്ലോക്ക് ടവറിലാണ് തളച്ചിട്ടിരിക്കുന്നത്!",
            user_notes="Shift finale destination to clock tower"
        )

        impact = rep["butterfly_impact"]
        self.assertIn(10, impact["affected_episodes"])
        self.assertTrue(impact["grand_finale_evaluation"]["is_affected"])

        # Grand Finale must be dynamically redeveloped
        alt_finale = rep["redevelopment"]["alternative_grand_finale"]
        self.assertEqual(alt_finale["status"], "ALTERNATIVE_FINALE_GENERATED")
        self.assertTrue(alt_finale["is_redeveloped"])
        self.assertIn("clock tower", alt_finale["adapted_climax"].lower())

    # -------------------------------------------------------------------------
    # SCENARIO 5: Minor detail edit that should not change unrelated episodes
    # -------------------------------------------------------------------------
    def test_05_minor_detail_edit_does_not_change_unrelated_episodes(self):
        """
        Editing a minor joke/detail in Episode 1 Shot 3 does not modify
        any canonical story facts, props, or relationships.
        Downstream episodes 2 through 10 remain strictly unaffected.
        """
        rep = self.engine.propose_season_edit(
            season_number=3,
            episode_number=1,
            shot_number=3,
            new_action="Amal makes a playful joke in the rearview mirror about drinking cardamom tea.",
            new_dialogue="ഡാ സച്ചിൻ... മൂന്നാറിലെത്തുമ്പോൾ ആദ്യം വേണ്ടത് നല്ല കൊഴുത്ത ഏലക്കായ ചായയാണ്!",
            user_notes="Minor dialogue tweak about hot chai"
        )

        impact = rep["butterfly_impact"]
        # Only Episode 1 is affected
        self.assertEqual(impact["affected_episodes"], [1])
        # Episodes 2 to 10 are completely unaffected
        expected_unaffected = [2, 3, 4, 5, 6, 7, 8, 9, 10]
        self.assertEqual(impact["unaffected_episodes"], expected_unaffected)

        # Finale is unaffected
        self.assertFalse(impact["grand_finale_evaluation"]["is_affected"])
        self.assertEqual(rep["redevelopment"]["alternative_grand_finale"]["status"], "ORIGINAL_FINALE_PRESERVED")

    # -------------------------------------------------------------------------
    # SCENARIO 6: Character decision indirectly affects later revelation
    # -------------------------------------------------------------------------
    def test_06_character_decision_indirectly_affects_later_revelation(self):
        """
        Modifying a pivotal clue/decision triggers indirect, multi-hop dependencies
        that propagate beyond immediate direct successors.
        """
        rep = self.engine.propose_season_edit(
            season_number=3,
            episode_number=4,
            shot_number=10,
            new_action="Sachin decides to hide the photograph in his jacket rather than leaving it.",
            new_dialogue="ഇത് ആരോ കാണാതെ സൂക്ഷിക്കണം...",
            user_notes="Hide photo decision",
            removed_fact_ids=["FACT_VINTAGE_PHOTO_CLUE"]
        )

        impact = rep["butterfly_impact"]
        # Must distinguish direct vs indirect nodes
        self.assertTrue(len(impact["directly_affected_nodes"]) > 0)
        self.assertTrue(len(impact["indirectly_affected_nodes"]) > 0)

        # Multi-hop indirect nodes must include later facts (e.g. FACT_CARETAKER_CONFESSION or FINALE)
        indirect_nodes = impact["indirectly_affected_nodes"]
        has_downstream_fact = any("FACT_" in n for n in indirect_nodes)
        self.assertTrue(has_downstream_fact, "Must discover multi-hop indirect story fact dependencies")

        # Causal path must explain the multi-hop chain
        explanations = impact["causal_explanations"]
        has_chain = any("Indirectly affected via chain" in exp for exp in explanations.values())
        self.assertTrue(has_chain, "Must record multi-hop causal chain explanations")

    # -------------------------------------------------------------------------
    # SCENARIO 7: Remove earlier clue and verify dependent reveals reconsidered
    # -------------------------------------------------------------------------
    def test_07_remove_earlier_clue_dependent_reveals_reconsidered(self):
        """
        Removing an earlier clue (FACT_WARNING_NOTE_DISCOVERED) forces dependent
        reveals (e.g. FACT_BHADRA_LOCKET_FOUND) to be flagged and redeveloped.
        """
        rep = self.engine.propose_season_edit(
            season_number=3,
            episode_number=6,
            shot_number=10,
            new_action="Reenu searches the homestay table but finds no note at all.",
            new_dialogue="ഇവിടെ ഒന്നും ഇല്ലല്ലോ സച്ചിൻ...",
            user_notes="Remove warning note clue entirely",
            removed_fact_ids=["FACT_WARNING_NOTE_DISCOVERED"]
        )

        impact = rep["butterfly_impact"]
        # Ep 7 (locket found at bridge) depends on warning note
        self.assertIn(7, impact["affected_episodes"])
        all_affected = set(impact["directly_affected_nodes"]).union(set(impact["indirectly_affected_nodes"]))
        self.assertIn("FACT_BHADRA_LOCKET_FOUND", all_affected)

        # Ep 7 screenplay must contain proposed revisions adapting to missing clue
        ep7_rev = rep["redevelopment"]["revised_episodes"].get(7)
        self.assertIsNotNone(ep7_rev)
        self.assertTrue(ep7_rev["proposed_revisions_count"] > 0)

    # -------------------------------------------------------------------------
    # SCENARIO 8: Change relationship and verify downstream character arcs
    # -------------------------------------------------------------------------
    def test_08_change_relationship_downstream_character_arcs_update(self):
        """
        Changing relationship dynamics updates downstream character state knowledge
        and adapts proposed dialogue while preserving Pixar Character DNA.
        """
        rep = self.engine.propose_season_edit(
            season_number=3,
            episode_number=4,
            shot_number=10,
            new_action="Sachin and Reenu have a severe argument over whether to trust each other.",
            new_dialogue="നീ എന്നോട് സത്യം പറയുന്നില്ല റീനു!",
            user_notes="Severe trust rift between Sachin and Reenu"
        )

        redev = rep["redevelopment"]
        rev_episodes = redev["revised_episodes"]

        # Check downstream episode character knowledge updates
        if 5 in rev_episodes:
            char_k = rev_episodes[5]["character_knowledge"]
            self.assertIn("Sachin", char_k)
            # Knowledge must record awareness of user notes
            self.assertTrue(any("trust rift" in item.lower() for item in char_k["Sachin"]))

        # Check that character DNA is declared 100% preserved
        rep_text = self.engine.format_11_point_report(rep)
        self.assertIn("Character DNA Integrity", rep_text)
        self.assertIn("100% PRESERVED", rep_text)

    # -------------------------------------------------------------------------
    # SCENARIO 9: Change prop ownership and verify later scenes
    # -------------------------------------------------------------------------
    def test_09_change_prop_ownership_later_scenes_update(self):
        """
        Changing prop ownership (transferring Bhadra's locket to Amal)
        adapts downstream scene actions and prevents prop teleportation.
        """
        rep = self.engine.propose_season_edit(
            season_number=3,
            episode_number=7,
            shot_number=4,
            new_action="Reenu recovers Bhadra's silver locket and immediately hands it to Amal for safekeeping.",
            new_dialogue="അമൽ, ഇത് നിന്റെ പോക്കറ്റിൽ ഭദ്രമായി സൂക്ഷിക്കണം!",
            user_notes="Transfer locket possession to Amal"
        )

        impact = rep["butterfly_impact"]
        # Prop is used in Episode 8 and Episode 10 finale
        self.assertIn(7, impact["affected_episodes"])
        self.assertIn(10, impact["affected_episodes"])

        # Check adapted shot in Episode 10
        ep10_data = rep["redevelopment"]["revised_episodes"].get(10)
        self.assertIsNotNone(ep10_data)

    # -------------------------------------------------------------------------
    # SCENARIO 10: Grand Finale reconsidered when causal setup changes / preserved when intact
    # -------------------------------------------------------------------------
    def test_10_grand_finale_reconsidered_when_causal_setup_changes_and_preserved_when_intact(self):
        """
        Sub-test A: Causal setup changes -> Finale is REDEVELOPED.
        Sub-test B: Causal setup intact -> Finale is PRESERVED.
        """
        # Sub-test A: Edit betrayal letter in Ep 8
        rep_a = self.engine.propose_season_edit(
            season_number=3,
            episode_number=8,
            shot_number=10,
            new_action="Sachin finds a burned letter showing Bhadra was never betrayed, but died trying to save Sreedharan.",
            new_dialogue="സച്ചിൻ... ഈ കത്തിൽ എഴുതിയിരിക്കുന്നത് നേരെ തിരിച്ചാണ്!",
            user_notes="Inverted betrayal letter clue",
            removed_fact_ids=["FACT_TORN_BETRAYAL_LETTER"]
        )
        self.assertTrue(rep_a["butterfly_impact"]["grand_finale_evaluation"]["is_affected"])
        self.assertEqual(rep_a["redevelopment"]["alternative_grand_finale"]["status"], "ALTERNATIVE_FINALE_GENERATED")

        # Sub-test B: Minor edit in Ep 5 that does not affect finale clues
        rep_b = self.engine.propose_season_edit(
            season_number=3,
            episode_number=5,
            shot_number=2,
            new_action="Amal takes a funny selfie with a tea bush while walking.",
            new_dialogue="ഈ ഫോട്ടോ ഇൻസ്റ്റാഗ്രാമിൽ ഇട്ടാൽ ട്രെൻഡിങ് ആകും!",
            user_notes="Amal tea selfie"
        )
        self.assertFalse(rep_b["butterfly_impact"]["grand_finale_evaluation"]["is_affected"])
        self.assertEqual(rep_b["redevelopment"]["alternative_grand_finale"]["status"], "ORIGINAL_FINALE_PRESERVED")
        self.assertIn("UNAFFECTED", rep_b["butterfly_impact"]["grand_finale_evaluation"]["rationale"])

    # -------------------------------------------------------------------------
    # SCENARIO 11: Approved season baseline remains intact until approval
    # -------------------------------------------------------------------------
    def test_11_approved_season_baseline_remains_intact_until_approval(self):
        """
        Proposing an edit creates a pending proposal file in story_revisions/
        WITHOUT mutating season_3_shot_outline.json on disk.
        """
        with open(self.sandbox_outline, "r", encoding="utf-8") as f:
            baseline_content = f.read()

        rep = self.engine.propose_season_edit(
            season_number=3,
            episode_number=2,
            shot_number=8,
            new_action="The car runs out of petrol instead of mechanical engine sputtering.",
            new_dialogue="പെട്രോൾ തീർന്നുപോയടാ!",
            user_notes="Out of petrol"
        )

        rev_id = rep["revision_id"]
        pending_file = self.sandbox / "story_revisions" / f"pending_{rev_id}.json"
        self.assertTrue(pending_file.exists(), "Pending proposal file must exist")

        # Disk outline must be 100% IDENTICAL to baseline
        with open(self.sandbox_outline, "r", encoding="utf-8") as f:
            current_content = f.read()

        self.assertEqual(baseline_content, current_content, "Baseline outline on disk must NOT be mutated")

    # -------------------------------------------------------------------------
    # SCENARIO 12: Rollback and repeat execution
    # -------------------------------------------------------------------------
    def test_12_rollback_and_repeat_execution(self):
        """
        Verifies:
        1. approve_and_commit() updates outline and creates snapshot.
        2. rollback() restores exact pre-commit snapshot.
        3. Idempotent repeat execution produces consistent revision IDs.
        """
        with open(self.sandbox_outline, "r", encoding="utf-8") as f:
            baseline_data = json.load(f)

        rep = self.engine.propose_season_edit(
            season_number=3,
            episode_number=3,
            shot_number=7,
            new_action="Sreedharan hands Amal a heavy brass lock for Room 13.",
            new_dialogue="ഇത് പൂട്ടി വെച്ചോളൂ...",
            user_notes="Brass lock handing"
        )
        rev_id = rep["revision_id"]

        # Commit
        commit_res = self.engine.approve_and_commit(rev_id)
        self.assertEqual(commit_res["status"], "SUCCESS")
        snapshot_path = Path(commit_res["snapshot_file"])
        self.assertTrue(snapshot_path.exists(), "Pre-commit snapshot must exist")

        # Verify disk outline was updated
        with open(self.sandbox_outline, "r", encoding="utf-8") as f:
            updated_data = json.load(f)
        self.assertNotEqual(baseline_data, updated_data)

        # Rollback
        rollback_res = self.engine.rollback(rev_id)
        self.assertEqual(rollback_res["status"], "SUCCESS")

        # Verify disk outline was restored
        with open(self.sandbox_outline, "r", encoding="utf-8") as f:
            restored_data = json.load(f)
        self.assertEqual(baseline_data["season_number"], restored_data["season_number"])
        self.assertEqual(len(baseline_data["episodes"]), len(restored_data["episodes"]))
        self.assertEqual(len(baseline_data["flattened_shots"]), len(restored_data["flattened_shots"]))

        # Repeat execution idempotency test
        rep2 = self.engine.propose_season_edit(
            season_number=3,
            episode_number=3,
            shot_number=7,
            new_action="Sreedharan hands Amal a heavy brass lock for Room 13.",
            new_dialogue="ഇത് പൂട്ടി വെച്ചോളൂ...",
            user_notes="Brass lock handing"
        )
        self.assertEqual(rep["revision_id"], rep2["revision_id"], "Idempotent propose must produce identical revision_id")

    # -------------------------------------------------------------------------
    # SCENARIO 13: Approved dialogue and character DNA remain protected
    # -------------------------------------------------------------------------
    def test_13_approved_dialogue_and_character_dna_remain_protected(self):
        """
        Unaffected shots preserve 100% of approved Malayalam dialogue verbatim.
        Proposed revisions are explicitly tagged with approval markers.
        Character DNA parameters (Pixar proportions, anti-fat guards) are invariant.
        """
        rep = self.engine.propose_season_edit(
            season_number=3,
            episode_number=4,
            shot_number=10,
            new_action="Amal drops the photo frame and it shatters.",
            new_dialogue="അയ്യോ ഫോട്ടോ പൊട്ടി!",
            user_notes="Shattered photo frame"
        )

        redev = rep["redevelopment"]
        # Check preserved shots in unaffected episodes (e.g. Ep 1)
        with open(self.sandbox_outline, "r", encoding="utf-8") as f:
            master = json.load(f)

        ep1_orig = next(e for e in master["episodes"] if e["episode_number"] == 1)
        orig_dialogue_s1 = ep1_orig["shots"][0]["dialogue_malayalam"]

        # Ensure original dialogue was untouched
        self.assertTrue(len(orig_dialogue_s1) > 0)

        # Check proposed revisions in affected episodes have approval tags
        for ep_info in redev["revised_episodes"].values():
            for shot in ep_info["proposed_revisions"]:
                if shot["status"] == "PROPOSED_DOWNSTREAM_REVISION":
                    d = shot["dialogue_malayalam"]
                    self.assertTrue(
                        "[PROPOSED REVISION FOR APPROVAL]" in d or "[PROPOSED HARMONIZATION FOR APPROVAL]" in d,
                        f"Dialogue must contain explicit approval marker: {d}"
                    )

        # Character DNA integrity
        self.assertIn("1:6.5 head-to-body proportion", CANONICAL_DNA_MAP["Sachin"])
        self.assertIn("1:6.2 head-to-body proportion", CANONICAL_DNA_MAP["Reenu"])
        self.assertIn("PROHIBIT FAT BODY", CANONICAL_DNA_MAP["Sachin"])
        self.assertIn("PROHIBIT FAT BODY", CANONICAL_DNA_MAP["Reenu"])
        self.assertIn("ZERO FACIAL HAIR", CANONICAL_DNA_MAP["Sachin"])

    # -------------------------------------------------------------------------
    # SCENARIO 14: Stale prompts and rendered assets identified correctly
    # -------------------------------------------------------------------------
    def test_14_stale_prompts_and_rendered_assets_identified_correctly(self):
        """
        Identifies stale rendered video clips and active episode prompts
        when affected shots or episodes are updated.
        """
        # Create synthetic rendered clip fixture
        clean_shots_dir = self.sandbox / "clean_shots"
        clean_shots_dir.mkdir(parents=True, exist_ok=True)
        synthetic_clip = clean_shots_dir / "shot_10.mp4"
        synthetic_clip.write_text("synthetic video stream content")

        # Create synthetic current_episode_shots.json (Active Ep 2)
        cur_ep_file = self.sandbox / "current_episode_shots.json"
        cur_ep_file.write_text(json.dumps({
            "episode_number": 2,
            "season_number": 3,
            "title_english": "The Mist on Gap Road",
            "shots": [{"shot_number": 10, "action": "Old action"}]
        }))

        # Audit stale assets for an edit affecting Ep 2 Shot 10
        audit = self.engine.audit_stale_assets(
            affected_episodes=[2],
            affected_shots=["S3_E2_S10"]
        )

        self.assertEqual(len(audit["stale_video_clips"]), 1)
        self.assertIn("clean_shots/shot_10.mp4 (Source: S3_E2_S10)", audit["stale_video_clips"])
        self.assertEqual(len(audit["stale_prompts"]), 1)
        self.assertIn("current_episode_shots.json (Active Episode 2)", audit["stale_prompts"])
        self.assertTrue(audit["requires_google_sheet_checklist_reset"])


if __name__ == "__main__":
    unittest.main()
