"""Artificial adapter contracts only; no benchmark import, evaluator or transport.

This is an ordinary API boundary, not a sandbox for hostile Python callers.
"""
from __future__ import annotations

import ast
import copy
import json
import math
import operator
from collections.abc import Callable, Sequence


class ContractError(ValueError):
    pass


class ExpressionError(ContractError):
    pass


FUNCTIONS = {name: getattr(math, name) for name in ("sin", "cos", "exp", "log", "sqrt")}
FUNCTIONS["abs"] = abs
CONSTANTS = {"pi": math.pi, "e": math.e}
BINARY = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
          ast.Div: operator.truediv, ast.Pow: operator.pow}
GRAMMAR = {
    "binary": ["+", "-", "*", "/", "**"], "unary": ["+", "-"],
    "functions": sorted(FUNCTIONS), "named_constants": sorted(CONSTANTS),
    "power_exponent": "finite numeric literal, optionally unary signed",
    "max_characters": 2048, "max_ast_nodes": 128, "max_ast_depth": 20,
    "numeric_semantics": "Python finite real float; domain/overflow/nonfinite is invalid; no clipping",
}


def _number(value: object) -> float:
    if type(value) not in (int, float):
        raise ContractError("expected a finite real number, excluding bool")
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise ContractError("number is not representable as finite float") from exc
    if not math.isfinite(result):
        raise ContractError("expected finite number")
    return result


def _literal(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return type(node.value) in (int, float)
    return (isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub))
            and isinstance(node.operand, ast.Constant)
            and type(node.operand.value) in (int, float))


class SafeExpression:
    """Interpret a finite mathematical AST; never execute a Python program."""

    def __init__(self, source: str, variables: Sequence[str]):
        if type(source) is not str or not source or len(source) > 2048:
            raise ExpressionError("expression must contain 1..2048 characters")
        if not isinstance(variables, (list, tuple)) or not variables:
            raise ExpressionError("ordered nonempty variables required")
        if any(type(v) is not str or not v.isascii() or not v.isidentifier()
               or v in FUNCTIONS or v in CONSTANTS for v in variables):
            raise ExpressionError("invalid or reserved variable name")
        if len(set(variables)) != len(variables):
            raise ExpressionError("duplicate variable")
        self.source, self.variables = source, tuple(variables)
        try:
            tree = ast.parse(source, mode="eval")
        except (SyntaxError, ValueError, RecursionError) as exc:
            raise ExpressionError("invalid expression syntax; no repair") from exc
        if sum(1 for _ in ast.walk(tree)) > 128:
            raise ExpressionError("too many AST nodes")

        def validate(n: ast.AST, depth: int) -> None:
            if depth > 20:
                raise ExpressionError("AST too deep")
            if isinstance(n, ast.Constant):
                _number(n.value)
            elif isinstance(n, ast.Name) and n.id in (*self.variables, *CONSTANTS):
                return
            elif isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
                validate(n.operand, depth + 1)
            elif isinstance(n, ast.BinOp) and type(n.op) in BINARY:
                if isinstance(n.op, ast.Pow) and not _literal(n.right):
                    raise ExpressionError("power requires a literal exponent")
                validate(n.left, depth + 1)
                validate(n.right, depth + 1)
            elif (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                  and n.func.id in FUNCTIONS and len(n.args) == 1 and not n.keywords):
                validate(n.args[0], depth + 1)
            else:
                raise ExpressionError("node outside expression grammar")
        try:
            validate(tree.body, 1)
        except ContractError as exc:
            raise ExpressionError(str(exc)) from exc
        self._root = tree.body

    def evaluate(self, point: Sequence[float]) -> float:
        if not isinstance(point, (list, tuple)) or len(point) != len(self.variables):
            raise ExpressionError("point dimension mismatch")
        env = dict(zip(self.variables, map(_number, point)))

        def visit(n: ast.AST) -> float:
            if isinstance(n, ast.Constant):
                value = float(n.value)
            elif isinstance(n, ast.Name):
                value = env[n.id] if n.id in env else CONSTANTS[n.id]
            elif isinstance(n, ast.UnaryOp):
                value = visit(n.operand) * (-1 if isinstance(n.op, ast.USub) else 1)
            elif isinstance(n, ast.BinOp):
                value = BINARY[type(n.op)](visit(n.left), visit(n.right))
            else:
                value = FUNCTIONS[n.func.id](visit(n.args[0]))
            return _number(value)
        try:
            return visit(self._root)
        except (ArithmeticError, ValueError, TypeError) as exc:
            raise ExpressionError("invalid numerical prediction") from exc


def signed_utility(prediction: Sequence[float], truth: Sequence[float]) -> dict:
    """Scale-invariant mathematically; floating-point limits are explicit."""
    if not isinstance(truth, (list, tuple)) or not truth:
        raise ContractError("nonempty truth vector required")
    y = tuple(map(_number, truth))
    zero = all(v == 0 for v in y)
    if not isinstance(prediction, (list, tuple)) or len(prediction) != len(y):
        raise ContractError("prediction length must preserve every target")
    try:
        p = tuple(map(_number, prediction))
    except ContractError:
        return {"U": 0.0, "status": "invalid_prediction", "degenerate_target": zero,
                "relative_squared_error": None, "numerical_limit": None}
    if zero:
        return {"U": float(all(v == 0 for v in p)), "status": "degenerate_target",
                "degenerate_target": True, "relative_squared_error": None,
                "numerical_limit": "relative error undefined for exact zero target"}
    scale = max(map(abs, (*y, *p)))
    scaled_y = tuple(v / scale for v in y)
    residuals = tuple(a / scale - b / scale for a, b in zip(p, y))
    energy = math.fsum(v ** 2 for v in scaled_y)
    error = math.fsum(v ** 2 for v in residuals)
    utility = energy / (energy + error)
    relative = error / energy if energy else math.inf
    limits = []
    if any(v != 0 and (s == 0 or s * s == 0) for v, s in zip(y, scaled_y)):
        limits.append("nonzero target component lost at scaling/squaring")
    if any(a != b and (r == 0 or r * r == 0) for a, b, r in zip(p, y, residuals)):
        limits.append("nonzero residual lost at scaling/squaring")
        if error == 0:
            relative = None
    if relative == 0 and error > 0:
        relative = None
        limits.append("positive relative squared error underflow")
    if relative is not None and not math.isfinite(relative):
        relative = None
        limits.append("relative squared error exceeds float range")
    if energy == 0:
        limits.append("scaled target energy underflow; raw target was nonzero")
    return {"U": utility, "status": "ok", "degenerate_target": False,
            "relative_squared_error": relative, "numerical_limit": "; ".join(limits) or None}


def _strict_json(raw: str) -> object:
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise ContractError("duplicate JSON key")
            obj[key] = value
        return obj
    def reject(value):
        raise ContractError("nonfinite JSON number: " + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)


class ScalarBroker:
    """Budget is submitted point attempts; malformed and duplicate attempts count.

    The actor receives only submit and public metadata. The trusted owner retains
    this object and callback. Introspection resistance is explicitly not claimed.
    """

    def __init__(self, bounds: Sequence[Sequence[float]], budget: int,
                 oracle: Callable[[tuple[float, ...]], float]):
        if type(budget) is not int or budget <= 0 or not callable(oracle):
            raise ContractError("positive integer budget and trusted callback required")
        if not isinstance(bounds, (list, tuple)) or not bounds:
            raise ContractError("nonempty ordered bounds required")
        checked = []
        for pair in bounds:
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise ContractError("bounds must be pairs")
            lo, hi = map(_number, pair)
            if lo >= hi:
                raise ContractError("bounds must be increasing")
            checked.append((lo, hi))
        self.bounds, self.budget = tuple(checked), budget
        self._oracle, self._records, self._seen = oracle, [], {}
        self.state = "OPEN"

    @property
    def trace(self) -> list[dict]:
        return copy.deepcopy(self._records)

    def submit(self, raw: str) -> dict:
        if self.state != "OPEN" or len(self._records) >= self.budget:
            raise ContractError("broker closed or attempt budget exhausted")
        record = {"attempt": len(self._records) + 1, "raw_request": raw if type(raw) is str else None,
                  "status": "invalid_request", "point": None, "value": None,
                  "duplicate_of": None, "error_type": None}
        self._records.append(record)
        try:
            if type(raw) is not str:
                raise ContractError("request must be JSON text")
            obj = _strict_json(raw)
            if type(obj) is not dict or set(obj) != {"x"} or type(obj["x"]) is not list:
                raise ContractError("request must have only x array")
            if len(obj["x"]) != len(self.bounds):
                raise ContractError("point dimension mismatch")
            point = tuple(map(_number, obj["x"]))
            if any(not lo <= x <= hi for x, (lo, hi) in zip(point, self.bounds)):
                raise ContractError("point outside prospective bounds")
        except (ContractError, ValueError, TypeError, RecursionError) as exc:
            record["error_type"] = type(exc).__name__
            return copy.deepcopy(record)
        record["point"] = list(point)
        record["duplicate_of"] = self._seen.get(point)
        self._seen.setdefault(point, record["attempt"])
        try:
            record["value"] = _number(self._oracle(point))
        except BaseException as exc:
            record["status"], record["error_type"], self.state = "oracle_failure", type(exc).__name__, "FAILED"
            raise
        record["status"] = "ok"
        return copy.deepcopy(record)

    def freeze(self) -> list[dict]:
        if self.state != "OPEN":
            raise ContractError("only open broker can freeze")
        self.state = "FROZEN"
        return self.trace
