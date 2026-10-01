import gi
import cv2
import numpy as np
import queue
import threading
import time
from datetime import datetime
import signal
import os

from concurrent.futures import ThreadPoolExecutor, TimeoutError

gi.require_version("Gst", "1.0")

from gi.repository import Gst, GLib

MODO = os.getenv("CONTROL_ACCESO_MODE", "rpi").lower()
MOSTRAR_GUI = os.getenv("CONTROL_ACCESO_GUI", "0") == "1"

DEST_HOST = os.getenv("DEST_HOST", "127.0.0.1")
DEST_PORT = os.getenv("DEST_PORT", "5000")

print(f"Modo de ejecución: {MODO}")
print(f"Interfaz gráfica: {'habilitada' if MOSTRAR_GUI else 'deshabilitada'}")
print(f"Destino RTP/UDP: {DEST_HOST}:{DEST_PORT}")

if MODO == "qemu":
    FUENTE_VIDEO = (
        "videotestsrc is-live=true pattern=smpte ! "
        "video/x-raw,width=1280,height=720,framerate=30/1 ! "
    )
else:
    FUENTE_VIDEO = (
        "libcamerasrc ! "
        "video/x-raw,width=1280,height=720,framerate=30/1 ! "
    )

if MOSTRAR_GUI:
    SINK_PREVIEW = "autovideosink sync=false "
else:
    SINK_PREVIEW = "fakesink sync=false "

ENCODER_H264 = (
    "x264enc tune=zerolatency bitrate=2000 "
    "speed-preset=veryfast key-int-max=30 "
    "option-string=scenecut=0 ! "
)

Gst.init(None)

# Cola de entrada hacia el procesamiento QR
cola_frames = queue.Queue(maxsize=2)

# Cola para enviar el frame procesado hacia la interfaz
cola_visual = queue.Queue(maxsize=1)

detener = threading.Event()
# Indica que el pipeline terminó debido a un error fatal
error_fatal = threading.Event()


detector = cv2.QRCodeDetector()

contador = 0
ultimo_codigo = ""
tiempo_callback_total_ns = 0
tiempo_callback_max_ns = 0
callbacks_medidos = 0
TIEMPO_MAX_DECISION = 0.5  # segundos, valor preliminar de prueba

executor_validacion = ThreadPoolExecutor(max_workers=1)
ARCHIVO_BITACORA = "bitacora_accesos.log"


identificadores_autorizados = {
    "MC001"
}

def validar_identificador(identificador):
    return identificador in identificadores_autorizados


def validar_con_timeout(identificador):
    future = executor_validacion.submit(
        validar_identificador,
        identificador
    )

    try:
        autorizado = future.result(
            timeout=TIEMPO_MAX_DECISION
        )

        return autorizado, False

    except TimeoutError:
        return False, True

def nuevo_frame(appsink):
    global contador
    global tiempo_callback_total_ns
    global tiempo_callback_max_ns
    global callbacks_medidos

    inicio_callback = time.perf_counter_ns()

    sample = appsink.emit("pull-sample")

    if sample is None:
        return Gst.FlowReturn.ERROR

    buffer = sample.get_buffer()
    caps = sample.get_caps()
    estructura = caps.get_structure(0)

    width = estructura.get_value("width")
    height = estructura.get_value("height")

    success, map_info = buffer.map(Gst.MapFlags.READ)

    if not success:
        return Gst.FlowReturn.ERROR

    try:
        frame = np.frombuffer(
            map_info.data,
            dtype=np.uint8
        ).reshape((height, width, 3)).copy()

    finally:
        buffer.unmap(map_info)

    contador += 1

    # Mantener el callback rápido.
    # Si la cola está llena, descartamos el frame anterior.
    try:
        cola_frames.put_nowait(frame)

    except queue.Full:
        try:
            cola_frames.get_nowait()
        except queue.Empty:
            pass

        try:
            cola_frames.put_nowait(frame)
        except queue.Full:
            pass

    if contador % 30 == 0:
        print(f"Frames recibidos: {contador}")

    fin_callback = time.perf_counter_ns()
    duracion_ns = fin_callback - inicio_callback

    tiempo_callback_total_ns += duracion_ns
    callbacks_medidos += 1

    if duracion_ns > tiempo_callback_max_ns:
        tiempo_callback_max_ns = duracion_ns

    return Gst.FlowReturn.OK

def registrar_evento(identificador, resultado):
    marca_tiempo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    linea = (
        f"{marca_tiempo} | "
        f"ID: {identificador} | "
        f"RESULTADO: {resultado}\n"
    )

    with open(ARCHIVO_BITACORA, "a", encoding="utf-8") as archivo:
        archivo.write(linea)

    print(f"Evento registrado en {ARCHIVO_BITACORA}")

def procesar_qr():
    global ultimo_codigo

    while not detener.is_set():

        try:
            frame = cola_frames.get(timeout=0.2)

        except queue.Empty:
            continue

        data, puntos, _ = detector.detectAndDecode(frame)

        # Si se detectó un QR, dibujar el contorno
        if puntos is not None:
            puntos = puntos.astype(int).reshape(-1, 2)

            for i in range(len(puntos)):
                p1 = tuple(puntos[i])
                p2 = tuple(puntos[(i + 1) % len(puntos)])

                cv2.line(
                    frame,
                    p1,
                    p2,
                    (0, 255, 0),
                    3
                )

        # Si además se logró decodificar
        if data:

            if puntos is not None:
                x = puntos[0][0]
                y = puntos[0][1] - 15

                cv2.putText(
                    frame,
                    data,
                    (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

            if data != ultimo_codigo:
                print("\nQR detectado:")
                print(data)

                autorizado, timeout = validar_con_timeout(data)

                if timeout:
                    print(
                        f"Tiempo máximo de decisión excedido "
                        f"({TIEMPO_MAX_DECISION:.1f} s)"
                    )
                    print("Resultado: ACCESO DENEGADO POR TIMEOUT")

                    registrar_evento(
                        data,
                        "DENEGADO_TIMEOUT"
                    )

                elif autorizado:
                    print("Resultado: ACCESO AUTORIZADO")

                    registrar_evento(
                        data,
                        "AUTORIZADO"
                    )

                else:
                    print("Resultado: ACCESO DENEGADO")

                    registrar_evento(
                        data,
                        "DENEGADO"
                    )

                print()

                ultimo_codigo = data

        # Entregar el último frame procesado
        try:
            cola_visual.put_nowait(frame)

        except queue.Full:
            try:
                cola_visual.get_nowait()
            except queue.Empty:
                pass

            try:
                cola_visual.put_nowait(frame)
            except queue.Full:
                pass


def mostrar_video():

    if not MOSTRAR_GUI:
        return not detener.is_set()

    try:
        frame = cola_visual.get_nowait()

        cv2.imshow(
            "QR procesado - OpenCV",
            frame
        )

    except queue.Empty:
        pass

    cv2.waitKey(1)

    return not detener.is_set()

def manejar_mensaje(bus, mensaje):
    tipo = mensaje.type

    if tipo == Gst.MessageType.ERROR:
        error, debug = mensaje.parse_error()

        print("\n[GStreamer ERROR]")
        print(f"Origen: {mensaje.src.get_name()}")
        print(f"Error: {error}")

        if debug:
            print(f"Debug: {debug}")

        # Registrar que ocurrió un error fatal.
        error_fatal.set()

        # Salir del bucle principal para iniciar el cierre.
        loop.quit()

    elif tipo == Gst.MessageType.WARNING:
        warning, debug = mensaje.parse_warning()

        print("\n[GStreamer WARNING]")
        print(f"Origen: {mensaje.src.get_name()}")
        print(f"Warning: {warning}")

        if debug:
            print(f"Debug: {debug}")

    elif tipo == Gst.MessageType.EOS:
        print("\n[GStreamer EOS]")
        print("Fin del flujo recibido.")

        loop.quit()

    return True


pipeline = Gst.parse_launch(
    # Fuente de video
    FUENTE_VIDEO +

    "tee name=t "

    # Rama 1: visualización directa
    "t. ! queue leaky=downstream max-size-buffers=2 "
    "max-size-bytes=0 max-size-time=0 ! "
    "videoconvert ! " +
    SINK_PREVIEW +

    # Rama 2: procesamiento QR de la companera
    "t. ! queue leaky=downstream max-size-buffers=2 "
    "max-size-bytes=0 max-size-time=0 ! "
    "videoconvert ! "
    "video/x-raw,format=BGR ! "
    "appsink name=sink "
    "emit-signals=true "
    "max-buffers=2 "
    "drop=true "
    "sync=false "

    # Rama 3: codificacion H.264
    "t. ! queue name=q_multimedia "
    "max-size-buffers=8 max-size-bytes=0 "
    "max-size-time=0 leaky=no ! "
    "videoconvert ! "
    "video/x-raw,format=NV12 ! " +
    ENCODER_H264 +
    "h264parse ! "
    "tee name=tm "

    # Rama 3A: almacenamiento MP4
    "tm. ! queue name=q_grab "
    "max-size-buffers=8 max-size-bytes=0 "
    "max-size-time=0 leaky=no ! "
    "mp4mux ! "
    "filesink location=evidencia_integrada.mp4 "

    # Rama 3B: transmision RTP/UDP
    "tm. ! queue name=q_stream "
    "max-size-buffers=2 max-size-bytes=0 "
    "max-size-time=0 leaky=no ! "
    "rtph264pay pt=96 config-interval=1 ! "
    f"udpsink host={DEST_HOST} port={DEST_PORT} sync=false"
)

appsink = pipeline.get_by_name("sink")
appsink.connect("new-sample", nuevo_frame)
bus = pipeline.get_bus()
bus.add_signal_watch()
bus.connect("message", manejar_mensaje)

hilo_qr = threading.Thread(
    target=procesar_qr,
    daemon=True
)

hilo_qr.start()

# Iniciar el pipeline
pipeline.set_state(Gst.State.PLAYING)

# Esperar a que el pipeline alcance el estado PLAYING
pipeline.get_state(5 * Gst.SECOND)

# Generar el grafo DOT del pipeline integrado
Gst.debug_bin_to_dot_file(
    pipeline,
    Gst.DebugGraphDetails.ALL,
    "pipeline_integrado_PLAYING"
)

loop = GLib.MainLoop()

# Indica que el sistema recibió una solicitud externa de detención.
cierre_solicitado = threading.Event()


# Solicitar la salida del GLib MainLoop de forma segura.
def salir_del_loop():
    loop.quit()
    return False


# Manejar SIGTERM enviado, por ejemplo, por systemd.
def manejar_sigterm(signum, frame):
    print("\nSIGTERM recibido. Iniciando cierre coordinado.")

    cierre_solicitado.set()

    # Ejecutar loop.quit() dentro del contexto de GLib.
    GLib.idle_add(salir_del_loop)


signal.signal(signal.SIGTERM, manejar_sigterm)

# Mostrar el frame procesado desde el hilo principal
GLib.timeout_add(30, mostrar_video)

print("Pipeline iniciado.")
print("Muestra un código QR frente a la cámara.")
print("Presiona Ctrl+C para detenerlo.\n")

try:
    loop.run()

except KeyboardInterrupt:
    print("\nCtrl+C recibido. Iniciando cierre coordinado.")
    cierre_solicitado.set()


# Si la detención fue solicitada mediante Ctrl+C o SIGTERM,
# enviar EOS antes de pasar el pipeline a NULL.
if cierre_solicitado.is_set():
    print("Enviando EOS al pipeline...")

    pipeline.send_event(Gst.Event.new_eos())

    mensaje = bus.timed_pop_filtered(
        5 * Gst.SECOND,
        Gst.MessageType.EOS | Gst.MessageType.ERROR
    )

    if mensaje is None:
        print("No se recibió EOS dentro del tiempo de espera.")

    elif mensaje.type == Gst.MessageType.EOS:
        print("EOS recibido correctamente. Cierre coordinado.")

    elif mensaje.type == Gst.MessageType.ERROR:
        error, debug = mensaje.parse_error()

        print(f"ERROR durante el cierre: {error}")

        if debug:
            print(f"Debug: {debug}")


# Liberar los recursos utilizados por la aplicación.
detener.set()

pipeline.set_state(Gst.State.NULL)

hilo_qr.join(timeout=1)

cv2.destroyAllWindows()

print(f"Total de frames recibidos: {contador}")

if callbacks_medidos > 0:
    promedio_ms = (
        tiempo_callback_total_ns / callbacks_medidos
    ) / 1_000_000

    maximo_ms = tiempo_callback_max_ns / 1_000_000

    print(f"Callbacks medidos: {callbacks_medidos}")
    print(f"Tiempo promedio del callback: {promedio_ms:.3f} ms")
    print(f"Tiempo máximo del callback: {maximo_ms:.3f} ms")


# Si el pipeline terminó debido a un error fatal,
# devolver un código de salida distinto de cero.
# Esto permitirá utilizar Restart=on-failure en systemd.
if error_fatal.is_set():
    print("Terminación por error fatal. Código de salida: 1")
    raise SystemExit(1)

