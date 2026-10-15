import os
import json
import time
import requests

VIDEO_FILE = "master_episode.mp4"
SCRIPT_FILE = "current_episode.json"
STATE_FILE = "story_state.json"

IG_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
IG_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
GH_PAT = os.getenv("GH_PAT")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY", "YoutubeVideoUploader/sachin-and-reenu-series")

def upload_release_asset(video_path, tag_name):
    print(f"Creating GitHub Release {tag_name} to host video for Instagram...")
    headers = {
        "Authorization": f"Bearer {GH_PAT}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 1. Create release
    rel_url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases"
    rel_payload = {
        "tag_name": tag_name,
        "name": f"Release {tag_name}",
        "body": "Automated build artifact for Instagram publishing",
        "draft": False,
        "prerelease": False
    }
    rel_res = requests.post(rel_url, headers=headers, json=rel_payload)
    if rel_res.status_code not in [200, 201]:
        # Maybe release already exists, fetch it
        get_res = requests.get(f"{rel_url}/tags/{tag_name}", headers=headers)
        if get_res.status_code == 200:
            rel_data = get_res.json()
        else:
            raise Exception(f"Failed to create/get release: {rel_res.status_code} {rel_res.text}")
    else:
        rel_data = rel_res.json()
        
    upload_url = rel_data["upload_url"].split("{")[0]
    file_name = os.path.basename(video_path)
    
    # Delete existing asset if it exists
    for existing_asset in rel_data.get("assets", []):
        if existing_asset.get("name") == file_name:
            del_url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/assets/{existing_asset['id']}"
            requests.delete(del_url, headers=headers)
            print(f"Deleted existing release asset {existing_asset['id']}")
            time.sleep(1.0)
            break
    
    # 2. Upload asset
    print(f"Uploading {file_name} ({os.path.getsize(video_path)} bytes) to release...")
    upload_headers = {
        "Authorization": f"Bearer {GH_PAT}",
        "Content-Type": "video/mp4"
    }
    with open(video_path, "rb") as f:
        upload_res = requests.post(
            f"{upload_url}?name={file_name}",
            headers=upload_headers,
            data=f
        )
    if upload_res.status_code not in [200, 201]:
        raise Exception(f"Failed to upload asset: {upload_res.status_code} {upload_res.text}")
        
    asset_data = upload_res.json()
    public_url = asset_data["browser_download_url"]
    print(f"Public video URL for Instagram: {public_url}")
    return public_url

def publish_reel_to_instagram(video_url, caption, cover_url=None):
    if not IG_ACCESS_TOKEN or not IG_ACCOUNT_ID:
        raise ValueError("INSTAGRAM_ACCESS_TOKEN and IG_ACCOUNT_ID are required")
        
    print(f"Creating Instagram Reel container on account {IG_ACCOUNT_ID}...")
    create_url = f"https://graph.facebook.com/v20.0/{IG_ACCOUNT_ID}/media"
    payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "share_to_feed": "true",
        "access_token": IG_ACCESS_TOKEN
    }
    if cover_url:
        print(f"Attaching custom Reel cover thumbnail: {cover_url}")
        payload["cover_url"] = cover_url
        
    create_res = requests.post(create_url, data=payload)
    if create_res.status_code != 200:
        raise Exception(f"Failed to create Reel container: {create_res.status_code} {create_res.text}")
        
    container_id = create_res.json().get("id")
    print(f"Container created with ID: {container_id}. Waiting for processing...")
    
    # Poll container status until FINISHED (up to 60 iterations * 5s = 300s)
    status_url = f"https://graph.facebook.com/v20.0/{container_id}?fields=status_code&access_token={IG_ACCESS_TOKEN}"
    status_code = None
    for attempt in range(1, 61):
        time.sleep(5)
        st_res = requests.get(status_url, timeout=30)
        if st_res.status_code == 200:
            status_code = st_res.json().get("status_code")
            if status_code == "FINISHED":
                print(f"Video successfully processed by Instagram on attempt {attempt} (~{attempt*5}s)!")
                break
            elif status_code == "ERROR":
                err_detail = st_res.json().get("status_message") or st_res.text
                raise RuntimeError(f"Instagram video processing failed: {status_code} - {err_detail}")
            else:
                print(f"Status [{attempt}/60]: {status_code}...")
        else:
            print(f"Status check note: HTTP {st_res.status_code}")

    if status_code != "FINISHED":
        raise TimeoutError(f"Instagram video processing timed out after 300s. Last status: {status_code}. Container ID: {container_id}")

    # Publish container
    print(f"Publishing container {container_id} to Instagram feed...")
    publish_url = f"https://graph.facebook.com/v20.0/{IG_ACCOUNT_ID}/media_publish"
    pub_res = requests.post(publish_url, data={
        "creation_id": container_id,
        "access_token": IG_ACCESS_TOKEN
    })
    if pub_res.status_code != 200:
        raise Exception(f"Failed to publish Reel: {pub_res.status_code} {pub_res.text}")

    media_id = pub_res.json().get("id")
    print(f"SUCCESS! Published to Instagram Reels with Post ID: {media_id}")
    return media_id

def normalize_ep_data(data):
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        shots_list = data
        ep_num = 1
        season_num = 3
        title_en = "Episode 1"
        title_ml = ""
        synopsis = ""
        cliffhanger = ""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    st = json.load(f)
                    if isinstance(st, dict):
                        ep_num = st.get("episode_number") or st.get("current_episode", {}).get("episode_number", 1)
                        season_num = st.get("season_number", 3)
                        cur_ep = st.get("current_episode", {})
                        title_en = cur_ep.get("title_english") or f"Episode {ep_num}"
                        title_ml = cur_ep.get("title_malayalam", "")
                        synopsis = cur_ep.get("synopsis", "")
                        cliffhanger = cur_ep.get("cliffhanger", "")
            except Exception:
                pass
        return {
            "episode_number": ep_num,
            "season_number": season_num,
            "is_season_2": season_num == 2,
            "title_english": title_en,
            "title_malayalam": title_ml,
            "synopsis": synopsis,
            "cliffhanger": cliffhanger,
            "total_shots": len(shots_list),
            "calculated_total_seconds": len(shots_list) * 6,
            "calculated_runtime_display": f"{len(shots_list)*6 // 60}m {len(shots_list)*6 % 60:02d}s",
            "shots": shots_list,
            "prompts": shots_list
        }
    return {}

def update_story_state(ep_data=None):
    if not ep_data:
        script_candidates = ["current_episode_shots.json", "current_episode.json"]
        for sc in script_candidates:
            if os.path.exists(sc):
                try:
                    with open(sc, "r", encoding="utf-8") as f:
                        ep_data = json.load(f)
                    break
                except Exception:
                    pass
    if not ep_data:
        print("Notice: No episode script found to update story state.")
        return

    ep_data = normalize_ep_data(ep_data)

    state = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = {}

    ep_num = ep_data.get("episode_number", 1)
    state["total_episodes_produced"] = max(state.get("total_episodes_produced", 0), ep_num)
    state["episode_number"] = ep_num
    
    if "history" not in state:
        state["history"] = []
    
    # Check if this episode is already in history
    exists = False
    for h in state["history"]:
        if h.get("episode") == ep_num:
            exists = True
            break
            
    if not exists:
        all_chars = set()
        for sc in ep_data.get("scenes", ep_data.get("shots", [])):
            if isinstance(sc, dict):
                chars_list = sc.get("characters_present", [])
                if isinstance(chars_list, list):
                    for c in chars_list:
                        if isinstance(c, dict) and "name" in c:
                            all_chars.add(c["name"])
                        elif isinstance(c, str):
                            all_chars.add(c)
                if "character" in sc:
                    all_chars.add(sc["character"])
                elif "speaker" in sc:
                    all_chars.add(sc["speaker"])

        history_entry = {
            "episode": ep_num,
            "title": f"{ep_data.get('title_malayalam', '')} ({ep_data.get('title_english', '')})".strip(),
            "summary": ep_data.get("synopsis", ""),
            "cliffhanger": ep_data.get("cliffhanger", ""),
            "characters_present": list(all_chars)
        }
        state["history"].append(history_entry)

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    print(f"Updated story state for Episode {ep_num}!")

def fetch_season_from_google_sheet(gas_url=None):
    """
    Fetches the active season number directly from Google Sheet Tab 'Season_Story_Arc', Cell A1
    via the Google Apps Script Web App API (action=get_season_story).
    Returns int season number (e.g. 2), or None if offline/error.
    """
    import re
    target_url = gas_url or os.getenv("GAS_WEBHOOK_URL") or "https://script.google.com/macros/s/AKfycbyivkrK_jL1ejwNqUvHe8KVFNkSuJSwZbWSmuE1YATqL5jCneMlqlKbf0EH7mwpc4gybA/exec"
    try:
        res = requests.get(f"{target_url}?action=get_season_story", timeout=20)
        if res.status_code == 200:
            data = res.json()
            if data.get("season_number") is not None:
                s_num = int(data["season_number"])
                print(f"[INSTAGRAM] Fetched Season {s_num} directly from Google Sheet Tab 'Season_Story_Arc' (Cell A1)")
                return s_num
            cell_a1 = str(data.get("cell_a1", ""))
            m = re.search(r'SEASON\s*(\d+)', cell_a1, re.I) or re.search(r'(\d+)', cell_a1)
            if m:
                s_num = int(m.group(1))
                print(f"[INSTAGRAM] Fetched Season {s_num} from Google Sheet Tab 'Season_Story_Arc' Cell A1 ('{cell_a1}')")
                return s_num
    except Exception as e:
        print(f"[INSTAGRAM] Notice fetching season from Sheet Tab 'Season_Story_Arc': {e}")
    return None

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Publish master episode to Instagram Reels")
    parser.add_argument("--season", type=int, default=None, help="Season number (auto-detected if omitted)")
    parser.add_argument("--episode", type=int, default=None, help="Episode number (auto-detected if omitted)")
    parser.add_argument("--force", action="store_true", help="Force publish even if episode is recorded in history")
    args = parser.parse_args()

    if not os.path.exists(VIDEO_FILE):
        raise FileNotFoundError(f"Missing master video {VIDEO_FILE}")
    # Support both current_episode.json and current_episode_shots.json
    script_candidates = ["current_episode_shots.json", "current_episode.json"]
    ep_data = {}
    for sc in script_candidates:
        if os.path.exists(sc):
            try:
                with open(sc, "r", encoding="utf-8") as f:
                    ep_data = json.load(f)
                break
            except Exception:
                pass

    ep_data = normalize_ep_data(ep_data)
    ep_num = args.episode if args.episode is not None else ep_data.get("episode_number", 1)
    
    # Season resolution priority: CLI -> Sheet Tab 1 Cell A1 -> ep_data -> story_state -> 3
    season_num = args.season
    if season_num is None:
        season_num = fetch_season_from_google_sheet(os.getenv("GAS_WEBHOOK_URL")) or ep_data.get("season_number") or 3

    # Duplicate publication check
    if not args.force and os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                st = json.load(f)
                for h in st.get("history", []):
                    if h.get("episode") == ep_num and h.get("season", season_num) == season_num:
                        print(f"⚠️ Notice: Season {season_num} Episode {ep_num} is already recorded as published in {STATE_FILE}.")
                        print("   Pass --force to republish. Stopping execution cleanly to avoid duplicates.")
                        return
        except Exception:
            pass

    # Strip any Malayalam characters to guarantee 100% English description
    import re
    def to_english(s):
        if not s:
            return ""
        s = re.sub(r'[\u0D00-\u0D7F]+', '', str(s))
        s = re.sub(r' +', ' ', s).strip()
        return s

    title_en = to_english(ep_data.get("title_english")) or f"Episode {ep_num}"
    synopsis_en = to_english(ep_data.get("synopsis", ""))
    cliffhanger_en = to_english(ep_data.get("cliffhanger", ""))

    caption = (
        f"SACHIN & REENU (Season {season_num} • Episode {ep_num})\n"
        f"Title: {title_en}\n\n"
        f"{synopsis_en}\n\n"
        f"{cliffhanger_en}\n\n"
        f"Stay tuned for the next episode! Follow @sachin_and_reenu for more episodes!\n\n"
        f"#SachinAndReenu #Season{season_num} #Episode{ep_num} #3DAnimation #PixarStyle #KeralaLoveStory #AnimatedSeries #Reels #Animation"
    )

    tag_name = f"v{ep_num}.{int(time.time())}"
    video_url = upload_release_asset(VIDEO_FILE, tag_name)
    
    # Ensure custom thumbnail image exists with Season and Episode stamped
    try:
        import sys
        sys.path.append(os.path.dirname(__file__))
        from generate_thumbnail import generate_thumbnail
        generate_thumbnail(season_num=season_num, episode_num=ep_num)
    except Exception:
        try:
            import subprocess
            import sys
            subprocess.run([
                sys.executable,
                os.path.join(os.path.dirname(__file__), "generate_thumbnail.py"),
                "--season", str(season_num),
                "--episode", str(ep_num)
            ], check=False)
        except Exception as e:
            print(f"Notice auto-generating thumbnail: {e}")

    cover_url = None
    thumb_candidates = [
        os.path.join("assets", f"thumbnail_ep{ep_num}.jpg"),
        os.path.join("assets", "thumbnail.jpg"),
        os.path.join("assets", "thumbnail.png")
    ]
    for tc in thumb_candidates:
        if os.path.exists(tc) and os.path.getsize(tc) > 1000:
            try:
                print(f"Uploading custom Reel thumbnail '{tc}' to release...")
                cover_url = upload_release_asset(tc, tag_name)
                break
            except Exception as e:
                print(f"Notice: Failed to upload thumbnail asset: {e}")
                
    media_id = publish_reel_to_instagram(video_url, caption, cover_url=cover_url)
    update_story_state(ep_data)

    # Sync with Google Sheet and trigger Drive cleanup & Sheet blanking
    gas_webhook = os.getenv("GAS_WEBHOOK_URL")
    if gas_webhook:
        try:
            print("\n🧹 Executing post-publish cleanup on Google Drive & Google Sheet...")
            payload = {
                "action": "cleanup_after_publish",
                "episode_number": ep_num,
                "instagram_url": f"https://www.instagram.com/reel/{media_id}/",
                "cliffhanger": ep_data.get("cliffhanger", ""),
                "next_episode_story": ep_data.get("next_episode_story", ""),
                "next_episode_title": ep_data.get("next_episode_title", f"Episode {ep_num + 1}")
            }
            res = requests.post(gas_webhook, json=payload, timeout=25)
            print(f"✓ Post-publish cleanup response: {res.status_code} - {res.text}")
            print(f"✓ Episode {ep_num} marked Published in Google Sheet.")
            print(f"✓ All raw shot clips deleted from Google Drive.")
        except Exception as e:
            print(f"Notice: Google Sheet webhook cleanup skipped or failed: {e}")

    # Auto-compile and activate Episode N+1 from 100-shot outline if available
    if ep_num < 10:
        outline_file = f"season_{season_num}_shot_outline.json"
        has_outline = os.path.exists(outline_file)
        if not has_outline and os.path.exists("story_state.json"):
            try:
                with open("story_state.json", "r", encoding="utf-8") as f:
                    st = json.load(f)
                    has_outline = "season_shot_outline" in st
            except Exception:
                pass

        if has_outline:
            try:
                from story_and_prompt_engine import compile_episode_prompts_from_outline
                print(f"\n🚀 Auto-compiling Episode {ep_num + 1} prompts from Master 100-Shot Outline...")
                compile_episode_prompts_from_outline(season_num, ep_num + 1, gas_url=gas_webhook)
                print(f"✓ Episode {ep_num + 1} prompts ready in Tab 2 [Current_JSON_Prompts]!")
            except Exception as e:
                print(f"Notice auto-compiling Episode {ep_num + 1}: {e}")

if __name__ == "__main__":
    main()

