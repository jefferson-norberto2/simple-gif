"""Janela principal da aplicação Simple GIF Maker com layout Widescreen em Tela Única."""

from pathlib import Path
import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QCloseEvent, QDesktopServices, QGuiApplication, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSpinBox,
)

from simplegif.core import SimpleGIF
from simplegif.ui.controllers import ConversionController, ConversionWorker, PreviewController
from simplegif.ui.helpers import format_seconds, load_stylesheet
from simplegif.ui.widgets import (
    InitialScreen,
    OptionsScreen,
    ProcessingScreen,
    RangeSlider,
    ResultScreen,
    VideoPreviewWidget,
)
from simplegif.utils.processor import FrameProcessor
from simplegif.utils.reader import VideoReader
from simplegif.utils.writer import GifWriter

__all__ = [
    "GifConverterApp",
    "RangeSlider",
    "ConversionWorker",
    "ConversionController",
    "PreviewController",
    "VideoPreviewWidget",
    "InitialScreen",
    "OptionsScreen",
    "ProcessingScreen",
    "ResultScreen",
    "main",
]


class _CompatStackedWidget:
    """Proxy de compatibilidade para testes que verificam o estado da pilha de telas."""

    def __init__(self, app: "GifConverterApp") -> None:
        self._app = app

    def currentIndex(self) -> int:
        return 1 if self._app.selected_file is not None else 0

    def setCurrentIndex(self, _index: int) -> None:
        pass


class GifConverterApp(QMainWindow):
    """Janela principal em Widescreen de tela única dividida em visualização e configurações."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Simple GIF Maker")
        self.resize(1000, 600)
        self.setMinimumSize(920, 520)
        self.setStyleSheet(load_stylesheet())

        self.gif_maker = SimpleGIF()
        self.selected_file: Path | None = None
        self.output_dir: Path | None = None
        self.result_gif_path: Path | None = None

        # Controllers
        self.preview_controller = PreviewController(self)
        self.conversion_controller = ConversionController(self.gif_maker, self)
        self.worker: ConversionWorker | None = None

        # Interface Principal Widescreen (Tela Única)
        self.screen_options = OptionsScreen(self)
        self.setCentralWidget(self.screen_options)

        # Referências legadas opcionais para manter compatibilidade com testes unitários modulares
        self._screen_initial = None
        self._screen_processing = None
        self._screen_result = None

        self._connect_signals()

    def _connect_signals(self) -> None:
        """Conecta os sinais da tela única e controllers."""
        self.screen_options.select_file_requested.connect(self.select_file)
        self.screen_options.browse_output_requested.connect(self.browse_output_dir)
        self.screen_options.start_conversion_requested.connect(self.start_conversion)
        self.screen_options.open_folder_requested.connect(self.open_destination_folder)
        self.screen_options.options_changed.connect(self._on_options_changed)

        # Preview de vídeo
        preview_w = self.screen_options.video_preview
        preview_w.preview_frame_requested.connect(self._on_preview_frame_requested)
        preview_w.toggle_playback_requested.connect(self._on_toggle_playback_requested)

        # Preview Controller
        self.preview_controller.frame_ready.connect(self._on_frame_rendered)
        self.preview_controller.playback_state_changed.connect(
            preview_w.set_playback_playing
        )

        # Conversion Controller
        self.conversion_controller.read_progress_updated.connect(self._on_read_progress)
        self.conversion_controller.save_progress_updated.connect(self._on_save_progress)
        self.conversion_controller.conversion_completed.connect(self.on_conversion_completed)
        self.conversion_controller.conversion_failed.connect(self.on_conversion_failed)

    # --- Propriedades de Retrocompatibilidade para Testes e Componentes Externos ---
    @property
    def stacked_widget(self) -> _CompatStackedWidget:
        return _CompatStackedWidget(self)

    @property
    def preview_reader(self) -> VideoReader | None:
        return self.preview_controller.reader

    @property
    def lbl_video_preview(self) -> QLabel:
        return self.screen_options.video_preview.lbl_video_preview

    @property
    def range_slider(self) -> RangeSlider:
        return self.screen_options.video_preview.range_slider

    @property
    def spin_start_time(self) -> QDoubleSpinBox:
        return self.screen_options.video_preview.spin_start_time

    @property
    def spin_end_time(self) -> QDoubleSpinBox:
        return self.screen_options.video_preview.spin_end_time

    @property
    def combo_scale(self) -> QComboBox:
        return self.screen_options.combo_scale

    @property
    def spin_frame_skip(self) -> QSpinBox:
        return self.screen_options.spin_frame_skip

    @property
    def chk_less_colors(self) -> QCheckBox:
        return self.screen_options.chk_less_colors

    @property
    def chk_overwrite(self) -> QCheckBox:
        return self.screen_options.chk_overwrite

    @property
    def lbl_size_estimate(self) -> QLabel:
        return self.screen_options.lbl_size_estimate

    @property
    def entry_input_path(self) -> QLineEdit:
        return self.screen_options.entry_input_path

    @property
    def entry_output_dir(self) -> QLineEdit:
        return self.screen_options.entry_output_dir

    @property
    def read_progress_bar(self) -> QProgressBar:
        return self.screen_options.progress_bar

    @property
    def save_progress_bar(self) -> QProgressBar:
        return self.screen_options.progress_bar

    @property
    def lbl_read_status(self) -> QLabel:
        return self.screen_options.lbl_progress_status

    @property
    def lbl_save_status(self) -> QLabel:
        return self.screen_options.lbl_progress_status

    @property
    def btn_play_preview(self) -> QPushButton:
        return self.screen_options.video_preview.btn_play_preview

    # --- Ações de Fluxo da UI ---
    def select_file(self) -> None:
        """Abre o diálogo nativo do SO para escolher o arquivo de vídeo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecione o Vídeo",
            "",
            "Arquivos de Vídeo (*.mp4 *.avi *.mov *.mkv);;Todos os Arquivos (*.*)",
        )
        if file_path:
            self.load_video_file(Path(file_path).resolve())

    def load_video_file(self, video_path: Path) -> None:
        """Carrega os metadados e o preview do vídeo selecionado e ativa o estado pronto."""
        self.selected_file = video_path.resolve()
        self.output_dir = self.selected_file.parent

        try:
            meta = self.preview_controller.load_video(self.selected_file)
            meta_str = (
                f"{meta.width}x{meta.height} • {meta.fps:.1f} FPS • "
                f"{format_seconds(self.preview_controller.video_duration)}"
            )
            self.screen_options.video_preview.setup_video(
                fps=meta.fps,
                total_frames=meta.total_frames,
                duration_seconds=self.preview_controller.video_duration,
            )
            self.screen_options.set_video_loaded_state(
                video_path=self.selected_file,
                output_dir=self.output_dir,
                meta_text=meta_str,
            )
            self.preview_controller.render_frame_at(0)
            self._update_size_estimate()
        except Exception as exc:
            self.screen_options.lbl_video_meta.setText("")
            self.screen_options.video_preview.set_preview_text(
                f"Não foi possível carregar preview: {exc}"
            )
            self.screen_options.set_size_estimate_text("📊 Tamanho estimado: --")

    def _on_preview_frame_requested(self, frame_index: int) -> None:
        self.preview_controller.stop_playback()
        self.preview_controller.render_frame_at(frame_index)

    def _on_frame_rendered(self, pixmap: QPixmap, frame_index: int) -> None:
        self.screen_options.video_preview.set_preview_pixmap(pixmap)
        self.screen_options.video_preview.range_slider.set_current_value(frame_index)

    def _on_toggle_playback_requested(self) -> None:
        start_f, end_f = self.screen_options.video_preview.get_selected_range_frames()
        curr_f = self.screen_options.video_preview.range_slider.current_value()
        self.preview_controller.toggle_playback(start_f, end_f, curr_f)

    def browse_output_dir(self) -> None:
        """Permite ao usuário escolher outra pasta de destino."""
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "Selecione a Pasta de Destino",
            str(self.output_dir or Path.home()),
        )
        if selected_dir:
            self.output_dir = Path(selected_dir).resolve()
            self.entry_output_dir.setText(str(self.output_dir))

    def get_estimated_gif_size_bytes(self) -> int:
        """Calcula a estimativa de tamanho do GIF em bytes com as opções selecionadas."""
        start_f, end_f = self.screen_options.video_preview.get_selected_range_frames()
        scale = self.screen_options.get_selected_scale()
        frame_skip = self.spin_frame_skip.value()
        less_colors = self.chk_less_colors.isChecked()

        return self.preview_controller.estimate_size_bytes(
            scale=scale,
            frame_skip=frame_skip,
            less_colors=less_colors,
            start_frame=start_f,
            end_frame=end_f,
        )

    def _on_options_changed(self) -> None:
        """Responde a qualquer alteração nos parâmetros restaurando a estimativa."""
        if not self.conversion_controller.is_running:
            self.screen_options.restore_estimate_display()
            self._update_size_estimate()

    def _update_size_estimate(self) -> None:
        """Recalcula e atualiza o badge com a estimativa de tamanho do GIF."""
        if self.preview_controller.reader is None:
            self.screen_options.set_size_estimate_text("📊 Estimado: --")
            return

        meta = self.preview_controller.reader.metadata
        scale = self.screen_options.get_selected_scale()
        frame_skip = self.spin_frame_skip.value()
        start_f, end_f = self.screen_options.video_preview.get_selected_range_frames()
        clip_frames = max(1, end_f - start_f + 1)
        output_frames = (clip_frames + frame_skip - 1) // frame_skip

        target_w, target_h = FrameProcessor.calculate_target_dimensions(
            meta.width, meta.height, scale
        )
        estimated_bytes = self.get_estimated_gif_size_bytes()
        formatted_size = GifWriter.format_file_size(estimated_bytes)
        self.screen_options.set_size_estimate_text(
            f"📊 Tamanho estimado: ~{formatted_size} ({target_w}x{target_h} px • {output_frames} quadros)"
        )

    def start_conversion(self) -> None:
        """Dispara a conversão em background via ConversionController com progresso in-place."""
        if not self.selected_file or not self.output_dir:
            return

        self.preview_controller.stop_playback()

        scale = self.screen_options.get_selected_scale()
        frame_skip = self.spin_frame_skip.value()
        less_colors = self.chk_less_colors.isChecked()
        overwrite = self.chk_overwrite.isChecked()
        start_time, end_time = self.screen_options.video_preview.get_selected_time_range()

        self.screen_options.set_converting_state()

        self.worker = self.conversion_controller.start_conversion(
            input_path=self.selected_file,
            output_path=self.output_dir,
            scale=scale,
            frame_skip=frame_skip,
            less_colors=less_colors,
            overwrite=overwrite,
            start_time=start_time,
            end_time=end_time if end_time > start_time else None,
        )

    def _on_read_progress(self, current: int, total: int) -> None:
        """Atualiza o status e a barra visual na etapa de leitura de quadros."""
        pct = int((current / total) * 100) if total > 0 else 0
        self.screen_options.lbl_progress_status.setText(f"Convertendo quadros... ({pct}%)")
        self.screen_options.progress_bar.setValue(int(pct * 0.5))

    def _on_save_progress(self, current: int, total: int) -> None:
        """Atualiza o status e a barra visual na etapa de gravação do arquivo GIF."""
        pct = int((current / total) * 100) if total > 0 else 0
        self.screen_options.lbl_progress_status.setText(f"Salvando arquivo GIF... ({pct}%)")
        self.screen_options.progress_bar.setValue(50 + int(pct * 0.5))

    def on_conversion_completed(self, gif_path: Path) -> None:
        """Chamado quando a conversão for concluída com sucesso."""
        self.result_gif_path = gif_path
        self.screen_options.set_conversion_completed_state(success=True)

    def on_conversion_failed(self, error_message: str, is_file_exists: bool) -> None:
        """Chamado quando a conversão falha."""
        self.result_gif_path = None
        self.screen_options.set_conversion_completed_state(
            success=False,
            msg=error_message,
            is_file_exists=is_file_exists,
        )

    def copy_path_to_clipboard(self) -> None:
        """Copia o caminho do GIF gerado para a área de transferência."""
        if self.result_gif_path:
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(str(self.result_gif_path))

    def open_destination_folder(self) -> None:
        """Abre a pasta de destino de forma segura e nativa usando QDesktopServices."""
        target_dir = self.output_dir
        if self.result_gif_path and self.result_gif_path.parent.is_dir():
            target_dir = self.result_gif_path.parent

        if target_dir and target_dir.is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(target_dir)))

    def closeEvent(self, event: QCloseEvent) -> None:
        """Garante liberação dos recursos de vídeo ao fechar a janela."""
        self.preview_controller.close()
        super().closeEvent(event)


def main() -> None:
    """Função de entrada para inicialização da interface gráfica PySide6."""
    app = QApplication(sys.argv)
    window = GifConverterApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
