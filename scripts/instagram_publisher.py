import os
import json
import time
import requests

IG_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
IG_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
GH_PAT = os.getenv("GH_PAT") or os.getenv("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY", "YoutubeVideoUploader/sachin-and-reenu-series")

SCRIPT_FILE = "current_episode.json"
STATE_FILE = "story_state.json"
VIDEO_FILE = "master_episode.mp4"

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

def publish_reel_to_instagram(video_url, caption):
    if not IG_ACCESS_TOKEN or not IG_ACCOUNT_ID:
        raise ValueError("INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_ACCOUNT_ID are required")
        
    print(f"Creating Instagram Reel container on account {IG_ACCOUNT_ID}...")
    create_url = f"https://graph.facebook.com/v20.0/{IG_ACCOUNT_ID}/media"
    payload = {
        "media_type": "REELS",
        "video_url": video_url,
        "caption": caption,
        "share_to_feed": "true",
        "access_token": IG_ACCESS_TOKEN
    }
    
    res = requests.post(create_url, data=payload)
    if res.status_code != 200:
        raise Exception(f"Failed to create Instagram container: {res.status_code} {res.text}")
        
    container_id = res.json().get("id")
    print(f"Container created with ID: {container_id}. Waiting for processing...")
    
    # Poll status
    status_url = f"https://graph.facebook.com/v20.0/{container_id}"
    for attempt in range(40):
        time.sleep(10)
        status_res = requests.get(status_url, params={"fields": "status_code,status", "access_token": IG_ACCESS_TOKEN})
        if status_res.status_code == 200:
            st = status_res.json().get("status_code")
            print(f"Processing status [{attempt+1}/40]: {st}")
            if st == "FINISHED":
                print("Video successfully processed by Instagram!")
                break
            elif st in ["ERROR", "EXPIRED"]:
                raise Exception(f"Instagram video processing failed: {status_res.text}")
        else:
            print(f"Error checking status: {status_res.text}")
    else:
        raise TimeoutError("Timed out waiting for Instagram to process video.")
        
    # Publish container
    print(f"Publishing container {container_id} to Instagram feed...")
    publish_url = f"https://graph.facebook.com/v20.0/{IG_ACCOUNT_ID}/media_publish"
    pub_res = requests.post(publish_url, data={"creation_id": container_id, "access_token": IG_ACCESS_TOKEN})
    if pub_res.status_code != 200:
        raise Exception(f"Failed to publish reel: {pub_res.status_code} {pub_res.text}")
        
    published_id = pub_res.json().get("id")
    print(f"SUCCESS! Published to Instagram Reels with Post ID: {published_id}")
    return published_id

def update_story_state():
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        ep_data = json.load(f)
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        state = load_state = json.load(f)
        
    ep_num = ep_data.get("episode_number")
    history_entry = {
        "episode": ep_num,
        "title": f"{ep_data.get('title_malayalam')} ({ep_data.get('title_english')})",
        "summary": ep_data.get("synopsis"),
        "cliffhanger": ep_data.get("cliffhanger"),
        "characters_present": list(set(s.get("speaker") for s in ep_data.get("scenes", []) if s.get("speaker") != "Narrator"))
    }
    
    state["total_episodes_produced"] = ep_num
    state.setdefault("history", []).append(history_entry)
    
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    print(f"Updated story_state.json with Episode {ep_num} summary.")

def main():
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        ep_data = json.load(f)
        
    ep_num = ep_data.get("episode_number")
    caption = (
        f"❤️ സച്ചിൻ & റീനു — ഭാഗം {ep_num}: {ep_data.get('title_malayalam')} ({ep_data.get('title_english')})\n\n"
        f"{ep_data.get('synopsis')}\n\n"
        f"തുടരും... അടുത്ത ഭാഗം ഉടൻ വരുന്നു!\n\n"
        f"#SachinAndReenu #MalayalamWebSeries #KeralaRomance #MalayalamAnime #InstaReels #MalluAnimation #KeralaLovers #CIAL"
    )
    
    tag_name = f"v1.{ep_num}"
    public_url = upload_release_asset(VIDEO_FILE, tag_name)
    publish_reel_to_instagram(public_url, caption)
    update_story_state()

if __name__ == "__main__":
    main()
