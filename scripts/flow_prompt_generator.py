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

# CANONICAL CHARACTER DNA FOR GOOGLE FLOW VIDEO GENERATION
REENU_DNA = (
    "Reenu, an attractive 22yo South Indian Malayali girl with shoulder-length voluminous layered wavy dark-brown hair "
    "and soft curtain bangs, warm sparkling hazel-brown eyes, glowing honey complexion. "
    "Attire: classic pastel camouflage t-shirt in baby-blue and soft yellow patches with sky-blue denim skirt."
)

SACHIN_DNA = (
    "Sachin, a handsome 22yo South Indian Malayali young man with messy wavy textured dark hair styled with casual volume, "
    "warm dark-brown eyes, handsome clean jawline, charming boyish smile. "
    "Attire: terracotta rust-orange crewneck t-shirt with subtle chest pocket, dark-gray joggers, black digital watch."
)

AMAL_DNA = (
    "Amal, a witty 22yo South Indian Malayali friend with cropped soft curly black hair, "
    "subtle neat mustache, warm humorous brown eyes, and an energetic cheerful smile. "
    "Attire: sage olive-green crewneck t-shirt, blue denim jeans, black wristwatch."
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

def generate_flow_prompts(custom_outline=None, episode_num=None):
    # Load story state
    state = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)
            
    current_ep = episode_num or (state.get("total_episodes_produced", 0) + 1)
    
    # Prompt with Malayalam dialogue constraints and dynamic 4s/6s/8s durations
    prompt = f"""
You are the Lead Cinematographer, Screenwriter & Director for the 3D Disney/Pixar animated vertical Malayalam web series 'SACHIN & REENU (സച്ചിൻ & റീനു)'.
We are producing Episode {current_ep}.

SERIES CONTEXT:
Sachin (22, returned from UK) and Reenu (22, waiting in Kochi) are deeply in love. Amal is Sachin's witty, loyal best friend.
Setting: Kochi, Kerala (CIAL airport, monsoon highway, cozy car interior, rain-slicked roadside tea stall).

EPISODE PREMISE:
{custom_outline or f"Episode {current_ep}: Stepping out into the sudden Kochi monsoon, Sachin and Reenu share an umbrella and an intimate car ride, rekindling their unspoken chemistry while Amal playfully navigates the rain-swept streets."}

CRITICAL DURATION & LENGTH REQUIREMENTS:
1. TARGET TOTAL REEL DURATION: Exactly between 2.0 minutes and 2.5 minutes (120 seconds to 150 seconds).
2. DYNAMIC SHOT DURATION RULE:
   - '4s' (4 seconds): Establishing shot, silent emotional gaze, ambient background, OR very short dialogue (1 to 3 words, e.g. "സച്ചിൻ!", "എന്താടാ?").
   - '6s' (6 seconds): Medium dialogue sentence (4 to 8 words).
   - '8s' (8 seconds): Extended dialogue sentence, emotional speech, or two-line exchange (9 to 16 words).
3. NUMBER OF SHOTS: Generate 20 to 24 discrete sequential shots so the sum of durations strictly totals between 120s and 150s.

DIALOGUE REQUIREMENTS (VERY IMPORTANT):
- Every shot featuring character speech MUST include the FULL Malayalam dialogue in authentic Malayalam script (മലയാളം ലിപി).
- All visual, cinematic, lighting, and camera instructions must be in English.
- Inside the 'flow_prompt', clearly state the character speaking and quote the full Malayalam dialogue:
  Example:
  Character Sachin speaks in Malayalam: "റീനൂ, നിന്നെ കാണുമ്പോൾ ഈ മഴ പോലും എത്ര മനോഹരമായി തോന്നുന്നു..."
- If the shot is a silent reaction or visual beat, specify:
  "No spoken dialogue; character gazes with quiet affection."

REQUIREMENTS FOR EACH GOOGLE FLOW PROMPT:
1. Always start with: "Disney Pixar 3D animated film, vertical 9:16 video."
2. Character visual DNA consistency:
   - Reenu: {REENU_DNA}
   - Sachin: {SACHIN_DNA}
   - Amal: {AMAL_DNA}
3. Character kinetics and facial emotion (smiling shyly, widening eyes, natural mouth movement matching Malayalam speech).
4. Cinematic camera movement (slow tracking shot, gentle forward dolly, low-angle pan, over-the-shoulder push-in).
5. Atmospheric lighting: Kochi monsoon rain droplets, glistening asphalt reflections, warm golden amber vehicle interior dome light, creamy neon bokeh, 4k 60fps render.
6. Center composition: keep characters centered in the middle 55% of the 9:16 frame.

OUTPUT FORMAT:
Return ONLY valid JSON (no markdown fences, no code blocks):
{{
  "episode_number": {current_ep},
  "title_malayalam": "മലയാളം ശീർഷകം",
  "title_english": "English Title",
  "synopsis": "Comprehensive 2-sentence synopsis",
  "target_duration_seconds": 132,
  "total_shots": 22,
  "shots": [
    {{
      "shot_number": 1,
      "duration": "4s",
      "duration_seconds": 4,
      "character": "Reenu",
      "camera": "Slow tilt-down from airport canopy",
      "dialogue_malayalam": "",
      "action_summary": "Reenu pauses by the curb as rain starts drumming against the awning",
      "flow_prompt": "Disney Pixar 3D animated film, vertical 9:16 video. Outside CIAL airport terminal, sparkling monsoon rain begins drumming against sleek glass awnings. Reenu, an attractive 22yo South Indian Malayali girl with shoulder-length wavy dark-brown hair and soft curtain bangs, wearing a pastel cloud camouflage baby-blue and yellow t-shirt with sky-blue skirt, pauses at the curb, holding her hands out playfully to feel the cool raindrops. No spoken dialogue; pure ambient atmospheric beat. Slow cinematic tilt-down, centered framing in middle 55%, volumetric amber bokeh, cinematic rain physics, 4k 60fps render."
    }},
    {{
      "shot_number": 2,
      "duration": "6s",
      "duration_seconds": 6,
      "character": "Amal",
      "camera": "Dynamic low-angle tracking shot",
      "dialogue_malayalam": "ഡാ സച്ചിൻ, വേഗം വാടാ! മഴ കനക്കാൻ തുടങ്ങി!",
      "action_summary": "Amal pops open an umbrella and calls them urgently with a grin",
      "flow_prompt": "Disney Pixar 3D animated film, vertical 9:16 video. Amal, a witty 22yo South Indian Malayali friend with cropped soft curly black hair, neat mustache, wearing a sage olive-green crewneck t-shirt, pops open a wide black umbrella with a snap and turns backward, waving his arm. Character Amal speaks in Malayalam: \\\"ഡാ സച്ചിൻ, വേഗം വാടാ! മഴ കനക്കാൻ തുടങ്ങി!\\\" Dynamic low-angle tracking shot, centered subject framing, splashing puddle droplets in slow motion, golden airport exterior lighting, natural mouth animation, 4k 60fps render."
    }}
  ]
}}
"""

    # Generate content with model fallback and key rotation
    models_to_try = [
        "gemini-3.5-flash", 
        "gemini-3.7-flash", 
        "gemini-3.8-flash", 
        "gemini-flash-latest", 
        "gemini-3.5-flash-lite"
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
                print(f"Directing Episode {current_ep} Google Flow shots using {m} (key ...{ak[-6:]})...")
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
    
    # Calculate actual runtime
    total_sec = sum(int(s.get("duration", "4s").replace("s", "")) for s in ep_shots.get("shots", []))
    ep_shots["calculated_total_seconds"] = total_sec
    ep_shots["calculated_runtime_display"] = f"{int(total_sec // 60)}m {int(total_sec % 60):02d}s"
    ep_shots["total_shots"] = len(ep_shots.get("shots", []))

    with open(OUTPUT_SHOTS_FILE, "w", encoding="utf-8") as f:
        json.dump(ep_shots, f, ensure_ascii=False, indent=2)
        
    print(f"✓ Generated {ep_shots['total_shots']} shots totaling {ep_shots['calculated_runtime_display']} (~{total_sec}s)!")
    print(f"✓ All prompts formatted with Malayalam dialogues & dynamic 4s/6s/8s durations.")
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

