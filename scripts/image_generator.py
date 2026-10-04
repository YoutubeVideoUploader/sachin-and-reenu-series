import os
import json
import time
from google import genai
from google.genai import types

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable is required")

client = genai.Client(api_key=api_key)

SCRIPT_FILE = "current_episode.json"
IMAGE_DIR = "generated_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

def generate_scene_images():
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        ep_data = json.load(f)
    
    scenes = ep_data.get("scenes", [])
    print(f"Generating {len(scenes)} visual frames for Episode {ep_data.get('episode_number')}...")
    
    for sc in scenes:
        idx = sc["scene_index"]
        out_png = os.path.join(IMAGE_DIR, f"scene_{idx}.png")
        
        if os.path.exists(out_png) and os.path.getsize(out_png) > 10000:
            print(f"Skipping scene_{idx}.png (already generated).")
            continue
            
        print(f"Rendering scene_{idx}.png...")
        prompt = sc["visual_prompt"]
        
        for attempt in range(3):
            try:
                res = client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=prompt,
                    config=types.GenerateContentConfig(response_modalities=["IMAGE"])
                )
                img_bytes = res.candidates[0].content.parts[0].inline_data.data
                with open(out_png, "wb") as f:
                    f.write(img_bytes)
                print(f"  -> Saved scene_{idx}.png ({len(img_bytes)} bytes)")
                time.sleep(2.5)
                break
            except Exception as e:
                print(f"  -> Attempt {attempt+1} error on scene_{idx}.png: {e}. Retrying...")
                time.sleep(10.0)

if __name__ == "__main__":
    generate_scene_images()
    print("All scene images generated successfully!")
