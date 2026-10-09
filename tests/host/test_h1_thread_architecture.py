#!/usr/bin/env python3

from pathlib import Path
import ast
import sys


APP = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "prueba_integrada_h1.py"
)

RESULTADOS = Path("resultados")
RESULTADOS.mkdir(parents=True, exist_ok=True)

REPORTE = RESULTADOS / "H1_arquitectura_hilos.txt"

codigo = APP.read_text(encoding="utf-8")
arbol = ast.parse(codigo)


def obtener_funcion(nombre):
    for nodo in ast.walk(arbol):
        if (
            isinstance(nodo, ast.FunctionDef)
            and nodo.name == nombre
        ):
            return nodo

    return None


callback = obtener_funcion("nuevo_frame")
procesar_qr = obtener_funcion("procesar_qr")
validar_timeout = obtener_funcion("validar_con_timeout")


if callback is None:
    print("FAIL: no existe nuevo_frame().")
    raise SystemExit(1)

if procesar_qr is None:
    print("FAIL: no existe procesar_qr().")
    raise SystemExit(1)

if validar_timeout is None:
    print("FAIL: no existe validar_con_timeout().")
    raise SystemExit(1)


callback_texto = (
    ast.get_source_segment(
        codigo,
        callback
    )
    or ""
)

qr_texto = (
    ast.get_source_segment(
        codigo,
        procesar_qr
    )
    or ""
)

validacion_texto = (
    ast.get_source_segment(
        codigo,
        validar_timeout
    )
    or ""
)


# ============================================================
# H1.1 - EL CALLBACK SOLO DELEGA EL FRAME
# ============================================================

callback_encola = (
    "cola_frames.put_nowait" in callback_texto
)

callback_no_decide = not any(
    token in callback_texto
    for token in (
        "detector.detectAndDecode",
        "validar_con_timeout(",
        "validar_identificador(",
        "executor_validacion.submit",
    )
)


# ============================================================
# H1.2 - QR CORRE EN HILO INDEPENDIENTE
# ============================================================

hilo_qr_existe = (
    "threading.Thread" in codigo
    and "target=procesar_qr" in codigo
    and "hilo_qr.start()" in codigo
)

qr_consume_cola = (
    "cola_frames.get" in qr_texto
)

qr_hace_deteccion = (
    "detector.detectAndDecode" in qr_texto
)

qr_solicita_validacion = (
    "validar_con_timeout(" in qr_texto
)


# ============================================================
# H1.3 - CLASIFICADOR EN EXECUTOR SEPARADO
# ============================================================

executor_existe = (
    "ThreadPoolExecutor" in codigo
)

validacion_delegada = (
    "executor_validacion.submit" in validacion_texto
    and "validar_identificador" in validacion_texto
)


criterios = [
    (
        "Callback encola frames",
        callback_encola
    ),
    (
        "Callback no ejecuta deteccion ni decision",
        callback_no_decide
    ),
    (
        "Existe hilo QR independiente",
        hilo_qr_existe
    ),
    (
        "Hilo QR consume cola de frames",
        qr_consume_cola
    ),
    (
        "Deteccion QR fuera del callback",
        qr_hace_deteccion
    ),
    (
        "Decision solicitada desde hilo QR",
        qr_solicita_validacion
    ),
    (
        "Existe ThreadPoolExecutor",
        executor_existe
    ),
    (
        "Clasificador delegado al executor",
        validacion_delegada
    ),
]


lineas = [
    "H1 - ARQUITECTURA DE HILOS",
    "",
    "Objetivo:",
    (
        "Demostrar que la decision de acceso no "
        "bloquea el hilo de GStreamer."
    ),
    "",
]


todo_ok = True

for nombre, resultado in criterios:

    estado = (
        "PASS"
        if resultado
        else "FAIL"
    )

    lineas.append(
        f"[{estado}] {nombre}"
    )

    if not resultado:
        todo_ok = False


lineas.extend(
    [
        "",
        "Arquitectura verificada:",
        (
            "GStreamer/appsink -> cola_frames -> "
            "hilo procesar_qr -> "
            "ThreadPoolExecutor -> clasificador"
        ),
        "",
    ]
)


if todo_ok:

    lineas.append(
        "PASS: la decision de acceso corre fuera "
        "del hilo de GStreamer."
    )

else:

    lineas.append(
        "FAIL: la arquitectura no garantiza "
        "separacion del hilo de GStreamer."
    )


REPORTE.write_text(
    "\n".join(lineas) + "\n",
    encoding="utf-8"
)

print("\n".join(lineas))
print()
print(f"Evidencia: {REPORTE}")


if not todo_ok:
    raise SystemExit(1)


print()
print("========================================")
print(" TEST H1 ARQUITECTURA HILOS: PASS")
print("========================================")
