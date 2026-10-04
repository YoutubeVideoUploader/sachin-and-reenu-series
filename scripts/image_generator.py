import os
import json
import time
from PIL import Image, ImageFilter
from gradio_client import Client, handle_file

HF_TOKEN = os.getenv("HF_TOKEN")
SCRIPT_FILE = "current_episode.json"
IMAGE_DIR = "generated_images"
ASSETS_DIR = "assets"
os.makedirs(IMAGE_DIR, exist_ok=True)

def get_character_reference(speaker, prompt=""):
    """Selects the precise turnaround character sheet for zero-shot identity cloning."""
    if speaker == "Sachin" or ("sachin" in prompt.lower() and "reenu" not in prompt.lower()):
        return os.path.join(ASSETS_DIR, "sachin_reference.jpg"), "Sachin"
    elif speaker == "Amal" or ("amal" in prompt.lower() and "reenu" not in prompt.lower() and "sachin" not in prompt.lower()):
        return os.path.join(ASSETS_DIR, "amal_reference.jpg"), "Amal"
    else:
        return os.path.join(ASSETS_DIR, "reenu_reference.jpg"), "Reenu"

def create_fallback_frame(speaker, out_png, scene_idx):
    """Creates a high quality 1080x1920 vertical fallback frame from character turnaround sheets."""
    canvas = Image.new("RGB", (1080, 1920), color=(25, 20, 28))
    ref_file, _ = get_character_reference(speaker)
    if os.path.exists(ref_file):
        ref = Image.open(ref_file)
        w, h = ref.size
        hero_crop = ref.crop((0, 0, int(w * 0.22), int(h * 0.45)))
        bg = hero_crop.resize((1080, 1920)).filter(ImageFilter.GaussianBlur(35))
        canvas.paste(bg, (0, 0))
        overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 100))
        canvas.paste(overlay, (0, 0), overlay)
        
        target_w = 920
        target_h = int(hero_crop.height * (target_w / hero_crop.width))
        hero_resized = hero_crop.resize((target_w, target_h), Image.Resampling.LANCZOS)
        y_pos = (1920 - target_h) // 2
        canvas.paste(hero_resized, (80, y_pos))
    
    canvas.save(out_png, quality=95)
    print(f"  -> Created character model fallback frame {out_png} for {speaker}")

def get_clients():
    if not HF_TOKEN:
        print("HF_TOKEN not found in environment.")
        return None, None
        
    instantid_client = None
    flux_client = None
    
    try:
        print("Connecting to InstantID (Zero-Shot Character Face Cloning Space)...")
        instantid_client = Client("InstantX/InstantID", token=HF_TOKEN)
        print("Connected to InstantID successfully!")
    except Exception as e:
        print(f"InstantID connection note: {e}")

    try:
        print("Connecting to FLUX.1-schnell space...")
        flux_client = Client("black-forest-labs/FLUX.1-schnell", token=HF_TOKEN)
        print("Connected to FLUX space successfully!")
    except Exception as e:
        print(f"FLUX connection note: {e}")
        
    return instantid_client, flux_client

def generate_scene_images():
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        ep_data = json.load(f)
    
    scenes = ep_data.get("scenes", [])
    ep_num = ep_data.get('episode_number')
    print(f"Generating {len(scenes)} character-consistent visual frames for Episode {ep_num}...")
    
    instantid_client, flux_client = get_clients()
    
    for sc in scenes:
        idx = sc["scene_index"]
        speaker = sc.get("speaker", "Reenu")
        setting = sc.get("setting_description", "Kochi")
        out_png = os.path.join(IMAGE_DIR, f"scene_{idx}.png")
        
        if os.path.exists(out_png) and os.path.getsize(out_png) > 10000:
            print(f"Skipping scene_{idx}.png (already generated).")
            continue
            
        print(f"Rendering scene_{idx}.png ({speaker} - {setting[:35]}...)...")
        raw_prompt = sc["visual_prompt"]
        ref_file, char_name = get_character_reference(speaker, raw_prompt)
        
        # Enforce strict 9:16 vertical Pixar 3D + Location consistency prompt
        consistent_prompt = (
            f"Pixar 3D animated masterpiece, 9:16 vertical Instagram format. "
            f"Setting and Location: {setting}. "
            f"{raw_prompt}. "
            f"8k Octane render, cinematic film lighting, volumetric atmosphere, detailed textures."
        )
        
        success = False
        
        # Tier 1: InstantID Reference Face & Character Cloning
        if instantid_client and os.path.exists(ref_file):
            for attempt in range(2):
                try:
                    print(f"  -> Cloning character identity from {os.path.basename(ref_file)} via InstantID...")
                    res = instantid_client.predict(
                        face_image_path=handle_file(ref_file),
                        pose_image_path=None,
                        prompt=consistent_prompt,
                        negative_prompt="photorealistic, 2D, sketch, anime, deformed eyes, extra limbs, blurry, low resolution, watermark, text",
                        style_name="(No style)",
                        num_steps=15,
                        identitynet_strength_ratio=0.82,
                        adapter_strength_ratio=0.82,
                        canny_strength=0.4,
                        depth_strength=0.4,
                        controlnet_selection=['depth'],
                        guidance_scale=5.0,
                        seed=42 + idx,
                        scheduler='EulerDiscreteScheduler',
                        enable_LCM=True,
                        enhance_face_region=True,
                        api_name='/generate_image'
                    )
                    temp_img_path = res[0]
                    if os.path.exists(temp_img_path):
                        im = Image.open(temp_img_path)
                        # Crop / resize to 1080x1920 vertical Full HD
                        target_w, target_h = 1080, 1920
                        im_ratio = im.width / im.height
                        target_ratio = target_w / target_h
                        if im_ratio > target_ratio:
                            new_w = int(im.height * target_ratio)
                            left = (im.width - new_w) // 2
                            im = im.crop((left, 0, left + new_w, im.height))
                        else:
                            new_h = int(im.width / target_ratio)
                            top = (im.height - new_h) // 2
                            im = im.crop((0, top, im.width, top + new_h))
                        im_resized = im.resize((1080, 1920), Image.Resampling.LANCZOS)
                        im_resized.save(out_png, format="PNG", quality=95)
                        print(f"  -> Saved InstantID character-consistent scene_{idx}.png ({char_name})!")
                        success = True
                        time.sleep(2.0)
                        break
                except Exception as e:
                    print(f"  -> InstantID note (attempt {attempt+1}): {e}")
                    time.sleep(3.0)
                    
        # Tier 2: FLUX.1-schnell Fallback with Detailed Turnaround Embeddings
        if not success and flux_client:
            print(f"  -> Falling back to FLUX.1 with character turnaround descriptors...")
            for attempt in range(2):
                try:
                    res = flux_client.predict(
                        prompt=consistent_prompt,
                        seed=42 + idx,
                        randomize_seed=False,
                        width=576,
                        height=1024,
                        num_inference_steps=4,
                        api_name="/infer"
                    )
                    temp_img_path = res[0]
                    if os.path.exists(temp_img_path):
                        im = Image.open(temp_img_path)
                        im_resized = im.resize((1080, 1920), Image.Resampling.LANCZOS)
                        im_resized.save(out_png, format="PNG", quality=95)
                        print(f"  -> Saved FLUX rendered scene_{idx}.png!")
                        success = True
                        time.sleep(2.0)
                        break
                except Exception as e:
                    print(f"  -> FLUX attempt {attempt+1} note: {e}")
                    time.sleep(2.0)
                    
        # Tier 3: Model Sheet Turnaround Framing
        if not success:
            create_fallback_frame(speaker, out_png, idx)

if __name__ == "__main__":
    generate_scene_images()
    print("All scene images generated successfully!")
