import importlib.util
import json
import subprocess
import sys
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from runtime._symbolic_safe_parser import UnsafeExpression, validate_expression
from runtime.symbolic_answer import SymPyAnswerChecker


class SymbolicInputBoundaryTests(unittest.TestCase):
    def test_rejects_non_math_before_any_parser_or_worker_call(self):
        expressions = [
            "__import__('os')", "open('example.txt')", "x.__class__", "x[0]",
            "lambda: 1", "[x for x in y]", "{'x': 1}", "(x := 1)", "x; 1",
            "sin(x, evaluate=True)", "sin(*x)", "sum(x)", "factorial(100)",
            "Integral(x, x)", "True", "None", "'x'", "x // 2", "x % 2",
            "x << 2", "x and y", "1 if x else 2", "x # comment", "nan", "0x10",
        ]
        for expression in expressions:
            with self.subTest(expression=expression):
                parser, simplify = Mock(), Mock()
                checker = SymPyAnswerChecker(sympify=parser, simplify=simplify)
                result = checker.check(expression, "1")
                self.assertIsNone(result.equivalent)
                self.assertTrue(result.reason.startswith("unsupported_expression:"))
                parser.assert_not_called()
                simplify.assert_not_called()

    def test_expected_answer_has_the_same_input_boundary(self):
        parser = Mock()
        checker = SymPyAnswerChecker(sympify=parser, simplify=Mock())
        self.assertIsNone(checker.check("1", "x.__class__").equivalent)
        parser.assert_not_called()

    def test_limits_size_depth_nodes_exponents_and_numeric_growth(self):
        expressions = ["x" * 4097, "1e101", "9" * 65, "x**9", "2**(2**8)",
                       "(((9**8)**8)**8)**8", "x**0.5", "+".join(["x"] * 100),
                       "a+b+c+d+e+f+g+h+j", "(x**8)**8", "-" * 40 + "1"]
        for expression in expressions:
            with self.subTest(expression=expression):
                with self.assertRaises(UnsafeExpression):
                    validate_expression(expression)

    def test_domain_sensitive_input_is_unknown_without_calling_parser(self):
        for expression in ["x/x", "1/x", "x**-1", "sqrt(x)", "log(x)", "tan(x)"]:
            with self.subTest(expression=expression):
                parser = Mock()
                result = SymPyAnswerChecker(sympify=parser, simplify=Mock()).check(expression, "1")
                self.assertIsNone(result.equivalent)
                self.assertEqual(result.reason, "domain_unverified")
                parser.assert_not_called()

    def test_simple_math_is_accepted_without_loading_sympy(self):
        for expression in ["x+x", "(x+1)^2", "1e-20", "0.1+0.2", "sin(x)^2+cos(x)^2", "Abs(x)", "sqrt(4)"]:
            with self.subTest(expression=expression):
                self.assertFalse(validate_expression(expression).domain_unverified)

    def test_empty_type_and_configuration_errors_remain_explicit(self):
        checker = SymPyAnswerChecker(sympify=Mock(), simplify=Mock())
        with self.assertRaises(ValueError): checker.check("", "1")
        with self.assertRaises(TypeError): checker.check(1, "1")
        for timeout in [-1, 0, 11, float("nan"), True]:
            with self.assertRaises(ValueError): SymPyAnswerChecker(sympify=Mock(), simplify=Mock(), timeout_seconds=timeout)
        with self.assertRaises(TypeError): SymPyAnswerChecker(sympify=Mock())

    @patch("runtime.symbolic_answer.importlib.util.find_spec", return_value=object())
    def test_timeout_and_worker_failure_are_unknown_not_wrong(self, _find_spec):
        checker = SymPyAnswerChecker()
        with patch("runtime.symbolic_answer.subprocess.run", side_effect=subprocess.TimeoutExpired("worker", 5)):
            self.assertEqual(checker.check("1", "1").reason, "symbolic_timeout")
        with patch("runtime.symbolic_answer.subprocess.run", side_effect=OSError()):
            self.assertEqual(checker.check("1", "1").reason, "symbolic_worker_unavailable")
        with patch("runtime.symbolic_answer.subprocess.run", return_value=Mock(returncode=1, stdout="")):
            self.assertEqual(checker.check("1", "1").reason, "symbolic_worker_failed")

    @patch("runtime.symbolic_answer.importlib.util.find_spec", return_value=object())
    def test_runtime_engine_pin_is_verified_before_accepting_a_boolean(self, _find_spec):
        checker = SymPyAnswerChecker()
        payload = json.dumps({"equivalent": True, "reason": "symbolic_difference_zero", "engine_version": "unverified"})
        with patch("runtime.symbolic_answer.subprocess.run", return_value=Mock(returncode=0, stdout=payload)):
            result = checker.check("1", "1")
            self.assertIsNone(result.equivalent)
            self.assertEqual(result.reason, "symbolic_engine_version_mismatch")

    @patch("runtime.symbolic_answer.importlib.util.find_spec", return_value=object())
    def test_bad_worker_protocol_is_unknown_and_answers_use_stdin(self, _find_spec):
        checker = SymPyAnswerChecker()
        for payload in ["not json", "[]", '{}', '{"equivalent":"true","reason":"wrong type"}',
                        json.dumps({"equivalent": True, "reason": "symbolic_difference_zero", "engine_version": "1.14.0", "normalized_student": "x" * 4097}),
                        json.dumps({"equivalent": True, "reason": "symbolic_timeout", "engine_version": "1.14.0"})]:
            with self.subTest(payload=payload[:50]):
                with patch("runtime.symbolic_answer.subprocess.run", return_value=Mock(returncode=0, stdout=payload)) as runner:
                    self.assertIsNone(checker.check("x+x", "2*x").equivalent)
                    args, kwargs = runner.call_args
                    self.assertNotIn("x+x", args[0])
                    self.assertEqual(json.loads(kwargs["input"]), {"student": "x+x", "expected": "2*x"})
                    self.assertEqual(kwargs["timeout"], 5.0)
                    self.assertFalse(kwargs.get("shell", False))


@unittest.skipUnless(importlib.util.find_spec("sympy"), "install requirements-extras/symbolic.txt for real SymPy checks")
class RealSymPyWorkerTests(unittest.TestCase):
    def setUp(self):
        self.checker = SymPyAnswerChecker()

    def test_real_polynomial_trigonometry_and_exact_decimal_identities(self):
        for left, right in [("x+x", "2*x"), ("(x+1)^2", "x^2+2*x+1"),
                            ("sin(x)^2+cos(x)^2", "1"), ("0.1+0.2", "0.3"),
                            ("sqrt(4)", "2"), ("I^2", "-1"), ("sin(pi)", "0")]:
            with self.subTest(left=left, right=right):
                result = self.checker.check(left, right)
                self.assertIs(result.equivalent, True, result)

    def test_real_definite_mismatch_and_undetermined_symbolic_result(self):
        self.assertIs(self.checker.check("2", "3").equivalent, False)
        result = self.checker.check("x", "2*x")
        self.assertIsNone(result.equivalent)
        self.assertEqual(result.reason, "symbolic_result_undetermined")

    def test_undefined_numeric_inputs_cannot_cancel_to_a_correct_answer(self):
        for left, right in [("1/0", "1/0"), ("1/(1-1)", "0"), ("log(0)", "log(0)")]:
            with self.subTest(left=left):
                result = self.checker.check(left, right)
                self.assertIsNone(result.equivalent, result)
                self.assertEqual(result.reason, "undefined_expression")

    def test_cli_runs_real_comparison_without_claiming_a_grade(self):
        root = Path(__file__).resolve().parents[1]
        completed = subprocess.run([sys.executable, str(root / "tools/check_symbolic_answer.py")],
            input=json.dumps({"student": "x+x", "expected": "2*x"}),
            text=True, capture_output=True, timeout=10, check=True)
        result = json.loads(completed.stdout)
        self.assertIs(result["equivalent"], True)
        self.assertIs(result["automatic_grade"], False)
        self.assertEqual(result["schema_version"], "symbolic_diagnostic_v1")

    def test_default_path_does_not_call_sympify_on_expression_strings(self):
        # Patch the upstream string-to-expression entrypoint inside a local script.
        # The default worker is separately process-bound; this checks the constructor bridge.
        import sympy
        from runtime._symbolic_safe_parser import to_sympy
        original = sympy.sympify
        def guarded(value, *args, **kwargs):
            if isinstance(value, str): raise AssertionError("string sympify is forbidden")
            return original(value, *args, **kwargs)
        with patch.object(sympy, "sympify", side_effect=guarded):
            expression = to_sympy(validate_expression("sin(x)^2+cos(x)^2"))
            self.assertEqual(sympy.simplify(expression), 1)


if __name__ == "__main__":
    unittest.main()
