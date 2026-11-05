"""Módulo de processamento e transformação de quadros de imagem."""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


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
    def get_font(cls, font_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """Carrega fonte TrueType proporcional com fallback seguro para a fonte padrão."""
        for font_name in ("arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "segoeui.ttf", "Helvetica.ttf"):
            try:
                return ImageFont.truetype(font_name, font_size)
            except OSError:
                continue
        try:
            return ImageFont.load_default(size=font_size)
        except TypeError:
            return ImageFont.load_default()

    @classmethod
    def draw_speed_badge(
        cls,
        image: Image.Image,
        speed: float,
        position: str = "Superior Direito",
        size_mode: str = "Médio",
    ) -> Image.Image:
        """Desenha um banner flutuante em formato de pílula com o multiplicador de velocidade.

        O tamanho da fonte, espaçamentos internos (padding), cantos arredondados e margens
        são calculados proporcionalmente à resolução do quadro para manter consistência
        perfeita tanto no preview quanto no GIF final redimensionado.
        """
        w, h = image.size
        if w <= 0 or h <= 0:
            return image

        size_lower = size_mode.lower()
        if "pequeno" in size_lower or "4%" in size_lower:
            factor = 0.040
        elif "grande" in size_lower or "8%" in size_lower:
            factor = 0.080
        else:
            factor = 0.060

        font_size = max(9, int(round(h * factor)))
        font = cls.get_font(font_size)

        speed_val = max(0.1, speed)
        speed_str = f"{speed_val:.2f}".rstrip("0").rstrip(".")
        if "." not in speed_str:
            speed_str = f"{speed_val:.1f}"

        if speed_val >= 1.0:
            text = f">> {speed_str}x"
        else:
            text = f"<< {speed_str}x"

        dummy = Image.new("RGBA", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy)
        bbox = dummy_draw.textbbox((0, 0), text, font=font)
        tw = max(1, bbox[2] - bbox[0])
        th = max(1, bbox[3] - bbox[1])

        pad_x = max(6, int(round(font_size * 0.55)))
        pad_y = max(3, int(round(font_size * 0.35)))
        bw = min(w, tw + 2 * pad_x)
        bh = min(h, th + 2 * pad_y)
        radius = max(3, int(round(bh * 0.45)))
        margin = max(4, int(round(h * 0.035)))

        pos_lower = position.lower()
        if "esquerdo" in pos_lower:
            x0 = margin
        elif "centro" in pos_lower:
            x0 = (w - bw) // 2
        else:  # padrão: direito
            x0 = w - bw - margin

        if "inferior" in pos_lower:
            y0 = h - bh - margin
        else:  # padrão: superior
            y0 = margin

        x0 = max(0, min(w - bw, x0))
        y0 = max(0, min(h - bh, y0))
        x1 = x0 + bw
        y1 = y0 + bh

        pill = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        pdraw = ImageDraw.Draw(pill)
        pdraw.rounded_rectangle([0, 0, bw, bh], radius=radius, fill=(0, 0, 0, 150))

        tx = (bw - tw) // 2 - bbox[0]
        ty = (bh - th) // 2 - bbox[1]
        stroke_w = max(0, int(round(font_size * 0.04)))
        pdraw.text(
            (tx, ty),
            text,
            font=font,
            fill=(255, 255, 255, 255),
            stroke_width=stroke_w,
            stroke_fill=(255, 255, 255, 255),
        )

        orig_mode = image.mode
        base_rgba = image.convert("RGBA") if orig_mode != "RGBA" else image.copy()
        crop_box = (x0, y0, x1, y1)
        crop = base_rgba.crop(crop_box)
        comp = Image.alpha_composite(crop, pill)
        base_rgba.paste(comp, crop_box)

        if orig_mode != "RGBA":
            return base_rgba.convert(orig_mode)
        return base_rgba

    @classmethod
    def process_frame(
        cls,
        frame: np.ndarray,
        target_w: int,
        target_h: int,
        less_colors: bool = False,
        show_speed_badge: bool = False,
        speed: float = 1.0,
        badge_position: str = "Superior Direito",
        badge_size: str = "Médio",
    ) -> Image.Image:
        """Aplica o pipeline completo de transformação em um único quadro."""
        resized = cls.resize(frame, target_w, target_h)
        rgb_frame = cls.bgr_to_rgb(resized)
        if less_colors:
            rgb_frame = cls.reduce_colors(rgb_frame)
        pil_frame = cls.to_pil(rgb_frame)
        if show_speed_badge:
            pil_frame = cls.draw_speed_badge(
                image=pil_frame,
                speed=speed,
                position=badge_position,
                size_mode=badge_size,
            )
        return pil_frame
