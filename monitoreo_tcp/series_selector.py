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

MAGNITUDES = (
    ("v", "V", "Tensión"),
    ("i", "I", "Corriente"),
    ("p", "P", "Potencia"),
)


class SeriesSelector(QGroupBox):
    changed = Signal(int, str, bool)
    remove_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__("Series visibles", parent)
        self._rows = {}

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

    def add_sensor(self, sensor_id: int):
        if sensor_id in self._rows:
            return
        label = QLabel(f"S{sensor_id}")
        boxes = {}
        for mag, _, tip in MAGNITUDES:
            cb = QCheckBox()
            cb.setChecked(True)
            cb.setToolTip(f"{tip} - sensor {sensor_id}")
            cb.toggled.connect(
                lambda chk, s=sensor_id, m=mag: self.changed.emit(s, m, chk)
            )
            boxes[mag] = cb

        btn_remove = QPushButton("✕")
        btn_remove.setFixedWidth(24)
        btn_remove.setToolTip(f"Quitar sensor {sensor_id}")
        btn_remove.clicked.connect(lambda: self.remove_requested.emit(sensor_id))

        self._rows[sensor_id] = (label, boxes, btn_remove)
        self._relayout()

    def remove_sensor(self, sensor_id: int):
        row = self._rows.pop(sensor_id, None)
        if row is None:
            return
        label, boxes, btn_remove = row
        for w in (label, *boxes.values(), btn_remove):
            self._grid.removeWidget(w)
            w.deleteLater()
        self._relayout()

    def is_visible(self, sensor_id: int, mag: str) -> bool:
        row = self._rows.get(sensor_id)
        return True if row is None else row[1][mag].isChecked()

    def set_all(self, state: bool):
        for _, boxes, _ in self._rows.values():
            for cb in boxes.values():
                cb.setChecked(state)

    def _relayout(self):
        for row, sid in enumerate(sorted(self._rows), start=1):
            label, boxes, btn_remove = self._rows[sid]
            self._grid.removeWidget(label)
            self._grid.addWidget(label, row, 0)
            for col, (mag, _, _) in enumerate(MAGNITUDES, start=1):
                self._grid.removeWidget(boxes[mag])
                self._grid.addWidget(boxes[mag], row, col, alignment=Qt.AlignCenter)
            self._grid.removeWidget(btn_remove)
            self._grid.addWidget(btn_remove, row, len(MAGNITUDES) + 1)