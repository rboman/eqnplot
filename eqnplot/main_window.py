import sys
from typing import Callable, List, Sequence, Tuple

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QColorDialog,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from pathlib import Path
import ctypes

from eqnplot.models import CurveSpec, PlotOptions
from eqnplot.parser import ExpressionError, ExpressionParser
from eqnplot.plot_widget import PlotWidget

DEFAULT_EXPRESSION = "sin(x)"
DEFAULT_X_MIN = "-10"
DEFAULT_X_MAX = "10"
DEFAULT_SHOW_AXES = True
DEFAULT_SHOW_GRID = True
DEFAULT_SHOW_AXIS_LABELS = True
DEFAULT_SHOW_LEGEND = True
DEFAULT_OPTIMIZED_RENDER = False
DEFAULT_PALETTE = "Light"
MAX_HISTORY_ITEMS = 10
APP_ID = "OpenAI.Codex.EqnPlot"
DEFAULT_RECENT_EXPRESSIONS = [
    "sin(x)",
    "cos(x) * exp(-x**2 / 18)",
    "sin(3*x) / (1 + x**2 / 10)",
    "exp(-x**2 / 12) * (sin(4*x) + cos(2*x))",
    "sqrt(fabs(x)) * sin(2*x)",
]
LIGHT_CURVE_COLORS = [
    "#d1495b",
    "#2563eb",
    "#059669",
    "#d97706",
    "#7c3aed",
    "#0f766e",
    "#dc2626",
    "#0891b2",
    "#65a30d",
    "#ea580c",
]
DARK_CURVE_COLORS = [
    "#fb7185",
    "#60a5fa",
    "#34d399",
    "#fbbf24",
    "#a78bfa",
    "#22d3ee",
    "#f87171",
    "#2dd4bf",
    "#a3e635",
    "#fb923c",
]

PALETTES = {
    "Light": {
        "background": "#ffffff",
        "axis": "#222222",
        "grid": "#c8d5dd",
        "curves": LIGHT_CURVE_COLORS,
    },
    "Dark": {
        "background": "#111827",
        "axis": "#f3f4f6",
        "grid": "#334155",
        "curves": DARK_CURVE_COLORS,
    },
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EqnPlot")
        self.resize(1470, 680)
        self._settings = QSettings("EqnPlot", "EqnPlot")

        self._parser = ExpressionParser()
        self._background_color = PALETTES[DEFAULT_PALETTE]["background"]
        self._axis_color = PALETTES[DEFAULT_PALETTE]["axis"]
        self._grid_color = PALETTES[DEFAULT_PALETTE]["grid"]
        self._custom_background_color = self._background_color
        self._custom_axis_color = self._axis_color
        self._custom_grid_color = self._grid_color
        self._custom_curve_colors: List[str] = []
        self._color_labels = []

        icon = load_app_icon()
        if not icon.isNull():
            self.setWindowIcon(icon)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        control_panel = self._build_controls()
        self.plot_widget = PlotWidget()
        self.plot_widget.viewport_changed.connect(self._sync_range_inputs)

        layout.addWidget(control_panel, 0)
        layout.addWidget(self.plot_widget, 1)

        self._apply_defaults()

    def _build_controls(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(360)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setSpacing(12)

        form_group = QGroupBox("Equation")
        form_layout = QFormLayout(form_group)

        self.history_combo = QComboBox()
        self.history_combo.setToolTip("Retrouve rapidement une equation recente.")
        self.history_combo.currentTextChanged.connect(self._apply_history_expression)

        self.expression_input = QLineEdit(DEFAULT_EXPRESSION)
        self.expression_input.setPlaceholderText("Ex: sin(x) ou x**2")
        self.expression_input.setToolTip(
            "Entrez une expression en fonction de x, par exemple sin(x), x**2 ou exp(-x**2)."
        )
        self.expression_input.editingFinished.connect(self.plot_expression)
        self.expression_input.returnPressed.connect(self.plot_expression)
        form_layout.addRow("y =", self.expression_input)
        form_layout.addRow("Recents", self.history_combo)

        self.curve_list = QListWidget()
        self.curve_list.setToolTip(
            "Liste des courbes affichees. En mode Custom, double-cliquez une courbe pour changer sa couleur."
        )
        self.curve_list.currentTextChanged.connect(self._load_selected_curve)
        self.curve_list.itemDoubleClicked.connect(self._edit_curve_color)
        self.add_curve_button = QPushButton("Ajouter")
        self.add_curve_button.setToolTip("Ajoute l'expression courante a la liste des courbes.")
        self.add_curve_button.clicked.connect(self.add_curve)
        self.update_curve_button = QPushButton("Mettre a jour")
        self.update_curve_button.setToolTip("Remplace la courbe selectionnee par l'expression courante.")
        self.update_curve_button.clicked.connect(self.update_selected_curve)
        self.remove_curve_button = QPushButton("Supprimer")
        self.remove_curve_button.setToolTip("Supprime la courbe selectionnee.")
        self.remove_curve_button.clicked.connect(self.remove_selected_curve)
        self.clear_curves_button = QPushButton("Vider")
        self.clear_curves_button.setToolTip("Vide toute la liste de courbes.")
        self.clear_curves_button.clicked.connect(self.clear_curves)

        curve_actions_layout = QGridLayout()
        curve_actions_layout.setHorizontalSpacing(8)
        curve_actions_layout.setVerticalSpacing(8)
        curve_actions_layout.addWidget(self.add_curve_button, 0, 0)
        curve_actions_layout.addWidget(self.update_curve_button, 0, 1)
        curve_actions_layout.addWidget(self.remove_curve_button, 1, 0)
        curve_actions_layout.addWidget(self.clear_curves_button, 1, 1)

        form_layout.addRow("Courbes", self.curve_list)
        form_layout.addRow("", curve_actions_layout)

        self.x_min_input = QLineEdit(DEFAULT_X_MIN)
        self.x_max_input = QLineEdit(DEFAULT_X_MAX)
        self.x_min_input.setToolTip("Borne minimale de l'intervalle de trace sur l'axe X.")
        self.x_max_input.setToolTip("Borne maximale de l'intervalle de trace sur l'axe X.")
        self.x_min_input.editingFinished.connect(self.plot_expression)
        self.x_min_input.returnPressed.connect(self.plot_expression)
        self.x_max_input.editingFinished.connect(self.plot_expression)
        self.x_max_input.returnPressed.connect(self.plot_expression)
        self.expression_help_button = QPushButton("Aide expressions")
        self.expression_help_button.setToolTip("Affiche les expressions, constantes et fonctions supportees.")
        self.expression_help_button.clicked.connect(self.show_expression_help)
        form_layout.addRow("x min", self.x_min_input)
        form_layout.addRow("x max", self.x_max_input)
        form_layout.addRow("", self.expression_help_button)

        display_group = QGroupBox("Affichage")
        display_layout = QVBoxLayout(display_group)

        self.axes_checkbox = QCheckBox("Afficher les axes")
        self.axes_checkbox.setChecked(DEFAULT_SHOW_AXES)
        self.axes_checkbox.setToolTip("Affiche les axes X et Y sur le graphe.")
        self.grid_checkbox = QCheckBox("Afficher la grille")
        self.grid_checkbox.setChecked(DEFAULT_SHOW_GRID)
        self.grid_checkbox.setToolTip("Affiche une grille de lecture dans la zone de trace.")
        self.axis_labels_checkbox = QCheckBox("Afficher les valeurs des axes")
        self.axis_labels_checkbox.setChecked(DEFAULT_SHOW_AXIS_LABELS)
        self.axis_labels_checkbox.setToolTip("Affiche les graduations numeriques sur les axes.")
        self.legend_checkbox = QCheckBox("Afficher la legende")
        self.legend_checkbox.setChecked(DEFAULT_SHOW_LEGEND)
        self.legend_checkbox.setToolTip("Affiche un rappel colore des courbes dans le graphe.")
        self.optimized_render_checkbox = QCheckBox("Mode optimise (plus rapide)")
        self.optimized_render_checkbox.setChecked(DEFAULT_OPTIMIZED_RENDER)
        self.optimized_render_checkbox.setToolTip(
            "Mode plus rapide pour les grandes plages, avec un rendu parfois moins lisse."
        )
        self.axes_checkbox.toggled.connect(self.plot_expression)
        self.grid_checkbox.toggled.connect(self.plot_expression)
        self.axis_labels_checkbox.toggled.connect(self.plot_expression)
        self.legend_checkbox.toggled.connect(self.plot_expression)
        self.optimized_render_checkbox.toggled.connect(self.plot_expression)
        display_layout.addWidget(self.axes_checkbox)
        display_layout.addWidget(self.grid_checkbox)
        display_layout.addWidget(self.axis_labels_checkbox)
        display_layout.addWidget(self.legend_checkbox)
        display_layout.addWidget(self.optimized_render_checkbox)

        color_group = QGroupBox("Couleurs")
        color_layout = QGridLayout(color_group)

        self.palette_combo = QComboBox()
        self.palette_combo.addItems(["Light", "Dark", "Custom"])
        self.palette_combo.setToolTip(
            "Choisissez une palette predefinie ou Custom pour regler les couleurs manuellement."
        )
        self.palette_combo.currentTextChanged.connect(self._apply_palette_choice)
        self.axis_color_button = QPushButton("Axes")
        self.grid_color_button = QPushButton("Grille")
        self.background_color_button = QPushButton("Fond")
        self.background_color_button.setToolTip("Choisit la couleur de fond de la zone de trace.")
        self.axis_color_button.setToolTip("Choisit la couleur des axes et du cadre du graphe.")
        self.grid_color_button.setToolTip("Choisit la couleur de la grille.")
        self.background_color_button.clicked.connect(lambda: self._pick_color("background"))
        self.axis_color_button.clicked.connect(lambda: self._pick_color("axis"))
        self.grid_color_button.clicked.connect(lambda: self._pick_color("grid"))

        palette_label = QLabel("Palette")
        background_label = QLabel("Fond")
        axis_label = QLabel("Axes")
        grid_label = QLabel("Grille")
        self._color_labels = [background_label, axis_label, grid_label]

        color_layout.addWidget(palette_label, 0, 0)
        color_layout.addWidget(self.palette_combo, 0, 1)
        color_layout.addWidget(background_label, 1, 0)
        color_layout.addWidget(self.background_color_button, 1, 1)
        color_layout.addWidget(axis_label, 2, 0)
        color_layout.addWidget(self.axis_color_button, 2, 1)
        color_layout.addWidget(grid_label, 3, 0)
        color_layout.addWidget(self.grid_color_button, 3, 1)

        actions_layout = QHBoxLayout()
        self.default_button = QPushButton("Default")
        self.reset_view_button = QPushButton("Reset View")
        self.about_button = QPushButton("About")
        self.save_button = QPushButton("Capture")
        self.default_button.setToolTip("Remet tous les parametres aux valeurs par defaut.")
        self.reset_view_button.setToolTip("Revient a la derniere vue de base du trace courant.")
        self.about_button.setToolTip("Affiche les informations et credits de l'application.")
        self.save_button.setToolTip("Enregistre l'image courante du graphe au format PNG.")
        self.default_button.clicked.connect(self.reset_to_defaults)
        self.reset_view_button.clicked.connect(self.reset_view)
        self.about_button.clicked.connect(self.show_about_dialog)
        self.save_button.clicked.connect(self.save_plot)
        actions_layout.addWidget(self.default_button)
        actions_layout.addWidget(self.reset_view_button)
        actions_layout.addWidget(self.about_button)
        actions_layout.addWidget(self.save_button)

        self.status_label = QLabel("Pret.")
        self.status_label.setWordWrap(True)
        self.status_label.setToolTip("Resume l'etat courant du trace ou les messages d'erreur.")

        panel_layout.addWidget(form_group)
        panel_layout.addWidget(display_group)
        panel_layout.addWidget(color_group)
        panel_layout.addLayout(actions_layout)
        panel_layout.addWidget(self.status_label)
        panel_layout.addStretch(1)

        return panel

    def _apply_defaults(self) -> None:
        self._apply_palette(DEFAULT_PALETTE, trigger_redraw=False)
        self._set_custom_color_controls_enabled(False)
        self.palette_combo.setCurrentText(DEFAULT_PALETTE)
        self._update_color_button(self.background_color_button, self._background_color)
        self._update_color_button(self.axis_color_button, self._axis_color)
        self._update_color_button(self.grid_color_button, self._grid_color)
        self._load_settings()
        self.plot_expression()

    def _pick_color(self, role: str) -> None:
        if self.palette_combo.currentText() != "Custom":
            return
        current_color = {
            "background": self._background_color,
            "axis": self._axis_color,
            "grid": self._grid_color,
        }[role]
        chosen = QColorDialog.getColor(QColor(current_color), self, "Choisir une couleur")
        if not chosen.isValid():
            return

        color_name = chosen.name()
        if role == "background":
            self._background_color = color_name
            self._custom_background_color = color_name
            self._update_color_button(self.background_color_button, color_name)
        elif role == "axis":
            self._axis_color = color_name
            self._custom_axis_color = color_name
            self._update_color_button(self.axis_color_button, color_name)
        else:
            self._grid_color = color_name
            self._custom_grid_color = color_name
            self._update_color_button(self.grid_color_button, color_name)
        self.plot_expression()

    def _apply_palette_choice(self, palette_name: str) -> None:
        if palette_name == "Custom":
            self._restore_custom_colors()
            self._set_custom_color_controls_enabled(True)
            self.plot_expression()
            return

        self._apply_palette(palette_name, trigger_redraw=True)
        self._set_custom_color_controls_enabled(False)

    def _apply_palette(self, palette_name: str, trigger_redraw: bool) -> None:
        palette = PALETTES[palette_name]
        self._background_color = palette["background"]
        self._axis_color = palette["axis"]
        self._grid_color = palette["grid"]
        self._update_color_button(self.background_color_button, self._background_color)
        self._update_color_button(self.axis_color_button, self._axis_color)
        self._update_color_button(self.grid_color_button, self._grid_color)
        self._refresh_curve_list_colors()
        if trigger_redraw:
            self.plot_expression()

    def _set_custom_color_controls_enabled(self, enabled: bool) -> None:
        self.background_color_button.setEnabled(enabled)
        self.axis_color_button.setEnabled(enabled)
        self.grid_color_button.setEnabled(enabled)
        for label in self._color_labels:
            label.setEnabled(enabled)

    def _restore_custom_colors(self) -> None:
        self._background_color = self._custom_background_color
        self._axis_color = self._custom_axis_color
        self._grid_color = self._custom_grid_color
        self._update_color_button(self.background_color_button, self._background_color)
        self._update_color_button(self.axis_color_button, self._axis_color)
        self._update_color_button(self.grid_color_button, self._grid_color)
        self._refresh_curve_list_colors()

    def _active_curve_specs(self) -> List[CurveSpec]:
        items: List[CurveSpec] = []
        for index in range(self.curve_list.count()):
            item = self.curve_list.item(index)
            expression = item.text().strip()
            if expression:
                items.append(CurveSpec(expression=expression, color=self._display_curve_color(index)))
        if items:
            return items

        expression = self.expression_input.text().strip()
        if not expression:
            return []
        return [CurveSpec(expression=expression, color=self._display_curve_color(0))]

    def _set_curve_list_items(self, curves: Sequence[CurveSpec]) -> None:
        previous = self.curve_list.blockSignals(True)
        try:
            self.curve_list.clear()
            for index, curve in enumerate(curves):
                expression = curve.expression.strip()
                if not expression:
                    continue
                item = QListWidgetItem(expression)
                self.curve_list.addItem(item)
                color = curve.color or self._default_custom_curve_color(index)
                self._apply_curve_item_color(item, color)
        finally:
            self.curve_list.blockSignals(previous)
        self._ensure_custom_curve_colors_length()
        self._refresh_curve_list_colors()

    def _load_selected_curve(self, expression: str) -> None:
        expression = expression.strip()
        if expression:
            self.expression_input.setText(expression)

    def _edit_curve_color(self, item: QListWidgetItem) -> None:
        if self.palette_combo.currentText() != "Custom":
            return
        row = self.curve_list.row(item)
        current_color = self._custom_curve_color_for_index(row)
        chosen = QColorDialog.getColor(QColor(current_color), self, "Choisir la couleur de la courbe")
        if not chosen.isValid():
            return
        self._set_custom_curve_color(row, chosen.name())
        self._apply_curve_item_color(item, chosen.name())
        self.plot_expression()

    def _apply_curve_item_color(self, item: QListWidgetItem, color_hex: str) -> None:
        item.setData(Qt.UserRole, color_hex)
        item.setForeground(QColor(color_hex))
        pixmap = QPixmap(12, 12)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        try:
            painter.setPen(QColor("#666666"))
            painter.setBrush(QColor(color_hex))
            painter.drawRect(1, 1, 10, 10)
        finally:
            painter.end()
        item.setIcon(QIcon(pixmap))

    def _curve_specs_in_list(self) -> List[CurveSpec]:
        return [
            CurveSpec(
                expression=self.curve_list.item(index).text().strip(),
                color=self.curve_list.item(index).data(Qt.UserRole) or self._display_curve_color(index),
            )
            for index in range(self.curve_list.count())
            if self.curve_list.item(index).text().strip()
        ]

    def _default_custom_curve_color(self, index: int) -> str:
        return LIGHT_CURVE_COLORS[index % len(LIGHT_CURVE_COLORS)]

    def _display_curve_color(self, index: int) -> str:
        if self.palette_combo.currentText() == "Custom":
            if index < len(self._custom_curve_colors):
                return self._custom_curve_colors[index]
            return self._default_custom_curve_color(index)
        palette_name = self.palette_combo.currentText() or DEFAULT_PALETTE
        palette_curves = PALETTES.get(palette_name, PALETTES[DEFAULT_PALETTE])["curves"]
        return palette_curves[index % len(palette_curves)]

    def _custom_curve_color_for_index(self, index: int) -> str:
        self._ensure_custom_curve_colors_length()
        return self._custom_curve_colors[index]

    def _set_custom_curve_color(self, index: int, color_hex: str) -> None:
        self._ensure_custom_curve_colors_length()
        self._custom_curve_colors[index] = color_hex

    def _ensure_custom_curve_colors_length(self) -> None:
        needed = self.curve_list.count()
        while len(self._custom_curve_colors) < needed:
            self._custom_curve_colors.append(self._default_custom_curve_color(len(self._custom_curve_colors)))
        if len(self._custom_curve_colors) > needed:
            self._custom_curve_colors = self._custom_curve_colors[:needed]

    def _refresh_curve_list_colors(self) -> None:
        for index in range(self.curve_list.count()):
            item = self.curve_list.item(index)
            self._apply_curve_item_color(item, self._display_curve_color(index))

    def add_curve(self) -> None:
        expression = self.expression_input.text().strip()
        if not expression:
            self.status_label.setText("Veuillez saisir une equation avant de l'ajouter.")
            return
        try:
            self._parser.parse(expression)
        except ExpressionError as exc:
            self.status_label.setText(str(exc))
            return

        items = [self.curve_list.item(index).text() for index in range(self.curve_list.count())]
        if expression not in items:
            item = QListWidgetItem(expression)
            self.curve_list.addItem(item)
            self._ensure_custom_curve_colors_length()
            if self.palette_combo.currentText() != "Custom":
                self._custom_curve_colors[self.curve_list.count() - 1] = self._display_curve_color(
                    self.curve_list.count() - 1
                )
            self._refresh_curve_list_colors()
        self.curve_list.setCurrentRow(self.curve_list.count() - 1)
        self.plot_expression()

    def update_selected_curve(self) -> None:
        current_row = self.curve_list.currentRow()
        if current_row < 0:
            self.status_label.setText("Selectionnez d'abord une courbe a mettre a jour.")
            return
        expression = self.expression_input.text().strip()
        if not expression:
            self.status_label.setText("Veuillez saisir une equation avant la mise a jour.")
            return
        try:
            self._parser.parse(expression)
        except ExpressionError as exc:
            self.status_label.setText(str(exc))
            return

        self.curve_list.item(current_row).setText(expression)
        self.plot_expression()

    def remove_selected_curve(self) -> None:
        current_row = self.curve_list.currentRow()
        if current_row < 0:
            self.status_label.setText("Selectionnez une courbe a supprimer.")
            return
        self.curve_list.takeItem(current_row)
        if current_row < len(self._custom_curve_colors):
            self._custom_curve_colors.pop(current_row)
        self._refresh_curve_list_colors()
        self.plot_expression()

    def clear_curves(self) -> None:
        self._custom_curve_colors = []
        self._set_curve_list_items([])
        self.plot_expression()

    def _read_options(self) -> Tuple[PlotOptions, List[Callable[[float], float]]]:
        curves = self._active_curve_specs()
        if not curves:
            raise ExpressionError("Veuillez saisir une equation.")

        try:
            x_min = float(self.x_min_input.text())
            x_max = float(self.x_max_input.text())
        except ValueError as exc:
            raise ExpressionError("Les bornes x doivent etre numeriques.") from exc

        if x_min >= x_max:
            raise ExpressionError("x min doit etre strictement inferieur a x max.")

        plot_functions = [self._parser.parse(curve.expression) for curve in curves]
        options = PlotOptions(
            curves=curves,
            x_min=x_min,
            x_max=x_max,
            show_axes=self.axes_checkbox.isChecked(),
            show_grid=self.grid_checkbox.isChecked(),
            show_axis_labels=self.axis_labels_checkbox.isChecked(),
            show_legend=self.legend_checkbox.isChecked(),
            use_optimized_render=self.optimized_render_checkbox.isChecked(),
            background_color=self._background_color,
            axis_color=self._axis_color,
            grid_color=self._grid_color,
        )
        return options, plot_functions

    def plot_expression(self) -> None:
        try:
            options, plot_functions = self._read_options()
        except ExpressionError as exc:
            self.plot_widget.clear_plot(str(exc))
            self.status_label.setText(str(exc))
            return

        self.plot_widget.set_plot(plot_functions, options)
        if len(options.curves) == 1:
            self.status_label.setText(
                f"Trace de y = {options.curves[0].expression} sur [{options.x_min}, {options.x_max}]"
            )
        else:
            self.status_label.setText(
                f"Trace de {len(options.curves)} courbes sur [{options.x_min}, {options.x_max}]"
            )
        for curve in options.curves:
            self._remember_expression(curve.expression)
        self._save_settings()

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
        color = QColor(color_hex)
        text_color = "#000000" if color.lightness() > 140 else "#ffffff"
        button.setStyleSheet(
            "QPushButton {"
            f"background-color: {color_hex};"
            f"color: {text_color};"
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

    def _remember_expression(self, expression: str) -> None:
        expression = expression.strip()
        if not expression:
            return
        items = [self.history_combo.itemText(i) for i in range(self.history_combo.count())]
        items = [item for item in items if item != expression]
        items.insert(0, expression)
        self._set_history_items(items[:MAX_HISTORY_ITEMS])

    def _set_history_items(self, items) -> None:
        previous = self.history_combo.blockSignals(True)
        try:
            self.history_combo.clear()
            for item in items:
                self.history_combo.addItem(item)
            if items:
                self.history_combo.setCurrentIndex(0)
        finally:
            self.history_combo.blockSignals(previous)

    def _apply_history_expression(self, expression: str) -> None:
        expression = expression.strip()
        if not expression or expression == self.expression_input.text().strip():
            return
        self.expression_input.setText(expression)
        self.plot_expression()

    def show_about_dialog(self) -> None:
        QMessageBox.about(
            self,
            "About EqnPlot",
            "EqnPlot\n\n"
            "Petit traceur d'equations PyQt5.\n\n"
            "Conception et implementation: OpenAI Codex.",
        )

    def show_expression_help(self) -> None:
        QMessageBox.information(
            self,
            "Expressions supportees",
            "Variable:\n"
            "x\n\n"
            "Operateurs:\n"
            "+   -   *   /   **   %\n\n"
            "Constantes:\n"
            "pi, e\n\n"
            "Fonctions:\n"
            "sin, cos, tan, asin, acos, atan,\n"
            "sinh, cosh, tanh, exp, log, log10,\n"
            "sqrt, fabs, floor, ceil\n\n"
            "Exemples:\n"
            "sin(x)\n"
            "x**2 - 4*x + 1\n"
            "sqrt(x)\n"
            "exp(-x**2)",
        )

    def reset_view(self) -> None:
        self.plot_widget.reset_view()

    def reset_to_defaults(self) -> None:
        widgets = [
            self.history_combo,
            self.expression_input,
            self.curve_list,
            self.x_min_input,
            self.x_max_input,
            self.axes_checkbox,
            self.grid_checkbox,
            self.axis_labels_checkbox,
            self.legend_checkbox,
            self.optimized_render_checkbox,
            self.palette_combo,
        ]
        previous_states = [(widget, widget.blockSignals(True)) for widget in widgets]
        try:
            self.expression_input.setText(DEFAULT_EXPRESSION)
            self.x_min_input.setText(DEFAULT_X_MIN)
            self.x_max_input.setText(DEFAULT_X_MAX)
            self.axes_checkbox.setChecked(DEFAULT_SHOW_AXES)
            self.grid_checkbox.setChecked(DEFAULT_SHOW_GRID)
            self.axis_labels_checkbox.setChecked(DEFAULT_SHOW_AXIS_LABELS)
            self.legend_checkbox.setChecked(DEFAULT_SHOW_LEGEND)
            self.optimized_render_checkbox.setChecked(DEFAULT_OPTIMIZED_RENDER)
            self.palette_combo.setCurrentText(DEFAULT_PALETTE)
            self._apply_palette(DEFAULT_PALETTE, trigger_redraw=False)
            self._set_curve_list_items([])
            self._custom_background_color = PALETTES[DEFAULT_PALETTE]["background"]
            self._custom_axis_color = PALETTES[DEFAULT_PALETTE]["axis"]
            self._custom_grid_color = PALETTES[DEFAULT_PALETTE]["grid"]
            self._custom_curve_colors = []
            self._set_custom_color_controls_enabled(False)
            self._set_history_items(DEFAULT_RECENT_EXPRESSIONS)
        finally:
            for widget, previous_state in previous_states:
                widget.blockSignals(previous_state)

        self.plot_expression()

    def _load_settings(self) -> None:
        widgets = [
            self.history_combo,
            self.expression_input,
            self.curve_list,
            self.x_min_input,
            self.x_max_input,
            self.axes_checkbox,
            self.grid_checkbox,
            self.axis_labels_checkbox,
            self.legend_checkbox,
            self.optimized_render_checkbox,
            self.palette_combo,
        ]
        previous_states = [(widget, widget.blockSignals(True)) for widget in widgets]
        try:
            palette_name = self._settings.value("palette", DEFAULT_PALETTE, type=str)
            if palette_name not in {"Light", "Dark", "Custom"}:
                palette_name = DEFAULT_PALETTE

            self.expression_input.setText(self._settings.value("expression", DEFAULT_EXPRESSION, type=str))
            self.x_min_input.setText(self._settings.value("x_min", DEFAULT_X_MIN, type=str))
            self.x_max_input.setText(self._settings.value("x_max", DEFAULT_X_MAX, type=str))
            self.axes_checkbox.setChecked(self._settings.value("show_axes", DEFAULT_SHOW_AXES, type=bool))
            self.grid_checkbox.setChecked(self._settings.value("show_grid", DEFAULT_SHOW_GRID, type=bool))
            self.axis_labels_checkbox.setChecked(
                self._settings.value("show_axis_labels", DEFAULT_SHOW_AXIS_LABELS, type=bool)
            )
            self.legend_checkbox.setChecked(
                self._settings.value("show_legend", DEFAULT_SHOW_LEGEND, type=bool)
            )
            self.optimized_render_checkbox.setChecked(
                self._settings.value("use_optimized_render", DEFAULT_OPTIMIZED_RENDER, type=bool)
            )
            self.palette_combo.setCurrentText(palette_name)
            curve_list_raw = self._settings.value("curve_list", [], type=list)
            curve_list = [item for item in curve_list_raw if isinstance(item, str) and item.strip()]
            custom_curve_colors = self._settings.value("custom_curve_colors", [], type=list)
            self._custom_curve_colors = [
                color for color in custom_curve_colors if isinstance(color, str) and color.strip()
            ]
            self._set_curve_list_items([CurveSpec(expression=item, color="") for item in curve_list])
            history_raw = self._settings.value("recent_expressions", [], type=list)
            history = [item for item in history_raw if isinstance(item, str) and item.strip()]
            if not history:
                history = list(DEFAULT_RECENT_EXPRESSIONS)
            self._set_history_items(self._merge_recent_defaults(history))

            if palette_name == "Custom":
                self._custom_background_color = self._settings.value("custom_background_color", "#ffffff", type=str)
                self._custom_axis_color = self._settings.value("custom_axis_color", "#222222", type=str)
                self._custom_grid_color = self._settings.value("custom_grid_color", "#c8d5dd", type=str)
                self._restore_custom_colors()
                self._set_custom_color_controls_enabled(True)
            else:
                self._custom_background_color = self._settings.value(
                    "custom_background_color", PALETTES[DEFAULT_PALETTE]["background"], type=str
                )
                self._custom_axis_color = self._settings.value(
                    "custom_axis_color", PALETTES[DEFAULT_PALETTE]["axis"], type=str
                )
                self._custom_grid_color = self._settings.value(
                    "custom_grid_color", PALETTES[DEFAULT_PALETTE]["grid"], type=str
                )
                self._apply_palette(palette_name, trigger_redraw=False)
                self._set_custom_color_controls_enabled(False)

            self._update_color_button(self.background_color_button, self._background_color)
            self._update_color_button(self.axis_color_button, self._axis_color)
            self._update_color_button(self.grid_color_button, self._grid_color)
            self._refresh_curve_list_colors()
        finally:
            for widget, previous_state in previous_states:
                widget.blockSignals(previous_state)

    def _save_settings(self) -> None:
        self._ensure_custom_curve_colors_length()
        self._settings.setValue("expression", self.expression_input.text().strip())
        self._settings.setValue("x_min", self.x_min_input.text().strip())
        self._settings.setValue("x_max", self.x_max_input.text().strip())
        self._settings.setValue("show_axes", self.axes_checkbox.isChecked())
        self._settings.setValue("show_grid", self.grid_checkbox.isChecked())
        self._settings.setValue("show_axis_labels", self.axis_labels_checkbox.isChecked())
        self._settings.setValue("show_legend", self.legend_checkbox.isChecked())
        self._settings.setValue("use_optimized_render", self.optimized_render_checkbox.isChecked())
        self._settings.setValue("palette", self.palette_combo.currentText())
        self._settings.setValue("background_color", self._background_color)
        self._settings.setValue("axis_color", self._axis_color)
        self._settings.setValue("grid_color", self._grid_color)
        self._settings.setValue("custom_background_color", self._custom_background_color)
        self._settings.setValue("custom_axis_color", self._custom_axis_color)
        self._settings.setValue("custom_grid_color", self._custom_grid_color)
        self._settings.setValue("custom_curve_colors", self._custom_curve_colors)
        self._settings.setValue(
            "recent_expressions",
            [self.history_combo.itemText(i) for i in range(self.history_combo.count())],
        )
        self._settings.setValue(
            "curve_list",
            [self.curve_list.item(i).text() for i in range(self.curve_list.count())],
        )
        self._settings.sync()

    def _merge_recent_defaults(self, items: Sequence[str]) -> List[str]:
        merged: List[str] = []
        for expression in list(items) + DEFAULT_RECENT_EXPRESSIONS:
            expression = expression.strip()
            if expression and expression not in merged:
                merged.append(expression)
        return merged[:MAX_HISTORY_ITEMS]


def run() -> None:
    if sys.platform.startswith("win"):
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        except Exception:
            pass

    app = QApplication.instance() or QApplication(sys.argv)
    icon = load_app_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


def load_app_icon() -> QIcon:
    project_root = Path(__file__).resolve().parent.parent
    candidates = [
        project_root / "assets" / "eqnplot-icon.ico",
        project_root / "assets" / "eqnplot.ico",
        project_root / "assets" / "eqnplot-icon.png",
    ]
    for path in candidates:
        if path.exists():
            return QIcon(str(path))
    return QIcon()
