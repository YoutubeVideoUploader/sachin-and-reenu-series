import json
import re
from pathlib import Path

def build_season_3_outline():
    raw_path = Path("s3_outline_raw.txt")
    if not raw_path.exists():
        print("Error: s3_outline_raw.txt not found")
        return

    with open(raw_path, "r", encoding="utf-8") as f:
        text = f.read()

    lines = text.split("\n")
    flat_shots = []
    
    for l in lines:
        line = l.strip()
        if not line or line.startswith("<"):
            continue
        if "Season #" in line and "Episode #" in line:
            continue
        parts = [p.strip() for p in line.split("\t")]
        if len(parts) >= 6 and parts[0] in ["3", "Season 3"]:
            s_num = int(parts[0].replace("Season", "").strip())
            ep_num = int(parts[1])
            shot_num = int(parts[2])
            raw_title = parts[3]
            speaker = parts[4]
            action = parts[5]
            dialogue = parts[6] if len(parts) > 6 else ""
            location = parts[7] if len(parts) > 7 else ""
            props_str = parts[8] if len(parts) > 8 else ""
            status = parts[9] if len(parts) > 9 else "Upcoming"
            if "Upcoming" in status:
                status = "Upcoming"
            elif "Active" in status:
                status = "Active"

            props = [p.strip() for p in props_str.split(",") if p.strip() and p.strip().lower() != "none"]

            m = re.match(r"^(.*?)\s*\((.*?)\)$", raw_title)
            if m:
                title_mal = m.group(1).strip()
                title_eng = m.group(2).strip()
            else:
                title_mal = raw_title
                title_eng = raw_title

            flat_shots.append({
                "season_number": s_num,
                "episode_number": ep_num,
                "shot_number": shot_num,
                "episode_title": raw_title,
                "title_malayalam": title_mal,
                "title_english": title_eng,
                "speaker": speaker,
                "action": action,
                "dialogue_malayalam": dialogue,
                "location": location,
                "persistent_props": props,
                "status": status
            })

    print(f"Parsed {len(flat_shots)} flat shots.")

    # Group into episodes
    episodes_map = {}
    for s in flat_shots:
        episodes_map.setdefault(s["episode_number"], []).append(s)

    episodes = []
    for ep_num in sorted(episodes_map.keys()):
        shots_in_ep = episodes_map[ep_num]
        title_eng = shots_in_ep[0]["title_english"]
        title_mal = shots_in_ep[0]["title_malayalam"]

        # Formulate synopsis from the shots
        synopsis = f"{shots_in_ep[0]['action']} {shots_in_ep[4]['action']}"
        cliffhanger = shots_in_ep[-1]["action"] + f" Dialogue: '{shots_in_ep[-1]['dialogue_malayalam']}'"

        formatted_shots = []
        for s in shots_in_ep:
            camera_hint = "Dynamic cinematic 3D medium shot"
            if "close" in s["action"].lower() or "look" in s["action"].lower() or "whisper" in s["action"].lower():
                camera_hint = "Cinematic 3D close-up with expressive emotional focus"
            elif "road" in s["location"].lower() or "mist" in s["action"].lower() or "mountain" in s["action"].lower():
                camera_hint = "Wide atmospheric cinematic 3D shot with mist and high-range depth"
            elif "car" in s["location"].lower():
                camera_hint = "Interior car medium shot, dynamic angle"

            formatted_shots.append({
                "shot_number": s["shot_number"],
                "speaker": s["speaker"],
                "action": s["action"],
                "dialogue_malayalam": s["dialogue_malayalam"],
                "location": s["location"],
                "persistent_props": s["persistent_props"],
                "camera_hint": camera_hint
            })

        episodes.append({
            "episode_number": ep_num,
            "title_english": title_eng,
            "title_malayalam": title_mal,
            "synopsis": synopsis,
            "cliffhanger": cliffhanger,
            "shots": formatted_shots
        })

    master_outline = {
        "season_number": 3,
        "season_title": "Season 3: The Munnar Trip (മൂന്നാർ യാത്ര)",
        "total_episodes": len(episodes),
        "total_shots": len(flat_shots),
        "episodes": episodes,
        "flattened_shots": flat_shots
    }

    out_file = Path("season_3_shot_outline.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(master_outline, f, ensure_ascii=False, indent=2)

    print(f"[SUCCESS] Created {out_file} with {len(episodes)} episodes and {len(flat_shots)} shots!")

if __name__ == "__main__":
    build_season_3_outline()
