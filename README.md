# EqnPlot

Mini application PyQt5 pour tracer une equation de type `y = f(x)`.

## Fonctionnalites

- Saisie d'une equation en fonction de `x`
- Mode multi-courbes simple avec liste de fonctions
- Affichage optionnel des axes
- Affichage optionnel d'une grille
- Affichage optionnel des valeurs de graduation sur les axes
- Choix des couleurs de la courbe, des axes et de la grille
- Reglage de la plage `x_min` / `x_max`
- Zoom a la molette de la souris
- Deplacement horizontal par glisser-deposer
- Lecture continue de `x` et `y` sous la souris
- Choix entre rendu optimise rapide et rendu lisse
- Couleur de fond configurable
- Palettes `Light`, `Dark` et `Custom`
- Historique recent des equations
- Bouton `Reset View` pour revenir a la vue de base
- Aide integree sur les expressions supportees
- Export de l'image au format PNG

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Lancement

```bash
python main.py
```

## Expressions supportees

L'application accepte:

- la variable `x`
- les nombres
- les operateurs `+`, `-`, `*`, `/`, `**`, `%`
- les constantes `pi`, `e`
- les fonctions `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sinh`, `cosh`, `tanh`, `exp`, `log`, `log10`, `sqrt`, `fabs`, `floor`, `ceil`

Exemples:

- `sin(x)`
- `x**2 - 4*x + 1`
- `sqrt(x)`
- `exp(-x**2)`

## Tests

```bash
python -m unittest discover -s tests -v
```

## Distribution and Packaging

### Build on Windows

Recommended folder build:

```powershell
.\build.ps1
```

Single executable:

```powershell
.\build.ps1 -OneFile
```

Enable UPX only when you explicitly want it:

```powershell
.\build.ps1 -Upx
.\build.ps1 -OneFile -Upx
```

The folder build produces `dist/EqnPlot/EqnPlot.exe`.
This is now a true `onedir` build: the executable is placed inside a `dist/EqnPlot/` folder with its companion files.

### Cross-platform build

The project now includes a portable build helper:

```bash
python build.py
python build.py --onefile
python build.py --upx
python build.py --onefile --upx
```

This helper:

- uses `.venv/Scripts/python.exe` on Windows
- uses `.venv/bin/python` on Linux and macOS
- uses only relative paths
- chooses the correct PyInstaller data separator automatically
- keeps UPX disabled by default

The PyInstaller spec also uses relative paths now, so the project can be moved to another machine or folder without edits.
The checked-in `EqnPlot.spec` is still useful: it defines the normal `onedir` build. The `onefile` build is generated directly from `main.py`, but now writes any temporary spec into `build/` so it no longer overwrites the project spec.

### If PowerShell blocks scripts

Depending on your Windows policy, PowerShell may refuse `Activate.ps1` or `build.ps1` with a message like `running scripts is disabled on this system`.

The simplest workaround is to allow scripts only for the current session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\build.ps1
```

Or in a single command:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

For `onefile` mode:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -OneFile
```

Note: you do not need to activate the virtualenv manually to use `build.ps1`, because it directly calls `.\.venv\Scripts\python.exe`.

### Installateur Windows

Le fichier [installer.iss](D:/dev/VIBECODING/eqnplot/installer.iss) est prevu pour Inno Setup.

1. Installer Inno Setup
2. Generer d'abord `dist\EqnPlot\`
3. Ouvrir `installer.iss` dans Inno Setup
4. Compiler l'installateur

The result will be generated in `installer-output\`.

This installer is Windows-only by design. On Linux, the application should be launched directly with Python or packaged with a Linux-specific format such as AppImage.

### Icone

The default application icon is `assets/eqnplot-icon.ico`.

It is now:

- injected into the Windows executable via `--icon`
- bundled as an application resource so it can still be loaded correctly in PyInstaller builds
