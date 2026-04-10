import unittest

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


if __name__ == "__main__":
    unittest.main()
