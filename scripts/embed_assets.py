import base64
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

fav_path = Path(r'c:\Users\HP\OneDrive\Desktop\VISHNU\WEB\assets\favicon.png')
med_path = Path(r'c:\Users\HP\OneDrive\Desktop\VISHNU\WEB\assets\sachin_reenu_logo_med.jpg')

with open(fav_path, 'rb') as f:
    fav_b64 = 'data:image/png;base64,' + base64.b64encode(f.read()).decode('utf-8')

with open(med_path, 'rb') as f:
    logo_b64 = 'data:image/jpeg;base64,' + base64.b64encode(f.read()).decode('utf-8')

portal_path = Path(r'c:\Users\HP\OneDrive\Desktop\VISHNU\WEB\Sachin_And_Reenu_Series\repo_studio\portal.html')
content = portal_path.read_text(encoding='utf-8')

# 1. Update favicon in <head>
fav_tags = f'''  <title>Sachin & Reenu — 3D Animation Creator Studio</title>
  <link rel="icon" type="image/png" href="{fav_b64}">
  <link rel="shortcut icon" type="image/png" href="{fav_b64}">
  <link rel="apple-touch-icon" href="{logo_b64}">'''

content = re.sub(
    r'<title>Sachin & Reenu.*?</title>.*?<link rel="preconnect"',
    fav_tags + '\n  <link rel="preconnect"',
    content,
    flags=re.DOTALL
)

# 2. Update .studio-loader-overlay CSS to be visible by default, and .hidden to hide
css_old = r'\.studio-loader-overlay\s*\{.*?\.studio-loader-card\s*\{'
css_new = '''    .studio-loader-overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      background: rgba(9, 12, 21, 0.94);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      z-index: 999999;
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 1;
      visibility: visible;
      transition: opacity 0.45s cubic-bezier(0.4, 0, 0.2, 1), visibility 0.45s ease;
      pointer-events: all;
    }

    .studio-loader-overlay.hidden {
      opacity: 0;
      visibility: hidden;
      pointer-events: none;
    }

    .studio-loader-card {'''

content = re.sub(css_old, css_new, content, count=1, flags=re.DOTALL)

# 3. Update transform on .studio-loader-overlay.hidden .studio-loader-card
content = re.sub(
    r'\.studio-loader-overlay\.active \.studio-loader-card\s*\{\s*transform:\s*scale\(1\);\s*\}',
    '.studio-loader-overlay.hidden .studio-loader-card {\n      transform: scale(0.92);\n    }',
    content
)

# 4. Update the img src in studioLoaderOverlay and brand-logo to use inline logo_b64
content = re.sub(
    r'<img src="assets/sachin_reenu_logo\.jpg" alt="Sachin & Reenu" class="studio-loader-img">',
    f'<img src="{logo_b64}" alt="Sachin & Reenu" class="studio-loader-img">',
    content
)

content = re.sub(
    r'<div class="brand-logo"[^>]*>\s*<img src="assets/sachin_reenu_logo\.jpg"',
    f'<div class="brand-logo" style="overflow: hidden; padding: 0; background: none; border: 2px solid rgba(249, 115, 22, 0.4);">\n          <img src="{logo_b64}"',
    content
)

# 5. Update showStudioLoader / hideStudioLoader JS
js_loader_old = r'function showStudioLoader\(statusText\)\s*\{.*?function hideStudioLoader\(\)\s*\{.*?\}'
js_loader_new = '''function showStudioLoader(statusText) {
      const overlay = document.getElementById('studioLoaderOverlay');
      const textEl = document.getElementById('studioLoaderStatusText');
      if (textEl && statusText) textEl.innerText = statusText;
      if (overlay) {
        overlay.classList.remove('hidden');
      }
    }

    function updateStudioLoaderStatus(statusText) {
      const textEl = document.getElementById('studioLoaderStatusText');
      if (textEl && statusText) textEl.innerText = statusText;
    }

    function hideStudioLoader() {
      const overlay = document.getElementById('studioLoaderOverlay');
      if (overlay) {
        overlay.classList.add('hidden');
      }
    }'''

content = re.sub(js_loader_old, js_loader_new, content, count=1, flags=re.DOTALL)

# 6. Update window.onload to keep loader visible for at least 900ms on first launch
onload_old = r'window\.onload = async \(\) =>\s*\{.*?renderSeriesThumbnailPrompt\(\);.*?try\s*\{.*?await Promise\.allSettled\(.*?\);.*?\}\s*catch\s*\(e\)\s*\{\s*\}\s*\};'
onload_new = '''window.onload = async () => {
      initGeminiChat();
      renderShots();
      renderSeasonStoryRoadmap();
      renderCharacterCards();
      renderSeriesThumbnailPrompt();

      try {
        await Promise.allSettled([
          syncDriveStatus(),
          syncLiveFromGoogleSheet(),
          fetchSeasonStoryData(),
          fetchCharacterData()
        ]);
        updateStudioLoaderStatus("✓ Studio Ready!");
      } catch (e) {}

      setTimeout(() => {
        hideStudioLoader();
      }, 900);
    };'''

content = re.sub(onload_old, onload_new, content, count=1, flags=re.DOTALL)

# Write back to repo_studio
portal_path.write_text(content, encoding='utf-8')
print('[SUCCESS] repo_studio/portal.html updated with inline base64 assets and default-visible loader!')

# Now copy to all targets
targets = [
    Path(r'C:\Users\HP\OneDrive\Desktop\New folder (3)\portal.html'),
    Path(r'C:\Users\HP\OneDrive\Desktop\New folder (3)\index.html'),
    Path(r'c:\Users\HP\OneDrive\Desktop\VISHNU\WEB\Sachin_And_Reenu_Series\portal.html'),
    Path(r'c:\Users\HP\OneDrive\Desktop\VISHNU\WEB\portal.html')
]

for t in targets:
    t.parent.mkdir(parents=True, exist_ok=True)
    t.write_text(content, encoding='utf-8')
    print('[SUCCESS] Updated:', t)
