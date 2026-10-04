# ❤️ SACHIN & REENU (സച്ചിൻ & റീനു) — Autonomous AI Drama Studio

An end-to-end autonomous 3D animated web series production pipeline powered by **Google Gemini** and **GitHub Actions**, with direct automated publishing to **Instagram Reels**.

---

## 🌟 How It Works

1. **Persistent Story Memory (`story_state.json`):**
   - Keeps track of all produced episodes, character relationships, and overarching drama arcs.
   - For every new run, the Gemini Story Engine reads the complete previous history to craft the next logical, dramatic episode.

2. **Strict Character Turnaround Anchors (`assets/`):**
   - **Sachin (Age 26):** Tousled wavy dark hair, signature rust-orange crew neck tee with subtle pineapple crest, black joggers, white sneakers, black sport watch.
   - **Reenu (Age 24):** Layered chestnut hair with bangs, pastel yellow & blue cloud-camo crop tee, baby-blue denim skirt with side slit, white sneakers.
   - **Amal (Age 26):** Cropped curly dark hair, trim mustache & goatee, olive-green crew neck tee, blue denim jeans, white sneakers.

3. **Multi-Character Malayalam Voice Acting:**
   - Synthesizes studio-grade Malayalam dialogue via **Gemini 3.8 Flash TTS**:
     - Narrator & Reenu: Voice `Kore`
     - Sachin: Voice `Fenrir`
     - Amal: Voice `Puck`

4. **Zero-Collision Audio Synchronization & Dynamic FFmpeg Assembly:**
   - Measures speech durations to the millisecond (`audio_duration + 0.6s lead-in + 0.9s tail-out`).
   - Strictly renders 9:16 vertical video (1080x1920) with no stretched or distorted bodies.

5. **Direct Publishing to Instagram Reels:**
   - Automatically releases the compiled video asset and calls the **Instagram Graph API** to upload, verify, and publish directly to your feed.

---

## 🚀 Running The Studio

### Manual Trigger:
1. Go to the **Actions** tab in this GitHub repository.
2. Select **Autonomous Episode Studio: Produce & Publish to Instagram**.
3. Click **Run workflow**. (Optional: check *dry_run* to preview without posting).

### Automated Schedule:
Uncomment the `schedule` block in `.github/workflows/produce_and_publish.yml` to publish episodes automatically on a recurring cron (e.g. every Sunday or daily at 18:00 IST).

---

## 🔐 Configured GitHub Secrets

- `GEMINI_API_KEY`: Google Gemini API Key
- `INSTAGRAM_ACCESS_TOKEN`: Meta Graph API Access Token
- `INSTAGRAM_ACCOUNT_ID`: Instagram Business Account ID
- `GH_PAT`: GitHub Personal Access Token for releases and pushing story updates
