# EqnPlot

Mini application PyQt5 pour tracer une equation de type `y = f(x)`.

## Fonctionnalites

- Saisie d'une equation en fonction de `x`
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

## Distribution Windows

### Build executable

Mode dossier recommande:

```powershell
.\build.ps1
```

Mode executable unique:

```powershell
.\build.ps1 -OneFile
```

Le mode dossier produit `dist\EqnPlot\EqnPlot.exe`.

### PyInstaller manuel

```powershell
pip install pyinstaller
pyinstaller --noconfirm --clean EqnPlot.spec
```

### Si PowerShell bloque les scripts

Selon la configuration Windows, PowerShell peut refuser `Activate.ps1` ou `build.ps1` avec un message du type `running scripts is disabled on this system`.

Le plus simple est d'autoriser les scripts uniquement pour la session en cours:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\build.ps1
```

Ou en une seule commande:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

Pour le mode `onefile`:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -OneFile
```

Note: il n'est pas necessaire d'activer manuellement le virtualenv pour utiliser `build.ps1`, car le script appelle directement `.\.venv\Scripts\python.exe`.

### Installateur Windows

Le fichier [installer.iss](D:/dev/VIBECODING/eqnplot/installer.iss) est prevu pour Inno Setup.

1. Installer Inno Setup
2. Generer d'abord `dist\EqnPlot\`
3. Ouvrir `installer.iss` dans Inno Setup
4. Compiler l'installateur

Le resultat sera genere dans `installer-output\`.

### Icone

L'icone Windows utilisee par defaut est `assets\eqnplot-icon.ico`.
