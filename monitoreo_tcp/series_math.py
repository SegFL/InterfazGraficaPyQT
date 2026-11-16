"""
series_math.py
Operaciones entre series y unidad del resultado. Sin dependencias de Qt.
"""
import numpy as np

OPS = {
    "sum": ("+", lambda a, b: a + b),
    "sub": ("-", lambda a, b: a - b),
    "mul": ("*", lambda a, b: a * b),
    "div": ("/", lambda a, b: a / b),
}

# (unidad A, unidad B) -> unidad del resultado
_MUL = {
    ("V", "A"): "W", ("A", "V"): "W",
    ("V", "mA"): "mW", ("mA", "V"): "mW",
    ("mV", "A"): "mW", ("A", "mV"): "mW",
    ("mV", "mA"): "uW", ("mA", "mV"): "uW",
}
_DIV = {
    ("V", "A"): "ohm", ("V", "mA"): "kohm",
    ("mV", "A"): "mohm", ("mV", "mA"): "ohm",
    ("W", "V"): "A", ("mW", "V"): "mA",
    ("W", "A"): "V", ("mW", "mA"): "V",
    ("mW", "mV"): "A",
}


def apply_op(op, ya, yb):
    """Opera por indice, trunca al largo menor. Devuelve (n, y)."""
    n = min(len(ya), len(yb))
    ya = np.asarray(ya[:n], float)
    yb = np.asarray(yb[:n], float)
    with np.errstate(divide="ignore", invalid="ignore"):
        y = OPS[op][1](ya, yb)
    y[~np.isfinite(y)] = np.nan
    return n, y


def result_unit(op, ua, ub):
    """Unidad del resultado. '' = adimensional o no determinable."""
    ua, ub = ua or "", ub or ""
    if op in ("sum", "sub"):
        return ua if ua == ub else ""
    if op == "mul":
        if (ua, ub) in _MUL:
            return _MUL[(ua, ub)]
        return "*".join(u for u in (ua, ub) if u)
    if op == "div":
        if ua == ub:
            return ""                      # cociente: adimensional
        if (ua, ub) in _DIV:
            return _DIV[(ua, ub)]
        if ua and ub:
            return f"{ua}/{ub}"
        return ua if ua else f"1/{ub}"
    return ""


def unit_warning(op, ua, ub):
    """Texto de aviso si se suma/resta entre unidades distintas, o ''."""
    if op in ("sum", "sub") and ua and ub and ua != ub:
        return f"ojo: {OPS[op][0]} entre unidades distintas ({ua} y {ub})"
    return ""