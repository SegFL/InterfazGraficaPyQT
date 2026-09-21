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
    QLineEdit,
    QTableWidgetItem,
    QComboBox,

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

                        # 1. Trama de datos (arranca con "0,")
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

                        # 2. Menú o texto general para consola
                        else:
                            if line_str:
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

        self.btn_refresh.clicked.connect(self.refresh_ports)
        self.btnIniciar.clicked.connect(self.toggle_connection)
        self.pushButton_2.clicked.connect(self.send_data)

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

        self.curve_plot = pg.PlotWidget()

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

        layout = self.curve_editor.layout()

        if layout is None:
            layout = QVBoxLayout(self.curve_editor)

        layout.addWidget(self.curve_plot)
                    
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
        """Configura el PlotWidget con auto-escalado dinámico en Y para todos los ejes."""
        pg.setConfigOptions(antialias=True)
        self.graph_widget = pg.PlotWidget(title="Telemetría de Sensores - Tiempo Real")
        self.graph_widget.setBackground("#0c0c0c")
        self.graph_widget.showGrid(x=True, y=True, alpha=0.3)
        self.graph_widget.setLabel("bottom", "Tiempo", units="s")
        self.graph_widget.addLegend(offset=(10, 10))

        # Eje Principal (Izquierda) -> Tensión
        self.graph_widget.setLabel("left", "Tensión", units="V", color="#00ffff")

        # Eje Adicional 1 (Derecha) -> Corriente
        self.vb2 = pg.ViewBox()
        self.graph_widget.plotItem.scene().addItem(self.vb2)
        axis2 = pg.AxisItem("right")
        self.graph_widget.plotItem.layout.addItem(axis2, 2, 3)
        axis2.linkToView(self.vb2)
        axis2.setLabel("Corriente", units="mA", color="#ffff00")

        # Eje Adicional 2 (Derecha exterior) -> Potencia
        self.vb3 = pg.ViewBox()
        self.graph_widget.plotItem.scene().addItem(self.vb3)
        axis3 = pg.AxisItem("right")
        self.graph_widget.plotItem.layout.addItem(axis3, 2, 4)
        axis3.linkToView(self.vb3)
        axis3.setLabel("Potencia", units="mW", color="#ff00ff")

        # Sincronización X entre las distintas capas (ViewBoxes)
        self.vb2.setXLink(self.graph_widget.plotItem.vb)
        self.vb3.setXLink(self.graph_widget.plotItem.vb)

        # Habilitar auto-escalado vertical (Eje Y) independiente en cada capa
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

        container_layout = self.layout_plots.layout()
        if container_layout is None:
            container_layout = QVBoxLayout(self.layout_plots)
        container_layout.addWidget(self.graph_widget)

    @Slot(int, float, float, float, float)
    def store_sensor_data(self, sensor_id, t, v1, v2, v3):
        s = self._get_or_create_sensor(sensor_id)
        s["time"].append(t)
        s["tension"].append(v1)
        s["corriente"].append(v2)
        s["potencia"].append(v3)



    def _get_or_create_sensor(self, sensor_id):
        """Inicializa dinámicamente las estructuras de datos y curvas usando el buffer_size actual."""
        if sensor_id not in self.sensors_data:
            # Paleta de colores para cada sensor: (Tensión, Corriente, Potencia)
            color_palette = {
                0: ("#00ffff", "#ffff00", "#ff00ff"),
                1: ("#00ff00", "#ff8800", "#ff0055"),
                2: ("#3388ff", "#ffcc00", "#cc00ff"),
            }

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

            # 1. Crear curva de Tensión (Eje Y principal / Izquierda)
            curve_v = self.graph_widget.plot(pen=pen_tension, name=f"Tensión - {suffix}")

            # 2. Crear curva de Corriente (Eje Y secundario / Derecha 1)
            curve_i = pg.PlotCurveItem(pen=pen_corriente, name=f"Corriente - {suffix}")
            self.vb2.addItem(curve_i)

            # 3. Crear curva de Potencia (Eje Y terciario / Derecha 2)
            curve_p = pg.PlotCurveItem(pen=pen_potencia, name=f"Potencia - {suffix}")
            self.vb3.addItem(curve_p)

            # Guardar estructuras con el buffer_size activo
            self.sensors_data[sensor_id] = {
                "time": deque(maxlen=10000),
                "tension": deque(maxlen=10000),
                "corriente": deque(maxlen=10000),
                "potencia": deque(maxlen=10000),
                "curves": {"v": curve_v, "i": curve_i, "p": curve_p},
            }

        return self.sensors_data[sensor_id]
        
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
                    s["time"] = deque(s["time"], maxlen=self.buffer_size)
                    s["tension"] = deque(s["tension"], maxlen=self.buffer_size)
                    s["corriente"] = deque(s["corriente"], maxlen=self.buffer_size)
                    s["potencia"] = deque(s["potencia"], maxlen=self.buffer_size)

                self.update_plot()
                self.statusbar.showMessage(
                    f"Muestras visibles: {self.buffer_size}"
                )
                return

        # Si el valor no es válido, volver al valor anterior
        self.input_muestras.setText(str(self.buffer_size))

    def update_plot(self):
        """Actualiza las curvas mostrando solamente las últimas buffer_size muestras."""
        if self.is_paused or not self.sensors_data:
            return

        global_t_min = float("inf")
        global_t_max = float("-inf")
        has_data = False

        for s_id, s in self.sensors_data.items():

            if len(s["time"]) < 1:
                continue

            has_data = True

            # Tomar solamente las últimas buffer_size muestras
            times = list(s["time"])[-self.buffer_size:]
            v_data = list(s["tension"])[-self.buffer_size:]
            i_data = list(s["corriente"])[-self.buffer_size:]
            p_data = list(s["potencia"])[-self.buffer_size:]

            # Actualizar curvas
            s["curves"]["v"].setData(times, v_data)
            s["curves"]["i"].setData(times, i_data)
            s["curves"]["p"].setData(times, p_data)

            # Rango temporal mostrado
            if len(times) > 0:
                global_t_min = min(global_t_min, times[0])
                global_t_max = max(global_t_max, times[-1])

        # Ajustar eje X exactamente a las muestras mostradas
        if has_data and global_t_max > global_t_min:
            self.graph_widget.setXRange(
                global_t_min,
                global_t_max,
                padding=0
            )

                    
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

            if tipo not in ("STEP", "LINEAR", "S_CURVE"):
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
                value = float(value_item.text())
            except ValueError:
                continue

            curve_type = type_widget.currentText()

            points.append((t, value, curve_type))

        # Ordenar por tiempo
        points.sort(key=lambda x: x[0])

        if len(points) == 0:
            return [], []

        if len(points) == 1:
            return [points[0][0]], [points[0][1]]

        x = []
        y = []

        for i in range(len(points) - 1):

            t1, v1, tipo = points[i]
            t2, v2, _ = points[i + 1]

            if t2 <= t1:
                continue

            if tipo == "STEP":

                # Valor constante hasta el próximo punto
                x.extend([
                    t1,
                    t2
                ])

                y.extend([
                    v1,
                    v1
                ])

            elif tipo == "LINEAR":

                # Recta entre los dos puntos
                x.extend([
                    t1,
                    t2
                ])

                y.extend([
                    v1,
                    v2
                ])

        # Agregar el último punto
        x.append(points[-1][0])
        y.append(points[-1][1])

        return x, y
    def send_curve(self):

        try:
            data = self.get_curve_data()
        except ValueError as e:
            self.statusbar.showMessage(str(e))
            return

        valid, error = self.validate_curve_data(data)

        if not valid:
            self.statusbar.showMessage(error)
            return

        curve_id = self.spinBoxCurveID.value()

        print("ID:", curve_id)
        print("CURVA:", data)


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