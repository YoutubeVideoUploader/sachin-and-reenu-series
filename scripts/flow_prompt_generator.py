import os
import sys
import json
import time
from google import genai

# Fix Windows console UTF-8 output
if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr:
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Load local environment if present
if os.path.exists(".env"):
    try:
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
    except Exception:
        pass

STATE_FILE = "story_state.json"
OUTPUT_SHOTS_FILE = "current_episode_shots.json"

# CANONICAL CHARACTER DNA FOR COMPLETE CONSISTENCY
REENU_DNA = (
    "Reenu: Attractive 22yo South Indian Malayali girl with shoulder-length voluminous layered wavy dark-brown hair "
    "and soft curtain bangs, warm sparkling hazel-brown doe eyes, glowing radiant honey complexion. "
    "Attire: Classic pastel camouflage t-shirt in baby-blue and soft yellow cloud patches with sky-blue denim skirt."
)

SACHIN_DNA = (
    "Sachin: Handsome 22yo South Indian Malayali young man with messy wavy textured dark-brown hair styled with casual volume, "
    "warm dark-brown expressive eyes, clean defined jawline, charming boyish smile. "
    "Attire: Terracotta rust-orange crewneck t-shirt with subtle chest pocket, relaxed dark-gray joggers, black digital sports watch."
)

AMAL_DNA = (
    "Amal: Witty 22yo South Indian Malayali friend with cropped soft curly black hair, "
    "neat trim mustache and subtle goatee beard, warm humorous brown eyes, and energetic cheerful smile. "
    "Attire: Sage olive-green crewneck t-shirt, blue denim jeans, black wristwatch."
)

def get_gemini_client():
    keys = []
    if os.getenv("GEMINI_API_KEYS"):
        keys.extend([k.strip() for k in os.getenv("GEMINI_API_KEYS").split(",") if k.strip()])
    for var in ["GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"]:
        k = os.getenv(var)
        if k and k.strip() and k.strip() not in keys:
            keys.append(k.strip())
            
    if not keys:
        raise ValueError("No GEMINI_API_KEY found in environment.")
    return genai.Client(api_key=keys[0])

def generate_flow_prompts(custom_outline=None, episode_num=3):
    state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
            
    current_ep = episode_num or (state.get("total_episodes_produced", 0) + 1)
    
    prompt = f"""
You are the Lead Cinematographer, Technical AI Director & Screenwriter for the 3D Disney/Pixar animated vertical Malayalam web series 'SACHIN & REENU (സച്ചിൻ & റീനു)'.
We are directing Episode {current_ep}.

SERIES CONTEXT:
Sachin (22, returned from UK) and Reenu (22, waiting in Kochi) are deeply in love. Amal is Sachin's witty, loyal best friend.
Setting: Kochi, Kerala (CIAL airport, monsoon highway, cozy car interior, rain-slicked roadside tea stall).

EPISODE PREMISE:
{custom_outline or f"Episode {current_ep}: Stepping out into the sudden Kochi monsoon, Sachin and Reenu share an umbrella and an intimate car ride, rekindling their unspoken chemistry while Amal playfully navigates the rain-swept streets."}

CRITICAL PRODUCTION CONSTRAINTS:
1. TOTAL RUNTIME: Between 2.0 minutes and 2.5 minutes (120 to 150 seconds).
2. DYNAMIC SHOT DURATION RULE:
   - '4s' (4 seconds): Establishing shot, silent emotional gaze, ambient background, OR very short dialogue (1 to 3 words).
   - '6s' (6 seconds): Medium dialogue sentence (4 to 8 words).
   - '8s' (8 seconds): Extended dialogue sentence, emotional speech, or two-line exchange (9 to 16 words).
3. NUMBER OF SHOTS: Generate 20 to 24 sequential shots totaling between 120s and 150s.

MANDATORY JSON PROMPT STRUCTURE FOR EVERY SHOT:
For every shot, you must produce a detailed JSON prompt object ('json_prompt') containing:
- 'style': "Disney Pixar 3D animated film, vertical 9:16 format, hyper-detailed 3D CGI animation, Octane render 4k 60fps."
- 'duration': "4s", "6s", or "8s"
- 'characters_present': Array of detailed character descriptions. If a shot contains Sachin and Reenu, you MUST include the FULL detailed description for BOTH characters so the AI maintains 100% visual consistency.
   - Reenu DNA: "{REENU_DNA}"
   - Sachin DNA: "{SACHIN_DNA}"
   - Amal DNA: "{AMAL_DNA}"
- 'location_details': Specific, vivid description of the environment (e.g., CIAL airport terminal curb with wet asphalt reflecting amber streetlamps, or inside the cozy sedan back seat with monsoon rain streaming down the glass).
- 'camera_direction': Camera angle, framing (centered in middle 55% of vertical 9:16 frame), and movement (slow dolly, tracking pan, intimate close-up).
- 'action_details': Exact physical motion and facial emotion.
- 'dialogue': 
   - 'speaker': Character name or "None"
   - 'language': "Malayalam"
   - 'line': Full spoken sentence in Malayalam script (മലയാളം ലിപി), or "" if silent.
- 'audio_directive': "STRICTLY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean Malayalam voice dialogue and natural ambient foley sound effects only (rain drizzle, car engine, cloth rustle)."
- 'negative_prompt': "background music, musical score, singing, low resolution, 2D illustration, deformed faces, distorted anatomy, cutoff framing, on-screen text, visible text, typography, fonts, writing, letters, words, alphabet, script, typography overlay, Disney text, Pixar text, Disney Pixar text, Disney logo, Pixar logo, Walt Disney logo, studio watermark, brand name, brand logo, character names on screen, Sachin text, Reenu text, Amal text, character name labels, name tags, name badges, floating names, timestamps, time text, clock numbers, timecode display, 6:30 PM, 4:45 PM, 5s, 6s, 4s, 8s, duration numbers, countdown timer, digital clock overlay, 4K text, 60fps text, Octane Render text, 9:16 text, aspect ratio labels, camera metadata text, resolution stamps, specification text, subtitles, closed captions, captions, lower thirds, title cards, watermarks, credits, copyright notices, UI text, user interface elements, graphic banners"

Also provide a compiled text 'flow_prompt' that combines all of these into a single copy-pasteable prompt string for Google Flow, explicitly including the NO-MUSIC directive and full Malayalam dialogue.

OUTPUT FORMAT:
Return ONLY valid JSON (no markdown fences, no code blocks):
{{
  "episode_number": {current_ep},
  "title_malayalam": "മലയാളം ശീർഷകം",
  "title_english": "English Title",
  "synopsis": "Comprehensive 2-sentence synopsis",
  "total_shots": 22,
  "shots": [
    {{
      "shot_number": 1,
      "duration": "4s",
      "duration_seconds": 4,
      "character": "Reenu",
      "dialogue_malayalam": "",
      "action_summary": "Reenu pauses by the curb feeling the raindrops",
      "json_prompt": {{
        "style": "Disney Pixar 3D animated film, vertical 9:16 format, hyper-detailed 3D CGI animation, Octane render 4k 60fps",
        "duration": "4s",
        "characters_present": [
          {{
            "name": "Reenu",
            "description": "{REENU_DNA}"
          }}
        ],
        "location_details": "Outside CIAL airport arrival terminal canopy, glistening wet asphalt reflecting golden amber streetlights, monsoon rain drizzling onto glass awnings.",
        "camera_direction": "Slow cinematic tilt-down, centered framing in middle 55% of vertical 9:16 frame.",
        "action_details": "Reenu pauses at the curb, raising her hand gently with a playful curious smile to catch falling raindrops.",
        "dialogue": {{
          "speaker": "None",
          "language": "Malayalam",
          "line": ""
        }},
        "audio_directive": "STRICTLY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. Clean ambient rain foley only.",
        "negative_prompt": "background music, musical score, low resolution, wide aspect ratio, on-screen text, visible text, typography, fonts, writing, letters, words, Disney logo, Pixar logo, Disney text, brand names, character names on screen, Sachin text, Reenu text, Amal text, timestamps, time text, clock numbers, 4K text, 60fps text, Octane Render text, subtitles, captions, lower thirds, title cards, watermarks, credits, UI text"
      }},
      "flow_prompt": "Disney Pixar 3D animated film, vertical 9:16 video. Outside CIAL airport terminal, sparkling monsoon rain begins drumming against sleek glass awnings. Reenu: Attractive 22yo South Indian Malayali girl with shoulder-length voluminous layered wavy dark-brown hair and soft curtain bangs, warm sparkling hazel-brown doe eyes, wearing classic pastel camouflage baby-blue and yellow t-shirt with sky-blue skirt, pauses at the curb, holding her hands out playfully. No spoken dialogue. AUDIO DIRECTIVE: STRICTLY NO BACKGROUND MUSIC, clean ambient rain foley only. Slow cinematic tilt-down, centered framing in middle 55%, volumetric amber bokeh, 4k 60fps render."
    }}
  ]
}}
"""

    models_to_try = [
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-flash-latest"
    ]


    keys = []
    if os.getenv("GEMINI_API_KEYS"):
        keys.extend([k.strip() for k in os.getenv("GEMINI_API_KEYS").split(",") if k.strip()])
    for var in ["GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"]:
        k = os.getenv(var)
        if k and k.strip() and k.strip() not in keys:
            keys.append(k.strip())

    text = None
    last_err = None
    for m in models_to_try:
        for ak in keys:
            try:
                print(f"Directing Episode {current_ep} detailed JSON prompts using {m} (key ...{ak[-6:]})...")
                c = genai.Client(api_key=ak)
                res = c.models.generate_content(
                    model=m,
                    contents=prompt
                )
                if res and res.text:
                    text = res.text.strip()
                    break
            except Exception as e:
                last_err = e
                print(f"Notice: {m} attempt encountered {e}. Retrying with next candidate...")
                time.sleep(1.0)
        if text:
            break

    if not text:
        raise RuntimeError(f"All Gemini model and key attempts failed. Last error: {last_err}")

    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        
    ep_shots = json.loads(text)
    
    total_sec = sum(int(s.get("duration", "4s").replace("s", "")) for s in ep_shots.get("shots", []))
    ep_shots["calculated_total_seconds"] = total_sec
    ep_shots["calculated_runtime_display"] = f"{int(total_sec // 60)}m {int(total_sec % 60):02d}s"
    ep_shots["total_shots"] = len(ep_shots.get("shots", []))

    with open(OUTPUT_SHOTS_FILE, "w", encoding="utf-8") as f:
        json.dump(ep_shots, f, ensure_ascii=False, indent=2)
        
    print(f"✓ Generated {ep_shots['total_shots']} shots totaling {ep_shots['calculated_runtime_display']} (~{total_sec}s)!")
    print(f"✓ Formatted with detailed JSON prompt structure, character DNAs, location, camera, Malayalam dialogues & NO-BGM directive.")
    print(f"Saved to: {OUTPUT_SHOTS_FILE}")
    return ep_shots

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Google Flow Shot & Dialogue Prompt Generator")
    parser.add_argument("--episode", type=int, default=3, help="Episode number to generate")
    parser.add_argument("--outline", type=str, default=None, help="Custom episode story outline")
    args = parser.parse_args()

    generate_flow_prompts(custom_outline=args.outline, episode_num=args.episode)

if __name__ == "__main__":
    main()
