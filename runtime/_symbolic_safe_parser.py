"""Small arithmetic grammar for SymPy; never evaluate a Python expression string."""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass

MAX_CHARS = 4096
MAX_NODES = 128
MAX_DEPTH = 20
MAX_WEIGHT = 2048
MAX_BITS = 4096
MAX_DEGREE = 32
CONSTANTS = {"pi", "E", "I"}
FUNCTIONS = {"sin", "cos", "tan", "exp", "log", "ln", "sqrt", "Abs", "abs"}
NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,31}\Z")
NUMBER = re.compile(r"(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE]([+-]?[0-9]+))?\Z")


class UnsafeExpression(ValueError):
    pass


@dataclass(frozen=True)
class CheckedExpression:
    source: str
    tree: ast.Expression
    domain_unverified: bool


def _signed_integer(node: ast.AST) -> int:
    sign = 1
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        sign = -1 if isinstance(node.op, ast.USub) else 1
        node = node.operand
    if not isinstance(node, ast.Constant) or type(node.value) is not int:
        raise UnsafeExpression("integer_exponent_required")
    value = sign * node.value
    if abs(value) > 8:
        raise UnsafeExpression("exponent_budget_exceeded")
    return value


def validate_expression(source: str) -> CheckedExpression:
    if not isinstance(source, str) or not source.strip() or len(source) > MAX_CHARS:
        raise UnsafeExpression("expression_size_invalid")
    source = source.strip().replace("^", "**")
    if len(source) > MAX_CHARS or "#" in source:
        raise UnsafeExpression("expression_size_invalid")
    try:
        tree = ast.parse(source, mode="eval")
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise UnsafeExpression("unsupported_syntax") from exc
    if sum(1 for _ in ast.walk(tree)) > MAX_NODES:
        raise UnsafeExpression("node_budget_exceeded")
    symbols: set[str] = set()
    domain_unverified = False

    # Cost estimates reject explosive nested powers before constructing SymPy objects.
    def visit(node: ast.AST, depth: int = 0) -> tuple[int, int, int, bool]:
        nonlocal domain_unverified
        if depth > MAX_DEPTH:
            raise UnsafeExpression("depth_budget_exceeded")
        weight, bits, degree, has_symbol = 1, 1, 0, False
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            token = ast.get_source_segment(source, node) or ""
            match = NUMBER.fullmatch(token)
            if not match or len(token) > 64 or abs(int(match.group(1) or 0)) > 100:
                raise UnsafeExpression("numeric_literal_budget_exceeded")
            bits = 4 * (len(token) + abs(int(match.group(1) or 0)))
        elif isinstance(node, ast.Name):
            if not NAME.fullmatch(node.id) or "__" in node.id or node.id in {"nan", "oo", "zoo", "inf", "Infinity"}:
                raise UnsafeExpression("unsupported_symbol")
            has_symbol = node.id not in CONSTANTS
            if has_symbol:
                symbols.add(node.id)
                degree = 1
            if len(symbols) > 8:
                raise UnsafeExpression("symbol_budget_exceeded")
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            weight, bits, degree, has_symbol = visit(node.operand, depth + 1)
            weight += 1
        elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
            left = visit(node.left, depth + 1)
            if isinstance(node.op, ast.Pow):
                exponent = _signed_integer(node.right)
                visit(node.right, depth + 1)
                weight, bits, degree, has_symbol = left
                weight *= abs(exponent) + 1
                bits *= max(abs(exponent), 1)
                degree *= abs(exponent)
                domain_unverified |= exponent < 0 and has_symbol
            else:
                right = visit(node.right, depth + 1)
                weight = left[0] + right[0] + 1
                bits = left[1] + right[1]
                degree = max(left[2], right[2]) if isinstance(node.op, (ast.Add, ast.Sub)) else left[2] + right[2]
                has_symbol = left[3] or right[3]
                domain_unverified |= isinstance(node.op, ast.Div) and right[3]
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCTIONS and len(node.args) == 1 and not node.keywords:
            weight, bits, degree, has_symbol = visit(node.args[0], depth + 1)
            weight = weight * 2 + 1
            domain_unverified |= has_symbol and node.func.id in {"tan", "sqrt", "log", "ln"}
        else:
            raise UnsafeExpression("unsupported_syntax")
        if weight > MAX_WEIGHT or bits > MAX_BITS or degree > MAX_DEGREE:
            raise UnsafeExpression("complexity_budget_exceeded")
        return weight, bits, degree, has_symbol

    visit(tree.body)
    return CheckedExpression(source, tree, domain_unverified)


def to_sympy(checked: CheckedExpression):
    """Construct only explicit SymPy nodes from the previously checked AST."""
    import sympy as sp

    functions = {"sin": sp.sin, "cos": sp.cos, "tan": sp.tan, "exp": sp.exp,
                 "log": sp.log, "ln": sp.log, "sqrt": sp.sqrt, "Abs": sp.Abs, "abs": sp.Abs}
    constants = {"pi": sp.pi, "E": sp.E, "I": sp.I}

    def build(node: ast.AST):
        if isinstance(node, ast.Constant):
            # The numeric token has a closed lexical grammar, not arbitrary Python.
            return sp.Rational(ast.get_source_segment(checked.source, node))
        if isinstance(node, ast.Name):
            return constants.get(node.id, sp.Symbol(node.id))
        if isinstance(node, ast.UnaryOp):
            value = build(node.operand)
            return sp.Mul(-1, value, evaluate=False) if isinstance(node.op, ast.USub) else value
        if isinstance(node, ast.BinOp):
            left = build(node.left)
            if isinstance(node.op, ast.Pow):
                return sp.Pow(left, _signed_integer(node.right), evaluate=False)
            right = build(node.right)
            if isinstance(node.op, ast.Add): return sp.Add(left, right, evaluate=False)
            if isinstance(node.op, ast.Sub): return sp.Add(left, sp.Mul(-1, right, evaluate=False), evaluate=False)
            if isinstance(node.op, ast.Mult): return sp.Mul(left, right, evaluate=False)
            if isinstance(node.op, ast.Div): return sp.Mul(left, sp.Pow(right, -1, evaluate=False), evaluate=False)
        if isinstance(node, ast.Call):
            return functions[node.func.id](build(node.args[0]), evaluate=False)
        raise UnsafeExpression("unsupported_syntax")

    return build(checked.tree.body)
