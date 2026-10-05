import json
import re

with open('current_episode_shots.json', 'r', encoding='utf-8') as f:
    ep_data = json.load(f)

# Load existing base portal.html for CSS and framework
with open('portal.html', 'r', encoding='utf-8') as f:
    base_html = f.read()

# Replace episodeData
shots_json_str = json.dumps(ep_data, ensure_ascii=False, indent=2)

# Update renderShots in JavaScript so prompt-box displays formatted JSON prompt
new_render_shots = """
    function renderShots() {
      const container = document.getElementById('shotsContainer');
      const uploadList = document.getElementById('uploadList');
      container.innerHTML = '';
      uploadList.innerHTML = '';

      const runtimeStr = episodeData.calculated_runtime_display || '2m 08s';
      document.getElementById('epNumberTag').innerText = `CURRENT PRODUCTION • EPISODE ${episodeData.episode_number}`;
      document.getElementById('epTitle').innerHTML = `${episodeData.title_english} <span>${episodeData.title_malayalam}</span>`;
      document.getElementById('epSynopsis').innerText = episodeData.synopsis;
      document.getElementById('shotCountBadge').innerText = `${episodeData.shots.length} Shots • ⏱️ ${runtimeStr}`;

      episodeData.shots.forEach((shot) => {
        const durClass = shot.duration === '4s' ? 'dur-4s' : (shot.duration === '8s' ? 'dur-8s' : 'dur-6s');
        const dialogueHtml = shot.dialogue_malayalam ? `
          <div class="dialogue-box">
            <b>💬 സംഭാഷണം (Malayalam Dialogue):</b> "${shot.dialogue_malayalam}"
          </div>
        ` : `
          <div class="dialogue-box-silent">
            <span style="color: var(--text-muted); font-size: 13px;">🤫 <i>No spoken dialogue (Silent emotional gaze / ambient beat)</i></span>
          </div>
        `;

        const jsonPromptFormatted = JSON.stringify(shot.json_prompt, null, 2);

        // 1. Render Shot Card
        const card = document.createElement('div');
        card.className = 'shot-card';
        card.innerHTML = `
          <div class="shot-header">
            <div class="shot-meta">
              <span class="shot-badge">Shot #${shot.shot_number}</span>
              <span class="dur-badge ${durClass}">⏱️ ${shot.duration}</span>
              <span class="char-badge">👤 ${shot.character}</span>
              <span style="font-size: 12px; background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); padding: 3px 8px; border-radius: 6px; font-weight: 700;">
                🔇 NO BGM
              </span>
            </div>
            <button class="copy-btn" style="background: linear-gradient(135deg, #f97316, #ea580c); font-weight: 700; border: none; padding: 10px 18px; box-shadow: 0 4px 12px rgba(249, 115, 22, 0.35);" onclick="copyJsonPrompt(${shot.shot_number}, this)">
              📋 Copy JSON Prompt
            </button>
          </div>
          ${dialogueHtml}
          <p style="font-size: 14px; margin-bottom: 8px;"><b>Action:</b> ${shot.action_summary}</p>
          <div class="prompt-box" style="background: #080a10; border: 1px solid #1e2640; border-radius: 8px; padding: 14px 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 1px solid #1a2238; padding-bottom: 6px;">
              <span style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--accent-blue); font-weight: 700;">
                📦 GOOGLE FLOW JSON PROMPT (Character DNA • Location • Camera • Dialogue • No-BGM):
              </span>
              <span style="font-size: 11px; color: var(--text-muted);">JSON Format</span>
            </div>
            <pre style="margin: 0; font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; line-height: 1.5; color: #a5f3fc; white-space: pre-wrap; word-break: break-word;" id="promptJson_${shot.shot_number}">${escapeHtml(jsonPromptFormatted)}</pre>
          </div>
        `;
        container.appendChild(card);

        // 2. Render Upload Item
        const upItem = document.createElement('div');
        upItem.className = 'upload-item';
        upItem.id = `upItem_${shot.shot_number}`;
        upItem.innerHTML = `
          <div>
            <b>Shot #${shot.shot_number}</b> (<span class="dur-badge ${durClass}" style="padding: 2px 6px; font-size: 11px;">${shot.duration}</span>) — <span style="color: var(--text-muted); font-size: 13px;">${shot.character}</span>
            ${shot.dialogue_malayalam ? `<div style="font-size: 12px; color: #fde047; font-family: 'Noto Sans Malayalam'; margin-top: 4px;">"${shot.dialogue_malayalam}"</div>` : ''}
          </div>
          <span class="status-pill status-pending" id="statusPill_${shot.shot_number}">⏳ Awaiting Video</span>
        `;
        uploadList.appendChild(upItem);
      });
    }

    function escapeHtml(str) {
      return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    function copyJsonPrompt(shotNum, btn) {
      const text = document.getElementById(`promptJson_${shotNum}`).innerText;
      navigator.clipboard.writeText(text).then(() => {
        const originalText = btn.innerHTML;
        btn.innerHTML = '✓ Copied JSON Prompt!';
        btn.style.background = '#059669';
        setTimeout(() => {
          btn.innerHTML = originalText;
          btn.style.background = 'linear-gradient(135deg, #f97316, #ea580c)';
        }, 2000);
      });
    }
"""

# Replace episodeData in base_html
updated_html = re.sub(r'let episodeData = \{.*?\};\n\n    let selectedFiles', f'let episodeData = {shots_json_str};\n\n    let selectedFiles', base_html, flags=re.DOTALL)

# Replace renderShots function
updated_html = re.sub(r'function renderShots\(\) \{.*?function switchTab', new_render_shots + "\n\n    function switchTab", updated_html, flags=re.DOTALL)

# Write to all 3 paths
paths = [
    "c:/Users/HP/OneDrive/Desktop/VISHNU/WEB/Sachin_And_Reenu_Series/portal.html",
    "c:/Users/HP/OneDrive/Desktop/VISHNU/WEB/Sachin_And_Reenu_Series/repo_studio/portal.html",
    "c:/Users/HP/OneDrive/Desktop/VISHNU/WEB/portal.html"
]

for p in paths:
    with open(p, 'w', encoding='utf-8') as f:
        f.write(updated_html)
    print(f"Updated: {p}")

print("All portals successfully updated with JSON prompt boxes!")
