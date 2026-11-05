"""Testes unitários e de integração para preview de vídeo e seleção de intervalo (range)."""

import os
from pathlib import Path
import socket
from PIL import Image
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from simplegif import SimpleGIF
from simplegif.ui.app import GifConverterApp
from simplegif.utils import ConversionOptions, FrameProcessor, GifWriter, VideoReader


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Garante uma instância de QApplication para testes de widgets PySide6."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_video_metadata_and_preview_frame_reading(sample_video_path: Path) -> None:
    """Valida a leitura de metadados de duração e extração de quadros de preview sob demanda."""
    with VideoReader(sample_video_path) as reader:
        meta = reader.metadata
        assert meta.width == 120
        assert meta.height == 90
        assert meta.fps == pytest.approx(10.0, abs=0.5)
        assert meta.total_frames == 30
        assert meta.duration_seconds == pytest.approx(3.0, abs=0.2)

        frame_start = reader.read_frame_at(0)
        frame_mid = reader.read_frame_at_time(1.5)
        frame_end = reader.read_frame_at(29)

        assert frame_start is not None
        assert frame_mid is not None
        assert frame_end is not None
        assert frame_start.shape == (90, 120, 3)


def test_convert_file_with_selected_time_range(sample_video_path: Path, tmp_path: Path) -> None:
    """Verifica se a conversão gera o GIF apenas com os quadros do intervalo de tempo selecionado."""
    gif_maker = SimpleGIF()
    output_gif = tmp_path / "trimmed.gif"

    # Vídeo tem 3.0s (30 frames a 10 FPS). Recorte de 1.0s a 2.0s = 10 frames (frame_skip=1).
    result_path = gif_maker.convert_file(
        path=sample_video_path,
        output_path=output_gif,
        scale=0.5,
        frame_skip=1,
        start_time=1.0,
        end_time=2.0,
        overwrite=True,
    )

    assert result_path.is_file()
    with Image.open(result_path) as gif_img:
        assert gif_img.size == (60, 45)
        assert getattr(gif_img, "n_frames", 1) == 10


def test_invalid_time_range_raises_value_error(sample_video_path: Path, tmp_path: Path) -> None:
    """Garante que parâmetros inválidos de start_time e end_time levantam ValueError."""
    with pytest.raises(ValueError, match="start_time"):
        ConversionOptions(start_time=-1.0)

    with pytest.raises(ValueError, match="end_time"):
        ConversionOptions(start_time=2.0, end_time=1.0)

    gif_maker = SimpleGIF()
    with pytest.raises(ValueError):
        gif_maker.convert_file(
            path=sample_video_path,
            output_path=tmp_path,
            start_time=2.5,
            end_time=1.0,
        )


def test_ui_preview_and_range_slider_sync(qapp: QApplication, sample_video_path: Path) -> None:
    """Testa o carregamento do preview na interface gráfica e a sincronização entre RangeSlider e SpinBoxes."""
    window = GifConverterApp()
    try:
        window.load_video_file(sample_video_path)

        assert window.stacked_widget.currentIndex() == 1
        assert window.preview_reader is not None
        assert window.lbl_video_preview.pixmap() is not None
        assert not window.lbl_video_preview.pixmap().isNull()

        # Altera o range pelo slider (frames 5 a 20 em um vídeo de 10 FPS -> 0.5s a 2.1s)
        window.range_slider.set_values(5, 20, emit_signals=True)
        assert window.spin_start_time.value() == pytest.approx(0.5, abs=0.05)
        assert window.spin_end_time.value() == pytest.approx(2.1, abs=0.05)

        # Altera pelos spinboxes e verifica atualização do RangeSlider
        window.spin_start_time.setValue(1.0)
        window.spin_end_time.setValue(2.5)
        assert window.range_slider.start_value() == 10
        assert window.range_slider.end_value() == 24
    finally:
        window.close()


def test_gif_size_estimation_core_and_ui(qapp: QApplication, sample_video_path: Path) -> None:
    """Valida o cálculo e a atualização dinâmica da estimativa de tamanho do GIF no core e na UI."""
    gif_maker = SimpleGIF()
    est_full = gif_maker.estimate_file_size(sample_video_path, scale=1.0, frame_skip=1, less_colors=False)
    est_half_range = gif_maker.estimate_file_size(
        sample_video_path, scale=1.0, frame_skip=1, less_colors=False, start_time=0.0, end_time=1.5
    )
    est_less_colors = gif_maker.estimate_file_size(
        sample_video_path, scale=1.0, frame_skip=1, less_colors=True
    )

    assert est_full > est_half_range > 0
    assert est_less_colors < est_full
    assert "KB" in GifWriter.format_file_size(50 * 1024)
    assert "MB" in GifWriter.format_file_size(3 * 1024 * 1024)

    window = GifConverterApp()
    try:
        window.load_video_file(sample_video_path)
        size_initial = window.get_estimated_gif_size_bytes()
        assert size_initial > 0
        assert "Tamanho estimado: ~" in window.lbl_size_estimate.text()

        # Reduzir o range pela metade reduz o tamanho estimado
        window.range_slider.set_values(0, 14, emit_signals=True)
        size_shorter_range = window.get_estimated_gif_size_bytes()
        assert size_shorter_range < size_initial

        # Aumentar o frame_skip reduz o tamanho estimado
        window.spin_frame_skip.setValue(1)
        size_skip_1 = window.get_estimated_gif_size_bytes()
        window.spin_frame_skip.setValue(5)
        size_skip_5 = window.get_estimated_gif_size_bytes()
        assert size_skip_5 < size_skip_1

        # Desmarcar redução de paleta aumenta o tamanho estimado
        window.chk_less_colors.setChecked(True)
        size_less_colors = window.get_estimated_gif_size_bytes()
        window.chk_less_colors.setChecked(False)
        size_more_colors = window.get_estimated_gif_size_bytes()
        assert size_less_colors < size_more_colors
    finally:
        window.close()


def test_offline_isolation_during_range_conversion(
    sample_video_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Garante que nenhuma chamada de rede seja realizada durante o preview ou conversão."""

    def guard_socket(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("Chamada de rede bloqueada pela política 100% offline!")

    monkeypatch.setattr(socket, "socket", guard_socket)

    gif_maker = SimpleGIF()
    out_file = gif_maker.convert_file(
        path=sample_video_path,
        output_path=tmp_path / "offline.gif",
        start_time=0.5,
        end_time=1.5,
        frame_skip=2,
    )
    assert out_file.is_file()


def test_convert_file_with_playback_speed(sample_video_path: Path, tmp_path: Path) -> None:
    """Verifica se a conversão com velocidade ajusta a duração dos quadros no GIF."""
    gif_maker = SimpleGIF()

    # Duração calculada diretamente
    dur_1x = GifWriter.calculate_frame_duration_ms(video_fps=10.0, frame_skip=1, speed=1.0)
    dur_2x = GifWriter.calculate_frame_duration_ms(video_fps=10.0, frame_skip=1, speed=2.0)
    dur_half = GifWriter.calculate_frame_duration_ms(video_fps=10.0, frame_skip=1, speed=0.5)

    assert dur_1x == 100
    assert dur_2x == 50
    assert dur_half == 200

    out_2x = tmp_path / "speed_2x.gif"
    gif_maker.convert_file(
        path=sample_video_path,
        output_path=out_2x,
        scale=0.5,
        speed=2.0,
        frame_skip=1,
        start_time=0.0,
        end_time=1.0,
        overwrite=True,
    )
    with Image.open(out_2x) as img:
        assert img.info["duration"] == 50

    out_half = tmp_path / "speed_half.gif"
    gif_maker.convert_file(
        path=sample_video_path,
        output_path=out_half,
        scale=0.5,
        speed=0.5,
        frame_skip=1,
        start_time=0.0,
        end_time=1.0,
        overwrite=True,
    )
    with Image.open(out_half) as img:
        assert img.info["duration"] == 200


def test_frame_processor_draw_speed_badge_positions_and_sizes() -> None:
    """Valida o desenho do indicador de velocidade para todas as posições, tamanhos e proporção."""
    base_img = Image.new("RGB", (640, 360), (128, 128, 128))

    # Testa as 6 posições suportadas
    positions = [
        "Superior Direito",
        "Superior Esquerdo",
        "Inferior Direito",
        "Inferior Esquerdo",
        "Centro Superior",
        "Centro Inferior",
    ]
    for pos in positions:
        result = FrameProcessor.draw_speed_badge(
            image=base_img,
            speed=2.0,
            position=pos,
            size_mode="Médio",
        )
        assert result.size == (640, 360)
        assert result.mode == "RGB"
        # Deve haver pixels pretos/transparentes e brancos desenhados pelo banner
        diff = sum(1 for p1, p2 in zip(result.getdata(), base_img.getdata()) if p1 != p2)
        assert diff > 0

    # Testa tamanhos (Pequeno, Médio, Grande) e proporção
    small = FrameProcessor.draw_speed_badge(base_img, speed=1.5, position="Superior Direito", size_mode="Pequeno")
    med = FrameProcessor.draw_speed_badge(base_img, speed=1.5, position="Superior Direito", size_mode="Médio")
    large = FrameProcessor.draw_speed_badge(base_img, speed=1.5, position="Superior Direito", size_mode="Grande")

    diff_small = sum(1 for p1, p2 in zip(small.getdata(), base_img.getdata()) if p1 != p2)
    diff_med = sum(1 for p1, p2 in zip(med.getdata(), base_img.getdata()) if p1 != p2)
    diff_large = sum(1 for p1, p2 in zip(large.getdata(), base_img.getdata()) if p1 != p2)

    # Grande ocupa mais pixels modificados que Médio, que ocupa mais que Pequeno
    assert diff_large > diff_med > diff_small


def test_convert_file_with_speed_badge_overlay(sample_video_path: Path, tmp_path: Path) -> None:
    """Verifica se a conversão com indicador de velocidade gera o GIF com o banner renderizado."""
    gif_maker = SimpleGIF()
    out_no_badge = tmp_path / "no_badge.gif"
    out_with_badge = tmp_path / "with_badge.gif"

    gif_maker.convert_file(
        path=sample_video_path,
        output_path=out_no_badge,
        scale=0.5,
        speed=2.0,
        frame_skip=2,
        start_time=0.0,
        end_time=1.0,
        show_speed_badge=False,
        overwrite=True,
    )

    gif_maker.convert_file(
        path=sample_video_path,
        output_path=out_with_badge,
        scale=0.5,
        speed=2.0,
        frame_skip=2,
        start_time=0.0,
        end_time=1.0,
        show_speed_badge=True,
        badge_position="Superior Direito",
        badge_size="Médio",
        overwrite=True,
    )

    assert out_no_badge.is_file()
    assert out_with_badge.is_file()

    with Image.open(out_no_badge) as img1, Image.open(out_with_badge) as img2:
        img1.seek(0)
        img2.seek(0)
        # O quadro com badge deve ter diferenças visuais devido ao banner desenhado
        frame1 = img1.convert("RGB")
        frame2 = img2.convert("RGB")
        diff_count = sum(1 for p1, p2 in zip(frame1.getdata(), frame2.getdata()) if p1 != p2)
        assert diff_count > 0
