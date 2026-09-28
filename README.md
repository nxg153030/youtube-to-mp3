# YouTube Downloader for macOS

A macOS desktop app for downloading YouTube videos as MP4, extracting audio as MP3, or saving both. It uses `yt-dlp` to fetch media and PySide6 for the interface.

## Features

- Download audio as MP3, video as MP4, or both.
- Queue multiple URLs or import a shared note.
- Optionally download a clip using start and end timestamps.
- Track item and overall progress while downloads run in the background.
- Package the app as a standalone macOS application with PyInstaller.

## Install

1. Download `YouTubeDownloader.zip` from the project's GitHub Releases page.
2. Unzip the download and move `YouTubeDownloader.app` to Applications.
3. On first launch, macOS may block the unsigned app. Control-click the app and choose **Open**, then confirm **Open** in the dialog. If that option is unavailable, go to **System Settings > Privacy & Security** and choose **Open Anyway** for the app.

## Use

1. Paste a YouTube URL and add it to the queue, or import a shared note.
2. To download a clip, enable **Clip Video (Timestamps)** and enter its start and end times.
3. Choose **Audio Only (MP3)**, **Video Only (MP4)**, or **Both (MP3 + MP4)**.
4. Select an output folder and start the download.

## Run from source

Python 3.10 or later is required. From the project directory:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python gui.py
```

For build and release instructions, see [DEVELOPER.md](DEVELOPER.md).
