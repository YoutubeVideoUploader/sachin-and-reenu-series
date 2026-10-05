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
    "Disney Pixar 3D animated film still, 8k masterpiece CGI render. "
    "Reenu, an attractive 22-year-old South Indian Malayali girl with shoulder-length voluminous layered wavy dark-brown hair "
    "and soft wispy curtain bangs framing her cheerful face, warm sparkling hazel-brown eyes, glowing honey complexion. "
    "Attire: classic short-sleeved cotton t-shirt featuring a pastel camouflage pattern in baby-blue, soft light-yellow, and off-white patches, "
    "paired with a sky-blue denim skirt and white sneakers. "
    "Authentic Disney Pixar 3D CGI character model, subsurface skin scattering, realistic natural facial anatomy, not 2D, not flat, not a caricature."
)

SACHIN_DNA = (
    "Disney Pixar 3D animated film still, 8k masterpiece CGI render. "
    "Sachin, a handsome 22-year-old South Indian Malayali young man with thick messy wavy textured dark hair styled with casual volume, "
    "natural neat eyebrows, warm dark-brown eyes, handsome defined clean jawline, boyish charming smile. "
    "Attire: terracotta rust-orange cotton t-shirt with subtle pocket design on left chest, relaxed dark-gray joggers, "
    "and a black digital sports watch. "
    "Authentic Disney Pixar 3D CGI character model, subsurface skin scattering, realistic natural facial anatomy, not a caricature."
)

AMAL_DNA = (
    "Disney Pixar 3D animated film still, 8k masterpiece CGI render. "
    "Amal, a witty 22-year-old South Indian Malayali young man with cropped soft curly black hair, "
    "subtle natural neat 3D mustache, clean jawline, warm humorous brown eyes, and an energetic cheerful smile. "
    "Attire: sage olive-green crewneck t-shirt with subtle thin horizontal lines on the chest, blue denim jeans, and a black wristwatch. "
    "Authentic Disney Pixar 3D CGI character model, realistic natural facial proportions, not a caricature."
)

AMAL_AND_REENU_DNA = (
    "Disney Pixar 3D animated film still, 8k masterpiece CGI render. "
    "Vertical 9:16 portrait composition, close-up two-shot tightly centered in the middle of frame with wide background buffers on left and right borders. "
    "Two young South Indian friends standing close together in the center. "
    "Left: Amal (22, cropped soft curly black hair, subtle natural mustache, sage olive-green t-shirt). "
    "Right: Reenu (22, shoulder-length wavy dark-brown hair with curtain bangs, joyful smile, pastel baby-blue and yellow camouflage t-shirt, sky-blue denim skirt). "
    "Both faces fully visible and centered inside the vertical frame, authentic Pixar character models, octane render."
)

SACHIN_AND_REENU_DNA = (
    "Disney Pixar 3D animated romantic movie still, cinematic render, 8k masterpiece CGI. "
    "Vertical 9:16 portrait composition, close-up two-shot tightly centered in the middle of frame with wide background buffers on left and right borders. "
    "Two young adult characters interacting together closely in the center. "
    "Left: Sachin (handsome 22yo South Indian young man, messy wavy dark hair, boyish smile, rust-orange t-shirt, dark joggers). "
    "Right: Reenu (attractive 22yo South Indian girl, shoulder-length layered wavy dark-brown hair with curtain bangs, warm hazel eyes, pastel baby-blue and yellow camouflage t-shirt). "
    "Both faces fully visible and centered inside the vertical frame, authentic Pixar 3D character models."
)

SACHIN_AND_AMAL_DNA = (
    "Disney Pixar 3D animated movie still, 8k masterpiece CGI render. "
    "Vertical 9:16 portrait composition, close-up two-shot tightly centered in the middle of frame with wide background buffers on left and right borders. "
    "Two young South Indian best friends reuniting excitedly side by side in the center. "
    "Left: Sachin (22, messy wavy dark hair, charming boyish grin, rust-orange t-shirt). "
    "Right: Amal (22, cropped curly black hair, subtle natural mustache, laughing cheerfully, olive-green t-shirt). "
    "Both faces fully visible and centered inside the vertical frame, authentic Pixar character models."
)

TRIO_DNA = (
    "Disney Pixar 3D animated film still, 8k masterpiece CGI render. "
    "Vertical 9:16 portrait composition, tight medium three-shot grouped in the center of frame with wide background buffers on left and right borders. "
    "Three young South Indian friends posing happily side by side for a photo. "
    "Center: Reenu (22, cheerful smiling girl with shoulder-length wavy dark-brown hair, curtain bangs, pastel cloud camouflage t-shirt, denim skirt). "
    "Left: Sachin (22, handsome boyish smile, messy wavy dark hair, terracotta rust-orange t-shirt). "
    "Right: Amal (22, energetic smiling friend, cropped curly black hair, subtle natural mustache, olive-green t-shirt). "
    "All three faces close together centered in the middle 55% of the frame, fully visible without cutoff, authentic Pixar 3D character models."
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
        if "amal" in action.lower():
            char_base = AMAL_DNA
        elif "sachin" in action.lower():
            char_base = SACHIN_DNA
        else:
            char_base = REENU_DNA

    # 2. Combine with emotion, action, framing buffer, and location lighting
    framing_rule = (
        "Vertical 9:16 framing, subjects positioned strictly within central 55% horizontal zone with wide background clearance on left and right borders so heads are never cut off. "
        "Headroom above heads, full shoulders visible."
    )
    prompt = (
        f"{char_base} "
        f"{framing_rule} "
        f"Expression: {emotion}. "
        f"Action: {action}. "
        f"Environment: {primary_location}, {location_palette}. "
        f"Cinematic composition, Pixar character render, octane render, volumetric lighting, depth of field, 8k."
    )
    return prompt

def make_full_bleed_9_16(pil_img, out_path):
    """Smart subject-centering crop & scale from 1:1 image to 1080x1920 Full-Bleed (zero blurred borders, zero cutoffs)."""
    target_w, target_h = 1080, 1920
    scale = target_h / pil_img.height
    new_w = int(pil_img.width * scale)
    new_h = target_h
    im_scaled = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Calculate horizontal centroid of subjects in upper 65% of the frame
    try:
        import numpy as np
        gray = np.array(im_scaled.convert("L"))
        h_sample = gray[int(new_h * 0.1):int(new_h * 0.7), :]
        dx = np.abs(np.diff(h_sample.astype(float), axis=1))
        profile = np.sum(dx, axis=0)
        total_p = np.sum(profile)
        if total_p > 0:
            x_coords = np.arange(len(profile))
            centroid_x = int(np.sum(x_coords * profile) / total_p)
            # Center the 1080 crop window on subject centroid
            left = max(0, min(new_w - target_w, centroid_x - target_w // 2))
        else:
            left = (new_w - target_w) // 2
    except Exception:
        left = (new_w - target_w) // 2
        
    im_cropped = im_scaled.crop((left, 0, left + target_w, target_h))
    im_cropped.save(out_path, format="PNG", quality=95)

def get_cloudflare_accounts():
    accounts = []
    for acc_var, tok_var in [
        ("CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN"),
        ("CLOUDFLARE_ACCOUNT_ID_2", "CLOUDFLARE_API_TOKEN_2")
    ]:
        acc = os.getenv(acc_var, "").strip()
        tok = os.getenv(tok_var, "").strip()
        if acc and tok and (acc, tok) not in accounts:
            accounts.append((acc, tok))
    return accounts

def call_cloudflare_flux(prompt):
    """Calls Cloudflare Workers AI FLUX.1-schnell model with multi-account failover."""
    accounts = get_cloudflare_accounts()
    if not accounts:
        print("  -> Notice: CLOUDFLARE credentials not configured.")
        return None
        
    payload = {"prompt": prompt}
    
    for acc_idx, (acc_id, api_token) in enumerate(accounts, 1):
        url = f"https://api.cloudflare.com/client/v4/accounts/{acc_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"
        headers = {"Authorization": f"Bearer {api_token}"}
        
        for attempt in range(2):
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
                    print(f"  -> Cloudflare Acct #{acc_idx} note (attempt {attempt+1}): {resp.status_code} {resp.text[:120]}")
                    if resp.status_code == 429:
                        print(f"  -> Acct #{acc_idx} quota reached. Failing over to next account...")
                        break
            except Exception as e:
                print(f"  -> Cloudflare Acct #{acc_idx} connection note (attempt {attempt+1}): {e}")
            time.sleep(1.5)
            
    return None

def create_fallback_frame(speaker, out_png):
    """Fallback if API is unreachable: crops character portrait cleanly without sheet borders or text."""
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
        # Crop inner character figure, avoiding top-left title banner ('Reference')
        hero_crop = ref.crop((int(w * 0.05), int(h * 0.15), int(w * 0.35), int(h * 0.75)))
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
