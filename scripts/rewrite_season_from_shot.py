from __future__ import annotations
import json, os, re, sys, time
from pathlib import Path
import requests
from google import genai
from google.genai import types

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
from universal_continuity_engine import compile_single_shot_prompt, UniversalSceneTracker

GAS_URL = os.environ["GAS_WEBHOOK_URL"]
SEASON = int(os.environ["SEASON_NUMBER"])
PIVOT = int(os.environ["PIVOT_GLOBAL_SHOT_ID"])
ACTIVE_EP = int(os.environ["ACTIVE_EPISODE"])
IDEA = os.environ["STORY_IDEA"]
ROADMAP = json.loads(os.environ["ROADMAP_JSON"])


def get_json(action: str, **params):
    response = requests.get(GAS_URL, params={"action": action, **params}, timeout=45)
    response.raise_for_status()
    data = response.json()
    if data.get("success") is False:
        raise RuntimeError(data.get("message", f"Google Apps Script {action} failed"))
    return data


def gemini_json(prompt: str, schema: dict, label: str):
    api_keys = []
    for name in ("GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3"):
        key = os.getenv(name, "").strip()
        if key and key not in api_keys:
            api_keys.append(key)
    if not api_keys:
        raise RuntimeError("No Gemini API key is configured in GitHub Actions secrets.")

    # Start with Google's current stable Flash model. Keep fallbacks because model
    # availability and capacity can vary by project and over time.
    models = ("gemini-3.8-flash", "gemini-3.5-flash", "gemini-3-flash-preview", "gemini-flash-latest")
    errors = []
    retryable_statuses = {429, 500, 502, 503, 504}
    for model in models:
        for key_index, api_key in enumerate(api_keys):
            client = genai.Client(api_key=api_key)
            for attempt in range(3):
                try:
                    result = client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=schema,
                            max_output_tokens=65536,
                        ),
                    )
                    if result.text:
                        parsed = json.loads(result.text)
                        print(f"{label} generated with {model} (key slot {key_index + 1})")
                        return parsed
                    raise RuntimeError("Gemini returned an empty response.")
                except Exception as exc:
                    status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                    if callable(status):
                        try:
                            status = status()
                        except Exception:
                            status = None
                    if status is None:
                        match = re.search(r"\b(400|401|403|404|429|500|502|503|504)\b", str(exc))
                        status = int(match.group(1)) if match else None
                    errors.append(f"{model} key-slot-{key_index + 1} attempt-{attempt + 1}: {exc}")
                    print(f"{label} attempt failed on {model} (key slot {key_index + 1}, attempt {attempt + 1}): {exc}")

                    # Invalid credentials/permissions are key-specific; try the next
                    # configured key without repeatedly sending the same bad request.
                    if status in {401, 403}:
                        break
                    # An unavailable/retired model should be skipped immediately.
                    if status == 404:
                        break
                    if status in retryable_statuses and attempt < 2:
                        delay = 2 ** (attempt + 1)
                        print(f"Retrying {model} in {delay}s after a temporary Gemini service error.")
                        time.sleep(delay)
                        continue
                    # Capacity/rate limits may differ by key; try the next configured key.
                    if status == 429:
                        break
                    # Don't spend more quota retrying permanent request/schema errors.
                    break
    raise RuntimeError(f"Gemini could not generate {label}: {' | '.join(errors)}")


def main():
    if not (1 <= PIVOT <= 100 and 1 <= ACTIVE_EP <= 10):
        raise ValueError("Pivot must be 1–100 and active episode 1–10.")
    if int(ROADMAP.get("season_number", SEASON)) != SEASON or len(ROADMAP.get("episodes", [])) != 10:
        raise ValueError("The confirmed roadmap must contain exactly ten episodes for the selected season.")

    live = get_json("get_season_shot_outline", season=SEASON)
    current = live.get("shots", [])
    if len(current) != 100:
        raise ValueError(f"Tab 5 must have exactly 100 shots; found {len(current)}.")
    current.sort(key=lambda s: int(s.get("global_shot_id", 0)))
    for index, shot in enumerate(current):
        if int(shot.get("global_shot_id", 0)) != index + 1:
            raise ValueError(f"Tab 5 has an invalid/missing global shot at position {index + 1}.")

    cast_data = get_json("get_characters")
    cast = cast_data.get("characters", [])
    if not cast:
        raise ValueError("Tab 4 returned no character registry; refusing to make prompts without its character details.")
    pivot_ep, pivot_shot = divmod(PIVOT - 1, 10)
    tail = current[PIVOT - 1:]
    proposal_episodes = ROADMAP["episodes"]
    prompt = f'''You are the showrunner for the Malayalam cinematic animated series Sachin & Reenu.
The creator has CONFIRMED this whole-season direction: {IDEA}
Confirmed 10-episode season roadmap (story guidance): {json.dumps(proposal_episodes, ensure_ascii=False)}
Before drafting, infer the season's central dramatic question, each lead's want/flaw, the opposing pressure, and the emotional stakes from this confirmed premise and roadmap. Escalate consequences and character choices across the affected episodes; give each episode a distinct objective, obstacle, turning point, emotional shift, and cliffhanger. Use the roadmap as guidance, not a beat-by-beat template.
Rewrite only the following Tab 5 range: Global Shot {PIVOT} through Global Shot 100 ({len(tail)} shots).
The current shot at the pivot is the story starting point, and all preceding shots are frozen context.
Frozen preceding shots for continuity only: {json.dumps(current[:PIVOT-1], ensure_ascii=False)}
Current shots to replace in order: {json.dumps(tail, ensure_ascii=False)}
Use the existing Tab 4 character registry without changing it: {json.dumps(cast, ensure_ascii=False)}. Do not introduce new characters; speaker must be a character in that registry or Third-Person Narrator.
Return JSON object {{"shots":[...]}} with EXACTLY {len(tail)} shots. Each shot must have global_shot_id, episode_number, shot_number, speaker, action, dialogue_malayalam, location, persistent_props (array), camera_hint. Preserve the same global_shot_id, episode_number, and shot_number positions. Give each shot one primary visible action and one readable emotion that can be staged in about six seconds; avoid packing several actions/cuts into one beat. Use visual behavior, eyelines, silence, environment, and props to reveal information. Each camera_hint must give a motivated frame/angle and at most one purposeful move (or a deliberate locked frame); vary shot scale and composition. Stage transitions with clear screen direction, positions, props, and cause-and-effect. Give each affected episode a distinct dramatic rhythm rather than repeating a fixed shot template. Make every episode Shot 10 a specific, earned cliffhanger/turn in Episodes 1–9; the next episode's Shot 1 must show its immediate consequence and preserve the scene state. Episode 10 Shot 10 must pay off the season's central dramatic question and character arcs. Keep character identity and the existing Tab 4 attire consistent. Use natural spoken Malayalam: target 3–8 words and never exceed 10 words per spoken line; a silent visual shot may have an empty dialogue field. The speaker is already in its own field, so dialogue_malayalam must contain only spoken words: never prefix it with the speaker's name/label (such as "Sachin:"), acting directions, parenthetical notes, or quotation marks. A character's name may appear only when naturally addressed in the spoken line. Before returning, silently audit every affected episode's dramatic progression, Shot 10-to-Shot 1 handoff, filmability, camera variation, and dialogue rules. Never change the frozen shots.'''
    schema = {"type": "OBJECT", "properties": {"shots": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
        "global_shot_id": {"type": "INTEGER"}, "episode_number": {"type": "INTEGER"}, "shot_number": {"type": "INTEGER"},
        "speaker": {"type": "STRING"}, "action": {"type": "STRING"}, "dialogue_malayalam": {"type": "STRING"}, "location": {"type": "STRING"},
        "persistent_props": {"type": "ARRAY", "items": {"type": "STRING"}}, "camera_hint": {"type": "STRING"}
    }, "required": ["global_shot_id", "episode_number", "shot_number", "speaker", "action", "dialogue_malayalam", "location", "persistent_props", "camera_hint"]}}}, "required": ["shots"]}
    generated = gemini_json(prompt, schema, "Tab 5 season rewrite")
    rewritten = generated.get("shots", [])
    if len(rewritten) != len(tail):
        raise ValueError(f"Gemini returned {len(rewritten)} shots; expected {len(tail)}.")
    final = [dict(s) for s in current[:PIVOT-1]]
    position_repairs = []
    for offset, shot in enumerate(rewritten):
        expected_id = PIVOT + offset
        expected_ep, expected_shot = divmod(expected_id - 1, 10)
        # The response array is requested in strict shot order. Gemini occasionally
        # mislabels an otherwise valid row's position (often at episode boundaries).
        # The array index is the stable source of truth, so repair the three position
        # fields deterministically instead of aborting the entire season rewrite.
        if not isinstance(shot, dict):
            raise ValueError(f"Gemini returned a non-object at expected Global Shot {expected_id}.")
        returned_position = (shot.get("global_shot_id"), shot.get("episode_number"), shot.get("shot_number"))
        expected_position = (expected_id, expected_ep + 1, expected_shot + 1)
        if tuple(str(value) for value in returned_position) != tuple(str(value) for value in expected_position):
            position_repairs.append(f"{expected_id}: {returned_position} -> {expected_position}")
        shot["global_shot_id"], shot["episode_number"], shot["shot_number"] = expected_position
        if not str(shot.get("action") or "").strip():
            raise ValueError(f"Gemini returned empty action content at Global Shot {expected_id}.")
        if not isinstance(shot.get("persistent_props"), list):
            raise ValueError(f"Gemini returned invalid persistent_props at Global Shot {expected_id}; expected an array.")
        for field in ("speaker", "dialogue_malayalam", "location", "camera_hint"):
            if not isinstance(shot.get(field), str):
                raise ValueError(f"Gemini returned invalid {field} content at Global Shot {expected_id}.")
        shot["season_number"] = SEASON
        shot["global_shot_id"] = expected_id
        shot["persistent_props"] = shot.get("persistent_props") or []
        dialogue = str(shot.get("dialogue_malayalam") or "").strip()
        dialogue_words = dialogue.split()
        if len(dialogue_words) > 10:
            raise ValueError(f"Dialogue at Global Shot {expected_id} exceeds the 10-word limit; no update was saved.")
        speaker = str(shot.get("speaker") or "").strip()
        if speaker and dialogue.casefold().startswith(f"{speaker.casefold()}:"):
            raise ValueError(f"Dialogue at Global Shot {expected_id} repeats the speaker label; no update was saved.")
        if dialogue.startswith(("(", "[") ) or '"' in dialogue or "“" in dialogue or "”" in dialogue:
            raise ValueError(f"Dialogue at Global Shot {expected_id} contains stage directions or quotation marks; no update was saved.")
        if not str(shot.get("camera_hint") or "").strip():
            raise ValueError(f"Global Shot {expected_id} is missing a motivated camera hint; no update was saved.")
        final.append(shot)
    if position_repairs:
        print(f"Normalized {len(position_repairs)} Gemini shot-position label(s) using the requested output order:")
        for repair in position_repairs:
            print(f"  {repair}")

    # Keep all prefix rows byte-for-byte as received and rebuild episode structures.
    outline_path = ROOT / f"season_{SEASON}_shot_outline.json"
    existing = json.loads(outline_path.read_text(encoding="utf-8")) if outline_path.exists() else {}
    episodes = existing.get("episodes", [])
    if len(episodes) != 10:
        episodes = [{"episode_number": i + 1, "title_english": f"Episode {i+1}", "shots": []} for i in range(10)]
    for ep_i, ep in enumerate(episodes):
        if ep_i >= pivot_ep:
            proposed = proposal_episodes[ep_i]
            for key in ("title_english", "title_malayalam", "synopsis", "cliffhanger"):
                if proposed.get(key): ep[key] = proposed[key]
        ep["episode_number"] = ep_i + 1
        ep["shots"] = [dict(s, season_number=SEASON, episode_number=ep_i+1) for s in final[ep_i*10:(ep_i+1)*10]]
    flattened = []
    for ep in episodes:
        title = f"{ep.get('title_malayalam','')} ({ep.get('title_english','')})".strip()
        for shot in ep["shots"]:
            flattened.append({**shot, "episode_title": title})
    outline = {**existing, "season_number": SEASON, "season_title": ROADMAP.get("season_title") or existing.get("season_title") or f"Season {SEASON}",
               "episodes": episodes, "flattened_shots": flattened, "total_shots": 100}
    outline_path.write_text(json.dumps(outline, ensure_ascii=False, indent=2), encoding="utf-8")

    prompt_shots = []
    active_start_global = (ACTIVE_EP - 1) * 10 + 1
    active_end_global = ACTIVE_EP * 10
    if active_end_global >= PIVOT:
        start_global = max(PIVOT, active_start_global)
        active_rows = final[start_global - 1:active_end_global]
        registry = {str(c.get("name", "")).casefold(): c for c in cast}
        tracker = UniversalSceneTracker()
        # Prime continuity with any unchanged earlier episode shots.
        for old in final[active_start_global - 1:start_global - 1]:
            compile_single_shot_prompt(int(old["shot_number"]), str(old.get("speaker") or "Narrator"), str(old.get("dialogue_malayalam") or ""),
                str(old.get("action") or ""), str(old.get("location") or "Kochi"), old.get("persistent_props") or [], old.get("camera_hint"), tracker)
        for row in active_rows:
            speaker = str(row.get("speaker") or "Third-Person Narrator")
            action = str(row.get("action") or "")
            shot_num = int(row["shot_number"])
            jp = compile_single_shot_prompt(shot_num, speaker, str(row.get("dialogue_malayalam") or ""), action,
                str(row.get("location") or "Kochi"), row.get("persistent_props") or [], row.get("camera_hint"), tracker)
            # Replace generated character DNA with the unchanged live Tab 4 entries.
            names = {speaker.casefold()}
            names.update(name.casefold() for name in registry if name and name.casefold() in action.casefold())
            present = []
            for name in names:
                character = registry.get(name)
                if character:
                    present.append({"name": character.get("name", name), "visual_dna": character.get("visual_dna", "")})
            if present:
                jp["characters_present"] = present
            prompt_shots.append({"shot_number": shot_num, "duration": "6s", "character": speaker,
                "dialogue_malayalam": row.get("dialogue_malayalam", ""), "action_summary": action, "json_prompt": jp})

    # Save generated active-episode prompts in repo for audit. Apps Script preserves prior Tab 2 rows itself.
    current_ep_file = ROOT / "current_episode_shots.json"
    current_ep = json.loads(current_ep_file.read_text(encoding="utf-8")) if current_ep_file.exists() else {}
    if prompt_shots:
        live_prompts = get_json("get_current_episode_prompts").get("shots", [])
        first_rewritten_shot = int(prompt_shots[0]["shot_number"])
        preserved_prompt_prefix = [s for s in live_prompts if int(s.get("shot_number", 0)) < first_rewritten_shot]
        prompt_shots = preserved_prompt_prefix + prompt_shots
        current_ep.update({"season_number": SEASON, "episode_number": ACTIVE_EP, "title_english": episodes[ACTIVE_EP-1].get("title_english"),
            "title_malayalam": episodes[ACTIVE_EP-1].get("title_malayalam", ""), "synopsis": episodes[ACTIVE_EP-1].get("synopsis", ""), "shots": prompt_shots})
        current_ep_file.write_text(json.dumps(current_ep, ensure_ascii=False, indent=2), encoding="utf-8")

    state_path = ROOT / "story_state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    state[f"season_{SEASON}_shot_outline"] = outline
    state["season_shot_outline"] = outline
    state["season_number"] = SEASON
    state["season_title"] = outline["season_title"]
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    payload = {"action": "apply_director_season_rewrite", "season_number": SEASON, "season_title": outline["season_title"],
               "pivot_global_shot_id": PIVOT, "active_episode": ACTIVE_EP, "shots": final, "prompts": prompt_shots}
    response = requests.post(GAS_URL, data=json.dumps(payload, ensure_ascii=False), headers={"Content-Type": "text/plain"}, timeout=120)
    response.raise_for_status()
    result = response.json()
    if result.get("success") is not True:
        raise RuntimeError(result.get("message", "Apps Script did not confirm the Tab 5/Tab 2 update."))
    print(result.get("message", "Tab 5 and Tab 2 synchronized."))

if __name__ == "__main__":
    main()
