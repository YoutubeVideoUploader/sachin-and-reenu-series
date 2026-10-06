import os
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

TEMPLATE_PATH = Path("assets/thumbnail_template.jpg")
OUTPUT_PATH = Path("assets/thumbnail.jpg")

def generate_thumbnail(season_num=1, episode_num=1, output_file=None):
    if not TEMPLATE_PATH.exists():
        print(f"Warning: Template {TEMPLATE_PATH} not found.")
        return None

    if output_file is None:
        output_file = OUTPUT_PATH

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    im = Image.open(TEMPLATE_PATH).convert("RGB")
    draw = ImageDraw.Draw(im)

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

    font_size = 44
    if font_path:
        font = ImageFont.truetype(font_path, font_size)
    else:
        font = ImageFont.load_default()

    season_text = str(season_num).zfill(2)
    episode_text = str(episode_num).zfill(2)

    def draw_centered_text(draw, text, center_x, center_y, font, fill_color=(38, 28, 20)):
        bbox = font.getbbox(text)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = center_x - w / 2 - bbox[0]
        y = center_y - h / 2 - bbox[1]
        draw.text((x + 1, y + 1), text, font=font, fill=(185, 155, 125))
        draw.text((x, y), text, font=font, fill=fill_color)

    draw_centered_text(draw, season_text, 468, 118, font)
    draw_centered_text(draw, episode_text, 468, 275, font)

    im.save(output_path, "JPEG", quality=95)
    print(f"[THUMBNAIL] Generated Reel thumbnail: {output_path} (Season {season_text} - Episode {episode_text})")

    specific_thumb = Path(f"assets/thumbnail_ep{episode_num}.jpg")
    im.save(specific_thumb, "JPEG", quality=95)
    return output_path

def resolve_episode_num():
    import json
    for fn in ["current_episode_shots.json", "current_episode.json", "story_state.json"]:
        if os.path.exists(fn):
            try:
                with open(fn, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    val = d.get("episode_number") or d.get("total_episodes_produced")
                    if val:
                        return int(val)
            except Exception:
                pass
    return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate episode thumbnail cover")
    parser.add_argument("--season", type=int, default=1, help="Season number")
    parser.add_argument("--episode", type=int, default=None, help="Episode number")
    parser.add_argument("--output", type=str, default=None, help="Output image path")
    args = parser.parse_args()

    ep_num = args.episode if args.episode is not None else resolve_episode_num()
    generate_thumbnail(season_num=args.season, episode_num=ep_num, output_file=args.output)
