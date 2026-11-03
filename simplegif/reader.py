"""Módulo de leitura e extração de quadros de vídeo usando OpenCV."""

from collections.abc import Callable, Generator
from pathlib import Path
from types import TracebackType

import cv2
import numpy as np

from simplegif import VideoMetadata


class VideoReader:
    """Leitor de arquivos de vídeo baseado em OpenCV implementado como context manager."""

    def __init__(self, video_path: str | Path) -> None:
        self.video_path = Path(video_path).resolve()
        if not self.video_path.is_file():
            raise FileNotFoundError(f"Arquivo de vídeo não encontrado: {self.video_path}")

        self._cap: cv2.VideoCapture | None = None
        self._metadata: VideoMetadata | None = None

    def __enter__(self) -> "VideoReader":
        self.open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def open(self) -> None:
        """Abre o arquivo de vídeo e valida a integridade do fluxo."""
        if self._cap is None:
            self._cap = cv2.VideoCapture(str(self.video_path))
            if not self._cap.isOpened():
                raise RuntimeError(f"Não foi possível abrir o arquivo de vídeo: {self.video_path}")

            orig_fps = float(self._cap.get(cv2.CAP_PROP_FPS) or 0.0)
            if orig_fps <= 0.0 or np.isnan(orig_fps):
                orig_fps = 30.0

            orig_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            orig_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = max(0, int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT)))

            if orig_w <= 0 or orig_h <= 0:
                self.close()
                raise RuntimeError(f"Dimensões inválidas do vídeo: {orig_w}x{orig_h}")

            self._metadata = VideoMetadata(
                width=orig_w,
                height=orig_h,
                fps=orig_fps,
                total_frames=total_frames,
            )

    def close(self) -> None:
        """Libera os recursos e descritores do OpenCV."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    @property
    def metadata(self) -> VideoMetadata:
        """Retorna os metadados do vídeo aberto."""
        if self._metadata is None:
            self.open()
        assert self._metadata is not None
        return self._metadata

    def iter_frames(
        self,
        max_frames: int = 2000,
        frame_skip: int = 1,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Generator[tuple[int, np.ndarray], None, None]:
        """Gera quadros brutos lidos do vídeo aplicando a amostragem configurada.

        Yields:
            tuple[int, np.ndarray]: Tupla contendo (índice_quadro, quadro_bgr_numpy).
        """
        if self._cap is None:
            self.open()
        assert self._cap is not None

        meta = self.metadata
        target_frames = min(meta.total_frames, max_frames) if meta.total_frames > 0 else max_frames

        if progress_callback:
            progress_callback(0, target_frames)

        frame_idx = 0
        while frame_idx < target_frames:
            ret, frame = self._cap.read()
            if not ret or frame is None:
                break

            if frame_idx % frame_skip == 0:
                yield frame_idx, frame

            frame_idx += 1
            if progress_callback:
                progress_callback(frame_idx, target_frames)

        if progress_callback:
            progress_callback(target_frames, target_frames)
