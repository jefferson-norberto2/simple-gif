"""Testes unitários para a arquitetura modular da UI (controllers e widgets)."""

import os
from pathlib import Path
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from simplegif.core import SimpleGIF
from simplegif.ui.controllers import ConversionController, PreviewController
from simplegif.ui.helpers import format_seconds, load_stylesheet
from simplegif.ui.widgets import (
    InitialScreen,
    OptionsScreen,
    ProcessingScreen,
    RangeSlider,
    ResultScreen,
    VideoPreviewWidget,
)


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_ui_helpers() -> None:
    """Verifica funções auxiliares de formatação e stylesheet."""
    assert format_seconds(0.0) == "00:00.0"
    assert format_seconds(65.5) == "01:05.5"
    stylesheet = load_stylesheet()
    assert isinstance(stylesheet, str)
    assert len(stylesheet) > 0


def test_range_slider_widget(qapp: QApplication) -> None:
    """Valida o funcionamento e limites do widget RangeSlider."""
    slider = RangeSlider()
    slider.set_range_bounds(0, 100)
    assert slider.minimum() == 0
    assert slider.maximum() == 100

    slider.set_values(10, 50, emit_signals=True)
    assert slider.start_value() == 10
    assert slider.end_value() == 50

    slider.set_current_value(30)
    assert slider.current_value() == 30


def test_preview_controller(qapp: QApplication, sample_video_path: Path) -> None:
    """Valida o carregamento, renderização e cálculo de estimativa no PreviewController."""
    controller = PreviewController()
    try:
        meta = controller.load_video(sample_video_path)
        assert meta.total_frames == 30
        assert meta.fps == pytest.approx(10.0, abs=0.5)

        pixmap = controller.render_frame_at(0)
        assert pixmap is not None
        assert not pixmap.isNull()

        # Estimativa de tamanho
        est_bytes = controller.estimate_size_bytes(
            scale=0.5,
            frame_skip=1,
            less_colors=True,
            start_frame=0,
            end_frame=29,
        )
        assert est_bytes > 0

        # Reprodução em loop
        controller.start_playback(start_frame=0, end_frame=10, current_frame=0)
        assert controller.is_playing
        controller.stop_playback()
        assert not controller.is_playing
    finally:
        controller.close()


def test_video_preview_widget(qapp: QApplication) -> None:
    """Valida o widget composto VideoPreviewWidget."""
    preview_widget = VideoPreviewWidget()
    preview_widget.setup_video(fps=10.0, total_frames=30, duration_seconds=3.0)

    start_f, end_f = preview_widget.get_selected_range_frames()
    assert start_f == 0
    assert end_f == 29

    start_sec, end_sec = preview_widget.get_selected_time_range()
    assert start_sec == 0.0
    assert end_sec == pytest.approx(3.0, abs=0.1)

    preview_widget.set_playback_playing(True)
    assert preview_widget.btn_play_preview.text() == "⏸ Pausar"
    preview_widget.set_playback_playing(False)
    assert preview_widget.btn_play_preview.text() == "▶ Preview"


def test_screens_instantiation(qapp: QApplication, tmp_path: Path) -> None:
    """Valida a criação e atualização de estado das telas individuais."""
    s1 = InitialScreen()
    assert s1.btn_select is not None

    s2 = OptionsScreen()
    s2.set_size_estimate_text("Estimativa teste")
    assert s2.lbl_size_estimate.text() == "Estimativa teste"
    assert s2.get_selected_scale() > 0.0

    s3 = ProcessingScreen()
    s3.reset_progress()
    assert s3.read_progress_bar.value() == 0
    s3.update_read_progress(10, 20)
    assert s3.read_progress_bar.value() == 50
    s3.update_save_progress(5, 10)
    assert s3.save_progress_bar.value() == 50

    s4 = ResultScreen()
    fake_gif = tmp_path / "result.gif"
    fake_gif.touch()
    s4.show_result(success=True, gif_path=fake_gif)
    assert not s4.entry_res_path.isHidden()
    assert s4.entry_res_path.text() == str(fake_gif)

    s4.show_result(success=False, error_msg="Erro de teste")
    assert s4.entry_res_path.isHidden()
