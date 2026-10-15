#!/usr/bin/env python3
"""
audit_and_fix_columns.py
Standardizes and harmonizes all columns across all 100 shots of Season 3:
1. Normalizes Speaker names (Renu -> Reenu, Mist -> Sachin, Shadow -> Amal).
2. Normalizes Malayalam character spelling (രേണു -> റീനു).
3. Standardizes dialogue formatting: Speaker: (Performance note) 'Dialogue text'.
4. Cleans Persistent Props (removes non-props like Bed in mud, Mist, Wall, Door; adds actual physical props).
5. Ensures Location accuracy and naming consistency.
6. Refines Visual Action transitions for seamless narrative pacing and zero tonal fractures.
"""

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTLINE_PATH = REPO_ROOT / "season_3_shot_outline.json"


def clean_malayalam_text(text: str) -> str:
    if not text:
        return ""
    # Normalize രേണു to റീനു
    text = text.replace("രേണു", "റീനു")
    # Clean redundant spaces
    text = re.sub(r' +', ' ', text).strip()
    return text


def run():
    with open(OUTLINE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    episodes = data.get("episodes", [])
    flattened_shots = []

    for ep in episodes:
        ep_num = ep.get("episode_number")
        shots = ep.get("shots", [])

        for s in shots:
            sh_num = s.get("shot_number")
            speaker = s.get("speaker", "").strip()
            action = s.get("action", "").strip()
            dia = s.get("dialogue_malayalam", "").strip()
            loc = s.get("location", "").strip()
            props = list(s.get("persistent_props", []))

            # --- 1. SPEAKER NORMALIZATION ---
            if speaker in ["Renu", "റീനു", "രേണു"]:
                speaker = "Reenu"
            elif ep_num == 7 and sh_num == 7 and speaker == "Mist":
                speaker = "Sachin"
            elif ep_num == 7 and sh_num == 8 and speaker == "Shadow":
                speaker = "Amal"

            # --- 2. MALAYALAM SPELLING NORMALIZATION ---
            dia = clean_malayalam_text(dia)
            action = action.replace("Renu", "Reenu").replace("രേണു", "റീനു")

            # --- 3. DIALOGUE FORMATTING & MULTI-SPEAKER CLEANUP ---
            # Ep 3 Shot 1: Caretaker's chilling warning only
            if ep_num == 3 and sh_num == 1:
                dia = "കെയർടേക്കർ: (തണുത്ത സ്വരത്തിൽ) 'താക്കോലുകൾ ഇതാ... പക്ഷേ ഓർക്കുക, ആ ഇടനാഴിയുടെ അറ്റത്തുള്ള പതിമൂന്നാം നമ്പർ മുറി... ഒരിക്കലും ആരും തുറക്കരുത്.'"
            elif ep_num == 3 and sh_num == 2:
                dia = "സച്ചിൻ: (കിതപ്പ് അടക്കിക്കൊണ്ട്) 'പുറത്ത് ആ ഇരുട്ടിൽ എന്തോ ഒന്നുണ്ടായിരുന്നു... എന്നിട്ടും ഇയാൾ ഈ മുറി പൂട്ടി സൂക്ഷിക്കാൻ പറയുന്നു! ഇതിനുള്ളിൽ എന്താ ഇത്ര വലിയ രഹസ്യം?'"
            elif ep_num == 7 and sh_num == 1:
                # Timeline fix: not "before sunset" since it's already deep night
                dia = "റീനു: (വിറയ്ക്കുന്ന കൈകളോടെ കത്ത് മുറുകെപ്പിടിച്ച്, ദൃഢനിശ്ചയത്തോടെ) 'ഈ കുറിപ്പ് വെറുമൊരു ഭീഷണിയല്ല സച്ചിൻ... ആ പഴയ പാലത്തിൽ എന്തോ ഒളിഞ്ഞിരിപ്പുണ്ട്. നേരം വെളുക്കും മുൻപ് നമ്മൾ അവിടേക്ക് പോയി സത്യം അറിയണം!'"
            elif ep_num == 7 and sh_num == 5:
                dia = "അമൽ: (പേടിച്ചോടിവന്ന്, കിതച്ചുകൊണ്ട്) 'അയ്യോ നിൽക്കാനൊന്നും പറ്റില്ല! അവിടെ എന്നെ തനിച്ചാക്കി പോന്നതല്ലേ... ദാ, പുറകിൽ ഏതോ ഒരുത്തൻ നമ്മളെ നോക്കി വരുന്നുണ്ട്! ഓടിക്കോ!'"
            elif ep_num == 7 and sh_num == 6:
                dia = "സച്ചിൻ: (ദേഷ്യത്തോടെ, ബാഗ് പിടിച്ചുവാങ്ങിക്കൊണ്ട്) 'അത് എന്റെ ബാഗാണ്, പൊട്ടാ! അവിടുന്ന് ഏതോ പ്രേതം ചാടിവീഴാൻ നിൽക്കുമ്പോഴാ നിന്റെ ഒരു ബാഗ് പിടുത്തം!'"
            elif ep_num == 7 and sh_num == 7:
                dia = "സച്ചിൻ: (വിറച്ചുകൊണ്ട്, റീനുവിനെ നോക്കി അലറുന്നു) 'എന്റെ പൊന്നോ... ഇത് സാധാരണ കോടയല്ല! പാലമൊക്കെ ആടുന്നുണ്ട്, വേഗം ഓട്!'"
            elif ep_num == 7 and sh_num == 8:
                dia = "അമൽ: (വിറച്ചുകൊണ്ട്, വിരൽ ചൂണ്ടിക്കൊണ്ട്) 'അങ്ങോട്ട്... അങ്ങോട്ട് എന്തോ നമ്മളെ നോക്കുന്നുണ്ട്! എന്റെ അമ്മോ, എന്നെ തിരിച്ചു വിട്!'"
            elif ep_num == 6 and sh_num == 1:
                dia = "അമൽ: (വിറച്ചുകൊണ്ട്, ഫോൺ ഉയർത്തിക്കാട്ടി) 'അയ്യോ, പേടിക്കണ്ട... നോക്കിക്കേ, ഇതാണ് എന്റെ ആത്മ-സംവേദന ഉപകരണം! കിടിലൻ ഐഡിയ അല്ലേ?'"
            elif ep_num == 6 and sh_num == 2:
                dia = "സച്ചിൻ: (ദേഷ്യവും ഭയവും കലർന്ന്) 'അതൊരു ശബ്ദമായിരുന്നു! നീ ഇവിടെ വന്ന് റീൽസ് ഉണ്ടാക്കുകയാണോ കുന്തേ?! ഞങ്ങളിവിടെ പേടിച്ചു ചാവുന്നു!'"
            elif ep_num == 6 and sh_num == 3:
                dia = "റീനു: (ഗൗരവത്തോടെ, ടോർച്ച് അടിച്ചു കാണിച്ച്) 'അമലിന്റെ കളി നിർത്തിയിട്ട് ഇങ്ങോട്ട് നോക്ക്. ഇത് എന്താ ഇവിടെ ഈ ഭിത്തിയിൽ?'"

            # --- 4. PERSISTENT PROPS ACCURACY ---
            # Remove environment items like Bed in mud, Mist, Wall, Door, Path, Debris
            cleaned_props = []
            for p in props:
                if p not in ["Bed", "Mist", "Room", "Hallway", "Path", "Wall", "Door", "Debris"]:
                    cleaned_props.append(p)

            # Assign accurate physical props per shot context
            if ep_num == 3 and sh_num == 1:
                cleaned_props = ["Keys"]
            elif ep_num == 3 and sh_num == 2:
                cleaned_props = ["Keys", "Padlock"]
            elif ep_num == 3 and sh_num == 3:
                cleaned_props = ["Flashlight", "Shawl"]
            elif ep_num == 3 and sh_num == 4:
                cleaned_props = ["Flashlight"]
            elif ep_num == 3 and sh_num == 5:
                cleaned_props = ["Travel bag", "Candlestick"]
            elif ep_num == 3 and sh_num == 6:
                cleaned_props = ["Blanket", "Candlestick"]
            elif ep_num == 3 and sh_num == 7:
                cleaned_props = ["Candlestick"]
            elif ep_num == 3 and sh_num == 8:
                cleaned_props = ["Hoodie", "Flashlight"]
            elif ep_num == 3 and sh_num == 9:
                cleaned_props = ["Velvet curtain"]
            elif ep_num == 3 and sh_num == 10:
                cleaned_props = ["Padlock", "Velvet curtain"]
            elif ep_num == 4 and sh_num == 1:
                cleaned_props = ["Smartphone", "Old photo"]
            elif ep_num == 4 and sh_num == 6:
                cleaned_props = ["Smartphone"]
            elif ep_num == 4 and sh_num == 7:
                cleaned_props = ["Smartphone"]
            elif ep_num == 4 and sh_num == 8:
                cleaned_props = ["Smartphone"]
            elif ep_num == 5 and sh_num == 1:
                cleaned_props = ["Silver-framed photo", "Camera"]
            elif ep_num == 5 and sh_num == 2:
                cleaned_props = ["Smartphone"]
            elif ep_num == 5 and sh_num == 3:
                cleaned_props = ["Silver-framed photo"]
            elif ep_num == 5 and sh_num == 4:
                cleaned_props = ["Smartphone"]
            elif ep_num == 5 and sh_num == 5:
                cleaned_props = ["Flashlight"]  # Notebook is discovered in shot 6!
            elif ep_num == 5 and sh_num == 6:
                cleaned_props = ["Old ledger", "Flashlight"]
            elif ep_num == 5 and sh_num == 7:
                cleaned_props = ["Iron pipe", "Flashlight"]
            elif ep_num == 5 and sh_num == 8:
                cleaned_props = ["Drawing", "Iron pipe", "Flashlight"]
            elif ep_num == 5 and sh_num == 9:
                cleaned_props = ["Drawing", "Flashlight"]
            elif ep_num == 5 and sh_num == 10:
                cleaned_props = ["Flashlight", "Smartphone"]
            elif ep_num == 6 and sh_num == 1:
                cleaned_props = ["Smartphone", "Stick", "Flashlight"]
            elif ep_num == 6 and sh_num == 2:
                cleaned_props = ["Flashlight", "Smartphone"]
            elif ep_num == 6 and sh_num == 3:
                cleaned_props = ["Flashlight"]
            elif ep_num == 6 and sh_num == 4:
                cleaned_props = ["Smartphone", "Flashlight"]
            elif ep_num == 6 and sh_num == 5:
                cleaned_props = ["Flashlight", "Backpack"]
            elif ep_num == 6 and sh_num == 6:
                cleaned_props = ["Smartphone", "Footprints"]
            elif ep_num == 6 and sh_num == 7:
                cleaned_props = ["Smartphone", "Footprints"]  # Removed Bed!
            elif ep_num == 6 and sh_num == 8:
                cleaned_props = ["Deadbolt", "Candlestick"]
            elif ep_num == 6 and sh_num == 9:
                cleaned_props = ["Candlestick"]
            elif ep_num == 6 and sh_num == 10:
                cleaned_props = ["Note", "Candlestick", "Oil lamp"]
            elif ep_num == 7 and sh_num == 1:
                cleaned_props = ["Note", "Oil lamp"]
            elif ep_num == 7 and sh_num == 2:
                cleaned_props = ["Smartphone", "Blanket"]
            elif ep_num == 7 and sh_num == 3:
                cleaned_props = ["Flashlight"]
            elif ep_num == 7 and sh_num == 4:
                cleaned_props = ["Locket", "Flashlight"]
            elif ep_num == 7 and sh_num == 5:
                cleaned_props = ["Red Backpack", "Flashlight"]
            elif ep_num == 7 and sh_num == 6:
                cleaned_props = ["Red Backpack", "Flashlight"]
            elif ep_num == 7 and sh_num == 7:
                cleaned_props = ["Red Backpack", "Flashlight"]  # Removed Mist!
            elif ep_num == 7 and sh_num == 8:
                cleaned_props = ["Flashlight"]
            elif ep_num == 7 and sh_num == 9:
                cleaned_props = ["Flashlight", "Locket"]
            elif ep_num == 7 and sh_num == 10:
                cleaned_props = ["Flashlight"]
            elif ep_num == 8 and sh_num == 3:
                cleaned_props = ["Flashlight", "Salt"]
            elif ep_num == 8 and sh_num == 6:
                cleaned_props = ["Box", "Clippings"]
            elif ep_num == 8 and sh_num == 8:
                cleaned_props = ["Letter", "Flashlight"]
            elif ep_num == 8 and sh_num == 9:
                cleaned_props = ["Letter", "Flashlight"]
            elif ep_num == 9 and sh_num == 2:
                cleaned_props = ["Evidence", "Letter", "Locket"]
            elif ep_num == 9 and sh_num == 3:
                cleaned_props = ["Evidence", "Letter", "Locket"]
            elif ep_num == 9 and sh_num == 5:
                cleaned_props = ["Evidence", "Letter", "Locket"]
            elif ep_num == 9 and sh_num == 6:
                cleaned_props = ["Evidence", "Letter", "Locket"]
            elif ep_num == 9 and sh_num == 7:
                cleaned_props = ["Evidence", "Letter", "Locket"]
            elif ep_num == 9 and sh_num == 8:
                cleaned_props = ["Evidence", "Letter", "Locket"]
            elif ep_num == 9 and sh_num == 9:
                cleaned_props = ["Evidence", "Letter", "Locket"]
            elif ep_num == 10 and sh_num == 2:
                cleaned_props = ["Flashlight"]
            elif ep_num == 10 and sh_num == 6:
                cleaned_props = ["Evidence", "Flashlight"]
            elif ep_num == 10 and sh_num == 7:
                cleaned_props = ["Evidence", "Flashlight"]

            # --- 5. LOCATION CONSISTENCY ---
            if ep_num == 3 and sh_num in [1, 2]:
                loc = "Homestay hallway"
            elif ep_num == 3 and sh_num in [3, 4]:
                loc = "Homestay hallway, outside Room 13"
            elif ep_num == 3 and sh_num in [5, 6, 7]:
                loc = "Homestay - Bedroom"
            elif ep_num == 3 and sh_num in [8, 9, 10]:
                loc = "Homestay hallway, outside Room 13"

            # --- 6. VISUAL ACTION CONTINUITY REFINEMENTS ---
            # Ep 6 Shot 1: Seamless bridge from Ep 5 Shot 10 ghost whisper
            if ep_num == 6 and sh_num == 1:
                action = (
                    "Wide Shot (WS) transitioning to Close-Up (CU), Pixar 3D Camera: The terrifying female whisper from the high factory rafters still echoes in the freezing air. Sachin and Reenu cling to each other, Sachin's flashlight beam trembling wildly across the rusted machinery. Suddenly, the beam illuminates Amal huddled near a massive gear shaft. Terrified out of his wits, Amal is frantically waving his smartphone duct-taped to a tree branch like an improvised ghost-detector, trying to mask his overwhelming dread with hysterical comedic bluster."
                )

            # Update shot object
            s["speaker"] = speaker
            s["action"] = action
            s["dialogue_malayalam"] = dia
            s["location"] = loc
            s["persistent_props"] = cleaned_props

            # Flattened copy
            flat_s = dict(s)
            flat_s["season_number"] = 3
            flat_s["episode_number"] = ep_num
            flat_s["episode_title"] = ep.get("title_malayalam", ep.get("title_english", ""))
            flat_s["title_malayalam"] = ep.get("title_malayalam", "")
            flattened_shots.append(flat_s)

    data["flattened_shots"] = flattened_shots

    # Write back outline
    with open(OUTLINE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[SUCCESS] Successfully audited and harmonized all {len(flattened_shots)} shots in {OUTLINE_PATH}")


if __name__ == "__main__":
    run()
