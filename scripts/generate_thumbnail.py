import os
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

TEMPLATE_PATH = Path("assets/thumbnail_template.jpg")
OUTPUT_PATH = Path("assets/thumbnail.jpg")

def sync_thumbnail_template_from_drive(gas_url=None):
    """
    Checks Google Apps Script / Google Drive 'Series_Thumbnails' folder
    for the latest active series thumbnail uploaded by the user.
    If found, downloads it and updates TEMPLATE_PATH.
    """
    import requests
    target_url = gas_url or os.getenv("GAS_WEBHOOK_URL") or "https://script.google.com/macros/s/AKfycbyivkrK_jL1ejwNqUvHe8KVFNkSuJSwZbWSmuE1YATqL5jCneMlqlKbf0EH7mwpc4gybA/exec"
    try:
        res = requests.get(f"{target_url}?action=get_series_thumbnail", timeout=20)
        if res.status_code == 200:
            data = res.json()
            if data.get("success") and data.get("has_thumbnail") and data.get("file_id"):
                file_id = data["file_id"]
                download_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download"
                img_res = requests.get(download_url, timeout=40)
                if img_res.status_code == 200 and len(img_res.content) > 10000:
                    TEMPLATE_PATH.parent.mkdir(parents=True, exist_ok=True)
                    TEMPLATE_PATH.write_bytes(img_res.content)
                    print(f"[THUMBNAIL] Successfully synced active Series Thumbnail from Drive: {data.get('filename')} ({len(img_res.content)} bytes)")
                    return True
    except Exception as e:
        print(f"[THUMBNAIL] Notice syncing thumbnail from Drive: {e}")
    return False

def fetch_season_from_google_sheet(gas_url=None):
    """
    Fetches the active season number directly from Google Sheet Tab 'Season_Story_Arc', Cell A1
    via the Google Apps Script Web App API (action=get_season_story).
    Returns int season number (e.g. 2), or None if offline/error.
    """
    import requests
    target_url = gas_url or os.getenv("GAS_WEBHOOK_URL") or "https://script.google.com/macros/s/AKfycbyivkrK_jL1ejwNqUvHe8KVFNkSuJSwZbWSmuE1YATqL5jCneMlqlKbf0EH7mwpc4gybA/exec"
    try:
        res = requests.get(f"{target_url}?action=get_season_story", timeout=20)
        if res.status_code == 200:
            data = res.json()
            if data.get("season_number") is not None:
                s_num = int(data["season_number"])
                print(f"[THUMBNAIL] Fetched Season {s_num} directly from Google Sheet Tab 'Season_Story_Arc' (Cell A1)")
                return s_num
            cell_a1 = str(data.get("cell_a1", ""))
            import re
            m = re.search(r'SEASON\s*(\d+)', cell_a1, re.I) or re.search(r'(\d+)', cell_a1)
            if m:
                s_num = int(m.group(1))
                print(f"[THUMBNAIL] Fetched Season {s_num} from Google Sheet Tab 'Season_Story_Arc' Cell A1 ('{cell_a1}')")
                return s_num
    except Exception as e:
        print(f"[THUMBNAIL] Notice fetching season from Sheet Tab 'Season_Story_Arc': {e}")
    return None

def resolve_season_and_episode_num(gas_url=None):
    """
    Resolves active season number and episode number.
    Priority 1 for Season: Live Google Sheet Tab 'Season_Story_Arc', Cell A1!
    Priority 2: Local project state files (current_episode_shots.json, story_state.json).
    """
    season_num = fetch_season_from_google_sheet(gas_url)
    episode_num = None

    for fn in ["current_episode_shots.json", "current_episode.json", "story_state.json"]:
        if os.path.exists(fn):
            try:
                with open(fn, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    if not isinstance(d, dict):
                        continue
                    if season_num is None and d.get("season_number"):
                        season_num = int(d.get("season_number"))
                    if episode_num is None:
                        if d.get("episode_number"):
                            episode_num = int(d.get("episode_number"))
                        elif d.get("current_episode", {}).get("episode_number"):
                            episode_num = int(d["current_episode"]["episode_number"])
                        elif d.get("total_episodes_produced"):
                            episode_num = int(d.get("total_episodes_produced"))
                    if season_num is not None and episode_num is not None:
                        break
            except Exception:
                pass

    if season_num is None:
        season_num = 3
    if episode_num is None:
        episode_num = 1
    return season_num, episode_num

def generate_thumbnail(season_num=None, episode_num=None, output_file=None, sync_drive=True, gas_url=None):
    if sync_drive:
        sync_thumbnail_template_from_drive(gas_url)

    detected_season, detected_ep = resolve_season_and_episode_num(gas_url)
    season_num = season_num if season_num is not None else detected_season
    episode_num = episode_num if episode_num is not None else detected_ep

    if not TEMPLATE_PATH.exists():
        print(f"Warning: Template {TEMPLATE_PATH} not found.")
        return None

    if output_file is None:
        output_file = OUTPUT_PATH

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    im = Image.open(TEMPLATE_PATH).convert("RGB")
    w, h = im.size

    # Precise relative coordinates of the blank paper areas inside the sticky notes
    cx = int(w * 0.814)
    sy = int(h * 0.0903)
    ey = int(h * 0.1950)
    font_size = int(72 * (h / 1672.0))

    font_candidates = [
        "C:/Windows/Fonts/comicbd.ttf",
        "C:/Windows/Fonts/comic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/segoeprb.ttf",
        "C:/Windows/Fonts/arialbd.ttf"
    ]

    font_path = None
    for fc in font_candidates:
        if os.path.exists(fc):
            font_path = fc
            break

    if font_path:
        font = ImageFont.truetype(font_path, font_size)
    else:
        font = ImageFont.load_default()

    season_text = str(season_num).zfill(2)
    episode_text = str(episode_num).zfill(2)

    def render_tilted_styled_text(text, font, text_color=(28, 20, 16, 255), shadow_color=(205, 180, 145, 180), angle=0.0):
        bbox = font.getbbox(text)
        bw = bbox[2] - bbox[0] + 30
        bh = bbox[3] - bbox[1] + 30
        canvas = Image.new("RGBA", (bw + 20, bh + 20), (0, 0, 0, 0))
        d = ImageDraw.Draw(canvas)
        ox = 10 - bbox[0]
        oy = 10 - bbox[1]
        # Soft warm paper shadow
        for sx, sy_off in [(2, 2), (2, 3), (3, 2), (1, 3)]:
            d.text((ox + sx, oy + sy_off), text, font=font, fill=shadow_color)
        # Deep espresso ink
        d.text((ox, oy), text, font=font, fill=text_color)
        if angle != 0:
            canvas = canvas.rotate(angle, resample=Image.BICUBIC, expand=True)
        return canvas

    # Top sticky note (Season) has a -3.5 degree tilt; bottom (Episode) has a -2.0 degree tilt
    s_img = render_tilted_styled_text(season_text, font, angle=-3.5)
    e_img = render_tilted_styled_text(episode_text, font, angle=-2.0)

    im.paste(s_img, (cx - s_img.width // 2, sy - s_img.height // 2), s_img)
    im.paste(e_img, (cx - e_img.width // 2, ey - e_img.height // 2), e_img)

    im.save(output_path, "JPEG", quality=95)
    print(f"[THUMBNAIL] Generated Reel thumbnail: {output_path} (Season {season_text} - Episode {episode_text}) in sticky note boxes")

    specific_thumb = Path(f"assets/thumbnail_ep{episode_num}.jpg")
    im.save(specific_thumb, "JPEG", quality=95)
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate episode thumbnail cover")
    parser.add_argument("--gas_url", type=str, default=None, help="Google Apps Script Web App URL")
    parser.add_argument("--season", type=int, default=None, help="Season number (auto-detected from Sheet Tab 'Season_Story_Arc' Cell A1 if omitted)")
    parser.add_argument("--episode", type=int, default=None, help="Episode number (auto-detected if omitted)")
    parser.add_argument("--output", type=str, default=None, help="Output image path")
    parser.add_argument("--no_sync", action="store_true", help="Skip syncing template from Google Drive")
    args = parser.parse_args()

    generate_thumbnail(
        season_num=args.season,
        episode_num=args.episode,
        output_file=args.output,
        sync_drive=not args.no_sync,
        gas_url=args.gas_url
    )
