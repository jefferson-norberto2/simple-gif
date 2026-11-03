"""Módulo central para conversão de vídeos em GIFs animados usando OpenCV e Pillow."""

from collections.abc import Callable, Generator
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


class SimpleGIF:
    """Classe para conversão de arquivos de vídeo em formato GIF de forma eficiente e offline.

    Utiliza OpenCV para leitura e pré-processamento de quadros e Pillow para codificação progressiva,
    fornecendo callbacks de progresso independentes tanto para a leitura quanto para o salvamento em disco.

    Methods:
        - convert_file: Converte um único arquivo de vídeo para GIF com controle de etapas.
        - convert_folder: Converte todos os arquivos de vídeo de uma pasta para GIF.
        - less_colors: Reduz a profundidade de cor de um frame.
    """

    SUPPORTED_EXTENSIONS: tuple[str, ...] = (".mp4", ".avi", ".mov", ".mkv")

    def __init__(self) -> None:
        """Inicializa uma instância do conversor SimpleGIF."""
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
        """Converte um arquivo de vídeo para o formato GIF fornecendo progresso em 2 etapas.

        Args:
            path: Caminho do arquivo de vídeo de entrada.
            output_path: Diretório de destino ou caminho completo do arquivo .gif resultante.
            scale: Fator de escala para redimensionamento dos quadros (deve ser > 0).
            less_colors: Se True, reduz a profundidade de cor para gerar GIFs mais leves.
            max_frames: Número máximo de quadros a processar (deve ser >= 1).
            frame_skip: Intervalo de captura de quadros (deve ser >= 1).
            overwrite: Se True, permite sobrescrever o arquivo de saída se já existir.
            progress_callback: Função unificada de progresso chamada durante o processo (atual, total).
            read_progress_callback: Callback específico da etapa 1: Leitura do vídeo (atual, total).
            save_progress_callback: Callback específico da etapa 2: Gravação em disco (atual, total).

        Returns:
            Path: Caminho do arquivo GIF gerado no disco.

        Raises:
            FileNotFoundError: Se o arquivo de entrada não for encontrado.
            FileExistsError: Se o arquivo de saída já existir e overwrite for False.
            ValueError: Se parâmetros como scale, frame_skip ou max_frames forem inconsistentes.
            RuntimeError: Se o vídeo não puder ser aberto ou se nenhum frame for extraído.
        """
        if scale <= 0:
            raise ValueError(f"Escala deve ser maior que zero: {scale}")
        if frame_skip < 1:
            raise ValueError(f"frame_skip deve ser maior ou igual a 1: {frame_skip}")
        if max_frames < 1:
            raise ValueError(f"max_frames deve ser maior ou igual a 1: {max_frames}")

        input_path = Path(path).resolve()
        if not input_path.is_file():
            raise FileNotFoundError(f"Arquivo de vídeo não encontrado: {input_path}")

        output_target = Path(output_path).resolve()
        if output_target.suffix.lower() == ".gif":
            dest_file = output_target
            output_dir = dest_file.parent
        else:
            output_dir = output_target
            dest_file = output_dir / f"{input_path.stem}.gif"

        output_dir.mkdir(parents=True, exist_ok=True)

        if dest_file.exists() and not overwrite:
            raise FileExistsError(f"O arquivo de destino já existe: {dest_file}")

        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise RuntimeError(f"Não foi possível abrir o arquivo de vídeo: {input_path}")

        try:
            orig_fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
            if orig_fps <= 0.0 or np.isnan(orig_fps):
                orig_fps = 30.0

            orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            if orig_w <= 0 or orig_h <= 0:
                raise RuntimeError(f"Dimensões inválidas do vídeo: {orig_w}x{orig_h}")

            target_frames = min(total_frames, max_frames) if total_frames > 0 else max_frames
            target_w = max(1, int(orig_w * scale))
            target_h = max(1, int(orig_h * scale))

            effective_fps = max(1.0, orig_fps / frame_skip)
            duration_per_frame_ms = max(20, int(round((1.0 / effective_fps) * 1000)))

            # --- ETAPA 1: Leitura e Redimensionamento dos Quadros ---
            if read_progress_callback:
                read_progress_callback(0, target_frames)
            elif progress_callback:
                progress_callback(0, 100)

            frames: list[Image.Image] = []
            frame_idx = 0

            while frame_idx < target_frames:
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                if frame_idx % frame_skip == 0:
                    resized = cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)
                    rgb_frame = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

                    if less_colors:
                        rgb_frame = self.less_colors(rgb_frame)

                    pil_img = Image.fromarray(rgb_frame)
                    frames.append(pil_img)

                frame_idx += 1
                if read_progress_callback:
                    read_progress_callback(frame_idx, target_frames)
                elif progress_callback:
                    pct = int((frame_idx / target_frames) * 50)
                    progress_callback(pct, 100)

            if not frames:
                raise RuntimeError(f"Nenhum frame válido pôde ser lido do vídeo: {input_path}")

            if read_progress_callback:
                read_progress_callback(target_frames, target_frames)

            # --- ETAPA 2: Codificação e Gravação do GIF com Monitoramento Frame-a-Frame ---
            total_to_save = len(frames)
            first_frame = frames[0]
            rest_frames = frames[1:]

            def save_monitor_generator() -> Generator[Image.Image, None, None]:
                for idx, im in enumerate(rest_frames):
                    curr = idx + 2
                    if save_progress_callback:
                        save_progress_callback(curr, total_to_save)
                    elif progress_callback:
                        pct = 50 + int((curr / total_to_save) * 50)
                        progress_callback(pct, 100)
                    yield im

            if save_progress_callback:
                save_progress_callback(1, total_to_save)
            elif progress_callback:
                progress_callback(50, 100)

            first_frame.save(
                dest_file,
                save_all=True,
                append_images=save_monitor_generator(),
                duration=duration_per_frame_ms,
                loop=0,
                optimize=False,
            )

            if save_progress_callback:
                save_progress_callback(total_to_save, total_to_save)
            elif progress_callback:
                progress_callback(100, 100)

            return dest_file
        finally:
            cap.release()

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

        Raises:
            FileNotFoundError: Se a pasta de entrada não existir.
            ValueError: Se o caminho de entrada não for um diretório válido.
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
        """Reduz a profundidade de cor de uma imagem aplicando quantização uniforme.

        Args:
            image: Array NumPy representando uma imagem (frame RGB).

        Returns:
            np.ndarray: Imagem com profundidade de cores reduzida.
        """
        data = np.asarray(image)
        r_data = (data // 8) * 8
        return r_data.astype(np.uint8)
