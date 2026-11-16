"""
csv_header.py
Interpreta encabezados de CSV de la forma  "nombre [unidad]"  y los mapea a
magnitudes conocidas (tiempo, corriente, tension, tension de bus, potencia)
o a magnitudes genericas (eficiencia, ruido, ...). Sin dependencias de Qt.

Formatos aceptados por columna:
    Corriente [mA]    Corriente (mA)    Corriente_mA (formato legado)    Eficiencia
"""
import re
import unicodedata
from dataclasses import dataclass

# clave canonica -> (nombre de display, unidad por defecto)
KNOWN = {
    "time":    ("Tiempo",        "s"),
    "current": ("Corriente",     "mA"),
    "voltage": ("Tension",       "V"),
    "vbus":    ("Tension de bus", "V"),
    "power":   ("Potencia",      "mW"),
}

# nombre normalizado (exacto, no subcadena) -> clave canonica
ALIASES = {
    "tiempo": "time", "time": "time", "t": "time",
    "corriente": "current", "current": "current", "i": "current",
    "tension": "voltage", "voltaje": "voltage", "voltage": "voltage",
    "volt": "voltage", "v": "voltage",
    "tension de bus": "vbus", "tension bus": "vbus", "bus": "vbus",
    "vbus": "vbus", "v bus": "vbus", "bus voltage": "vbus",
    "voltaje de bus": "vbus",
    "potencia": "power", "power": "power", "p": "power",
}

# unidad en minusculas -> escritura canonica
UNITS = {
    "s": "s", "ms": "ms", "us": "us",
    "v": "V", "mv": "mV", "uv": "uV",
    "a": "A", "ma": "mA", "ua": "uA",
    "w": "W", "mw": "mW", "uw": "uW",
    "%": "%", "db": "dB", "hz": "Hz", "khz": "kHz",
    "j": "J", "mj": "mJ", "ohm": "ohm", "mvrms": "mVrms", "vrms": "Vrms",
}

TIME_TO_SECONDS = {"s": 1.0, "ms": 1e-3, "us": 1e-6}

# [unidad]: acepta cualquier contenido sin corchetes anidados.
_SQUARE_RE = re.compile(r"^(.*?)\s*\[\s*([^\[\]]*?)\s*\]\s*$")
# (unidad): solo se acepta si el contenido es una unidad conocida, para no
# confundir nombres de series generadas como "V(S1000)+V(S1001)".
_PAREN_RE = re.compile(r"^(.*?)\s*\(\s*([^()]*?)\s*\)\s*$")


@dataclass
class Column:
    index: int          # posicion en el archivo
    key: str            # clave interna unica ("voltage", "efficiency", ...)
    name: str           # nombre para mostrar
    unit: str           # unidad canonica ("" si es adimensional / desconocida)
    raw: str            # encabezado original
    known: bool         # True si es una de las magnitudes de KNOWN

    @property
    def label(self) -> str:
        return format_header(self.name, self.unit)


def normalize(text: str) -> str:
    """minusculas, sin tildes, '_' y espacios multiples -> un espacio."""
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.replace("_", " ").lower().strip()
    return re.sub(r"\s+", " ", t)


def canon_unit(unit: str) -> str:
    u = unit.strip()
    return UNITS.get(u.lower(), u)


def format_header(name: str, unit: str) -> str:
    return f"{name} [{unit}]" if unit else name


def split_header(header: str):
    """'Corriente [mA]' -> ('Corriente', 'mA'). Sin unidad -> (nombre, '')."""
    h = header.strip().lstrip("\ufeff")
    m = _SQUARE_RE.match(h)
    if m and m.group(1):
        return m.group(1).strip(), canon_unit(m.group(2))
    m = _PAREN_RE.match(h)
    if m and m.group(1) and m.group(2).lower() in UNITS:
        return m.group(1).strip(), canon_unit(m.group(2))
    # formato legado: sufijo tras el ultimo '_' si es una unidad conocida
    if "_" in h:
        base, suf = h.rsplit("_", 1)
        if base and suf.lower() in UNITS:
            return base.strip(), canon_unit(suf)
    return h, ""


def _slug(norm_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", norm_name).strip("_") or "col"


def parse_header(header: str, index: int = 0) -> Column:
    name, unit = split_header(header)
    norm = normalize(name)
    key = ALIASES.get(norm)
    if key:
        disp, default_unit = KNOWN[key]
        return Column(index, key, disp, unit or default_unit, header, True)
    return Column(index, _slug(norm), name, unit, header, False)


def parse_columns(headers) -> list:
    """Lista de Column con claves unicas (sufijo _2, _3 si se repiten)."""
    cols, seen = [], {}
    for i, h in enumerate(headers):
        c = parse_header(h, i)
        n = seen.get(c.key, 0) + 1
        seen[c.key] = n
        if n > 1:
            c.key = f"{c.key}_{n}"
            c.name = f"{c.name} ({n})"
        cols.append(c)
    return cols


def time_scale(col: Column) -> float:
    """Factor para convertir la columna de tiempo a segundos."""
    return TIME_TO_SECONDS.get(col.unit, 1.0)


def pick_time(cols):
    """Columna de tiempo, o None si no existe."""
    return next((c for c in cols if c.key == "time"), None)