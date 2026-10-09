#!/usr/bin/env python3

import gi
import os
import sys
import time

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib

Gst.init(None)

MODO = sys.argv[1] if len(sys.argv) > 1 else "qemu"
DURACION = int(sys.argv[2]) if len(sys.argv) > 2 else 10

os.makedirs("resultados", exist_ok=True)

ARCHIVO = f"resultados/A3_framerate_{MODO}.txt"

if MODO == "qemu":
    FUENTE = (
        "videotestsrc is-live=true pattern=smpte ! "
        "video/x-raw,width=1280,height=720,framerate=30/1 ! "
    )

elif MODO == "rpi":
    FUENTE = (
        "libcamerasrc ! "
        "video/x-raw,width=1280,height=720,framerate=30/1 ! "
    )

else:
    print("Uso:")
    print("  test_a3_framerate.py qemu [segundos]")
    print("  test_a3_framerate.py rpi [segundos]")
    raise SystemExit(1)


pipeline = Gst.parse_launch(
    FUENTE +
    "appsink name=sink "
    "emit-signals=true "
    "max-buffers=2 "
    "drop=true "
    "sync=false"
)

appsink = pipeline.get_by_name("sink")

contador = 0
inicio = None
fin = None
error_detectado = False

loop = GLib.MainLoop()


def nuevo_frame(sink):
    global contador
    global inicio
    global fin

    sample = sink.emit("pull-sample")

    if sample is None:
        return Gst.FlowReturn.ERROR

    ahora = time.perf_counter()

    if inicio is None:
        inicio = ahora

    contador += 1
    fin = ahora

    return Gst.FlowReturn.OK


def manejar_bus(bus, mensaje):
    global error_detectado

    if mensaje.type == Gst.MessageType.ERROR:
        error, debug = mensaje.parse_error()

        print("ERROR GStreamer:", error)

        if debug:
            print("Debug:", debug)

        error_detectado = True
        loop.quit()

    return True


def terminar_prueba():
    loop.quit()
    return False


appsink.connect("new-sample", nuevo_frame)

bus = pipeline.get_bus()
bus.add_signal_watch()
bus.connect("message", manejar_bus)

resultado = pipeline.set_state(Gst.State.PLAYING)

if resultado == Gst.StateChangeReturn.FAILURE:
    print("FAIL: no se pudo iniciar el pipeline.")
    raise SystemExit(1)

resultado_estado, estado, pendiente = pipeline.get_state(
    5 * Gst.SECOND
)

if estado != Gst.State.PLAYING:
    print("FAIL: el pipeline no llego a PLAYING.")
    pipeline.set_state(Gst.State.NULL)
    raise SystemExit(1)

print("========================================")
print(" A3 - FRAMERATE REAL")
print(f" Modo: {MODO}")
print(f" Duracion: {DURACION} s")
print("========================================")
print()
print("Contando cuadros reales...")

GLib.timeout_add_seconds(
    DURACION,
    terminar_prueba
)

loop.run()

pipeline.set_state(Gst.State.NULL)

if error_detectado:
    raise SystemExit(1)

if contador < 2 or inicio is None or fin is None:
    print("FAIL: no se recibieron suficientes cuadros.")
    raise SystemExit(1)

tiempo_real = fin - inicio

fps_real = (contador - 1) / tiempo_real

resultado_texto = (
    f"Modo: {MODO}\n"
    f"Cuadros contados: {contador}\n"
    f"Tiempo medido: {tiempo_real:.3f} s\n"
    f"Framerate real: {fps_real:.3f} fps\n"
)

with open(
    ARCHIVO,
    "w",
    encoding="utf-8"
) as archivo:
    archivo.write(resultado_texto)

print()
print(resultado_texto)

print("Evidencia guardada en:")
print(ARCHIVO)

print()
print("========================================")
print(" TEST A3 FRAMERATE: PASS")
print("========================================")
