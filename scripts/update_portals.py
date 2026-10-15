import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Load current episode shots
with open('current_episode_shots.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

# Normalize into full episodeData object
if isinstance(raw_data, list):
    shots_list = raw_data
    ep_num = 1
    season_num = 3
    title_en = "Episode 1"
    title_ml = ""
    synopsis = ""
    cliffhanger = ""
    if os.path.exists('story_state.json'):
        try:
            with open('story_state.json', 'r', encoding='utf-8') as sf:
                st = json.load(sf)
                ep_num = st.get("episode_number") or st.get("current_episode", {}).get("episode_number", 1)
                season_num = st.get("season_number", 3)
                cur_ep = st.get("current_episode", {})
                title_en = cur_ep.get("title_english") or f"Episode {ep_num}"
                title_ml = cur_ep.get("title_malayalam", "")
                synopsis = cur_ep.get("synopsis", "")
                cliffhanger = cur_ep.get("cliffhanger", "")
        except Exception:
            pass
    ep_obj = {
        "episode_number": ep_num,
        "season_number": season_num,
        "is_season_2": season_num == 2,
        "title_english": title_en,
        "title_malayalam": title_ml,
        "synopsis": synopsis,
        "cliffhanger": cliffhanger,
        "total_shots": len(shots_list),
        "calculated_runtime_display": f"{len(shots_list)*6 // 60}m {len(shots_list)*6 % 60:02d}s",
        "shots": shots_list,
        "prompts": shots_list
    }
else:
    ep_obj = raw_data
    if "shots" not in ep_obj and "prompts" in ep_obj:
        ep_obj["shots"] = ep_obj["prompts"]

# Load existing base portal.html
with open('portal.html', 'r', encoding='utf-8') as f:
    base_html = f.read()

# Replace episodeData
shots_json_str = json.dumps(ep_obj, ensure_ascii=False, indent=2)
updated_html = re.sub(
    r'let episodeData = (?:\[.*?\]|\{.*?\});\s+// Tracks current state',
    lambda m: f'let episodeData = {shots_json_str};\n\n    // Tracks current state',
    base_html,
    flags=re.DOTALL
)

# Ensure overlay is hidden by default
updated_html = updated_html.replace(
    '<div id="studioLoaderOverlay" class="studio-loader-overlay">',
    '<div id="studioLoaderOverlay" class="studio-loader-overlay hidden">'
)

# Load story_state.json for dynamic character wardrobe & season story arc
state_path = Path('story_state.json')
if state_path.exists():
    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)

        season_num = state.get('season_number', 2)
        chars = state.get('characters', {})

        default_roles = {
            "Reenu": "Lead Female",
            "Sachin": "Lead Male",
            "Amal": "Best Friend / Comic Anchor",
            "Annamma": "Reenu's Mother",
            "Kurian": "Reenu's Father",
            "Broker Shaji": "Kochi Real Estate Broker"
        }
        default_voices = {
            "Reenu": "Sweet, expressive 22yo South Indian Malayali female voice, warm, gentle, clear studio warmth.",
            "Sachin": "Endearing, slightly nervous young Malayali male voice, warm, playful, sincere, clear studio cadence.",
            "Amal": "Youthful energetic Malayali male voice, friendly, casual, slightly teasing tone, natural cheerful energy."
        }

        registry_list = []
        ordered_names = ["Reenu", "Sachin", "Amal", "Annamma", "Kurian", "Broker Shaji"]
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
                "visual_dna": vdna or f"{cname}: Stylized 3D cartoon animation character (Strictly non-human realism).",
                "locked_attire": attire or "Locked signature costume. Absolutely zero variations.",
                "voice_persona": voice
            })

        char_reg_str = json.dumps(registry_list, ensure_ascii=False, indent=2)
        updated_html = re.sub(
            r'let characterRegistryData = \[.*?\];',
            lambda m: f'let characterRegistryData = {char_reg_str};',
            updated_html,
            flags=re.DOTALL
        )

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
                lambda m: f'let seasonStoryData = {season_story_str};',
                updated_html,
                flags=re.DOTALL
            )
            print("✓ Updated seasonStoryData and characterRegistryData from story_state.json!")

        outline_obj = state.get(f"season_{season_num}_shot_outline") or state.get("season_shot_outline") or state.get("season_outline")
        if Path(f"season_{season_num}_shot_outline.json").exists():
            try:
                outline_obj = json.loads(Path(f"season_{season_num}_shot_outline.json").read_text(encoding="utf-8"))
            except Exception:
                pass
        if outline_obj:
            outline_str = json.dumps(outline_obj, ensure_ascii=False, indent=2)
            if "let seasonShotOutlineData = {" in updated_html:
                updated_html = re.sub(
                    r'let seasonShotOutlineData = \{.*?\};',
                    lambda m: f'let seasonShotOutlineData = {outline_str};',
                    updated_html,
                    flags=re.DOTALL
                )
                print("✓ Updated seasonShotOutlineData from story_state.json!")

    except Exception as e:
        print(f"Notice updating character registry from story_state.json: {e}")

# Target paths across project workspace
target_paths = [
    Path("portal.html"),
    Path("c:/Users/HP/OneDrive/Desktop/VISHNU/WEB/Sachin_And_Reenu_Series/portal.html"),
    Path("c:/Users/HP/OneDrive/Desktop/VISHNU/WEB/Sachin_And_Reenu_Series/repo_studio/portal.html"),
    Path("c:/Users/HP/OneDrive/Desktop/VISHNU/WEB/portal.html"),
    Path("c:/Users/HP/OneDrive/Desktop/New folder (3)/portal.html"),
    Path("c:/Users/HP/OneDrive/Desktop/New folder (3)/index.html")
]

for p in target_paths:
    try:
        if p.exists() or p.parent.exists():
            p.write_text(updated_html, encoding='utf-8')
            print(f"Updated: {p}")
    except Exception as e:
        print(f"Notice skipping {p}: {e}")

print("All portals successfully updated with valid episodeData and instant-load fixes!")
