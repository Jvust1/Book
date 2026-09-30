import unittest

from runtime.symbolic_answer import SymPyAnswerChecker


class Expr:
    def __init__(self, value):
        self.value = value

    def __sub__(self, other):
        return Expr(self.value - other.value)

    def __str__(self):
        return str(self.value)


class SymbolicAnswerCheckerTests(unittest.TestCase):
    def test_equivalent_when_simplified_difference_is_zero(self):
        checker = SymPyAnswerChecker(
            sympify=lambda value: Expr({"x+x": 2, "2*x": 2}[value]),
            simplify=lambda expr: expr.value,
        )
        result = checker.check("x+x", "2*x")
        self.assertTrue(result.equivalent)

    def test_non_equivalent_when_difference_remains(self):
        checker = SymPyAnswerChecker(
            sympify=lambda value: Expr(int(value)),
            simplify=lambda expr: expr.value,
        )
        result = checker.check("2", "3")
        self.assertFalse(result.equivalent)

    def test_parse_failure_is_unknown_not_incorrect(self):
        def bad(_value):
            raise ValueError("bad syntax")

        checker = SymPyAnswerChecker(sympify=bad, simplify=lambda value: value)
        result = checker.check("bad", "1")
        self.assertIsNone(result.equivalent)
        self.assertIn("parse_or_simplify_failed", result.reason)


if __name__ == "__main__":
    unittest.main()
