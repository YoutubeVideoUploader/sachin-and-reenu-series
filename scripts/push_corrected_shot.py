#!/usr/bin/env python3
import sys
import json
import requests
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

url = "https://script.google.com/macros/s/AKfycbyivkrK_jL1ejwNqUvHe8KVFNkSuJSwZbWSmuE1YATqL5jCneMlqlKbf0EH7mwpc4gybA/exec"

# Exact corrected prompt according to specification mistakes (100% keeping dialogue & action)
clean_prompt = {
  "style": "High-end Disney Pixar 3D animated cartoon movie, stylized 3D cartoon character render, cute expressive animated features, soft smooth 3D cartoon shaders, vertical 9:16 format, Octane 3D render 4k 60fps",
  "duration": "6s",
  "perspective": "Character Dialogue (Amal Speaking)",
  "characters_present": [
    {
      "name": "Amal",
      "visual_dna": "Amal: Stylized 3D Pixar-style cartoon animation character, 18-19 year old South Indian Malayali teenage boy. Clean-shaven youthful teenage face, cheerful energetic jawline, warm dusky South Indian skin tone with smooth cartoon shaders, lively witty dark-brown animated eyes, expressive comedic eyebrows (STRICTLY TEENAGER / YOUTHFUL TEEN GUY, ZERO BEARD, ZERO STUBBLE, ZERO MATURE WRINKLES). Messy stylish short curly dark teen cartoon hair with textured volume. Slender athletic teenage build (height 5'8\", youthful 1:6.5 proportions, relaxed teen posture, strictly non-chibi) (PROHIBIT CHILD/TODDLER/BABY/CHIBI ANATOMY, PROHIBIT REALISTIC HUMAN SKIN PORES, PROHIBIT UNCANNY REALISM, PROHIBIT OVERWEIGHT, PROHIBIT CHUBBY, PROHIBIT FAT BODY, PROHIBIT BULKY/HEAVY/STOCKY BUILD, PROHIBIT DOUBLE CHIN, ZERO BEARD, ZERO STUBBLE). STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Plain Terracotta Rust-Orange solid T-shirt, faded blue denim jeans, black slip-on sneakers. Absolutely zero costume variations."
    }
  ],
  "sequence_continuity": {
    "scene_id": "SCENE_MUNNAR_ROAD_NIGHT",
    "time_of_day": "Late Evening",
    "lighting_palette": "Eerie blue moonlight cutting through thick white mountain fog",
    "weather": "Heavy mountain fog",
    "spatial_blocking": {
      "Amal": "Sitting in the driver's seat gripping the steering wheel tightly"
    },
    "eyeline_direction": "Looking frantically into the rearview mirror",
    "persistent_props": [
      "Car steering wheel",
      "Rearview mirror"
    ],
    "camera_lens": "Cinematic prime lens, shallow depth of field"
  },
  "location": "Mountain road car interior",
  "camera": "Medium shot",
  "action": "Amal nervously grips the steering wheel, his eyes darting across the dark rearview mirrors. Amal's mouth moves in natural, expressive 3D lip-sync animation corresponding to his spoken Malayalam line. Other character lips remain closed.",
  "dialogue": {
    "speaker": "Amal",
    "voice_persona": "Amal: 18-19yo witty relatable Malayali teenage friend voice, energetic comedic youthful Malayalam tone (Gemini Voice 'Puck' / Edge-TTS 'ml-IN-MidhunNeural')",
    "language": "Malayalam",
    "script": "ഇത്രയും കോടമഞ്ഞിൽ ആരും നടന്നുപോവില്ല സച്ചിൻ.",
    "line": "ഇത്രയും കോടമഞ്ഞിൽ ആരും നടന്നുപോവില്ല സച്ചിൻ."
  },
  "audio_directive": "MALE CHARACTER DIALOGUE (AMAL). Character mouth animates in natural lip-sync with spoken Malayalam dialogue line. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voice audio and natural ambient foley sound effects only."
}

payload = {
    "action": "update_shot_prompt",
    "episode_number": 2,
    "shot_number": 2,
    "shot_data": {
        "duration": "6s",
        "character": "Amal",
        "dialogue_malayalam": "ഇത്രയും കോടമഞ്ഞിൽ ആരും നടന്നുപോവില്ല സച്ചിൻ.",
        "action_summary": "Amal nervously grips the steering wheel, his eyes darting across the dark rearview mirrors.",
        "json_prompt": clean_prompt
    }
}

print("Pushing corrected Shot 2 prompt to Google Sheet...")
res = requests.post(url, data=json.dumps(payload), headers={"Content-Type": "text/plain"}, timeout=45)
print(f"GAS Response: HTTP {res.status_code} - {res.text}")

# Also update story_state.json
st_path = Path("story_state.json")
if st_path.exists():
    with open(st_path, "r", encoding="utf-8") as f:
        st = json.load(f)
    cur_ep = st.get("current_episode", {})
    shots = cur_ep.get("shots", [])
    for s in shots:
        if s.get("shot_number") == 2:
            s["character"] = "Amal"
            s["dialogue_malayalam"] = "ഇത്രയും കോടമഞ്ഞിൽ ആരും നടന്നുപോവില്ല സച്ചിൻ."
            s["action_summary"] = "Amal nervously grips the steering wheel, his eyes darting across the dark rearview mirrors."
            s["json_prompt"] = clean_prompt
            break
    with open(st_path, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)
    print("✓ Updated story_state.json for Shot 2.")

print("Done!")
