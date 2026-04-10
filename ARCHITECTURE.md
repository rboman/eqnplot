# EqnPlot Architecture Notes

## Purpose

EqnPlot is a small PyQt5 desktop application for plotting one or more equations of the form `y = f(x)`.

This file is meant as a short developer handoff so the project can be resumed later without needing the original implementation context.

## Project Structure

- `main.py`
  Entry point. Starts the Qt application through `eqnplot.main_window.run()`.

- `eqnplot/main_window.py`
  Main window and UI orchestration.
  Responsibilities:
  - builds the control panel
  - manages recent expressions
  - manages the curve list
  - manages palettes and custom per-curve colors
  - persists user settings with `QSettings`
  - prepares `PlotOptions` and compiled functions for the plot widget

- `eqnplot/plot_widget.py`
  Custom drawing widget.
  Responsibilities:
  - evaluates functions over the current X range
  - computes Y bounds automatically
  - draws grid, axes, labels, legend, curves, hover markers, and hover tooltip
  - handles zoom and pan interactions
  - exports the current graph as PNG

- `eqnplot/parser.py`
  Safe expression parser.
  Responsibilities:
  - validates user input via AST
  - only allows approved operators, constants, and math functions
  - returns a callable `f(x)`

- `eqnplot/models.py`
  Shared dataclasses:
  - `CurveSpec`
  - `PlotOptions`

- `tests/test_parser.py`
  Parser validation tests.

- `tests/test_plot_widget.py`
  Plot widget behavior tests.

- `build.py`
  Cross-platform PyInstaller build helper.

- `build.ps1`
  Windows wrapper around `build.py`.

- `EqnPlot.spec`
  Checked-in PyInstaller spec for the normal `onedir` build.

- `installer.iss`
  Windows Inno Setup installer script.

## Rendering Design

### Plot evaluation

- Function sampling is based on plot width in pixels, not directly on `x_min/x_max`.
- Current rule: `sample_count = max(2, round(pixel_width) * 5)`.
- This keeps plotting cost roughly tied to screen size instead of numeric range size.

### Rendering modes

- Smooth mode:
  - draws a classic Qt path/polyline style curve
  - visually cleaner
  - can become slower on very dense plots

- Optimized mode:
  - uses a faster rendering strategy for dense data
  - intended for very large visible ranges
  - may introduce minor visual artifacts in extreme cases

The optimized mode is optional and disabled by default.

### Hover display

- Hover can show:
  - vertical guide line
  - points on curves at current mouse X
  - floating tooltip near the mouse cursor
- The tooltip can be turned on/off from the UI.

### Legend

- The legend is drawn inside the plot area.
- It can be turned on/off from the UI.

## UI and Settings

### Main behaviors

- Plot redraw is automatic on:
  - expression edit completion
  - Enter in expression or X bounds
  - display option changes
  - palette changes
  - custom color changes

- The old manual `Plot` button was intentionally removed.

### Recent expressions

- Recent expressions are stored in `QSettings`.
- A built-in starter set of nice demo expressions is merged into recents so a fresh session always has quick examples.

### Multi-curve mode

- The curve list is the source of truth when it contains at least one item.
- If the curve list is empty, the current expression field is treated as a single curve.

### Curve colors

- `Light` and `Dark` palettes provide default colors for at least 10 curves.
- `Custom` mode enables per-curve colors.
- In `Custom`, double-clicking a curve in the list opens a color picker.

### Persistence

`QSettings` persists:

- expression and X range
- display toggles
- palette choice
- custom colors
- custom per-curve colors
- recent expressions
- current curve list

## Packaging Notes

### Build modes

- `python build.py`
  Normal `onedir` build using `EqnPlot.spec`

- `python build.py --onefile`
  Direct PyInstaller onefile build from `main.py`

- `UPX` is disabled by default
- Enable it only explicitly with:
  - `python build.py --upx`
  - `python build.py --onefile --upx`

### Why keep `EqnPlot.spec`

The checked-in spec is useful and should be kept.

It defines the stable `onedir` build and avoids relying on a generated spec. The `onefile` path is intentionally separate and writes temporary spec data under `build/` so the repository spec is not overwritten.

### Portability

- Packaging paths were converted to relative/pathlib-based paths.
- `build.py` is cross-platform.
- `build.ps1` and `installer.iss` are Windows-specific.
- The application code itself is mostly portable to Linux/macOS as long as PyQt5 and Qt runtime dependencies are available.

### Windows installer

`installer.iss` currently supports:

- per-user install
- all-users install
- uninstall display icon

Per-user install should not require admin rights. All-users install may require elevation.

## Known Limitations

- No zoom rectangle
- No panning in Y
- No manual Y bounds
- No parametric or polar modes
- No packaging path yet for Linux distributions

## Good Next Improvements

- per-curve visibility checkbox
- per-curve rename/label
- better export options such as custom resolution
- Linux packaging path
- optional status bar instead of inline status label
- more widget tests for UI-specific behavior
