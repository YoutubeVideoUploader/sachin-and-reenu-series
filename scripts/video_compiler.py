import os
import json
import wave
import subprocess

SCRIPT_FILE = "current_episode.json"
AUDIO_DIR = "generated_audio"
IMAGE_DIR = "generated_images"
OUTPUT_VIDEO = "master_episode.mp4"

def compile_master_video():
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        ep_data = json.load(f)
    
    scenes = ep_data.get("scenes", [])
    timeline = []
    current_time = 0.0
    
    for sc in scenes:
        idx = sc["scene_index"]
        wav_path = os.path.join(AUDIO_DIR, f"speech_{idx}.wav")
        img_path = os.path.join(IMAGE_DIR, f"scene_{idx}.png")
        
        audio_dur = 4.0
        if os.path.exists(wav_path):
            with wave.open(wav_path, "r") as w:
                audio_dur = w.getnframes() / float(w.getframerate())
        
        lead_in = 0.6
        tail_out = 0.9
        shot_dur = round(max(4.5, lead_in + audio_dur + tail_out), 2)
        diag_start = round(current_time + lead_in, 2)
        diag_end = round(diag_start + audio_dur, 2)
        
        timeline.append({
            "idx": idx,
            "img": img_path,
            "wav": wav_path,
            "shot_start": round(current_time, 2),
            "shot_dur": shot_dur,
            "diag_start_ms": int(diag_start * 1000),
            "audio_dur": round(audio_dur, 2)
        })
        current_time = round(current_time + shot_dur, 2)
    
    print(f"Total video duration: {current_time:.2f}s (~{int(current_time//60)}m {int(current_time%60)}s)")
    
    # Render individual clips
    clip_files = []
    for t in timeline:
        clip_name = f"clip_{t['idx']}.mp4"
        clip_files.append(clip_name)
        total_frames = int(t["shot_dur"] * 30)
        
        vf = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920:(iw-1080)/2:(ih-1920)/2,"
            f"zoompan=z='min(zoom+0.0006,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s=1080x1920:fps=30,"
            f"format=yuv420p"
        )
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", t["img"],
            "-vf", vf,
            "-c:v", "libx264",
            "-t", str(t["shot_dur"]),
            "-pix_fmt", "yuv420p",
            clip_name
        ]
        subprocess.run(cmd, check=True)
    
    # Concatenate clips
    concat_txt = "clips_concat.txt"
    with open(concat_txt, "w") as f:
        for c in clip_files:
            f.write(f"file '{c}'\n")
            
    video_seq = "video_sequence.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt, "-c", "copy", video_seq], check=True)
    
    # Audio Mix
    amb_path = os.path.join(AUDIO_DIR, "ambient.wav")
    bgm_path = os.path.join(AUDIO_DIR, "romance_score.wav")
    
    filter_parts = [
        "[1:a]volume=0.18[amb];",
        "[2:a]volume=0.30[bgm];"
    ]
    mix_inputs = ["[amb]", "[bgm]"]
    
    for idx, t in enumerate(timeline, 1):
        stream_idx = 2 + idx # 0 is video, 1 is amb, 2 is bgm, 3+ is speech
        d_ms = t["diag_start_ms"]
        filter_parts.append(f"[{stream_idx}:a]adelay={d_ms}|{d_ms},volume=1.0[d{idx}];")
        mix_inputs.append(f"[d{idx}]")
        
    filter_parts.append(f"{''.join(mix_inputs)}amix=inputs={len(mix_inputs)}:duration=longest:dropout_transition=2[aout]")
    filter_complex = "".join(filter_parts)
    
    cmd_master = [
        "ffmpeg", "-y",
        "-i", video_seq,
        "-i", amb_path,
        "-i", bgm_path
    ]
    for t in timeline:
        cmd_master.extend(["-i", t["wav"]])
        
    cmd_master.extend([
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        OUTPUT_VIDEO
    ])
    
    print("Compiling final master video...")
    subprocess.run(cmd_master, check=True)
    print(f"Master video created successfully: {OUTPUT_VIDEO}")

if __name__ == "__main__":
    compile_master_video()
