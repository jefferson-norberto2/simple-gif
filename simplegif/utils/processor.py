"""Módulo de processamento e transformação de quadros de imagem."""

import cv2
import numpy as np
from PIL import Image


class FrameProcessor:
    """Processador de quadros de vídeo responsável por redimensionamento e transformações de cor.

    Contém funções puras, testáveis de forma isolada sem dependência de arquivos no disco.
    """

    @staticmethod
    def calculate_target_dimensions(orig_w: int, orig_h: int, scale: float) -> tuple[int, int]:
        """Calcula as dimensões alvo preservando a proporção com base na escala."""
        if orig_w <= 0 or orig_h <= 0 or scale <= 0:
            raise ValueError(f"Parâmetros de dimensão inválidos: {orig_w}x{orig_h}, escala={scale}")
        target_w = max(1, int(round(orig_w * scale)))
        target_h = max(1, int(round(orig_h * scale)))
        return target_w, target_h

    @staticmethod
    def resize(frame: np.ndarray, target_w: int, target_h: int) -> np.ndarray:
        """Redimensiona um quadro para a resolução alvo utilizando interpolação por área."""
        return cv2.resize(frame, (target_w, target_h), interpolation=cv2.INTER_AREA)

    @staticmethod
    def bgr_to_rgb(frame: np.ndarray) -> np.ndarray:
        """Converte o espaço de cores de BGR (padrão OpenCV) para RGB (padrão Pillow)."""
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    @staticmethod
    def reduce_colors(image: np.ndarray) -> np.ndarray:
        """Reduz a profundidade de cor de uma imagem aplicando quantização uniforme."""
        data = np.asarray(image)
        r_data = (data // 8) * 8
        return r_data.astype(np.uint8)

    @staticmethod
    def to_pil(frame: np.ndarray) -> Image.Image:
        """Converte um array NumPy RGB em um objeto de imagem do Pillow."""
        return Image.fromarray(frame)

    @classmethod
    def process_frame(
        cls,
        frame: np.ndarray,
        target_w: int,
        target_h: int,
        less_colors: bool = False,
    ) -> Image.Image:
        """Aplica o pipeline completo de transformação em um único quadro."""
        resized = cls.resize(frame, target_w, target_h)
        rgb_frame = cls.bgr_to_rgb(resized)
        if less_colors:
            rgb_frame = cls.reduce_colors(rgb_frame)
        return cls.to_pil(rgb_frame)
