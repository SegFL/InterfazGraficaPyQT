import sys
import serial
import serial.tools.list_ports
from collections import deque

import pyqtgraph as pg
from PySide6.QtCore import QThread, Signal, Slot, QTimer, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
)

from interfaz_ui import Ui_MainWindow


# ----------------------------------------------------------------------
# HILO DE LECTURA DE PUERTO SERIE (MULTI-SENSOR)
# ----------------------------------------------------------------------
class SerialReaderThread(QThread):
    data_received = Signal(str)
    # Emite: (sensor_id, tiempo_seg, tension, corriente, potencia)
    parsed_data_received = Signal(int, float, float, float, float)
    error_occurred = Signal(str)

    def __init__(self, serial_port):
        super().__init__()
        self.serial_port = serial_port
        self._is_running = True
        self._rx_buffer = ""


    def run(self):
        while self._is_running and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    raw_data = self.serial_port.read(self.serial_port.in_waiting)
                    text = raw_data.decode("utf-8", errors="replace")
                    self._rx_buffer += text

                    while "\n" in self._rx_buffer:
                        line, self._rx_buffer = self._rx_buffer.split("\n", 1)
                        line_str = line.strip()

                        # 1. Si es trama de datos (arranca con "0,"), la parseamos para el gráfico
                        if line_str.startswith("0,"):
                            if "*" in line_str:
                                clean_line = line_str.split("*")[0]
                                parts = clean_line.split(",")

                                if len(parts) >= 5:
                                    try:
                                        time_sec = float(parts[1]) / 1000.0
                                        i_corriente = float(parts[2])
                                        v_tension = float(parts[3])
                                        p_potencia = float(parts[4])

                                        # Obtener sensor_id (último campo antes del checksum)
                                        sensor_id = 0
                                        if len(parts) >= 7 and parts[6].strip().isdigit():
                                            sensor_id = int(parts[6].strip())
                                        elif len(parts) >= 6 and parts[5].strip().isdigit():
                                            sensor_id = int(parts[5].strip())

                                        self.parsed_data_received.emit(
                                            sensor_id, time_sec, v_tension, i_corriente, p_potencia
                                        )
                                    except ValueError:
                                        pass

                        # 2. Si NO es trama de datos (es menú u otro texto), lo mandamos a la consola
                        else:
                            if line_str:  # Evitamos mandar líneas vacías sobrantes
                                self.data_received.emit(line + "\n")

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
    def __init__(self):
        super().__init__()

        self.setupUi(self)

        self.serial_port = None
        self.reader_thread = None
        self.is_paused = False

        self.buffer_size = 200

        # Estilos de trazo por Sensor ID
        self.sensor_styles = {
            0: {"style": Qt.SolidLine, "suffix": "S0 (Solido)"},
            1: {"style": Qt.DashLine, "suffix": "S1 (Punteado)"},
            2: {"style": Qt.DashDotLine, "suffix": "S2 (Raya-Punto)"},
        }

        self.sensors_data = {}

        # Terminal retro
        self.textEdit.setStyleSheet(
            "QTextEdit { background-color: #0d0d0d; color: #00ff00; font-family: Consolas, 'Courier New', monospace; font-size: 11pt; }"
        )

        if self.comboBox_2.count() == 0:
            self.comboBox_2.addItems(["115200", "9600", "57600", "230400"])

        self.input_send_widget = getattr(self, "input_send", None) or getattr(
            self, "lineEdit", None
        )
        self.btn_pause_widget = getattr(self, "btn_pause", None) or getattr(
            self, "pushButton_3", None
        )

        if self.btn_pause_widget:
            self.btn_pause_widget.clicked.connect(self.toggle_pause)

        self._setup_graph()

        self.btn_refresh.clicked.connect(self.refresh_ports)
        self.btnIniciar.clicked.connect(self.toggle_connection)
        self.pushButton_2.clicked.connect(self.send_data)

        if self.input_send_widget:
            self.input_send_widget.returnPressed.connect(self.send_data)

        self.plot_timer = QTimer()
        self.plot_timer.setInterval(33)
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start()

        self.refresh_ports()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.btn_pause_widget:
            if self.is_paused:
                self.btn_pause_widget.setText("Reanudar")
                self.statusbar.showMessage("Gráfico en pausa (inspección de datos)")
            else:
                self.btn_pause_widget.setText("Pausar")
                self.statusbar.showMessage("Gráfico en tiempo real")

    def _setup_graph(self):
        """Configura el PlotWidget con Tensión en el eje izquierdo."""
        pg.setConfigOptions(antialias=True)
        self.graph_widget = pg.PlotWidget(
            title="Telemetría de Sensores - Tiempo Real"
        )
        self.graph_widget.setBackground("#0c0c0c")
        self.graph_widget.showGrid(x=True, y=True, alpha=0.3)
        self.graph_widget.setLabel("bottom", "Tiempo", units="s")
        self.graph_widget.addLegend(offset=(10, 10))

        # EJE Y 1 (Izquierda - Principal) -> Tension
        self.graph_widget.setLabel("left", "Tension", units="V", color="#00ffff")

        # EJE Y 2 (Derecha - Eje adicional 1) -> Corriente
        self.vb2 = pg.ViewBox()
        self.graph_widget.plotItem.scene().addItem(self.vb2)

        axis2 = pg.AxisItem("right")
        self.graph_widget.plotItem.layout.addItem(axis2, 2, 3)
        axis2.linkToView(self.vb2)
        axis2.setLabel("Corriente", units="mA", color="#ffff00")

        # EJE Y 3 (Derecha - Eje adicional 2) -> Potencia
        self.vb3 = pg.ViewBox()
        self.graph_widget.plotItem.scene().addItem(self.vb3)

        axis3 = pg.AxisItem("right")
        self.graph_widget.plotItem.layout.addItem(axis3, 2, 4)
        axis3.linkToView(self.vb3)
        axis3.setLabel("Potencia", units="mW", color="#ff00ff")

        # Sincronización de ejes X
        self.vb2.setXLink(self.graph_widget.plotItem.vb)
        self.vb3.setXLink(self.graph_widget.plotItem.vb)

        def update_views():
            rect = self.graph_widget.plotItem.vb.sceneBoundingRect()
            self.vb2.setGeometry(rect)
            self.vb2.linkedViewChanged(self.graph_widget.plotItem.vb, self.vb2.XAxis)

            self.vb3.setGeometry(rect)
            self.vb3.linkedViewChanged(self.graph_widget.plotItem.vb, self.vb3.XAxis)

        self.graph_widget.plotItem.vb.sigResized.connect(update_views)
        update_views()

        self.graph_widget.disableAutoRange(axis=pg.ViewBox.XAxis)

        container_layout = self.layout_plots.layout()
        if container_layout is None:
            container_layout = QVBoxLayout(self.layout_plots)
        container_layout.addWidget(self.graph_widget)

    def _get_or_create_sensor(self, sensor_id):
            """Crea curvas dinámicas con colores diferenciados por cada sensor."""
            if sensor_id not in self.sensors_data:
                # Paleta de colores diferenciada por Sensor ID
                # Formato: {sensor_id: (color_v, color_i, color_p)}
                color_palette = {
                    0: ("#00ffff", "#ffff00", "#ff00ff"),  # S0: Cian, Amarillo, Magenta
                    1: ("#00ff00", "#ff8800", "#ff0055"),  # S1: Verde, Naranja, Rosa
                    2: ("#3388ff", "#ffcc00", "#cc00ff"),  # S2: Azul, Amarillo claro, Violeta
                }

                # Si se conecta un sensor > 2, asigna colores por defecto
                c_v, c_i, c_p = color_palette.get(
                    sensor_id, ("#ffffff", "#aaaaaa", "#777777")
                )

                style_cfg = self.sensor_styles.get(
                    sensor_id, {"style": Qt.SolidLine, "suffix": f"S{sensor_id}"}
                )
                line_style = style_cfg["style"]
                suffix = style_cfg["suffix"]

                pen_tension = pg.mkPen(color=c_v, width=2, style=line_style)
                pen_corriente = pg.mkPen(color=c_i, width=2, style=line_style)
                pen_potencia = pg.mkPen(color=c_p, width=2, style=line_style)

                # Tension -> Vista Principal (Izquierda)
                curve_v = self.graph_widget.plot(pen=pen_tension, name=f"Tensión - {suffix}")

                # Corriente -> Vista 2 (Derecha 1)
                curve_i = pg.PlotCurveItem(pen=pen_corriente, name=f"Corriente - {suffix}")
                self.vb2.addItem(curve_i)

                # Potencia -> Vista 3 (Derecha 2)
                curve_p = pg.PlotCurveItem(pen=pen_potencia, name=f"Potencia - {suffix}")
                self.vb3.addItem(curve_p)

                self.sensors_data[sensor_id] = {
                    "time": deque(maxlen=self.buffer_size),
                    "tension": deque(maxlen=self.buffer_size),
                    "corriente": deque(maxlen=self.buffer_size),
                    "potencia": deque(maxlen=self.buffer_size),
                    "curves": {"v": curve_v, "i": curve_i, "p": curve_p},
                }

            return self.sensors_data[sensor_id]

    @Slot(int, float, float, float, float)
    def store_sensor_data(self, sensor_id, t, v1, v2, v3):
        s = self._get_or_create_sensor(sensor_id)
        s["time"].append(t)
        s["tension"].append(v1)
        s["corriente"].append(v2)
        s["potencia"].append(v3)

    def update_plot(self):
        if self.is_paused or not self.sensors_data:
            return

        global_t_min = float("inf")
        global_t_max = float("-inf")

        all_v, all_i, all_p = [], [], []

        for s_id, s in self.sensors_data.items():
            if len(s["time"]) > 1:
                times = list(s["time"])
                v_data = list(s["tension"])
                i_data = list(s["corriente"])
                p_data = list(s["potencia"])

                s["curves"]["v"].setData(times, v_data)
                s["curves"]["i"].setData(times, i_data)
                s["curves"]["p"].setData(times, p_data)

                global_t_min = min(global_t_min, times[0])
                global_t_max = max(global_t_max, times[-1])

                all_v.extend(v_data)
                all_i.extend(i_data)
                all_p.extend(p_data)

        margin = 1.1

        # Tensión en eje izquierdo
        if all_v:
            y1_min_fijo = -1.0
            max_v = max(all_v)
            y1_max = max(max_v * margin, y1_min_fijo + 1.0)
            self.graph_widget.plotItem.vb.setYRange(y1_min_fijo, y1_max, padding=0)

        # Corriente en eje derecho 1
        if all_i:
            y2_min_fijo = 0.0
            max_i = max(all_i)
            y2_max = max(max_i * margin, y2_min_fijo + 1.0)
            self.vb2.setYRange(y2_min_fijo, y2_max, padding=0)

        # Potencia en eje derecho 2
        if all_p:
            y3_min_fijo = -5.0
            max_p = max(all_p)
            y3_max = max(max_p * margin, y3_min_fijo + 1.0)
            self.vb3.setYRange(y3_min_fijo, y3_max, padding=0)

        if global_t_max > global_t_min:
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
            for s_id, s in self.sensors_data.items():
                s["curves"]["v"].clear()
                s["curves"]["i"].clear()
                s["curves"]["p"].clear()
            self.sensors_data.clear()

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

    @Slot(str)
    def append_text(self, text):
        cursor = self.textEdit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self.textEdit.setTextCursor(cursor)
        self.textEdit.ensureCursorVisible()

    def send_data(self):
        if self.serial_port and self.serial_port.is_open and self.input_send_widget:
            text = self.input_send_widget.text()
            if text:
                payload = (text + "\r\n").encode("utf-8")
                self.serial_port.write(payload)

                cursor = self.textEdit.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                cursor.insertText(f">> {text}\n")
                self.textEdit.setTextCursor(cursor)
                self.textEdit.ensureCursorVisible()

                self.input_send_widget.clear()

    @Slot(str)
    def handle_error(self, error_msg):
        self.statusbar.showMessage(f"Error de lectura: {error_msg}")
        self.disconnect_serial()

    def closeEvent(self, event):
        self.disconnect_serial()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())