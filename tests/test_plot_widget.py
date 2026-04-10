import math
import unittest

from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QApplication

from eqnplot.models import PlotOptions
from eqnplot.parser import ExpressionParser
from eqnplot.plot_widget import PlotWidget


class PlotWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.widget = PlotWidget()
        self.widget.resize(640, 420)
        function = ExpressionParser().parse("sin(x)")
        self.widget.set_plot(function, PlotOptions(expression="sin(x)", x_min=-10, x_max=10))

    def tearDown(self):
        self.widget.close()
        self.widget.deleteLater()

    def test_current_x_range_reflects_plot_state(self):
        self.assertEqual(self.widget.current_x_range(), (-10, 10))

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
        self.assertIn("y =", captured[-1])

    def test_cursor_value_signal_handles_undefined_value(self):
        widget = PlotWidget()
        widget.resize(640, 420)
        function = ExpressionParser().parse("1/x")
        widget.set_plot(function, PlotOptions(expression="1/x", x_min=-1, x_max=1))
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
        widget.set_plot(counted, PlotOptions(expression="x", x_min=-10, x_max=10))
        plot_rect = widget._plot_area()

        widget._get_render_data(plot_rect)
        first_call_count = counter["calls"]
        widget._get_render_data(plot_rect)

        self.assertGreater(first_call_count, 0)
        self.assertEqual(counter["calls"], first_call_count)
        widget.close()
        widget.deleteLater()

    def test_simplify_samples_reduces_dense_draw_points(self):
        plot_rect = self.widget._plot_area()
        dense_samples = [(index * 0.001, math.sin(index * 0.001)) for index in range(5000)]

        simplified = self.widget._simplify_samples_for_drawing(dense_samples, plot_rect, -1.2, 1.2)

        self.assertLess(len(simplified), len(dense_samples))
        self.assertGreater(len(simplified), 0)


if __name__ == "__main__":
    unittest.main()
