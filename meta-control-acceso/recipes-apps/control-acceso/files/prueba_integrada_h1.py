import gi
import cv2
import numpy as np
import queue
import threading
import time
import os
import signal

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError

gi.require_version("Gst", "1.0")

from gi.repository import Gst, GLib

Gst.init(None)


# ============================================================
# CONFIGURACION GENERAL
# ============================================================

MODO = os.getenv(
    "CONTROL_ACCESO_MODE",
    "rpi"
).lower()

MOSTRAR_GUI = (
    os.getenv(
        "CONTROL_ACCESO_GUI",
        "0"
    )
    == "1"
)

VIDEO_DEVICE = os.getenv(
    "VIDEO_DEVICE",
    "/dev/video0"
)

DEST_HOST = os.getenv(
    "DEST_HOST",
    "127.0.0.1"
)

DEST_PORT = int(
    os.getenv(
        "DEST_PORT",
        "5000"
    )
)

TIEMPO_MAX_DECISION = 10.0
DURACION_EVIDENCIA = 60
TIEMPO_REARME_QR = 3.0
TIEMPO_BLOQUEO_MISMO_QR = 60.0
DIAS_RETENCION_VIDEO = 7
DIAS_RETENCION_BITACORA = 30

# Si la fuente deja de producir cuadros
# durante este tiempo, la cámara se considera
# no operativa y la aplicación termina con error.
TIEMPO_MAX_SIN_FRAMES = 3.0


# ============================================================
# CONTROL DE APERTURA
# ============================================================

TIEMPO_APERTURA = 2.0

GPIO_APERTURA_SYSFS = (
    529
    # GPIO17 BCM = base 512 + 17
)

GPIO_APERTURA_HABILITADO = (
    MODO == "rpi"
    and os.getenv(
        "CONTROL_ACCESO_GPIO",
        "1"
    )
    == "1"
)

RUTA_GPIO_APERTURA = (
    f"/sys/class/gpio/"
    f"gpio{GPIO_APERTURA_SYSFS}"
)

temporizador_apertura = None

bloqueo_gpio = (
    threading.Lock()
)


# ============================================================
# DIRECTORIOS
# ============================================================

DATA_DIR = os.getenv(
    "CONTROL_ACCESO_DATA_DIR",
    os.getcwd()
)

ARCHIVO_BITACORA = os.path.join(
    DATA_DIR,
    "bitacora_accesos.log"
)

CARPETA_EVIDENCIAS = os.path.join(
    DATA_DIR,
    "evidencias"
)

os.makedirs(
    CARPETA_EVIDENCIAS,
    exist_ok=True
)


# ============================================================
# RETENCION DE EVIDENCIAS
# ============================================================

def limpiar_evidencias_antiguas():

    ahora = datetime.now()

    # Evitar borrados si el reloj
    # del sistema aún no es válido.
    if ahora < datetime(
        2026,
        1,
        1
    ):

        print(
            "Limpieza de evidencias omitida: "
            "fecha del sistema no válida."
        )

        return

    eliminadas = 0

    for nombre in os.listdir(
        CARPETA_EVIDENCIAS
    ):

        try:

            fecha_evidencia = (
                datetime.strptime(
                    nombre,
                    (
                        "evidencia_"
                        "%Y-%m-%d_"
                        "%H-%M-%S_%f.mp4"
                    )
                )
            )

        except ValueError:

            continue

        antiguedad = (
            ahora
            - fecha_evidencia
        )

        if (
            antiguedad.total_seconds()
            >= DIAS_RETENCION_VIDEO
            * 86400
        ):

            ruta = os.path.join(
                CARPETA_EVIDENCIAS,
                nombre
            )

            try:

                os.remove(
                    ruta
                )

                eliminadas += 1

                print(
                    "Evidencia eliminada "
                    "por retención: "
                    f"{ruta}"
                )

            except OSError as error:

                print(
                    "No se pudo eliminar "
                    f"{ruta}: {error}"
                )

    if eliminadas > 0:

        print(
            "Total de evidencias "
            f"eliminadas: {eliminadas}"
        )


# ============================================================
# INFORMACION DE ARRANQUE
# ============================================================

print(
    f"Modo de ejecucion: "
    f"{MODO}"
)

print(
    "Interfaz grafica: "
    f"{'habilitada' if MOSTRAR_GUI else 'deshabilitada'}"
)

print(
    f"Destino RTP/UDP: "
    f"{DEST_HOST}:{DEST_PORT}"
)

print(
    f"Directorio de datos: "
    f"{DATA_DIR}"
)


# ============================================================
# RETENCION DE BITACORA
# ============================================================

def limpiar_bitacora_antigua():

    ahora = datetime.now()

    if ahora < datetime(
        2026,
        1,
        1
    ):

        print(
            "Limpieza de bitácora omitida: "
            "fecha del sistema no válida."
        )

        return

    if not os.path.exists(
        ARCHIVO_BITACORA
    ):

        return

    lineas_conservadas = []

    eventos_eliminados = 0

    with open(
        ARCHIVO_BITACORA,
        "r",
        encoding="utf-8"
    ) as archivo:

        for linea in archivo:

            try:

                fecha_evento = (
                    datetime.strptime(
                        linea[:19],
                        "%Y-%m-%d %H:%M:%S"
                    )
                )

            except ValueError:

                # Una línea desconocida
                # se conserva por seguridad.
                lineas_conservadas.append(
                    linea
                )

                continue

            antiguedad = (
                ahora
                - fecha_evento
            )

            if (
                antiguedad.total_seconds()
                >= DIAS_RETENCION_BITACORA
                * 86400
            ):

                eventos_eliminados += 1

            else:

                lineas_conservadas.append(
                    linea
                )

    temporal = (
        ARCHIVO_BITACORA
        + ".tmp"
    )

    with open(
        temporal,
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.writelines(
            lineas_conservadas
        )

    os.replace(
        temporal,
        ARCHIVO_BITACORA
    )

    if eventos_eliminados > 0:

        print(
            "Eventos eliminados de la "
            "bitácora por retención: "
            f"{eventos_eliminados}"
        )


# ============================================================
# CONTROL GPIO DE APERTURA
# ============================================================

def escribir_gpio_apertura(
    valor
):

    if not GPIO_APERTURA_HABILITADO:

        return

    ruta_value = os.path.join(
        RUTA_GPIO_APERTURA,
        "value"
    )

    with open(
        ruta_value,
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(
            "1"
            if valor
            else "0"
        )


def inicializar_gpio_apertura():

    if not GPIO_APERTURA_HABILITADO:

        print(
            "GPIO de apertura: "
            "deshabilitado."
        )

        return

    if not os.path.isdir(
        RUTA_GPIO_APERTURA
    ):

        with open(
            "/sys/class/gpio/export",
            "w",
            encoding="utf-8"
        ) as archivo:

            archivo.write(
                str(
                    GPIO_APERTURA_SYSFS
                )
            )

        for _ in range(20):

            if os.path.isdir(
                RUTA_GPIO_APERTURA
            ):

                break

            time.sleep(
                0.05
            )

    if not os.path.isdir(
        RUTA_GPIO_APERTURA
    ):

        raise RuntimeError(
            "No fue posible exportar "
            "el GPIO de apertura."
        )

    ruta_direction = os.path.join(
        RUTA_GPIO_APERTURA,
        "direction"
    )

    # "low" configura salida y
    # garantiza estado seguro.
    with open(
        ruta_direction,
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(
            "low"
        )

    print(
        "GPIO de apertura preparado: "
        "BCM17 / sysfs 529, "
        "estado LOW."
    )


def desactivar_apertura():

    global temporizador_apertura

    if not GPIO_APERTURA_HABILITADO:

        return

    with bloqueo_gpio:

        if (
            temporizador_apertura
            is not None
        ):

            temporizador_apertura.cancel()

            temporizador_apertura = None

        try:

            escribir_gpio_apertura(
                False
            )

        except OSError as error:

            print(
                "[ERROR GPIO] "
                "No fue posible "
                "desactivar la apertura: "
                f"{error}"
            )

            return

    print(
        "Salida de apertura: "
        "DESACTIVADA"
    )


def activar_apertura():

    global temporizador_apertura

    if not GPIO_APERTURA_HABILITADO:

        return

    with bloqueo_gpio:

        if (
            temporizador_apertura
            is not None
        ):

            temporizador_apertura.cancel()

        try:

            escribir_gpio_apertura(
                True
            )

        except OSError as error:

            print(
                "[ERROR GPIO] "
                "No fue posible activar "
                "la apertura: "
                f"{error}"
            )

            try:

                escribir_gpio_apertura(
                    False
                )

            except OSError:

                pass

            return

        temporizador_apertura = (
            threading.Timer(
                TIEMPO_APERTURA,
                desactivar_apertura
            )
        )

        temporizador_apertura.daemon = (
            True
        )

        temporizador_apertura.start()

    print(
        "Salida de apertura: "
        "ACTIVADA "
        f"durante "
        f"{TIEMPO_APERTURA:.1f} s"
    )


# ============================================================
# FUENTE DE VIDEO
# ============================================================

if MODO == "qemu":

    FUENTE_VIDEO = (
        "videotestsrc "
        "is-live=true "
        "pattern=smpte ! "
        "video/x-raw,"
        "width=1280,"
        "height=720,"
        "framerate=30/1 ! "
    )

elif MODO == "host":

    FUENTE_VIDEO = (
        f"v4l2src "
        f"device={VIDEO_DEVICE} ! "
        "image/jpeg,"
        "width=1280,"
        "height=720,"
        "framerate=30/1 ! "
        "jpegdec ! "
    )

else:

    FUENTE_VIDEO = (
        "libcamerasrc ! "
        "video/x-raw,"
        "width=1280,"
        "height=720,"
        "framerate=30/1 ! "
    )


if MOSTRAR_GUI:

    SINK_PREVIEW = (
        "autovideosink "
        "sync=false "
    )

else:

    SINK_PREVIEW = (
        "fakesink "
        "sync=false "
    )


ENCODER_H264 = (
    "x264enc "
    "tune=zerolatency "
    "bitrate=2000 "
    "speed-preset=veryfast "
    "key-int-max=30 "
    "option-string=scenecut=0 ! "
)


# ============================================================
# COLAS Y EVENTOS
# ============================================================

cola_frames = (
    queue.Queue(
        maxsize=2
    )
)

cola_visual = (
    queue.Queue(
        maxsize=1
    )
)

detener = threading.Event()

error_fatal = threading.Event()

cierre_solicitado = (
    threading.Event()
)


# ============================================================
# QR, METRICAS Y WATCHDOG
# ============================================================

detector = (
    cv2.QRCodeDetector()
)

contador = 0

ultimo_codigo = ""

ultimo_qr_visto_t = 0.0

ultimo_evento_por_codigo = {}


# Momento del último frame válido recibido.
ultimo_frame_monotonic = None

# Momento desde el cual el pipeline
# quedó confirmado en PLAYING.
inicio_pipeline_monotonic = None


tiempo_callback_total_ns = 0

tiempo_callback_max_ns = 0

callbacks_medidos = 0


def permitir_evento_qr(
    codigo
):

    ahora = time.monotonic()

    ultimo_evento = (
        ultimo_evento_por_codigo.get(
            codigo
        )
    )

    if (
        ultimo_evento is not None
        and (
            ahora
            - ultimo_evento
        )
        < TIEMPO_BLOQUEO_MISMO_QR
    ):

        restante = (
            TIEMPO_BLOQUEO_MISMO_QR
            - (
                ahora
                - ultimo_evento
            )
        )

        print(
            "QR repetido ignorado: "
            f"{codigo} "
            f"({restante:.1f} s "
            "restantes)"
        )

        return False

    ultimo_evento_por_codigo[
        codigo
    ] = ahora

    return True


# ============================================================
# VALIDACION
# ============================================================

executor_validacion = (
    ThreadPoolExecutor(
        max_workers=1
    )
)

identificadores_autorizados = {
    "MC001",
    "MC002"
}


def validar_identificador(
    identificador
):

    return (
        identificador
        in identificadores_autorizados
    )


def validar_con_timeout(
    identificador
):

    future = (
        executor_validacion.submit(
            validar_identificador,
            identificador
        )
    )

    try:

        autorizado = future.result(
            timeout=TIEMPO_MAX_DECISION
        )

        return (
            autorizado,
            False
        )

    except TimeoutError:

        return (
            False,
            True
        )


# ============================================================
# CONTROL DE GRABACIONES
# ============================================================

grabaciones_activas = {}

contador_grabaciones = 0


def solicitar_grabacion_evento():

    marca_tiempo = (
        datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S_%f"
        )
    )

    ruta_video = os.path.join(
        CARPETA_EVIDENCIAS,
        (
            "evidencia_"
            f"{marca_tiempo}.mp4"
        )
    )

    GLib.idle_add(
        iniciar_grabacion_evento,
        ruta_video
    )

    return ruta_video


def iniciar_grabacion_evento(
    ruta_video
):

    global contador_grabaciones

    contador_grabaciones += 1

    id_grabacion = (
        contador_grabaciones
    )

    bin_grabacion = None
    tee_pad = None
    sink_pad = None

    descripcion = (
        f"queue "
        f"name=q_evento_"
        f"{id_grabacion} "
        f"max-size-buffers=8 "
        f"max-size-bytes=0 "
        f"max-size-time=0 "
        f"leaky=no ! "
        f"h264parse "
        f"config-interval=-1 ! "
        f"mp4mux "
        f"name=mux_evento_"
        f"{id_grabacion} ! "
        f"filesink "
        f"name=archivo_evento_"
        f"{id_grabacion} "
        f'location="{ruta_video}" '
        f"sync=false"
    )

    try:

        bin_grabacion = (
            Gst.parse_bin_from_description(
                descripcion,
                True
            )
        )

        bin_grabacion.set_name(
            (
                "grabacion_evento_"
                f"{id_grabacion}"
            )
        )

        pipeline.add(
            bin_grabacion
        )

        tee_pad = (
            tm.request_pad_simple(
                "src_%u"
            )
        )

        sink_pad = (
            bin_grabacion
            .get_static_pad(
                "sink"
            )
        )

        if (
            tee_pad is None
            or sink_pad is None
        ):

            raise RuntimeError(
                "No fue posible obtener "
                "los pads de grabacion."
            )

        resultado_link = (
            tee_pad.link(
                sink_pad
            )
        )

        if (
            resultado_link
            != Gst.PadLinkReturn.OK
        ):

            raise RuntimeError(
                "No fue posible enlazar "
                "la rama de grabacion."
            )

        filesink = (
            bin_grabacion.get_by_name(
                (
                    "archivo_evento_"
                    f"{id_grabacion}"
                )
            )
        )

        filesink_pad = (
            filesink.get_static_pad(
                "sink"
            )
        )

        filesink_pad.add_probe(
            (
                Gst.PadProbeType
                .EVENT_DOWNSTREAM
            ),
            detectar_eos_grabacion,
            id_grabacion
        )

        grabaciones_activas[
            id_grabacion
        ] = {
            "bin": bin_grabacion,
            "tee_pad": tee_pad,
            "sink_pad": sink_pad,
            "ruta": ruta_video,
            "probe_bloqueo": None
        }

        if not (
            bin_grabacion
            .sync_state_with_parent()
        ):

            raise RuntimeError(
                "No se pudo sincronizar "
                "la grabacion."
            )

        GLib.timeout_add_seconds(
            DURACION_EVIDENCIA,
            detener_grabacion_evento,
            id_grabacion
        )

        print()

        print(
            "Grabacion de evidencia "
            "iniciada."
        )

        print(
            "Duracion: "
            f"{DURACION_EVIDENCIA} s"
        )

        print(
            f"Archivo: "
            f"{ruta_video}"
        )

        print()

    except Exception as error:

        print()

        print(
            "[ERROR AL INICIAR EVIDENCIA]"
        )

        print(
            error
        )

        if (
            tee_pad is not None
            and sink_pad is not None
            and tee_pad.is_linked()
        ):

            tee_pad.unlink(
                sink_pad
            )

        if tee_pad is not None:

            tm.release_request_pad(
                tee_pad
            )

        if bin_grabacion is not None:

            bin_grabacion.set_state(
                Gst.State.NULL
            )

            try:

                pipeline.remove(
                    bin_grabacion
                )

            except Exception:

                pass

    return False


def detener_grabacion_evento(
    id_grabacion
):

    datos = (
        grabaciones_activas.get(
            id_grabacion
        )
    )

    if datos is None:

        return False

    tee_pad = datos[
        "tee_pad"
    ]

    print()

    print(
        "Se cumplieron "
        f"{DURACION_EVIDENCIA} s "
        "de la evidencia "
        f"{id_grabacion}."
    )

    probe_id = (
        tee_pad.add_probe(
            (
                Gst.PadProbeType
                .BLOCK_DOWNSTREAM
            ),
            bloquear_y_finalizar_grabacion,
            id_grabacion
        )
    )

    datos[
        "probe_bloqueo"
    ] = probe_id

    return False


def bloquear_y_finalizar_grabacion(
    pad,
    info,
    id_grabacion
):

    datos = (
        grabaciones_activas.get(
            id_grabacion
        )
    )

    if datos is None:

        return (
            Gst.PadProbeReturn.REMOVE
        )

    print(
        "Finalizando evidencia "
        f"{id_grabacion}..."
    )

    enviado = (
        datos[
            "bin"
        ].send_event(
            Gst.Event.new_eos()
        )
    )

    if not enviado:

        print(
            "Advertencia: no fue posible "
            "enviar EOS a la grabacion."
        )

    return Gst.PadProbeReturn.OK


def detectar_eos_grabacion(
    pad,
    info,
    id_grabacion
):

    evento = (
        info.get_event()
    )

    if (
        evento is not None
        and evento.type
        == Gst.EventType.EOS
    ):

        GLib.idle_add(
            limpiar_grabacion_evento,
            id_grabacion
        )

    return Gst.PadProbeReturn.OK


def limpiar_grabacion_evento(
    id_grabacion
):

    datos = (
        grabaciones_activas.pop(
            id_grabacion,
            None
        )
    )

    if datos is None:

        return False

    bin_grabacion = datos[
        "bin"
    ]

    tee_pad = datos[
        "tee_pad"
    ]

    sink_pad = datos[
        "sink_pad"
    ]

    probe_bloqueo = (
        datos.get(
            "probe_bloqueo"
        )
    )

    if tee_pad.is_linked():

        tee_pad.unlink(
            sink_pad
        )

    if probe_bloqueo is not None:

        try:

            tee_pad.remove_probe(
                probe_bloqueo
            )

        except Exception:

            pass

    tm.release_request_pad(
        tee_pad
    )

    bin_grabacion.set_state(
        Gst.State.NULL
    )

    pipeline.remove(
        bin_grabacion
    )

    print(
        "Evidencia guardada "
        "correctamente:"
    )

    print(
        datos[
            "ruta"
        ]
    )

    print()

    return False


# ============================================================
# CALLBACK DE VIDEO
# ============================================================

def nuevo_frame(
    appsink
):

    global contador
    global ultimo_frame_monotonic
    global tiempo_callback_total_ns
    global tiempo_callback_max_ns
    global callbacks_medidos

    inicio_callback = (
        time.perf_counter_ns()
    )

    sample = appsink.emit(
        "pull-sample"
    )

    if sample is None:

        return Gst.FlowReturn.ERROR

    # Se recibió un frame válido del pipeline.
    # Esta marca alimenta el watchdog.
    ultimo_frame_monotonic = (
        time.monotonic()
    )

    buffer = (
        sample.get_buffer()
    )

    caps = (
        sample.get_caps()
    )

    estructura = (
        caps.get_structure(
            0
        )
    )

    width = (
        estructura.get_value(
            "width"
        )
    )

    height = (
        estructura.get_value(
            "height"
        )
    )

    success, map_info = (
        buffer.map(
            Gst.MapFlags.READ
        )
    )

    if not success:

        return Gst.FlowReturn.ERROR

    try:

        frame = (
            np.frombuffer(
                map_info.data,
                dtype=np.uint8
            )
            .reshape(
                (
                    height,
                    width,
                    3
                )
            )
            .copy()
        )

    finally:

        buffer.unmap(
            map_info
        )

    contador += 1

    try:

        cola_frames.put_nowait(
            frame
        )

    except queue.Full:

        try:

            cola_frames.get_nowait()

        except queue.Empty:

            pass

        try:

            cola_frames.put_nowait(
                frame
            )

        except queue.Full:

            pass

    if contador % 30 == 0:

        print(
            "Frames recibidos: "
            f"{contador}"
        )

    fin_callback = (
        time.perf_counter_ns()
    )

    duracion_ns = (
        fin_callback
        - inicio_callback
    )

    tiempo_callback_total_ns += (
        duracion_ns
    )

    callbacks_medidos += 1

    if (
        duracion_ns
        > tiempo_callback_max_ns
    ):

        tiempo_callback_max_ns = (
            duracion_ns
        )

    return Gst.FlowReturn.OK


# ============================================================
# BITACORA
# ============================================================

def registrar_evento(
    identificador,
    resultado,
    archivo_video
):

    marca_tiempo = (
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    video_relativo = (
        os.path.relpath(
            archivo_video,
            DATA_DIR
        )
    )

    linea = (
        f"{marca_tiempo} | "
        f"ID: {identificador} | "
        f"RESULTADO: {resultado} | "
        f"EVIDENCIA: "
        f"{video_relativo}\n"
    )

    with open(
        ARCHIVO_BITACORA,
        "a",
        encoding="utf-8"
    ) as archivo:

        archivo.write(
            linea
        )

    print(
        "Evento registrado en "
        f"{ARCHIVO_BITACORA}"
    )

    print(
        "Evidencia asociada: "
        f"{video_relativo}"
    )


# ============================================================
# PROCESAMIENTO QR
# ============================================================

def procesar_qr():

    global ultimo_codigo
    global ultimo_qr_visto_t

    while not detener.is_set():

        try:

            frame = (
                cola_frames.get(
                    timeout=0.2
                )
            )

        except queue.Empty:

            continue

        data, puntos, _ = (
            detector.detectAndDecode(
                frame
            )
        )

        if puntos is not None:

            puntos = (
                puntos.astype(
                    int
                )
                .reshape(
                    -1,
                    2
                )
            )

            for i in range(
                len(
                    puntos
                )
            ):

                p1 = tuple(
                    puntos[
                        i
                    ]
                )

                p2 = tuple(
                    puntos[
                        (
                            i + 1
                        )
                        % len(
                            puntos
                        )
                    ]
                )

                cv2.line(
                    frame,
                    p1,
                    p2,
                    (
                        0,
                        255,
                        0
                    ),
                    3
                )

        if puntos is not None:

            ultimo_qr_visto_t = (
                time.monotonic()
            )

        if data:

            if puntos is not None:

                x = (
                    puntos[
                        0
                    ][
                        0
                    ]
                )

                y = (
                    puntos[
                        0
                    ][
                        1
                    ]
                    - 15
                )

                cv2.putText(
                    frame,
                    data,
                    (
                        x,
                        y
                    ),
                    (
                        cv2
                        .FONT_HERSHEY_SIMPLEX
                    ),
                    0.6,
                    (
                        0,
                        255,
                        0
                    ),
                    2
                )

            if (
                data
                != ultimo_codigo
            ):

                ultimo_codigo = (
                    data
                )

                if not permitir_evento_qr(
                    data
                ):

                    continue

                print()

                print(
                    "QR detectado:"
                )

                print(
                    data
                )

                archivo_video = (
                    solicitar_grabacion_evento()
                )

                autorizado, timeout = (
                    validar_con_timeout(
                        data
                    )
                )

                if timeout:

                    print(
                        "Tiempo maximo "
                        "de decision excedido "
                        f"("
                        f"{TIEMPO_MAX_DECISION:.1f}"
                        " s)"
                    )

                    print(
                        "Resultado: "
                        "ACCESO DENEGADO "
                        "POR TIMEOUT"
                    )

                    resultado = (
                        "DENEGADO_TIMEOUT"
                    )

                elif autorizado:

                    print(
                        "Resultado: "
                        "ACCESO AUTORIZADO"
                    )

                    resultado = (
                        "AUTORIZADO"
                    )

                    activar_apertura()

                else:

                    print(
                        "Resultado: "
                        "ACCESO DENEGADO"
                    )

                    resultado = (
                        "DENEGADO"
                    )

                registrar_evento(
                    data,
                    resultado,
                    archivo_video
                )

                print()

                ultimo_codigo = (
                    data
                )

        else:

            if (
                puntos is None
                and ultimo_codigo
                and (
                    time.monotonic()
                    - ultimo_qr_visto_t
                )
                >= TIEMPO_REARME_QR
            ):

                ultimo_codigo = ""

        try:

            cola_visual.put_nowait(
                frame
            )

        except queue.Full:

            try:

                cola_visual.get_nowait()

            except queue.Empty:

                pass

            try:

                cola_visual.put_nowait(
                    frame
                )

            except queue.Full:

                pass


# ============================================================
# VISUALIZACION
# ============================================================

def mostrar_video():

    if not MOSTRAR_GUI:

        return (
            not detener.is_set()
        )

    try:

        frame = (
            cola_visual.get_nowait()
        )

        cv2.imshow(
            "QR procesado - OpenCV",
            frame
        )

    except queue.Empty:

        pass

    cv2.waitKey(
        1
    )

    return (
        not detener.is_set()
    )


# ============================================================
# WATCHDOG DE CAMARA
# ============================================================

def verificar_watchdog_camara():

    if detener.is_set():

        return False

    if cierre_solicitado.is_set():

        return False

    ahora = (
        time.monotonic()
    )

    # Si ya recibimos al menos un frame,
    # se mide desde ese último frame.
    if (
        ultimo_frame_monotonic
        is not None
    ):

        referencia = (
            ultimo_frame_monotonic
        )

    else:

        # Si todavía no llegó ninguno,
        # se mide desde que el pipeline
        # quedó confirmado en PLAYING.
        referencia = (
            inicio_pipeline_monotonic
        )

    if referencia is None:

        return True

    tiempo_sin_frames = (
        ahora
        - referencia
    )

    if (
        tiempo_sin_frames
        >= TIEMPO_MAX_SIN_FRAMES
    ):

        print()

        print(
            "[WATCHDOG CAMARA]"
        )

        print(
            "No se recibieron frames "
            "durante "
            f"{tiempo_sin_frames:.2f} s."
        )

        print(
            "La fuente de video se "
            "considera no operativa."
        )

        print(
            "Terminando la aplicacion "
            "con error para permitir "
            "la recuperacion por systemd."
        )

        # Fail-secure:
        # antes de abandonar la aplicación,
        # forzar la salida de apertura
        # a su estado seguro.
        desactivar_apertura()

        error_fatal.set()

        loop.quit()

        return False

    return True


# ============================================================
# BUS DE GSTREAMER
# ============================================================

def manejar_mensaje(
    bus,
    mensaje
):

    tipo = (
        mensaje.type
    )

    if (
        tipo
        == Gst.MessageType.ERROR
    ):

        error, debug = (
            mensaje.parse_error()
        )

        print()

        print(
            "[GStreamer ERROR]"
        )

        print(
            "Origen: "
            f"{mensaje.src.get_name()}"
        )

        print(
            f"Error: {error}"
        )

        if debug:

            print(
                f"Debug: {debug}"
            )

        error_fatal.set()

        loop.quit()

    elif (
        tipo
        == Gst.MessageType.WARNING
    ):

        warning, debug = (
            mensaje.parse_warning()
        )

        print()

        print(
            "[GStreamer WARNING]"
        )

        print(
            "Origen: "
            f"{mensaje.src.get_name()}"
        )

        print(
            f"Warning: {warning}"
        )

        if debug:

            print(
                f"Debug: {debug}"
            )

    elif (
        tipo
        == Gst.MessageType.EOS
    ):

        print()

        print(
            "[GStreamer EOS]"
        )

        print(
            "Fin del flujo recibido."
        )

        loop.quit()

    return True


# ============================================================
# PREPARACION INICIAL
# ============================================================

limpiar_evidencias_antiguas()

limpiar_bitacora_antigua()

inicializar_gpio_apertura()


# ============================================================
# PIPELINE
# ============================================================

pipeline = Gst.parse_launch(

    FUENTE_VIDEO +

    "tee name=t "

    # Rama 1: visualizacion
    "t. ! "
    "queue "
    "name=q_preview "
    "leaky=downstream "
    "max-size-buffers=2 "
    "max-size-bytes=0 "
    "max-size-time=0 ! "
    "videoconvert ! " +

    SINK_PREVIEW +

    # Rama 2: QR
    "t. ! "
    "queue "
    "name=q_qr "
    "leaky=downstream "
    "max-size-buffers=2 "
    "max-size-bytes=0 "
    "max-size-time=0 ! "
    "videoconvert ! "
    "video/x-raw,"
    "format=BGR ! "
    "appsink "
    "name=sink "
    "emit-signals=true "
    "max-buffers=2 "
    "drop=true "
    "sync=false "

    # Rama 3: H264
    "t. ! "
    "queue "
    "name=q_multimedia "
    "max-size-buffers=8 "
    "max-size-bytes=0 "
    "max-size-time=0 "
    "leaky=no ! "
    "videoconvert ! "
    "video/x-raw,"
    "format=NV12 ! " +

    ENCODER_H264 +

    "h264parse "
    "config-interval=-1 ! "
    "tee name=tm "

    # Streaming permanente
    "tm. ! "
    "queue "
    "name=q_stream "
    "max-size-buffers=2 "
    "max-size-bytes=0 "
    "max-size-time=0 "
    "leaky=no ! "
    "rtph264pay "
    "pt=96 "
    "config-interval=1 ! "
    f"udpsink "
    f"host={DEST_HOST} "
    f"port={DEST_PORT} "
    "sync=false"
)


# ============================================================
# ELEMENTOS DEL PIPELINE
# ============================================================

appsink = (
    pipeline.get_by_name(
        "sink"
    )
)

tm = (
    pipeline.get_by_name(
        "tm"
    )
)

if appsink is None:

    raise RuntimeError(
        "No se encontro "
        "el appsink."
    )

if tm is None:

    raise RuntimeError(
        "No se encontro "
        "el tee H.264."
    )

appsink.connect(
    "new-sample",
    nuevo_frame
)


# ============================================================
# BUS Y LOOP
# ============================================================

bus = (
    pipeline.get_bus()
)

bus.add_signal_watch()

bus.connect(
    "message",
    manejar_mensaje
)

loop = (
    GLib.MainLoop()
)


# ============================================================
# SIGNALS
# ============================================================

def salir_del_loop():

    loop.quit()

    return False


def manejar_sigterm(
    signum,
    frame
):

    print()

    print(
        "SIGTERM recibido. "
        "Iniciando cierre "
        "coordinado."
    )

    cierre_solicitado.set()

    GLib.idle_add(
        salir_del_loop
    )


signal.signal(
    signal.SIGTERM,
    manejar_sigterm
)


# ============================================================
# HILO QR
# ============================================================

hilo_qr = (
    threading.Thread(
        target=procesar_qr,
        daemon=True
    )
)

hilo_qr.start()


# ============================================================
# INICIAR PIPELINE
# ============================================================

resultado_estado = (
    pipeline.set_state(
        Gst.State.PLAYING
    )
)

if (
    resultado_estado
    == Gst.StateChangeReturn.FAILURE
):

    raise RuntimeError(
        "No fue posible iniciar "
        "el pipeline."
    )


resultado_arranque, \
estado_actual, \
estado_pendiente = (
    pipeline.get_state(
        5 * Gst.SECOND
    )
)


if (
    resultado_arranque
    == Gst.StateChangeReturn.FAILURE
    or estado_actual
    != Gst.State.PLAYING
):

    print()

    print(
        "No fue posible llevar "
        "el pipeline a PLAYING."
    )

    print(
        "Estado alcanzado: "
        f"{estado_actual.value_nick}"
    )

    detener.set()

    pipeline.set_state(
        Gst.State.NULL
    )

    hilo_qr.join(
        timeout=1
    )

    executor_validacion.shutdown(
        wait=False,
        cancel_futures=True
    )

    raise SystemExit(
        1
    )


# A partir de este momento el watchdog
# exige que sigan llegando frames.
inicio_pipeline_monotonic = (
    time.monotonic()
)


# Comprobar cada 500 ms si la cámara
# dejó de producir cuadros.
GLib.timeout_add(
    500,
    verificar_watchdog_camara
)


Gst.debug_bin_to_dot_file(
    pipeline,
    Gst.DebugGraphDetails.ALL,
    "pipeline_integrado_PLAYING"
)


GLib.timeout_add(
    30,
    mostrar_video
)


print()

print(
    "Pipeline iniciado."
)

print(
    "Muestra un codigo QR "
    "frente a la camara."
)

print(
    "Cada evento QR genera "
    "una evidencia de "
    f"{DURACION_EVIDENCIA} "
    "segundos."
)

print(
    "Timeout de decision: "
    f"{TIEMPO_MAX_DECISION:.1f} "
    "segundos."
)

print(
    "Watchdog de camara: "
    f"{TIEMPO_MAX_SIN_FRAMES:.1f} "
    "s sin frames."
)

print(
    "Carpeta de evidencias: "
    f"{CARPETA_EVIDENCIAS}"
)

print(
    "Presiona Ctrl+C "
    "para detenerlo."
)

print()


# ============================================================
# LOOP PRINCIPAL
# ============================================================

try:

    loop.run()

except KeyboardInterrupt:

    print()

    print(
        "Ctrl+C recibido. "
        "Iniciando cierre "
        "coordinado."
    )

    cierre_solicitado.set()


# ============================================================
# CIERRE COORDINADO
# ============================================================

if cierre_solicitado.is_set():

    print(
        "Enviando EOS "
        "al pipeline..."
    )

    pipeline.send_event(
        Gst.Event.new_eos()
    )

    mensaje = (
        bus.timed_pop_filtered(
            5 * Gst.SECOND,
            (
                Gst.MessageType.EOS
                | Gst.MessageType.ERROR
            )
        )
    )

    if mensaje is None:

        print(
            "No se recibio EOS "
            "dentro del tiempo "
            "de espera."
        )

    elif (
        mensaje.type
        == Gst.MessageType.EOS
    ):

        print(
            "EOS recibido correctamente. "
            "Cierre coordinado."
        )

    elif (
        mensaje.type
        == Gst.MessageType.ERROR
    ):

        error, debug = (
            mensaje.parse_error()
        )

        print(
            "ERROR durante "
            f"el cierre: {error}"
        )

        if debug:

            print(
                f"Debug: {debug}"
            )


# ============================================================
# LIBERAR RECURSOS
# ============================================================

# Estado seguro antes de finalizar.
desactivar_apertura()

detener.set()

pipeline.set_state(
    Gst.State.NULL
)

hilo_qr.join(
    timeout=1
)

cv2.destroyAllWindows()

executor_validacion.shutdown(
    wait=False,
    cancel_futures=True
)


# ============================================================
# RESULTADOS
# ============================================================

print()

print(
    "Total de frames recibidos: "
    f"{contador}"
)


if callbacks_medidos > 0:

    promedio_ms = (
        (
            tiempo_callback_total_ns
            / callbacks_medidos
        )
        / 1_000_000
    )

    maximo_ms = (
        tiempo_callback_max_ns
        / 1_000_000
    )

    print(
        "Callbacks medidos: "
        f"{callbacks_medidos}"
    )

    print(
        "Tiempo promedio "
        "del callback: "
        f"{promedio_ms:.3f} ms"
    )

    print(
        "Tiempo maximo "
        "del callback: "
        f"{maximo_ms:.3f} ms"
    )


# ============================================================
# CODIGO DE SALIDA
# ============================================================

if error_fatal.is_set():

    print()

    print(
        "Terminacion por error fatal. "
        "Codigo de salida: 1"
    )

    raise SystemExit(
        1
    )
