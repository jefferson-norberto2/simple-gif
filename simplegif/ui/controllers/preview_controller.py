"""Controller de gerenciamento do preview de vídeo e estimativa de tamanho."""

from pathlib import Path

import numpy as np
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap

from simplegif.utils.config import ConversionOptions, VideoMetadata
from simplegif.utils.processor import FrameProcessor
from simplegif.utils.reader import VideoReader
from simplegif.utils.writer import GifWriter


class PreviewController(QObject):
    """Controlador responsável pela leitura sob demanda, reprodução de preview e cálculo de estimativa."""

    frame_ready = Signal(QPixmap, int)           # (pixmap, frame_index)
    metadata_loaded = Signal(VideoMetadata)      # metadados do vídeo
    playback_state_changed = Signal(bool)        # is_playing
    error_occurred = Signal(str)                 # mensagem de erro

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.reader: VideoReader | None = None
        self._sample_frame_bgr: np.ndarray | None = None
        self._frame_byte_cache: dict[tuple[float, bool], int] = {}

        self.video_fps: float = 30.0
        self.video_total_frames: int = 1
        self.video_duration: float = 0.0

        self._playback_start: int = 0
        self._playback_end: int = 0
        self._playback_current: int = 0

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer_tick)

    @property
    def is_playing(self) -> bool:
        """Indica se a reprodução do preview está ativa."""
        return self._timer.isActive()

    def load_video(self, video_path: Path) -> VideoMetadata:
        """Abre o arquivo de vídeo e carrega seus metadados."""
        self.close()
        self.reader = VideoReader(video_path)
        self.reader.open()

        meta = self.reader.metadata
        self.video_fps = meta.fps
        self.video_total_frames = max(1, meta.total_frames)
        self.video_duration = (
            meta.duration_seconds
            if meta.duration_seconds > 0
            else (self.video_total_frames / self.video_fps)
        )

        self._sample_frame_bgr = self.reader.read_frame_at(0)
        self._frame_byte_cache.clear()
        self.metadata_loaded.emit(meta)
        return meta

    def render_frame_at(self, frame_index: int, max_w: int = 800, max_h: int = 450) -> QPixmap | None:
        """Lê um quadro sob demanda e o converte em um QPixmap otimizado para o visor."""
        if self.reader is None:
            return None

        frame_bgr = self.reader.read_frame_at(frame_index)
        if frame_bgr is None:
            return None

        orig_h, orig_w = frame_bgr.shape[:2]
        scale = min(max_w / max(1, orig_w), max_h / max(1, orig_h))
        target_w, target_h = FrameProcessor.calculate_target_dimensions(orig_w, orig_h, scale)

        resized_bgr = FrameProcessor.resize(frame_bgr, target_w, target_h)
        rgb_frame = FrameProcessor.bgr_to_rgb(resized_bgr)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w

        qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
        pixmap = QPixmap.fromImage(qimg)
        self.frame_ready.emit(pixmap, frame_index)
        return pixmap

    def toggle_playback(self, start_frame: int, end_frame: int, current_frame: int) -> None:
        """Alterna entre reproduzir e pausar o trecho selecionado em loop."""
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback(start_frame, end_frame, current_frame)

    def start_playback(self, start_frame: int, end_frame: int, current_frame: int) -> None:
        """Inicia a reprodução do trecho selecionado em loop."""
        if self.reader is None:
            return

        self._playback_start = start_frame
        self._playback_end = end_frame
        self._playback_current = (
            current_frame
            if (start_frame <= current_frame <= end_frame)
            else start_frame
        )

        interval_ms = max(30, int(round(1000.0 / min(30.0, self.video_fps))))
        self._timer.start(interval_ms)
        self.playback_state_changed.emit(True)

    def stop_playback(self) -> None:
        """Interrompe a reprodução do preview."""
        if self._timer.isActive():
            self._timer.stop()
            self.playback_state_changed.emit(False)

    def _on_timer_tick(self) -> None:
        if self.reader is None:
            self.stop_playback()
            return

        step = max(1, int(round(self.video_fps / 15.0))) if self.video_fps > 30.0 else 1
        next_f = self._playback_current + step
        if next_f > self._playback_end:
            next_f = self._playback_start

        self._playback_current = next_f
        self.render_frame_at(next_f)

    def estimate_size_bytes(
        self,
        scale: float,
        frame_skip: int,
        less_colors: bool,
        start_frame: int,
        end_frame: int,
        max_frames: int | None = None,
    ) -> int:
        """Calcula a estimativa de tamanho do GIF em bytes com base nas opções."""
        if self.reader is None:
            return 0

        meta = self.reader.metadata
        cache_key = (scale, less_colors)
        if cache_key not in self._frame_byte_cache:
            single_opts = ConversionOptions(
                scale=scale,
                frame_skip=1,
                less_colors=less_colors,
                max_frames=1,
            )
            single_est = GifWriter.estimate_gif_size(
                meta, single_opts, sample_frame=self._sample_frame_bgr
            )
            self._frame_byte_cache[cache_key] = max(96, single_est - 800)

        per_frame_bytes = self._frame_byte_cache[cache_key]
        clip_frames = max(1, end_frame - start_frame + 1)
        inspected_frames = (
            min(clip_frames, max_frames) if max_frames is not None else clip_frames
        )
        output_frames = (inspected_frames + frame_skip - 1) // frame_skip
        return 800 + (output_frames * per_frame_bytes)

    def close(self) -> None:
        """Fecha com segurança o leitor de vídeo e libera recursos."""
        self.stop_playback()
        self._sample_frame_bgr = None
        self._frame_byte_cache.clear()
        if self.reader is not None:
            self.reader.close()
            self.reader = None
