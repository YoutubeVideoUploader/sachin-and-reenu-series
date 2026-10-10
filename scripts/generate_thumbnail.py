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

def resolve_season_and_episode_num():
    """Resolves active season number and episode number from project state files."""
    season_num = 1
    episode_num = 1
    for fn in ["current_episode_shots.json", "current_episode.json", "story_state.json"]:
        if os.path.exists(fn):
            try:
                with open(fn, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    if d.get("season_number"):
                        season_num = int(d.get("season_number"))
                    if d.get("episode_number"):
                        episode_num = int(d.get("episode_number"))
                    elif d.get("total_episodes_produced"):
                        episode_num = int(d.get("total_episodes_produced"))
                    break
            except Exception:
                pass
    return season_num, episode_num

def generate_thumbnail(season_num=None, episode_num=None, output_file=None, sync_drive=True):
    if sync_drive:
        sync_thumbnail_template_from_drive()

    detected_season, detected_ep = resolve_season_and_episode_num()
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
    draw = ImageDraw.Draw(im)

    # Relative coordinates scaled proportionally to template image size
    cx = int(w * (468.0 / 576.0))
    sy = int(h * (118.0 / 1024.0))
    ey = int(h * (275.0 / 1024.0))
    font_size = int(44 * (h / 1024.0))

    font_candidates = [
        "C:/Windows/Fonts/comicbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
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

    def draw_centered_text(draw, text, center_x, center_y, font, fill_color=(38, 28, 20)):
        bbox = font.getbbox(text)
        bw = bbox[2] - bbox[0]
        bh = bbox[3] - bbox[1]
        x = center_x - bw / 2 - bbox[0]
        y = center_y - bh / 2 - bbox[1]
        draw.text((x + 2, y + 2), text, font=font, fill=(185, 155, 125))
        draw.text((x, y), text, font=font, fill=fill_color)

    draw_centered_text(draw, season_text, cx, sy, font)
    draw_centered_text(draw, episode_text, cx, ey, font)

    im.save(output_path, "JPEG", quality=95)
    print(f"[THUMBNAIL] Generated Reel thumbnail: {output_path} (Season {season_text} - Episode {episode_text})")

    specific_thumb = Path(f"assets/thumbnail_ep{episode_num}.jpg")
    im.save(specific_thumb, "JPEG", quality=95)
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate episode thumbnail cover")
    parser.add_argument("--season", type=int, default=None, help="Season number (auto-detected if omitted)")
    parser.add_argument("--episode", type=int, default=None, help="Episode number (auto-detected if omitted)")
    parser.add_argument("--output", type=str, default=None, help="Output image path")
    parser.add_argument("--no_sync", action="store_true", help="Skip syncing template from Google Drive")
    args = parser.parse_args()

    generate_thumbnail(
        season_num=args.season,
        episode_num=args.episode,
        output_file=args.output,
        sync_drive=not args.no_sync
    )
