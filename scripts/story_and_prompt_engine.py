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
import re
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

# Stylized 3D Cartoon Animation Character Visual DNA Constants (Strictly Animated, Never Human-like, 100% LOCKED ATTIRE)
DNA_REENU = "Reenu: Stylized 3D Pixar-style cartoon animation character, 22yo South Indian Malayali girl, big expressive hazel-brown animated cartoon doe eyes with lush stylized eyelashes, soft rounded cute cartoon cheeks, sweet warm animated smile, voluminous bouncy wavy dark-brown cartoon hair with soft curtain bangs, stylized 3D character proportions with smooth vibrant cartoon shaders (STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Pastel baby-blue and soft yellow cloud-pattern camouflage t-shirt, sky-blue denim skirt, white sneakers, silver wrist watch. Absolutely zero costume variations."
DNA_SACHIN = "Sachin: Stylized 3D Pixar-style cartoon animation character, 24yo South Indian Malayali boy, endearing boyish cartoon features, large expressive warm animated brown eyes, playful genuine contagious cartoon smile, stylized soft textured wavy dark cartoon hair, cute slightly exaggerated 3D character proportions with smooth cartoon shaders (STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Forest-green and dark navy-blue check flannel button-down shirt worn open over a plain crisp white crewneck inner t-shirt, dark charcoal denim jeans, brown leather travel cross-bag worn diagonally across chest. Absolutely zero costume variations."
DNA_AMAL = "Amal: Stylized 3D Pixar-style cartoon animation character, 24yo South Indian Malayali boy, cheerful animated face, lively expressive cartoon eyes, broad energetic friendly cartoon smile, neat stylized short cartoon hairstyle, warm medium brown cartoon skin tone (STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Solid mustard-yellow polo t-shirt with brown buttons, slim-fit beige chinos. Absolutely zero costume variations."

NARRATOR_VOICE = "Consistent Third-Person Female Narrator: 22-24yo charming South Indian Malayali female storyteller voice, warm expressive sweet melodic tone, gentle youthful evocative Malayalam cadence, clear acoustic studio warmth"

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY_2") or os.getenv("GEMINI_API_KEY_3")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    return genai.Client(api_key=api_key)

def generate_next_episode_screenplay(current_ep_num, previous_story, cliffhanger, next_ep_premise=""):
    """
    Calls Gemini to generate a captivating 1-minute next episode screenplay (10-11 shots)
    with locked character dress, strict lip-movement rules, female narrator, and pure Malayalam dialogue.
    """
    next_ep_num = current_ep_num + 1
    client = get_gemini_client()
    
    print(f"\n=======================================================")
    print(f"✨ GEMINI AUTONOMOUS SCREENPLAY WRITER: EPISODE {next_ep_num} (1-MINUTE REEL)")
    print(f"=======================================================")
    print(f"Previous Episode Summary: {previous_story[:100]}...")
    print(f"Cliffhanger: {cliffhanger}")

    system_instruction = (
        "You are an acclaimed Malayalam romantic film director and 3D animated series showrunner. "
        "You write punchy, fast-paced, emotionally rich 1-MINUTE vertical episodes (Reels format) for the 3D animated cartoon series 'Sachin & Reenu'. "
        "Characters are strictly stylized 3D cartoon animation characters in high-end Disney Pixar / DreamWorks style. Real or human-like figures are strictly prohibited! "
        "LOCKED ATTIRE: Character clothing must be 100% consistent across every shot without exception. "
        "LIP SYNC & NARRATION RULES (CRITICAL): "
        "1. When the Third-Person Narrator is speaking (voice-over), NO CHARACTER'S MOUTH OR LIPS MUST MOVE. Characters' lips must be strictly closed with natural subtle emotional reactions. Characters must NOT speak the narrator's line! "
        "2. When characters converse, ONLY the speaking character's mouth moves in lip sync. The listening character's mouth remains closed. "
        "DIALOGUE STYLE: Use natural, standard, emotionally genuine conversational Malayalam (ശുദ്ധമായ സ്വാഭാവിക മലയാളം). Do NOT force slang. Focus on genuine romantic warmth, emotional vulnerability, and touching expressions. "
        "NARRATOR VOICE: The third-person narrator is a young, expressive female narrator with a melodic, charming Malayalam storytelling voice. "
        "AUDIO RESTRICTION: STRICTLY NO BACKGROUND MUSIC, NO INSTRUMENTAL BGM, NO MUSIC SCORE. Clean voice audio and natural ambient foley effects only. "
        "You will output ONLY valid JSON according to the specified schema."
    )

    prompt = f"""
Write the full screenplay and shot-by-shot Google Flow JSON prompts for Episode {next_ep_num} of 'Sachin & Reenu'.

CONTEXT FROM PREVIOUS EPISODE {current_ep_num}:
Story: {previous_story}
Cliffhanger: {cliffhanger}
Premise/Hook for Episode {next_ep_num}: {next_ep_premise or 'Reenu and Amal wait at Kochi CIAL airport arrival gates. An emotional reunion as Sachin arrives, but he clutches a secret London pouch.'}

CRITICAL PRODUCTION RULES:
1. TARGET DURATION: STRICTLY AROUND 1 MINUTE (55 to 65 seconds total).
2. NUMBER OF SHOTS: STRICTLY 10 TO 11 SHOTS (No more than 11 shots, no fewer than 10 shots).
3. DURATION LOGIC PER SHOT:
   - Fast reaction / cut: "5s" (5 seconds)
   - Dialogue exchange / scenic moment: "6s" (6 seconds)
   - Total sum of shot durations MUST be between 55s and 65s (~1 minute).
4. STRICT ANIMATION CHARACTER REQUIREMENT & LOCKED ATTIRE:
   - All characters MUST be stylized Disney-Pixar 3D animated cartoon models.
   - STRICTLY PROHIBIT photorealistic humans, realistic humans, live-action actors, real people, human skin pores, or uncanny valley realism.
   - Character visual DNA and locked clothing must be followed 100% identically:
     • Reenu Visual DNA: "{DNA_REENU}"
     • Sachin Visual DNA: "{DNA_SACHIN}"
     • Amal Visual DNA: "{DNA_AMAL}"
5. STRICT SPEAKING & LIP MOVEMENT RULES (MANDATORY):
   - NARRATION SHOTS: If the Third-Person Narrator is speaking, character lips MUST BE COMPLETELY CLOSED. In the 'action' and 'audio_directive', explicitly state: "Characters' lips remain completely closed. Absolutely NO mouth movement or speaking animation on characters. This is an external voiceover narration."
   - CONVERSATION SHOTS: Only the designated speaking character moves their mouth. The listening character's mouth remains closed.
6. EMOTIONAL INTENSITY & STANDARD MALAYALAM:
   - Dialogue must be in natural, heartfelt, conversational Malayalam written in Malayalam script (മലയാളം ലിപി). Do NOT include forced slang.
   - Emphasize authentic romantic and emotional expressions: trembling hands, shimmering eyes, radiant smiles, hesitant nervous glances.
7. ABSOLUTELY NO BACKGROUND MUSIC (BGM):
   - In every shot, "audio_directive" MUST strictly state: "CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voice dialogue and natural ambient foley sound effects only."
8. NEGATIVE PROMPT:
   - Must strictly include: "character mouth moving during voiceover, character lip sync during narration, open mouth talking during voiceover, real human, realistic human, real person, live-action actor, photorealistic human face, human skin pores, hyperrealistic, uncanny valley, real life photography, realistic skin texture, 2D illustration, deformed faces, distorted anatomy, background music, musical score, instrumental BGM, singing"
9. STYLE STRING:
   - "High-end Disney Pixar 3D animated cartoon movie, stylized 3D cartoon character render, cute expressive animated features, soft smooth 3D cartoon shaders, vertical 9:16 format, Octane 3D render 4k 60fps"

Output JSON structure:
{{
  "episode_number": {next_ep_num},
  "title_malayalam": "...",
  "title_english": "...",
  "synopsis": "Full exciting synopsis of the episode...",
  "cliffhanger": "Next cliffhanger...",
  "total_shots": 10,
  "calculated_total_seconds": 60,
  "calculated_runtime_display": "1m 00s",
  "shots": [
    {{
      "shot_number": 1,
      "duration": "6s",
      "duration_seconds": 6,
      "character": "Third-Person Narrator",
      "dialogue_malayalam": "...",
      "action_summary": "...",
      "json_prompt": {{
        "style": "High-end Disney Pixar 3D animated cartoon movie, stylized 3D cartoon character render, cute expressive animated features, soft smooth 3D cartoon shaders, vertical 9:16 format, Octane 3D render 4k 60fps",
        "duration": "6s",
        "perspective": "Third-Person Narrator",
        "characters_present": [
          {{
            "name": "Reenu",
            "visual_dna": "{DNA_REENU}"
          }}
        ],
        "location": "...",
        "camera": "...",
        "action": "Reenu looks around with trembling anticipation. Reenu's lips remain completely closed. Absolutely NO mouth movement or speaking animation on Reenu. This is an external voiceover narration.",
        "dialogue": {{
          "speaker": "Third-Person Narrator",
          "voice_persona": "{NARRATOR_VOICE}",
          "language": "Malayalam",
          "script": "മലയാളം ലിപി",
          "line": "..."
        }},
        "audio_directive": "EXTERNAL FEMALE VOICEOVER ONLY. The characters do NOT speak. Character lips remain completely closed with NO lip sync animation. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voiceover audio and natural ambient foley sound effects only.",
        "negative_prompt": "character mouth moving during voiceover, character lip sync during narration, open mouth talking during voiceover, real human, realistic human, real person, live-action actor, photorealistic human face, human skin pores, hyperrealistic, uncanny valley, real life photography, realistic skin texture, 2D illustration, deformed faces, distorted anatomy, background music, musical score, instrumental BGM, singing"
      }}
    }}
  ]
}}
"""

    candidate_models = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]
    parsed_data = None
    last_err = None

    def clean_json_text(raw_text):
        text = raw_text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        # Remove trailing commas
        text = re.sub(r',\s*([\]\}])', r'\1', text)
        return text

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
                        temperature=0.7
                    )
                )
                if response and response.text:
                    try:
                        clean_text = clean_json_text(response.text)
                        parsed_data = json.loads(clean_text)
                        if "shots" in parsed_data and len(parsed_data["shots"]) > 0:
                            break
                    except Exception as je:
                        print(f"  Attempt {attempt + 1} JSON parse error: {je}")
            except Exception as e:
                last_err = e
                print(f"  Attempt {attempt + 1} with {model_name} failed: {e}")
                time.sleep(3)
        if parsed_data:
            break

    if not parsed_data:
        raise RuntimeError(f"All Gemini models failed to generate valid screenplay JSON. Last error: {last_err}")

    data = parsed_data
    
    # Calculate exact total runtime
    total_sec = sum(s.get("duration_seconds", 6) for s in data["shots"])
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
    Updates current_episode_shots.json, story_state.json, and injects the new prompts into portal.html.
    """
    json_path = Path("current_episode_shots.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(episode_data, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved updated screenplay to {json_path.name}")

    # Update story_state.json history
    state_path = Path("story_state.json")
    if state_path.exists():
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
            ep_num = episode_data.get("episode_number", 1)
            state["total_episodes_produced"] = max(state.get("total_episodes_produced", 0), ep_num)
            history = state.get("history", [])
            existing_eps = [h.get("episode") for h in history]
            if ep_num not in existing_eps:
                chars = list(set([
                    s.get("character") for s in episode_data.get("shots", [])
                    if s.get("character") and s.get("character") != "Third-Person Narrator"
                ]))
                history.append({
                    "episode": ep_num,
                    "title": f"{episode_data.get('title_malayalam', '')} ({episode_data.get('title_english', '')})",
                    "summary": episode_data.get("synopsis", ""),
                    "cliffhanger": episode_data.get("cliffhanger", ""),
                    "characters_present": chars
                })
                state["history"] = history
            with open(state_path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            print("✓ Updated story_state.json with new episode progression!")
        except Exception as e:
            print(f"Notice updating story_state.json: {e}")

    # Re-run portal updater if available
    updater_script = Path("scripts/update_portals.py")
    if updater_script.exists():
        import subprocess
        subprocess.run([sys.executable, str(updater_script)], check=False)
        print("✓ Creator Portal website updated with new episode prompts!")

def main():
    parser = argparse.ArgumentParser(description="Generate Next Episode Screenplay & Prompts")
    parser.add_argument("--current_ep", type=int, default=1, help="Completed episode number")
    parser.add_argument("--target_ep", type=int, default=None, help="Explicit target episode number to generate")
    parser.add_argument("--gas_url", default=os.getenv("GAS_WEBHOOK_URL", ""), help="Google Apps Script Web App URL")
    args = parser.parse_args()

    # Robust default context
    previous_story = (
        "Episode 1: After two long years of waiting, Reenu and Amal wait at Kochi CIAL airport arrivals. "
        "Sachin emerges through the doors resulting in an emotional reunion, but Sachin secretly clutches an anxious London leather pouch."
    )
    cliffhanger = "As Sachin hugs Reenu, an anxious look crosses his face while holding the mysterious pouch."
    premise = ""
    effective_current_ep = args.current_ep

    # Check local current_episode_shots.json if present for context
    if os.path.exists("current_episode_shots.json"):
        try:
            with open("current_episode_shots.json", "r", encoding="utf-8") as f:
                cur = json.load(f)
                previous_story = cur.get("synopsis") or previous_story
                cliffhanger = cur.get("cliffhanger") or cliffhanger
                effective_current_ep = cur.get("episode_number", args.current_ep)
        except Exception as e:
            print(f"Notice reading current_episode_shots.json: {e}")

    if args.target_ep == 1:
        effective_current_ep = 0
        previous_story = "Series Pilot: Sachin has been away in the UK for two long years, while Reenu waited for him in Kerala. Today is Sachin's return flight arriving at Kochi CIAL airport."
        cliffhanger = "Reenu waits with trembling hands behind the arrival barrier, not having seen Sachin in person for 730 days."
        premise = "Episode 1 Pilot ('തിരിച്ചുവരവ്' / 'The Homecoming'): Reenu and Amal wait anxiously at Kochi CIAL international arrival terminal. Amal teases Reenu in playful Kochi slang to break her tension. Sachin finally emerges through the glass doors, resulting in an emotional, tender, tearful reunion. Cliffhanger: As they embrace, Sachin clutches a secret leather pouch from London with a nervous look."
    elif args.target_ep is not None:
        effective_current_ep = args.target_ep - 1
        premise = ""

    # 1. Generate Next Episode with Gemini
    ep_data = generate_next_episode_screenplay(
        current_ep_num=effective_current_ep,
        previous_story=previous_story,
        cliffhanger=cliffhanger,
        next_ep_premise=premise
    )

    # 2. Update local files & portal website
    update_creator_portal(ep_data)

    # 3. Sync to Google Sheet 3-Tab structure
    sync_new_episode_to_google_sheet(args.gas_url, ep_data)

if __name__ == "__main__":
    main()
