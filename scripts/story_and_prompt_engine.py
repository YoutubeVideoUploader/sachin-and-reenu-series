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

# Stylized 3D Cartoon Animation Character Visual DNA Constants (Strictly Young Adults / Adults, Never Boy/Girl/Child-like)
BASE_DNA_REENU = (
    "Reenu: Stylized 3D Pixar-style cartoon animation character, 22-year-old young adult South Indian Malayali woman, "
    "graceful defined adult female jawline, high elegant cheekbones with subtle warm blush, mature feminine facial structure (STRICTLY ADULT WOMAN, NEVER A GIRL OR CHILD), "
    "large sparkling expressive hazel-brown animated cartoon doe eyes with lush stylized eyelashes, natural refined feminine arched eyebrows, "
    "radiant warm genuine animated smile, voluminous bouncy wavy dark-brown cartoon hair with soft curtain bangs, "
    "elegant slender adult female proportions, natural adult posture with realistic adult head-to-body scale (STRICTLY YOUNG ADULT WOMAN, PROHIBIT GIRL/CHILD/TEEN/CHIBI ANATOMY, PROHIBIT REALISTIC HUMAN SKIN PORES)."
)
# Reenu's preference: Strictly casual T-shirt WITH EYE-CATCHING PATTERNS/PRINTS (clouds, florals, doodles, stripes) + denim skirt/jeans + sneakers + watch
DEFAULT_ATTIRE_REENU = "Pastel baby-blue and soft yellow cloud-pattern camouflage t-shirt, sky-blue denim skirt, white sneakers, silver wrist watch."

BASE_DNA_SACHIN = (
    "Sachin: Stylized 3D Pixar-style cartoon animation character, 24-year-old young adult South Indian Malayali man, "
    "handsome defined adult jawline, mature stylized Pixar adult male facial structure, light natural 5 o'clock stubble shadow along jawline and chin (STRICTLY ADULT MALE FACE, NEVER A BOY OR CHILD), "
    "large expressive warm animated dark-brown eyes, natural masculine eyebrows, confident genuine warm animated smile, "
    "stylized soft textured wavy dark cartoon hair with volume, tall lean athletic adult male build with broad shoulders and natural adult head-to-body scale "
    "(STRICTLY YOUNG ADULT MAN, PROHIBIT BOY/CHILD/TEEN/CHIBI ANATOMY, PROHIBIT REALISTIC HUMAN SKIN PORES)."
)
# Sachin's preference: Strictly casual PLAIN T-shirt (100% solid color, ZERO patterns, ZERO graphics) + casual denim jeans + sneakers + cross-bag
DEFAULT_ATTIRE_SACHIN = "Solid forest-green plain crewneck t-shirt (strictly zero patterns or graphics), classic dark blue denim jeans, white sneakers, brown leather travel cross-bag worn diagonally across chest."

BASE_DNA_AMAL = (
    "Amal: Stylized 3D Pixar-style cartoon animation character, 24-year-old young adult South Indian Malayali man, "
    "defined adult square jawline, neatly trimmed adult mustache and trim goatee beard, lively expressive animated dark-brown eyes, energetic witty friendly cartoon smile, "
    "neat stylized short cartoon hairstyle with clean faded sides, athletic adult male proportions with broad shoulders and natural adult head-to-body scale "
    "(STRICTLY YOUNG ADULT MAN, PROHIBIT BOY/CHILD/TEEN/CHIBI ANATOMY, PROHIBIT REALISTIC HUMAN SKIN PORES)."
)
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
    Enforces strict casuals for lead characters, prohibiting ethnic kurtis/sarees and formal shirts.
    """
    if "STRICTLY LOCKED ATTIRE" in physical_dna:
        return physical_dna
    p_dna = physical_dna.strip()
    if not p_dna.startswith(f"{name}:"):
        p_dna = f"{name}: {p_dna}"
    attire_clean = attire.strip().rstrip('.')
    anti_traditional = " (PROHIBIT ALL TRADITIONAL/ETHNIC WEAR: NO KURTIS, NO SAREES, NO FORMAL SHIRTS, NO FORMAL TROUSERS, NO DUPATTAS; STRICT MODERN CASUALS ONLY)" if name in ["Sachin", "Reenu", "Amal"] else ""
    return f"{p_dna} STRICTLY LOCKED ATTIRE{anti_traditional} (IDENTICAL IN EVERY SHOT): {attire_clean}. Absolutely zero costume variations."

DNA_REENU = format_character_visual_dna("Reenu", BASE_DNA_REENU, DEFAULT_ATTIRE_REENU)
DNA_SACHIN = format_character_visual_dna("Sachin", BASE_DNA_SACHIN, DEFAULT_ATTIRE_SACHIN)
DNA_AMAL = format_character_visual_dna("Amal", BASE_DNA_AMAL, DEFAULT_ATTIRE_AMAL)

DNA_MADHAVAN = (
    "Madhavan (Reenu's Father): Stylized 3D Pixar-style cartoon animation character, 52-year-old mature South Indian Malayali gentleman, "
    "dignified traditional Malayali father features, expressive salt-and-pepper mustache, warm yet stern dark eyes, "
    "slightly greying temples in dark curly hair, gentle grandfatherly warmth beneath traditional composure "
    "(STRICTLY 3D ANIMATION ADULT CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Crisp traditional Kerala cream-white cotton jubba worn over "
    "a traditional off-white kasavu mundu with thin golden border, black leather sandals, silver vintage wrist watch. "
    "Absolutely zero costume variations."
)

DNA_GIRIJA = (
    "Girija (Reenu's Mother): Stylized 3D Pixar-style cartoon animation character, 48-year-old mature South Indian Malayali lady, "
    "kind round motherly face, warm expressive dark-brown eyes, neat traditional hair bun adorned with fresh fragrant "
    "white jasmine flowers (mulla poo), endearing affectionate smile with cute cartoon dimple "
    "(STRICTLY 3D ANIMATION ADULT CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Elegant Kerala traditional cream cotton set-saree with "
    "emerald-green border, delicate gold necklace and small traditional jhumka earrings, gold bangles on right wrist. "
    "Absolutely zero costume variations."
)

NARRATOR_VOICE = "Consistent Third-Person Female Narrator: 22-24yo charming South Indian Malayalam female storyteller voice, warm expressive sweet melodic tone, gentle youthful evocative Malayalam cadence, clear acoustic studio warmth"

MASTER_STYLE = "High-end Disney Pixar 3D animated cartoon movie, stylized 3D cartoon character render, cute expressive animated features, soft smooth 3D cartoon shaders, vertical 9:16 format, Octane 3D render 4k 60fps"

MASTER_NEGATIVE_PROMPT = (
    "child, kid, toddler, baby, boy, girl, infant, chibi, teen, teenager, underage, adolescent, babyface, oversized head, baby cheeks, diminutive body proportions, doll, "
    "kurti, kurta, salwar, saree, dupatta, jhumka, jhumkas, ethnic Indian wear, traditional festive wear, formal collared shirt, button-up shirt, pleated trousers, formal pants, "
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

DNA_CARETAKER = (
    "Sreedharan (The Caretaker): Stylized 3D Pixar-style cartoon animation character, 65-year-old elderly South Indian Malayali man, "
    "weathered mature Pixar elderly face, distinguished thick expressive grey mustache, bushy grey eyebrows, deep mysterious observant unblinking cartoon eyes, "
    "slightly hunched dignified elderly build, thinning salt-and-pepper hair (STRICTLY 3D ANIMATION ELDERLY CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Traditional white Kerala cotton mundu and a faded grey cotton jubba with brown leather sandals. Absolutely zero costume variations."
)

DNA_SHOPKEEPER = (
    "Tea Shopkeeper: Stylized 3D Pixar-style cartoon animation character, 48-year-old middle-aged South Indian Malayali man, "
    "warm expressive weathered cartoon face, thick black-and-grey mustache, welcoming dark eyes, sturdy working adult build (STRICTLY 3D ANIMATION CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Faded blue cotton half-sleeve shirt and traditional checkered cotton lungi. Absolutely zero costume variations."
)

DNA_WOMAN_IN_MIST = (
    "Bhadra (The Woman in the Mist): Ethereal stylized 3D Pixar-style cartoon animation character, 28-year-old adult South Indian Malayali woman, "
    "enigmatic soft glowing animated eyes, haunting elegant adult female facial features, flowing dark wavy hair drifting like mountain mist, graceful floating adult posture (STRICTLY 3D ANIMATION CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Traditional white Kerala Set-Mundu with dull gold border, edges softly dissolving into misty fog. Absolutely zero costume variations."
)

DNA_REGISTRY = {
    "Reenu": DNA_REENU,
    "Sachin": DNA_SACHIN,
    "Amal": DNA_AMAL,
    "Madhavan": DNA_MADHAVAN,
    "Girija": DNA_GIRIJA,
    "Caretaker": DNA_CARETAKER,
    "Shopkeeper": DNA_SHOPKEEPER,
    "Bhadra": DNA_WOMAN_IN_MIST
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
            entry = register_new_character(nc)
            if entry:
                active_map[entry["name"]] = entry["visual_dna"]

    return active_map

def register_new_character(character_data, story_state_path="story_state.json"):
    """
    Registers a new character with strictly enforced adult/elderly physical specifications,
    preventing childlike or chibi generation. Updates story_state.json and DNA_REGISTRY.
    """
    if not character_data or not isinstance(character_data, dict):
        return None
    name = character_data.get("name")
    if not name:
        return None

    age = character_data.get("age", 24)
    gender = str(character_data.get("gender", "male")).lower()

    if age >= 55:
        age_group = "Elderly"
        adult_noun = "elderly gentleman" if gender == "male" else "elderly lady"
    elif age >= 35:
        age_group = "Middle-Aged"
        adult_noun = "middle-aged man" if gender == "male" else "middle-aged woman"
    else:
        age_group = "Young Adult"
        adult_noun = "young adult man" if gender == "male" else "young adult woman"

    raw_v_dna = character_data.get("visual_dna", "")
    sanitized_dna = raw_v_dna
    # Replace boy/girl terms with explicit adult descriptions
    sanitized_dna = re.sub(r'\b(boy|young boy)\b', f'{age}-year-old young adult man', sanitized_dna, flags=re.IGNORECASE)
    sanitized_dna = re.sub(r'\b(girl|young girl)\b', f'{age}-year-old young adult woman', sanitized_dna, flags=re.IGNORECASE)

    if not sanitized_dna or len(sanitized_dna) < 20:
        sanitized_dna = (
            f"{name}: Stylized 3D Pixar-style cartoon animation character, {age}-year-old {age_group.lower()} South Indian Malayali {adult_noun}, "
            f"defined adult facial structure, natural adult proportions (STRICTLY {age_group.upper()} ADULT CHARACTER, "
            f"PROHIBIT BOY/GIRL/CHILD/TEEN/CHIBI ANATOMY, PROHIBIT REALISTIC HUMAN SKIN PORES)."
        )
    elif "PROHIBIT" not in sanitized_dna:
        sanitized_dna += f" (STRICTLY {age_group.upper()} {adult_noun.upper()}, PROHIBIT BOY/GIRL/CHILD/TEEN/CHIBI ANATOMY, PROHIBIT REALISTIC HUMAN SKIN PORES)."

    attire = character_data.get("locked_attire") or character_data.get("attire", "Casual modern attire.")
    voice = character_data.get("voice") or character_data.get("voice_persona", "Expressive Malayalam voice")

    full_dna = format_character_visual_dna(name, sanitized_dna, attire)

    entry = {
        "name": name,
        "age": age,
        "age_group": age_group,
        "gender": gender,
        "role": character_data.get("role", "Character"),
        "height_build": character_data.get("height_build", "Natural adult proportions, head-to-body ratio 1:7.5, broad shoulders, strictly non-chibi"),
        "face": character_data.get("face", f"Defined mature adult facial structure, expressive Pixar animation features"),
        "hair": character_data.get("hair", "Stylized dark textured cartoon hair"),
        "attire": attire,
        "locked_attire": attire,
        "voice": voice,
        "voice_persona": voice,
        "visual_dna": full_dna
    }

    # Persist in story_state.json
    p = Path(story_state_path)
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                st = json.load(f)
            st.setdefault("characters", {})[name] = entry
            with open(p, "w", encoding="utf-8") as f:
                json.dump(st, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Notice saving character to state: {e}")

    DNA_REGISTRY[name] = full_dna
    return entry

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
    candidate_models = ["gemini-3.5-flash", "gemini-3-flash-preview", "gemini-3.1-flash-lite", "gemini-3.1-flash-lite-preview", "gemini-3.8-flash", "gemini-flash-latest"]

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
   - NEW CHARACTERS RULES (STRICTLY ADULT / ELDERLY SPECIFICATIONS):
     * Every newly created character MUST have full, mature physical specifications.
     * Age groups: 'Young Adult' (20-35), 'Middle-Aged' (36-55), or 'Elderly' (56+).
     * NEVER use the words 'boy' or 'girl' for adult characters. Use 'young adult man' or 'young adult woman'.
     * Specify defined adult facial structure (mature jawline, facial hair for adult men, elegant adult cheekbones for women).
     * Specify adult body proportions: 'Natural adult proportions, head-to-body ratio 1:7.5, broad shoulders, strictly non-chibi'.
     * Visual DNA MUST end with: (STRICTLY ADULT CHARACTER, PROHIBIT BOY/GIRL/CHILD/TEEN/CHIBI ANATOMY, PROHIBIT REALISTIC HUMAN SKIN PORES).
     * Traditional Kerala elderly parents wear traditional attire (mundu, jubba, saree). Younger friends or colleagues follow casuals.

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
                        max_output_tokens=32768
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
                err_s = str(e)
                print(f"  Attempt {attempt + 1} with {model_name} failed: {e}")
                if "503" in err_s or "UNAVAILABLE" in err_s:
                    time.sleep(4 * (attempt + 1))
                else:
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

def generate_next_episode_screenplay(current_ep_num, season_number=1, previous_story="", cliffhanger="", next_ep_premise="", cliffhanger_scene_state=None, is_new_season=False, target_entry=None, season_title="", active_character_dna=None, past_timeline_summary="", last_shot_details=None, upcoming_target_entry=None, season_climax_entry=None):
    """
    Calls Gemini to generate a captivating 1-minute next episode screenplay (10-11 shots)
    with locked character dress, strict lip-movement rules, female narrator, pure Malayalam dialogue,
    and rigorous sequence continuity (lighting, weather, spatial blocking, eyelines, persistent props, camera lens).
    Dynamically adheres to the Master Season Roadmap and inherits cliffhanger scene state for episode continuity.
    Enforces a strict two-way narrative bridge: connects back to previous episode, and actively sets up the upcoming episode!
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

    upcoming_title_en = upcoming_target_entry.get("title_english", f"Episode {next_ep_num + 1}") if upcoming_target_entry else ""
    upcoming_title_ml = upcoming_target_entry.get("title_malayalam", "") if upcoming_target_entry else ""
    upcoming_synopsis = upcoming_target_entry.get("synopsis", "") if upcoming_target_entry else ""
    climax_synopsis = season_climax_entry.get("synopsis", "") if season_climax_entry else ""

    future_bridge_block = ""
    if next_ep_num < 10 and upcoming_synopsis:
        future_bridge_block = f"""
===================================================================================
CRITICAL TWO-WAY NARRATIVE BRIDGE MANDATE (CONNECTING EPISODE {next_ep_num} -> EPISODE {next_ep_num + 1}):
===================================================================================
You are strictly engineering Episode {next_ep_num} as an intentional bridge between:
1. THE ORIGIN (Episode {current_ep_num} Ending):
   - You MUST pick up the narrative and emotional baton cleanly from Episode {current_ep_num}'s closing shot, setting, and dialogue.

2. THE UPCOMING DESTINATION (Episode {next_ep_num + 1} Target):
   - Upcoming Episode {next_ep_num + 1} Title: {upcoming_title_ml} ({upcoming_title_en})
   - Upcoming Episode {next_ep_num + 1} Premise: {upcoming_synopsis}
   - Season Finale Climax (Episode 10): {climax_synopsis}

MANDATORY SHOT 10 OUT-POINT RULE:
Shot 10's final dialogue, character reaction, and cliffhanger punchline MUST directly and deliberately ignite the premise of Episode {next_ep_num + 1}!
You are STRICTLY FORBIDDEN from ending arbitrarily or concluding the story in a way that breaks continuity with Episode {next_ep_num + 1}. The ending of Shot 10 MUST act as the direct narrative springboard into Episode {next_ep_num + 1}!
"""
    elif next_ep_num >= 10:
        future_bridge_block = f"""
===================================================================================
CRITICAL GRAND FINALE MANDATE (SEASON {season_number} CLIMAX - EPISODE 10):
===================================================================================
This is the DEFINITIVE SEASON FINALE (Episode 10)!
- Resolve all seasonal conflicts, family approvals, and romantic hurdles.
- Shot 10 MUST deliver a joyful, emotional, unforgettable Disney Pixar romantic climax for Sachin and Reenu!
"""

    print(f"\n=======================================================")
    print(f"✨ GEMINI AUTONOMOUS SCREENPLAY WRITER: SEASON {season_number} EPISODE {next_ep_num} (1-MINUTE REEL)")
    print(f"=======================================================")
    print(f"Target Title: {planned_title_ml} ({planned_title_en})")
    print(f"Previous Episode {current_ep_num} Summary: {previous_story[:100]}...")
    print(f"Target Narrative Beat: {effective_premise[:100]}...")
    if upcoming_synopsis:
        print(f"Upcoming Episode {next_ep_num + 1} Destination: {upcoming_synopsis[:100]}...")
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
    if last_shot_details:
        jp = last_shot_details.get("json_prompt") or {}
        sc = jp.get("sequence_continuity") or {}
        handoff_text = f"""
EXACT PREVIOUS EPISODE {current_ep_num} ENDING (SHOT 10 RECORD FROM GOOGLE SHEET):
- Action Summary: {last_shot_details.get('action_summary', '')}
- Spoken Dialogue: "{last_shot_details.get('dialogue_malayalam', '')}"
- Setting/Location: {jp.get('location', 'Scene Location')}
- Spatial Blocking: {json.dumps(sc.get('spatial_blocking', {}), ensure_ascii=False)}
- Persistent Hero Props: {', '.join(sc.get('persistent_props', []))}
"""
    elif cliffhanger_scene_state:
        handoff_text = f"""
CONTINUITY HANDOFF FROM PREVIOUS EPISODE {current_ep_num} ENDING SCENE:
The previous episode ended with the following physical scene continuity state:
{json.dumps(cliffhanger_scene_state, ensure_ascii=False, indent=2)}
CRITICAL HANDOFF RULE: If Episode {next_ep_num} Shot 1 begins in this continuous sequence/location, you MUST seamlessly inherit this exact scene_id, weather, lighting palette, character spatial blocking, and prop placement to guarantee 100% continuous multi-shot flow across episode boundaries!
"""

    past_timeline_block = f"\nMASTER STORY TIMELINE UP TO NOW (FROM TAB: PAST_EPISODES_PROMPTS):\n{past_timeline_summary}\n" if past_timeline_summary else ""

    prompt = f"""
Write the full screenplay and shot-by-shot Google Flow JSON prompts for Episode {next_ep_num} of 'Sachin & Reenu'.

MASTER ROADMAP GUIDANCE:
- Expected Episode Title: {planned_title_ml} ({planned_title_en})
- Target Premise / Narrative Beat: {effective_premise}
- Target Climax / Cliffhanger: {target_cliffhanger_guide}
{future_bridge_block}

{past_timeline_block}
CONTEXT FROM PREVIOUS EPISODE {current_ep_num}:
Story: {previous_story}
Cliffhanger: {cliffhanger}
Premise/Hook for Episode {next_ep_num}: {effective_premise}
{handoff_text}

CRITICAL CONTINUITY MANDATE (ABSOLUTELY NO EPISODE JUMPING):
Episode {next_ep_num} Shot 1 MUST start directly and seamlessly from the exact closing situation, location, and emotional state where Episode {current_ep_num} ended in Shot 10!
The story CANNOT jump forward abruptly in time or skip to an unrelated event without addressing and resolving the previous cliffhanger. Characters must react directly to what just occurred in Shot 10 before naturally evolving the scene forward!

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
          "script": "കൊച്ചിയിലെ ഒരു മനോഹരമായ ഞായറാഴ്ച ഉച്ച.",
          "line": "കൊച്ചിയിലെ ഒരു മനോഹരമായ ഞായറാഴ്ച ഉച്ച."
        }},
        "audio_directive": "EXTERNAL FEMALE VOICEOVER ONLY. The characters do NOT speak. Character lips remain completely closed with NO lip sync animation. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voiceover audio and natural ambient foley sound effects only."
      }}
    }}
  ]
}}
"""

    candidate_models = [
        "gemini-3.5-flash",
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite",
        "gemini-3.1-flash-lite-preview",
        "gemini-3.8-flash",
        "gemini-flash-latest"
    ]
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
                if repaired and isinstance(repaired, str):
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
                        max_output_tokens=65536
                    )
                )
                if response and response.text:
                    try:
                        clean_text = clean_json_text(response.text)
                        try:
                            parsed_data = json.loads(clean_text)
                        except Exception as pe:
                            if repair_json:
                                try:
                                    parsed_data = repair_json(response.text, return_objects=True)
                                except Exception:
                                    parsed_data = None
                            if not parsed_data:
                                raise pe

                        if isinstance(parsed_data, list):
                            parsed_data = {
                                "episode_number": next_ep_num,
                                "season_number": season_number,
                                "title_english": planned_title_en,
                                "title_malayalam": planned_title_ml,
                                "synopsis": effective_premise,
                                "cliffhanger": target_cliffhanger_guide,
                                "shots": parsed_data,
                                "total_shots": len(parsed_data)
                            }

                        if isinstance(parsed_data, dict) and "shots" in parsed_data and len(parsed_data["shots"]) >= 10:
                            break
                        else:
                            shot_cnt = len(parsed_data.get("shots", [])) if isinstance(parsed_data, dict) else 0
                            print(f"  Attempt {attempt + 1}: Model returned {shot_cnt} shots instead of required 10 shots. Retrying...")
                            parsed_data = None
                    except Exception as je:
                        print(f"  Attempt {attempt + 1} JSON parse error: {je}")
            except Exception as e:
                last_err = e
                err_s = str(e)
                print(f"  Attempt {attempt + 1} with {model_name} failed: {e}")
                if "503" in err_s or "UNAVAILABLE" in err_s:
                    time.sleep(5 * (attempt + 1))
                elif "429" in err_s or "RESOURCE_EXHAUSTED" in err_s:
                    time.sleep(10)
                else:
                    time.sleep(2)
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
    if isinstance(data, list):
        data = {"shots": data}
    elif not isinstance(data, dict):
        data = {}

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

        # 5. Guarantee dialogue script is real Malayalam text (never literal placeholder 'മലയാളം ലിപി')
        dlg = jp.get("dialogue", {})
        if isinstance(dlg, dict):
            ml_line = dlg.get("line") or s.get("dialogue_malayalam") or ""
            if dlg.get("script") == "മലയാളം ലിപി" or not dlg.get("script"):
                dlg["script"] = ml_line
            if ml_line and not dlg.get("line"):
                dlg["line"] = ml_line

        # 6. Normalize perspective to Prompt 1 benchmark
        persp = jp.get("perspective", "")
        if not persp or any(kw in persp.lower() for kw in ["shot", "lens", "close-up", "medium shot", "framing", "angle"]):
            jp["perspective"] = "Third-Person Narrator"

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

def reconcile_and_harmonize_season_arc(season_number, current_ep_num, current_ep_data, existing_arc=None, gas_url=None):
    """
    Evaluates the ground truth of what occurred in current_ep_num and dynamically reconciles
    the remaining roadmap (from current_ep_num + 1 to 10) so the story connects seamlessly
    and delivers a powerful, satisfying Season 10 finale.
    Synchronizes the updated arc to story_state.json and Google Sheet Tab 4 (Season_Story_Arc).
    """
    if current_ep_num >= 10:
        print(f"✓ Season {season_number} finale reached (Episode {current_ep_num}). No further arc harmonization needed.")
        return existing_arc or []

    client = get_gemini_client()
    candidate_models = [
        "gemini-3.5-flash",
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite",
        "gemini-3.1-flash-lite-preview",
        "gemini-3.8-flash",
        "gemini-flash-latest"
    ]

    fallback_map = SEASON_2_ROADMAP if season_number == 2 else (SEASON_1_ROADMAP if season_number == 1 else {})
    base_arc = []
    if existing_arc and isinstance(existing_arc, list) and len(existing_arc) >= 1:
        base_arc = [dict(x) for x in existing_arc]
    else:
        base_arc = [
            {
                "episode_number": idx,
                "title_english": info["title_english"],
                "title_malayalam": info["title_malayalam"],
                "status": "Completed" if idx < current_ep_num else ("Active" if idx == current_ep_num else "Upcoming"),
                "synopsis": info["synopsis"],
                "cliffhanger": info["cliffhanger"]
            }
            for idx, info in fallback_map.items()
        ]

    # Canonical completed history
    canonical_history = []
    for idx in range(1, current_ep_num + 1):
        if idx == current_ep_num:
            canonical_history.append({
                "episode_number": current_ep_num,
                "title_english": current_ep_data.get("title_english", f"Episode {current_ep_num}"),
                "title_malayalam": current_ep_data.get("title_malayalam", ""),
                "status": "Active",
                "synopsis": current_ep_data.get("synopsis", ""),
                "cliffhanger": current_ep_data.get("cliffhanger", "")
            })
        else:
            entry = next((x for x in base_arc if x.get("episode_number") == idx), None)
            if entry:
                entry["status"] = "Completed"
                canonical_history.append(entry)
            elif idx in fallback_map:
                fb = fallback_map[idx]
                canonical_history.append({
                    "episode_number": idx,
                    "title_english": fb["title_english"],
                    "title_malayalam": fb["title_malayalam"],
                    "status": "Completed",
                    "synopsis": fb["synopsis"],
                    "cliffhanger": fb["cliffhanger"]
                })

    remaining_start_ep = current_ep_num + 1
    remaining_existing = [x for x in base_arc if x.get("episode_number") >= remaining_start_ep]
    if not remaining_existing and fallback_map:
        remaining_existing = [
            {
                "episode_number": idx,
                "title_english": info["title_english"],
                "title_malayalam": info["title_malayalam"],
                "status": "Upcoming",
                "synopsis": info["synopsis"],
                "cliffhanger": info["cliffhanger"]
            }
            for idx, info in fallback_map.items() if idx >= remaining_start_ep
        ]

    history_str = "\n".join([
        f"Episode {e['episode_number']}: {e.get('title_malayalam', '')} ({e.get('title_english', '')})\n- Synopsis: {e.get('synopsis', '')}\n- Ending Cliffhanger: {e.get('cliffhanger', '')}"
        for e in canonical_history
    ])

    remaining_str = "\n".join([
        f"Episode {e['episode_number']}: {e.get('title_malayalam', '')} ({e.get('title_english', '')})\n- Planned Synopsis: {e.get('synopsis', '')}\n- Planned Cliffhanger: {e.get('cliffhanger', '')}"
        for e in remaining_existing
    ])

    prompt = f"""You are the Master Showrunner and Screenplay Writer for the viral Disney Pixar 3D animated Malayalam romantic series 'Sachin & Reenu' (സച്ചിൻ & റീനു).
SEASON {season_number} MASTER ROADMAP RE-HARMONIZATION

GROUND TRUTH CANONICAL HISTORY (EPISODES 1 TO {current_ep_num} ESTABLISHED):
{history_str}

MOST RECENT EPISODE {current_ep_num} GROUND TRUTH:
- Title: {current_ep_data.get('title_malayalam')} ({current_ep_data.get('title_english')})
- Synopsis: {current_ep_data.get('synopsis')}
- Ending Cliffhanger: {current_ep_data.get('cliffhanger')}

CURRENT REMAINING OUTLINE (EPISODES {remaining_start_ep} TO 10):
{remaining_str}

MISSION:
Re-harmonize and adapt the remaining upcoming episodes (from Episode {remaining_start_ep} to Episode 10 Climax).
CRITICAL RULES:
1. Episode {remaining_start_ep} MUST pick up directly and logically from Episode {current_ep_num}'s ending cliffhanger.
2. The remaining episodes must connect in an unbroken, believable cause-and-effect chain.
3. Episode 10 MUST be the grand emotional climax delivering a conclusive, happy resolution for Sachin & Reenu's relationship.
4. Output exactly {10 - current_ep_num} episodes (from {remaining_start_ep} to 10).

Output JSON matching this schema:
{{
  "season_title": "Season {season_number} Title",
  "episodes": [
    {{
      "episode_number": {remaining_start_ep},
      "title_english": "...",
      "title_malayalam": "...",
      "status": "Upcoming",
      "synopsis": "...",
      "cliffhanger": "..."
    }}
  ]
}}
"""

    system_instruction = (
        "You are the Showrunner and Head Screenplay Writer for 'Sachin & Reenu'."
        " Ensure tight narrative continuity leading to a definitive seasonal climax. Output ONLY valid JSON."
    )

    harmonized_remaining = None
    for model_name in candidate_models:
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.7,
                    max_output_tokens=32768
                )
            )
            if resp and resp.text:
                raw_text = resp.text.strip()
                if raw_text.startswith("```"):
                    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                    raw_text = re.sub(r"\s*```$", "", raw_text)
                try:
                    parsed = json.loads(raw_text)
                except Exception:
                    if repair_json:
                        parsed = repair_json(raw_text, return_objects=True)
                    else:
                        parsed = None
                if parsed and isinstance(parsed, dict) and "episodes" in parsed and len(parsed["episodes"]) > 0:
                    harmonized_remaining = parsed["episodes"]
                    break
        except Exception as e:
            print(f"Notice during arc harmonization with {model_name}: {e}")

    if not harmonized_remaining:
        print("Notice: Arc harmonization model unavailable, preserving existing outline.")
        harmonized_remaining = remaining_existing

    full_arc = list(canonical_history)
    for ep in harmonized_remaining:
        ep["status"] = "Upcoming"
        full_arc.append(ep)

    full_arc.sort(key=lambda x: x.get("episode_number", 0))

    if os.path.exists("story_state.json"):
        try:
            with open("story_state.json", "r", encoding="utf-8") as f:
                st = json.load(f)
            st["season_arc"] = full_arc
            with open("story_state.json", "w", encoding="utf-8") as f:
                json.dump(st, f, ensure_ascii=False, indent=2)
            print(f"✓ Synchronized harmonized Season {season_number} arc to story_state.json!")
        except Exception as e:
            print(f"Notice saving arc to story_state.json: {e}")

    target_gas = gas_url or os.getenv("GAS_WEBHOOK_URL")
    if target_gas:
        try:
            payload_arc = {
                "action": "update_season_story_arc",
                "season_number": season_number,
                "season_title": f"Season {season_number}: Continuous Story Arc",
                "episodes": full_arc
            }
            r = requests.post(target_gas, data=json.dumps(payload_arc), headers={"Content-Type": "text/plain"}, timeout=30)
            print(f"✓ Google Sheet Tab 4 [Season_Story_Arc] synchronized! (HTTP {r.status_code})")
        except Exception as e:
            print(f"Notice updating Sheet Tab 4: {e}")

    return full_arc

def generate_100_shot_season_outline(season_number, season_premise=None, gas_url=None):
    """
    Generates a master 100-shot screenplay beat sheet for the entire season (10 episodes x 10 shots).
    Lightweight, token-efficient, and structured in columns.
    Saves to:
    - season_{season_number}_shot_outline.json
    - Tab 7: Season_Shot_Outline via Google Apps Script
    - Tab 4: Season_Story_Arc via Google Apps Script
    """
    client = get_gemini_client()
    candidate_models = [
        "gemini-3.5-flash",
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite",
        "gemini-3.1-flash-lite-preview",
        "gemini-3.8-flash",
        "gemini-flash-latest"
    ]

    premise_text = season_premise or (
        "Sachin and Reenu start a vibrant new chapter in Kochi. Testing their love, "
        "managing unexpected family visits from Kurian and Annamma, and pursuing their dream heritage cafe."
    )

    prompt = f"""You are the Master Showrunner and Head Screenplay Writer for the viral Disney Pixar 3D animated Malayalam romantic series 'Sachin & Reenu' (സച്ചിൻ & റീനു).
SEASON {season_number} COMPLETE 100-SHOT MASTER SCREENPLAY BEAT SHEET

CORE SEASON PREMISE:
{premise_text}

CRITICAL ARCHITECTURE RULES:
1. OUTPUT EXACTLY 10 EPISODES (Episodes 1 to 10).
2. OUTPUT EXACTLY 10 SHOTS PER EPISODE (Shots 1 to 10 for each episode) = 100 SHOTS TOTAL.
3. Episode 1 Shot 1 sets the inciting incident and vibrant season kickoff.
4. Shot 10 of EVERY episode (Episodes 1 to 9) MUST be an intense, suspenseful cliffhanger or dramatic turning point.
5. Shot 1 of EVERY subsequent episode (Episodes 2 to 10) MUST seamlessly resolve and continue from the preceding episode's cliffhanger.
6. Episode 10 Shot 10 (Shot 100) MUST be the grand emotional season climax delivering a heartwarming, decisive relationship payoff for Sachin and Reenu.
7. Dialogue MUST be authentic conversational Malayalam phonetics in Malayalam script with natural emotion.
8. Visual Actions MUST describe character body language, comedic or tender expressions, and staging clearly.

OUTPUT STRICTLY VALID JSON MATCHING THIS EXACT SCHEMA:
{{
  "season_number": {season_number},
  "season_title": "Season {season_number}: Title in English (മലയാളം തലക്കെട്ട്)",
  "total_episodes": 10,
  "total_shots": 100,
  "episodes": [
    {{
      "episode_number": 1,
      "title_english": "...",
      "title_malayalam": "...",
      "synopsis": "Full episode summary...",
      "cliffhanger": "Ending cliffhanger...",
      "shots": [
        {{
          "shot_number": 1,
          "speaker": "Third-Person Narrator",
          "action": "...",
          "dialogue_malayalam": "...",
          "location": "Kakkanad apartment living room",
          "persistent_props": ["..."],
          "camera_hint": "Dynamic high-angle shot..."
        }}
      ]
    }}
  ]
}}
"""

    system_instruction = (
        "You are the Showrunner and Head Screenplay Writer for 'Sachin & Reenu'."
        " Write a master 100-shot screenplay beat sheet (10 episodes x 10 shots). Output ONLY valid JSON."
    )

    parsed_data = None
    for model_name in candidate_models:
        print(f"Generating 100-shot season outline with {model_name}...")
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.7,
                    max_output_tokens=65536
                )
            )
            if resp and resp.text:
                raw_text = resp.text.strip()
                if raw_text.startswith("```"):
                    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                    raw_text = re.sub(r"\s*```$", "", raw_text)
                try:
                    parsed_data = json.loads(raw_text)
                except Exception:
                    if repair_json:
                        parsed_data = repair_json(raw_text, return_objects=True)
                if parsed_data and isinstance(parsed_data, dict) and "episodes" in parsed_data:
                    break
        except Exception as e:
            print(f"Notice with {model_name}: {e}")

    if not parsed_data or "episodes" not in parsed_data:
        raise RuntimeError("Failed to generate 100-shot season outline with Gemini models.")

    episodes = parsed_data.get("episodes", [])
    season_title = parsed_data.get("season_title", f"Season {season_number}")

    flattened_shots = []
    arc_summaries = []
    for ep in episodes:
        ep_num = ep.get("episode_number", len(arc_summaries) + 1)
        t_en = ep.get("title_english", f"Episode {ep_num}")
        t_ml = ep.get("title_malayalam", "")
        arc_summaries.append({
            "season_number": season_number,
            "episode_number": ep_num,
            "title_english": t_en,
            "title_malayalam": t_ml,
            "status": "Active" if ep_num == 1 else "Upcoming",
            "synopsis": ep.get("synopsis", ""),
            "cliffhanger": ep.get("cliffhanger", "")
        })

        for s_idx, s in enumerate(ep.get("shots", []), start=1):
            raw_num = s.get("shot_number", s_idx)
            try:
                s_num = ((int(raw_num) - 1) % 10) + 1
            except Exception:
                s_num = s_idx
            s["shot_number"] = s_num
            flattened_shots.append({
                "season_number": season_number,
                "episode_number": ep_num,
                "shot_number": s_num,
                "episode_title": f"{t_ml} ({t_en})".strip(),
                "speaker": s.get("speaker", "Third-Person Narrator"),
                "action": s.get("action", ""),
                "dialogue_malayalam": s.get("dialogue_malayalam", ""),
                "location": s.get("location", "Kochi, Kerala"),
                "persistent_props": s.get("persistent_props", []),
                "camera_hint": s.get("camera_hint", "Dynamic cinematic shot"),
                "status": "Active" if ep_num == 1 else "Upcoming"
            })

    outline_payload = {
        "season_number": season_number,
        "season_title": season_title,
        "total_episodes": len(episodes),
        "total_shots": len(flattened_shots),
        "episodes": episodes,
        "flattened_shots": flattened_shots
    }

    out_fn = f"season_{season_number}_shot_outline.json"
    with open(out_fn, "w", encoding="utf-8") as f:
        json.dump(outline_payload, f, ensure_ascii=False, indent=2)
    print(f"✓ Saved 100-shot Master Screenplay Outline ({len(flattened_shots)} shots) to {out_fn}!")

    if os.path.exists("story_state.json"):
        try:
            with open("story_state.json", "r", encoding="utf-8") as f:
                st = json.load(f)
            st["season_shot_outline"] = outline_payload
            st["season_arc"] = arc_summaries
            st["season_title"] = season_title
            st["season_number"] = season_number
            with open("story_state.json", "w", encoding="utf-8") as f:
                json.dump(st, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Notice saving outline to story_state.json: {e}")

    target_gas = gas_url or os.getenv("GAS_WEBHOOK_URL")
    if target_gas:
        try:
            # 1. Update Tab 7: Season_Shot_Outline (100 shots)
            p7 = {
                "action": "save_season_shot_outline",
                "season_number": season_number,
                "season_title": season_title,
                "shots": flattened_shots
            }
            r7 = requests.post(target_gas, data=json.dumps(p7), headers={"Content-Type": "text/plain"}, timeout=45)
            print(f"✓ Google Sheet Tab 7 [Season_Shot_Outline] updated with {len(flattened_shots)} shots! (HTTP {r7.status_code})")

            # 2. Update Tab 4: Season_Story_Arc
            p4 = {
                "action": "update_season_story_arc",
                "season_number": season_number,
                "season_title": season_title,
                "episodes": arc_summaries
            }
            r4 = requests.post(target_gas, data=json.dumps(p4), headers={"Content-Type": "text/plain"}, timeout=30)
            print(f"✓ Google Sheet Tab 4 [Season_Story_Arc] synchronized! (HTTP {r4.status_code})")
        except Exception as e:
            print(f"Notice syncing outline to Sheet: {e}")

    return outline_payload

def compile_episode_prompts_from_outline(season_number, target_ep, outline_file=None, gas_url=None):
    """
    Pulls the 10 shots of target_ep from the 100-shot beat sheet and programmatically
    compiles them into full 10-key Disney Pixar Google Flow JSON prompts.
    """
    fn = outline_file or f"season_{season_number}_shot_outline.json"
    if not os.path.exists(fn):
        if os.path.exists("story_state.json"):
            try:
                with open("story_state.json", "r", encoding="utf-8") as f:
                    st = json.load(f)
                    if "season_shot_outline" in st:
                        fn = "story_state.json"
            except Exception:
                pass

    outline_data = {}
    if not os.path.exists(fn):
        print(f"Outline file {fn} not found. Attempting to generate fresh 100-shot outline first...")
        try:
            generate_100_shot_season_outline(season_number, gas_url=gas_url)
            fn = f"season_{season_number}_shot_outline.json"
        except Exception as e:
            print(f"Notice generating outline: {e}. Falling back to existing roadmap.")

    if os.path.exists(fn):
        with open(fn, "r", encoding="utf-8") as f:
            data = json.load(f)
        outline_data = data.get("season_shot_outline", data) if "season_shot_outline" in data else data

    episodes = outline_data.get("episodes", [])
    target_ep_obj = next((e for e in episodes if e.get("episode_number") == target_ep), None)

    if not target_ep_obj:
        flat = outline_data.get("flattened_shots", [])
        ep_shots = [s for s in flat if s.get("episode_number") == target_ep]
        if not ep_shots:
            fb_roadmap = SEASON_2_ROADMAP if season_number == 2 else SEASON_1_ROADMAP
            fb_entry = fb_roadmap.get(target_ep, {})
            ep_shots = [
                {
                    "shot_number": i,
                    "speaker": "Third-Person Narrator",
                    "action": f"{fb_entry.get('synopsis', 'Story beat')}. Shot {i}.",
                    "dialogue_malayalam": "കൊച്ചിയിലെ മനോഹരമായ നിമിഷം.",
                    "location": "Kakkanad apartment living room",
                    "persistent_props": ["Sachin's cross-bag", "Reenu's silver wrist watch"],
                    "camera_hint": "Dynamic cinematic medium shot"
                }
                for i in range(1, 11)
            ]
        target_ep_obj = {
            "episode_number": target_ep,
            "title_english": f"Episode {target_ep}",
            "title_malayalam": "",
            "synopsis": f"Episode {target_ep} narrative.",
            "cliffhanger": "",
            "shots": ep_shots
        }

    raw_shots = target_ep_obj.get("shots", [])
    active_dna_map = get_active_character_dna_map(season_number)

    known_chars = ["Sachin", "Reenu", "Renu", "Amal", "Caretaker", "Shopkeeper", "Kurian", "Annamma", "Madhavan", "Girija", "Broker Shaji", "Varghese"]
    compiled_shots = []

    for idx, s in enumerate(raw_shots, start=1):
        s_action = s.get("action", "")
        s_speaker = s.get("speaker", "Third-Person Narrator")
        s_diag = s.get("dialogue_malayalam") or s.get("dialogue") or ""
        s_loc = s.get("location", "Kochi, Kerala")
        s_camera = s.get("camera_hint") or s.get("camera") or "Dynamic cinematic 3D medium shot"

        # Detect characters present
        present_names = []
        action_lower = s_action.lower()
        speaker_lower = s_speaker.lower()

        if "sachin" in action_lower or "sachin" in speaker_lower:
            present_names.append("Sachin")
        if "renu" in action_lower or "reenu" in action_lower or "renu" in speaker_lower or "reenu" in speaker_lower:
            present_names.append("Reenu")
        if "amal" in action_lower or "amal" in speaker_lower:
            present_names.append("Amal")
        if "caretaker" in action_lower or "caretaker" in speaker_lower:
            present_names.append("Caretaker")
        if "shopkeeper" in action_lower or "shopkeeper" in speaker_lower:
            present_names.append("Shopkeeper")

        for c in ["Kurian", "Annamma", "Madhavan", "Girija", "Broker Shaji", "Varghese"]:
            if c.lower() in action_lower or c.lower() in speaker_lower:
                if c not in present_names:
                    present_names.append(c)

        if not present_names:
            present_names = ["Sachin", "Reenu"]

        characters_present = []
        blocking = {}
        loc_upper = s_loc.upper()
        # Contextual spatial blocking and eyeline direction
        eyeline = "Characters looking attentively toward scene focal action"
        if "CAR" in loc_upper:
            for c in present_names:
                if c == "Amal":
                    blocking["Amal"] = "Driver seat, hands on steering wheel / checking phone GPS"
                elif c == "Sachin":
                    blocking["Sachin"] = "Front passenger seat, leaning forward with itinerary / looking ahead"
                elif c == "Reenu":
                    blocking["Reenu"] = "Rear passenger seat, looking out through misty car window"
                else:
                    blocking[c] = "Inside car reacting to journey"
            if "Amal" in present_names and "Sachin" in present_names:
                eyeline = "Amal and Sachin exchanging glances over the route, Reenu looking out misty window"
        elif "LIVING" in loc_upper:
            for c in present_names:
                if c == "Sachin":
                    blocking["Sachin"] = "Screen-center holding travel map / itinerary excitedly"
                elif c == "Reenu":
                    blocking["Reenu"] = "Screen-left reacting with surprise and warm smile"
                elif c == "Amal":
                    blocking["Amal"] = "Screen-right doorway entering holding car keys with comedic annoyed expression"
                else:
                    blocking[c] = "Screen-center reacting to conversation"
            eyeline = "Characters actively looking at each other during animated conversation"
        elif "BEDROOM" in loc_upper:
            for c in present_names:
                if c == "Sachin":
                    blocking["Sachin"] = "Screen-center packing suitcase with flower bouquet"
                elif c == "Reenu":
                    blocking["Reenu"] = "Screen-left doorway watching affectionately"
                else:
                    blocking[c] = "In room reacting"
            eyeline = "Sachin looking smiling at flower bouquet and suitcase"
        else:
            for b_idx, c in enumerate(present_names):
                pos = ["Screen-center", "Screen-left", "Screen-right", "Background"][b_idx % 4]
                blocking[c] = f"{pos} reacting expressively to scene action"

        for c in present_names:
            if c == "Caretaker":
                c_dna = DNA_CARETAKER
            elif c == "Shopkeeper":
                c_dna = DNA_SHOPKEEPER
            else:
                c_dna = active_dna_map.get(c, DNA_REGISTRY.get(c, f"{c}: Stylized 3D Pixar character"))
            characters_present.append({"name": c, "visual_dna": c_dna})

        scene_clean_loc = re.sub(r'[^A-Za-z0-9]+', '_', s_loc).upper()[:22]
        
        if season_number == 3:
            if any(k in loc_upper for k in ["ROAD", "CAR", "MOUNTAIN", "PLANTATION", "TEA"]):
                time_of_day = "Late Afternoon Misty Mountain Atmosphere"
                weather = "Cool misty high-range fog drifting through pine trees"
                lighting = "Diffused cinematic mountain daylight through cool high-range fog"
            elif any(k in loc_upper for k in ["HOMESTAY", "LOCKED ROOM", "FACTORY", "BRIDGE", "HALLWAY"]):
                time_of_day = "Eerie Chilly High-Range Dusk"
                weather = "Misty drafts filtering through window slats"
                lighting = "Moody atmospheric amber lampglow with deep cinematic shadows"
            else:
                time_of_day = "Warm Ambient Indoor Daytime"
                weather = "Calm interior ambiance"
                lighting = "Soft warm domestic ambient lighting with cozy room tones"
        else:
            time_of_day = "Late Afternoon Monsoon Dusk"
            weather = "Continuous Kochi monsoon drizzle with soft humid atmosphere"
            lighting = "Soft natural overcast exterior daylight with warm interior amber glow"

        # Expand persistent props
        raw_props = s.get("persistent_props") or []
        expanded_props = []
        for p in raw_props:
            p_low = p.lower()
            if "map" in p_low:
                expanded_props.append("Sachin's unfolded travel map")
            elif "suitcase" in p_low:
                expanded_props.append("Open travel suitcase")
            elif "itinerary" in p_low:
                expanded_props.append("Romantic Munnar travel itinerary sheet in Sachin's hand")
            elif "key" in p_low:
                expanded_props.append("Set of car keys in Amal's hand")
            elif "flower" in p_low or "bouquet" in p_low:
                expanded_props.append("Fresh flower bouquet in Sachin's hand")
            elif "phone" in p_low or "smart" in p_low:
                expanded_props.append("Amal's smartphone running GPS navigation app")
            elif "steer" in p_low:
                expanded_props.append("Car steering wheel")
            elif "window" in p_low:
                expanded_props.append("Misty car passenger window with water droplets")
            elif "car" in p_low:
                expanded_props.append("Car interior dashboard")
            elif "photo" in p_low:
                expanded_props.append("Mysterious vintage photograph")
            else:
                expanded_props.append(p)
        if "Sachin" in present_names and "Sachin's brown leather cross-bag" not in expanded_props:
            expanded_props.append("Sachin's brown leather cross-bag")
        if "Reenu" in present_names and "Reenu's silver wrist watch" not in expanded_props:
            expanded_props.append("Reenu's silver wrist watch")

        seq_cont = {
            "scene_id": f"SCENE_{scene_clean_loc}",
            "time_of_day": time_of_day,
            "lighting_palette": lighting,
            "weather": weather,
            "spatial_blocking": blocking,
            "eyeline_direction": eyeline,
            "persistent_props": expanded_props,
            "camera_lens": "Cinematic prime lens, shallow depth of field, soft circular bokeh"
        }

        speaker_display = s_speaker.strip()
        if speaker_display.lower() in ["renu", "reenu"]:
            speaker_display = "Reenu"

        is_narrator = speaker_display.lower() in ["narrator", "third-person narrator", "third person narrator", "voiceover", "voice-over"]

        if is_narrator:
            speaker_name = "Off-Screen Third-Person Narrator (Voiceover Only - Characters Do Not Speak)"
            voice_p = "Consistent Third-Person Female Narrator: 22-24yo charming South Indian Malayalam female storyteller voice, warm expressive sweet melodic tone, gentle youthful evocative Malayalam cadence, clear acoustic studio warmth (Gemini Voice 'Kore' / Edge-TTS 'ml-IN-SobhanaNeural')"
            perspective = "Third-Person Narrator"
            action_text = f"{s_action.strip()} PURE VISUAL SCENE ACTION. All characters on screen are completely silent with lips firmly closed and relaxed. Absolutely NO character speaking, lip movement, or mouth animation."
            audio_text = (
                "OFF-SCREEN FEMALE STORYTELLER VOICEOVER ONLY. NO CHARACTER SPEAKS ON SCREEN. "
                "All characters maintain strictly closed lips with zero talking or mouth animation. "
                "CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. "
                "Clean voiceover audio and natural ambient foley sound effects only."
            )
        else:
            speaker_name = speaker_display
            perspective = f"Character Dialogue ({speaker_display} Speaking)"
            if speaker_display == "Sachin":
                voice_p = "Sachin: 24yo charming South Indian Malayali boy, endearing boyish expressive voice, warm Malayalam cadence (Gemini Voice 'Fenrir' / Edge-TTS 'ml-IN-MidhunNeural')"
            elif speaker_display == "Reenu":
                voice_p = "Reenu: 22yo South Indian Malayali girl, sweet expressive warm feminine Malayalam voice (Gemini Voice 'Kore' / Edge-TTS 'ml-IN-SobhanaNeural')"
            elif speaker_display == "Amal":
                voice_p = "Amal: 24yo witty relatable Malayali friend voice, comedic energetic Malayalam tone (Gemini Voice 'Puck' / Edge-TTS 'ml-IN-MidhunNeural')"
            elif speaker_display == "Shopkeeper":
                voice_p = "Tea Shopkeeper: Local Malayali tea vendor, cautionary rustic high-range tone"
            elif speaker_display == "Caretaker":
                voice_p = "Sreedharan (The Caretaker): Deep raspy mysterious high-range Malayalam tone (Central Travancore / Idukki dialect)"
            else:
                voice_p = f"{speaker_display}: Native Malayalam expressive character voice"

            action_text = f"{s_action.strip()} {speaker_display} actively speaks their dialogue on screen with natural animated lip movement, authentic facial expressions, and speech sync. Other characters present listen and react expressively."
            audio_text = (
                f"CHARACTER DIALOGUE SPOKEN BY {speaker_display.upper()} ON SCREEN. "
                f"{speaker_display} speaks directly with clear character voice and synchronized animated lip movement. "
                "CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. "
                "Clean character dialogue and natural ambient foley sound effects only."
            )

        json_prompt = {
            "style": MASTER_STYLE,
            "duration": "6s",
            "perspective": perspective,
            "characters_present": characters_present,
            "sequence_continuity": seq_cont,
            "location": s_loc,
            "camera": s_camera,
            "action": action_text,
            "dialogue": {
                "speaker": speaker_name,
                "voice_persona": voice_p,
                "language": "Malayalam",
                "script": s_diag,
                "line": s_diag
            },
            "audio_directive": audio_text
        }

        compiled_shots.append({
            "shot_number": idx,
            "duration": "6s",
            "duration_seconds": 6,
            "character": speaker_display,
            "dialogue_malayalam": s_diag,
            "action_summary": s_action,
            "json_prompt": json_prompt
        })

    is_new = (target_ep == 1 and season_number > 1)
    ep_data = {
        "episode_number": target_ep,
        "season_number": season_number,
        "is_new_season": is_new,
        "season_title": outline_data.get("season_title", f"Season {season_number}"),
        "title_english": target_ep_obj.get("title_english", f"Episode {target_ep}"),
        "title_malayalam": target_ep_obj.get("title_malayalam", ""),
        "synopsis": target_ep_obj.get("synopsis", ""),
        "cliffhanger": target_ep_obj.get("cliffhanger", ""),
        "total_shots": len(compiled_shots),
        "calculated_total_seconds": len(compiled_shots) * 6,
        "calculated_runtime_display": f"{len(compiled_shots) * 6 // 60}m {len(compiled_shots) * 6 % 60:02d}s",
        "shots": compiled_shots
    }

    # Save to disk
    with open("current_episode_shots.json", "w", encoding="utf-8") as f:
        json.dump(ep_data, f, ensure_ascii=False, indent=2)
    print(f"[SUCCESS] Compiled {len(compiled_shots)} Disney Pixar JSON prompts for Season {season_number} Episode {target_ep} into current_episode_shots.json!")

    # Update story_state.json
    if os.path.exists("story_state.json"):
        try:
            with open("story_state.json", "r", encoding="utf-8") as f:
                s_state = json.load(f)
            s_state["episode_number"] = target_ep
            s_state["season_number"] = season_number
            s_state["season_title"] = ep_data["season_title"]
            s_state["current_arc"] = ep_data["synopsis"]
            s_state["cliffhanger"] = ep_data["cliffhanger"]
            with open("story_state.json", "w", encoding="utf-8") as f:
                json.dump(s_state, f, ensure_ascii=False, indent=2)
            print(f"[SUCCESS] Updated story_state.json to Season {season_number} Episode {target_ep}!")
        except Exception as e:
            print(f"Notice updating story_state.json: {e}")

    # Update creator portal
    update_creator_portal(ep_data)

    # Sync to Google Sheet (Tab 2, Tab 1)
    target_gas = gas_url or os.getenv("GAS_WEBHOOK_URL")
    if target_gas:
        sync_new_episode_to_google_sheet(target_gas, ep_data)

    return ep_data

def reharmonize_outline_from_pivot(season_number, pivot_ep, pivot_shot, new_action, new_dialogue, outline_file=None, gas_url=None):
    """
    Ripples a story change at (pivot_ep, pivot_shot) through all subsequent shots
    up to Episode 10 Climax so the entire season remains causally unbroken.
    """
    fn = outline_file or f"season_{season_number}_shot_outline.json"
    if not os.path.exists(fn):
        raise FileNotFoundError(f"Master outline {fn} not found.")

    with open(fn, "r", encoding="utf-8") as f:
        data = json.load(f)

    flat_shots = data.get("flattened_shots", [])
    # Normalize existing shot numbers
    for s in flat_shots:
        try:
            raw_s = int(s.get("shot_number", 1))
            s["shot_number"] = ((raw_s - 1) % 10) + 1
        except Exception:
            pass

    pivot_idx = -1
    for i, s in enumerate(flat_shots):
        try:
            s_ep = int(s.get("episode_number", 0))
            s_shot = int(s.get("shot_number", 0))
        except Exception:
            continue
        if s_ep == pivot_ep and s_shot == pivot_shot:
            pivot_idx = i
            break

    if pivot_idx == -1:
        raise ValueError(f"Shot (Ep {pivot_ep}, Shot {pivot_shot}) not found in outline.")

    # Apply pivot edit
    flat_shots[pivot_idx]["action"] = new_action
    flat_shots[pivot_idx]["dialogue_malayalam"] = new_dialogue

    locked_history = flat_shots[:pivot_idx + 1]
    subsequent_shots = flat_shots[pivot_idx + 1:]

    if not subsequent_shots:
        print("Pivot shot is the final shot of the season. No subsequent shots to re-harmonize.")
        with open(fn, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return data

    client = get_gemini_client()
    candidate_models = [
        "gemini-3.5-flash",
        "gemini-3-flash-preview",
        "gemini-3.1-flash-lite",
        "gemini-3.1-flash-lite-preview",
        "gemini-3.8-flash",
        "gemini-flash-latest"
    ]

    history_summary = "\n".join([
        f"[Ep {s['episode_number']} Shot {s['shot_number']}]: {s['action']} | Line: '{s['dialogue_malayalam']}'"
        for s in locked_history[-10:] # last 10 established shots
    ])

    subsequent_summary = "\n".join([
        f"[Ep {s['episode_number']} Shot {s['shot_number']}]: {s['action']} | Line: '{s['dialogue_malayalam']}'"
        for s in subsequent_shots
    ])

    prompt = f"""You are the Master Showrunner for 'Sachin & Reenu' (Season {season_number}).
A major story change occurred at Episode {pivot_ep} Shot {pivot_shot}:
- New Action: {new_action}
- New Dialogue: {new_dialogue}

RECENT ESTABLISHED HISTORY LEADING UP TO THIS PIVOT:
{history_summary}

PLANNED SUBSEQUENT SHOTS THAT NEED RE-HARMONIZATION ({len(subsequent_shots)} shots):
{subsequent_summary}

MISSION:
Adapt and re-harmonize all {len(subsequent_shots)} subsequent shots so that they logically flow from the new pivot event.
- Maintain unbroken cause-and-effect.
- Shot 10 of every episode must remain a strong cliffhanger.
- Episode 10 Shot 10 MUST deliver the definitive happy emotional climax.
- Output exactly {len(subsequent_shots)} shots in JSON:
{{
  "shots": [
    {{
      "episode_number": {subsequent_shots[0]['episode_number']},
      "shot_number": {subsequent_shots[0]['shot_number']},
      "action": "...",
      "dialogue_malayalam": "..."
    }}
  ]
}}
"""

    system_instruction = "Adapt subsequent screenplay shots to preserve narrative continuity following a pivot change. Output ONLY valid JSON."
    harmonized = None

    for model_name in candidate_models:
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.7,
                    max_output_tokens=32768
                )
            )
            if resp and resp.text:
                raw_text = resp.text.strip()
                if raw_text.startswith("```"):
                    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
                    raw_text = re.sub(r"\s*```$", "", raw_text)
                try:
                    p = json.loads(raw_text)
                except Exception:
                    p = repair_json(raw_text, return_objects=True) if repair_json else None
                if p and isinstance(p, dict) and "shots" in p and len(p["shots"]) > 0:
                    harmonized = p["shots"]
                    break
        except Exception as e:
            print(f"Notice during pivot re-harmonization with {model_name}: {e}")

    if harmonized:
        for idx, new_s in enumerate(harmonized):
            target_idx = pivot_idx + 1 + idx
            if target_idx < len(flat_shots):
                flat_shots[target_idx]["action"] = new_s.get("action", flat_shots[target_idx]["action"])
                flat_shots[target_idx]["dialogue_malayalam"] = new_s.get("dialogue_malayalam", flat_shots[target_idx]["dialogue_malayalam"])

    data["flattened_shots"] = flat_shots
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✓ Re-harmonized {len(subsequent_shots)} subsequent shots following pivot at Ep {pivot_ep} Shot {pivot_shot}!")

    target_gas = gas_url or os.getenv("GAS_WEBHOOK_URL")
    if target_gas:
        try:
            payload_shots = {
                "action": "save_season_shot_outline",
                "season_number": season_number,
                "season_title": data.get("season_title", f"Season {season_number}"),
                "shots": flat_shots
            }
            r = requests.post(target_gas, data=json.dumps(payload_shots), headers={"Content-Type": "text/plain"}, timeout=45)
            print(f"✓ Google Sheet Tab 7 updated after pivot re-harmonization! (HTTP {r.status_code})")
        except Exception as e:
            print(f"Notice updating Sheet after pivot: {e}")

    return data

def main():
    parser = argparse.ArgumentParser(description="Generate Next Episode Screenplay & Prompts")
    parser.add_argument("--current_ep", type=int, default=None, help="Completed episode number")
    parser.add_argument("--target_ep", type=int, default=None, help="Explicit target episode number to generate")
    parser.add_argument("--season", type=int, default=None, help="Season number (1 or 2)")
    parser.add_argument("--is_new_season", action="store_true", help="Flag to launch a new season")
    parser.add_argument("--premise", type=str, default="", help="Custom story idea or premise to guide generation")
    parser.add_argument("--gas_url", default=os.getenv("GAS_WEBHOOK_URL", ""), help="Google Apps Script Web App URL")
    parser.add_argument("--mode", type=str, default="auto", choices=["auto", "generate_100_outline", "compile_episode", "reharmonize_outline"], help="Operation mode")
    parser.add_argument("--pivot_ep", type=int, default=None, help="Pivot episode for re-harmonization")
    parser.add_argument("--pivot_shot", type=int, default=None, help="Pivot shot for re-harmonization")
    parser.add_argument("--new_action", type=str, default="", help="Updated action text for pivot shot")
    parser.add_argument("--new_dialogue", type=str, default="", help="Updated dialogue text for pivot shot")
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

    # Route based on explicit mode
    if args.mode == "generate_100_outline":
        print(f"\n🌟 Launching 100-Shot Master Screenplay Beat Sheet Generator for Season {season_num}...")
        outline = generate_100_shot_season_outline(season_num, args.premise, gas_url=args.gas_url)
        print(f"\n✨ Compiling Episode 1 prompts from the new 100-shot outline...")
        compile_episode_prompts_from_outline(season_num, 1, gas_url=args.gas_url)
        return

    if args.mode == "compile_episode":
        target = args.target_ep or 1
        print(f"\n✨ Compiling Episode {target} prompts from Master 100-Shot Outline...")
        compile_episode_prompts_from_outline(season_num, target, gas_url=args.gas_url)
        return

    if args.mode == "reharmonize_outline":
        p_ep = args.pivot_ep or 1
        p_shot = args.pivot_shot or 1
        print(f"\n⚡ Re-harmonizing 100-Shot Outline from pivot Season {season_num} Ep {p_ep} Shot {p_shot}...")
        reharmonize_outline_from_pivot(season_num, p_ep, p_shot, args.new_action, args.new_dialogue, gas_url=args.gas_url)
        return

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
        if detected_ep >= 10:
            print("\n" + "="*70)
            print(f"🎯 SEASON {season_num} FINALE REACHED (Episode 10).")
            print("Automatic background advancement halted.")
            print(f"Please open Creator Portal to launch Season {season_num + 1} via GitHub Actions!")
            print("="*70 + "\n")
            return
        effective_current_ep = detected_ep
        target_ep = effective_current_ep + 1

    if target_ep > 10:
        print(f"\n⚠️ Target episode {target_ep} exceeds season limit (10 episodes per season). Halting.")
        return

    # Check if a Master 100-Shot Outline exists for this season (on disk or in story_state)
    outline_fn = f"season_{season_num}_shot_outline.json"
    outline_available = os.path.exists(outline_fn)
    if not outline_available and os.path.exists("story_state.json"):
        try:
            with open("story_state.json", "r", encoding="utf-8") as f:
                s_st = json.load(f)
                if "season_shot_outline" in s_st and s_st.get("season_number") == season_num:
                    outline_available = True
        except Exception:
            pass

    if outline_available:
        print(f"\n[INFO] Master 100-Shot Screenplay Outline detected for Season {season_num}!")
        print(f"[INFO] Compiling Episode {target_ep} prompts strictly from Tab 7 Master Outline...")
        ep_data = compile_episode_prompts_from_outline(season_num, target_ep, gas_url=args.gas_url)
        return

    # Resolve roadmap & storyline
    active_roadmap = SEASON_2_ROADMAP if season_num == 2 else SEASON_1_ROADMAP
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

        # Also auto-generate the 100-shot master outline for Tab 7 (Season_Shot_Outline)
        try:
            print(f"\n🎬 Generating 100-Shot Master Screenplay Beat Sheet for Season {season_num}...")
            generate_100_shot_season_outline(season_num, user_premise, gas_url=args.gas_url)
            print(f"✓ 100-Shot Beat Sheet created and synced to Google Sheet Tab 7 [Season_Shot_Outline]!")
            print(f"\n✨ Compiling Season {season_num} Episode 1 prompts strictly from Tab 7 Master Outline...")
            ep_data = compile_episode_prompts_from_outline(season_num, 1, gas_url=args.gas_url)
            return
        except Exception as e:
            print(f"Notice generating 100-shot outline: {e}")

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

    past_timeline_summary = ""
    last_shot_details = None
    gas_target_url = args.gas_url or os.getenv("GAS_WEBHOOK_URL")
    if gas_target_url and not is_new_season and effective_current_ep >= 1:
        try:
            print(f"Fetching master past episodes prompts from Google Sheet ({gas_target_url})...")
            res_past = requests.get(f"{gas_target_url}?action=get_past_prompts&episode={target_ep}", timeout=25)
            if res_past.status_code == 200:
                p_data = res_past.json()
                if p_data.get("success"):
                    past_timeline_summary = p_data.get("timeline_summary", "")
                    last_shot_details = p_data.get("last_shot")
                    if last_shot_details:
                        jp = last_shot_details.get("json_prompt")
                        if isinstance(jp, dict) and "sequence_continuity" in jp:
                            cliffhanger_scene_state = jp.get("sequence_continuity")
                        if last_shot_details.get("action_summary"):
                            previous_story += f" Ending shot: {last_shot_details['action_summary']}. Final dialogue: '{last_shot_details.get('dialogue_malayalam', '')}'"
                    print(f"✓ Retrieved master Past_Episodes_Prompts ({len(p_data.get('episodes', []))} episodes) from Google Sheet!")
        except Exception as err:
            print(f"Notice querying Past_Episodes_Prompts from Sheet: {err}")

    # Resolve upcoming target (Ep N+1) and Season climax (Ep 10) for two-way narrative bridge
    upcoming_target_entry = None
    season_climax_entry = None
    if season_arc and len(season_arc) >= target_ep + 1:
        upcoming_target_entry = season_arc[target_ep]  # 0-indexed: target_ep is Ep N+1
    elif active_roadmap and (target_ep + 1) in active_roadmap:
        upcoming_target_entry = active_roadmap[target_ep + 1]

    if season_arc and len(season_arc) >= 10:
        season_climax_entry = season_arc[-1]
    elif active_roadmap and 10 in active_roadmap:
        season_climax_entry = active_roadmap[10]

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
        active_character_dna=active_dna_map,
        past_timeline_summary=past_timeline_summary,
        last_shot_details=last_shot_details,
        upcoming_target_entry=upcoming_target_entry,
        season_climax_entry=season_climax_entry
    )

    if is_new_season:
        ep_data["season_arc"] = season_arc
        ep_data["season_title"] = season_title
        ep_data["character_updates"] = character_updates
        ep_data["new_characters_introduced"] = new_characters
    else:
        # Re-harmonize the living season arc (Sheet Tab 4) so all remaining episodes adapt to the ground truth
        if target_ep < 10:
            print(f"\n✨ Re-harmonizing Living Season Story Arc for remaining episodes ({target_ep + 1} to 10)...")
            harmonized_arc = reconcile_and_harmonize_season_arc(
                season_number=season_num,
                current_ep_num=target_ep,
                current_ep_data=ep_data,
                existing_arc=season_arc,
                gas_url=args.gas_url
            )
            if harmonized_arc:
                ep_data["season_arc"] = harmonized_arc
                season_arc = harmonized_arc
        elif season_arc:
            ep_data["season_arc"] = season_arc

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
        f"High-end Disney Pixar 3D animated vertical 9:16 poster thumbnail for 'Sachin & Reenu'.\n\n"
        f"[CRITICAL CLOTHING MANDATE - 100% MODERN CASUAL ONLY]:\n"
        f"- PROHIBIT ALL TRADITIONAL CLOTHING: ABSOLUTELY ZERO KURTIS, ZERO SAREES, ZERO SALWARS, ZERO DUPATTAS, ZERO JHUMKA EARRINGS, ZERO FORMAL COLLARED SHIRTS, ZERO TROUSERS. STRICTLY MODERN YOUTH CASUAL STREETWEAR ONLY.\n"
        f"- SACHIN ATTIRE: {sachin_attire}\n"
        f"- REENU ATTIRE: {reenu_attire}\n\n"
        f"[LAYOUT & GRAPHIC BRANDING]:\n"
        f"- Top-Left: Stylized, playful 3D cartoon title logo with vibrant bubble typography reading 'Sachin & Reenu', featuring a tiny cartoon crown icon above the 'S' and a playful pink heart over the 'e'.\n"
        f"- Top-Right: Two paper note card stickers pinned with beige masking tape on corners in the exact same location:\n"
        f"  1. Top sticker banner labeled 'Season' in handwritten font with a blank cream rectangular note card directly below it.\n"
        f"  2. Bottom sticker banner labeled 'Episode' in handwritten font with a blank cream rectangular note card directly below it.\n"
        f"- Decorative playful floating white cartoon hearts and doodle lines around the couple.\n\n"
        f"[CHARACTERS & SCENE - {season_title}]:\n"
        f"- Stylized 3D Pixar cartoon characters: 24yo Malayali boy Sachin (wavy dark hair, warm brown eyes, endearing smile) and 22yo Malayali girl Reenu (bouncy wavy dark hair with curtain bangs, large doe eyes, sweet smile).\n"
        f"- Setting: {setting_description}.\n"
        f"- Action: {action_description}\n\n"
        f"[RENDER QUALITY]:\n"
        f"- Disney Pixar 3D animation movie render, smooth velvety cartoon shaders, Octane 3D render, vertical 9:16 aspect ratio, clean vibrant 4K resolution."
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
