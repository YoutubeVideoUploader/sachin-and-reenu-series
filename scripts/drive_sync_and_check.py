#!/usr/bin/env python3
"""
drive_sync_and_check.py - Google Sheet Checklist & Drive Downloader
Strictly verifies that ALL required shots (e.g. 22/22) are marked 'Present'
in the Google Sheet checklist before downloading. If any shot is missing or the
sheet is blank, execution exits cleanly with no error and prevents video generation.
"""

import os
import sys
import re
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import json
import time
import argparse
import requests
import cv2
from pathlib import Path

def verify_video(file_path):
    """Verifies that the downloaded file is a valid, readable video with frames."""
    try:
        cap = cv2.VideoCapture(str(file_path))
        if not cap.isOpened():
            cap.release()
            return False
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        return frames > 0 and fps > 0
    except Exception:
        return False

def download_file_from_drive(file_id, download_url, destination_path):
    """Downloads a file from Google Drive using direct export links and verifies with OpenCV."""
    dest = Path(destination_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    session = requests.Session()
    urls_to_try = [
        f"https://drive.usercontent.google.com/download?id={file_id}&export=download",
        f"https://drive.google.com/uc?export=download&id={file_id}"
    ]
    
    downloaded = False
    for export_url in urls_to_try:
        try:
            res = session.get(export_url, headers=headers, stream=True, timeout=90)
            
            # Check for virus scan confirmation token if Google returns an HTML interstitial
            content_type = res.headers.get("Content-Type", "")
            if "text/html" in content_type:
                token = None
                for k, v in session.cookies.items():
                    if k.startswith("download_warning"):
                        token = v
                        break
                if not token:
                    match = re.search(r'confirm=([0-9A-Za-z_-]+)', res.text)
                    if match:
                        token = match.group(1)
                if token:
                    confirm_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm={token}"
                    res = session.get(confirm_url, headers=headers, stream=True, timeout=90)

            # Write file in chunks
            with open(dest, "wb") as f:
                for chunk in res.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)

            # Verify downloaded file size and playable video format
            if dest.exists() and dest.stat().st_size > 50000 and verify_video(dest):
                downloaded = True
                break
        except Exception as err:
            print(f"      Attempt via {export_url[:40]}... failed: {err}")

    if downloaded:
        return True
    else:
        file_size = dest.stat().st_size if dest.exists() else 0
        raise RuntimeError(f"Downloaded file for ID {file_id} failed video validation (Size: {file_size} bytes, Valid: False)")

def check_and_download(gas_url, episode_num=1, target_dir="uploaded_shots"):
    """
    Queries Google Apps Script for Google Sheet checklist status.
    If all shots present, downloads them into target_dir.
    """
    print(f"\n=======================================================")
    print(f"📊 GOOGLE SHEET & DRIVE PRE-CHECK: EPISODE {episode_num}")
    print(f"=======================================================")
    
    if not gas_url:
        print("⚠️ Warning: GAS_WEBHOOK_URL is not set.")
        # Check if local files already exist in target_dir
        local_dir = Path(target_dir)
        local_vids = list(local_dir.glob("*.mp4")) if local_dir.exists() else []
        if len(local_vids) >= 20:
            print(f"Found {len(local_vids)} local video files in {target_dir}. Proceeding with local files.")
            set_github_output("should_run", "true")
            set_github_output("ready", "true")
            return True
        else:
            print("GAS_WEBHOOK_URL not provided and local files not found. Clean exit.")
            set_github_output("should_run", "false")
            set_github_output("ready", "false")
            return False

    # Call Google Apps Script Web App GET endpoint with retry
    check_url = f"{gas_url}?action=check_status&episode={episode_num}"
    try:
        req_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        res = None
        for attempt in range(1, 4):
            try:
                res = requests.get(check_url, headers=req_headers, timeout=60)
                if res.status_code == 200:
                    break
            except requests.exceptions.RequestException as re_err:
                print(f"Attempt {attempt}/3 failed: {re_err}. Retrying in 3s...")
                time.sleep(3)

        if not res or res.status_code != 200:
            print(f"Error fetching checklist: HTTP {res.status_code if res else 'Timeout'}")
            set_github_output("should_run", "false")
            set_github_output("ready", "false")
            return False
            
        data = res.json()
        sheet_data = data.get("data", {})
        total_shots = sheet_data.get("total_shots", 0)
        present_shots = sheet_data.get("present_shots", 0)
        is_ready = sheet_data.get("ready", False)
        files = sheet_data.get("files", [])
        
        print(f"Total Shots in Checklist : {total_shots}")
        print(f"Present Shots in Drive   : {present_shots}")
        print(f"All Shots Ready          : {is_ready}")
        
        # Condition 1: Blank or 0 shots in Sheet
        if total_shots == 0:
            print("\nℹ️  Google Sheet checklist is BLANK or empty. No video production required.")
            print("   Stopping workflow cleanly without running.")
            set_github_output("should_run", "false")
            set_github_output("ready", "false")
            return "skip"
            
        # Condition 2: Not all shots present (e.g. 19 of 22)
        if not is_ready or present_shots < total_shots:
            missing = total_shots - present_shots
            print(f"\n⚠️  PRE-CHECK NOT MET: Only {present_shots} of {total_shots} shots are present in Google Drive.")
            print(f"   Missing {missing} shot(s). Code execution stopped cleanly.")
            print("   Workflow will automatically run once all videos are uploaded to Google Drive.")
            set_github_output("should_run", "false")
            set_github_output("ready", "false")
            return "skip"
            
        # Condition 3: ALL shots present!
        print(f"\n🎉 ALL {total_shots}/{total_shots} SHOTS ARE VERIFIED PRESENT!")
        print(f"Downloading {len(files)} video clips from Google Drive to '{target_dir}'...")
        
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        
        # Sort files in numerical order by shot number
        def get_shot_idx(file_obj):
            fname = file_obj.get("filename") or file_obj.get("name") or ""
            m = re.search(r'(?:shot|scene|take|part)[_\s-]*0*(\d+)', fname, re.IGNORECASE)
            if m:
                return int(m.group(1))
            return file_obj.get("shot_number", 0)

        sorted_files = sorted(files, key=get_shot_idx)

        for f in sorted_files:
            filename = f.get("filename") or f.get("name") or "shot.mp4"
            shot_num = get_shot_idx(f) or 1
            file_id = f.get("file_id") or f.get("id")
            dl_url = f.get("download_url") or f.get("downloadUrl") or f.get("url")
            
            if not file_id:
                raise ValueError(f"No valid Google Drive file ID found in object: {f}")

            # Standardize destination filename: shot_01.mp4, shot_02.mp4...
            dest_file = target_path / f"shot_{shot_num:02d}.mp4"
            print(f"  ⬇️  Downloading Shot {shot_num:02d} ({filename}) [Drive ID: {file_id}]...")
            download_file_from_drive(file_id, dl_url, dest_file)
            print(f"     ✓ Verified {dest_file.name} ({dest_file.stat().st_size} bytes)")
            
        print(f"\n✓ All {len(sorted_files)} clips downloaded and verified successfully!")
        set_github_output("should_run", "true")
        set_github_output("ready", "true")
        return "success"

    except Exception as e:
        print(f"\n❌ Error downloading or verifying shots from Google Drive: {e}")
        set_github_output("should_run", "false")
        set_github_output("ready", "false")
        return "error"

def set_github_output(name, value):
    """Sets output variable for GitHub Actions step if GITHUB_OUTPUT environment variable is present."""
    gh_output_path = os.getenv("GITHUB_OUTPUT")
    if gh_output_path:
        with open(gh_output_path, "a", encoding="utf-8") as f:
            f.write(f"{name}={value}\n")
    print(f"[Action Output] {name}={value}")

def main():
    parser = argparse.ArgumentParser(description="Google Sheet & Drive Checklist Sync")
    parser.add_argument("--gas_url", default=os.getenv("GAS_WEBHOOK_URL", ""), help="Google Apps Script Web App URL")
    parser.add_argument("--episode", type=int, default=1, help="Episode number to check")
    parser.add_argument("--target_dir", default="uploaded_shots", help="Directory to save downloaded shots")
    args = parser.parse_args()

    status = check_and_download(
        gas_url=args.gas_url,
        episode_num=args.episode,
        target_dir=args.target_dir
    )
    if status == "error":
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
