import os
import sys
import tempfile
import re
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QHBoxLayout, QMessageBox, QFileDialog,
    QProgressBar, QComboBox, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QTextEdit, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, QObject
from moviepy import VideoFileClip
from youtube_to_mp3 import download_youtube_video

TEMP_DIR = os.path.join(tempfile.gettempdir(), "YoutubeDownloader_Temp")

def convert_to_mp3(input_file, output_file):
    video = VideoFileClip(input_file)
    video.audio.write_audiofile(output_file, logger=None)
    video.close()

def parse_time(time_str):
    if not time_str:
        return None
    try:
        parts = str(time_str).strip().split(':')
        parts.reverse()
        return sum(int(part) * (60 ** i) for i, part in enumerate(parts))
    except Exception:
        return None

# --- Bulk Import Window ---
class ImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Shared Note")
        self.setGeometry(350, 350, 500, 400)
        self.setStyleSheet(parent.styleSheet())
        
        layout = QVBoxLayout()
        label = QLabel("Paste your entire shared note below:")
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Yemito (0:20-4:28)\nhttps://youtube.com/...\n\nBangaru Kalla Bujjamo\nhttps://...")
        
        btn_layout = QHBoxLayout()
        self.import_btn = QPushButton("Process Note")
        self.import_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.import_btn)
        
        layout.addWidget(label)
        layout.addWidget(self.text_edit)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def get_text(self):
        return self.text_edit.toPlainText()

# --- Batch Worker ---
class BatchDownloadWorker(QObject):
    finished = Signal()
    error = Signal(str)
    item_progress = Signal(int, str, int) 
    overall_progress = Signal(int)

    def __init__(self, queue_items, save_location, format_choice):
        super().__init__()
        self.queue_items = queue_items
        self.save_location = save_location
        self.format_choice = format_choice

    def run(self):
        total_items = len(self.queue_items)
        
        for index, item in enumerate(self.queue_items):
            row = item['row']
            url = item['url']
            title = item['title']
            start_sec = parse_time(item['start'])
            end_sec = parse_time(item['end'])
            
            downloaded_mp4_path = None
            try:
                def progress_bridge(percent, status_text):
                    scaled_percent = int(percent) if self.format_choice == "Video Only (MP4)" else int(percent * 0.8)
                    self.item_progress.emit(row, f"{status_text} ({scaled_percent}%)", scaled_percent)

                self.item_progress.emit(row, "Downloading...", 0)
                download_dir = TEMP_DIR if self.format_choice == "Audio Only (MP3)" else self.save_location

                # 1. Download
                downloaded_mp4_path = download_youtube_video(url, download_dir, progress_bridge, start_sec, end_sec)
                
                if self.format_choice == "Video Only (MP4)":
                    self.item_progress.emit(row, "Done! Video saved.", 100)
                else:
                    # 2. Convert to MP3
                    self.item_progress.emit(row, "Converting to MP3...", 90)
                    
                    # If title is from a single URL add, it will be "(Auto-fetch)". Let yt-dlp name it.
                    if title and title != "(Auto-fetch)":
                        base_name = re.sub(r'[\\/*?:"<>|]', "", title) 
                    else:
                        base_name = os.path.splitext(os.path.basename(downloaded_mp4_path))[0]
                        
                    mp3_output_path = os.path.join(self.save_location, f"{base_name}.mp3")
                    convert_to_mp3(downloaded_mp4_path, mp3_output_path)
                    
                    self.item_progress.emit(row, "Done!", 100)

            except Exception as e:
                self.item_progress.emit(row, "Error!", 0)
            finally:
                if self.format_choice == "Audio Only (MP3)" and downloaded_mp4_path and os.path.exists(downloaded_mp4_path):
                    try:
                        os.remove(downloaded_mp4_path)
                    except:
                        pass
            
            self.overall_progress.emit(int(((index + 1) / total_items) * 100))

        self.finished.emit()


class YouTubeConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader Ultimate")
        self.thread = None
        self.worker = None

        self.init_ui()
        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; color: #ffffff; font-family: 'Segoe UI', sans-serif; font-size: 13px; }
            QLineEdit, QComboBox, QTextEdit { background-color: #3b3b3b; border: 1px solid #555; border-radius: 5px; padding: 6px; color: #fff; }
            QPushButton { background-color: #3daee9; color: white; border: none; border-radius: 5px; padding: 8px 15px; font-weight: bold; }
            QPushButton:hover { background-color: #4dbef9; }
            QPushButton:pressed { background-color: #2c9cd7; }
            QPushButton:disabled { background-color: #555; color: #888; }
            QProgressBar { border: 1px solid #444; border-radius: 5px; text-align: center; background-color: #3b3b3b; height: 15px; color: white; }
            QProgressBar::chunk { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3daee9, stop:1 #5fdfff); border-radius: 4px; }
            QLabel { color: #cccccc; font-weight: bold; }
            QCheckBox { color: #cccccc; font-weight: bold; }
            QTableWidget { background-color: #333; gridline-color: #555; border: 1px solid #555; border-radius: 5px; }
            QHeaderView::section { background-color: #222; color: #aaa; padding: 4px; border: 1px solid #444; font-weight: bold; }
            QFrame#separator { background-color: #444; }
        """)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12) 
        main_layout.setContentsMargins(20, 20, 20, 20) 

        # --- SECTION 1: Single URL Input ---
        single_input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste a single YouTube URL here...")
        
        self.add_single_btn = QPushButton("➕ Add to Queue")
        self.add_single_btn.clicked.connect(self.add_single_url)
        
        single_input_layout.addWidget(self.url_input)
        single_input_layout.addWidget(self.add_single_btn)
        main_layout.addLayout(single_input_layout)

        # Single URL Timestamps
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

        # Visual Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setObjectName("separator")
        main_layout.addWidget(separator)

        # --- SECTION 2: Bulk Import & Format ---
        top_layout = QHBoxLayout()
        self.import_btn = QPushButton("📋 Import Shared Note")
        self.import_btn.setStyleSheet("background-color: #2ecc71;") 
        self.import_btn.clicked.connect(self.open_import_dialog)
        top_layout.addWidget(self.import_btn)
        
        top_layout.addStretch()

        self.format_label = QLabel("Format:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Audio Only (MP3)", "Video Only (MP4)", "Both (MP3 + MP4)"])
        top_layout.addWidget(self.format_label)
        top_layout.addWidget(self.format_combo)
        main_layout.addLayout(top_layout)

        # --- SECTION 3: Queue Table ---
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Title", "URL", "Start", "End", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(2, 60)
        self.table.setColumnWidth(3, 60)
        self.table.setColumnWidth(4, 150)
        main_layout.addWidget(self.table)

        # --- SECTION 4: Bottom Controls ---
        bottom_layout = QHBoxLayout()
        self.clear_btn = QPushButton("Clear Queue")
        self.clear_btn.setStyleSheet("background-color: #e74c3c;")
        self.clear_btn.clicked.connect(lambda: self.table.setRowCount(0))
        
        self.download_all_btn = QPushButton("🚀 Start Download")
        self.download_all_btn.clicked.connect(self.start_batch_download)
        
        bottom_layout.addWidget(self.clear_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.download_all_btn)
        main_layout.addLayout(bottom_layout)

        # Overall Progress
        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setRange(0, 100)
        self.overall_progress_bar.setValue(0)
        main_layout.addWidget(self.overall_progress_bar)

        self.setLayout(main_layout)
        self.setGeometry(200, 200, 800, 600)

    def toggle_timestamps(self, is_checked):
        self.start_input.setEnabled(is_checked)
        self.end_input.setEnabled(is_checked)

    def add_single_url(self):
        """Grabs the single URL and adds it to the table queue."""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a YouTube URL.")
            return

        start_sec, end_sec = "", ""
        if self.time_checkbox.isChecked():
            start_sec = self.start_input.text().strip()
            end_sec = self.end_input.text().strip()
            
            if parse_time(start_sec) is None or parse_time(end_sec) is None:
                QMessageBox.warning(self, "Error", "Invalid timestamps. Use MM:SS.")
                return
            
        self.add_to_table("(Auto-fetch)", url, start_sec, end_sec)
        
        # Clear inputs after adding
        self.url_input.clear()
        self.start_input.clear()
        self.end_input.clear()
        self.time_checkbox.setChecked(False)

    def open_import_dialog(self):
        dialog = ImportDialog(self)
        if dialog.exec():
            text = dialog.get_text()
            self.parse_and_queue(text)

    def parse_and_queue(self, text):
        lines = text.split('\n')
        current_title, current_start, current_end = "", "", ""

        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("http://") or line.startswith("https://") or line.startswith("youtu.be"):
                url = line.split('&')[0] 
                title_to_add = current_title if current_title else "(Auto-fetch)"
                self.add_to_table(title_to_add, url, current_start, current_end)
                current_title, current_start, current_end = "", "", ""
            else:
                match = re.search(r'\((.*?)-(.*?)\)', line)
                if match:
                    current_start = match.group(1).strip()
                    current_end = match.group(2).strip()
                    current_title = line[:match.start()].strip() 
                else:
                    current_title = line
                    current_start, current_end = "", ""

    def add_to_table(self, title, url, start, end):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(title))
        self.table.setItem(row, 1, QTableWidgetItem(url))
        self.table.setItem(row, 2, QTableWidgetItem(start))
        self.table.setItem(row, 3, QTableWidgetItem(end))
        self.table.setItem(row, 4, QTableWidgetItem("Waiting..."))

    def start_batch_download(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Empty Queue", "Please add a URL or import a note first.")
            return

        save_dir = QFileDialog.getExistingDirectory(self, "Select Output Folder", os.path.expanduser("~"))
        if not save_dir:
            return

        queue_items = []
        for row in range(self.table.rowCount()):
            if "Done" in self.table.item(row, 4).text():
                continue
                
            queue_items.append({
                'row': row,
                'title': self.table.item(row, 0).text(),
                'url': self.table.item(row, 1).text(),
                'start': self.table.item(row, 2).text(),
                'end': self.table.item(row, 3).text()
            })

        if not queue_items:
            return

        # Disable UI
        self.add_single_btn.setEnabled(False)
        self.import_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.download_all_btn.setEnabled(False)
        self.overall_progress_bar.setValue(0)

        format_choice = self.format_combo.currentText()
        self.thread = QThread()
        self.worker = BatchDownloadWorker(queue_items, save_dir, format_choice)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.item_progress.connect(self.update_table_status)
        self.worker.overall_progress.connect(self.overall_progress_bar.setValue)
        
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.reset_ui)
        
        self.thread.start()

    def update_table_status(self, row, status_text, percent):
        self.table.setItem(row, 4, QTableWidgetItem(status_text))

    def reset_ui(self):
        self.add_single_btn.setEnabled(True)
        self.import_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        self.download_all_btn.setEnabled(True)
        QMessageBox.information(self, "Success", "Queue processing completed!")

def main():
    app = QApplication(sys.argv)
    window = YouTubeConverterApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()