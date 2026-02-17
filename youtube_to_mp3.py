import os
import sys
import subprocess
from yt_dlp import YoutubeDL


def check_and_update_ytdlp():
    """
    Checks for updates to yt-dlp and upgrades if available.
    """
    try:
        print("Checking for yt-dlp updates...")
        # This effectively runs 'pip install --upgrade yt-dlp'
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"])
        print("yt-dlp is up to date.")
    except Exception as e:
        print(f"Failed to update yt-dlp: {e}")


def download_youtube_video(url, output_path):
    """Download the YouTube video using yt-dlp."""
    ydl_opts = {
        # 'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', # Get best video/audio and combine
        'format': 'best',  # For simplicity, let yt-dlp pick the best combined format (usually mp4)
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'noplaylist': True,  # Ensure we only download a single video
        'quiet': True,  # Suppress command-line output
        'no_warnings': True,
        'nocheckcertificate': True, # Ignore SSL errors
        'ignoreerrors': True, # Skip errors and continue
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # yt-dlp returns the full info dictionary. We need the actual file path.
            # This is the expected path after successful download
            filename = ydl.prepare_filename(info)
    except Exception as e:
        # Re-raise the exception so the GUI can catch it and show the error.
        raise RuntimeError(f"yt-dlp failed to download: {str(e)}")


    return filename


if __name__ == "__main__":
    check_and_update_ytdlp()