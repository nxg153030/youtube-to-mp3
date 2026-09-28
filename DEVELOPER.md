# Developer Guide: Build and Release

This guide covers building the macOS app and publishing it on GitHub Releases.

## Prerequisites

- macOS
- Python 3.10 or later
- The project dependencies from `requirements.txt`

From the project root, create and activate a virtual environment, then install the dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

## Build

If you need a clean build, remove only the generated `build` and `dist` directories from the project root:

```bash
rm -rf build dist
```

Build using the checked-in PyInstaller spec. It configures the app bundle, icon, and required package metadata:

```bash
pyinstaller YouTubeDownloader.spec
```

The app bundle is created at `dist/YouTubeDownloader.app`.

## Package

Create a zip archive from the project root:

```bash
ditto -c -k --sequesterRsrc --keepParent \
	"dist/YouTubeDownloader.app" \
	"dist/YouTubeDownloader.zip"
```

Attach `dist/YouTubeDownloader.zip` to the GitHub Release.

## Publish a GitHub Release

1. Create and push a version tag.
2. Draft the release title and notes.
3. Attach `YouTubeDownloader.zip` from the build output.
4. Publish the release.

The app is currently unsigned. Tell users that macOS may block it on first launch; they can Control-click the app and choose **Open**, or use **System Settings > Privacy & Security > Open Anyway**.
