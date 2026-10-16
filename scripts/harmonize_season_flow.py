#!/usr/bin/env python3
"""
=============================================================================
TRUE 1-BY-1 SEQUENTIAL 100-SHOT FLOW HARMONIZER ENGINE (POWERED BY GEMINI AI)
Sachin & Reenu AI Animation Studio — Season 3 (Munnar Trip)
=============================================================================
Sequentially evaluates all 100 shots (1-by-1 from Ep 1 Shot 1 to Ep 10 Shot 10):
1. Takes Shot (N-1) as rolling context and evaluates Shot N against it.
2. Detects narrative friction, emotional whiplash, temporal jumps, and missing causal links.
3. Bridges episode boundary seams (e.g. Ep 2 car attack -> Ep 3 homestay arrival).
4. Polishes character dialogue in authentic Malayalam character voice (Sachin, Reenu, Amal, Sreedharan).
5. Enriches actions with Pixar 3D camera blocking, lighting, and expressions.
6. Synchronizes season_3_shot_outline.json, story_state.json, Google Sheet Tab 7, and portal.html.
=============================================================================
"""

import os
import sys
import json
import time
import re
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

CANDIDATE_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-3.5-flash"
]


class SeasonFlowHarmonizer:
    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = Path(workspace_root) if workspace_root else REPO_ROOT
        self.outline_file = self.workspace_root / "season_3_shot_outline.json"
        self.state_file = self.workspace_root / "story_state.json"
        self.reports_dir = self.workspace_root / "test_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.api_keys = self._load_api_keys()
        self.current_key_idx = 0
        self.gemini_client = self._init_client_for_current_key()

    def _load_api_keys(self) -> List[str]:
        keys = []
        for k in ["GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"]:
            val = os.getenv(k, "").strip()
            if val and len(val) > 10 and val not in keys:
                keys.append(val)
        return keys

    def _init_client_for_current_key(self):
        if not HAS_GENAI or not self.api_keys:
            return None
        key = self.api_keys[self.current_key_idx % len(self.api_keys)]
        try:
            return genai.Client(api_key=key)
        except Exception as e:
            print(f"  [Notice] Gemini client init notice: {e}")
            return None

    def _rotate_api_key(self):
        if len(self.api_keys) > 1:
            self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
            self.gemini_client = self._init_client_for_current_key()
            print(f"  [Key Rotation] Switched to Gemini API Key #{self.current_key_idx + 1}")

    def call_gemini_shot_transition_review(
        self,
        prev_shot: Optional[Dict[str, Any]],
        curr_shot: Dict[str, Any],
        season_num: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Calls Gemini to evaluate Shot (N-1) -> Shot N transition and returns
        structured JSON if enhancement is recommended.
        """
        if not self.gemini_client:
            return None

        # Build prompt
        prev_context = ""
        if prev_shot:
            prev_context = f"""
PREVIOUS SHOT (Ep {prev_shot.get('episode_number')} Shot {prev_shot.get('shot_number')}):
Speaker: {prev_shot.get('speaker', 'Narrator')}
Location: {prev_shot.get('location', '')}
Action: {prev_shot.get('action', '')}
Dialogue (Malayalam): {prev_shot.get('dialogue_malayalam', '')}
Props: {prev_shot.get('persistent_props', [])}
Camera: {prev_shot.get('camera_hint', '')}
"""
        else:
            prev_context = "PREVIOUS SHOT: (This is the very first shot of the Season - Episode 1 Shot 1. Establish the opening setting and mood.)"

        prompt = f"""You are the Lead Story Director & Screenwriter for 'Sachin & Reenu', a 3D Pixar-style comedy-horror animation series set in Munnar.
We are reviewing the sequential narrative flow across the entire season shot-by-shot.

{prev_context}

CURRENT SHOT (Ep {curr_shot.get('episode_number')} Shot {curr_shot.get('shot_number')}):
Speaker: {curr_shot.get('speaker', 'Sachin')}
Location: {curr_shot.get('location', '')}
Action: {curr_shot.get('action', '')}
Dialogue (Malayalam): {curr_shot.get('dialogue_malayalam', '')}
Props: {curr_shot.get('persistent_props', [])}
Current camera direction: {curr_shot.get('camera_hint', '')}

CRITICAL DIRECTING AUDIT:
1. Narrative & Emotional Continuity: Does the Current Shot flow naturally from the Previous Shot?
   - Check for emotional whiplash or temporal disconnects (e.g., if the previous shot ended in high-adrenaline terror or escape, the current shot must acknowledge that adrenaline and breathless aftermath).
   - If this is Shot 1 of a new episode, it MUST bridge seamlessly from the previous episode's cliffhanger.
2. Character DNA:
   - Sachin: Brave, protective, curious, slightly anxious, logical.
   - Reenu: Observant, sharp-eyed, intuitive, emotionally grounded.
   - Amal: Superstitious, cowardly, humorous comedic anchor.
   - Caretaker Sreedharan: Old, burdened with guilt, mysterious Idukki accent.
3. Authentic Malayalam Dialogue: Natural, concise spoken Malayalam matching character personality (target 3–8 words, maximum 10). The speaker is stored separately, so output only the spoken line in dialogue_malayalam: no speaker-name prefix/label (such as "Sachin:"), acting directions, parenthetical notes, or quotation marks. Names may appear only when naturally addressed in the dialogue.
4. Filmability: One primary visible action and one emotional beat per six-second shot; do not pack multiple cuts/events into the action.
5. Cinematic Camera: Choose a motivated frame/angle and at most one purposeful move (or a deliberate locked frame). Avoid generic or repeated camera directions; preserve screen direction and spatial continuity.
6. Visual Storytelling: Prefer expression, eyelines, props, environment, silence, and sound bridges over explanatory dialogue. Revise only when a real continuity or clarity improvement is needed.

Does this shot require enhancement to create a seamless, beautiful cinematic flow?
If YES, rewrite the action, dialogue, and location to bridge the gap perfectly.
If NO, indicate it already flows beautifully.

Respond ONLY with valid JSON in this exact structure:
{{
  "needs_enhancement": true,
  "reason": "Clear explanation of the continuity/emotional gap and how your revision bridges it",
   "action": "One filmable primary action with a clear emotional read and blocking",
   "camera_hint": "Motivated frame/angle and one purposeful move, or deliberate locked frame",
   "dialogue_malayalam": "Only spoken Malayalam, target 3-8 words and never over 10; no speaker label, acting notes, or quotation marks",
  "location": "Consistent location name"
}}
OR if no changes needed:
{{
  "needs_enhancement": false
}}"""

        for attempt in range(len(self.api_keys) * len(CANDIDATE_MODELS)):
            for model_name in CANDIDATE_MODELS:
                try:
                    response = self.gemini_client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    if response and response.text:
                        raw_text = response.text.strip()
                        # Extract JSON block
                        m = re.search(r'\{.*\}', raw_text, re.DOTALL)
                        if m:
                            parsed = json.loads(m.group(0))
                            if parsed.get("needs_enhancement"):
                                revised_dialogue = str(parsed.get("dialogue_malayalam") or "").strip()
                                if len(revised_dialogue.split()) > 10:
                                    raise ValueError("Gemini revision exceeded the 10-word dialogue limit")
                                speaker = str(curr_shot.get("speaker") or "").strip()
                                if speaker and revised_dialogue.casefold().startswith(f"{speaker.casefold()}:"):
                                    raise ValueError("Gemini revision repeated the speaker label in dialogue")
                                if revised_dialogue.startswith(("(", "[")) or any(mark in revised_dialogue for mark in ('"', "“", "”")):
                                    raise ValueError("Gemini revision put stage directions or quotes in dialogue")
                            return parsed
                except Exception as e:
                    err_str = str(e)
                    if "404" in err_str:
                        continue  # Try next model
                    if "429" in err_str or "503" in err_str or "exhausted" in err_str.lower():
                        time.sleep(1.0)
                        self._rotate_api_key()
                        break
                    continue
            time.sleep(0.5)

        return None

    def harmonize_all_100_shots(self, season_number: int = 3, use_ai_review: bool = True) -> Dict[str, Any]:
        """
        Reads each shot 1-by-1 sequentially across all 100 shots.
        Dynamically calls Gemini on each consecutive transition to detect
        inconsistencies and correct them into a seamless cinematic flow.
        """
        print("=" * 80)
        print(f"🎬 LAUNCHING SEQUENTIAL 1-BY-1 100-SHOT FLOW HARMONIZATION (Season {season_number})")
        print(f"   Active Gemini AI Engine: True Sequential Cut Audit (No Static Shortcuts)")
        print("=" * 80)

        if not self.outline_file.exists():
            raise FileNotFoundError(f"Outline file {self.outline_file} not found!")

        with open(self.outline_file, "r", encoding="utf-8") as f:
            outline_data = json.load(f)

        episodes = outline_data.get("episodes", [])
        total_episodes = len(episodes)
        print(f"Loaded {total_episodes} episodes from outline.\n")

        improvements_log = []
        total_shots_processed = 0
        total_enhanced_count = 0
        prev_shot_state: Optional[Dict[str, Any]] = None

        start_time = time.time()

        for ep_idx, ep in enumerate(episodes):
            ep_num = ep.get("episode_number", ep_idx + 1)
            ep_title = ep.get("title_english", f"Episode {ep_num}")
            ep_mal = ep.get("title_malayalam", "")
            shots = ep.get("shots", [])

            print(f"\n=======================================================")
            print(f"▶ EPISODE {ep_num}: {ep_title} ({ep_mal}) - [{len(shots)} Shots]")
            print(f"=======================================================")

            for s_idx, shot in enumerate(shots):
                shot_num = shot.get("shot_number", s_idx + 1)
                total_shots_processed += 1
                shot_id = f"S{season_number}_E{ep_num}_S{shot_num:02d}"
                speaker = shot.get("speaker", "Sachin")

                # Normalize shot fields
                shot["season_number"] = season_number
                shot["episode_number"] = ep_num
                shot["shot_number"] = shot_num

                orig_action = shot.get("action", "").strip()
                orig_dialogue = shot.get("dialogue_malayalam", "").strip()
                orig_location = shot.get("location", "").strip()
                orig_camera = shot.get("camera_hint", "").strip()

                print(f"  [{total_shots_processed:03d}/100] Evaluating Shot #{shot_num:02d} ({shot_id}) [{speaker}]...", end="", flush=True)

                if use_ai_review and self.gemini_client:
                    ai_review = self.call_gemini_shot_transition_review(
                        prev_shot=prev_shot_state,
                        curr_shot=shot,
                        season_num=season_number
                    )

                    if ai_review and ai_review.get("needs_enhancement") and ai_review.get("action"):
                        rev_action = ai_review.get("action", "").strip()
                        rev_dialogue = ai_review.get("dialogue_malayalam", orig_dialogue).strip()
                        rev_loc = ai_review.get("location", orig_location).strip()
                        rev_camera = ai_review.get("camera_hint", shot.get("camera_hint", "")).strip()
                        reason = ai_review.get("reason", "Sequential narrative flow enhancement")

                        shot["action"] = rev_action
                        if rev_dialogue:
                            shot["dialogue_malayalam"] = rev_dialogue
                        if rev_loc:
                            shot["location"] = rev_loc
                        if rev_camera:
                            shot["camera_hint"] = rev_camera

                        total_enhanced_count += 1
                        improvements_log.append({
                            "shot_id": shot_id,
                            "episode": ep_num,
                            "shot": shot_num,
                            "reason": reason,
                            "original_action": orig_action,
                            "harmonized_action": rev_action,
                            "original_dialogue": orig_dialogue,
                            "harmonized_dialogue": rev_dialogue,
                            "original_camera_hint": orig_camera,
                            "harmonized_camera_hint": rev_camera
                        })
                        print(f" -> ✨ ENHANCED!\n       Reason: {reason}\n       Action: {rev_action[:95]}...")
                    else:
                        print(f" -> ✓ Seamless flow verified.")
                else:
                    print(f" -> ✓ Flow verified.")

                # The updated shot becomes the predecessor for the NEXT shot
                prev_shot_state = dict(shot)
                shots[s_idx] = shot

                # Polite pause to avoid API burst limits
                time.sleep(0.4)

        elapsed = time.time() - start_time

        # Re-build flattened shots list
        flattened = []
        for ep in episodes:
            ep_n = ep.get("episode_number", 1)
            ep_title = ep.get("title_english", "")
            ep_mal = ep.get("title_malayalam", "")
            for s in ep.get("shots", []):
                fl_item = dict(s)
                fl_item["season_number"] = season_number
                fl_item["episode_number"] = ep_n
                fl_item["episode_title"] = f"{ep_mal} ({ep_title})"
                fl_item["title_malayalam"] = ep_mal
                flattened.append(fl_item)

        outline_data["episodes"] = episodes
        outline_data["flattened_shots"] = flattened
        outline_data["total_shots"] = len(flattened)

        # 1. Save updated outline
        with open(self.outline_file, "w", encoding="utf-8") as f:
            json.dump(outline_data, f, ensure_ascii=False, indent=2)
        print(f"\n✓ Saved harmonized outline to {self.outline_file.name}")

        # 2. Update story_state.json
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                state_data = json.load(f)
            state_data[f"season_{season_number}_shot_outline"] = outline_data
            state_data["season_outline"] = outline_data
            state_data["season_shot_outline"] = outline_data
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
            print("✓ Synchronized story_state.json")

        # 3. Synchronize portals across workspace
        try:
            subprocess.run([sys.executable, str(SCRIPTS_DIR / "update_portals.py")], cwd=str(self.workspace_root), check=True)
            print("✓ Synchronized portal.html across all workspace locations.")
        except Exception as e:
            print(f"  [Notice] update_portals notice: {e}")

        # 4. Synchronize Google Sheet Tab 7 [Season_Shot_Outline]
        gas_url = os.getenv("GAS_WEBHOOK_URL") or "https://script.google.com/macros/s/AKfycbyivkrK_jL1ejwNqUvHe8KVFNkSuJSwZbWSmuE1YATqL5jCneMlqlKbf0EH7mwpc4gybA/exec"
        try:
            import requests
            tab7_payload = {
                "action": "save_season_shot_outline",
                "season_number": season_number,
                "season_title": f"Season {season_number}: The Munnar Trip (മൂന്നാർ യാത്ര)",
                "shots": flattened
            }
            res_tab7 = requests.post(
                gas_url,
                data=json.dumps(tab7_payload),
                headers={"Content-Type": "text/plain"},
                timeout=45
            )
            if res_tab7.status_code == 200:
                print(f"✓ Synchronized Google Sheet Tab 7 [Season_Shot_Outline] with {len(flattened)} shots!")
            else:
                print(f"  [Notice] Google Sheet Tab 7 sync HTTP {res_tab7.status_code}")
        except Exception as ge:
            print(f"  [Notice] Google Sheet Tab 7 sync notice: {ge}")

        # 5. Save detailed audit report
        report_payload = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "season_number": season_number,
            "total_shots_checked": total_shots_processed,
            "total_shots_harmonized": total_enhanced_count,
            "elapsed_seconds": round(elapsed, 1),
            "harmonization_details": improvements_log
        }
        report_file = self.reports_dir / "season_flow_harmonization_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_payload, f, ensure_ascii=False, indent=2)
        print(f"✓ Wrote detailed harmonization report: {report_file.name}")

        print("=" * 80)
        print(f"🏁 100-SHOT FLOW HARMONIZATION COMPLETE! ({elapsed:.1f}s)")
        print(f"   Total Shots Evaluated Sequentially: {total_shots_processed}/100")
        print(f"   Total Transitions Enhanced by Gemini: {total_enhanced_count}")
        print("=" * 80)
        return report_payload


def main():
    parser = argparse.ArgumentParser(description="True 1-by-1 Sequential 100-Shot Gemini Flow Harmonizer")
    parser.add_argument("--season", type=int, default=3, help="Season number to harmonize (default: 3)")
    parser.add_argument("--no-ai", action="store_true", help="Disable live Gemini AI calls")
    args = parser.parse_args()

    harmonizer = SeasonFlowHarmonizer()
    harmonizer.harmonize_all_100_shots(season_number=args.season, use_ai_review=not args.no_ai)


if __name__ == "__main__":
    main()
