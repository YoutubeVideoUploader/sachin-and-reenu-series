#!/usr/bin/env python3
"""
story_and_prompt_engine.py - Autonomous Next Episode Screenplay & JSON Prompt Generator
Powered by Google Gemini 2.5 / 1.5 Flash.
1. Reads previous story memory & cliffhanger.
2. Writes an exciting, emotionally engaging Malayalam romance continuation for Sachin & Reenu.
3. Structures 20-24 shots totaling 2 to 2.5 minutes with dialogue-matched durations (4s / 6s / 8s).
4. Generates hyper-detailed Disney Pixar 3D JSON prompts with Character Visual DNA & No-BGM directives.
5. Updates Google Sheet Tabs:
   - Tab 1: Episode_Story (Story memory)
   - Tab 2: Current_JSON_Prompts (Overwritten with new episode prompts)
   - Tab 3: Video_Checklist (Reset to Pending for all new shots)
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import json
import time
import argparse
import requests
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from google import genai
from google.genai import types

# Character Visual DNA Constants
DNA_REENU = "Reenu: Attractive 22yo South Indian Malayali girl with shoulder-length voluminous layered wavy dark-brown hair and soft curtain bangs, warm sparkling hazel-brown doe eyes, glowing radiant honey complexion. Attire: Classic pastel camouflage t-shirt in baby-blue and soft yellow cloud patches with sky-blue denim skirt."
DNA_SACHIN = "Sachin: Endearing 24yo South Indian Malayali young man with soft textured wavy dark hair, warm expressive almond-shaped brown eyes, genuine contagious boyish smile, radiant dusky wheatish skin tone. Attire: Tailored forest-green and navy-blue check flannel shirt over crisp white inner crewneck tee with dark denim jeans and a leather travel cross-bag."
DNA_AMAL = "Amal: Cheerful 24yo Malayali young man with neat casual short hair, playful lively eyes, friendly smile, warm medium brown complexion. Attire: Mustard yellow polo t-shirt with beige chinos."

NARRATOR_VOICE = "Consistent Third-Person Male Narrator: 30yo mature male storyteller voice, warm reflective baritone, gentle evocative cadence, studio acoustic clarity"

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY_2") or os.getenv("GEMINI_API_KEY_3")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    return genai.Client(api_key=api_key)

def generate_next_episode_screenplay(current_ep_num, previous_story, cliffhanger, next_ep_premise=""):
    """
    Calls Gemini to generate a captivating next episode screenplay with detailed JSON prompts.
    """
    next_ep_num = current_ep_num + 1
    client = get_gemini_client()
    
    print(f"\n=======================================================")
    print(f"✨ GEMINI AUTONOMOUS SCREENPLAY WRITER: EPISODE {next_ep_num}")
    print(f"=======================================================")
    print(f"Previous Episode Summary: {previous_story[:100]}...")
    print(f"Cliffhanger: {cliffhanger}")

    system_instruction = (
        "You are an acclaimed Malayalam romantic film director and screenplay writer, known for heartwarming, "
        "relatable Kochi romance cinema (like 'Premalu', 'Bangalore Days', 'Hridayam'). "
        "You write compelling 2 to 2.5 minute vertical episodes (Reels format) for the animated 3D web series 'Sachin & Reenu'. "
        "Characters: Sachin (just returned from UK after 2 years), Reenu (deeply in love, nervous, overwhelmed), and Amal (Sachin's witty loyal best friend). "
        "Every episode must feel deeply emotional, charming, culturally authentic to Kerala/Kochi, and end on an irresistible cliffhanger. "
        "You will output ONLY valid JSON according to the specified schema."
    )

    prompt = f"""
Write the full screenplay and shot-by-shot Google Flow JSON prompts for Episode {next_ep_num} of 'Sachin & Reenu'.

CONTEXT FROM PREVIOUS EPISODE {current_ep_num}:
Story: {previous_story}
Cliffhanger: {cliffhanger}
Premise/Hook for Episode {next_ep_num}: {next_ep_premise or 'Stepping outside Kochi airport into the sudden monsoon rain. An intimate car ride with Amal driving, while Sachin hesitates to reveal his UK secret.'}

CRITICAL RULES:
1. TARGET DURATION: Between 120 and 150 seconds (2m 00s to 2m 30s).
2. NUMBER OF SHOTS: Exactly 20 to 24 shots.
3. DURATION LOGIC:
   - Short dialogue (< 10 words) or swift reaction: "4s" (4 seconds)
   - Medium dialogue (10-20 words) or meaningful conversation: "6s" (6 seconds)
   - Long dialogue (> 20 words) or intense emotional exchange: "8s" (8 seconds)
4. AUDIO DIRECTIVE:
   - Dialogue must be in pure, natural, conversational Malayalam written in Malayalam script (മലയാളം ലിപി).
   - If a shot has no dialogue between characters, use the Third-Person Narrator voice to give lively emotional narration.
   - For every shot, "audio_directive" MUST strictly state: "CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voice dialogue and natural ambient foley sound effects only."
5. CHARACTER VISUAL CONSISTENCY:
   - Reenu Visual DNA: "{DNA_REENU}"
   - Sachin Visual DNA: "{DNA_SACHIN}"
   - Amal Visual DNA: "{DNA_AMAL}"
6. STYLE:
   - "Disney Pixar 3D animated film, vertical 9:16 format, hyper-detailed 3D CGI animation, Octane render 4k 60fps"

Output JSON structure:
{{
  "episode_number": {next_ep_num},
  "title_malayalam": "...",
  "title_english": "...",
  "synopsis": "Full exciting synopsis of the episode...",
  "cliffhanger": "Next cliffhanger...",
  "total_shots": 22,
  "calculated_total_seconds": 126,
  "calculated_runtime_display": "2m 06s",
  "shots": [
    {{
      "shot_number": 1,
      "duration": "4s",
      "duration_seconds": 4,
      "character": "Third-Person Narrator",
      "dialogue_malayalam": "...",
      "action_summary": "...",
      "json_prompt": {{
        "style": "Disney Pixar 3D animated film, vertical 9:16 format, hyper-detailed 3D CGI animation, Octane render 4k 60fps",
        "duration": "4s",
        "perspective": "Third-Person Narrator",
        "characters_present": [
          {{
            "name": "Reenu",
            "visual_dna": "{DNA_REENU}"
          }}
        ],
        "location": "...",
        "camera": "...",
        "action": "...",
        "dialogue": {{
          "speaker": "Third-Person Narrator",
          "voice_persona": "{NARRATOR_VOICE}",
          "language": "Malayalam",
          "script": "മലയാളം ലിപി",
          "line": "..."
        }},
        "audio_directive": "CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voice dialogue and natural ambient foley sound effects only.",
        "negative_prompt": "background music, musical score, singing, low resolution, 2D illustration, deformed faces, distorted anatomy, cutoff framing"
      }}
    }}
  ]
}}
"""

    candidate_models = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]
    response = None
    last_err = None

    for model_name in candidate_models:
        print(f"Generating episode with {model_name}...")
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.8
                    )
                )
                if response and response.text:
                    break
            except Exception as e:
                last_err = e
                print(f"  Attempt {attempt + 1} with {model_name} failed: {e}")
                time.sleep(2)
        if response and response.text:
            break

    if not response or not response.text:
        raise RuntimeError(f"All Gemini models failed to generate screenplay. Last error: {last_err}")

    data = json.loads(response.text)
    
    # Calculate exact total runtime
    total_sec = sum(s.get("duration_seconds", 4) for s in data["shots"])
    data["calculated_total_seconds"] = total_sec
    data["calculated_runtime_display"] = f"{total_sec // 60}m {total_sec % 60:02d}s"
    data["total_shots"] = len(data["shots"])
    
    print(f"✓ Successfully generated Episode {next_ep_num}: '{data.get('title_malayalam')}' ({data.get('title_english')})")
    print(f"✓ Total Shots: {data['total_shots']} | Runtime: {data['calculated_runtime_display']}")
    return data

def sync_new_episode_to_google_sheet(gas_url, episode_data):
    """
    Calls Google Apps Script to:
    1. Update Tab 1 (Episode_Story) with the new episode outline.
    2. Overwrite Tab 2 (Current_JSON_Prompts) with the new JSON prompts.
    3. Reset Tab 3 (Video_Checklist) for Shot 1..N with 'Pending' status.
    """
    if not gas_url:
        print("Notice: GAS_WEBHOOK_URL not set. Skipping remote Google Sheet sync.")
        return False
        
    print(f"\nUpdating Google Sheet with Episode {episode_data['episode_number']} prompts & checklist...")
    
    payload = {
        "action": "update_next_episode_full",
        "episode_number": episode_data["episode_number"],
        "title_english": episode_data.get("title_english", ""),
        "title_malayalam": episode_data.get("title_malayalam", ""),
        "synopsis": episode_data.get("synopsis", ""),
        "cliffhanger": episode_data.get("cliffhanger", ""),
        "total_shots": episode_data["total_shots"],
        "shots": [
            {
                "shot_number": s["shot_number"],
                "duration": s["duration"],
                "character": s["character"],
                "dialogue_malayalam": s.get("dialogue_malayalam", ""),
                "action_summary": s.get("action_summary", ""),
                "json_prompt": s["json_prompt"]
            }
            for s in episode_data["shots"]
        ]
    }
    
    # 1. Try POST
    try:
        res = requests.post(gas_url, json=payload, timeout=30)
        if res.status_code == 200:
            print(f"✓ Google Sheet updated via POST: HTTP {res.status_code}")
            return True
        else:
            print(f"POST returned HTTP {res.status_code}, falling back to GET sync...")
    except Exception as e:
        print(f"Notice on POST sync: {e}, falling back to GET sync...")
        
    # 2. Resilient GET fallback (Calls Apps Script to sync from GitHub)
    try:
        sync_url = f"{gas_url}?action=sync_from_github&episode={episode_data['episode_number']}"
        res2 = requests.get(sync_url, timeout=30)
        print(f"✓ Google Sheet synced from GitHub via GET: HTTP {res2.status_code}")
        return res2.status_code == 200
    except Exception as e:
        print(f"Warning: Failed to update Google Sheet: {e}")
        return False

def update_creator_portal(episode_data):
    """
    Updates current_episode_shots.json and injects the new prompts into portal.html.
    """
    json_path = Path("current_episode_shots.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(episode_data, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved updated screenplay to {json_path.name}")

    # Re-run portal updater if available
    updater_script = Path("scripts/update_portals.py")
    if updater_script.exists():
        import subprocess
        subprocess.run([sys.executable, str(updater_script)], check=False)
        print("✓ Creator Portal website updated with new episode prompts!")

def main():
    parser = argparse.ArgumentParser(description="Generate Next Episode Screenplay & Prompts")
    parser.add_argument("--current_ep", type=int, default=1, help="Completed episode number")
    parser.add_argument("--gas_url", default=os.getenv("GAS_WEBHOOK_URL", ""), help="Google Apps Script Web App URL")
    args = parser.parse_args()

    # Load current episode context
    previous_story = "After two years apart, Sachin returns from London to Kochi CIAL and reunites emotionally with Reenu and Amal."
    cliffhanger = "Sachin holds Reenu close, but nervously clutches a secret pouch brought from London."
    
    if os.path.exists("current_episode_shots.json"):
        try:
            with open("current_episode_shots.json", "r", encoding="utf-8") as f:
                cur = json.load(f)
                previous_story = cur.get("synopsis", previous_story)
                cliffhanger = cur.get("cliffhanger", cliffhanger)
                args.current_ep = cur.get("episode_number", args.current_ep)
        except Exception:
            pass

    # 1. Generate Next Episode with Gemini
    ep_data = generate_next_episode_screenplay(
        current_ep_num=args.current_ep,
        previous_story=previous_story,
        cliffhanger=cliffhanger
    )

    # 2. Update local files & portal website
    update_creator_portal(ep_data)

    # 3. Sync to Google Sheet 3-Tab structure
    sync_new_episode_to_google_sheet(args.gas_url, ep_data)

if __name__ == "__main__":
    main()
