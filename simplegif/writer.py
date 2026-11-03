"""Módulo de codificação e gravação de arquivos GIF animados usando Pillow."""

from PIL import Image
from pathlib import Path
from collections.abc import Callable, Generator


class GifWriter:
    """Escritor e codificador de GIFs animados baseado no Pillow com suporte a progresso em tempo real."""

    @staticmethod
    def calculate_frame_duration_ms(video_fps: float, frame_skip: int) -> int:
        """Calcula a duração por quadro em milissegundos respeitando a taxa real de amostragem."""
        effective_fps = max(1.0, video_fps / max(1, frame_skip))
        return max(20, int(round((1.0 / effective_fps) * 1000)))

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
