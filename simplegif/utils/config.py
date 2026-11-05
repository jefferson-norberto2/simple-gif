"""Módulo de configuração e modelos de dados para simplegif."""

from dataclasses import dataclass


@dataclass(frozen=True)
class VideoMetadata:
    """Metadados extraídos de um arquivo de vídeo."""

    width: int
    height: int
    fps: float
    total_frames: int

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError(f"Dimensões do vídeo devem ser positivas: {self.width}x{self.height}")
        if self.fps <= 0:
            raise ValueError(f"FPS do vídeo deve ser maior que zero: {self.fps}")
        if self.total_frames < 0:
            raise ValueError(f"Contagem de quadros não pode ser negativa: {self.total_frames}")

    @property
    def duration_seconds(self) -> float:
        """Retorna a duração total estimada do vídeo em segundos."""
        return self.total_frames / self.fps if self.fps > 0 else 0.0


@dataclass(frozen=True)
class ConversionOptions:
    """Opções de configuração para o processo de conversão de vídeo para GIF."""

    scale: float = 0.6
    frame_skip: int = 5
    speed: float = 1.0
    less_colors: bool = False
    max_frames: int | None = None
    overwrite: bool = False
    start_time: float = 0.0
    end_time: float | None = None

    def __post_init__(self) -> None:
        if self.scale <= 0:
            raise ValueError(f"Escala deve ser maior que zero: {self.scale}")
        if self.frame_skip < 1:
            raise ValueError(f"frame_skip deve ser maior ou igual a 1: {self.frame_skip}")
        if self.speed <= 0:
            raise ValueError(f"speed deve ser maior que zero: {self.speed}")
        if self.max_frames is not None and self.max_frames < 1:
            raise ValueError(f"max_frames deve ser maior ou igual a 1: {self.max_frames}")
        if self.start_time < 0:
            raise ValueError(f"start_time não pode ser negativo: {self.start_time}")
        if self.end_time is not None and self.end_time <= self.start_time:
            raise ValueError(
                f"end_time ({self.end_time}) deve ser maior que start_time ({self.start_time})"
            )

