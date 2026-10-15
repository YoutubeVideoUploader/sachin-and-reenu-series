#!/usr/bin/env python3
"""
gemini_story_director.py
=============================================================================
GEMINI AI STORY & SHOT DIRECTOR ENGINE (5-TAB ARCHITECTURE)
=============================================================================
Powers the 3-mode Interactive Showrunner:
1. Change Specific Shot (with automated Inconsistency Detection & Dual-Button Healing)
2. Change Whole Episode (intelligently steering to Episode Climax)
3. Change Whole Season (clean 100-shot generation or downstream ripple K -> 100)

Architecture Rules:
- Tab 5 [Season_Shot_Outline] is the single source of truth.
- Tab 4 [Character_Registry] supplies persistent 3D Pixar DNA & season attire.
- Tab 2 [Current_JSON_Prompts] is derived from Tab 5 + Tab 4.
- Tab 1 [Episode_Story] is populated directly from Tab 5.
- Preceding shots (1 to K-1) are strictly frozen.
=============================================================================
"""

import os
import re
import sys
import json
import requests
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

OUTLINE_PATH = REPO_ROOT / "season_3_shot_outline.json"
STATE_PATH = REPO_ROOT / "story_state.json"
GAS_URL = os.getenv("GAS_WEBHOOK_URL") or "https://script.google.com/macros/s/AKfycbyivkrK_jL1ejwNqUvHe8KVFNkSuJSwZbWSmuE1YATqL5jCneMlqlKbf0EH7mwpc4gybA/exec"


class GeminiStoryDirector:
    def __init__(self, workspace_root: Path = None):
        self.workspace_root = Path(workspace_root) if workspace_root else REPO_ROOT
        self.state_path = self.workspace_root / "story_state.json"
        season = 3
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                season = int(json.load(f).get("season_number", season))
        except (OSError, ValueError, TypeError):
            pass
        self.season_number = season
        self.outline_path = self.workspace_root / f"season_{season}_shot_outline.json"

    @staticmethod
    def _locations_conflict(left: str, right: str) -> bool:
        """Avoid false alarms for descriptive variants of the same location."""
        normalize = lambda value: re.sub(r"[^a-z0-9]+", " ", str(value).casefold()).strip()
        a, b = normalize(left), normalize(right)
        if not a or not b or a == b:
            return False
        a_words, b_words = set(a.split()), set(b.split())
        if len(a_words & b_words) >= min(2, len(a_words), len(b_words)):
            return False
        return True

    def load_outline(self) -> dict:
        with open(self.outline_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_outline(self, data: dict):
        with open(self.outline_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_shot(self, episode_number: int, shot_number: int) -> dict:
        data = self.load_outline()
        shots = data.get("flattened_shots", [])
        for s in shots:
            if s.get("episode_number") == episode_number and s.get("shot_number") == shot_number:
                return dict(s)
        return {}

    def evaluate_shot_change(self, episode_number: int, shot_number: int, user_idea: str) -> dict:
        """
        Mode 1: Evaluates a proposed shot change.
        1. Drafts the new shot action & Malayalam dialogue.
        2. Detects continuity fractures with Shot K+1 (e.g., car interior vs living room).
        3. Offers dual-path healing options (Episode-Wise Steer vs Season-Wise Ripple).
        """
        current_shot = self.get_shot(episode_number, shot_number)
        previous_shot = self.get_shot(episode_number, shot_number - 1) if shot_number > 1 else None
        next_shot = self.get_shot(episode_number, shot_number + 1)
        if not next_shot and shot_number == 10:
            next_shot = self.get_shot(episode_number + 1, 1)

        # 1. Draft revised shot based on user idea
        user_idea_clean = user_idea.strip()
        speaker = current_shot.get("speaker", "Sachin")
        
        # Determine speaker if mentioned
        for char in ["Sachin", "Reenu", "Amal", "Caretaker", "Voice", "Narrator"]:
            if char.lower() in user_idea_clean.lower():
                speaker = char
                break

        # Check for location cues
        loc = current_shot.get("location", "Homestay")
        if "car" in user_idea_clean.lower():
            loc = "Car Interior / Mountain Road"
        elif "bridge" in user_idea_clean.lower():
            loc = "Old Munnar Suspension Bridge - Exterior Night"
        elif "room 13" in user_idea_clean.lower():
            loc = "Homestay hallway, outside Room 13"
        elif "factory" in user_idea_clean.lower():
            loc = "Abandoned tea factory - Interior"
        elif "clearing" in user_idea_clean.lower() or "outside" in user_idea_clean.lower():
            loc = "Abandoned tea factory - Exterior Clearing"

        # Construct Pixar 3D Action
        camera_shot_type = "Medium Shot (MS)" if "medium" in user_idea_clean.lower() else "Dynamic Cinematic Shot"
        proposed_action = f"{camera_shot_type}, Pixar 3D Camera: {user_idea_clean}. Lighting emphasizes character expressions and atmospheric mist."

        # Construct authentic Malayalam dialogue
        current_dia = current_shot.get("dialogue_malayalam", "")
        proposed_dialogue = f"{speaker}: (ഭാവത്തോടെ) '{user_idea_clean[:40]}...'"
        if "car" in user_idea_clean.lower() and "start" in user_idea_clean.lower():
            proposed_dialogue = f"{speaker}: (വെപ്രാളത്തോടെ) 'പെട്ടെന്ന് വണ്ടി സ്റ്റാർട്ട് ചെയ്യ്, അവിടെ എന്തോ അനങ്ങുന്നുണ്ട്!'"
        elif "run" in user_idea_clean.lower() or "ഓട്" in user_idea_clean:
            proposed_dialogue = f"{speaker}: (അലറിക്കൊണ്ട്) 'നിൽക്കാനല്ലേ പറഞ്ഞത്, ഓടിക്കോ രക്ഷപെട്!!'"

        proposed_shot = {
            "episode_number": episode_number,
            "shot_number": shot_number,
            "speaker": speaker,
            "action": proposed_action,
            "dialogue_malayalam": proposed_dialogue,
            "location": loc,
            "persistent_props": current_shot.get("persistent_props", [])
        }

        # 2. Inconsistency & Flow Detection with Shot K+1
        has_inconsistency = False
        inconsistency_details = ""
        recommendation = ""
        can_episode_steer = True

        if previous_shot and self._locations_conflict(previous_shot.get("location", ""), loc):
            has_inconsistency = True
            inconsistency_details = (
                f"Physical Location Fracture Detected: Shot {shot_number - 1} ends at "
                f"'{previous_shot.get('location', '')}', while the proposed Shot {shot_number} begins at '{loc}'."
            )
            recommendation = "EPISODE_STEER_RECOMMENDED"

        if next_shot:
            next_loc = next_shot.get("location", "")
            next_act = next_shot.get("action", "")

            # Location mismatch (e.g. entering car vs talking in living room)
            if self._locations_conflict(loc, next_loc):
                has_inconsistency = True
                details = (
                    f"⚠️ Physical Location Fracture Detected: Shot {shot_number} places characters in '{loc}', "
                    f"but Shot {shot_number + 1} takes place in '{next_loc}'. Characters cannot instantaneously teleport without a transition."
                )
                inconsistency_details = f"{inconsistency_details} {details}".strip()

            # Radical change that cannot lead to current episode cliffhanger
            if shot_number >= 8 and "escape" in user_idea_clean.lower() and "Room 13" in next_loc:
                can_episode_steer = False
                recommendation = "SEASON_WISE_REQUIRED"
                inconsistency_details += " Additionally, this radical change breaks the planned Episode Climax at Shot 10. A Season-Wise Change is required."
            elif has_inconsistency:
                recommendation = "EPISODE_STEER_RECOMMENDED"

            proposed_props = {str(p).casefold() for p in proposed_shot.get("persistent_props", [])}
            next_text = f"{next_act} {next_shot.get('dialogue_malayalam', '')}".casefold()
            next_props = {str(p).casefold() for p in next_shot.get("persistent_props", [])}
            lost_props = [p for p in proposed_props if p not in next_props and p not in next_text]
            if lost_props:
                has_inconsistency = True
                details = f"Persistent prop continuity break: {', '.join(sorted(lost_props))} are carried into Shot {shot_number} but are absent from Shot {shot_number + 1}."
                inconsistency_details = f"{inconsistency_details} {details}".strip()
                recommendation = "EPISODE_STEER_RECOMMENDED"

        return {
            "success": True,
            "episode_number": episode_number,
            "shot_number": shot_number,
            "current_shot": current_shot,
            "previous_shot": previous_shot,
            "next_shot": next_shot,
            "proposed_shot": proposed_shot,
            "has_inconsistency": has_inconsistency,
            "inconsistency_details": inconsistency_details,
            "can_episode_steer": can_episode_steer,
            "recommendation": recommendation or "EPISODE_STEER_RECOMMENDED"
        }

    def apply_episode_wise_change(self, episode_number: int, shot_number: int, proposed_shot: dict) -> dict:
        """
        Applies changes to current episode only:
        - Updates Shot K with proposed_shot.
        - Intelligently realigns Shots K+1 through 9 to lead naturally into existing Shot 10 cliffhanger.
        - Updates Tab 5 and regenerates Tab 2 for this episode.
        """
        data = self.load_outline()
        episodes = data.get("episodes", [])
        target_ep = next((ep for ep in episodes if ep.get("episode_number") == episode_number), None)
        if not target_ep:
            return {"error": f"Episode {episode_number} not found"}

        ep_shots = target_ep.get("shots", [])
        
        # 1. Update Shot K
        for s in ep_shots:
            if s.get("shot_number") == shot_number:
                s.update({
                    "speaker": proposed_shot.get("speaker", s.get("speaker")),
                    "action": proposed_shot.get("action", s.get("action")),
                    "dialogue_malayalam": proposed_shot.get("dialogue_malayalam", s.get("dialogue_malayalam")),
                    "location": proposed_shot.get("location", s.get("location")),
                    "persistent_props": proposed_shot.get("persistent_props", s.get("persistent_props"))
                })
                break

        # 2. Intelligently realign intermediate shots (K+1 to 9) toward Shot 10
        shot_10 = next((s for s in ep_shots if s.get("shot_number") == 10), None)
        dest_loc = shot_10.get("location") if shot_10 else proposed_shot.get("location")
        start_loc = proposed_shot.get("location")

        for s in ep_shots:
            sn = s.get("shot_number")
            if shot_number < sn < 10:
                # Smooth the transition toward dest_loc
                if sn == shot_number + 1:
                    s["action"] = f"Medium Shot (MS), Pixar 3D Camera: Reacting to the events at {start_loc}, the trio hastily transitions toward {dest_loc}. Tension mounts as Sachin leads the way."
                    s["location"] = start_loc
                else:
                    s["action"] = f"Cinematic Shot, Pixar 3D Camera: Approaching {dest_loc}. " + s.get("action", "")
                    s["location"] = dest_loc

        # Re-flatten
        self._rebuild_and_save(data)
        self._sync_tab2_and_portals(episode_number)
        self._push_to_tab5_in_sheet()

        return {
            "success": True,
            "scope": "EPISODE_WISE",
            "message": f"Successfully applied intelligent Episode-Wise change to Episode {episode_number}! Shots {shot_number} to 9 reconciled and naturally connected to Shot 10."
        }

    def apply_season_wise_change(self, episode_number: int, shot_number: int, proposed_shot: dict) -> dict:
        """
        Applies changes downstream across Season:
        - Freezes all shots prior to K (1 to K-1).
        - Modifies Shot K.
        - Propagates ripple across downstream shots and episodes (K to 100).
        - Updates Tab 5, regenerates Tab 2, updates Tab 1.
        """
        data = self.load_outline()
        flattened = data.get("flattened_shots", [])
        
        target_idx = None
        for i, s in enumerate(flattened):
            if s.get("episode_number") == episode_number and s.get("shot_number") == shot_number:
                target_idx = i
                break

        if target_idx is None:
            return {"error": "Target shot not found"}

        # 1. Update target shot K
        flattened[target_idx].update({
            "speaker": proposed_shot.get("speaker", flattened[target_idx].get("speaker")),
            "action": proposed_shot.get("action", flattened[target_idx].get("action")),
            "dialogue_malayalam": proposed_shot.get("dialogue_malayalam", flattened[target_idx].get("dialogue_malayalam")),
            "location": proposed_shot.get("location", flattened[target_idx].get("location")),
            "persistent_props": proposed_shot.get("persistent_props", flattened[target_idx].get("persistent_props"))
        })

        # 2. Downstream ripple across remaining shots (K+1 to end)
        new_loc = proposed_shot.get("location")
        for i in range(target_idx + 1, len(flattened)):
            s = flattened[i]
            directive = f"Continuity from Episode {episode_number} Shot {shot_number}: account for {proposed_shot.get('speaker')}'s changed action at {new_loc}."
            action = str(s.get("action", ""))
            if directive not in action:
                s["action"] = f"{directive} {action}".strip()

        # Reconstruct episodes structure from flattened
        episodes_map = {}
        for s in flattened:
            ep_n = s.get("episode_number")
            episodes_map.setdefault(ep_n, []).append(s)

        for ep in data.get("episodes", []):
            ep_n = ep.get("episode_number")
            if ep_n in episodes_map:
                ep["shots"] = episodes_map[ep_n]

        data["flattened_shots"] = flattened
        self.save_outline(data)
        self._sync_tab2_and_portals(episode_number)
        self._push_to_tab5_in_sheet()

        return {
            "success": True,
            "scope": "SEASON_WISE",
            "message": f"Successfully applied Season-Wise ripple from Episode {episode_number} Shot {shot_number} downstream! Preceding shots strictly preserved."
        }

    def _rebuild_and_save(self, data: dict):
        flattened = []
        for ep in data.get("episodes", []):
            ep_n = ep.get("episode_number")
            for s in ep.get("shots", []):
                flat = dict(s)
                flat["season_number"] = self.season_number
                flat["episode_number"] = ep_n
                flat["episode_title"] = ep.get("title_malayalam", ep.get("title_english", ""))
                flattened.append(flat)
        data["flattened_shots"] = flattened
        self.save_outline(data)

    def _sync_tab2_and_portals(self, active_episode: int):
        try:
            import subprocess
            subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "story_and_prompt_engine.py"), "--mode", "compile_episode",
                 "--season", str(self.season_number), "--target_ep", str(active_episode)],
                cwd=str(self.workspace_root), check=True, timeout=180
            )
            subprocess.run([sys.executable, str(SCRIPTS_DIR / "update_portals.py")], cwd=str(self.workspace_root), check=True)
        except Exception as e:
            print(f"[Notice] prompt/portal synchronization: {e}")

    def _push_to_tab5_in_sheet(self):
        try:
            data = self.load_outline()
            shots = data.get("flattened_shots", [])
            payload = {
                "action": "save_season_shot_outline",
                "season_number": self.season_number,
                "season_title": f"Season {self.season_number}",
                "shots": shots
            }
            requests.post(GAS_URL, data=json.dumps(payload), headers={"Content-Type": "text/plain"}, timeout=30)
        except Exception as e:
            print(f"[Notice] Google Sheet Tab 5 sync: {e}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    director = GeminiStoryDirector()
    eval_res = director.evaluate_shot_change(3, 1, "Sachin and Amal get into the car and drive away")
    print(json.dumps(eval_res, indent=2, ensure_ascii=False))
