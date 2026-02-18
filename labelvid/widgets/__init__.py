"""Widgets for labelvid."""

from .canvas import Canvas
from .caption_analysis_widget import CaptionAnalysisWidget
from .clip_dialog import ClipDialog
from .clip_dialog import get_object_list
from .clip_dialog import set_object_list
from .clip_list_widget import ClipListWidget
from .clip_list_widget import ClipListWidgetItem
from .clip_timeline_widget import ClipTimelineWidget
from .label_dialog import LabelDialog
from .label_dialog import set_label_dialog_object_list
from .label_dialog import get_label_dialog_object_list
from .object_list_dialog import ObjectListDialog
from .video_player_widget import VideoPlayerWidget

__all__ = [
    "Canvas",
    "CaptionAnalysisWidget",
    "ClipDialog",
    "ClipListWidget",
    "ClipListWidgetItem",
    "ClipTimelineWidget",
    "LabelDialog",
    "ObjectListDialog",
    "VideoPlayerWidget",
    "get_object_list",
    "set_object_list",
    "set_label_dialog_object_list",
    "get_label_dialog_object_list",
]
