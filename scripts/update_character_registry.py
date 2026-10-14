import json
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GAS_URL = os.getenv("GAS_WEBHOOK_URL", "https://script.google.com/macros/s/AKfycbyivkrK_jL1ejwNqUvHe8KVFNkSuJSwZbWSmuE1YATqL5jCneMlqlKbf0EH7mwpc4gybA/exec")

CHARACTER_DATABASE = {
    "Sachin": {
        "name": "Sachin",
        "age": 24,
        "age_group": "Young Adult",
        "gender": "male",
        "role": "Lead Male Protagonist",
        "height_build": "Tall, lean athletic adult male build (height 5'11\"), broad shoulders tapering to a slim waist, realistic adult head-to-body scale (1:7), strictly non-chibi",
        "face": "Handsome defined adult male facial geometry, sculpted masculine jawline with a subtle chin cleft, clean-shaven smooth caramel-tan South Indian skin with soft Pixar subsurface scattering shaders. Warm expressive dark-brown almond-shaped animated cartoon eyes, thick dark sculpted masculine eyebrows with a slight expressive arch, confident genuine contagious warm animated smile revealing clean straight white upper teeth",
        "hair": "Voluminous jet-black stylized textured wavy cartoon hair swept back and to the side with sculpted animated clumps and soft glossy sheen",
        "attire": "Plain Navy Blue solid crewneck T-shirt, charcoal-black denim jeans, brown leather travel cross-bag, clean white sneakers.",
        "locked_attire": "Plain Navy Blue solid crewneck T-shirt, charcoal-black denim jeans, brown leather travel cross-bag, clean white sneakers.",
        "voice": "Fenrir",
        "voice_persona": "Sachin: 24yo charming South Indian Malayali boyish adult expressive voice, warm Malayalam cadence (Gemini Voice 'Fenrir' / Edge-TTS 'ml-IN-MidhunNeural')",
        "visual_dna": (
            "Sachin: Stylized 3D Pixar-style cartoon animation character, 24-year-old young adult South Indian Malayali man. "
            "Handsome defined adult male facial geometry, sculpted masculine jawline with a subtle chin cleft, clean-shaven smooth caramel-tan South Indian skin with soft Pixar subsurface scattering shaders. "
            "Warm expressive dark-brown almond-shaped animated cartoon eyes, thick dark sculpted masculine eyebrows with a slight expressive arch, "
            "confident genuine contagious warm animated smile revealing clean straight white upper teeth. "
            "Voluminous jet-black stylized textured wavy cartoon hair swept back and to the side with sculpted animated clumps and soft glossy sheen. "
            "Tall lean athletic adult male build (height 5'11\"), broad shoulders narrowing to a slim waist, defined neck and realistic adult proportions with 1:7 head-to-body scale "
            "(STRICTLY YOUNG ADULT MAN, PROHIBIT BOY/CHILD/TEEN/CHIBI/TODDLER ANATOMY, PROHIBIT REALISTIC HUMAN SKIN PORES, PROHIBIT UNCANNY REALISM)."
        )
    },
    "Reenu": {
        "name": "Reenu",
        "age": 22,
        "age_group": "Young Adult",
        "gender": "female",
        "role": "Lead Female Protagonist",
        "height_build": "Slender, graceful young adult female proportions (height 5'4\"), elegant upright adult posture with realistic adult head-to-body scale (1:6.5), strictly non-chibi",
        "face": "Adorable Disney-Pixar heroine facial structure, soft heart-shaped jawline, delicate rounded cheeks with a gentle peach-rose blush, warm golden-fair South Indian skin with velvety cartoon subsurface scattering shaders. Captivating large expressive hazel-brown animated cartoon doe eyes with luminous clarity, lush defined dark-brown cartoon eyelashes, elegantly arched soft feminine dark eyebrows, delicate small sculpted button nose, radiant joyful warm animated smile revealing clean straight white teeth",
        "hair": "Shoulder-length voluminous rich chocolate-brown wavy hair with soft bouncy curls and cute curtain bangs framing forehead and temples",
        "attire": "Pastel Lavender T-shirt with white cloud and daisy floral prints, light-wash denim skirt, silver wristwatch, white sneakers.",
        "locked_attire": "Pastel Lavender T-shirt with white cloud and daisy floral prints, light-wash denim skirt, silver wristwatch, white sneakers.",
        "voice": "Kore",
        "voice_persona": "Reenu: 22yo South Indian Malayali young woman, sweet expressive warm feminine Malayalam voice (Gemini Voice 'Kore' / Edge-TTS 'ml-IN-SobhanaNeural')",
        "visual_dna": (
            "Reenu: Stylized 3D Pixar-style cartoon animation character, 22-year-old young adult South Indian Malayali woman. "
            "Adorable Disney-Pixar heroine facial structure, soft heart-shaped jawline, delicate rounded cheeks with a gentle peach-rose blush, "
            "warm golden-fair South Indian skin with velvety cartoon subsurface scattering shaders. "
            "Captivating large expressive hazel-brown animated cartoon doe eyes with luminous clarity, lush defined dark-brown cartoon eyelashes, "
            "elegantly arched soft feminine dark eyebrows, delicate small sculpted button nose, radiant joyful warm animated smile revealing clean straight white teeth. "
            "Shoulder-length voluminous rich chocolate-brown wavy hair with soft bouncy curls and cute curtain bangs framing her forehead and temples. "
            "Slender graceful young adult female proportions (height 5'4\"), elegant upright adult posture with 1:6.5 head-to-body scale "
            "(STRICTLY YOUNG ADULT WOMAN, PROHIBIT GIRL/CHILD/TEEN/CHIBI/TODDLER ANATOMY, PROHIBIT REALISTIC HUMAN SKIN PORES, PROHIBIT UNCANNY REALISM)."
        )
    },
    "Amal": {
        "name": "Amal",
        "age": 24,
        "age_group": "Young Adult",
        "gender": "male",
        "role": "Best Friend & Comic Relief",
        "height_build": "Sturdy athletic adult male proportions (height 5'10\"), broad shoulders, adult build and posture with realistic adult head-to-body scale (1:7), strictly non-chibi",
        "face": "Defined adult square jawline, neatly trimmed stylish dark mustache and short goatee beard, warm dusky South Indian skin tone with smooth cartoon shaders, lively humorous dark-brown animated eyes, dynamic expressive comedic eyebrows, warm energetic friendly cartoon grin",
        "hair": "Modern textured short dark curls with clean faded sides",
        "attire": "Plain Terracotta Rust-Orange solid T-shirt, faded blue denim jeans, black slip-on sneakers.",
        "locked_attire": "Plain Terracotta Rust-Orange solid T-shirt, faded blue denim jeans, black slip-on sneakers.",
        "voice": "Puck",
        "voice_persona": "Amal: 24yo witty relatable Malayali friend voice, comedic energetic Malayalam tone (Gemini Voice 'Puck' / Edge-TTS 'ml-IN-MidhunNeural')",
        "visual_dna": (
            "Amal: Stylized 3D Pixar-style cartoon animation character, 24-year-old young adult South Indian Malayali man. "
            "Defined adult square jawline, neatly trimmed stylish dark mustache and short goatee beard, warm dusky South Indian skin tone with smooth cartoon shaders. "
            "Lively humorous dark-brown animated eyes, dynamic expressive comedic eyebrows, warm energetic friendly cartoon grin. "
            "Modern textured short dark curls with clean faded sides. "
            "Sturdy athletic adult male proportions (height 5'10\"), broad shoulders and realistic adult head-to-body scale "
            "(STRICTLY YOUNG ADULT MAN, PROHIBIT BOY/CHILD/TEEN/CHIBI/TODDLER ANATOMY, PROHIBIT REALISTIC HUMAN SKIN PORES, PROHIBIT UNCANNY REALISM)."
        )
    },
    "Sreedharan (The Caretaker)": {
        "name": "Sreedharan (The Caretaker)",
        "age": 65,
        "age_group": "Elderly",
        "gender": "male",
        "role": "Mysterious Munnar Homestay Caretaker",
        "height_build": "Slightly hunched dignified elderly build, slow calculated movements, height 5'7\"",
        "face": "Weathered mature Pixar elderly face, distinguished thick expressive grey mustache, bushy grey eyebrows, deep mysterious observant unblinking cartoon eyes",
        "hair": "Thinning salt-and-pepper hair, greying temples",
        "attire": "Traditional white Kerala cotton mundu and a faded grey cotton jubba with brown leather sandals.",
        "locked_attire": "Traditional white Kerala cotton mundu and a faded grey cotton jubba with brown leather sandals.",
        "voice": "Deep, raspy, slow-paced Idukki Malayalam baritone",
        "voice_persona": "Sreedharan (The Caretaker): Deep raspy mysterious high-range Malayalam tone (Central Travancore / Idukki dialect)",
        "visual_dna": (
            "Sreedharan (The Caretaker): Stylized 3D Pixar-style cartoon animation character, 65-year-old elderly South Indian Malayali man. "
            "Weathered dignified mature Pixar elderly face, distinguished thick expressive grey mustache, bushy grey eyebrows, deep mysterious observant unblinking dark cartoon eyes, "
            "slightly hunched dignified elderly build, thinning salt-and-pepper hair with greying temples (STRICTLY 3D ANIMATION ELDERLY CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES)."
        )
    },
    "Tea Shopkeeper": {
        "name": "Tea Shopkeeper",
        "age": 48,
        "age_group": "Middle-Aged",
        "gender": "male",
        "role": "High-Range Tea Stall Owner",
        "height_build": "Sturdy working adult build, broad shoulders, height 5'8\"",
        "face": "Warm expressive weathered high-range cartoon face, thick black-and-grey mustache, welcoming animated dark eyes",
        "hair": "Thick black hair with grey specks, combed back",
        "attire": "Faded blue cotton half-sleeve shirt and traditional checkered cotton lungi.",
        "locked_attire": "Faded blue cotton half-sleeve shirt and traditional checkered cotton lungi.",
        "voice": "Rustic high-range Malayalam tea vendor voice",
        "voice_persona": "Tea Shopkeeper: Local Malayali tea vendor, cautionary rustic high-range tone",
        "visual_dna": (
            "Tea Shopkeeper: Stylized 3D Pixar-style cartoon animation character, 48-year-old middle-aged South Indian Malayali man. "
            "Warm expressive weathered high-range cartoon face, thick black-and-grey mustache, welcoming animated dark eyes, sturdy working adult build, thick dark hair with grey specks combed back "
            "(STRICTLY 3D ANIMATION CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES)."
        )
    },
    "Bhadra (The Woman in the Mist)": {
        "name": "Bhadra (The Woman in the Mist)",
        "age": 28,
        "age_group": "Young Adult",
        "gender": "female",
        "role": "Enigmatic Spirit of the High Ranges",
        "height_build": "Graceful floating slender adult female proportions, ethereal posture",
        "face": "Ethereal, hauntingly elegant adult female facial features, glowing animated eyes, melancholic calm expression",
        "hair": "Long flowing dark wavy hair drifting like mountain mist vapors",
        "attire": "Traditional white Kerala Set-Mundu with dull gold border, edges dissolving into white mist.",
        "locked_attire": "Traditional white Kerala Set-Mundu with dull gold border, mist-infused translucent edges.",
        "voice": "Echoing, soft, melancholic whisper",
        "voice_persona": "Bhadra: Soft echoing ethereal whisper in pure Malayalam cadence",
        "visual_dna": (
            "Bhadra (The Woman in the Mist): Ethereal stylized 3D Pixar-style cartoon animation character, 28-year-old adult South Indian Malayali woman. "
            "Enigmatic soft glowing animated hazel eyes, hauntingly elegant adult female facial features, flowing dark wavy hair drifting like mountain mist vapors, "
            "graceful floating slender adult posture with ethereal luminescence (STRICTLY 3D ANIMATION CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES)."
        )
    },
    "Kurian": {
        "name": "Kurian",
        "age": 57,
        "age_group": "Elderly",
        "gender": "male",
        "role": "Reenu's Traditional Father (Retired Treasury Officer)",
        "height_build": "Upright dignified mature build, height 5'10\"",
        "face": "Rigid square jaw, salt-and-pepper mustache, wire-rimmed reading glasses on a stern nose, piercing observant eyes",
        "hair": "Short salt-and-pepper hair, neatly parted",
        "attire": "Crisp starched white cotton Jubba paired with pristine white double Mundu with gold Kasavu border, brown leather sandals, analog Titan watch.",
        "locked_attire": "Crisp white cotton Jubba, white Kasavu Mundu, brown leather sandals, analog Titan watch.",
        "voice": "Deep authoritative Kottayam Malayalam baritone",
        "voice_persona": "Kurian: Deep, authoritative, slow-paced stern Malayali father voice with judicial gravity",
        "visual_dna": (
            "Kurian (Reenu's Father): Stylized 3D Pixar-style cartoon animation character, 57-year-old mature South Indian Malayali gentleman. "
            "Rigid square jaw, distinguished salt-and-pepper mustache, wire-rimmed reading glasses resting on a stern nose, piercing observant dark eyes, "
            "tall upright dignified posture, short neatly parted salt-and-pepper hair (STRICTLY 3D ANIMATION ELDERLY CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES)."
        )
    },
    "Annamma": {
        "name": "Annamma",
        "age": 53,
        "age_group": "Elderly",
        "gender": "female",
        "role": "Reenu's Observant Mother",
        "height_build": "Soft rounded maternal silhouette, height 5'4\"",
        "face": "Gentle face with sharp observational glances, warm twinkling eyes, expressive domestic intuition",
        "hair": "Silver-streaked black hair pinned in a neat traditional bun",
        "attire": "Handloom bottle-green cotton saree with mustard border, thin gold bangles that clink rhythmically, gold crucifix necklace.",
        "locked_attire": "Handloom bottle-green cotton saree with mustard border, thin gold bangles, gold crucifix necklace.",
        "voice": "Melodic Central Travancore maternal Malayalam tone",
        "voice_persona": "Annamma: Soft-spoken, melodic Central Travancore inflection laced with maternal warmth and sharp wit",
        "visual_dna": (
            "Annamma (Reenu's Mother): Stylized 3D Pixar-style cartoon animation character, 53-year-old mature South Indian Malayali matriarch. "
            "Soft rounded maternal facial silhouette, gentle expressive face framed by silver-streaked black hair pinned in a neat traditional bun, "
            "warm observant brown eyes with gentle domestic intuition (STRICTLY 3D ANIMATION ELDERLY CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES)."
        )
    },
    "Madhavan": {
        "name": "Madhavan",
        "age": 52,
        "age_group": "Middle-Aged",
        "gender": "male",
        "role": "Reenu's Traditional Father (Season 2)",
        "height_build": "Dignified traditional posture, height 5'10\"",
        "face": "Expressive salt-and-pepper mustache, warm yet stern dark eyes, slightly greying temples in dark curly hair",
        "hair": "Dark curly hair with grey temples",
        "attire": "Crisp traditional Kerala cream-white cotton jubba, off-white kasavu mundu with thin golden border, black leather sandals, silver vintage wrist watch.",
        "locked_attire": "Traditional Kerala cream-white cotton jubba, off-white kasavu mundu, black leather sandals, silver vintage watch.",
        "voice": "Deep stern traditional Malayalam father voice",
        "voice_persona": "Madhavan: Deep authoritative South Indian male voice with stern commanding tone",
        "visual_dna": (
            "Madhavan (Reenu's Father): Stylized 3D Pixar-style cartoon animation character, 52-year-old mature South Indian Malayali gentleman. "
            "Dignified traditional Malayali father features, expressive salt-and-pepper mustache, warm yet stern dark eyes, "
            "slightly greying temples in dark curly hair (STRICTLY 3D ANIMATION ADULT CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES)."
        )
    },
    "Girija": {
        "name": "Girija",
        "age": 48,
        "age_group": "Middle-Aged",
        "gender": "female",
        "role": "Reenu's Loving Mother (Season 2)",
        "height_build": "Kind motherly build, height 5'4\"",
        "face": "Kind round motherly face, warm expressive dark-brown eyes, endearing affectionate smile with cute dimple",
        "hair": "Neat traditional hair bun adorned with fresh white jasmine flowers (mulla poo)",
        "attire": "Elegant Kerala traditional cream cotton set-saree with emerald-green border, delicate gold necklace, small jhumka earrings, gold bangles.",
        "locked_attire": "Traditional cream cotton set-saree with emerald-green border, gold jewelry, jasmine hair flowers.",
        "voice": "Warm affectionate maternal Malayalam tone",
        "voice_persona": "Girija: Gentle affectionate maternal Malayalam voice",
        "visual_dna": (
            "Girija (Reenu's Mother): Stylized 3D Pixar-style cartoon animation character, 48-year-old mature South Indian Malayali lady. "
            "Kind round motherly face, warm expressive dark-brown eyes, neat traditional hair bun adorned with fresh fragrant "
            "white jasmine flowers (mulla poo), endearing affectionate smile with cute cartoon dimple "
            "(STRICTLY 3D ANIMATION ADULT CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES)."
        )
    },
    "Broker Shaji": {
        "name": "Broker Shaji",
        "age": 45,
        "age_group": "Middle-Aged",
        "gender": "male",
        "role": "Real Estate Broker",
        "height_build": "Slightly plump comical build, energetic posture, height 5'7\"",
        "face": "Round expressive cartoon face, thin animated mustache, glistening slicked-back hair, expressive comedic eyebrows",
        "hair": "Slicked-back dark hair glistening with raindrops",
        "attire": "Bright mustard-yellow casual polo t-shirt, chocolate-brown casual trousers, black rubber slip-on shoes, compact black folding umbrella.",
        "locked_attire": "Mustard-yellow casual polo t-shirt, chocolate-brown trousers, black rubber slip-ons, umbrella in hand.",
        "voice": "Lively theatrical broker cadence",
        "voice_persona": "Broker Shaji: Booming theatrical uninhibited South Indian Malayalam broker voice",
        "visual_dna": (
            "Broker Shaji: Stylized 3D Pixar-style cartoon animation character, 45-year-old middle-aged South Indian Malayali broker. "
            "Energetic round cartoon face, thin animated mustache, slicked-back dark cartoon hair glistening with raindrops, "
            "expressive comedic eyebrows, slightly plump cartoon build (STRICTLY 3D ANIMATION CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES)."
        )
    }
}

def update_character_registry():
    state_file = Path("story_state.json")
    if not state_file.exists():
        print("story_state.json not found!")
        return

    with open(state_file, "r", encoding="utf-8") as f:
        st = json.load(f)

    st["characters"] = CHARACTER_DATABASE

    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)

    print(f"[SUCCESS] Updated story_state.json with {len(CHARACTER_DATABASE)} hyper-detailed adult character entries!")

    # Sync to Google Sheet Tab 5 (Character_Registry)
    if GAS_URL:
        char_updates = [
            {
                "name": c["name"],
                "role": c.get("role", "Character"),
                "attire": c["locked_attire"],
                "locked_attire": c["locked_attire"],
                "visual_dna": c["visual_dna"],
                "voice_persona": c["voice_persona"]
            }
            for c in CHARACTER_DATABASE.values()
        ]
        payload = {
            "action": "update_character_registry",
            "character_updates": char_updates,
            "new_characters": char_updates
        }
        try:
            r = requests.post(GAS_URL, data=json.dumps(payload), headers={"Content-Type": "text/plain"}, timeout=30)
            print(f"[SUCCESS] Synced all character updates to Google Sheet Tab 5! (HTTP {r.status_code})")
        except Exception as e:
            print(f"Notice syncing characters to Sheet: {e}")

if __name__ == "__main__":
    update_character_registry()
