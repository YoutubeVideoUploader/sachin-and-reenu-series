import json
import os
import sys
from pathlib import Path

# Add scripts directory to path if needed
sys.path.insert(0, str(Path(__file__).parent))
from story_and_prompt_engine import enforce_prompt_completeness, get_active_character_dna_map, sync_new_episode_to_google_sheet

shots_file = Path("current_episode_shots.json")
if not shots_file.exists():
    print("current_episode_shots.json not found!")
    sys.exit(1)

with open(shots_file, "r", encoding="utf-8") as f:
    data = json.load(f)

season_num = data.get("season_number", 2)
active_dna = get_active_character_dna_map(season_num=season_num)

print(f"Active DNA resolved for Season {season_num}:")
for k in active_dna:
    print(f"  - {k}")

# Re-enforce prompts with dynamic season wardrobe
updated_data = enforce_prompt_completeness(data, active_dna)

with open(shots_file, "w", encoding="utf-8") as f:
    json.dump(updated_data, f, ensure_ascii=False, indent=2)
print("✓ Updated current_episode_shots.json with active season wardrobe!")

# Run update_portals.py
import subprocess
subprocess.run([sys.executable, "scripts/update_portals.py"], check=True)
print("✓ Updated all portal.html instances!")

# Also sync to Google Apps Script if URL available
gas_url = os.getenv("GAS_WEBHOOK_URL", "")
if not gas_url and Path(".env").exists():
    try:
        from dotenv import load_dotenv
        load_dotenv()
        gas_url = os.getenv("GAS_WEBHOOK_URL", "")
    except Exception:
        pass

if gas_url:
    print(f"Syncing updated prompts and wardrobe to Google Apps Script...")
    sync_new_episode_to_google_sheet(gas_url, updated_data)
else:
    print("Notice: GAS_WEBHOOK_URL not available for remote sync.")
