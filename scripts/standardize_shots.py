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

with open('current_episode_shots.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for s in data['shots']:
    char_name = s.get('character', '')
    chars_list = []
    
    # Determine who is present
    has_reenu = 'Reenu' in char_name or 'Reenu' in s.get('action_summary', '') or 'Reenu' in s.get('flow_prompt', '')
    has_sachin = 'Sachin' in char_name or 'Sachin' in s.get('action_summary', '') or 'Sachin' in s.get('flow_prompt', '')
    has_amal = 'Amal' in char_name or 'Amal' in s.get('action_summary', '') or 'Amal' in s.get('flow_prompt', '')

    if has_reenu:
        chars_list.append({"name": "Reenu", "visual_dna": REENU_DNA})
    if has_sachin:
        chars_list.append({"name": "Sachin", "visual_dna": SACHIN_DNA})
    if has_amal:
        chars_list.append({"name": "Amal", "visual_dna": AMAL_DNA})

    if not chars_list:
        chars_list.append({"name": char_name, "visual_dna": REENU_DNA if 'Reenu' in char_name else SACHIN_DNA})

    loc = s.get('json_prompt', {}).get('location_details', '')
    if not loc or len(loc) < 15:
        if s['shot_number'] <= 9:
            loc = "Outside CIAL airport arrival terminal pickup curb under heavy Kochi monsoon rain. Wet glistening asphalt reflecting warm amber streetlights and neon lights, rain pouring from glass canopy."
        else:
            loc = "Inside Amal's cozy sedan car traveling on the rain-slicked Kochi highway. Heavy raindrops streaming across car side windows, warm golden cabin dome light, blurred neon city bokeh outside."

    cam = s.get('json_prompt', {}).get('camera_direction', '')
    if not cam or len(cam) < 10:
        cam = f"{s.get('camera', 'Cinematic shot')}, centered framing in middle 55% of vertical 9:16 frame."

    diag_text = s.get('dialogue_malayalam', '')
    speaker = s.get('character', 'None')
    if not diag_text:
        speaker = "None"

    # Construct the exact canonical JSON prompt object
    s['json_prompt'] = {
        "style": "Disney Pixar 3D animated film, vertical 9:16 format, hyper-detailed 3D CGI animation, Octane render 4k 60fps",
        "duration": s['duration'],
        "characters_present": chars_list,
        "location": loc,
        "camera": cam,
        "action": s.get('action_summary', ''),
        "dialogue": {
            "speaker": speaker,
            "language": "Malayalam",
            "script": "മലയാളം ലിപി",
            "line": diag_text if diag_text else "None (Silent visual emotion)"
        },
        "audio_directive": "CRITICAL: ABSOLUTELY NO BACKGROUND MUSIC. NO INSTRUMENTAL BGM. NO MUSIC SCORE. Clean Malayalam voice dialogue and natural ambient foley sound effects only.",
        "negative_prompt": "background music, musical score, singing, low resolution, 2D illustration, deformed faces, distorted anatomy, cutoff framing"
    }

with open('current_episode_shots.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Standardized all 22 shots with canonical json_prompt objects!")
