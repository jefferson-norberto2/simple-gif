"""Testes dos 4 estados da interface Widescreen em Tela Única conforme adjust_interface.md."""

import os
from pathlib import Path
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from simplegif.ui.app import GifConverterApp


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_state_1_initial_without_video(qapp: QApplication) -> None:
    """Valida o Estado 1 — Inicial: placeholder exibido e controles desabilitados."""
    window = GifConverterApp()
    try:
        # Verifica dimensões widescreen
        assert window.minimumWidth() >= 900
        assert window.minimumHeight() >= 500

        # Placeholder do preview
        assert "Nenhum vídeo selecionado" in window.lbl_video_preview.text()

        # Controles desabilitados até carregar vídeo
        assert not window.range_slider.isEnabled()
        assert not window.spin_start_time.isEnabled()
        assert not window.spin_end_time.isEnabled()
        assert not window.btn_play_preview.isEnabled()
        assert not window.screen_options.btn_start.isEnabled()

        # Metadados e caminhos vazios
        assert window.screen_options.lbl_video_meta.text() == ""
        assert window.entry_input_path.text() == ""
        assert window.entry_output_dir.text() == ""

        # Estimativa inicial
        assert "📊 Estimado: --" in window.lbl_size_estimate.text()
        assert not window.screen_options.progress_bar.isVisible()
        assert not window.screen_options.btn_open_folder.isVisible()
    finally:
        window.close()


def test_state_2_video_loaded(qapp: QApplication, sample_video_path: Path) -> None:
    """Valida o Estado 2 — Vídeo Carregado: preview ativo, metadados e controles habilitados."""
    window = GifConverterApp()
    try:
        window.load_video_file(sample_video_path)

        # Metadados no topo
        meta_text = window.screen_options.lbl_video_meta.text()
        assert "120x90" in meta_text
        assert "10.0 FPS" in meta_text

        # Preview e controles habilitados
        assert window.lbl_video_preview.pixmap() is not None
        assert not window.lbl_video_preview.pixmap().isNull()
        assert window.range_slider.isEnabled()
        assert window.spin_start_time.isEnabled()
        assert window.spin_end_time.isEnabled()
        assert window.btn_play_preview.isEnabled()
        assert window.screen_options.btn_start.isEnabled()

        # Pasta de saída preenchida automaticamente com a pasta do vídeo
        assert window.entry_output_dir.text() == str(sample_video_path.parent)

        # Estimativa e botão de início visíveis
        assert "Tamanho estimado: ~" in window.lbl_size_estimate.text()
        assert not window.lbl_size_estimate.isHidden()
        assert not window.screen_options.btn_start.isHidden()
        assert window.screen_options.progress_bar.isHidden()
    finally:
        window.close()


def test_state_3_converting_in_place(qapp: QApplication, sample_video_path: Path) -> None:
    """Valida o Estado 3 — Convertendo: inputs bloqueados e barra de progresso visível in-place."""
    window = GifConverterApp()
    try:
        window.load_video_file(sample_video_path)

        # Simula o início da conversão (set_converting_state)
        window.screen_options.set_converting_state()

        # Controles desabilitados
        assert not window.range_slider.isEnabled()
        assert not window.spin_start_time.isEnabled()
        assert not window.combo_scale.isEnabled()
        assert not window.spin_frame_skip.isEnabled()
        assert not window.chk_less_colors.isEnabled()
        assert not window.chk_overwrite.isEnabled()

        # Estimativa e botão Iniciar ocultos
        assert window.lbl_size_estimate.isHidden()
        assert window.screen_options.btn_start.isHidden()

        # Barra e status visíveis
        assert not window.screen_options.progress_bar.isHidden()
        assert not window.screen_options.lbl_progress_status.isHidden()

        # Simula progresso da etapa 1 (leitura de frames: 0% a 50%)
        window._on_read_progress(15, 30)
        assert window.screen_options.progress_bar.value() == 25
        assert "50%" in window.screen_options.lbl_progress_status.text()

        # Simula progresso da etapa 2 (salvamento: 50% a 100%)
        window._on_save_progress(10, 20)
        assert window.screen_options.progress_bar.value() == 75
        assert "Salvando arquivo GIF" in window.screen_options.lbl_progress_status.text()
    finally:
        window.close()


def test_state_4_conversion_completed_and_parameter_change(
    qapp: QApplication, sample_video_path: Path, tmp_path: Path
) -> None:
    """Valida o Estado 4 — Conclusão com sucesso, reabilitação e restauração ao alterar parâmetros."""
    window = GifConverterApp()
    try:
        window.load_video_file(sample_video_path)
        fake_gif = tmp_path / "out.gif"
        fake_gif.touch()

        # Simula término da conversão
        window.on_conversion_completed(fake_gif)

        # Controles reabilitados
        assert window.range_slider.isEnabled()
        assert window.combo_scale.isEnabled()
        assert window.spin_frame_skip.isEnabled()
        assert window.screen_options.btn_start.isEnabled()
        assert not window.screen_options.btn_start.isHidden()

        # Feedback in-place de sucesso e botão para abrir pasta
        assert window.screen_options.progress_bar.isHidden()
        assert not window.screen_options.lbl_result_status.isHidden()
        assert "✅ GIF salvo com sucesso!" in window.screen_options.lbl_result_status.text()
        assert not window.screen_options.btn_open_folder.isHidden()

        # Ao alterar qualquer parâmetro (ex: escala), volta a exibir a estimativa normalmente
        window.combo_scale.setCurrentIndex(0)
        assert window.screen_options.lbl_result_status.isHidden()
        assert window.screen_options.btn_open_folder.isHidden()
        assert not window.lbl_size_estimate.isHidden()
        assert "Tamanho estimado: ~" in window.lbl_size_estimate.text()
    finally:
        window.close()


def test_state_4_conversion_failed_feedback(
    qapp: QApplication, sample_video_path: Path
) -> None:
    """Valida o feedback in-place quando a conversão falha."""
    window = GifConverterApp()
    try:
        window.load_video_file(sample_video_path)

        window.on_conversion_failed("Erro de disco", is_file_exists=False)

        assert window.screen_options.btn_start.isEnabled()
        assert not window.screen_options.btn_start.isHidden()
        assert not window.screen_options.lbl_result_status.isHidden()
        assert "❌ Erro de disco" in window.screen_options.lbl_result_status.text()
        assert window.screen_options.btn_open_folder.isHidden()
    finally:
        window.close()
