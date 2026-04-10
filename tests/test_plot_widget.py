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


if __name__ == "__main__":
    unittest.main()
