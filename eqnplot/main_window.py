import sys
from typing import Callable, Tuple

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from eqnplot.models import PlotOptions
from eqnplot.parser import ExpressionError, ExpressionParser
from eqnplot.plot_widget import PlotWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EqnPlot")
        self.resize(980, 680)

        self._parser = ExpressionParser()
        self._curve_color = "#d1495b"
        self._axis_color = "#222222"
        self._grid_color = "#c8d5dd"

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        control_panel = self._build_controls()
        self.plot_widget = PlotWidget()
        self.plot_widget.viewport_changed.connect(self._sync_range_inputs)
        self.plot_widget.cursor_value_changed.connect(self._sync_cursor_value)

        layout.addWidget(control_panel, 0)
        layout.addWidget(self.plot_widget, 1)

        self._apply_defaults()

    def _build_controls(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(280)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setSpacing(12)

        form_group = QGroupBox("Equation")
        form_layout = QFormLayout(form_group)

        self.expression_input = QLineEdit("sin(x)")
        self.expression_input.setPlaceholderText("Ex: sin(x) ou x**2")
        self.expression_input.editingFinished.connect(self.plot_expression)
        self.expression_input.returnPressed.connect(self.plot_expression)
        form_layout.addRow("y =", self.expression_input)

        self.x_min_input = QLineEdit("-10")
        self.x_max_input = QLineEdit("10")
        self.x_min_input.editingFinished.connect(self.plot_expression)
        self.x_min_input.returnPressed.connect(self.plot_expression)
        self.x_max_input.editingFinished.connect(self.plot_expression)
        self.x_max_input.returnPressed.connect(self.plot_expression)
        form_layout.addRow("x min", self.x_min_input)
        form_layout.addRow("x max", self.x_max_input)

        display_group = QGroupBox("Affichage")
        display_layout = QVBoxLayout(display_group)

        self.axes_checkbox = QCheckBox("Afficher les axes")
        self.axes_checkbox.setChecked(True)
        self.grid_checkbox = QCheckBox("Afficher la grille")
        self.grid_checkbox.setChecked(True)
        self.axis_labels_checkbox = QCheckBox("Afficher les valeurs des axes")
        self.axis_labels_checkbox.setChecked(True)
        self.axes_checkbox.toggled.connect(self.plot_expression)
        self.grid_checkbox.toggled.connect(self.plot_expression)
        self.axis_labels_checkbox.toggled.connect(self.plot_expression)
        display_layout.addWidget(self.axes_checkbox)
        display_layout.addWidget(self.grid_checkbox)
        display_layout.addWidget(self.axis_labels_checkbox)

        color_group = QGroupBox("Couleurs")
        color_layout = QGridLayout(color_group)

        self.curve_color_button = QPushButton("Courbe")
        self.axis_color_button = QPushButton("Axes")
        self.grid_color_button = QPushButton("Grille")
        self.curve_color_button.clicked.connect(lambda: self._pick_color("curve"))
        self.axis_color_button.clicked.connect(lambda: self._pick_color("axis"))
        self.grid_color_button.clicked.connect(lambda: self._pick_color("grid"))

        color_layout.addWidget(QLabel("Courbe"), 0, 0)
        color_layout.addWidget(self.curve_color_button, 0, 1)
        color_layout.addWidget(QLabel("Axes"), 1, 0)
        color_layout.addWidget(self.axis_color_button, 1, 1)
        color_layout.addWidget(QLabel("Grille"), 2, 0)
        color_layout.addWidget(self.grid_color_button, 2, 1)

        actions_layout = QHBoxLayout()
        self.plot_button = QPushButton("Tracer")
        self.save_button = QPushButton("Sauvegarder")
        self.plot_button.clicked.connect(self.plot_expression)
        self.save_button.clicked.connect(self.save_plot)
        actions_layout.addWidget(self.plot_button)
        actions_layout.addWidget(self.save_button)

        self.status_label = QLabel("Pret.")
        self.status_label.setWordWrap(True)
        self.cursor_value_label = QLabel("")
        self.cursor_value_label.setWordWrap(True)

        panel_layout.addWidget(form_group)
        panel_layout.addWidget(display_group)
        panel_layout.addWidget(color_group)
        panel_layout.addLayout(actions_layout)
        panel_layout.addWidget(self.status_label)
        panel_layout.addWidget(self.cursor_value_label)
        panel_layout.addStretch(1)

        return panel

    def _apply_defaults(self) -> None:
        self._update_color_button(self.curve_color_button, self._curve_color)
        self._update_color_button(self.axis_color_button, self._axis_color)
        self._update_color_button(self.grid_color_button, self._grid_color)
        self.plot_expression()

    def _pick_color(self, role: str) -> None:
        current_color = {
            "curve": self._curve_color,
            "axis": self._axis_color,
            "grid": self._grid_color,
        }[role]
        chosen = QColorDialog.getColor(QColor(current_color), self, "Choisir une couleur")
        if not chosen.isValid():
            return

        color_name = chosen.name()
        if role == "curve":
            self._curve_color = color_name
            self._update_color_button(self.curve_color_button, color_name)
        elif role == "axis":
            self._axis_color = color_name
            self._update_color_button(self.axis_color_button, color_name)
        else:
            self._grid_color = color_name
            self._update_color_button(self.grid_color_button, color_name)

    def _read_options(self) -> Tuple[PlotOptions, Callable[[float], float]]:
        expression = self.expression_input.text().strip()
        if not expression:
            raise ExpressionError("Veuillez saisir une equation.")

        try:
            x_min = float(self.x_min_input.text())
            x_max = float(self.x_max_input.text())
        except ValueError as exc:
            raise ExpressionError("Les bornes x doivent etre numeriques.") from exc

        if x_min >= x_max:
            raise ExpressionError("x min doit etre strictement inferieur a x max.")

        plot_function = self._parser.parse(expression)
        options = PlotOptions(
            expression=expression,
            x_min=x_min,
            x_max=x_max,
            show_axes=self.axes_checkbox.isChecked(),
            show_grid=self.grid_checkbox.isChecked(),
            show_axis_labels=self.axis_labels_checkbox.isChecked(),
            curve_color=self._curve_color,
            axis_color=self._axis_color,
            grid_color=self._grid_color,
        )
        return options, plot_function

    def plot_expression(self) -> None:
        try:
            options, plot_function = self._read_options()
        except ExpressionError as exc:
            self.plot_widget.clear_plot(str(exc))
            self.status_label.setText(str(exc))
            return

        self.plot_widget.set_plot(plot_function, options)
        self.status_label.setText(f"Trace de y = {options.expression} sur [{options.x_min}, {options.x_max}]")

    def save_plot(self) -> None:
        if not self.plot_widget.has_plot():
            QMessageBox.warning(self, "Aucun trace", "Veuillez d'abord tracer une equation.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer l'image",
            "graphique.png",
            "Images PNG (*.png)",
        )
        if not path:
            return

        if not path.lower().endswith(".png"):
            path += ".png"

        if self.plot_widget.export_png(path):
            self.status_label.setText(f"Image sauvegardee: {path}")
        else:
            QMessageBox.critical(self, "Erreur", "Impossible de sauvegarder l'image.")

    @staticmethod
    def _update_color_button(button: QPushButton, color_hex: str) -> None:
        button.setStyleSheet(
            "QPushButton {"
            f"background-color: {color_hex};"
            "border: 1px solid #999999;"
            "padding: 6px;"
            "}"
        )
        button.setText(color_hex)

    def _sync_range_inputs(self, x_min: float, x_max: float) -> None:
        self.x_min_input.setText(f"{x_min:.6g}")
        self.x_max_input.setText(f"{x_max:.6g}")
        if self.expression_input.text().strip():
            self.status_label.setText(
                f"Trace de y = {self.expression_input.text().strip()} sur [{x_min:.6g}, {x_max:.6g}]"
            )

    def _sync_cursor_value(self, text: str) -> None:
        self.cursor_value_label.setText(text)


def run() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
