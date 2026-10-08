#!/usr/bin/env python3

from pathlib import Path
import statistics
import sys
import time

import gi

gi.require_version("Gst", "1.0")

from gi.repository import Gst


APP = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "prueba_integrada_h1.py"
)

FPS_REAL = float(
    sys.argv[2]
    if len(sys.argv) > 2
    else "30.0"
)

DURACION = 12

RESULTADOS = Path("resultados")
RESULTADOS.mkdir(
    parents=True,
    exist_ok=True
)

REPORTE = RESULTADOS / (
    "D3_keyframes_rpi.txt"
)


# ============================================================
# VERIFICAR QUE EL GOP ESTE DECLARADO EN LA APLICACION
# ============================================================

codigo = APP.read_text(
    encoding="utf-8"
)


gop_declarado = (
    "key-int-max=30" in codigo
)

scenecut_desactivado = (
    "option-string=scenecut=0"
    in codigo
)


if not (
    gop_declarado
    and scenecut_desactivado
):

    print(
        "FAIL: la configuracion de GOP "
        "no esta declarada explicitamente."
    )

    raise SystemExit(1)


# ============================================================
# INICIAR GSTREAMER
# ============================================================

Gst.init(None)


pipeline_texto = (
    "libcamerasrc ! "
    "video/x-raw,"
    "width=1280,"
    "height=720,"
    "framerate=30/1 ! "

    "videoconvert ! "
    "video/x-raw,format=NV12 ! "

    "x264enc "
    "tune=zerolatency "
    "bitrate=2000 "
    "speed-preset=veryfast "
    "key-int-max=30 "
    "option-string=scenecut=0 ! "

    "h264parse ! "
    "video/x-h264,alignment=au ! "

    "appsink "
    "name=ksink "
    "sync=false "
    "max-buffers=10 "
    "drop=false"
)


try:

    pipeline = Gst.parse_launch(
        pipeline_texto
    )

except Exception as exc:

    print(
        "FAIL: no se pudo construir "
        "el pipeline D3."
    )

    print(exc)

    raise SystemExit(1)


appsink = pipeline.get_by_name(
    "ksink"
)

bus = pipeline.get_bus()


if appsink is None:

    print(
        "FAIL: no se encontro appsink."
    )

    raise SystemExit(1)


# ============================================================
# EJECUTAR Y DETECTAR KEYFRAMES
# ============================================================

print("========================================")
print(" D3 - INTERVALO DE KEYFRAMES")
print("========================================")
print()
print("Configuracion:")
print("  key-int-max=30")
print("  scenecut=0")
print()
print(
    f"FPS real de referencia: "
    f"{FPS_REAL:.3f}"
)
print()


estado = pipeline.set_state(
    Gst.State.PLAYING
)


if estado == Gst.StateChangeReturn.FAILURE:

    print(
        "FAIL: el pipeline no pudo "
        "entrar en PLAYING."
    )

    pipeline.set_state(
        Gst.State.NULL
    )

    raise SystemExit(1)


inicio = time.monotonic()

keyframes = []

frames_totales = 0

error_gstreamer = None


while (
    time.monotonic()
    - inicio
    < DURACION
):

    mensaje = bus.pop_filtered(
        Gst.MessageType.ERROR
    )

    if mensaje is not None:

        error, debug = (
            mensaje.parse_error()
        )

        error_gstreamer = (
            f"{error}: {debug}"
        )

        break


    sample = appsink.emit(
        "try-pull-sample",
        Gst.SECOND
    )


    if sample is None:

        continue


    buffer = sample.get_buffer()

    if buffer is None:

        continue


    frames_totales += 1


    # Un frame H.264 que NO tiene DELTA_UNIT
    # es un keyframe / frame de referencia.
    es_keyframe = not buffer.has_flags(
        Gst.BufferFlags.DELTA_UNIT
    )


    if (
        es_keyframe
        and buffer.pts
        != Gst.CLOCK_TIME_NONE
    ):

        tiempo_s = (
            buffer.pts
            / Gst.SECOND
        )

        keyframes.append(
            tiempo_s
        )


pipeline.set_state(
    Gst.State.NULL
)


if error_gstreamer is not None:

    print(
        "FAIL: GStreamer reporto ERROR."
    )

    print(
        error_gstreamer
    )

    raise SystemExit(1)


if frames_totales == 0:

    print(
        "FAIL: no se recibieron frames."
    )

    raise SystemExit(1)


if len(keyframes) < 3:

    print(
        "FAIL: no se detectaron suficientes "
        "keyframes."
    )

    print(
        f"Frames totales: {frames_totales}"
    )

    print(
        f"Keyframes: {len(keyframes)}"
    )

    raise SystemExit(1)


# ============================================================
# MEDIR INTERVALOS
# ============================================================

intervalos = [
    keyframes[i]
    - keyframes[i - 1]

    for i in range(
        1,
        len(keyframes)
    )
]


promedio = statistics.mean(
    intervalos
)

minimo = min(
    intervalos
)

maximo = max(
    intervalos
)


# GOP = 30 cuadros.
esperado = (
    30.0 / FPS_REAL
)


# Tolerancia del 20 %.
tolerancia = (
    esperado * 0.20
)


intervalo_ok = (
    abs(
        promedio - esperado
    )
    <= tolerancia
)


# ============================================================
# REPORTE
# ============================================================

lineas = [
    "D3 - INTERVALO DE KEYFRAMES",
    "",
    "Plataforma: Raspberry Pi real / Yocto",
    "",
    "Configuracion declarada:",
    "key-int-max=30",
    "scenecut=0",
    "",
    f"FPS real A3: {FPS_REAL:.3f} fps",
    f"GOP declarado: 30 frames",
    (
        "Intervalo esperado: "
        f"{esperado:.3f} s"
    ),
    "",
    f"Duracion prueba: {DURACION} s",
    f"Frames observados: {frames_totales}",
    f"Keyframes detectados: {len(keyframes)}",
    "",
    (
        "Intervalo minimo: "
        f"{minimo:.3f} s"
    ),
    (
        "Intervalo promedio: "
        f"{promedio:.3f} s"
    ),
    (
        "Intervalo maximo: "
        f"{maximo:.3f} s"
    ),
    (
        "Tolerancia: +/- "
        f"{tolerancia:.3f} s"
    ),
    "",
]


if intervalo_ok:

    lineas.append(
        "PASS: el intervalo real de "
        "keyframes coincide con el "
        "GOP declarado."
    )

else:

    lineas.append(
        "FAIL: el intervalo real de "
        "keyframes no coincide con "
        "el GOP declarado."
    )


REPORTE.write_text(
    "\n".join(lineas) + "\n",
    encoding="utf-8"
)


print(
    "\n".join(lineas)
)

print()
print(
    f"Evidencia: {REPORTE}"
)


if not intervalo_ok:

    raise SystemExit(1)


print()
print("========================================")
print(" TEST D3 KEYFRAMES: PASS")
print("========================================")
