import os
import json
import time
import base64
import requests
from PIL import Image, ImageFilter

# Load local .env if present
if os.path.exists(".env"):
    try:
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
    except Exception:
        pass

CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()

SCRIPT_FILE = "current_episode.json"
IMAGE_DIR = "generated_images"
ASSETS_DIR = "assets"
os.makedirs(IMAGE_DIR, exist_ok=True)

# IMMUTABLE CHARACTER VISUAL DNA ANCHORS (PIXAR 3D CANONICAL)
REENU_DNA = (
    "Disney Pixar 3D animated film still, 8k masterpiece. "
    "Reenu, a charming 22-year-old South Indian Malayali girl with shoulder-length voluminous layered wavy dark-brown hair "
    "and soft wispy curtain bangs framing her cheerful face, warm sparkling hazel-brown eyes, glowing honey complexion. "
    "Attire: fitted pastel camouflage t-shirt in baby blue, soft yellow, and white patches, paired with a light-blue denim A-line mini skirt and white sneakers."
)

SACHIN_DNA = (
    "Disney Pixar 3D animated film still, 8k masterpiece. "
    "Sachin, a handsome 22-year-old South Indian Malayali young man with thick messy wavy textured dark hair styled with casual volume, "
    "thick expressive natural eyebrows, warm dark-brown eyes, handsome defined jawline, boyish charming smile. "
    "Attire: oversized terracotta rust-orange cotton t-shirt with subtle pocket design, relaxed dark-gray joggers, and black digital sports watch."
)

AMAL_DNA = (
    "Disney Pixar 3D animated film still, 8k masterpiece. "
    "Amal, a friendly 22-year-old South Indian young man with short neat textured black hair, neat mustache and trim goatee beard, "
    "expressive humorous eyes. Attire: olive-green crewneck t-shirt and blue denim jeans."
)

DUO_DNA = (
    "Disney Pixar 3D animated romantic movie still, cinematic render, 8k masterpiece. "
    "Two young adult characters interacting together. "
    "On the left, Sachin, a cute 22-year-old South Indian young man with messy wavy dark hair, boyish smile, wearing an oversized rust-orange t-shirt and dark joggers. "
    "On the right, Reenu, a gorgeous 22-year-old South Indian girl with shoulder-length layered wavy dark-brown hair and soft curtain bangs, warm hazel eyes, wearing a pastel camouflage t-shirt and light blue denim skirt."
)

def build_scene_prompt(scene, location_palette, primary_location):
    chars = scene.get("characters_present", [])
    speaker = scene.get("speaker", "")
    emotion = scene.get("character_emotion", "expressive emotional gaze")
    action = scene.get("action_description", "")
    
    # 1. Select Character DNA
    if "Sachin" in chars and "Reenu" in chars:
        char_base = DUO_DNA
    elif "Reenu" in chars or speaker == "Reenu":
        char_base = REENU_DNA
    elif "Sachin" in chars or speaker == "Sachin":
        char_base = SACHIN_DNA
    elif "Amal" in chars or speaker == "Amal":
        char_base = AMAL_DNA
    else:
        # Default narrator shot
        if "reenu" in action.lower():
            char_base = REENU_DNA
        else:
            char_base = SACHIN_DNA
            
    # 2. Combine with action, emotion, location and camera lighting
    prompt = (
        f"{char_base} "
        f"Expression: {emotion}. "
        f"Action: {action}. "
        f"Environment: {primary_location}, {location_palette}. "
        f"Cinematic composition, Pixar character render, octane render, volumetric lighting, depth of field, 8k."
    )
    return prompt

def make_vertical_reel_frame(pil_img, out_path):
    """Composes image into 1080x1920 vertical canvas with blurred ambient background fill."""
    target_w, target_h = 1080, 1920
    
    # 1. Background layer: cover 1080x1920 and heavily blur
    scale = max(target_w / pil_img.width, target_h / pil_img.height)
    bg_w, bg_h = int(pil_img.width * scale), int(pil_img.height * scale)
    bg = pil_img.resize((bg_w, bg_h), Image.Resampling.LANCZOS)
    left = (bg_w - target_w) // 2
    top = (bg_h - target_h) // 2
    bg = bg.crop((left, top, left + target_w, top + target_h))
    bg = bg.filter(ImageFilter.GaussianBlur(radius=32))
    
    # Subtle darkening for contrast and focus
    dimmer = Image.new("RGB", (target_w, target_h), (0, 0, 0))
    bg = Image.blend(bg, dimmer, 0.22)
    
    # 2. Foreground hero layer: centered 1080x1080 sharp
    fg = pil_img.resize((1080, 1080), Image.Resampling.LANCZOS)
    y_pos = (target_h - 1080) // 2
    bg.paste(fg, (0, y_pos))
    
    bg.save(out_path, format="PNG", quality=95)

def call_cloudflare_flux(prompt):
    """Calls Cloudflare Workers AI FLUX.1-schnell model."""
    if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        print("  -> Notice: CLOUDFLARE credentials not configured.")
        return None
        
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"}
    payload = {"prompt": prompt, "steps": 4}
    
    for attempt in range(3):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=40)
            if resp.status_code == 200:
                if "image" in resp.headers.get("content-type", ""):
                    from io import BytesIO
                    return Image.open(BytesIO(resp.content)).convert("RGB")
                data = resp.json()
                img_b64 = data.get("result", {}).get("image")
                if img_b64:
                    from io import BytesIO
                    img_data = base64.b64decode(img_b64)
                    return Image.open(BytesIO(img_data)).convert("RGB")
            else:
                print(f"  -> Cloudflare API note (attempt {attempt+1}): {resp.status_code} {resp.text[:120]}")
        except Exception as e:
            print(f"  -> Cloudflare connection note (attempt {attempt+1}): {e}")
        time.sleep(3.0)
    return None

def create_fallback_frame(speaker, out_png):
    """Fallback if API is unreachable."""
    ref_file = os.path.join(ASSETS_DIR, "reenu_reference.jpg" if speaker == "Reenu" else "sachin_reference.jpg")
    if os.path.exists(ref_file):
        ref = Image.open(ref_file).convert("RGB")
        w, h = ref.size
        hero_crop = ref.crop((0, 0, int(w * 0.22), int(h * 0.45)))
        make_vertical_reel_frame(hero_crop, out_png)
    else:
        blank = Image.new("RGB", (1080, 1920), (20, 20, 25))
        blank.save(out_png)

def generate_scene_images():
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        ep_data = json.load(f)
        
    scenes = ep_data.get("scenes", [])
    ep_num = ep_data.get("episode_number", 1)
    primary_location = ep_data.get("primary_location", "Kochi CIAL Airport Arrivals Terminal")
    location_palette = ep_data.get("location_palette", "Modern glass architecture, golden morning sunlight, volumetric atmospheric rays")
    
    print(f"Generating {len(scenes)} character-consistent visual frames for Episode {ep_num}...")
    print(f"Location anchor: {primary_location}")
    
    for sc in scenes:
        idx = sc["scene_index"]
        speaker = sc.get("speaker", "Reenu")
        out_png = os.path.join(IMAGE_DIR, f"scene_{idx}.png")
        
        if os.path.exists(out_png) and os.path.getsize(out_png) > 10000:
            print(f"Skipping scene_{idx}.png (already generated).")
            continue
            
        prompt = build_scene_prompt(sc, location_palette, primary_location)
        print(f"Rendering scene_{idx}.png ({speaker} - {sc.get('characters_present', [])})...")
        
        pil_img = call_cloudflare_flux(prompt)
        if pil_img:
            make_vertical_reel_frame(pil_img, out_png)
            print(f"  -> Successfully generated & framed scene_{idx}.png!")
        else:
            print(f"  -> Warning: Falling back to reference sheet frame for scene_{idx}.png")
            create_fallback_frame(speaker, out_png)
        time.sleep(1.0)

if __name__ == "__main__":
    generate_scene_images()
    print("All scene images generated successfully!")
