"""Controle deslizante duplo (dual-handle) para seleção de intervalo de quadros."""

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QWidget


class RangeSlider(QWidget):
    """Controle deslizante duplo (dual-handle) para seleção de intervalo de quadros de vídeo."""

    start_value_changed = Signal(int)
    end_value_changed = Signal(int)
    range_changed = Signal(int, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._minimum: int = 0
        self._maximum: int = 100
        self._start_value: int = 0
        self._end_value: int = 100
        self._current_value: int = 0
        self._active_handle: str | None = None
        self._margin: int = 10
        self._handle_radius: int = 8
        self.setFixedHeight(30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def minimum(self) -> int:
        """Retorna o limite mínimo do slider."""
        return self._minimum

    def maximum(self) -> int:
        """Retorna o limite máximo do slider."""
        return self._maximum

    def start_value(self) -> int:
        """Retorna o índice inicial selecionado."""
        return self._start_value

    def end_value(self) -> int:
        """Retorna o índice final selecionado."""
        return self._end_value

    def current_value(self) -> int:
        """Retorna o índice atual do cursor de reprodução (playhead)."""
        return self._current_value

    def set_range_bounds(self, minimum: int, maximum: int) -> None:
        """Define os limites mínimo e máximo do controle deslizante."""
        self._minimum = max(0, int(minimum))
        self._maximum = max(self._minimum + 1, int(maximum))
        self._start_value = self._minimum
        self._end_value = self._maximum
        self._current_value = self._start_value
        self.update()

    def set_values(self, start_val: int, end_val: int, emit_signals: bool = False) -> None:
        """Atualiza os valores inicial e final garantindo consistência dos limites."""
        clamped_start = max(self._minimum, min(int(start_val), self._maximum - 1))
        clamped_end = max(clamped_start + 1, min(int(end_val), self._maximum))

        start_changed = clamped_start != self._start_value
        end_changed = clamped_end != self._end_value

        self._start_value = clamped_start
        self._end_value = clamped_end
        if self._current_value < self._start_value or self._current_value > self._end_value:
            self._current_value = self._start_value

        self.update()

        if emit_signals:
            if start_changed:
                self.start_value_changed.emit(self._start_value)
            if end_changed:
                self.end_value_changed.emit(self._end_value)
            if start_changed or end_changed:
                self.range_changed.emit(self._start_value, self._end_value)

    def set_current_value(self, current_val: int) -> None:
        """Define a posição do indicador de reprodução atual."""
        self._current_value = max(self._start_value, min(int(current_val), self._end_value))
        self.update()

    def _value_to_x(self, value: int) -> float:
        span = max(1, self._maximum - self._minimum)
        usable_w = max(1, self.width() - 2 * self._margin)
        ratio = (value - self._minimum) / span
        return self._margin + ratio * usable_w

    def _x_to_value(self, x_pos: float) -> int:
        usable_w = max(1, self.width() - 2 * self._margin)
        clamped_x = max(0.0, min(float(x_pos - self._margin), float(usable_w)))
        ratio = clamped_x / usable_w
        span = max(1, self._maximum - self._minimum)
        return int(round(self._minimum + ratio * span))

    def paintEvent(self, _event: object) -> None:
        """Renderiza a trilha, a faixa selecionada, o playhead e os dois cursores."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        mid_y = self.height() / 2.0
        track_h = 6.0
        usable_w = max(1.0, float(self.width() - 2 * self._margin))

        # Trilha de fundo
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#3f3f46"))
        painter.drawRoundedRect(
            QRectF(self._margin, mid_y - track_h / 2.0, usable_w, track_h),
            3.0,
            3.0,
        )

        start_x = self._value_to_x(self._start_value)
        end_x = self._value_to_x(self._end_value)
        curr_x = self._value_to_x(self._current_value)

        # Faixa ativa selecionada
        painter.setBrush(QColor("#10b981"))
        painter.drawRoundedRect(
            QRectF(start_x, mid_y - track_h / 2.0, max(2.0, end_x - start_x), track_h),
            3.0,
            3.0,
        )

        # Marcador do quadro atual (playhead)
        painter.setPen(QPen(QColor("#38bdf8"), 2.0))
        painter.drawLine(int(curr_x), int(mid_y - 9), int(curr_x), int(mid_y + 9))

        # Cursores de Início e Fim
        for handle_name, hx in (("start", start_x), ("end", end_x)):
            is_active = self._active_handle == handle_name
            fill_color = QColor("#10b981") if is_active else QColor("#f4f4f5")
            border_color = QColor("#ffffff") if is_active else QColor("#059669")
            painter.setPen(QPen(border_color, 2.0))
            painter.setBrush(fill_color)
            r = float(self._handle_radius)
            painter.drawEllipse(QRectF(hx - r, mid_y - r, r * 2.0, r * 2.0))

        painter.end()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Seleciona o cursor mais próximo do clique e atualiza o valor."""
        if event.button() != Qt.MouseButton.LeftButton:
            return
        click_x = event.position().x()
        start_x = self._value_to_x(self._start_value)
        end_x = self._value_to_x(self._end_value)

        if abs(click_x - start_x) <= abs(click_x - end_x):
            self._active_handle = "start"
        else:
            self._active_handle = "end"

        self._update_from_mouse(click_x)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Arrasta o cursor ativo mantendo os limites do intervalo."""
        if self._active_handle is not None:
            self._update_from_mouse(event.position().x())

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Finaliza o arraste do cursor."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._active_handle = None
            self.update()

    def _update_from_mouse(self, x_pos: float) -> None:
        new_val = self._x_to_value(x_pos)
        if self._active_handle == "start":
            clamped = max(self._minimum, min(new_val, self._end_value - 1))
            if clamped != self._start_value:
                self._start_value = clamped
                self._current_value = clamped
                self.update()
                self.start_value_changed.emit(self._start_value)
                self.range_changed.emit(self._start_value, self._end_value)
        elif self._active_handle == "end":
            clamped = max(self._start_value + 1, min(new_val, self._maximum))
            if clamped != self._end_value:
                self._end_value = clamped
                self._current_value = clamped
                self.update()
                self.end_value_changed.emit(self._end_value)
                self.range_changed.emit(self._start_value, self._end_value)
