import os
import json
import time
from google import genai
from google.genai import types

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is required")

client = genai.Client(api_key=api_key)

STATE_FILE = "story_state.json"
OUTPUT_FILE = "current_episode.json"

def load_story_state():
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_next_episode():
    state = load_story_state()
    next_ep_num = state.get("total_episodes_produced", 1) + 1
    
    prompt = f"""
You are the Lead Showrunner and Screenwriter for the hit 3D animated romantic drama series: "SACHIN & REENU" (സച്ചിൻ & റീനു).
Language: Malayalam (മലയാളം).
Format: Instagram Reels 9:16 vertical video (~2 minutes duration, exactly 12-14 scenes).

SERIES BIBLE & CHARACTERS:
- Sachin (Age 26): Tousled thick wavy dark-brown hair, warm hazel eyes, clean-shaven, radiant charming smile.
  Costume: Rust-orange crew neck tee with subtle pineapple crest, black joggers, white sneakers, black sport watch.
  Voice: Fenrir. Back from UK after 6 long years.
- Reenu (Age 24): Shoulder-length layered chestnut-brown hair with side-swept fringe bangs and soft curled tips, large sparkling dark-brown doe eyes.
  Costume: Pastel yellow and light-blue cloud camouflage short-sleeved crop t-shirt, baby-blue denim mini-skirt with side slit, white sneakers.
  Voice: Kore. Bubbly, emotional, deeply in love, waited 6 years in Kochi.
- Amal (Age 26): Sachin's witty best friend. Cropped curly textured black hair, trim mustache and goatee beard.
  Costume: Olive-green crew neck tee with subtle horizontal graphic lines, blue denim jeans, white sneakers.
  Voice: Puck. Humorous Malayali friend banter.
- Narrator: Voice Kore. Poetic third-person storyteller explaining emotional depths.

PREVIOUS EPISODE HISTORY:
{json.dumps(state.get("history", []), ensure_ascii=False, indent=2)}

CURRENT STORY ARC: {state.get("current_arc")}

TASK FOR EPISODE {next_ep_num}:
Write the complete script for Episode {next_ep_num}.
Directly continue from the Episode 1 cliffhanger (Sachin and Reenu have just embraced at Cochin Airport; now they walk to the parking lot with Amal, but Sachin receives a mysterious UK phone call or Reenu notices a ring / letter in his bag, creating deep romantic tension and suspense!).

STRICT REQUIREMENTS:
1. Dialogues must be authentic, natural spoken colloquial Malayalam (സംഭാഷണ മലയാളം).
2. Third-person narration must be emotional and connect with the audience.
3. Every scene visual prompt must strictly adhere to the character anchors (Sachin in rust-orange tee, Reenu in cloud camo tee & skirt, Amal in olive tee). DO NOT CHANGE THEIR OUTFITS.
4. DO NOT include any written text or letters inside the visual prompts.
5. Exactly 12 to 14 scenes.

OUTPUT FORMAT: Return ONLY valid JSON matching this schema:
{{
  "episode_number": {next_ep_num},
  "title_malayalam": "...",
  "title_english": "...",
  "synopsis": "...",
  "cliffhanger": "...",
  "scenes": [
    {{
      "scene_index": 1,
      "setting_description": "...",
      "visual_prompt": "Pixar 3D animated style, 9:16 vertical Instagram format. [Detailed scene with character appearance & lighting, no text]...",
      "speaker": "Narrator" | "Reenu" | "Sachin" | "Amal",
      "voice": "Kore" | "Fenrir" | "Puck",
      "dialogue_malayalam": "..."
    }}
  ]
}}
"""

    models_to_try = [
        "gemini-3.5-flash",
        "gemini-3.7-flash",
        "gemini-flash-latest",
        "gemini-3.1-flash-lite",
        "gemini-3.8-flash"
    ]
    script_text = None
    
    for model_name in models_to_try:
        print(f"Calling Gemini ({model_name}) to script Episode {next_ep_num}...")
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
            print(f"  -> Note on {model_name}: {e}. Trying next model...")
            time.sleep(1.0)
            
    if not script_text:
        raise RuntimeError("Failed to generate screenplay after trying all active models.")
    
    # Clean json formatting if wrapped in codeblocks
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
