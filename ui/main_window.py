"""
Main window for Echo Audio Converter.
Industrial theme inspired by the banner.
"""

import os
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QFileDialog,
    QTableWidget, QTableWidgetItem, QProgressBar, QMessageBox,
    QHeaderView, QFrame, QStatusBar, QAbstractItemView,
    QTextEdit, QMenu, QSizePolicy, QCheckBox, QSpinBox,
)
from PyQt6.QtCore import Qt, QSettings, QTimer, QUrl
from PyQt6.QtGui import QAction, QKeySequence, QShortcut, QColor, QPainter, QPen, QDesktopServices

from core import (
    FFmpegWrapper, FFmpegUpdater, BatchProcessor, JobStatus,
    get_format_names, get_format_settings, get_quality_options,
    get_default_quality, is_supported_input, SUPPORTED_INPUT_EXTENSIONS,
)
from core.logger import setup_logging, log_buffer
from ui.workers import UpdateWorker, BatchWorker, AnalyzeWorker, CheckUpdateWorker


class ArrowComboBox(QComboBox):
    """ComboBox with custom Unicode arrow."""
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def paintEvent(self, event):
        super().paintEvent(event)
        # Draw arrow manually
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor("#7cb342"))
        
        # Position arrow on right side
        arrow = "▼"
        font = self.font()
        font.setPointSize(8)
        painter.setFont(font)
        
        rect = self.rect()
        arrow_x = rect.width() - 18
        arrow_y = rect.height() // 2 + 4
        painter.drawText(arrow_x, arrow_y, arrow)
        painter.end()


# Industrial color scheme
STYLE_SHEET = """
QMainWindow, QWidget {
    background-color: #1a1a1a;
    color: #c0c0c0;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
}

QGroupBox {
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: bold;
    color: #7cb342;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #7cb342;
}

QPushButton {
    background-color: #2d2d2d;
    border: 1px solid #4a4a4a;
    border-radius: 3px;
    padding: 6px 14px;
    color: #c0c0c0;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #3d3d3d;
    border-color: #7cb342;
}

QPushButton:pressed {
    background-color: #4a4a4a;
}

QPushButton:disabled {
    background-color: #252525;
    color: #606060;
    border-color: #353535;
}

QPushButton#convertBtn {
    background-color: #2e4a1e;
    border-color: #7cb342;
    color: #7cb342;
    font-weight: bold;
    padding: 8px 20px;
}

QPushButton#convertBtn:hover {
    background-color: #3e5a2e;
}

QPushButton#convertBtn:disabled {
    background-color: #252525;
    border-color: #404040;
    color: #505050;
}

QPushButton#cancelBtn {
    background-color: #4a2020;
    border-color: #a04040;
    color: #d08080;
}

QPushButton#cancelBtn:hover {
    background-color: #5a2828;
}

QComboBox {
    background-color: #2d2d2d;
    border: 1px solid #4a4a4a;
    border-radius: 3px;
    padding: 5px 10px;
    padding-right: 25px;
    color: #c0c0c0;
    min-height: 22px;
}

QComboBox:hover {
    border-color: #7cb342;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
    subcontrol-origin: padding;
    subcontrol-position: right center;
}

QComboBox::down-arrow {
    image: none;
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    border: 1px solid #4a4a4a;
    selection-background-color: #3e5a2e;
    color: #c0c0c0;
}

QLineEdit {
    background-color: #252525;
    border: 1px solid #4a4a4a;
    border-radius: 3px;
    padding: 5px 8px;
    color: #c0c0c0;
    min-height: 22px;
}

QLineEdit:focus {
    border-color: #7cb342;
}

QLineEdit:disabled {
    background-color: #1a1a1a;
    border-color: #353535;
    color: #505050;
}

QTableWidget {
    background-color: #1e1e1e;
    alternate-background-color: #242424;
    border: 1px solid #3a3a3a;
    gridline-color: #2a2a2a;
    color: #c0c0c0;
    selection-background-color: #3e5a2e;
}

QTableWidget::item {
    padding: 4px;
    border: none;
}

QTableWidget::item:selected {
    background-color: #3e5a2e;
}

QHeaderView::section {
    background-color: #2a2a2a;
    color: #7cb342;
    padding: 6px;
    border: none;
    border-bottom: 2px solid #7cb342;
    font-weight: bold;
}

QProgressBar {
    background-color: #252525;
    border: 1px solid #3a3a3a;
    border-radius: 3px;
    height: 18px;
    text-align: center;
    color: #c0c0c0;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4a7a2a, stop:1 #7cb342);
    border-radius: 2px;
}

QTextEdit {
    background-color: #151515;
    border: 1px solid #2a2a2a;
    color: #808080;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 9pt;
}

QStatusBar {
    background-color: #1a1a1a;
    border-top: 1px solid #2a2a2a;
    color: #7cb342;
}

QLabel {
    color: #a0a0a0;
}

QLabel#titleLabel {
    color: #7cb342;
    font-size: 11pt;
    font-weight: bold;
}

QLabel#ffmpegStatus {
    color: #7cb342;
    font-size: 9pt;
}

QLabel#ffmpegStatusBad {
    color: #c04040;
    font-size: 9pt;
}

QFrame#separator {
    background-color: #3a3a3a;
    max-height: 1px;
}

QSplitter::handle {
    background-color: #2a2a2a;
}

QSplitter::handle:horizontal {
    width: 3px;
}

QScrollBar:vertical {
    background-color: #1a1a1a;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #3a3a3a;
    border-radius: 4px;
    min-height: 30px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4a4a4a;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QMenu {
    background-color: #2d2d2d;
    border: 1px solid #4a4a4a;
    color: #c0c0c0;
}

QMenu::item:selected {
    background-color: #3e5a2e;
}

QCheckBox {
    color: #a0a0a0;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #4a4a4a;
    border-radius: 2px;
    background-color: #252525;
}

QCheckBox::indicator:hover {
    border-color: #7cb342;
}

QCheckBox::indicator:checked {
    background-color: #7cb342;
    border-color: #7cb342;
}

QCheckBox:disabled {
    color: #505050;
}

QCheckBox::indicator:disabled {
    background-color: #1a1a1a;
    border-color: #353535;
}

QWidget#leftPanel {
    background-color: #161616;
    border-right: 1px solid #252525;
}

QPushButton#donateBtn {
    background: transparent;
    border: none;
    color: #7cb342;
    font-size: 8pt;
    padding: 0px 10px;
    min-height: 0;
    letter-spacing: 1px;
}

QPushButton#donateBtn:hover {
    color: #9dd35a;
}
"""


class MainBackground(QWidget):
    """Central widget with a subtle vertical stripe texture matching the banner aesthetic."""
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        pen = QPen(QColor(255, 255, 255, 6))
        pen.setWidth(1)
        painter.setPen(pen)
        x = 1
        while x < self.width():
            painter.drawLine(x, 0, x, self.height())
            x += 4
        painter.end()


class MainWindow(QMainWindow):
    APP_NAME = "Echo Audio Converter"
    APP_VERSION = "0.6.1"
    
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
        self.check_worker: Optional[CheckUpdateWorker] = None
        self.batch_worker: Optional[BatchWorker] = None
        self.analyze_worker: Optional[AnalyzeWorker] = None
        self._last_log_tail: Optional[str] = None
        
        self.settings = QSettings("EchoStorm", "EchoAudioConverter")
        
        self.setStyleSheet(STYLE_SHEET)
        self._setup_ui()
        self._load_settings()
        self._update_ffmpeg_status()

        # Auto-download FFmpeg on first run if not present
        self._maybe_auto_download_ffmpeg()
        
        self.setAcceptDrops(True)
        
        self.log_timer = QTimer(self)
        self.log_timer.timeout.connect(self._refresh_log_view)
        self.log_timer.start(500)
    
    def _setup_ui(self):
        self.setWindowTitle(f"{self.APP_NAME} v{self.APP_VERSION}")
        self.setMinimumSize(950, 700)
        
        central = MainBackground()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # === Header Banner (Industrial Style) ===
        header_container = QWidget()
        header_container.setFixedHeight(70)
        header_container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a2a2a,
                    stop:0.3 #1f1f1f,
                    stop:0.7 #1a1a1a,
                    stop:1 #151515);
                border-bottom: 2px solid #3a3a3a;
            }
        """)
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(15)
        
        # Left decorative element
        left_deco = QLabel("◢◤◢◤")
        left_deco.setStyleSheet("color: #4a4a4a; font-size: 16pt; border: none; background: transparent;")
        header_layout.addWidget(left_deco)
        
        # Left accent bar
        left_bar = QFrame()
        left_bar.setFixedHeight(3)
        left_bar.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2a2a2a, stop:1 #7cb342); border: none;")
        left_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        header_layout.addWidget(left_bar)
        
        # Title
        title_label = QLabel("ECHO AUDIO CONVERTER")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            color: #7cb342;
            font-size: 22pt;
            font-weight: bold;
            font-family: "Segoe UI", "Arial Black", sans-serif;
            letter-spacing: 3px;
            background: transparent;
            border: none;
            padding: 0 15px;
        """)
        header_layout.addWidget(title_label)
        
        # Right accent bar
        right_bar = QFrame()
        right_bar.setFixedHeight(3)
        right_bar.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7cb342, stop:1 #2a2a2a); border: none;")
        right_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        header_layout.addWidget(right_bar)
        
        # Right decorative element
        right_deco = QLabel("◥◣◥◣")
        right_deco.setStyleSheet("color: #4a4a4a; font-size: 16pt; border: none; background: transparent;")
        header_layout.addWidget(right_deco)
        
        main_layout.addWidget(header_container)
        
        # Content wrapper with margins
        content_wrapper = QWidget()
        content_wrapper_layout = QVBoxLayout(content_wrapper)
        content_wrapper_layout.setSpacing(8)
        content_wrapper_layout.setContentsMargins(12, 8, 12, 12)
        
        # === Top bar: FFmpeg status (compact) ===
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)
        
        self.ffmpeg_status_label = QLabel("Checking FFmpeg...")
        self.ffmpeg_status_label.setObjectName("ffmpegStatus")
        top_bar.addWidget(self.ffmpeg_status_label)
        
        self.update_progress = QProgressBar()
        self.update_progress.setFixedWidth(150)
        self.update_progress.setFixedHeight(16)
        self.update_progress.setVisible(False)
        top_bar.addWidget(self.update_progress)
        
        top_bar.addStretch()
        
        self.update_btn = QPushButton("Check for Updates")
        self.update_btn.setFixedHeight(26)
        self.update_btn.clicked.connect(self._on_update_clicked)
        top_bar.addWidget(self.update_btn)
        
        content_wrapper_layout.addLayout(top_bar)
        
        # Separator
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        content_wrapper_layout.addWidget(sep)
        
        # === Main content area ===
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)
        
        # --- Left panel: Controls ---
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        
        # Input section
        input_label = QLabel("INPUT")
        input_label.setObjectName("titleLabel")
        left_panel.addWidget(input_label)
        
        add_files_btn = QPushButton("Add Files...")
        add_files_btn.clicked.connect(self._on_add_files)
        left_panel.addWidget(add_files_btn)
        
        add_folder_btn = QPushButton("Add Folder...")
        add_folder_btn.clicked.connect(self._on_add_folder)
        left_panel.addWidget(add_folder_btn)
        
        drop_label = QLabel("or drag && drop")
        drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_label.setStyleSheet("color: #505050; font-style: italic; font-size: 9pt;")
        left_panel.addWidget(drop_label)
        
        left_panel.addSpacing(10)
        
        # Options section
        options_label = QLabel("OPTIONS")
        options_label.setObjectName("titleLabel")
        left_panel.addWidget(options_label)
        
        self.recursive_checkbox = QCheckBox("Include subdirectories")
        self.recursive_checkbox.setToolTip("When adding a folder, also scan all subdirectories for audio files")
        left_panel.addWidget(self.recursive_checkbox)
        
        self.delete_source_checkbox = QCheckBox("Delete source after conversion")
        self.delete_source_checkbox.setToolTip("Delete the original file after successful conversion (irreversible!)")
        self.delete_source_checkbox.setStyleSheet("QCheckBox { color: #c08080; }")
        left_panel.addWidget(self.delete_source_checkbox)
        
        left_panel.addSpacing(10)
        
        # Output section
        output_label = QLabel("OUTPUT")
        output_label.setObjectName("titleLabel")
        left_panel.addWidget(output_label)
        
        # Format row
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.format_combo = ArrowComboBox()
        self.format_combo.addItems(get_format_names())
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        self.format_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        format_layout.addWidget(self.format_combo)
        left_panel.addLayout(format_layout)
        
        # Quality row
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality:"))
        self.quality_combo = ArrowComboBox()
        self.quality_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.quality_combo.currentTextChanged.connect(self._on_quality_changed)
        quality_layout.addWidget(self.quality_combo)
        left_panel.addLayout(quality_layout)

        # Sample rate row
        sample_rate_layout = QHBoxLayout()
        sample_rate_layout.addWidget(QLabel("Sample rate:"))
        self.sample_rate_combo = ArrowComboBox()
        self.sample_rate_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.sample_rate_combo.addItems([
            "Source (keep)",
            "44.1 kHz",
            "48 kHz",
            "88.2 kHz",
            "96 kHz",
        ])
        self.sample_rate_combo.setToolTip(
            "Override the output sample rate.\n"
            "'Source (keep)' passes the original rate through unchanged.\n"
            "Note: Opus always encodes at 48 kHz regardless of this setting."
        )
        self.sample_rate_combo.currentTextChanged.connect(self._on_sample_rate_changed)
        sample_rate_layout.addWidget(self.sample_rate_combo)
        left_panel.addLayout(sample_rate_layout)
        
        # Loudness normalization row
        loudness_layout = QHBoxLayout()
        loudness_layout.addWidget(QLabel("Loudness:"))
        self.loudness_combo = ArrowComboBox()
        self.loudness_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.loudness_combo.addItems([
            "Off",
            "-14 LUFS (Streaming)",
            "-16 LUFS (Apple)",
            "-23 LUFS (Broadcast)",
        ])
        self.loudness_combo.setToolTip("Two-pass loudness normalization (analyzes first, then converts)")
        self.loudness_combo.currentTextChanged.connect(self._on_loudness_changed)
        loudness_layout.addWidget(self.loudness_combo)
        left_panel.addLayout(loudness_layout)
        
        # Output folder row
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel("Folder:")
        folder_layout.addWidget(self.folder_label)
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Same as source")
        folder_layout.addWidget(self.output_dir_edit)
        self.browse_btn = QPushButton("...")
        self.browse_btn.setFixedWidth(30)
        self.browse_btn.clicked.connect(self._on_browse_output)
        folder_layout.addWidget(self.browse_btn)
        left_panel.addLayout(folder_layout)
        
        # Save to original directory checkbox
        self.save_to_source_checkbox = QCheckBox("Save to original directory")
        self.save_to_source_checkbox.setToolTip("Save converted files alongside the originals (useful for batch subdirectory conversions)")
        self.save_to_source_checkbox.stateChanged.connect(self._on_save_to_source_changed)
        left_panel.addWidget(self.save_to_source_checkbox)
        
        left_panel.addSpacing(10)
        
        # Queue section
        queue_label = QLabel("QUEUE")
        queue_label.setObjectName("titleLabel")
        left_panel.addWidget(queue_label)

        # Parallel workers spinbox
        workers_layout = QHBoxLayout()
        workers_layout.addWidget(QLabel("Workers:"))
        self.workers_spin = QSpinBox()
        self.workers_spin.setMinimum(1)
        self.workers_spin.setMaximum(min(os.cpu_count() or 4, 8))
        self.workers_spin.setValue(1)
        self.workers_spin.setToolTip(
            "Number of files to convert simultaneously.\n"
            "1 = sequential (safest, uses least CPU).\n"
            "2–4 = faster on large queues; each worker\n"
            "runs a separate FFmpeg process."
        )
        workers_layout.addWidget(self.workers_spin)
        workers_layout.addStretch()
        left_panel.addLayout(workers_layout)
        
        self.analyze_btn = QPushButton("Analyze LUFS")
        self.analyze_btn.setToolTip("Measure loudness (LUFS) of queued files")
        self.analyze_btn.clicked.connect(self._on_analyze_clicked)
        left_panel.addWidget(self.analyze_btn)
        
        clear_completed_btn = QPushButton("Clear Completed")
        clear_completed_btn.clicked.connect(self._on_clear_completed)
        left_panel.addWidget(clear_completed_btn)
        
        clear_all_btn = QPushButton("Clear All")
        clear_all_btn.clicked.connect(self._on_clear_all)
        left_panel.addWidget(clear_all_btn)
        
        left_panel.addStretch()
        
        # Left panel container
        left_widget = QWidget()
        left_widget.setObjectName("leftPanel")
        left_widget.setLayout(left_panel)
        left_widget.setFixedWidth(295)
        content_layout.addWidget(left_widget)
        
        # --- Right panel: Queue table ---
        right_panel = QVBoxLayout()
        right_panel.setSpacing(8)
        
        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(12)
        self.queue_table.setHorizontalHeaderLabels([
            "Src", "Bitrate", "kHz", "LUFS", "Time", "File", "Output", "→kbps", "→kHz", "→LUFS", "Status", "%"
        ])
        # Column resize modes
        self.queue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Src
        self.queue_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Bitrate
        self.queue_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # kHz
        self.queue_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # LUFS
        self.queue_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Time
        self.queue_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)           # File
        self.queue_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Output
        self.queue_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # Quality
        self.queue_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)  # →kHz
        self.queue_table.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)  # →kbps
        self.queue_table.horizontalHeader().setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents) # Status
        self.queue_table.horizontalHeader().setSectionResizeMode(11, QHeaderView.ResizeMode.ResizeToContents) # %
        self.queue_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.queue_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.queue_table.setAlternatingRowColors(True)
        self.queue_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.queue_table.customContextMenuRequested.connect(self._on_queue_context_menu)
        self.queue_table.verticalHeader().setVisible(False)
        
        delete_shortcut = QShortcut(QKeySequence.StandardKey.Delete, self.queue_table)
        delete_shortcut.activated.connect(self._on_delete_selected)
        
        right_panel.addWidget(self.queue_table)
        
        # Log viewer (compact, at bottom of queue)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(80)
        self.log_view.setPlaceholderText("Log output...")
        right_panel.addWidget(self.log_view)
        
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        content_layout.addWidget(right_widget)
        
        content_wrapper_layout.addLayout(content_layout)
        
        # === Bottom bar: Actions ===
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(12)
        
        self.queue_summary_label = QLabel("Ready")
        self.queue_summary_label.setStyleSheet("color: #7cb342;")
        bottom_bar.addWidget(self.queue_summary_label)
        
        bottom_bar.addStretch()
        
        self.overall_progress = QProgressBar()
        self.overall_progress.setFixedWidth(200)
        self.overall_progress.setVisible(False)
        bottom_bar.addWidget(self.overall_progress)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        self.cancel_btn.setVisible(False)
        bottom_bar.addWidget(self.cancel_btn)
        
        self.convert_btn = QPushButton("Convert All")
        self.convert_btn.setObjectName("convertBtn")
        self.convert_btn.clicked.connect(self._on_convert_clicked)
        self.convert_btn.setEnabled(False)
        bottom_bar.addWidget(self.convert_btn)
        
        # Separator above action bar
        action_sep = QFrame()
        action_sep.setObjectName("separator")
        action_sep.setFrameShape(QFrame.Shape.HLine)
        content_wrapper_layout.addWidget(action_sep)
        content_wrapper_layout.addLayout(bottom_bar)
        
        # Add content wrapper to main layout
        main_layout.addWidget(content_wrapper)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Ko-fi donate button — permanent widget, far right of status bar
        donate_btn = QPushButton("donate  ♥  ko-fi")
        donate_btn.setObjectName("donateBtn")
        donate_btn.setFlat(True)
        donate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        donate_btn.setToolTip("Support development on Ko-fi")
        donate_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://ko-fi.com/xechostormx/tip"))
        )
        self.status_bar.addPermanentWidget(donate_btn)

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
        
        # Load loudness setting
        last_loudness = self.settings.value("loudness_setting", "Off")
        idx = self.loudness_combo.findText(last_loudness)
        if idx >= 0:
            self.loudness_combo.setCurrentIndex(idx)

        # Load sample rate setting
        last_sample_rate = self.settings.value("sample_rate_setting", "Source (keep)")
        idx = self.sample_rate_combo.findText(last_sample_rate)
        if idx >= 0:
            self.sample_rate_combo.setCurrentIndex(idx)
        
        # Load checkbox states (default to False for safety)
        recursive = self.settings.value("recursive_subdirs", False, type=bool)
        self.recursive_checkbox.setChecked(recursive)
        
        save_to_source = self.settings.value("save_to_source", False, type=bool)
        self.save_to_source_checkbox.setChecked(save_to_source)
        # Trigger UI update to disable/enable folder controls
        self._on_save_to_source_changed(save_to_source)

        # Worker count (default 1 = sequential, same as old behaviour)
        worker_count = self.settings.value("worker_count", 1, type=int)
        worker_count = max(1, min(worker_count, self.workers_spin.maximum()))
        self.workers_spin.setValue(worker_count)
        
        # Never auto-restore delete_source - too dangerous, user must explicitly enable each session
        self.delete_source_checkbox.setChecked(False)
    
    def _save_settings(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("last_format", self.format_combo.currentText())
        self.settings.setValue("last_output_dir", self.output_dir_edit.text())
        self.settings.setValue("loudness_setting", self.loudness_combo.currentText())
        self.settings.setValue("sample_rate_setting", self.sample_rate_combo.currentText())
        self.settings.setValue("recursive_subdirs", self.recursive_checkbox.isChecked())
        self.settings.setValue("save_to_source", self.save_to_source_checkbox.isChecked())
        self.settings.setValue("worker_count", self.workers_spin.value())
        # Note: delete_source is intentionally NOT saved - must be enabled manually each session
    
    def closeEvent(self, event):
        self._save_settings()
        if self.analyze_worker and self.analyze_worker.isRunning():
            reply = QMessageBox.question(self, "Analysis in Progress",
                "LUFS analysis is running. Quit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            self.analyze_worker.request_cancel()
            self.analyze_worker.wait(3000)
        if self.batch_worker and self.batch_worker.isRunning():
            reply = QMessageBox.question(self, "Conversion in Progress",
                "A conversion is in progress. Quit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            self.batch_worker.request_cancel()
            self.batch_worker.wait(5000)
        event.accept()
    
    def _update_ffmpeg_status(self):
        if self.ffmpeg.is_available():
            version = self.ffmpeg.get_version()
            # Extract just version number
            if "version" in version:
                parts = version.split()
                for i, p in enumerate(parts):
                    if p == "version" and i + 1 < len(parts):
                        version = f"FFmpeg {parts[i+1]}"
                        break
            if len(version) > 40:
                version = version[:40] + "..."
            self.ffmpeg_status_label.setText(f"✓ {version}")
            self.ffmpeg_status_label.setObjectName("ffmpegStatus")
            self.update_btn.setText("Update")
        else:
            self.ffmpeg_status_label.setText("✗ FFmpeg not found")
            self.ffmpeg_status_label.setObjectName("ffmpegStatusBad")
            self.update_btn.setText("Download")
        # Refresh style
        self.ffmpeg_status_label.setStyle(self.ffmpeg_status_label.style())
    
    def _on_update_clicked(self):
        # Disable immediately to prevent double-invocation during the network check.
        # The actual version fetch happens in a background thread so the UI stays
        # responsive — a blocking requests.get on the main thread would freeze
        # the window for up to 30 seconds on a slow connection.
        self.update_btn.setEnabled(False)
        self.status_bar.showMessage("Checking for updates...")

        self.check_worker = CheckUpdateWorker(self.updater, self)
        self.check_worker.result.connect(self._on_update_check_result)
        self.check_worker.error.connect(self._on_update_check_error)
        self.check_worker.start()

    def _on_update_check_result(self, available: bool, latest: str, installed):
        self.check_worker = None
        self.status_bar.clearMessage()

        if not available and installed:
            self.update_btn.setEnabled(True)
            QMessageBox.information(self, "Up to Date", f"FFmpeg {installed} is the latest.")
            return

        msg = f"Update: {installed} → {latest}" if installed else f"Download FFmpeg {latest}?"
        reply = QMessageBox.question(self, "FFmpeg", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply != QMessageBox.StandardButton.Yes:
            self.update_btn.setEnabled(True)
            return

        self.update_progress.setVisible(True)
        self.update_progress.setValue(0)

        self.update_worker = UpdateWorker(self.updater, self)
        self.update_worker.progress.connect(self._on_update_progress)
        self.update_worker.finished.connect(self._on_update_finished)
        self.update_worker.start()

    def _on_update_check_error(self, message: str):
        self.check_worker = None
        self.update_btn.setEnabled(True)
        self.status_bar.clearMessage()
        QMessageBox.warning(self, "Error", f"Could not check for updates: {message}")
    
    def _on_update_progress(self, message: str, progress: float):
        self.update_progress.setValue(int(progress * 100))
        self.status_bar.showMessage(message)
    
    def _on_update_finished(self, success: bool, message: str):
        self.update_worker = None
        self.update_btn.setEnabled(True)
        self.update_progress.setVisible(False)
        if success:
            self.ffmpeg.clear_cache()
            self._update_ffmpeg_status()
            self.status_bar.showMessage("FFmpeg updated successfully", 3000)
        else:
            QMessageBox.warning(self, "Update Failed", message)
            self.status_bar.clearMessage()

    def _maybe_auto_download_ffmpeg(self):
        """Auto-download FFmpeg on first run if not present — no user action required."""
        if self.ffmpeg.is_available():
            return

        self.logger.info("FFmpeg not found — starting automatic first-run download")
        self.status_bar.showMessage("First run: downloading FFmpeg automatically...")

        self.update_btn.setEnabled(False)
        self.update_progress.setVisible(True)
        self.update_progress.setValue(0)

        self.update_worker = UpdateWorker(self.updater, self)
        self.update_worker.progress.connect(self._on_update_progress)
        self.update_worker.finished.connect(self._on_auto_download_finished)
        self.update_worker.start()

    def _on_auto_download_finished(self, success: bool, message: str):
        """Called after the automatic first-run FFmpeg download completes."""
        self.update_worker = None
        self.update_btn.setEnabled(True)
        self.update_progress.setVisible(False)
        if success:
            self.ffmpeg.clear_cache()
            self._update_ffmpeg_status()
            self.status_bar.showMessage("FFmpeg downloaded — ready to convert", 4000)
            self.logger.info("First-run FFmpeg download complete")
        else:
            self._update_ffmpeg_status()
            QMessageBox.warning(
                self,
                "FFmpeg Download Failed",
                f"Could not download FFmpeg automatically:\n\n{message}\n\n"
                "You can try again using the Download button at the top."
            )
    
    def _on_add_files(self):
        extensions = " ".join(f"*{ext}" for ext in sorted(SUPPORTED_INPUT_EXTENSIONS))
        files, _ = QFileDialog.getOpenFileNames(self, "Select Audio Files", "", f"Audio Files ({extensions});;All Files (*)")
        if files:
            self._add_files_to_queue(files)
    
    def _on_add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            base_path = Path(folder)
            recursive = self.recursive_checkbox.isChecked()
            
            if recursive:
                # Recursive: walk all subdirectories
                files = [
                    str(f) for f in base_path.rglob("*")
                    if f.is_file() and is_supported_input(str(f))
                ]
            else:
                # Shallow: only immediate children
                files = [
                    str(f) for f in base_path.iterdir()
                    if f.is_file() and is_supported_input(str(f))
                ]
            
            if files:
                self._add_files_to_queue(files, base_dir=str(base_path) if recursive else None)
            else:
                QMessageBox.information(self, "No Audio Files", "No supported audio files found.")
    
    def _add_files_to_queue(self, files: list, base_dir: str = None):
        format_name = self.format_combo.currentText()
        quality = self.quality_combo.currentText()
        loudness_target = self._get_loudness_target()
        output_sample_rate = self._get_output_sample_rate()
        fmt_settings = get_format_settings(format_name)
        extension = fmt_settings["extension"]
        
        # Determine output directory strategy
        save_to_source = self.save_to_source_checkbox.isChecked()
        output_dir = self.output_dir_edit.text().strip() if not save_to_source else ""
        
        added = 0
        skipped = 0
        
        for filepath in files:
            # Probe file for source info
            source_format = None
            source_bitrate = None
            source_duration = None
            source_sample_rate = None
            source_channels = None
            
            if self.ffmpeg.is_available():
                try:
                    probe = self.ffmpeg.probe_file(filepath)
                    source_duration = probe.get("duration")
                    source_bitrate = probe.get("bit_rate")
                    
                    # Get codec info from audio stream
                    audio_stream = probe.get("audio_stream")
                    if audio_stream:
                        codec = audio_stream.get("codec_name", "").upper()
                        source_format = self._friendly_codec_name(codec)
                        sr = audio_stream.get("sample_rate")
                        try:
                            source_sample_rate = int(sr) if sr is not None else None
                        except (ValueError, TypeError):
                            source_sample_rate = None
                        source_channels = audio_stream.get("channels")
                except Exception as e:
                    self.logger.warning(f"Could not probe '{Path(filepath).name}': {e}")
            
            # If save_to_source is checked (or output_dir is empty), use source file's directory
            file_output_dir = output_dir if output_dir else str(Path(filepath).parent)
            job = self.batch_processor.add_job(
                filepath, file_output_dir, format_name, quality, extension,
                base_dir=base_dir,
                loudness_target=loudness_target,
                output_sample_rate=output_sample_rate,
                source_format=source_format,
                source_bitrate=source_bitrate,
                source_duration=source_duration,
                source_sample_rate=source_sample_rate,
                source_channels=source_channels,
            )
            if job:
                added += 1
            else:
                skipped += 1
        
        self._refresh_queue_table()
        
        msg = f"Added {added} file(s)"
        if skipped > 0:
            msg += f", {skipped} skipped"
        self.status_bar.showMessage(msg, 3000)
        self.logger.info(f"Added {added} files, skipped {skipped} duplicates")
    
    def _output_lufs_display(self, job) -> str:
        """Loudness normalization target for the →LUFS column.
        Shows 'off' when normalization is disabled."""
        if job.loudness_target is None:
            return "off"
        t = job.loudness_target
        return str(int(t)) if t == int(t) else f"{t:.1f}"

    def _output_khz_display(self, job) -> str:
        """Clean kHz string for the output sample rate column.
        Returns 'src' when no override is set (source rate passes through)."""
        if job.output_sample_rate is None:
            return "src"
        khz = job.output_sample_rate / 1000
        return str(int(khz)) if khz == int(khz) else f"{khz:.1f}"

    def _output_quality_display(self, job) -> str:
        """Clean short quality value for the →kbps column.
        Examples: '320k', 'Q5', 'L5', '24b', '∞'."""
        fmt = get_format_settings(job.format_name)
        if not fmt:
            return ""
        mode = fmt.get("quality_mode", "")
        value = fmt.get("quality_options", {}).get(job.quality_option)
        if mode == "bitrate":
            return value or ""                          # "320k", "192k"
        elif mode == "vbr":
            return f"Q{value}" if value else ""         # "Q5", "Q10"
        elif mode == "compression":
            return f"L{value}" if value else ""         # "L5", "L8"
        elif mode == "bitdepth":
            depth_map = {
                "pcm_s16le": "16b", "pcm_s24le": "24b",
                "pcm_s32le": "32b", "pcm_f32le": "32b",
            }
            return depth_map.get(value or "", "")
        elif mode == "lossless":
            return "∞"
        return ""

    def _friendly_codec_name(self, codec: str) -> str:
        """Convert ffprobe codec name to friendly display name."""
        codec_map = {
            "MP3": "MP3",
            "FLAC": "FLAC",
            "VORBIS": "OGG",
            "OPUS": "OPUS",
            "AAC": "AAC",
            "ALAC": "ALAC",
            "PCM_S16LE": "WAV",
            "PCM_S24LE": "WAV",
            "PCM_S32LE": "WAV",
            "PCM_F32LE": "WAV",
            "PCM_S16BE": "AIFF",
            "PCM_S24BE": "AIFF",
            "PCM_AIFF": "AIFF",
            "WMAV2": "WMA",
            "WMAPRO": "WMA",
            "APE": "APE",
            "WAVPACK": "WV",
            "TAK": "TAK",
            "MPC": "MPC",
        }
        return codec_map.get(codec, codec[:6] if codec else "?")
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        files = []
        base_dir = None
        recursive = self.recursive_checkbox.isChecked()
        dir_count = 0
        single_dir_path = None
        
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path) and is_supported_input(path):
                files.append(path)
            elif os.path.isdir(path):
                dir_count += 1
                dir_path = Path(path)
                single_dir_path = str(dir_path)
                if recursive:
                    for f in dir_path.rglob("*"):
                        if f.is_file() and is_supported_input(str(f)):
                            files.append(str(f))
                else:
                    for f in dir_path.iterdir():
                        if f.is_file() and is_supported_input(str(f)):
                            files.append(str(f))
        
        # Only use base_dir for relative path display if exactly one directory was dropped recursively
        if recursive and dir_count == 1 and single_dir_path:
            base_dir = single_dir_path
        
        if files:
            self._add_files_to_queue(files, base_dir=base_dir)
        else:
            self.status_bar.showMessage("No supported audio files in drop", 3000)

    def _on_format_changed(self, format_name: str):
        # Block quality combo signals while we repopulate it so that
        # _on_quality_changed doesn't fire 2–3 times during clear/addItems/setCurrentText.
        # We call _update_pending_jobs_settings once ourselves at the end.
        self.quality_combo.blockSignals(True)
        self.quality_combo.clear()
        options = get_quality_options(format_name)
        self.quality_combo.addItems(options)
        default = get_default_quality(format_name)
        if default in options:
            self.quality_combo.setCurrentText(default)
        self.quality_combo.blockSignals(False)
        self._update_pending_jobs_settings()

    def _on_quality_changed(self, quality_option: str):
        """Update pending jobs when quality selection changes."""
        self._update_pending_jobs_settings()
    
    def _on_loudness_changed(self, loudness_option: str):
        """Update pending jobs when loudness selection changes."""
        self._update_pending_jobs_settings()

    def _on_sample_rate_changed(self, sample_rate_option: str):
        """Update pending jobs when sample rate selection changes."""
        self._update_pending_jobs_settings()

    _SAMPLE_RATE_MAP = {
        "Source (keep)": None,
        "44.1 kHz":       44100,
        "48 kHz":         48000,
        "88.2 kHz":       88200,
        "96 kHz":         96000,
    }

    def _get_output_sample_rate(self) -> Optional[int]:
        """Return the selected output sample rate in Hz, or None to keep the source rate."""
        return self._SAMPLE_RATE_MAP.get(self.sample_rate_combo.currentText())
    
    def _get_loudness_target(self) -> float | None:
        """Parse loudness combo selection to LUFS value or None."""
        text = self.loudness_combo.currentText()
        if text == "Off":
            return None
        # Parse "-14 LUFS (Streaming)" -> -14.0
        try:
            lufs_str = text.split()[0]  # Get "-14" part
            return float(lufs_str)
        except (ValueError, IndexError):
            return None
    
    def _update_pending_jobs_settings(self):
        """Apply current format/quality/loudness settings to all pending jobs."""
        if self.batch_processor.pending_count == 0:
            return
        
        format_name = self.format_combo.currentText()
        quality = self.quality_combo.currentText()
        if not format_name or not quality:
            return
        
        fmt_settings = get_format_settings(format_name)
        if not fmt_settings:
            return
        
        extension = fmt_settings["extension"]
        loudness_target = self._get_loudness_target()
        output_sample_rate = self._get_output_sample_rate()
        self.batch_processor.update_pending_jobs(
            format_name, quality, extension,
            loudness_target=loudness_target,
            output_sample_rate=output_sample_rate,
        )
        self._refresh_queue_table()
    
    def _on_browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_dir_edit.setText(folder)
    
    def _on_save_to_source_changed(self, state):
        """Enable/disable output folder controls based on checkbox state."""
        is_checked = bool(state)
        self.output_dir_edit.setEnabled(not is_checked)
        self.browse_btn.setEnabled(not is_checked)
        self.folder_label.setEnabled(not is_checked)
        
        if is_checked:
            # Visual feedback: gray out and show placeholder
            self.output_dir_edit.setPlaceholderText("Using source directories")
        else:
            self.output_dir_edit.setPlaceholderText("Same as source")
    
    def _refresh_queue_table(self):
        self.queue_table.setRowCount(len(self.batch_processor.jobs))
        
        for row, job in enumerate(self.batch_processor.jobs):
            # Source format (col 0)
            src_item = QTableWidgetItem(job.source_format or "?")
            src_item.setForeground(QColor("#808080"))
            self.queue_table.setItem(row, 0, src_item)
            
            # Source bitrate (col 1) - with detailed tooltip
            bitrate_item = QTableWidgetItem(job.bitrate_display)
            bitrate_item.setForeground(QColor("#808080"))
            # Build detailed source info tooltip
            source_info_parts = []
            if job.source_format:
                source_info_parts.append(f"Format: {job.source_format}")
            if job.source_bitrate:
                source_info_parts.append(f"Bitrate: {job.source_bitrate // 1000} kbps")
            if job.source_sample_rate:
                source_info_parts.append(f"Sample rate: {job.source_sample_rate} Hz")
            if job.source_channels:
                ch_str = "Mono" if job.source_channels == 1 else "Stereo" if job.source_channels == 2 else f"{job.source_channels}ch"
                source_info_parts.append(f"Channels: {ch_str}")
            if job.source_duration:
                source_info_parts.append(f"Duration: {job.duration_display}")
            if job.source_lufs is not None:
                source_info_parts.append(f"Loudness: {job.source_lufs:.1f} LUFS")
            if source_info_parts:
                bitrate_item.setToolTip("\n".join(source_info_parts))
            self.queue_table.setItem(row, 1, bitrate_item)
            
            # Sample rate (col 2)
            sample_item = QTableWidgetItem(job.sample_rate_display)
            sample_item.setForeground(QColor("#808080"))
            self.queue_table.setItem(row, 2, sample_item)
            
            # LUFS (col 3) - color coded based on loudness target
            lufs_item = QTableWidgetItem(job.lufs_display)
            if job.source_lufs is not None:
                loudness_target = self._get_loudness_target()
                if loudness_target is not None:
                    diff = job.source_lufs - loudness_target
                    if abs(diff) <= 1.0:
                        # Within 1 LUFS of target - green (good)
                        lufs_item.setForeground(QColor("#7cb342"))
                    elif diff > 1.0:
                        # Louder than target - yellow (will be reduced)
                        lufs_item.setForeground(QColor("#c0a040"))
                    else:
                        # Quieter than target - cyan (will be boosted)
                        lufs_item.setForeground(QColor("#4a9fd4"))
                else:
                    lufs_item.setForeground(QColor("#808080"))
            self.queue_table.setItem(row, 3, lufs_item)
            
            # Duration (col 4)
            time_item = QTableWidgetItem(job.duration_display)
            time_item.setForeground(QColor("#808080"))
            self.queue_table.setItem(row, 4, time_item)
            
            # Filename (col 5) - or relative path if from subdirectory scan
            file_item = QTableWidgetItem(job.display_name)
            file_item.setToolTip(job.input_path)  # Full path on hover
            self.queue_table.setItem(row, 5, file_item)
            
            # Output format (col 6) — mirrors "Src"
            self.queue_table.setItem(row, 6, QTableWidgetItem(job.format_name))

            # Output quality clean value (col 7) — mirrors "Bitrate"
            out_q_item = QTableWidgetItem(self._output_quality_display(job))
            out_q_item.setForeground(QColor("#7cb342"))
            self.queue_table.setItem(row, 7, out_q_item)

            # Output sample rate (col 8) — mirrors "kHz"
            out_khz_item = QTableWidgetItem(self._output_khz_display(job))
            out_khz_item.setForeground(QColor("#7cb342"))
            self.queue_table.setItem(row, 8, out_khz_item)

            # Output LUFS normalization target (col 9) — mirrors "LUFS"
            out_lufs_item = QTableWidgetItem(self._output_lufs_display(job))
            out_lufs_item.setForeground(
                QColor("#7cb342") if job.loudness_target is not None else QColor("#505050")
            )
            self.queue_table.setItem(row, 9, out_lufs_item)

            # Status with color (col 10)
            status_item = QTableWidgetItem(job.status.value.title())
            if job.status == JobStatus.COMPLETE:
                status_item.setForeground(QColor("#7cb342"))
            elif job.status == JobStatus.FAILED:
                status_item.setForeground(QColor("#c04040"))
            elif job.status == JobStatus.CONVERTING:
                status_item.setForeground(QColor("#4a9fd4"))
            elif job.status == JobStatus.CANCELLED:
                status_item.setForeground(QColor("#808080"))
            self.queue_table.setItem(row, 10, status_item)

            # Progress (col 11)
            progress_text = f"{int(job.progress * 100)}%" if job.progress > 0 else ""
            self.queue_table.setItem(row, 11, QTableWidgetItem(progress_text))
        
        summary = self.batch_processor.get_summary()
        parts = []
        if summary['pending'] > 0:
            parts.append(f"{summary['pending']} pending")
        if summary['complete'] > 0:
            parts.append(f"{summary['complete']} complete")
        if summary['failed'] > 0:
            parts.append(f"{summary['failed']} failed")
        if summary['cancelled'] > 0:
            parts.append(f"{summary['cancelled']} cancelled")
        
        self.queue_summary_label.setText(" · ".join(parts) if parts else "Ready")
        
        can_convert = summary['pending'] > 0 and self.ffmpeg.is_available() and not self.batch_processor.is_processing
        analyzing = self.analyze_worker is not None and self.analyze_worker.isRunning()
        can_analyze = summary['pending'] > 0 and self.ffmpeg.is_available() and not self.batch_processor.is_processing and not analyzing
        self.convert_btn.setEnabled(can_convert and not analyzing)
        self.analyze_btn.setEnabled(can_analyze)
    
    def _on_clear_completed(self):
        self.batch_processor.clear_completed()
        self._refresh_queue_table()
    
    def _on_clear_all(self):
        if self.batch_processor.is_processing:
            QMessageBox.warning(self, "Cannot Clear", "Cannot clear while converting.")
            return
        total = len(self.batch_processor.jobs)
        if total > 5:
            reply = QMessageBox.question(
                self, "Clear Queue",
                f"Remove all {total} file(s) from the queue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self.batch_processor.clear_all()
        self._refresh_queue_table()
    
    def _on_analyze_clicked(self):
        """Start LUFS analysis on queued files."""
        if not self.ffmpeg.is_available():
            QMessageBox.warning(self, "FFmpeg Not Found", "Please download FFmpeg first.")
            return
        
        # Count files needing analysis
        need_analysis = sum(
            1 for job in self.batch_processor.jobs
            if job.status == JobStatus.PENDING and job.source_lufs is None
        )
        
        if need_analysis == 0:
            QMessageBox.information(self, "Analysis", "All queued files have already been analyzed.")
            return
        
        self.analyze_btn.setEnabled(False)
        self.convert_btn.setEnabled(False)
        self.status_bar.showMessage(f"Analyzing {need_analysis} file(s)...")
        
        self.analyze_worker = AnalyzeWorker(self.ffmpeg, self.batch_processor, parent=self)
        self.analyze_worker.job_analyzed.connect(self._on_job_analyzed)
        self.analyze_worker.job_failed.connect(self._on_job_analyze_failed)  # was never connected
        self.analyze_worker.progress.connect(self._on_analyze_progress)
        self.analyze_worker.finished.connect(self._on_analyze_finished)
        self.analyze_worker.start()
    
    def _on_job_analyzed(self, job_id: str, lufs: float):
        """Called when a single file's LUFS is measured."""
        self._refresh_queue_table()

    def _on_job_analyze_failed(self, job_id: str, error_msg: str):
        """Called when a single file's LUFS analysis fails."""
        # The job stays PENDING so conversion can still proceed without normalization.
        job = self.batch_processor.get_job_by_id(job_id)
        fname = job.input_filename if job else job_id
        self.logger.warning(f"LUFS analysis failed for '{fname}': {error_msg}")
        self._refresh_queue_table()
    
    def _on_analyze_progress(self, current: int, total: int):
        """Update status bar with analysis progress."""
        self.status_bar.showMessage(f"Analyzing file {current}/{total}...")
    
    def _on_analyze_finished(self, analyzed: int, failed: int):
        """Called when all analysis is complete."""
        self.analyze_worker = None  # Clean up worker reference
        self._refresh_queue_table()
        if failed > 0:
            self.status_bar.showMessage(f"Analyzed {analyzed} file(s), {failed} failed", 5000)
        else:
            self.status_bar.showMessage(f"Analyzed {analyzed} file(s)", 3000)
    
    def _on_convert_clicked(self):
        if not self.ffmpeg.is_available():
            QMessageBox.warning(self, "FFmpeg Not Found", "Please download FFmpeg first.")
            return
        
        pending = self.batch_processor.pending_count
        if pending == 0:
            return
        
        delete_source = self.delete_source_checkbox.isChecked()
        
        # Confirm if delete source is enabled - this is irreversible
        if delete_source:
            reply = QMessageBox.warning(
                self,
                "Confirm Delete Source Files",
                f"You have 'Delete source after conversion' enabled.\n\n"
                f"This will PERMANENTLY DELETE {pending} original file(s) after successful conversion.\n\n"
                f"This action cannot be undone. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self.convert_btn.setEnabled(False)
        self.cancel_btn.setVisible(True)
        self.overall_progress.setVisible(True)
        self.overall_progress.setValue(0)
        
        self.batch_worker = BatchWorker(
            self.ffmpeg, self.batch_processor,
            max_workers=self.workers_spin.value(),
            delete_source=delete_source,
            parent=self
        )
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

        # Update only the progress cell for this specific row.
        # Rebuilding the whole table at 20 Hz per worker was unnecessary and
        # caused visible jank on large queues.
        for row, j in enumerate(self.batch_processor.jobs):
            if j.id == job_id:
                progress_text = f"{int(progress * 100)}%"
                item = self.queue_table.item(row, 11)
                if item:
                    item.setText(progress_text)
                else:
                    self.queue_table.setItem(row, 11, QTableWidgetItem(progress_text))
                break

        # Update the overall progress bar
        jobs = self.batch_processor.jobs
        if jobs:
            done_statuses = (JobStatus.COMPLETE, JobStatus.FAILED, JobStatus.CANCELLED)
            total = sum(j.progress for j in jobs if j.status == JobStatus.CONVERTING)
            total += sum(1.0 for j in jobs if j.status in done_statuses)
            self.overall_progress.setValue(int((total / len(jobs)) * 100))
    
    def _on_job_finished(self, job_id: str, success: bool, message: str):
        self._refresh_queue_table()
    
    def _on_batch_finished(self, completed: int, failed: int, cancelled: int):
        self.batch_worker = None  # Clean up worker reference
        self.cancel_btn.setVisible(False)
        self.overall_progress.setVisible(False)
        self._refresh_queue_table()  # sets convert_btn state correctly
        
        parts = []
        if completed > 0:
            parts.append(f"{completed} completed")
        if failed > 0:
            parts.append(f"{failed} failed")
        if cancelled > 0:
            parts.append(f"{cancelled} cancelled")
        
        self.status_bar.showMessage(" · ".join(parts) if parts else "Done", 5000)
        
        if failed > 0:
            QMessageBox.warning(self, "Conversion Issues", f"{failed} file(s) failed. Check log for details.")
    
    def _refresh_log_view(self):
        buf = log_buffer.buffer
        if not buf:
            return
        # Compare only the last entry to decide whether the buffer has changed.
        # This avoids joining 500 lines into a string on every 500ms tick.
        tail = buf[-1]
        if tail == self._last_log_tail:
            return
        self._last_log_tail = tail
        self.log_view.setPlainText("\n".join(buf))
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
                if self.batch_processor.remove_job(job.id):
                    removed += 1

        if removed > 0:
            self._refresh_queue_table()
            self.status_bar.showMessage(f"Removed {removed} file(s)", 3000)
