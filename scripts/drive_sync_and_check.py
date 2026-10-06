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
from pathlib import Path

def download_file_from_drive(file_id, download_url, destination_path):
    """Downloads a file from Google Drive using direct URL or export link."""
    dest = Path(destination_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    # 1. Try provided direct download_url if available
    if download_url:
        try:
            r = requests.get(download_url, headers=headers, stream=True, timeout=60)
            if r.status_code == 200 and int(r.headers.get('content-length', 1000)) > 500:
                with open(dest, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                if dest.stat().st_size > 5000:
                    return True
        except Exception as e:
            print(f"Direct download attempt failed: {e}")

    # 2. Fallback to Google Drive uc export link
    drive_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    session = requests.Session()
    res = session.get(drive_url, headers=headers, stream=True, timeout=60)
    
    # Check for virus scan confirmation token for larger files
    token = None
    for k, v in res.cookies.items():
        if k.startswith('download_warning'):
            token = v
            break
            
    if token:
        confirm_url = f"https://drive.google.com/uc?export=download&confirm={token}&id={file_id}"
        res = session.get(confirm_url, headers=headers, stream=True, timeout=60)
        
    with open(dest, 'wb') as f:
        for chunk in res.iter_content(chunk_size=1024*1024):
            if chunk:
                f.write(chunk)
                
    if dest.exists() and dest.stat().st_size > 5000:
        return True
    else:
        raise RuntimeError(f"Downloaded file for ID {file_id} is corrupt or empty ({dest.stat().st_size if dest.exists() else 0} bytes).")

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
    print(f"Checking Google Sheet checklist via: {check_url[:45]}...")
    
    try:
        res = None
        for attempt in range(1, 4):
            try:
                res = requests.get(check_url, timeout=60)
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
            return False
            
        # Condition 2: Not all shots present (e.g. 19 of 22)
        if not is_ready or present_shots < total_shots:
            missing = total_shots - present_shots
            print(f"\n⚠️  PRE-CHECK NOT MET: Only {present_shots} of {total_shots} shots are present in Google Drive.")
            print(f"   Missing {missing} shot(s). Code execution stopped cleanly.")
            print("   Workflow will automatically run once all videos are uploaded to Google Drive.")
            set_github_output("should_run", "false")
            set_github_output("ready", "false")
            return False
            
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
            print(f"     ✓ Saved to {dest_file.name} ({dest_file.stat().st_size} bytes)")
            
        print(f"\n✓ All {len(sorted_files)} clips downloaded successfully!")
        set_github_output("should_run", "true")
        set_github_output("ready", "true")
        return True

    except Exception as e:
        print(f"Error checking/downloading shots from Google Drive: {e}")
        set_github_output("should_run", "false")
        set_github_output("ready", "false")
        return False

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

    success = check_and_download(
        gas_url=args.gas_url,
        episode_num=args.episode,
        target_dir=args.target_dir
    )
    # Always exit 0 so GitHub Actions handles the condition cleanly via 'if' step checks
    sys.exit(0)

if __name__ == "__main__":
    main()
