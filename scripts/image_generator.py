import os
import json
import time
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from google import genai
from google.genai import types

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is required")

client = genai.Client(api_key=api_key)

SCRIPT_FILE = "current_episode.json"
IMAGE_DIR = "generated_images"
ASSETS_DIR = "assets"
os.makedirs(IMAGE_DIR, exist_ok=True)

def create_fallback_frame(speaker, out_png, scene_idx, setting="Cochin International Airport"):
    """Creates a high quality 1080x1920 fallback vertical frame from character turnaround sheets if image API quota is 0."""
    canvas = Image.new("RGB", (1080, 1920), color=(25, 20, 28))
    
    # Pick character sheet
    char_file = None
    if speaker == "Sachin":
        char_file = os.path.join(ASSETS_DIR, "sachin_reference.jpg")
    elif speaker == "Amal":
        char_file = os.path.join(ASSETS_DIR, "amal_reference.jpg")
    else:
        # Default Reenu / Narrator
        char_file = os.path.join(ASSETS_DIR, "reenu_reference.jpg")
        
    if os.path.exists(char_file):
        ref = Image.open(char_file)
        
        # Crop hero close-up / portrait section from top left of model sheet
        w, h = ref.size
        # The reference sheet has hero reference at top-left (~0.25 width, ~0.45 height)
        hero_crop = ref.crop((0, 0, int(w * 0.22), int(h * 0.45)))
        
        # Blurred atmospheric background
        bg = hero_crop.resize((1080, 1920)).filter(ImageFilter.GaussianBlur(35))
        canvas.paste(bg, (0, 0))
        
        # Subtle dark vignette gradient
        overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 100))
        canvas.paste(overlay, (0, 0), overlay)
        
        # Paste crisp character in central frame
        target_w = 920
        target_h = int(hero_crop.height * (target_w / hero_crop.width))
        hero_resized = hero_crop.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        y_pos = (1920 - target_h) // 2
        canvas.paste(hero_resized, (80, y_pos))
    
    canvas.save(out_png, quality=95)
    print(f"  -> Created character model frame {out_png} for {speaker}")

def generate_scene_images():
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        ep_data = json.load(f)
    
    scenes = ep_data.get("scenes", [])
    print(f"Generating {len(scenes)} visual frames for Episode {ep_data.get('episode_number')}...")
    
    for sc in scenes:
        idx = sc["scene_index"]
        speaker = sc.get("speaker", "Reenu")
        out_png = os.path.join(IMAGE_DIR, f"scene_{idx}.png")
        
        if os.path.exists(out_png) and os.path.getsize(out_png) > 10000:
            print(f"Skipping scene_{idx}.png (already generated).")
            continue
            
        print(f"Rendering scene_{idx}.png ({speaker})...")
        prompt = sc["visual_prompt"]
        
        success = False
        for attempt in range(2):
            try:
                res = client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=prompt,
                    config=types.GenerateContentConfig(response_modalities=["IMAGE"])
                )
                img_bytes = res.candidates[0].content.parts[0].inline_data.data
                with open(out_png, "wb") as f:
                    f.write(img_bytes)
                print(f"  -> Saved AI rendered scene_{idx}.png ({len(img_bytes)} bytes)")
                success = True
                time.sleep(2.0)
                break
            except Exception as e:
                print(f"  -> AI Image API attempt {attempt+1} note: {e}")
                time.sleep(2.0)
                
        if not success:
            # Fallback to model sheet framing so workflow never fails
            create_fallback_frame(speaker, out_png, idx)

if __name__ == "__main__":
    generate_scene_images()
    print("All scene images generated successfully!")
