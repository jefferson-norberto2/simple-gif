"""Fixtures de vídeo sintético para testes rápidos e 100% offline."""

from pathlib import Path
import cv2
import numpy as np
import pytest


@pytest.fixture
def sample_video_path(tmp_path: Path) -> Path:
    """Gera um vídeo sintético MP4 de 30 quadros a 10 FPS (3.0 segundos) para testes."""
    video_file = tmp_path / "test_video.mp4"
    width, height = 120, 90
    fps = 10.0
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(video_file), fourcc, fps, (width, height))

    try:
        for i in range(30):
            img = np.zeros((height, width, 3), dtype=np.uint8)
            color = ((i * 8) % 255, (i * 15) % 255, 180)
            cv2.rectangle(img, (10 + i * 2, 20), (40 + i * 2, 70), color, -1)
            out.write(img)
    finally:
        out.release()

    return video_file
