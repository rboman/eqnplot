import math
import unittest

from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QApplication

from eqnplot.models import CurveSpec, PlotOptions
from eqnplot.parser import ExpressionParser
from eqnplot.plot_widget import PlotWidget


def build_options(expression: str, x_min: float, x_max: float) -> PlotOptions:
    return PlotOptions(curves=[CurveSpec(expression=expression, color="#d1495b")], x_min=x_min, x_max=x_max)


class PlotWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.widget = PlotWidget()
        self.widget.resize(640, 420)
        function = ExpressionParser().parse("sin(x)")
        self.widget.set_plot([function], build_options("sin(x)", -10, 10))

    def tearDown(self):
        self.widget.close()
        self.widget.deleteLater()

    def test_current_x_range_reflects_plot_state(self):
        self.assertEqual(self.widget.current_x_range(), (-10, 10))
        self.assertTrue(self.widget._plot_options.use_optimized_render)

    def test_set_x_range_emits_signal_and_updates_state(self):
        captured = []
        self.widget.viewport_changed.connect(lambda x_min, x_max: captured.append((x_min, x_max)))

        self.widget._set_x_range(-5, 5)

        self.assertEqual(self.widget.current_x_range(), (-5, 5))
        self.assertEqual(captured, [(-5, 5)])

    def test_cursor_value_signal_reports_function_value(self):
        captured = []
        self.widget.cursor_value_changed.connect(captured.append)
        self.widget._hover_pos = QPoint(320, 200)

        self.widget._emit_cursor_value()

        self.assertTrue(captured)
        self.assertIn("x =", captured[-1])
        self.assertIn("sin(x) =", captured[-1])

    def test_cursor_value_signal_handles_undefined_value(self):
        widget = PlotWidget()
        widget.resize(640, 420)
        function = ExpressionParser().parse("1/x")
        widget.set_plot([function], build_options("1/x", -1, 1))
        captured = []
        widget.cursor_value_changed.connect(captured.append)
        widget._hover_pos = QPoint(320, 200)

        widget._emit_cursor_value()

        self.assertTrue(captured)
        self.assertIn("indefini", captured[-1])
        widget.close()
        widget.deleteLater()

    def test_render_data_is_cached_for_same_plot_area(self):
        counter = {"calls": 0}

        def counted(x_value):
            counter["calls"] += 1
            return x_value

        widget = PlotWidget()
        widget.resize(640, 420)
        widget.set_plot([counted], build_options("x", -10, 10))
        plot_rect = widget._plot_area()

        widget._get_render_data(plot_rect)
        first_call_count = counter["calls"]
        widget._get_render_data(plot_rect)

        self.assertGreater(first_call_count, 0)
        self.assertEqual(counter["calls"], first_call_count)
        widget.close()
        widget.deleteLater()

    def test_sample_count_depends_only_on_pixel_width(self):
        self.assertEqual(self.widget._sample_count_for_width(604), 3020)
        self.assertEqual(self.widget._sample_count_for_width(12), 60)

    def test_sampling_cost_is_independent_from_x_range(self):
        counts = []

        def counted(x_value):
            counts[-1] += 1
            return x_value

        widget = PlotWidget()
        widget.resize(640, 420)
        plot_rect = widget._plot_area()

        counts.append(0)
        widget.set_plot([counted], build_options("x", -10, 10))
        widget._get_render_data(plot_rect)
        first_count = counts[-1]

        counts.append(0)
        widget.set_plot([counted], build_options("x", -1000, 1000))
        widget._get_render_data(plot_rect)
        second_count = counts[-1]

        self.assertEqual(first_count, second_count)
        self.assertEqual(first_count, widget._sample_count_for_width(int(plot_rect.width())))
        widget.close()
        widget.deleteLater()

    def test_simplify_samples_reduces_dense_draw_points(self):
        plot_rect = self.widget._plot_area()
        dense_samples = [(index * 0.001, math.sin(index * 0.001)) for index in range(5000)]

        simplified = self.widget._simplify_samples_for_drawing(dense_samples, plot_rect, -1.2, 1.2)

        self.assertLess(len(simplified), len(dense_samples))
        self.assertGreater(len(simplified), 0)

    def test_dense_column_renderer_groups_points_by_pixel(self):
        plot_rect = self.widget._plot_area()
        samples = [(0.0, -1.0), (0.001, 0.0), (0.002, 1.0)]

        columns = {}
        for x_value, y_value in samples:
            pixel_x = int(round(self.widget._map_x(x_value, plot_rect)))
            pixel_y = self.widget._map_y(y_value, plot_rect, -1.2, 1.2)
            bucket = columns.setdefault(pixel_x, [pixel_y, pixel_y])
            bucket[0] = min(bucket[0], pixel_y)
            bucket[1] = max(bucket[1], pixel_y)

        self.assertEqual(len(columns), 1)
        min_y, max_y = next(iter(columns.values()))
        self.assertLess(min_y, max_y)

    def test_multi_curve_cursor_report_contains_each_expression(self):
        widget = PlotWidget()
        widget.resize(640, 420)
        parser = ExpressionParser()
        widget.set_plot(
            [parser.parse("sin(x)"), parser.parse("cos(x)")],
            PlotOptions(
                curves=[
                    CurveSpec(expression="sin(x)", color="#d1495b"),
                    CurveSpec(expression="cos(x)", color="#2563eb"),
                ],
                x_min=-10,
                x_max=10,
            ),
        )
        captured = []
        widget.cursor_value_changed.connect(captured.append)
        widget._hover_pos = QPoint(320, 200)

        widget._emit_cursor_value()

        self.assertTrue(captured)
        self.assertIn("sin(x) =", captured[-1])
        self.assertIn("cos(x) =", captured[-1])
        widget.close()
        widget.deleteLater()


if __name__ == "__main__":
    unittest.main()
