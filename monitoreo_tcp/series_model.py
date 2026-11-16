"""
series_model.py
Lectura de CSV y reparto de ejes Y por unidad. Sin dependencias de Qt.

read_csv(path) -> LoadedCsv
    .time            np.ndarray, en segundos
    .series          {clave: (Column, np.ndarray)} solo columnas con datos
    .synthetic_time  True si el archivo no tenia columna de tiempo (se uso
                     el indice de muestra 0, 1, 2, ...)
    .warnings        avisos (columnas descartadas, filas ignoradas)

Las columnas completamente vacias / NaN se descartan, asi un CSV generado por
la herramienta de matematicas (una sola columna con datos y el resto en 'nan')
se relee como una sola serie.
"""
import csv
from dataclasses import dataclass, field

import numpy as np

from csv_header import Column, parse_columns, pick_time, time_scale

MAX_AXES = 3   # ejes Y simultaneos: 1 izquierdo + 2 derechos


@dataclass
class LoadedCsv:
    time: np.ndarray
    series: dict
    synthetic_time: bool = False
    warnings: list = field(default_factory=list)


def _to_float(text: str) -> float:
    t = text.strip().replace(",", ".")
    return float("nan") if t == "" else float(t)


def read_csv(path: str) -> LoadedCsv:
    with open(path, newline="", encoding="utf-8-sig") as f:
        first = f.readline()
        f.seek(0)
        # Separador: el que mas aparece en el encabezado (';' gana empates,
        # porque con coma decimal ',' tambien aparece en los datos).
        delim = max(";,\t", key=lambda d: (first.count(d), d == ";"))
        if first.count(delim) == 0:
            delim = ";"          # archivo de una sola columna
        reader = csv.reader(f, delimiter=delim)
        try:
            header = next(reader)
        except StopIteration:
            raise ValueError("archivo vacio")
        rows = list(reader)

    cols = parse_columns(header)
    warnings = []

    good = [r for r in rows if len(r) == len(header)]
    if len(good) < len(rows):
        warnings.append(f"{len(rows) - len(good)} fila(s) ignoradas por columnas incompletas")
    if not good:
        raise ValueError("sin filas de datos validas")

    arrays = {}
    for c in cols:
        try:
            arrays[c.key] = np.array([_to_float(r[c.index]) for r in good], float)
        except ValueError:
            warnings.append(f"columna '{c.raw}' no numerica, descartada")

    tcol = pick_time(cols)
    if tcol is not None and tcol.key in arrays:
        t = arrays[tcol.key] * time_scale(tcol)
        synthetic = False
    else:
        t = np.arange(len(good), dtype=float)
        synthetic = True
        warnings.append("sin columna de tiempo: se uso el indice de muestra")

    series = {}
    for c in cols:
        if tcol is not None and c.key == tcol.key:
            continue
        y = arrays.get(c.key)
        if y is None:
            continue
        if np.all(np.isnan(y)):
            warnings.append(f"columna '{c.raw}' vacia, descartada")
            continue
        series[c.key] = (c, y)

    if not series:
        raise ValueError("el archivo no tiene columnas de datos")
    return LoadedCsv(t, series, synthetic, warnings)


def axis_slot(unit: str, slots: list) -> int:
    """Indice de eje para 'unit'. 'slots' es la lista de unidades ya asignadas
    (se modifica); un None es un eje libre y se reutiliza. Pasado MAX_AXES,
    las unidades nuevas comparten el ultimo eje."""
    if unit in slots:
        return slots.index(unit)
    if None in slots:
        i = slots.index(None)
        slots[i] = unit
        return i
    if len(slots) < MAX_AXES:
        slots.append(unit)
        return len(slots) - 1
    return MAX_AXES - 1