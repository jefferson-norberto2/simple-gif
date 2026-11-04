"""Módulo de widgets e telas personalizadas da interface gráfica."""

from simplegif.ui.widgets.range_slider import RangeSlider
from simplegif.ui.widgets.screen_initial import InitialScreen
from simplegif.ui.widgets.screen_options import OptionsScreen
from simplegif.ui.widgets.screen_processing import ProcessingScreen
from simplegif.ui.widgets.screen_result import ResultScreen
from simplegif.ui.widgets.video_preview import VideoPreviewWidget

__all__ = [
    "RangeSlider",
    "VideoPreviewWidget",
    "InitialScreen",
    "OptionsScreen",
    "ProcessingScreen",
    "ResultScreen",
]
