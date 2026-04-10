from dataclasses import dataclass


@dataclass
class CurveSpec:
    expression: str
    color: str


@dataclass
class PlotOptions:
    curves: list[CurveSpec]
    x_min: float
    x_max: float
    show_axes: bool = True
    show_grid: bool = True
    show_axis_labels: bool = True
    use_optimized_render: bool = True
    background_color: str = "#ffffff"
    curve_color: str = "#d1495b"
    axis_color: str = "#222222"
    grid_color: str = "#c8d5dd"
