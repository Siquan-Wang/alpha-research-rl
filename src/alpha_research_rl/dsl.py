"""Bounded causal array expressions interpreted directly from a validated AST."""

from __future__ import annotations

import ast
import math

import numpy as np
from scipy.stats import rankdata

from .data import MarketPanel

MAX_LOOKBACK = 60
MAX_NODES = 128
MAX_DEPTH = 16
MAX_LENGTH = 2048


class ExpressionError(ValueError):
    """A proposal violates the safe expression grammar."""


def _cross_section(x: np.ndarray, method: str) -> np.ndarray:
    result = np.full_like(x, np.nan)
    for t, row in enumerate(x):
        mask = np.isfinite(row)
        n = int(mask.sum())
        if not n:
            continue
        if method == "rank":
            result[t, mask] = (rankdata(row[mask], method="average") - 1) / (n - 1) if n > 1 else 0.5
        else:
            scale = row[mask].std()
            if scale > 0:
                result[t, mask] = (row[mask] - row[mask].mean()) / scale
    return result


def evaluate_expression(expression: str, panel: MarketPanel) -> np.ndarray:
    """Return [time,asset] values using information available at each row.

    Rolling windows include the current row and require k finite observations.
    delay/delta require positive k<=60. Undefined log/division/standardization
    yields NaN. Rank is cross-sectional, average ties, scaled to [0,1].
    Numeric finite constants (absolute value <=1e6) broadcast to the panel.
    """
    if not isinstance(expression, str) or not expression.strip() or len(expression) > MAX_LENGTH:
        raise ExpressionError("expression must be nonempty and at most 2048 characters")
    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, RecursionError, ValueError) as exc:
        raise ExpressionError("invalid expression syntax") from exc
    if sum(1 for _ in ast.walk(tree)) > MAX_NODES:
        raise ExpressionError("expression exceeds node limit")
    inputs = {"close": panel.close, "volume": panel.volume, "returns": panel.returns}
    unary = {"neg", "abs", "log", "rank", "zscore"}
    binary = {"add", "sub", "mul", "div"}
    temporal = {"delay", "delta", "ts_mean", "ts_std"}

    def validate(node: ast.AST, depth: int = 0) -> None:
        if depth > MAX_DEPTH:
            raise ExpressionError("expression exceeds depth limit")
        if isinstance(node, ast.Name) and node.id in inputs:
            if node.id not in panel.metadata.get("supported_features", inputs):
                raise ExpressionError(f"feature unavailable in source: {node.id}")
            return
        if isinstance(node, ast.Constant):
            if type(node.value) not in (int, float) or abs(node.value) > 1e6 or not math.isfinite(node.value):
                raise ExpressionError("only bounded finite numeric constants are allowed")
            return
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            validate(node.operand, depth + 1)
            return
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            validate(node.left, depth + 1)
            validate(node.right, depth + 1)
            return
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
            name = node.func.id
            if name in unary and len(node.args) == 1:
                validate(node.args[0], depth + 1)
                return
            if name in binary and len(node.args) == 2:
                for arg in node.args:
                    validate(arg, depth + 1)
                return
            if name in temporal and len(node.args) == 2:
                lookback = node.args[1]
                if not isinstance(lookback, ast.Constant) or type(lookback.value) is not int:
                    raise ExpressionError("lookback must be a literal positive integer")
                if not 1 <= lookback.value <= MAX_LOOKBACK:
                    raise ExpressionError("lookback must be between 1 and 60")
                validate(node.args[0], depth + 1)
                return
        raise ExpressionError(f"unsupported expression node: {type(node).__name__}")

    validate(tree.body)

    def array(value: np.ndarray | float) -> np.ndarray:
        return np.broadcast_to(value, panel.close.shape)

    def calculate(node: ast.AST) -> np.ndarray | float:
        if isinstance(node, ast.Name):
            return inputs[node.id]
        if isinstance(node, ast.Constant):
            return float(node.value)
        if isinstance(node, ast.UnaryOp):
            x = calculate(node.operand)
            return -x if isinstance(node.op, ast.USub) else x
        if isinstance(node, ast.BinOp):
            x, y = calculate(node.left), calculate(node.right)
            op = {ast.Add: "add", ast.Sub: "sub", ast.Mult: "mul", ast.Div: "div"}[type(node.op)]
            return arithmetic(op, x, y)
        name = node.func.id
        x = calculate(node.args[0])
        if name in binary:
            return arithmetic(name, x, calculate(node.args[1]))
        if name == "neg":
            return -x
        if name == "abs":
            return np.abs(x)
        if name == "log":
            return np.where(array(x) > 0, np.log(array(x)), np.nan)
        if name in {"rank", "zscore"}:
            return _cross_section(array(x), name)
        k = node.args[1].value
        values = array(x)
        result = np.full(panel.close.shape, np.nan)
        if name in {"delay", "delta"}:
            result[k:] = values[:-k] if name == "delay" else values[k:] - values[:-k]
            return result
        for t in range(k - 1, len(values)):
            window = values[t - k + 1:t + 1]
            mask = np.isfinite(window).all(axis=0)
            if mask.any():
                operation = np.mean if name == "ts_mean" else np.std
                result[t, mask] = operation(window[:, mask], axis=0)
        return result

    def arithmetic(name: str, x: np.ndarray | float, y: np.ndarray | float) -> np.ndarray:
        x, y = array(x), array(y)
        if name == "add":
            return x + y
        if name == "sub":
            return x - y
        if name == "mul":
            return x * y
        return np.divide(x, y, out=np.full(panel.close.shape, np.nan), where=y != 0)

    with np.errstate(divide="ignore", invalid="ignore", over="ignore", under="ignore"):
        result = np.array(array(calculate(tree.body)), dtype=float, copy=True)
    result[~np.isfinite(result)] = np.nan
    return result
