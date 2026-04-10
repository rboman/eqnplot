import ast
import math
from typing import Callable


class ExpressionError(ValueError):
    """Raised when the expression is invalid or unsafe."""


ALLOWED_FUNCTIONS = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    "exp": math.exp,
    "log": math.log,
    "log10": math.log10,
    "sqrt": math.sqrt,
    "fabs": math.fabs,
    "floor": math.floor,
    "ceil": math.ceil,
}

ALLOWED_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}

ALLOWED_BINARY_OPS = (
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
)

ALLOWED_UNARY_OPS = (
    ast.UAdd,
    ast.USub,
)


class ExpressionParser:
    """Parses a safe subset of Python math expressions into a callable."""

    def parse(self, expression: str) -> Callable[[float], float]:
        text = expression.strip()
        if not text:
            raise ExpressionError("L'expression ne peut pas etre vide.")

        try:
            tree = ast.parse(text, mode="eval")
        except SyntaxError as exc:
            raise ExpressionError("Syntaxe invalide dans l'expression.") from exc

        self._validate(tree)

        def compiled(x_value: float) -> float:
            value = self._evaluate(tree.body, x_value)
            if not math.isfinite(value):
                raise ValueError("Le resultat n'est pas fini.")
            return value

        return compiled

    def _validate(self, node: ast.AST) -> None:
        if isinstance(node, ast.Expression):
            self._validate(node.body)
            return

        if isinstance(node, ast.BinOp):
            if not isinstance(node.op, ALLOWED_BINARY_OPS):
                raise ExpressionError("Operateur non autorise.")
            self._validate(node.left)
            self._validate(node.right)
            return

        if isinstance(node, ast.UnaryOp):
            if not isinstance(node.op, ALLOWED_UNARY_OPS):
                raise ExpressionError("Operateur unaire non autorise.")
            self._validate(node.operand)
            return

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ExpressionError("Appel de fonction non autorise.")
            if node.func.id not in ALLOWED_FUNCTIONS:
                raise ExpressionError(f"Fonction non autorisee: {node.func.id}")
            if len(node.keywords) != 0:
                raise ExpressionError("Les arguments nommes ne sont pas autorises.")
            if len(node.args) != 1:
                raise ExpressionError("Les fonctions doivent avoir un seul argument.")
            self._validate(node.args[0])
            return

        if isinstance(node, ast.Name):
            if node.id not in {"x", *ALLOWED_CONSTANTS.keys()}:
                raise ExpressionError(f"Nom non autorise: {node.id}")
            return

        if isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float)):
                raise ExpressionError("Seules les constantes numeriques sont autorisees.")
            return

        if hasattr(ast, "Num") and isinstance(node, ast.Num):
            return

        raise ExpressionError(f"Element non autorise: {type(node).__name__}")

    def _evaluate(self, node: ast.AST, x_value: float) -> float:
        if isinstance(node, ast.BinOp):
            left = self._evaluate(node.left, x_value)
            right = self._evaluate(node.right, x_value)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.Pow):
                return left ** right
            if isinstance(node.op, ast.Mod):
                return left % right

        if isinstance(node, ast.UnaryOp):
            operand = self._evaluate(node.operand, x_value)
            if isinstance(node.op, ast.UAdd):
                return +operand
            if isinstance(node.op, ast.USub):
                return -operand

        if isinstance(node, ast.Call):
            func = ALLOWED_FUNCTIONS[node.func.id]
            value = self._evaluate(node.args[0], x_value)
            return func(value)

        if isinstance(node, ast.Name):
            if node.id == "x":
                return x_value
            return ALLOWED_CONSTANTS[node.id]

        if isinstance(node, ast.Constant):
            return float(node.value)

        if hasattr(ast, "Num") and isinstance(node, ast.Num):
            return float(node.n)

        raise ExpressionError("Impossible d'evaluer l'expression.")
