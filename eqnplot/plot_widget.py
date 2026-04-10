import math
from dataclasses import dataclass, replace
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from PyQt5.QtCore import QPoint, QPointF, QRect, QRectF, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QPolygonF
from PyQt5.QtWidgets import QWidget

from eqnplot.models import PlotOptions


PointData = Tuple[float, Optional[float]]


@dataclass
class RenderData:
    samples: List[PointData]
    y_min: float
    y_max: float


class PlotWidget(QWidget):
    viewport_changed = pyqtSignal(float, float)
    cursor_value_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(640, 420)
        self._plot_options: Optional[PlotOptions] = None
        self._plot_function: Optional[Callable[[float], float]] = None
        self._status_message = "Saisissez une equation puis cliquez sur Tracer."
        self._dragging = False
        self._last_drag_pos: Optional[QPoint] = None
        self._hover_pos: Optional[QPoint] = None
        self._render_cache: Optional[RenderData] = None
        self._render_cache_size: Optional[Tuple[int, int]] = None
        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)

    def set_plot(self, plot_function: Callable[[float], float], options: PlotOptions) -> None:
        self._plot_function = plot_function
        self._plot_options = options
        self._status_message = ""
        self._hover_pos = None
        self._invalidate_render_cache()
        self.update()

    def clear_plot(self, message: str) -> None:
        self._plot_function = None
        self._plot_options = None
        self._status_message = message
        self._hover_pos = None
        self._invalidate_render_cache()
        self.cursor_value_changed.emit("")
        self.update()

    def export_png(self, path: str) -> bool:
        image = QImage(self.size(), QImage.Format_ARGB32)
        fill_color = QColor(self._plot_options.background_color) if self._plot_options else QColor("#ffffff")
        image.fill(fill_color)
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

        if self.has_plot() and self._plot_area().contains(event.pos()):
            self._hover_pos = event.pos()
            self._emit_cursor_value()
            self.update()
            event.accept()
            return

        self._hover_pos = None
        self.cursor_value_changed.emit("")
        self.update()
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
        self._hover_pos = None
        self.cursor_value_changed.emit("")
        self.update()
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
        background = QColor(self._plot_options.background_color) if self._plot_options else QColor("#ffffff")
        painter.fillRect(rect, background)
        accent_color = QColor(self._plot_options.axis_color) if self._plot_options else QColor("#444444")

        if not self._plot_function or not self._plot_options:
            painter.setPen(accent_color)
            painter.drawText(rect, Qt.AlignCenter, self._status_message)
            return

        plot_rect = self._plot_area()
        if plot_rect.width() <= 0 or plot_rect.height() <= 0:
            return

        render_data = self._get_render_data(plot_rect)
        if render_data is None:
            painter.setPen(QColor("#aa0000"))
            painter.drawText(rect, Qt.AlignCenter, "Aucune valeur exploitable sur cet intervalle.")
            return
        samples = render_data.samples
        y_min = render_data.y_min
        y_max = render_data.y_max

        if self._plot_options.show_grid:
            self._draw_grid(painter, plot_rect, y_min, y_max)

        if self._plot_options.show_axes:
            self._draw_axes(painter, plot_rect, y_min, y_max)

        if self._plot_options.show_axis_labels:
            self._draw_axis_labels(painter, plot_rect, y_min, y_max)

        self._draw_curve(painter, plot_rect, samples, y_min, y_max)
        self._draw_hover_indicator(painter, plot_rect, y_min, y_max)
        painter.setPen(accent_color)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(plot_rect)

    def _plot_area(self) -> QRectF:
        return self.rect().adjusted(18, 18, -18, -18)

    def _set_x_range(self, x_min: float, x_max: float) -> None:
        if self._plot_options is None:
            return
        if not math.isfinite(x_min) or not math.isfinite(x_max) or x_min >= x_max:
            return
        self._plot_options = replace(self._plot_options, x_min=x_min, x_max=x_max)
        self._invalidate_render_cache()
        self.viewport_changed.emit(x_min, x_max)
        self._emit_cursor_value()
        self.update()

    def resizeEvent(self, event):  # noqa: N802
        self._invalidate_render_cache()
        super().resizeEvent(event)

    def _sample_points(self, pixel_width: int) -> List[PointData]:
        assert self._plot_function is not None
        assert self._plot_options is not None
        sample_count = self._sample_count_for_width(pixel_width)
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

    @staticmethod
    def _sample_count_for_width(pixel_width: int) -> int:
        return max(2, int(round(pixel_width)) * 5)

    def _get_render_data(self, plot_rect: QRectF) -> Optional[RenderData]:
        cache_size = (int(plot_rect.width()), int(plot_rect.height()))
        if self._render_cache is not None and self._render_cache_size == cache_size:
            return self._render_cache

        samples = self._sample_points(plot_rect.width())
        y_values = [y for _, y in samples if y is not None and math.isfinite(y)]
        if not y_values:
            self._render_cache = None
            self._render_cache_size = cache_size
            return None

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

        self._render_cache = RenderData(samples=samples, y_min=y_min, y_max=y_max)
        self._render_cache_size = cache_size
        return self._render_cache

    def _invalidate_render_cache(self) -> None:
        self._render_cache = None
        self._render_cache_size = None

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

    def _draw_axis_labels(self, painter: QPainter, plot_rect: QRectF, y_min: float, y_max: float) -> None:
        assert self._plot_options is not None
        painter.setPen(QColor(self._plot_options.axis_color))
        font_metrics = painter.fontMetrics()
        x_axis_y = self._label_x_axis_y(plot_rect, y_min, y_max)
        y_axis_x = self._label_y_axis_x(plot_rect)

        for x_tick in self._generate_ticks(self._plot_options.x_min, self._plot_options.x_max):
            x_pos = self._map_x(x_tick, plot_rect)
            label = self._format_tick(x_tick)
            text_width = font_metrics.horizontalAdvance(label)
            text_rect = QRect(
                int(x_pos - text_width / 2 - 2),
                int(x_axis_y + 4),
                text_width + 4,
                font_metrics.height(),
            )
            if plot_rect.left() <= text_rect.center().x() <= plot_rect.right():
                painter.drawText(text_rect, Qt.AlignCenter, label)

        for y_tick in self._generate_ticks(y_min, y_max):
            y_pos = self._map_y(y_tick, plot_rect, y_min, y_max)
            label = self._format_tick(y_tick)
            text_width = font_metrics.horizontalAdvance(label)
            text_rect = QRect(
                int(y_axis_x - text_width - 8),
                int(y_pos - font_metrics.height() / 2),
                text_width + 4,
                font_metrics.height(),
            )
            if plot_rect.top() <= y_pos <= plot_rect.bottom():
                painter.drawText(text_rect, Qt.AlignRight | Qt.AlignVCenter, label)

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

        if not self._plot_options.use_optimized_render:
            self._draw_curve_smooth_path(painter, plot_rect, samples, y_min, y_max)
            return

        if len(samples) > int(plot_rect.width()) * 3:
            self._draw_dense_curve_by_columns(painter, plot_rect, samples, y_min, y_max)
            return

        simplified_samples = self._simplify_samples_for_drawing(samples, plot_rect, y_min, y_max)
        current_segment = QPolygonF()

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

        for x_value, y_value in simplified_samples:
            if y_value is None:
                if current_segment.size() >= 2:
                    painter.drawPolyline(current_segment)
                elif current_segment.size() == 1:
                    painter.drawPoint(current_segment[0])
                current_segment = QPolygonF()
                continue

            if y_value < y_min - (y_max - y_min) * 5 or y_value > y_max + (y_max - y_min) * 5:
                if current_segment.size() >= 2:
                    painter.drawPolyline(current_segment)
                elif current_segment.size() == 1:
                    painter.drawPoint(current_segment[0])
                current_segment = QPolygonF()
                continue

            point = QPointF(
                self._map_x(x_value, plot_rect),
                self._map_y(y_value, plot_rect, y_min, y_max),
            )
            current_segment.append(point)

        if current_segment.size() >= 2:
            painter.drawPolyline(current_segment)
        elif current_segment.size() == 1:
            painter.drawPoint(current_segment[0])

        painter.restore()

    def _draw_curve_smooth_path(
        self,
        painter: QPainter,
        plot_rect: QRectF,
        samples: Sequence[PointData],
        y_min: float,
        y_max: float,
    ) -> None:
        path = QPainterPath()
        drawing_segment = False

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)

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
        painter.restore()

    def _draw_dense_curve_by_columns(
        self,
        painter: QPainter,
        plot_rect: QRectF,
        samples: Sequence[PointData],
        y_min: float,
        y_max: float,
    ) -> None:
        columns: Dict[int, List[float]] = {}
        x_out_of_range_margin = (y_max - y_min) * 5

        for x_value, y_value in samples:
            if y_value is None:
                continue
            if y_value < y_min - x_out_of_range_margin or y_value > y_max + x_out_of_range_margin:
                continue
            pixel_x = int(round(self._map_x(x_value, plot_rect)))
            if pixel_x < int(plot_rect.left()) or pixel_x > int(plot_rect.right()):
                continue
            pixel_y = self._map_y(y_value, plot_rect, y_min, y_max)
            bucket = columns.setdefault(pixel_x, [pixel_y, pixel_y])
            if pixel_y < bucket[0]:
                bucket[0] = pixel_y
            if pixel_y > bucket[1]:
                bucket[1] = pixel_y

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)
        for pixel_x in sorted(columns):
            min_y, max_y = columns[pixel_x]
            if math.isclose(min_y, max_y, abs_tol=0.5):
                painter.drawPoint(QPointF(pixel_x, min_y))
            else:
                painter.drawLine(QPointF(pixel_x, min_y), QPointF(pixel_x, max_y))
        painter.restore()

    def _simplify_samples_for_drawing(
        self,
        samples: Sequence[PointData],
        plot_rect: QRectF,
        y_min: float,
        y_max: float,
    ) -> List[PointData]:
        if len(samples) <= max(300, int(plot_rect.width()) * 3):
            return list(samples)

        simplified: List[PointData] = []
        current_pixel_x: Optional[int] = None
        current_bucket: List[PointData] = []

        for sample in samples:
            x_value, y_value = sample
            if y_value is None:
                simplified.extend(self._flush_bucket(current_bucket, y_min, y_max))
                current_bucket = []
                current_pixel_x = None
                if not simplified or simplified[-1][1] is not None:
                    simplified.append((x_value, None))
                continue

            pixel_x = int(round(self._map_x(x_value, plot_rect)))
            if current_pixel_x is None or pixel_x == current_pixel_x:
                current_bucket.append(sample)
                current_pixel_x = pixel_x
                continue

            simplified.extend(self._flush_bucket(current_bucket, y_min, y_max))
            current_bucket = [sample]
            current_pixel_x = pixel_x

        simplified.extend(self._flush_bucket(current_bucket, y_min, y_max))
        return simplified

    @staticmethod
    def _flush_bucket(bucket: Sequence[PointData], y_min: float, y_max: float) -> List[PointData]:
        if not bucket:
            return []

        valid_points = [
            point for point in bucket
            if point[1] is not None and y_min - (y_max - y_min) * 5 <= point[1] <= y_max + (y_max - y_min) * 5
        ]
        if not valid_points:
            return [(bucket[0][0], None)]

        if len(valid_points) <= 2:
            return list(valid_points)

        lowest = min(valid_points, key=lambda point: point[1])
        highest = max(valid_points, key=lambda point: point[1])
        ordered = sorted(
            {valid_points[0], lowest, highest, valid_points[-1]},
            key=lambda point: point[0],
        )
        return ordered

    def _draw_hover_indicator(self, painter: QPainter, plot_rect: QRectF, y_min: float, y_max: float) -> None:
        if self._hover_pos is None or self._plot_options is None or self._plot_function is None:
            return
        if not plot_rect.contains(self._hover_pos):
            return

        x_value = self._pixel_to_x(self._hover_pos.x(), plot_rect)
        try:
            y_value = self._plot_function(x_value)
            if not math.isfinite(y_value):
                return
        except (ValueError, ZeroDivisionError, OverflowError):
            return

        if y_value < y_min or y_value > y_max:
            return

        x_pos = self._map_x(x_value, plot_rect)
        y_pos = self._map_y(y_value, plot_rect, y_min, y_max)

        guide_pen = QPen(QColor("#666666"), 1)
        guide_pen.setStyle(Qt.DotLine)
        painter.setPen(guide_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(QPointF(x_pos, plot_rect.top()), QPointF(x_pos, plot_rect.bottom()))
        painter.drawLine(QPointF(plot_rect.left(), y_pos), QPointF(plot_rect.right(), y_pos))

        painter.setPen(QPen(QColor(self._plot_options.curve_color), 2))
        painter.setBrush(QColor(self._plot_options.curve_color))
        painter.drawEllipse(QPointF(x_pos, y_pos), 4, 4)

    def _map_x(self, x_value: float, plot_rect: QRectF) -> float:
        assert self._plot_options is not None
        x_min = self._plot_options.x_min
        x_max = self._plot_options.x_max
        span = x_max - x_min
        if math.isclose(span, 0.0):
            return plot_rect.center().x()
        return plot_rect.left() + ((x_value - x_min) / span) * plot_rect.width()

    def _pixel_to_x(self, pixel_x: float, plot_rect: QRectF) -> float:
        assert self._plot_options is not None
        span = self._plot_options.x_max - self._plot_options.x_min
        if math.isclose(plot_rect.width(), 0.0):
            return self._plot_options.x_min
        ratio = (pixel_x - plot_rect.left()) / plot_rect.width()
        ratio = min(max(ratio, 0.0), 1.0)
        return self._plot_options.x_min + ratio * span

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

    def _emit_cursor_value(self) -> None:
        if (
            self._hover_pos is None
            or self._plot_options is None
            or self._plot_function is None
            or not self._plot_area().contains(self._hover_pos)
        ):
            self.cursor_value_changed.emit("")
            return

        x_value = self._pixel_to_x(self._hover_pos.x(), self._plot_area())
        try:
            y_value = self._plot_function(x_value)
            if not math.isfinite(y_value):
                raise ValueError
            self.cursor_value_changed.emit(
                f"x = {x_value:.6g}    y = {y_value:.6g}"
            )
        except (ValueError, ZeroDivisionError, OverflowError):
            self.cursor_value_changed.emit(f"x = {x_value:.6g}    y = indefini")

    @staticmethod
    def _format_tick(value: float) -> str:
        if math.isclose(value, 0.0, abs_tol=1e-12):
            value = 0.0
        return f"{value:.6g}"

    @staticmethod
    def _label_x_axis_y(plot_rect: QRectF, y_min: float, y_max: float) -> float:
        if y_min <= 0 <= y_max:
            return max(plot_rect.top(), min(plot_rect.bottom() - 18, PlotWidget._map_y(0.0, plot_rect, y_min, y_max)))
        return plot_rect.bottom() - 18

    @staticmethod
    def _label_y_axis_x(plot_rect: QRectF) -> float:
        return plot_rect.left() + 42
