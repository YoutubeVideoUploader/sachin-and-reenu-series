import unittest
import sys
import os
import json
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from drive_sync_and_check import resolve_active_season_and_episode
from generate_thumbnail import resolve_season_and_episode_num
from instagram_publisher import normalize_ep_data
from video_merger import validate_master_video

class TestMetadataResolution(unittest.TestCase):

    def test_drive_sync_dynamic_resolution(self):
        """drive_sync_and_check must auto-resolve (3, 2) from current state without defaulting to 1."""
        season, episode = resolve_active_season_and_episode()
        self.assertEqual(season, 3)
        self.assertEqual(episode, 2)

    def test_drive_sync_cli_and_env_override(self):
        """CLI arguments and environment variables must override local file defaults."""
        # Test CLI args
        season, episode = resolve_active_season_and_episode(ep_arg=5, season_arg=4)
        self.assertEqual(season, 4)
        self.assertEqual(episode, 5)

        # Test ENV vars
        os.environ["EPISODE_NUMBER"] = "7"
        os.environ["SEASON_NUMBER"] = "5"
        try:
            s_env, ep_env = resolve_active_season_and_episode()
            self.assertEqual(s_env, 5)
            self.assertEqual(ep_env, 7)
        finally:
            del os.environ["EPISODE_NUMBER"]
            del os.environ["SEASON_NUMBER"]

    def test_thumbnail_resolution_no_s2e7_fallback(self):
        """Thumbnail resolution must resolve active season 3 without falling back to Season 2 Episode 7."""
        s, ep = resolve_season_and_episode_num()
        self.assertEqual(s, 3)
        self.assertEqual(ep, 2)
        self.assertNotEqual((s, ep), (2, 7))

    def test_instagram_normalize_no_monsoon_revelation_fallback(self):
        """Instagram normalization on raw shot list must pull live metadata, never hardcoded 'Monsoon Revelation'."""
        dummy_shots = [{"shot_number": 1, "action": "Test action"}]
        norm = normalize_ep_data(dummy_shots)
        self.assertEqual(norm.get("season_number"), 3)
        self.assertEqual(norm.get("episode_number"), 2)
        self.assertNotEqual(norm.get("title_english"), "The Monsoon Revelation")

    def test_master_video_validation_guards(self):
        """validate_master_video must strictly reject non-existent, empty, or truncated files."""
        # Non-existent file
        with self.assertRaises(FileNotFoundError):
            validate_master_video("non_existent_output_file.mp4")

        # Empty / tiny file (< 50KB)
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(b"not a video file")
            tmp_path = tmp.name

        try:
            with self.assertRaises(ValueError):
                validate_master_video(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

if __name__ == "__main__":
    unittest.main()
