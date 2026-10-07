#!/usr/bin/env python3

from pathlib import Path
import sys

APP = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "prueba_integrada_h1.py"
)

RESULTADO = Path(
    "resultados/B2_queue_policy_rpi.txt"
)

RESULTADO.parent.mkdir(
    parents=True,
    exist_ok=True
)

codigo = APP.read_text(
    encoding="utf-8"
)


politicas = {
    "q_preview": {
        "buffers": "max-size-buffers=2",
        "leaky": "leaky=downstream",
        "decision": (
            "Puede perder cuadros antiguos para "
            "mantener la visualizacion reciente."
        ),
    },

    "q_qr": {
        "buffers": "max-size-buffers=2",
        "leaky": "leaky=downstream",
        "decision": (
            "Puede perder cuadros antiguos; "
            "el analisis QR prioriza frames recientes."
        ),
    },

    "q_multimedia": {
        "buffers": "max-size-buffers=8",
        "leaky": "leaky=no",
        "decision": (
            "No debe descartar cuadros antes "
            "de la codificacion H.264."
        ),
    },

    "q_stream": {
        "buffers": "max-size-buffers=2",
        "leaky": "leaky=no",
        "decision": (
            "No descarta cuadros dentro de la queue; "
            "aplica backpressure si se llena."
        ),
    },

    "q_evento_": {
        "buffers": "max-size-buffers=8",
        "leaky": "leaky=no",
        "decision": (
            "La evidencia de grabacion no debe "
            "perder cuadros deliberadamente."
        ),
    },
}


lineas = [
    "B2 - POLITICA DE QUEUES",
    "Modo: Raspberry Pi / pipeline final",
    "",
]

fallos = 0


for nombre, esperado in politicas.items():

    indice = codigo.find(
        f"name={nombre}"
    )

    if indice < 0:
        indice = codigo.find(
            f'"name={nombre}'
        )

    if indice < 0:

        lineas.append(
            f"[FAIL] {nombre}: cola no encontrada."
        )

        fallos += 1
        continue

    bloque = codigo[
        indice:indice + 350
    ]

    buffers_ok = (
        esperado["buffers"] in bloque
    )

    leaky_ok = (
        esperado["leaky"] in bloque
    )

    ok = buffers_ok and leaky_ok

    estado = "PASS" if ok else "FAIL"

    lineas.append(
        f"[{estado}] {nombre}"
    )

    lineas.append(
        f"  {esperado['buffers']}"
    )

    lineas.append(
        f"  {esperado['leaky']}"
    )

    lineas.append(
        f"  Decision: {esperado['decision']}"
    )

    if not ok:
        fallos += 1

    lineas.append("")


if fallos == 0:

    lineas.append(
        "PASS: todas las queues tienen "
        "una politica explicita de perdida/backpressure."
    )

else:

    lineas.append(
        f"FAIL: {fallos} queues no cumplen "
        "la politica esperada."
    )


RESULTADO.write_text(
    "\n".join(lineas) + "\n",
    encoding="utf-8"
)

print(
    "\n".join(lineas)
)

print()
print("Evidencia guardada en:")
print(RESULTADO)

if fallos:
    raise SystemExit(1)

print()
print("========================================")
print(" TEST B2 POLITICA QUEUES: PASS")
print("========================================")
