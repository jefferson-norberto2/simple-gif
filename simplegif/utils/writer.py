"""Módulo de codificação e gravação de arquivos GIF animados usando Pillow."""

from collections.abc import Callable, Generator
import io
from pathlib import Path

import numpy as np
from PIL import Image

from simplegif.utils.config import ConversionOptions, VideoMetadata
from simplegif.utils.processor import FrameProcessor


class GifWriter:
    """Escritor e codificador de GIFs animados baseado no Pillow com suporte a progresso em tempo real."""

    @staticmethod
    def calculate_frame_duration_ms(video_fps: float, frame_skip: int) -> int:
        """Calcula a duração por quadro em milissegundos respeitando a taxa real de amostragem."""
        effective_fps = max(1.0, video_fps / max(1, frame_skip))
        return max(20, int(round((1.0 / effective_fps) * 1000)))

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Formata um tamanho em bytes para exibição legível (B, KB ou MB)."""
        size = max(0, int(size_bytes))
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024.0:.1f} KB"
        return f"{size / (1024.0 * 1024.0):.2f} MB"

    @classmethod
    def estimate_gif_size(
        cls,
        metadata: VideoMetadata,
        options: ConversionOptions,
        sample_frame: np.ndarray | None = None,
    ) -> int:
        """Calcula uma estimativa em bytes do tamanho final do arquivo GIF."""
        start_frame = max(0, int(round(options.start_time * metadata.fps)))
        if options.end_time is not None:
            end_frame = int(round(options.end_time * metadata.fps))
            if metadata.total_frames > 0:
                end_frame = min(metadata.total_frames, end_frame)
            end_frame = (
                max(start_frame + 1, end_frame)
                if (metadata.total_frames == 0 or start_frame < metadata.total_frames)
                else start_frame
            )
        else:
            end_frame = (
                metadata.total_frames
                if metadata.total_frames > 0
                else (start_frame + (options.max_frames if options.max_frames is not None else 2000))
            )

        range_frames = max(0, end_frame - start_frame)
        if options.max_frames is not None:
            inspected_frames = min(range_frames, options.max_frames) if range_frames > 0 else 0
        else:
            inspected_frames = range_frames if range_frames > 0 else 0
        output_frames = (
            (inspected_frames + options.frame_skip - 1) // options.frame_skip
            if inspected_frames > 0
            else 0
        )
        if output_frames <= 0:
            return 0

        target_w, target_h = FrameProcessor.calculate_target_dimensions(
            metadata.width, metadata.height, options.scale
        )

        header_bytes = 800
        if sample_frame is not None:
            pil_base = FrameProcessor.process_frame(
                sample_frame, target_w, target_h, less_colors=False
            )
            buf_base = io.BytesIO()
            pil_base.save(buf_base, format="GIF")
            base_frame_bytes = max(128, buf_base.tell() - header_bytes)

            if options.less_colors:
                pil_reduced = FrameProcessor.process_frame(
                    sample_frame, target_w, target_h, less_colors=True
                )
                buf_reduced = io.BytesIO()
                pil_reduced.save(buf_reduced, format="GIF")
                reduced_frame_bytes = max(96, buf_reduced.tell() - header_bytes)
                per_frame_bytes = min(reduced_frame_bytes, max(96, int(base_frame_bytes * 0.78)))
            else:
                per_frame_bytes = base_frame_bytes
        else:
            bpp = 0.22 if options.less_colors else 0.35
            per_frame_bytes = max(128, int(target_w * target_h * bpp))

        return header_bytes + (output_frames * per_frame_bytes)

    @classmethod
    def write_gif(
        cls,
        frames: list[Image.Image],
        dest_path: str | Path,
        duration_ms: int,
        overwrite: bool = False,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Path:
        """Codifica e grava a lista de frames como um GIF animado no disco.

        Args:
            frames: Lista de quadros Pillow prontos para escrita.
            dest_path: Caminho de saída do arquivo .gif.
            duration_ms: Duração de exibição de cada quadro em milissegundos.
            overwrite: Se True, sobrescreve arquivo pré-existente.
            progress_callback: Callback chamado para cada frame gravado no disco (atual, total).

        Returns:
            Path: Caminho do arquivo GIF gerado.
        """
        if not frames:
            raise ValueError("A lista de quadros para gravação não pode ser vazia.")

        target_file = Path(dest_path).resolve()
        target_file.parent.mkdir(parents=True, exist_ok=True)

        if target_file.exists() and not overwrite:
            raise FileExistsError(f"O arquivo de destino já existe: {target_file}")

        total_frames = len(frames)
        first_frame = frames[0]
        rest_frames = frames[1:]

        def monitored_generator() -> Generator[Image.Image, None, None]:
            for idx, im in enumerate(rest_frames):
                curr = idx + 2
                if progress_callback:
                    progress_callback(curr, total_frames)
                yield im

        if progress_callback:
            progress_callback(1, total_frames)

        first_frame.save(
            target_file,
            save_all=True,
            append_images=monitored_generator(),
            duration=duration_ms,
            loop=0,
            optimize=False,
        )

        if progress_callback:
            progress_callback(total_frames, total_frames)

        return target_file
