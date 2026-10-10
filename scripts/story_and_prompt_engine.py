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

# Stylized 3D Cartoon Animation Character Visual DNA Constants (Strictly Animated, Never Human-like)
BASE_DNA_REENU = "Reenu: Stylized 3D Pixar-style cartoon animation character, 22yo South Indian Malayali girl, big expressive hazel-brown animated cartoon doe eyes with lush stylized eyelashes, soft rounded cute cartoon cheeks, sweet warm animated smile, voluminous bouncy wavy dark-brown cartoon hair with soft curtain bangs, stylized 3D character proportions with smooth vibrant cartoon shaders (STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES)."
# Reenu's preference: Strictly casual T-shirt WITH EYE-CATCHING PATTERNS/PRINTS (clouds, florals, doodles, stripes) + denim skirt/jeans + sneakers + watch
DEFAULT_ATTIRE_REENU = "Pastel baby-blue and soft yellow cloud-pattern camouflage t-shirt, sky-blue denim skirt, white sneakers, silver wrist watch."

BASE_DNA_SACHIN = "Sachin: Stylized 3D Pixar-style cartoon animation character, 24yo South Indian Malayali boy, endearing boyish cartoon features, large expressive warm animated brown eyes, playful genuine contagious cartoon smile, stylized soft textured wavy dark cartoon hair, cute slightly exaggerated 3D character proportions with smooth cartoon shaders (STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES)."
# Sachin's preference: Strictly casual PLAIN T-shirt (100% solid color, ZERO patterns, ZERO graphics) + casual denim jeans + sneakers + cross-bag
DEFAULT_ATTIRE_SACHIN = "Solid forest-green plain crewneck t-shirt (strictly zero patterns or graphics), classic dark blue denim jeans, white sneakers, brown leather travel cross-bag worn diagonally across chest."

BASE_DNA_AMAL = "Amal: Stylized 3D Pixar-style cartoon animation character, 24yo South Indian Malayali boy, cheerful animated face, lively expressive cartoon eyes, broad energetic friendly cartoon smile, neat stylized short cartoon hairstyle, warm medium brown cartoon skin tone (STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES)."
# Amal's preference: Strictly casual PLAIN T-shirt (100% solid color, ZERO patterns, ZERO graphics) in a distinct contrasting color + casual denim jeans/pants
DEFAULT_ATTIRE_AMAL = "Solid mustard-yellow plain crewneck t-shirt (strictly zero patterns or graphics), slim-fit charcoal-black denim jeans, casual slip-on sneakers."

# Season 2 Canon Casual Wardrobes (Distinct contrasting colors across all 3 characters)
SEASON_2_CASUAL_ATTIRE = {
    "Sachin": "Solid olive-green plain crewneck t-shirt (strictly solid color, zero patterns or graphics), relaxed-fit dark indigo denim jeans, classic white sneakers, brown leather travel cross-bag worn diagonally across chest.",
    "Reenu": "Pastel lavender and blush-pink floral-doodle pattern printed oversized t-shirt, high-waisted medium-blue denim skirt, clean white sneakers, silver wrist watch.",
    "Amal": "Solid terracotta rust-orange plain crewneck t-shirt (strictly solid color, zero patterns or graphics), slim-fit charcoal-black denim jeans, casual slip-on sneakers."
}

BASE_DNA_MAP = {
    "Reenu": BASE_DNA_REENU,
    "Sachin": BASE_DNA_SACHIN,
    "Amal": BASE_DNA_AMAL
}

def format_character_visual_dna(name, physical_dna, attire):
    """
    Combines physical animation DNA with strictly locked attire into the canonical prompt format.
    """
    if "STRICTLY LOCKED ATTIRE" in physical_dna:
        return physical_dna
    p_dna = physical_dna.strip()
    if not p_dna.startswith(f"{name}:"):
        p_dna = f"{name}: {p_dna}"
    attire_clean = attire.strip().rstrip('.')
    return f"{p_dna} STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): {attire_clean}. Absolutely zero costume variations."

DNA_REENU = format_character_visual_dna("Reenu", BASE_DNA_REENU, DEFAULT_ATTIRE_REENU)
DNA_SACHIN = format_character_visual_dna("Sachin", BASE_DNA_SACHIN, DEFAULT_ATTIRE_SACHIN)
DNA_AMAL = format_character_visual_dna("Amal", BASE_DNA_AMAL, DEFAULT_ATTIRE_AMAL)

DNA_MADHAVAN = (
    "Madhavan (Reenu's Father): Stylized 3D Pixar-style cartoon animation character, 52yo South Indian Malayali gentleman, "
    "dignified traditional Malayali father features, expressive salt-and-pepper mustache, warm yet stern dark eyes, "
    "slightly greying temples in dark curly hair, gentle grandfatherly warmth beneath traditional composure "
    "(STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Crisp traditional Kerala cream-white cotton jubba worn over "
    "a traditional off-white kasavu mundu with thin golden border, black leather sandals, silver vintage wrist watch. "
    "Absolutely zero costume variations."
)

DNA_GIRIJA = (
    "Girija (Reenu's Mother): Stylized 3D Pixar-style cartoon animation character, 48yo South Indian Malayali lady, "
    "kind round motherly face, warm expressive dark-brown eyes, neat traditional hair bun adorned with fresh fragrant "
    "white jasmine flowers (mulla poo), endearing affectionate smile with cute cartoon dimple "
    "(STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Elegant Kerala traditional cream cotton set-saree with "
    "emerald-green border, delicate gold necklace and small traditional jhumka earrings, gold bangles on right wrist. "
    "Absolutely zero costume variations."
)

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
    "Amal": DNA_AMAL,
    "Madhavan": DNA_MADHAVAN,
    "Girija": DNA_GIRIJA
}

def is_formal_attire(attire_str):
    """
    Checks if an attire description contains formal or semi-formal elements that violate the casuals rule.
    """
    if not attire_str or not isinstance(attire_str, str):
        return False
    lower = attire_str.lower()
    formal_keywords = ["formal", "kurti", "kurta", "cigarette pants", "moccasins", "linen button-down", "linen shirt", "tailored trousers", "pressed half-sleeve"]
    return any(kw in lower for kw in formal_keywords)

def get_active_character_dna_map(season_num=1, character_updates=None, new_characters=None):
    """
    Builds the active character visual DNA dictionary, dynamically respecting season transitions,
    character_updates from dynamic season arc, and story_state.json.
    Strictly enforces casuals (plain t-shirts for Sachin & Amal, patterned t-shirt for Reenu, contrasting colors).
    """
    active_map = {
        "Reenu": DNA_REENU,
        "Sachin": DNA_SACHIN,
        "Amal": DNA_AMAL,
        "Madhavan": DNA_MADHAVAN,
        "Girija": DNA_GIRIJA
    }

    if season_num == 2:
        for cname, cattire in SEASON_2_CASUAL_ATTIRE.items():
            active_map[cname] = format_character_visual_dna(cname, BASE_DNA_MAP[cname], cattire)

    # 1. Read persisted wardrobe and cast from story_state.json
    state_file = Path("story_state.json")
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                sstate = json.load(f)
                chars = sstate.get("characters", {})
                for cname, cinfo in chars.items():
                    if not isinstance(cinfo, dict):
                        continue
                    v_dna = cinfo.get("visual_dna", "")
                    attire = cinfo.get("attire") or cinfo.get("locked_attire", "")

                    # Enforce casuals: if Sachin, Reenu, or Amal was assigned formals, sanitize to casuals
                    if cname in ["Sachin", "Reenu", "Amal"]:
                        if is_formal_attire(attire) or is_formal_attire(v_dna):
                            attire = SEASON_2_CASUAL_ATTIRE.get(cname) if season_num == 2 else (
                                DEFAULT_ATTIRE_REENU if cname == "Reenu" else (DEFAULT_ATTIRE_SACHIN if cname == "Sachin" else DEFAULT_ATTIRE_AMAL)
                            )
                            v_dna = ""
                    
                    if v_dna and "STRICTLY LOCKED ATTIRE" in v_dna:
                        active_map[cname] = v_dna
                    elif attire:
                        base = BASE_DNA_MAP.get(cname, v_dna or f"{cname}: Stylized 3D Pixar-style cartoon animation character.")
                        active_map[cname] = format_character_visual_dna(cname, base, attire)
                    elif v_dna:
                        active_map[cname] = v_dna
        except Exception as e:
            print(f"Notice reading story_state.json in get_active_character_dna_map: {e}")

    # 2. Apply fresh character_updates if passed (e.g. from generate_connected_season_arc)
    if character_updates:
        for cu in character_updates:
            cname = cu.get("name")
            if not cname:
                continue
            v_dna = cu.get("visual_dna", "")
            attire = cu.get("locked_attire") or cu.get("attire", "")
            if v_dna and "STRICTLY LOCKED ATTIRE" in v_dna:
                active_map[cname] = v_dna
            elif attire:
                base = BASE_DNA_MAP.get(cname, v_dna or f"{cname}: Stylized 3D Pixar-style cartoon animation character.")
                active_map[cname] = format_character_visual_dna(cname, base, attire)
            elif v_dna:
                active_map[cname] = v_dna

    # 3. Add fresh new characters if introduced
    if new_characters:
        for nc in new_characters:
            cname = nc.get("name")
            if not cname:
                continue
            v_dna = nc.get("visual_dna", "")
            attire = nc.get("locked_attire") or nc.get("attire", "")
            if v_dna and "STRICTLY LOCKED ATTIRE" in v_dna:
                active_map[cname] = v_dna
            elif attire:
                base = v_dna or f"{cname}: Stylized 3D Pixar-style cartoon animation character."
                active_map[cname] = format_character_visual_dna(cname, base, attire)
            elif v_dna:
                active_map[cname] = v_dna

    return active_map

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

# Master Season 2 Story Roadmap (10 Episodes)
SEASON_2_ROADMAP = {
    1: {
        "title_english": "The Unannounced Guests",
        "title_malayalam": "വിരുന്നുകാർ",
        "synopsis": "Reenu's traditional parents arrive in Kochi without warning, throwing Sachin and Reenu into sudden panic as they scramble to keep their apartment presentable.",
        "cliffhanger": "Just as Sachin finishes hiding a giant pile of dirty clothes, the doorbell rings, and he opens the door face-to-face with Reenu's stern father."
    },
    2: {
        "title_english": "The Living Room Trial",
        "title_malayalam": "ലിവിംഗ് റൂമിലെ വിചാരണ",
        "synopsis": "Madhavan inspects every corner of the house with a magnifying-glass stare, grilling Sachin on his life choices while Girija lovingly inspects the kitchen spice jars.",
        "cliffhanger": "Madhavan sternly asks Sachin: 'So, young man... what is your 5-year financial blueprint for my daughter?'"
    },
    3: {
        "title_english": "Chai, Jalebi & A Silent War",
        "title_malayalam": "ചായയും ജിലേബിയും ഒരു നിശ്ശബ്ദ യുദ്ധവും",
        "synopsis": "Reenu nervously serves freshly made tea while Amal bursts in unexpectedly, completely misunderstanding the situation and cracking hilarious jokes at the worst possible moments.",
        "cliffhanger": "Amal accidentally reveals Sachin's wild secret plan to start a coastal cafe in Fort Kochi!"
    },
    4: {
        "title_english": "A Stroll Along Marine Drive",
        "title_malayalam": "മറൈൻ ഡ്രൈവിലെ സായാഹ്നം",
        "synopsis": "Sachin accompanies Madhavan on an evening walk along Marine Drive walkway, attempting to bridge the generational divide with honest conversations about dreams and love.",
        "cliffhanger": "Madhavan stops, looks out across the backwaters, and shares a surprising memory of his own rebellious youth."
    },
    5: {
        "title_english": "Mother's Intuition",
        "title_malayalam": "അമ്മയുടെ മനസ്സും ചില ചോദ്യങ്ങളും",
        "synopsis": "Back at the house, Girija has a heart-to-heart talk with Reenu, noticing how happy and confident she looks beside Sachin.",
        "cliffhanger": "Girija pulls out a traditional family heirloom gold bangle and asks Reenu if she is truly sure about Sachin."
    },
    6: {
        "title_english": "The Fort Kochi Site Discovery",
        "title_malayalam": "ഫോർട്ട് കൊച്ചിയിലെ പുതിയ താവളം",
        "synopsis": "Sachin, Reenu, and Amal take the parents on a sight-seeing trip to Fort Kochi, subtly guiding them past the dream heritage building they want to turn into their cafe.",
        "cliffhanger": "A rival real estate developer arrives on scene, trying to seal the cafe lease before Sachin can submit his offer!"
    },
    7: {
        "title_english": "Race Against the Clock",
        "title_malayalam": "സമയവുമായുള്ള ഓട്ടം",
        "synopsis": "With Amal creating comical distractions, Sachin and Reenu rush through the rain-slicked heritage streets to reach the cafe property owner before the rival agent.",
        "cliffhanger": "The owner holds two competing lease agreements in his hands, waiting for Sachin to make his final pitch."
    },
    8: {
        "title_english": "Madhavan Steps In",
        "title_malayalam": "അച്ഛന്റെ അപ്രതീക്ഷിത ഇടപെടൽ",
        "synopsis": "Just as the cafe deal appears slipping away, Madhavan steps forward with unexpected gravitas and sharp negotiating wisdom, standing up for Sachin's integrity.",
        "cliffhanger": "The property owner smiles and hands the heritage cafe keys directly to Sachin and Reenu!"
    },
    9: {
        "title_english": "A Celebration at the Cafe Portico",
        "title_malayalam": "പഴയ പോർട്ടിക്കോയിലെ ആഘോഷം",
        "synopsis": "The family gathers on the wooden verandah of the new cafe space overlooking the Chinese fishing nets, sharing sweets and laughter as the evening rain begins.",
        "cliffhanger": "Madhavan raises his cup and formally gives his blessing to Sachin and Reenu's wedding and dream venture!"
    },
    10: {
        "title_english": "New Horizons & An Unbreakable Promise",
        "title_malayalam": "പുതിയ തുടക്കവും ആ സത്യവും",
        "synopsis": "SEASON 2 GRAND FINALE: As the cafe grand opening banner goes up under fairy lights, Sachin and Reenu share a tender, joyous look toward their bright future together in Kerala.",
        "cliffhanger": "Reenu holds Sachin's hand tight: 'We made our home together, Sachin.' Season 2 Climax completed!"
    }
}

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY_2") or os.getenv("GEMINI_API_KEY_3")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required")
    return genai.Client(api_key=api_key)

def generate_connected_season_arc(season_number, premise):
    """
    Calls Gemini to dynamically generate a cohesive, continuous 10-episode story roadmap based on user's premise.
    Also handles character costume updates and introduces new characters if required by the story.
    """
    client = get_gemini_client()
    candidate_models = ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-flash-latest"]

    system_instruction = (
        "You are the Showrunner and Head Screenplay Writer for the viral Disney Pixar 3D animated Malayalam romantic comedy series 'Sachin & Reenu' (സച്ചിൻ & റീനു). "
        "Language: Malayalam setting in Kerala (Kochi). "
        "You are architecting the complete 10-EPISODE MASTER STORY ROADMAP for an entire new season. "
        "CRITICAL PROGRESSION RULE: Every single episode must connect seamlessly into the next episode. "
        "Episode 1 introduces the premise/arrival. "
        "Episode 2 directly follows Episode 1's cliffhanger. "
        "Episode 3 escalates the narrative with comedic or emotional complications. "
        "Episodes continue sequentially without filler or narrative drag, culminating in Episode 10 as the grand emotional climax resolving the core story. "
        "Output ONLY valid JSON."
    )

    prompt = f"""
Architect a continuous, tightly interconnected 10-EPISODE MASTER STORY ROADMAP for Season {season_number} of 'Sachin & Reenu' (സച്ചിൻ & റീനു).

CORE USER STORY PREMISE / PLOT:
"{premise}"

REQUIREMENTS:
1. STRICT CHRONOLOGICAL CONTINUITY (EVERY EPISODE CONNECTS TO THE NEXT):
   - Episode 1: Direct opening inciting incident introducing the premise (e.g. if parents arrive, their unexpected arrival at the Kochi flat).
   - Episode 2: Direct continuation of Episode 1 cliffhanger (e.g. living room interrogation, parents inspecting the flat).
   - Episode 3: Humorous complication or friend intervention (e.g. Amal barging in unexpectedly, awkward tea conversation).
   - Episode 4: Growing tension or outdoor interaction (e.g. walk along Marine Drive, testing Sachin's career/intentions).
   - Episode 5: Secret or emotional vulnerability shared (e.g. mother's intuition, heart-to-heart talk with Reenu).
   - Episode 6: A major shared challenge or adventure in Kochi (e.g. shopping, visiting Fort Kochi, vehicle trouble).
   - Episode 7: Misunderstanding or rising conflict (e.g. father disapproving or rival proposal mention).
   - Episode 8: Turning point / Sachin proving his genuine love, maturity, and responsibility.
   - Episode 9: Pre-climax high emotion / pivotal decision or parents' impending departure.
   - Episode 10: Grand Season Finale Climax / full emotional blessing, heartwarming romantic victory directly resolving the plot.

2. EPISODE FORMAT:
   - Exactly 10 episodes numbered 1 to 10.
   - Each episode has:
     • "episode_number": integer (1..10)
     • "title_english": Catchy English title
     • "title_malayalam": Accurate, natural Malayalam title in Malayalam script (മലയാളം ലിപി)
     • "status": "Active" for Episode 1, "Upcoming" for Episodes 2 through 10. (NONE marked Published).
     • "synopsis": Clear, detailed 2-3 sentence narrative describing the action of that 1-minute reel.
     • "cliffhanger": Dramatic ending hook that leads directly into the next episode.

3. CHARACTER ATTIRE RULES (STRICT CASUALS ONLY - NO FORMALS):
   - ABSOLUTELY NO FORMALS OR SEMI-FORMALS for the core trio (NO formal shirts, NO formal trousers, NO kurtas, NO cigarette pants, NO button-downs, NO linen formals).
   - Sachin, Reenu, and Amal MUST ALWAYS WEAR CASUALS (T-shirts & jeans / denim skirts / pants / sneakers).
   - SACHIN'S STYLE PREFERENCE:
     • Strictly a PLAIN casual T-shirt (100% solid color, ZERO patterns, ZERO prints, ZERO graphics).
     • Casual denim jeans (dark indigo, charcoal, or faded blue denim), clean sneakers, and his signature brown leather cross-bag.
   - AMAL'S STYLE PREFERENCE:
     • Strictly a PLAIN casual T-shirt (100% solid color, ZERO patterns, ZERO prints, ZERO graphics) or plain polo.
     • Casual denim jeans or chinos, casual sneakers/slip-ons.
   - REENU'S STYLE PREFERENCE:
     • Strictly a casual T-shirt WITH EYE-CATCHING PATTERNS/PRINTS (STRICTLY PATTERNED: graphic doodles, cute floral prints, cloud prints, retro stripes, or abstract geometric patterns). Every season she gets a fresh new distinctive pattern!
     • Casual denim skirt, mom jeans, or denim pants, clean sneakers, and silver wrist watch.
   - MANDATORY COLOR CONTRAST & DIVERSITY (NO MATCHING OR SIMILAR COLORS):
     • Sachin, Reenu, and Amal MUST NEVER wear matching, identical, or similar colors in the same season! (It looks awkward on screen).
     • Each of the 3 characters MUST wear distinctly contrasting, harmonious colors (e.g. Sachin in Olive Green, Amal in Terracotta Rust-Orange, Reenu in Pastel Lavender/Pink pattern).
   - NEW CHARACTERS (e.g., traditional parents like Reenu's Father or Mother):
     • Traditional Kerala elderly parents wear traditional attire (mundu, jubba, saree). Younger friends or colleagues follow casuals.

Output JSON matching this exact schema:
{{
  "season_title": "Season Title in English (മലയാളം ശീർഷകം)",
  "character_updates": [
    {{
      "name": "Sachin",
      "locked_attire": "...",
      "visual_dna": "..."
    }},
    {{
      "name": "Reenu",
      "locked_attire": "...",
      "visual_dna": "..."
    }}
  ],
  "new_characters": [
    {{
      "name": "Character Name",
      "role": "Role in story",
      "age": 52,
      "gender": "male",
      "visual_dna": "Stylized 3D Pixar-style cartoon character...",
      "locked_attire": "...",
      "voice_persona": "..."
    }}
  ],
  "episodes": [
    {{
      "episode_number": 1,
      "title_english": "...",
      "title_malayalam": "...",
      "status": "Active",
      "synopsis": "...",
      "cliffhanger": "..."
    }},
    ... up to episode_number 10
  ]
}}
"""
    def clean_json(raw_text):
        text = raw_text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        if repair_json:
            try:
                return json.loads(repair_json(text))
            except Exception:
                pass
        text = re.sub(r',\s*([\]\}])', r'\1', text)
        return json.loads(text)

    for model_name in candidate_models:
        print(f"Architecting Season {season_number} 10-episode continuous roadmap with {model_name}...")
        for attempt in range(3):
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.7,
                        max_output_tokens=8192
                    )
                )
                if resp and resp.text:
                    arc_data = clean_json(resp.text)
                    if "episodes" in arc_data and len(arc_data["episodes"]) >= 10:
                        arc_data["episodes"] = arc_data["episodes"][:10]
                        for idx, ep in enumerate(arc_data["episodes"]):
                            ep["episode_number"] = idx + 1
                            ep["status"] = "Active" if idx == 0 else "Upcoming"
                        print(f"✓ Successfully architected 10-episode continuous storyline for Season {season_number}: '{arc_data.get('season_title')}'")
                        return arc_data
            except Exception as e:
                print(f"  Attempt {attempt + 1} with {model_name} failed: {e}")
                time.sleep(2)

    print("Notice: Using fallback roadmap due to API timeout.")
    fallback_map = SEASON_2_ROADMAP if season_number == 2 else SEASON_1_ROADMAP
    return {
        "season_title": f"Season {season_number}: Fort Kochi Days (ഫോർട്ട് കൊച്ചി ദിനങ്ങൾ)",
        "character_updates": [],
        "new_characters": [],
        "episodes": [
            {
                "episode_number": idx,
                "title_english": info["title_english"],
                "title_malayalam": info["title_malayalam"],
                "status": "Active" if idx == 1 else "Upcoming",
                "synopsis": info["synopsis"],
                "cliffhanger": info["cliffhanger"]
            }
            for idx, info in fallback_map.items()
        ]
    }

def generate_next_episode_screenplay(current_ep_num, season_number=1, previous_story="", cliffhanger="", next_ep_premise="", cliffhanger_scene_state=None, is_new_season=False, target_entry=None, season_title="", active_character_dna=None):
    """
    Calls Gemini to generate a captivating 1-minute next episode screenplay (10-11 shots)
    with locked character dress, strict lip-movement rules, female narrator, pure Malayalam dialogue,
    and rigorous sequence continuity (lighting, weather, spatial blocking, eyelines, persistent props, camera lens).
    Dynamically adheres to the Master Season Roadmap and inherits cliffhanger scene state for episode continuity.
    """
    next_ep_num = 1 if is_new_season else (current_ep_num + 1)
    client = get_gemini_client()

    if active_character_dna is None:
        active_character_dna = get_active_character_dna_map(season_number)

    dna_guidelines_list = []
    for cname in ["Reenu", "Sachin", "Amal"]:
        if cname in active_character_dna:
            dna_guidelines_list.append(f"     • {cname} Visual DNA: \"{active_character_dna[cname]}\"")
    for cname, cdna in active_character_dna.items():
        if cname not in ["Reenu", "Sachin", "Amal"]:
            dna_guidelines_list.append(f"     • {cname} Visual DNA: \"{cdna}\"")
    dna_guidelines = "\n".join(dna_guidelines_list)

    active_roadmap = SEASON_2_ROADMAP if season_number == 2 else SEASON_1_ROADMAP
    roadmap_target = active_roadmap.get(next_ep_num, {})
    planned_title_en = roadmap_target.get("title_english", f"Episode {next_ep_num}")
    planned_title_ml = roadmap_target.get("title_malayalam", "")
    planned_synopsis = roadmap_target.get("synopsis", "")
    planned_cliffhanger = roadmap_target.get("cliffhanger", "")

    # Resolve previous episode context
    if is_new_season:
        previous_story = "Season 1 Climax: Sachin cancelled his London visa and decided to stay in Kerala for love. Season 2 begins a new chapter in Kochi with Reenu."
        cliffhanger = "A new beginning awaits in Kochi."
    elif not previous_story and current_ep_num in active_roadmap:
        previous_story = active_roadmap[current_ep_num]["synopsis"]
        cliffhanger = cliffhanger or active_roadmap[current_ep_num]["cliffhanger"]

    # Target premise: use explicitly passed next_ep_premise or planned roadmap synopsis
    effective_premise = next_ep_premise or planned_synopsis or f"Episode {next_ep_num} story continuation."
    target_cliffhanger_guide = planned_cliffhanger or cliffhanger or "Tense romantic cliffhanger."
    
    print(f"\n=======================================================")
    print(f"✨ GEMINI AUTONOMOUS SCREENPLAY WRITER: SEASON {season_number} EPISODE {next_ep_num} (1-MINUTE REEL)")
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
2. NUMBER OF SHOTS: STRICTLY EXACTLY 10 SHOTS (Shot 1 to Shot 10. Absolutely NO more than 10 shots, NO fewer than 10 shots).
3. DURATION LOGIC PER SHOT:
   - Dialogue exchange / action: "6s" (6 seconds per shot) for each of the 10 shots.
   - Total sum of shot durations MUST be exactly 60 seconds (1 minute total).
4. STRICT CINEMATIC SHOT FLOW & CAUSE-AND-EFFECT CONTINUITY (MANDATORY):
   - Every episode MUST tell a fluid 10-shot story with CLEAR CAUSE-AND-EFFECT PROGRESSION:
     • Shot 1: Establishing setting, mood, and initial character activity (Warm atmosphere).
     • Shot 2: Playful/organic dialogue exchange between characters.
     • Shot 3: Counter-reaction or continuing conversation beat.
     • Shot 4: Scenic intimate/humorous bonding moment or action beat.
     • Shot 5: THE DISRUPTION / HOOK: An external sound, event, phone ring, or knock that shatters the calm.
     • Shot 6: Investigation / reaction to the disruption (walking toward door/window/source).
     • Shot 7: Comic panic / preparatory action (hiding mess, whispering, scrambling).
     • Shot 8: THE REVELATION / CLIMAX ACTION: The door opens / the arrival / the discovery (gasps, shock).
     • Shot 9: THE REACTION SHOT: Contrasting perspective of the other character frozen/caught red-handed.
     • Shot 10: THE CLIFFHANGER PUNCHLINE: The definitive line or frozen confrontation that ends the episode.
   - ZERO REPETITIVE DIALOGUE: Never repeat the same question or line in consecutive shots (e.g. asking "Who is at the door?" twice).
   - ZERO REPEATED PHYSICAL ACTIONS: An irreversible physical action can happen ONLY ONCE in a scene (e.g. if the door is opened in Shot 8, do NOT open the door again in Shot 9 or 10; keep it open!).
   - CANONICAL CHARACTER NAMES: Never mix up family names (e.g. Reenu's father is Kurian, NOT Roy; her mother is Annamma, NOT Molly).
4. STRICT ANIMATION CHARACTER REQUIREMENT & LOCKED CASUAL ATTIRE:
   - All characters MUST be stylized Disney-Pixar 3D animated cartoon models.
   - STRICTLY PROHIBIT photorealistic humans, realistic humans, live-action actors, real people, human skin pores, or uncanny valley realism.
   - STRICT CASUAL ATTIRE RULES FOR SACHIN, REENU & AMAL (ZERO FORMALS):
     • Sachin, Reenu, and Amal MUST strictly wear CASUALS (T-shirts & jeans / denim skirts / pants). Absolutely NO formal shirts, NO formal trousers, NO kurtis/kurtas, NO cigarette pants!
     • Sachin & Amal: Strictly PLAIN solid t-shirts (zero patterns/prints), contrasting distinct solid colors.
     • Reenu: Strictly a casual t-shirt WITH PATTERNS/PRINTS (florals, doodles, clouds, stripes), casual denim skirt or mom jeans, white sneakers.
     • Contrasting colors: All 3 characters must wear distinctly different colors (never matching or similar colors in the same season).
   - Character visual DNA and locked clothing must be followed 100% identically:
{dna_guidelines}
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
     • "time_of_day": Pure atmospheric descriptive time (e.g. "Late Afternoon Monsoon Dusk", "Monsoon Night"). STRICTLY FORBIDDEN: NEVER use clock timestamps or numbers like "4:45 PM", "8:30 PM", because video AI prints them as slate text!
     • "lighting_palette": Pure visual lighting atmosphere (e.g. "Cool overcast daylight with soft warm amber dashboard glow", "Moonlight with warm porch lamp glow"). STRICTLY FORBIDDEN: NEVER use Kelvin numbers like "5600K" or "3200K" because video AI prints them as slate text!
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
     • "camera_lens": Pure cinematic depth description (e.g. "Cinematic prime lens, shallow depth of field, soft circular bokeh"). STRICTLY FORBIDDEN: NEVER use millimeter or f-stop numbers like "50mm", "85mm", "f/1.8", "f/2.0" because video AI prints them as slate text!

13. MANDATORY COMPLETE SELF-CONTAINED PROMPT FOR EVERY SHOT (ZERO SHORTCUTS):
   - Video generation AIs (Google Flow, Veo, Kling, Hailuo) generate each clip INDEPENDENTLY. They do NOT carry over memory from previous shots.
   - NEVER shorten, abbreviate, or omit fields in subsequent shots (e.g. Shot 2, Shot 3, Shot 4)!
   - In EVERY single shot, "characters_present" MUST contain full objects with "name" and the COMPLETE "visual_dna" with locked attire for EVERY character present in that shot/frame. FORBIDDEN: NEVER write plain string arrays like ["Sachin", "Reenu"]!
   - In EVERY single shot, "style" MUST be the full master 3D Pixar render string without truncating words.
   - In EVERY single shot, "persistent_props" MUST list all active scene props present in that sequence.
   - DO NOT include "negative_prompt" inside "json_prompt". Single-box video generators like Google Flow read all fields inside the prompt box as positive instructions, so negative words cause text hallucination.

14. STRICT PROHIBITION OF ON-SCREEN TEXT, TYPOGRAPHY, TIMESTAMPS & WATERMARKS (MANDATORY):
   - The visual video frames MUST be 100% clean and free of ANY written characters, symbols, numbers, or graphics.
   - SPECIFIC INDIVIDUAL TEXT PROHIBITIONS (Must strictly enforce across all prompts):
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
            "visual_dna": "{active_character_dna.get('Reenu', DNA_REENU)}"
          }}
        ],
        "sequence_continuity": {{
          "scene_id": "SCENE_CAR_KOCHI_RAIN",
          "time_of_day": "Late Afternoon Monsoon Dusk",
          "lighting_palette": "Cool overcast exterior daylight with soft warm amber dashboard glow",
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
          "camera_lens": "Cinematic prime lens, shallow depth of field, soft circular bokeh"
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
        "audio_directive": "EXTERNAL FEMALE VOICEOVER ONLY. The characters do NOT speak. Character lips remain completely closed with NO lip sync animation. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voiceover audio and natural ambient foley sound effects only."
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

    data = enforce_prompt_completeness(parsed_data, active_character_dna)
    
    # Calculate exact total runtime
    total_sec = sum(s.get("duration_seconds", 6) for s in data["shots"])
    data["calculated_total_seconds"] = total_sec
    data["calculated_runtime_display"] = f"{total_sec // 60}m {total_sec % 60:02d}s"
    data["total_shots"] = len(data["shots"])
    data["episode_number"] = next_ep_num
    data["season_number"] = season_number
    data["is_new_season"] = is_new_season
    
    if season_number == 2:
        data["season_title"] = "The Unannounced Guests & Fort Kochi Days (വിരുന്നുകാരും പുതിയ തുടക്കവും)"
        data["season_arc"] = [
            {
                "season_number": 2,
                "episode_number": ep_idx,
                "title_english": ep_info["title_english"],
                "title_malayalam": ep_info["title_malayalam"],
                "status": "Active" if ep_idx == next_ep_num else ("Published" if ep_idx < next_ep_num else "Upcoming"),
                "synopsis": ep_info["synopsis"],
                "cliffhanger": ep_info["cliffhanger"]
            }
            for ep_idx, ep_info in SEASON_2_ROADMAP.items()
        ]
    else:
        data["season_title"] = "The Homecoming & The London Secret (തിരിച്ചുവരവ്)"
        data["season_arc"] = [
            {
                "season_number": 1,
                "episode_number": ep_idx,
                "title_english": ep_info["title_english"],
                "title_malayalam": ep_info["title_malayalam"],
                "status": "Active" if ep_idx == next_ep_num else ("Published" if ep_idx < next_ep_num else "Upcoming"),
                "synopsis": ep_info["synopsis"],
                "cliffhanger": ep_info["cliffhanger"]
            }
            for ep_idx, ep_info in SEASON_1_ROADMAP.items()
        ]
    
    print(f"✓ Successfully generated Season {season_number} Episode {next_ep_num}: '{data.get('title_malayalam')}' ({data.get('title_english')})")
    print(f"✓ Total Shots: {data['total_shots']} | Runtime: {data['calculated_runtime_display']}")
    return data

def enforce_prompt_completeness(data, active_dna=None):
    """
    Guarantees that 100% of the prompts are self-contained and fully detailed:
    1. Guarantees the complete 3D Pixar render MASTER_STYLE string on EVERY shot.
    2. Guarantees that EVERY character in characters_present has their FULL visual_dna object with locked attire.
       Never permits plain string arrays (e.g. ['Sachin', 'Reenu']) or stripped-down descriptions.
       Dynamically respects the active season's costume changes.
    3. Guarantees complete persistent_props across all shots in the sequence.
    4. Guarantees complete MASTER_NEGATIVE_PROMPT.
    """
    if active_dna is None:
        active_dna = get_active_character_dna_map(data.get("season_number", 1))
    else:
        active_dna = dict(active_dna)

    # Incorporate any character_updates or new characters inside data
    for cu in data.get("character_updates", []):
        if isinstance(cu, dict) and cu.get("name"):
            cname = cu["name"]
            attire = cu.get("locked_attire") or cu.get("attire", "")
            vdna = cu.get("visual_dna", "")
            # Enforce casuals: never allow formals to override casual wardrobe
            if cname in ["Sachin", "Reenu", "Amal"]:
                if is_formal_attire(attire) or is_formal_attire(vdna):
                    season_n = data.get("season_number", 2)
                    attire = SEASON_2_CASUAL_ATTIRE.get(cname) if season_n == 2 else (
                        DEFAULT_ATTIRE_REENU if cname == "Reenu" else (DEFAULT_ATTIRE_SACHIN if cname == "Sachin" else DEFAULT_ATTIRE_AMAL)
                    )
                    vdna = ""
            if vdna and "STRICTLY LOCKED ATTIRE" in vdna:
                active_dna[cname] = vdna
            elif attire:
                base = BASE_DNA_MAP.get(cname, vdna or f"{cname}: Stylized 3D Pixar-style cartoon animation character.")
                active_dna[cname] = format_character_visual_dna(cname, base, attire)
            elif vdna:
                active_dna[cname] = vdna

    for nc in data.get("new_characters_introduced", []):
        if isinstance(nc, dict) and nc.get("name"):
            cname = nc["name"]
            attire = nc.get("locked_attire") or nc.get("attire", "")
            vdna = nc.get("visual_dna", "")
            if cname in ["Sachin", "Reenu", "Amal"]:
                if is_formal_attire(attire) or is_formal_attire(vdna):
                    season_n = data.get("season_number", 2)
                    attire = SEASON_2_CASUAL_ATTIRE.get(cname) if season_n == 2 else (
                        DEFAULT_ATTIRE_REENU if cname == "Reenu" else (DEFAULT_ATTIRE_SACHIN if cname == "Sachin" else DEFAULT_ATTIRE_AMAL)
                    )
                    vdna = ""
            if vdna and "STRICTLY LOCKED ATTIRE" in vdna:
                active_dna[cname] = vdna
            elif attire:
                base = vdna or f"{cname}: Stylized 3D Pixar-style cartoon animation character."
                active_dna[cname] = format_character_visual_dna(cname, base, attire)
            elif vdna:
                active_dna[cname] = vdna

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
            # Priority 1: active_dna (season costume changes)
            dna = active_dna.get(cname)
            # Priority 2: character's own visual_dna from Gemini if complete
            if not dna and isinstance(c, dict) and c.get("visual_dna") and "STRICTLY LOCKED ATTIRE" in c.get("visual_dna"):
                dna = c.get("visual_dna")
            # Priority 3: Fallback DNA registry
            if not dna:
                dna = DNA_REGISTRY.get(cname) or f"{cname}: Stylized 3D Pixar-style cartoon animation character."
            normalized_chars.append({
                "name": cname,
                "visual_dna": dna
            })
        
        # If characters_present was empty but dialogue character is specified, add them
        char_speaker = s.get("character")
        if char_speaker and char_speaker != "Third-Person Narrator":
            if not any(nc["name"] == char_speaker for nc in normalized_chars):
                dna = active_dna.get(char_speaker) or DNA_REGISTRY.get(char_speaker, f"{char_speaker}: Stylized 3D Pixar character.")
                normalized_chars.append({
                    "name": char_speaker,
                    "visual_dna": dna
                })

        jp["characters_present"] = normalized_chars

        # 3. Clean slate metadata and remove negative_prompt so single-box tools never draw badges
        jp.pop("negative_prompt", None)

        # 4. Normalize and clean sequence_continuity
        if "sequence_continuity" in jp and isinstance(jp["sequence_continuity"], dict):
            sc = jp["sequence_continuity"]
            sc_props = sc.get("persistent_props", [])
            # If props were stripped down in this shot, restore all props from the scene
            if len(sc_props) < len(all_props) and len(all_props) > 0:
                sc["persistent_props"] = sorted(list(all_props))

            # Strip clock numbers (e.g., '8:30 PM ', '4:45 PM ')
            if "time_of_day" in sc and isinstance(sc["time_of_day"], str):
                sc["time_of_day"] = re.sub(r'\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?\s*', '', sc["time_of_day"]).strip()
                if not sc["time_of_day"]:
                    sc["time_of_day"] = "Monsoon Night"

            # Strip Kelvin temperature numbers (e.g., '3200K', '5200K')
            if "lighting_palette" in sc and isinstance(sc["lighting_palette"], str):
                sc["lighting_palette"] = re.sub(r'\b\d{4,5}K\s*', '', sc["lighting_palette"]).strip()

            # Strip lens millimeter and aperture numbers (e.g., '85mm', 'f/1.8')
            if "camera_lens" in sc and isinstance(sc["camera_lens"], str):
                clean_lens = re.sub(r'\b\d{2,3}mm\s*', '', sc["camera_lens"])
                clean_lens = re.sub(r'f/\d+(\.\d+)?\s*', '', clean_lens).strip()
                clean_lens = re.sub(r',\s*,', ',', clean_lens).strip(', ')
                if not clean_lens:
                    clean_lens = "Cinematic prime lens, shallow depth of field"
                sc["camera_lens"] = clean_lens

    # Strictly guarantee exactly 10 shots per episode
    shots = data.get("shots", [])
    if len(shots) > 10:
        shots = shots[:10]
    for idx, shot in enumerate(shots, start=1):
        shot["shot_number"] = idx
        if "json_prompt" in shot:
            # ensure shot duration is 6s
            shot["duration"] = "6s"
            shot["duration_seconds"] = 6
            shot["json_prompt"]["duration"] = "6s"
    data["shots"] = shots
    data["total_shots"] = len(shots)
    data["calculated_total_seconds"] = len(shots) * 6
    data["calculated_runtime_display"] = f"{data['calculated_total_seconds'] // 60}m {data['calculated_total_seconds'] % 60:02d}s"

    return data

def sync_new_episode_to_google_sheet(gas_url, episode_data):
    """
    Calls Google Apps Script to:
    1. Update Tab 1 (Episode_Story) with the new episode outline.
    2. Overwrite Tab 2 (Current_JSON_Prompts) with the new JSON prompts.
    3. Tab 3 (Video_Checklist) remains UNTOUCHED during season transition.
    4. Overwrite Tab 4 (Season_Story_Arc) with the full 10-episode continuous roadmap.
    5. Update Tab 5 (Character_Registry) with costume changes and new characters.
    """
    if not gas_url:
        print("Notice: GAS_WEBHOOK_URL not set. Skipping remote Google Sheet sync.")
        return False
        
    season_num = episode_data.get("season_number", 1)
    is_new_season = episode_data.get("is_new_season", False)
    season_title = episode_data.get("season_title", f"Season {season_num}")
    season_arc = episode_data.get("season_arc", [])
    
    print(f"\nUpdating Google Sheet with Season {season_num} Episode {episode_data['episode_number']} prompts & roadmap...")
    
    action_name = "clean_slate_season_transition" if is_new_season else "update_next_episode_full"
    payload = {
        "action": action_name,
        "season_number": season_num,
        "is_new_season": is_new_season,
        "season_title": season_title,
        "season_arc": season_arc,
        "episodes": season_arc,
        "character_updates": episode_data.get("character_updates", []),
        "new_characters": episode_data.get("new_characters_introduced", []),
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
    
    # 1. Try POST with text/plain
    try:
        res = requests.post(gas_url, data=json.dumps(payload), headers={"Content-Type": "text/plain"}, timeout=45)
        if res.status_code == 200:
            res_json = {}
            try:
                res_json = res.json()
            except Exception:
                pass
            if res_json.get("error") == "Unknown action" and is_new_season:
                print("clean_slate_season_transition not recognized on older GAS deployment, falling back to update_next_episode_full...")
                payload["action"] = "update_next_episode_full"
                res = requests.post(gas_url, data=json.dumps(payload), headers={"Content-Type": "text/plain"}, timeout=45)
            print(f"✓ Google Sheet updated via POST: HTTP {res.status_code}")
            return True
        else:
            print(f"POST returned HTTP {res.status_code}, falling back to GET sync...")
    except Exception as e:
        print(f"Notice on POST sync: {e}, falling back to GET sync...")
        
    # 2. Resilient GET fallback
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
            is_new = episode_data.get("is_new_season", False)

            if is_new:
                state["season_number"] = episode_data.get("season_number", 2)
                state["total_episodes_produced"] = 1
                state["episode_number"] = 1
                state["history"] = []
                if episode_data.get("season_arc"):
                    state["season_arc"] = episode_data["season_arc"]
                if episode_data.get("season_title"):
                    state["season_title"] = episode_data["season_title"]
                
                # Update character costumes if changed
                char_updates = episode_data.get("character_updates", [])
                if char_updates and isinstance(char_updates, list):
                    if "characters" not in state:
                        state["characters"] = {}
                    for cu in char_updates:
                        cname = cu.get("name")
                        if cname:
                            if cname not in state["characters"]:
                                state["characters"][cname] = {}
                            if cu.get("locked_attire") or cu.get("attire"):
                                state["characters"][cname]["attire"] = cu.get("locked_attire") or cu.get("attire")
                            if cu.get("visual_dna"):
                                state["characters"][cname]["visual_dna"] = cu.get("visual_dna")
                            print(f"✨ Updated costume for '{cname}' in story_state.json!")
            else:
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
    parser.add_argument("--season", type=int, default=None, help="Season number (1 or 2)")
    parser.add_argument("--is_new_season", action="store_true", help="Flag to launch a new season")
    parser.add_argument("--premise", type=str, default="", help="Custom story idea or premise to guide generation")
    parser.add_argument("--gas_url", default=os.getenv("GAS_WEBHOOK_URL", ""), help="Google Apps Script Web App URL")
    args = parser.parse_args()

    # Determine season
    season_num = args.season
    if season_num is None:
        if os.path.exists("story_state.json"):
            try:
                with open("story_state.json", "r", encoding="utf-8") as f:
                    s_state = json.load(f)
                    season_num = s_state.get("season_number", 1)
            except Exception:
                season_num = 1
        else:
            season_num = 1

    is_new_season = args.is_new_season or (season_num > 1 and args.target_ep == 1)

    # Determine target episode and previous episode
    if is_new_season:
        target_ep = 1
        effective_current_ep = 0
    elif args.target_ep is not None:
        target_ep = args.target_ep
        effective_current_ep = target_ep - 1
    elif args.current_ep is not None:
        effective_current_ep = args.current_ep
        target_ep = effective_current_ep + 1
    else:
        detected_ep = 1
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
        if season_num == 1 and detected_ep >= 10:
            print("\n" + "="*70)
            print("🎯 SEASON 1 FINALE REACHED (Episode 10).")
            print("Automatic background advancement halted.")
            print("Please open Creator Portal to launch Season 2 via GitHub Actions!")
            print("="*70 + "\n")
            return
        effective_current_ep = detected_ep
        target_ep = effective_current_ep + 1

    # Resolve roadmap & storyline
    dynamic_arc_data = None
    season_title = ""
    season_arc = []
    character_updates = []
    new_characters = []
    cliffhanger_scene_state = None

    if is_new_season:
        print(f"\n🌟 Launching Season {season_num} with Dynamic Storyline Architect...")
        user_premise = args.premise or "Meeting the Families: Reenu's traditional parents visit Kochi unexpectedly, testing Sachin and Reenu's relationship with hilarious cultural clashes."
        dynamic_arc_data = generate_connected_season_arc(season_num, user_premise)
        season_title = dynamic_arc_data.get("season_title", f"Season {season_num}: Fort Kochi Days")
        season_arc = dynamic_arc_data.get("episodes", [])
        character_updates = dynamic_arc_data.get("character_updates", [])
        new_characters = dynamic_arc_data.get("new_characters", [])
        
        target_entry = season_arc[0] if season_arc else {}
        premise = target_entry.get("synopsis", user_premise)
        previous_story = f"Season {season_num - 1} Climax: Sachin cancelled his London visa and decided to stay in Kerala for love. Season {season_num} begins a new chapter in Kochi."
        cliffhanger = "A new beginning awaits in Kochi."

        # Build active character DNA map for new season
        active_dna_map = get_active_character_dna_map(season_num, character_updates=character_updates, new_characters=new_characters)
    else:
        active_dna_map = get_active_character_dna_map(season_num)
        # Check if story_state.json has a saved season_arc for this season
        saved_arc = None
        if os.path.exists("story_state.json"):
            try:
                with open("story_state.json", "r", encoding="utf-8") as f:
                    sstate = json.load(f)
                    saved_arc = sstate.get("season_arc")
                    season_title = sstate.get("season_title", "")
                    cliffhanger_scene_state = sstate.get("cliffhanger_scene_state")
                    for h in sstate.get("history", []):
                        if h.get("episode") == effective_current_ep:
                            previous_story = h.get("summary") or ""
                            cliffhanger = h.get("cliffhanger") or ""
            except Exception as e:
                print(f"Notice reading story_state.json: {e}")

        if saved_arc and isinstance(saved_arc, list) and len(saved_arc) >= target_ep:
            target_entry = saved_arc[target_ep - 1]
            season_arc = saved_arc
            premise = args.premise or target_entry.get("synopsis", "")
            prev_entry = saved_arc[effective_current_ep - 1] if effective_current_ep > 0 else {}
            previous_story = prev_entry.get("synopsis", "Season prologue.")
            cliffhanger = prev_entry.get("cliffhanger", "Prologue hook.")
        else:
            active_roadmap = SEASON_2_ROADMAP if season_num == 2 else SEASON_1_ROADMAP
            target_entry = active_roadmap.get(target_ep, {})
            premise = args.premise or target_entry.get("synopsis", "")
            prev_entry = active_roadmap.get(effective_current_ep, {})
            previous_story = prev_entry.get("synopsis", "Season prologue.")
            cliffhanger = prev_entry.get("cliffhanger", "Prologue ending.")

    print(f"Directing Season {season_num} Episode {target_ep} from Master Roadmap:")
    print(f"  Target: {target_entry.get('title_malayalam', '')} ({target_entry.get('title_english', '')})")
    print(f"  Premise: {premise}")

    # 1. Generate Episode Screenplay & Long Disney Pixar Prompts
    ep_data = generate_next_episode_screenplay(
        current_ep_num=effective_current_ep,
        season_number=season_num,
        previous_story=previous_story,
        cliffhanger=cliffhanger,
        next_ep_premise=premise,
        cliffhanger_scene_state=cliffhanger_scene_state,
        is_new_season=is_new_season,
        target_entry=target_entry,
        season_title=season_title,
        active_character_dna=active_dna_map
    )

    if is_new_season:
        ep_data["season_arc"] = season_arc
        ep_data["season_title"] = season_title
        ep_data["character_updates"] = character_updates
        ep_data["new_characters_introduced"] = new_characters
    else:
        if season_arc:
            ep_data["season_arc"] = season_arc
            ep_data["season_title"] = season_title
        if os.path.exists("story_state.json"):
            try:
                with open("story_state.json", "r", encoding="utf-8") as f:
                    st = json.load(f)
                    chars_in_state = st.get("characters", {})
                    ep_data["character_updates"] = [
                        {"name": k, "attire": v.get("attire", ""), "visual_dna": v.get("visual_dna", "")}
                        for k, v in chars_in_state.items() if k in ["Sachin", "Reenu", "Amal"]
                    ]
            except Exception:
                pass
        ep_data["season_title"] = season_title

    # 2. Update local files & portal website
    update_creator_portal(ep_data)

    # 3. Sync to Google Sheet (Sheets 1, 4, 2 updated, Sheet 3 untouched, Sheet 5 updated)
    sync_new_episode_to_google_sheet(args.gas_url, ep_data)

def generate_series_thumbnail_prompt(season_number=None, story_state=None):
    """
    Generates the exact series thumbnail prompt with locked layout placeholders
    and dynamic story situation & casual costumes for the active season.
    - Top-left: Title logo 'Sachin & Reenu' with crown and heart
    - Top-right: Taped note stickers for 'Season' and 'Episode' placeholders
    - Center/Foreground: Sachin & Reenu in the current season story setting & casual wardrobe
    """
    if story_state is None and os.path.exists("story_state.json"):
        try:
            with open("story_state.json", "r", encoding="utf-8") as f:
                story_state = json.load(f)
        except Exception:
            story_state = {}
    story_state = story_state or {}

    season_num = season_number or story_state.get("season_number", 2)
    season_title = story_state.get("season_title", f"Season {season_num}")
    
    # Resolve costumes
    chars = story_state.get("characters", {})
    sachin_attire = chars.get("Sachin", {}).get("attire")
    reenu_attire = chars.get("Reenu", {}).get("attire")

    if not sachin_attire or is_formal_attire(sachin_attire):
        sachin_attire = SEASON_2_CASUAL_ATTIRE.get("Sachin") if season_num == 2 else DEFAULT_ATTIRE_SACHIN
    if not reenu_attire or is_formal_attire(reenu_attire):
        reenu_attire = SEASON_2_CASUAL_ATTIRE.get("Reenu") if season_num == 2 else DEFAULT_ATTIRE_REENU

    # Determine setting from season arc or default
    if season_num == 1:
        setting_description = "Kochi CIAL airport arrival gates / Cochin city monsoon street with rain-washed ambience"
        action_description = "Sachin excitedly holding a vintage London travel pouch while Reenu stands joyfully beside him, laughing with affectionate eyes under a cozy shared umbrella."
    elif season_num == 2:
        setting_description = "Cozy Kakkanad apartment living room with warm golden afternoon sunlight streaming through the French balcony windows"
        action_description = "Sachin and Reenu are decorating with warm glowing multi-colored fairy lights, looking adorably at each other with beaming smiles and playful laughter."
    else:
        setting_description = f"Vibrant Kerala cinematic backdrop matching {season_title}"
        action_description = "Sachin and Reenu sharing an affectionate, romantic smile in the center of the scene, highlighting their charming chemistry."

    prompt_text = (
        f"High-end Disney Pixar 3D animated vertical 9:16 YouTube Shorts poster thumbnail for the romantic comedy series 'Sachin & Reenu'.\n\n"
        f"[LAYOUT & GRAPHIC BRANDING]:\n"
        f"- Top-Left: Stylized, playful 3D cartoon title logo with vibrant bubble typography reading 'Sachin & Reenu', featuring a tiny cartoon crown icon above the 'S' and a playful pink heart over the 'e'.\n"
        f"- Top-Right: Two paper note card stickers pinned with beige masking tape on corners in the exact same location:\n"
        f"  1. Top sticker banner labeled 'Season' in handwritten font with a blank cream rectangular note card directly below it.\n"
        f"  2. Bottom sticker banner labeled 'Episode' in handwritten font with a blank cream rectangular note card directly below it.\n"
        f"- Decorative playful floating white cartoon hearts and doodle lines around the couple.\n\n"
        f"[CHARACTERS & CURRENT STORY SCENE - {season_title}]:\n"
        f"- Setting: {setting_description}.\n"
        f"- Action: {action_description}\n"
        f"- Sachin Visuals & Costume: Stylized 3D Pixar character, 24yo Malayali boy, wavy dark hair, warm brown eyes, endearing smile. Wearing {sachin_attire}.\n"
        f"- Reenu Visuals & Costume: Stylized 3D Pixar character, 22yo Malayali girl, voluminous bouncy wavy dark-brown hair with curtain bangs, large expressive hazel-brown doe eyes, sweet dimpled cartoon smile. Wearing {reenu_attire}.\n\n"
        f"[LIGHTING & RENDER QUALITY]:\n"
        f"- Disney Pixar 3D animated movie render, soft velvety cartoon shaders, Octane 3D render, vertical 9:16 ratio, clean vibrant 4K resolution."
    )

    return {
        "season_number": season_num,
        "season_title": season_title,
        "thumbnail_prompt": prompt_text,
        "sachin_costume": sachin_attire,
        "reenu_costume": reenu_attire,
        "setting": setting_description
    }

if __name__ == "__main__":
    main()
