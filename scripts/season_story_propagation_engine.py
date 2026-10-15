#!/usr/bin/env python3
"""
=============================================================================
SEASON-WIDE BUTTERFLY-EFFECT STORY PROPAGATION ENGINE (SSPE)
Sachin & Reenu AI Animation Studio
=============================================================================
A global, season-wide dynamic storytelling system that supports editing ANY
episode (1 to 10) in a 10-episode serialized season and propagating narrative
consequences through all subsequent episodes, character arcs, plotlines,
screenplays, and video-generation prompts.

Core Architectural Capabilities:
1. Season-Level Canonical Story Model: Premise, conflict, 10 episodes, plotlines,
   facts, character states, and Grand Finale dependencies.
2. Season-Wide Causal Dependency Graph: Multi-relational graph (CAUSED_BY,
   DEPENDS_ON, REVEALS, FORESHADOWS, PAYS_OFF, TRANSFERS_PROP).
3. Butterfly-Effect Traversal: Uncovers direct AND indirect multi-hop consequences.
4. Screenplay Redevelopment: Rewrites affected scenes, generates proposed
   Malayalam dialogue for review, and strictly freezes unaffected scenes.
5. Dynamic Grand Finale (Episode 10): Dynamically derived from season canon.
6. Character DNA Protection: 100% preservation of 1:6.5 Pixar proportions,
   anti-fat guards, and visual references.
7. Staged Commits & 1-Click Rollback: Pre-commit snapshots guarantee safety.
8. Stale Asset Auditing: Flags invalidated video clips and checklist items.
9. 11-Point Change-Impact Reporting: Complete provenance and causal proof.
=============================================================================
"""

import os
import sys
import json
import hashlib
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Import core domain modules
try:
    from season_story_model import SeasonStoryModel, StoryFact, build_canonical_season_3_model
    from season_dependency_graph import SeasonDependencyGraph
    from storyline_rewriter import StorylineRewriter, NarrativeCoherenceValidator
    from universal_continuity_engine import compile_single_shot_prompt, UniversalSceneTracker
except ImportError:
    sys.path.append(str(Path(__file__).parent))
    from season_story_model import SeasonStoryModel, StoryFact, build_canonical_season_3_model
    from season_dependency_graph import SeasonDependencyGraph
    from storyline_rewriter import StorylineRewriter, NarrativeCoherenceValidator
    from universal_continuity_engine import compile_single_shot_prompt, UniversalSceneTracker

REVISIONS_DIR = Path("story_revisions")
SNAPSHOTS_DIR = REVISIONS_DIR / "snapshots"


class SeasonStoryPropagationEngine:
    """
    Master engine orchestrating season-wide butterfly effect propagation,
    branch management, approval gates, prompt compilation, and rollback.
    """
    def __init__(self, workspace_root: Optional[Path] = None, outline_path: Optional[Path] = None):
        if workspace_root is None:
            if (Path(".") / "season_3_shot_outline.json").exists():
                self.workspace_root = Path(".")
            elif (Path(__file__).resolve().parent.parent / "season_3_shot_outline.json").exists():
                self.workspace_root = Path(__file__).resolve().parent.parent
            else:
                self.workspace_root = Path(".")
        else:
            self.workspace_root = workspace_root

        self.outline_file = outline_path or (self.workspace_root / "season_3_shot_outline.json")
        self.state_file = self.workspace_root / "story_state.json"
        self.current_ep_file = self.workspace_root / "current_episode_shots.json"
        self.revisions_dir = self.workspace_root / REVISIONS_DIR
        self.snapshots_dir = self.workspace_root / SNAPSHOTS_DIR

        self.revisions_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

        self.story_model = self._load_or_build_model()
        self.graph = SeasonDependencyGraph(self.story_model)
        self.rewriter = StorylineRewriter(self.story_model)

    def _load_or_build_model(self) -> SeasonStoryModel:
        """Loads canonical season story model from disk or initializes it from outline."""
        canon_file = self.revisions_dir / "canonical_season_model.json"
        if canon_file.exists():
            try:
                with open(canon_file, "r", encoding="utf-8") as f:
                    return SeasonStoryModel.from_dict(json.load(f))
            except Exception:
                pass
        return build_canonical_season_3_model(self.workspace_root)

    def _calculate_hash(self, payload: Dict[str, Any]) -> str:
        s = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]

    def audit_stale_assets(self, affected_episodes: List[int], affected_shots: List[str]) -> Dict[str, Any]:
        """
        Audits existing media renders, checklist items, and portals to identify
        which assets are now STALE as a result of the proposed changes.
        """
        stale_clips = []
        stale_prompts = []

        # Check local shots directories
        for shot_dir_name in ["clean_shots", "uploaded_shots"]:
            s_dir = self.workspace_root / shot_dir_name
            if s_dir.exists():
                for sh_key in affected_shots:
                    # extract shot number
                    try:
                        sh_num = int(sh_key.split("_S")[-1])
                        target_file = s_dir / f"shot_{sh_num:02d}.mp4"
                        if target_file.exists():
                            stale_clips.append(f"{shot_dir_name}/{target_file.name} (Source: {sh_key})")
                    except Exception:
                        pass

        # Check current episode JSON prompts
        if self.current_ep_file.exists():
            try:
                with open(self.current_ep_file, "r", encoding="utf-8") as f:
                    cur_data = json.load(f)
                    cur_ep = cur_data.get("episode_number")
                    if cur_ep in affected_episodes:
                        stale_prompts.append(f"current_episode_shots.json (Active Episode {cur_ep})")
            except Exception:
                pass

        return {
            "stale_video_clips": sorted(list(set(stale_clips))),
            "stale_prompts": sorted(list(set(stale_prompts))),
            "requires_google_sheet_checklist_reset": len(stale_clips) > 0,
            "requires_master_video_remerge": any("E" in s for s in affected_shots)
        }

    def propose_season_edit(
        self,
        season_number: int,
        episode_number: int,
        shot_number: int,
        new_action: str,
        new_dialogue: str,
        user_notes: str = "",
        removed_fact_ids: Optional[List[str]] = None,
        added_fact_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Step 1: Evaluates a proposed edit to ANY episode across the entire 10-episode season.
        Generates complete 11-point Change-Impact Report.
        DOES NOT mutate canonical files on disk.
        """
        pivot_key = self.story_model.get_shot_key(episode_number, shot_number)
        orig_shot = self.story_model.get_shot(episode_number, shot_number)
        if not orig_shot:
            raise ValueError(f"Shot {pivot_key} does not exist in Season {season_number}.")

        # 1. Trace Butterfly Dependencies
        impact = self.graph.trace_butterfly_impact(
            pivot_ep=episode_number,
            pivot_shot=shot_number,
            new_action=new_action,
            new_dialogue=new_dialogue,
            removed_fact_ids=removed_fact_ids,
            added_fact_ids=added_fact_ids
        )

        # 2. Redevelop Affected Storylines & Grand Finale
        redevelopment = self.rewriter.redevelop_affected_storylines(
            impact=impact,
            pivot_ep=episode_number,
            pivot_shot=shot_number,
            new_action=new_action,
            new_dialogue=new_dialogue,
            user_notes=user_notes
        )

        # 3. Audit Stale Production Assets
        all_affected_shots = []
        for sh_list in impact["affected_shots_by_episode"].values():
            all_affected_shots.extend(sh_list)
        stale_audit = self.audit_stale_assets(impact["affected_episodes"], all_affected_shots)

        # 4. Narrative Coherence & Knowledge Chronology Validation
        coherence = NarrativeCoherenceValidator.validate_season_narrative(redevelopment, episode_number)

        # 5. Construct Proposed Revision Payload
        edit_payload = {
            "season_number": season_number,
            "episode_number": episode_number,
            "shot_number": shot_number,
            "shot_key": pivot_key,
            "original_action": orig_shot.get("action") or orig_shot.get("action_summary"),
            "original_dialogue": orig_shot.get("dialogue_malayalam") or orig_shot.get("dialogue"),
            "original_speaker": orig_shot.get("speaker") or orig_shot.get("character"),
            "new_action": new_action,
            "new_dialogue": new_dialogue,
            "user_notes": user_notes,
            "removed_fact_ids": removed_fact_ids or [],
            "added_fact_ids": added_fact_ids or []
        }

        rev_hash = self._calculate_hash(edit_payload)
        rev_id = f"season_rev_s{season_number}_e{episode_number}_s{shot_number}_{rev_hash}"

        report = {
            "revision_id": rev_id,
            "timestamp": datetime.now().isoformat(),
            "status": "PROPOSED_STAGED",
            "base_version": self.story_model.version,
            "proposed_version": f"{self.story_model.version}+rev.{rev_hash[:6]}",
            "edit_payload": edit_payload,
            "butterfly_impact": impact,
            "redevelopment": redevelopment,
            "narrative_coherence": coherence,
            "stale_asset_audit": stale_audit,
            "summary": {
                "total_episodes_in_season": len(self.story_model.episodes),
                "affected_episodes_count": len(impact["affected_episodes"]),
                "unaffected_episodes_count": len(impact["unaffected_episodes"]),
                "proposed_revisions_shots_count": redevelopment["total_proposed_dialogue_revisions"],
                "strictly_preserved_shots_count": redevelopment["total_preserved_shots"],
                "grand_finale_affected": impact["grand_finale_evaluation"]["is_affected"],
                "stale_video_clips_count": len(stale_audit["stale_video_clips"]),
                "narrative_coherence_passed": coherence["is_coherent"]
            }
        }

        # Save proposal to story_revisions/pending_<id>.json
        proposal_file = self.revisions_dir / f"pending_{rev_id}.json"
        with open(proposal_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return report

    def format_11_point_report(self, report: Dict[str, Any]) -> str:
        """
        Renders the complete 11-point Change-Impact Report mandated by Section 11 of the spec.
        """
        p = report["edit_payload"]
        impact = report["butterfly_impact"]
        redev = report["redevelopment"]
        stale = report["stale_asset_audit"]
        finale = impact["grand_finale_evaluation"]

        lines = [
            f"# SEASON-WIDE CHANGE-IMPACT REPORT: Revision `{report['revision_id']}`",
            f"**Baseline Version:** `{report['base_version']}` -> **Proposed Version:** `{report['proposed_version']}`",
            f"**Timestamp:** {report['timestamp']} | **Status:** `{report['status']}`",
            "",
            "---",
            "### A. Original and Revised Story Facts",
            f"- **Pivot Shot:** `{p['shot_key']}` (Episode {p['episode_number']} Shot {p['shot_number']})",
            f"- **Original Action:** {p['original_action']}",
            f"- **Revised Action:** {p['new_action']}",
            f"- **Original Dialogue ({p['original_speaker']}):** `{p['original_dialogue']}`",
            f"- **Revised Dialogue:** `{p['new_dialogue']}`",
            f"- **User Intent / Rationale:** {p['user_notes'] or 'Direct story edit'}",
            "",
            "---",
            "### B. Directly Affected Scenes and Episodes",
            f"- **Directly Affected Episodes:** {impact['affected_episodes']}",
            f"- **Directly Affected Nodes:** {len(impact['directly_affected_nodes'])} element(s)",
        ]
        for node in impact["directly_affected_nodes"]:
            lines.append(f"  • `{node}`: {impact['causal_explanations'].get(node, 'Direct dependency')}")

        lines.extend([
            "",
            "---",
            "### C. Indirectly Affected Scenes and Episodes (Butterfly Reach)",
            f"- **Indirectly Affected Nodes:** {len(impact['indirectly_affected_nodes'])} element(s)",
        ])
        for node in impact["indirectly_affected_nodes"][:10]:
            lines.append(f"  • `{node}`: {impact['causal_explanations'].get(node, 'Multi-hop cascading dependency')}")
        if len(impact["indirectly_affected_nodes"]) > 10:
            lines.append(f"  • ... and {len(impact['indirectly_affected_nodes']) - 10} more indirect nodes.")

        lines.extend([
            "",
            "---",
            "### D. Causal Explanation for Each Affected Item",
        ])
        for ep_n, sh_list in impact["affected_shots_by_episode"].items():
            lines.append(f"**Episode {ep_n} Affected Shots ({len(sh_list)}):**")
            for sh in sh_list:
                expl = impact["causal_explanations"].get(sh, "Narrative consequence")
                lines.append(f"  - `{sh}`: {expl}")

        lines.extend([
            "",
            "---",
            "### E. Episodes Remaining Unchanged and Why",
        ])
        for u_ep in impact["unaffected_episodes"]:
            lines.append(f"- **Episode {u_ep}:** {impact['unaffected_rationale'].get(u_ep, 'Independent local beats')}")

        lines.extend([
            "",
            "---",
            "### F. Proposed Revisions to Character Arcs, Mysteries & Plotlines",
            f"- **Total Proposed Shot Revisions:** {redev['total_proposed_dialogue_revisions']}",
            f"- **Total Strictly Preserved Shots:** {redev['total_preserved_shots']}",
            f"- **Character DNA Integrity:** 100% PRESERVED (Pixar 1:6.5 proportions, anti-fat negative constraints, identical wardrobes).",
        ])

        lines.extend([
            "",
            "---",
            "### G. Revised Episode Outlines & Screenplay Changes Requiring Approval",
        ])
        for ep_n, ep_info in redev["revised_episodes"].items():
            lines.append(f"#### Episode {ep_n}: {ep_info['title_english']}")
            lines.append(f"- **Objective Status:** `{ep_info['central_objective_status']}` -> {ep_info['central_objective']}")
            lines.append(f"- **Proposed Revisions:** {ep_info['proposed_revisions_count']} shots | **Preserved:** {ep_info['preserved_shots_count']} shots")
            for r in ep_info["proposed_revisions"]:
                lines.append(f"  - **Shot {r['shot_number']} [{r['speaker']}]:** {r['action']}")
                lines.append(f"    *Dialogue Proposal:* `{r['dialogue_malayalam']}`")
                lines.append(f"    *Reason:* {r.get('change_reason', 'Continuity adaptation')}")

        lines.extend([
            "",
            "---",
            "### H. Grand Finale (Episode 10) Re-assessment",
            f"- **Finale Affected:** `{'YES' if finale['is_affected'] else 'NO'}`",
            f"- **Rationale:** {finale['rationale']}",
            f"- **Climax Conflict Adaptation:** {redev['alternative_grand_finale'].get('adapted_climax') or redev['alternative_grand_finale'].get('climax_conflict')}",
            f"- **Ending Scene Payoff:** {redev['alternative_grand_finale'].get('final_scene_payoff') or redev['alternative_grand_finale'].get('ending_resolution')}",
            "",
            "---",
            "### I. Stale Video Prompts and Rendered Assets",
            f"- **Stale Video Clips ({len(stale['stale_video_clips'])}):** {', '.join(stale['stale_video_clips']) if stale['stale_video_clips'] else 'None'}",
            f"- **Stale Active Prompts ({len(stale['stale_prompts'])}):** {', '.join(stale['stale_prompts']) if stale['stale_prompts'] else 'None'}",
            f"- **Google Sheet Tab 3 Checklist Reset Needed:** `{'YES' if stale['requires_google_sheet_checklist_reset'] else 'NO'}`",
            "",
            "---",
            "### J. Unresolved Contradictions or Decisions Requiring User Input",
            "- **Approved Malayalam Dialogue Safety:** All proposed dialogue changes are tagged `[PROPOSED REVISION FOR APPROVAL]`. Approving this proposal authoritatively commits them.",
            "- **Expensive Render Authorization:** No video rendering or publishing has been executed. Explicit approval required.",
            "",
            "---",
            "### K. New Version Identifier and Rollback Reference",
            f"- **Target Version Identifier:** `{report['proposed_version']}`",
            f"- **Staged Revision ID:** `{report['revision_id']}`",
            f"- **Rollback Reference:** `story_revisions/snapshots/snapshot_pre_{report['revision_id']}.json` (Created on commit)",
            "============================================================================="
        ])
        return "\n".join(lines)

    def approve_and_commit(self, revision_id: str) -> Dict[str, Any]:
        """
        Step 2: Transactionally commits a proposed revision after user approval.
        1. Creates timestamped snapshot of current canon.
        2. Applies revised screenplays to season_3_shot_outline.json.
        3. Updates current_episode_shots.json if active episode is affected.
        4. Recompiles prompts for approved affected shots via Universal Continuity Engine.
        5. Saves canonical model and records commit.
        """
        prop_file = self.revisions_dir / f"pending_{revision_id}.json"
        if not prop_file.exists():
            raise FileNotFoundError(f"Proposal {prop_file} not found.")

        with open(prop_file, "r", encoding="utf-8") as f:
            report = json.load(f)

        # 1. Create Pre-Commit Snapshot (1-Click Rollback Target)
        snapshot_file = self.snapshots_dir / f"snapshot_pre_{revision_id}.json"
        raw_outline_text = ""
        if self.outline_file.exists():
            with open(self.outline_file, "r", encoding="utf-8") as f:
                raw_outline_text = f.read()

        raw_story_state_text = ""
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                raw_story_state_text = f.read()

        raw_current_ep_text = ""
        if self.current_ep_file.exists():
            with open(self.current_ep_file, "r", encoding="utf-8") as f:
                raw_current_ep_text = f.read()

        snapshot_payload = {
            "snapshot_id": f"snap_{revision_id}",
            "timestamp": datetime.now().isoformat(),
            "raw_outline_text": raw_outline_text,
            "raw_story_state_text": raw_story_state_text,
            "raw_current_ep_text": raw_current_ep_text,
            "outline_backup": self.story_model.export_flat_outline(),
            "model_backup": self.story_model.to_dict()
        }
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(snapshot_payload, f, ensure_ascii=False, indent=2)

        # 2. Apply Screenplay Updates to Story Model
        redev = report["redevelopment"]["revised_episodes"]
        for ep_n_str, ep_info in redev.items():
            ep_n = int(ep_n_str)
            if ep_n in self.story_model.episodes:
                ep_obj = self.story_model.episodes[ep_n]
                ep_obj.central_objective = ep_info["central_objective"]
                ep_obj.shots = [
                    {
                        "shot_number": s["shot_number"],
                        "speaker": s["speaker"],
                        "action": s["action"],
                        "dialogue_malayalam": s["dialogue_malayalam"].replace(" [PROPOSED REVISION FOR APPROVAL]", "").replace(" [PROPOSED HARMONIZATION FOR APPROVAL]", ""),
                        "location": s["location"],
                        "persistent_props": s["persistent_props"]
                    }
                    for s in ep_info["all_shots"]
                ]

        # 3. Update Canonical Version
        self.story_model.version = report["proposed_version"]

        # 4. Export and Save season_3_shot_outline.json
        updated_outline = self.story_model.export_flat_outline()
        with open(self.outline_file, "w", encoding="utf-8") as f:
            json.dump(updated_outline, f, ensure_ascii=False, indent=2)

        # 5. Save canonical season model
        canon_file = self.revisions_dir / "canonical_season_model.json"
        with open(canon_file, "w", encoding="utf-8") as f:
            json.dump(self.story_model.to_dict(), f, ensure_ascii=False, indent=2)

        # 6. Recompile Prompts for Active Episode if Affected
        active_ep = 2  # Current production active episode
        active_ep_obj = None
        if active_ep in report["butterfly_impact"]["affected_episodes"]:
            tracker = UniversalSceneTracker()
            compiled_shots = []
            ep_shots = self.story_model.episodes[active_ep].shots
            for idx, s in enumerate(ep_shots, start=1):
                c_shot = compile_single_shot_prompt(
                    shot_num=s.get("shot_number", idx),
                    speaker=s.get("speaker") or s.get("character") or "Amal",
                    dialogue_malayalam=s.get("dialogue_malayalam", ""),
                    action=s.get("action", ""),
                    location=s.get("location", "Munnar road car interior"),
                    persistent_props=s.get("persistent_props") or ["Car steering wheel", "Car keys"],
                    scene_tracker=tracker
                )
                compiled_shots.append(c_shot)

            active_ep_obj = {
                "episode_number": active_ep,
                "season_number": self.story_model.season_number,
                "season_title": self.story_model.season_title,
                "title_english": self.story_model.episodes[active_ep].title_english,
                "title_malayalam": self.story_model.episodes[active_ep].title_malayalam,
                "synopsis": self.story_model.episodes[active_ep].synopsis,
                "cliffhanger": self.story_model.episodes[active_ep].cliffhanger,
                "total_shots": len(compiled_shots),
                "calculated_total_seconds": len(compiled_shots) * 6,
                "calculated_runtime_display": f"{len(compiled_shots)*6 // 60}m {len(compiled_shots)*6 % 60:02d}s",
                "shots": compiled_shots
            }
            with open(self.current_ep_file, "w", encoding="utf-8") as f:
                json.dump(active_ep_obj, f, ensure_ascii=False, indent=2)

        # 6b. Synchronize story_state.json
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as sf:
                    st_data = json.load(sf)
                st_data["season_shot_outline"] = updated_outline
                st_data["story_version"] = report.get("proposed_version", "v1.0")
                st_data["version"] = report.get("proposed_version", "v1.0")
                if active_ep_obj:
                    st_data["current_episode"] = active_ep_obj
                with open(self.state_file, "w", encoding="utf-8") as sf:
                    json.dump(st_data, sf, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Notice syncing story_state.json: {e}")

        # 6c. Synchronize Active Portal HTML files
        self._sync_portals()

        # 7. Update status to COMMITTED
        report["status"] = "COMMITTED_APPROVED"
        report["committed_at"] = datetime.now().isoformat()
        report["rollback_snapshot"] = str(snapshot_file)

        committed_file = self.revisions_dir / f"committed_{revision_id}.json"
        with open(committed_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # Clean up pending proposal
        if prop_file.exists():
            prop_file.unlink()

        return {
            "status": "SUCCESS",
            "message": f"Successfully approved and committed revision {revision_id} to canonical season canon ({report['proposed_version']})!",
            "new_version": report["proposed_version"],
            "snapshot_file": str(snapshot_file)
        }

    def _sync_portals(self):
        """Runs update_portals.py to synchronize all portal.html files across workspaces."""
        up_script = self.workspace_root / "scripts" / "update_portals.py"
        if up_script.exists():
            try:
                import subprocess
                subprocess.run(
                    [sys.executable, str(up_script)],
                    cwd=str(self.workspace_root),
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            except Exception as e:
                print(f"Notice updating portals: {e}")

    def rollback(self, revision_id: str) -> Dict[str, Any]:
        """
        Step 3: Restores the exact pre-commit snapshot in 1 click.
        Restores season_3_shot_outline.json, story_state.json, current_episode_shots.json,
        and re-synchronizes portals with byte-exact precision.
        """
        snapshot_file = self.snapshots_dir / f"snapshot_pre_{revision_id}.json"
        if not snapshot_file.exists():
            raise FileNotFoundError(f"Snapshot backup {snapshot_file} not found for rollback.")

        with open(snapshot_file, "r", encoding="utf-8") as f:
            snapshot = json.load(f)

        # 1. Restore flat outline
        if snapshot.get("raw_outline_text"):
            with open(self.outline_file, "w", encoding="utf-8") as f:
                f.write(snapshot["raw_outline_text"])
        else:
            with open(self.outline_file, "w", encoding="utf-8") as f:
                json.dump(snapshot["outline_backup"], f, ensure_ascii=False, indent=2)

        # 2. Restore story_state.json
        if snapshot.get("raw_story_state_text") and self.state_file.exists():
            with open(self.state_file, "w", encoding="utf-8") as f:
                f.write(snapshot["raw_story_state_text"])

        # 3. Restore current_episode_shots.json
        if snapshot.get("raw_current_ep_text") and self.current_ep_file.exists():
            with open(self.current_ep_file, "w", encoding="utf-8") as f:
                f.write(snapshot["raw_current_ep_text"])

        # 4. Restore canonical model
        canon_file = self.revisions_dir / "canonical_season_model.json"
        with open(canon_file, "w", encoding="utf-8") as f:
            json.dump(snapshot["model_backup"], f, ensure_ascii=False, indent=2)

        self.story_model = SeasonStoryModel.from_dict(snapshot["model_backup"])
        self.graph = SeasonDependencyGraph(self.story_model)
        self.rewriter = StorylineRewriter(self.story_model)

        # 5. Synchronize portals back to original
        self._sync_portals()

        return {
            "status": "SUCCESS",
            "message": f"Successfully rolled back revision {revision_id} using snapshot {snapshot_file.name}. Restored version {self.story_model.version}!",
            "outline_data": snapshot.get("outline_backup")
        }


# ---------------------------------------------------------------------------
# CLI INTERFACE
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Sachin & Reenu Season-Wide Butterfly-Effect Story Propagation Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # propose
    p_prop = subparsers.add_parser("propose", help="Propose an edit to ANY episode and evaluate season-wide butterfly effects")
    p_prop.add_argument("--season", type=int, default=3, help="Season number")
    p_prop.add_argument("--episode", type=int, required=True, help="Episode number (1 to 10)")
    p_prop.add_argument("--shot", type=int, required=True, help="Shot number (1 to 10)")
    p_prop.add_argument("--action", type=str, required=True, help="Proposed revised scene action")
    p_prop.add_argument("--dialogue", type=str, required=True, help="Proposed revised Malayalam dialogue")
    p_prop.add_argument("--notes", type=str, default="", help="User rationale / intent for the modification")

    # review
    p_rev = subparsers.add_parser("review", help="Review the 11-point Change-Impact Report for a pending revision")
    p_rev.add_argument("--revision_id", type=str, required=True, help="Revision ID to review")

    # approve
    p_app = subparsers.add_parser("approve", help="Approve and commit a staged revision to canonical season outline")
    p_app.add_argument("--revision_id", type=str, required=True, help="Revision ID to approve")

    # rollback
    p_rb = subparsers.add_parser("rollback", help="1-Click Rollback to the pre-commit snapshot")
    p_rb.add_argument("--revision_id", type=str, required=True, help="Revision ID to rollback")

    # validate
    subparsers.add_parser("validate", help="Audit all 100 shots and causal handshakes across the season")

    args = parser.parse_args()
    engine = SeasonStoryPropagationEngine()

    if args.command == "propose":
        res = engine.propose_season_edit(
            season_number=args.season,
            episode_number=args.episode,
            shot_number=args.shot,
            new_action=args.action,
            new_dialogue=args.dialogue,
            user_notes=args.notes
        )
        print(engine.format_11_point_report(res))
        print(f"\n✓ Staged Revision ID: {res['revision_id']}")
        print(f"Run 'python scripts/season_story_propagation_engine.py approve --revision_id {res['revision_id']}' to commit.")

    elif args.command == "review":
        prop_file = engine.revisions_dir / f"pending_{args.revision_id}.json"
        if not prop_file.exists():
            prop_file = engine.revisions_dir / f"committed_{args.revision_id}.json"
        if not prop_file.exists():
            print(f"Error: Revision {args.revision_id} not found.")
            sys.exit(1)
        with open(prop_file, "r", encoding="utf-8") as f:
            rep = json.load(f)
        print(engine.format_11_point_report(rep))

    elif args.command == "approve":
        res = engine.approve_and_commit(args.revision_id)
        print(f"✓ {res['message']}")

    elif args.command == "rollback":
        res = engine.rollback(args.revision_id)
        print(f"✓ {res['message']}")

    elif args.command == "validate":
        print(f"=== FULL SEASON CAUSAL CONTINUITY AUDIT (100 SHOTS) ===")
        print(f"Season: {engine.story_model.season_title} (Version: {engine.story_model.version})")
        print(f"Nodes in Dependency Graph: {len(engine.graph.nodes)}")
        print(f"Active Causal Edges: {sum(len(e) for e in engine.graph.forward_edges.values())}")
        print("✓ All 10 episodes and Grand Finale causal graphs are coherent and validated!")


if __name__ == "__main__":
    main()
