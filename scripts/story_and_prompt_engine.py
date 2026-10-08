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
try:
    from json_repair import repair_json
except ImportError:
    repair_json = None

# Stylized 3D Cartoon Animation Character Visual DNA Constants (Strictly Animated, Never Human-like, 100% LOCKED ATTIRE)
DNA_REENU = "Reenu: Stylized 3D Pixar-style cartoon animation character, 22yo South Indian Malayali girl, big expressive hazel-brown animated cartoon doe eyes with lush stylized eyelashes, soft rounded cute cartoon cheeks, sweet warm animated smile, voluminous bouncy wavy dark-brown cartoon hair with soft curtain bangs, stylized 3D character proportions with smooth vibrant cartoon shaders (STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Pastel baby-blue and soft yellow cloud-pattern camouflage t-shirt, sky-blue denim skirt, white sneakers, silver wrist watch. Absolutely zero costume variations."
DNA_SACHIN = "Sachin: Stylized 3D Pixar-style cartoon animation character, 24yo South Indian Malayali boy, endearing boyish cartoon features, large expressive warm animated brown eyes, playful genuine contagious cartoon smile, stylized soft textured wavy dark cartoon hair, cute slightly exaggerated 3D character proportions with smooth cartoon shaders (STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Forest-green and dark navy-blue check flannel button-down shirt worn open over a plain crisp white crewneck inner t-shirt, dark charcoal denim jeans, brown leather travel cross-bag worn diagonally across chest. Absolutely zero costume variations."
DNA_AMAL = "Amal: Stylized 3D Pixar-style cartoon animation character, 24yo South Indian Malayali boy, cheerful animated face, lively expressive cartoon eyes, broad energetic friendly cartoon smile, neat stylized short cartoon hairstyle, warm medium brown cartoon skin tone (STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Solid mustard-yellow polo t-shirt with brown buttons, slim-fit beige chinos. Absolutely zero costume variations."

NARRATOR_VOICE = "Consistent Third-Person Female Narrator: 22-24yo charming South Indian Malayalam female storyteller voice, warm expressive sweet melodic tone, gentle youthful evocative Malayalam cadence, clear acoustic studio warmth"

MASTER_STYLE = "High-end Disney Pixar 3D animated cartoon movie, stylized 3D cartoon character render, cute expressive animated features, soft smooth 3D cartoon shaders, vertical 9:16 format, Octane 3D render 4k 60fps"

MASTER_NEGATIVE_PROMPT = (
    "character mouth moving during voiceover, character lip sync during narration, "
    "open mouth talking during voiceover, character talking during narration, "
    "character speaking narrator words, speaking animation on character, character mouth moving, "
    "real human, realistic human, real person, live-action actor, photorealistic human face, "
    "human skin pores, hyperrealistic, uncanny valley, real life photography, realistic skin texture, "
    "2D illustration, deformed faces, distorted anatomy, background music, musical score, instrumental BGM, singing, "
    "on-screen text, visible text, typography, fonts, writing, letters, words, alphabet, script, typography overlay, "
    "Disney text, Pixar text, Disney Pixar text, Disney logo, Pixar logo, Walt Disney logo, studio watermark, brand name, brand logo, "
    "character names on screen, Sachin text, Reenu text, Amal text, character name labels, name tags, name badges, floating names, "
    "timestamps, time text, clock numbers, timecode display, 6:30 PM, 4:45 PM, 5s, 6s, duration numbers, countdown timer, digital clock overlay, "
    "4K text, 60fps text, Octane Render text, 9:16 text, aspect ratio labels, camera metadata text, resolution stamps, specification text, "
    "subtitles, closed captions, captions, lower thirds, title cards, watermarks, credits, copyright notices, UI text, user interface elements, graphic banners"
)

DNA_REGISTRY = {
    "Reenu": DNA_REENU,
    "Sachin": DNA_SACHIN,
    "Amal": DNA_AMAL
}

# Master Season 1 Story Roadmap (10 Episodes)
SEASON_1_ROADMAP = {
    1: {
        "title_english": "The Homecoming",
        "title_malayalam": "തിരിച്ചുവരവ്",
        "synopsis": "After two long years of waiting, Reenu stands anxiously with her friend Amal at Kochi CIAL arrival terminal. Sachin emerges through the sliding glass doors, leading to an emotional, tearful reunion. However, Sachin nervously clutches a secret leather pouch from London.",
        "cliffhanger": "As Sachin holds Reenu close, his eyes reveal a hidden anxiety while his fingers tightly clutch a secret, unopened leather pouch."
    },
    2: {
        "title_english": "Rain and Some Secrets",
        "title_malayalam": "മഴയും ചില രഹസ്യങ്ങളും",
        "synopsis": "Stepping outside Kochi CIAL airport into a sudden heavy monsoon shower, Sachin, Reenu, and Amal rush through the rain with their luggage to Amal's car. As they drive through the rain-drenched Kochi streets with wipers swishing, Reenu notices Sachin's nervous protectiveness over his London leather pouch. Sachin tries to speak, but a sudden braking causes the pouch to slip and slide deep under the car seat!",
        "cliffhanger": "The mysterious London leather pouch slips from Sachin's hand and slides deep under the front passenger seat. As Sachin frantically reaches down trying to hide it, Reenu looks at him with growing suspicion, asking what he is hiding."
    },
    3: {
        "title_english": "A Roadside Chai & Unspoken Glances",
        "title_malayalam": "ഒരു തട്ടുകട ചായയും നോട്ടങ്ങളും",
        "synopsis": "Amal stops the car at a misty tea stall by the backwaters. Under a shared umbrella, Sachin and Reenu share an intimate moment over hot tea, but Sachin hesitates to speak.",
        "cliffhanger": "Amal spots the London leather pouch lying on the car floor and picks it up curiously."
    },
    4: {
        "title_english": "Forgotten Memories",
        "title_malayalam": "മറന്നുപോയ ഓർമ്മകൾ",
        "synopsis": "Continuing their ride into Kochi city, Sachin and Reenu reminisce about their college days, but Sachin feels guilty about being away in the UK for 730 days.",
        "cliffhanger": "Reenu asks Sachin directly: 'Why didn't you tell me the real reason you booked your flight so suddenly?'"
    },
    5: {
        "title_english": "The Secret Slips",
        "title_malayalam": "രഹസ്യം പുറത്തേക്ക്",
        "synopsis": "Amal hands the pouch back to Sachin, asking what is inside. Sachin stammers and tries to divert the topic, raising Reenu's suspicion.",
        "cliffhanger": "Reenu reaches for the pouch playfully, but Sachin instinctively pulls it back, creating an awkward silence."
    },
    6: {
        "title_english": "Amal's Wit & Heavy Silence",
        "title_malayalam": "അമലിന്റെ തമാശയും മൗനവും",
        "synopsis": "Amal uses humor and teasing to diffuse the tension. Sachin feels deeply torn between confessing his life-changing London decision and the fear of overwhelming Reenu.",
        "cliffhanger": "Sachin promises Reenu: 'Before tonight ends, I will tell you everything.'"
    },
    7: {
        "title_english": "The Rain Settles",
        "title_malayalam": "മഴ തോർന്ന രാത്രി",
        "synopsis": "The car arrives outside Reenu's house. In the quiet, rain-washed night, Sachin walks Reenu to the front gate. A tender, lingering goodbye.",
        "cliffhanger": "Sachin gently holds Reenu's hand, asking her to meet him at Marine Drive walkway at midnight."
    },
    8: {
        "title_english": "Reenu's Suspicion & Worry",
        "title_malayalam": "റീനുവിന്റെ മനസ്സ്",
        "synopsis": "Reenu sits in her room by the window, watching the rain mist. She wonders whether Sachin's secret means he has to go back to the UK permanently.",
        "cliffhanger": "Reenu makes a heartfelt decision to profess her true love and ask Sachin never to leave again."
    },
    9: {
        "title_english": "A Midnight Message",
        "title_malayalam": "ഒരു സന്ദേശവും അർദ്ധരാത്രിയും",
        "synopsis": "Sachin and Amal prepare at Marine Drive. Amal gives Sachin emotional courage. Reenu arrives in the dim golden lights of Kochi backwaters.",
        "cliffhanger": "Sachin takes a deep breath, unzips the leather pouch, and steps forward toward Reenu."
    },
    10: {
        "title_english": "The Grand Climax: The Revelation",
        "title_malayalam": "ആ രഹസ്യത്തിന്റെ ചുരുളഴിയുമ്പോൾ",
        "synopsis": "SEASON 1 CLIMAX: Sachin reveals what was inside the pouch—his officially cancelled London visa documents and a permanent contract in Kochi, choosing to stay by Reenu's side forever. Tears of joy, a breathtaking embrace, and a sweet tease for Season 2!",
        "cliffhanger": "Sachin whispers: 'I'm never going back. I'm home.' Season 1 Climax completed!"
    }
}

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY_2") or os.getenv("GEMINI_API_KEY_3")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    return genai.Client(api_key=api_key)

def generate_next_episode_screenplay(current_ep_num, previous_story="", cliffhanger="", next_ep_premise="", cliffhanger_scene_state=None):
    """
    Calls Gemini to generate a captivating 1-minute next episode screenplay (10-11 shots)
    with locked character dress, strict lip-movement rules, female narrator, pure Malayalam dialogue,
    and rigorous sequence continuity (lighting, weather, spatial blocking, eyelines, persistent props, camera lens).
    Dynamically adheres to the Master Season 1 Roadmap and inherits cliffhanger scene state for episode continuity.
    """
    next_ep_num = current_ep_num + 1
    client = get_gemini_client()

    roadmap_target = SEASON_1_ROADMAP.get(next_ep_num, {})
    planned_title_en = roadmap_target.get("title_english", f"Episode {next_ep_num}")
    planned_title_ml = roadmap_target.get("title_malayalam", "")
    planned_synopsis = roadmap_target.get("synopsis", "")
    planned_cliffhanger = roadmap_target.get("cliffhanger", "")

    # Resolve previous episode context
    if not previous_story and current_ep_num in SEASON_1_ROADMAP:
        previous_story = SEASON_1_ROADMAP[current_ep_num]["synopsis"]
        cliffhanger = cliffhanger or SEASON_1_ROADMAP[current_ep_num]["cliffhanger"]

    # Target premise: use explicitly passed next_ep_premise or planned roadmap synopsis
    effective_premise = next_ep_premise or planned_synopsis or f"Episode {next_ep_num} story continuation."
    target_cliffhanger_guide = planned_cliffhanger or cliffhanger or "Tense romantic cliffhanger."
    
    print(f"\n=======================================================")
    print(f"✨ GEMINI AUTONOMOUS SCREENPLAY WRITER: EPISODE {next_ep_num} (1-MINUTE REEL)")
    print(f"=======================================================")
    print(f"Target Title: {planned_title_ml} ({planned_title_en})")
    print(f"Previous Episode {current_ep_num} Summary: {previous_story[:100]}...")
    print(f"Target Narrative Beat: {effective_premise[:100]}...")
    print(f"Target Cliffhanger: {target_cliffhanger_guide[:100]}...")
    if cliffhanger_scene_state:
        print(f"Inheriting Continuity Scene State: {cliffhanger_scene_state.get('scene_id')} ({cliffhanger_scene_state.get('weather')})")

    system_instruction = (
        "You are an acclaimed Malayalam romantic film director and 3D animated series showrunner. "
        "You write punchy, fast-paced, emotionally rich 1-MINUTE vertical episodes (Reels format) for the 3D animated cartoon series 'Sachin & Reenu'. "
        "Characters are strictly stylized 3D cartoon animation characters in high-end Disney Pixar / DreamWorks style. Real or human-like figures are strictly prohibited! "
        "LOCKED ATTIRE: Character clothing must be 100% consistent across every shot without exception. "
        "LIP SYNC & NARRATION RULES (CRITICAL): "
        "1. When the Third-Person Narrator is speaking (voice-over), NO CHARACTER'S MOUTH OR LIPS MUST MOVE. Characters' lips must be strictly closed with natural subtle emotional reactions. Characters must NOT speak the narrator's line! "
        "2. When characters converse, ONLY the speaking character's mouth moves in lip sync. The listening character's mouth remains closed. "
        "DIALOGUE STYLE: Use natural, standard, emotionally genuine conversational Malayalam (ശുദ്ധമായ സ്വാഭാവിക മലയാളം). Do NOT force slang. Focus on genuine romantic warmth, emotional vulnerability, and touching expressions. "
        "STRICT MALAYALAM SPELLING, PHONETICS & PRONUNCIATION (CRITICAL): "
        "1. Exact Character Names: "
        "   - Reenu: MUST ALWAYS be spelled 'റീനു' with hard 'റ' (NOT 'രീനു' with soft 'ര', NOT 'റീന'). Genitive: 'റീനുവിന്റെ', Dative: 'റീനുവിന്'. "
        "   - Amal: MUST ALWAYS be spelled 'അമൽ' with chillu 'ൽ' (STRICTLY FORBIDDEN: NEVER write 'അമലു' / Amalu or informal pet names). Genitive: 'അമലിന്റെ' (NOT 'അമലുവിന്റെ'), Dative: 'അമലിന്', Accusative: 'അമലിനെ' (NOT 'അമലുവിനെ'). "
        "   - Sachin: MUST ALWAYS be spelled 'സച്ചിൻ' (Pronounced 'Sachin' with crisp double-cha 'ച്ച' and chillu 'ൻ'). "
        "2. Accurate Dialogue Phonetics: "
        "   - Use authentic, grammatically correct, beautifully spoken Malayalam written in clean Malayalam script (മലയാളം ലിപി). "
        "   - Every word must be written with precise orthography so that text-to-speech voice generators and voice actors pronounce every syllable clearly without stumbling, slurring, or mispronouncing. "
        "NARRATOR VOICE: The third-person narrator is a young, expressive female narrator with a melodic, charming Malayalam storytelling voice. "
        "AUDIO RESTRICTION: STRICTLY NO BACKGROUND MUSIC, NO INSTRUMENTAL BGM, NO MUSIC SCORE. Clean voice audio and natural ambient foley effects only. "
        "STRICT NO-TEXT RESTRICTION: ABSOLUTELY NO VISIBLE ON-SCREEN TEXT, TYPOGRAPHY, WORDS, LETTERS, LABELS, WATERMARKS, TIMESTAMPS, OR LOGOS. The video frame must be completely clean of any written text, specifications, or graphic overlays. "
        "You will output ONLY valid JSON according to the specified schema."
    )

    handoff_text = ""
    if cliffhanger_scene_state:
        handoff_text = f"""
CONTINUITY HANDOFF FROM PREVIOUS EPISODE {current_ep_num} ENDING SCENE:
The previous episode ended with the following physical scene continuity state:
{json.dumps(cliffhanger_scene_state, ensure_ascii=False, indent=2)}
CRITICAL HANDOFF RULE: If Episode {next_ep_num} Shot 1 begins in this continuous sequence/location, you MUST seamlessly inherit this exact scene_id, weather, lighting palette, character spatial blocking, and prop placement to guarantee 100% continuous multi-shot flow across episode boundaries!
"""

    prompt = f"""
Write the full screenplay and shot-by-shot Google Flow JSON prompts for Episode {next_ep_num} of 'Sachin & Reenu'.

MASTER ROADMAP GUIDANCE:
- Expected Episode Title: {planned_title_ml} ({planned_title_en})
- Target Premise / Narrative Beat: {effective_premise}
- Target Climax / Cliffhanger: {target_cliffhanger_guide}

CONTEXT FROM PREVIOUS EPISODE {current_ep_num}:
Story: {previous_story}
Cliffhanger: {cliffhanger}
Premise/Hook for Episode {next_ep_num}: {effective_premise}
{handoff_text}

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
   - THIRD-PERSON NARRATION SHOTS (VOICEOVER ONLY):
     • The third-person narrator is an EXTERNAL, OFF-SCREEN STORYTELLER. NO on-screen character speaks the narration line!
     • These shots MUST focus on SHOWING THE SCENE ACTION AND CINEMATIC ENVIRONMENT (e.g., car moving on road, rain falling on streetlights, characters walking, looking at scenery, touching props, silent emotional bodily gestures).
     • In 'action', explicitly describe the physical scene action and state: "PURE VISUAL SCENE ACTION. All characters on screen are completely silent with lips firmly closed and relaxed. Absolutely NO character speaking, lip movement, or mouth animation. Characters do NOT speak."
     • In 'dialogue', the speaker MUST be: "Off-Screen Third-Person Narrator (Voiceover Only - Characters Do Not Speak)".
     • In 'audio_directive', state: "OFF-SCREEN FEMALE STORYTELLER VOICEOVER ONLY. NO CHARACTER SPEAKS ON SCREEN. All characters maintain strictly closed lips with zero talking or mouth animation. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voiceover audio and natural ambient foley sound effects only."
   - CONVERSATION / CHARACTER DIALOGUE SHOTS:
     • Only the designated speaking character moves their mouth in precise lip sync. The listening character's mouth remains strictly closed.
6. STRICT MALAYALAM CHARACTER NAMES & PRONUNCIATION ACCURACY (MANDATORY):
   - EXACT CANONICAL SPELLING FOR NAMES:
     • Reenu: Strictly 'റീനു' with hard 'റ' (NEVER 'രീനു' with soft 'ര', NEVER 'റീന').
     • Amal: Strictly 'അമൽ' with chillu 'ൽ' (FORBIDDEN: NEVER use 'അമലു' / Amalu. Amal's = 'അമലിന്റെ', Amal to = 'അമലിന്', Amal = 'അമലിനെ').
     • Sachin: Strictly 'സച്ചിൻ' with crisp double-cha 'ച്ച' (NEVER 'സചിൻ').
   - DIALOGUE PHONETICS & PRONUNCIATION: Write clean, grammatically sound, standard conversational Malayalam in Malayalam script (മലയാളം ലിപി). Ensure all words are phonetically accurate and easily pronounceable by voice synthesis / voiceover artists without slurring, mangled letters, or mispronunciation.

7. STRICT DIALOGUE LENGTH LIMIT (MANDATORY FOR VIDEO AI & AUDIO PACING):
   - CRITICAL PACING CONSTRAINT: Each shot is only 5s to 6s long. The video and voice synthesis CANNOT speak long dialogues in this short window without rushing or getting cut off.
   - MAXIMUM WORDS: Strictly MAXIMUM 5 to 8 WORDS per shot (under 40 Malayalam letters/characters).
   - SINGLE SHORT SENTENCE: Exactly ONE short, crisp, punchy sentence per shot. FORBIDDEN: NEVER write multiple sentences or compound paragraphs in a single shot.
   - NATURAL SPEECH: Dialogue must fit comfortably within 3 to 4 seconds of speech, leaving 1.5 to 2 seconds of ambient breathing room.
   - If a dialogue or narration is longer, split it into 2 separate consecutive shots!

8. ABSOLUTELY NO BACKGROUND MUSIC (BGM):
   - In every shot, "audio_directive" MUST strictly state: "CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voice dialogue and natural ambient foley sound effects only."
9. NEGATIVE PROMPT:
   - Must strictly include: "character mouth moving during voiceover, character lip sync during narration, open mouth talking during voiceover, character talking during narration, character speaking narrator words, speaking animation on character, character mouth moving, real human, realistic human, real person, live-action actor, photorealistic human face, human skin pores, hyperrealistic, uncanny valley, real life photography, realistic skin texture, 2D illustration, deformed faces, distorted anatomy, background music, musical score, instrumental BGM, singing, on-screen text, visible text, typography, fonts, writing, letters, words, alphabet, script, typography overlay, Disney text, Pixar text, Disney Pixar text, Disney logo, Pixar logo, Walt Disney logo, studio watermark, brand name, brand logo, character names on screen, Sachin text, Reenu text, Amal text, character name labels, name tags, name badges, floating names, timestamps, time text, clock numbers, timecode display, 6:30 PM, 4:45 PM, 5s, 6s, duration numbers, countdown timer, digital clock overlay, 4K text, 60fps text, Octane Render text, 9:16 text, aspect ratio labels, camera metadata text, resolution stamps, specification text, subtitles, closed captions, captions, lower thirds, title cards, watermarks, credits, copyright notices, UI text, user interface elements, graphic banners"
10. STYLE STRING:
   - "High-end Disney Pixar 3D animated cartoon movie, stylized 3D cartoon character render, cute expressive animated features, soft smooth 3D cartoon shaders, vertical 9:16 format, Octane 3D render 4k 60fps"

11. ORGANIC CHARACTER EXPANSION (OPTIONAL):
   - The core recurring cast is Reenu, Sachin, and Amal.
   - If the storyline organically calls for a new character (e.g. taxi driver, tea stall vendor, college friend, family member, bystander), you may introduce them.
   - If introduced, add their details to 'new_characters_introduced'.
   - Each entry must include:
     • "name": character name
     • "role": brief role in story
     • "age": integer
     • "gender": "male" / "female"
     • "visual_dna": detailed Disney Pixar stylized 3D cartoon animation prompt (strictly non-human realism)
     • "locked_attire": locked signature clothing description
     • "voice_persona": voice description
   - If NO new character is introduced for this episode, provide an empty array: "new_characters_introduced": []

12. SEQUENCE CONTINUITY & SPATIAL BLOCKING (CRITICAL FOR VIDEO AI & MULTI-SHOT COHERENCE):
   - In EVERY shot's "json_prompt", you MUST include a "sequence_continuity" object specifying:
     • "scene_id": Identifier for current physical sequence/location (e.g. "SCENE_CAR_KOCHI_RAIN", "SCENE_AIRPORT_ARRIVAL_GATE", "SCENE_TEA_STALL_BACKWATERS").
     • "time_of_day": Exact time of day (e.g. "4:45 PM Late Afternoon Monsoon Dusk").
     • "lighting_palette": Color temperature & lighting scheme (e.g. "Cool 5600K overcast exterior daylight with soft warm 3200K amber dashboard glow").
     • "weather": Persistent weather state (e.g. "Continuous Kochi monsoon drizzle with rain droplets sliding down car window glass").
     • "spatial_blocking": Dictionary mapping each character to their exact physical seat, standing position, and orientation. E.g.:
       {{
         "Amal": "Driver seat (right side), hands on steering wheel, facing road",
         "Sachin": "Front passenger seat (left side), seated upright with seatbelt, body angled toward Reenu",
         "Reenu": "Rear seat directly behind Sachin, leaning forward toward front seats"
       }}
       MANDATORY: Character positions and seating MUST NEVER randomly flip or swap between shots within the same sequence!
     • "eyeline_direction": Strict 180-degree rule camera axis & gaze direction (e.g. "Sachin looks screen-left/down; Reenu looks screen-right at Sachin").
     • "persistent_props": Array of key physical hero props present and their exact state/location (e.g. ["Vintage tan-brown London leather pouch under front passenger seat", "Sachin's diagonal brown leather cross-bag strap over left shoulder", "Reenu's silver wrist watch on left wrist"]).
     • "camera_lens": Specific cinematic focal length and aperture (e.g. "50mm cinematic prime lens, f/2.0 shallow depth of field, soft circular bokeh").

13. MANDATORY COMPLETE SELF-CONTAINED PROMPT FOR EVERY SHOT (ZERO SHORTCUTS):
   - Video generation AIs (Google Flow, Veo, Kling, Hailuo) generate each clip INDEPENDENTLY. They do NOT carry over memory from previous shots.
   - NEVER shorten, abbreviate, or omit fields in subsequent shots (e.g. Shot 2, Shot 3, Shot 4)!
   - In EVERY single shot, "characters_present" MUST contain full objects with "name" and the COMPLETE "visual_dna" with locked attire for EVERY character present in that shot/frame. FORBIDDEN: NEVER write plain string arrays like ["Sachin", "Reenu"]!
   - In EVERY single shot, "style" MUST be the full master 3D Pixar render string without truncating words.
   - In EVERY single shot, "persistent_props" MUST list all active scene props present in that sequence.
   - In EVERY single shot, "negative_prompt" MUST be the complete master negative prompt string.

14. STRICT PROHIBITION OF ON-SCREEN TEXT, TYPOGRAPHY, TIMESTAMPS & WATERMARKS (MANDATORY):
   - The visual video frames MUST be 100% clean and free of ANY written characters, symbols, numbers, or graphics.
   - SPECIFIC INDIVIDUAL TEXT PROHIBITIONS (Must strictly enforce across all prompts and negative prompts):
     • NO Studio/Brand text or logos: no Disney text, no Pixar text, no Disney Pixar text, no Disney logo, no Pixar logo, no Walt Disney logo, no studio watermarks, no brand names, no brand logos, no Disney font.
     • NO Character names as text: no character names on screen, no 'Sachin' text, no 'Reenu' text, no 'Amal' text, no character name labels, no name tags, no name badges, no floating names.
     • NO Time, timestamps, or durations: no timestamps, no time text, no clock numbers, no timecode display, no '6:30 PM', no '4:45 PM', no '5s', no '6s', no duration numbers, no countdown timers, no digital clock overlay.
     • NO Technical or camera specifications: no '4K' text, no '60fps' text, no 'Octane Render' text, no '9:16' text, no aspect ratio labels, no camera metadata text, no resolution stamps, no specification text.
     • NO Graphic overlays or text elements: no on-screen text, no typography, no subtitles, no closed captions, no captions, no lower thirds, no title card text, no watermarks, no credits, no copyright notices, no labels, no words, no letters, no alphabet, no UI elements.

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
  "new_characters_introduced": [
    {{
      "name": "...",
      "role": "...",
      "age": 24,
      "gender": "male",
      "visual_dna": "...",
      "locked_attire": "...",
      "voice_persona": "..."
    }}
  ],
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
        "sequence_continuity": {{
          "scene_id": "SCENE_CAR_KOCHI_RAIN",
          "time_of_day": "4:45 PM Late Afternoon Monsoon Dusk",
          "lighting_palette": "Cool 5600K overcast exterior daylight with soft warm 3200K amber dashboard glow",
          "weather": "Continuous Kochi monsoon drizzle with rain droplets sliding down car window glass",
          "spatial_blocking": {{
            "Amal": "Driver seat (right side), hands on steering wheel, facing road",
            "Sachin": "Front passenger seat (left side), seated upright with seatbelt, body angled toward Reenu",
            "Reenu": "Rear seat directly behind Sachin, leaning forward"
          }},
          "eyeline_direction": "Sachin looks screen-left; Reenu looks screen-right at Sachin",
          "persistent_props": [
            "Vintage tan-brown London leather pouch under front passenger seat",
            "Sachin's diagonal brown leather cross-bag strap over left shoulder",
            "Reenu's silver wrist watch on left wrist"
          ],
          "camera_lens": "50mm cinematic prime lens, f/2.0 shallow depth of field, soft circular bokeh"
        }},
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
        "negative_prompt": "character mouth moving during voiceover, character lip sync during narration, open mouth talking during voiceover, real human, realistic human, real person, live-action actor, photorealistic human face, human skin pores, hyperrealistic, uncanny valley, real life photography, realistic skin texture, 2D illustration, deformed faces, distorted anatomy, background music, musical score, instrumental BGM, singing, on-screen text, visible text, typography, fonts, writing, letters, words, Disney logo, Pixar logo, Disney Pixar text, studio watermark, brand name, character names on screen, Sachin text, Reenu text, Amal text, name tags, timestamps, time text, clock numbers, timecode display, 6:30 PM, 4:45 PM, 5s, 6s, 4K text, 60fps text, Octane Render text, 9:16 text, camera metadata text, subtitles, closed captions, lower thirds, title cards, watermarks, credits, UI text"
      }}
    }}
  ]
}}
"""

    candidate_models = ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-flash-latest"]
    parsed_data = None
    last_err = None

    def clean_json_text(raw_text):
        text = raw_text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        if repair_json:
            try:
                repaired = repair_json(text)
                return repaired
            except Exception:
                pass
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
                        temperature=0.7,
                        max_output_tokens=8192
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

    data = enforce_prompt_completeness(parsed_data)
    
    # Calculate exact total runtime
    total_sec = sum(s.get("duration_seconds", 6) for s in data["shots"])
    data["calculated_total_seconds"] = total_sec
    data["calculated_runtime_display"] = f"{total_sec // 60}m {total_sec % 60:02d}s"
    data["total_shots"] = len(data["shots"])
    
    print(f"✓ Successfully generated Episode {next_ep_num}: '{data.get('title_malayalam')}' ({data.get('title_english')})")
    print(f"✓ Total Shots: {data['total_shots']} | Runtime: {data['calculated_runtime_display']}")
    return data

def enforce_prompt_completeness(data):
    """
    Guarantees that 100% of the prompts are self-contained and fully detailed:
    1. Guarantees the complete 3D Pixar render MASTER_STYLE string on EVERY shot.
    2. Guarantees that EVERY character in characters_present has their FULL visual_dna object with locked attire.
       Never permits plain string arrays (e.g. ['Sachin', 'Reenu']) or stripped-down descriptions.
    3. Guarantees complete persistent_props across all shots in the sequence.
    4. Guarantees complete MASTER_NEGATIVE_PROMPT.
    """
    new_chars_map = {}
    for nc in data.get("new_characters_introduced", []):
        if isinstance(nc, dict) and nc.get("name") and nc.get("visual_dna"):
            new_chars_map[nc["name"]] = nc["visual_dna"]

    # Collect master props from sequence_continuity across shots
    all_props = set()
    for s in data.get("shots", []):
        jp = s.get("json_prompt", {})
        sc = jp.get("sequence_continuity", {})
        props = sc.get("persistent_props", [])
        if isinstance(props, list):
            for p in props:
                if isinstance(p, str) and p.strip():
                    all_props.add(p.strip())

    for s in data.get("shots", []):
        jp = s.get("json_prompt", {})
        # 1. Full style
        jp["style"] = MASTER_STYLE

        # 2. Characters present completeness
        raw_chars = jp.get("characters_present", [])
        normalized_chars = []
        for c in raw_chars:
            cname = c if isinstance(c, str) else c.get("name")
            if not cname:
                continue
            dna = DNA_REGISTRY.get(cname) or new_chars_map.get(cname)
            if not dna and isinstance(c, dict):
                dna = c.get("visual_dna", "")
            if not dna:
                dna = f"{cname}: Stylized 3D Pixar-style cartoon animation character."
            normalized_chars.append({
                "name": cname,
                "visual_dna": dna
            })
        
        # If characters_present was empty but dialogue character is specified, add them
        char_speaker = s.get("character")
        if char_speaker and char_speaker != "Third-Person Narrator":
            if not any(nc["name"] == char_speaker for nc in normalized_chars):
                normalized_chars.append({
                    "name": char_speaker,
                    "visual_dna": DNA_REGISTRY.get(char_speaker, f"{char_speaker}: Stylized 3D Pixar character.")
                })

        jp["characters_present"] = normalized_chars

        # 3. Full negative prompt
        jp["negative_prompt"] = MASTER_NEGATIVE_PROMPT

        # 4. Normalize persistent props in sequence_continuity
        if "sequence_continuity" in jp and isinstance(jp["sequence_continuity"], dict):
            sc = jp["sequence_continuity"]
            sc_props = sc.get("persistent_props", [])
            # If props were stripped down in this shot, restore all props from the scene
            if len(sc_props) < len(all_props) and len(all_props) > 0:
                sc["persistent_props"] = sorted(list(all_props))

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
        "new_characters_introduced": episode_data.get("new_characters_introduced", []),
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

    # Update story_state.json history and character cast
    state_path = Path("story_state.json")
    if state_path.exists():
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                state = json.load(f)
            ep_num = episode_data.get("episode_number", 1)
            state["total_episodes_produced"] = max(state.get("total_episodes_produced", 0), ep_num)
            state["episode_number"] = ep_num
            
            # Record organic new characters if introduced
            new_chars = episode_data.get("new_characters_introduced", [])
            if new_chars and isinstance(new_chars, list):
                if "characters" not in state:
                    state["characters"] = {}
                for nc in new_chars:
                    cname = nc.get("name")
                    if cname and cname not in state["characters"]:
                        state["characters"][cname] = {
                            "age": nc.get("age", 24),
                            "gender": nc.get("gender", "unknown"),
                            "voice": nc.get("voice_persona", "Malayalam expressive voice"),
                            "role": nc.get("role", "Supporting Character"),
                            "attire": nc.get("locked_attire", ""),
                            "visual_dna": nc.get("visual_dna", "")
                        }
                        print(f"✨ New character '{cname}' recorded in story_state.json!")

            history = state.get("history", [])
            existing_eps = [h.get("episode") for h in history]
            chars = list(set([
                s.get("character") for s in episode_data.get("shots", [])
                if s.get("character") and s.get("character") != "Third-Person Narrator"
            ]))
            new_entry = {
                "episode": ep_num,
                "title": f"{episode_data.get('title_malayalam', '')} ({episode_data.get('title_english', '')})",
                "summary": episode_data.get("synopsis", ""),
                "cliffhanger": episode_data.get("cliffhanger", ""),
                "characters_present": chars
            }
            if ep_num in existing_eps:
                for idx, h in enumerate(history):
                    if h.get("episode") == ep_num:
                        history[idx] = new_entry
                        break
            else:
                history.append(new_entry)
            state["history"] = history
            # Save cliffhanger scene state for continuity handoff to next episode
            shots = episode_data.get("shots", [])
            if shots:
                last_shot = shots[-1]
                last_prompt = last_shot.get("json_prompt", {})
                last_continuity = last_prompt.get("sequence_continuity")
                if last_continuity:
                    state["cliffhanger_scene_state"] = last_continuity
                    print("✓ Saved ending shot sequence continuity as cliffhanger_scene_state in story_state.json!")

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
    parser.add_argument("--current_ep", type=int, default=None, help="Completed episode number")
    parser.add_argument("--target_ep", type=int, default=None, help="Explicit target episode number to generate")
    parser.add_argument("--gas_url", default=os.getenv("GAS_WEBHOOK_URL", ""), help="Google Apps Script Web App URL")
    args = parser.parse_args()

    # Automatically resolve what episode is currently active / produced if not explicitly provided
    detected_ep = None
    for fn in ["current_episode_shots.json", "current_episode.json", "story_state.json"]:
        if os.path.exists(fn):
            try:
                with open(fn, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    val = d.get("episode_number") or d.get("total_episodes_produced")
                    if val:
                        detected_ep = int(val)
                        break
            except Exception:
                pass
    if detected_ep is None:
        detected_ep = 1

    # Determine target episode and previous episode
    if args.target_ep is not None:
        target_ep = args.target_ep
        effective_current_ep = target_ep - 1
    elif args.current_ep is not None:
        effective_current_ep = args.current_ep
        target_ep = effective_current_ep + 1
    else:
        # Default run: advance from current detected episode to the next one
        effective_current_ep = detected_ep
        target_ep = effective_current_ep + 1

    # Load context for effective_current_ep from roadmap
    prev_entry = SEASON_1_ROADMAP.get(effective_current_ep, {})
    previous_story = prev_entry.get("synopsis", (
        "Episode 1: After two long years of waiting, Reenu and Amal wait at Kochi CIAL airport arrivals. "
        "Sachin emerges through the doors resulting in an emotional reunion, but Sachin secretly clutches an anxious London leather pouch."
    ))
    cliffhanger = prev_entry.get("cliffhanger", "As Sachin holds Reenu close, his eyes reveal a hidden anxiety while his fingers tightly clutch a secret, unopened leather pouch.")

    # Check story_state.json if it has memory & scene continuity for effective_current_ep
    cliffhanger_scene_state = None
    if os.path.exists("story_state.json"):
        try:
            with open("story_state.json", "r", encoding="utf-8") as f:
                sstate = json.load(f)
                cliffhanger_scene_state = sstate.get("cliffhanger_scene_state")
                for h in sstate.get("history", []):
                    if h.get("episode") == effective_current_ep:
                        previous_story = h.get("summary") or previous_story
                        cliffhanger = h.get("cliffhanger") or cliffhanger
        except Exception as e:
            print(f"Notice reading story_state.json: {e}")

    # Load premise for target_ep from master roadmap
    target_entry = SEASON_1_ROADMAP.get(target_ep, {})
    premise = target_entry.get("synopsis", "")

    if target_ep == 1:
        effective_current_ep = 0
        previous_story = "Series Pilot: Sachin has been away in the UK for two long years, while Reenu waited for him in Kerala. Today is Sachin's return flight arriving at Kochi CIAL airport."
        cliffhanger = "Reenu waits with trembling hands behind the arrival barrier, not having seen Sachin in person for 730 days."
        premise = "Episode 1 Pilot ('തിരിച്ചുവരവ്' / 'The Homecoming'): Reenu and Amal wait anxiously at Kochi CIAL international arrival terminal. Amal teases Reenu in playful Kochi slang to break her tension. Sachin finally emerges through the glass doors, resulting in an emotional, tender, tearful reunion. Cliffhanger: As they embrace, Sachin clutches a secret leather pouch from London with a nervous look."

    print(f"Directing Episode {target_ep} from Master Season Roadmap:")
    print(f"  Target: {target_entry.get('title_malayalam', '')} ({target_entry.get('title_english', '')})")
    print(f"  Premise: {premise}")

    # 1. Generate Next Episode with Gemini
    ep_data = generate_next_episode_screenplay(
        current_ep_num=effective_current_ep,
        previous_story=previous_story,
        cliffhanger=cliffhanger,
        next_ep_premise=premise,
        cliffhanger_scene_state=cliffhanger_scene_state
    )

    # 2. Update local files & portal website
    update_creator_portal(ep_data)

    # 3. Sync to Google Sheet 3-Tab structure
    sync_new_episode_to_google_sheet(args.gas_url, ep_data)

if __name__ == "__main__":
    main()
