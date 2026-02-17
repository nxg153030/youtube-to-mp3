import os
import sys
import time
import tempfile
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QHBoxLayout, QMessageBox, QFileDialog,
    QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from moviepy import VideoFileClip
from youtube_to_mp3 import download_youtube_video


TEMP_DIR = os.path.join(tempfile.gettempdir(), "ytdownloader_temp")


def convert_to_mp3(input_file, output_file):
    """Converts a video file (MP4) to an audio file (MP3)."""
    video = VideoFileClip(input_file)
    video.audio.write_audiofile(output_file, logger=None)


# --- Worker class (Runs in a separate thread) ---
class DownloadWorker(QObject):
    # Signals emitted by the worker to communicate with the main thread
    finished = Signal()
    error = Signal(str)
    progress_update = Signal(str)
    progress_value = Signal(int)

    def __init__(self, youtube_url, save_location):
        super().__init__()
        self.url = youtube_url
        self.save_location = save_location

    def report_progress(self, percent):
        self.progress_value.emit(percent)

    def run(self):
        """The main task function that runs in the background thread."""
        mp4_path = None
        try:
            def progress_bridge(percent, status_text):
                scaled_percent = int(percent * 0.8)
                self.progress_value.emit(scaled_percent)
                self.progress_update.emit(status_text)

            self.progress_update.emit("Starting download...")
            # NOTE: pytube/yt-dlp doesn't have a simple callback for progress.
            # We will split the 100% manually: 1-40% for download, 41-100% for conversion.

            # 1. Download the MP4 file
            mp4_path = download_youtube_video(self.url, TEMP_DIR, progress_bridge)

            self.progress_update.emit(f"Download complete. Starting conversion...")
            self.progress_value.emit(80)

            # 2. Convert to MP3
            base_name = os.path.splitext(os.path.basename(mp4_path))[0]
            mp3_output_path = os.path.join(self.save_location, f"{base_name}.mp3")

            self.progress_update.emit(f"Converting audio...")
            self.progress_value.emit(90)

            convert_to_mp3(mp4_path, mp3_output_path)

            self.progress_value.emit(100)
            self.progress_update.emit("All Done!")

        except Exception as e:
            error_message = f"An error occured: {str(e)}"
            self.error.emit(error_message)
        finally:
            if mp4_path and os.path.exists(mp4_path):
                os.remove(mp4_path)
            if os.path.exists(TEMP_DIR):
                os.rmdir(TEMP_DIR)

            # Always signal that the worker task is finished.
            self.finished.emit()


class YouTubeConverterApp(QWidget):
    """The main application window for the YouTube to MP3 Converter."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube to MP3 Converter")
        self.thread = None
        self.worker = None

        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Input Section
        input_layout = QHBoxLayout()
        self.url_label = QLabel("YouTube URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste the YouTube video URL here...")
        input_layout.addWidget(self.url_label)
        input_layout.addWidget(self.url_input)
        main_layout.addLayout(input_layout)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Action Button
        self.download_button = QPushButton("Download && Convert to MP3")
        self.download_button.clicked.connect(self.start_conversion)
        main_layout.addWidget(self.download_button)

        # Status Message
        self.status_label = QLabel("Ready.")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Apply the main layout to the window
        self.setLayout(main_layout)
        self.setGeometry(300, 300, 500, 180)  # x, y, width, height
    
    def apply_styles(self):
        # A modern "Dark Mode" theme
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #3b3b3b;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px;
                color: #fff;
                selection-background-color: #3daee9;
            }
            QLineEdit:focus {
                border: 1px solid #3daee9;
            }
            QPushButton {
                background-color: #3daee9;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4dbef9;
            }
            QPushButton:pressed {
                background-color: #2c9cd7;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
            QProgressBar {
                border: 1px solid #444;
                border-radius: 5px;
                text-align: center;
                background-color: #3b3b3b;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                                  stop:0 #3daee9, stop:1 #5fdfff);
                border-radius: 4px;
            }
            QLabel {
                color: #cccccc;
            }
        """)

    def reset_ui_state(self):
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.download_button.setEnabled(True)
        self.url_input.setEnabled(True)
        self.status_label.setText("Ready.")

    def start_conversion(self):
        """Handler for the Download button click."""
        youtube_url =self.url_input.text()

        if not youtube_url.strip():
            self.status_label.setText("Error: Please paste a YouTube URL.")
            return

        # 1. Ask the user where to save the MP3 file.
        save_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory for MP3",
            os.path.expanduser("~") # Starts in the user's home directory.
        )

        if not save_dir:
            self.status_label.setText("Canceled by user.")
            return

        # Disable the UI while the process is running
        self.download_button.setEnabled(False)
        self.url_input.setEnabled(False)
        self.status_label.setText("Processing started...")

        self.progress_bar.setVisible(True)
        # self.progress_bar.setRange(0, 0)  # Set to busy/indeterminate mode during setup/initial stages
        self.progress_bar.setRange(0, 100)

        self.thread = QThread()
        self.worker = DownloadWorker(youtube_url, save_dir)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress_update.connect(self.update_status)
        self.worker.progress_value.connect(self.progress_bar.setValue)
        self.worker.error.connect(self.handle_error)

        # Clean up and enable UI when the worker finishes (success or failure)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.reset_ui_state)

        self.thread.start()

    def update_status(self, message):
        """Updates the status bar in the UI."""
        self.status_label.setText(message)

    def handle_error(self, error_message):
        """Displays a critical error message box."""
        QMessageBox.critical(self, "Conversion Error", error_message)
        self.status_label.setText("Error: Check message box.")


def main():
    app = QApplication(sys.argv)
    window = YouTubeConverterApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()