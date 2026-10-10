import json
import os
import sys
from pathlib import Path

MASTER_STYLE = "High-end Disney Pixar 3D animated cartoon movie, stylized 3D cartoon character render, cute expressive animated features, soft smooth 3D cartoon shaders, vertical 9:16 format, Octane 3D render 4k 60fps"

DNA_SACHIN = (
    "Sachin: Stylized 3D Pixar-style cartoon animation character, 24yo South Indian Malayali boy, "
    "endearing boyish cartoon features, large expressive warm animated brown eyes, playful genuine contagious cartoon smile, "
    "stylized soft textured wavy dark cartoon hair, cute slightly exaggerated 3D character proportions with smooth cartoon shaders "
    "(STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Solid olive-green plain crewneck t-shirt (strictly solid color, "
    "zero patterns or graphics), relaxed-fit dark indigo denim jeans, classic white sneakers, brown leather travel cross-bag "
    "worn diagonally across chest. Absolutely zero costume variations."
)

DNA_REENU = (
    "Reenu: Stylized 3D Pixar-style cartoon animation character, 22yo South Indian Malayali girl, "
    "big expressive hazel-brown animated cartoon doe eyes with lush stylized eyelashes, soft rounded cute cartoon cheeks, "
    "sweet warm animated smile, voluminous bouncy wavy dark-brown cartoon hair with soft curtain bangs, stylized 3D character "
    "proportions with smooth vibrant cartoon shaders (STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Pastel lavender and blush-pink floral-doodle pattern printed oversized t-shirt, "
    "high-waisted medium-blue denim skirt, clean white sneakers, silver wrist watch. Absolutely zero costume variations."
)

DNA_KURIAN = (
    "Kurian (Reenu's Father): Stylized 3D Pixar character with rigid square jaw, salt-and-pepper mustache, "
    "wire-rimmed reading glasses resting on a stern nose, piercing observant eyes, and dignified posture. "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Crisp starched white cotton Jubba paired with a double-folded pristine "
    "white Mundu featuring a thin gold Kasavu border, brown leather sandals, and an analog Titan watch. Absolutely zero costume variations."
)

DNA_ANNAMMA = (
    "Annamma (Reenu's Mother): Soft, rounded Pixar matriarch silhouette, gentle face framed by silver-streaked black hair "
    "pinned in a neat traditional bun, expressive eyes that instantly spot domestic flaws. "
    "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT): Handloom bottle-green cotton saree with mustard border, thin gold bangles "
    "that clink rhythmically, and a classic gold crucifix necklace. Absolutely zero costume variations."
)

PERSISTENT_PROPS = [
    "Cardboard snack box",
    "Dirty clothes pile",
    "Fairy lights strand",
    "Front apartment door",
    "Laundry basket",
    "Plastic stepping stool",
    "Reenu's silver wrist watch",
    "Sachin's cross-bag",
    "Two large VIP suitcases"
]

shots_data = [
    # Shot 1
    {
        "shot_number": 1,
        "duration": "6s",
        "duration_seconds": 6,
        "character": "Third-Person Narrator",
        "dialogue_malayalam": "കൊച്ചിയിലെ ഒരു മനോഹരമായ ഞായറാഴ്ച ഉച്ച.",
        "action_summary": "Living room: Sachin stands on a small stool reaching up to hang fairy lights while Reenu holds the strand, smiling warmly. Lips firmly closed.",
        "json_prompt": {
            "style": MASTER_STYLE,
            "duration": "6s",
            "perspective": "Third-Person Narrator",
            "characters_present": [
                {"name": "Sachin", "visual_dna": DNA_SACHIN},
                {"name": "Reenu", "visual_dna": DNA_REENU}
            ],
            "sequence_continuity": {
                "scene_id": "SCENE_KAKKANAD_LIVING_ROOM",
                "time_of_day": "Sunday Afternoon",
                "lighting_palette": "Warm golden hour sunlight streaming through apartment window",
                "weather": "Clear sunny weather",
                "spatial_blocking": {
                    "Sachin": "Standing on a small stool reaching up to the curtain rod",
                    "Reenu": "Standing beside Sachin holding a box of lights"
                },
                "eyeline_direction": "Both looking at the fairy lights",
                "persistent_props": PERSISTENT_PROPS,
                "camera_lens": "Cinematic prime lens, shallow depth of field"
            },
            "location": "Living room",
            "camera": "Close up shot",
            "action": "Sachin and Reenu are decorating. Lips are firmly closed. Pure visual scene action.",
            "dialogue": {
                "speaker": "Third-Person Narrator",
                "voice_persona": "Consistent Third-Person Female Narrator: 22-24yo charming South Indian Malayalam female storyteller voice, warm expressive sweet melodic tone, gentle youthful evocative Malayalam cadence, clear acoustic studio warmth",
                "language": "Malayalam",
                "script": "കൊച്ചിയിലെ ഒരു മനോഹരമായ ഞായറാഴ്ച ഉച്ച.",
                "line": "കൊച്ചിയിലെ ഒരു മനോഹരമായ ഞായറാഴ്ച ഉച്ച."
            },
            "audio_directive": "EXTERNAL FEMALE VOICEOVER ONLY. NO CHARACTER SPEAKS ON SCREEN. All characters maintain strictly closed lips with zero talking or mouth animation. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voiceover audio and natural ambient foley sound effects only."
        }
    },
    # Shot 2
    {
        "shot_number": 2,
        "duration": "6s",
        "duration_seconds": 6,
        "character": "Sachin",
        "dialogue_malayalam": "റീനു, ഇത് നേരെയാണോ അതോ ചരിയുന്നുണ്ടോ?",
        "action_summary": "Sachin looks down playfully at Reenu while holding the golden light string against the wall, mouth moving in precise lip sync.",
        "json_prompt": {
            "style": MASTER_STYLE,
            "duration": "6s",
            "perspective": "Sachin talking to Reenu",
            "characters_present": [
                {"name": "Sachin", "visual_dna": DNA_SACHIN},
                {"name": "Reenu", "visual_dna": DNA_REENU}
            ],
            "sequence_continuity": {
                "scene_id": "SCENE_KAKKANAD_LIVING_ROOM",
                "time_of_day": "Sunday Afternoon",
                "lighting_palette": "Warm golden hour sunlight streaming through apartment window",
                "weather": "Clear sunny weather",
                "spatial_blocking": {
                    "Sachin": "Standing on stool looking down at Reenu",
                    "Reenu": "Standing on floor looking up at Sachin"
                },
                "eyeline_direction": "Sachin looks down at Reenu; Reenu looks up at Sachin",
                "persistent_props": PERSISTENT_PROPS,
                "camera_lens": "Cinematic prime lens, shallow depth of field"
            },
            "location": "Living room",
            "camera": "Medium shot",
            "action": "Sachin speaks with precise lip sync. Reenu listens with lips closed and gentle smile.",
            "dialogue": {
                "speaker": "Sachin",
                "voice_persona": "Sachin: 24yo endearing, youthful boyish Malayalam voice with light playful Alappuzha cadence",
                "language": "Malayalam",
                "script": "റീനു, ഇത് നേരെയാണോ അതോ ചരിയുന്നുണ്ടോ?",
                "line": "റീനു, ഇത് നേരെയാണോ അതോ ചരിയുന്നുണ്ടോ?"
            },
            "audio_directive": "Sachin speaks. Reenu listens. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voice dialogue and natural ambient foley sound effects only."
        }
    },
    # Shot 3
    {
        "shot_number": 3,
        "duration": "6s",
        "duration_seconds": 6,
        "character": "Reenu",
        "dialogue_malayalam": "കുറച്ചുകൂടി വലത്തോട്ട് വെക്ക് സച്ചിൻ!",
        "action_summary": "Reenu giggles with hands on hips, pointing playfully upward to the right side of the wall. Mouth moves in sync.",
        "json_prompt": {
            "style": MASTER_STYLE,
            "duration": "6s",
            "perspective": "Reenu giving directions to Sachin",
            "characters_present": [
                {"name": "Reenu", "visual_dna": DNA_REENU},
                {"name": "Sachin", "visual_dna": DNA_SACHIN}
            ],
            "sequence_continuity": {
                "scene_id": "SCENE_KAKKANAD_LIVING_ROOM",
                "time_of_day": "Sunday Afternoon",
                "lighting_palette": "Warm golden hour sunlight streaming through apartment window",
                "weather": "Clear sunny weather",
                "spatial_blocking": {
                    "Reenu": "Standing near center room pointing up",
                    "Sachin": "Standing on stool adjusting the wire"
                },
                "eyeline_direction": "Reenu looks up at Sachin's hands; Sachin looks at wall",
                "persistent_props": PERSISTENT_PROPS,
                "camera_lens": "Cinematic prime lens, shallow depth of field"
            },
            "location": "Living room",
            "camera": "Medium shot",
            "action": "Reenu speaks with energetic lip sync. Sachin smiles silently.",
            "dialogue": {
                "speaker": "Reenu",
                "voice_persona": "Reenu: 22yo sweet, warm, charming young Kochi working woman voice, melodic cadence",
                "language": "Malayalam",
                "script": "കുറച്ചുകൂടി വലത്തോട്ട് വെക്ക് സച്ചിൻ!",
                "line": "കുറച്ചുകൂടി വലത്തോട്ട് വെക്ക് സച്ചിൻ!"
            },
            "audio_directive": "Reenu speaks. Sachin listens silently with closed lips. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voice dialogue and natural ambient foley sound effects only."
        }
    },
    # Shot 4
    {
        "shot_number": 4,
        "duration": "6s",
        "duration_seconds": 6,
        "character": "Third-Person Narrator",
        "dialogue_malayalam": "സമാധാനവും സന്തോഷവും നിറഞ്ഞ നിമിഷങ്ങൾ.",
        "action_summary": "Sachin playfully tosses a Kerala banana chip snack down to Reenu, who catches it effortlessly and takes a bite, both sharing a quiet laugh. Lips closed.",
        "json_prompt": {
            "style": MASTER_STYLE,
            "duration": "6s",
            "perspective": "Third-Person Narrator",
            "characters_present": [
                {"name": "Sachin", "visual_dna": DNA_SACHIN},
                {"name": "Reenu", "visual_dna": DNA_REENU}
            ],
            "sequence_continuity": {
                "scene_id": "SCENE_KAKKANAD_LIVING_ROOM",
                "time_of_day": "Sunday Afternoon",
                "lighting_palette": "Warm golden hour sunlight streaming through apartment window",
                "weather": "Clear sunny weather",
                "spatial_blocking": {
                    "Sachin": "Sitting relaxed atop the stool holding snack box",
                    "Reenu": "Leaning against sofa eating snack"
                },
                "eyeline_direction": "Looking at each other warmly",
                "persistent_props": PERSISTENT_PROPS,
                "camera_lens": "Cinematic prime lens, shallow depth of field"
            },
            "location": "Living room",
            "camera": "Close up shot",
            "action": "PURE VISUAL SCENE ACTION. Both characters laugh silently with closed lips. No dialogue.",
            "dialogue": {
                "speaker": "Third-Person Narrator",
                "voice_persona": "Consistent Third-Person Female Narrator: 22-24yo charming South Indian Malayalam female storyteller voice, warm expressive sweet melodic tone, gentle youthful evocative Malayalam cadence, clear acoustic studio warmth",
                "language": "Malayalam",
                "script": "സമാധാനവും സന്തോഷവും നിറഞ്ഞ നിമിഷങ്ങൾ.",
                "line": "സമാധാനവും സന്തോഷവും നിറഞ്ഞ നിമിഷങ്ങൾ."
            },
            "audio_directive": "EXTERNAL FEMALE VOICEOVER ONLY. NO CHARACTER SPEAKS ON SCREEN. All characters maintain strictly closed lips with zero talking or mouth animation. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voiceover audio and natural ambient foley sound effects only."
        }
    },
    # Shot 5 (The Turning Point: Aggressive Calling Bell / Knock)
    {
        "shot_number": 5,
        "duration": "6s",
        "duration_seconds": 6,
        "character": "Third-Person Narrator",
        "dialogue_malayalam": "പെട്ടെന്നാണ് വാതിലിൽ ശക്തമായ കോളിംഗ് ബെൽ മുഴങ്ങിയത്!",
        "action_summary": "The front door vibrates as an aggressive, loud series of doorbell chimes ring out! Sachin and Reenu startle, their eyes darting to the entrance in shock. Lips closed.",
        "json_prompt": {
            "style": MASTER_STYLE,
            "duration": "6s",
            "perspective": "Third-Person Narrator",
            "characters_present": [
                {"name": "Sachin", "visual_dna": DNA_SACHIN},
                {"name": "Reenu", "visual_dna": DNA_REENU}
            ],
            "sequence_continuity": {
                "scene_id": "SCENE_KAKKANAD_LIVING_ROOM",
                "time_of_day": "Sunday Afternoon",
                "lighting_palette": "Warm golden hour sunlight with dramatic focus toward entrance",
                "weather": "Clear sunny weather",
                "spatial_blocking": {
                    "Sachin": "Stiffening mid-air on stool",
                    "Reenu": "Dropping snack box on couch, turning toward hallway"
                },
                "eyeline_direction": "Both eyes locked in shock at the front door",
                "persistent_props": PERSISTENT_PROPS,
                "camera_lens": "Cinematic prime lens, shallow depth of field"
            },
            "location": "Living room hallway",
            "camera": "Medium wide shot",
            "action": "PURE VISUAL SCENE ACTION. Both characters freeze in startle as calling bell rings. Closed lips.",
            "dialogue": {
                "speaker": "Third-Person Narrator",
                "voice_persona": "Consistent Third-Person Female Narrator: 22-24yo charming South Indian Malayalam female storyteller voice, warm expressive sweet melodic tone, gentle youthful evocative Malayalam cadence, clear acoustic studio warmth",
                "language": "Malayalam",
                "script": "പെട്ടെന്നാണ് വാതിലിൽ ശക്തമായ കോളിംഗ് ബെൽ മുഴങ്ങിയത്!",
                "line": "പെട്ടെന്നാണ് വാതിലിൽ ശക്തമായ കോളിംഗ് ബെൽ മുഴങ്ങിയത്!"
            },
            "audio_directive": "EXTERNAL FEMALE VOICEOVER ONLY. Loud realistic doorbell sound foley. NO CHARACTER SPEAKS ON SCREEN. Lips firmly closed. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE."
        }
    },
    # Shot 6 (Reenu heading to door)
    {
        "shot_number": 6,
        "duration": "6s",
        "duration_seconds": 6,
        "character": "Reenu",
        "dialogue_malayalam": "ആരാ ഈ സമയത്ത്?",
        "action_summary": "Reenu walks swiftly toward the hallway door with furrowed eyebrows, wondering aloud who would visit unannounced. Mouth moves in sync.",
        "json_prompt": {
            "style": MASTER_STYLE,
            "duration": "6s",
            "perspective": "Reenu walking to front door",
            "characters_present": [
                {"name": "Reenu", "visual_dna": DNA_REENU}
            ],
            "sequence_continuity": {
                "scene_id": "SCENE_KAKKANAD_HALLWAY",
                "time_of_day": "Sunday Afternoon",
                "lighting_palette": "Soft corridor lighting leading to dark teak front door",
                "weather": "Clear sunny weather",
                "spatial_blocking": {
                    "Reenu": "Walking along apartment hallway toward front door lock"
                },
                "eyeline_direction": "Reenu looking directly at front door peephole/handle",
                "persistent_props": PERSISTENT_PROPS,
                "camera_lens": "Cinematic prime lens, shallow depth of field"
            },
            "location": "Apartment hallway",
            "camera": "Medium tracking shot",
            "action": "Reenu speaks with puzzled expression. Precise lip sync.",
            "dialogue": {
                "speaker": "Reenu",
                "voice_persona": "Reenu: 22yo sweet, warm, charming young Kochi working woman voice, melodic cadence",
                "language": "Malayalam",
                "script": "ആരാ ഈ സമയത്ത്?",
                "line": "ആരാ ഈ സമയത്ത്?"
            },
            "audio_directive": "Reenu speaks. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voice dialogue and natural ambient foley sound effects only."
        }
    },
    # Shot 7 (Sachin panicking with bachelor mess)
    {
        "shot_number": 7,
        "duration": "6s",
        "duration_seconds": 6,
        "character": "Sachin",
        "dialogue_malayalam": "റീനു, നോക്കിക്കേ ഞാൻ പെട്ടെന്ന് ഇതൊന്ന് മാറ്റാം!",
        "action_summary": "In the living room, Sachin frantically hops down from the stool, scooping messy clothes and snack packets into a basket under the couch. Mouth moves in sync.",
        "json_prompt": {
            "style": MASTER_STYLE,
            "duration": "6s",
            "perspective": "Sachin scrambling to tidy up",
            "characters_present": [
                {"name": "Sachin", "visual_dna": DNA_SACHIN}
            ],
            "sequence_continuity": {
                "scene_id": "SCENE_KAKKANAD_LIVING_ROOM",
                "time_of_day": "Sunday Afternoon",
                "lighting_palette": "Warm golden hour sunlight streaming across cluttered rug",
                "weather": "Clear sunny weather",
                "spatial_blocking": {
                    "Sachin": "Crouched on knees shoving dirty laundry basket beneath couch"
                },
                "eyeline_direction": "Sachin glances anxiously back toward the entrance hallway",
                "persistent_props": PERSISTENT_PROPS,
                "camera_lens": "Cinematic prime lens, shallow depth of field"
            },
            "location": "Living room",
            "camera": "Medium shot",
            "action": "Sachin speaks in hurried comic panic while tidying. Lip sync matching words.",
            "dialogue": {
                "speaker": "Sachin",
                "voice_persona": "Sachin: 24yo endearing, youthful boyish Malayalam voice with frantic comedic whisper",
                "language": "Malayalam",
                "script": "റീനു, നോക്കിക്കേ ഞാൻ പെട്ടെന്ന് ഇതൊന്ന് മാറ്റാം!",
                "line": "റീനു, നോക്കിക്കേ ഞാൻ പെട്ടെന്ന് ഇതൊന്ന് മാറ്റാം!"
            },
            "audio_directive": "Sachin speaks. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voice dialogue and natural ambient foley sound effects only."
        }
    },
    # Shot 8 (Reenu opens door: Shock revelation)
    {
        "shot_number": 8,
        "duration": "6s",
        "duration_seconds": 6,
        "character": "Third-Person Narrator",
        "dialogue_malayalam": "വാതിൽ തുറന്ന റീനു ഞെട്ടിത്തരിച്ചുപോയി!",
        "action_summary": "Reenu pulls the front door wide open and freezes in sheer disbelief. Standing outside in the corridor are her stern father Kurian in starched Jubba and mother Annamma in green saree, flanked by huge suitcases! Lips closed.",
        "json_prompt": {
            "style": MASTER_STYLE,
            "duration": "6s",
            "perspective": "Third-Person Narrator",
            "characters_present": [
                {"name": "Reenu", "visual_dna": DNA_REENU},
                {"name": "Kurian (Reenu's Father)", "visual_dna": DNA_KURIAN},
                {"name": "Annamma (Reenu's Mother)", "visual_dna": DNA_ANNAMMA}
            ],
            "sequence_continuity": {
                "scene_id": "SCENE_KAKKANAD_DOORWAY_ENTRANCE",
                "time_of_day": "Sunday Afternoon",
                "lighting_palette": "Bright hallway corridor daylight framing parents against darker interior",
                "weather": "Clear sunny weather",
                "spatial_blocking": {
                    "Reenu": "Holding door handle inside, mouth open in silent gasp",
                    "Kurian (Reenu's Father)": "Standing tall in center corridor beside two large suitcases",
                    "Annamma (Reenu's Mother)": "Standing beside Kurian holding travel bag"
                },
                "eyeline_direction": "Reenu staring at parents; parents looking into apartment",
                "persistent_props": PERSISTENT_PROPS,
                "camera_lens": "Cinematic prime lens, shallow depth of field"
            },
            "location": "Apartment entrance doorway",
            "camera": "Over-the-shoulder medium shot",
            "action": "PURE VISUAL SCENE ACTION. Reenu gasps in silent shock. Parents stand imposing. Lips closed.",
            "dialogue": {
                "speaker": "Third-Person Narrator",
                "voice_persona": "Consistent Third-Person Female Narrator: 22-24yo charming South Indian Malayalam female storyteller voice, warm expressive sweet melodic tone, gentle youthful evocative Malayalam cadence, clear acoustic studio warmth",
                "language": "Malayalam",
                "script": "വാതിൽ തുറന്ന റീനു ഞെട്ടിത്തരിച്ചുപോയി!",
                "line": "വാതിൽ തുറന്ന റീനു ഞെട്ടിത്തരിച്ചുപോയി!"
            },
            "audio_directive": "EXTERNAL FEMALE VOICEOVER ONLY. NO CHARACTER SPEAKS ON SCREEN. All characters maintain strictly closed lips with zero talking or mouth animation. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voiceover audio and natural ambient foley sound effects only."
        }
    },
    # Shot 9 (The interior contrast: Sachin frozen)
    {
        "shot_number": 9,
        "duration": "6s",
        "duration_seconds": 6,
        "character": "Third-Person Narrator",
        "dialogue_malayalam": "മുന്നിൽ സ്യൂട്ട്കേസുമായി മാതാപിതാക്കൾ... ഉള്ളിൽ പതറി സച്ചിൻ!",
        "action_summary": "View looking from the doorway past Reenu into the living room: Sachin has scrambled back onto the stool trying to look innocent, clutching a tangled mess of lights like a deer caught in headlights. Lips closed.",
        "json_prompt": {
            "style": MASTER_STYLE,
            "duration": "6s",
            "perspective": "Third-Person Narrator",
            "characters_present": [
                {"name": "Reenu", "visual_dna": DNA_REENU},
                {"name": "Sachin", "visual_dna": DNA_SACHIN},
                {"name": "Kurian (Reenu's Father)", "visual_dna": DNA_KURIAN}
            ],
            "sequence_continuity": {
                "scene_id": "SCENE_KAKKANAD_DOORWAY_TO_LIVING_ROOM",
                "time_of_day": "Sunday Afternoon",
                "lighting_palette": "Golden sunlight illuminating frozen Sachin in living room",
                "weather": "Clear sunny weather",
                "spatial_blocking": {
                    "Kurian (Reenu's Father)": "Standing at threshold looking past Reenu",
                    "Reenu": "Standing frozen by doorway",
                    "Sachin": "Perched awkwardly on stool in background clutching fairy lights"
                },
                "eyeline_direction": "Kurian staring directly at Sachin; Sachin staring wide-eyed back",
                "persistent_props": PERSISTENT_PROPS,
                "camera_lens": "Cinematic prime lens, deep focus"
            },
            "location": "Doorway into living room",
            "camera": "Wide composition shot",
            "action": "PURE VISUAL SCENE ACTION. Sachin frozen completely motionless. Pure comedic tension. Closed lips.",
            "dialogue": {
                "speaker": "Third-Person Narrator",
                "voice_persona": "Consistent Third-Person Female Narrator: 22-24yo charming South Indian Malayalam female storyteller voice, warm expressive sweet melodic tone, gentle youthful evocative Malayalam cadence, clear acoustic studio warmth",
                "language": "Malayalam",
                "script": "മുന്നിൽ സ്യൂട്ട്കേസുമായി മാതാപിതാക്കൾ... ഉള്ളിൽ പതറി സച്ചിൻ!",
                "line": "മുന്നിൽ സ്യൂട്ട്കേസുമായി മാതാപിതാക്കൾ... ഉള്ളിൽ പതറി സച്ചിൻ!"
            },
            "audio_directive": "EXTERNAL FEMALE VOICEOVER ONLY. NO CHARACTER SPEAKS ON SCREEN. All characters maintain strictly closed lips with zero talking or mouth animation. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voiceover audio and natural ambient foley sound effects only."
        }
    },
    # Shot 10 (Cliffhanger: Kurian delivers killer question)
    {
        "shot_number": 10,
        "duration": "6s",
        "duration_seconds": 6,
        "character": "Kurian (Reenu's Father)",
        "dialogue_malayalam": "മോളേ... അകത്ത് നിൽക്കുന്ന ഈ പയ്യൻ ആരാ?",
        "action_summary": "Dramatic close-up on Kurian: he deliberately slides down his wire-rimmed reading glasses with one finger, his stern Kottayam eyes piercing straight at Sachin. Mouth moves in precise, icy lip sync.",
        "json_prompt": {
            "style": MASTER_STYLE,
            "duration": "6s",
            "perspective": "Kurian interrogating Reenu and Sachin",
            "characters_present": [
                {"name": "Kurian (Reenu's Father)", "visual_dna": DNA_KURIAN},
                {"name": "Sachin", "visual_dna": DNA_SACHIN}
            ],
            "sequence_continuity": {
                "scene_id": "SCENE_KAKKANAD_APARTMENT_THRESHOLD",
                "time_of_day": "Sunday Afternoon",
                "lighting_palette": "High contrast cinematic lighting focusing on Kurian's stern expression",
                "weather": "Clear sunny weather",
                "spatial_blocking": {
                    "Kurian (Reenu's Father)": "Dominating foreground, adjusting reading glasses",
                    "Sachin": "Visible in blurred background frozen on stool"
                },
                "eyeline_direction": "Kurian glaring down at Sachin with intense inspection",
                "persistent_props": PERSISTENT_PROPS,
                "camera_lens": "Cinematic prime lens, shallow depth of field"
            },
            "location": "Apartment entrance threshold",
            "camera": "Intense close-up shot",
            "action": "Kurian lowers glasses and speaks in slow, calculating baritone. Mouth moves in precise lip sync. Sachin in background is frozen.",
            "dialogue": {
                "speaker": "Kurian (Reenu's Father)",
                "voice_persona": "Kurian: Deep baritone Kottayam Christian dialect, formal, stern and calculating",
                "language": "Malayalam",
                "script": "മോളേ... അകത്ത് നിൽക്കുന്ന ഈ പയ്യൻ ആരാ?",
                "line": "മോളേ... അകത്ത് നിൽക്കുന്ന ഈ പയ്യൻ ആരാ?"
            },
            "audio_directive": "Kurian speaks. Characters in background remain completely silent with closed lips. CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voice dialogue and natural ambient foley sound effects only."
        }
    }
]

# Write to current_episode_shots.json
episode_payload = {
    "episode_number": 1,
    "title_malayalam": "അപ്രതീക്ഷിത കോളിംഗ് ബെൽ",
    "title_english": "The Surprise Calling Bell",
    "synopsis": "On a lazy Sunday afternoon in Reenu's Kakkanad apartment, Sachin is clumsily helping her hang fairy lights while playfully sharing snacks. The peaceful romance is shattered by an aggressive calling bell; Reenu opens the door to discover her conservative parents Kurian and Annamma standing in the hallway flanked by heavy VIP suitcases.",
    "cliffhanger": "Kurian lowers his reading glasses and peers past Reenu, locking eyes with Sachin frozen mid-air atop a wobbly plastic stool holding a tangled ball of lights: 'Moley... akathu nilkkunna ee payyan aara?'",
    "total_shots": 10,
    "calculated_total_seconds": 60,
    "calculated_runtime_display": "1m 00s",
    "new_characters_introduced": [
        {
            "name": "Kurian (Reenu's Father)",
            "role": "Reenu's traditional, hyper-vigilant father, a retired Central Government Treasury Officer",
            "age": 57,
            "gender": "male",
            "visual_dna": DNA_KURIAN,
            "locked_attire": "Crisp starched white cotton Jubba paired with a double-folded pristine white Mundu featuring a thin gold Kasavu border, brown leather sandals, and an analog Titan watch.",
            "voice_persona": "Deep baritone Kottayam Christian dialect, formal and calculating, shifting between stern cross-examinations and dry, deadpan sarcasm."
        },
        {
            "name": "Annamma (Reenu's Mother)",
            "role": "Reenu's observant, warm-hearted yet discerning mother",
            "age": 53,
            "gender": "female",
            "visual_dna": DNA_ANNAMMA,
            "locked_attire": "Handloom bottle-green cotton saree with mustard border, thin gold bangles that clink rhythmically, and a classic gold crucifix necklace.",
            "voice_persona": "Soft-spoken, melodic Central Travancore inflection, laced with maternal warmth, subtle guilt-tripping, and sharp observational wit."
        }
    ],
    "shots": shots_data,
    "season_number": 2,
    "is_new_season": True,
    "season_title": "Season 2: The Unexpected Guests (അപ്രതീക്ഷിത അതിഥികൾ)"
}

# Preserve season_arc from current file if present
current_file = Path("current_episode_shots.json")
if current_file.exists():
    with open(current_file, "r", encoding="utf-8") as f:
        old_data = json.load(f)
        if "season_arc" in old_data:
            episode_payload["season_arc"] = old_data["season_arc"]

with open("current_episode_shots.json", "w", encoding="utf-8") as f:
    json.dump(episode_payload, f, ensure_ascii=False, indent=2)

print("[OK] Saved refined 10-shot episode flow to current_episode_shots.json")
