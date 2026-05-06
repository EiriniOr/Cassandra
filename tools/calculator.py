import ast
import math
import operator

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_ALLOWED = {
    "sqrt": math.sqrt,
    "log": math.log,
    "log2": math.log2,
    "log10": math.log10,
    "exp": math.exp,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "atan2": math.atan2,
    "abs": abs,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "min": min,
    "max": max,
    "sum": sum,
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


def _eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _OPS[type(node.op)](_eval(node.operand))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return _ALLOWED[node.func.id](*[_eval(a) for a in node.args])
    if isinstance(node, ast.Name) and node.id in _ALLOWED:
        return _ALLOWED[node.id]
    if isinstance(node, ast.Tuple):
        return tuple(_eval(e) for e in node.elts)
    if isinstance(node, ast.List):
        return [_eval(e) for e in node.elts]
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


def calculate(expression: str):
    """Safely evaluate a math expression. Supports +-*/%**, math.* functions, pi/e/tau."""
    try:
        tree = ast.parse(expression, mode="eval")
        return str(_eval(tree.body))
    except Exception as exc:
        return f"Error: {exc}"


SCHEMA = {
    "name": "calculate",
    "description": "Evaluate a math expression. Supports +,-,*,/,%,**, sqrt, log, log2, log10, exp, sin, cos, tan, asin, acos, atan, atan2, abs, round, floor, ceil, min, max, sum. Constants: pi, e, tau.",
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Math expression, e.g. 'sqrt(2) * pi' or '(1+2) * 3'",
            }
        },
        "required": ["expression"],
    },
}
