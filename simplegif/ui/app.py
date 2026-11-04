"""Janela principal da aplicação Simple GIF Maker desenvolvida com PySide6."""

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
    QStackedWidget,
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


class GifConverterApp(QMainWindow):
    """Janela principal da aplicação orquestrando telas, controllers e ciclo de vida."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Simple GIF Maker")
        self.setFixedSize(620, 795)
        self.setStyleSheet(load_stylesheet())

        self.gif_maker = SimpleGIF()
        self.selected_file: Path | None = None
        self.output_dir: Path | None = None
        self.result_gif_path: Path | None = None

        # Controllers
        self.preview_controller = PreviewController(self)
        self.conversion_controller = ConversionController(self.gif_maker, self)
        self.worker: ConversionWorker | None = None

        # Pilha de Telas
        self.stacked_widget = QStackedWidget(self)
        self.setCentralWidget(self.stacked_widget)

        self.screen_initial = InitialScreen(self)
        self.screen_options = OptionsScreen(self)
        self.screen_processing = ProcessingScreen(self)
        self.screen_result = ResultScreen(self)

        self.stacked_widget.addWidget(self.screen_initial)     # Index 0
        self.stacked_widget.addWidget(self.screen_options)     # Index 1
        self.stacked_widget.addWidget(self.screen_processing)  # Index 2
        self.stacked_widget.addWidget(self.screen_result)      # Index 3

        self._connect_signals()
        self.show_screen_initial()

    def _connect_signals(self) -> None:
        """Conecta os sinais das telas e controllers."""
        # Tela 1: Seleção Inicial
        self.screen_initial.select_file_clicked.connect(self.select_file)

        # Tela 2: Opções e Preview
        self.screen_options.browse_output_requested.connect(self.browse_output_dir)
        self.screen_options.back_requested.connect(self.show_screen_initial)
        self.screen_options.start_conversion_requested.connect(self.start_conversion)
        self.screen_options.options_changed.connect(self._update_size_estimate)

        preview_w = self.screen_options.video_preview
        preview_w.preview_frame_requested.connect(self._on_preview_frame_requested)
        preview_w.toggle_playback_requested.connect(self._on_toggle_playback_requested)

        # Preview Controller
        self.preview_controller.frame_ready.connect(self._on_frame_rendered)
        self.preview_controller.playback_state_changed.connect(
            preview_w.set_playback_playing
        )

        # Conversion Controller
        self.conversion_controller.read_progress_updated.connect(
            self.screen_processing.update_read_progress
        )
        self.conversion_controller.save_progress_updated.connect(
            self.screen_processing.update_save_progress
        )
        self.conversion_controller.conversion_completed.connect(self.on_conversion_completed)
        self.conversion_controller.conversion_failed.connect(self.on_conversion_failed)

        # Tela 4: Resultado
        self.screen_result.copy_path_requested.connect(self.copy_path_to_clipboard)
        self.screen_result.open_folder_requested.connect(self.open_destination_folder)
        self.screen_result.new_file_requested.connect(self.show_screen_initial)

    # --- Propriedades de Retrocompatibilidade para Testes e Componentes Externos ---
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
        return self.screen_processing.read_progress_bar

    @property
    def save_progress_bar(self) -> QProgressBar:
        return self.screen_processing.save_progress_bar

    @property
    def lbl_read_status(self) -> QLabel:
        return self.screen_processing.lbl_read_status

    @property
    def lbl_save_status(self) -> QLabel:
        return self.screen_processing.lbl_save_status

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
        """Carrega os metadados e o preview do vídeo selecionado e exibe tela de opções."""
        self.selected_file = video_path.resolve()
        self.output_dir = self.selected_file.parent
        self.entry_input_path.setText(str(self.selected_file))
        self.entry_output_dir.setText(str(self.output_dir))

        try:
            meta = self.preview_controller.load_video(self.selected_file)
            self.screen_options.lbl_video_meta.setText(
                f"{meta.width}x{meta.height} • {meta.fps:.1f} FPS • {format_seconds(self.preview_controller.video_duration)}"
            )
            self.screen_options.video_preview.setup_video(
                fps=meta.fps,
                total_frames=meta.total_frames,
                duration_seconds=self.preview_controller.video_duration,
            )
            self.preview_controller.render_frame_at(0)
            self._update_size_estimate()
            self.stacked_widget.setCurrentIndex(1)
        except Exception as exc:
            self.screen_options.lbl_video_meta.setText("")
            self.screen_options.video_preview.set_preview_text(
                f"Não foi possível carregar preview: {exc}"
            )
            self.screen_options.set_size_estimate_text("📊 Tamanho estimado do GIF: --")

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

    def _update_size_estimate(self) -> None:
        """Recalcula e atualiza o badge com a estimativa de tamanho do GIF."""
        if self.preview_controller.reader is None:
            self.screen_options.set_size_estimate_text("📊 Tamanho estimado do GIF: --")
            return

        meta = self.preview_controller.reader.metadata
        scale = self.screen_options.get_selected_scale()
        frame_skip = self.spin_frame_skip.value()
        start_f, end_f = self.screen_options.video_preview.get_selected_range_frames()
        clip_frames = max(1, end_f - start_f + 1)
        output_frames = (min(clip_frames, 3000) + frame_skip - 1) // frame_skip

        target_w, target_h = FrameProcessor.calculate_target_dimensions(
            meta.width, meta.height, scale
        )
        estimated_bytes = self.get_estimated_gif_size_bytes()
        formatted_size = GifWriter.format_file_size(estimated_bytes)
        self.screen_options.set_size_estimate_text(
            f"📊 Tamanho estimado: ~{formatted_size}  ({output_frames} quadros no GIF • {target_w}x{target_h} px)"
        )

    def start_conversion(self) -> None:
        """Dispara a conversão em background via ConversionController."""
        if not self.selected_file or not self.output_dir:
            return

        self.preview_controller.close()

        scale = self.screen_options.get_selected_scale()
        frame_skip = self.spin_frame_skip.value()
        less_colors = self.chk_less_colors.isChecked()
        overwrite = self.chk_overwrite.isChecked()
        start_time, end_time = self.screen_options.video_preview.get_selected_time_range()

        self.screen_processing.reset_progress()
        self.stacked_widget.setCurrentIndex(2)

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

    def on_conversion_completed(self, gif_path: Path) -> None:
        """Chamado quando a conversão for concluída com sucesso."""
        self.result_gif_path = gif_path
        self.show_screen_result(success=True)

    def on_conversion_failed(self, error_message: str, is_file_exists: bool) -> None:
        """Chamado quando a conversão falha."""
        self.result_gif_path = None
        self.show_screen_result(
            success=False,
            error_msg=error_message,
            is_file_exists=is_file_exists,
        )

    def show_screen_result(
        self,
        success: bool,
        error_msg: str = "",
        is_file_exists: bool = False,
    ) -> None:
        """Exibe a tela de resultado."""
        self.screen_result.show_result(
            success=success,
            gif_path=self.result_gif_path,
            error_msg=error_msg,
            is_file_exists=is_file_exists,
        )
        self.stacked_widget.setCurrentIndex(3)

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

    def show_screen_initial(self) -> None:
        """Retorna para a tela inicial liberando recursos."""
        self.preview_controller.close()
        self.selected_file = None
        self.result_gif_path = None
        self.stacked_widget.setCurrentIndex(0)

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
