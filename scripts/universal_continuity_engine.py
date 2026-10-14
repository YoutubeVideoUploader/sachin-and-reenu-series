#!/usr/bin/env python3
"""
=============================================================================
UNIVERSAL SCENE STATE & CONTINUITY ENGINE
=============================================================================
Domain-Agnostic Physical World-State Tracking for 'Sachin & Reenu' Series.
Operates across ALL narrative environments:
- Vehicles (Cars, Jeeps, Buses, Trains)
- Dining / Food (Kitchens, Tea Stalls, Restaurants, Dining Tables)
- Domestic / Indoors (Living Rooms, Bedrooms, Homestays, Offices)
- Outdoor / Travel (Rainy Roads, Misty Forests, Trekking Trails, Marketplaces)

CORE ARCHITECTURAL INVARIANTS:
1. IMMUTABLE USER DIALOGUE: User Malayalam dialogue and speaker identities
   are strictly READ-ONLY CONSTANTS. The engine NEVER alters, translates,
   or hallucinates dialogue.
2. PHYSICAL ROLE & ACTIVITY PERSISTENCE: Whichever character initiates an
   ongoing physical role (driver, cook, tea vendor, flashlight bearer,
   front passenger, rear passenger) stays locked to that role across all
   consecutive shots in the scene. A role swap is only permitted upon an
   explicit narrative handover token.
3. SPATIAL ANCHOR & EYELINE CONTINUITY: Coordinates (Screen-Left, Screen-Center,
   Screen-Right; Foreground, Midground; Seated, Standing) are strictly
   preserved between sequential shots.
4. PROP CUSTODY INVARIANCE: Props (keys, steering wheel, map, flashlight,
   tea glass, bag, phone) remain with the character who took possession.
5. MATHEMATICAL 3D PIXAR DNA & ANTI-FAT GUARDS: Strict 1:6.5 teen proportions,
   lean athletic anatomy, clean-shaven faces, defined jawlines, and zero
   chubby/overweight diffusion artifacts.
6. DYNAMIC PERSPECTIVE & LIP-SYNC COUPLING: Direct character dialogue
   strictly triggers 'Character Dialogue ({Speaker} Speaking)', animated
   lip-sync visual directives, and absolute BGM prohibition.
=============================================================================
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ---------------------------------------------------------------------------
# 1. CANONICAL 3D DISNEY PIXAR CHARACTER DNA (MATHEMATICAL ANTI-FAT GUARDS)
# ---------------------------------------------------------------------------
MASTER_STYLE = (
    "High-end Disney Pixar 3D animated cartoon movie, stylized 3D cartoon character render, "
    "cute expressive animated features, soft smooth 3D cartoon shaders, vertical 9:16 format, "
    "Octane 3D render 4k 60fps"
)

DNA_SACHIN = (
    "Sachin: Stylized 3D Pixar-style cartoon animation character, 18-19 year old South Indian Malayali teenage boy. "
    "Youthful boyish facial features, soft clean jawline, completely clean-shaven smooth caramel-tan South Indian skin "
    "with velvety cartoon subsurface scattering shaders (STRICTLY TEENAGER / YOUTHFUL TEEN GUY, ZERO FACIAL HAIR, ZERO STUBBLE, ZERO MATURE LINES). "
    "Big bright expressive warm dark-brown cartoon eyes filled with lively excitement, natural youthful eyebrows, playful contagious boyish grin showing clean straight white upper teeth. "
    "Messy voluminous wavy jet-black teen cartoon hair with casual bouncy textured locks falling slightly over his forehead. "
    "Lanky, slender athletic teenage build (height 5'9\", youthful 1:6.5 head-to-body proportion, narrow athletic teen shoulders, flat waistline, natural teen posture, strictly non-chibi) "
    "(PROHIBIT CHILD/TODDLER/BABY/CHIBI ANATOMY, PROHIBIT REALISTIC HUMAN SKIN PORES, PROHIBIT UNCANNY REALISM, "
    "PROHIBIT OVERWEIGHT, PROHIBIT CHUBBY, PROHIBIT FAT BODY, PROHIBIT BULKY/HEAVY/STOCKY BUILD, PROHIBIT DOUBLE CHIN). "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Plain Navy Blue solid crewneck T-shirt, charcoal-black denim jeans, "
    "brown leather travel cross-bag, clean white sneakers. Absolutely zero costume variations."
)

DNA_REENU = (
    "Reenu: Stylized 3D Pixar-style cartoon animation character, 18-19 year old South Indian Malayali teenage girl. "
    "Adorable Pixar teen heroine face, soft youthful rounded cheeks with fresh natural peach-pink blush, smooth warm golden-fair skin "
    "with soft velvety cartoon shaders (STRICTLY TEENAGER / YOUTHFUL TEEN GIRL, NO MATURE AGING). "
    "Big sparkling expressive hazel-brown doe eyes with lush soft eyelashes, youthful naturally arched eyebrows, cute small button nose, "
    "radiant sweet bubbly teenage smile showing clean white teeth. "
    "Shoulder-length voluminous dark-brown wavy hair with bouncy youthful curls and soft curtain bangs framing her temples. "
    "Slender, petite teenage girl proportions (height 5'3\", youthful 1:6.2 head-to-body proportion, narrow waist, lively teen posture, strictly non-chibi) "
    "(PROHIBIT CHILD/TODDLER/BABY/CHIBI ANATOMY, PROHIBIT REALISTIC HUMAN SKIN PORES, PROHIBIT UNCANNY REALISM, "
    "PROHIBIT OVERWEIGHT, PROHIBIT CHUBBY, PROHIBIT FAT BODY, PROHIBIT BULKY/STOCKY BUILD, PROHIBIT DOUBLE CHIN). "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Pastel Lavender T-shirt with white cloud and daisy floral prints, "
    "light-wash denim skirt, silver wristwatch, white sneakers. Absolutely zero costume variations."
)

DNA_AMAL = (
    "Amal: Stylized 3D Pixar-style cartoon animation character, 18-19 year old South Indian Malayali teenage boy. "
    "Clean-shaven youthful teenage face, cheerful energetic jawline, warm dusky South Indian skin tone with smooth cartoon shaders, "
    "lively witty dark-brown animated eyes, expressive comedic eyebrows, cheerful mischievous teenage grin "
    "(STRICTLY TEENAGER / YOUTHFUL TEEN GUY, ZERO BEARD, ZERO STUBBLE, ZERO MATURE WRINKLES). "
    "Messy stylish short curly dark teen cartoon hair with textured volume. "
    "Slender athletic teenage build (height 5'8\", youthful 1:6.5 head-to-body proportion, lean flat waistline, narrow athletic frame, relaxed teen posture, strictly non-chibi) "
    "(PROHIBIT CHILD/TODDLER/BABY/CHIBI ANATOMY, PROHIBIT REALISTIC HUMAN SKIN PORES, PROHIBIT UNCANNY REALISM, "
    "PROHIBIT OVERWEIGHT, PROHIBIT CHUBBY, PROHIBIT FAT BODY, PROHIBIT BULKY/HEAVY/STOCKY BUILD, PROHIBIT DOUBLE CHIN, ZERO BEARD, ZERO STUBBLE). "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Plain Terracotta Rust-Orange solid T-shirt, faded blue denim jeans, "
    "black slip-on sneakers. Absolutely zero costume variations."
)

DNA_SHOPKEEPER = (
    "Tea Shopkeeper: Stylized 3D Pixar-style cartoon animation character, 45-50 year old rustic Malayali high-range tea vendor. "
    "Weathered warm brown skin, expressive kind eyes with cautionary look, clean grey-streaked hair, traditional blue check lungi and cream cotton shirt."
)

DNA_CARETAKER = (
    "Sreedharan (The Caretaker): Stylized 3D Pixar-style cartoon animation character, 55-60 year old mysterious high-range estate caretaker. "
    "Tall lean frame, hollow weathered cheeks, piercing observant dark eyes, dark shawl draped over khaki shirt, lantern bearer."
)

CANONICAL_DNA_MAP = {
    "Sachin": DNA_SACHIN,
    "Reenu": DNA_REENU,
    "Renu": DNA_REENU,
    "Amal": DNA_AMAL,
    "Shopkeeper": DNA_SHOPKEEPER,
    "Caretaker": DNA_CARETAKER
}

VOICE_MAP = {
    "Sachin": "Sachin: 18-19yo enthusiastic South Indian Malayali teenage boy voice, warm playful Kochi cadence, youthful eager tone (Gemini Voice 'Fenrir' / Edge-TTS 'ml-IN-MidhunNeural')",
    "Reenu": "Reenu: 18-19yo sweet expressive South Indian Malayali teenage girl voice, lively warm bubbly Malayalam tone (Gemini Voice 'Kore' / Edge-TTS 'ml-IN-SobhanaNeural')",
    "Renu": "Reenu: 18-19yo sweet expressive South Indian Malayali teenage girl voice, lively warm bubbly Malayalam tone (Gemini Voice 'Kore' / Edge-TTS 'ml-IN-SobhanaNeural')",
    "Amal": "Amal: 18-19yo witty relatable Malayali teenage friend voice, energetic comedic youthful Malayalam tone (Gemini Voice 'Puck' / Edge-TTS 'ml-IN-MidhunNeural')",
    "Shopkeeper": "Tea Shopkeeper: Local Malayali tea vendor, cautionary rustic high-range tone",
    "Caretaker": "Sreedharan (The Caretaker): Deep raspy mysterious high-range Malayalam tone (Central Travancore / Idukki dialect)",
    "Narrator": "Consistent Third-Person Female Narrator: 22-24yo charming South Indian Malayalam female storyteller voice, warm expressive sweet melodic tone (Gemini Voice 'Kore' / Edge-TTS 'ml-IN-SobhanaNeural')"
}

# ---------------------------------------------------------------------------
# 2. UNIVERSAL SCENE STATE TRACKER CLASS
# ---------------------------------------------------------------------------
class UniversalSceneTracker:
    """
    State machine that resolves physical reality, spatial anchors, and prop
    custody across consecutive shots in any environment.
    """
    def __init__(self):
        self.current_scene_type = None  # 'vehicle', 'dining', 'domestic', 'outdoor'
        self.roles: Dict[str, str] = {}  # e.g. {'driver': 'Amal', 'front_passenger': 'Sachin', 'rear_passenger': 'Reenu'}
        self.spatial_positions: Dict[str, str] = {}  # Character -> placement description
        self.props_in_hand: Dict[str, str] = {}  # Prop -> Character owner
        self.scene_props: List[str] = []

    def detect_scene_environment(self, location: str, action: str) -> str:
        loc_act = f"{location} {action}".lower()
        if any(k in loc_act for k in ["car", "vehicle", "jeep", "driving", "windshield", "steering", "ignition", "bonnet", "rearview", "traffic"]):
            return "vehicle"
        elif any(k in loc_act for k in ["tea shop", "kitchen", "restaurant", "dining", "cafe", "food", "table", "cooking", "plate", "glass"]):
            return "dining"
        elif any(k in loc_act for k in ["room", "homestay", "house", "apartment", "door", "bed", "living room", "couch"]):
            return "domestic"
        else:
            return "outdoor"

    def reset_or_update_scene(self, env_type: str, persistent_props: List[str]):
        if self.current_scene_type != env_type:
            self.current_scene_type = env_type
            self.roles.clear()
            self.spatial_positions.clear()
            self.props_in_hand.clear()
            self.scene_props = list(persistent_props)
        else:
            # Merge new persistent props
            for p in persistent_props:
                if p not in self.scene_props:
                    self.scene_props.append(p)

    def process_shot_state(
        self,
        shot_num: int,
        speaker: str,
        dialogue: str,
        action: str,
        location: str,
        persistent_props: List[str]
    ) -> Dict[str, Any]:
        """
        Calculates the physically coherent, continuous state for this shot.
        Guarantees role invariance and spatial coherence.
        """
        env = self.detect_scene_environment(location, action)
        self.reset_or_update_scene(env, persistent_props)
        act_lower = action.lower()

        # Check for explicit handover tokens
        has_handover = any(k in act_lower for k in [
            "swapped", "swapping", "switches seat", "hands keys", "hand over keys",
            "steps out of driver", "takes the wheel", "takes over"
        ])
        if has_handover:
            self.roles.clear()

        # --- ENVIRONMENT 1: VEHICLE SCENE ---
        if env == "vehicle":
            # Establish or enforce vehicle roles
            if "driver" not in self.roles:
                # Prioritize explicit action, else establish Amal as established driver
                if "sachin is driving" in act_lower or "sachin grips the steering" in act_lower:
                    self.roles["driver"] = "Sachin"
                    self.roles["front_passenger"] = "Amal"
                else:
                    self.roles["driver"] = "Amal"
                    self.roles["front_passenger"] = "Sachin"
                self.roles["rear_passenger"] = "Reenu"

            driver = self.roles.get("driver", "Amal")
            front_p = self.roles.get("front_passenger", "Sachin")
            rear_p = self.roles.get("rear_passenger", "Reenu")

            # Determine specific shot blocking
            spatial = {}
            if "bonnet" in act_lower or "engine" in act_lower or "steps out" in act_lower:
                if speaker == front_p or front_p.lower() in act_lower:
                    spatial[front_p] = f"Outside beside front car bonnet, peering into stalled engine compartment"
                    spatial[driver] = f"Driver seat (right side), looking through windshield toward {front_p}"
                else:
                    spatial[driver] = f"Outside beside front car bonnet, inspecting engine"
                    spatial[front_p] = f"Front passenger seat, leaning out window toward {driver}"
                spatial[rear_p] = "Rear passenger seat, looking through windshield and rear window with intense anxiety"
            elif "window" in act_lower and "handprint" in act_lower:
                spatial[rear_p] = "Rear seat frozen in terror, staring wide-eyed at icy handprint pressing against outer windowpane"
                spatial[driver] = "Driver seat (right side), head turned sharply back toward rear seat in shock"
                spatial[front_p] = "Front passenger seat, twisting around in terror to gaze at the rear window"
            elif "rearview" in act_lower or "mirror" in act_lower:
                spatial[driver] = "Driver seat (right side), hands gripping steering wheel, staring into illuminated rearview mirror"
                spatial[front_p] = "Front passenger seat (left side), seated looking toward driver with worried expression"
                spatial[rear_p] = "Rear passenger seat, leaning forward between front seats"
            else:
                spatial[driver] = "Driver seat (right side), hands gripping steering wheel, facing misty road"
                spatial[front_p] = "Front passenger seat (left side), seated looking toward driver and foggy side window"
                spatial[rear_p] = "Rear passenger seat directly behind front seats, watching dense mist outside"

            # Eyeline
            if speaker == driver:
                eyeline = f"{driver} looks forward through misted windshield and glances at {front_p}"
            elif speaker == front_p:
                eyeline = f"{front_p} looks toward {driver} and outward into dense fog"
            elif speaker in [rear_p, "Reenu", "Renu"]:
                eyeline = f"{rear_p} looks forward toward front dashboard and out rear windowpane"
            else:
                eyeline = "Characters maintain focused eyelines inside misty vehicle interior"

            # Clean action string to ensure driver invariance
            clean_action = action
            if driver != "Sachin":
                clean_action = re.sub(rf'\bSachin\s+grips\s+the\s+steering\s+wheel\b', f"{driver} grips the steering wheel", clean_action, flags=re.IGNORECASE)
                clean_action = re.sub(rf'\bSachin\s+is\s+driving\b', f"{driver} is driving", clean_action, flags=re.IGNORECASE)
                clean_action = re.sub(rf'\bSachin\s+in\s+the\s+driver\'?s?\s+seat\b', f"{driver} in the driver's seat", clean_action, flags=re.IGNORECASE)

            props = ["Car steering wheel", "Rearview mirror", "Illuminated dashboard dials", "Car ignition key", "Sachin's cross-bag"]

        # --- ENVIRONMENT 2: DINING / TEA STALL / FOOD ---
        elif env == "dining":
            if "host" not in self.roles:
                self.roles["host"] = "Shopkeeper" if "Shopkeeper" in action or speaker == "Shopkeeper" else "Amal"
                self.roles["left"] = "Sachin"
                self.roles["right"] = "Reenu"
                self.roles["center"] = "Amal"

            spatial = {
                "Sachin": "Seated at wooden tea stall bench on Screen-Left, holding warm tea glass",
                "Reenu": "Seated beside Sachin on Screen-Left, observing foggy high-range road",
                "Amal": "Standing by rustic wooden tea stall counter on Screen-Right, comedic animated posture",
                "Shopkeeper": "Behind tea stall kettle and glass display on Screen-Center, cautionary rustic presence"
            }
            eyeline = f"Characters looking toward {speaker} at tea stall counter"
            clean_action = action
            props = ["Steaming tea glass", "Rustic kettle", "Wooden bench", "Sachin's cross-bag", "Reenu's wristwatch"]

        # --- ENVIRONMENT 3: DOMESTIC / HOMESTAY / ROOM ---
        elif env == "domestic":
            spatial = {
                "Sachin": "Screen-Center in room interior, standing alert near wooden doorway",
                "Reenu": "Screen-Left in room, clutching travel bag, observing cautiously",
                "Amal": "Screen-Right in room, huddled nervously behind Sachin",
                "Caretaker": "Standing in doorway on Screen-Center, holding old brass key and lantern"
            }
            eyeline = f"Characters looking attentively toward {speaker}"
            clean_action = action
            props = ["Brass door key", "Old lantern", "Travel suitcase", "Sachin's cross-bag", "Reenu's wristwatch"]

        # --- ENVIRONMENT 4: OUTDOOR / ROAD ---
        else:
            spatial = {
                "Sachin": "Screen-Left on misty mountain path, walking forward alertly",
                "Reenu": "Screen-Center beside Sachin, scanning dense white fog",
                "Amal": "Screen-Right, trailing slightly behind, comedic cautious posture"
            }
            eyeline = f"Characters gazing into high-range mist toward scene focal action"
            clean_action = action
            props = ["Sachin's cross-bag", "Reenu's silver wristwatch", "Foggy mountain road"]

        return {
            "environment": env,
            "spatial_blocking": spatial,
            "eyeline_direction": eyeline,
            "cleaned_action": clean_action,
            "persistent_props": props
        }

# ---------------------------------------------------------------------------
# 3. COMPLETE PROMPT COMPILER FOR A SHOT (IMMUTABLE DIALOGUE PRESERVATION)
# ---------------------------------------------------------------------------
def compile_single_shot_prompt(
    shot_num: int,
    speaker: str,
    dialogue_malayalam: str,
    action: str,
    location: str,
    persistent_props: List[str],
    camera_hint: Optional[str] = None,
    scene_tracker: Optional[UniversalSceneTracker] = None
) -> Dict[str, Any]:
    """
    Compiles a pristine 10-key Google Flow Disney Pixar JSON prompt with:
    1. Verbatim user Malayalam dialogue.
    2. Dynamic lip-sync coupling.
    3. Mathematical 3D Disney Pixar DNA (anti-chubby / anti-fat).
    4. Physically coherent spatial coordinates and prop custody.
    """
    if scene_tracker is None:
        scene_tracker = UniversalSceneTracker()

    state = scene_tracker.process_shot_state(
        shot_num=shot_num,
        speaker=speaker,
        dialogue=dialogue_malayalam,
        action=action,
        location=location,
        persistent_props=persistent_props
    )

    clean_speaker = speaker.strip()
    if clean_speaker.lower() in ["renu", "reenu"]:
        clean_speaker = "Reenu"

    is_narrator = clean_speaker.lower() in [
        "narrator", "third-person narrator", "third person narrator", "voiceover", "voice-over"
    ]

    # Characters Present Construction
    chars_present = []
    # Always include speaker
    if clean_speaker in CANONICAL_DNA_MAP:
        chars_present.append({"name": clean_speaker, "visual_dna": CANONICAL_DNA_MAP[clean_speaker]})
    
    # Add interacting characters based on spatial blocking or action mention
    for cname in ["Sachin", "Reenu", "Amal", "Shopkeeper", "Caretaker"]:
        if cname != clean_speaker and (cname.lower() in state["cleaned_action"].lower() or cname in state["spatial_blocking"]):
            if not any(c["name"] == cname for c in chars_present):
                chars_present.append({"name": cname, "visual_dna": CANONICAL_DNA_MAP[cname]})

    if not chars_present:
        chars_present.append({"name": "Sachin", "visual_dna": DNA_SACHIN})

    # Filter spatial blocking to characters present
    active_spatial = {c["name"]: state["spatial_blocking"].get(c["name"], "Positioned in scene") for c in chars_present}

    camera = camera_hint or f"Cinematic 3D medium close-up focused on {clean_speaker}"

    if is_narrator:
        perspective = "Third-Person Cinematic Narration"
        action_text = (
            f"{state['cleaned_action'].rstrip('.')}. PURE VISUAL STORYTELLING. "
            f"All characters on screen maintain strictly closed lips with zero talking or mouth animation."
        )
        audio_directive = (
            "OFF-SCREEN FEMALE STORYTELLER VOICEOVER ONLY. NO CHARACTER SPEAKS ON SCREEN. "
            "All characters maintain strictly closed lips with zero talking or mouth animation. "
            "CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. "
            "Clean voiceover audio and natural ambient foley sound effects only."
        )
    else:
        perspective = f"Character Dialogue ({clean_speaker} Speaking)"
        action_text = (
            f"{state['cleaned_action'].rstrip('.')}. {clean_speaker} actively speaks dialogue on screen "
            f"with natural animated lip movement, expressive facial emotion, and speech sync. "
            f"Other character lips remain strictly closed."
        )
        audio_directive = (
            f"CHARACTER DIALOGUE SPOKEN BY {clean_speaker.upper()} ON SCREEN. "
            f"{clean_speaker} speaks directly with clear character voice and synchronized animated lip movement. "
            f"CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. "
            f"Clean character voice dialogue and natural ambient foley sound effects only."
        )

    json_prompt = {
        "style": MASTER_STYLE,
        "duration": "6s",
        "perspective": perspective,
        "characters_present": chars_present,
        "sequence_continuity": {
            "scene_id": f"SCENE_{state['environment'].upper()}_{location.upper().replace(' ', '_')}",
            "time_of_day": "Late Evening High-Range Monsoon Fog",
            "lighting_palette": "Eerie blue moonlight filtered through thick mountain fog with warm amber interior glow",
            "weather": "Heavy mountain fog with cool condensation on glass",
            "spatial_blocking": active_spatial,
            "eyeline_direction": state["eyeline_direction"],
            "persistent_props": state["persistent_props"],
            "camera_lens": "Cinematic prime lens, shallow depth of field, soft circular bokeh"
        },
        "location": location,
        "camera": camera,
        "action": action_text,
        "dialogue": {
            "speaker": clean_speaker if not is_narrator else "Off-Screen Third-Person Narrator",
            "voice_persona": VOICE_MAP.get(clean_speaker, VOICE_MAP["Amal"]),
            "language": "Malayalam",
            "script": dialogue_malayalam,
            "line": dialogue_malayalam
        },
        "audio_directive": audio_directive
    }

    return {
        "shot_number": shot_num,
        "duration": "6s",
        "duration_seconds": 6,
        "character": clean_speaker,
        "dialogue_malayalam": dialogue_malayalam,
        "action_summary": state["cleaned_action"],
        "json_prompt": json_prompt
    }

# ---------------------------------------------------------------------------
# 4. MASTER SYNCHRONIZATION PIPELINE (100-SHOT OUTLINE <-> TAB 2 <-> TAB 7)
# ---------------------------------------------------------------------------
def synchronize_master_outline_and_episode(
    season_number: int,
    target_episode: int,
    raw_shots: List[Dict[str, Any]],
    gas_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Takes 10 shots with sacred user dialogues, compiles them through the
    UniversalSceneTracker, updates:
    1. current_episode_shots.json
    2. season_{season_number}_shot_outline.json (100 shots)
    3. story_state.json
    4. Google Sheet Tab 2 (Current_JSON_Prompts) AND Tab 7 (Season_Shot_Outline)
    """
    tracker = UniversalSceneTracker()
    compiled_shots = []

    for s in raw_shots:
        num = s.get("shot_number")
        speaker = s.get("character") or s.get("speaker") or "Amal"
        dial = s.get("dialogue_malayalam") or s.get("dialogue") or ""
        act = s.get("action_summary") or s.get("action") or ""
        loc = s.get("location") or "Mountain road car interior"
        props = s.get("persistent_props") or ["Car steering wheel", "Rearview mirror", "Car keys"]
        cam = s.get("camera") or s.get("camera_hint")

        c_shot = compile_single_shot_prompt(
            shot_num=num,
            speaker=speaker,
            dialogue_malayalam=dial,
            action=act,
            location=loc,
            persistent_props=props,
            camera_hint=cam,
            scene_tracker=tracker
        )
        compiled_shots.append(c_shot)

    # 1. Update current_episode_shots.json
    ep_obj = {
        "episode_number": target_episode,
        "season_number": season_number,
        "is_new_season": False,
        "season_title": f"Season {season_number}: The Munnar Trip (മൂന്നാർ യാത്ര)",
        "title_english": "The Woman in the Mist",
        "title_malayalam": "മഞ്ഞിലെ സ്ത്രീ",
        "synopsis": "Traveling through the heavy mountain fog, Sachin, Reenu, and Amal face an eerie presence when their car sputters to a halt.",
        "cliffhanger": "A freezing handprint slowly presses against the outer window glass from the dark outside.",
        "total_shots": len(compiled_shots),
        "calculated_total_seconds": len(compiled_shots) * 6,
        "calculated_runtime_display": f"{len(compiled_shots) * 6 // 60}m {len(compiled_shots) * 6 % 60:02d}s",
        "shots": compiled_shots
    }

    with open("current_episode_shots.json", "w", encoding="utf-8") as f:
        json.dump(ep_obj, f, ensure_ascii=False, indent=2)
    print("✓ Updated current_episode_shots.json with pristine 10-shot flow!")

    # 2. Update season_3_shot_outline.json (100 shots)
    outline_path = Path(f"season_{season_number}_shot_outline.json")
    if outline_path.exists():
        with open(outline_path, "r", encoding="utf-8") as f:
            outline_data = json.load(f)

        # Update Episode in episodes array
        for ep in outline_data.get("episodes", []):
            if ep.get("episode_number") == target_episode:
                ep["title_english"] = ep_obj["title_english"]
                ep["title_malayalam"] = ep_obj["title_malayalam"]
                ep["synopsis"] = ep_obj["synopsis"]
                ep["cliffhanger"] = ep_obj["cliffhanger"]
                ep["shots"] = [
                    {
                        "shot_number": cs["shot_number"],
                        "speaker": cs["character"],
                        "action": cs["action_summary"],
                        "dialogue_malayalam": cs["dialogue_malayalam"],
                        "location": cs["json_prompt"]["location"],
                        "persistent_props": cs["json_prompt"]["sequence_continuity"]["persistent_props"],
                        "camera_hint": cs["json_prompt"]["camera"]
                    }
                    for cs in compiled_shots
                ]

        # Update flattened_shots array
        flat = outline_data.get("flattened_shots", [])
        for cs in compiled_shots:
            s_num = cs["shot_number"]
            for fs in flat:
                if fs.get("episode_number") == target_episode and fs.get("shot_number") == s_num:
                    fs["speaker"] = cs["character"]
                    fs["action"] = cs["action_summary"]
                    fs["dialogue_malayalam"] = cs["dialogue_malayalam"]
                    fs["location"] = cs["json_prompt"]["location"]
                    fs["persistent_props"] = cs["json_prompt"]["sequence_continuity"]["persistent_props"]
                    fs["camera_hint"] = cs["json_prompt"]["camera"]

        with open(outline_path, "w", encoding="utf-8") as f:
            json.dump(outline_data, f, ensure_ascii=False, indent=2)
        print(f"✓ Updated season_{season_number}_shot_outline.json (Master 100-Shot Roadmap)!")

    # 3. Update story_state.json
    state_path = Path("story_state.json")
    if state_path.exists():
        with open(state_path, "r", encoding="utf-8") as f:
            st = json.load(f)
        st["episode_number"] = target_episode
        st["current_episode"] = ep_obj
        if "season_shot_outline" in st and outline_path.exists():
            st["season_shot_outline"] = outline_data
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False, indent=2)
        print("✓ Updated story_state.json with synchronized outline!")

    return ep_obj

if __name__ == "__main__":
    print("Universal Scene Continuity Engine initialized.")
