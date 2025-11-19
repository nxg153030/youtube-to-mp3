# 🎶 YouTube to MP3 Converter (macOS Desktop App)

A simple, standalone desktop application built with Python and PySide6 that allows users to paste a YouTube URL and convert the video's audio track into a downloadable MP3 file. The core download functionality is handled by the robust `yt-dlp` library, ensuring reliable performance against YouTube's frequent API changes.

The application is packaged as a single `.app` bundle for macOS for easy distribution and use.

## ✨ Features

* **Simple GUI:** Clean interface built with PySide6 (Qt) for a native macOS look and feel.
* **Reliable Download:** Uses the actively maintained `yt-dlp` library for robust video fetching.
* **Threaded Processing:** Download and conversion happen in the background thread, keeping the UI responsive.
* **Progress Feedback:** Displays a progress bar and status messages during the download and conversion process.
* **Automatic Cleanup:** Automatically removes the temporary MP4 video file after successful MP3 conversion.
* **Standalone App:** Packaged using PyInstaller for zero dependency installation on the user's macOS machine.

## 🚀 Installation (For End Users)

Since this application is packaged as a standalone bundle, installation is simple:

1.  **Download:** Download the latest release of the `MP3 Converter.app.zip` file from the [Releases page](LINK_TO_YOUR_RELEASES_PAGE_HERE).
2.  **Extract:** Unzip the file to get the `MP3 Converter.app` application.
3.  **Install:** Drag the `MP3 Converter.app` file into your Mac's **`/Applications`** folder.
4.  **First Run:** The first time you run the app, macOS may show a security warning. To bypass this: **Right-click** the app icon and select **"Open"**. Click **"Open"** again in the resulting dialog.

## 💻 Usage

1.  **Paste URL:** Copy the URL of the YouTube video you want to convert.
2.  **Run App:** Launch the **MP3 Converter** app.
3.  **Click Download:** Paste the URL into the input field and click **"Download & Convert to MP3"**.
4.  **Select Location:** A dialog will pop up asking you to choose the destination folder for the final MP3 file.
5.  **Wait:** The status bar and progress bar will update as the video is downloaded and converted.
6.  **Done:** Once complete, the status will show "Conversion finished successfully!", and your MP3 file will be in the selected folder.

## ⚙️ Development & Building (For Developers)

If you wish to run the app directly from the source code or rebuild the executable, follow these steps.

### Prerequisites

You need **Python 3.10+** (Python 3.12 is recommended) and the following libraries:

```bash
# Set up a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install PySide6 yt-dlp moviepy