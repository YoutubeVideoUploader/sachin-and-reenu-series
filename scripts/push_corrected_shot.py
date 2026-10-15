#!/usr/bin/env python3
"""
=============================================================================
push_corrected_shot.py - Integrated Production Episode & Shot Revision Workflow
Sachin & Reenu AI Animation Studio
=============================================================================
Connects episode and scene editing directly to the Season-Wide Butterfly-Effect
Story Propagation Engine.

Workflow:
1. Accepts proposed scene action and Malayalam dialogue changes for ANY episode and shot.
2. Traces direct and indirect season-wide consequences using the Causal Dependency Graph.
3. Formulates coherent alternative screenplay proposals, adapting downstream scenes and the Grand Finale.
4. Preserves 100% of Character DNA and approved dialogue in unaffected scenes.
5. Audits stale video assets and prompts; protects video rendering behind explicit approval.
6. Stages revisions for user review with full 11-point Change-Impact Reports.
7. Upon approval (--approve), commits updates transactionally to:
   - season_3_shot_outline.json (100-shot master roadmap)
   - current_episode_shots.json (if active episode affected)
   - story_state.json
   - workspace portals (via update_portals.py)
   - optionally Google Sheets (Tab 2, Tab 7) if --sync-gas is set
8. Supports 1-click instant rollback (--rollback <revision_id>) using pre-commit snapshots.
=============================================================================
"""

import sys
import os
import json
import argparse
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from season_story_propagation_engine import SeasonStoryPropagationEngine
except ImportError:
    from scripts.season_story_propagation_engine import SeasonStoryPropagationEngine

DEFAULT_GAS_URL = "https://script.google.com/macros/s/AKfycbyivkrK_jL1ejwNqUvHe8KVFNkSuJSwZbWSmuE1YATqL5jCneMlqlKbf0EH7mwpc4gybA/exec"


def main():
    parser = argparse.ArgumentParser(
        description="Sachin & Reenu Production Episode Editing & Butterfly Propagation Workflow"
    )
    parser.add_argument("--season", type=int, default=3, help="Season number (default: 3)")
    parser.add_argument("--episode", type=int, default=2, help="Episode number (1 to 10, default: 2)")
    parser.add_argument("--shot", type=int, default=2, help="Shot number (1 to 10, default: 2)")
    parser.add_argument("--action", type=str, default="", help="Proposed revised scene action")
    parser.add_argument("--dialogue", type=str, default="", help="Proposed revised Malayalam dialogue")
    parser.add_argument("--notes", type=str, default="", help="User intent / rationale for revision")
    parser.add_argument("--removed-facts", nargs="*", default=None, help="Fact IDs removed by this edit")
    parser.add_argument("--added-facts", nargs="*", default=None, help="Fact IDs added by this edit")
    parser.add_argument("--approve", nargs="?", const="AUTO", default=None, help="Approve and commit the staged revision (or pass revision ID)")
    parser.add_argument("--rollback", type=str, default="", help="Rollback revision ID to its pre-commit snapshot")
    parser.add_argument("--sync-gas", action="store_true", help="Push committed changes to Google Sheets")
    parser.add_argument("--gas-url", type=str, default=DEFAULT_GAS_URL, help="Google Apps Script endpoint")

    args = parser.parse_args()

    # Initialize Engine pointing to repository root or sandbox
    ws_root = Path.cwd() if (Path.cwd() / "season_3_shot_outline.json").exists() else REPO_ROOT
    engine = SeasonStoryPropagationEngine(workspace_root=ws_root)

    # 1. Handle Standalone Approve by ID
    if args.approve and args.approve != "AUTO" and not args.action:
        print(f"\n[WORKFLOW] Approving and committing revision: {args.approve}")
        commit_res = engine.approve_and_commit(args.approve)
        print(f"✓ {commit_res['message']}")
        return

    # 2. Handle Rollback Command
    if args.rollback:
        print(f"\n[WORKFLOW] Executing 1-Click Rollback for revision: {args.rollback}")
        res = engine.rollback(args.rollback)
        print(f"✓ {res['message']}")
        # Keep portals in sync
        try:
            import update_portals
        except Exception:
            pass
        return

    # 2. Determine Action & Dialogue (with sensible defaults for Ep 2 Shot 2 if empty)
    action = args.action
    dialogue = args.dialogue
    notes = args.notes

    if not action and not dialogue and args.episode == 2 and args.shot == 2:
        action = "Amal nervously grips the steering wheel, his eyes darting across the dark rearview mirrors."
        dialogue = "ഇത്രയും കോടമഞ്ഞിൽ ആരും നടന്നുപോവില്ല സച്ചിൻ."
        notes = "Specification correction for Episode 2 Shot 2"

    if not action:
        print("Error: --action must be provided.")
        parser.print_help()
        sys.exit(1)

    print(f"\n=============================================================================")
    print(f"🎬 SACHIN & REENU EPISODE EDITING WORKFLOW: Season {args.season} Episode {args.episode} Shot {args.shot}")
    print(f"=============================================================================")
    print(f"Proposed Action:   {action}")
    print(f"Proposed Dialogue: {dialogue}")
    print(f"Rationale:         {notes or 'Direct scene revision'}")
    print("-----------------------------------------------------------------------------")

    # Step 1: Trace Season-Wide Butterfly Consequences & Stage Proposal
    print("\n[STEP 1/3] Tracing season-wide causal dependencies and generating 11-point Change-Impact Report...")
    proposal = engine.propose_season_edit(
        season_number=args.season,
        episode_number=args.episode,
        shot_number=args.shot,
        new_action=action,
        new_dialogue=dialogue,
        user_notes=notes,
        removed_fact_ids=args.removed_facts,
        added_fact_ids=args.added_facts
    )

    report_text = engine.format_11_point_report(proposal)
    print("\n" + report_text)

    rev_id = proposal["revision_id"]
    print(f"\n✓ Revision staged successfully: `{rev_id}`")
    print(f"  Pending file: story_revisions/pending_{rev_id}.json")
    print(f"  Canonical baseline on disk remains 100% UNCHANGED until explicit approval.")

    # Step 2: Handle Approval & Commit if requested
    if args.approve:
        print(f"\n[STEP 2/3] Approving and committing revision `{rev_id}`...")
        commit_res = engine.approve_and_commit(rev_id)
        print(f"✓ {commit_res['message']}")
        print(f"  Pre-commit rollback snapshot created: {commit_res['snapshot_file']}")

        # Synchronize portals
        print("\n[STEP 3/3] Synchronizing workspace portals...")
        try:
            import update_portals
            print("✓ Portal HTML files synchronized with updated season canon.")
        except Exception as e:
            print(f"Notice updating portals: {e}")

        # Optional Google Sheets push
        if args.sync_gas:
            import requests
            print(f"\nPushing synchronized outline to Google Sheets ({args.gas_url})...")
            try:
                with open(REPO_ROOT / "season_3_shot_outline.json", "r", encoding="utf-8") as f:
                    outline_data = json.load(f)
                tab7_payload = {
                    "action": "save_season_shot_outline",
                    "season_number": args.season,
                    "season_title": outline_data.get("season_title", "Season 3: The Munnar Trip"),
                    "shots": outline_data.get("flattened_shots", [])
                }
                res = requests.post(args.gas_url, data=json.dumps(tab7_payload), headers={"Content-Type": "text/plain"}, timeout=45)
                print(f"Google Sheet response: HTTP {res.status_code}")
            except Exception as ge:
                print(f"Notice pushing to Google Sheets: {ge}")

    else:
        print(f"\n[NEXT STEPS]")
        print(f"To approve and commit this revision, execute:")
        print(f"  python scripts/push_corrected_shot.py --approve --season {args.season} --episode {args.episode} --shot {args.shot} --action \"{action}\" --dialogue \"{dialogue}\"")
        print(f"Or via the Master Propagation CLI:")
        print(f"  python scripts/season_story_propagation_engine.py approve --revision_id {rev_id}")


if __name__ == "__main__":
    main()

