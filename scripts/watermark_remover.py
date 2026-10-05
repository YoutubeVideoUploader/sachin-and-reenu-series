#!/usr/bin/env python3
"""
watermark_remover.py - Seamless Gemini Watermark Remover
Removes the 4-pointed Gemini sparkle watermark from Google Flow / Imagen video clips
without leaving any sign, blur, or smudge.
Supports processing single files or entire batch folders.
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import argparse
import subprocess
import cv2
import numpy as np
from pathlib import Path

def generate_star_mask(roi_w, roi_h, cx, cy, rx, ry):
    """
    Generates a mathematically precise concave 4-pointed star mask.
    Astroid equation: ( |x-cx|/rx )^(2/3) + ( |y-cy|/ry )^(2/3) <= 1
    """
    y_coords, x_coords = np.ogrid[:roi_h, :roi_w]
    dx = np.abs(x_coords - cx) / float(rx)
    dy = np.abs(y_coords - cy) / float(ry)
    astroid = (dx ** (2.0 / 3.0) + dy ** (2.0 / 3.0))
    mask = (astroid <= 1.05).astype(np.uint8) * 255
    
    # Slight dilation (1-2 px) to guarantee full anti-aliasing edge coverage
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    dilated = cv2.dilate(mask, kernel, iterations=1)
    return dilated

def remove_watermark_from_video(input_path, output_path):
    """
    Removes the Gemini sparkle watermark from input_path and writes clean video to output_path.
    Preserves exact audio, frame rate, duration, and video resolution.
    """
    input_str = str(input_path)
    output_str = str(output_path)
    
    if not os.path.exists(input_str):
        raise FileNotFoundError(f"Input video not found: {input_str}")
        
    cap = cv2.VideoCapture(input_str)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video: {input_str}")
        
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"🎬 Processing: {os.path.basename(input_str)} ({width}x{height}, {fps:.1f} fps, {total_frames} frames)")
    
    # Calculate scale factors relative to base 720x1280
    scale_x = width / 720.0
    scale_y = height / 1280.0
    
    # Base coordinates in 720x1280:
    # Star center is at (598, 1159), tips span rx=24, ry=23
    x1 = int(560 * scale_x)
    x2 = int(640 * scale_x)
    y1 = int(1120 * scale_y)
    y2 = int(1185 * scale_y)
    
    roi_w = x2 - x1
    roi_h = y2 - y1
    cx = int((598 - 560) * scale_x)
    cy = int((1159 - 1120) * scale_y)
    rx = int(24 * scale_x)
    ry = int(23 * scale_y)
    
    mask = generate_star_mask(roi_w, roi_h, cx, cy, rx, ry)
    
    Path(output_str).parent.mkdir(parents=True, exist_ok=True)
    temp_video = output_str + ".temp.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))
    
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        roi = frame[y1:y2, x1:x2]
        # Telea inpainting with radius=2 reconstructs texture flawlessly
        clean_roi = cv2.inpaint(roi, mask, inpaintRadius=2, flags=cv2.INPAINT_TELEA)
        frame[y1:y2, x1:x2] = clean_roi
        
        out.write(frame)
        frame_idx += 1
        
    cap.release()
    out.release()
    
    # Mux back with original audio track using ffmpeg
    cmd = [
        'ffmpeg', '-y',
        '-i', temp_video,
        '-i', input_str,
        '-c:v', 'libx264', '-crf', '18', '-preset', 'fast',
        '-c:a', 'copy',
        '-map', '0:v:0', '-map', '1:a:0?',
        output_str
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Cleanup temp video
    if os.path.exists(temp_video):
        os.remove(temp_video)
        
    print(f"   ✓ Cleaned without trace -> {os.path.basename(output_str)}")
    return output_str

def batch_remove_watermarks(input_dir, output_dir):
    """Batch removes watermarks from all videos in input_dir."""
    in_path = Path(input_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    video_files = []
    for ext in ("*.mp4", "*.mov", "*.webm", "*.m4v"):
        video_files.extend(in_path.glob(ext))
        
    if not video_files:
        print(f"No video files found in {input_dir}")
        return []
        
    video_files = sorted(video_files)
    print(f"\n=======================================================")
    print(f"✨ BATCH WATERMARK REMOVAL: {len(video_files)} VIDEO(S)")
    print(f"=======================================================")
    
    cleaned_files = []
    for v in video_files:
        out_file = out_path / v.name
        remove_watermark_from_video(v, out_file)
        cleaned_files.append(out_file)
        
    print(f"✓ All {len(cleaned_files)} videos successfully de-watermarked!\n")
    return cleaned_files

def main():
    parser = argparse.ArgumentParser(description="Gemini Watermark Remover")
    parser.add_argument("input", nargs="?", default=None, help="Input video file")
    parser.add_argument("output", nargs="?", default=None, help="Output clean video file")
    parser.add_argument("--input_dir", default=None, help="Input directory for batch processing")
    parser.add_argument("--output_dir", default=None, help="Output directory for batch processing")
    args = parser.parse_args()

    if args.input_dir and args.output_dir:
        batch_remove_watermarks(args.input_dir, args.output_dir)
    elif args.input:
        out = args.output if args.output else "clean_" + os.path.basename(args.input)
        remove_watermark_from_video(args.input, out)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
