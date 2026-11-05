"""Controller e Worker de execução assíncrona da conversão de vídeo para GIF."""

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from simplegif.core import SimpleGIF


class ConversionWorker(QThread):
    """Worker que executa a conversão do vídeo para GIF em segundo plano via QThread."""

    read_progress_updated = Signal(int, int)  # (atual, total)
    save_progress_updated = Signal(int, int)  # (atual, total)
    conversion_completed = Signal(Path)
    conversion_failed = Signal(str, bool)     # (mensagem_erro, eh_file_exists)

    def __init__(
        self,
        gif_maker: SimpleGIF,
        input_path: Path,
        output_path: Path,
        scale: float,
        frame_skip: int,
        less_colors: bool,
        overwrite: bool,
        speed: float = 1.0,
        start_time: float = 0.0,
        end_time: float | None = None,
        max_frames: int | None = None,
    ) -> None:
        super().__init__()
        self.gif_maker = gif_maker
        self.input_path = input_path
        self.output_path = output_path
        self.scale = scale
        self.frame_skip = frame_skip
        self.less_colors = less_colors
        self.overwrite = overwrite
        self.speed = speed
        self.start_time = start_time
        self.end_time = end_time
        self.max_frames = max_frames

    def run(self) -> None:
        """Executa a conversão com callbacks reportados por Signals."""
        try:
            result_path = self.gif_maker.convert_file(
                path=self.input_path,
                output_path=self.output_path,
                scale=self.scale,
                less_colors=self.less_colors,
                speed=self.speed,
                max_frames=self.max_frames,
                frame_skip=self.frame_skip,
                overwrite=self.overwrite,
                start_time=self.start_time,
                end_time=self.end_time,
                read_progress_callback=self._on_read_progress,
                save_progress_callback=self._on_save_progress,
            )
            self.conversion_completed.emit(result_path)
        except FileExistsError as e:
            self.conversion_failed.emit(str(e), True)
        except Exception as e:
            self.conversion_failed.emit(str(e), False)

    def _on_read_progress(self, current: int, total: int) -> None:
        self.read_progress_updated.emit(current, total)

    def _on_save_progress(self, current: int, total: int) -> None:
        self.save_progress_updated.emit(current, total)


class ConversionController(QObject):
    """Controller que orquestra workers de conversão e expõe interface uniforme."""

    read_progress_updated = Signal(int, int)
    save_progress_updated = Signal(int, int)
    conversion_completed = Signal(Path)
    conversion_failed = Signal(str, bool)

    def __init__(self, gif_maker: SimpleGIF | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.gif_maker = gif_maker or SimpleGIF()
        self._current_worker: ConversionWorker | None = None

    @property
    def is_running(self) -> bool:
        """Indica se há uma conversão em execução."""
        return self._current_worker is not None and self._current_worker.isRunning()

    def start_conversion(
        self,
        input_path: Path,
        output_path: Path,
        scale: float,
        frame_skip: int,
        less_colors: bool,
        overwrite: bool,
        speed: float = 1.0,
        start_time: float = 0.0,
        end_time: float | None = None,
        max_frames: int | None = None,
    ) -> ConversionWorker:
        """Cria e inicia o worker de conversão em segundo plano."""
        worker = ConversionWorker(
            gif_maker=self.gif_maker,
            input_path=input_path,
            output_path=output_path,
            scale=scale,
            frame_skip=frame_skip,
            less_colors=less_colors,
            overwrite=overwrite,
            speed=speed,
            start_time=start_time,
            end_time=end_time,
            max_frames=max_frames,
        )
        worker.read_progress_updated.connect(self.read_progress_updated)
        worker.save_progress_updated.connect(self.save_progress_updated)
        worker.conversion_completed.connect(self.conversion_completed)
        worker.conversion_failed.connect(self.conversion_failed)

        self._current_worker = worker
        worker.start()
        return worker
