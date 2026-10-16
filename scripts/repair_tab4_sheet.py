import urllib.request
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

GAS_URL = "https://script.google.com/macros/s/AKfycbyivkrK_jL1ejwNqUvHe8KVFNkSuJSwZbWSmuE1YATqL5jCneMlqlKbf0EH7mwpc4gybA/exec"

canonical_updates = [
    {
        "name": "Sachin",
        "role": "Lead Male Protagonist",
        "visual_dna": "Sachin: Stylized 3D Pixar-style cartoon animation character, 18-19 year old South Indian Malayali teenage boy. Youthful boyish facial features, soft clean jawline, completely clean-shaven smooth caramel-tan South Indian skin with velvety cartoon subsurface scattering shaders (STRICTLY TEENAGER / YOUTHFUL TEEN GUY, ZERO FACIAL HAIR, ZERO STUBBLE, ZERO MATURE LINES). Big bright expressive warm dark-brown cartoon eyes filled with lively excitement, natural youthful eyebrows, playful contagious boyish grin showing clean straight white upper teeth. Messy voluminous wavy jet-black teen cartoon hair with casual bouncy textured locks falling slightly over his forehead. Lanky, slender athletic teenage build (height 5'9\", youthful 1:6.5 proportions, natural teen posture, strictly non-chibi) (PROHIBIT CHILD/TODDLER/BABY/CHIBI ANATOMY, PROHIBIT REALISTIC HUMAN SKIN PORES, PROHIBIT UNCANNY REALISM).",
        "locked_attire": "Plain Navy Blue solid crewneck T-shirt, charcoal-black denim jeans, brown leather travel cross-bag, clean white sneakers. Absolutely zero costume variations.",
        "voice_persona": "Sachin: 18-19yo enthusiastic South Indian Malayali teenage boy voice, warm playful Kochi cadence, youthful eager tone (Gemini Voice 'Fenrir' / Edge-TTS 'ml-IN-MidhunNeural')"
    },
    {
        "name": "Reenu",
        "role": "Lead Female Protagonist",
        "visual_dna": "Reenu: Stylized 3D Pixar-style cartoon animation character, 18-19 year old South Indian Malayali teenage girl. Adorable Pixar teen heroine face, soft rounded cheeks with fresh natural peach-pink blush, smooth warm golden-fair skin with soft velvety cartoon shaders (STRICTLY TEENAGER / YOUTHFUL TEEN GIRL, NO MATURE AGING). Big sparkling expressive hazel-brown doe eyes with lush soft eyelashes, youthful naturally arched eyebrows, cute small button nose, radiant sweet bubbly teenage smile showing clean white teeth. Shoulder-length voluminous dark-brown wavy hair with bouncy youthful curls and soft curtain bangs framing her temples. Slender, petite teenage girl proportions (height 5'3\", youthful 1:6.2 proportions, lively teen posture, strictly non-chibi) (PROHIBIT CHILD/TODDLER/BABY/CHIBI ANATOMY, PROHIBIT REALISTIC HUMAN SKIN PORES, PROHIBIT UNCANNY REALISM).",
        "locked_attire": "Pastel Lavender T-shirt with white cloud and daisy floral prints, light-wash denim skirt, silver wristwatch, white sneakers. Absolutely zero costume variations.",
        "voice_persona": "Reenu: 18-19yo sweet expressive South Indian Malayali teenage girl voice, lively warm bubbly Malayalam tone (Gemini Voice 'Kore' / Edge-TTS 'ml-IN-SobhanaNeural')"
    },
    {
        "name": "Amal",
        "role": "Best Friend & Comic Relief",
        "visual_dna": "Amal: Stylized 3D Pixar-style cartoon animation character, 18-19 year old South Indian Malayali teenage boy. Clean-shaven youthful teenage face, cheerful energetic jawline, warm dusky South Indian skin tone with smooth cartoon shaders, lively witty dark-brown animated eyes, expressive comedic eyebrows, cheerful mischievous teenage grin (STRICTLY TEENAGER / YOUTHFUL TEEN GUY, ZERO BEARD, ZERO STUBBLE, ZERO MATURE WRINKLES). Messy stylish short curly dark teen cartoon hair with textured volume. Energetic, slender athletic teenage build (height 5'8\", youthful 1:6.5 proportions, relaxed teen posture, strictly non-chibi) (PROHIBIT CHILD/TODDLER/BABY/CHIBI ANATOMY, PROHIBIT REALISTIC HUMAN SKIN PORES, PROHIBIT UNCANNY REALISM).",
        "locked_attire": "Plain Terracotta Rust-Orange solid T-shirt, faded blue denim jeans, black slip-on sneakers. Absolutely zero costume variations.",
        "voice_persona": "Amal: 18-19yo witty relatable Malayali teenage friend voice, energetic comedic youthful Malayalam tone (Gemini Voice 'Puck' / Edge-TTS 'ml-IN-MidhunNeural')"
    }
]

def repair_tab4():
    payload = {
        "action": "sync_character_registry",
        "character_updates": canonical_updates
    }
    
    print("Sending character_updates to Google Apps Script...")
    req = urllib.request.Request(
        GAS_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'text/plain; charset=utf-8', 'User-Agent': 'Mozilla/5.0'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = resp.read().decode('utf-8')
            print("Response:", body)
            data = json.loads(body)
            if data.get("success"):
                print("✓ Successfully updated Tab 4 on Google Sheets!")
            else:
                print("Error returned:", data)
    except Exception as e:
        print("Failed to update via sync_character_registry:", e)

    print("\nVerifying updated characters from live sheet...")
    get_req = urllib.request.Request(f"{GAS_URL}?action=get_characters", headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(get_req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for c in data.get("characters", []):
                if c["name"] in ["Sachin", "Reenu", "Amal"]:
                    print(f"\n--- {c['name']} ---")
                    print(f"Role: {c.get('role')}")
                    print(f"Visual DNA: {c.get('visual_dna')[:90]}...")
                    print(f"Locked Attire: {c.get('locked_attire')}")
                    print(f"Voice Persona: {c.get('voice_persona')}")
    except Exception as e:
        print("Failed to verify live characters:", e)

if __name__ == "__main__":
    repair_tab4()
