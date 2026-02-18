from __future__ import annotations

import base64
import csv
import enum
import functools
import io
import json
import os
import os.path as osp
import shutil
import types
import time
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path

import cv2
import natsort
import numpy as np
import PIL.Image
from loguru import logger
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox

from labelvid import __appname__
from labelvid import __version__
from labelvid.label_file import LabelFile
from labelvid.shape import Shape
from labelvid.widgets import Canvas
from labelvid.widgets import CaptionAnalysisWidget
from labelvid.widgets import ClipDialog
from labelvid.widgets import ClipListWidget
from labelvid.widgets import ClipListWidgetItem
from labelvid.widgets import ClipTimelineWidget
from labelvid.widgets import get_object_list
from labelvid.widgets import LabelDialog
from labelvid.widgets import ObjectListDialog
from labelvid.widgets import set_object_list
from labelvid.widgets import VideoPlayerWidget

# Try to import Whisper support
try:
    from labelvid._whisper import WHISPER_MODELS
    from labelvid._whisper import WhisperTranscriber

    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    WHISPER_MODELS = ["turbo", "tiny", "base", "small", "medium", "large"]
    WhisperTranscriber = None  # type: ignore

# Try to import multimedia support for audio playback
try:
    from PyQt5 import QtMultimedia
    from PyQt5.QtMultimedia import QMediaContent
    from PyQt5.QtMultimedia import QMediaPlayer

    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    QtMultimedia = None  # type: ignore
    QMediaPlayer = None  # type: ignore
    QMediaContent = None  # type: ignore

VIDEO_EXTENSIONS = [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v"]
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"]


def _find_executable(name: str) -> str | None:
    """Find executable in system PATH.
    
    Args:
        name: Name of executable (e.g., 'ffmpeg', 'ffprobe')
        
    Returns:
        Full path to executable or None if not found
    """
    # First try shutil.which
    path = shutil.which(name)
    if path:
        return path
    
    # Common installation paths
    common_paths = [
        f"/usr/local/bin/{name}",
        f"/opt/homebrew/bin/{name}",  # Apple Silicon Homebrew
        f"/usr/bin/{name}",
        f"/opt/local/bin/{name}",  # MacPorts
        os.path.expanduser(f"~/bin/{name}"),
    ]
    
    for path in common_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    
    return None


class AppMode(enum.Enum):
    """Application mode: Video clipping or Image annotation."""

    VIDEO = "video"
    IMAGE = "image"


class ImageModeSource(enum.Enum):
    """Source for image in Image mode."""

    CURRENT_FRAME = "current_frame"  # Use current video frame
    WST = "wst"  # Work with Saved Thumbnails (extracted frames)
    AUTO_EXTRACT = "auto_extract"  # Auto-extract when switching


# Available SAM models
SAM_MODELS = [
    "sam2:latest",
    "sam2:tiny",
    "sam2:small",
    "sam2:base",
    "sam2:large",
    "sam:vit_h",
    "sam:vit_l",
    "sam:vit_b",
]


@dataclass
class VideoClip:
    """Represents a marked video clip segment."""

    label: str
    start_frame: int
    end_frame: int
    color: tuple[int, int, int] = field(default_factory=lambda: (0, 255, 0))
    detection_score: float | None = None  # Detection confidence (0-5)
    recognition_score: float | None = None  # Recognition confidence (0-5)
    is_hazard: bool | None = None  # Whether object is a hazard
    description: str = ""  # Additional description
    recognition: str = ""  # Recognition result (same as label for LLM)
    scene: str = ""  # Scene description
    category_id: int = 0  # Category ID from object list
    instance_id: int = 0  # Instance ID from object list

    def __post_init__(self) -> None:
        if self.end_frame < self.start_frame:
            self.start_frame, self.end_frame = self.end_frame, self.start_frame


class MainWindow(QtWidgets.QMainWindow):
    """Main window for video clipping and image annotation application."""

    filename: str | None = None
    _video_capture: cv2.VideoCapture | None = None
    _total_frames: int = 0
    _fps: float = 30.0  # Nominal FPS from cv2 / ffprobe metadata
    _actual_duration: float = 0.0  # Actual container duration in seconds (from ffprobe)
    _effective_fps: float = 30.0  # Effective FPS = total_frames / actual_duration (for timing)
    _frame_width: int = 0
    _frame_height: int = 0
    _current_frame: int = 0
    _is_playing: bool = False
    _playback_speed: float = 1.0
    _playback_start_ms: float | None = None  # Wall-clock ms when playback started
    _pending_start_frame: int | None = None
    _clips: list[VideoClip]
    _is_changed: bool = False
    _auto_save_path: str | None = None  # Auto-save path
    _last_displayed_frame: int = -1  # Used to avoid redisplaying the same frame
    _preview_scale: float = 0.5  # Preview scale ratio (0.25, 0.5, 0.75, 1.0)

    # Image annotation mode
    _app_mode: AppMode = AppMode.VIDEO
    _image_data: bytes | None = None
    _label_list: list[str] = []
    _image_mode_source: ImageModeSource = ImageModeSource.CURRENT_FRAME
    _wst_frames_dir: str | None = None  # Directory with extracted frames for WST mode
    _wst_current_image: str | None = None  # Current image path in WST mode
    _wst_image_files: list[str] = []  # List of image files in WST folder
    _sam_model_name: str = "sam2:latest"  # Selected SAM model

    # Audio and Whisper
    _audio_enabled: bool = True  # Whether audio playback is enabled
    _audio_player: QMediaPlayer | None = None  # Audio player
    _extracted_audio_path: str | None = None  # Path to extracted audio file
    _whisper_enabled: bool = False  # Whether Whisper caption extraction is enabled
    _whisper_model_name: str = "medium.en"  # Selected Whisper model
    _whisper_transcriber: WhisperTranscriber | None = None  # Whisper transcriber
    _caption_segments: list = []  # Caption segments from Whisper
    _current_caption: str = ""  # Current caption text
    _caption_search_results: list[int] = []  # Frame numbers where keywords found
    _caption_search_keywords: list[str] = []  # Current search keywords
    _llm_detections: list = []  # Object detections from LLM analysis

    # Preview quality options
    PREVIEW_SCALES = {
        "25% (fastest)": 0.25,
        "50% (recommended)": 0.5,
        "75%": 0.75,
        "100% (original)": 1.0,
    }

    def __init__(
        self,
        filename: str | None = None,
        output_dir: str | None = None,
        labels: list[str] | None = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle(__appname__)

        self._clips = []
        self.output_dir = output_dir
        self._video_output_dir: str | None = None  # Video-specific output directory
        self._prev_opened_dir: str | None = None
        self._label_list = labels or []

        self._init_ui()
        self._init_actions()
        self._init_menus()
        self._init_toolbar()
        self._init_statusbar()
        self._init_timer()

        # Restore window settings
        self.settings = QtCore.QSettings("labelvid", "labelvid")
        size = self.settings.value("window/size", QtCore.QSize(1200, 800))
        position = self.settings.value("window/position", QtCore.QPoint(100, 100))
        self.resize(size)
        self.move(position)

        if filename:
            if osp.isdir(filename):
                self._import_videos_from_dir(root_dir=filename)
                self._open_next_video()
            else:
                self._load_video(filename)

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Central widget - stacked widget for video player and image canvas
        self.centralStack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.centralStack)

        # Video player widget (index 0)
        self.videoPlayer = VideoPlayerWidget()
        self.centralStack.addWidget(self.videoPlayer)

        # Image annotation canvas (index 1)
        self.canvas = Canvas(epsilon=10.0, double_click="close")
        self.canvas.newShape.connect(self._on_new_shape)
        self.canvas.selectionChanged.connect(self._on_shape_selection_changed)
        self.canvas.shapeMoved.connect(self._on_shapes_changed)
        self.canvas.drawingPolygon.connect(self._on_drawing_polygon)
        self.canvas.zoomRequest.connect(self._on_zoom_request)
        self.canvas.scrollRequest.connect(self._on_scroll_request)
        self.canvas.statusUpdated.connect(self.statusBar().showMessage)
        
        # Setup canvas right-click context menus (will be populated in _init_actions)
        # menus[0]: no selection/copy, menus[1]: with selection/copy
        self._setup_canvas_context_menus()

        # Scroll area for canvas
        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setWidget(self.canvas)
        self.scrollArea.setWidgetResizable(True)
        self.centralStack.addWidget(self.scrollArea)

        # Label dialog for annotation
        self.labelDialog = LabelDialog(
            parent=self,
            labels=self._label_list,
            sort_labels=True,
            show_text_field=True,
        )

        # File list dock
        self.fileSearch = QtWidgets.QLineEdit()
        self.fileSearch.setPlaceholderText(self.tr("Search Filename"))
        self.fileSearch.textChanged.connect(self._file_search_changed)
        self.fileListWidget = QtWidgets.QListWidget()
        self.fileListWidget.itemSelectionChanged.connect(self._file_selection_changed)
        fileListLayout = QtWidgets.QVBoxLayout()
        fileListLayout.setContentsMargins(0, 0, 0, 0)
        fileListLayout.setSpacing(0)
        fileListLayout.addWidget(self.fileSearch)
        fileListLayout.addWidget(self.fileListWidget)
        self.file_dock = QtWidgets.QDockWidget(self.tr("Video List"), self)
        self.file_dock.setObjectName("Videos")
        fileListWidget = QtWidgets.QWidget()
        fileListWidget.setLayout(fileListLayout)
        self.file_dock.setWidget(fileListWidget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.file_dock)

        # Clip list dock (for video mode)
        self.clipListWidget = ClipListWidget()
        self.clipListWidget.itemSelectionChanged.connect(self._clip_selection_changed)
        self.clipListWidget.itemDoubleClicked.connect(self._clip_double_clicked)
        self.clipListWidget.deleteRequested.connect(self._delete_selected_clip)
        # Enable right-click context menu for clips
        self.clipListWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.clipListWidget.customContextMenuRequested.connect(self._pop_clip_list_menu)
        self.clip_dock = QtWidgets.QDockWidget(self.tr("Clips"), self)
        self.clip_dock.setObjectName("Clips")
        self.clip_dock.setWidget(self.clipListWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.clip_dock)
        
        # Create clip list context menu
        self._clip_context_menu = QtWidgets.QMenu(self)
        self._clip_edit_action = self._clip_context_menu.addAction(
            self.tr("Edit Label")
        )
        self._clip_edit_action.triggered.connect(self._edit_selected_clip)
        self._clip_goto_start_action = self._clip_context_menu.addAction(
            self.tr("Go to Start Frame")
        )
        self._clip_goto_start_action.triggered.connect(self._goto_clip_start)
        self._clip_goto_end_action = self._clip_context_menu.addAction(
            self.tr("Go to End Frame")
        )
        self._clip_goto_end_action.triggered.connect(self._goto_clip_end)
        self._clip_context_menu.addSeparator()
        self._clip_delete_action = self._clip_context_menu.addAction(
            self.tr("Delete")
        )
        self._clip_delete_action.setShortcut("Delete")
        self._clip_delete_action.triggered.connect(self._delete_selected_clip)

        # Shape list dock (for image mode)
        self.shapeListWidget = QtWidgets.QListWidget()
        self.shapeListWidget.itemSelectionChanged.connect(
            self._shape_list_selection_changed
        )
        self.shapeListWidget.itemDoubleClicked.connect(self._shape_list_double_clicked)
        # Enable right-click context menu for shapes
        self.shapeListWidget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.shapeListWidget.customContextMenuRequested.connect(self._pop_shape_list_menu)
        self.shape_dock = QtWidgets.QDockWidget(self.tr("Shapes"), self)
        self.shape_dock.setObjectName("Shapes")
        self.shape_dock.setWidget(self.shapeListWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.shape_dock)
        self.shape_dock.hide()  # Hidden by default (video mode)
        
        # Create shape list context menu
        self._shape_context_menu = QtWidgets.QMenu(self)
        self._shape_edit_label_action = self._shape_context_menu.addAction(
            self.tr("Edit Label")
        )
        self._shape_edit_label_action.triggered.connect(self._edit_shape_label)
        self._shape_context_menu.addSeparator()
        self._shape_delete_action = self._shape_context_menu.addAction(
            self.tr("❌ Delete Shape")
        )
        self._shape_delete_action.triggered.connect(self._delete_selected_shapes)

        # Image list dock (for image mode - similar to video list)
        self.imageSearch = QtWidgets.QLineEdit()
        self.imageSearch.setPlaceholderText(self.tr("Search Image"))
        self.imageSearch.textChanged.connect(self._image_search_changed)
        self.imageListWidget = QtWidgets.QListWidget()
        self.imageListWidget.itemSelectionChanged.connect(self._image_selection_changed)
        self.imageListWidget.itemDoubleClicked.connect(self._image_double_clicked)
        imageListLayout = QtWidgets.QVBoxLayout()
        imageListLayout.setContentsMargins(0, 0, 0, 0)
        imageListLayout.setSpacing(0)
        imageListLayout.addWidget(self.imageSearch)
        imageListLayout.addWidget(self.imageListWidget)
        self.image_dock = QtWidgets.QDockWidget(self.tr("Image List"), self)
        self.image_dock.setObjectName("Images")
        imageListContainer = QtWidgets.QWidget()
        imageListContainer.setLayout(imageListLayout)
        self.image_dock.setWidget(imageListContainer)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.image_dock)
        self.image_dock.hide()  # Hidden by default (video mode)

        # Playback controls dock (for video mode)
        controlsWidget = self._create_playback_controls()
        self.controls_dock = QtWidgets.QDockWidget(self.tr("Playback Controls"), self)
        self.controls_dock.setObjectName("Controls")
        self.controls_dock.setWidget(controlsWidget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.controls_dock)

        # Annotation controls dock (for image mode)
        annotationWidget = self._create_annotation_controls()
        self.annotation_dock = QtWidgets.QDockWidget(
            self.tr("Annotation Controls"), self
        )
        self.annotation_dock.setObjectName("AnnotationControls")
        self.annotation_dock.setWidget(annotationWidget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.annotation_dock)
        self.annotation_dock.hide()  # Hidden by default (video mode)

    def _create_playback_controls(self) -> QtWidgets.QWidget:
        """Create the playback control panel."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        # Timeline slider
        sliderLayout = QtWidgets.QHBoxLayout()
        self.frameLabel = QtWidgets.QLabel("0 / 0")
        self.frameLabel.setMinimumWidth(120)
        self.timelineSlider = QtWidgets.QSlider(Qt.Horizontal)
        self.timelineSlider.setMinimum(0)
        self.timelineSlider.setMaximum(0)
        self.timelineSlider.valueChanged.connect(self._on_slider_changed)
        self.timelineSlider.sliderPressed.connect(self._on_slider_pressed)
        self.timelineSlider.sliderReleased.connect(self._on_slider_released)
        self.timeLabel = QtWidgets.QLabel("00:00:00 / 00:00:00")
        self.timeLabel.setMinimumWidth(150)
        sliderLayout.addWidget(self.frameLabel)
        sliderLayout.addWidget(self.timelineSlider, 1)
        sliderLayout.addWidget(self.timeLabel)
        layout.addLayout(sliderLayout)
        
        # Clip timeline (shows clip markers below the slider)
        clipTimelineLayout = QtWidgets.QHBoxLayout()
        clipTimelineLayout.setContentsMargins(0, 0, 0, 0)
        # Add spacer to align with slider (same width as frameLabel)
        clipTimelineSpacer = QtWidgets.QWidget()
        clipTimelineSpacer.setMinimumWidth(120)
        clipTimelineSpacer.setMaximumWidth(120)
        clipTimelineLayout.addWidget(clipTimelineSpacer)
        
        self.clipTimeline = ClipTimelineWidget()
        self.clipTimeline.markerDragging.connect(self._on_clip_marker_dragging)
        self.clipTimeline.markerDragFinished.connect(self._on_clip_marker_drag_finished)
        self.clipTimeline.markerClicked.connect(self._on_clip_marker_clicked)
        clipTimelineLayout.addWidget(self.clipTimeline, 1)
        
        # Add spacer to align with time label
        clipTimelineEndSpacer = QtWidgets.QWidget()
        clipTimelineEndSpacer.setMinimumWidth(150)
        clipTimelineEndSpacer.setMaximumWidth(150)
        clipTimelineLayout.addWidget(clipTimelineEndSpacer)
        
        layout.addLayout(clipTimelineLayout)

        # Playback buttons
        buttonLayout = QtWidgets.QHBoxLayout()

        self.prevFrameBtn = QtWidgets.QPushButton("⏮ Prev")
        self.prevFrameBtn.clicked.connect(self._prev_frame)
        buttonLayout.addWidget(self.prevFrameBtn)

        self.playPauseBtn = QtWidgets.QPushButton("▶ Play")
        self.playPauseBtn.clicked.connect(self._toggle_play)
        buttonLayout.addWidget(self.playPauseBtn)

        self.nextFrameBtn = QtWidgets.QPushButton("Next ⏭")
        self.nextFrameBtn.clicked.connect(self._next_frame)
        buttonLayout.addWidget(self.nextFrameBtn)

        buttonLayout.addSpacing(20)

        # Speed control
        speedLabel = QtWidgets.QLabel("Speed:")
        buttonLayout.addWidget(speedLabel)
        self.speedCombo = QtWidgets.QComboBox()
        self.speedCombo.addItems(["0.25x", "0.5x", "1x", "1.5x", "2x", "4x"])
        self.speedCombo.setCurrentText("1x")
        self.speedCombo.currentTextChanged.connect(self._on_speed_changed)
        buttonLayout.addWidget(self.speedCombo)

        buttonLayout.addSpacing(10)

        # Jump control for long videos
        jumpLabel = QtWidgets.QLabel("Jump:")
        buttonLayout.addWidget(jumpLabel)
        self.jumpCombo = QtWidgets.QComboBox()
        self.jumpCombo.addItems(["1s", "5s", "10s", "30s", "1min", "5min"])
        self.jumpCombo.setCurrentText("10s")
        buttonLayout.addWidget(self.jumpCombo)

        self.jumpBackBtn = QtWidgets.QPushButton("◀◀")
        self.jumpBackBtn.setMaximumWidth(40)
        self.jumpBackBtn.clicked.connect(self._jump_backward)
        self.jumpBackBtn.setToolTip("Jump backward")
        buttonLayout.addWidget(self.jumpBackBtn)

        self.jumpFwdBtn = QtWidgets.QPushButton("▶▶")
        self.jumpFwdBtn.setMaximumWidth(40)
        self.jumpFwdBtn.clicked.connect(self._jump_forward)
        self.jumpFwdBtn.setToolTip("Jump forward")
        buttonLayout.addWidget(self.jumpFwdBtn)

        buttonLayout.addSpacing(10)

        # FPS adjustment control
        fpsLabel = QtWidgets.QLabel("FPS:")
        buttonLayout.addWidget(fpsLabel)
        self.fpsSpinBox = QtWidgets.QDoubleSpinBox()
        self.fpsSpinBox.setRange(1.0, 120.0)
        self.fpsSpinBox.setDecimals(2)
        self.fpsSpinBox.setSingleStep(0.1)
        self.fpsSpinBox.setValue(30.0)
        self.fpsSpinBox.setMaximumWidth(80)
        self.fpsSpinBox.valueChanged.connect(self._on_fps_adjusted)
        self.fpsSpinBox.setToolTip(
            "Effective FPS (= frames / actual duration)\n"
            "Adjust if video playback speed is incorrect\n"
            "Lower = slower playback, Higher = faster playback"
        )
        buttonLayout.addWidget(self.fpsSpinBox)

        buttonLayout.addSpacing(10)

        # Preview quality control
        qualityLabel = QtWidgets.QLabel("Preview:")
        buttonLayout.addWidget(qualityLabel)
        self.qualityCombo = QtWidgets.QComboBox()
        self.qualityCombo.addItems(list(self.PREVIEW_SCALES.keys()))
        self.qualityCombo.setCurrentText("50% (recommended)")
        self.qualityCombo.currentTextChanged.connect(self._on_quality_changed)
        self.qualityCombo.setToolTip(
            "Preview quality - Lower quality improves playback smoothness for long videos\n"
            "Frame extraction always uses original quality"
        )
        buttonLayout.addWidget(self.qualityCombo)

        buttonLayout.addSpacing(20)

        # Clip marking buttons
        self.markStartBtn = QtWidgets.QPushButton("[ Mark Start")
        self.markStartBtn.clicked.connect(self._mark_start)
        self.markStartBtn.setStyleSheet("background-color: #4CAF50; color: white;")
        buttonLayout.addWidget(self.markStartBtn)

        self.markEndBtn = QtWidgets.QPushButton("Mark End ]")
        self.markEndBtn.clicked.connect(self._mark_end)
        self.markEndBtn.setStyleSheet("background-color: #f44336; color: white;")
        self.markEndBtn.setEnabled(False)
        buttonLayout.addWidget(self.markEndBtn)

        buttonLayout.addStretch()

        # Extract button
        self.extractBtn = QtWidgets.QPushButton("📤 Extract Frames")
        self.extractBtn.clicked.connect(self._extract_frames)
        self.extractBtn.setStyleSheet(
            "background-color: #2196F3; color: white; padding: 5px 15px;"
        )
        buttonLayout.addWidget(self.extractBtn)

        layout.addLayout(buttonLayout)

        # Pending clip indicator
        self.pendingLabel = QtWidgets.QLabel("")
        self.pendingLabel.setStyleSheet("color: #4CAF50; font-weight: bold;")
        layout.addWidget(self.pendingLabel)

        # Audio and Caption controls
        audioLayout = QtWidgets.QHBoxLayout()

        # Audio enable checkbox
        self.audioEnableCheck = QtWidgets.QCheckBox("🔊 Audio")
        self.audioEnableCheck.setChecked(self._audio_enabled)
        self.audioEnableCheck.setEnabled(AUDIO_AVAILABLE)
        self.audioEnableCheck.stateChanged.connect(self._on_audio_toggle)
        if not AUDIO_AVAILABLE:
            self.audioEnableCheck.setToolTip(
                "Audio not available. Install PyQt5 with multimedia support."
            )
        audioLayout.addWidget(self.audioEnableCheck)

        # Volume slider
        volumeLabel = QtWidgets.QLabel("Vol:")
        audioLayout.addWidget(volumeLabel)
        self.volumeSlider = QtWidgets.QSlider(Qt.Horizontal)
        self.volumeSlider.setMinimum(0)
        self.volumeSlider.setMaximum(100)
        self.volumeSlider.setValue(80)
        self.volumeSlider.setMaximumWidth(100)
        self.volumeSlider.valueChanged.connect(self._on_volume_changed)
        self.volumeSlider.setEnabled(AUDIO_AVAILABLE and self._audio_enabled)
        audioLayout.addWidget(self.volumeSlider)

        audioLayout.addSpacing(20)

        # Whisper caption enable checkbox
        self.whisperEnableCheck = QtWidgets.QCheckBox("📝 Captions (Whisper)")
        self.whisperEnableCheck.setChecked(False)
        self.whisperEnableCheck.setEnabled(WHISPER_AVAILABLE)
        self.whisperEnableCheck.stateChanged.connect(self._on_whisper_toggle)
        if not WHISPER_AVAILABLE:
            self.whisperEnableCheck.setToolTip(
                "Whisper not available. Run: pip install openai-whisper"
            )
        audioLayout.addWidget(self.whisperEnableCheck)

        # Whisper model selector
        whisperModelLabel = QtWidgets.QLabel("Model:")
        audioLayout.addWidget(whisperModelLabel)
        self.whisperModelCombo = QtWidgets.QComboBox()
        self.whisperModelCombo.addItems(WHISPER_MODELS)
        self.whisperModelCombo.setCurrentText(self._whisper_model_name)
        self.whisperModelCombo.currentTextChanged.connect(self._on_whisper_model_changed)
        self.whisperModelCombo.setEnabled(WHISPER_AVAILABLE)
        self.whisperModelCombo.setToolTip(
            "Whisper model size:\n"
            "• tiny/base: Fastest, ~1GB VRAM\n"
            "• small: ~2GB VRAM\n"
            "• medium: ~5GB VRAM\n"
            "• large/turbo: Best quality, ~6-10GB VRAM"
        )
        audioLayout.addWidget(self.whisperModelCombo)

        # Language selector
        langLabel = QtWidgets.QLabel("Lang:")
        audioLayout.addWidget(langLabel)
        self.whisperLangCombo = QtWidgets.QComboBox()
        self.whisperLangCombo.addItems([
            "auto", "en", "zh", "ja", "ko", "es", "fr", "de", "ru", "ar", "hi"
        ])
        self.whisperLangCombo.setCurrentText("auto")
        self.whisperLangCombo.setEnabled(WHISPER_AVAILABLE)
        self.whisperLangCombo.setToolTip("Language for transcription (auto = auto-detect)")
        audioLayout.addWidget(self.whisperLangCombo)

        # Extract captions button
        self.extractCaptionsBtn = QtWidgets.QPushButton("🎙️ Extract Captions")
        self.extractCaptionsBtn.clicked.connect(self._extract_captions)
        self.extractCaptionsBtn.setEnabled(WHISPER_AVAILABLE)
        self.extractCaptionsBtn.setToolTip("Extract captions using Whisper AI")
        audioLayout.addWidget(self.extractCaptionsBtn)

        # Export captions button
        self.exportCaptionsBtn = QtWidgets.QPushButton("💾 Export SRT")
        self.exportCaptionsBtn.clicked.connect(self._export_captions)
        self.exportCaptionsBtn.setEnabled(False)
        self.exportCaptionsBtn.setToolTip("Export captions to SRT subtitle file")
        audioLayout.addWidget(self.exportCaptionsBtn)

        audioLayout.addStretch()
        layout.addLayout(audioLayout)

        # Caption search controls
        searchLayout = QtWidgets.QHBoxLayout()
        
        searchLabel = QtWidgets.QLabel("Search in Captions:")
        searchLayout.addWidget(searchLabel)
        
        self.captionSearchInput = QtWidgets.QLineEdit()
        self.captionSearchInput.setPlaceholderText("Enter keywords (e.g., start, stop)")
        self.captionSearchInput.setMaximumWidth(200)
        self.captionSearchInput.textChanged.connect(self._on_caption_search_changed)
        searchLayout.addWidget(self.captionSearchInput)
        
        self.searchCaptionsBtn = QtWidgets.QPushButton("🔍 Search")
        self.searchCaptionsBtn.clicked.connect(self._search_captions)
        self.searchCaptionsBtn.setEnabled(False)
        self.searchCaptionsBtn.setToolTip("Search for keywords in captions")
        searchLayout.addWidget(self.searchCaptionsBtn)
        
        self.clearSearchBtn = QtWidgets.QPushButton("✕ Clear")
        self.clearSearchBtn.clicked.connect(self._clear_caption_search)
        self.clearSearchBtn.setEnabled(False)
        self.clearSearchBtn.setToolTip("Clear search results")
        searchLayout.addWidget(self.clearSearchBtn)
        
        searchLayout.addSpacing(10)
        
        # Navigation buttons for search results
        self.prevSearchBtn = QtWidgets.QPushButton("◀ Prev")
        self.prevSearchBtn.clicked.connect(self._goto_prev_search_result)
        self.prevSearchBtn.setEnabled(False)
        self.prevSearchBtn.setToolTip("Go to previous search result (Shift+Up)")
        searchLayout.addWidget(self.prevSearchBtn)
        
        self.nextSearchBtn = QtWidgets.QPushButton("Next ▶")
        self.nextSearchBtn.clicked.connect(self._goto_next_search_result)
        self.nextSearchBtn.setEnabled(False)
        self.nextSearchBtn.setToolTip("Go to next search result (Shift+Down)")
        searchLayout.addWidget(self.nextSearchBtn)
        
        self.searchResultLabel = QtWidgets.QLabel("")
        self.searchResultLabel.setStyleSheet("color: #4CAF50;")
        searchLayout.addWidget(self.searchResultLabel)
        
        searchLayout.addStretch()
        layout.addLayout(searchLayout)

        # LLM Caption Analysis widget
        self.captionAnalysisWidget = CaptionAnalysisWidget()
        self.captionAnalysisWidget.analysisRequested.connect(self._on_llm_analysis_requested)
        self.captionAnalysisWidget.setEnabled(False)  # Disabled until captions loaded
        layout.addWidget(self.captionAnalysisWidget)

        # Caption display area
        self.captionLabel = QtWidgets.QLabel("")
        self.captionLabel.setAlignment(Qt.AlignCenter)
        self.captionLabel.setWordWrap(True)
        self.captionLabel.setStyleSheet(
            "QLabel {"
            "  background-color: rgba(0, 0, 0, 0.7);"
            "  color: white;"
            "  font-size: 14px;"
            "  padding: 8px 16px;"
            "  border-radius: 4px;"
            "  min-height: 30px;"
            "}"
        )
        self.captionLabel.hide()  # Hidden until captions are extracted
        layout.addWidget(self.captionLabel)

        return widget

    def _create_annotation_controls(self) -> QtWidgets.QWidget:
        """Create the annotation control panel for image mode."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        # Drawing mode buttons
        modeLayout = QtWidgets.QHBoxLayout()

        modeLabel = QtWidgets.QLabel("Draw Mode:")
        modeLayout.addWidget(modeLabel)

        self.polygonBtn = QtWidgets.QPushButton("🔷 Polygon")
        self.polygonBtn.setCheckable(True)
        self.polygonBtn.setChecked(True)
        self.polygonBtn.clicked.connect(lambda: self._set_create_mode("polygon"))
        modeLayout.addWidget(self.polygonBtn)

        self.rectangleBtn = QtWidgets.QPushButton("⬜ Rectangle")
        self.rectangleBtn.setCheckable(True)
        self.rectangleBtn.clicked.connect(lambda: self._set_create_mode("rectangle"))
        modeLayout.addWidget(self.rectangleBtn)

        self.circleBtn = QtWidgets.QPushButton("⭕ Circle")
        self.circleBtn.setCheckable(True)
        self.circleBtn.clicked.connect(lambda: self._set_create_mode("circle"))
        modeLayout.addWidget(self.circleBtn)

        self.lineBtn = QtWidgets.QPushButton("📏 Line")
        self.lineBtn.setCheckable(True)
        self.lineBtn.clicked.connect(lambda: self._set_create_mode("line"))
        modeLayout.addWidget(self.lineBtn)

        self.pointBtn = QtWidgets.QPushButton("📍 Point")
        self.pointBtn.setCheckable(True)
        self.pointBtn.clicked.connect(lambda: self._set_create_mode("point"))
        modeLayout.addWidget(self.pointBtn)

        modeLayout.addSpacing(20)

        # AI-assisted annotation (SAM)
        self.aiPolygonBtn = QtWidgets.QPushButton("🤖 AI Polygon")
        self.aiPolygonBtn.setCheckable(True)
        self.aiPolygonBtn.setToolTip(
            "AI-assisted polygon annotation using SAM.\n"
            "Click to add positive points, Shift+Click for negative points."
        )
        self.aiPolygonBtn.clicked.connect(lambda: self._set_create_mode("ai_polygon"))
        modeLayout.addWidget(self.aiPolygonBtn)

        modeLayout.addSpacing(10)

        # SAM model selector
        samLabel = QtWidgets.QLabel("SAM:")
        modeLayout.addWidget(samLabel)
        self.samModelCombo = QtWidgets.QComboBox()
        self.samModelCombo.addItems(SAM_MODELS)
        self.samModelCombo.setCurrentText(self._sam_model_name)
        self.samModelCombo.currentTextChanged.connect(self._on_sam_model_changed)
        self.samModelCombo.setToolTip(
            "Select SAM model version:\n"
            "- sam2:tiny/small/base/large - SAM2 variants (recommended)\n"
            "- sam:vit_h/l/b - Original SAM variants"
        )
        modeLayout.addWidget(self.samModelCombo)

        modeLayout.addStretch()

        # Edit mode toggle (for moving/resizing shapes)
        self.editModeBtn = QtWidgets.QPushButton("🔧 Edit/Move")
        self.editModeBtn.setCheckable(True)
        self.editModeBtn.setToolTip("Toggle edit mode to move/resize shapes (E)")
        self.editModeBtn.clicked.connect(self._toggle_edit_mode)
        modeLayout.addWidget(self.editModeBtn)

        layout.addLayout(modeLayout)

        # Action buttons
        actionLayout = QtWidgets.QHBoxLayout()

        self.undoBtn = QtWidgets.QPushButton("↩ Undo")
        self.undoBtn.clicked.connect(self._undo_shape_edit)
        actionLayout.addWidget(self.undoBtn)

        self.deleteShapeBtn = QtWidgets.QPushButton("❌ Delete")
        self.deleteShapeBtn.setToolTip("Delete selected shapes (Delete key)")
        self.deleteShapeBtn.clicked.connect(self._delete_selected_shapes)
        actionLayout.addWidget(self.deleteShapeBtn)

        actionLayout.addSpacing(20)

        # Zoom controls
        zoomLabel = QtWidgets.QLabel("Zoom:")
        actionLayout.addWidget(zoomLabel)

        self.zoomInBtn = QtWidgets.QPushButton("+")
        self.zoomInBtn.setMaximumWidth(30)
        self.zoomInBtn.clicked.connect(self._zoom_in)
        actionLayout.addWidget(self.zoomInBtn)

        self.zoomOutBtn = QtWidgets.QPushButton("-")
        self.zoomOutBtn.setMaximumWidth(30)
        self.zoomOutBtn.clicked.connect(self._zoom_out)
        actionLayout.addWidget(self.zoomOutBtn)

        self.zoomFitBtn = QtWidgets.QPushButton("Fit")
        self.zoomFitBtn.clicked.connect(self._zoom_fit)
        actionLayout.addWidget(self.zoomFitBtn)

        self.zoom100Btn = QtWidgets.QPushButton("100%")
        self.zoom100Btn.clicked.connect(self._zoom_100)
        actionLayout.addWidget(self.zoom100Btn)

        actionLayout.addStretch()

        # Save annotation button
        self.saveAnnotationBtn = QtWidgets.QPushButton("💾 Save Annotation")
        self.saveAnnotationBtn.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 5px 15px;"
        )
        self.saveAnnotationBtn.clicked.connect(self._save_annotation)
        actionLayout.addWidget(self.saveAnnotationBtn)

        layout.addLayout(actionLayout)

        # WST (Work with Saved Thumbnails) mode controls
        wstLayout = QtWidgets.QHBoxLayout()

        wstLabel = QtWidgets.QLabel("Image Source:")
        wstLayout.addWidget(wstLabel)

        self.imageSourceCombo = QtWidgets.QComboBox()
        self.imageSourceCombo.addItems([
            "Current Frame",
            "WST (Extracted Frames)",
            "Auto Extract",
        ])
        self.imageSourceCombo.setToolTip(
            "Select image source for annotation:\n"
            "- Current Frame: Use current video frame\n"
            "- WST: Load from extracted frames folder\n"
            "- Auto Extract: Auto-extract current clip frames"
        )
        self.imageSourceCombo.currentIndexChanged.connect(self._on_image_source_changed)
        wstLayout.addWidget(self.imageSourceCombo)

        wstLayout.addSpacing(10)

        # WST folder selection
        self.wstFolderBtn = QtWidgets.QPushButton("📁 Select Frames Folder")
        self.wstFolderBtn.clicked.connect(self._select_wst_folder)
        self.wstFolderBtn.setEnabled(False)
        wstLayout.addWidget(self.wstFolderBtn)

        wstLayout.addSpacing(10)

        # Image navigation buttons (images are shown in left panel list)
        self.wstPrevBtn = QtWidgets.QPushButton("◀ Prev")
        self.wstPrevBtn.clicked.connect(self._wst_prev_image)
        self.wstPrevBtn.setEnabled(False)
        self.wstPrevBtn.setToolTip("Previous image (images shown in left panel)")
        wstLayout.addWidget(self.wstPrevBtn)

        # Hidden combo box for backward compatibility (not displayed)
        self.wstImageCombo = QtWidgets.QComboBox()
        self.wstImageCombo.setMinimumWidth(200)
        self.wstImageCombo.currentTextChanged.connect(self._on_wst_image_changed)
        self.wstImageCombo.setEnabled(False)
        self.wstImageCombo.hide()  # Hidden - use image list in left panel instead

        self.wstNextBtn = QtWidgets.QPushButton("Next ▶")
        self.wstNextBtn.clicked.connect(self._wst_next_image)
        self.wstNextBtn.setEnabled(False)
        self.wstNextBtn.setToolTip("Next image (images shown in left panel)")
        wstLayout.addWidget(self.wstNextBtn)

        # Image counter label
        self.imageCountLabel = QtWidgets.QLabel("")
        self.imageCountLabel.setStyleSheet("color: gray;")
        wstLayout.addWidget(self.imageCountLabel)

        wstLayout.addStretch()

        layout.addLayout(wstLayout)

        # Status label
        self.annotationStatusLabel = QtWidgets.QLabel("")
        layout.addWidget(self.annotationStatusLabel)

        return widget

    def _init_actions(self) -> None:
        """Initialize actions."""
        action = functools.partial(_new_action, self)

        open_file = action(
            self.tr("&Open Video"),
            self._open_file_dialog,
            "Ctrl+O",
            tip=self.tr("Open a video file"),
        )
        open_dir = action(
            self.tr("Open &Directory"),
            self._open_dir_dialog,
            "Ctrl+D",
            tip=self.tr("Open a directory containing videos"),
        )
        save_clips = action(
            self.tr("&Save Clips"),
            self._save_clips,
            "Ctrl+S",
            tip=self.tr("Save clip list to file"),
        )
        load_clips = action(
            self.tr("&Load Clips"),
            self._load_clips,
            "Ctrl+L",
            tip=self.tr("Load clip list from file"),
        )
        extract = action(
            self.tr("&Extract Frames"),
            self._extract_frames,
            "Ctrl+E",
            tip=self.tr("Extract frames from marked clips"),
        )
        quit_action = action(
            self.tr("&Quit"),
            self.close,
            "Ctrl+Q",
            tip=self.tr("Quit application"),
        )
        prev_video = action(
            self.tr("&Previous Video"),
            self._open_prev_video,
            "Ctrl+Left",
            tip=self.tr("Open previous video"),
        )
        next_video = action(
            self.tr("&Next Video"),
            self._open_next_video,
            "Ctrl+Right",
            tip=self.tr("Open next video"),
        )
        play_pause = action(
            self.tr("Play/Pause"),
            self._toggle_play,
            "Space",
            tip=self.tr("Toggle playback"),
        )
        prev_frame = action(
            self.tr("Previous Frame"),
            self._prev_frame,
            "Left",
            tip=self.tr("Go to previous frame"),
        )
        next_frame = action(
            self.tr("Next Frame"),
            self._next_frame,
            "Right",
            tip=self.tr("Go to next frame"),
        )
        mark_start = action(
            self.tr("Mark Start"),
            self._mark_start,
            "[",
            tip=self.tr("Mark clip start"),
        )
        mark_end = action(
            self.tr("Mark End"),
            self._mark_end,
            "]",
            tip=self.tr("Mark clip end"),
        )
        delete_clip = action(
            self.tr("Delete Clip"),
            self._delete_selected_clip,
            "Delete",
            tip=self.tr("Delete selected clip"),
        )
        jump_back = action(
            self.tr("Jump Backward"),
            self._jump_backward,
            "Shift+Left",
            tip=self.tr("Jump backward"),
        )
        jump_fwd = action(
            self.tr("Jump Forward"),
            self._jump_forward,
            "Shift+Right",
            tip=self.tr("Jump forward"),
        )
        
        # Caption search navigation
        prev_search = action(
            self.tr("Previous Search Result"),
            self._goto_prev_search_result,
            "Shift+Up",
            tip=self.tr("Go to previous caption search result"),
        )
        next_search = action(
            self.tr("Next Search Result"),
            self._goto_next_search_result,
            "Shift+Down",
            tip=self.tr("Go to next caption search result"),
        )

        # Object List action
        manage_object_list = action(
            self.tr("📋 Manage Object List"),
            self._manage_object_list,
            tip=self.tr("Import and manage object list for label selection"),
        )
        
        # Batch Process actions
        batch_caption_only = action(
            self.tr("📝 Caption Extraction Only"),
            lambda: self._batch_process(llm_analyze=False),
            tip=self.tr("Batch extract captions for all loaded videos"),
        )
        batch_caption_and_llm = action(
            self.tr("🤖 Caption + LLM Analysis"),
            lambda: self._batch_process(llm_analyze=True),
            tip=self.tr("Batch extract captions and analyze with LLM for all loaded videos"),
        )

        # Mode toggle action
        toggle_mode = action(
            self.tr("Toggle Video/Image Mode"),
            self._toggle_app_mode,
            "Ctrl+M",
            tip=self.tr("Switch between video clipping and image annotation modes"),
        )

        # Image annotation actions
        create_polygon = action(
            self.tr("Create Polygon"),
            lambda: self._set_create_mode("polygon"),
            "P",
            tip=self.tr("Start drawing a polygon"),
        )
        create_rectangle = action(
            self.tr("Create Rectangle"),
            lambda: self._set_create_mode("rectangle"),
            "R",
            tip=self.tr("Start drawing a rectangle"),
        )
        create_ai_polygon = action(
            self.tr("AI Polygon (SAM)"),
            lambda: self._set_create_mode("ai_polygon"),
            "A",
            tip=self.tr("AI-assisted polygon annotation using SAM"),
        )
        edit_mode = action(
            self.tr("🔧 Edit/Move"),
            self._toggle_edit_mode,
            "E",
            tip=self.tr("Toggle edit mode to move/resize shapes"),
        )
        edit_shape_label = action(
            self.tr("Edit Label"),
            self._edit_shape_label,
            tip=self.tr("Edit selected shape's label"),
        )
        delete_shape = action(
            self.tr("❌ Delete"),
            self._delete_selected_shapes,
            "Delete",
            tip=self.tr("Delete selected shapes"),
        )
        undo_shape = action(
            self.tr("Undo"),
            self._undo_shape_edit,
            "Ctrl+Z",
            tip=self.tr("Undo last shape edit"),
        )
        save_annotation = action(
            self.tr("Save Annotation"),
            self._save_annotation,
            "Ctrl+Shift+S",
            tip=self.tr("Save annotation to JSON file"),
        )

        self.actions = types.SimpleNamespace(
            open_file=open_file,
            open_dir=open_dir,
            save_clips=save_clips,
            load_clips=load_clips,
            extract=extract,
            quit=quit_action,
            prev_video=prev_video,
            next_video=next_video,
            play_pause=play_pause,
            prev_frame=prev_frame,
            next_frame=next_frame,
            mark_start=mark_start,
            mark_end=mark_end,
            delete_clip=delete_clip,
            jump_back=jump_back,
            jump_fwd=jump_fwd,
            prev_search=prev_search,
            next_search=next_search,
            manage_object_list=manage_object_list,
            batch_caption_only=batch_caption_only,
            batch_caption_and_llm=batch_caption_and_llm,
            toggle_mode=toggle_mode,
            create_polygon=create_polygon,
            create_rectangle=create_rectangle,
            create_ai_polygon=create_ai_polygon,
            edit_mode=edit_mode,
            edit_shape_label=edit_shape_label,
            delete_shape=delete_shape,
            undo_shape=undo_shape,
            save_annotation=save_annotation,
            about=action(
                text=f"&About {__appname__}",
                slot=functools.partial(
                    QMessageBox.about,
                    self,
                    f"About {__appname__}",
                    f"""
<h3>{__appname__}</h3>
<p>Video Clipping Tool for Frame Extraction</p>
<p>Version: {__version__}</p>
<p>Works with Labelme for video annotation workflows.</p>
""",
                ),
            ),
        )

    def _init_menus(self) -> None:
        """Initialize menus."""
        self.menus = types.SimpleNamespace(
            file=self.menuBar().addMenu(self.tr("&File")),
            edit=self.menuBar().addMenu(self.tr("&Edit")),
            view=self.menuBar().addMenu(self.tr("&View")),
            batch=self.menuBar().addMenu(self.tr("&Batch Process")),
            mode=self.menuBar().addMenu(self.tr("&Mode")),
            annotation=self.menuBar().addMenu(self.tr("&Annotation")),
            help=self.menuBar().addMenu(self.tr("&Help")),
        )

        # File menu
        self.menus.file.addAction(self.actions.open_file)
        self.menus.file.addAction(self.actions.open_dir)
        self.menus.file.addSeparator()
        self.menus.file.addAction(self.actions.prev_video)
        self.menus.file.addAction(self.actions.next_video)
        self.menus.file.addSeparator()
        self.menus.file.addAction(self.actions.manage_object_list)
        self.menus.file.addSeparator()
        self.menus.file.addAction(self.actions.save_clips)
        self.menus.file.addAction(self.actions.load_clips)
        self.menus.file.addAction(self.actions.save_annotation)
        self.menus.file.addSeparator()
        self.menus.file.addAction(self.actions.extract)
        self.menus.file.addSeparator()
        self.menus.file.addAction(self.actions.quit)

        # Edit menu
        self.menus.edit.addAction(self.actions.mark_start)
        self.menus.edit.addAction(self.actions.mark_end)
        self.menus.edit.addSeparator()
        self.menus.edit.addAction(self.actions.delete_clip)
        self.menus.edit.addSeparator()
        self.menus.edit.addAction(self.actions.jump_back)
        self.menus.edit.addAction(self.actions.jump_fwd)

        # View menu
        self.menus.view.addAction(self.file_dock.toggleViewAction())
        self.menus.view.addAction(self.clip_dock.toggleViewAction())
        self.menus.view.addAction(self.shape_dock.toggleViewAction())
        self.menus.view.addAction(self.controls_dock.toggleViewAction())
        self.menus.view.addAction(self.annotation_dock.toggleViewAction())

        # Batch Process menu
        self.menus.batch.addAction(self.actions.batch_caption_only)
        self.menus.batch.addAction(self.actions.batch_caption_and_llm)

        # Mode menu
        self.menus.mode.addAction(self.actions.toggle_mode)

        # Annotation menu (for image mode)
        self.menus.annotation.addAction(self.actions.create_polygon)
        self.menus.annotation.addAction(self.actions.create_rectangle)
        self.menus.annotation.addAction(self.actions.create_ai_polygon)
        self.menus.annotation.addSeparator()
        self.menus.annotation.addAction(self.actions.edit_mode)
        self.menus.annotation.addSeparator()
        self.menus.annotation.addAction(self.actions.save_annotation)

        # Help menu
        self.menus.help.addAction(self.actions.about)

    def _init_toolbar(self) -> None:
        """Initialize toolbar."""
        toolbar = QtWidgets.QToolBar("Main Toolbar")
        toolbar.setObjectName("MainToolbar")
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        toolbar.addAction(self.actions.open_file)
        toolbar.addAction(self.actions.open_dir)
        toolbar.addSeparator()
        toolbar.addAction(self.actions.prev_video)
        toolbar.addAction(self.actions.next_video)
        toolbar.addSeparator()
        toolbar.addAction(self.actions.extract)
        toolbar.addSeparator()

        # Batch Process button
        self.batchProcessBtn = QtWidgets.QPushButton("⚡ Batch Process")
        self.batchProcessBtn.setToolTip("Batch process multiple videos (Caption + LLM)")
        self.batchProcessBtn.clicked.connect(self._show_batch_process_dialog)
        toolbar.addWidget(self.batchProcessBtn)
        toolbar.addSeparator()

        # Mode toggle button
        self.modeToggleBtn = QtWidgets.QPushButton("🎬 Video Mode")
        self.modeToggleBtn.setCheckable(True)
        self.modeToggleBtn.setToolTip(
            "Switch between Video clipping and Image annotation modes"
        )
        self.modeToggleBtn.clicked.connect(self._toggle_app_mode)
        toolbar.addWidget(self.modeToggleBtn)

    def _init_statusbar(self) -> None:
        """Initialize status bar."""
        self.statusBar().showMessage(self.tr("%s started.") % __appname__)

    def _init_timer(self) -> None:
        """Initialize playback timer."""
        self._playback_timer = QtCore.QTimer()
        self._playback_timer.timeout.connect(self._on_timer_tick)
        self._slider_dragging = False

    # Video loading methods

    def _get_container_duration_ffprobe(self, video_path: str) -> float | None:
        """Get container duration from ffprobe.
        
        Returns the CONTAINER duration (format.duration), which is what
        QuickTime, VLC, and other players use as the total timeline.
        
        This may be longer than the video stream duration if the audio
        track is longer. In that case, video frames are "stretched" to
        fill the container duration (the last frame holds until audio ends).
        
        Args:
            video_path: Path to video file
            
        Returns:
            Container duration in seconds, or None if detection failed
        """
        try:
            import subprocess
            import json as _json
            
            # Find ffprobe executable
            ffprobe = _find_executable("ffprobe")
            if not ffprobe:
                logger.warning("ffprobe not found in PATH. Using OpenCV duration fallback.")
                return None
            
            cmd = [
                ffprobe,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                video_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout:
                probe = _json.loads(result.stdout)
                duration = float(probe["format"]["duration"])
                logger.info("Container duration from ffprobe: {:.3f}s", duration)
                return duration
            
            return None
        except Exception as e:
            logger.warning("Failed to get duration from ffprobe: {}", e)
            return None

    def _load_video(self, filename: str) -> bool:
        """Load a video file."""
        # Stop playback
        if self._is_playing:
            self._toggle_play()

        if self._video_capture is not None:
            self._video_capture.release()
            self._video_capture = None

        try:
            self._video_capture = cv2.VideoCapture(filename)
            if not self._video_capture.isOpened():
                QMessageBox.critical(
                    self,
                    self.tr("Error"),
                    self.tr("Failed to open video: %s") % filename,
                )
                return False

            self.filename = filename
            self._total_frames = int(self._video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Get nominal FPS from cv2
            cv2_fps = self._video_capture.get(cv2.CAP_PROP_FPS) or 30.0
            self._fps = cv2_fps
            
            # Get CONTAINER duration from ffprobe
            # QuickTime/VLC use container duration as the timeline, not video stream duration.
            # When audio is longer than video, the video frames are "stretched" across
            # the container duration (last frame holds until audio ends).
            # We must use container duration for correct sync with these players.
            container_duration = self._get_container_duration_ffprobe(filename)
            cv2_duration = self._total_frames / cv2_fps if cv2_fps > 0 else 0
            
            # Use container duration from ffprobe (matches QuickTime behavior)
            if container_duration and container_duration > 0:
                self._actual_duration = container_duration
            else:
                self._actual_duration = cv2_duration
            
            # Effective FPS = total_frames / container_duration
            # This ensures video plays over the same duration as QuickTime
            if self._actual_duration > 0 and self._total_frames > 0:
                self._effective_fps = self._total_frames / self._actual_duration
            else:
                self._effective_fps = cv2_fps
            
            # Log timing info for debugging
            speed_diff = ((cv2_fps / self._effective_fps) - 1.0) * 100 if self._effective_fps > 0 else 0
            logger.info(
                "Video timing: cv2_fps={:.3f}, container_duration={:.3f}s, "
                "effective_fps={:.3f}, speed_correction={:.1f}%",
                cv2_fps, self._actual_duration,
                self._effective_fps, speed_diff,
            )
            
            self._frame_width = int(self._video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            self._frame_height = int(self._video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self._current_frame = 0
            self._last_displayed_frame = -1

            # Reset output directory for new video - will be created on first use
            self._video_output_dir = None
            
            # Set auto-save path in video output directory: <video_dir>/<video_name>/clips.csv
            video_output_dir = self._get_video_output_dir()  # Creates <video_dir>/<video_name>/
            self._auto_save_path = osp.join(video_output_dir, "clips.csv") if video_output_dir else None

            # Update UI
            self.timelineSlider.setMaximum(max(0, self._total_frames - 1))
            self.timelineSlider.setValue(0)
            
            # Update clip timeline
            self.clipTimeline.setTotalFrames(self._total_frames)
            self.clipTimeline.setCurrentFrame(0)
            
            # Update FPS spinbox to show effective FPS
            self.fpsSpinBox.blockSignals(True)
            self.fpsSpinBox.setValue(self._effective_fps)
            self.fpsSpinBox.blockSignals(False)
            
            self._update_frame_display()
            self._seek_to_frame(0)

            # Clear clips and pending state
            self._clips.clear()
            self._pending_start_frame = None
            self.pendingLabel.setText("")
            self.markEndBtn.setEnabled(False)

            # Try to auto-load existing clips CSV
            self._auto_load_clips()

            self._update_clip_list()
            self._is_changed = False

            # Update window title
            self.setWindowTitle(f"{__appname__} - {osp.basename(filename)}")
            
            # Calculate video duration using actual container duration
            duration_sec = self._actual_duration
            duration_str = _format_time(duration_sec)
            
            self.statusBar().showMessage(
                self.tr("Loaded: %s | %dx%d | %d frames | %.2f eff.fps | Duration: %s")
                % (
                    osp.basename(filename),
                    self._frame_width,
                    self._frame_height,
                    self._total_frames,
                    self._effective_fps,
                    duration_str,
                )
            )

            logger.info(
                "Loaded video: {} ({}x{}, {} frames, {:.2f} eff.fps, {})",
                filename,
                self._frame_width,
                self._frame_height,
                self._total_frames,
                self._effective_fps,
                duration_str,
            )

            # Clean up previous audio and load new
            self._cleanup_extracted_audio()
            if self._audio_player:
                self._audio_player.stop()
            self._load_audio_for_video(filename)

            # Clear previous captions before auto-loading
            self._caption_segments = []
            self._current_caption = ""
            self.captionLabel.setText("")
            self.captionLabel.hide()
            self.exportCaptionsBtn.setEnabled(False)
            if self._whisper_transcriber:
                self._whisper_transcriber.clear()

            # Try to auto-load existing captions SRT (after clearing)
            self._auto_load_captions()

            return True

        except Exception as e:
            logger.error("Failed to load video {}: {}", filename, e)
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("Failed to open video: %s\n\nError: %s") % (filename, str(e)),
            )
            return False

    def _auto_load_clips(self) -> None:
        """Auto-load clips CSV file from video output directory."""
        if not self._auto_save_path:
            return
            
        # Check new location: <video_dir>/<video_name>/clips.csv
        if osp.exists(self._auto_save_path):
            try:
                self._read_clips_csv(self._auto_save_path)
                logger.info(
                    "Auto-loaded {} clips from {}", len(self._clips), self._auto_save_path
                )
                self.statusBar().showMessage(
                    self.tr("Auto-loaded %d clips from %s")
                    % (len(self._clips), osp.basename(self._auto_save_path)),
                    5000,
                )
                return
            except Exception as e:
                logger.warning("Failed to auto-load clips from {}: {}", self._auto_save_path, e)
        
        # Also check legacy location: <video_path>_clips.csv
        if self.filename:
            legacy_path = osp.splitext(self.filename)[0] + "_clips.csv"
            if osp.exists(legacy_path):
                try:
                    self._read_clips_csv(legacy_path)
                    logger.info(
                        "Auto-loaded {} clips from legacy path {}", len(self._clips), legacy_path
                    )
                    self.statusBar().showMessage(
                        self.tr("Auto-loaded %d clips from %s (legacy location)")
                        % (len(self._clips), osp.basename(legacy_path)),
                        5000,
                    )
                except Exception as e:
                    logger.warning("Failed to auto-load clips from legacy path: {}", e)

    def _auto_load_captions(self) -> None:
        """Auto-load SRT captions file from video output directory."""
        if not self.filename:
            logger.debug("_auto_load_captions: No filename set")
            return

        video_name = osp.splitext(osp.basename(self.filename))[0]
        srt_path = None
        
        logger.debug("_auto_load_captions: Looking for captions for video: {}", video_name)
        logger.debug("_auto_load_captions: _video_output_dir = {}", self._video_output_dir)
        
        # Check new location: <video_dir>/<video_name>/captions/<video_name>.srt
        if self._video_output_dir:
            captions_dir = osp.join(self._video_output_dir, "captions")
            new_srt_path = osp.join(captions_dir, f"{video_name}.srt")
            logger.debug("_auto_load_captions: Checking new path: {} (exists: {})", 
                        new_srt_path, osp.exists(new_srt_path))
            if osp.exists(new_srt_path):
                srt_path = new_srt_path
        
        # Also check for legacy location (same directory as video)
        if not srt_path:
            legacy_srt_path = osp.splitext(self.filename)[0] + ".srt"
            logger.debug("_auto_load_captions: Checking legacy path: {} (exists: {})", 
                        legacy_srt_path, osp.exists(legacy_srt_path))
            if osp.exists(legacy_srt_path):
                srt_path = legacy_srt_path
        
        if not srt_path:
            logger.debug("_auto_load_captions: No SRT file found")
            return
        
        logger.info("_auto_load_captions: Found SRT file at {}", srt_path)
        
        # Load SRT without requiring Whisper (just need to parse the file)
        try:
            # Load SRT file directly (no need for Whisper transcriber)
            self._caption_segments = self._load_srt_file(srt_path)

            if self._caption_segments:
                logger.info("Auto-loaded {} captions from {}", len(self._caption_segments), srt_path)
                self.statusBar().showMessage(
                    self.tr("Auto-loaded %d captions from %s")
                    % (len(self._caption_segments), osp.basename(srt_path)),
                    3000,
                )
                self.exportCaptionsBtn.setEnabled(True)
                # Enable search if we have text in search box
                if self.captionSearchInput.text().strip():
                    self.searchCaptionsBtn.setEnabled(True)
                # Enable LLM analysis widget
                self.captionAnalysisWidget.setEnabled(True)
                # Auto-show captions when loaded from file
                self.captionLabel.show()
                self._update_caption_display()
                logger.info("Caption label shown, segments loaded: {}", len(self._caption_segments))
        except Exception as e:
            logger.warning("Failed to auto-load captions: {}", e)
            import traceback
            logger.warning("Traceback: {}", traceback.format_exc())

    def _load_srt_file(self, srt_path: str) -> list:
        """Load caption segments from SRT file.
        
        Args:
            srt_path: Path to SRT file
            
        Returns:
            List of TranscriptSegment objects (or simple dicts if Whisper not available)
        """
        segments = []
        try:
            with open(srt_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            i = 0
            while i < len(lines):
                # Skip empty lines
                if not lines[i].strip():
                    i += 1
                    continue

                # Read index
                if not lines[i].strip().isdigit():
                    i += 1
                    continue
                i += 1

                # Read timestamp
                if i >= len(lines):
                    break
                timestamp_line = lines[i].strip()
                if " --> " not in timestamp_line:
                    i += 1
                    continue

                start_str, end_str = timestamp_line.split(" --> ")
                start_sec = self._parse_srt_time(start_str)
                end_sec = self._parse_srt_time(end_str)
                i += 1

                # Read text (may be multiple lines)
                text_lines = []
                while i < len(lines) and lines[i].strip():
                    text_lines.append(lines[i].strip())
                    i += 1

                text = " ".join(text_lines)

                # Try to use TranscriptSegment dataclass, fallback to dict
                try:
                    from labelvid._whisper._transcriber import TranscriptSegment
                    segments.append(TranscriptSegment(
                        start=start_sec,
                        end=end_sec,
                        text=text,
                    ))
                except ImportError:
                    # Fallback: use simple dict-like object
                    class SimpleSegment:
                        def __init__(self, start, end, text):
                            self.start = start
                            self.end = end
                            self.text = text
                    segments.append(SimpleSegment(start_sec, end_sec, text))

            # Store in transcriber if available
            if self._whisper_transcriber:
                self._whisper_transcriber._segments = segments

            logger.debug("Loaded {} segments from SRT file", len(segments))
            return segments
        except Exception as e:
            logger.error("Error loading SRT file {}: {}", srt_path, e)
            import traceback
            logger.error("Traceback: {}", traceback.format_exc())
            return []

    def _parse_srt_time(self, time_str: str) -> float:
        """Parse SRT timestamp to seconds.
        
        Args:
            time_str: Time string like "00:01:23,456"
            
        Returns:
            Time in seconds
        """
        # Format: HH:MM:SS,mmm
        time_str = time_str.replace(",", ".")
        parts = time_str.split(":")
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds

    def _auto_save_clips(self) -> None:
        """Auto-save clips to CSV file."""
        if not self._auto_save_path:
            return

        try:
            self._write_clips_csv(self._auto_save_path)
            self._is_changed = False
            logger.debug("Auto-saved {} clips to {}", len(self._clips), self._auto_save_path)
            self.statusBar().showMessage(
                self.tr("Auto-saved %d clips") % len(self._clips), 2000
            )
        except Exception as e:
            logger.error("Failed to auto-save clips: {}", e)
            self.statusBar().showMessage(
                self.tr("Failed to auto-save: %s") % str(e), 5000
            )

    def _open_file_dialog(self) -> None:
        """Open file dialog to select a video."""
        if not self._can_continue():
            return

        path = osp.dirname(self.filename) if self.filename else "."
        filters = self.tr("Video files (%s)") % " ".join(
            f"*{ext}" for ext in VIDEO_EXTENSIONS
        )
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.tr("%s - Open Video") % __appname__,
            path,
            filters,
        )
        if filename:
            self._load_video(filename)

    def _open_dir_dialog(self) -> None:
        """Open directory dialog to select a folder with videos."""
        if not self._can_continue():
            return

        default_dir = self._prev_opened_dir or (
            osp.dirname(self.filename) if self.filename else "."
        )
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            self.tr("%s - Open Directory") % __appname__,
            default_dir,
            QtWidgets.QFileDialog.ShowDirsOnly,
        )
        if dir_path:
            self._import_videos_from_dir(root_dir=dir_path)
            self._open_next_video()

    def _import_videos_from_dir(
        self, root_dir: str | None, pattern: str | None = None
    ) -> None:
        """Import videos from a directory."""
        if not root_dir:
            return

        self._prev_opened_dir = root_dir
        self.fileListWidget.clear()

        videos = _scan_video_files(root_dir)
        if pattern:
            import re

            try:
                videos = [v for v in videos if re.search(pattern, v)]
            except re.error:
                pass

        for video in videos:
            item = QtWidgets.QListWidgetItem(video)
            self.fileListWidget.addItem(item)

        logger.info("Found {} videos in {}", len(videos), root_dir)

    def _file_search_changed(self) -> None:
        """Handle file search text change."""
        self._import_videos_from_dir(
            root_dir=self._prev_opened_dir, pattern=self.fileSearch.text()
        )

    def _file_selection_changed(self) -> None:
        """Handle file selection change."""
        items = self.fileListWidget.selectedItems()
        if not items:
            return

        if not self._can_continue():
            return

        filename = items[0].text()
        self._load_video(filename)

    def _open_prev_video(self) -> None:
        """Open previous video in list."""
        row = self.fileListWidget.currentRow() - 1
        if row >= 0:
            self.fileListWidget.setCurrentRow(row)

    def _open_next_video(self) -> None:
        """Open next video in list."""
        row = self.fileListWidget.currentRow() + 1
        if row < self.fileListWidget.count():
            self.fileListWidget.setCurrentRow(row)

    @property
    def videoList(self) -> list[str]:
        """Get list of video filenames."""
        return [
            self.fileListWidget.item(i).text()
            for i in range(self.fileListWidget.count())
        ]

    # Playback control methods

    def _toggle_play(self) -> None:
        """Toggle video playback."""
        if self._video_capture is None:
            return

        self._is_playing = not self._is_playing
        if self._is_playing:
            self.playPauseBtn.setText("⏸ Pause")
            # Record wall-clock start time so we can sync by time instead of tick count
            # Use _effective_fps (= total_frames / actual_duration) for correct timing
            now_ms = time.monotonic() * 1000.0
            current_video_ms = (self._current_frame / self._effective_fps) * 1000.0 if self._effective_fps > 0 else 0
            self._playback_start_ms = now_ms - (current_video_ms / self._playback_speed)

            # Run timer at ~60fps (16ms) for smoother sync; we compute target frame from time
            self._playback_timer.start(16)
            logger.debug(
                "Playback started: effective_fps={:.3f}, speed={}, current_frame={}, start_ms={}",
                self._effective_fps,
                self._playback_speed,
                self._current_frame,
                self._playback_start_ms,
            )
            # Start audio playback
            self._play_audio()
        else:
            self.playPauseBtn.setText("▶ Play")
            self._playback_timer.stop()
            self._playback_start_ms = None
            # Pause audio playback
            self._pause_audio()

    def _on_timer_tick(self) -> None:
        """Handle playback timer tick.
        
        Uses wall-clock time to determine which frame to display,
        matching how QuickTime/VLC/Gradio play videos.
        
        Key insight: We use _effective_fps (= total_frames / actual_container_duration)
        for timing, NOT the nominal FPS from cv2. This ensures the video plays
        over the correct real-world duration.
        
        When audio is enabled, we sync video to the audio position instead,
        since the audio player already uses the correct container timing.
        """
        if self._video_capture is None or self._effective_fps <= 0:
            self._toggle_play()
            return

        # If audio is enabled and playing, sync video to audio position
        if self._audio_player and self._audio_enabled and AUDIO_AVAILABLE:
            # Get current audio position in milliseconds
            audio_pos_ms = self._audio_player.position()
            # Convert audio time to frame number using effective FPS
            target_frame = int((audio_pos_ms / 1000.0) * self._effective_fps)
            
            # Debug: log periodically
            if target_frame % 60 == 0 and target_frame != self._current_frame:
                logger.debug(
                    "A/V sync: audio_pos={}ms, target_frame={}, current_frame={}, eff_fps={:.3f}",
                    audio_pos_ms, target_frame, self._current_frame, self._effective_fps,
                )
        else:
            # No audio — use wall-clock time
            if self._playback_start_ms is None:
                now_ms = time.monotonic() * 1000.0
                current_video_ms = (self._current_frame / self._effective_fps) * 1000.0
                self._playback_start_ms = now_ms - (current_video_ms / self._playback_speed)

            elapsed_ms = (time.monotonic() * 1000.0) - self._playback_start_ms
            # elapsed_ms * speed gives real video time elapsed
            video_time_ms = elapsed_ms * self._playback_speed
            target_frame = int((video_time_ms / 1000.0) * self._effective_fps)

        if target_frame >= self._total_frames:
            self._toggle_play()
            return

        # Only advance if target is ahead of current
        if target_frame > self._current_frame:
            self._current_frame = target_frame
            try:
                # Use time-based seeking (POS_MSEC) for better accuracy
                # This lets OpenCV use the container timestamps directly
                target_ms = (target_frame / self._effective_fps) * 1000.0
                self._video_capture.set(cv2.CAP_PROP_POS_MSEC, target_ms)
                ret, frame = self._video_capture.read()

                if ret and frame is not None:
                    preview_frame = self._scale_frame_for_preview(frame)
                    self.videoPlayer.display_frame(preview_frame)
                    self._last_displayed_frame = target_frame
                else:
                    logger.warning("Failed to read frame {} (target_ms={:.1f})", target_frame, target_ms)

                if not self._slider_dragging:
                    self.timelineSlider.blockSignals(True)
                    self.timelineSlider.setValue(self._current_frame)
                    self.timelineSlider.blockSignals(False)

                # Update frame display (time, captions)
                self._update_frame_display()
            except Exception as e:
                logger.error("Playback error at frame {}: {}", self._current_frame, e)
                self._toggle_play()
        elif target_frame == self._current_frame:
            # Still update caption display even if frame hasn't changed
            self._update_frame_display()

    def _prev_frame(self) -> None:
        """Go to previous frame."""
        if self._current_frame > 0:
            self._current_frame -= 1
            self._seek_to_frame(self._current_frame)
            self.timelineSlider.setValue(self._current_frame)

    def _next_frame(self) -> None:
        """Go to next frame."""
        if self._current_frame < self._total_frames - 1:
            self._current_frame += 1
            self._seek_to_frame(self._current_frame)
            self.timelineSlider.setValue(self._current_frame)

    def _on_slider_changed(self, value: int) -> None:
        """Handle slider value change."""
        self._current_frame = value
        self._seek_to_frame(value)
        self._update_frame_display()

    def _on_slider_pressed(self) -> None:
        """Handle slider press."""
        self._slider_dragging = True

    def _on_slider_released(self) -> None:
        """Handle slider release."""
        self._slider_dragging = False
        if self._is_playing:
            # Reset wall-clock origin after manual seek
            now_ms = time.monotonic() * 1000.0
            current_video_ms = (self._current_frame / self._effective_fps) * 1000.0 if self._effective_fps > 0 else 0
            self._playback_start_ms = now_ms - (current_video_ms / self._playback_speed)
            # Sync audio position after seeking
            self._sync_audio_position()

    def _on_speed_changed(self, text: str) -> None:
        """Handle playback speed change."""
        speed_map = {
            "0.25x": 0.25,
            "0.5x": 0.5,
            "1x": 1.0,
            "1.5x": 1.5,
            "2x": 2.0,
            "4x": 4.0,
        }
        self._playback_speed = speed_map.get(text, 1.0)
        if self._is_playing:
            # Reset wall-clock origin so timing stays correct after speed change
            now_ms = time.monotonic() * 1000.0
            current_video_ms = (self._current_frame / self._effective_fps) * 1000.0 if self._effective_fps > 0 else 0
            self._playback_start_ms = now_ms - (current_video_ms / self._playback_speed)

        # Update audio playback rate
        if self._audio_player and AUDIO_AVAILABLE:
            self._audio_player.setPlaybackRate(self._playback_speed)

    def _on_fps_adjusted(self, value: float) -> None:
        """Handle manual effective FPS adjustment."""
        self._effective_fps = value
        # Also update actual_duration to stay consistent
        if self._total_frames > 0 and value > 0:
            self._actual_duration = self._total_frames / value
        logger.info("Effective FPS manually adjusted to: {:.2f} (duration={:.3f}s)", 
                    self._effective_fps, self._actual_duration)
        
        # Update time display immediately
        self._update_frame_display()
        
        # If playing, restart playback with new timing
        if self._is_playing:
            self._toggle_play()  # Stop
            QtCore.QTimer.singleShot(50, self._toggle_play)  # Restart after a short delay
        
        # Update audio sync if needed
        if self._audio_player and AUDIO_AVAILABLE and self._audio_player.state() == QtMultimedia.QMediaPlayer.PlayingState:
            self._sync_audio_position()

    def _on_quality_changed(self, text: str) -> None:
        """Handle preview quality change."""
        self._preview_scale = self.PREVIEW_SCALES.get(text, 0.5)
        logger.info("Preview quality changed to: {} (scale={})", text, self._preview_scale)
        
        # Show preview resolution info
        if self._frame_width > 0 and self._frame_height > 0:
            preview_w = int(self._frame_width * self._preview_scale)
            preview_h = int(self._frame_height * self._preview_scale)
            self.statusBar().showMessage(
                self.tr("Preview: %dx%d (Original: %dx%d) - Extract uses original quality")
                % (preview_w, preview_h, self._frame_width, self._frame_height),
                3000,
            )
        
        # Force refresh current frame to apply new quality settings
        self._last_displayed_frame = -1
        self._seek_to_frame(self._current_frame, force=True)

    # =========================================================================
    # Audio and Caption Methods
    # =========================================================================

    def _init_audio_player(self) -> None:
        """Initialize audio player for video playback."""
        if not AUDIO_AVAILABLE:
            logger.warning("Audio playback not available - PyQt5 multimedia not installed")
            return

        if self._audio_player is None:
            # Create media player without flags for better compatibility
            self._audio_player = QMediaPlayer()
            self._audio_player.setVolume(self.volumeSlider.value())
            # Connect error signal for debugging
            self._audio_player.error.connect(self._on_audio_error)
            self._audio_player.mediaStatusChanged.connect(self._on_audio_status_changed)
            self._audio_player.stateChanged.connect(self._on_audio_state_changed)
            logger.info("Audio player initialized")

    def _on_audio_state_changed(self, state) -> None:
        """Handle audio player state changes."""
        from PyQt5.QtMultimedia import QMediaPlayer as QMP
        state_names = {
            QMP.StoppedState: "Stopped",
            QMP.PlayingState: "Playing",
            QMP.PausedState: "Paused",
        }
        logger.info("Audio state changed: {}", state_names.get(state, state))

    def _on_audio_error(self, error) -> None:
        """Handle audio player errors."""
        if self._audio_player:
            error_string = self._audio_player.errorString()
            logger.error("Audio player error: {} - {}", error, error_string)
            self.statusBar().showMessage(
                self.tr("Audio error: %s") % error_string, 5000
            )

    def _on_audio_status_changed(self, status) -> None:
        """Handle audio player status changes."""
        from PyQt5.QtMultimedia import QMediaPlayer as QMP
        status_names = {
            QMP.UnknownMediaStatus: "Unknown",
            QMP.NoMedia: "NoMedia",
            QMP.LoadingMedia: "Loading",
            QMP.LoadedMedia: "Loaded",
            QMP.StalledMedia: "Stalled",
            QMP.BufferingMedia: "Buffering",
            QMP.BufferedMedia: "Buffered",
            QMP.EndOfMedia: "EndOfMedia",
            QMP.InvalidMedia: "InvalidMedia",
        }
        logger.debug("Audio status: {}", status_names.get(status, status))

    def _check_video_has_audio(self, video_path: str) -> bool:
        """Check if video file has an audio stream using ffprobe."""
        try:
            import subprocess

            # Find ffprobe executable
            ffprobe = _find_executable("ffprobe")
            if not ffprobe:
                logger.warning("ffprobe not found. Cannot check audio stream.")
                return True  # Assume has audio if ffprobe not available

            cmd = [
                ffprobe,
                "-v", "error",
                "-select_streams", "a",
                "-show_entries", "stream=codec_type",
                "-of", "csv=p=0",
                video_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return "audio" in result.stdout
        except Exception as e:
            logger.warning("Could not check audio stream: {}", e)
            return True  # Assume has audio if check fails

    def _extract_audio_to_file(self, video_path: str) -> str | None:
        """Extract audio from video to a temporary WAV file using ffmpeg.
        
        This handles videos with codecs not supported by macOS/QuickTime.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to extracted audio file, or None if extraction failed
        """
        import subprocess
        import tempfile

        # Clean up previous extracted audio
        self._cleanup_extracted_audio()

        try:
            # Find ffmpeg executable
            ffmpeg = _find_executable("ffmpeg")
            if not ffmpeg:
                logger.error("ffmpeg not found in PATH. Cannot extract audio.")
                QMessageBox.warning(
                    self,
                    "FFmpeg Not Found",
                    "ffmpeg is required for audio playback but was not found.\n\n"
                    "Please install ffmpeg:\n"
                    "• macOS: brew install ffmpeg\n"
                    "• Ubuntu: sudo apt install ffmpeg\n"
                    "• Windows: choco install ffmpeg"
                )
                return None

            # Create temp file for extracted audio
            fd, audio_path = tempfile.mkstemp(suffix=".wav", prefix="labelvid_audio_")
            os.close(fd)

            # Use ffmpeg to extract and convert audio to WAV (universal format)
            cmd = [
                ffmpeg,
                "-i", video_path,
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # PCM 16-bit (universal)
                "-ar", "44100",  # 44.1kHz sample rate
                "-ac", "2",  # Stereo
                "-y",  # Overwrite
                audio_path,
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error("ffmpeg audio extraction failed: {}", result.stderr)
                if osp.exists(audio_path):
                    os.remove(audio_path)
                return None

            self._extracted_audio_path = audio_path
            logger.info("Extracted audio to: {}", audio_path)
            return audio_path

        except Exception as e:
            logger.error("Failed to extract audio: {}", e)
            return None

    def _cleanup_extracted_audio(self) -> None:
        """Clean up temporary extracted audio file."""
        if self._extracted_audio_path and osp.exists(self._extracted_audio_path):
            try:
                os.remove(self._extracted_audio_path)
                logger.debug("Cleaned up extracted audio: {}", self._extracted_audio_path)
            except Exception as e:
                logger.warning("Failed to clean up audio file: {}", e)
        self._extracted_audio_path = None

    def _load_audio_for_video(self, video_path: str) -> None:
        """Load audio from video file for playback.
        
        Uses ffmpeg to extract audio to a universal format (WAV) for compatibility
        with videos that use Windows-only codecs.
        """
        if not AUDIO_AVAILABLE or not self._audio_enabled:
            logger.info("Audio not loading: available={}, enabled={}", 
                       AUDIO_AVAILABLE, self._audio_enabled)
            return

        # Check if video has audio stream
        if not self._check_video_has_audio(video_path):
            logger.warning("Video has no audio stream: {}", video_path)
            self.statusBar().showMessage(
                self.tr("Video has no audio stream"), 3000
            )
            self.audioEnableCheck.setEnabled(False)
            self.audioEnableCheck.setToolTip(
                self.tr("This video has no audio stream")
            )
            return

        # Re-enable audio checkbox if it was disabled
        self.audioEnableCheck.setEnabled(True)
        self.audioEnableCheck.setToolTip("")

        self._init_audio_player()
        if self._audio_player is None:
            return

        # Extract audio using ffmpeg for codec compatibility
        self.statusBar().showMessage(self.tr("Extracting audio..."), 0)
        QtWidgets.QApplication.processEvents()

        audio_path = self._extract_audio_to_file(video_path)
        
        if audio_path:
            # Load extracted audio file
            url = QtCore.QUrl.fromLocalFile(audio_path)
            content = QMediaContent(url)
            self._audio_player.setMedia(content)
            logger.info("Audio loaded from extracted file: {}", audio_path)
            self.statusBar().showMessage(self.tr("Audio ready"), 2000)
        else:
            # Fallback: try loading video directly (may not work for all codecs)
            logger.warning("Audio extraction failed, trying direct load")
            abs_path = osp.abspath(video_path)
            url = QtCore.QUrl.fromLocalFile(abs_path)
            content = QMediaContent(url)
            self._audio_player.setMedia(content)
            self.statusBar().showMessage(
                self.tr("Audio extraction failed - playback may not work"), 3000
            )

    def _on_audio_toggle(self, state: int) -> None:
        """Handle audio enable/disable toggle."""
        self._audio_enabled = state == Qt.Checked
        self.volumeSlider.setEnabled(self._audio_enabled)

        if self._audio_enabled:
            # Load audio if video is loaded but audio player not initialized
            if self.filename and self._audio_player is None:
                self._load_audio_for_video(self.filename)
            elif self._audio_player:
                # Sync audio position with video
                self._sync_audio_position()
                if self._is_playing:
                    self._audio_player.play()
        else:
            if self._audio_player:
                self._audio_player.pause()

        logger.info("Audio playback: {}", "enabled" if self._audio_enabled else "disabled")

    def _on_volume_changed(self, value: int) -> None:
        """Handle volume slider change."""
        if self._audio_player:
            self._audio_player.setVolume(value)

    def _sync_audio_position(self) -> None:
        """Sync audio player position with current video frame."""
        if not self._audio_player or not self._audio_enabled:
            return

        if self._effective_fps > 0:
            position_ms = int((self._current_frame / self._effective_fps) * 1000)
            self._audio_player.setPosition(position_ms)

    def _play_audio(self) -> None:
        """Start audio playback."""
        if self._audio_player and self._audio_enabled:
            self._sync_audio_position()
            # Set playback rate to match video speed
            self._audio_player.setPlaybackRate(self._playback_speed)
            self._audio_player.play()
            logger.info(
                "Audio play: state={}, volume={}, position={}ms, rate={}",
                self._audio_player.state(),
                self._audio_player.volume(),
                self._audio_player.position(),
                self._audio_player.playbackRate(),
            )
        else:
            logger.debug("Audio play skipped: player={}, enabled={}", 
                        self._audio_player is not None, self._audio_enabled)

    def _pause_audio(self) -> None:
        """Pause audio playback."""
        if self._audio_player:
            self._audio_player.pause()
            logger.debug("Audio paused")

    def _on_whisper_toggle(self, state: int) -> None:
        """Handle Whisper caption enable/disable toggle."""
        self._whisper_enabled = state == Qt.Checked
        self.whisperModelCombo.setEnabled(self._whisper_enabled)
        self.whisperLangCombo.setEnabled(self._whisper_enabled)
        self.extractCaptionsBtn.setEnabled(self._whisper_enabled)

        if self._whisper_enabled and self._caption_segments:
            self.captionLabel.show()
            self._update_caption_display()
        else:
            self.captionLabel.hide()

        logger.info("Whisper captions: {}", "enabled" if self._whisper_enabled else "disabled")

    def _on_whisper_model_changed(self, model_name: str) -> None:
        """Handle Whisper model selection change."""
        self._whisper_model_name = model_name
        # Reset transcriber to use new model
        if self._whisper_transcriber:
            self._whisper_transcriber.model_name = model_name
        logger.info("Whisper model changed to: {}", model_name)

    def _extract_captions(self) -> None:
        """Extract captions from current video using Whisper."""
        if not WHISPER_AVAILABLE:
            QMessageBox.warning(
                self,
                self.tr("Whisper Not Available"),
                self.tr("Please install Whisper: pip install openai-whisper"),
            )
            return

        if not self.filename:
            QMessageBox.warning(
                self,
                self.tr("No Video"),
                self.tr("Please load a video first."),
            )
            return

        # Create progress dialog
        progress = QtWidgets.QProgressDialog(
            self.tr("Extracting captions..."),
            self.tr("Cancel"),
            0, 100,
            self,
        )
        progress.setWindowTitle(self.tr("Whisper Transcription"))
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()

        def update_progress(value: float, message: str) -> None:
            if progress.wasCanceled():
                return
            progress.setValue(int(value * 100))
            progress.setLabelText(message)
            QtWidgets.QApplication.processEvents()

        try:
            # Initialize transcriber if needed
            if self._whisper_transcriber is None:
                self._whisper_transcriber = WhisperTranscriber(self._whisper_model_name)
            else:
                self._whisper_transcriber.model_name = self._whisper_model_name

            # Get language setting
            lang = self.whisperLangCombo.currentText()
            if lang == "auto":
                lang = None

            # Transcribe
            self._caption_segments = self._whisper_transcriber.transcribe(
                self.filename,
                language=lang,
                progress_callback=update_progress,
            )

            progress.close()

            # Show caption display
            self.captionLabel.show()
            self.exportCaptionsBtn.setEnabled(True)
            # Enable search if we have text in search box
            if self.captionSearchInput.text().strip():
                self.searchCaptionsBtn.setEnabled(True)
            # Enable LLM analysis widget
            self.captionAnalysisWidget.setEnabled(True)
            self._update_caption_display()

            QMessageBox.information(
                self,
                self.tr("Captions Extracted"),
                self.tr("Successfully extracted %d caption segments.") % len(self._caption_segments),
            )

        except Exception as e:
            progress.close()
            logger.error("Failed to extract captions: {}", e)
            QMessageBox.critical(
                self,
                self.tr("Extraction Failed"),
                self.tr("Failed to extract captions:\n%s") % str(e),
            )

    def _update_caption_display(self) -> None:
        """Update the caption display based on current video position."""
        if not self._caption_segments:
            self.captionLabel.setText("")
            return

        if self._effective_fps <= 0:
            return

        # Get current time in seconds (use effective FPS for correct timing)
        current_time = self._current_frame / self._effective_fps

        # Find caption at current time - search through segments directly
        caption_text = ""
        for segment in self._caption_segments:
            if segment.start <= current_time <= segment.end:
                caption_text = segment.text
                break

        if caption_text != self._current_caption:
            self._current_caption = caption_text
            self.captionLabel.setText(caption_text)
            logger.debug("Caption at {:.2f}s: {}", current_time, caption_text[:50] if caption_text else "(none)")

    def _export_captions(self) -> None:
        """Export captions to SRT file."""
        if not self._caption_segments or not self._whisper_transcriber:
            QMessageBox.warning(
                self,
                self.tr("No Captions"),
                self.tr("Please extract captions first."),
            )
            return

        # Get captions output directory (creates <video_name>/captions/)
        captions_dir = self._get_video_output_dir("captions")
        if not captions_dir:
            return

        # Default filename
        video_name = osp.splitext(osp.basename(self.filename))[0] if self.filename else "video"
        default_path = osp.join(captions_dir, f"{video_name}.srt")

        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            self.tr("Export Captions"),
            default_path,
            self.tr("SRT Files (*.srt);;WebVTT Files (*.vtt);;All Files (*)"),
        )

        if not path:
            return

        try:
            if path.endswith(".vtt"):
                self._whisper_transcriber.export_vtt(path)
            else:
                self._whisper_transcriber.export_srt(path)

            QMessageBox.information(
                self,
                self.tr("Export Complete"),
                self.tr("Captions exported to:\n%s") % path,
            )
        except Exception as e:
            logger.error("Failed to export captions: {}", e)
            QMessageBox.critical(
                self,
                self.tr("Export Failed"),
                self.tr("Failed to export captions:\n%s") % str(e),
            )

    def _on_caption_search_changed(self, text: str) -> None:
        """Handle caption search text change."""
        # Enable search button if we have text and captions
        has_text = bool(text.strip())
        has_captions = bool(self._caption_segments)
        self.searchCaptionsBtn.setEnabled(has_text and has_captions)

    def _search_captions(self) -> None:
        """Search for keywords in captions and highlight on timeline."""
        if not self._caption_segments:
            return
        
        keywords_text = self.captionSearchInput.text().strip()
        if not keywords_text:
            return
        
        # Split keywords by comma or space
        keywords = [k.strip().lower() for k in keywords_text.replace(',', ' ').split() if k.strip()]
        if not keywords:
            return
        
        self._caption_search_keywords = keywords
        self._caption_search_results = []
        
        # Search through all caption segments
        for segment in self._caption_segments:
            text_lower = segment.text.lower()
            # Check if any keyword is in this segment
            if any(keyword in text_lower for keyword in keywords):
                # Calculate frame range for this segment
                start_frame = int(segment.start * self._effective_fps)
                end_frame = int(segment.end * self._effective_fps)
                # Add all frames in this segment
                for frame in range(start_frame, end_frame + 1):
                    if frame not in self._caption_search_results:
                        self._caption_search_results.append(frame)
        
        # Sort results
        self._caption_search_results.sort()
        
        # Update UI
        result_count = len(self._caption_search_results)
        if result_count > 0:
            self.searchResultLabel.setText(
                f"1 / {result_count}"
            )
            self.clearSearchBtn.setEnabled(True)
            self.prevSearchBtn.setEnabled(True)
            self.nextSearchBtn.setEnabled(True)
            
            # Update clip timeline to show search results
            self.clipTimeline.setSearchResults(self._caption_search_results)
            
            logger.info("Caption search: found {} frames with keywords: {}", 
                       result_count, keywords)
            
            # Jump to first result
            if self._caption_search_results:
                first_frame = self._caption_search_results[0]
                self._current_frame = first_frame
                self._seek_to_frame(first_frame)
                self.timelineSlider.setValue(first_frame)
        else:
            self.searchResultLabel.setText("No results found")
            self.clearSearchBtn.setEnabled(False)
            self.prevSearchBtn.setEnabled(False)
            self.nextSearchBtn.setEnabled(False)
            self.clipTimeline.setSearchResults([])

    def _clear_caption_search(self) -> None:
        """Clear caption search results."""
        self._caption_search_results = []
        self._caption_search_keywords = []
        self.captionSearchInput.clear()
        self.searchResultLabel.setText("")
        self.clearSearchBtn.setEnabled(False)
        self.prevSearchBtn.setEnabled(False)
        self.nextSearchBtn.setEnabled(False)
        
        # Clear search results from timeline
        self.clipTimeline.setSearchResults([])
        
        logger.info("Caption search cleared")

    def _goto_prev_search_result(self) -> None:
        """Go to previous search result."""
        if not self._caption_search_results:
            return
        
        # Find the previous result frame (before current frame)
        prev_frames = [f for f in self._caption_search_results if f < self._current_frame]
        
        if prev_frames:
            # Go to the last one before current
            target_frame = prev_frames[-1]
        else:
            # Wrap around to last result
            target_frame = self._caption_search_results[-1]
        
        self._current_frame = target_frame
        self._seek_to_frame(target_frame)
        self.timelineSlider.setValue(target_frame)
        
        # Update result label to show position
        current_index = self._caption_search_results.index(target_frame) + 1
        self.searchResultLabel.setText(
            f"{current_index} / {len(self._caption_search_results)}"
        )

    def _goto_next_search_result(self) -> None:
        """Go to next search result."""
        if not self._caption_search_results:
            return
        
        # Find the next result frame (after current frame)
        next_frames = [f for f in self._caption_search_results if f > self._current_frame]
        
        if next_frames:
            # Go to the first one after current
            target_frame = next_frames[0]
        else:
            # Wrap around to first result
            target_frame = self._caption_search_results[0]
        
        self._current_frame = target_frame
        self._seek_to_frame(target_frame)
        self.timelineSlider.setValue(target_frame)
        
        # Update result label to show position
        current_index = self._caption_search_results.index(target_frame) + 1
        self.searchResultLabel.setText(
            f"{current_index} / {len(self._caption_search_results)}"
        )

    def _export_llm_detections(self) -> None:
        """Export LLM detection results to JSON."""
        if not self._llm_detections:
            return
        
        # Get output directory
        detections_dir = self._get_video_output_dir("detections")
        if not detections_dir:
            return
        
        # Default filename
        video_name = osp.splitext(osp.basename(self.filename))[0] if self.filename else "video"
        default_path = osp.join(detections_dir, f"{video_name}_detections.json")
        
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            self.tr("Export Detections"),
            default_path,
            self.tr("JSON Files (*.json);;All Files (*)"),
        )
        
        if not path:
            return
        
        try:
            from labelvid.agent import CaptionAnalyzer
            
            # Create a temporary analyzer just for export
            analyzer = CaptionAnalyzer()
            analyzer.export_to_json(self._llm_detections, path)
            
            QMessageBox.information(
                self,
                self.tr("Export Complete"),
                self.tr("Detections exported to:\n%s") % path,
            )
        except Exception as e:
            logger.error("Failed to export detections: {}", e)
            QMessageBox.critical(
                self,
                self.tr("Export Failed"),
                self.tr("Failed to export detections:\n%s") % str(e),
            )

    def _scale_frame_for_preview(self, frame):
        """Scale frame for preview display.
        
        Args:
            frame: Original frame from video
            
        Returns:
            Scaled frame for preview (or original if scale is 1.0)
        """
        if frame is None:
            return None
            
        if self._preview_scale >= 1.0:
            return frame
            
        # Calculate new dimensions
        height, width = frame.shape[:2]
        new_width = int(width * self._preview_scale)
        new_height = int(height * self._preview_scale)
        
        # Use INTER_AREA for downscaling, best quality
        scaled = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
        return scaled

    def _get_jump_frames(self) -> int:
        """Get number of frames to jump based on current setting."""
        jump_map = {
            "1s": 1,
            "5s": 5,
            "10s": 10,
            "30s": 30,
            "1min": 60,
            "5min": 300,
        }
        seconds = jump_map.get(self.jumpCombo.currentText(), 10)
        return int(seconds * self._effective_fps)

    def _jump_backward(self) -> None:
        """Jump backward by selected time."""
        if self._video_capture is None:
            return
        jump_frames = self._get_jump_frames()
        new_frame = max(0, self._current_frame - jump_frames)
        self._current_frame = new_frame
        self._seek_to_frame(new_frame, force=True)
        self.timelineSlider.setValue(new_frame)

    def _jump_forward(self) -> None:
        """Jump forward by selected time."""
        if self._video_capture is None:
            return
        jump_frames = self._get_jump_frames()
        new_frame = min(self._total_frames - 1, self._current_frame + jump_frames)
        self._current_frame = new_frame
        self._seek_to_frame(new_frame, force=True)
        self.timelineSlider.setValue(new_frame)

    def _seek_to_frame(self, frame_num: int, force: bool = False) -> None:
        """Seek to a specific frame and display it (with preview scaling).
        
        Args:
            frame_num: Target frame number
            force: Force refresh even if same frame
        """
        if self._video_capture is None:
            return

        # Avoid redisplaying the same frame for performance
        if not force and frame_num == self._last_displayed_frame:
            return

        try:
            # For long videos, use more reliable seek method
            current_pos = int(self._video_capture.get(cv2.CAP_PROP_POS_FRAMES))
            
            # If target frame is close to current position, read directly (faster)
            if 0 < frame_num - current_pos <= 5:
                # Skip forward a few frames by reading
                for _ in range(frame_num - current_pos):
                    self._video_capture.read()
                ret, frame = self._video_capture.read()
            else:
                # Otherwise use seek
                self._video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = self._video_capture.read()

            if ret and frame is not None:
                # Apply preview scaling
                preview_frame = self._scale_frame_for_preview(frame)
                self.videoPlayer.display_frame(preview_frame)
                self._last_displayed_frame = frame_num
            else:
                logger.warning("Failed to read frame {}", frame_num)
                
        except Exception as e:
            logger.error("Error seeking to frame {}: {}", frame_num, e)

        self._update_frame_display()

    def _update_frame_display(self) -> None:
        """Update frame number and time displays."""
        self.frameLabel.setText(f"{self._current_frame} / {self._total_frames - 1}")

        # Use effective FPS for time display (matches actual container duration)
        current_time = self._current_frame / self._effective_fps if self._effective_fps > 0 else 0
        total_time = self._actual_duration if self._actual_duration > 0 else (
            self._total_frames / self._effective_fps if self._effective_fps > 0 else 0
        )
        self.timeLabel.setText(
            f"{_format_time(current_time)} / {_format_time(total_time)}"
        )

        # Update clip timeline current frame indicator
        self.clipTimeline.setCurrentFrame(self._current_frame)

        # Update caption display
        self._update_caption_display()

    # Clip marking methods

    def _mark_start(self) -> None:
        """Mark the start of a new clip."""
        if self._video_capture is None:
            return

        self._pending_start_frame = self._current_frame
        self.pendingLabel.setText(
            f"📍 Clip start marked at frame {self._pending_start_frame}"
        )
        self.markEndBtn.setEnabled(True)
        
        # Show pending start marker on timeline
        self.clipTimeline.setPendingStartFrame(self._pending_start_frame)
        
        logger.info("Marked clip start at frame {}", self._pending_start_frame)

    def _mark_end(self) -> None:
        """Mark the end of the current clip and prompt for label."""
        if self._video_capture is None or self._pending_start_frame is None:
            return

        end_frame = self._current_frame

        # Show dialog to get clip information
        dialog = ClipDialog(
            parent=self,
            label=f"clip_{len(self._clips) + 1}",
            title=self.tr("Create Clip"),
        )
        
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            label, det_score, rec_score, is_hazard, description, recognition, scene, category_id, instance_id = dialog.get_values()
            
            if label:
                clip = VideoClip(
                    label=label,
                    start_frame=self._pending_start_frame,
                    end_frame=end_frame,
                    color=_get_color_for_index(len(self._clips)),
                    detection_score=det_score,
                    recognition_score=rec_score,
                    is_hazard=is_hazard,
                    description=description,
                    recognition=recognition,
                    scene=scene,
                    category_id=category_id,
                    instance_id=instance_id,
                )
                self._clips.append(clip)
                self._update_clip_list()
                self._is_changed = True

                logger.info(
                    "Created clip '{}': frames {} - {} (det:{}, rec:{}, hazard:{})",
                    label,
                    clip.start_frame,
                    clip.end_frame,
                    det_score,
                    rec_score,
                    is_hazard,
                )

                # Auto-save
                self._auto_save_clips()

        # Reset pending state
        self._pending_start_frame = None
        self.pendingLabel.setText("")
        self.markEndBtn.setEnabled(False)
        
        # Clear pending marker from timeline
        self.clipTimeline.setPendingStartFrame(None)

    def _update_clip_list(self) -> None:
        """Update the clip list widget and timeline."""
        self.clipListWidget.clear()
        for clip in self._clips:
            item = ClipListWidgetItem(clip)
            self.clipListWidget.addItem(item)
        
        # Also update clip timeline
        self.clipTimeline.setClips(self._clips)

    def _clip_selection_changed(self) -> None:
        """Handle clip selection change."""
        pass  # Can be used for future features
    
    def _clip_double_clicked(self, item) -> None:
        """Handle double-click on clip - edit it."""
        if isinstance(item, ClipListWidgetItem):
            self._edit_clip(item.clip)
    
    def _delete_selected_clip(self) -> None:
        """Delete selected clips (triggered by Delete key)."""
        selected_items = self.clipListWidget.selectedItems()
        if not selected_items:
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            self.tr("Delete Clips"),
            self.tr("Delete %d selected clip(s)?") % len(selected_items),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        
        if reply == QMessageBox.Yes:
            for item in selected_items:
                if isinstance(item, ClipListWidgetItem):
                    self._delete_clip(item.clip)
    
    def _edit_clip(self, clip: VideoClip) -> None:
        """Edit a clip's information."""
        dialog = ClipDialog(
            parent=self,
            label=clip.label,
            detection_score=clip.detection_score,
            recognition_score=clip.recognition_score,
            is_hazard=clip.is_hazard,
            description=clip.description,
            recognition=clip.recognition,
            scene=clip.scene,
            category_id=clip.category_id,
            instance_id=clip.instance_id,
            title=self.tr("Edit Clip"),
        )
        
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            label, det_score, rec_score, is_hazard, description, recognition, scene, category_id, instance_id = dialog.get_values()
            
            if label:
                clip.label = label
                clip.detection_score = det_score
                clip.recognition_score = rec_score
                clip.is_hazard = is_hazard
                clip.description = description
                clip.recognition = recognition
                clip.scene = scene
                clip.category_id = category_id
                clip.instance_id = instance_id
                
                self._update_clip_list()
                self._is_changed = True
                self._auto_save_clips()
                
                logger.info("Updated clip '{}' (cat:{}, inst:{}, det:{}, rec:{}, hazard:{})", 
                          label, category_id, instance_id, det_score, rec_score, is_hazard)
    
    def _delete_clip(self, clip: VideoClip) -> None:
        """Delete a clip."""
        if clip in self._clips:
            self._clips.remove(clip)
            self._update_clip_list()
            self._is_changed = True
            self._auto_save_clips()
            logger.info("Deleted clip '{}'", clip.label)
    
    def _fill_clips_from_llm_detections(self, detections: list) -> None:
        """Fill or update clips from LLM detection results.
        
        Args:
            detections: List of ObjectDetection from LLM analysis
        """
        if not detections or not self._video_capture:
            return
        
        # Get FPS for time to frame conversion
        fps = self._effective_fps if hasattr(self, '_effective_fps') and self._effective_fps else 30.0
        
        updated_count = 0
        created_count = 0
        
        for det in detections:
            # Convert timestamps to frames
            start_frame = int(det.timestamp_start * fps)
            end_frame = int(det.timestamp_end * fps)
            
            # Clamp to valid frame range
            start_frame = max(0, min(start_frame, self._total_frames - 1))
            end_frame = max(0, min(end_frame, self._total_frames - 1))
            
            # Check if there's an existing clip that overlaps with this detection
            existing_clip = None
            for clip in self._clips:
                # Check for overlap
                if not (end_frame < clip.start_frame or start_frame > clip.end_frame):
                    existing_clip = clip
                    break
            
            if existing_clip:
                # Update existing clip with LLM data
                existing_clip.label = det.object_name
                existing_clip.detection_score = det.detection_score
                existing_clip.recognition_score = det.recognition_score
                existing_clip.is_hazard = det.is_hazard
                existing_clip.description = det.description
                existing_clip.recognition = det.object_name  # Same as label
                existing_clip.scene = ""  # Leave empty
                existing_clip.category_id = 0  # Default
                existing_clip.instance_id = 0  # Default
                updated_count += 1
                logger.info("Updated clip '{}' with LLM data", det.object_name)
            else:
                # Create new clip
                clip = VideoClip(
                    label=det.object_name,
                    start_frame=start_frame,
                    end_frame=end_frame,
                    color=_get_color_for_index(len(self._clips)),
                    detection_score=det.detection_score,
                    recognition_score=det.recognition_score,
                    is_hazard=det.is_hazard,
                    description=det.description,
                    recognition=det.object_name,  # Same as label
                    scene="",  # Leave empty
                    category_id=0,  # Default
                    instance_id=0,  # Default
                )
                self._clips.append(clip)
                created_count += 1
                logger.info("Created clip '{}' from LLM detection", det.object_name)
        
        # Update UI
        self._update_clip_list()
        self._is_changed = True
        self._auto_save_clips()
        
        # Show summary
        QMessageBox.information(
            self,
            self.tr("Clips Updated"),
            self.tr(
                "LLM analysis complete!\n\n"
                "Created: %d new clips\n"
                "Updated: %d existing clips"
            ) % (created_count, updated_count),
        )
    
    def _manage_object_list(self) -> None:
        """Show dialog to manage object list."""
        dialog = ObjectListDialog(self)
        
        # Load current object list
        current_objects = get_object_list()
        if current_objects:
            dialog.set_objects(current_objects)
        
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            # Save the new object list
            objects = dialog.get_objects()
            set_object_list(objects)
            
            # Show confirmation
            QtWidgets.QMessageBox.information(
                self,
                self.tr("Object List Updated"),
                self.tr(f"Object list updated with {len(objects)} objects.\n"
                       "Labels will now be available as dropdown in clip dialogs."),
            )
            
            logger.info("Object list updated with {} objects", len(objects))
    
    def _on_llm_analysis_requested(self, provider: str, model: str, api_key: str | None) -> None:
        """Handle LLM caption analysis request."""
        if not hasattr(self, '_caption_segments') or not self._caption_segments:
            QMessageBox.warning(
                self,
                self.tr("No Captions"),
                self.tr("Please extract or load captions first."),
            )
            return
        
        # Import LLM modules
        try:
            from labelvid.agent import CaptionAnalyzer
            from labelvid.agent import LLMClient
            from labelvid.agent import LLMProvider
        except ImportError as e:
            QMessageBox.critical(
                self,
                self.tr("Import Error"),
                self.tr("Failed to import LLM modules: %s\n\nInstall with: pip install -e \".[llm]\"") % str(e),
            )
            return
        
        # Map provider string to enum
        provider_map = {
            "openai": LLMProvider.OPENAI,
            "gemini": LLMProvider.GEMINI,
            "claude": LLMProvider.CLAUDE,
        }
        provider_enum = provider_map.get(provider, LLMProvider.OPENAI)
        
        # Create progress dialog
        progress = QtWidgets.QProgressDialog(
            self.tr("Analyzing captions with LLM..."),
            self.tr("Cancel"),
            0, 100,
            self,
        )
        progress.setWindowTitle(self.tr("LLM Caption Analysis"))
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.show()
        
        def update_progress(value: float, message: str) -> None:
            if progress.wasCanceled():
                return
            progress.setValue(int(value * 100))
            progress.setLabelText(message)
            QtWidgets.QApplication.processEvents()
        
        try:
            # Create LLM client and analyzer
            llm_client = LLMClient(provider=provider_enum, api_key=api_key, model=model)
            analyzer = CaptionAnalyzer(llm_client=llm_client)
            
            # Analyze captions
            detections = analyzer.analyze_captions(
                self._caption_segments,
                progress_callback=update_progress,
            )
            
            progress.close()
            
            if detections:
                # Automatically save JSON to video output directory
                try:
                    output_dir = self._get_video_output_dir("llm_analysis")
                    if self._video_path:
                        video_name = Path(self._video_path).stem
                        json_path = output_dir / f"{video_name}_llm_detections.json"
                        
                        # Export to JSON
                        analyzer.export_to_json(detections, str(json_path))
                        logger.info("LLM detections automatically saved to: {}", json_path)
                except Exception as e:
                    logger.error("Failed to auto-save LLM detections: {}", e)
                
                # Automatically fill clips from detections
                self._fill_clips_from_llm_detections(detections)
                
                # Show success message
                QMessageBox.information(
                    self,
                    self.tr("Analysis Complete"),
                    self.tr("Found {} object detections.\nResults saved to: {}\nClips have been updated.").format(
                        len(detections),
                        json_path.name if 'json_path' in locals() else "llm_analysis folder"
                    ),
                )
            else:
                QMessageBox.information(
                    self,
                    self.tr("Analysis Complete"),
                    self.tr("No object detections found in captions."),
                )
        
        except Exception as e:
            progress.close()
            logger.error("LLM analysis failed: {}", e)
            QMessageBox.critical(
                self,
                self.tr("Analysis Failed"),
                self.tr("Failed to analyze captions:\n%s") % str(e),
            )

    def _show_batch_process_dialog(self) -> None:
        """Show batch process dialog to choose processing mode."""
        if not self.videoList:
            QMessageBox.warning(
                self,
                self.tr("No Videos Loaded"),
                self.tr("Please load videos first using File > Open Directory."),
            )
            return
        
        # Create dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(self.tr("Batch Process"))
        dialog.setMinimumWidth(400)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Info label
        info_label = QtWidgets.QLabel(
            self.tr(f"Process {len(self.videoList)} loaded videos:")
        )
        layout.addWidget(info_label)
        
        # Options
        caption_only_btn = QtWidgets.QPushButton("📝 Caption Extraction Only")
        caption_only_btn.setToolTip("Extract captions using Whisper and save to SRT")
        caption_only_btn.clicked.connect(lambda: (dialog.accept(), self._batch_process(False)))
        layout.addWidget(caption_only_btn)
        
        caption_llm_btn = QtWidgets.QPushButton("🤖 Caption + LLM Analysis")
        caption_llm_btn.setToolTip("Extract captions and analyze with LLM")
        caption_llm_btn.clicked.connect(lambda: (dialog.accept(), self._batch_process(True)))
        layout.addWidget(caption_llm_btn)
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        layout.addWidget(cancel_btn)
        
        dialog.exec_()

    def _batch_process(self, llm_analyze: bool = False) -> None:
        """Batch process all loaded videos.
        
        Args:
            llm_analyze: If True, also run LLM analysis after caption extraction
        """
        if not self.videoList:
            QMessageBox.warning(
                self,
                self.tr("No Videos Loaded"),
                self.tr("Please load videos first using File > Open Directory."),
            )
            return
        
        # Check if Whisper is available
        if not WHISPER_AVAILABLE:
            QMessageBox.warning(
                self,
                self.tr("Whisper Not Available"),
                self.tr("Please install Whisper: pip install -e \".[whisper]\""),
            )
            return
        
        # If LLM analysis is requested, check LLM availability
        if llm_analyze:
            try:
                from labelvid.agent import CaptionAnalyzer, LLMClient, LLMProvider
            except ImportError:
                QMessageBox.warning(
                    self,
                    self.tr("LLM Not Available"),
                    self.tr("Please install LLM dependencies: pip install -e \".[llm]\""),
                )
                return
            
            # Get LLM settings from widget
            if not hasattr(self, 'captionAnalysisWidget'):
                QMessageBox.warning(
                    self,
                    self.tr("LLM Settings Not Available"),
                    self.tr("Please configure LLM settings first."),
                )
                return
        
        # Create progress dialog with detailed status
        total_videos = len(self.videoList)
        progress = QtWidgets.QProgressDialog(
            self.tr("Initializing batch process..."),
            self.tr("Cancel"),
            0, 100,  # Use percentage instead of video count for finer control
            self,
        )
        progress.setWindowTitle(self.tr("Batch Process"))
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setMinimumWidth(500)
        progress.show()
        
        def update_batch_progress(video_idx: int, video_name: str, step: str, detail: str = "") -> None:
            """Update batch progress with detailed information."""
            if progress.wasCanceled():
                return
            
            # Calculate overall progress
            base_progress = int((video_idx / total_videos) * 100)
            progress.setValue(base_progress)
            
            # Build detailed status message
            status_lines = [
                f"📹 Video {video_idx + 1}/{total_videos}: {video_name}",
                f"",
                f"🔄 Current Step: {step}",
            ]
            
            if detail:
                status_lines.append(f"   {detail}")
            
            progress.setLabelText("\n".join(status_lines))
            QtWidgets.QApplication.processEvents()
        
        # Process each video
        success_count = 0
        failed_videos = []
        
        for i, video_path in enumerate(self.videoList):
            if progress.wasCanceled():
                break
            
            video_name = Path(video_path).name
            
            try:
                # Step 1: Load video
                update_batch_progress(i, video_name, "Loading video...", "")
                self._load_video(video_path)
                QtWidgets.QApplication.processEvents()
                
                # Step 2: Check/Extract captions
                caption_exists = bool(self._caption_segments)
                
                if caption_exists:
                    update_batch_progress(
                        i, video_name, 
                        "Captions found ✓", 
                        f"Loaded {len(self._caption_segments)} caption segments"
                    )
                    logger.info("Captions already exist for: {} ({} segments)", video_name, len(self._caption_segments))
                else:
                    update_batch_progress(i, video_name, "Extracting captions...", "Using Whisper ASR")
                    logger.info("Extracting captions for: {}", video_name)
                    self._extract_captions()
                    QtWidgets.QApplication.processEvents()
                    
                    if self._caption_segments:
                        update_batch_progress(
                            i, video_name, 
                            "Caption extraction complete ✓", 
                            f"Extracted {len(self._caption_segments)} segments"
                        )
                
                # Step 3: Run LLM analysis if requested
                if llm_analyze and self._caption_segments:
                    num_segments = len(self._caption_segments)
                    num_chunks = (num_segments + 19) // 20  # Calculate number of 20-segment chunks
                    
                    update_batch_progress(
                        i, video_name, 
                        "Starting LLM analysis...", 
                        f"{num_segments} segments → {num_chunks} chunks"
                    )
                    logger.info("Running LLM analysis for: {} ({} segments, {} chunks)", 
                               video_name, num_segments, num_chunks)
                    
                    # Get LLM settings
                    provider_index = self.captionAnalysisWidget.providerCombo.currentIndex()
                    provider_names = ["openai", "gemini", "claude"]
                    provider = provider_names[provider_index]
                    model = self.captionAnalysisWidget.modelCombo.currentText()
                    api_key = self.captionAnalysisWidget.apiKeyInput.text().strip() or None
                    
                    # Map provider
                    provider_map = {
                        "openai": LLMProvider.OPENAI,
                        "gemini": LLMProvider.GEMINI,
                        "claude": LLMProvider.CLAUDE,
                    }
                    provider_enum = provider_map.get(provider, LLMProvider.OPENAI)
                    
                    # Create LLM client and analyzer
                    llm_client = LLMClient(provider=provider_enum, api_key=api_key, model=model)
                    analyzer = CaptionAnalyzer(llm_client=llm_client)
                    
                    # Analyze with progress callback
                    def llm_progress_callback(chunk_progress: float, message: str) -> None:
                        if progress.wasCanceled():
                            return
                        # Extract chunk info from message if available
                        detail_msg = f"{message}"
                        update_batch_progress(i, video_name, "Analyzing captions...", detail_msg)
                    
                    detections = analyzer.analyze_captions(
                        self._caption_segments,
                        progress_callback=llm_progress_callback
                    )
                    
                    if detections:
                        update_batch_progress(
                            i, video_name, 
                            "Saving results...", 
                            f"Found {len(detections)} detections"
                        )
                        
                        # Save JSON
                        output_dir = self._get_video_output_dir("llm_analysis")
                        json_path = Path(output_dir) / f"{Path(video_path).stem}_llm_detections.json"
                        analyzer.export_to_json(detections, str(json_path))
                        
                        # Fill clips
                        self._fill_clips_from_llm_detections(detections)
                        
                        update_batch_progress(
                            i, video_name, 
                            "Complete ✓", 
                            f"{len(detections)} detections saved & clips updated"
                        )
                        logger.info("LLM analysis complete for: {}, found {} detections", video_name, len(detections))
                    else:
                        update_batch_progress(i, video_name, "Complete ✓", "No detections found")
                else:
                    update_batch_progress(i, video_name, "Complete ✓", "Captions saved")
                
                success_count += 1
                
            except Exception as e:
                logger.error("Failed to process {}: {}", video_name, e)
                failed_videos.append((video_name, str(e)))
                update_batch_progress(i, video_name, "Failed ✗", str(e)[:50])
        
        progress.setValue(100)
        progress.close()
        
        # Show summary
        summary = self.tr(f"Batch processing complete!\n\n")
        summary += self.tr(f"Successfully processed: {success_count}/{total_videos}\n")
        
        if failed_videos:
            summary += self.tr(f"\nFailed videos:\n")
            for video_name, error in failed_videos[:5]:  # Show first 5
                summary += self.tr(f"  - {video_name}: {error}\n")
            if len(failed_videos) > 5:
                summary += self.tr(f"  ... and {len(failed_videos) - 5} more\n")
        
        QMessageBox.information(
            self,
            self.tr("Batch Process Complete"),
            summary,
        )

    def _on_clip_marker_dragging(self, clip_index: int, is_start: bool, frame: int) -> None:
        """Handle clip marker being dragged - update display in real-time."""
        if clip_index < 0 or clip_index >= len(self._clips):
            return
        
        # Update frame display to show the frame being dragged to
        self._current_frame = frame
        self._seek_to_frame(frame)
        self.timelineSlider.blockSignals(True)
        self.timelineSlider.setValue(frame)
        self.timelineSlider.blockSignals(False)
        
        # Temporarily update the clip for visual feedback
        clip = self._clips[clip_index]
        if is_start:
            clip.start_frame = frame
        else:
            clip.end_frame = frame
        
        # Update timeline display
        self.clipTimeline.update()

    def _on_clip_marker_drag_finished(self, clip_index: int, is_start: bool, frame: int) -> None:
        """Handle clip marker drag finished - save the change."""
        if clip_index < 0 or clip_index >= len(self._clips):
            return
        
        clip = self._clips[clip_index]
        old_value = clip.start_frame if is_start else clip.end_frame
        
        # Update the clip
        if is_start:
            clip.start_frame = frame
        else:
            clip.end_frame = frame
        
        # Log the change
        marker_type = "start" if is_start else "end"
        logger.info(
            "Clip '{}' {} frame changed: {} -> {}",
            clip.label, marker_type, old_value, frame
        )
        
        # Update UI
        self._update_clip_list()
        self._is_changed = True
        
        # Auto-save
        self._auto_save_clips()
        
        self.statusBar().showMessage(
            self.tr("Clip '%s' %s updated to frame %d") % (clip.label, marker_type, frame),
            3000
        )

    def _on_clip_marker_clicked(self, clip_index: int) -> None:
        """Handle clip marker clicked - select the clip in the list."""
        if clip_index < 0 or clip_index >= len(self._clips):
            return
        
        # Select the clip in the list widget
        self.clipListWidget.setCurrentRow(clip_index)

    def _clip_selection_changed(self) -> None:
        """Handle clip selection change."""
        pass

    def _clip_double_clicked(self, item: ClipListWidgetItem) -> None:
        """Handle clip double-click - seek to clip start."""
        clip = item.clip
        self._current_frame = clip.start_frame
        self._seek_to_frame(clip.start_frame)
        self.timelineSlider.setValue(clip.start_frame)

    def _pop_clip_list_menu(self, point: QtCore.QPoint) -> None:
        """Show context menu for clip list."""
        item = self.clipListWidget.itemAt(point)
        if item is not None:
            # Enable/disable actions based on selection
            has_selection = len(self.clipListWidget.selectedItems()) > 0
            self._clip_edit_action.setEnabled(has_selection)
            self._clip_goto_start_action.setEnabled(has_selection)
            self._clip_goto_end_action.setEnabled(has_selection)
            self._clip_delete_action.setEnabled(has_selection)
            
            # Show menu at cursor position
            self._clip_context_menu.exec_(self.clipListWidget.mapToGlobal(point))

    def _edit_selected_clip(self) -> None:
        """Edit the selected clip (all fields)."""
        items = self.clipListWidget.selectedItems()
        if not items:
            return
        
        item = items[0]  # Edit first selected
        clip = item.clip
        
        # Use ClipDialog to edit all fields
        self._edit_clip(clip)

    def _goto_clip_start(self) -> None:
        """Go to the start frame of the selected clip."""
        items = self.clipListWidget.selectedItems()
        if not items:
            return
        
        clip = items[0].clip
        self._current_frame = clip.start_frame
        self._seek_to_frame(clip.start_frame)
        self.timelineSlider.setValue(clip.start_frame)

    def _goto_clip_end(self) -> None:
        """Go to the end frame of the selected clip."""
        items = self.clipListWidget.selectedItems()
        if not items:
            return
        
        clip = items[0].clip
        self._current_frame = clip.end_frame
        self._seek_to_frame(clip.end_frame)
        self.timelineSlider.setValue(clip.end_frame)

    def _delete_selected_clip(self) -> None:
        """Delete the selected clip."""
        items = self.clipListWidget.selectedItems()
        if not items:
            return

        reply = QMessageBox.question(
            self,
            self.tr("Delete Clip"),
            self.tr("Are you sure you want to delete the selected clip?"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            for item in items:
                clip = item.clip
                if clip in self._clips:
                    self._clips.remove(clip)
            self._update_clip_list()
            self._is_changed = True

            # Auto-save
            self._auto_save_clips()

    # Save/Load clips methods

    def _save_clips(self) -> None:
        """Save clips to a CSV file."""
        if not self._clips:
            QMessageBox.information(
                self,
                self.tr("No Clips"),
                self.tr("There are no clips to save."),
            )
            return

        default_name = (
            osp.splitext(osp.basename(self.filename))[0] + "_clips.csv"
            if self.filename
            else "clips.csv"
        )
        default_path = osp.join(
            self.output_dir or osp.dirname(self.filename or "."), default_name
        )

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            self.tr("Save Clips"),
            default_path,
            self.tr("CSV files (*.csv)"),
        )

        if filename:
            self._write_clips_csv(filename)
            self._is_changed = False
            self.statusBar().showMessage(self.tr("Clips saved to %s") % filename)

    def _load_clips(self) -> None:
        """Load clips from a CSV file."""
        path = osp.dirname(self.filename) if self.filename else "."
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.tr("Load Clips"),
            path,
            self.tr("CSV files (*.csv)"),
        )

        if filename:
            self._read_clips_csv(filename)
            self._update_clip_list()
            self.statusBar().showMessage(
                self.tr("Loaded %d clips from %s") % (len(self._clips), filename)
            )

    def _write_clips_csv(self, filename: str) -> None:
        """Write clips to CSV file."""
        try:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Header with all fields
                writer.writerow([
                    "label", "start_frame", "end_frame", "video_file",
                    "detection_score", "recognition_score", "is_hazard", "description",
                    "recognition", "scene", "category_id", "instance_id"
                ])
                video_basename = osp.basename(self.filename) if self.filename else ""
                for clip in self._clips:
                    writer.writerow([
                        clip.label,
                        clip.start_frame,
                        clip.end_frame,
                        video_basename,
                        clip.detection_score if clip.detection_score is not None else "",
                        clip.recognition_score if clip.recognition_score is not None else "",
                        clip.is_hazard if clip.is_hazard is not None else "",
                        clip.description,
                        clip.recognition,
                        clip.scene,
                        clip.category_id,
                        clip.instance_id,
                    ])
        except Exception as e:
            logger.error("Failed to write clips CSV {}: {}", filename, e)
            raise

    def _read_clips_csv(self, filename: str) -> None:
        """Read clips from CSV file."""
        self._clips.clear()
        try:
            with open(filename, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    # Parse optional fields
                    det_score = None
                    if "detection_score" in row and row["detection_score"]:
                        try:
                            det_score = float(row["detection_score"])
                        except ValueError:
                            pass
                    
                    rec_score = None
                    if "recognition_score" in row and row["recognition_score"]:
                        try:
                            rec_score = float(row["recognition_score"])
                        except ValueError:
                            pass
                    
                    is_hazard = None
                    if "is_hazard" in row and row["is_hazard"]:
                        is_hazard_str = row["is_hazard"].lower()
                        if is_hazard_str in ("true", "1", "yes"):
                            is_hazard = True
                        elif is_hazard_str in ("false", "0", "no"):
                            is_hazard = False
                    
                    description = row.get("description", "")
                    recognition = row.get("recognition", "")
                    scene = row.get("scene", "")
                    
                    # Parse category_id and instance_id
                    category_id = 0
                    if "category_id" in row and row["category_id"]:
                        try:
                            category_id = int(row["category_id"])
                        except ValueError:
                            pass
                    
                    instance_id = 0
                    if "instance_id" in row and row["instance_id"]:
                        try:
                            instance_id = int(row["instance_id"])
                        except ValueError:
                            pass
                    
                    clip = VideoClip(
                        label=row["label"],
                        start_frame=int(row["start_frame"]),
                        end_frame=int(row["end_frame"]),
                        color=_get_color_for_index(i),
                        detection_score=det_score,
                        recognition_score=rec_score,
                        is_hazard=is_hazard,
                        description=description,
                        recognition=recognition,
                        scene=scene,
                        category_id=category_id,
                        instance_id=instance_id,
                    )
                    self._clips.append(clip)
        except Exception as e:
            logger.error("Failed to read clips CSV {}: {}", filename, e)
            raise

    # Frame extraction methods

    def _get_video_output_dir(self, subdir: str | None = None, prompt: bool = False) -> str | None:
        """Get or create video-specific output directory.
        
        Creates a directory structure like:
            <video_dir>/<video_name>/
            <video_dir>/<video_name>/frames/
            <video_dir>/<video_name>/annotations/
            <video_dir>/<video_name>/captions/
            <video_dir>/<video_name>/clips.csv
        
        By default, uses the video's directory as the base. If prompt=True,
        allows user to select a different base directory.
        
        Args:
            subdir: Optional subdirectory name (e.g., 'frames', 'annotations', 'captions')
            prompt: If True, prompt user to select base directory
            
        Returns:
            Path to the output directory, or None if no video is loaded
        """
        if not self.filename:
            return None

        # If video output dir not set, create it
        if not self._video_output_dir:
            # Default: use video's directory as base
            base_dir = self.output_dir or osp.dirname(self.filename)
            
            # If prompt requested, let user choose different location
            if prompt:
                selected_dir = QtWidgets.QFileDialog.getExistingDirectory(
                    self,
                    self.tr("Select Output Directory"),
                    base_dir,
                    QtWidgets.QFileDialog.ShowDirsOnly,
                )
                if selected_dir:
                    base_dir = selected_dir
                elif prompt:
                    # User cancelled when prompt was required
                    return None

            # Create video-named folder
            video_name = osp.splitext(osp.basename(self.filename))[0]
            self._video_output_dir = osp.join(base_dir, video_name)
            os.makedirs(self._video_output_dir, exist_ok=True)
            logger.info("Video output directory: {}", self._video_output_dir)

        # Create subdirectory if specified
        if subdir:
            subdir_path = osp.join(self._video_output_dir, subdir)
            os.makedirs(subdir_path, exist_ok=True)
            return subdir_path

        return self._video_output_dir

    def _extract_frames(self) -> None:
        """Extract frames from all marked clips."""
        if not self._clips:
            QMessageBox.information(
                self,
                self.tr("No Clips"),
                self.tr("There are no clips to extract frames from."),
            )
            return

        if self._video_capture is None or not self.filename:
            return

        # Get frames output directory (creates <video_name>/frames/)
        frames_dir = self._get_video_output_dir("frames")
        if not frames_dir:
            return

        # Create progress dialog
        progress = QtWidgets.QProgressDialog(
            self.tr("Extracting frames..."),
            self.tr("Cancel"),
            0,
            len(self._clips) * 2,
            self,
        )
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle(self.tr("Extracting Frames"))

        extracted_count = 0
        csv_data: list[dict] = []

        for i, clip in enumerate(self._clips):
            if progress.wasCanceled():
                break

            # Extract start frame
            progress.setValue(i * 2)
            progress.setLabelText(
                self.tr("Extracting start frame for clip '%s'...") % clip.label
            )
            QtWidgets.QApplication.processEvents()

            start_frame = self._extract_single_frame(
                clip.start_frame,
                frames_dir,
                f"{clip.label}_start_{clip.start_frame}.jpg",
            )

            # Extract end frame
            progress.setValue(i * 2 + 1)
            progress.setLabelText(
                self.tr("Extracting end frame for clip '%s'...") % clip.label
            )
            QtWidgets.QApplication.processEvents()

            end_frame = self._extract_single_frame(
                clip.end_frame,
                frames_dir,
                f"{clip.label}_end_{clip.end_frame}.jpg",
            )

            if start_frame and end_frame:
                extracted_count += 1
                csv_data.append(
                    {
                        "label": clip.label,
                        "start_frame": clip.start_frame,
                        "end_frame": clip.end_frame,
                        "start_image": osp.basename(start_frame),
                        "end_image": osp.basename(end_frame),
                    }
                )

        progress.setValue(len(self._clips) * 2)

        # Write CSV to video output root (not in frames subfolder)
        csv_path = osp.join(self._video_output_dir, "clips.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "label",
                    "start_frame",
                    "end_frame",
                    "start_image",
                    "end_image",
                ],
            )
            writer.writeheader()
            writer.writerows(csv_data)

        QMessageBox.information(
            self,
            self.tr("Extraction Complete"),
            self.tr(
                "Successfully extracted frames from %d clips.\n\n"
                "Output directory: %s\n"
                "Frames folder: frames/\n"
                "CSV file: clips.csv\n\n"
                "You can now open the frames folder in Labelme for annotation."
            )
            % (extracted_count, self._video_output_dir),
        )

        logger.info(
            "Extracted frames from {} clips to {}", extracted_count, frames_dir
        )

    def _extract_single_frame(
        self, frame_num: int, output_dir: str, filename: str
    ) -> str | None:
        """Extract a single frame and save it at ORIGINAL quality.
        
        Note: This always uses the original video resolution,
        regardless of the preview scale setting.
        """
        if self._video_capture is None:
            return None

        self._video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = self._video_capture.read()

        if ret:
            output_path = osp.join(output_dir, filename)
            cv2.imwrite(output_path, frame)
            return output_path
        return None

    # Window event handlers

    def _can_continue(self) -> bool:
        """Check if it's safe to continue (e.g., close file).
        
        With auto-save enabled, prompts are usually not needed.
        Only prompt if auto-save fails.
        """
        # Auto-save is enabled, clips should already be saved
        if self._auto_save_path and self._clips:
            try:
                self._auto_save_clips()
            except Exception:
                # Auto-save失败，提示用户
                reply = QMessageBox.question(
                    self,
                    self.tr("Save Failed"),
                    self.tr("Auto-save failed. Do you want to save clips manually?"),
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                    QMessageBox.Save,
                )
                if reply == QMessageBox.Save:
                    self._save_clips()
                    return True
                elif reply == QMessageBox.Discard:
                    return True
                else:
                    return False
        return True

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Handle window close event."""
        if not self._can_continue():
            event.ignore()
            return

        # Save window settings
        self.settings.setValue("window/size", self.size())
        self.settings.setValue("window/position", self.pos())

        # Release video capture
        if self._video_capture is not None:
            self._video_capture.release()

        # Clean up extracted audio file
        self._cleanup_extracted_audio()

        # Stop audio player
        if self._audio_player:
            self._audio_player.stop()

        event.accept()

    # ==================== Mode Toggle Methods ====================

    def _toggle_app_mode(self) -> None:
        """Toggle between Video and Image modes."""
        if self._app_mode == AppMode.VIDEO:
            self._switch_to_image_mode()
        else:
            self._switch_to_video_mode()

    def _switch_to_video_mode(self) -> None:
        """Switch to video clipping mode."""
        self._app_mode = AppMode.VIDEO
        self.modeToggleBtn.setText("🎬 Video Mode")
        self.modeToggleBtn.setChecked(False)

        # Update UI visibility
        self.centralStack.setCurrentIndex(0)  # Video player
        self.clip_dock.show()
        self.shape_dock.hide()
        self.controls_dock.show()
        self.annotation_dock.hide()
        self.file_dock.show()  # Show video list
        self.image_dock.hide()  # Hide image list

        # Update menu state
        self.menus.annotation.setEnabled(False)

        self.statusBar().showMessage(self.tr("Switched to Video Mode"))
        logger.info("Switched to Video Mode")

    def _switch_to_image_mode(self) -> None:
        """Switch to image annotation mode with source selection dialog."""
        # Show source selection dialog
        source = self._show_image_source_dialog()
        if source is None:
            # User cancelled
            return

        self._image_mode_source = source
        self._app_mode = AppMode.IMAGE
        self.modeToggleBtn.setText("🖼️ Image Mode")
        self.modeToggleBtn.setChecked(True)

        # Update UI visibility
        self.centralStack.setCurrentIndex(1)  # Canvas/ScrollArea
        self.clip_dock.hide()
        self.shape_dock.show()
        self.controls_dock.hide()
        self.annotation_dock.show()
        self.file_dock.hide()  # Hide video list
        self.image_dock.show()  # Show image list

        # Update menu state
        self.menus.annotation.setEnabled(True)

        # Update image source combo to match
        source_index = {
            ImageModeSource.CURRENT_FRAME: 0,
            ImageModeSource.WST: 1,
            ImageModeSource.AUTO_EXTRACT: 2,
        }.get(source, 0)
        self.imageSourceCombo.blockSignals(True)
        self.imageSourceCombo.setCurrentIndex(source_index)
        self.imageSourceCombo.blockSignals(False)

        # Load image based on selected source mode
        self._load_image_for_annotation()

        self.statusBar().showMessage(self.tr("Switched to Image Mode"))
        logger.info("Switched to Image Mode with source: {}", source.value)

    def _show_image_source_dialog(self) -> ImageModeSource | None:
        """Show dialog for selecting image source when switching to Image mode."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(self.tr("Select Image Source"))
        dialog.setMinimumWidth(450)

        layout = QtWidgets.QVBoxLayout(dialog)

        # Description
        desc = QtWidgets.QLabel(
            self.tr(
                "Choose how to load images for annotation:\n"
            )
        )
        layout.addWidget(desc)

        # Radio buttons for source selection
        self._source_dialog_group = QtWidgets.QButtonGroup(dialog)

        # Option 1: Current Frame
        currentFrameRadio = QtWidgets.QRadioButton(
            self.tr("📷 Current Video Frame")
        )
        currentFrameRadio.setToolTip(
            self.tr("Use the current video frame for annotation")
        )
        currentFrameRadio.setChecked(True)
        self._source_dialog_group.addButton(currentFrameRadio, 0)
        layout.addWidget(currentFrameRadio)

        currentFrameDesc = QtWidgets.QLabel(
            self.tr("   Annotate the current frame from the video")
        )
        currentFrameDesc.setStyleSheet("color: gray; margin-left: 20px;")
        layout.addWidget(currentFrameDesc)

        layout.addSpacing(10)

        # Option 2: WST (Load from folder)
        wstRadio = QtWidgets.QRadioButton(
            self.tr("📁 WST - Load Extracted Frames")
        )
        wstRadio.setToolTip(
            self.tr("Load images from a folder of previously extracted frames")
        )
        self._source_dialog_group.addButton(wstRadio, 1)
        layout.addWidget(wstRadio)

        wstDesc = QtWidgets.QLabel(
            self.tr("   Select a folder with extracted frame images")
        )
        wstDesc.setStyleSheet("color: gray; margin-left: 20px;")
        layout.addWidget(wstDesc)

        layout.addSpacing(10)

        # Option 3: Auto Extract
        autoExtractRadio = QtWidgets.QRadioButton(
            self.tr("🔄 Auto Extract - Extract Clip Frames")
        )
        autoExtractRadio.setToolTip(
            self.tr("Automatically extract frames from all marked clips")
        )
        autoExtractRadio.setEnabled(len(self._clips) > 0)
        self._source_dialog_group.addButton(autoExtractRadio, 2)
        layout.addWidget(autoExtractRadio)

        clipCount = len(self._clips)
        autoExtractDesc = QtWidgets.QLabel(
            self.tr("   Extract start/end frames from %d clips") % clipCount
            if clipCount > 0
            else self.tr("   (No clips marked yet)")
        )
        autoExtractDesc.setStyleSheet("color: gray; margin-left: 20px;")
        layout.addWidget(autoExtractDesc)

        layout.addSpacing(10)

        # Option 4: Open single image file
        openImageRadio = QtWidgets.QRadioButton(
            self.tr("🖼️ Open Image File")
        )
        openImageRadio.setToolTip(
            self.tr("Open a single image file for annotation")
        )
        self._source_dialog_group.addButton(openImageRadio, 3)
        layout.addWidget(openImageRadio)

        openImageDesc = QtWidgets.QLabel(
            self.tr("   Select a single image file to annotate")
        )
        openImageDesc.setStyleSheet("color: gray; margin-left: 20px;")
        layout.addWidget(openImageDesc)

        layout.addSpacing(20)

        # Buttons
        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)
        layout.addWidget(buttonBox)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            selected_id = self._source_dialog_group.checkedId()
            if selected_id == 0:
                return ImageModeSource.CURRENT_FRAME
            elif selected_id == 1:
                # WST - need to select folder first
                self._select_wst_folder()
                if self._wst_frames_dir:
                    return ImageModeSource.WST
                else:
                    return ImageModeSource.CURRENT_FRAME
            elif selected_id == 2:
                return ImageModeSource.AUTO_EXTRACT
            elif selected_id == 3:
                # Open single image
                if self._open_single_image():
                    return ImageModeSource.WST  # Use WST mode for single image
                else:
                    return ImageModeSource.CURRENT_FRAME

        return None  # User cancelled

    def _open_single_image(self) -> bool:
        """Open a single image file for annotation."""
        filters = self.tr("Image files (%s)") % " ".join(
            f"*{ext}" for ext in IMAGE_EXTENSIONS
        )
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.tr("Open Image"),
            osp.dirname(self.filename) if self.filename else ".",
            filters,
        )

        if filename:
            self._wst_frames_dir = osp.dirname(filename)
            self._wst_current_image = filename

            # Update combo with just this file
            self.wstImageCombo.blockSignals(True)
            self.wstImageCombo.clear()
            self.wstImageCombo.addItem(osp.basename(filename))
            self.wstImageCombo.blockSignals(False)

            self.wstPrevBtn.setEnabled(False)
            self.wstNextBtn.setEnabled(False)
            self.wstImageCombo.setEnabled(True)
            self.wstFolderBtn.setEnabled(True)

            return True
        return False

    def _load_image_for_annotation(self) -> None:
        """Load image for annotation based on current source mode."""
        if self._image_mode_source == ImageModeSource.CURRENT_FRAME:
            if self._video_capture is not None and self._current_frame >= 0:
                self._load_current_frame_to_canvas()
        elif self._image_mode_source == ImageModeSource.WST:
            if self._wst_current_image:
                self._load_wst_image(self._wst_current_image)
            elif self._wst_frames_dir:
                self._scan_wst_folder(self._wst_frames_dir)
        elif self._image_mode_source == ImageModeSource.AUTO_EXTRACT:
            self._auto_extract_and_load()

    def _load_current_frame_to_canvas(self) -> None:
        """Load the current video frame into the annotation canvas."""
        if self._video_capture is None:
            return

        self._video_capture.set(cv2.CAP_PROP_POS_FRAMES, self._current_frame)
        ret, frame = self._video_capture.read()

        if ret and frame is not None:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = frame_rgb.shape
            bytes_per_line = 3 * width
            qimage = QtGui.QImage(
                frame_rgb.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888
            )
            pixmap = QtGui.QPixmap.fromImage(qimage)
            self.canvas.loadPixmap(pixmap)
            self.canvas.setEnabled(True)

            # Store image data for saving
            pil_image = PIL.Image.fromarray(frame_rgb)
            with io.BytesIO() as f:
                pil_image.save(f, format="PNG")
                self._image_data = f.getvalue()

            self._zoom_fit()
            logger.info("Loaded frame {} to canvas for annotation", self._current_frame)

    # ==================== SAM Model Methods ====================

    def _on_sam_model_changed(self, model_name: str) -> None:
        """Handle SAM model selection change."""
        self._sam_model_name = model_name
        self.canvas.set_ai_model_name(model_name)
        logger.info("SAM model changed to: {}", model_name)
        self.statusBar().showMessage(self.tr("SAM model: %s") % model_name, 3000)

    # ==================== WST (Work with Saved Thumbnails) Methods ====================

    def _on_image_source_changed(self, index: int) -> None:
        """Handle image source mode change."""
        source_map = {
            0: ImageModeSource.CURRENT_FRAME,
            1: ImageModeSource.WST,
            2: ImageModeSource.AUTO_EXTRACT,
        }
        self._image_mode_source = source_map.get(index, ImageModeSource.CURRENT_FRAME)

        # Update WST controls visibility
        is_wst = self._image_mode_source == ImageModeSource.WST
        self.wstFolderBtn.setEnabled(is_wst)
        self.wstPrevBtn.setEnabled(is_wst and self._wst_frames_dir is not None)
        self.wstNextBtn.setEnabled(is_wst and self._wst_frames_dir is not None)
        self.wstImageCombo.setEnabled(is_wst and self._wst_frames_dir is not None)

        logger.info("Image source changed to: {}", self._image_mode_source.value)

        # Reload image if in image mode
        if self._app_mode == AppMode.IMAGE:
            self._load_image_for_annotation()

    def _select_wst_folder(self) -> None:
        """Select folder containing extracted frames for WST mode."""
        # Default to output_dir or video directory
        default_dir = self.output_dir or (
            osp.dirname(self.filename) if self.filename else "."
        )

        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            self.tr("Select Extracted Frames Folder"),
            default_dir,
            QtWidgets.QFileDialog.ShowDirsOnly,
        )

        if folder:
            self._scan_wst_folder(folder)

    def _scan_wst_folder(self, folder: str) -> None:
        """Scan folder for image files and populate image list."""
        self._wst_frames_dir = folder

        # Find all image files
        images = []
        for ext in IMAGE_EXTENSIONS:
            for f in os.listdir(folder):
                if f.lower().endswith(ext):
                    images.append(f)

        images = natsort.natsorted(images)
        self._wst_image_files = images

        # Update image list widget (left panel, like video list)
        self.imageListWidget.blockSignals(True)
        self.imageListWidget.clear()
        for img in images:
            item = QtWidgets.QListWidgetItem(img)
            item.setData(Qt.UserRole, osp.join(folder, img))  # Store full path
            self.imageListWidget.addItem(item)
        self.imageListWidget.blockSignals(False)

        # Also update combo box for backward compatibility
        self.wstImageCombo.blockSignals(True)
        self.wstImageCombo.clear()
        self.wstImageCombo.addItems(images)
        self.wstImageCombo.blockSignals(False)

        # Enable navigation controls
        has_images = len(images) > 0
        self.wstPrevBtn.setEnabled(has_images)
        self.wstNextBtn.setEnabled(has_images)
        self.wstImageCombo.setEnabled(has_images)

        # Update image count label
        self.imageCountLabel.setText(f"{len(images)} images")

        if has_images:
            # Select first image in list
            self.imageListWidget.setCurrentRow(0)
            self.wstImageCombo.setCurrentIndex(0)
            self._on_wst_image_changed(images[0])
            self.statusBar().showMessage(
                self.tr("Loaded %d images from %s") % (len(images), folder), 3000
            )
        else:
            self.statusBar().showMessage(
                self.tr("No images found in %s") % folder, 3000
            )

        logger.info("Scanned WST folder: {} ({} images)", folder, len(images))

    def _on_wst_image_changed(self, image_name: str) -> None:
        """Handle WST image selection change (from combo box)."""
        if not image_name or not self._wst_frames_dir:
            return

        image_path = osp.join(self._wst_frames_dir, image_name)
        self._load_wst_image(image_path)

        # Sync image list selection
        idx = self.wstImageCombo.currentIndex()
        if idx >= 0 and idx < self.imageListWidget.count():
            self.imageListWidget.blockSignals(True)
            self.imageListWidget.setCurrentRow(idx)
            self.imageListWidget.blockSignals(False)

    def _load_wst_image(self, image_path: str) -> None:
        """Load an image from WST folder into the canvas."""
        if not osp.exists(image_path):
            logger.warning("WST image not found: {}", image_path)
            return

        try:
            # Load image
            pil_image = PIL.Image.open(image_path)
            pil_image = pil_image.convert("RGB")

            # Convert to QPixmap
            img_array = np.array(pil_image)
            height, width, channel = img_array.shape
            bytes_per_line = 3 * width
            qimage = QtGui.QImage(
                img_array.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888
            )
            pixmap = QtGui.QPixmap.fromImage(qimage)

            # Load into canvas
            self.canvas.loadPixmap(pixmap)
            self.canvas.setEnabled(True)

            # Store image data for saving
            with io.BytesIO() as f:
                pil_image.save(f, format="PNG")
                self._image_data = f.getvalue()

            self._wst_current_image = image_path
            self._zoom_fit()

            # Try to load existing annotation
            self._load_existing_annotation(image_path)

            logger.info("Loaded WST image: {}", image_path)
            self.annotationStatusLabel.setText(
                f"Image: {osp.basename(image_path)}"
            )

        except Exception as e:
            logger.error("Failed to load WST image {}: {}", image_path, e)
            QMessageBox.warning(
                self,
                self.tr("Error"),
                self.tr("Failed to load image: %s") % str(e),
            )

    def _load_existing_annotation(self, image_path: str) -> None:
        """Load existing annotation JSON file if it exists."""
        json_path = osp.splitext(image_path)[0] + ".json"
        if not osp.exists(json_path):
            return

        try:
            label_file = LabelFile(json_path)
            shapes = []
            for shape_dict in label_file.shapes:
                shape = Shape(
                    label=shape_dict["label"],
                    shape_type=shape_dict["shape_type"],
                    flags=shape_dict.get("flags"),
                    group_id=shape_dict.get("group_id"),
                    description=shape_dict.get("description"),
                )
                for point in shape_dict["points"]:
                    shape.addPoint(QtCore.QPointF(point[0], point[1]))
                shape.close()
                shapes.append(shape)

            self.canvas.loadShapes(shapes)
            self._update_shape_list()
            logger.info("Loaded existing annotation from: {}", json_path)
            self.statusBar().showMessage(
                self.tr("Loaded %d shapes from existing annotation") % len(shapes),
                3000,
            )
        except Exception as e:
            logger.warning("Failed to load annotation {}: {}", json_path, e)

    def _wst_prev_image(self) -> None:
        """Go to previous image in WST mode."""
        current_row = self.imageListWidget.currentRow()
        if current_row > 0:
            self.imageListWidget.setCurrentRow(current_row - 1)

    def _wst_next_image(self) -> None:
        """Go to next image in WST mode."""
        current_row = self.imageListWidget.currentRow()
        if current_row < self.imageListWidget.count() - 1:
            self.imageListWidget.setCurrentRow(current_row + 1)

    def _image_search_changed(self, text: str) -> None:
        """Filter image list by search text."""
        for i in range(self.imageListWidget.count()):
            item = self.imageListWidget.item(i)
            if text.lower() in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)

    def _image_selection_changed(self) -> None:
        """Handle image list selection change."""
        items = self.imageListWidget.selectedItems()
        if not items:
            return

        item = items[0]
        image_path = item.data(Qt.UserRole)
        if image_path:
            self._load_wst_image(image_path)

            # Sync combo box
            idx = self.imageListWidget.row(item)
            self.wstImageCombo.blockSignals(True)
            self.wstImageCombo.setCurrentIndex(idx)
            self.wstImageCombo.blockSignals(False)

            # Update count label to show current position
            total = self.imageListWidget.count()
            self.imageCountLabel.setText(f"{idx + 1} / {total}")

    def _image_double_clicked(self, item: QtWidgets.QListWidgetItem) -> None:
        """Handle double click on image list item."""
        image_path = item.data(Qt.UserRole)
        if image_path:
            self._load_wst_image(image_path)

    def _auto_extract_and_load(self) -> None:
        """Auto-extract frames from current clip and load for annotation."""
        if self._video_capture is None:
            QMessageBox.warning(
                self,
                self.tr("No Video"),
                self.tr("Please load a video first."),
            )
            return

        if not self._clips:
            # No clips, just use current frame
            self._load_current_frame_to_canvas()
            return

        # Get output directory
        default_dir = self.output_dir or (
            osp.dirname(self.filename) if self.filename else "."
        )

        # Create temp folder for extracted frames
        video_name = osp.splitext(osp.basename(self.filename))[0] if self.filename else "video"
        extract_dir = osp.join(default_dir, f"{video_name}_frames")

        # Ask user for confirmation
        reply = QMessageBox.question(
            self,
            self.tr("Auto Extract"),
            self.tr(
                "Extract frames from %d clips to:\n%s\n\nContinue?"
            ) % (len(self._clips), extract_dir),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )

        if reply != QMessageBox.Yes:
            self._load_current_frame_to_canvas()
            return

        # Create directory
        os.makedirs(extract_dir, exist_ok=True)

        # Extract frames
        extracted_count = 0
        for clip in self._clips:
            # Extract start frame
            start_path = self._extract_single_frame(
                clip.start_frame,
                extract_dir,
                f"{clip.label}_start_{clip.start_frame}.png",
            )
            # Extract end frame
            end_path = self._extract_single_frame(
                clip.end_frame,
                extract_dir,
                f"{clip.label}_end_{clip.end_frame}.png",
            )
            if start_path and end_path:
                extracted_count += 1

        # Switch to WST mode with extracted folder
        self._image_mode_source = ImageModeSource.WST
        self.imageSourceCombo.setCurrentIndex(1)  # WST mode
        self._scan_wst_folder(extract_dir)

        self.statusBar().showMessage(
            self.tr("Extracted frames from %d clips to %s") % (extracted_count, extract_dir),
            5000,
        )
        logger.info("Auto-extracted frames from {} clips to {}", extracted_count, extract_dir)

    # ==================== Image Annotation Methods ====================

    def _set_create_mode(self, mode: str) -> None:
        """Set the canvas create mode."""
        self.canvas.createMode = mode
        self.canvas.setEditing(False)

        # Update button states
        self.polygonBtn.setChecked(mode == "polygon")
        self.rectangleBtn.setChecked(mode == "rectangle")
        self.circleBtn.setChecked(mode == "circle")
        self.lineBtn.setChecked(mode == "line")
        self.pointBtn.setChecked(mode == "point")
        self.aiPolygonBtn.setChecked(mode == "ai_polygon")
        self.editModeBtn.setChecked(False)

        self.statusBar().showMessage(self.tr("Create mode: %s") % mode)

    def _toggle_edit_mode(self) -> None:
        """Toggle between create and edit mode."""
        is_editing = not self.canvas.editing()
        self.canvas.setEditing(is_editing)
        self.editModeBtn.setChecked(is_editing)

        # Uncheck all create mode buttons when in edit mode
        if is_editing:
            self.polygonBtn.setChecked(False)
            self.rectangleBtn.setChecked(False)
            self.circleBtn.setChecked(False)
            self.lineBtn.setChecked(False)
            self.pointBtn.setChecked(False)
            self.aiPolygonBtn.setChecked(False)
            self.statusBar().showMessage(self.tr("Edit mode"))
        else:
            self.statusBar().showMessage(self.tr("Create mode"))

    def _on_new_shape(self) -> None:
        """Handle new shape created on canvas."""
        # Prompt for label
        text, flags, group_id, description = self.labelDialog.popUp()

        if text:
            self.canvas.setLastLabel(text, flags)
            shape = self.canvas.shapes[-1]
            shape.group_id = group_id
            shape.description = description
            self._update_shape_list()
            self._is_changed = True
            self.labelDialog.addLabelHistory(text)
        else:
            # User cancelled, remove the shape
            self.canvas.undoLastLine()
            self.canvas.shapesBackups.pop()

    def _on_shape_selection_changed(self, shapes: list) -> None:
        """Handle shape selection change on canvas."""
        self.canvas.selectedShapes = shapes
        for shape in self.canvas.shapes:
            shape.selected = shape in shapes
        self.canvas.update()

        # Update shape list selection
        self.shapeListWidget.blockSignals(True)
        self.shapeListWidget.clearSelection()
        for shape in shapes:
            for i in range(self.shapeListWidget.count()):
                item = self.shapeListWidget.item(i)
                if item.data(Qt.UserRole) is shape:
                    item.setSelected(True)
        self.shapeListWidget.blockSignals(False)

    def _on_shapes_changed(self) -> None:
        """Handle shapes changed (moved, etc.)."""
        self._is_changed = True

    def _on_drawing_polygon(self, drawing: bool) -> None:
        """Handle drawing polygon state change."""
        pass  # Can be used for UI updates

    def _on_zoom_request(self, delta: int, pos) -> None:
        """Handle zoom request from canvas."""
        zoom_factor = 1.1 if delta > 0 else 0.9
        self.canvas.scale *= zoom_factor
        self.canvas.adjustSize()
        self.canvas.update()

    def _on_scroll_request(self, delta: int, orientation: int) -> None:
        """Handle scroll request from canvas."""
        if orientation == Qt.Horizontal:
            bar = self.scrollArea.horizontalScrollBar()
        else:
            bar = self.scrollArea.verticalScrollBar()
        bar.setValue(bar.value() - delta)

    def _shape_list_selection_changed(self) -> None:
        """Handle shape list selection change."""
        items = self.shapeListWidget.selectedItems()
        shapes = [item.data(Qt.UserRole) for item in items]
        self.canvas.selectShapes(shapes)

    def _shape_list_double_clicked(self, item) -> None:
        """Handle shape list double click - edit label."""
        shape = item.data(Qt.UserRole)
        if shape is None:
            return

        text, flags, group_id, description = self.labelDialog.popUp(
            text=shape.label,
            flags=shape.flags,
            group_id=shape.group_id,
            description=shape.description,
        )

        if text:
            shape.label = text
            shape.flags = flags
            shape.group_id = group_id
            shape.description = description
            self._update_shape_list()
            self._is_changed = True

    def _pop_shape_list_menu(self, point: QtCore.QPoint) -> None:
        """Show context menu for shape list."""
        item = self.shapeListWidget.itemAt(point)
        if item is not None:
            # Enable/disable actions based on selection
            has_selection = len(self.shapeListWidget.selectedItems()) > 0
            self._shape_edit_label_action.setEnabled(has_selection)
            self._shape_delete_action.setEnabled(has_selection)
            
            # Show menu at cursor position
            self._shape_context_menu.exec_(self.shapeListWidget.mapToGlobal(point))

    def _update_shape_list(self) -> None:
        """Update the shape list widget."""
        self.shapeListWidget.clear()
        for shape in self.canvas.shapes:
            item = QtWidgets.QListWidgetItem(shape.label or "Unnamed")
            item.setData(Qt.UserRole, shape)
            self.shapeListWidget.addItem(item)

    def _setup_canvas_context_menus(self) -> None:
        """Setup right-click context menus for canvas.
        
        The canvas has two menus:
        - menus[0]: shown when right-clicking without shape copy
        - menus[1]: shown when right-clicking with shape copy (drag copy)
        
        Both menus show shape editing options.
        """
        # Create actions for context menu
        edit_label_action = QtWidgets.QAction(self.tr("Edit Label"), self)
        edit_label_action.triggered.connect(self._edit_shape_label)
        
        edit_mode_action = QtWidgets.QAction(self.tr("🔧 Edit/Move Mode"), self)
        edit_mode_action.triggered.connect(self._toggle_edit_mode)
        
        # Remove point action (only enabled when a vertex is selected)
        self._remove_point_action = QtWidgets.QAction(self.tr("Remove Selected Point"), self)
        self._remove_point_action.triggered.connect(self._remove_selected_point)
        self._remove_point_action.setEnabled(False)
        
        delete_shape_action = QtWidgets.QAction(self.tr("❌ Delete Shape"), self)
        delete_shape_action.triggered.connect(self._delete_selected_shapes)
        
        undo_action = QtWidgets.QAction(self.tr("Undo"), self)
        undo_action.triggered.connect(self._undo_shape_edit)
        
        # Drawing mode actions
        polygon_action = QtWidgets.QAction(self.tr("Draw Polygon"), self)
        polygon_action.triggered.connect(lambda: self._set_create_mode("polygon"))
        
        rectangle_action = QtWidgets.QAction(self.tr("Draw Rectangle"), self)
        rectangle_action.triggered.connect(lambda: self._set_create_mode("rectangle"))
        
        ai_polygon_action = QtWidgets.QAction(self.tr("AI Polygon (SAM)"), self)
        ai_polygon_action.triggered.connect(lambda: self._set_create_mode("ai_polygon"))
        
        # Add actions to both menus
        for menu in self.canvas.menus:
            menu.addAction(edit_label_action)
            menu.addAction(edit_mode_action)
            menu.addSeparator()
            menu.addAction(polygon_action)
            menu.addAction(rectangle_action)
            menu.addAction(ai_polygon_action)
            menu.addSeparator()
            menu.addAction(self._remove_point_action)
            menu.addAction(delete_shape_action)
            menu.addAction(undo_action)
        
        # Connect vertexSelected signal to enable/disable remove point action
        self.canvas.vertexSelected.connect(self._remove_point_action.setEnabled)

    def _edit_shape_label(self) -> None:
        """Edit the label of the selected shape."""
        if not self.canvas.selectedShapes:
            return
        
        shape = self.canvas.selectedShapes[0]
        
        # Show label dialog
        text, flags, group_id, description = self.labelDialog.popUp(
            text=shape.label,
            flags=shape.flags,
            group_id=shape.group_id,
            description=shape.description,
        )
        
        if text is not None:
            shape.label = text
            shape.flags = flags
            shape.group_id = group_id
            shape.description = description
            self._update_shape_list()
            self._is_changed = True
            logger.info("Shape label changed to: {}", text)

    def _undo_shape_edit(self) -> None:
        """Undo last shape edit."""
        if self.canvas.isShapeRestorable:
            self.canvas.restoreShape()
            self._update_shape_list()
            self._is_changed = True

    def _remove_selected_point(self) -> None:
        """Remove the selected point from a polygon shape."""
        self.canvas.removeSelectedPoint()
        self.canvas.update()
        
        # If the shape has no points left, delete it
        if self.canvas.hShape and not self.canvas.hShape.points:
            self.canvas.deleteShape(self.canvas.hShape)
            self._update_shape_list()
        
        self._is_changed = True

    def _delete_selected_shapes(self) -> None:
        """Delete selected shapes."""
        deleted = self.canvas.deleteSelected()
        if deleted:
            self._update_shape_list()
            self._is_changed = True

    def _zoom_in(self) -> None:
        """Zoom in."""
        self.canvas.scale *= 1.2
        self.canvas.adjustSize()
        self.canvas.update()

    def _zoom_out(self) -> None:
        """Zoom out."""
        self.canvas.scale *= 0.8
        self.canvas.adjustSize()
        self.canvas.update()

    def _zoom_fit(self) -> None:
        """Zoom to fit window."""
        if not self.canvas.pixmap:
            return
        # Calculate scale to fit
        canvas_size = self.scrollArea.size()
        pixmap_size = self.canvas.pixmap.size()
        scale_w = canvas_size.width() / pixmap_size.width()
        scale_h = canvas_size.height() / pixmap_size.height()
        self.canvas.scale = min(scale_w, scale_h) * 0.95
        self.canvas.adjustSize()
        self.canvas.update()

    def _zoom_100(self) -> None:
        """Zoom to 100%."""
        self.canvas.scale = 1.0
        self.canvas.adjustSize()
        self.canvas.update()

    def _save_annotation(self) -> None:
        """Save annotation to labelme JSON format."""
        if not self.canvas.shapes:
            QMessageBox.information(
                self,
                self.tr("No Shapes"),
                self.tr("There are no shapes to save."),
            )
            return

        # Get annotations output directory (creates <video_name>/annotations/)
        annotations_dir = self._get_video_output_dir("annotations")
        if not annotations_dir:
            return

        # Determine output filename
        if self.filename:
            base_name = osp.splitext(osp.basename(self.filename))[0]
            # Include current image name if in WST mode
            if self._wst_current_image:
                img_name = osp.splitext(osp.basename(self._wst_current_image))[0]
                default_name = f"{img_name}.json"
            else:
                default_name = f"{base_name}_frame{self._current_frame}.json"
        else:
            default_name = "annotation.json"

        default_path = osp.join(annotations_dir, default_name)

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            self.tr("Save Annotation"),
            default_path,
            self.tr("JSON files (*.json)"),
        )

        if not filename:
            return

        # Also save the image
        image_filename = osp.splitext(filename)[0] + ".png"

        try:
            # Prepare shapes data
            shapes_data = []
            for shape in self.canvas.shapes:
                shape_dict = {
                    "label": shape.label or "",
                    "points": [[p.x(), p.y()] for p in shape.points],
                    "shape_type": shape.shape_type,
                    "flags": shape.flags or {},
                    "group_id": shape.group_id,
                    "description": shape.description or "",
                }
                if shape.mask is not None:
                    # Encode mask as base64 PNG
                    mask_img = PIL.Image.fromarray(shape.mask.astype(np.uint8) * 255)
                    with io.BytesIO() as f:
                        mask_img.save(f, format="PNG")
                        shape_dict["mask"] = base64.b64encode(f.getvalue()).decode(
                            "utf-8"
                        )
                shapes_data.append(shape_dict)

            # Get image dimensions
            if self.canvas.pixmap:
                img_height = self.canvas.pixmap.height()
                img_width = self.canvas.pixmap.width()
            else:
                img_height = self._frame_height
                img_width = self._frame_width

            # Prepare label file data (labelme format)
            label_data = {
                "version": __version__,
                "flags": {},
                "shapes": shapes_data,
                "imagePath": osp.basename(image_filename),
                "imageData": None,  # Don't embed image data by default
                "imageHeight": img_height,
                "imageWidth": img_width,
            }

            # Write JSON
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(label_data, f, ensure_ascii=False, indent=2)

            # Save image
            if self._image_data:
                with open(image_filename, "wb") as f:
                    f.write(self._image_data)

            self._is_changed = False
            self.statusBar().showMessage(
                self.tr("Saved annotation to %s") % filename, 5000
            )
            logger.info("Saved annotation to {} and image to {}", filename, image_filename)

        except Exception as e:
            logger.error("Failed to save annotation: {}", e)
            QMessageBox.critical(
                self,
                self.tr("Error"),
                self.tr("Failed to save annotation: %s") % str(e),
            )


def _new_action(
    parent: QtWidgets.QWidget,
    text: str,
    slot=None,
    shortcut: str | None = None,
    icon: str | None = None,
    tip: str | None = None,
    checkable: bool = False,
    enabled: bool = True,
) -> QtWidgets.QAction:
    """Create a new QAction."""
    action = QtWidgets.QAction(text, parent)
    if slot is not None:
        action.triggered.connect(slot)
    if shortcut is not None:
        action.setShortcut(shortcut)
    if tip is not None:
        action.setToolTip(tip)
        action.setStatusTip(tip)
    action.setCheckable(checkable)
    action.setEnabled(enabled)
    return action


def _scan_video_files(root_dir: str) -> list[str]:
    """Scan directory for video files."""
    videos: list[str] = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in VIDEO_EXTENSIONS):
                rel_path = os.path.normpath(osp.join(root, file))
                videos.append(rel_path)

    logger.debug("Found {} videos in {}", len(videos), root_dir)
    return natsort.os_sorted(videos)


def _format_time(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _get_color_for_index(index: int) -> tuple[int, int, int]:
    """Get a distinct color for a clip index."""
    colors = [
        (76, 175, 80),  # Green
        (33, 150, 243),  # Blue
        (255, 152, 0),  # Orange
        (156, 39, 176),  # Purple
        (0, 188, 212),  # Cyan
        (244, 67, 54),  # Red
        (255, 235, 59),  # Yellow
        (121, 85, 72),  # Brown
    ]
    return colors[index % len(colors)]
