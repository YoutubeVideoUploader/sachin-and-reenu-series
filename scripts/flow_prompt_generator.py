import os
import json
import time
from google import genai

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

STYLE_DIRECTIVE = (
    "Disney Pixar 3D animated cinematic movie still in vertical 9:16 format. "
    "Hyper-detailed 3D CGI animation, subsurface skin scattering, realistic hair physics, "
    "volumetric atmospheric lighting, Octane render 4k 60fps, authentic Disney Pixar character design, "
    "centered vertical framing with subjects in the middle 55% of the frame."
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
    history = state.get("history", [])
    
    # Context prompt
    prompt = f"""
You are the Lead Cinematographer & Director for the 3D Disney/Pixar animated vertical web series 'SACHIN & REENU (സച്ചിൻ & റീനു)'.
We are producing Episode {current_ep}.

SERIES CONTEXT:
Sachin (22, returned from UK) and Reenu (22, waiting in Kochi) are deeply in love. Amal is Sachin's witty, loyal best friend.
Setting: Kochi, Kerala (CIAL airport, monsoon streets, cozy cafes).

EPISODE PREMISE:
{custom_outline or f"Episode {current_ep}: Continuing the emotional romantic journey of Sachin and Reenu after their reunion."}

TASK:
Break down this episode into 10 to 12 discrete, cinematic video shots of either 4 seconds ('4s') or 6 seconds ('6s') duration.
Total episode video duration should be between 45 seconds and 60 seconds (perfect for vertical Instagram Reels).

For each shot, formulate an exact, production-ready video generation prompt specifically engineered for 'Google Flow' (Veo / VideoFX AI video generator).

REQUIREMENTS FOR EACH GOOGLE FLOW PROMPT:
1. Always start with: "Disney Pixar 3D animated film, vertical 9:16 video."
2. Clearly describe character appearance using these canonical visual DNAs:
   - Reenu: {REENU_DNA}
   - Sachin: {SACHIN_DNA}
   - Amal: {AMAL_DNA}
3. Describe specific, natural physical motion (e.g., "Reenu looks up with widening eyes, smiling radiantly as the camera slowly dollies forward", "Sachin steps forward rolling his suitcase, raising one hand in excitement").
4. Specify camera movement (slow tracking shot, gentle orbit, close-up tilt, handheld dynamic movement).
5. Specify lighting and atmosphere (volumetric morning sunbeams, golden amber reflections, Kochi monsoon rain drizzle outside glass windows, 4k 60fps render).
6. Keep framing centered: subjects in the middle 55% of the vertical frame.

OUTPUT FORMAT:
Return ONLY valid JSON (no markdown formatting, no code blocks):
{{
  "episode_number": {current_ep},
  "title_malayalam": "മലയാളം ശീർഷകം",
  "title_english": "English Title",
  "synopsis": "Brief 2-sentence episode summary",
  "total_shots": 10,
  "shots": [
    {{
      "shot_number": 1,
      "duration": "4s",
      "character": "Reenu",
      "camera": "Slow dolly forward",
      "action_summary": "Reenu nervously waiting by the barrier looking across the crowd",
      "flow_prompt": "Disney Pixar 3D animated film, vertical 9:16 video. Reenu, 22yo attractive South Indian girl with wavy brown hair and curtain bangs, wearing pastel cloud camouflage t-shirt, standing on tiptoes looking eagerly across the arrival hall. Slow cinematic dolly forward, warm volumetric sunlight, 4k 60fps render."
    }}
  ]
}}
"""

    client = get_gemini_client()
    print(f"Directing Google Flow shots for Episode {current_ep} with Gemini 3.8 Flash...")
    res = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt
    )
    
    text = res.text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        
    ep_shots = json.loads(text)
    with open(OUTPUT_SHOTS_FILE, "w", encoding="utf-8") as f:
        json.dump(ep_shots, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully generated {len(ep_shots.get('shots', []))} Google Flow prompts for Episode {current_ep}!")
    print(f"Saved to: {OUTPUT_SHOTS_FILE}")
    return ep_shots

if __name__ == "__main__":
    generate_flow_prompts()
