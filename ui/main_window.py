"""
Main window for Echo Audio Converter.
"""

import os
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QFileDialog,
    QTableWidget, QTableWidgetItem, QProgressBar, QMessageBox,
    QHeaderView, QGroupBox, QSplitter, QStatusBar, QAbstractItemView,
    QTextEdit, QMenu,
)
from PyQt6.QtCore import Qt, QSettings, QTimer
from PyQt6.QtGui import QAction, QKeySequence, QShortcut

from core import (
    FFmpegWrapper, FFmpegUpdater, BatchProcessor, JobStatus,
    get_format_names, get_format_settings, get_quality_options,
    get_default_quality, is_supported_input, SUPPORTED_INPUT_EXTENSIONS,
)
from core.logger import setup_logging, log_buffer
from ui.workers import UpdateWorker, BatchWorker


class MainWindow(QMainWindow):
    APP_NAME = "Echo Audio Converter"
    APP_VERSION = "0.1.0"
    
    def __init__(self):
        super().__init__()
        
        self.app_dir = Path(__file__).parent.parent
        self.ffmpeg_dir = self.app_dir / "ffmpeg"
        
        self.logger = setup_logging(self.app_dir)
        self.logger.info(f"{self.APP_NAME} v{self.APP_VERSION} starting")
        
        self.ffmpeg = FFmpegWrapper(str(self.ffmpeg_dir))
        self.updater = FFmpegUpdater(str(self.ffmpeg_dir))
        self.batch_processor = BatchProcessor()
        
        self.update_worker: Optional[UpdateWorker] = None
        self.batch_worker: Optional[BatchWorker] = None
        
        self.settings = QSettings("EchoStorm", "EchoAudioConverter")
        
        self._setup_ui()
        self._load_settings()
        self._update_ffmpeg_status()
        
        self.setAcceptDrops(True)
        
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self._refresh_log_view)
        self.log_timer.start(500)
    
    def _setup_ui(self):
        self.setWindowTitle(f"{self.APP_NAME} v{self.APP_VERSION}")
        self.setMinimumSize(900, 600)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        
        # FFmpeg status
        ffmpeg_group = QGroupBox("FFmpeg")
        ffmpeg_layout = QHBoxLayout(ffmpeg_group)
        
        self.ffmpeg_status_label = QLabel("Checking...")
        self.ffmpeg_status_label.setMinimumWidth(400)
        ffmpeg_layout.addWidget(self.ffmpeg_status_label)
        ffmpeg_layout.addStretch()
        
        self.update_btn = QPushButton("Check for Updates")
        self.update_btn.clicked.connect(self._on_update_clicked)
        ffmpeg_layout.addWidget(self.update_btn)
        
        self.update_progress = QProgressBar()
        self.update_progress.setMaximumWidth(200)
        self.update_progress.setVisible(False)
        ffmpeg_layout.addWidget(self.update_progress)
        
        main_layout.addWidget(ffmpeg_group)
        
        # Log viewer
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(5, 5, 5, 5)
        
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(100)
        self.log_view.setStyleSheet("QTextEdit { font-family: Consolas, monospace; font-size: 9pt; }")
        log_layout.addWidget(self.log_view)
        
        main_layout.addWidget(log_group)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        
        input_group = QGroupBox("Input")
        input_layout = QVBoxLayout(input_group)
        
        add_files_btn = QPushButton("Add Files...")
        add_files_btn.clicked.connect(self._on_add_files)
        input_layout.addWidget(add_files_btn)
        
        add_folder_btn = QPushButton("Add Folder...")
        add_folder_btn.clicked.connect(self._on_add_folder)
        input_layout.addWidget(add_folder_btn)
        
        drop_label = QLabel("Or drag && drop files here")
        drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_label.setStyleSheet("color: gray; font-style: italic;")
        input_layout.addWidget(drop_label)
        
        settings_layout.addWidget(input_group)
        
        output_group = QGroupBox("Output Settings")
        output_layout = QGridLayout(output_group)
        
        output_layout.addWidget(QLabel("Format:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(get_format_names())
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        output_layout.addWidget(self.format_combo, 0, 1)
        
        output_layout.addWidget(QLabel("Quality:"), 1, 0)
        self.quality_combo = QComboBox()
        output_layout.addWidget(self.quality_combo, 1, 1)
        
        output_layout.addWidget(QLabel("Output Folder:"), 2, 0)
        output_dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Same as input file")
        output_dir_layout.addWidget(self.output_dir_edit)
        browse_btn = QPushButton("...")
        browse_btn.setMaximumWidth(30)
        browse_btn.clicked.connect(self._on_browse_output)
        output_dir_layout.addWidget(browse_btn)
        output_layout.addLayout(output_dir_layout, 2, 1)
        
        settings_layout.addWidget(output_group)
        
        queue_controls = QGroupBox("Queue")
        queue_btn_layout = QVBoxLayout(queue_controls)
        
        clear_completed_btn = QPushButton("Clear Completed")
        clear_completed_btn.clicked.connect(self._on_clear_completed)
        queue_btn_layout.addWidget(clear_completed_btn)
        
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.clicked.connect(self._on_clear_all)
        queue_btn_layout.addWidget(clear_all_btn)
        
        settings_layout.addWidget(queue_controls)
        settings_layout.addStretch()
        
        splitter.addWidget(settings_widget)
        
        # Right panel - queue table
        queue_widget = QWidget()
        queue_layout = QVBoxLayout(queue_widget)
        queue_layout.setContentsMargins(0, 0, 0, 0)
        
        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(5)
        self.queue_table.setHorizontalHeaderLabels(["Input File", "Output Format", "Quality", "Status", "Progress"])
        self.queue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.queue_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.queue_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.queue_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.queue_table.customContextMenuRequested.connect(self._on_queue_context_menu)
        
        delete_shortcut = QShortcut(QKeySequence.StandardKey.Delete, self.queue_table)
        delete_shortcut.activated.connect(self._on_delete_selected)
        
        queue_layout.addWidget(self.queue_table)
        splitter.addWidget(queue_widget)
        splitter.setSizes([300, 600])
        
        main_layout.addWidget(splitter)
        
        # Bottom bar
        bottom_layout = QHBoxLayout()
        
        self.queue_summary_label = QLabel("Queue: 0 files")
        bottom_layout.addWidget(self.queue_summary_label)
        bottom_layout.addStretch()
        
        self.overall_progress = QProgressBar()
        self.overall_progress.setMinimumWidth(200)
        self.overall_progress.setVisible(False)
        bottom_layout.addWidget(self.overall_progress)
        
        self.convert_btn = QPushButton("Convert All")
        self.convert_btn.setMinimumWidth(120)
        self.convert_btn.clicked.connect(self._on_convert_clicked)
        self.convert_btn.setEnabled(False)
        bottom_layout.addWidget(self.convert_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        self.cancel_btn.setVisible(False)
        bottom_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(bottom_layout)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self._on_format_changed(self.format_combo.currentText())
    
    def _load_settings(self):
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        last_format = self.settings.value("last_format")
        if last_format and last_format in get_format_names():
            self.format_combo.setCurrentText(last_format)
        last_output = self.settings.value("last_output_dir")
        if last_output:
            self.output_dir_edit.setText(last_output)
    
    def _save_settings(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("last_format", self.format_combo.currentText())
        self.settings.setValue("last_output_dir", self.output_dir_edit.text())
    
    def closeEvent(self, event):
        self._save_settings()
        if self.batch_worker and self.batch_worker.isRunning():
            reply = QMessageBox.question(self, "Conversion in Progress",
                "A conversion is in progress. Quit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        event.accept()
    
    def _update_ffmpeg_status(self):
        if self.ffmpeg.is_available():
            version = self.ffmpeg.get_version()
            if len(version) > 60:
                version = version[:60] + "..."
            self.ffmpeg_status_label.setText(f"✓ {version}")
            self.ffmpeg_status_label.setStyleSheet("color: green;")
            self.update_btn.setText("Check for Updates")
        else:
            self.ffmpeg_status_label.setText("✗ FFmpeg not found")
            self.ffmpeg_status_label.setStyleSheet("color: red;")
            self.update_btn.setText("Download FFmpeg")
    
    def _on_update_clicked(self):
        try:
            available, latest, installed = self.updater.is_update_available()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not check for updates: {e}")
            return
        
        if not available and installed:
            QMessageBox.information(self, "Up to Date", f"FFmpeg {installed} is the latest.")
            return
        
        msg = f"Update available: {installed} → {latest}" if installed else f"FFmpeg {latest} will be downloaded."
        reply = QMessageBox.question(self, "Download FFmpeg", f"{msg}\n\nProceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.update_btn.setEnabled(False)
        self.update_progress.setVisible(True)
        self.update_progress.setValue(0)
        
        self.update_worker = UpdateWorker(self.updater, self)
        self.update_worker.progress.connect(self._on_update_progress)
        self.update_worker.finished.connect(self._on_update_finished)
        self.update_worker.start()
    
    def _on_update_progress(self, message: str, progress: float):
        self.update_progress.setValue(int(progress * 100))
        self.status_bar.showMessage(message)
    
    def _on_update_finished(self, success: bool, message: str):
        self.update_btn.setEnabled(True)
        self.update_progress.setVisible(False)
        if success:
            self.ffmpeg.clear_cache()
            self._update_ffmpeg_status()
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Update Failed", message)
        self.status_bar.clearMessage()
    
    def _on_add_files(self):
        extensions = " ".join(f"*{ext}" for ext in sorted(SUPPORTED_INPUT_EXTENSIONS))
        files, _ = QFileDialog.getOpenFileNames(self, "Select Audio Files", "", f"Audio Files ({extensions});;All Files (*)")
        if files:
            self._add_files_to_queue(files)
    
    def _on_add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            files = [str(f) for f in Path(folder).iterdir() if f.is_file() and is_supported_input(str(f))]
            if files:
                self._add_files_to_queue(files)
            else:
                QMessageBox.information(self, "No Audio Files", "No supported audio files found.")
    
    def _add_files_to_queue(self, files: list):
        format_name = self.format_combo.currentText()
        quality = self.quality_combo.currentText()
        fmt_settings = get_format_settings(format_name)
        extension = fmt_settings["extension"]
        output_dir = self.output_dir_edit.text().strip()
        
        added = 0
        skipped = 0
        
        for filepath in files:
            file_output_dir = output_dir if output_dir else str(Path(filepath).parent)
            job = self.batch_processor.add_job(filepath, file_output_dir, format_name, quality, extension)
            if job:
                added += 1
            else:
                skipped += 1
        
        self._refresh_queue_table()
        
        if skipped > 0:
            self.status_bar.showMessage(f"Added {added}, skipped {skipped} duplicate(s)", 3000)
        else:
            self.status_bar.showMessage(f"Added {added} file(s)", 3000)
        self.logger.info(f"Added {added} files, skipped {skipped} duplicates")
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path) and is_supported_input(path):
                files.append(path)
            elif os.path.isdir(path):
                for f in Path(path).iterdir():
                    if f.is_file() and is_supported_input(str(f)):
                        files.append(str(f))
        if files:
            self._add_files_to_queue(files)
    
    def _on_format_changed(self, format_name: str):
        self.quality_combo.clear()
        options = get_quality_options(format_name)
        self.quality_combo.addItems(options)
        default = get_default_quality(format_name)
        if default in options:
            self.quality_combo.setCurrentText(default)
    
    def _on_browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_dir_edit.setText(folder)
    
    def _refresh_queue_table(self):
        self.queue_table.setRowCount(len(self.batch_processor.jobs))
        
        for row, job in enumerate(self.batch_processor.jobs):
            self.queue_table.setItem(row, 0, QTableWidgetItem(job.input_filename))
            self.queue_table.setItem(row, 1, QTableWidgetItem(job.format_name))
            self.queue_table.setItem(row, 2, QTableWidgetItem(job.quality_option))
            
            status_item = QTableWidgetItem(job.status.value.title())
            if job.status == JobStatus.COMPLETE:
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif job.status == JobStatus.FAILED:
                status_item.setForeground(Qt.GlobalColor.red)
            elif job.status == JobStatus.CONVERTING:
                status_item.setForeground(Qt.GlobalColor.blue)
            self.queue_table.setItem(row, 3, status_item)
            
            progress_text = f"{int(job.progress * 100)}%" if job.progress > 0 else ""
            self.queue_table.setItem(row, 4, QTableWidgetItem(progress_text))
        
        summary = self.batch_processor.get_summary()
        self.queue_summary_label.setText(
            f"Queue: {summary['pending']} pending, {summary['complete']} complete, {summary['failed']} failed"
        )
        
        can_convert = summary['pending'] > 0 and self.ffmpeg.is_available() and not self.batch_processor.is_processing
        self.convert_btn.setEnabled(can_convert)
    
    def _on_clear_completed(self):
        self.batch_processor.clear_completed()
        self._refresh_queue_table()
    
    def _on_clear_all(self):
        if self.batch_processor.is_processing:
            QMessageBox.warning(self, "Cannot Clear", "Cannot clear while converting.")
            return
        self.batch_processor.clear_all()
        self._refresh_queue_table()
    
    def _on_convert_clicked(self):
        if not self.ffmpeg.is_available():
            QMessageBox.warning(self, "FFmpeg Not Found", "Please download FFmpeg first.")
            return
        
        pending = self.batch_processor.pending_count
        if pending == 0:
            return
        
        self.convert_btn.setEnabled(False)
        self.cancel_btn.setVisible(True)
        self.overall_progress.setVisible(True)
        self.overall_progress.setValue(0)
        
        self.batch_worker = BatchWorker(self.ffmpeg, self.batch_processor, self)
        self.batch_worker.job_started.connect(self._on_job_started)
        self.batch_worker.job_progress.connect(self._on_job_progress)
        self.batch_worker.job_finished.connect(self._on_job_finished)
        self.batch_worker.batch_finished.connect(self._on_batch_finished)
        self.batch_worker.start()
        
        self.status_bar.showMessage(f"Converting {pending} file(s)...")
    
    def _on_cancel_clicked(self):
        if self.batch_worker:
            self.batch_worker.request_cancel()
            self.status_bar.showMessage("Cancelling...")
    
    def _on_job_started(self, job_id: str):
        self._refresh_queue_table()
    
    def _on_job_progress(self, job_id: str, progress: float):
        job = self.batch_processor.get_job_by_id(job_id)
        if job:
            job.progress = progress
        
        jobs = self.batch_processor.jobs
        if jobs:
            total = sum(j.progress for j in jobs if j.status in (JobStatus.CONVERTING, JobStatus.COMPLETE))
            total += sum(1.0 for j in jobs if j.status == JobStatus.COMPLETE)
            self.overall_progress.setValue(int((total / len(jobs)) * 100))
        
        self._refresh_queue_table()
    
    def _on_job_finished(self, job_id: str, success: bool, message: str):
        self._refresh_queue_table()
    
    def _on_batch_finished(self, completed: int, failed: int, cancelled: int):
        self.convert_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
        self.overall_progress.setVisible(False)
        self._refresh_queue_table()
        
        parts = []
        if completed > 0:
            parts.append(f"{completed} completed")
        if failed > 0:
            parts.append(f"{failed} failed")
        if cancelled > 0:
            parts.append(f"{cancelled} cancelled")
        
        self.status_bar.showMessage(", ".join(parts) if parts else "No files processed", 5000)
        
        if failed > 0:
            QMessageBox.warning(self, "Some Conversions Failed", f"{failed} file(s) failed. Check queue for details.")
    
    def _refresh_log_view(self):
        logs = log_buffer.get_logs()
        if logs:
            current = self.log_view.toPlainText()
            new_text = "\n".join(logs)
            if current != new_text:
                self.log_view.setPlainText(new_text)
                self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())
    
    def _on_queue_context_menu(self, position):
        selected = self.queue_table.selectionModel().selectedRows()
        if not selected:
            return
        menu = QMenu(self)
        delete_action = QAction("Remove from Queue", self)
        delete_action.triggered.connect(self._on_delete_selected)
        menu.addAction(delete_action)
        menu.exec(self.queue_table.viewport().mapToGlobal(position))
    
    def _on_delete_selected(self):
        selected = self.queue_table.selectionModel().selectedRows()
        if not selected:
            return
        
        rows = sorted([idx.row() for idx in selected], reverse=True)
        removed = 0
        for row in rows:
            if row < len(self.batch_processor.jobs):
                job = self.batch_processor.jobs[row]
                if job.status == JobStatus.PENDING:
                    self.batch_processor.jobs.pop(row)
                    removed += 1
        
        if removed > 0:
            self._refresh_queue_table()
            self.status_bar.showMessage(f"Removed {removed} file(s)", 3000)
