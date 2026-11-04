"""Widget composto para pré-visualização de vídeo e seleção de trecho."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from simplegif.ui.helpers import format_seconds
from simplegif.ui.widgets.range_slider import RangeSlider


class VideoPreviewWidget(QWidget):
    """Widget que agrupa o visor do vídeo, controle deslizante duplo e campos de tempo."""

    range_changed = Signal(int, int)              # (start_frame, end_frame)
    time_range_changed = Signal(float, float)      # (start_sec, end_sec)
    preview_frame_requested = Signal(int)         # (frame_index)
    toggle_playback_requested = Signal()          # Requisição para iniciar/pausar playback

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.video_fps: float = 30.0
        self.total_frames: int = 100
        self.duration_seconds: float = 0.0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 1. Visor de Vídeo
        self.lbl_video_preview = QLabel("Pré-visualização do vídeo")
        self.lbl_video_preview.setObjectName("videoPreviewLabel")
        self.lbl_video_preview.setFixedHeight(190)
        self.lbl_video_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_video_preview)

        # 2. Controles de Reprodução e Range Slider
        slider_row = QHBoxLayout()
        slider_row.setSpacing(10)

        self.btn_play_preview = QPushButton("▶ Preview")
        self.btn_play_preview.setFixedWidth(95)
        self.btn_play_preview.setFixedHeight(30)
        self.btn_play_preview.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_play_preview.clicked.connect(self.toggle_playback_requested.emit)

        self.range_slider = RangeSlider()
        self.range_slider.start_value_changed.connect(self._on_slider_start_changed)
        self.range_slider.end_value_changed.connect(self._on_slider_end_changed)

        slider_row.addWidget(self.btn_play_preview)
        slider_row.addWidget(self.range_slider, stretch=1)
        layout.addLayout(slider_row)

        # 3. Controles Numéricos de Tempo e Resumo do Trecho
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

        layout.addLayout(time_row)

    def setup_video(self, fps: float, total_frames: int, duration_seconds: float) -> None:
        """Inicializa limites do slider e dos controles de tempo com base no vídeo."""
        self.video_fps = max(1.0, fps)
        self.total_frames = max(1, total_frames)
        self.duration_seconds = max(0.01, duration_seconds)

        max_frame_idx = max(1, self.total_frames - 1)
        self.range_slider.set_range_bounds(0, max_frame_idx)

        step_sec = max(0.01, round(1.0 / self.video_fps, 2))
        self.spin_start_time.blockSignals(True)
        self.spin_end_time.blockSignals(True)

        self.spin_start_time.setRange(0.0, max(0.0, self.duration_seconds - step_sec))
        self.spin_start_time.setSingleStep(step_sec)
        self.spin_start_time.setValue(0.0)

        self.spin_end_time.setRange(step_sec, max(step_sec, self.duration_seconds))
        self.spin_end_time.setSingleStep(step_sec)
        self.spin_end_time.setValue(self.duration_seconds)

        self.spin_start_time.blockSignals(False)
        self.spin_end_time.blockSignals(False)

        self.update_range_summary()

    def set_preview_pixmap(self, pixmap: QPixmap) -> None:
        """Define o frame renderizado no visor de preview."""
        self.lbl_video_preview.setPixmap(pixmap)

    def set_preview_text(self, text: str) -> None:
        """Define mensagem descritiva no visor de preview."""
        self.lbl_video_preview.setPixmap(QPixmap())
        self.lbl_video_preview.setText(text)

    def set_playback_playing(self, is_playing: bool) -> None:
        """Altera o texto do botão de reprodução dependendo do estado."""
        self.btn_play_preview.setText("⏸ Pausar" if is_playing else "▶ Preview")

    def get_selected_range_frames(self) -> tuple[int, int]:
        """Retorna os quadros inicial e final selecionados."""
        return self.range_slider.start_value(), self.range_slider.end_value()

    def get_selected_time_range(self) -> tuple[float, float]:
        """Retorna os instantes em segundos inicial e final selecionados."""
        return self.spin_start_time.value(), self.spin_end_time.value()

    def update_range_summary(self) -> None:
        """Atualiza o resumo textual do intervalo selecionado."""
        start_sec = self.spin_start_time.value()
        end_sec = self.spin_end_time.value()
        clip_duration = max(0.0, end_sec - start_sec)
        clip_frames = max(1, self.range_slider.end_value() - self.range_slider.start_value() + 1)
        self.lbl_range_summary.setText(
            f"{format_seconds(start_sec)} → {format_seconds(end_sec)} ({clip_duration:.1f}s • {clip_frames} frames)"
        )

    def _on_slider_start_changed(self, start_frame: int) -> None:
        start_sec = round(start_frame / self.video_fps, 2)
        self.spin_start_time.blockSignals(True)
        self.spin_start_time.setValue(start_sec)
        self.spin_start_time.blockSignals(False)
        self.update_range_summary()
        self.preview_frame_requested.emit(start_frame)
        self.range_changed.emit(self.range_slider.start_value(), self.range_slider.end_value())
        self.time_range_changed.emit(self.spin_start_time.value(), self.spin_end_time.value())

    def _on_slider_end_changed(self, end_frame: int) -> None:
        end_sec = min(self.duration_seconds, round((end_frame + 1) / self.video_fps, 2))
        self.spin_end_time.blockSignals(True)
        self.spin_end_time.setValue(end_sec)
        self.spin_end_time.blockSignals(False)
        self.update_range_summary()
        self.preview_frame_requested.emit(end_frame)
        self.range_changed.emit(self.range_slider.start_value(), self.range_slider.end_value())
        self.time_range_changed.emit(self.spin_start_time.value(), self.spin_end_time.value())

    def _on_spin_start_changed(self, start_sec: float) -> None:
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
        self.update_range_summary()
        self.preview_frame_requested.emit(start_frame)
        self.range_changed.emit(self.range_slider.start_value(), self.range_slider.end_value())
        self.time_range_changed.emit(self.spin_start_time.value(), self.spin_end_time.value())

    def _on_spin_end_changed(self, end_sec: float) -> None:
        min_gap = max(0.01, 1.0 / self.video_fps)
        if end_sec <= self.spin_start_time.value():
            clamped_end = min(self.duration_seconds, self.spin_start_time.value() + min_gap)
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
        self.update_range_summary()
        self.preview_frame_requested.emit(end_frame)
        self.range_changed.emit(self.range_slider.start_value(), self.range_slider.end_value())
        self.time_range_changed.emit(self.spin_start_time.value(), self.spin_end_time.value())
