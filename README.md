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
