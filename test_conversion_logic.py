import unittest
import os
import shutil
from unittest.mock import patch, MagicMock

from gui import download_youtube_video, convert_to_mp3, TEMP_DIR

# --- Configuration ---
# Use a short, public domain video URL for reliable testing
TEST_URL = "https://www.youtube.com/watch?v=fY_4zJu9hg4"
TEST_OUTPUT_DIR = "test_output"


class TestConversionLogic(unittest.TestCase):
    """Unit tests for the download and conversion functions."""

    @classmethod
    def setUpClass(cls):
        """Set up the environment before running any tests."""
        os.makedirs(TEMP_DIR, exist_ok=True)
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        """Clean up the environment after all tests are done."""
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
        if os.path.exists(TEST_OUTPUT_DIR):
            shutil.rmtree(TEST_OUTPUT_DIR)

    def test_01_download_youtube_video_success(self):
        """Tests successful download of a video."""
        print("\n--- Testing Download Success ---")
        try:
            # Call the function being tested
            mp4_path = download_youtube_video(TEST_URL, TEMP_DIR)

            # Assertions
            self.assertTrue(os.path.exists(mp4_path), "Downloaded file should exist.")
            self.assertTrue(mp4_path.endswith(".mp4"), "Downloaded file should be MP4 format.")
            self.assertIn(TEMP_DIR, mp4_path, "File should be saved in the temporary directory.")

            # Store the path for the next test
            self.downloaded_mp4_path = mp4_path
            print(f"Downloaded file path: {mp4_path}")

        except Exception as e:
            # If the download fails (e.g., HTTP 400), print the error and fail the test
            self.fail(f"Download failed with exception: {e}")

    def test_02_convert_to_mp3_success(self):
        """Tests successful conversion of an MP4 file to MP3."""
        print("\n--- Testing Conversion Success ---")
        # Pre-condition: Assume test_01 was run and self.downloaded_mp4_path exists
        # In a real run, tests can be dependent, but here we'll ensure the file exists.
        if not hasattr(self, 'downloaded_mp4_path') or not os.path.exists(self.downloaded_mp4_path):
            self.skipTest("Skipping conversion test: MP4 file was not downloaded in the previous step.")
            return

        input_file = self.downloaded_mp4_path
        output_file = os.path.join(TEST_OUTPUT_DIR, "test_output.mp3")

        try:
            # Call the function being tested
            convert_to_mp3(input_file, output_file)

            # Assertions
            self.assertTrue(os.path.exists(output_file), "Converted MP3 file should exist.")
            self.assertTrue(output_file.endswith(".mp3"), "Output file should be MP3 format.")
            self.assertGreater(os.path.getsize(output_file), 1024, "MP3 file size should be greater than 1KB.")
            print(f"Converted MP3 path: {output_file}")

        except Exception as e:
            self.fail(f"Conversion failed with exception: {e}")

    # Optional: Test edge cases like invalid URL
    def test_03_download_invalid_url(self):
        """Tests handling of an invalid YouTube URL."""
        print("\n--- Testing Invalid URL ---")
        invalid_url = "https://www.youtube.com/watch?v=NOT_A_VALID_ID"
        # We expect pytube to raise an exception for an invalid video ID
        with self.assertRaises((Exception)):
            download_youtube_video(invalid_url, TEMP_DIR)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)