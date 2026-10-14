#!/usr/bin/env python3
"""
Full System Master Synchronization Script
Synchronizes:
1. Tab 2 [Current_JSON_Prompts] in Google Sheet
2. Tab 7 [Season_Shot_Outline] in Google Sheet
3. current_episode_shots.json
4. season_3_shot_outline.json (Master 100-Shot Roadmap)
5. story_state.json
6. All workspace portal.html files
"""

import sys
import os
import json
import requests
from pathlib import Path

sys.path.append(os.path.dirname(__file__))
from universal_continuity_engine import (
    synchronize_master_outline_and_episode,
    compile_single_shot_prompt,
    UniversalSceneTracker,
    MASTER_STYLE,
    DNA_AMAL,
    DNA_SACHIN,
    DNA_REENU,
    CANONICAL_DNA_MAP,
    VOICE_MAP
)

DEFAULT_GAS_URL = "https://script.google.com/macros/s/AKfycbyivkrK_jL1ejwNqUvHe8KVFNkSuJSwZbWSmuE1YATqL5jCneMlqlKbf0EH7mwpc4gybA/exec"

# SACRED, UNALTERED USER DIALOGUE & EPISODE 2 SCRIPT
EPISODE_2_RAW = [
    {
        "shot_number": 1,
        "character": "Sachin",
        "dialogue_malayalam": "ആ വഴിപോക്കയായ സ്ത്രീയെ പെട്ടെന്ന് കാണാതായല്ലോ!",
        "action_summary": "Sachin peers through the misty passenger-side window in astonishment, noticing the woman disappearing into the thick fog while Amal navigates the car forward.",
        "location": "Mountain road car interior",
        "persistent_props": ["Car steering wheel", "Rearview mirror", "Dashboard dials", "Car keys", "Sachin's cross-bag"],
        "camera": "Cinematic 3D medium close-up focused on Sachin looking out window"
    },
    {
        "shot_number": 2,
        "character": "Amal",
        "dialogue_malayalam": "ഇത്രയും കോടമഞ്ഞിൽ ആരും നടന്നുപോവില്ല സച്ചിൻ.",
        "action_summary": "Amal nervously grips the steering wheel tightly in the driver's seat, his eyes darting across the dark rearview mirrors and misted windshield.",
        "location": "Mountain road car interior",
        "persistent_props": ["Car steering wheel", "Rearview mirror", "Dashboard dials", "Car keys"],
        "camera": "Cinematic 3D medium shot focused on Amal in driver seat"
    },
    {
        "shot_number": 3,
        "character": "Amal",
        "dialogue_malayalam": "ചെക്കാ, നമ്മുടെ വണ്ടി ഇപ്പോൾ പണി തന്നു!",
        "action_summary": "Amal twists the car ignition key frantically in the driver's seat as the vehicle shudders, the dashboard lights flicker, and the engine sputters dead on the dark mountain road.",
        "location": "Mountain road car interior",
        "persistent_props": ["Car steering wheel", "Car ignition key", "Dashboard dials"],
        "camera": "Dramatic 3D medium close-up of Amal turning ignition key with worried look"
    },
    {
        "shot_number": 4,
        "character": "Sachin",
        "dialogue_malayalam": "നീ പേടിക്കാതെടാ, ഞാൻ ബോണറ്റ് തുറന്ന് നോക്കാം.",
        "action_summary": "Sachin unbuckles his seatbelt in the front passenger seat and prepares to crack open the passenger door into the biting mountain cold to inspect the car bonnet.",
        "location": "Mountain road car interior",
        "persistent_props": ["Car steering wheel", "Passenger door handle", "Sachin's cross-bag"],
        "camera": "Cinematic 3D medium shot of Sachin unbuckling in passenger seat"
    },
    {
        "shot_number": 5,
        "character": "Reenu",
        "dialogue_malayalam": "സച്ചിൻ, പുറത്തിറങ്ങരുത്... ആരോ നമ്മുടെ കാറിനെ പിന്തുടരുന്നുണ്ട്!",
        "action_summary": "Reenu leans forward anxiously from the rear seat, clutching the front headrest in dread, warning Sachin not to leave the vehicle as dark shadows drift outside.",
        "location": "Mountain road car interior",
        "persistent_props": ["Rear seat headrest", "Reenu's silver wristwatch", "Foggy rear window"],
        "camera": "Expressive 3D close-up of Reenu leaning between front seats in dread"
    },
    {
        "shot_number": 6,
        "character": "Amal",
        "dialogue_malayalam": "വാതിലുകൾ പെട്ടെന്ന് ലോക്ക് ചെയ്യ്!",
        "action_summary": "Amal urgently snaps the driver-side door lock down and frantically gestures for Sachin and Reenu to secure all doors as fear grips the cabin.",
        "location": "Mountain road car interior",
        "persistent_props": ["Driver door lock switch", "Car steering wheel", "Rearview mirror"],
        "camera": "Dynamic 3D medium close-up of Amal snapping lock down"
    },
    {
        "shot_number": 7,
        "character": "Sachin",
        "dialogue_malayalam": "എന്തൊരു തണുപ്പാണ് ഈ കാറ്റിൽ...",
        "action_summary": "Sachin pulls his travel jacket tight against the freezing monsoon mountain gust blowing through the cracked window glass, breath misting in the cold air.",
        "location": "Mountain road car interior",
        "persistent_props": ["Cracked window glass", "Sachin's cross-bag", "Condensation on glass"],
        "camera": "Cinematic 3D close-up of Sachin shivering by passenger window"
    },
    {
        "shot_number": 8,
        "character": "Amal",
        "dialogue_malayalam": "എന്റെ അമ്മോ, ആ കണ്ണാടിയിൽ എന്തോ നിഴലിക്കുന്നു!",
        "action_summary": "Amal recoils in terror in the driver's seat, staring wide-eyed into the illuminated side rearview mirror where an eerie shadowy silhouette looms close.",
        "location": "Mountain road car interior",
        "persistent_props": ["Illuminated side rearview mirror", "Car steering wheel"],
        "camera": "Over-the-shoulder 3D shot past Amal looking into mirror reflection"
    },
    {
        "shot_number": 9,
        "character": "Sachin",
        "dialogue_malayalam": "ഡോർ ലോക്ക് ആയില്ലേ അമൽ, വേഗം വണ്ടി സ്റ്റാർട്ട് ചെയ്യ്!",
        "action_summary": "Sachin quickly pulls his legs back inside the passenger seat, slams the door shut, and urgently turns to Amal in the driver seat, yelling to start the engine.",
        "location": "Mountain road car interior",
        "persistent_props": ["Passenger door handle", "Car dashboard", "Car keys"],
        "camera": "Tense two-shot of Sachin turning frantically to Amal in driver seat"
    },
    {
        "shot_number": 10,
        "character": "Reenu",
        "dialogue_malayalam": "ആ കൈപ്പാട്... അത് ജനാലയിലാണ്!",
        "action_summary": "Reenu freezes in pure shock and horror in the rear seat, pointing trembling fingers at a freezing translucent handprint slowly appearing on the condensation of the outer window glass from the blackness outside.",
        "location": "Mountain road car interior",
        "persistent_props": ["Foggy window pane", "Translucent handprint on glass", "Reenu's silver wristwatch"],
        "camera": "Chilling 3D close-up of Reenu's terrified face with glowing handprint on glass"
    }
]

def main():
    print("=== STARTING FULL SYSTEM MASTER SYNCHRONIZATION ===")
    
    # 1. Synchronize local state files & 100-shot outline
    ep_data = synchronize_master_outline_and_episode(
        season_number=3,
        target_episode=2,
        raw_shots=EPISODE_2_RAW,
        gas_url=DEFAULT_GAS_URL
    )
    
    # 2. Push directly to Google Sheet Tab 1, Tab 2, and Tab 7
    payload = {
        "action": "update_next_episode_full",
        "episode_number": 2,
        "season_number": 3,
        "is_new_season": False,
        "season_title": "Season 3: The Munnar Trip (മൂന്നാർ യാത്ര)",
        "title_english": ep_data["title_english"],
        "title_malayalam": ep_data["title_malayalam"],
        "synopsis": ep_data["synopsis"],
        "cliffhanger": ep_data["cliffhanger"],
        "total_shots": 10,
        "shots": [
            {
                "shot_number": s["shot_number"],
                "duration": s["duration"],
                "character": s["character"],
                "dialogue_malayalam": s["dialogue_malayalam"],
                "action_summary": s["action_summary"],
                "json_prompt": s["json_prompt"]
            }
            for s in ep_data["shots"]
        ]
    }
    
    print("\nPushing synchronized Episode 2 to Google Apps Script...")
    try:
        res = requests.post(DEFAULT_GAS_URL, data=json.dumps(payload), headers={"Content-Type": "text/plain"}, timeout=45)
        print(f"Google Sheet update response: HTTP {res.status_code} - {res.text[:200]}")
    except Exception as e:
        print(f"Notice pushing to Google Sheet: {e}")

    # 3. Synchronize Tab 7 Season_Shot_Outline in Google Sheet
    outline_path = Path("season_3_shot_outline.json")
    if outline_path.exists():
        with open(outline_path, "r", encoding="utf-8") as f:
            outline_data = json.load(f)
        tab7_payload = {
            "action": "save_season_shot_outline",
            "season_number": 3,
            "season_title": "Season 3: The Munnar Trip (മൂന്നാർ യാത്ര)",
            "shots": outline_data.get("flattened_shots", [])
        }
        print("\nPushing complete 100-shot roadmap to Google Sheet Tab 7 [Season_Shot_Outline]...")
        try:
            res7 = requests.post(DEFAULT_GAS_URL, data=json.dumps(tab7_payload), headers={"Content-Type": "text/plain"}, timeout=60)
            print(f"Tab 7 update response: HTTP {res7.status_code} - {res7.text[:200]}")
        except Exception as e:
            print(f"Notice pushing Tab 7: {e}")

    # 4. Synchronize all portal.html files
    print("\nSynchronizing all workspace portal.html files...")
    import update_portals
    
    print("\n=== MASTER SYNCHRONIZATION COMPLETE ===")

if __name__ == "__main__":
    main()
