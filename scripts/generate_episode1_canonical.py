import json

SACHIN_DNA = (
    "Sachin: Handsome 22yo South Indian Malayali young man with messy wavy textured dark-brown hair styled with casual volume, "
    "warm dark-brown expressive doe eyes, clean defined jawline, charming boyish smile. "
    "Attire: Terracotta rust-orange crewneck t-shirt with subtle chest pocket, relaxed dark-gray joggers, black digital sports watch."
)

REENU_DNA = (
    "Reenu: Attractive 22yo South Indian Malayali girl with shoulder-length voluminous layered wavy dark-brown hair "
    "and soft curtain bangs, warm sparkling hazel-brown doe eyes, glowing radiant honey complexion. "
    "Attire: Classic pastel camouflage t-shirt in baby-blue and soft yellow cloud patches with sky-blue denim skirt."
)

AMAL_DNA = (
    "Amal: Witty 22yo South Indian Malayali friend with cropped soft curly black hair, "
    "neat trim mustache and subtle goatee beard, warm humorous brown eyes, and energetic cheerful smile. "
    "Attire: Sage olive-green crewneck t-shirt, blue denim jeans, black wristwatch."
)

NARRATOR_VOICE = "Consistent Third-Person Male Narrator: 30yo mature male storyteller voice, warm reflective baritone, gentle evocative cadence, studio acoustic clarity"

STYLE_DIRECTIVE = "Disney Pixar 3D animated film, vertical 9:16 format, hyper-detailed 3D CGI animation, Octane render 4k 60fps"
NO_BGM_DIRECTIVE = "CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean voice dialogue and natural ambient foley sound effects only."
NEG_PROMPT = "background music, musical score, singing, low resolution, 2D illustration, deformed faces, distorted anatomy, cutoff framing"

shots_raw = [
    {
        "shot_number": 1,
        "duration": "4s",
        "duration_seconds": 4,
        "character": "Third-Person Narrator",
        "perspective": "Third-Person Narrator",
        "characters_present": [
            {"name": "Reenu", "visual_dna": REENU_DNA}
        ],
        "location": "Inside Kochi CIAL Airport international arrival terminal hall. Polished reflective marble floor, modern glass sliding doors with green exit signage, chrome metal barrier railings, warm overhead ambient terminal lighting.",
        "camera": "Slow cinematic tilt-down from terminal ceiling to Reenu standing anxiously by the barrier, centered 55% in vertical 9:16 frame.",
        "action": "Reenu stands on her tiptoes behind the arrival barrier, holding onto the metal railing with trembling fingers as she scans the crowds.",
        "dialogue": {
            "speaker": "Third-Person Narrator",
            "voice_persona": NARRATOR_VOICE,
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "രണ്ടു നീണ്ട വർഷങ്ങൾ... കൊച്ചി വിമാനത്താവളത്തിന്റെ തിരക്കിലും, റീനുവിന്റെ മനസ്സിൽ ഒരു കടലിരമ്പമായിരുന്നു."
        }
    },
    {
        "shot_number": 2,
        "duration": "6s",
        "duration_seconds": 6,
        "character": "Amal & Reenu",
        "perspective": "Direct Character Dialogue",
        "characters_present": [
            {"name": "Reenu", "visual_dna": REENU_DNA},
            {"name": "Amal", "visual_dna": AMAL_DNA}
        ],
        "location": "Beside the passenger arrival barrier railing at Kochi CIAL terminal. Crowds waiting with welcome placards blurred in the background.",
        "camera": "Eye-level medium two-shot, smooth pan from Amal to Reenu, centered framing.",
        "action": "Amal nudges Reenu playfully on the shoulder with his elbow, grinning to break her anxious tension. Reenu bites her lip nervously.",
        "dialogue": {
            "speaker": "Amal",
            "voice_persona": "22yo energetic Malayali young man, witty teasing tone",
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "എന്താ റീനു, ഇങ്ങനെ പേടിക്കുന്നത്? അവൻ ലണ്ടനിൽ നിന്ന് വരില്ലെന്നാണോ?"
        }
    },
    {
        "shot_number": 3,
        "duration": "8s",
        "duration_seconds": 8,
        "character": "Reenu",
        "perspective": "Direct Character Dialogue",
        "characters_present": [
            {"name": "Reenu", "visual_dna": REENU_DNA}
        ],
        "location": "At the arrival barrier railings inside Kochi CIAL terminal, warm amber bokeh lights reflecting off polished floors.",
        "camera": "Intimate close-up on Reenu's expressive face, shallow depth of field, centered 55%.",
        "action": "Reenu fidgets with the strap of her bag, her hazel eyes glistening with raw emotional vulnerability as she speaks.",
        "dialogue": {
            "speaker": "Reenu",
            "voice_persona": "22yo attractive South Indian girl, sweet vulnerable tone, nervous flutter in voice",
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "രണ്ടു വർഷമായില്ലേ അമൽ... എനിക്കറിയില്ല, അവനെ കാണുമ്പോൾ എനിക്ക് ശ്വാസം കിട്ടുമോ എന്ന് പോലും പേടിയാകുന്നു."
        }
    },
    {
        "shot_number": 4,
        "duration": "4s",
        "duration_seconds": 4,
        "character": "Third-Person Narrator",
        "perspective": "Third-Person Narrator",
        "characters_present": [
            {"name": "Reenu", "visual_dna": REENU_DNA}
        ],
        "location": "The frosted-glass automatic sliding doors of the international arrival gate at Kochi CIAL airport.",
        "camera": "Low-angle dynamic push-in toward the sliding glass doors, dramatic depth of field.",
        "action": "The frosted glass doors glide open with a pneumatic whoosh, bright white light spilling into the darker waiting hall.",
        "dialogue": {
            "speaker": "Third-Person Narrator",
            "voice_persona": NARRATOR_VOICE,
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "അവസാനം... കാത്തിരിപ്പിന്റെ ആ വലിയ ചില്ലുവാതിലുകൾ പതുക്കെ തുറക്കപ്പെടുകയാണ്."
        }
    },
    {
        "shot_number": 5,
        "duration": "6s",
        "duration_seconds": 6,
        "character": "Amal",
        "perspective": "Direct Character Dialogue",
        "characters_present": [
            {"name": "Amal", "visual_dna": AMAL_DNA},
            {"name": "Sachin", "visual_dna": SACHIN_DNA}
        ],
        "location": "At the arrival gate threshold. Behind the barrier, Amal spots Sachin emerging with his silver luggage trolley.",
        "camera": "Dynamic over-the-shoulder tracking shot from behind Amal looking out at the gate, centered 55%.",
        "action": "Amal jumps up waving both hands in excitement, shouting over the airport ambient noise with a huge smile.",
        "dialogue": {
            "speaker": "Amal",
            "voice_persona": "22yo energetic Malayali friend, booming joyful shout",
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "ഡാ റീനൂ, ദേ നോക്ക്! അവൻ വരുന്നുണ്ട്!"
        }
    },
    {
        "shot_number": 6,
        "duration": "6s",
        "duration_seconds": 6,
        "character": "Third-Person Narrator",
        "perspective": "Third-Person Narrator",
        "characters_present": [
            {"name": "Sachin", "visual_dna": SACHIN_DNA},
            {"name": "Reenu", "visual_dna": REENU_DNA}
        ],
        "location": "Across the bustling Kochi CIAL arrival hall. Passengers with carts walking past in blurred slow motion.",
        "camera": "Cinematic whip-pan cutting between Sachin's searching eyes and Reenu's widening gaze, centered composition.",
        "action": "In slow motion, Sachin abruptly stops pushing his trolley as his eyes find Reenu in the distance. The world around them seems to freeze.",
        "dialogue": {
            "speaker": "Third-Person Narrator",
            "voice_persona": NARRATOR_VOICE,
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "ആയിരക്കണക്കിന് അപരിചിതർക്കിടയിൽ, അവരുടെ കണ്ണുകൾ ആ നിമിഷം പരസ്പരം കോർത്തു."
        }
    },
    {
        "shot_number": 7,
        "duration": "4s",
        "duration_seconds": 4,
        "character": "Sachin",
        "perspective": "Direct Character Dialogue",
        "characters_present": [
            {"name": "Sachin", "visual_dna": SACHIN_DNA}
        ],
        "location": "Terminal hall floor, next to his abandoned luggage trolley.",
        "camera": "Tight emotional portrait close-up on Sachin's face, golden airport lights illuminating his eyes.",
        "action": "Sachin leaves the trolley handle, his jaw slackening in breathless disbelief before a radiant boyish smile breaks across his face.",
        "dialogue": {
            "speaker": "Sachin",
            "voice_persona": "22yo handsome young man, soft breathless whisper",
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "റീനു..."
        }
    },
    {
        "shot_number": 8,
        "duration": "4s",
        "duration_seconds": 4,
        "character": "Reenu",
        "perspective": "Direct Character Dialogue",
        "characters_present": [
            {"name": "Reenu", "visual_dna": REENU_DNA}
        ],
        "location": "Behind the arrival barrier, hands slipping off the metal railing.",
        "camera": "Close-up dolly-in on Reenu, tears welling in her hazel eyes.",
        "action": "Reenu covers her mouth in sheer joy, a tear escaping down her glowing cheek as she calls his name.",
        "dialogue": {
            "speaker": "Reenu",
            "voice_persona": "22yo girl, emotional tear-choked cry of joy",
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "സച്ചിൻ!"
        }
    },
    {
        "shot_number": 9,
        "duration": "6s",
        "duration_seconds": 6,
        "character": "Third-Person Narrator",
        "perspective": "Third-Person Narrator",
        "characters_present": [
            {"name": "Sachin", "visual_dna": SACHIN_DNA},
            {"name": "Reenu", "visual_dna": REENU_DNA}
        ],
        "location": "The open corridor between arrival gate and visitor barrier inside CIAL airport.",
        "camera": "Tracking side-pan in slow motion following them as they run towards each other, centered 55%.",
        "action": "Sachin dashes forward, sneakers squeaking on the marble tiles. Reenu slips past the barrier opening and runs directly toward him.",
        "dialogue": {
            "speaker": "Third-Person Narrator",
            "voice_persona": NARRATOR_VOICE,
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "ആ നിമിഷം, ആ വിമാനത്താവളത്തിലെ മറ്റൊരു ശബ്ദവും അവർ കേൾക്കുന്നുണ്ടായിരുന്നില്ല."
        }
    },
    {
        "shot_number": 10,
        "duration": "8s",
        "duration_seconds": 8,
        "character": "Sachin & Reenu",
        "perspective": "Direct Character Dialogue",
        "characters_present": [
            {"name": "Sachin", "visual_dna": SACHIN_DNA},
            {"name": "Reenu", "visual_dna": REENU_DNA}
        ],
        "location": "Center of the arrival terminal hall, beneath soaring glass ceilings.",
        "camera": "Smooth 360-degree orbital camera rotation around the embracing couple, centered in middle 55% of vertical 9:16 frame.",
        "action": "Sachin sweeps Reenu into his arms, lifting her off her feet. Reenu buries her face into his neck, wrapping her arms tightly around his shoulders.",
        "dialogue": {
            "speaker": "Sachin",
            "voice_persona": "22yo young man, tender emotional whisper close to ear",
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "ഞാൻ വന്നു റീനൂ... ഇനി നിന്നെ വിട്ട് എങ്ങോട്ടുമില്ല."
        }
    },
    {
        "shot_number": 11,
        "duration": "6s",
        "duration_seconds": 6,
        "character": "Reenu",
        "perspective": "Direct Character Dialogue",
        "characters_present": [
            {"name": "Sachin", "visual_dna": SACHIN_DNA},
            {"name": "Reenu", "visual_dna": REENU_DNA}
        ],
        "location": "Terminal hall center, warm amber lighting falling upon their tear-streaked faces.",
        "camera": "Intimate over-the-shoulder close-up from Sachin's shoulder looking at Reenu's emotional face.",
        "action": "Reenu pulls back slightly, her hands framing Sachin's clean jawline, crying and laughing simultaneously.",
        "dialogue": {
            "speaker": "Reenu",
            "voice_persona": "22yo girl, breathless mixture of tears and overflowing joy",
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "എത്ര നാളായി സച്ചിൻ... ഞാൻ കാത്തിരുന്നതെന്നറിയുമോ?"
        }
    },
    {
        "shot_number": 12,
        "duration": "4s",
        "duration_seconds": 4,
        "character": "Third-Person Narrator",
        "perspective": "Third-Person Narrator",
        "characters_present": [
            {"name": "Sachin", "visual_dna": SACHIN_DNA},
            {"name": "Reenu", "visual_dna": REENU_DNA}
        ],
        "location": "Center of Kochi CIAL arrival hall, soft reflections on polished marble floor.",
        "camera": "Slow cinematic pull-back two-shot, centered vertical framing, shallow depth of field.",
        "action": "Sachin rests his forehead against Reenu's, their eyes closed as they breathe in the reassurance of being together again.",
        "dialogue": {
            "speaker": "Third-Person Narrator",
            "voice_persona": NARRATOR_VOICE,
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "വാക്കുകൾക്ക് അതീതമായി, രണ്ടു ഹൃദയങ്ങൾ ഒന്നിച്ചു തുടിച്ച് തുടങ്ങിയ നിമിഷം."
        }
    },
    {
        "shot_number": 13,
        "duration": "6s",
        "duration_seconds": 6,
        "character": "Amal",
        "perspective": "Direct Character Dialogue",
        "characters_present": [
            {"name": "Amal", "visual_dna": AMAL_DNA},
            {"name": "Sachin", "visual_dna": SACHIN_DNA},
            {"name": "Reenu", "visual_dna": REENU_DNA}
        ],
        "location": "Beside the passenger barrier railings, Amal leaning on the railing watching them.",
        "camera": "Medium three-shot, Amal in foreground smiling wryly, Sachin and Reenu behind him.",
        "action": "Amal crosses his arms, coughing comically into his fist and tapping his wristwatch with a teasing grin.",
        "dialogue": {
            "speaker": "Amal",
            "voice_persona": "22yo witty best friend, humorous teasing Malayali cadence",
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "മതി മതി... ഇവിടെ ആൾക്കാർ നോക്കുന്നുണ്ട്! ബാക്കി വീട്ടിൽ ചെന്നിട്ട്!"
        }
    },
    {
        "shot_number": 14,
        "duration": "6s",
        "duration_seconds": 6,
        "character": "Reenu & Sachin",
        "perspective": "Direct Character Dialogue",
        "characters_present": [
            {"name": "Reenu", "visual_dna": REENU_DNA},
            {"name": "Amal", "visual_dna": AMAL_DNA}
        ],
        "location": "Beside the airport barrier railing, crowds smiling at their reunion.",
        "camera": "Medium reaction shot, warm lighting, centered 55%.",
        "action": "Reenu wipes her tears with the back of her hand and playfully scowls at Amal, unable to stop giggling.",
        "dialogue": {
            "speaker": "Reenu",
            "voice_persona": "22yo girl, playful scolding tone with a bubbly laugh",
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "നീ ഒന്ന് മിണ്ടാതിരിക്ക് അമൽ! ഞങ്ങളുടെ സന്തോഷം കളയാൻ വന്നേക്കുന്നു!"
        }
    },
    {
        "shot_number": 15,
        "duration": "8s",
        "duration_seconds": 8,
        "character": "Sachin",
        "perspective": "Direct Character Dialogue",
        "characters_present": [
            {"name": "Sachin", "visual_dna": SACHIN_DNA},
            {"name": "Reenu", "visual_dna": REENU_DNA}
        ],
        "location": "Airport arrival hall corridor.",
        "camera": "Tight medium two-shot, slow push-in focusing on Sachin's tender smile.",
        "action": "Sachin gently tucks a strand of wavy hair behind Reenu's ear, looking at her with quiet adoration.",
        "dialogue": {
            "speaker": "Sachin",
            "voice_persona": "22yo young man, warm affectionate baritone",
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "നീ ഒട്ടും മാറിയിട്ടില്ല റീനൂ... ആ പഴയ കൊഞ്ചലും ചിരിയും ഇപ്പോഴും അതുപോലെയുണ്ട്."
        }
    },
    {
        "shot_number": 16,
        "duration": "6s",
        "duration_seconds": 6,
        "character": "Reenu",
        "perspective": "Direct Character Dialogue",
        "characters_present": [
            {"name": "Reenu", "visual_dna": REENU_DNA},
            {"name": "Sachin", "visual_dna": SACHIN_DNA}
        ],
        "location": "Terminal walkway, golden ambient lighting.",
        "camera": "Eye-level close-up on Reenu, soft rim light on her wavy brown hair.",
        "action": "Reenu inspects Sachin's face and terracotta t-shirt, tilting her head with an admiring smile.",
        "dialogue": {
            "speaker": "Reenu",
            "voice_persona": "22yo girl, teasing admiring tone",
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "പക്ഷേ നീ മാറിയിട്ടുണ്ട്... കുറച്ചുകൂടി സുന്ദരനായിട്ടുണ്ട്, കണ്ടാൽ തിരിച്ചറിയില്ല!"
        }
    },
    {
        "shot_number": 17,
        "duration": "4s",
        "duration_seconds": 4,
        "character": "Third-Person Narrator",
        "perspective": "Third-Person Narrator",
        "characters_present": [
            {"name": "Sachin", "visual_dna": SACHIN_DNA},
            {"name": "Reenu", "visual_dna": REENU_DNA}
        ],
        "location": "CIAL arrival walkway, warm golden reflections on polished floor tiles.",
        "camera": "Slow forward tracking shot, centered vertical framing, cinematic depth.",
        "action": "Sachin chuckles softly, shaking his head as he and Reenu share an intimate, knowing laugh.",
        "dialogue": {
            "speaker": "Third-Person Narrator",
            "voice_persona": NARRATOR_VOICE,
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "ഒരു ചെറിയ ചിരിയിൽ രണ്ടു വർഷത്തെ സങ്കടങ്ങളെല്ലാം മാഞ്ഞുപോയ നിമിഷം."
        }
    },
    {
        "shot_number": 18,
        "duration": "6s",
        "duration_seconds": 6,
        "character": "Amal",
        "perspective": "Direct Character Dialogue",
        "characters_present": [
            {"name": "Amal", "visual_dna": AMAL_DNA},
            {"name": "Sachin", "visual_dna": SACHIN_DNA}
        ],
        "location": "Luggage trolley pickup point near the glass sliding exit doors.",
        "camera": "Medium tracking shot following Amal as he pushes the trolley toward the exit, centered 55%.",
        "action": "Amal grabs the handle of Sachin's luggage trolley and pushes it forward with an energetic bounce.",
        "dialogue": {
            "speaker": "Amal",
            "voice_persona": "22yo energetic Malayali friend, lively conversational",
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "വാ, പുറത്ത് വണ്ടി ഇട്ടിട്ടുണ്ട്... മഴ കനക്കുന്നതിന് മുൻപ് ഇറങ്ങാം."
        }
    },
    {
        "shot_number": 19,
        "duration": "6s",
        "duration_seconds": 6,
        "character": "Third-Person Narrator",
        "perspective": "Third-Person Narrator",
        "characters_present": [
            {"name": "Sachin", "visual_dna": SACHIN_DNA},
            {"name": "Reenu", "visual_dna": REENU_DNA}
        ],
        "location": "Approaching the outer glass doors of CIAL airport, rain streaking down the exterior glass in the distance.",
        "camera": "Wide tracking shot from behind, following the couple walking side by side, centered framing.",
        "action": "Sachin and Reenu walk together side by side, Sachin's hand gently brushing Reenu's arm as they step toward the automatic glass exit.",
        "dialogue": {
            "speaker": "Third-Person Narrator",
            "voice_persona": NARRATOR_VOICE,
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "അവർ ഒന്നിച്ച് നടന്നു തുടങ്ങി... കാത്തിരിപ്പ് അവസാനിച്ച പുതിയൊരു ജീവിതത്തിലേക്ക്."
        }
    },
    {
        "shot_number": 20,
        "duration": "8s",
        "duration_seconds": 8,
        "character": "Third-Person Narrator",
        "perspective": "Third-Person Narrator",
        "characters_present": [
            {"name": "Sachin", "visual_dna": SACHIN_DNA}
        ],
        "location": "Near the terminal exit doors, reflections of rain and amber streetlamps on the glass.",
        "camera": "Close-up on Sachin's side profile, subtle tracking pan down to the black travel pouch slung across his shoulder.",
        "action": "As Reenu looks away toward the rain, Sachin's fingers slowly trace the zipper of his small black leather travel pouch, a sudden shadow of mystery crossing his eyes.",
        "dialogue": {
            "speaker": "Third-Person Narrator",
            "voice_persona": NARRATOR_VOICE,
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "എന്നാൽ, സച്ചിന്റെ ബാഗിനുള്ളിൽ... റീനുവിനോട് പറയാത്തൊരു വലിയ രഹസ്യവുമുണ്ടായിരുന്നു."
        }
    },
    {
        "shot_number": 21,
        "duration": "4s",
        "duration_seconds": 4,
        "character": "Third-Person Narrator",
        "perspective": "Third-Person Narrator",
        "characters_present": [
            {"name": "Sachin", "visual_dna": SACHIN_DNA}
        ],
        "location": "Close-up on the black leather travel pouch resting against Sachin's hip.",
        "camera": "Extreme macro close-up on the metal zipper and luggage tag stamped with 'LHR - LONDON HEATHROW', centered.",
        "action": "The pouch is slightly unzipped, revealing the corner of an ornate, velvet jewelry box tucked discreetly inside.",
        "dialogue": {
            "speaker": "Third-Person Narrator",
            "voice_persona": NARRATOR_VOICE,
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "ആ ലണ്ടൻ യാത്ര വെറുമൊരു മടങ്ങിവരവ് മാത്രമായിരുന്നില്ല."
        }
    },
    {
        "shot_number": 22,
        "duration": "4s",
        "duration_seconds": 4,
        "character": "Third-Person Narrator",
        "perspective": "Third-Person Narrator",
        "characters_present": [
            {"name": "Sachin", "visual_dna": SACHIN_DNA},
            {"name": "Reenu", "visual_dna": REENU_DNA}
        ],
        "location": "Stepping out through the CIAL terminal sliding doors into the cool mist of the Kochi monsoon night.",
        "camera": "Slow cinematic dolly-out, vertical 9:16 framing, glistening raindrops reflecting neon lights, 4k 60fps.",
        "action": "Sachin quickly looks back up at Reenu with an enigmatic, loving smile as they step out into the rain together, closing Episode 1 on an emotional cliffhanger.",
        "dialogue": {
            "speaker": "Third-Person Narrator",
            "voice_persona": NARRATOR_VOICE,
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": "ആ രഹസ്യം അവരുടെ സ്നേഹത്തെ എങ്ങോട്ടാണ് കൊണ്ടുപോകുന്നത്?"
        }
    }
]

# Build JSON prompt objects
for s in shots_raw:
    s["json_prompt"] = {
        "style": STYLE_DIRECTIVE,
        "duration": s["duration"],
        "perspective": s["perspective"],
        "characters_present": s["characters_present"],
        "location": s["location"],
        "camera": s["camera"],
        "action": s["action"],
        "dialogue": s["dialogue"],
        "audio_directive": NO_BGM_DIRECTIVE,
        "negative_prompt": NEG_PROMPT
    }
    s["dialogue_malayalam"] = s["dialogue"]["line"]
    s["action_summary"] = s["action"]

total_sec = sum(s["duration_seconds"] for s in shots_raw)

episode_1_data = {
    "episode_number": 1,
    "title_malayalam": "തിരിച്ചുവരവ്",
    "title_english": "The Homecoming",
    "synopsis": "After two long years of separation, Sachin returns from the UK to a nervous Reenu waiting with Amal at Kochi CIAL airport. Amidst the tearful, tender joy of their reunion, Sachin's subtle glance toward his travel pouch hints at a hidden secret brought from London.",
    "target_duration_seconds": total_sec,
    "total_shots": len(shots_raw),
    "calculated_total_seconds": total_sec,
    "calculated_runtime_display": f"{int(total_sec // 60)}m {int(total_sec % 60):02d}s",
    "shots": shots_raw
}

# Save current_episode_shots.json
with open('current_episode_shots.json', 'w', encoding='utf-8') as f:
    json.dump(episode_1_data, f, ensure_ascii=False, indent=2)

print(f"Generated Episode 1 dataset: {len(shots_raw)} shots, {episode_1_data['calculated_runtime_display']} (~{total_sec}s)")
