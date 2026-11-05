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
        assert window.entry_gif_name.text() == ""
        assert not window.entry_gif_name.isEnabled()
        assert not window.chk_overwrite.isEnabled()
        assert not window.chk_overwrite.isChecked()

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

        # Nome do GIF preenchido automaticamente com o stem do vídeo e habilitado
        assert window.entry_gif_name.text() == sample_video_path.stem
        assert window.entry_gif_name.isEnabled()
        assert window.chk_overwrite.isEnabled()

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


def test_estimation_beyond_3000_frames(qapp: QApplication) -> None:
    """Valida que vídeos com mais de 3000 quadros não são limitados artificialmente a 600 quadros."""
    import numpy as np
    from simplegif.utils.config import ConversionOptions, VideoMetadata
    from simplegif.utils.writer import GifWriter

    # Testa o estimador com metadados sintéticos de 5000 quadros vs 3000 quadros
    meta_5000 = VideoMetadata(width=640, height=360, fps=30.0, total_frames=5000)
    meta_3000 = VideoMetadata(width=640, height=360, fps=30.0, total_frames=3000)
    opts_skip5 = ConversionOptions(scale=0.5, frame_skip=5, less_colors=True)
    sample_frame = np.zeros((360, 640, 3), dtype=np.uint8)

    est_5000 = GifWriter.estimate_gif_size(meta_5000, opts_skip5, sample_frame=sample_frame)
    est_3000 = GifWriter.estimate_gif_size(meta_3000, opts_skip5, sample_frame=sample_frame)

    assert est_5000 > est_3000

    # Testa na janela da aplicação com RangeSlider simulando 5000 quadros
    window = GifConverterApp()
    try:
        class _MockReader:
            metadata = meta_5000

            def close(self) -> None:
                pass

        window.preview_controller.reader = _MockReader()
        window.range_slider.set_range_bounds(0, 4999)
        window.range_slider.set_values(0, 4999, emit_signals=False)
        window.spin_frame_skip.setValue(5)

        window._update_size_estimate()
        # 5000 quadros com frame_skip=5 deve resultar em 1000 quadros no GIF, não 600
        assert "1000 quadros" in window.lbl_size_estimate.text()
    finally:
        window.close()


def test_gif_name_validation_and_sanitization(
    qapp: QApplication, sample_video_path: Path
) -> None:
    """Valida a sanitização do nome do GIF, extensão única e fallback quando vazio."""
    window = GifConverterApp()
    try:
        window.load_video_file(sample_video_path)

        # 1. Padrão inicial
        assert window.entry_gif_name.text() == sample_video_path.stem
        assert window.get_target_gif_path().name == f"{sample_video_path.stem}.gif"

        # 2. Nome customizado
        window.entry_gif_name.setText("meu_animado")
        assert window.get_target_gif_path().name == "meu_animado.gif"

        # 3. Nome customizado digitado com .gif (não deve duplicar para .gif.gif)
        window.entry_gif_name.setText("animacao_teste.gif")
        assert window.get_target_gif_path().name == "animacao_teste.gif"

        # 4. Caracteres inválidos de sistema de arquivos são removidos
        window.entry_gif_name.setText("meu:video/final*teste?.gif")
        assert window.get_target_gif_path().name == "meuvideofinalteste.gif"

        # 5. Campo vazio usa nome do vídeo original como fallback
        window.entry_gif_name.setText("   ")
        assert window.get_target_gif_path().name == f"{sample_video_path.stem}.gif"
    finally:
        window.close()


def test_overwrite_blocking_when_file_exists(
    qapp: QApplication, sample_video_path: Path, tmp_path: Path
) -> None:
    """Valida bloqueio e exibição de alerta caso o arquivo já exista e sobrescrever esteja desmarcado."""
    window = GifConverterApp()
    try:
        window.load_video_file(sample_video_path)
        existing_gif = tmp_path / "existente.gif"
        existing_gif.touch()

        window.output_dir = tmp_path
        window.entry_output_dir.setText(str(tmp_path))
        window.entry_gif_name.setText("existente")
        window.chk_overwrite.setChecked(False)

        # Dispara conversão com arquivo já existente e overwrite=False
        window.start_conversion()

        # Conversão deve ser bloqueada sem iniciar worker
        assert window.worker is None

        # Alerta in-place de erro exibido informando que o arquivo já existe
        assert not window.screen_options.lbl_result_status.isHidden()
        assert "já existe" in window.screen_options.lbl_result_status.text()
        assert not window.screen_options.btn_open_folder.isHidden()

        # Agora marca a opção de sobrescrever
        window.chk_overwrite.setChecked(True)
        window.start_conversion()

        # Com overwrite=True, o worker deve ser iniciado com sucesso
        assert window.worker is not None
        window.worker.wait(2000)
    finally:
        window.close()


def test_speed_control_ui_parsing_and_preview_sync(
    qapp: QApplication, sample_video_path: Path
) -> None:
    """Valida o seletor de velocidade, parsing flexível, cálculo de duração e timer do preview."""
    window = GifConverterApp()
    try:
        window.load_video_file(sample_video_path)

        # 1. Padrão inicial é 1.0x (vídeo sintético de 3.0s)
        assert window.screen_options.get_selected_speed() == 1.0
        assert "Duração: 00:03.0" in window.lbl_size_estimate.text()

        # 2. Seleção de preset 2.0x (3.0s / 2.0 = 1.5s)
        window.combo_speed.setCurrentText("2.0x")
        assert window.screen_options.get_selected_speed() == 2.0
        assert "Duração: 00:01.5 (2x)" in window.lbl_size_estimate.text()

        # 3. Digitação customizada com vírgula (ex: 1,5 -> 3.0s / 1.5 = 2.0s)
        window.combo_speed.setEditText("1,5")
        assert window.screen_options.get_selected_speed() == 1.5
        assert "Duração: 00:02.0 (1.5x)" in window.lbl_size_estimate.text()

        # 4. Digitação com sufixo 'x' (ex: 2.5x -> 3.0s / 2.5 = 1.2s)
        window.combo_speed.setEditText("2.5x")
        assert window.screen_options.get_selected_speed() == 2.5
        assert "Duração: 00:01.2 (2.5x)" in window.lbl_size_estimate.text()

        # 5. Entrada menor que 0.1 é limitada a 0.1
        window.combo_speed.setEditText("0.05")
        assert window.screen_options.get_selected_speed() == 0.1

        # 6. Entrada inválida faz fallback para 1.0
        window.combo_speed.setEditText("invalido")
        assert window.screen_options.get_selected_speed() == 1.0

        # 7. Sincronização com o preview player
        window.combo_speed.setCurrentText("2.0x")
        window.preview_controller.start_playback(0, 29, 0, speed=2.0)
        assert window.preview_controller.is_playing
        assert window.preview_controller._playback_speed == 2.0

        # Altera velocidade enquanto roda o preview
        window.combo_speed.setEditText("0.5")
        assert window.preview_controller._playback_speed == 0.5
        window.preview_controller.stop_playback()
    finally:
        window.close()
