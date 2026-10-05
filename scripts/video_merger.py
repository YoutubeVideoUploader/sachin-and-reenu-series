import os
import sys
import glob
import re
import json
import argparse
import subprocess
from pathlib import Path

# Fix Windows console UTF-8 output
if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr:
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def get_video_info(video_path):
    """Inspects video duration, width, height, and fps using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,duration",
        "-show_entries", "format=duration",
        "-of", "json",
        str(video_path)
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        data = json.loads(res.stdout)
        stream = data.get("streams", [{}])[0]
        fmt = data.get("format", {})
        
        width = int(stream.get("width", 1080))
        height = int(stream.get("height", 1920))
        duration = float(stream.get("duration") or fmt.get("duration") or 0.0)
        return {"width": width, "height": height, "duration": duration}
    except Exception as e:
        print(f"Warning: ffprobe failed for {video_path}: {e}")
        return {"width": 1080, "height": 1920, "duration": 4.0}

def standardize_clip(input_path, output_path, target_w=1080, target_h=1920, fps=30):
    """
    Standardizes any video to vertical 9:16 (1080x1920), 30fps, 
    cropped & scaled to fill, without letterboxing distortion.
    """
    vf_filter = (
        f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
        f"crop={target_w}:{target_h}:(iw-{target_w})/2:(ih-{target_h})/2,"
        f"fps={fps},format=yuv420p"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vf", vf_filter,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-an", # Drop shot audio so BGM remains pure & studio-grade
        str(output_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def merge_episode_shots(shots_dir, output_file, episode_num=3, title_en="", title_ml="", bgm_num=None):
    """
    Merges all shot clips from shots_dir into a master 9:16 Instagram Reel with BGM.
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

    # Sort numerically based on filename digits (e.g., shot_1, shot_2, shot_10)
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

    # Create temporary directory for standardized clips
    temp_dir = Path("temp_merger")
    temp_dir.mkdir(exist_ok=True)
    
    standardized_clips = []
    total_video_duration = 0.0

    print("\n1. Standardizing clips to vertical 9:16 (1080x1920 @ 30fps)...")
    for i, shot in enumerate(sorted_shots, start=1):
        std_name = temp_dir / f"std_shot_{i:02d}.mp4"
        print(f"   Processing shot {i}/{len(sorted_shots)}: {shot.name} -> {std_name.name}")
        standardize_clip(shot, std_name)
        info = get_video_info(std_name)
        total_video_duration += info["duration"]
        standardized_clips.append(std_name)

    print(f"✓ All clips standardized! Total runtime: {total_video_duration:.2f}s (~{int(total_video_duration//60)}m {int(total_video_duration%60)}s)")

    # Write concat manifest
    concat_manifest = temp_dir / "concat_list.txt"
    with open(concat_manifest, "w", encoding="utf-8") as f:
        for clip in standardized_clips:
            # Escape path for ffmpeg concat demuxer
            safe_path = clip.resolve().as_posix().replace("'", "'\\''")
            f.write(f"file '{safe_path}'\n")

    # Step 2: Concatenate all video streams
    print("\n2. Concatenating video sequences...")
    concatenated_raw = temp_dir / "concatenated_raw.mp4"
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_manifest),
        "-c", "copy",
        str(concatenated_raw)
    ]
    subprocess.run(cmd_concat, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    # Step 3: Select BGM from 10-track romantic music library
    if bgm_num is None:
        bgm_num = ((int(episode_num) - 1) % 10) + 1
    
    bgm_candidates = [
        Path(f"assets/music/bgm_{bgm_num}.mp3"),
        Path(f"assets/music/bgm_1.mp3")
    ]
    selected_bgm = None
    for cand in bgm_candidates:
        if cand.exists():
            selected_bgm = cand
            break
            
    if not selected_bgm:
        print("Warning: No BGM file found in assets/music! Creating silent audio track...")
        selected_bgm = temp_dir / "silence.mp3"
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
            "-t", str(total_video_duration), str(selected_bgm)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    else:
        print(f"🎵 Active BGM Track: {selected_bgm.name} (Track #{bgm_num})")

    # Step 4: Final Assembly with BGM, Audio Ducking, and Title Overlay
    print("\n3. Mastering Audio, Adding Fade-In/Out & Title Graphics...")
    
    # Audio filters: loop if BGM shorter than video, fade in at 0s (1.5s dur), fade out at end (2.5s dur)
    fade_out_start = max(0.0, total_video_duration - 2.5)
    audio_filter = (
        f"aloop=loop=-1:size=2e+09,"
        f"afade=t=in:ss=0:d=1.5,"
        f"afade=t=out:st={fade_out_start:.2f}:d=2.5,"
        f"volume=0.85"
    )

    # Video Title overlay (Cinematic banner during first 5 seconds)
    header_text = f"SACHIN & REENU • EPISODE {episode_num}"
    if title_en:
        subtitle_text = title_en.upper()
    else:
        subtitle_text = f"CHAPTER {episode_num}"

    # Drawtext filter for cinematic episode opening
    # We place a subtle semi-transparent box at the top with fade-in (0.5s) and fade-out (4.5s)
    draw_filter = (
        f"drawbox=y=160:color=black@0.45:width=iw:height=140:t=fill:enable='between(t,0.5,5.0)',"
        f"drawtext=text='{header_text}':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=180:enable='between(t,0.5,5.0)',"
        f"drawtext=text='{subtitle_text}':fontcolor=#F97316:fontsize=48:x=(w-text_w)/2:y=230:enable='between(t,0.5,5.0)'"
    )

    output_path = Path(output_file)
    cmd_master = [
        "ffmpeg", "-y",
        "-i", str(concatenated_raw),
        "-i", str(selected_bgm),
        "-vf", draw_filter,
        "-filter:a", audio_filter,
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path)
    ]
    
    # Run mastering
    try:
        subprocess.run(cmd_master, check=True)
    except subprocess.CalledProcessError:
        # If drawtext fails due to font availability on certain bare OS containers, fall back without drawtext
        print("Note: Falling back to direct video mix without drawtext overlay...")
        cmd_master_fallback = [
            "ffmpeg", "-y",
            "-i", str(concatenated_raw),
            "-i", str(selected_bgm),
            "-filter:a", audio_filter,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", "44100",
            "-shortest",
            "-movflags", "+faststart",
            str(output_path)
        ]
        subprocess.run(cmd_master_fallback, check=True)

    print(f"\n=======================================================")
    print(f"🎉 MASTER EPISODE PRODUCED SUCCESSFULLY!")
    print(f"File: {output_path.resolve()}")
    print(f"Duration: {total_video_duration:.2f}s | Resolution: 1080x1920 (9:16) | Format: MP4")
    print(f"=======================================================\n")
    return output_path

def main():
    parser = argparse.ArgumentParser(description="Sachin & Reenu Video Merger")
    parser.add_argument("--shots_dir", default="uploaded_shots", help="Directory containing shot_1.mp4, shot_2.mp4...")
    parser.add_argument("--output", default="master_episode.mp4", help="Output master video filename")
    parser.add_argument("--episode", type=int, default=None, help="Episode number")
    parser.add_argument("--title_en", default="", help="Episode English title")
    parser.add_argument("--title_ml", default="", help="Episode Malayalam title")
    parser.add_argument("--bgm", type=int, default=None, help="BGM track index (1-10)")
    args = parser.parse_args()

    # Auto-load metadata from current_episode_shots.json if present
    ep_num = args.episode
    title_en = args.title_en
    title_ml = args.title_ml
    
    if os.path.exists("current_episode_shots.json"):
        try:
            with open("current_episode_shots.json", "r", encoding="utf-8") as f:
                ep_json = json.load(f)
                if ep_num is None:
                    ep_num = ep_json.get("episode_number", 3)
                if not title_en:
                    title_en = ep_json.get("title_english", "")
                if not title_ml:
                    title_ml = ep_json.get("title_malayalam", "")
        except Exception:
            pass

    if ep_num is None:
        ep_num = 3

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
