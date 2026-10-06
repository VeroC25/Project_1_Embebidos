#!/usr/bin/env python3

import os
import sys

APP = "prueba_integrada_h1.py"

MODO = sys.argv[1] if len(sys.argv) > 1 else "qemu"
FORMATO_ENCODER = sys.argv[2] if len(sys.argv) > 2 else "NV12"

if MODO not in ("qemu", "rpi"):
    print("Uso:")
    print("  test_a4_capsfilters.py qemu")
    print("  test_a4_capsfilters.py rpi [FORMATO_ENCODER]")
    raise SystemExit(1)

with open(APP, "r", encoding="utf-8") as archivo:
    codigo = archivo.read()

os.makedirs("resultados", exist_ok=True)

ARCHIVO = f"resultados/A4_capsfilters_{MODO}.txt"

resultados = []


def verificar(nombre, texto, justificacion):

    encontrado = texto in codigo

    resultados.append(
        (
            nombre,
            texto,
            justificacion,
            encontrado
        )
    )

    return encontrado


# ============================================================
# CAPS DE FUENTE
# ============================================================

if MODO == "qemu":

    verificar(
        "Fuente simulada",
        "video/x-raw,width=1280,height=720,framerate=30/1",
        "Fija la resolucion y la tasa objetivo para que "
        "las ramas posteriores trabajen con parametros conocidos."
    )

else:

    verificar(
        "Fuente Raspberry Pi",
        "libcamerasrc",
        "Confirma que la fuente final corresponde a la "
        "camara de Raspberry Pi."
    )

    verificar(
        "Resolucion y framerate de captura",
        "video/x-raw,width=1280,height=720,framerate=30/1",
        "Define la resolucion y tasa objetivo de captura "
        "para el pipeline final."
    )


# ============================================================
# RAMA OPENCV
# ============================================================

verificar(
    "Formato para OpenCV",
    "video/x-raw,format=BGR",
    "OpenCV procesa los frames de la rama QR en BGR."
)


# ============================================================
# RAMA DEL ENCODER
# ============================================================

verificar(
    "Formato de entrada al encoder",
    f"video/x-raw,format={FORMATO_ENCODER}",
    "Establece explicitamente un formato de pixel "
    "compatible con la entrada del encoder H.264."
)


# ============================================================
# GENERAR REPORTE
# ============================================================

fallos = 0

lineas = []

lineas.append("A4 - JUSTIFICACION DE CAPSFILTERS")
lineas.append(f"Modo: {MODO}")
lineas.append(f"Formato esperado del encoder: {FORMATO_ENCODER}")
lineas.append("")

for nombre, texto, justificacion, encontrado in resultados:

    estado = "PASS" if encontrado else "FAIL"

    if not encontrado:
        fallos += 1

    lineas.append(f"[{estado}] {nombre}")
    lineas.append(f"Caps/elemento: {texto}")
    lineas.append(f"Justificacion: {justificacion}")
    lineas.append("")


with open(
    ARCHIVO,
    "w",
    encoding="utf-8"
) as archivo:

    archivo.write(
        "\n".join(lineas)
    )


print("\n".join(lineas))

print("Evidencia guardada en:")
print(ARCHIVO)
print()


if fallos > 0:

    print(
        f"FAIL: se encontraron {fallos} "
        "capsfilters/elementos faltantes."
    )

    raise SystemExit(1)


print("========================================")
print(" TEST A4 CAPSFILTERS: PASS")
print("========================================")
