"""Interface gráfica para conversão de vídeos em GIF utilizando PySide6 (Qt)."""

from pathlib import Path
import sys

import numpy as np
from PySide6.QtCore import QRectF, Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import (
    QCloseEvent,
    QColor,
    QDesktopServices,
    QGuiApplication,
    QImage,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from simplegif import SimpleGIF
from simplegif.utils import ConversionOptions, FrameProcessor, GifWriter, VideoReader


def load_stylesheet(qss_name: str = "style.qss") -> str:
    """Carrega as folhas de estilo QSS a partir de arquivo externo (compatível com PyInstaller)."""
    if hasattr(sys, "_MEIPASS"):
        base_dir = Path(sys._MEIPASS)
        qss_file = base_dir / "simplegif/ui" / qss_name
        if not qss_file.is_file():
            qss_file = base_dir / qss_name
    else:
        qss_file = Path(__file__).resolve().parent / qss_name

    if qss_file.is_file():
        return qss_file.read_text(encoding="utf-8")
    return ""


def format_seconds(seconds: float) -> str:
    """Formata um valor em segundos para o padrão MM:SS.d."""
    total_sec = max(0.0, float(seconds))
    mins = int(total_sec // 60)
    secs = total_sec - (mins * 60)
    return f"{mins:02d}:{secs:04.1f}"


class RangeSlider(QWidget):
    """Controle deslizante duplo (dual-handle) para seleção de intervalo de quadros de vídeo."""

    start_value_changed = Signal(int)
    end_value_changed = Signal(int)
    range_changed = Signal(int, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._minimum: int = 0
        self._maximum: int = 100
        self._start_value: int = 0
        self._end_value: int = 100
        self._current_value: int = 0
        self._active_handle: str | None = None
        self._margin: int = 10
        self._handle_radius: int = 8
        self.setFixedHeight(30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def minimum(self) -> int:
        """Retorna o limite mínimo do slider."""
        return self._minimum

    def maximum(self) -> int:
        """Retorna o limite máximo do slider."""
        return self._maximum

    def start_value(self) -> int:
        """Retorna o índice inicial selecionado."""
        return self._start_value

    def end_value(self) -> int:
        """Retorna o índice final selecionado."""
        return self._end_value

    def current_value(self) -> int:
        """Retorna o índice atual do cursor de reprodução (playhead)."""
        return self._current_value

    def set_range_bounds(self, minimum: int, maximum: int) -> None:
        """Define os limites mínimo e máximo do controle deslizante."""
        self._minimum = max(0, int(minimum))
        self._maximum = max(self._minimum + 1, int(maximum))
        self._start_value = self._minimum
        self._end_value = self._maximum
        self._current_value = self._start_value
        self.update()

    def set_values(self, start_val: int, end_val: int, emit_signals: bool = False) -> None:
        """Atualiza os valores inicial e final garantindo consistência dos limites."""
        clamped_start = max(self._minimum, min(int(start_val), self._maximum - 1))
        clamped_end = max(clamped_start + 1, min(int(end_val), self._maximum))

        start_changed = clamped_start != self._start_value
        end_changed = clamped_end != self._end_value

        self._start_value = clamped_start
        self._end_value = clamped_end
        if self._current_value < self._start_value or self._current_value > self._end_value:
            self._current_value = self._start_value

        self.update()

        if emit_signals:
            if start_changed:
                self.start_value_changed.emit(self._start_value)
            if end_changed:
                self.end_value_changed.emit(self._end_value)
            if start_changed or end_changed:
                self.range_changed.emit(self._start_value, self._end_value)

    def set_current_value(self, current_val: int) -> None:
        """Define a posição do indicador de reprodução atual."""
        self._current_value = max(self._start_value, min(int(current_val), self._end_value))
        self.update()

    def _value_to_x(self, value: int) -> float:
        span = max(1, self._maximum - self._minimum)
        usable_w = max(1, self.width() - 2 * self._margin)
        ratio = (value - self._minimum) / span
        return self._margin + ratio * usable_w

    def _x_to_value(self, x_pos: float) -> int:
        usable_w = max(1, self.width() - 2 * self._margin)
        clamped_x = max(0.0, min(float(x_pos - self._margin), float(usable_w)))
        ratio = clamped_x / usable_w
        span = max(1, self._maximum - self._minimum)
        return int(round(self._minimum + ratio * span))

    def paintEvent(self, _event: object) -> None:
        """Renderiza a trilha, a faixa selecionada, o playhead e os dois cursores."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        mid_y = self.height() / 2.0
        track_h = 6.0
        usable_w = max(1.0, float(self.width() - 2 * self._margin))

        # Trilha de fundo
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#3f3f46"))
        painter.drawRoundedRect(
            QRectF(self._margin, mid_y - track_h / 2.0, usable_w, track_h),
            3.0,
            3.0,
        )

        start_x = self._value_to_x(self._start_value)
        end_x = self._value_to_x(self._end_value)
        curr_x = self._value_to_x(self._current_value)

        # Faixa ativa selecionada
        painter.setBrush(QColor("#10b981"))
        painter.drawRoundedRect(
            QRectF(start_x, mid_y - track_h / 2.0, max(2.0, end_x - start_x), track_h),
            3.0,
            3.0,
        )

        # Marcador do quadro atual (playhead)
        painter.setPen(QPen(QColor("#38bdf8"), 2.0))
        painter.drawLine(int(curr_x), int(mid_y - 9), int(curr_x), int(mid_y + 9))

        # Cursores de Início e Fim
        for handle_name, hx in (("start", start_x), ("end", end_x)):
            is_active = self._active_handle == handle_name
            fill_color = QColor("#10b981") if is_active else QColor("#f4f4f5")
            border_color = QColor("#ffffff") if is_active else QColor("#059669")
            painter.setPen(QPen(border_color, 2.0))
            painter.setBrush(fill_color)
            r = float(self._handle_radius)
            painter.drawEllipse(QRectF(hx - r, mid_y - r, r * 2.0, r * 2.0))

        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Seleciona o cursor mais próximo do clique e atualiza o valor."""
        if event.button() != Qt.MouseButton.LeftButton:
            return
        click_x = event.position().x()
        start_x = self._value_to_x(self._start_value)
        end_x = self._value_to_x(self._end_value)

        if abs(click_x - start_x) <= abs(click_x - end_x):
            self._active_handle = "start"
        else:
            self._active_handle = "end"

        self._update_from_mouse(click_x)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Arrasta o cursor ativo mantendo os limites do intervalo."""
        if self._active_handle is not None:
            self._update_from_mouse(event.position().x())

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Finaliza o arraste do cursor."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._active_handle = None
            self.update()

    def _update_from_mouse(self, x_pos: float) -> None:
        new_val = self._x_to_value(x_pos)
        if self._active_handle == "start":
            clamped = max(self._minimum, min(new_val, self._end_value - 1))
            if clamped != self._start_value:
                self._start_value = clamped
                self._current_value = clamped
                self.update()
                self.start_value_changed.emit(self._start_value)
                self.range_changed.emit(self._start_value, self._end_value)
        elif self._active_handle == "end":
            clamped = max(self._start_value + 1, min(new_val, self._maximum))
            if clamped != self._end_value:
                self._end_value = clamped
                self._current_value = clamped
                self.update()
                self.end_value_changed.emit(self._end_value)
                self.range_changed.emit(self._start_value, self._end_value)


class ConversionWorker(QThread):
    """Worker que executa a conversão do vídeo para GIF em segundo plano via QThread."""

    read_progress_updated = Signal(int, int)  # (atual, total)
    save_progress_updated = Signal(int, int)  # (atual, total)
    conversion_completed = Signal(Path)
    conversion_failed = Signal(str, bool)     # (mensagem_erro, eh_file_exists)

    def __init__(
        self,
        gif_maker: SimpleGIF,
        input_path: Path,
        output_path: Path,
        scale: float,
        frame_skip: int,
        less_colors: bool,
        overwrite: bool,
        start_time: float = 0.0,
        end_time: float | None = None,
    ) -> None:
        super().__init__()
        self.gif_maker = gif_maker
        self.input_path = input_path
        self.output_path = output_path
        self.scale = scale
        self.frame_skip = frame_skip
        self.less_colors = less_colors
        self.overwrite = overwrite
        self.start_time = start_time
        self.end_time = end_time

    def run(self) -> None:
        """Executa a conversão com callbacks reportados por Signals."""
        try:
            result_path = self.gif_maker.convert_file(
                path=self.input_path,
                output_path=self.output_path,
                scale=self.scale,
                less_colors=self.less_colors,
                max_frames=3000,
                frame_skip=self.frame_skip,
                overwrite=self.overwrite,
                start_time=self.start_time,
                end_time=self.end_time,
                read_progress_callback=self._on_read_progress,
                save_progress_callback=self._on_save_progress,
            )
            self.conversion_completed.emit(result_path)
        except FileExistsError as e:
            self.conversion_failed.emit(str(e), True)
        except Exception as e:
            self.conversion_failed.emit(str(e), False)

    def _on_read_progress(self, current: int, total: int) -> None:
        self.read_progress_updated.emit(current, total)

    def _on_save_progress(self, current: int, total: int) -> None:
        self.save_progress_updated.emit(current, total)


class GifConverterApp(QMainWindow):
    """Janela principal da aplicação Simple GIF Maker desenvolvida com PySide6."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Simple GIF Maker")
        self.setFixedSize(620, 795)
        self.setStyleSheet(load_stylesheet())

        self.gif_maker = SimpleGIF()
        self.selected_file: Path | None = None
        self.output_dir: Path | None = None
        self.result_gif_path: Path | None = None
        self.worker: ConversionWorker | None = None

        self.preview_reader: VideoReader | None = None
        self.video_fps: float = 30.0
        self.video_total_frames: int = 100
        self.video_duration: float = 0.0
        self._sample_frame_bgr: np.ndarray | None = None
        self._frame_byte_cache: dict[tuple[float, bool], int] = {}

        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self._advance_preview_frame)

        self.stacked_widget = QStackedWidget(self)
        self.setCentralWidget(self.stacked_widget)

        self.screen_initial = self._create_screen_initial()
        self.screen_options = self._create_screen_options()
        self.screen_processing = self._create_screen_processing()
        self.screen_result = self._create_screen_result()

        self.stacked_widget.addWidget(self.screen_initial)     # Index 0
        self.stacked_widget.addWidget(self.screen_options)     # Index 1
        self.stacked_widget.addWidget(self.screen_processing)  # Index 2
        self.stacked_widget.addWidget(self.screen_result)      # Index 3

        self.show_screen_initial()

    # --- TELA 1: Seleção Inicial ---
    def _create_screen_initial(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(35, 40, 35, 40)
        layout.setSpacing(15)

        card = QFrame()
        card.setObjectName("cardFrame")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 40, 30, 40)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(18)

        lbl_icon = QLabel("🎬")
        lbl_icon.setStyleSheet("font-size: 54px;")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_title = QLabel("Simple GIF Maker")
        lbl_title.setObjectName("titleLabel")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_sub = QLabel("Conversor de vídeo para GIF 100% offline, rápido e seguro.")
        lbl_sub.setObjectName("subtitleLabel")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_select = QPushButton(" Escolher Arquivo de Vídeo")
        btn_select.setObjectName("primaryButton")
        btn_select.setFixedHeight(48)
        btn_select.setFixedWidth(240)
        btn_select.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_select.clicked.connect(self.select_file)

        lbl_formats = QLabel("Formatos suportados: MP4, AVI, MOV, MKV")
        lbl_formats.setObjectName("subtitleLabel")
        lbl_formats.setStyleSheet("font-size: 11px; color: #71717a;")
        lbl_formats.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(lbl_icon)
        card_layout.addWidget(lbl_title)
        card_layout.addWidget(lbl_sub)
        card_layout.addSpacing(10)
        card_layout.addWidget(btn_select, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(lbl_formats)

        layout.addWidget(card)
        return widget

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
        """Carrega os metadados e o preview do vídeo selecionado e avança para a tela de opções."""
        self._close_preview_reader()
        self.selected_file = video_path.resolve()
        self.output_dir = self.selected_file.parent
        self.update_options_screen()
        self.stacked_widget.setCurrentIndex(1)

    # --- TELA 2: Configuração, Preview de Vídeo e Seleção de Range ---
    def _create_screen_options(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(26, 16, 26, 16)
        layout.setSpacing(12)

        card = QFrame()
        card.setObjectName("cardFrame")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 16, 22, 16)
        card_layout.setSpacing(10)

        header_row = QHBoxLayout()
        lbl_title = QLabel("Configurar Conversão e Trecho")
        lbl_title.setObjectName("sectionTitle")
        self.lbl_video_meta = QLabel("")
        self.lbl_video_meta.setObjectName("subtitleLabel")
        self.lbl_video_meta.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_row.addWidget(lbl_title)
        header_row.addWidget(self.lbl_video_meta)
        card_layout.addLayout(header_row)

        # Área de Preview do Vídeo
        self.lbl_video_preview = QLabel("Pré-visualização do vídeo")
        self.lbl_video_preview.setObjectName("videoPreviewLabel")
        self.lbl_video_preview.setFixedHeight(190)
        self.lbl_video_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.lbl_video_preview)

        # Controles de Reprodução e Range Slider
        slider_row = QHBoxLayout()
        slider_row.setSpacing(10)
        self.btn_play_preview = QPushButton("▶ Preview")
        self.btn_play_preview.setFixedWidth(95)
        self.btn_play_preview.setFixedHeight(30)
        self.btn_play_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_play_preview.clicked.connect(self.toggle_preview_playback)

        self.range_slider = RangeSlider()
        self.range_slider.start_value_changed.connect(self._on_slider_start_changed)
        self.range_slider.end_value_changed.connect(self._on_slider_end_changed)

        slider_row.addWidget(self.btn_play_preview)
        slider_row.addWidget(self.range_slider, stretch=1)
        card_layout.addLayout(slider_row)

        # Controles numéricos de Início / Fim (em segundos) e resumo do trecho
        time_row = QHBoxLayout()
        time_row.setSpacing(10)

        time_row.addWidget(QLabel("De:"))
        self.spin_start_time = QDoubleSpinBox()
        self.spin_start_time.setDecimals(2)
        self.spin_start_time.setSingleStep(0.1)
        self.spin_start_time.setSuffix(" s")
        self.spin_start_time.valueChanged.connect(self._on_spin_start_changed)
        time_row.addWidget(self.spin_start_time)

        time_row.addWidget(QLabel("Até:"))
        self.spin_end_time = QDoubleSpinBox()
        self.spin_end_time.setDecimals(2)
        self.spin_end_time.setSingleStep(0.1)
        self.spin_end_time.setSuffix(" s")
        self.spin_end_time.valueChanged.connect(self._on_spin_end_changed)
        time_row.addWidget(self.spin_end_time)

        self.lbl_range_summary = QLabel("Trecho: 00:00.0 → 00:00.0")
        self.lbl_range_summary.setObjectName("rangeSummaryLabel")
        self.lbl_range_summary.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        time_row.addWidget(self.lbl_range_summary, stretch=1)

        card_layout.addLayout(time_row)

        # Vídeo de entrada
        card_layout.addWidget(QLabel("Vídeo Selecionado:"))
        self.entry_input_path = QLineEdit()
        self.entry_input_path.setReadOnly(True)
        card_layout.addWidget(self.entry_input_path)

        # Pasta de saída
        card_layout.addWidget(QLabel("Salvar na Pasta:"))
        out_row = QHBoxLayout()
        self.entry_output_dir = QLineEdit()
        self.entry_output_dir.setReadOnly(True)
        btn_browse_out = QPushButton("Alterar...")
        btn_browse_out.clicked.connect(self.browse_output_dir)
        out_row.addWidget(self.entry_output_dir)
        out_row.addWidget(btn_browse_out)
        card_layout.addLayout(out_row)

        # Grade de Opções
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(QLabel("Escala de Tamanho:"), 0, 0)
        self.combo_scale = QComboBox()
        self.combo_scale.addItems(["100% (Original)", "75%", "60% (Recomendado)", "50%", "35%", "25%"])
        self.combo_scale.setCurrentIndex(2)  # 60%
        self.combo_scale.currentIndexChanged.connect(self._update_size_estimate)
        grid.addWidget(self.combo_scale, 0, 1)

        grid.addWidget(QLabel("Intervalo de Quadros (Skip):"), 1, 0)
        self.spin_frame_skip = QSpinBox()
        self.spin_frame_skip.setRange(1, 30)
        self.spin_frame_skip.setValue(5)
        self.spin_frame_skip.setSuffix(" quadros")
        self.spin_frame_skip.valueChanged.connect(self._update_size_estimate)
        grid.addWidget(self.spin_frame_skip, 1, 1)

        card_layout.addLayout(grid)

        # Checkboxes
        self.chk_less_colors = QCheckBox("Reduzir paleta de cores (Gera arquivos menores)")
        self.chk_less_colors.setChecked(True)
        self.chk_less_colors.toggled.connect(self._update_size_estimate)
        card_layout.addWidget(self.chk_less_colors)

        self.chk_overwrite = QCheckBox("Sobrescrever arquivo se já existir")
        self.chk_overwrite.setChecked(False)
        card_layout.addWidget(self.chk_overwrite)

        # Estimativa de Tamanho do GIF
        self.lbl_size_estimate = QLabel("📊 Tamanho estimado do GIF: --")
        self.lbl_size_estimate.setObjectName("sizeEstimateLabel")
        self.lbl_size_estimate.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.lbl_size_estimate)

        layout.addWidget(card)

        # Botões de Ação
        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("Voltar")
        btn_cancel.setObjectName("secondaryButton")
        btn_cancel.setFixedHeight(40)
        btn_cancel.clicked.connect(self.show_screen_initial)

        btn_start = QPushButton("🚀 Iniciar Conversão")
        btn_start.setObjectName("primaryButton")
        btn_start.setFixedHeight(40)
        btn_start.clicked.connect(self.start_conversion)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_start)
        layout.addLayout(btn_box)

        return widget

    def update_options_screen(self) -> None:
        """Atualiza os campos e inicializa o preview e os limites de tempo do vídeo."""
        if self.selected_file:
            self.entry_input_path.setText(str(self.selected_file))
        if self.output_dir:
            self.entry_output_dir.setText(str(self.output_dir))

        self._stop_preview_playback()
        self._close_preview_reader()

        if not self.selected_file or not self.selected_file.is_file():
            return

        try:
            self.preview_reader = VideoReader(self.selected_file)
            self.preview_reader.open()
            meta = self.preview_reader.metadata

            self.video_fps = meta.fps
            self.video_total_frames = max(1, meta.total_frames)
            self.video_duration = meta.duration_seconds if meta.duration_seconds > 0 else (self.video_total_frames / self.video_fps)

            self.lbl_video_meta.setText(
                f"{meta.width}x{meta.height} • {meta.fps:.1f} FPS • {format_seconds(self.video_duration)}"
            )

            max_frame_idx = max(1, self.video_total_frames - 1)
            self.range_slider.set_range_bounds(0, max_frame_idx)

            step_sec = max(0.01, round(1.0 / self.video_fps, 2))
            self.spin_start_time.blockSignals(True)
            self.spin_end_time.blockSignals(True)

            self.spin_start_time.setRange(0.0, max(0.0, self.video_duration - step_sec))
            self.spin_start_time.setSingleStep(step_sec)
            self.spin_start_time.setValue(0.0)

            self.spin_end_time.setRange(step_sec, max(step_sec, self.video_duration))
            self.spin_end_time.setSingleStep(step_sec)
            self.spin_end_time.setValue(self.video_duration)

            self.spin_start_time.blockSignals(False)
            self.spin_end_time.blockSignals(False)

            self._frame_byte_cache.clear()
            self._sample_frame_bgr = self.preview_reader.read_frame_at(0)

            self._show_preview_frame(0)
            self._update_range_summary()
        except Exception as exc:
            self.lbl_video_meta.setText("")
            self.lbl_video_preview.setPixmap(QPixmap())
            self.lbl_video_preview.setText(f"Não foi possível carregar preview: {exc}")
            self.lbl_size_estimate.setText("📊 Tamanho estimado do GIF: --")

    def _show_preview_frame(self, frame_index: int) -> None:
        """Lê um único quadro sob demanda e o renderiza no QLabel de preview."""
        if self.preview_reader is None:
            return

        frame_bgr = self.preview_reader.read_frame_at(frame_index)
        if frame_bgr is None:
            return

        self.range_slider.set_current_value(frame_index)

        preview_w = max(160, self.lbl_video_preview.width() - 8)
        preview_h = max(120, self.lbl_video_preview.height() - 8)
        orig_h, orig_w = frame_bgr.shape[:2]
        scale = min(preview_w / max(1, orig_w), preview_h / max(1, orig_h))
        target_w, target_h = FrameProcessor.calculate_target_dimensions(orig_w, orig_h, scale)

        resized_bgr = FrameProcessor.resize(frame_bgr, target_w, target_h)
        rgb_frame = FrameProcessor.bgr_to_rgb(resized_bgr)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w

        qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
        self.lbl_video_preview.setPixmap(QPixmap.fromImage(qimg))

    def _on_slider_start_changed(self, start_frame: int) -> None:
        """Slot acionado quando o usuário move o cursor inicial do RangeSlider."""
        self._stop_preview_playback()
        start_sec = round(start_frame / self.video_fps, 2)
        self.spin_start_time.blockSignals(True)
        self.spin_start_time.setValue(start_sec)
        self.spin_start_time.blockSignals(False)
        self._update_range_summary()
        self._show_preview_frame(start_frame)

    def _on_slider_end_changed(self, end_frame: int) -> None:
        """Slot acionado quando o usuário move o cursor final do RangeSlider."""
        self._stop_preview_playback()
        end_sec = min(self.video_duration, round((end_frame + 1) / self.video_fps, 2))
        self.spin_end_time.blockSignals(True)
        self.spin_end_time.setValue(end_sec)
        self.spin_end_time.blockSignals(False)
        self._update_range_summary()
        self._show_preview_frame(end_frame)

    def _on_spin_start_changed(self, start_sec: float) -> None:
        """Slot acionado quando o usuário altera o tempo inicial no QDoubleSpinBox."""
        self._stop_preview_playback()
        min_gap = max(0.01, 1.0 / self.video_fps)
        if start_sec >= self.spin_end_time.value():
            clamped_start = max(0.0, self.spin_end_time.value() - min_gap)
            self.spin_start_time.blockSignals(True)
            self.spin_start_time.setValue(clamped_start)
            self.spin_start_time.blockSignals(False)
            start_sec = clamped_start

        start_frame = max(0, int(round(start_sec * self.video_fps)))
        end_frame = max(start_frame + 1, self.range_slider.end_value())
        self.range_slider.set_values(start_frame, end_frame, emit_signals=False)
        self._update_range_summary()
        self._show_preview_frame(start_frame)

    def _on_spin_end_changed(self, end_sec: float) -> None:
        """Slot acionado quando o usuário altera o tempo final no QDoubleSpinBox."""
        self._stop_preview_playback()
        min_gap = max(0.01, 1.0 / self.video_fps)
        if end_sec <= self.spin_start_time.value():
            clamped_end = min(self.video_duration, self.spin_start_time.value() + min_gap)
            self.spin_end_time.blockSignals(True)
            self.spin_end_time.setValue(clamped_end)
            self.spin_end_time.blockSignals(False)
            end_sec = clamped_end

        start_frame = self.range_slider.start_value()
        end_frame = min(
            self.range_slider.maximum(),
            max(start_frame + 1, int(round(end_sec * self.video_fps)) - 1),
        )
        self.range_slider.set_values(start_frame, end_frame, emit_signals=False)
        self._update_range_summary()
        self._show_preview_frame(end_frame)

    def _update_range_summary(self) -> None:
        """Atualiza o rótulo com o resumo do intervalo de tempo, contagem de quadros e tamanho estimado."""
        start_sec = self.spin_start_time.value()
        end_sec = self.spin_end_time.value()
        clip_duration = max(0.0, end_sec - start_sec)
        clip_frames = max(1, self.range_slider.end_value() - self.range_slider.start_value() + 1)
        self.lbl_range_summary.setText(
            f"{format_seconds(start_sec)} → {format_seconds(end_sec)} ({clip_duration:.1f}s • {clip_frames} frames)"
        )
        self._update_size_estimate()

    def _get_selected_scale(self) -> float:
        """Retorna o fator numérico de escala correspondente à opção selecionada no combo."""
        scale_map = {
            "100% (Original)": 1.0,
            "75%": 0.75,
            "60% (Recomendado)": 0.6,
            "50%": 0.5,
            "35%": 0.35,
            "25%": 0.25,
        }
        return scale_map.get(self.combo_scale.currentText(), 0.6)

    def get_estimated_gif_size_bytes(self) -> int:
        """Calcula e retorna a estimativa de tamanho do GIF em bytes com base nas configurações atuais."""
        if self.preview_reader is None:
            return 0

        meta = self.preview_reader.metadata
        chosen_scale = self._get_selected_scale()
        frame_skip = self.spin_frame_skip.value()
        less_colors = self.chk_less_colors.isChecked()

        cache_key = (chosen_scale, less_colors)
        if cache_key not in self._frame_byte_cache:
            single_opts = ConversionOptions(
                scale=chosen_scale,
                frame_skip=1,
                less_colors=less_colors,
                max_frames=1,
            )
            single_est = GifWriter.estimate_gif_size(
                meta, single_opts, sample_frame=self._sample_frame_bgr
            )
            self._frame_byte_cache[cache_key] = max(96, single_est - 800)

        per_frame_bytes = self._frame_byte_cache[cache_key]
        clip_frames = max(1, self.range_slider.end_value() - self.range_slider.start_value() + 1)
        inspected_frames = min(clip_frames, 3000)
        output_frames = (inspected_frames + frame_skip - 1) // frame_skip
        return 800 + (output_frames * per_frame_bytes)

    def _update_size_estimate(self) -> None:
        """Atualiza o componente visual de estimativa de tamanho do arquivo GIF."""
        if self.preview_reader is None:
            self.lbl_size_estimate.setText("📊 Tamanho estimado do GIF: --")
            return

        meta = self.preview_reader.metadata
        chosen_scale = self._get_selected_scale()
        frame_skip = self.spin_frame_skip.value()
        clip_frames = max(1, self.range_slider.end_value() - self.range_slider.start_value() + 1)
        output_frames = (min(clip_frames, 3000) + frame_skip - 1) // frame_skip
        target_w, target_h = FrameProcessor.calculate_target_dimensions(
            meta.width, meta.height, chosen_scale
        )

        estimated_bytes = self.get_estimated_gif_size_bytes()
        formatted_size = GifWriter.format_file_size(estimated_bytes)
        self.lbl_size_estimate.setText(
            f"📊 Tamanho estimado: ~{formatted_size}  ({output_frames} quadros no GIF • {target_w}x{target_h} px)"
        )

    def toggle_preview_playback(self) -> None:
        """Inicia ou pausa a reprodução em loop do intervalo selecionado."""
        if self.preview_timer.isActive():
            self._stop_preview_playback()
        else:
            if self.preview_reader is None:
                return
            curr = self.range_slider.current_value()
            if curr < self.range_slider.start_value() or curr >= self.range_slider.end_value():
                self.range_slider.set_current_value(self.range_slider.start_value())
            interval_ms = max(30, int(round(1000.0 / min(30.0, self.video_fps))))
            self.btn_play_preview.setText("⏸ Pausar")
            self.preview_timer.start(interval_ms)

    def _stop_preview_playback(self) -> None:
        """Interrompe o timer de reprodução do preview."""
        if self.preview_timer.isActive():
            self.preview_timer.stop()
        if hasattr(self, "btn_play_preview"):
            self.btn_play_preview.setText("▶ Preview")

    def _advance_preview_frame(self) -> None:
        """Avança um quadro na reprodução do preview fazendo loop dentro do range selecionado."""
        if self.preview_reader is None:
            self._stop_preview_playback()
            return

        start_f = self.range_slider.start_value()
        end_f = self.range_slider.end_value()
        step = max(1, int(round(self.video_fps / 15.0))) if self.video_fps > 30.0 else 1
        next_f = self.range_slider.current_value() + step
        if next_f > end_f:
            next_f = start_f
        self._show_preview_frame(next_f)

    def _close_preview_reader(self) -> None:
        """Fecha com segurança o VideoReader usado pelo preview."""
        self._stop_preview_playback()
        self._sample_frame_bgr = None
        self._frame_byte_cache.clear()
        if self.preview_reader is not None:
            self.preview_reader.close()
            self.preview_reader = None

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

    # --- TELA 3: Processamento com Duas Barras de Progresso ---
    def _create_screen_processing(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(35, 30, 35, 30)

        card = QFrame()
        card.setObjectName("cardFrame")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 25, 30, 25)
        card_layout.setSpacing(14)

        lbl_title = QLabel("Processando seu GIF...")
        lbl_title.setObjectName("titleLabel")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(lbl_title)

        # --- ETAPA 1: Leitura e Processamento ---
        card_layout.addSpacing(6)
        lbl_step1 = QLabel("Passo 1/2: Leitura e Preparação dos Quadros")
        lbl_step1.setObjectName("sectionTitle")
        card_layout.addWidget(lbl_step1)

        self.lbl_read_status = QLabel("Aguardando início...")
        self.lbl_read_status.setObjectName("subtitleLabel")
        card_layout.addWidget(self.lbl_read_status)

        self.read_progress_bar = QProgressBar()
        self.read_progress_bar.setRange(0, 100)
        self.read_progress_bar.setValue(0)
        card_layout.addWidget(self.read_progress_bar)

        # --- ETAPA 2: Gravação e Codificação do GIF ---
        card_layout.addSpacing(10)
        lbl_step2 = QLabel("Passo 2/2: Codificação e Gravação do GIF")
        lbl_step2.setObjectName("sectionTitle")
        card_layout.addWidget(lbl_step2)

        self.lbl_save_status = QLabel("Aguardando leitura dos frames...")
        self.lbl_save_status.setObjectName("subtitleLabel")
        card_layout.addWidget(self.lbl_save_status)

        self.save_progress_bar = QProgressBar()
        self.save_progress_bar.setRange(0, 100)
        self.save_progress_bar.setValue(0)
        card_layout.addWidget(self.save_progress_bar)

        layout.addWidget(card)
        return widget

    def start_conversion(self) -> None:
        """Coleta as opções (incluindo o intervalo selecionado) e dispara o QThread de processamento."""
        if not self.selected_file or not self.output_dir:
            return

        self._close_preview_reader()

        chosen_scale = self._get_selected_scale()
        frame_skip = self.spin_frame_skip.value()
        less_colors = self.chk_less_colors.isChecked()
        overwrite = self.chk_overwrite.isChecked()
        start_time = self.spin_start_time.value()
        end_time = self.spin_end_time.value()

        self.read_progress_bar.setValue(0)
        self.save_progress_bar.setValue(0)
        self.lbl_read_status.setText("Iniciando leitura do trecho selecionado...")
        self.lbl_read_status.setStyleSheet("color: #a1a1aa;")
        self.lbl_save_status.setText("Aguardando preparação dos frames...")
        self.lbl_save_status.setStyleSheet("color: #71717a;")
        self.stacked_widget.setCurrentIndex(2)

        self.worker = ConversionWorker(
            gif_maker=self.gif_maker,
            input_path=self.selected_file,
            output_path=self.output_dir,
            scale=chosen_scale,
            frame_skip=frame_skip,
            less_colors=less_colors,
            overwrite=overwrite,
            start_time=start_time,
            end_time=end_time if end_time > start_time else None,
        )
        self.worker.read_progress_updated.connect(self.on_read_progress_update)
        self.worker.save_progress_updated.connect(self.on_save_progress_update)
        self.worker.conversion_completed.connect(self.on_conversion_completed)
        self.worker.conversion_failed.connect(self.on_conversion_failed)
        self.worker.start()

    def on_read_progress_update(self, current: int, total: int) -> None:
        """Slot para atualização em tempo real da barra de leitura dos frames."""
        if total > 0:
            percentage = int((current / total) * 100)
            self.read_progress_bar.setValue(percentage)
            if percentage >= 100:
                self.lbl_read_status.setText(f"✓ Todos os {total} frames do trecho foram lidos e preparados!")
                self.lbl_read_status.setStyleSheet("color: #10b981; font-weight: 500;")
                self.lbl_save_status.setText("Iniciando codificação e gravação no disco...")
                self.lbl_save_status.setStyleSheet("color: #38bdf8;")
            else:
                self.lbl_read_status.setText(f"Lendo e redimensionando: {current}/{total} frames ({percentage}%)")
                self.lbl_read_status.setStyleSheet("color: #a1a1aa;")

    def on_save_progress_update(self, current: int, total: int) -> None:
        """Slot para atualização em tempo real da barra de gravação do GIF."""
        if total > 0:
            percentage = int((current / total) * 100)
            self.save_progress_bar.setValue(percentage)
            if percentage >= 100:
                self.lbl_save_status.setText("✓ GIF codificado e gravado no disco com sucesso!")
                self.lbl_save_status.setStyleSheet("color: #10b981; font-weight: 500;")
            else:
                self.lbl_save_status.setText(f"Codificando e gravando frame {current}/{total} ({percentage}%)...")
                self.lbl_save_status.setStyleSheet("color: #38bdf8;")

    def on_conversion_completed(self, gif_path: Path) -> None:
        """Slot acionado quando a conversão for concluída com sucesso."""
        self.result_gif_path = gif_path
        self.show_screen_result(success=True)

    def on_conversion_failed(self, error_message: str, is_file_exists: bool) -> None:
        """Slot acionado em caso de erro na conversão."""
        self.result_gif_path = None
        self.show_screen_result(success=False, error_msg=error_message, is_file_exists=is_file_exists)

    # --- TELA 4: Resultado ---
    def _create_screen_result(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(35, 30, 35, 30)

        card = QFrame()
        card.setObjectName("cardFrame")
        self.card_result_layout = QVBoxLayout(card)
        self.card_result_layout.setContentsMargins(30, 30, 30, 30)
        self.card_result_layout.setSpacing(16)
        self.card_result_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_res_icon = QLabel("✅")
        self.lbl_res_icon.setStyleSheet("font-size: 46px;")
        self.lbl_res_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_res_title = QLabel("Concluído!")
        self.lbl_res_title.setObjectName("titleLabel")
        self.lbl_res_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_res_desc = QLabel("Arquivo salvo em:")
        self.lbl_res_desc.setObjectName("subtitleLabel")
        self.lbl_res_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Container do caminho de saída
        self.path_box = QHBoxLayout()
        self.entry_res_path = QLineEdit()
        self.entry_res_path.setReadOnly(True)
        btn_copy = QPushButton("Copiar")
        btn_copy.clicked.connect(self.copy_path_to_clipboard)
        self.path_box.addWidget(self.entry_res_path)
        self.path_box.addWidget(btn_copy)

        self.btn_open_folder = QPushButton("📁 Abrir Pasta de Destino")
        self.btn_open_folder.clicked.connect(self.open_destination_folder)
        self.btn_open_folder.setFixedHeight(38)

        self.btn_new_file = QPushButton("Converter Novo Vídeo")
        self.btn_new_file.setObjectName("primaryButton")
        self.btn_new_file.setFixedHeight(42)
        self.btn_new_file.setFixedWidth(200)
        self.btn_new_file.clicked.connect(self.show_screen_initial)

        self.card_result_layout.addWidget(self.lbl_res_icon)
        self.card_result_layout.addWidget(self.lbl_res_title)
        self.card_result_layout.addWidget(self.lbl_res_desc)
        self.card_result_layout.addLayout(self.path_box)
        self.card_result_layout.addWidget(self.btn_open_folder, alignment=Qt.AlignmentFlag.AlignCenter)
        self.card_result_layout.addSpacing(10)
        self.card_result_layout.addWidget(self.btn_new_file, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(card)
        return widget

    def show_screen_result(
        self,
        success: bool,
        error_msg: str = "",
        is_file_exists: bool = False,
    ) -> None:
        """Configura e exibe a tela de resultado dependendo do status de sucesso ou erro."""
        if success:
            self.lbl_res_icon.setText("✅")
            self.lbl_res_title.setText("GIF Gerado com Sucesso!")
            self.lbl_res_title.setStyleSheet("color: #10b981; font-size: 20px; font-weight: bold;")
            self.lbl_res_desc.setText("Arquivo disponível em:")
            self.entry_res_path.setVisible(True)
            self.entry_res_path.setText(str(self.result_gif_path))
            self.btn_open_folder.setVisible(True)
        else:
            self.lbl_res_icon.setText("❌")
            self.lbl_res_title.setText("Falha na Conversão")
            self.lbl_res_title.setStyleSheet("color: #ef4444; font-size: 20px; font-weight: bold;")
            self.lbl_res_desc.setText(error_msg)
            self.entry_res_path.setVisible(False)
            self.btn_open_folder.setVisible(is_file_exists)

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
        """Retorna para a tela inicial de seleção liberando recursos de preview."""
        self._close_preview_reader()
        self.selected_file = None
        self.result_gif_path = None
        self.stacked_widget.setCurrentIndex(0)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Garante liberação dos recursos de vídeo ao fechar a janela."""
        self._close_preview_reader()
        super().closeEvent(event)


def main() -> None:
    """Função de entrada para inicialização da interface gráfica PySide6."""
    app = QApplication(sys.argv)
    window = GifConverterApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
