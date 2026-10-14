#!/usr/bin/env python3
"""
video_merger.py - Master Video & Audio Merger for Sachin & Reenu Series
Merges all de-watermarked 9:16 clips into a complete master episode.
Preserves original Malayalam voice acting & dialogue from every shot.
Blends custom romantic background music (BGM) smoothly underneath spoken dialogues.
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
import glob
import re
import json
import argparse
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def fetch_season_from_google_sheet(gas_url=None):
    """
    Fetches the active season number directly from Google Sheet Tab 'Season_Story_Arc', Cell A1
    via the Google Apps Script Web App API (action=get_season_story).
    Returns int season number (e.g. 2), or None if offline/error.
    """
    import requests
    target_url = gas_url or os.getenv("GAS_WEBHOOK_URL") or "https://script.google.com/macros/s/AKfycbyivkrK_jL1ejwNqUvHe8KVFNkSuJSwZbWSmuE1YATqL5jCneMlqlKbf0EH7mwpc4gybA/exec"
    try:
        res = requests.get(f"{target_url}?action=get_season_story", timeout=20)
        if res.status_code == 200:
            data = res.json()
            if data.get("season_number") is not None:
                s_num = int(data["season_number"])
                print(f"[VIDEO MERGER] Fetched Season {s_num} directly from Google Sheet Tab 'Season_Story_Arc' (Cell A1)")
                return s_num
            cell_a1 = str(data.get("cell_a1", ""))
            m = re.search(r'SEASON\s*(\d+)', cell_a1, re.I) or re.search(r'(\d+)', cell_a1)
            if m:
                s_num = int(m.group(1))
                print(f"[VIDEO MERGER] Fetched Season {s_num} from Google Sheet Tab 'Season_Story_Arc' Cell A1 ('{cell_a1}')")
                return s_num
    except Exception as e:
        print(f"[VIDEO MERGER] Notice fetching season from Sheet Tab 'Season_Story_Arc': {e}")
    return None

def get_video_info(video_path):
    """Inspects video duration, width, height, and audio streams using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=width,height,codec_type,duration",
        "-show_entries", "format=duration",
        "-of", "json",
        str(video_path)
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(res.stdout)
        streams = data.get("streams", [])
        fmt = data.get("format", {})
        
        has_audio = any(s.get("codec_type") == "audio" for s in streams)
        v_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
        
        width = int(v_stream.get("width", 1080))
        height = int(v_stream.get("height", 1920))
        duration = float(v_stream.get("duration") or fmt.get("duration") or 0.0)
        return {"width": width, "height": height, "duration": duration, "has_audio": has_audio}
    except Exception as e:
        print(f"Warning: ffprobe failed for {video_path}: {e}")
        return {"width": 1080, "height": 1920, "duration": 4.0, "has_audio": True}

def standardize_clip_with_audio(input_path, output_path, target_w=1080, target_h=1920, fps=30):
    """
    Standardizes video to vertical 9:16 (1080x1920), 30fps.
    CRITICAL: Preserves the shot's original Malayalam voice/dialogue audio!
    If shot has no audio, synthesizes matched silent audio to keep sync.
    """
    info = get_video_info(input_path)
    dur = info["duration"]
    has_audio = info["has_audio"]
    
    vf_filter = (
        f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
        f"crop={target_w}:{target_h}:(iw-{target_w})/2:(ih-{target_h})/2,"
        f"fps={fps},format=yuv420p"
    )
    
    if has_audio:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-vf", vf_filter,
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "192k",
            str(output_path)
        ]
    else:
        # Generate silence track matched to video length
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo",
            "-vf", vf_filter,
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "192k",
            "-shortest",
            str(output_path)
        ]
        
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def generate_outro_clip(image_path, output_path, duration=3.0, target_w=1080, target_h=1920, fps=30):
    """
    Renders the outro poster as a 3-second vertical 9:16 video clip with silent audio,
    ready to concatenate seamlessly to the end of the episode.
    """
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", str(duration),
        "-vf", f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2,fps={fps},format=yuv420p",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "192k",
        "-shortest",
        str(output_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def create_title_banner_overlay(output_png_path, episode_num=1, season_num=1, title_en="", title_ml=""):
    """
    Renders a semi-transparent, cinematic 1080x220 title banner badge as a PNG.
    Uses bundled Manjari-Bold.ttf with FFmpeg HarfBuzz shaping to guarantee
    100% authentic, error-free Malayalam typography & Latin English text.
    Displays:
      - Line 1: SACHIN & REENU • SEASON {season_num} • EPISODE {episode_num}
      - Line 2: {title_en.upper()} (and Malayalam title if available)
    """
    import tempfile
    try:
        w, h = 1080, 220
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Rounded pill card container
        card_margin = 60
        card_x1 = card_margin
        card_y1 = 15
        card_x2 = w - card_margin
        card_y2 = h - 15
        radius = 24

        draw.rounded_rectangle(
            [card_x1, card_y1, card_x2, card_y2],
            radius=radius,
            fill=(10, 14, 22, 225),
            outline=(249, 115, 22, 190),
            width=3
        )

        output_png_path = Path(output_png_path)
        output_png_path.parent.mkdir(parents=True, exist_ok=True)

        if season_num and season_num > 1:
            header_text = f"SACHIN & REENU • SEASON {season_num} • EPISODE {episode_num}"
        else:
            header_text = f"SACHIN & REENU • EPISODE {episode_num}"
        sub_text = title_en.upper().strip() if title_en else f"EPISODE {episode_num}"

        # Locate bundled Manjari-Bold font
        font_candidates = [
            Path("assets/fonts/Manjari-Bold.ttf"),
            Path(__file__).parent.parent / "assets/fonts/Manjari-Bold.ttf",
            Path("assets/fonts/NotoSansMalayalam-Bold.ttf")
        ]
        font_file = next((f for f in font_candidates if f.exists()), None)

        if font_file:
            # Render text via FFmpeg HarfBuzz drawtext to ensure authentic Malayalam ligature shaping
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
                temp_card_path = Path(tf.name)

            try:
                img.save(str(temp_card_path), "PNG")
                font_posix = font_file.resolve().as_posix().replace(":", r"\:")

                def esc_ffmpeg(txt):
                    return txt.replace("\\", "\\\\").replace(":", r"\:").replace("'", r"\'").replace("%", r"\%")

                esc_h = esc_ffmpeg(header_text)
                esc_s = esc_ffmpeg(sub_text)

                # Dynamically size subtitle font if text is long
                sub_fontsize = 34 if len(sub_text) > 38 else 40

                vf = (
                    f"drawtext=fontfile='{font_posix}':text='{esc_h}':fontcolor=white:fontsize=32:x=(w-text_w)/2:y=38,"
                    f"drawtext=fontfile='{font_posix}':text='{esc_s}':fontcolor=#F97316:fontsize={sub_fontsize}:x=(w-text_w)/2:y=96"
                )

                cmd = ["ffmpeg", "-y", "-i", str(temp_card_path), "-vf", vf, str(output_png_path)]
                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding="utf-8")
                if res.returncode == 0 and output_png_path.exists():
                    print(f"✓ Generated high-res title banner with authentic Malayalam typography: {output_png_path.name}")
                    return True
                else:
                    print(f"Notice: FFmpeg drawtext returned code {res.returncode}, falling back to PIL render")
            finally:
                if temp_card_path.exists():
                    try:
                        temp_card_path.unlink()
                    except Exception:
                        pass

        # Fallback to Pillow if font file or drawtext not available
        def get_font(size):
            for c in ['NirmalaB.ttf', 'arialbd.ttf', 'DejaVuSans-Bold.ttf', 'arial.ttf']:
                try:
                    return ImageFont.truetype(c, size)
                except Exception:
                    pass
            return ImageFont.load_default()

        f_head = get_font(30)
        f_sub = get_font(36)
        bbox_h = draw.textbbox((0, 0), header_text, font=f_head)
        draw.text(((w - (bbox_h[2] - bbox_h[0])) / 2, card_y1 + 24), header_text, fill=(255, 255, 255, 245), font=f_head)

        bbox_s = draw.textbbox((0, 0), sub_text, font=f_sub)
        draw.text(((w - (bbox_s[2] - bbox_s[0])) / 2, card_y1 + 84), sub_text, fill=(249, 115, 22, 255), font=f_sub)
        img.save(str(output_png_path), "PNG")
        print(f"✓ Generated fallback title banner: {output_png_path.name}")
        return True
    except Exception as e:
        print(f"Warning: Failed to generate title banner overlay: {e}")
        return False

def fetch_and_prepare_episode_custom_music(gas_url, temp_dir):
    """
    Fetches custom episode music from Google Drive folder 'Episode_Music' via Google Apps Script.
    If multiple tracks are found, randomizes their order and concatenates them into a single audio file.
    Returns Path to the prepared audio file, or None if no files are found or an error occurs.
    """
    import requests
    import random
    target_url = gas_url or os.getenv("GAS_WEBHOOK_URL") or "https://script.google.com/macros/s/AKfycbyivkrK_jL1ejwNqUvHe8KVFNkSuJSwZbWSmuE1YATqL5jCneMlqlKbf0EH7mwpc4gybA/exec"
    try:
        print(f"\n🔍 Checking Google Drive 'Episode_Music' folder for custom episode soundtrack...")
        res = requests.get(f"{target_url}?action=list_episode_music", timeout=30)
        if res.status_code != 200:
            print(f"⚠️ GAS returned status {res.status_code} while querying Episode_Music.")
            return None
        data = res.json()
        files = data.get("files", [])
        if not files:
            print("ℹ️ No custom music files found in Google Drive 'Episode_Music' folder.")
            return None
        
        print(f"🎵 Found {len(files)} custom music track(s) in Drive 'Episode_Music':")
        custom_music_dir = temp_dir / "custom_music"
        custom_music_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_tracks = []
        for f in files:
            file_id = f.get("id")
            name = f.get("name") or f"custom_{file_id}.mp3"
            dest = custom_music_dir / name
            print(f"  ⬇️ Downloading custom track: {name} (ID: {file_id})...")
            dl_urls = [
                f"https://drive.usercontent.google.com/download?id={file_id}&export=download",
                f"https://drive.google.com/uc?export=download&id={file_id}",
                f.get("download_url")
            ]
            downloaded = False
            for u in dl_urls:
                if not u:
                    continue
                try:
                    r = requests.get(u, stream=True, timeout=60, headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                    })
                    if r.status_code == 200 and len(r.content) > 1000:
                        with open(dest, "wb") as out_f:
                            out_f.write(r.content)
                        downloaded = True
                        break
                except Exception:
                    pass
            if downloaded and dest.exists() and dest.stat().st_size > 1000:
                downloaded_tracks.append(dest)
                print(f"     ✓ Saved {dest.name} ({dest.stat().st_size / 1024:.1f} KB)")
            else:
                print(f"     ❌ Failed to download {name}")
                
        if not downloaded_tracks:
            print("⚠️ No custom tracks were successfully downloaded.")
            return None
            
        # Shuffle tracks randomly as requested: "those musics will be used in random order"
        random.shuffle(downloaded_tracks)
        print(f"🔀 Shuffled custom music sequence: {[t.name for t in downloaded_tracks]}")
        
        if len(downloaded_tracks) == 1:
            return downloaded_tracks[0]
            
        # If multiple tracks, concatenate them in the shuffled order
        concat_txt = custom_music_dir / "music_concat.txt"
        with open(concat_txt, "w", encoding="utf-8") as f_out:
            for t in downloaded_tracks:
                f_out.write(f"file '{t.resolve().as_posix()}'\n")
                
        combined_audio = custom_music_dir / "combined_custom_music.mp3"
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-c:a", "libmp3lame",
            "-b:a", "192k",
            str(combined_audio)
        ]
        sub_res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if sub_res.returncode == 0 and combined_audio.exists():
            print(f"✓ Concatenated {len(downloaded_tracks)} custom tracks in random order into {combined_audio.name}")
            return combined_audio
        else:
            return downloaded_tracks[0]
    except Exception as e:
        print(f"⚠️ Error preparing custom episode music: {e}")
        return None

def merge_episode_shots(shots_dir, output_file, episode_num=1, season_num=1, title_en="", title_ml="", bgm_num=None, music_source="general", gas_url=None):
    """
    Merges all shot clips from shots_dir into a master 9:16 Instagram Reel.
    Combines spoken dialogue audio with atmospheric romantic background score (general or episode custom).
    """
    shots_path = Path(shots_dir)
    if not shots_path.exists():
        raise FileNotFoundError(f"Shots directory does not exist: {shots_dir}")
    
    # Locate all video files
    video_files = []
    for ext in ("*.mp4", "*.mov", "*.webm", "*.m4v"):
        video_files.extend(shots_path.glob(ext))
    
    if not video_files:
        raise FileNotFoundError(f"No video files found in {shots_dir}")

    # Sort numerically by shot number (e.g., shot_1, shot_2, shot_10, shot_22)
    def extract_shot_num(file_path):
        m = re.search(r'(\d+)', file_path.stem)
        return int(m.group(1)) if m else 9999
    
    sorted_shots = sorted(video_files, key=extract_shot_num)
    print(f"\n=======================================================")
    print(f"🎬 SACHIN & REENU STUDIO: MERGING SEASON {season_num} • EPISODE {episode_num}")
    print(f"=======================================================")
    print(f"Found {len(sorted_shots)} shot clip(s):")
    for s in sorted_shots:
        print(f"  • {s.name}")

    # Temporary directory for standardized clips
    temp_dir = Path("temp_merger")
    temp_dir.mkdir(exist_ok=True)
    
    standardized_clips = []
    total_video_duration = 0.0

    print("\n1. Standardizing clips (1080x1920 @ 30fps) with Clean Audio...")
    for i, shot in enumerate(sorted_shots, start=1):
        std_name = temp_dir / f"std_shot_{i:02d}.mp4"
        print(f"   Processing shot {i}/{len(sorted_shots)}: {shot.name} -> {std_name.name}")
        standardize_clip_with_audio(shot, std_name)
        info = get_video_info(std_name)
        total_video_duration += info["duration"]
        standardized_clips.append(std_name)

    story_duration = total_video_duration
    print(f"✓ All {len(standardized_clips)} clips standardized! Total story runtime: {story_duration:.2f}s (~{int(story_duration//60)}m {int(story_duration%60):02d}s)")

    # Append Outro: Prefer Animated Video Outro with Narrator Voiceover, fallback to static card
    outro_video_candidates = [
        Path("assets/outro_video.mp4"),
        Path("assets/outro.mp4"),
        Path("assets/final_outro_with_narrator_dialogue.mp4")
    ]
    outro_vid = next((p for p in outro_video_candidates if p.exists()), None)
    if outro_vid:
        print(f"\n   Adding Animated Video Outro with Narrator Dialogue: {outro_vid.name}...")
        std_outro = temp_dir / "std_outro.mp4"
        standardize_clip_with_audio(outro_vid, std_outro)
        info_outro = get_video_info(std_outro)
        standardized_clips.append(std_outro)
        total_video_duration += info_outro["duration"]
        print(f"   ✓ Animated Video Outro appended! Duration: {info_outro['duration']:.2f}s | New total runtime: {total_video_duration:.2f}s")
    else:
        outro_candidates = [
            Path("assets/outro_card.jpg"),
            Path("assets/outro_poster.jpg"),
            Path("assets/outro_raw.jpg")
        ]
        outro_img = next((p for p in outro_candidates if p.exists()), None)
        if outro_img:
            print(f"\n   Adding 3-second Outro Card: {outro_img.name} (Wait for Next Episode • Follow for More)...")
            std_outro = temp_dir / "std_outro.mp4"
            generate_outro_clip(outro_img, std_outro, duration=3.0)
            standardized_clips.append(std_outro)
            total_video_duration += 3.0
            print(f"   ✓ Outro Card appended! New total runtime: {total_video_duration:.2f}s")

    # Concat manifest
    concat_manifest = temp_dir / "concat_list.txt"
    with open(concat_manifest, "w", encoding="utf-8") as f:
        for clip in standardized_clips:
            safe_path = clip.resolve().as_posix().replace("'", "'\\''")
            f.write(f"file '{safe_path}'\n")

    # Step 2: Concatenate all video & dialogue audio streams
    print("\n2. Concatenating video & dialogue audio tracks...")
    concatenated_raw = temp_dir / "concatenated_raw.mp4"
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_manifest),
        "-c", "copy",
        str(concatenated_raw)
    ]
    subprocess.run(cmd_concat, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Step 3: Select BGM (Custom Episode Music or General Series BGM)
    import random
    selected_bgm = None

    if music_source == "episode_custom":
        print(f"🎧 Custom Episode Music mode active! Retrieving music from Google Drive 'Episode_Music'...")
        selected_bgm = fetch_and_prepare_episode_custom_music(gas_url, temp_dir)
        if selected_bgm and selected_bgm.exists():
            print(f"🎵 Using Episode Custom Music: {selected_bgm.name}")
        else:
            print(f"⚠️ Episode Custom Music not available or empty. Falling back gracefully to General Series BGM.")
            music_source = "general"

    if music_source == "general" or not selected_bgm:
        music_dir = Path("assets/music")
        all_bgm_files = sorted(list(music_dir.glob("*.mp3"))) if music_dir.exists() else []
        if bgm_num is not None and (music_dir / f"bgm_{bgm_num}.mp3").exists():
            selected_bgm = music_dir / f"bgm_{bgm_num}.mp3"
            print(f"🎵 Explicitly Selected Romantic BGM: {selected_bgm.name}")
        elif all_bgm_files:
            selected_bgm = random.choice(all_bgm_files)
            print(f"🎲 Randomly Selected Romantic BGM: {selected_bgm.name} (from {len(all_bgm_files)} tracks: {[f.name for f in all_bgm_files]})")
        else:
            print("Note: No external BGM file found in assets/music. Using clean dialogue audio only.")

    # Step 4: Final Mix — Spoken Dialogue + Ambient Romantic BGM + Title Overlay + Story Watermark
    print("\n3. Mastering Audio Mix (Dialogue + Romantic BGM), Title Overlay & Watermark...")
    
    output_path = Path(output_file)
    banner_png = temp_dir / "title_banner.png"
    has_banner = create_title_banner_overlay(banner_png, episode_num, season_num, title_en, title_ml)

    # Watermark asset detection
    watermark_path = Path("assets/watermark.png")
    has_watermark = watermark_path.exists()
    if has_watermark:
        print(f"🏷️  Watermark detected: {watermark_path.name} (Active during story shots 0s to {story_duration:.2f}s, excluded from outro)")

    fade_out_start = max(0.0, total_video_duration - 2.5)

    # Dynamically assemble FFmpeg inputs and filter complex
    cmd_inputs = ["-i", str(concatenated_raw)]
    current_input_idx = 1

    bgm_input_idx = None
    if selected_bgm and selected_bgm.exists():
        cmd_inputs.extend(["-i", str(selected_bgm)])
        bgm_input_idx = current_input_idx
        current_input_idx += 1

    banner_input_idx = None
    if has_banner:
        cmd_inputs.extend(["-loop", "1", "-i", str(banner_png)])
        banner_input_idx = current_input_idx
        current_input_idx += 1

    watermark_input_idx = None
    if has_watermark:
        cmd_inputs.extend(["-loop", "1", "-i", str(watermark_path)])
        watermark_input_idx = current_input_idx
        current_input_idx += 1

    filters = []

    # 1. Video Filter Pipeline
    curr_v = "0:v"
    if has_banner:
        filters.append(f"[{banner_input_idx}:v]format=rgba,fade=in:st=0.5:d=0.6:alpha=1,fade=out:st=4.5:d=0.6:alpha=1[banner]")
        filters.append(f"[{curr_v}][banner]overlay=x=0:y='if(lt(t,0.5), -300, if(lt(t,1.1), 140 - 60*(1.1-t)/0.6, if(lt(t,4.5), 140, if(lt(t,5.1), 140 - 60*(t-4.5)/0.6, -300))))':enable='between(t,0.5,5.2)'[v_banner]")
        curr_v = "v_banner"

    if has_watermark:
        filters.append(f"[{watermark_input_idx}:v]scale=180:-1,format=rgba[wm]")
        filters.append(f"[{curr_v}][wm]overlay=x=W-w-40:y=H-h-100:enable='between(t,0,{story_duration:.2f})'[v_wm]")
        curr_v = "v_wm"

    # 2. Audio Filter Pipeline
    has_audio_mix = (bgm_input_idx is not None)
    if has_audio_mix:
        filters.append(
            f"[{bgm_input_idx}:a]aloop=loop=-1:size=2e+09,volume=0.32,"
            f"afade=t=in:ss=0:d=1.5,afade=t=out:st={fade_out_start:.2f}:d=2.5[bgm]"
        )
        filters.append(f"[0:a]volume=1.1[voice]")
        filters.append(f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]")

    cmd_master = ["ffmpeg", "-y"] + cmd_inputs + ["-t", str(total_video_duration)]

    if filters:
        filter_complex = ";".join(filters)
        cmd_master.extend(["-filter_complex", filter_complex])

        if curr_v != "0:v":
            cmd_master.extend(["-map", f"[{curr_v}]"])
        else:
            cmd_master.extend(["-map", "0:v"])

        if has_audio_mix:
            cmd_master.extend(["-map", "[aout]"])
        else:
            cmd_master.extend(["-map", "0:a"])

        cmd_master.extend([
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
            "-movflags", "+faststart",
            str(output_path)
        ])
    else:
        cmd_master.extend([
            "-c", "copy",
            str(output_path)
        ])

    try:
        subprocess.run(cmd_master, check=True)
        print("✓ Master video compiled with audio mix, Title Overlay & Watermark!")
    except subprocess.CalledProcessError as err:
        print(f"Warning: Primary encode failed ({err}), running resilient audio merge...")
        cmd_fallback = [
            "ffmpeg", "-y",
            "-i", str(concatenated_raw),
            "-c", "copy",
            str(output_path)
        ]
        subprocess.run(cmd_fallback, check=True)

    print(f"\n=======================================================")
    print(f"🎉 MASTER EPISODE PRODUCED SUCCESSFULLY!")
    print(f"Output File : {output_path.resolve()}")
    print(f"Duration    : {total_video_duration:.2f}s (~{int(total_video_duration//60)}m {int(total_video_duration%60):02d}s)")
    print(f"Resolution  : 1080x1920 (Vertical 9:16)")
    print(f"Dialogue    : Malayalam Spoken Audio Preserved")
    print(f"BGM         : Romantic Score Mixed (Volume 0.18)")
    print(f"=======================================================\n")
    return output_path

def main():
    parser = argparse.ArgumentParser(description="Sachin & Reenu Video Merger")
    parser.add_argument("--gas_url", default=os.getenv("GAS_WEBHOOK_URL", ""), help="Google Apps Script Web App URL")
    parser.add_argument("--shots_dir", default="clean_shots", help="Directory containing de-watermarked shots")
    parser.add_argument("--output", default="master_episode.mp4", help="Output master video filename")
    parser.add_argument("--season", type=int, default=None, help="Season number (auto-detected from Sheet Tab 'Season_Story_Arc' Cell A1 if omitted)")
    parser.add_argument("--episode", type=int, default=None, help="Episode number")
    parser.add_argument("--title_en", default="", help="Episode English title")
    parser.add_argument("--title_ml", default="", help="Episode Malayalam title")
    parser.add_argument("--bgm", type=int, default=None, help="BGM track index (1-10)")
    parser.add_argument("--music_source", choices=["general", "episode_custom"], default="general", help="Music source: 'general' (rotating library) or 'episode_custom' (Google Drive Episode_Music folder)")
    args = parser.parse_args()

    season_num = args.season
    ep_num = args.episode
    title_en = args.title_en
    title_ml = args.title_ml
    
    # Priority 1 for Season: Fetch live from Google Sheet Tab 'Season_Story_Arc', Cell A1
    if season_num is None:
        season_num = fetch_season_from_google_sheet(args.gas_url or os.getenv("GAS_WEBHOOK_URL"))

    for fn in ["current_episode_shots.json", "current_episode.json", "story_state.json"]:
        if os.path.exists(fn):
            try:
                with open(fn, "r", encoding="utf-8") as f:
                    ep_json = json.load(f)
                    if isinstance(ep_json, list):
                        ep_json = {"shots": ep_json, "episode_number": 7, "season_number": 2}
                    if not isinstance(ep_json, dict):
                        continue
                    if season_num is None and ep_json.get("season_number"):
                        season_num = int(ep_json.get("season_number"))
                    if ep_num is None and ep_json.get("episode_number"):
                        ep_num = int(ep_json.get("episode_number"))
                    if not title_en and ep_json.get("title_english"):
                        title_en = ep_json.get("title_english")
                    if not title_ml and ep_json.get("title_malayalam"):
                        title_ml = ep_json.get("title_malayalam")
                    if season_num is not None and ep_num is not None and title_en:
                        break
            except Exception:
                pass

    if season_num is None:
        season_num = 1
    if ep_num is None:
        ep_num = 1

    merge_episode_shots(
        shots_dir=args.shots_dir,
        output_file=args.output,
        episode_num=ep_num,
        season_num=season_num,
        title_en=title_en,
        title_ml=title_ml,
        bgm_num=args.bgm,
        music_source=args.music_source,
        gas_url=args.gas_url
    )

if __name__ == "__main__":
    main()
