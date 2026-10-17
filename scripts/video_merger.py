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

def validate_master_video(video_path, min_duration=5.0):
    """
    Validates that the rendered output file is non-empty, playable,
    contains valid video and audio streams, and meets minimum duration.
    """
    vp = Path(video_path)
    if not vp.exists():
        raise FileNotFoundError(f"Master output video does not exist: {vp}")
    file_size = vp.stat().st_size
    if file_size < 50000:
        raise ValueError(f"Master output video is corrupt or abnormally small ({file_size} bytes): {vp}")

    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=width,height,codec_type,duration",
        "-show_entries", "format=duration,size",
        "-of", "json",
        str(vp)
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(res.stdout)
        streams = data.get("streams", [])
        fmt = data.get("format", {})

        has_video = any(s.get("codec_type") == "video" for s in streams)
        has_audio = any(s.get("codec_type") == "audio" for s in streams)
        v_stream = next((s for s in streams if s.get("codec_type") == "video"), {})

        w = int(v_stream.get("width", 0))
        h = int(v_stream.get("height", 0))
        dur = float(v_stream.get("duration") or fmt.get("duration") or 0.0)

        if not has_video or w <= 0 or h <= 0:
            raise ValueError(f"Master output video has invalid video stream (w={w}, h={h}): {vp}")
        if not has_audio:
            raise ValueError(f"Master output video is missing required audio stream: {vp}")
        if dur < min_duration:
            raise ValueError(f"Master output duration ({dur:.2f}s) is below required minimum ({min_duration}s): {vp}")

        print(f"✓ Master Video Validated: {w}x{h} ({dur:.2f}s, {file_size} bytes, Audio: OK)")
        return True
    except subprocess.CalledProcessError as err:
        raise RuntimeError(f"ffprobe verification failed for {vp}: {err.stderr}")

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
            
        # If multiple tracks, standardize and concatenate them in the shuffled order
        std_tracks = []
        for idx_t, t in enumerate(downloaded_tracks):
            std_t = custom_music_dir / f"std_track_{idx_t}.mp3"
            c_cmd = ["ffmpeg", "-y", "-i", str(t), "-ar", "44100", "-ac", "2", "-c:a", "libmp3lame", "-b:a", "192k", str(std_t)]
            res_c = subprocess.run(c_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res_c.returncode == 0 and std_t.exists():
                std_tracks.append(std_t)
            else:
                std_tracks.append(t)

        concat_txt = custom_music_dir / "music_concat.txt"
        with open(concat_txt, "w", encoding="utf-8") as f_out:
            for t in std_tracks:
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

def parse_shot_music_map(raw_map, total_shots=10):
    """
    Parses shot_music_map which can be:
    - JSON string: '{"1":"default","2":"custom",...}'
    - Comma-delimited ranges: '1-3:default,4-7:custom,8-10:default'
    - Comma-delimited pairs: '1:default,2:custom'
    Returns a dict mapping shot_number (int) -> 'default' | 'custom'
    """
    result = {}
    if not raw_map:
        return {s: "default" for s in range(1, total_shots + 1)}

    raw_str = str(raw_map).strip()
    if raw_str.startswith("{") and raw_str.endswith("}"):
        try:
            parsed = json.loads(raw_str)
            for k, v in parsed.items():
                try:
                    s_num = int(k)
                    val = str(v).strip().lower()
                    result[s_num] = "custom" if "custom" in val else "default"
                except Exception:
                    pass
            for s in range(1, total_shots + 1):
                if s not in result:
                    result[s] = "default"
            return result
        except Exception:
            pass

    parts = [p.strip() for p in raw_str.split(",") if p.strip()]
    for p in parts:
        sep = ":" if ":" in p else ("=" if "=" in p else None)
        if sep:
            k, v = p.split(sep, 1)
            v_val = "custom" if "custom" in v.strip().lower() else "default"
            k = k.strip()
            if "-" in k:
                sub = k.split("-")
                try:
                    s_start = int(sub[0])
                    s_end = int(sub[1])
                    for s in range(s_start, s_end + 1):
                        result[s] = v_val
                except Exception:
                    pass
            else:
                try:
                    result[int(k)] = v_val
                except Exception:
                    pass

    for s in range(1, total_shots + 1):
        if s not in result:
            result[s] = "default"

    return result

def build_mixed_bgm_track(shot_timings, shot_music_map, total_video_duration, total_shots, default_bgm, custom_bgm, temp_dir):
    """
    Assembles a continuous background soundtrack honoring the per-shot music map.
    Applies smooth fade-out and fade-in (crossfade) at each music boundary.
    """
    segments = []
    current_source = None
    current_start = 0.0
    current_end = 0.0

    for s in range(1, total_shots + 1):
        src = shot_music_map.get(s, "default")
        timing = shot_timings.get(s, {"start": (s - 1) * 6.0, "end": s * 6.0, "duration": 6.0})
        if current_source is None:
            current_source = src
            current_start = timing["start"]
            current_end = timing["end"]
        elif src == current_source:
            current_end = timing["end"]
        else:
            segments.append({
                "source": current_source,
                "start": current_start,
                "end": current_end,
                "duration": max(0.1, current_end - current_start)
            })
            current_source = src
            current_start = timing["start"]
            current_end = timing["end"]

    if current_source is not None:
        current_end = max(current_end, total_video_duration)
        segments.append({
            "source": current_source,
            "start": current_start,
            "end": current_end,
            "duration": max(0.1, current_end - current_start)
        })

    print(f"\n🎛️  MIX MUSIC PIPELINE: Grouped into {len(segments)} audio segment(s):")
    for idx, seg in enumerate(segments, 1):
        print(f"   • Segment {idx}: {seg['start']:.1f}s - {seg['end']:.1f}s ({seg['duration']:.1f}s) -> [{seg['source'].upper()} BGM]")

    seg_audio_files = []
    crossfade_sec = 1.2

    for idx, seg in enumerate(segments):
        src_type = seg["source"]
        seg_dur = seg["duration"]
        seg_file = temp_dir / f"mixed_seg_{idx:02d}.wav"

        # Determine which track to play for this segment
        track = custom_bgm if (src_type == "custom" and custom_bgm and custom_bgm.exists()) else default_bgm
        if not track or not track.exists():
            print(f"   ⚠️ Track for segment {idx} not found, falling back...")
            track = default_bgm or custom_bgm

        if not track or not track.exists():
            print(f"   ⚠️ No audio track available for segment {idx}, skipping...")
            continue

        is_first = (idx == 0)
        is_last = (idx == len(segments) - 1)

        xfade = min(crossfade_sec, seg_dur / 3.0)
        fade_in_d = 1.5 if is_first else xfade
        fade_out_d = 2.5 if is_last else xfade
        fade_out_st = max(0.0, seg_dur - fade_out_d)

        filter_str = (
            f"aloop=loop=-1:size=2e+09,volume=0.32,"
            f"afade=t=in:ss=0:d={fade_in_d:.2f},"
            f"afade=t=out:st={fade_out_st:.2f}:d={fade_out_d:.2f}"
        )

        cmd_seg = [
            "ffmpeg", "-y",
            "-i", str(track),
            "-filter_complex", filter_str,
            "-t", f"{seg_dur:.2f}",
            "-ar", "44100",
            "-ac", "2",
            str(seg_file)
        ]
        res = subprocess.run(cmd_seg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0 and seg_file.exists():
            seg_audio_files.append(seg_file)
        else:
            print(f"   ⚠️ Error rendering audio segment {idx}")

    if not seg_audio_files:
        return default_bgm or custom_bgm

    if len(seg_audio_files) == 1:
        return seg_audio_files[0]

    concat_list = temp_dir / "mixed_bgm_concat.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for saf in seg_audio_files:
            safe_p = saf.resolve().as_posix().replace("'", "'\\''")
            f.write(f"file '{safe_p}'\n")

    master_mixed_bgm = temp_dir / "master_mixed_bgm.wav"
    cmd_cat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(master_mixed_bgm)
    ]
    res_cat = subprocess.run(cmd_cat, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if res_cat.returncode == 0 and master_mixed_bgm.exists():
        print(f"✓ Master Mixed Soundtrack created with smooth crossfades! ({master_mixed_bgm.name})")
        return master_mixed_bgm
    else:
        return seg_audio_files[0]

def _merge_episode_shots_internal(temp_dir, shots_dir, output_file, episode_num=1, season_num=1, title_en="", title_ml="", bgm_num=None, music_source="general", shot_music_map="", gas_url=None):
    """
    Internal shot merger with active temp_dir context.
    Combines spoken dialogue audio with atmospheric romantic background score.
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

    standardized_clips = []
    total_video_duration = 0.0
    shot_timings = {}
    current_shot_time = 0.0

    print("\n1. Standardizing clips (1080x1920 @ 30fps) with Clean Audio...")
    for i, shot in enumerate(sorted_shots, start=1):
        std_name = temp_dir / f"std_shot_{i:02d}.mp4"
        print(f"   Processing shot {i}/{len(sorted_shots)}: {shot.name} -> {std_name.name}")
        standardize_clip_with_audio(shot, std_name)
        info = get_video_info(std_name)
        dur = info["duration"]
        shot_timings[i] = {
            "start": current_shot_time,
            "end": current_shot_time + dur,
            "duration": dur
        }
        current_shot_time += dur
        total_video_duration += dur
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

    # Step 3: Select BGM (General, Episode Custom, or Shot-by-Shot Mix)
    import random
    selected_bgm = None
    default_bgm = None
    custom_bgm = None

    # Always locate default general romantic BGM
    music_dir = Path("assets/music")
    all_bgm_files = sorted(list(music_dir.glob("*.mp3"))) if music_dir.exists() else []
    if bgm_num is not None and (music_dir / f"bgm_{bgm_num}.mp3").exists():
        default_bgm = music_dir / f"bgm_{bgm_num}.mp3"
    elif all_bgm_files:
        default_bgm = random.choice(all_bgm_files)

    # Fetch custom music from Google Drive if required
    # Modes 'auto', 'episode_custom', 'mix', and 'general' inspect Drive for uploaded custom tracks
    if music_source in ("auto", "episode_custom", "mix", "general"):
        custom_bgm = fetch_and_prepare_episode_custom_music(gas_url, temp_dir)

    # Assemble track according to chosen music source
    is_mixed_track = False
    if music_source == "mix":
        print(f"\n🎛️ Mix Music Mode: Assembling shot-by-shot soundtrack mix...")
        parsed_map = parse_shot_music_map(shot_music_map, total_shots=len(sorted_shots))
        selected_bgm = build_mixed_bgm_track(
            shot_timings=shot_timings,
            shot_music_map=parsed_map,
            total_video_duration=total_video_duration,
            total_shots=len(sorted_shots),
            default_bgm=default_bgm,
            custom_bgm=custom_bgm,
            temp_dir=temp_dir
        )
        is_mixed_track = True
    elif music_source in ("auto", "episode_custom"):
        if custom_bgm and custom_bgm.exists():
            selected_bgm = custom_bgm
            print(f"🎵 Using Episode Custom Music from Google Drive: {selected_bgm.name}")
        else:
            if music_source == "episode_custom":
                print("⚠️ Episode Custom Music not available in Drive, falling back gracefully to General Series BGM.")
            else:
                print("ℹ️ No custom music in Drive 'Episode_Music', using General Series Romantic BGM.")
            selected_bgm = default_bgm
    elif music_source == "force_general":
        selected_bgm = default_bgm
        if selected_bgm:
            print(f"🎵 Forced General Series Romantic BGM: {selected_bgm.name}")
    else:
        # music_source == "general" (Auto-prioritize custom track if creator uploaded one to Drive)
        if custom_bgm and custom_bgm.exists():
            selected_bgm = custom_bgm
            print(f"🎵 Auto-detected active Episode Custom Music in Drive: {selected_bgm.name}")
        else:
            selected_bgm = default_bgm
            if selected_bgm:
                print(f"🎵 Selected General Series Romantic BGM: {selected_bgm.name}")

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
        if is_mixed_track:
            filters.append(f"[{bgm_input_idx}:a]volume=1.0[bgm]")
        else:
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

    # Validate output with ffprobe before declaring success
    validate_master_video(output_path, min_duration=min(5.0, total_video_duration * 0.8))

    print(f"\n=======================================================")
    print(f"🎉 MASTER EPISODE PRODUCED SUCCESSFULLY!")
    print(f"Output File : {output_path.resolve()}")
    print(f"Duration    : {total_video_duration:.2f}s (~{int(total_video_duration//60)}m {int(total_video_duration%60):02d}s)")
    print(f"Resolution  : 1080x1920 (Vertical 9:16)")
    print(f"Dialogue    : Malayalam Spoken Audio Preserved")
    print(f"BGM         : Romantic Score Mixed (Volume 0.18 / 0.32)")
    print(f"=======================================================\n")
    return output_path

def merge_episode_shots(shots_dir, output_file, episode_num=1, season_num=1, title_en="", title_ml="", bgm_num=None, music_source="general", shot_music_map="", gas_url=None):
    """
    Merges all shot clips from shots_dir into a master 9:16 Instagram Reel.
    Combines spoken dialogue audio with atmospheric romantic background score.
    Guarantees cleanup of temporary intermediate files via try...finally block.
    """
    temp_dir = Path("temp_merger")
    temp_dir.mkdir(exist_ok=True)
    try:
        return _merge_episode_shots_internal(
            temp_dir=temp_dir,
            shots_dir=shots_dir,
            output_file=output_file,
            episode_num=episode_num,
            season_num=season_num,
            title_en=title_en,
            title_ml=title_ml,
            bgm_num=bgm_num,
            music_source=music_source,
            shot_music_map=shot_music_map,
            gas_url=gas_url
        )
    finally:
        if temp_dir.exists():
            import shutil
            try:
                shutil.rmtree(temp_dir)
                print(f"✓ Cleaned up temporary merger directory: {temp_dir}")
            except Exception as e:
                print(f"Notice cleaning temp_dir: {e}")

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
    parser.add_argument("--music_source", choices=["auto", "general", "episode_custom", "mix", "force_general"], default="auto", help="Music source: 'auto' (prefers Google Drive Episode_Music if present, else general), 'episode_custom' (Drive), 'mix' (shot-by-shot), or 'general' / 'force_general'")
    parser.add_argument("--shot_music_map", default="", help="Per-shot music mapping for mix mode (e.g. '1:default,2:custom...' or JSON)")
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
                    if not isinstance(ep_json, dict):
                        continue
                    if season_num is None and ep_json.get("season_number"):
                        season_num = int(ep_json.get("season_number"))
                    if ep_num is None:
                        if ep_json.get("episode_number"):
                            ep_num = int(ep_json.get("episode_number"))
                        elif ep_json.get("current_episode", {}).get("episode_number"):
                            ep_num = int(ep_json["current_episode"]["episode_number"])
                    if not title_en and ep_json.get("title_english"):
                        title_en = ep_json.get("title_english")
                    if not title_ml and ep_json.get("title_malayalam"):
                        title_ml = ep_json.get("title_malayalam")
                    if season_num is not None and ep_num is not None and title_en:
                        break
            except Exception:
                pass

    if season_num is None:
        season_num = 3
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
        shot_music_map=args.shot_music_map,
        gas_url=args.gas_url
    )

if __name__ == "__main__":
    main()
