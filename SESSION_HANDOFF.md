# Future Session Handoff

## Fast Restart Checklist

1. Create and install the virtual environment if needed.
2. Run tests:

```bash
python -m unittest discover -s tests -v
```

3. Launch the app:

```bash
python main.py
```

4. Read:
- `README.md` for usage and packaging
- `ARCHITECTURE.md` for technical context

## Most Important Files

- `eqnplot/main_window.py`
- `eqnplot/plot_widget.py`
- `eqnplot/parser.py`
- `eqnplot/models.py`
- `build.py`
- `EqnPlot.spec`
- `installer.iss`

## Current Product State

- Multi-curve plotting works
- Zoom and pan work
- Hover tooltip works and is optional
- Legend works and is optional
- Per-curve custom colors work in `Custom` palette mode
- Settings persist with `QSettings`
- PyInstaller build exists for `onedir` and `onefile`
- Inno Setup installer exists for Windows

## Important Build Commands

Standard build:

```bash
python build.py
```

Single-file build:

```bash
python build.py --onefile
```

Optional UPX:

```bash
python build.py --upx
python build.py --onefile --upx
```

## Notes

- `EqnPlot.spec` is intentionally kept under version control.
- `build.py --onefile` should no longer overwrite the repository spec.
- If Windows app icons look stale, Explorer icon cache may need time or a refresh after reinstall/rebuild.
