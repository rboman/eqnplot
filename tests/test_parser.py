import unittest

from eqnplot.parser import ExpressionError, ExpressionParser


class ExpressionParserTests(unittest.TestCase):
    def setUp(self):
        self.parser = ExpressionParser()

    def test_linear_expression(self):
        func = self.parser.parse("x + 2")
        self.assertEqual(func(3), 5)

    def test_quadratic_expression(self):
        func = self.parser.parse("x**2 - 4*x + 1")
        self.assertEqual(func(2), -3)

    def test_math_function(self):
        func = self.parser.parse("sin(x)")
        self.assertAlmostEqual(func(0), 0.0)

    def test_constants(self):
        func = self.parser.parse("cos(pi)")
        self.assertAlmostEqual(func(0), -1.0)

    def test_empty_expression_is_rejected(self):
        with self.assertRaises(ExpressionError):
            self.parser.parse("   ")

    def test_unsafe_name_is_rejected(self):
        with self.assertRaises(ExpressionError):
            self.parser.parse("__import__('os')")

    def test_unknown_function_is_rejected(self):
        with self.assertRaises(ExpressionError):
            self.parser.parse("pow(x)")

    def test_invalid_syntax_is_rejected(self):
        with self.assertRaises(ExpressionError):
            self.parser.parse("sin(x")

    def test_domain_error_is_raised_at_evaluation_time(self):
        func = self.parser.parse("sqrt(x)")
        with self.assertRaises(ValueError):
            func(-1)

    def test_division_by_zero_is_raised_at_evaluation_time(self):
        func = self.parser.parse("1 / x")
        with self.assertRaises(ZeroDivisionError):
            func(0)


if __name__ == "__main__":
    unittest.main()
