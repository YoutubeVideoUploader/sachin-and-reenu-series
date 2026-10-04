import os
import json
import time
import shutil
from PIL import Image, ImageDraw, ImageFilter
from gradio_client import Client

HF_TOKEN = os.getenv("HF_TOKEN")
SCRIPT_FILE = "current_episode.json"
IMAGE_DIR = "generated_images"
ASSETS_DIR = "assets"
os.makedirs(IMAGE_DIR, exist_ok=True)

def create_fallback_frame(speaker, out_png, scene_idx):
    """Creates a high quality 1080x1920 vertical fallback frame from character turnaround sheets if needed."""
    canvas = Image.new("RGB", (1080, 1920), color=(25, 20, 28))
    
    char_file = None
    if speaker == "Sachin":
        char_file = os.path.join(ASSETS_DIR, "sachin_reference.jpg")
    elif speaker == "Amal":
        char_file = os.path.join(ASSETS_DIR, "amal_reference.jpg")
    else:
        char_file = os.path.join(ASSETS_DIR, "reenu_reference.jpg")
        
    if os.path.exists(char_file):
        ref = Image.open(char_file)
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

def get_flux_client():
    if not HF_TOKEN:
        print("HF_TOKEN not found in environment.")
        return None
    try:
        print("Connecting to Hugging Face FLUX.1-schnell space...")
        client = Client("black-forest-labs/FLUX.1-schnell", token=HF_TOKEN)
        print("Connected to FLUX space successfully!")
        return client
    except Exception as e:
        print(f"Failed to connect to FLUX space: {e}")
        return None

def generate_scene_images():
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        ep_data = json.load(f)
    
    scenes = ep_data.get("scenes", [])
    print(f"Generating {len(scenes)} visual frames for Episode {ep_data.get('episode_number')}...")
    
    flux_client = get_flux_client()
    
    for sc in scenes:
        idx = sc["scene_index"]
        speaker = sc.get("speaker", "Reenu")
        out_png = os.path.join(IMAGE_DIR, f"scene_{idx}.png")
        
        if os.path.exists(out_png) and os.path.getsize(out_png) > 10000:
            print(f"Skipping scene_{idx}.png (already generated).")
            continue
            
        print(f"Rendering scene_{idx}.png ({speaker})...")
        prompt = sc["visual_prompt"]
        
        # Optimize prompt for FLUX Pixar 3D
        flux_prompt = (
            f"Pixar 3D animation masterpiece, 9:16 vertical orientation, highly detailed cinematic lighting. {prompt}"
        )
        
        success = False
        if flux_client:
            for attempt in range(3):
                try:
                    result = flux_client.predict(
                        prompt=flux_prompt,
                        seed=0,
                        randomize_seed=True,
                        width=576,
                        height=1024,
                        num_inference_steps=4,
                        api_name="/infer"
                    )
                    temp_img_path = result[0]
                    if os.path.exists(temp_img_path):
                        # Open and upscale to 1080x1920 high quality
                        im = Image.open(temp_img_path)
                        im_resized = im.resize((1080, 1920), Image.Resampling.LANCZOS)
                        im_resized.save(out_png, format="PNG", quality=95)
                        print(f"  -> Saved AI rendered scene_{idx}.png (1080x1920) via FLUX.1!")
                        success = True
                        time.sleep(2.0)
                        break
                except Exception as e:
                    print(f"  -> FLUX attempt {attempt+1} note: {e}")
                    time.sleep(3.0)
                    
        if not success:
            create_fallback_frame(speaker, out_png, idx)

if __name__ == "__main__":
    generate_scene_images()
    print("All scene images generated successfully!")
