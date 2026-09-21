"""
series_selector.py
Matriz de checkboxes (filas = sensores, columnas = V / I / P) para elegir
qué series se grafican. Las filas se agregan dinámicamente cuando aparece
un sensor nuevo y quedan ordenadas por ID.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

# (clave interna, encabezado, tooltip)
MAGNITUDES = (
    ("v", "V", "Tensión"),
    ("i", "I", "Corriente"),
    ("p", "P", "Potencia"),
)


class SeriesSelector(QGroupBox):
    changed = Signal(int, str, bool)   # (sensor_id, magnitud, visible)

    def __init__(self, parent=None):
        super().__init__("Series visibles", parent)
        self._rows = {}                # sensor_id -> (QLabel, {mag: QCheckBox})

        outer = QVBoxLayout(self)
        self._grid = QGridLayout()
        self._grid.setHorizontalSpacing(14)
        outer.addLayout(self._grid)

        buttons = QHBoxLayout()
        b_all = QPushButton("Todas")
        b_none = QPushButton("Ninguna")
        b_all.clicked.connect(lambda: self.set_all(True))
        b_none.clicked.connect(lambda: self.set_all(False))
        buttons.addWidget(b_all)
        buttons.addWidget(b_none)
        outer.addLayout(buttons)
        outer.addStretch(1)

        self._grid.addWidget(QLabel("Sensor"), 0, 0)
        for col, (_, txt, tip) in enumerate(MAGNITUDES, start=1):
            lbl = QLabel(txt)
            lbl.setToolTip(tip)
            lbl.setAlignment(Qt.AlignCenter)
            self._grid.addWidget(lbl, 0, col)

    # -- API ------------------------------------------------------------
    def add_sensor(self, sensor_id: int):
        if sensor_id in self._rows:
            return
        label = QLabel(f"S{sensor_id}")
        boxes = {}
        for mag, _, tip in MAGNITUDES:
            cb = QCheckBox()
            cb.setChecked(True)                      # por defecto todo visible
            cb.setToolTip(f"{tip} - sensor {sensor_id}")
            cb.toggled.connect(
                lambda chk, s=sensor_id, m=mag: self.changed.emit(s, m, chk)
            )
            boxes[mag] = cb
        self._rows[sensor_id] = (label, boxes)
        self._relayout()

    def is_visible(self, sensor_id: int, mag: str) -> bool:
        row = self._rows.get(sensor_id)
        return True if row is None else row[1][mag].isChecked()

    def set_all(self, state: bool):
        for _, boxes in self._rows.values():
            for cb in boxes.values():
                cb.setChecked(state)

    # -- interno ----------------------------------------------------------
    def _relayout(self):
        """Reubica las filas ordenadas por sensor_id (encabezado = fila 0)."""
        for row, sid in enumerate(sorted(self._rows), start=1):
            label, boxes = self._rows[sid]
            self._grid.removeWidget(label)
            self._grid.addWidget(label, row, 0)
            for col, (mag, _, _) in enumerate(MAGNITUDES, start=1):
                self._grid.removeWidget(boxes[mag])
                self._grid.addWidget(boxes[mag], row, col, alignment=Qt.AlignCenter)