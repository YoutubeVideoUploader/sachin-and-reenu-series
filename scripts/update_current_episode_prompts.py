#!/usr/bin/env python3
import sys
import os
import json
import requests
import re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DEFAULT_GAS_URL = "https://script.google.com/macros/s/AKfycbyivkrK_jL1ejwNqUvHe8KVFNkSuJSwZbWSmuE1YATqL5jCneMlqlKbf0EH7mwpc4gybA/exec"

# 1. Fetch current data from Google Sheet
print("1. Fetching current episode data from Google Sheet...")
res = requests.get(f"{DEFAULT_GAS_URL}?action=get_all_data")
data = res.json()
if not data.get("success"):
    print("Failed to fetch data:", data)
    sys.exit(1)

ep_num = data.get("episode") or data.get("episode_number") or 2
title_en = data.get("title_english") or "The Woman in the Mist"
title_ml = data.get("title_malayalam") or "മഞ്ഞിലെ സ്ത്രീ"
synopsis = data.get("synopsis") or "Traveling through the heavy mountain fog, Sachin, Reenu, and Amal face an eerie presence when their car sputters to a halt."
cliffhanger = data.get("cliffhanger") or "A freezing handprint slowly presses against the outer window glass from the dark outside."
raw_shots = data.get("shots") or []

print(f"Loaded Episode {ep_num}: '{title_en}' with {len(raw_shots)} shots.")

# Canonical DNA Strings with Anti-Fat & Anti-Beard Protections
DNA_AMAL = (
    "Amal: Stylized 3D Pixar-style cartoon animation character, 18-19 year old South Indian Malayali teenage boy. "
    "Clean-shaven youthful teenage face, cheerful energetic jawline, warm dusky South Indian skin tone with smooth cartoon shaders, "
    "lively witty dark-brown animated eyes, expressive comedic eyebrows (STRICTLY TEENAGER / YOUTHFUL TEEN GUY, ZERO BEARD, ZERO STUBBLE, ZERO MATURE WRINKLES). "
    "Messy stylish short curly dark teen cartoon hair with textured volume. "
    "Slender athletic teenage build (height 5'8\", youthful 1:6.5 proportions, relaxed teen posture, strictly non-chibi) "
    "(PROHIBIT CHILD/TODDLER/BABY/CHIBI ANATOMY, PROHIBIT REALISTIC HUMAN SKIN PORES, PROHIBIT UNCANNY REALISM, PROHIBIT OVERWEIGHT, PROHIBIT CHUBBY, PROHIBIT FAT BODY, PROHIBIT BULKY/HEAVY/STOCKY BUILD, PROHIBIT DOUBLE CHIN, ZERO BEARD, ZERO STUBBLE). "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Plain Terracotta Rust-Orange solid T-shirt, faded blue denim jeans, black slip-on sneakers. Absolutely zero costume variations."
)

DNA_SACHIN = (
    "Sachin: Stylized 3D Pixar-style cartoon animation character, 18-19 year old South Indian Malayali teenage boy. "
    "Youthful boyish facial features, soft clean jawline, completely clean-shaven smooth caramel-tan South Indian skin with velvety cartoon subsurface scattering shaders "
    "(STRICTLY TEENAGER / YOUTHFUL TEEN GUY, ZERO FACIAL HAIR, ZERO STUBBLE, ZERO MATURE LINES). "
    "Big bright expressive warm dark-brown cartoon eyes filled with lively excitement, natural youthful eyebrows, playful contagious boyish grin showing clean straight white upper teeth. "
    "Messy voluminous wavy jet-black teen cartoon hair with casual bouncy textured locks falling slightly over his forehead. "
    "Lanky, slender athletic teenage build (height 5'9\", youthful 1:6.5 proportions, natural teen posture, strictly non-chibi) "
    "(PROHIBIT CHILD/TODDLER/BABY/CHIBI ANATOMY, PROHIBIT REALISTIC HUMAN SKIN PORES, PROHIBIT UNCANNY REALISM, PROHIBIT OVERWEIGHT, PROHIBIT CHUBBY, PROHIBIT FAT BODY, PROHIBIT BULKY/HEAVY/STOCKY BUILD, PROHIBIT DOUBLE CHIN). "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Plain Navy Blue solid crewneck T-shirt, charcoal-black denim jeans, brown leather travel cross-bag, clean white sneakers. Absolutely zero costume variations."
)

DNA_REENU = (
    "Reenu: Stylized 3D Pixar-style cartoon animation character, 18-19 year old South Indian Malayali teenage girl. "
    "Adorable Pixar teen heroine face, soft rounded cheeks with fresh natural peach-pink blush, smooth warm golden-fair skin with soft velvety cartoon shaders "
    "(STRICTLY TEENAGER / YOUTHFUL TEEN GIRL, NO MATURE AGING). "
    "Big sparkling expressive hazel-brown doe eyes with lush soft eyelashes, youthful naturally arched eyebrows, cute small button nose, radiant sweet bubbly teenage smile showing clean white teeth. "
    "Shoulder-length voluminous dark-brown wavy hair with bouncy youthful curls and soft curtain bangs framing her temples. "
    "Slender, petite teenage girl proportions (height 5'3\", youthful 1:6.2 proportions, lively teen posture, strictly non-chibi) "
    "(PROHIBIT CHILD/TODDLER/BABY/CHIBI ANATOMY, PROHIBIT REALISTIC HUMAN SKIN PORES, PROHIBIT UNCANNY REALISM, PROHIBIT OVERWEIGHT, PROHIBIT CHUBBY, PROHIBIT FAT BODY, PROHIBIT BULKY/STOCKY BUILD). "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Pastel Lavender T-shirt with white cloud and daisy floral prints, light-wash denim skirt, silver wristwatch, white sneakers. Absolutely zero costume variations."
)

DNA_MAP = {
    "Amal": DNA_AMAL,
    "Sachin": DNA_SACHIN,
    "Reenu": DNA_REENU
}

VOICE_MAP = {
    "Amal": "Amal: 18-19yo witty relatable Malayali teenage friend voice, energetic comedic youthful Malayalam tone (Gemini Voice 'Puck' / Edge-TTS 'ml-IN-MidhunNeural')",
    "Sachin": "Sachin: 18-19yo enthusiastic South Indian Malayali teenage boy voice, warm playful Kochi cadence, youthful eager tone (Gemini Voice 'Fenrir' / Edge-TTS 'ml-IN-MidhunNeural')",
    "Reenu": "Reenu: 18-19yo sweet expressive South Indian Malayali teenage girl voice, lively warm bubbly Malayalam tone (Gemini Voice 'Kore' / Edge-TTS 'ml-IN-SobhanaNeural')"
}

MASTER_STYLE = "High-end Disney Pixar 3D animated cartoon movie, stylized 3D cartoon character render, cute expressive animated features, soft smooth 3D cartoon shaders, vertical 9:16 format, Octane 3D render 4k 60fps"

# Corrected, film-continuous 10 shots
corrected_shots = []

for s in raw_shots:
    num = s.get("shot_number")
    speaker = s.get("character") or "Amal"
    ml_line = s.get("dialogue_malayalam") or ""
    act_summary = s.get("action_summary") or ""
    
    jp = s.get("json_prompt") or {}
    if isinstance(jp, str):
        try:
            jp = json.loads(jp)
        except Exception:
            jp = {}

    # 1. Perspective & Speaker Coupling
    perspective = f"Character Dialogue ({speaker} Speaking)"
    
    # 2. Characters Present: Include the speaker and relevant interacting character
    chars_present = []
    if speaker in DNA_MAP:
        chars_present.append({"name": speaker, "visual_dna": DNA_MAP[speaker]})
    
    # If other character is interacting, add them cleanly
    if speaker == "Sachin" and num == 1:
        chars_present.append({"name": "Reenu", "visual_dna": DNA_MAP["Reenu"]})
    elif speaker == "Reenu" and num == 5:
        chars_present.append({"name": "Sachin", "visual_dna": DNA_MAP["Sachin"]})
    elif speaker == "Amal" and num == 8:
        pass # solo
    
    # Ensure characters present never empty
    if not chars_present:
        chars_present.append({"name": speaker, "visual_dna": DNA_MAP.get(speaker, DNA_AMAL)})

    # 3. Universal Seating & Spatial Blocking:
    # AMAL = DRIVER SEAT (Right side)
    # SACHIN = FRONT PASSENGER SEAT (Left side)
    # REENU = REAR SEAT
    spatial_blocking = {
        "Amal": "Driver seat (right side), hands gripping the steering wheel, looking through misted windshield and rearview mirror",
        "Sachin": "Front passenger seat (left side), seated looking toward Amal and passenger window",
        "Reenu": "Rear seat directly behind front seats, leaning forward with anxious focus"
    }

    # Fine-tune per shot based on action
    if num == 1:
        # Sachin passenger
        spatial_blocking["Sachin"] = "Front passenger seat (left side), turning around sharply to glance at rear window"
        spatial_blocking["Reenu"] = "Rear seat pointing anxiously toward the mist outside"
        eyeline = "Sachin looks screen-right toward rear seat; Reenu points out rear window"
    elif num in [2, 3]:
        # Amal driving / ignition
        spatial_blocking["Amal"] = "Driver seat (right side), hands gripping steering wheel tightly, twisting ignition key"
        eyeline = "Amal looks straight ahead into foggy road and down at dashboard ignition"
    elif num in [4, 7]:
        # Sachin at passenger door
        spatial_blocking["Sachin"] = "Front passenger door pushed ajar, Sachin pausing in doorway against cold wind"
        eyeline = "Sachin looks outward into dense white fog, then glances back at Amal"
    elif num in [5]:
        # Reenu grabbing Sachin
        spatial_blocking["Reenu"] = "Rear seat leaning forward, gripping Sachin's arm in dread"
        spatial_blocking["Sachin"] = "Front passenger seat turned toward Reenu"
        eyeline = "Reenu looks desperately at Sachin; Sachin looks back at Reenu"
    elif num in [6, 8]:
        # Amal locking doors / wiping window
        spatial_blocking["Amal"] = "Driver seat (right side), leaning toward driver-side window glass"
        eyeline = "Amal stares intently through driver window into dark mist"
    elif num in [9]:
        # Sachin slamming passenger door
        spatial_blocking["Sachin"] = "Front passenger seat, quickly pulling legs in and slamming passenger door shut"
        eyeline = "Sachin looks frantically screen-right toward Amal in the driver seat"
    elif num == 10:
        # Reenu seeing handprint
        spatial_blocking["Reenu"] = "Rear seat frozen in horror, staring directly at outer window glass"
        eyeline = "Reenu stares in shock at side windowpane"

    persistent_props = ["Car steering wheel", "Rearview mirror", "Illuminated dashboard dials", "Car ignition key", "Sachin's cross-bag strap"]

    action_text = f"{act_summary} {speaker} actively speaks dialogue on screen with natural animated lip movement, expressive facial emotion, and speech sync. Other character lips remain closed."
    
    audio_directive = (
        f"CHARACTER DIALOGUE SPOKEN BY {speaker.upper()} ON SCREEN. "
        f"{speaker} speaks directly with clear character voice and synchronized animated lip movement. "
        f"CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. "
        f"Clean character voice dialogue and natural car interior ambient foley sound effects only."
    )

    clean_json_prompt = {
        "style": MASTER_STYLE,
        "duration": "6s",
        "perspective": perspective,
        "characters_present": chars_present,
        "sequence_continuity": {
            "scene_id": "SCENE_MUNNAR_MOUNTAIN_ROAD_CAR",
            "time_of_day": "Late Evening High-Range Monsoon Fog",
            "lighting_palette": "Eerie blue moonlight filtered through thick mountain fog with warm amber dashboard glow",
            "weather": "Heavy mountain fog with cool condensation on car windows",
            "spatial_blocking": spatial_blocking,
            "eyeline_direction": eyeline,
            "persistent_props": persistent_props,
            "camera_lens": "Cinematic prime lens, shallow depth of field, soft circular bokeh"
        },
        "location": "Mountain road car interior",
        "camera": f"Cinematic 3D medium close-up focused on {speaker}",
        "action": action_text,
        "dialogue": {
            "speaker": speaker,
            "voice_persona": VOICE_MAP.get(speaker, VOICE_MAP["Amal"]),
            "language": "Malayalam",
            "script": ml_line,
            "line": ml_line
        },
        "audio_directive": audio_directive
    }

    corrected_shots.append({
        "shot_number": num,
        "duration": "6s",
        "duration_seconds": 6,
        "character": speaker,
        "dialogue_malayalam": ml_line,
        "action_summary": act_summary,
        "json_prompt": clean_json_prompt
    })

print(f"2. Successfully compiled all {len(corrected_shots)} shots with Amal locked as Driver and pristine teenage DNA.")

# 3. Push to Google Sheet
payload = {
    "action": "update_next_episode_full",
    "episode_number": ep_num,
    "season_number": 3,
    "is_new_season": False,
    "season_title": "Season 3: The Munnar Trip (മൂന്നാർ യാത്ര)",
    "title_english": title_en,
    "title_malayalam": title_ml,
    "synopsis": synopsis,
    "cliffhanger": cliffhanger,
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
        for s in corrected_shots
    ]
}

print("3. Pushing corrected 10 shots to Google Sheet Tab 1 & Tab 2...")
post_res = requests.post(DEFAULT_GAS_URL, data=json.dumps(payload), headers={"Content-Type": "text/plain"}, timeout=45)
print(f"Google Sheet response: HTTP {post_res.status_code} - {post_res.text[:200]}")

# 4. Update story_state.json
state_path = Path("story_state.json")
if state_path.exists():
    with open(state_path, "r", encoding="utf-8") as f:
        st = json.load(f)
    st["episode_number"] = ep_num
    st["current_episode"] = {
        "episode_number": ep_num,
        "season_number": 3,
        "title_english": title_en,
        "title_malayalam": title_ml,
        "synopsis": synopsis,
        "cliffhanger": cliffhanger,
        "total_shots": 10,
        "shots": corrected_shots
    }
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)
    print("✓ Updated story_state.json with clean 10 shots.")

print("All shots updated successfully!")
