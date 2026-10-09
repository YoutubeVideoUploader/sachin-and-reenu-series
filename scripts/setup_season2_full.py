import os
import sys
import json
import re
import requests

print("="*70)
print("ARCHITECTING SEASON 2: CLEAN RESET & FULL PIXAR 3D PROMPTS")
print("="*70)

# 1. API Keys & Endpoints
GEMINI_API_KEYS = [
    k for k in [
        os.getenv("GEMINI_API_KEY"),
        os.getenv("GEMINI_API_KEY_2"),
        os.getenv("GEMINI_API_KEY_3")
    ] if k
]

GAS_URL = os.getenv("GAS_WEBHOOK_URL", "https://script.google.com/macros/s/AKfycbyivkrK_jL1ejwNqUvHe8KVFNkSuJSwZbWSmuE1YATqL5jCneMlqlKbf0EH7mwpc4gybA/exec")

# 2. Inviolable Character DNA
DNA_REENU = (
    "Reenu: Stylized 3D Pixar-style cartoon animation character, 22yo South Indian Malayali girl, "
    "big expressive hazel-brown animated cartoon doe eyes with lush stylized eyelashes, soft rounded cute cartoon cheeks, "
    "sweet warm animated smile, voluminous bouncy wavy dark-brown cartoon hair with soft curtain bangs, "
    "stylized 3D character proportions with smooth vibrant cartoon shaders (STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Modern pastel mustard-yellow floral kurti with delicate white embroidery over crisp white cotton palazzo pants, white sneakers, silver wrist watch. Absolutely zero costume variations."
)

DNA_SACHIN = (
    "Sachin: Stylized 3D Pixar-style cartoon animation character, 24yo South Indian Malayali boy, "
    "endearing boyish cartoon features, large expressive warm animated brown eyes, playful genuine contagious cartoon smile, "
    "stylized soft textured wavy dark cartoon hair, cute slightly exaggerated 3D character proportions with smooth cartoon shaders "
    "(STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Crisp casual olive-green linen button-down shirt worn open over a plain crisp white crewneck inner t-shirt, dark charcoal denim jeans, brown leather travel cross-bag worn diagonally across chest. Absolutely zero costume variations."
)

DNA_AMAL = (
    "Amal: Stylized 3D Pixar-style cartoon animation character, 24yo South Indian Malayali boy, "
    "cheerful animated face, lively expressive cartoon eyes, broad energetic friendly cartoon smile, "
    "neat stylized short cartoon hairstyle, warm medium brown cartoon skin tone (STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Solid maroon polo t-shirt with dark navy denim jeans, casual slip-on sneakers. Absolutely zero costume variations."
)

DNA_MADHAVAN = (
    "Madhavan: Stylized 3D Pixar-style cartoon animation character, 52yo South Indian Malayali father, "
    "distinguished traditional features, neat salt-and-pepper mustache, stern yet deeply caring expressive animated eyes, "
    "slightly stout endearing 3D cartoon proportions with smooth shaders (STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Crisp white Kerala handloom cotton jubba shirt over matching white cotton mundu with thin gold kasavu border. Absolutely zero costume variations."
)

DNA_GIRIJA = (
    "Girija: Stylized 3D Pixar-style cartoon animation character, 48yo South Indian Malayali mother, "
    "warm motherly round face, loving expressive animated brown eyes, neat traditional dark hair tied in a graceful low bun with fresh jasmine flowers, "
    "sweet gentle 3D cartoon shaders (STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Traditional Kerala cotton cream and green saree with simple gold border, gold ear studs, small bindi. Absolutely zero costume variations."
)

# 3. Complete Master Season 2 Roadmap (10 Episodes)
SEASON_2_ROADMAP = [
    {
        "season_number": 2,
        "episode_number": 1,
        "title_english": "The Unannounced Guests",
        "title_malayalam": "വിരുന്നുകാർ",
        "status": "Active",
        "synopsis": "Reenu's traditional parents arrive in Kochi without warning, throwing Sachin and Reenu into sudden panic as they scramble to keep their apartment presentable.",
        "cliffhanger": "Just as Sachin finishes hiding a giant pile of dirty clothes, the doorbell rings, and he opens the door face-to-face with Reenu's stern father."
    },
    {
        "season_number": 2,
        "episode_number": 2,
        "title_english": "First Impressions & Spilled Chai",
        "title_malayalam": "ആദ്യ കൂടിക്കാഴ്ച",
        "status": "Upcoming",
        "synopsis": "Sachin nervously serves traditional Kerala tea to Reenu's parents while Amal desperately tries to coach Sachin via subtle hand gestures from the balcony.",
        "cliffhanger": "Madhavan suddenly asks Sachin what his long-term career stability looks like after quitting his London job."
    },
    {
        "season_number": 2,
        "episode_number": 3,
        "title_english": "The Kochi Job Dilemma",
        "title_malayalam": "പുതിയ ജോലി",
        "status": "Upcoming",
        "synopsis": "Sachin heads to his first official day at the InfoPark Kakkanad software office, facing a high-pressure corporate environment while Reenu cheers him on.",
        "cliffhanger": "Sachin receives an urgent project deadline that directly conflicts with an important family dinner with Reenu's parents."
    },
    {
        "season_number": 2,
        "episode_number": 4,
        "title_english": "A Secret Cafe Dream",
        "title_malayalam": "കഫേ സ്വപ്നം",
        "status": "Upcoming",
        "synopsis": "Over late-night roadside parotta, Sachin, Reenu, and Amal stumble upon a charming abandoned heritage building near Fort Kochi beach and dream of turning it into a book-cafe.",
        "cliffhanger": "The elderly Portuguese landlord mentions another buyer is ready to make a deposit by tomorrow morning."
    },
    {
        "season_number": 2,
        "episode_number": 5,
        "title_english": "The Fort Kochi Bid",
        "title_malayalam": "ഒരു പുതിയ തുടക്കം",
        "status": "Upcoming",
        "synopsis": "Amal pools together his quirky savings while Sachin and Reenu present an emotional pitch to the cafe owner, winning his heart with their creative vision.",
        "cliffhanger": "They sign the lease, but realize the plumbing and interiors need massive renovation within two weeks."
    },
    {
        "season_number": 2,
        "episode_number": 6,
        "title_english": "Paint Splatters & Stolen Moments",
        "title_malayalam": "ചായക്കൂട്ടുകൾ",
        "status": "Upcoming",
        "synopsis": "Sachin and Reenu spend late evenings renovating the cafe, sharing playful paint fights and quiet romantic glances amidst the sawdust and warm hanging lamps.",
        "cliffhanger": "Reenu's mother Girija secretly spots them together through the cafe window, noticing their undeniable bond."
    },
    {
        "season_number": 2,
        "episode_number": 7,
        "title_english": "A Mother's Heart",
        "title_malayalam": "അമ്മയുടെ മനസ്സ്",
        "status": "Upcoming",
        "synopsis": "Girija sits down with Reenu for a heart-to-heart conversation by the Marine Drive walkway, realizing how happy Sachin makes her daughter.",
        "cliffhanger": "Girija warns Reenu: 'Your father won't be as easy to convince, Reenu. You need to show him Sachin's true dedication.'"
    },
    {
        "season_number": 2,
        "episode_number": 8,
        "title_english": "The Tasting Night Chaos",
        "title_malayalam": "അമലിന്റെ വിരുന്ന്",
        "status": "Upcoming",
        "synopsis": "Amal hosts a mock tasting dinner for the cafe menu with Reenu's family, resulting in hilarious culinary mishaps with extra spicy chicken cutlets and dessert disasters.",
        "cliffhanger": "Despite the chaos, Madhavan takes a bite of Sachin's homemade dessert and pauses in deep silence."
    },
    {
        "season_number": 2,
        "episode_number": 9,
        "title_english": "A Father's Test",
        "title_malayalam": "തീരുമാനങ്ങൾ",
        "status": "Upcoming",
        "synopsis": "Madhavan invites Sachin for an early morning stroll by the Fort Kochi Chinese fishing nets, asking the difficult questions about their future and family responsibilities.",
        "cliffhanger": "Sachin honestly confesses his fears and wholehearted love for Reenu, standing tall without dodging any question."
    },
    {
        "season_number": 2,
        "episode_number": 10,
        "title_english": "The Grand Opening & The Blessing",
        "title_malayalam": "ഒരു പുതിയ പ്രഭാതം (ഗ്രാൻഡ് ക്ലൈമാക്സ്)",
        "status": "Upcoming",
        "synopsis": "SEASON 2 CLIMAX: The Fort Kochi book-cafe officially opens to glowing fairy lights and cheering friends. Madhavan and Girija arrive, giving their proud, heartfelt blessing to Sachin and Reenu.",
        "cliffhanger": "Sachin holds Reenu's hand under the glowing cafe lights, whispering: 'This is only the beginning.' Season 2 Grand Climax completed!"
    }
]

# 4. Generate Season 2 Episode 1 (All 10 Shots Full Pixar 3D Prompts)
print("\nDrafting Season 2, Episode 1 ('The Unannounced Guests')...")

EPISODE_1_DATA = {
    "season_number": 2,
    "episode_number": 1,
    "title_english": "The Unannounced Guests",
    "title_malayalam": "വിരുന്നുകാർ",
    "synopsis": "Reenu's traditional parents arrive in Kochi without warning, throwing Sachin and Reenu into sudden panic as they scramble to keep their apartment presentable.",
    "cliffhanger": "Just as Sachin finishes hiding a giant pile of dirty clothes, the doorbell rings, and he opens the door face-to-face with Reenu's stern father.",
    "total_shots": 10,
    "calculated_total_seconds": 60,
    "calculated_runtime_display": "1m 00s",
    "new_characters_introduced": [
        {
            "name": "Madhavan",
            "role": "Reenu's Father",
            "visual_dna": DNA_MADHAVAN,
            "locked_attire": "Crisp white Kerala handloom cotton jubba shirt over matching white cotton mundu with thin gold kasavu border.",
            "voice_persona": "52yo authoritative yet loving South Indian Malayalam male voice, deep traditional Thrissur cadence."
        },
        {
            "name": "Girija",
            "role": "Reenu's Mother",
            "visual_dna": DNA_GIRIJA,
            "locked_attire": "Traditional Kerala cotton cream and green saree with simple gold border, gold ear studs, small bindi.",
            "voice_persona": "48yo warm motherly South Indian Malayalam female voice, gentle affectionate cadence."
        }
    ],
    "shots": [
        {
            "shot_number": 1,
            "duration": "6s",
            "character": "Third-Person Narrator",
            "dialogue_malayalam": "കൊച്ചിയിലെ പുതിയ പ്രഭാതം സന്തോഷത്തോടെ തുടങ്ങി.",
            "action_summary": "Morning sunlight streams through the window of a cozy Kochi apartment living room. Sachin and Reenu are having a cheerful morning coffee together. Characters have closed lips with gentle smiling expressions.",
            "json_prompt": {
                "style": "High-end Disney Pixar 3D animated cartoon movie, stylized 3D cartoon character render, cute expressive animated features, soft smooth 3D cartoon shaders, vertical 9:16 format, Octane 3D render 4k 60fps",
                "duration": "6s",
                "perspective": "Medium wide shot, cozy living room morning composition",
                "characters_present": [
                    {"name": "Sachin", "visual_dna": DNA_SACHIN},
                    {"name": "Reenu", "visual_dna": DNA_REENU}
                ],
                "sequence_continuity": {
                    "scene_id": "SCENE_KOCHI_APARTMENT_MORNING",
                    "time_of_day": "Sunny Morning",
                    "lighting_palette": "Warm golden morning sunlight through sheer curtains, soft pastel highlights",
                    "weather": "Clear sunny morning",
                    "spatial_blocking": {
                        "Sachin": "Standing near kitchen counter, holding ceramic coffee mug",
                        "Reenu": "Seated on wooden bar stool, smiling cheerfully"
                    },
                    "eyeline_direction": "Sachin looks towards Reenu; Reenu looks towards Sachin with bright cheerful eyes",
                    "persistent_props": [
                        "Ceramic coffee mug in Sachin's hand",
                        "Reenu's silver wrist watch on left wrist"
                    ],
                    "camera_lens": "Cinematic prime lens, shallow depth of field, warm morning lens flare"
                },
                "location": "A cozy, sunlit Kochi apartment kitchen and living room",
                "camera": "Slow smooth pan from the sunny window to Sachin and Reenu",
                "action": "Sachin pours coffee into a mug, while Reenu takes a sip and laughs softly. Both characters have completely closed lips. Pure visual storytelling. No talking animation.",
                "dialogue": {
                    "speaker": "Third-Person Narrator",
                    "voice_persona": "Consistent Third-Person Female Narrator: 22-24yo charming South Indian Malayalam female storyteller voice, warm expressive sweet melodic tone",
                    "language": "Malayalam",
                    "script": "മലയാളം ലിപി",
                    "line": "കൊച്ചിയിലെ പുതിയ പ്രഭാതം സന്തോഷത്തോടെ തുടങ്ങി."
                },
                "audio_directive": "EXTERNAL FEMALE VOICEOVER ONLY. The characters do NOT speak. Character lips remain completely closed with NO lip sync animation. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voiceover audio and natural ambient morning foley sound effects only."
            }
        },
        {
            "shot_number": 2,
            "duration": "6s",
            "character": "Reenu",
            "dialogue_malayalam": "സച്ചിൻ, ഇന്ന് നമ്മൾ എന്താണ് ചെയ്യുന്നത്?",
            "action_summary": "Reenu places her mug on the table and looks up at Sachin with playful excitement. Her lips move in natural expressive 3D lip-sync.",
            "json_prompt": {
                "style": "High-end Disney Pixar 3D animated cartoon movie, stylized 3D cartoon character render, cute expressive animated features, soft smooth 3D cartoon shaders, vertical 9:16 format, Octane 3D render 4k 60fps",
                "duration": "6s",
                "perspective": "Close-up on Reenu, eye level",
                "characters_present": [
                    {"name": "Reenu", "visual_dna": DNA_REENU}
                ],
                "sequence_continuity": {
                    "scene_id": "SCENE_KOCHI_APARTMENT_MORNING",
                    "time_of_day": "Sunny Morning",
                    "lighting_palette": "Soft warm key light on Reenu's face, warm glowing rim light on wavy hair",
                    "weather": "Clear sunny morning",
                    "spatial_blocking": {
                        "Reenu": "Leaning slightly forward on counter, expressive playful tilt of head"
                    },
                    "eyeline_direction": "Reenu looks upward-right towards Sachin with sparkling eyes",
                    "persistent_props": [
                        "Reenu's silver wrist watch on left wrist",
                        "Coffee mug on counter"
                    ],
                    "camera_lens": "Cinematic portrait 50mm lens, creamy shallow depth of field"
                },
                "location": "Sunlit apartment kitchen counter",
                "camera": "Gentle push-in close-up focusing on Reenu's playful face",
                "action": "Reenu speaks cheerfully with charming animated gestures. Reenu's mouth moves in natural, expressive 3D lip-sync animation corresponding to her spoken Malayalam line.",
                "dialogue": {
                    "speaker": "Reenu",
                    "voice_persona": "Reenu: 22yo South Indian Malayalam female voice, sweet tender cheerful Kochi accent",
                    "language": "Malayalam",
                    "script": "മലയാളം ലിപി",
                    "line": "സച്ചിൻ, ഇന്ന് നമ്മൾ എന്താണ് ചെയ്യുന്നത്?"
                },
                "audio_directive": "FEMALE CHARACTER DIALOGUE (REENU). Character mouth animates in natural lip-sync with spoken Malayalam dialogue line. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voice audio and natural ambient foley sound effects only."
            }
        },
        {
            "shot_number": 3,
            "duration": "6s",
            "character": "Sachin",
            "dialogue_malayalam": "ഫോർട്ട് കൊച്ചിയിൽ ഒരു കറക്കം പോയാലോ?",
            "action_summary": "Sachin leans against the kitchen counter, smiling warmly as he suggests an outing to Fort Kochi. His mouth animates in natural lip-sync.",
            "json_prompt": {
                "style": "High-end Disney Pixar 3D animated cartoon movie, stylized 3D cartoon character render, cute expressive animated features, soft smooth 3D cartoon shaders, vertical 9:16 format, Octane 3D render 4k 60fps",
                "duration": "6s",
                "perspective": "Medium close-up on Sachin",
                "characters_present": [
                    {"name": "Sachin", "visual_dna": DNA_SACHIN}
                ],
                "sequence_continuity": {
                    "scene_id": "SCENE_KOCHI_APARTMENT_MORNING",
                    "time_of_day": "Sunny Morning",
                    "lighting_palette": "Warm amber morning light from side window, soft cyan fill",
                    "weather": "Clear sunny morning",
                    "spatial_blocking": {
                        "Sachin": "Standing comfortably by counter, holding his mug"
                    },
                    "eyeline_direction": "Sachin looks downward-left directly at Reenu with affectionate smile",
                    "persistent_props": [
                        "Ceramic mug in hand",
                        "Brown leather travel cross-bag strap on chest"
                    ],
                    "camera_lens": "Cinematic prime lens, beautiful soft circular bokeh"
                },
                "location": "Sunlit apartment kitchen counter",
                "camera": "Medium close-up tracking Sachin's charming boyish smile",
                "action": "Sachin speaks cheerfully. Sachin's mouth moves in natural, expressive 3D lip-sync animation corresponding to his spoken Malayalam line.",
                "dialogue": {
                    "speaker": "Sachin",
                    "voice_persona": "Sachin: 24yo endearing boyish South Indian Malayalam male voice, warm sincere Kochi accent",
                    "language": "Malayalam",
                    "script": "മലയാളം ലിപി",
                    "line": "ഫോർട്ട് കൊച്ചിയിൽ ഒരു കറക്കം പോയാലോ?"
                },
                "audio_directive": "MALE CHARACTER DIALOGUE (SACHIN). Character mouth animates in natural lip-sync with spoken Malayalam dialogue line. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voice audio and natural ambient foley sound effects only."
            }
        },
        {
            "shot_number": 4,
            "duration": "6s",
            "character": "Third-Person Narrator",
            "dialogue_malayalam": "പെട്ടെന്നാണ് ആ ഫോൺ കോൾ വന്നത്.",
            "action_summary": "Reenu's smartphone on the table suddenly vibrates and rings loudly, displaying 'അമ്മ' (Mother) on the glowing screen. Both freeze in surprise. Characters silent with closed lips.",
            "json_prompt": {
                "style": "High-end Disney Pixar 3D animated cartoon movie, stylized 3D cartoon character render, cute expressive animated features, soft smooth 3D cartoon shaders, vertical 9:16 format, Octane 3D render 4k 60fps",
                "duration": "6s",
                "perspective": "Macro close-up on vibrating phone",
                "characters_present": [
                    {"name": "Reenu", "visual_dna": DNA_REENU}
                ],
                "sequence_continuity": {
                    "scene_id": "SCENE_KOCHI_APARTMENT_MORNING",
                    "time_of_day": "Sunny Morning",
                    "lighting_palette": "Soft morning sunlight, glowing smartphone screen illumination",
                    "weather": "Clear sunny morning",
                    "spatial_blocking": {
                        "Reenu": "Hand reaching toward the phone in shock"
                    },
                    "eyeline_direction": "Reenu staring wide-eyed at the phone screen",
                    "persistent_props": [
                        "Vibrating smartphone on wooden table with incoming call",
                        "Reenu's silver wrist watch on left wrist"
                    ],
                    "camera_lens": "Macro portrait lens, intense shallow depth of field"
                },
                "location": "Wooden dining table surface",
                "camera": "Quick dynamic snap zoom to the ringing smartphone screen",
                "action": "The phone vibrates across the table. Reenu gasps softly with eyes wide in shock. Reenu's lips are firmly closed. No mouth movement. Pure visual storytelling.",
                "dialogue": {
                    "speaker": "Third-Person Narrator",
                    "voice_persona": "Consistent Third-Person Female Narrator: 22-24yo charming South Indian Malayalam female storyteller voice, warm expressive sweet melodic tone",
                    "language": "Malayalam",
                    "script": "മലയാളം ലിപി",
                    "line": "പെട്ടെന്നാണ് ആ ഫോൺ കോൾ വന്നത്."
                },
                "audio_directive": "EXTERNAL FEMALE VOICEOVER ONLY. The characters do NOT speak. Character lips remain completely closed with NO lip sync animation. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voiceover audio and natural ambient phone ringtone foley only."
            }
        },
        {
            "shot_number": 5,
            "duration": "6s",
            "character": "Reenu",
            "dialogue_malayalam": "സച്ചിൻ, അച്ഛനും അമ്മയും കൊച്ചിയിലെത്തി!",
            "action_summary": "Reenu holds the phone to her ear, her eyes popping with panic as she drops the news on Sachin. Her mouth moves in fast, panicked lip-sync.",
            "json_prompt": {
                "style": "High-end Disney Pixar 3D animated cartoon movie, stylized 3D cartoon character render, cute expressive animated features, soft smooth 3D cartoon shaders, vertical 9:16 format, Octane 3D render 4k 60fps",
                "duration": "6s",
                "perspective": "Tight close-up on Reenu's animated face",
                "characters_present": [
                    {"name": "Reenu", "visual_dna": DNA_REENU}
                ],
                "sequence_continuity": {
                    "scene_id": "SCENE_KOCHI_APARTMENT_MORNING",
                    "time_of_day": "Sunny Morning",
                    "lighting_palette": "Bright morning light emphasizing wide, shocked expressive cartoon doe eyes",
                    "weather": "Clear sunny morning",
                    "spatial_blocking": {
                        "Reenu": "Holding phone to ear, clutching counter with other hand in shock"
                    },
                    "eyeline_direction": "Reenu staring directly at Sachin in comical distress",
                    "persistent_props": [
                        "Smartphone at Reenu's ear",
                        "Reenu's silver wrist watch"
                    ],
                    "camera_lens": "Cinematic 50mm prime, soft blur on background"
                },
                "location": "Apartment kitchen",
                "camera": "Close-up tracking Reenu's comically panicked facial expression",
                "action": "Reenu speaks with urgent, frantic animated gestures. Reenu's mouth moves in natural, expressive 3D lip-sync animation corresponding to her spoken Malayalam line.",
                "dialogue": {
                    "speaker": "Reenu",
                    "voice_persona": "Reenu: 22yo South Indian Malayalam female voice, high-pitched panicked Kochi accent",
                    "language": "Malayalam",
                    "script": "മലയാളം ലിപി",
                    "line": "സച്ചിൻ, അച്ഛനും അമ്മയും കൊച്ചിയിലെത്തി!"
                },
                "audio_directive": "FEMALE CHARACTER DIALOGUE (REENU). Character mouth animates in natural lip-sync with spoken Malayalam dialogue line. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voice audio and natural ambient foley sound effects only."
            }
        },
        {
            "shot_number": 6,
            "duration": "6s",
            "character": "Sachin",
            "dialogue_malayalam": "എന്ത്? അവരിപ്പോൾ എവിടെയാണ് റീനു?",
            "action_summary": "Sachin nearly drops his coffee mug, his eyes widening in comical horror as he scrambles across the kitchen. His mouth animates in frantic lip-sync.",
            "json_prompt": {
                "style": "High-end Disney Pixar 3D animated cartoon movie, stylized 3D cartoon character render, cute expressive animated features, soft smooth 3D cartoon shaders, vertical 9:16 format, Octane 3D render 4k 60fps",
                "duration": "6s",
                "perspective": "Medium close-up on Sachin's comical panic",
                "characters_present": [
                    {"name": "Sachin", "visual_dna": DNA_SACHIN}
                ],
                "sequence_continuity": {
                    "scene_id": "SCENE_KOCHI_APARTMENT_MORNING",
                    "time_of_day": "Sunny Morning",
                    "lighting_palette": "Dynamic high-contrast morning sunlight",
                    "weather": "Clear sunny morning",
                    "spatial_blocking": {
                        "Sachin": "Stumbling backward slightly, balancing mug with exaggerated cartoon reaction"
                    },
                    "eyeline_direction": "Sachin looks wide-eyed directly at Reenu",
                    "persistent_props": [
                        "Coffee mug wobbling in hand",
                        "Brown leather travel cross-bag strap on chest"
                    ],
                    "camera_lens": "Cinematic prime lens, dynamic shallow depth of field"
                },
                "location": "Apartment kitchen counter",
                "camera": "Dynamic Dutch angle tracking Sachin's hilarious shocked reaction",
                "action": "Sachin throws his hands in the air comically. Sachin's mouth moves in natural, expressive 3D lip-sync animation corresponding to his spoken Malayalam line.",
                "dialogue": {
                    "speaker": "Sachin",
                    "voice_persona": "Sachin: 24yo endearing boyish South Indian Malayalam male voice, shocked frantic Kochi cadence",
                    "language": "Malayalam",
                    "script": "മലയാളം ലിപി",
                    "line": "എന്ത്? അവരിപ്പോൾ എവിടെയാണ് റീനു?"
                },
                "audio_directive": "MALE CHARACTER DIALOGUE (SACHIN). Character mouth animates in natural lip-sync with spoken Malayalam dialogue line. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voice audio and natural ambient foley sound effects only."
            }
        },
        {
            "shot_number": 7,
            "duration": "6s",
            "character": "Reenu",
            "dialogue_malayalam": "ലിഫ്റ്റിൽ കയറി! ഉടൻ വാതിൽ തുറക്കും!",
            "action_summary": "Reenu glances at the entrance door and points frantically towards the hallway. Her lips move in rapid lip-sync.",
            "json_prompt": {
                "style": "High-end Disney Pixar 3D animated cartoon movie, stylized 3D cartoon character render, cute expressive animated features, soft smooth 3D cartoon shaders, vertical 9:16 format, Octane 3D render 4k 60fps",
                "duration": "6s",
                "perspective": "Medium shot showing Reenu pointing frantically at front door",
                "characters_present": [
                    {"name": "Reenu", "visual_dna": DNA_REENU}
                ],
                "sequence_continuity": {
                    "scene_id": "SCENE_KOCHI_APARTMENT_MORNING",
                    "time_of_day": "Sunny Morning",
                    "lighting_palette": "Bright morning light illuminating living room",
                    "weather": "Clear sunny morning",
                    "spatial_blocking": {
                        "Reenu": "Standing in living room, pointing both hands toward hallway door"
                    },
                    "eyeline_direction": "Reenu alternating gaze between Sachin and the front entrance",
                    "persistent_props": [
                        "Reenu's silver wrist watch on left wrist"
                    ],
                    "camera_lens": "Cinematic 35mm wide lens, sharp focus"
                },
                "location": "Apartment living room",
                "camera": "Fast whip-pan from Reenu towards the apartment main door",
                "action": "Reenu gestures frantically at the door. Reenu's mouth moves in natural, expressive 3D lip-sync animation corresponding to her spoken Malayalam line.",
                "dialogue": {
                    "speaker": "Reenu",
                    "voice_persona": "Reenu: 22yo South Indian Malayalam female voice, hurried frantic high-energy Kochi accent",
                    "language": "Malayalam",
                    "script": "മലയാളം ലിപി",
                    "line": "ലിഫ്റ്റിൽ കയറി! ഉടൻ വാതിൽ തുറക്കും!"
                },
                "audio_directive": "FEMALE CHARACTER DIALOGUE (REENU). Character mouth animates in natural lip-sync with spoken Malayalam dialogue line. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voice audio and natural ambient foley sound effects only."
            }
        },
        {
            "shot_number": 8,
            "duration": "6s",
            "character": "Third-Person Narrator",
            "dialogue_malayalam": "അവിടെയൊരു വലിയ ബഹളം തുടങ്ങി.",
            "action_summary": "Hilarious montage of Sachin grabbing stray laundry and cushions, tossing them behind the sofa in hyper-speed cartoon motion. Characters have closed lips. Pure visual comedy.",
            "json_prompt": {
                "style": "High-end Disney Pixar 3D animated cartoon movie, stylized 3D cartoon character render, cute expressive animated features, soft smooth 3D cartoon shaders, vertical 9:16 format, Octane 3D render 4k 60fps",
                "duration": "6s",
                "perspective": "Wide comical shot of living room frenzy",
                "characters_present": [
                    {"name": "Sachin", "visual_dna": DNA_SACHIN},
                    {"name": "Reenu", "visual_dna": DNA_REENU}
                ],
                "sequence_continuity": {
                    "scene_id": "SCENE_KOCHI_APARTMENT_MORNING",
                    "time_of_day": "Sunny Morning",
                    "lighting_palette": "Bright warm sunbeams highlighting dust and laundry flying across room",
                    "weather": "Clear sunny morning",
                    "spatial_blocking": {
                        "Sachin": "Diving across sofa to hide clothes",
                        "Reenu": "Arranging magazines and cups in super speed"
                    },
                    "eyeline_direction": "Both frantically looking around room",
                    "persistent_props": [
                        "Piles of colorful laundry being stuffed under cushions",
                        "Sachin's diagonal brown leather cross-bag strap"
                    ],
                    "camera_lens": "Cinematic wide-angle lens, comical dynamic motion blur"
                },
                "location": "Living room center",
                "camera": "Dynamic low-angle tracking shot following Sachin's chaotic dive",
                "action": "Sachin slides across the hardwood floor stuffing clothes under the couch. Reenu straightens cushions. Both characters have closed lips. No speaking animation. Pure visual slapstick comedy.",
                "dialogue": {
                    "speaker": "Third-Person Narrator",
                    "voice_persona": "Consistent Third-Person Female Narrator: 22-24yo charming South Indian Malayalam female storyteller voice, energetic playful melodic tone",
                    "language": "Malayalam",
                    "script": "മലയാളം ലിപി",
                    "line": "അവിടെയൊരു വലിയ ബഹളം തുടങ്ങി."
                },
                "audio_directive": "EXTERNAL FEMALE VOICEOVER ONLY. The characters do NOT speak. Character lips remain completely closed with NO lip sync animation. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voiceover audio and comedic rustling foley sound effects only."
            }
        },
        {
            "shot_number": 9,
            "duration": "6s",
            "character": "Third-Person Narrator",
            "dialogue_malayalam": "അവസാനം ആ കോളിംഗ് ബെൽ അടിച്ചു.",
            "action_summary": "Extremely tense pause. Sachin and Reenu freeze instantly mid-stride. A loud 'DING-DONG' echoes. Both stare at the main wooden door in suspense. Closed lips.",
            "json_prompt": {
                "style": "High-end Disney Pixar 3D animated cartoon movie, stylized 3D cartoon character render, cute expressive animated features, soft smooth 3D cartoon shaders, vertical 9:16 format, Octane 3D render 4k 60fps",
                "duration": "6s",
                "perspective": "Extreme tension composition, low angle framed behind Sachin looking at door",
                "characters_present": [
                    {"name": "Sachin", "visual_dna": DNA_SACHIN},
                    {"name": "Reenu", "visual_dna": DNA_REENU}
                ],
                "sequence_continuity": {
                    "scene_id": "SCENE_KOCHI_APARTMENT_MORNING",
                    "time_of_day": "Sunny Morning",
                    "lighting_palette": "Dramatic morning sunlight casting long shadows across hallway",
                    "weather": "Clear sunny morning",
                    "spatial_blocking": {
                        "Sachin": "Frozen solid mid-step near the door handle",
                        "Reenu": "Standing behind him, clutching her hands in suspense"
                    },
                    "eyeline_direction": "Both eyes locked in terror on the apartment doorbell and wooden door",
                    "persistent_props": [
                        "Wooden apartment entrance door with golden handle",
                        "Reenu's silver wrist watch",
                        "Sachin's cross-bag strap"
                    ],
                    "camera_lens": "Cinematic prime lens, dramatic shallow depth of field"
                },
                "location": "Apartment entrance foyer",
                "camera": "Slow cinematic creep forward toward the closed wooden door",
                "action": "Sachin and Reenu stand completely motionless like statues. A loud doorbell chime sounds. Both characters keep strictly closed lips. Zero mouth movement.",
                "dialogue": {
                    "speaker": "Third-Person Narrator",
                    "voice_persona": "Consistent Third-Person Female Narrator: 22-24yo charming South Indian Malayalam female storyteller voice, suspenseful evocative tone",
                    "language": "Malayalam",
                    "script": "മലയാളം ലിപി",
                    "line": "അവസാനം ആ കോളിംഗ് ബെൽ അടിച്ചു."
                },
                "audio_directive": "EXTERNAL FEMALE VOICEOVER ONLY. The characters do NOT speak. Character lips remain completely closed with NO lip sync animation. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voiceover audio and loud realistic doorbell chime foley only."
            }
        },
        {
            "shot_number": 10,
            "duration": "6s",
            "character": "Third-Person Narrator",
            "dialogue_malayalam": "വാതിലിന് മുന്നിൽ അച്ഛൻ നിന്നു.",
            "action_summary": "SEASON 2 CLIFFHANGER: Sachin nervously clicks the door open. Standing right outside is Reenu's father Madhavan in a crisp Kerala mundu, arms crossed with an intense, stern gaze. Characters silent.",
            "json_prompt": {
                "style": "High-end Disney Pixar 3D animated cartoon movie, stylized 3D cartoon character render, cute expressive animated features, soft smooth 3D cartoon shaders, vertical 9:16 format, Octane 3D render 4k 60fps",
                "duration": "6s",
                "perspective": "Dramatic over-the-shoulder reveal shot from Sachin looking out at Madhavan",
                "characters_present": [
                    {"name": "Sachin", "visual_dna": DNA_SACHIN},
                    {"name": "Madhavan", "visual_dna": DNA_MADHAVAN}
                ],
                "sequence_continuity": {
                    "scene_id": "SCENE_KOCHI_APARTMENT_DOOR_CLIMAX",
                    "time_of_day": "Sunny Morning",
                    "lighting_palette": "Bright hallway overhead corridor light illuminating Madhavan's stern silhouette",
                    "weather": "Clear sunny morning",
                    "spatial_blocking": {
                        "Sachin": "Foreground left, clutching the door half-open in trembling shock",
                        "Madhavan": "Standing center frame outside in hallway, standing tall and dignified"
                    },
                    "eyeline_direction": "Madhavan stares sternly directly into Sachin's wide eyes",
                    "persistent_props": [
                        "Apartment door handle",
                        "Madhavan's gold-bordered white Kerala mundu"
                    ],
                    "camera_lens": "Cinematic prime 85mm lens, intense dramatic focus on Madhavan's eyes"
                },
                "location": "Apartment doorway corridor",
                "camera": "Slow dramatic reveal push-in directly onto Madhavan's formidable expression",
                "action": "The door swings open. Madhavan stands outside with arms folded, giving a piercing, stern inspection. Sachin freezes in sheer awe. Both characters have firmly closed lips. No mouth movement. High dramatic cliffhanger.",
                "dialogue": {
                    "speaker": "Third-Person Narrator",
                    "voice_persona": "Consistent Third-Person Female Narrator: 22-24yo charming South Indian Malayalam female storyteller voice, intense dramatic cliffhanger cadence",
                    "language": "Malayalam",
                    "script": "മലയാളം ലിപി",
                    "line": "വാതിലിന് മുന്നിൽ അച്ഛൻ നിന്നു."
                },
                "audio_directive": "OFF-SCREEN FEMALE STORYTELLER VOICEOVER ONLY. NO CHARACTER SPEAKS ON SCREEN. All characters maintain strictly closed lips with zero talking or mouth animation. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voiceover audio and natural ambient foley sound effects only."
            }
        }
    ]
}

print(f"[OK] All 10 shots generated with full Disney Pixar 3D schema and locked DNA!")

# 5. Push Clean Updates to Google Sheets
print("\n5. Pushing Clean Updates to Google Sheet...")

# A. Tab 4: Season_Story_Arc (Overwrites with strictly 10 episodes, NO Episode 11)
print("  -> Overwriting Tab 4 [Season_Story_Arc] with 10-episode Season 2 Roadmap...")
payload_tab4 = {
    "action": "update_season_story_arc",
    "season_number": 2,
    "season_title": "The Unannounced Guests & Fort Kochi Days (വിരുന്നുകാരും പുതിയ തുടക്കവും)",
    "episodes": SEASON_2_ROADMAP
}
try:
    r4 = requests.post(GAS_URL, data=json.dumps(payload_tab4), headers={"Content-Type": "text/plain"}, timeout=30)
    print("     Tab 4 Response:", r4.status_code, r4.text[:120])
except Exception as e:
    print("     Tab 4 Sync Notice:", e)

# B. Tab 1, Tab 2, Tab 3, Tab 5: Full Update for Season 2, Episode 1
print("  -> Overwriting Tab 1, Tab 2, Tab 3, Tab 5 for Season 2, Episode 1...")
payload_full = {
    "action": "update_next_episode_full",
    "season_number": 2,
    "is_new_season": True,
    "episode_number": 1,
    "title_english": EPISODE_1_DATA["title_english"],
    "title_malayalam": EPISODE_1_DATA["title_malayalam"],
    "synopsis": EPISODE_1_DATA["synopsis"],
    "cliffhanger": EPISODE_1_DATA["cliffhanger"],
    "total_shots": 10,
    "shots": EPISODE_1_DATA["shots"],
    "new_characters_introduced": EPISODE_1_DATA["new_characters_introduced"]
}
try:
    rf = requests.post(GAS_URL, data=json.dumps(payload_full), headers={"Content-Type": "text/plain"}, timeout=30)
    print("     Full Sheet Response:", rf.status_code, rf.text[:120])
except Exception as e:
    print("     Full Sheet Sync Notice:", e)

# 6. Update story_state.json
print("\n6. Updating story_state.json...")
state_file = "story_state.json"
story_state = {
    "series_title": "SACHIN & REENU (സച്ചിൻ & റീനു)",
    "season_number": 2,
    "episode_number": 1,
    "total_episodes_produced": 10,
    "season_title": "The Unannounced Guests & Fort Kochi Days (വിരുന്നുകാരും പുതിയ തുടക്കവും)",
    "current_arc": "Season 2: Reenu's Parents in Kochi & The Fort Kochi Cafe",
    "characters": {
        "Sachin": {"age": 24, "gender": "male", "attire": "Olive-green linen button-down shirt over white t-shirt, dark charcoal denim jeans"},
        "Reenu": {"age": 22, "gender": "female", "attire": "Pastel mustard-yellow floral kurti over white cotton palazzo pants"},
        "Amal": {"age": 24, "gender": "male", "attire": "Solid maroon polo t-shirt with dark navy denim jeans"},
        "Madhavan": {"age": 52, "gender": "male", "role": "Reenu's Father", "attire": "White Kerala cotton jubba over gold-bordered mundu"},
        "Girija": {"age": 48, "gender": "female", "role": "Reenu's Mother", "attire": "Traditional Kerala cotton cream and green saree"}
    },
    "history": SEASON_2_ROADMAP
}
with open(state_file, "w", encoding="utf-8") as f:
    json.dump(story_state, f, ensure_ascii=False, indent=2)
print("[OK] story_state.json updated for Season 2, Episode 1!")

# 7. Update current_episode_shots.json
print("\n7. Updating current_episode_shots.json...")
with open("current_episode_shots.json", "w", encoding="utf-8") as f:
    json.dump(EPISODE_1_DATA, f, ensure_ascii=False, indent=2)
print("[OK] current_episode_shots.json updated with Season 2, Episode 1!")

# 8. Update all 3 portal.html copies
print("\n8. Updating all 3 copies of portal.html...")
with open("portal.html", "r", encoding="utf-8") as f:
    portal_html = f.read()

ep1_json_str = json.dumps(EPISODE_1_DATA, ensure_ascii=False, indent=2)

portal_html = re.sub(
    r'let episodeData = \{.*?\};\s+// Tracks current state',
    f'let episodeData = {ep1_json_str};\n\n    // Tracks current state',
    portal_html,
    flags=re.DOTALL
)

portal_paths = [
    "c:/Users/HP/OneDrive/Desktop/VISHNU/WEB/Sachin_And_Reenu_Series/portal.html",
    "c:/Users/HP/OneDrive/Desktop/VISHNU/WEB/Sachin_And_Reenu_Series/repo_studio/portal.html",
    "c:/Users/HP/OneDrive/Desktop/VISHNU/WEB/portal.html"
]

for p in portal_paths:
    if os.path.exists(os.path.dirname(p)):
        with open(p, "w", encoding="utf-8") as f:
            f.write(portal_html)
        print(f"  [OK] Updated {p}")

print("\n" + "="*70)
print("[SUCCESS] SEASON 2 LAUNCH COMPLETE ACROSS REPO & GOOGLE SHEETS!")
print("="*70)
