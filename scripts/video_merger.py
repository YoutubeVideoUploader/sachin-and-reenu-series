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

def merge_episode_shots(shots_dir, output_file, episode_num=1, title_en="", title_ml="", bgm_num=None):
    """
    Merges all shot clips from shots_dir into a master 9:16 Instagram Reel.
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
    print(f"🎬 SACHIN & REENU STUDIO: MERGING EPISODE {episode_num}")
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

    print(f"✓ All {len(standardized_clips)} clips standardized! Total runtime: {total_video_duration:.2f}s (~{int(total_video_duration//60)}m {int(total_video_duration%60):02d}s)")

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

    # Step 3: Select BGM from 10-track romantic music library
    if bgm_num is None:
        bgm_num = ((int(episode_num) - 1) % 10) + 1
    
    bgm_candidates = [
        Path("assets/music/bgm_main_theme.mp3"),
        Path(f"assets/music/bgm_{bgm_num}.mp3"),
        Path("assets/music/bgm_1.mp3")
    ]
    selected_bgm = None
    for cand in bgm_candidates:
        if cand.exists():
            selected_bgm = cand
            break
            
    if not selected_bgm:
        print("Note: No external BGM file found in assets/music. Using clean dialogue audio only.")
    else:
        print(f"🎵 Selected Romantic BGM: {selected_bgm.name} (Track #{bgm_num})")

    # Step 4: Final Mix — Spoken Dialogue (Loud & Clear) + Ambient BGM Underlay (Vol 0.32 boosted) + Cinematic Title
    print("\n3. Mastering Audio Mix (Dialogue + Romantic BGM) & Title Overlay...")
    
    output_path = Path(output_file)
    
    # Title Overlay Banner during first 5 seconds
    header_text = f"SACHIN & REENU • EPISODE {episode_num}"
    subtitle_text = title_en.upper() if title_en else f"EPISODE {episode_num}"
    
    draw_filter = (
        f"drawbox=y=160:color=black@0.45:width=iw:height=140:t=fill:enable='between(t,0.5,5.0)',"
        f"drawtext=text='{header_text}':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=180:enable='between(t,0.5,5.0)',"
        f"drawtext=text='{subtitle_text}':fontcolor=#F97316:fontsize=48:x=(w-text_w)/2:y=230:enable='between(t,0.5,5.0)'"
    )

    fade_out_start = max(0.0, total_video_duration - 2.5)

    if selected_bgm and selected_bgm.exists():
        # Audio filter graph:
        # [0:a] Dialogue audio kept at volume 1.1 (crystal clear speech)
        # [1:a] BGM looped, volume boosted to 0.32 with gentle fade in/out
        # amix merges both audio streams
        complex_filter = (
            f"[1:a]aloop=loop=-1:size=2e+09,volume=0.32,"
            f"afade=t=in:ss=0:d=1.5,afade=t=out:st={fade_out_start:.2f}:d=2.5[bgm];"
            f"[0:a]volume=1.1[voice];"
            f"[voice][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )

        cmd_master = [
            "ffmpeg", "-y",
            "-i", str(concatenated_raw),
            "-i", str(selected_bgm),
            "-vf", draw_filter,
            "-filter_complex", complex_filter,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "libx264", "-preset", "slow", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
            "-shortest",
            "-movflags", "+faststart",
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd_master, check=True)
        except subprocess.CalledProcessError:
            print("Note: Fallback mix without drawtext overlay...")
            cmd_master_fallback = [
                "ffmpeg", "-y",
                "-i", str(concatenated_raw),
                "-i", str(selected_bgm),
                "-filter_complex", complex_filter,
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
                "-shortest",
                "-movflags", "+faststart",
                str(output_path)
            ]
            subprocess.run(cmd_master_fallback, check=True)
    else:
        # No BGM track: keep original dialogue audio
        cmd_master = [
            "ffmpeg", "-y",
            "-i", str(concatenated_raw),
            "-vf", draw_filter,
            "-c:v", "libx264", "-preset", "slow", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
            "-movflags", "+faststart",
            str(output_path)
        ]
        try:
            subprocess.run(cmd_master, check=True)
        except subprocess.CalledProcessError:
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
    parser.add_argument("--shots_dir", default="clean_shots", help="Directory containing de-watermarked shots")
    parser.add_argument("--output", default="master_episode.mp4", help="Output master video filename")
    parser.add_argument("--episode", type=int, default=None, help="Episode number")
    parser.add_argument("--title_en", default="", help="Episode English title")
    parser.add_argument("--title_ml", default="", help="Episode Malayalam title")
    parser.add_argument("--bgm", type=int, default=None, help="BGM track index (1-10)")
    args = parser.parse_args()

    ep_num = args.episode
    title_en = args.title_en
    title_ml = args.title_ml
    
    if os.path.exists("current_episode_shots.json"):
        try:
            with open("current_episode_shots.json", "r", encoding="utf-8") as f:
                ep_json = json.load(f)
                if ep_num is None:
                    ep_num = ep_json.get("episode_number", 1)
                if not title_en:
                    title_en = ep_json.get("title_english", "")
                if not title_ml:
                    title_ml = ep_json.get("title_malayalam", "")
        except Exception:
            pass

    if ep_num is None:
        ep_num = 1

    merge_episode_shots(
        shots_dir=args.shots_dir,
        output_file=args.output,
        episode_num=ep_num,
        title_en=title_en,
        title_ml=title_ml,
        bgm_num=args.bgm
    )

if __name__ == "__main__":
    main()
