import math
from dataclasses import replace
from typing import Callable, List, Optional, Sequence, Tuple

from PyQt5.QtCore import QPoint, QPointF, QRectF, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QImage, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QWidget

from eqnplot.models import PlotOptions


PointData = Tuple[float, Optional[float]]


class PlotWidget(QWidget):
    viewport_changed = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 420)
        self._plot_options: Optional[PlotOptions] = None
        self._plot_function: Optional[Callable[[float], float]] = None
        self._status_message = "Saisissez une equation puis cliquez sur Tracer."
        self._dragging = False
        self._last_drag_pos: Optional[QPoint] = None
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)

    def set_plot(self, plot_function: Callable[[float], float], options: PlotOptions) -> None:
        self._plot_function = plot_function
        self._plot_options = options
        self._status_message = ""
        self.update()

    def clear_plot(self, message: str) -> None:
        self._plot_function = None
        self._plot_options = None
        self._status_message = message
        self.update()

    def export_png(self, path: str) -> bool:
        image = QImage(self.size(), QImage.Format_ARGB32)
        image.fill(Qt.white)
        painter = QPainter(image)
        try:
            self._paint_contents(painter)
        finally:
            painter.end()
        return image.save(path, "PNG")

    def has_plot(self) -> bool:
        return self._plot_function is not None and self._plot_options is not None

    def current_x_range(self) -> Optional[Tuple[float, float]]:
        if self._plot_options is None:
            return None
        return (self._plot_options.x_min, self._plot_options.x_max)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        try:
            self._paint_contents(painter)
        finally:
            painter.end()

    def mousePressEvent(self, event):  # noqa: N802
        if (
            event.button() == Qt.LeftButton
            and self.has_plot()
            and self._plot_area().contains(event.pos())
        ):
            self._dragging = True
            self._last_drag_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):  # noqa: N802
        if self._dragging and self._last_drag_pos is not None and self._plot_options is not None:
            plot_rect = self._plot_area()
            if plot_rect.width() <= 0:
                return
            delta_pixels = event.pos().x() - self._last_drag_pos.x()
            if delta_pixels != 0:
                x_span = self._plot_options.x_max - self._plot_options.x_min
                delta_x = (delta_pixels / plot_rect.width()) * x_span
                self._set_x_range(
                    self._plot_options.x_min - delta_x,
                    self._plot_options.x_max - delta_x,
                )
                self._last_drag_pos = event.pos()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):  # noqa: N802
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            self._last_drag_pos = None
            self.setCursor(Qt.CrossCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):  # noqa: N802
        if not self._dragging:
            self.setCursor(Qt.CrossCursor)
        super().leaveEvent(event)

    def wheelEvent(self, event):  # noqa: N802
        if not self.has_plot() or self._plot_options is None:
            super().wheelEvent(event)
            return

        plot_rect = self._plot_area()
        if not plot_rect.contains(event.pos()):
            super().wheelEvent(event)
            return

        angle_delta = event.angleDelta().y()
        if angle_delta == 0 or plot_rect.width() <= 0:
            event.accept()
            return

        zoom_factor = 0.85 if angle_delta > 0 else 1.15
        x_min = self._plot_options.x_min
        x_max = self._plot_options.x_max
        x_span = x_max - x_min
        cursor_ratio = (event.pos().x() - plot_rect.left()) / plot_rect.width()
        cursor_ratio = min(max(cursor_ratio, 0.0), 1.0)
        anchor_x = x_min + cursor_ratio * x_span

        new_span = x_span * zoom_factor
        min_span = 1e-6
        max_span = 1e9
        new_span = min(max(new_span, min_span), max_span)

        new_x_min = anchor_x - cursor_ratio * new_span
        new_x_max = new_x_min + new_span
        self._set_x_range(new_x_min, new_x_max)
        event.accept()

    def _paint_contents(self, painter: QPainter) -> None:
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect()
        painter.fillRect(rect, Qt.white)

        if not self._plot_function or not self._plot_options:
            painter.setPen(QColor("#555555"))
            painter.drawText(rect, Qt.AlignCenter, self._status_message)
            return

        plot_rect = self._plot_area()
        if plot_rect.width() <= 0 or plot_rect.height() <= 0:
            return

        samples = self._sample_points(plot_rect.width())
        y_values = [y for _, y in samples if y is not None and math.isfinite(y)]

        if not y_values:
            painter.setPen(QColor("#aa0000"))
            painter.drawText(rect, Qt.AlignCenter, "Aucune valeur exploitable sur cet intervalle.")
            return

        y_min = min(y_values)
        y_max = max(y_values)
        if math.isclose(y_min, y_max, rel_tol=1e-9, abs_tol=1e-9):
            margin = 1.0 if math.isclose(y_min, 0.0, abs_tol=1e-9) else abs(y_min) * 0.1
            y_min -= margin
            y_max += margin
        else:
            padding = (y_max - y_min) * 0.08
            y_min -= padding
            y_max += padding

        if self._plot_options.show_grid:
            self._draw_grid(painter, plot_rect, y_min, y_max)

        if self._plot_options.show_axes:
            self._draw_axes(painter, plot_rect, y_min, y_max)

        self._draw_curve(painter, plot_rect, samples, y_min, y_max)
        painter.setPen(QColor("#444444"))
        painter.drawRect(plot_rect)

    def _plot_area(self) -> QRectF:
        return self.rect().adjusted(18, 18, -18, -18)

    def _set_x_range(self, x_min: float, x_max: float) -> None:
        if self._plot_options is None:
            return
        if not math.isfinite(x_min) or not math.isfinite(x_max) or x_min >= x_max:
            return
        self._plot_options = replace(self._plot_options, x_min=x_min, x_max=x_max)
        self.viewport_changed.emit(x_min, x_max)
        self.update()

    def _sample_points(self, pixel_width: int) -> List[PointData]:
        assert self._plot_function is not None
        assert self._plot_options is not None
        sample_count = max(300, pixel_width * 2)
        x_min = self._plot_options.x_min
        x_max = self._plot_options.x_max
        step = (x_max - x_min) / (sample_count - 1)
        points: List[PointData] = []

        for index in range(sample_count):
            x_value = x_min + index * step
            try:
                y_value = self._plot_function(x_value)
                if math.isfinite(y_value):
                    points.append((x_value, y_value))
                else:
                    points.append((x_value, None))
            except (ValueError, ZeroDivisionError, OverflowError):
                points.append((x_value, None))

        return points

    def _draw_grid(self, painter: QPainter, plot_rect: QRectF, y_min: float, y_max: float) -> None:
        assert self._plot_options is not None
        grid_pen = QPen(QColor(self._plot_options.grid_color), 1)
        grid_pen.setStyle(Qt.DashLine)
        painter.setPen(grid_pen)

        for x_tick in self._generate_ticks(self._plot_options.x_min, self._plot_options.x_max):
            x_pos = self._map_x(x_tick, plot_rect)
            painter.drawLine(QPointF(x_pos, plot_rect.top()), QPointF(x_pos, plot_rect.bottom()))

        for y_tick in self._generate_ticks(y_min, y_max):
            y_pos = self._map_y(y_tick, plot_rect, y_min, y_max)
            painter.drawLine(QPointF(plot_rect.left(), y_pos), QPointF(plot_rect.right(), y_pos))

    def _draw_axes(self, painter: QPainter, plot_rect: QRectF, y_min: float, y_max: float) -> None:
        assert self._plot_options is not None
        axis_pen = QPen(QColor(self._plot_options.axis_color), 1.5)
        painter.setPen(axis_pen)

        if self._plot_options.x_min <= 0 <= self._plot_options.x_max:
            x_zero = self._map_x(0.0, plot_rect)
            painter.drawLine(QPointF(x_zero, plot_rect.top()), QPointF(x_zero, plot_rect.bottom()))

        if y_min <= 0 <= y_max:
            y_zero = self._map_y(0.0, plot_rect, y_min, y_max)
            painter.drawLine(QPointF(plot_rect.left(), y_zero), QPointF(plot_rect.right(), y_zero))

    def _draw_curve(
        self,
        painter: QPainter,
        plot_rect: QRectF,
        samples: Sequence[PointData],
        y_min: float,
        y_max: float,
    ) -> None:
        assert self._plot_options is not None
        curve_pen = QPen(QColor(self._plot_options.curve_color), 2)
        painter.setPen(curve_pen)

        path = QPainterPath()
        drawing_segment = False

        for x_value, y_value in samples:
            if y_value is None:
                drawing_segment = False
                continue

            if y_value < y_min - (y_max - y_min) * 5 or y_value > y_max + (y_max - y_min) * 5:
                drawing_segment = False
                continue

            point = QPointF(
                self._map_x(x_value, plot_rect),
                self._map_y(y_value, plot_rect, y_min, y_max),
            )

            if not drawing_segment:
                path.moveTo(point)
                drawing_segment = True
            else:
                path.lineTo(point)

        painter.drawPath(path)

    def _map_x(self, x_value: float, plot_rect: QRectF) -> float:
        assert self._plot_options is not None
        x_min = self._plot_options.x_min
        x_max = self._plot_options.x_max
        span = x_max - x_min
        if math.isclose(span, 0.0):
            return plot_rect.center().x()
        return plot_rect.left() + ((x_value - x_min) / span) * plot_rect.width()

    @staticmethod
    def _map_y(y_value: float, plot_rect: QRectF, y_min: float, y_max: float) -> float:
        span = y_max - y_min
        if math.isclose(span, 0.0):
            return plot_rect.center().y()
        return plot_rect.bottom() - ((y_value - y_min) / span) * plot_rect.height()

    @staticmethod
    def _generate_ticks(min_value: float, max_value: float, target_count: int = 8) -> List[float]:
        span = max_value - min_value
        if span <= 0:
            return []

        raw_step = span / target_count
        magnitude = 10 ** math.floor(math.log10(raw_step))
        normalized = raw_step / magnitude
        if normalized < 1.5:
            step = 1 * magnitude
        elif normalized < 3:
            step = 2 * magnitude
        elif normalized < 7:
            step = 5 * magnitude
        else:
            step = 10 * magnitude

        first_tick = math.ceil(min_value / step) * step
        ticks = []
        value = first_tick
        guard = 0
        while value <= max_value + step * 0.5 and guard < 1000:
            ticks.append(value)
            value += step
            guard += 1
        return ticks
