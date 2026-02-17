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


def download_youtube_video(url, output_path, progress_callback=None):
    """
    Download the YouTube video using yt-dlp.
    progress_callback: A function that accepts the progress dictionary from yt-dlp.
    """
    def ytdl_hook(d):
        if d["status"] == "downloading":
            if d.get("total_bytes"):
                p = d["downloaded_bytes"] / d["total_bytes"] * 100
                if progress_callback:
                    progress_callback(int(p), "Downloading...")
                elif d.get("total_bytes_estimate"):
                    p = d["downloaded_bytes"] / d["total_bytes_estimate"] * 100
                    if progress_callback:
                        progress_callback(int(p), "Downloading...")
        elif d["status"] == "finished":
            if progress_callback:
                progress_callback(100, "Download complete, Converting...")

    ydl_opts = {
        'format': 'best',  # For simplicity, let yt-dlp pick the best combined format (usually mp4)
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'noplaylist': True,  # Ensure we only download a single video
        'quiet': True,  # Suppress command-line output
        'no_warnings': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        "progress_hooks": [ytdl_hook]
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
    except Exception as e:
        # Re-raise the exception so the GUI can catch it and show the error.
        raise RuntimeError(f"yt-dlp failed to download: {str(e)}")


    return filename


if __name__ == "__main__":
    check_and_update_ytdlp()