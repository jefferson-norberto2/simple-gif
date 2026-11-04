"""Funções e constantes utilitárias para a interface gráfica."""

from pathlib import Path
import sys

SCALE_MAP: dict[str, float] = {
    "100% (Original)": 1.0,
    "75%": 0.75,
    "60% (Recomendado)": 0.6,
    "50%": 0.5,
    "35%": 0.35,
    "25%": 0.25,
}


def load_stylesheet(qss_name: str = "style.qss") -> str:
    """Carrega as folhas de estilo QSS a partir de arquivo externo (compatível com PyInstaller)."""
    if hasattr(sys, "_MEIPASS"):
        base_dir = Path(sys._MEIPASS)
        qss_file = base_dir / "simplegif/ui" / qss_name
        if not qss_file.is_file():
            qss_file = base_dir / qss_name
    else:
        qss_file = Path(__file__).resolve().parent / qss_name

    if qss_file.is_file():
        return qss_file.read_text(encoding="utf-8")
    return ""


def format_seconds(seconds: float) -> str:
    """Formata um valor em segundos para o padrão MM:SS.d."""
    total_sec = max(0.0, float(seconds))
    mins = int(total_sec // 60)
    secs = total_sec - (mins * 60)
    return f"{mins:02d}:{secs:04.1f}"
