import numpy as np

OPS = {
    "sum": ("+", lambda a, b: a + b),
    "sub": ("-", lambda a, b: a - b),
    "mul": ("*", lambda a, b: a * b),
    "div": ("/", lambda a, b: a / b),
}


def apply_op(op, ya, yb):
    """Opera por índice, trunca al largo menor. Devuelve (n, y)."""
    n = min(len(ya), len(yb))
    ya = np.asarray(ya[:n], float)
    yb = np.asarray(yb[:n], float)
    with np.errstate(divide="ignore", invalid="ignore"):
        y = OPS[op][1](ya, yb)
    y[~np.isfinite(y)] = np.nan
    return n, y