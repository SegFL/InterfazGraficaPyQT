"""
series_selector.py
Arbol de series visibles: un grupo por sensor / archivo y, debajo, una fila
tildable por cada serie (columna del CSV) con su unidad.

    v S1000 (legacy.csv)                     x
        [x] Tension [V]
        [x] Corriente [mA]
    v V(S1000)+V(S1001)                      x
        [x] Tension [V]

API (compatible con la version de matriz):
    add_sensor(sensor_id, label=None, series=None)
    remove_sensor(sensor_id)
    is_visible(sensor_id, key) -> bool
    set_all(state)
    checked() -> [(sensor_id, key), ...]
Senales:
    changed(sensor_id, key, visible)
    remove_requested(sensor_id)
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

# Series de la ESP32 (clave, texto de la fila)
DEFAULT_SERIES = (
    ("voltage", "Tensión [V]"),
    ("current", "Corriente [mA]"),
    ("power", "Potencia [mW]"),
)

_ROLE = Qt.UserRole


class SeriesSelector(QGroupBox):
    changed = Signal(int, str, bool)
    remove_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__("Series visibles", parent)
        self._groups = {}            # sensor_id -> QTreeWidgetItem (grupo)

        outer = QVBoxLayout(self)

        self._tree = QTreeWidget()
        self._tree.setColumnCount(2)
        self._tree.setHeaderHidden(True)
        self._tree.setRootIsDecorated(True)
        self._tree.setUniformRowHeights(True)
        self._tree.setMinimumWidth(220)
        hdr = self._tree.header()
        hdr.setStretchLastSection(False)
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.Fixed)
        self._tree.setColumnWidth(1, 28)
        self._tree.itemChanged.connect(self._on_item_changed)
        outer.addWidget(self._tree, 1)

        buttons = QHBoxLayout()
        b_all = QPushButton("Todas")
        b_none = QPushButton("Ninguna")
        b_all.clicked.connect(lambda: self.set_all(True))
        b_none.clicked.connect(lambda: self.set_all(False))
        buttons.addWidget(b_all)
        buttons.addWidget(b_none)
        outer.addLayout(buttons)

    # -- API ------------------------------------------------------------
    def add_sensor(self, sensor_id: int, label: str = None, series=None):
        """series: iterable de (clave, texto). Por defecto V / I / P."""
        if sensor_id in self._groups:
            return
        title = label or f"S{sensor_id}"

        self._tree.blockSignals(True)
        group = QTreeWidgetItem()
        group.setText(0, title)
        group.setToolTip(0, title)
        group.setFlags(
            Qt.ItemIsEnabled | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate
        )
        group.setData(0, _ROLE, None)

        for key, text in (series if series is not None else DEFAULT_SERIES):
            child = QTreeWidgetItem(group)
            child.setText(0, text)
            child.setToolTip(0, f"{text} - {title}")
            child.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            child.setCheckState(0, Qt.Checked)
            child.setData(0, _ROLE, (sensor_id, key))

        index = sum(1 for sid in self._groups if sid < sensor_id)
        self._tree.insertTopLevelItem(index, group)
        group.setExpanded(True)
        self._groups[sensor_id] = group

        btn = QPushButton("✕")
        btn.setFixedWidth(24)
        btn.setToolTip(f"Quitar {title}")
        btn.clicked.connect(lambda: self.remove_requested.emit(sensor_id))
        self._tree.setItemWidget(group, 1, btn)
        self._tree.blockSignals(False)

    def remove_sensor(self, sensor_id: int):
        group = self._groups.pop(sensor_id, None)
        if group is None:
            return
        self._tree.takeTopLevelItem(self._tree.indexOfTopLevelItem(group))

    def is_visible(self, sensor_id: int, key: str) -> bool:
        item = self._find(sensor_id, key)
        return True if item is None else item.checkState(0) == Qt.Checked

    def set_all(self, state: bool):
        st = Qt.Checked if state else Qt.Unchecked
        for group in self._groups.values():
            for i in range(group.childCount()):
                group.child(i).setCheckState(0, st)

    def checked(self):
        """Lista ordenada de (sensor_id, clave) tildadas."""
        out = []
        for sid in sorted(self._groups):
            g = self._groups[sid]
            for i in range(g.childCount()):
                c = g.child(i)
                if c.checkState(0) == Qt.Checked:
                    out.append(c.data(0, _ROLE))
        return out

    # -- interno ----------------------------------------------------------
    def _find(self, sensor_id, key):
        g = self._groups.get(sensor_id)
        if g is None:
            return None
        for i in range(g.childCount()):
            c = g.child(i)
            if c.data(0, _ROLE) == (sensor_id, key):
                return c
        return None

    def _on_item_changed(self, item, column):
        if column != 0 or item.parent() is None:
            return                       # solo filas de serie, no el grupo
        data = item.data(0, _ROLE)
        if data:
            self.changed.emit(data[0], data[1], item.checkState(0) == Qt.Checked)