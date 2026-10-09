import json
import re
import urllib.request
import urllib.parse
import os

print("1. Loading Episode 10 from current_episode_shots.json...")
with open("current_episode_shots.json", "r", encoding="utf-8") as f:
    ep_data = json.load(f)

print(f"Loaded: Episode {ep_data.get('episode_number')} - {ep_data.get('title_english')}")

GAS_URL = "https://script.google.com/macros/s/AKfycbyivkrK_jL1ejwNqUvHe8KVFNkSuJSwZbWSmuE1YATqL5jCneMlqlKbf0EH7mwpc4gybA/exec"

print("\n2. Pushing Episode 10 to Google Sheet via Web App API...")
payload = {
    "action": "update_next_episode_full",
    "episode_number": ep_data.get("episode_number", 10),
    "title_english": ep_data.get("title_english", "The Grand Climax: The Revelation"),
    "title_malayalam": ep_data.get("title_malayalam", "ആ രഹസ്യത്തിന്റെ ചുരുളഴിയുമ്പോൾ"),
    "synopsis": ep_data.get("synopsis", ""),
    "cliffhanger": ep_data.get("cliffhanger", "Sachin whispers: 'I\\'m never going back. I\\'m home.' Season 1 Climax completed!"),
    "total_shots": len(ep_data.get("shots", [])),
    "shots": ep_data.get("shots", [])
}

req_data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    GAS_URL,
    data=req_data,
    headers={"Content-Type": "text/plain"},
    method="POST"
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        res_text = resp.read().decode("utf-8")
        print("Google Sheet Response:", res_text[:200])
except Exception as e:
    print("Notice connecting to Google Sheet:", e)

print("\n3. Embedding Episode 10 into portal.html...")
with open("portal.html", "r", encoding="utf-8") as f:
    portal_html = f.read()

shots_json_str = json.dumps(ep_data, ensure_ascii=False, indent=2)

portal_html = re.sub(
    r'let episodeData = \{.*?\};\s+// Tracks current state',
    f'let episodeData = {shots_json_str};\n\n    // Tracks current state',
    portal_html,
    flags=re.DOTALL
)

paths = [
    "c:/Users/HP/OneDrive/Desktop/VISHNU/WEB/Sachin_And_Reenu_Series/portal.html",
    "c:/Users/HP/OneDrive/Desktop/VISHNU/WEB/Sachin_And_Reenu_Series/repo_studio/portal.html",
    "c:/Users/HP/OneDrive/Desktop/VISHNU/WEB/portal.html"
]

for p in paths:
    if os.path.exists(os.path.dirname(p)):
        with open(p, "w", encoding="utf-8") as f:
            f.write(portal_html)
        print(f"Updated: {p}")

print("\n✓ Successfully restored all portals and Google Sheet to Season 1 Finale (Episode 10)!")
