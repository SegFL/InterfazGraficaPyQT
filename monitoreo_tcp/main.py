import sys
import serial
import os
import csv
import codecs
import pyte
import serial.tools.list_ports
import re
from collections import deque
import queue
import numpy as np
from curve_sender import CurveSenderThread, verify_and_strip
import pyqtgraph as pg
from series_math import OPS, apply_op, result_unit, unit_warning
from series_model import read_csv, axis_slot
from PySide6.QtCore import QThread, Signal, Slot, QTimer, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QSplitter        # sumar al import existente
from PySide6.QtGui import QTextCursor   # o PyQt según lo que uses

from series_selector import SeriesSelector

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QLineEdit,
    QTableWidgetItem,
    QComboBox,
    QFileDialog,
    QTextEdit, 
    QLabel,
    QCheckBox,
    QPushButton,
)

from interfaz_ui import Ui_MainWindow

DATA_RE = re.compile(r"0,\d+(?:,[-+]?\d+(?:\.\d+)?)+\*[0-9A-Fa-f]{2}")
print(bool(DATA_RE.search('0,10593,-0.152,0.870,0.010,-0.132,1*37\r')))   # debe dar True
PROTO_RE = re.compile(r"2,[^\r\n*]*\*[0-9A-Fa-f]{2}")


# Series de la ESP32: (clave, nombre, unidad)
LIVE_SERIES = (
    ("voltage", "Tensión", "V"),
    ("current", "Corriente", "mA"),
    ("power", "Potencia", "mW"),
)
# Nombre para mostrar (con tildes) de las magnitudes conocidas
DISPLAY_NAME = {
    "voltage": "Tensión",
    "vbus": "Tensión de bus",
    "current": "Corriente",
    "power": "Potencia",
}
# Letra para nombrar operandos, ej. V(S1000)
MAG_LETTER = {"voltage": "V", "current": "I", "power": "P", "vbus": "Vbus"}
# Los sensores 0-2 conservan su paleta original (V, I, P)
LEGACY_COLORS = {
    0: {"voltage": "#00ffff", "current": "#ffff00", "power": "#ff00ff"},
    1: {"voltage": "#00ff00", "current": "#ff8800", "power": "#ff0055"},
    2: {"voltage": "#3388ff", "current": "#ffcc00", "power": "#cc00ff"},
}
# Resto de las series (CSV, generadas, otras magnitudes): se reparten en ciclo
EXTRA_COLORS = [
    "#00ffff", "#ffff00", "#ff00ff", "#00ff00", "#ff8800", "#ff0055",
    "#3388ff", "#ffcc00", "#cc00ff", "#ffffff", "#66ffcc", "#aaaaaa",
]


# ----------------------------------------------------------------------
# HILO DE LECTURA DE PUERTO SERIE (MULTI-SENSOR)
# ----------------------------------------------------------------------
class SerialReaderThread(QThread):
    data_received = Signal(str)
    parsed_data_received = Signal(int, float, float, float, float, float)
    error_occurred = Signal(str)

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self._is_running = True
        self._rx_buffer = ""
        # Decoder incremental: evita caracteres rotos si un "ó" llega partido entre lecturas
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self.app_queue = queue.Queue()

    PARTIAL_RE = re.compile(r"[02](?:,[-+.,\d*A-Fa-f]*)?\r?$")

    @classmethod
    def _split_partial(cls, tail):
        """Devuelve (emitible, retenido)."""
        m = cls.PARTIAL_RE.search(tail)
        if m:
            return tail[:m.start()], tail[m.end() - len(m.group(0)):]
        return tail, ""
    

    def _parse_data_frame(self, line_str):
        if "*" not in line_str:
            return
        parts = line_str.split("*")[0].split(",")
        # [0]=tipo, [1]=ts_ms, [2]=I_mA, [3]=V, [4]=duty_%, [5]=P_mW, [6]=pin
        if len(parts) < 7:
            return
        try:
            time_sec    = float(parts[1]) / 1000.0
            i_corriente = float(parts[2])
            v_tension   = float(parts[3])
            duty        = float(parts[4])
            p_potencia  = float(parts[5])

            pin = parts[6].strip()
            sensor_id = int(pin) if pin.isdigit() else 0

            self.parsed_data_received.emit(
                sensor_id, time_sec, v_tension, i_corriente, p_potencia, duty
            )
        except ValueError:
            pass
    def _handle_line(self, line):
        rest = line
        m = DATA_RE.search(rest)
        if m:                                    # datos -> gráfico
            self._parse_data_frame(m.group(0))
            rest = rest[:m.start()] + rest[m.end():]
        else:
            m = PROTO_RE.search(rest)
            if m:                                # protocolo de curvas -> cola
                payload = verify_and_strip(m.group(0))
                if payload is not None:
                    self.app_queue.put(payload)
                rest = rest[:m.start()] + rest[m.end():]

        if m:
            # Se extrajo una trama: emitir solo lo que sobra, sin "\n"
            if rest.strip():
                self.data_received.emit(rest)
        else:
            self.data_received.emit(line + "\n")


    def run(self):
        while self._is_running and self.serial_port and self.serial_port.is_open:
            try:
                n = self.serial_port.in_waiting
                if n > 0:
                    self._rx_buffer += self._decoder.decode(self.serial_port.read(n))

                    while "\n" in self._rx_buffer:
                        line, self._rx_buffer = self._rx_buffer.split("\n", 1)
                        self._handle_line(line)

                    # Resto sin '\n': emitir lo que no pueda ser inicio de trama
                    # y retener la cola sospechosa hasta que llegue el '\n'.
                    if self._rx_buffer:
                        emit, keep = self._split_partial(self._rx_buffer)
                        if emit:
                            self.data_received.emit(emit)
                        self._rx_buffer = keep
            except Exception as e:
                self.error_occurred.emit(str(e))
                break
            self.msleep(5)

    def stop(self):
        self._is_running = False
        self.wait()



# ----------------------------------------------------------------------
# VENTANA PRINCIPAL
# ----------------------------------------------------------------------
class MainApp(QMainWindow, Ui_MainWindow):
    # Las series se identifican por clave: voltage, current, power, eficiencia, ...
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.grabando = False
        self.archivo_csv = None
        self.escritor_csv = None
        self.serial_port = None
        self.reader_thread = None
        self.is_paused = False
        self.buffer_size = 200
        self.curve_sender  = None
        self.sensor_styles = {
            0: {"style": Qt.SolidLine, "suffix": "S0 (Solido)"},
            1: {"style": Qt.DashLine, "suffix": "S1 (Punteado)"},
            2: {"style": Qt.DashDotLine, "suffix": "S2 (Raya-Punto)"},
        }
        self.btnSeleccionarCarpeta.clicked.connect(self.seleccionar_carpeta)
        self.sensors_data = {}
        self.axis_units = []        # unidad asignada a cada eje Y (None = libre)
        self._color_i = 0           # contador de colores para series nuevas

        # Terminal retro
        self.textEdit.setStyleSheet(
            "QTextEdit { background-color: #0d0d0d; color: #00ff00; font-family: Consolas, 'Courier New', monospace; font-size: 11pt; }"
        )


        # Emulador de terminal (pyte) con scrollback
        self.screen = pyte.HistoryScreen(80, 24, history=2000, ratio=0.5)
        self.vt_stream = pyte.Stream(self.screen)
        self.reset_terminal()


        self.textEdit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.textEdit.setReadOnly(True)

        self.term_timer = QTimer()
        self.term_timer.setInterval(30)
        self.term_timer.timeout.connect(self.render_terminal)
        self.term_timer.start()

        if self.comboBox_2.count() == 0:
            self.comboBox_2.addItems(["115200", "9600", "57600", "230400"])

        self.input_send_widget = getattr(self, "input_send", None) or getattr(
            self, "lineEdit", None
        )
        self.btn_pause_widget = self.btnStop

        # QLineEdit para controlar la cantidad de muestras en pantalla
        self.input_muestras = getattr(self, "lineEdit_muestras", None) or getattr(self, "lineEdit_2", None)

        print("INPUT MUESTRAS:", self.input_muestras)

        if self.input_muestras:
            self.input_muestras.setText(str(self.buffer_size))
            self.input_muestras.editingFinished.connect(self.on_muestras_changed)
        print("CONECTANDO INPUT MUESTRAS")
        if self.btn_pause_widget:
            self.btn_pause_widget.clicked.connect(self.toggle_pause)

        self.setup_curve_table()
        self.setup_curve_plot()
        self._setup_graph()

        self._math_swapped = False
        self._math_prev_sel = []
        self._math_result = None
        self.selector.changed.connect(self.refresh_math_operands)

        self.btnMathSumar.clicked.connect(lambda: self.on_math_op("sum"))
        self.btnMathRestar.clicked.connect(lambda: self.on_math_op("sub"))
        self.btnMathMultiplicar.clicked.connect(lambda: self.on_math_op("mul"))
        self.btnMathDividir.clicked.connect(lambda: self.on_math_op("div"))
        self.btnMathSwap.clicked.connect(self.swap_math_operands)
        self.btnMathMostrar.clicked.connect(self.show_math_result)
        self.btnMathGuardarCSV.clicked.connect(self.save_math_result)
        self.refresh_math_operands()


        self.btn_refresh.clicked.connect(self.refresh_ports)
        self.btnIniciar.clicked.connect(self.toggle_connection)
        self.pushButton_2.clicked.connect(self.send_data)
        self.btnCargarArchivo.clicked.connect(self.load_csv_files)
        self._setup_x_axis_tools()
        if self.input_send_widget:
            self.input_send_widget.returnPressed.connect(self.send_data)

        # Timer de refresco para PyPlot (~30 FPS)
        self.plot_timer = QTimer()
        self.plot_timer.setInterval(33)
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start()

        self.refresh_ports()


        self.btnAgregarFila.clicked.connect(self.add_curve_row)
        self.btnEliminarFila.clicked.connect(self.remove_curve_row)
        self.btnEnviarCurva.clicked.connect(self.send_curve)

        self.btnToggleFiles.toggled.connect(self.toggle_file_panel)
        self.btnToggleFiles.setCheckable(True)      # por si no lo marcaste en Designer
        self.btnToggleFiles.setChecked(False)
        self.toggle_file_panel(False)               # aplica oculto + flecha derecha

        self.btnToggleMath.setCheckable(True)       # por si no lo marcaste en Designer
        self.btnToggleMath.toggled.connect(self.toggle_math_panel)
        self.btnToggleMath.setChecked(False)
        self.toggle_math_panel(False)   

        if getattr(sys, 'frozen', False):
            ruta_base = os.path.dirname(sys.executable)
        else:
            ruta_base = os.path.dirname(os.path.abspath(__file__))

        self.carpeta_destino = os.path.join(ruta_base, "DatosPy")
        os.makedirs(self.carpeta_destino, exist_ok=True)

        # 2. Configurar el botón de grabación
        self.btn_grabar.setCheckable(True)
        self.btn_grabar.setText("Iniciar Grabación")
        self.btn_grabar.toggled.connect(self.on_toggle_grabar)

    def on_toggle_grabar(self, esta_presionado):
        if esta_presionado:
            if self.iniciar_grabacion():
                self.btn_grabar.setText("Grabando... (Clic para frenar)")
            else:
                self.btn_grabar.setChecked(False)
        else:
            self.detener_grabacion()
            self.btn_grabar.setText("Iniciar Grabación")

    def iniciar_grabacion(self):
        """Habilita la grabación. Los archivos se crearán dinámicamente por cada sensor."""
        from datetime import datetime

        self.timestamp_inicio = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Diccionarios para manejar múltiples archivos/escritores abiertos por ID
        self.archivos_csv = {}
        self.escritores_csv = {}
        
        self.grabando = True
        self.statusbar.showMessage("Grabación iniciada (archivos por sensor)")
        self.append_text(f"[REC] Grabación iniciada con timestamp: {self.timestamp_inicio}\n")
        return True

    def seleccionar_carpeta(self):
        carpeta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de destino",
            self.carpeta_destino
        )

        if carpeta:
            self.carpeta_destino = carpeta
            self.statusbar.showMessage(f"Carpeta de destino: {carpeta}")
            self.append_text(f"[REC] Carpeta seleccionada: {carpeta}\n")

    def detener_grabacion(self):
        """Cierra todos los archivos CSV que estén abiertos."""
        self.grabando = False
        if hasattr(self, 'archivos_csv') and self.archivos_csv:
            for sensor_id, archivo in self.archivos_csv.items():
                try:
                    archivo.close()
                except Exception as e:
                    print(f"Error al cerrar archivo del sensor {sensor_id}: {e}")
            
            self.archivos_csv.clear()
            self.escritores_csv.clear()
            
            self.statusbar.showMessage("Grabación finalizada y archivos cerrados")
            self.append_text("[REC] Grabación finalizada.\n")

    def toggle_file_panel(self, checked):
        self.framePanelArchivos.setVisible(checked)
        self.btnToggleFiles.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)

    def toggle_math_panel(self, checked):
        self.framePanelMath.setVisible(checked)
        if hasattr(self.btnToggleMath, "setArrowType"):   # solo QToolButton
            self.btnToggleMath.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
            
    def setup_curve_table(self):

        self.tableCurva.setColumnCount(3)

        self.tableCurva.setHorizontalHeaderLabels([
            "Tiempo",
            "Valor",
            "Tipo"
        ])

        self.tableCurva.setRowCount(0)

        self.tableCurva.itemChanged.connect(self.update_curve_plot)
        

    def add_curve_row(self):

        row = self.tableCurva.rowCount()

        self.tableCurva.insertRow(row)

        self.tableCurva.setItem(
            row, 0, QTableWidgetItem("0")
        )

        self.tableCurva.setItem(
            row, 1, QTableWidgetItem("0")
        )

        combo = QComboBox()
        combo.addItems([
            "STEP",
            "LINEAR"
        ])

        combo.currentTextChanged.connect(self.update_curve_plot)

        self.tableCurva.setCellWidget(row, 2, combo)

        self.update_curve_plot()

    def remove_curve_row(self):

        row = self.tableCurva.currentRow()

        if row >= 0:
            self.tableCurva.removeRow(row)
            self.update_curve_plot()
    def setup_curve_plot(self):


        self.curve_plot.setBackground("#0c0c0c")

        self.curve_plot.showGrid(
            x=True,
            y=True,
            alpha=0.3
        )

        self.curve_plot.setLabel(
            "bottom",
            "Tiempo",
            units="ms"
        )

        self.curve_plot.setLabel(
            "left",
            "Valor"
        )

        self.curve_plot.setTitle(
            "Curva"
        )

  
    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.btn_pause_widget:
            if self.is_paused:
                self.btn_pause_widget.setText("Reanudar")
                self.statusbar.showMessage("Gráfico en pausa (inspección de datos)")
            else:
                self.btn_pause_widget.setText("Pausar")
                self.statusbar.showMessage("Gráfico en tiempo real")
                self._reset_x_axis()

    def _setup_graph(self):
        """Configura los ejes y la visualización del PlotWidget que ya existe en la UI."""
        pg.setConfigOptions(antialias=True)

        self.graph_widget = self.layout_plots

        if self.graph_widget is None:
            print("ERROR: No se encontró ningún PlotWidget en la interfaz de Qt Designer.")
            return

        # Selector de series (árbol) creado por Qt Designer
        self.selector = self.containerSelector

        self.graph_widget.setTitle("Telemetría de Sensores - Tiempo Real")
        self.graph_widget.setBackground("#0c0c0c")
        self.graph_widget.showGrid(x=True, y=True, alpha=0.3)
        self.graph_widget.setLabel("bottom", "Tiempo", units="s")
        self.graph_widget.addLegend(offset=(10, 10))

        # Eje 0 (izquierda): el del PlotItem.
        # Ejes 1 y 2 (derecha): ViewBox propios con eje a la derecha.
        self.vb2 = pg.ViewBox()
        self.graph_widget.plotItem.scene().addItem(self.vb2)
        axis2 = pg.AxisItem("right")
        self.graph_widget.plotItem.layout.addItem(axis2, 2, 3)
        axis2.linkToView(self.vb2)

        self.vb3 = pg.ViewBox()
        self.graph_widget.plotItem.scene().addItem(self.vb3)
        axis3 = pg.AxisItem("right")
        self.graph_widget.plotItem.layout.addItem(axis3, 2, 4)
        axis3.linkToView(self.vb3)

        # Sincronización X entre ViewBoxes
        self.vb2.setXLink(self.graph_widget.plotItem.vb)
        self.vb3.setXLink(self.graph_widget.plotItem.vb)

        # Auto-escalado vertical independiente
        self.graph_widget.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)
        self.vb2.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)
        self.vb3.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)

        def update_views():
            rect = self.graph_widget.plotItem.vb.sceneBoundingRect()
            self.vb2.setGeometry(rect)
            self.vb2.linkedViewChanged(self.graph_widget.plotItem.vb, self.vb2.XAxis)

            self.vb3.setGeometry(rect)
            self.vb3.linkedViewChanged(self.graph_widget.plotItem.vb, self.vb3.XAxis)

        self.graph_widget.plotItem.vb.sigResized.connect(update_views)
        update_views()

        # Ejes Y por posición: la unidad de cada serie decide en cuál se dibuja
        self.axis_views = [self.graph_widget.plotItem.vb, self.vb2, self.vb3]
        self.axis_items = [self.graph_widget.getAxis("left"), axis2, axis3]
        for ax in self.axis_items:
            ax.enableAutoSIPrefix(False)     # la unidad ya viene en la etiqueta

        if self.selector:
            self.selector.changed.connect(self.on_series_toggled)
            self.selector.remove_requested.connect(self.remove_sensor)
        self._update_axes()
            
    @Slot(int, float, float, float, float, float)
    def store_sensor_data(self, sensor_id, t, v1, v2, v3, duty):
        s = self._get_or_create_sensor(sensor_id)
        s["time"].append(t)
        s["series"]["voltage"]["data"].append(v1)
        s["series"]["current"]["data"].append(v2)
        s["series"]["power"]["data"].append(v3)

        # Si la grabación está activa, escribir en el CSV del sensor correspondiente
        if self.grabando:
            try:
                # Si es la primera muestra de este sensor en esta sesión, crear su archivo CSV
                if sensor_id not in self.escritores_csv:
                    nombre_archivo = f"sensor_{sensor_id}_{self.timestamp_inicio}.csv"
                    path_completo = os.path.join(self.carpeta_destino, nombre_archivo)
                    
                    f = open(path_completo, mode="w", newline="", encoding="utf-8")
                    writer = csv.writer(f, delimiter=";")
                    
                    # Encabezado optimizado (sin Sensor_ID)
                    writer.writerow(["Tiempo_s", "Tension_V", "Corriente_mA", "Potencia_mW", "Duty_%"])
                    f.flush()
                    
                    self.archivos_csv[sensor_id] = f
                    self.escritores_csv[sensor_id] = writer
                    self.append_text(f"[REC] Creado archivo para Sensor {sensor_id}: {nombre_archivo}\n")

                # Escribir la muestra en el archivo específico del sensor
                self.escritores_csv[sensor_id].writerow([f"{t:.3f}", f"{v1:.3f}", f"{v2:.3f}", f"{v3:.3f}", f"{duty:.3f}"])
                
            except Exception as e:
                print(f"Error guardando muestra del sensor {sensor_id}: {e}")


    def _pick_color(self, sensor_id, key):
        legacy = LEGACY_COLORS.get(sensor_id, {}).get(key)
        if legacy:
            return legacy
        color = EXTRA_COLORS[self._color_i % len(EXTRA_COLORS)]
        self._color_i += 1
        return color

    def _add_curve(self, curve, slot):
        if slot == 0:
            self.graph_widget.addItem(curve)
        else:
            self.axis_views[slot].addItem(curve)

    def _remove_curve(self, curve, slot):
        if slot == 0:
            self.graph_widget.removeItem(curve)
        else:
            self.axis_views[slot].removeItem(curve)

    def _get_or_create_sensor(self, sensor_id, suffix=None, static=False,
                              label=None, series=None, title=None, expr=None):
        """Crea (una sola vez) el sensor con sus series.

        series : lista de (clave, nombre, unidad). Por defecto V/I/P de la ESP32.
        label  : nombre de leyenda para todas sus series (series generadas).
        title  : encabezado del grupo en el selector.
        expr   : expresión que generó la serie (para nombrar operandos).
        """
        if sensor_id in self.sensors_data:
            return self.sensors_data[sensor_id]

        series = series or LIVE_SERIES
        style_cfg = self.sensor_styles.get(
            sensor_id, {"style": Qt.SolidLine, "suffix": f"S{sensor_id}"}
        )
        line_style = style_cfg["style"]
        suffix = suffix or style_cfg["suffix"]

        s = {
            "time": deque(maxlen=10000),
            "series": {},
            "static": static,
            "expr": expr,
        }
        rows = []
        for key, name, unit in series:
            text = f"{name} [{unit}]" if unit else name
            legend_name = label or f"{text} - {suffix}"
            color = self._pick_color(sensor_id, key)
            pen = pg.mkPen(color=color, width=2, style=line_style)
            # connect="finite": los NaN (p. ej. división por cero) dejan un hueco
            curve = pg.PlotCurveItem(pen=pen, name=legend_name, connect="finite")
            slot = axis_slot(unit, self.axis_units)
            self._add_curve(curve, slot)
            s["series"][key] = {
                "name": name,
                "unit": unit,
                "data": deque(maxlen=10000),
                "curve": curve,
                "slot": slot,
                "legend": legend_name,
                "color": color,
            }
            rows.append((key, text))

        self.sensors_data[sensor_id] = s

        self.selector.add_sensor(
            sensor_id, label=title or label or f"S{sensor_id}", series=rows
        )
        for key in s["series"]:
            self.apply_series_visibility(sensor_id, key)
        self._update_axes()
        self.refresh_math_operands()
        self.refresh_x_axis_options()
        return s

    @Slot(int, str, bool)
    def on_series_toggled(self, sensor_id, key, visible):
        self.apply_series_visibility(sensor_id, key)

    def apply_series_visibility(self, sensor_id, key):
        """Muestra/oculta una serie y sincroniza leyenda y ejes."""
        s = self.sensors_data.get(sensor_id)
        if s is None or key not in s["series"]:
            return
        ser = s["series"][key]
        curve = ser["curve"]
        legend = self.graph_widget.plotItem.legend
        visible = self.selector.is_visible(sensor_id, key)

        curve.setVisible(visible)
        legend.removeItem(curve)                  # evita entradas duplicadas
        if visible:
            legend.addItem(curve, ser["legend"])
        self._update_axes()

    @Slot(int)
    def remove_sensor(self, sensor_id):
        s = self.sensors_data.pop(sensor_id, None)
        if s is None:
            return

        legend = self.graph_widget.plotItem.legend
        for ser in s["series"].values():
            self._remove_curve(ser["curve"], ser["slot"])
            if legend:
                legend.removeItem(ser["curve"])

        # Libera los ejes que quedaron sin series
        used = {ser["slot"] for t in self.sensors_data.values()
                for ser in t["series"].values()}
        for i in range(len(self.axis_units)):
            if i not in used:
                self.axis_units[i] = None

        self.selector.remove_sensor(sensor_id)
        self.refresh_math_operands()
        self.refresh_x_axis_options()
        self._update_axes()
        self.statusbar.showMessage(f"Serie {sensor_id} eliminada")

    def _update_axes(self):
        """Visibilidad, rótulo y color de cada eje Y según las series que usa."""
        for i, axis in enumerate(self.axis_items):
            visibles, todas = [], []
            for sid, s in self.sensors_data.items():
                for key, ser in s["series"].items():
                    if ser["slot"] != i:
                        continue
                    todas.append(ser)
                    if self.selector.is_visible(sid, key):
                        visibles.append(ser)

            axis.setVisible(bool(visibles) or i == 0)
            shown = visibles or todas
            if not shown:
                axis.showLabel(False)
                continue
            names = list(dict.fromkeys(x["name"] for x in shown))
            units = list(dict.fromkeys(x["unit"] for x in shown if x["unit"]))
            text = " / ".join(names[:3]) + ("…" if len(names) > 3 else "")
            axis.setLabel(
                text=text,
                units=" / ".join(units) or None,
                color=shown[0]["color"],
            )
            axis.showLabel(True)

 
    def on_muestras_changed(self):
        print("CAMBIO DE MUESTRAS:", self.input_muestras.text())
        """Actualiza la cantidad de muestras visibles."""
        if not self.input_muestras:
            return

        text_val = self.input_muestras.text().strip()

        if text_val.isdigit():
            new_size = int(text_val)

            if new_size >= 5:
                self.buffer_size = new_size

                for s in self.sensors_data.values():
                    if s.get("static"): continue
                    s["time"] = deque(s["time"], maxlen=self.buffer_size)
                    for ser in s["series"].values():
                        ser["data"] = deque(ser["data"], maxlen=self.buffer_size)

                self.update_plot()
                self.statusbar.showMessage(
                    f"Muestras visibles: {self.buffer_size}"
                )
                return

        # Si el valor no es válido, volver al valor anterior
        self.input_muestras.setText(str(self.buffer_size))



    def update_plot(self):
        """Actualiza solo las curvas visibles con las últimas buffer_size muestras."""
        if self.is_paused or self._x_sel is not None or self._x_rel or not self.sensors_data:
            return
 
        global_t_min = float("inf")
        global_t_max = float("-inf")
        has_data = False
 
        for s_id, s in self.sensors_data.items():

            if s.get("static"):
                continue

            if len(s["time"]) < 1:
                continue
 
            has_data = True
 
            times = list(s["time"])[-self.buffer_size:]
            for key, ser in s["series"].items():
                if self.selector.is_visible(s_id, key):
                    ser["curve"].setData(times, list(ser["data"])[-self.buffer_size:])
 
            if len(times) > 0:
                global_t_min = min(global_t_min, times[0])
                global_t_max = max(global_t_max, times[-1])
 
        if has_data and global_t_max > global_t_min:
            self.graph_widget.setXRange(global_t_min, global_t_max, padding=0)

 
                    
    def refresh_ports(self):
        self.comboBox.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.comboBox.addItem(
                f"{port.device} - {port.description}", port.device
            )
        if not ports:
            self.comboBox.addItem("Sin puertos disponibles", None)

    def toggle_connection(self):
        if self.serial_port and self.serial_port.is_open:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        port_name = self.comboBox.currentData()
        if not port_name:
            self.statusbar.showMessage("Error: No hay puerto seleccionado.")
            return
 
        baud_text = self.comboBox_2.currentText()
        baud_rate = int(baud_text) if baud_text.isdigit() else 115200
        try:
            for sid in [k for k, v in self.sensors_data.items() if not v.get("static")]:
                self.remove_sensor(sid)
            self._reset_x_axis()
            self.reset_terminal()
            self.serial_port = serial.Serial(port_name, baud_rate, timeout=0.1)
 
            self.reader_thread = SerialReaderThread(self.serial_port)
            self.reader_thread.data_received.connect(self.append_text)
            self.reader_thread.parsed_data_received.connect(
                self.store_sensor_data
            )
            self.reader_thread.error_occurred.connect(self.handle_error)
            self.reader_thread.start()
 
            self.btnIniciar.setText("Desconectar")
            self.comboBox.setEnabled(False)
            self.comboBox_2.setEnabled(False)
            self.btn_refresh.setEnabled(False)
 
            self.statusbar.showMessage(
                f"Conectado a {port_name} @ {baud_rate} bps"
            )
 
        except Exception as e:
            self.statusbar.showMessage(f"Error al abrir {port_name}: {e}")


            
    def disconnect_serial(self):
        if self.curve_sender  and self.curve_sender .isRunning():
            self.curve_sender .wait(3000)
        
        if self.reader_thread:
            self.reader_thread.stop()
            self.reader_thread = None

        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

        self.serial_port = None

        self.btnIniciar.setText("Iniciar")
        self.comboBox.setEnabled(True)
        self.comboBox_2.setEnabled(True)
        self.btn_refresh.setEnabled(True)

        self.statusbar.showMessage("Desconectado")

    def reset_terminal(self):
        self.screen.reset()
        self.screen.set_mode(pyte.modes.LNM)   # '\n' también hace retorno de carro

    @Slot(str)
    def append_text(self, text):
        self.vt_stream.feed(text)

    def _line_to_str(self, line):
        # Las filas del historial son diccionarios columna -> Char
        return "".join(line[x].data for x in range(self.screen.columns)).rstrip()

    def render_terminal(self):
        if not self.screen.dirty:
            return
        self.screen.dirty.clear()

        sb = self.textEdit.verticalScrollBar()
        at_bottom = sb.value() >= sb.maximum() - 4
        prev = sb.value()

        lines = [self._line_to_str(l) for l in self.screen.history.top]
        lines += [l.rstrip() for l in self.screen.display]   # pantalla completa, sin cortar en el cursor
        while lines and not lines[-1]:                       # solo quita filas vacías del final
            lines.pop()

        self.textEdit.setPlainText("\n".join(lines))

        # Mover el scroll después de que Qt termine el layout, sin tocar el cursor de texto
        if at_bottom:
            QTimer.singleShot(0, lambda: sb.setValue(sb.maximum()))
        else:
            sb.setValue(prev)

    def get_curve_data(self):
        data = []

        for row in range(self.tableCurva.rowCount()):

            tiempo = self.tableCurva.item(row, 0)
            valor = self.tableCurva.item(row, 1)
            tipo = self.tableCurva.cellWidget(row, 2)

            if tiempo is None or valor is None or tipo is None:
                raise ValueError(f"Fila {row + 1} incompleta")

            tiempo = int(tiempo.text())
            valor = int(valor.text())
            tipo = tipo.currentText()

            data.append((tiempo, valor, tipo))

        return data
        
    def validate_curve_data(self, data):

        if not data:
            return False, "La tabla está vacía."

        previous_time = -1

        for i, (tiempo, valor, tipo) in enumerate(data):

            if tiempo < 0:
                return False, f"Tiempo inválido en fila {i + 1}."

            if valor < 0:
                return False, f"Valor inválido en fila {i + 1}."

            if tipo not in ("STEP", "LINEAR"):
                return False, f"Tipo inválido en fila {i + 1}."

            if tiempo <= previous_time:
                return False, (
                    f"El tiempo en fila {i + 1} "
                    "debe ser mayor que el anterior."
                )

            previous_time = tiempo

        return True, ""
    def update_curve_plot(self):

        if not hasattr(self, "curve_plot"):
            return

        x, y = self.generate_curve_data()

        if not x:
            self.curve_plot.clear()
            return

        self.curve_plot.clear()

        self.curve_plot.plot(
            x,
            y,
            pen=pg.mkPen(
                color="#00ffff",
                width=2
            ),
            symbol="o",
            symbolSize=7
        )
            
    def generate_curve_data(self):
        points = []
        for row in range(self.tableCurva.rowCount()):
            time_item = self.tableCurva.item(row, 0)
            value_item = self.tableCurva.item(row, 1)
            type_widget = self.tableCurva.cellWidget(row, 2)
            if time_item is None or value_item is None or type_widget is None:
                continue
            try:
                t = float(time_item.text())
                v = float(value_item.text())
            except ValueError:
                continue
            points.append((t, v, type_widget.currentText()))

        points.sort(key=lambda p: p[0])
        if not points:
            return [], []
        if len(points) == 1:
            return [points[0][0]], [points[0][1]]

        # Semántica del firmware: el tipo de points[i] define cómo se LLEGA a él.
        x, y = [points[0][0]], [points[0][1]]
        for i in range(1, len(points)):
            t0, v0, _ = points[i - 1]
            t1, v1, tipo = points[i]
            if t1 <= t0:
                continue
            if tipo == "LINEAR":
                x.append(t1); y.append(v1)               # rampa
            else:                                        # STEP (y S_CURVE, sin implementar)
                x.extend([t1, t1]); y.extend([v0, v1])   # mantiene v0 y salta en t1
        return x, y

    def send_curve(self):
        if not (self.serial_port and self.serial_port.is_open and self.reader_thread):
            self.statusbar.showMessage("Puerto serie no conectado")
            return
        if self.curve_sender and self.curve_sender.isRunning():
            self.statusbar.showMessage("Ya hay un envío en curso")
            return

        try:
            data = self.get_curve_data()
        except ValueError as e:
            self.statusbar.showMessage(f"Datos inválidos (tiempo y valor deben ser enteros): {e}")
            return

        valid, error = self.validate_curve_data(data)
        if not valid:
            self.statusbar.showMessage(error)
            return

        self.curve_sender  = CurveSenderThread(
            self.serial_port,
            self.reader_thread.app_queue,
            self.spinBoxCurveID.value(),
            data,
        )
        self.curve_sender .progress.connect(self.statusbar.showMessage)
        self.curve_sender .result.connect(self.on_curve_sent)
        self.curve_sender .finished.connect(lambda: self.btnEnviarCurva.setEnabled(True))
        self.btnEnviarCurva.setEnabled(False)
        self.curve_sender .start()

    @Slot(bool, str)
    def on_curve_sent(self, ok, msg):
        self.statusbar.showMessage(("✔ " if ok else "✘ ") + msg)
        self.append_text(f"[CURVA] {msg}\n")

    def load_csv_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar archivos CSV", "", "CSV (*.csv)"
        )
        if not paths:
            return

        next_id = 1000
        loaded = 0

        for path in paths:
            fname = os.path.basename(path)
            try:
                data = read_csv(path)
            except Exception as e:
                self.statusbar.showMessage(f"Error al leer {fname}: {e}")
                continue
            for w in data.warnings:
                self.append_text(f"[CSV] {fname}: {w}\n")

            while next_id in self.sensors_data:
                next_id += 1

            base = os.path.splitext(fname)[0]
            defs = [
                (key, DISPLAY_NAME.get(key, col.name), col.unit)
                for key, (col, _) in data.series.items()
            ]
            s = self._get_or_create_sensor(
                next_id,
                suffix=base,
                static=True,
                series=defs,
                title=f"S{next_id} ({base})",
            )
            n = len(data.time)
            s["time"] = deque(data.time.tolist(), maxlen=n)
            for key, (_, y) in data.series.items():
                ser = s["series"][key]
                ser["data"] = deque(y.tolist(), maxlen=n)
                ser["curve"].setData(data.time, y)

            next_id += 1
            loaded += 1

        self.apply_x_axis()
        self.graph_widget.autoRange()
        self.statusbar.showMessage(f"{loaded} de {len(paths)} archivo(s) cargado(s)")

    # -- Eje X elegible y CSV combinado (solo con el tiempo real detenido) --
    def _setup_x_axis_tools(self):
        """Agrega al panel de archivos: selector de eje X, alinear inicios y
        boton para guardar un CSV con las series tildadas."""
        self._x_sel = None          # None = tiempo; si no (sensor_id, clave)
        self._x_rel = False         # True = cada serie con t relativo a su inicio
        lay = self.horizontalLayout_6
        lay.addWidget(QLabel("Eje X:"))
        self.comboEjeX = QComboBox()
        self.comboEjeX.setMinimumWidth(220)
        self.comboEjeX.setToolTip("Magnitud del eje X (solo con el gráfico en tiempo real detenido)")
        lay.addWidget(self.comboEjeX)
        self.chkAlinearInicio = QCheckBox("Alinear inicios (t=0)")
        self.chkAlinearInicio.setToolTip(
            "Cada serie usa su tiempo relativo a su primera muestra.\n"
            "Usar con archivos grabados en sesiones distintas.")
        lay.addWidget(self.chkAlinearInicio)
        self.btnGuardarCombinado = QPushButton("Guardar CSV combinado")
        self.btnGuardarCombinado.setToolTip("Guarda en un CSV las series tildadas con el eje X elegido")
        lay.addWidget(self.btnGuardarCombinado)
        self.refresh_x_axis_options()
        self.comboEjeX.currentIndexChanged.connect(self.apply_x_axis)
        self.chkAlinearInicio.toggled.connect(self.apply_x_axis)
        self.btnGuardarCombinado.clicked.connect(self.save_combined_csv)

    def _realtime_stopped(self):
        connected = self.serial_port is not None and self.serial_port.is_open
        return self.is_paused or not connected

    def refresh_x_axis_options(self):
        """Rearma la lista del eje X conservando la seleccion si sigue existiendo."""
        combo = getattr(self, "comboEjeX", None)
        if combo is None:
            return
        cur = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("Tiempo [s]", None)
        idx = 0
        for sid in sorted(self.sensors_data):
            for key, ser in self.sensors_data[sid]["series"].items():
                combo.addItem(f"S{sid}: {ser['legend']}", (sid, key))
                if cur is not None and tuple(cur) == (sid, key):
                    idx = combo.count() - 1
        combo.setCurrentIndex(idx)
        combo.blockSignals(False)
        if cur is not None and idx == 0:
            self.apply_x_axis()          # se quito la serie del eje X: vuelve a tiempo

    def _reset_x_axis(self):
        """Vuelve a eje X = tiempo absoluto (al reanudar o conectar)."""
        if not hasattr(self, "comboEjeX"):
            return
        if self._x_sel is None and not self._x_rel:
            return
        for w in (self.comboEjeX, self.chkAlinearInicio):
            w.blockSignals(True)
        self.comboEjeX.setCurrentIndex(0)
        self.chkAlinearInicio.setChecked(False)
        for w in (self.comboEjeX, self.chkAlinearInicio):
            w.blockSignals(False)
        self.apply_x_axis()

    def _series_xy(self, sid, key):
        """(t, y) como arrays; t relativo a su inicio si 'Alinear inicios'."""
        s = self.sensors_data[sid]
        t = np.asarray(s["time"], float)
        y = np.asarray(s["series"][key]["data"], float)
        n = min(len(t), len(y))
        t, y = t[:n], y[:n]
        if n and self._x_rel:
            t = t - t[0]
        return t, y

    @staticmethod
    def _resample(t_src, y_src, t_dst):
        """Interpolacion lineal de y_src(t_src) en t_dst; NaN fuera del rango comun."""
        ok = np.isfinite(t_src) & np.isfinite(y_src)
        t_src, y_src = t_src[ok], y_src[ok]
        if len(t_src) < 2:
            return np.full(len(t_dst), np.nan)
        order = np.argsort(t_src, kind="stable")
        t_src, y_src = t_src[order], y_src[order]
        out = np.interp(t_dst, t_src, y_src)
        eps = 1e-6                       # tolerancia de redondeo [s]
        out[(t_dst < t_src[0] - eps) | (t_dst > t_src[-1] + eps)] = np.nan
        return out

    def apply_x_axis(self, *_):
        """Redibuja todas las curvas contra el eje X elegido."""
        sel = self.comboEjeX.currentData()
        rel = self.chkAlinearInicio.isChecked()
        if (sel is not None or rel) and not self._realtime_stopped():
            self.statusbar.showMessage("Detené el gráfico en tiempo real para cambiar el eje X")
            self._x_sel, self._x_rel = (0, ""), True     # fuerza el reset
            self._reset_x_axis()
            return
        self._x_sel = tuple(sel) if sel is not None else None
        self._x_rel = rel
        bottom = self.graph_widget.getAxis("bottom")
        sin_solape = []
        if self._x_sel is None:
            for sid, s in self.sensors_data.items():
                for key, ser in s["series"].items():
                    ser["curve"].setData(*self._series_xy(sid, key))
            bottom.enableAutoSIPrefix(True)
            self.graph_widget.setLabel("bottom", "Tiempo", units="s")
        else:
            xsid, xkey = self._x_sel
            tx, x = self._series_xy(xsid, xkey)
            for sid, s in self.sensors_data.items():
                for key, ser in s["series"].items():
                    t, y = self._series_xy(sid, key)
                    xi = x[:len(y)] if sid == xsid else self._resample(tx, x, t)
                    if len(xi) < len(y):
                        y = y[:len(xi)]
                    if len(y) and np.all(np.isnan(xi)):
                        sin_solape.append(f"S{sid}")
                    ser["curve"].setData(xi, y)
            xs = self.sensors_data[xsid]["series"][xkey]
            bottom.enableAutoSIPrefix(False)
            self.graph_widget.setLabel("bottom", f"{xs['name']} (S{xsid})", units=xs["unit"] or None)
        self.graph_widget.autoRange()
        if sin_solape:
            self.statusbar.showMessage(
                "Sin solapamiento temporal con el eje X: " + ", ".join(dict.fromkeys(sin_solape))
                + " (probá 'Alinear inicios')")

    def save_combined_csv(self):
        """CSV con las series tildadas (de uno o varios archivos) sobre una base
        de tiempo comun: la de la serie del eje X, o la de la primera tildada.
        Las demas se interpolan linealmente; fuera del rango comun quedan en nan."""
        if not self._realtime_stopped():
            self.statusbar.showMessage("Detené el gráfico en tiempo real para guardar el CSV combinado")
            return
        sel = [tuple(o) for o in self.selector.checked() if tuple(o) != self._x_sel]
        if not sel:
            self.statusbar.showMessage("Tildá al menos una serie para guardar")
            return
        cols = ([self._x_sel] if self._x_sel is not None else []) + sel
        base = cols[0]
        t_base, _ = self._series_xy(*base)
        heads, data, sin_solape = ["Tiempo [s]"], [t_base], []
        for sid, key in cols:
            t, y = self._series_xy(sid, key)
            if sid == base[0]:
                v = np.full(len(t_base), np.nan)
                v[:min(len(y), len(t_base))] = y[:len(t_base)]
            else:
                v = self._resample(t, y, t_base)
                if np.all(np.isnan(v)):
                    sin_solape.append(f"S{sid}")
            data.append(v)
            ser = self.sensors_data[sid]["series"][key]
            tag = ser["legend"].split(" - ", 1)[1] if " - " in ser["legend"] else ""
            head = f"{ser['name']} S{sid}" + (f" {tag}" if tag else "")
            head = head.replace("[", "(").replace("]", ")").replace(";", ",")
            heads.append(f"{head} [{ser['unit']}]" if ser["unit"] else head)

        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar CSV combinado", os.path.join(self.carpeta_destino, "combinado.csv"),
            "CSV (*.csv)")
        if not path:
            return
        rows = np.column_stack(data)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(heads)
            for r in rows:
                if np.all(np.isnan(r[1:])):
                    continue                 # fila sin ningun dato
                w.writerow([f"{r[0]:.9g}"] + ["nan" if np.isnan(v) else f"{v:.6g}" for v in r[1:]])
        msg = f"Guardado: {path}"
        if sin_solape:
            msg += " - sin solapamiento temporal: " + ", ".join(dict.fromkeys(sin_solape))
        self.statusbar.showMessage(msg)

    def operand_label(self, sid, key):
        s = self.sensors_data[sid]
        if s.get("expr"):                      # serie generada
            return f"({s['expr']})"
        letter = MAG_LETTER.get(key) or s["series"][key]["name"]
        return f"{letter}(S{sid})"

    def refresh_math_operands(self, *_):
        sel = self.selector.checked()
        if sel != self._math_prev_sel:
            self._math_swapped = False
            self._math_prev_sel = sel
        n = len(sel)
        if n == 0:
            txt = "Operandos: (seleccioná hasta 2 series)"
        elif n > 2:
            txt = f"Operandos: {n} series tildadas, dejá como máximo 2"
        else:
            ops = sel[::-1] if self._math_swapped else sel
            names = [self.operand_label(*o) for o in ops]
            txt = "A: " + names[0] + (f"    B: {names[1]}" if n == 2 else "")
        self.lblMathOperandos.setText(txt)
        self.btnMathSwap.setEnabled(n == 2)

    def swap_math_operands(self):
        self._math_swapped = not self._math_swapped
        self.refresh_math_operands()

    @Slot(str)
    def on_math_op(self, op):
        sel = self.selector.checked()
        if len(sel) != 2:
            self.statusbar.showMessage("Tildá exactamente 2 series para operar")
            return
        if self._math_swapped:
            sel = sel[::-1]
        (sa, ka), (sb, kb) = sel
        A, B = self.sensors_data[sa], self.sensors_data[sb]
        ser_a, ser_b = A["series"][ka], B["series"][kb]
        ya = np.asarray(ser_a["data"], float)
        yb = np.asarray(ser_b["data"], float)
        if len(ya) == 0 or len(yb) == 0:
            self.statusbar.showMessage("Alguna de las series no tiene datos")
            return

        n, y = apply_op(op, ya, yb)             # sin alinear tiempos (por ahora)
        ta = np.asarray(A["time"], float)[:n]

        unit = result_unit(op, ser_a["unit"], ser_b["unit"])
        same = op in ("sum", "sub") and ka == kb       # conserva la magnitud
        name = f"{self.operand_label(sa, ka)}{OPS[op][0]}{self.operand_label(sb, kb)}"
        self._math_result = {
            "t": ta,
            "y": y,
            "unit": unit,
            "name": name,
            "key": ka if same else "result",
            "rname": ser_a["name"] if same else "Resultado",
        }

        self.lineEditNombreSerie.setText(name)
        for w in (self.lineEditNombreSerie, self.btnMathMostrar, self.btnMathGuardarCSV):
            w.setEnabled(True)
        msg = f"Calculado: {name} [{unit or 'adim.'}] ({n} puntos)"
        warn = unit_warning(op, ser_a["unit"], ser_b["unit"])
        self.statusbar.showMessage(msg + (f" - {warn}" if warn else ""))

    def show_math_result(self):
        r = self._math_result
        if r is None:
            return
        name = self.lineEditNombreSerie.text().strip() or r["name"]
        sid = 1000
        while sid in self.sensors_data:
            sid += 1
        s = self._get_or_create_sensor(
            sid,
            static=True,
            label=name,
            title=name,
            expr=name,
            series=[(r["key"], r["rname"], r["unit"])],
        )
        n = len(r["y"])
        s["time"] = deque(r["t"].tolist(), maxlen=n)
        ser = s["series"][r["key"]]
        ser["data"] = deque(r["y"].tolist(), maxlen=n)
        ser["curve"].setData(r["t"], r["y"])
        self.apply_x_axis()
        self.graph_widget.autoRange()
        self.statusbar.showMessage(f"Serie '{name}' agregada")

    def save_math_result(self):
        r = self._math_result
        if r is None:
            return
        name = self.lineEditNombreSerie.text().strip() or r["name"]
        safe = re.sub(r'[\\/:*?"<>|]', "_", name)
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar serie", os.path.join(self.carpeta_destino, safe + ".csv"),
            "CSV (*.csv)")
        if not path:
            return
        # Encabezado "nombre [unidad]": load_csv_files lo relee con su unidad
        head = name.replace("[", "(").replace("]", ")")
        if r["unit"]:
            head = f"{head} [{r['unit']}]"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Tiempo [s]", head])
            for t, y in zip(r["t"], r["y"]):
                w.writerow([f"{t:.3f}", "nan" if np.isnan(y) else f"{y:.6g}"])
        self.statusbar.showMessage(f"Guardado: {path}")
        
    def send_data(self):
        if self.serial_port and self.serial_port.is_open and self.input_send_widget:
            text = self.input_send_widget.text()
            if text:
                payload = (text + "\r\n").encode("utf-8")
                self.serial_port.write(payload)

                cursor = self.textEdit.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.append_text(f">> {text}\n")
                self.textEdit.setTextCursor(cursor)
                self.textEdit.ensureCursorVisible()

                self.input_send_widget.clear()

    @Slot(str)
    def handle_error(self, error_msg):
        self.statusbar.showMessage(f"Error de lectura: {error_msg}")
        self.disconnect_serial()

    def closeEvent(self, event):
        if self.grabando:
            self.detener_grabacion()
        self.disconnect_serial()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())