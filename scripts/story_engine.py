import os
import json
import time
from google import genai
from google.genai import types

def get_api_clients():
    keys = []
    for var in ["GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"]:
        k = os.getenv(var)
        if k and k.strip() and k.strip() not in keys:
            keys.append(k.strip())
    if not keys:
        raise ValueError("At least one GEMINI_API_KEY environment variable is required")
    return [genai.Client(api_key=k) for k in keys]

STATE_FILE = "story_state.json"
OUTPUT_FILE = "current_episode.json"

def load_story_state():
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_next_episode():
    state = load_story_state()
    next_ep_num = state.get("total_episodes_produced", 0) + 1

    history = state.get("history", [])
    if history:
        last_ep = history[-1]
        last_cliffhanger = last_ep.get("cliffhanger", "The emotional reunion begins to unfold.")
        last_title = last_ep.get("title", f"Episode {next_ep_num - 1}")
    else:
        last_cliffhanger = "Sachin is returning from the UK after 6 long years. Reenu and Amal are waiting at Kochi CIAL airport international arrivals."
        last_title = "Series Premiere"

    prompt = f"""
You are the Lead Showrunner and Screenwriter for the hit 3D animated romantic drama series: "SACHIN & REENU" (സച്ചിൻ & റീനു).
Language: Malayalam (മലയാളം).
Format: Instagram Reels 9:16 vertical video (~2 minutes duration, exactly 12-14 scenes).

SERIES BIBLE & CHARACTERS:
- Sachin (Age 22): Tousled thick wavy textured dark hair, warm hazel eyes, handsome defined jawline, boyish charming smile.
  Costume: Terracotta rust-orange oversized cotton crewneck t-shirt with subtle pocket design, relaxed dark-gray joggers, white sneakers, black sports watch.
  Voice: Fenrir. Returning from UK after years away.
- Reenu (Age 22): Shoulder-length voluminous layered wavy dark brown hair with soft curtain bangs, large sparkling hazel-brown doe eyes, radiant warm smile.
  Costume: Fitted pastel camouflage t-shirt in baby blue, soft yellow, and white patches, paired with a light blue denim A-line mini skirt, white sneakers.
  Voice: Kore. Bubbly, emotional, deeply in love, waited faithfully in Kochi.
- Amal (Age 22): Sachin's loyal witty best friend. Cropped curly textured black hair, neat mustache and trim goatee beard.
  Costume: Olive-green crew neck tee, blue denim jeans, white sneakers.
  Voice: Puck. Humorous Malayali banter.
- Narrator: Voice Kore. Poetic third-person storyteller explaining emotional depths.

PREVIOUS EPISODE HISTORY:
{json.dumps(history, ensure_ascii=False, indent=2)}

CURRENT STORY ARC: {state.get("current_arc", "The Airport Reunion")}

TASK FOR EPISODE {next_ep_num}:
Write the complete screenplay for Episode {next_ep_num}.
{"Directly continue from: " + last_cliffhanger if history else "Episode 1: The Airport Reunion at Kochi CIAL. Sachin arrives with his trolley; Reenu and Amal spot him."}

STRICT VISUAL, CHARACTER & LOCATION CONSISTENCY RULES:
1. UNIFIED LOCATION & ATMOSPHERE: The entire episode must maintain strict environment consistency (e.g. Cochin Airport CIAL Terminal Arrivals, morning golden sunbeams streaming through massive glass walls).
2. CHARACTER CONTINUITY: Every scene must specify `characters_present` as a JSON array containing ["Reenu"], ["Sachin"], ["Sachin", "Reenu"], or ["Amal"].
3. EMOTION & ACTION: Specify `character_emotion` (e.g. "joyful teary smile", "playful surprise", "affectionate gaze") and `action_description` (e.g. "waving enthusiastically", "pulling luggage trolley").
4. COLLOQUIAL SPOKEN MALAYALAM: Dialogues must be authentic, natural spoken Kerala colloquial Malayalam (സംഭാഷണ മലയാളം).
5. Exactly 12 to 14 scenes.
6. NO WRITTEN TEXT inside the visual prompts.

OUTPUT FORMAT: Return ONLY valid JSON matching this schema:
{{
  "episode_number": {next_ep_num},
  "title_malayalam": "...",
  "title_english": "...",
  "synopsis": "...",
  "cliffhanger": "...",
  "primary_location": "Kochi CIAL Airport Arrivals Terminal",
  "location_palette": "Modern glass architecture, golden morning sunbeams streaming through high windows, blue sky outside, volumetric cinematic lighting",
  "scenes": [
    {{
      "scene_index": 1,
      "characters_present": ["Reenu"],
      "character_emotion": "anxious hopeful smile, eyes scanning the crowd",
      "action_description": "standing on tiptoes looking eagerly toward the glass arrival gates",
      "speaker": "Reenu",
      "voice": "Kore",
      "dialogue_malayalam": "..."
    }}
  ]
}}
"""

    models_to_try = [
        "gemini-3.8-flash",
        "gemini-3.5-flash",
        "gemini-flash-latest"
    ]
    script_text = None
    clients = get_api_clients()
    
    for client_idx, client in enumerate(clients):
        for model_name in models_to_try:
            print(f"Calling Gemini ({model_name}) with client key #{client_idx+1} to script Episode {next_ep_num}...")
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                script_text = response.text.strip()
                print(f"  -> Successfully generated screenplay using {model_name}!")
                break
            except Exception as e:
                print(f"  -> Note on {model_name} (key #{client_idx+1}): {e}. Trying next...")
                time.sleep(2.0)
        if script_text:
            break
            
    if not script_text:
        raise RuntimeError("Failed to generate screenplay after trying all active models.")
    
    if script_text.startswith("```json"):
        script_text = script_text[7:]
    if script_text.endswith("```"):
        script_text = script_text[:-3]
    
    episode_data = json.loads(script_text)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(episode_data, f, ensure_ascii=False, indent=2)
    
    title_en = episode_data.get('title_english', 'Untitled')
    print(f"Successfully saved Episode {next_ep_num}: {title_en}")
    print(f"Total scenes generated: {len(episode_data.get('scenes', []))}")

if __name__ == "__main__":
    generate_next_episode()
