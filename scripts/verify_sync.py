import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
gas_url = 'https://script.google.com/macros/s/AKfycbyivkrK_jL1ejwNqUvHe8KVFNkSuJSwZbWSmuE1YATqL5jCneMlqlKbf0EH7mwpc4gybA/exec'

print("=== VERIFYING TAB 2 (Current_JSON_Prompts) ===")
res2 = requests.get(gas_url + '?action=get_all_data').json()
print("Tab 2 Episode:", res2.get('episode') or res2.get('episode_number'))
for s in res2.get('shots', []):
    print(f"Shot {s.get('shot_number')}: {s.get('character')} | '{s.get('dialogue_malayalam')}'")

print("\n=== VERIFYING TAB 7 (Season_Shot_Outline) ===")
res7 = requests.get(gas_url + '?action=get_season_shot_outline').json()
print("Tab 7 Total Shots:", len(res7.get('shots', [])))
for s in res7.get('shots', []):
    if s.get('episode_number') == 2:
        print(f"Ep 2 Shot {s.get('shot_number')}: {s.get('speaker')} | '{s.get('dialogue_malayalam')}'")
