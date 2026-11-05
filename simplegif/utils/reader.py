"""Módulo de leitura e extração de quadros de vídeo usando OpenCV."""

import cv2
import numpy as np

from collections.abc import Callable, Generator
from pathlib import Path
from types import TracebackType

from simplegif.utils import VideoMetadata


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

    def read_frame_at(self, frame_index: int) -> np.ndarray | None:
        """Busca e retorna um único quadro (BGR) pelo seu índice para pré-visualização."""
        if self._cap is None:
            self.open()
        assert self._cap is not None

        meta = self.metadata
        clamped_idx = max(0, int(frame_index))
        if meta.total_frames > 0:
            clamped_idx = min(clamped_idx, meta.total_frames - 1)

        self._cap.set(cv2.CAP_PROP_POS_FRAMES, clamped_idx)
        ret, frame = self._cap.read()
        if not ret or frame is None:
            return None
        return frame

    def read_frame_at_time(self, time_seconds: float) -> np.ndarray | None:
        """Busca e retorna um único quadro (BGR) correspondente ao instante em segundos."""
        meta = self.metadata
        frame_idx = int(round(max(0.0, time_seconds) * meta.fps))
        return self.read_frame_at(frame_idx)

    def iter_frames(
        self,
        max_frames: int | None = None,
        frame_skip: int = 1,
        start_time: float = 0.0,
        end_time: float | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Generator[tuple[int, np.ndarray], None, None]:
        """Gera quadros brutos lidos do vídeo aplicando o intervalo de tempo e a amostragem configurados.

        Yields:
            tuple[int, np.ndarray]: Tupla contendo (índice_quadro, quadro_bgr_numpy).
        """
        if start_time < 0:
            raise ValueError(f"start_time não pode ser negativo: {start_time}")
        if end_time is not None and end_time <= start_time:
            raise ValueError(f"end_time ({end_time}) deve ser maior que start_time ({start_time})")

        if self._cap is None:
            self.open()
        assert self._cap is not None

        meta = self.metadata
        start_frame = max(0, int(round(start_time * meta.fps)))

        if end_time is not None:
            end_frame = int(round(end_time * meta.fps))
            if meta.total_frames > 0:
                end_frame = min(meta.total_frames, end_frame)
            end_frame = (
                max(start_frame + 1, end_frame)
                if (meta.total_frames == 0 or start_frame < meta.total_frames)
                else start_frame
            )
        else:
            if meta.total_frames > 0:
                end_frame = meta.total_frames
            elif max_frames is not None:
                end_frame = start_frame + max_frames
            else:
                end_frame = start_frame + 2000

        if meta.total_frames > 0 and start_frame >= meta.total_frames:
            return

        range_frames = max(0, end_frame - start_frame)
        if max_frames is not None:
            target_frames = min(range_frames, max_frames) if range_frames > 0 else max_frames
        else:
            target_frames = range_frames

        self._cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        if progress_callback:
            progress_callback(0, target_frames)

        read_count = 0
        while read_count < target_frames:
            ret, frame = self._cap.read()
            if not ret or frame is None:
                break

            if read_count % frame_skip == 0:
                yield start_frame + read_count, frame

            read_count += 1
            if progress_callback:
                progress_callback(read_count, target_frames)

        if progress_callback:
            progress_callback(target_frames, target_frames)
