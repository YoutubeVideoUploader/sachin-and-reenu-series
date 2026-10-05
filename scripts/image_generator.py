import os
import json
import time
import base64
import requests
from PIL import Image

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

# STRICT DETERMINISTIC CHARACTER VISUAL DNA (PIXAR 3D CANONICAL)
REENU_DNA = (
    "Disney Pixar 3D animated film still, 8k masterpiece. "
    "Reenu, an attractive 22-year-old South Indian Malayali girl with shoulder-length voluminous layered wavy dark-brown hair "
    "and soft wispy curtain bangs framing her cheerful face, warm sparkling hazel-brown eyes, glowing honey complexion. "
    "Attire: fitted short-sleeved t-shirt featuring a pastel camouflage pattern in baby-blue, soft light-yellow, and off-white patches, "
    "paired with a sky-blue denim skirt and white sneakers."
)

SACHIN_DNA = (
    "Disney Pixar 3D animated film still, 8k masterpiece. "
    "Sachin, a handsome 22-year-old South Indian Malayali young man with thick messy wavy textured dark hair styled with casual volume, "
    "thick expressive natural eyebrows, warm dark-brown eyes, handsome defined jawline, boyish charming smile. "
    "Attire: oversized terracotta rust-orange cotton t-shirt with subtle pocket design on left chest, relaxed dark-gray joggers, "
    "and a black digital sports watch."
)

AMAL_DNA = (
    "Disney Pixar 3D animated film still, 8k masterpiece. "
    "Amal, a witty 22-year-old South Indian Malayali young man with tight curly textured black hair styled with volume on top, "
    "neat mustache and small chin soul patch, expressive humorous brown eyes, and an energetic cheerful smile. "
    "Attire: sage olive-green crewneck t-shirt with subtle thin horizontal lines on the chest, blue denim jeans, and a black wristwatch."
)

AMAL_AND_REENU_DNA = (
    "Disney Pixar 3D animated film still, 8k masterpiece. "
    "Two young adult South Indian friends standing together side by side. "
    "On the left, Amal (22, tight curly black hair, neat mustache, energetic smile, sage olive-green t-shirt, blue jeans). "
    "On the right, Reenu (22, shoulder-length wavy dark-brown hair with curtain bangs, joyful smile, pastel baby-blue and yellow camouflage t-shirt, sky-blue denim skirt)."
)

SACHIN_AND_REENU_DNA = (
    "Disney Pixar 3D animated romantic movie still, cinematic render, 8k masterpiece. "
    "Two young adult characters interacting together closely. "
    "On the left, Sachin (handsome 22-year-old South Indian young man, messy wavy dark hair, boyish smile, oversized rust-orange t-shirt, dark joggers). "
    "On the right, Reenu (gorgeous 22-year-old South Indian girl, shoulder-length layered wavy dark-brown hair with curtain bangs, warm hazel eyes, pastel baby-blue and yellow camouflage t-shirt, sky-blue denim skirt)."
)

SACHIN_AND_AMAL_DNA = (
    "Disney Pixar 3D animated movie still, 8k masterpiece. "
    "Two young adult South Indian best friends reuniting excitedly. "
    "On the left, Sachin (22, messy wavy dark hair, charming boyish grin, oversized rust-orange t-shirt). "
    "On the right, Amal (22, curly black hair, neat mustache, laughing cheerfully, olive-green t-shirt with thin stripes)."
)

TRIO_DNA = (
    "Disney Pixar 3D animated film still, 8k masterpiece. "
    "Three young adult South Indian friends together. "
    "In the center, Sachin (22, messy wavy hair, rust-orange pocket t-shirt). "
    "On his right, Reenu (22, layered wavy hair with bangs, joyful radiant smile, pastel cloud camouflage t-shirt, denim skirt). "
    "On his left, Amal (22, curly hair, neat mustache, grinning widely, olive-green t-shirt)."
)

def build_scene_prompt(scene, location_palette, primary_location):
    chars = scene.get("characters_present", [])
    speaker = scene.get("speaker", "")
    emotion = scene.get("character_emotion", "expressive emotional gaze")
    action = scene.get("action_description", "")
    
    # 1. Multi-Character & Speaker Routing (Ensuring Amal is NEVER skipped)
    if "Sachin" in chars and "Reenu" in chars and "Amal" in chars:
        char_base = TRIO_DNA
    elif "Sachin" in chars and "Reenu" in chars:
        char_base = SACHIN_AND_REENU_DNA
    elif ("Amal" in chars and "Reenu" in chars) or (speaker == "Amal" and "Reenu" in chars):
        if speaker == "Amal" and "look" not in action.lower():
            char_base = AMAL_DNA
        else:
            char_base = AMAL_AND_REENU_DNA
    elif "Sachin" in chars and "Amal" in chars:
        char_base = SACHIN_AND_AMAL_DNA
    elif speaker == "Amal" or ("Amal" in chars and len(chars) == 1):
        char_base = AMAL_DNA
    elif speaker == "Reenu" or ("Reenu" in chars and len(chars) == 1):
        char_base = REENU_DNA
    elif speaker == "Sachin" or ("Sachin" in chars and len(chars) == 1):
        char_base = SACHIN_DNA
    else:
        # Default narrator shot
        if "amal" in action.lower():
            char_base = AMAL_DNA
        elif "sachin" in action.lower():
            char_base = SACHIN_DNA
        else:
            char_base = REENU_DNA

    # 2. Combine with emotion, action, and location lighting
    prompt = (
        f"{char_base} "
        f"Expression: {emotion}. "
        f"Action: {action}. "
        f"Environment: {primary_location}, {location_palette}. "
        f"Cinematic composition, Pixar character render, octane render, volumetric lighting, depth of field, 8k."
    )
    return prompt

def make_full_bleed_9_16(pil_img, out_path):
    """Crops & scales 1:1 image to 1080x1920 Full-Bleed (zero blurred borders, zero black bars)."""
    target_w, target_h = 1080, 1920
    scale = target_h / pil_img.height
    new_w = int(pil_img.width * scale)
    new_h = target_h
    im_scaled = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    left = (new_w - target_w) // 2
    im_cropped = im_scaled.crop((left, 0, left + target_w, target_h))
    im_cropped.save(out_path, format="PNG", quality=95)

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
        time.sleep(2.0)
    return None

def create_fallback_frame(speaker, out_png):
    """Fallback if API is unreachable."""
    if speaker == "Amal":
        ref_name = "amal_reference.jpg"
    elif speaker == "Reenu":
        ref_name = "reenu_reference.jpg"
    else:
        ref_name = "sachin_reference.jpg"
        
    ref_file = os.path.join(ASSETS_DIR, ref_name)
    if os.path.exists(ref_file):
        ref = Image.open(ref_file).convert("RGB")
        w, h = ref.size
        hero_crop = ref.crop((0, 0, int(w * 0.22), int(h * 0.45)))
        make_full_bleed_9_16(hero_crop, out_png)
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
            make_full_bleed_9_16(pil_img, out_png)
            print(f"  -> Successfully generated & full-bleed framed scene_{idx}.png!")
        else:
            print(f"  -> Warning: Falling back to reference sheet frame for scene_{idx}.png")
            create_fallback_frame(speaker, out_png)
        time.sleep(1.0)

if __name__ == "__main__":
    generate_scene_images()
    print("All scene images generated successfully!")
