import os
import sys
import tempfile
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QHBoxLayout, QMessageBox, QFileDialog,
    QProgressBar, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from moviepy import VideoFileClip
from youtube_to_mp3 import download_youtube_video

TEMP_DIR = os.path.join(tempfile.gettempdir(), "YoutubeDownloader_Temp")

def convert_to_mp3(input_file, output_file):
    video = VideoFileClip(input_file)
    video.audio.write_audiofile(output_file, logger=None)
    video.close()

class DownloadWorker(QObject):
    finished = Signal()
    error = Signal(str)
    progress_update = Signal(str)
    progress_value = Signal(int)

    def __init__(self, youtube_url, save_location, format_choice, start_sec=None, end_sec=None):
        super().__init__()
        self.url = youtube_url
        self.save_location = save_location
        self.format_choice = format_choice
        self.start_sec = start_sec
        self.end_sec = end_sec

    def run(self):
        downloaded_mp4_path = None
        try:
            def progress_bridge(percent, status_text):
                if self.format_choice == "Video Only (MP4)":
                    self.progress_value.emit(int(percent))
                else:
                    self.progress_value.emit(int(percent * 0.8))
                self.progress_update.emit(status_text)

            self.progress_update.emit("Initializing...")
            
            download_dir = TEMP_DIR if self.format_choice == "Audio Only (MP3)" else self.save_location

            # Pass the timestamps to the downloader
            downloaded_mp4_path = download_youtube_video(
                self.url, download_dir, progress_bridge, self.start_sec, self.end_sec
            )
            
            if self.format_choice == "Video Only (MP4)":
                self.progress_value.emit(100)
                self.progress_update.emit("All Done! Video saved.")
                self.finished.emit()
                return

            self.progress_update.emit("Download complete. Starting conversion...")
            self.progress_value.emit(80) 

            base_name = os.path.splitext(os.path.basename(downloaded_mp4_path))[0]
            mp3_output_path = os.path.join(self.save_location, f"{base_name}.mp3")

            self.progress_update.emit(f"Converting: {base_name}...")
            self.progress_value.emit(90) 
            
            convert_to_mp3(downloaded_mp4_path, mp3_output_path)
            
            self.progress_value.emit(100)
            self.progress_update.emit("All Done!")

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            self.error.emit(error_message)
        finally:
            if self.format_choice == "Audio Only (MP3)" and downloaded_mp4_path and os.path.exists(downloaded_mp4_path):
                try:
                    os.remove(downloaded_mp4_path)
                except:
                    pass
            self.finished.emit()


class YouTubeConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader")
        self.thread = None
        self.worker = None

        self.init_ui()
        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #ffffff; font-family: 'Segoe UI', sans-serif; font-size: 14px; }
            QLineEdit, QComboBox { background-color: #3b3b3b; border: 1px solid #555; border-radius: 5px; padding: 8px; color: #fff; }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #3daee9; }
            QComboBox::drop-down { border: none; }
            QPushButton { background-color: #3daee9; color: white; border: none; border-radius: 5px; padding: 10px 15px; font-weight: bold; }
            QPushButton:hover { background-color: #4dbef9; }
            QPushButton:pressed { background-color: #2c9cd7; }
            QPushButton:disabled { background-color: #555; color: #888; }
            QProgressBar { border: 1px solid #444; border-radius: 5px; text-align: center; background-color: #3b3b3b; height: 20px; color: white; }
            QProgressBar::chunk { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3daee9, stop:1 #5fdfff); border-radius: 4px; }
            QLabel { color: #cccccc; }
            QCheckBox { color: #cccccc; font-weight: bold; font-size: 12px; }
        """)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15) 
        main_layout.setContentsMargins(20, 20, 20, 20) 

        # URL Input
        input_layout = QVBoxLayout()
        self.url_label = QLabel("YouTube URL:")
        self.url_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #aaa;")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste link here...")
        input_layout.addWidget(self.url_label)
        input_layout.addWidget(self.url_input)
        main_layout.addLayout(input_layout)

        # Format Selection
        format_layout = QHBoxLayout()
        self.format_label = QLabel("Format:")
        self.format_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #aaa;")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Audio Only (MP3)", "Video Only (MP4)", "Both (MP3 + MP4)"])
        format_layout.addWidget(self.format_label)
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        main_layout.addLayout(format_layout)

        # Timestamps Section
        time_layout = QHBoxLayout()
        self.time_checkbox = QCheckBox("Clip Video (Timestamps)")
        self.time_checkbox.toggled.connect(self.toggle_timestamps)
        
        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("Start (e.g. 1:15)")
        self.start_input.setEnabled(False)
        self.start_input.setFixedWidth(110)
        
        self.end_input = QLineEdit()
        self.end_input.setPlaceholderText("End (e.g. 2:30)")
        self.end_input.setEnabled(False)
        self.end_input.setFixedWidth(110)

        time_layout.addWidget(self.time_checkbox)
        time_layout.addWidget(self.start_input)
        time_layout.addWidget(QLabel("to"))
        time_layout.addWidget(self.end_input)
        time_layout.addStretch()
        main_layout.addLayout(time_layout)

        # Progress bar & Status
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 11px; color: #888;")
        main_layout.addWidget(self.status_label)

        # Action Button
        self.download_button = QPushButton("Download")
        self.download_button.clicked.connect(self.start_conversion)
        main_layout.addWidget(self.download_button)

        self.setLayout(main_layout)
        self.setGeometry(300, 300, 520, 340)

    def toggle_timestamps(self, is_checked):
        self.start_input.setEnabled(is_checked)
        self.end_input.setEnabled(is_checked)

    def parse_time(self, time_str):
        """Converts MM:SS or HH:MM:SS to total seconds."""
        try:
            parts = time_str.strip().split(':')
            parts.reverse()
            return sum(int(part) * (60 ** i) for i, part in enumerate(parts))
        except Exception:
            return None

    def reset_ui_state(self):
        self.download_button.setEnabled(True)
        self.url_input.setEnabled(True)
        self.format_combo.setEnabled(True)
        self.time_checkbox.setEnabled(True)
        if self.time_checkbox.isChecked():
            self.start_input.setEnabled(True)
            self.end_input.setEnabled(True)

    def start_conversion(self):
        youtube_url = self.url_input.text()
        format_choice = self.format_combo.currentText()

        if not youtube_url.strip():
            self.status_label.setText("Error: Please paste a YouTube URL.")
            return

        start_sec, end_sec = None, None
        if self.time_checkbox.isChecked():
            start_sec = self.parse_time(self.start_input.text())
            end_sec = self.parse_time(self.end_input.text())
            
            if start_sec is None or end_sec is None or start_sec >= end_sec:
                self.status_label.setText("Error: Invalid timestamps (use MM:SS format).")
                return

        save_dir = QFileDialog.getExistingDirectory(self, "Select Output Folder", os.path.expanduser("~"))
        if not save_dir:
            return

        # Disable UI during download
        self.download_button.setEnabled(False)
        self.url_input.setEnabled(False)
        self.format_combo.setEnabled(False)
        self.time_checkbox.setEnabled(False)
        self.start_input.setEnabled(False)
        self.end_input.setEnabled(False)
        self.status_label.setText("Initializing...")

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.thread = QThread()
        self.worker = DownloadWorker(youtube_url, save_dir, format_choice, start_sec, end_sec)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress_update.connect(self.update_status)
        self.worker.progress_value.connect(self.progress_bar.setValue)
        self.worker.error.connect(self.handle_error)

        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.reset_ui_state)

        self.thread.start()

    def update_status(self, message):
        self.status_label.setText(message)

    def handle_error(self, error_message):
        QMessageBox.critical(self, "Error", error_message)
        self.status_label.setText("Error occurred.")
        self.reset_ui_state()

def main():
    app = QApplication(sys.argv)
    window = YouTubeConverterApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()