import json
from pathlib import Path

shots_path = Path("current_episode_shots.json")
if shots_path.exists():
    with open(shots_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sachin_dna = (
        "Sachin: Stylized 3D Pixar-style cartoon animation character, 24yo South Indian Malayali boy, "
        "endearing boyish cartoon features, large expressive warm animated brown eyes, playful genuine contagious cartoon smile, "
        "stylized soft textured wavy dark cartoon hair, cute slightly exaggerated 3D character proportions with smooth cartoon shaders "
        "(STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). "
        "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT, PROHIBIT ALL TRADITIONAL/ETHNIC WEAR: NO FORMAL COLLARED SHIRTS, NO FORMAL TROUSERS, STRICT MODERN CASUAL STREETWEAR ONLY): "
        "Solid olive-green plain crewneck t-shirt (strictly flat solid color, zero patterns or graphics), relaxed-fit dark indigo denim jeans, classic white sneakers, brown leather travel cross-bag worn diagonally across chest. Absolutely zero costume variations."
    )

    reenu_dna = (
        "Reenu: Stylized 3D Pixar-style cartoon animation character, 22yo South Indian Malayali girl, "
        "big expressive hazel-brown animated cartoon doe eyes with lush stylized eyelashes, soft rounded cute cartoon cheeks, sweet warm animated smile, "
        "voluminous bouncy wavy dark-brown cartoon hair with soft curtain bangs, stylized 3D character proportions with smooth vibrant cartoon shaders "
        "(STRICTLY 3D ANIMATION CARTOON CHARACTER, PROHIBIT REALISTIC HUMAN FEATURES). "
        "STRICTLY LOCKED ATTIRE (IDENTICAL IN EVERY SHOT, PROHIBIT ALL TRADITIONAL/ETHNIC WEAR: NO KURTIS, NO SAREES, NO SALWARS, NO DUPATTAS, NO JHUMKAS, STRICT MODERN CASUAL STREETWEAR ONLY): "
        "Pastel lavender and blush-pink floral-doodle pattern printed oversized t-shirt, high-waisted medium-blue denim skirt, clean white sneakers, silver wrist watch. Absolutely zero costume variations."
    )

    for shot in data.get("shots", []):
        jp = shot.get("json_prompt", {})
        for c in jp.get("characters_present", []):
            if c.get("name") == "Sachin":
                c["visual_dna"] = sachin_dna
            elif c.get("name") == "Reenu":
                c["visual_dna"] = reenu_dna

    with open(shots_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("[OK] Successfully updated current_episode_shots.json with strict anti-traditional casual locks!")
