"""Módulo principal que expõe a Facade SimpleGIF para orquestração da conversão de vídeos para GIF."""

import numpy as np

from PIL import Image
from pathlib import Path
from collections.abc import Callable

from simplegif.utils import ConversionOptions, FrameProcessor, VideoReader, GifWriter

         
class SimpleGIF:
    """Facade central para conversão de vídeos em GIF animado de forma offline, modular e segura.

    Esta classe orquestra as operações especializadas de leitura (VideoReader),
    processamento visual (FrameProcessor) e gravação de GIF (GifWriter).

    Methods:
        - convert_file: Converte um único arquivo de vídeo para GIF.
        - convert_folder: Converte todos os arquivos de vídeo de uma pasta para GIF.
        - less_colors: Reduz a profundidade de cor de um frame (mantido para retrocompatibilidade).
    """

    SUPPORTED_EXTENSIONS: tuple[str, ...] = (".mp4", ".avi", ".mov", ".mkv")

    def __init__(self) -> None:
        """Inicializa uma instância da Facade SimpleGIF."""
        pass

    def convert_file(
        self,
        path: str | Path = "inputs/example.mp4",
        output_path: str | Path = "outputs",
        scale: float = 0.6,
        less_colors: bool = False,
        max_frames: int = 2000,
        frame_skip: int = 5,
        overwrite: bool = False,
        progress_callback: Callable[[int, int], None] | None = None,
        read_progress_callback: Callable[[int, int], None] | None = None,
        save_progress_callback: Callable[[int, int], None] | None = None,
    ) -> Path:
        """Converte um arquivo de vídeo para formato GIF com suporte a progresso em 2 etapas.

        Args:
            path: Caminho do arquivo de vídeo de entrada.
            output_path: Diretório de destino ou caminho completo do arquivo .gif resultante.
            scale: Fator de escala para redimensionamento dos quadros (> 0).
            less_colors: Se True, reduz a paleta de cores para gerar GIFs menores.
            max_frames: Número máximo de quadros a processar (>= 1).
            frame_skip: Intervalo de amostragem de quadros (>= 1).
            overwrite: Se True, permite sobrescrever o arquivo de saída existente.
            progress_callback: Callback unificado de progresso durante o ciclo completo (atual, total).
            read_progress_callback: Callback específico da etapa 1: Leitura do vídeo (atual, total).
            save_progress_callback: Callback específico da etapa 2: Gravação no disco (atual, total).

        Returns:
            Path: Caminho do arquivo GIF gerado no disco.
        """
        options = ConversionOptions(
            scale=scale,
            frame_skip=frame_skip,
            less_colors=less_colors,
            max_frames=max_frames,
            overwrite=overwrite,
        )

        input_path = Path(path).resolve()
        output_target = Path(output_path).resolve()
        if output_target.suffix.lower() == ".gif":
            dest_file = output_target
        else:
            dest_file = output_target / f"{input_path.stem}.gif"

        # --- ETAPA 1: Leitura e Processamento dos Quadros ---
        def on_read(current: int, total: int) -> None:
            if read_progress_callback:
                read_progress_callback(current, total)
            elif progress_callback:
                progress_callback(int((current / total) * 50) if total > 0 else 0, 100)

        processed_frames: list[Image.Image] = []

        with VideoReader(input_path) as reader:
            metadata = reader.metadata
            target_w, target_h = FrameProcessor.calculate_target_dimensions(
                metadata.width, metadata.height, options.scale
            )

            for _, frame in reader.iter_frames(
                max_frames=options.max_frames,
                frame_skip=options.frame_skip,
                progress_callback=on_read,
            ):
                processed_img = FrameProcessor.process_frame(
                    frame=frame,
                    target_w=target_w,
                    target_h=target_h,
                    less_colors=options.less_colors,
                )
                processed_frames.append(processed_img)

            duration_ms = GifWriter.calculate_frame_duration_ms(
                metadata.fps, options.frame_skip
            )

        if not processed_frames:
            raise RuntimeError(f"Nenhum frame válido pôde ser extraído do vídeo: {input_path}")

        # --- ETAPA 2: Codificação e Gravação do GIF no Disco ---
        def on_save(current: int, total: int) -> None:
            if save_progress_callback:
                save_progress_callback(current, total)
            elif progress_callback:
                pct = 50 + int(((current / total) * 50) if total > 0 else 0)
                progress_callback(pct, 100)

        return GifWriter.write_gif(
            frames=processed_frames,
            dest_path=dest_file,
            duration_ms=duration_ms,
            overwrite=options.overwrite,
            progress_callback=on_save,
        )

    def convert_folder(
        self,
        path: str | Path = "inputs/",
        output_path: str | Path = "outputs",
        scale: float = 0.6,
        less_colors: bool = False,
        max_frames: int = 2000,
        frame_skip: int = 5,
        overwrite: bool = False,
    ) -> list[Path]:
        """Converte todos os arquivos de vídeo suportados em uma pasta para formato GIF.

        Args:
            path: Pasta contendo os arquivos de vídeo de entrada.
            output_path: Pasta onde os arquivos GIF gerados serão salvos.
            scale: Fator de escala para redimensionamento dos quadros.
            less_colors: Flag para reduzir a profundidade de cor.
            max_frames: Máximo de quadros a processar por arquivo de vídeo.
            frame_skip: Intervalo entre quadros processados.
            overwrite: Se True, sobrescreve arquivos GIF existentes.

        Returns:
            list[Path]: Lista de caminhos para os arquivos GIF gerados com sucesso.
        """
        input_dir = Path(path).resolve()
        if not input_dir.exists():
            raise FileNotFoundError(f"Pasta de entrada não encontrada: {input_dir}")
        if not input_dir.is_dir():
            raise ValueError(f"O caminho especificado não é um diretório: {input_dir}")

        output_dir = Path(output_path).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        converted_files: list[Path] = []
        for file_path in sorted(input_dir.iterdir()):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                result = self.convert_file(
                    path=file_path,
                    output_path=output_dir,
                    scale=scale,
                    less_colors=less_colors,
                    max_frames=max_frames,
                    frame_skip=frame_skip,
                    overwrite=overwrite,
                )
                converted_files.append(result)

        return converted_files

    def save_gif(self, progress_callback: Callable[[int, int], None] | None = None) -> int:
        """Método mantido para retrocompatibilidade."""
        return 0

    def less_colors(self, image: np.ndarray) -> np.ndarray:
        """Reduz a profundidade de cor de uma imagem (retrocompatibilidade via FrameProcessor)."""
        return FrameProcessor.reduce_colors(image)
