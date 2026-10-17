import urllib.request
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

GAS_URL = "https://script.google.com/macros/s/AKfycbyivkrK_jL1ejwNqUvHe8KVFNkSuJSwZbWSmuE1YATqL5jCneMlqlKbf0EH7mwpc4gybA/exec"
OUTLINE_PATH = Path(__file__).resolve().parent.parent / "season_3_shot_outline.json"

def sync_tab5():
    with open(OUTLINE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    shots = data.get("flattened_shots", [])
    episodes = data.get("episodes", [])
    season_number = data.get("season_number", 3)
    season_title = data.get("season_title", "Season 3: The Munnar Mystery")
    
    print(f"Loaded {len(shots)} shots for Season {season_number} ('{season_title}').")
    print(f"Sample Shot 1 positions: {shots[0].get('character_positions')}")
    print(f"Sample Shot 11 positions: {shots[10].get('character_positions')}")
    
    payload = {
        "action": "save_season_shot_outline",
        "season_number": season_number,
        "season_title": season_title,
        "shots": shots,
        "episodes": episodes
    }
    
    print(f"\nSending 100 shots with Character Positions to Google Apps Script...")
    req = urllib.request.Request(
        GAS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "text/plain; charset=utf-8", "User-Agent": "Mozilla/5.0"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            print("Response:", body)
            res = json.loads(body)
            if res.get("success"):
                print("✓ Successfully synchronized Tab 5 [Season_Shot_Outline] on Google Sheets!")
            else:
                print("Notice returned:", res)
    except Exception as e:
        print("Failed to sync Tab 5:", e)

    print("\nVerifying Tab 5 from live sheet...")
    get_req = urllib.request.Request(f"{GAS_URL}?action=get_season_shot_outline&season={season_number}", headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(get_req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            returned_shots = data.get("shots", [])
            print(f"Live Sheet returned {len(returned_shots)} shots.")
            if returned_shots:
                s11 = returned_shots[10] if len(returned_shots) > 10 else returned_shots[0]
                print(f"Shot {s11.get('shot_number')} (Ep {s11.get('episode_number')}):")
                print(f"  Action: {s11.get('action')[:80]}...")
                print(f"  Character Positions: {s11.get('character_positions')}")
    except Exception as e:
        print("Failed to verify live Tab 5:", e)

if __name__ == "__main__":
    sync_tab5()
