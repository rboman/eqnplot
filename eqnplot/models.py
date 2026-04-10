from dataclasses import dataclass


@dataclass
class PlotOptions:
    expression: str
    x_min: float
    x_max: float
    show_axes: bool = True
    show_grid: bool = True
    show_axis_labels: bool = True
    curve_color: str = "#d1495b"
    axis_color: str = "#222222"
    grid_color: str = "#c8d5dd"
