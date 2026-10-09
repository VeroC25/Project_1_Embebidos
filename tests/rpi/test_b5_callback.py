#!/usr/bin/env python3

from pathlib import Path
import ast
import os
import re
import signal
import subprocess
import sys
import time


APP = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "prueba_integrada_h1.py"
)

DURACION = int(
    sys.argv[2]
    if len(sys.argv) > 2
    else "15"
)

FPS = float(
    sys.argv[3]
    if len(sys.argv) > 3
    else "30.0"
)

RESULTADOS = Path("resultados")

RESULTADOS.mkdir(
    parents=True,
    exist_ok=True
)

REPORTE = RESULTADOS / (
    "B5_callback_rpi.txt"
)

LOG = RESULTADOS / (
    "B5_callback_runtime_rpi.log"
)

codigo = APP.read_text(
    encoding="utf-8"
)


# ============================================================
# COMPROBAR ARQUITECTURA DEL CALLBACK
# ============================================================

arbol = ast.parse(codigo)

funcion_callback = None

for nodo in ast.walk(arbol):

    if (
        isinstance(nodo, ast.FunctionDef)
        and nodo.name == "nuevo_frame"
    ):
        funcion_callback = nodo
        break


if funcion_callback is None:
    print("FAIL: no se encontro nuevo_frame().")
    raise SystemExit(1)


callback_texto = ast.get_source_segment(
    codigo,
    funcion_callback
) or ""


trabajo_delegado = (
    "cola_frames.put_nowait" in callback_texto
    and "target=procesar_qr" in codigo
    and "ThreadPoolExecutor" in codigo
)

trabajo_largo_en_callback = any(
    token in callback_texto
    for token in (
        "validar_con_timeout(",
        "validar_identificador(",
        "detectarAndDecode",
        "QRCodeDetector",
    )
)


# ============================================================
# EJECUCION REAL EN RASPBERRY
# ============================================================

entorno = os.environ.copy()

entorno.update(
    {
        "CONTROL_ACCESO_MODE": "rpi",
        "CONTROL_ACCESO_GUI": "0",
        "CONTROL_ACCESO_GPIO": "0",
        "CONTROL_ACCESO_DATA_DIR":
            "/tmp/b5_control_acceso",
        "DEST_HOST": "127.0.0.1",
        "DEST_PORT": "5000",
        "PYTHONUNBUFFERED": "1",
    }
)

Path(
    "/tmp/b5_control_acceso"
).mkdir(
    parents=True,
    exist_ok=True
)


proceso = subprocess.Popen(
    [
        sys.executable,
        "-u",
        str(APP),
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    env=entorno,
)


time.sleep(DURACION)


if proceso.poll() is not None:

    salida, _ = proceso.communicate()

    LOG.write_text(
        salida,
        encoding="utf-8"
    )

    print(
        "FAIL: la aplicacion termino "
        "antes de completar la medicion."
    )

    print(salida)

    raise SystemExit(1)


proceso.send_signal(
    signal.SIGTERM
)


try:

    salida, _ = proceso.communicate(
        timeout=15
    )

except subprocess.TimeoutExpired:

    proceso.kill()

    salida, _ = proceso.communicate()

    LOG.write_text(
        salida,
        encoding="utf-8"
    )

    print(
        "FAIL: la aplicacion no termino "
        "tras SIGTERM."
    )

    raise SystemExit(1)


LOG.write_text(
    salida,
    encoding="utf-8"
)


m_callbacks = re.search(
    r"Callbacks medidos:\s*(\d+)",
    salida
)

m_promedio = re.search(
    r"Tiempo promedio del callback:\s*"
    r"([0-9.]+)\s*ms",
    salida
)

m_maximo = re.search(
    r"Tiempo maximo del callback:\s*"
    r"([0-9.]+)\s*ms",
    salida
)


if not (
    m_callbacks
    and m_promedio
    and m_maximo
):

    print(
        "FAIL: no se encontraron las "
        "metricas del callback."
    )

    print(salida)

    raise SystemExit(1)


callbacks = int(
    m_callbacks.group(1)
)

promedio_ms = float(
    m_promedio.group(1)
)

maximo_ms = float(
    m_maximo.group(1)
)

periodo_ms = 1000.0 / FPS


# El checklist no define un umbral numérico.
# Como criterio operacional, el promedio debe
# ser menor al período real de un cuadro.
callback_rapido = (
    promedio_ms < periodo_ms
)

arquitectura_ok = (
    trabajo_delegado
    and not trabajo_largo_en_callback
)

proceso_ok = (
    proceso.returncode == 0
)


lineas = [
    "B5 - CALLBACK APPSINK",
    "Medicion real en Raspberry Pi",
    "",
    f"Duracion de prueba: {DURACION} s",
    f"Framerate de referencia: {FPS:.3f} fps",
    f"Periodo por cuadro: {periodo_ms:.3f} ms",
    "",
    f"Callbacks medidos: {callbacks}",
    f"Promedio callback: {promedio_ms:.3f} ms",
    f"Maximo callback: {maximo_ms:.3f} ms",
    "",
    (
        "[PASS] Trabajo QR delegado fuera del callback."
        if arquitectura_ok
        else
        "[FAIL] Trabajo largo detectado dentro del callback."
    ),
    (
        "[PASS] Promedio del callback menor "
        "al periodo de un cuadro."
        if callback_rapido
        else
        "[FAIL] Promedio del callback demasiado alto."
    ),
    (
        "[PASS] Cierre coordinado del proceso."
        if proceso_ok
        else
        f"[FAIL] Codigo de salida: {proceso.returncode}"
    ),
    "",
    (
        "Nota: el maximo se registra como evidencia; "
        "el criterio temporal se aplica al promedio "
        "porque pueden existir picos ocasionales."
    ),
]


ok = (
    arquitectura_ok
    and callback_rapido
    and proceso_ok
    and callbacks > 0
)


if ok:
    lineas.append("")
    lineas.append(
        "PASS: callback corto y procesamiento "
        "largo delegado."
    )
else:
    lineas.append("")
    lineas.append(
        "FAIL: B5 no cumple todos los criterios."
    )


REPORTE.write_text(
    "\n".join(lineas) + "\n",
    encoding="utf-8"
)

print(
    "\n".join(lineas)
)

print()
print("Evidencias:")
print(REPORTE)
print(LOG)

if not ok:
    raise SystemExit(1)

print()
print("========================================")
print(" TEST B5 CALLBACK: PASS")
print("========================================")
