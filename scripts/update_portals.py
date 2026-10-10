import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Load current episode shots
with open('current_episode_shots.json', 'r', encoding='utf-8') as f:
    ep_data = json.load(f)

# Load existing base portal.html
with open('portal.html', 'r', encoding='utf-8') as f:
    base_html = f.read()

# Replace episodeData
shots_json_str = json.dumps(ep_data, ensure_ascii=False, indent=2)
updated_html = re.sub(
    r'let episodeData = \{.*?\};\s+// Tracks current state',
    f'let episodeData = {shots_json_str};\n\n    // Tracks current state',
    base_html,
    flags=re.DOTALL
)

# Load story_state.json for dynamic character wardrobe & season story arc
state_path = Path('story_state.json')
if state_path.exists():
    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)

        season_num = state.get('season_number', 1)
        chars = state.get('characters', {})

        # Default fallbacks
        default_roles = {
            "Reenu": "Lead Female",
            "Sachin": "Lead Male",
            "Amal": "Best Friend / Comic Anchor",
            "Roy (Reenu's Father)": "Reenu's Father (Retired Bank Manager)",
            "Molly (Reenu's Mother)": "Reenu's Mother",
            "Madhavan": "Reenu's Father",
            "Girija": "Reenu's Mother"
        }
        default_voices = {
            "Reenu": "Sweet, expressive 22yo South Indian Malayali female voice, warm, gentle, clear studio warmth.",
            "Sachin": "Endearing, slightly nervous young Malayali male voice, warm, playful, sincere, clear studio cadence.",
            "Amal": "Youthful energetic Malayali male voice, friendly, casual, slightly teasing tone, natural cheerful energy."
        }

        # Build clean character registry
        registry_list = []
        # Ensure lead characters first
        ordered_names = ["Reenu", "Sachin", "Amal"]
        for cname in chars.keys():
            if cname not in ordered_names:
                ordered_names.append(cname)

        for cname in ordered_names:
            cinfo = chars.get(cname, {})
            attire = cinfo.get("attire") or cinfo.get("locked_attire", "")
            vdna = cinfo.get("visual_dna", "")
            first_app = "Season 1 • Ep 1" if cname in ["Reenu", "Sachin", "Amal"] else f"Season {season_num} • Ep 1"
            role = cinfo.get("role") or default_roles.get(cname, "Supporting Character")
            voice = cinfo.get("voice") or default_voices.get(cname, "Expressive Malayalam voice")

            registry_list.append({
                "name": cname,
                "role": role,
                "first_appearance": first_app,
                "status": "Active",
                "visual_dna": vdna or f"{cname}: Stylized 3D Pixar-style cartoon animation character (Strictly non-human realism).",
                "locked_attire": attire or "Locked signature costume. Absolutely zero variations.",
                "voice_persona": voice
            })

        char_reg_str = json.dumps(registry_list, ensure_ascii=False, indent=2)
        updated_html = re.sub(
            r'let characterRegistryData = \[.*?\];',
            f'let characterRegistryData = {char_reg_str};',
            updated_html,
            flags=re.DOTALL
        )

        # Update seasonStoryData if season_arc is present
        if state.get("season_arc"):
            season_story_obj = {
                "season_number": season_num,
                "season_title": state.get("season_title", f"Season {season_num}"),
                "total_episodes": len(state.get("season_arc", [])),
                "climax_target_episode": 10,
                "episodes": state.get("season_arc", [])
            }
            season_story_str = json.dumps(season_story_obj, ensure_ascii=False, indent=2)
            updated_html = re.sub(
                r'let seasonStoryData = \{.*?\};',
                f'let seasonStoryData = {season_story_str};',
                updated_html,
                flags=re.DOTALL
            )
            print("✓ Updated seasonStoryData and characterRegistryData from story_state.json!")

    except Exception as e:
        print(f"Notice updating character registry from story_state.json: {e}")

# Target paths across project workspace
target_paths = [
    Path("portal.html"),
    Path("c:/Users/HP/OneDrive/Desktop/VISHNU/WEB/Sachin_And_Reenu_Series/portal.html"),
    Path("c:/Users/HP/OneDrive/Desktop/VISHNU/WEB/Sachin_And_Reenu_Series/repo_studio/portal.html"),
    Path("c:/Users/HP/OneDrive/Desktop/VISHNU/WEB/portal.html")
]

for p in target_paths:
    try:
        if p.exists() or p.parent.exists():
            p.write_text(updated_html, encoding='utf-8')
            print(f"Updated: {p}")
    except Exception as e:
        print(f"Notice skipping {p}: {e}")

print("All portals successfully updated with dynamic episode prompts and character wardrobe!")
