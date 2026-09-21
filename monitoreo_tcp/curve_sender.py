"""
curve_sender.py
Replica en Python el envío de curvas de la app MATLAB
(sendCurveFromTable.m + buildChunkLine.m).

Protocolo:
  PC -> ESP32 : '@'                                   (entrar APP_MODE, crudo)
  ESP32 -> PC : 2,APP_MODE_ON*XX
  PC -> ESP32 : CURVE,<id>,<total>,<t>,<v>,<tipo>;...,<CS>\r\n
  PC -> ESP32 : CURVEC,<id>,<t>,<v>,<tipo>;...,<CS>\r\n
  ESP32 -> PC : 2,ACK,<recibidos>,<total>*XX
  ESP32 -> PC : 2,OK,<id>*XX                          (tras el último ACK)
  PC -> ESP32 : '#'                                   (salir APP_MODE, crudo)
"""
import queue
import time

from PySide6.QtCore import QThread, Signal

TIPO_MAP = {"STEP": 0, "LINEAR": 1, "S_CURVE": 2}


# ----------------------------------------------------------------------
# Checksum (XOR de bytes, hex 2 dígitos mayúsculas)
# ----------------------------------------------------------------------
def xor_checksum(payload: str) -> str:
    c = 0
    for b in payload.encode("ascii", errors="replace"):
        c ^= b
    return f"{c:02X}"


def verify_and_strip(line: str):
    """Línea recibida 'payload*XX' -> payload, o None si el checksum es inválido."""
    if "*" not in line:
        return None
    payload, chk = line.rsplit("*", 1)
    return payload if chk.strip().upper() == xor_checksum(payload) else None


def build_chunk_line(cmd: str, curve_id: int, total, pts: str) -> str:
    """Replica buildChunkLine.m -> '<payload>,<CS>\\r\\n'."""
    if total is None:  # CURVEC
        payload = f"{cmd},{curve_id},{pts}"
    else:              # CURVE
        payload = f"{cmd},{curve_id},{total},{pts}"
    return f"{payload},{xor_checksum(payload)}\r\n"


# ----------------------------------------------------------------------
# Hilo emisor
# ----------------------------------------------------------------------
class CurveSenderThread(QThread):
    progress = Signal(str)
    result = Signal(bool, str)   # (éxito, mensaje)

    CHUNK_SIZE = 10
    MAX_RETRIES = 3
    TIMEOUT = 10.0      # s, por respuesta
    RETRY_PAUSE = 0.5   # s, entre reintentos

    def __init__(self, ser, rx_queue, curve_id, data):
        """
        ser      : serial.Serial abierto
        rx_queue : queue.Queue con payloads '2,...' ya verificados
        curve_id : int
        data     : lista de (tiempo:int, valor:int, tipo:str)
        """
        super().__init__()
        self.ser = ser
        self.q = rx_queue
        self.curve_id = curve_id
        self.data = data

    # -- utilidades ----------------------------------------------------
    def _flush(self):
        while True:
            try:
                self.q.get_nowait()
            except queue.Empty:
                break

    def _wait_line(self, prefix: str) -> str:
        """Espera una línea que empiece con prefix (descarta las demás)."""
        end = time.monotonic() + self.TIMEOUT
        while (rem := end - time.monotonic()) > 0:
            try:
                line = self.q.get(timeout=rem)
            except queue.Empty:
                break
            if line.startswith(prefix):
                return line
        return ""

    # -- envío de chunks ------------------------------------------------
    def _send_chunks(self, pts):
        total = len(pts)
        idx, first = 0, True
        msg = "Sin respuesta del dispositivo"

        while idx < total:
            end = min(idx + self.CHUNK_SIZE, total)
            chunk = ";".join(pts[idx:end])
            if first:
                line = build_chunk_line("CURVE", self.curve_id, total, chunk)
            else:
                line = build_chunk_line("CURVEC", self.curve_id, None, chunk)

            chunk_ok = False
            for attempt in range(1, self.MAX_RETRIES + 1):
                self.progress.emit(
                    f"Enviando puntos {idx + 1}-{end} de {total} "
                    f"(intento {attempt}/{self.MAX_RETRIES})"
                )
                self.ser.write(line.encode("ascii"))
                resp = self._wait_line("2,")

                if not resp:
                    msg = f"Sin respuesta del ESP32 en chunk {idx + 1}-{end} (timeout)"
                    time.sleep(self.RETRY_PAUSE)
                    continue

                p = resp.split(",")

                if len(p) >= 2 and p[1] == "ERROR":
                    msg = f"Error reportado por ESP32: {p[2] if len(p) > 2 else ''}"
                    time.sleep(self.RETRY_PAUSE)
                    continue

                if len(p) >= 4 and p[1] == "ACK":
                    try:
                        recv, tot = int(p[2]), int(p[3])
                    except ValueError:
                        msg = f"ACK mal formado: {resp}"
                        time.sleep(self.RETRY_PAUSE)
                        continue

                    if recv != end:
                        msg = f"Desincronización: esperado {end}, ESP32 reportó {recv}"
                        time.sleep(self.RETRY_PAUSE)
                        continue

                    chunk_ok = True
                    if recv == tot:  # último chunk: esperar OK final
                        fin = self._wait_line("2,").split(",")
                        if len(fin) >= 3 and fin[1] == "OK":
                            return True, (f"Curva cargada correctamente. "
                                          f"ID confirmado: {fin[2]}, puntos: {total}")
                        return False, "No se recibió confirmación final (OK) del ESP32"
                    break

                msg = f"Respuesta no reconocida del ESP32: {resp}"
                time.sleep(self.RETRY_PAUSE)

            if not chunk_ok:
                return False, msg

            idx, first = end, False

        return False, msg

    # -- hilo -----------------------------------------------------------
    def run(self):
        ok, msg = False, "Sin respuesta del dispositivo"
        in_app_mode = False
        try:
            pts = [f"{t},{v},{TIPO_MAP[tp]}" for t, v, tp in self.data]
            self._flush()

            self.progress.emit("Activando APP_MODE...")
            self.ser.write(b"@")
            in_app_mode = True

            if not self._wait_line("2,APP_MODE_ON"):
                msg = "No se pudo activar APP_MODE"
            else:
                ok, msg = self._send_chunks(pts)
        except Exception as e:
            ok, msg = False, f"Error inesperado: {e}"
        finally:
            if in_app_mode:
                try:
                    self.ser.write(b"#")  # salir de APP_MODE siempre
                    time.sleep(1)
                except Exception:
                    pass
            self.result.emit(ok, msg)