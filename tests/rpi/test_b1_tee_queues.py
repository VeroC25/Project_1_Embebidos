#!/usr/bin/env python3

from pathlib import Path
import sys

APP = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "prueba_integrada_h1.py"
)

RESULTADO = Path(
    "resultados/B1_tee_queues_rpi.txt"
)

RESULTADO.parent.mkdir(
    parents=True,
    exist_ok=True
)

codigo = APP.read_text(
    encoding="utf-8"
)

pipeline_inicio = codigo.find(
    "pipeline = Gst.parse_launch("
)

pipeline_fin = codigo.find(
    "# ELEMENTOS DEL PIPELINE",
    pipeline_inicio
)

if pipeline_inicio < 0 or pipeline_fin < 0:
    print(
        "FAIL: no se encontro la definicion "
        "del pipeline integrado."
    )
    raise SystemExit(1)

pipeline = codigo[
    pipeline_inicio:pipeline_fin
]

comprobaciones = []

def comprobar(nombre, condicion, detalle):
    comprobaciones.append(
        (nombre, condicion, detalle)
    )


comprobar(
    "Tee principal",
    '"tee name=t "' in pipeline,
    "Existe tee principal t."
)

comprobar(
    "Tres ramas del tee principal",
    pipeline.count('"t. ! "') == 3,
    "El tee principal tiene tres salidas."
)

for cola in (
    "q_preview",
    "q_qr",
    "q_multimedia",
):

    indice = pipeline.find(
        f'"name={cola} "'
    )

    bloque_previo = (
        pipeline[
            max(0, indice - 120):indice
        ]
        if indice >= 0
        else ""
    )

    comprobar(
        cola,
        indice >= 0
        and '"queue "' in bloque_previo,
        f"La rama {cola} comienza con queue."
    )


comprobar(
    "Tee H264",
    '"tee name=tm "' in pipeline,
    "Existe tee multimedia tm."
)

indice_stream = pipeline.find(
    '"name=q_stream "'
)

bloque_stream = (
    pipeline[
        max(0, indice_stream - 120):
        indice_stream
    ]
    if indice_stream >= 0
    else ""
)

comprobar(
    "q_stream",
    indice_stream >= 0
    and '"queue "' in bloque_stream
    and '"tm. ! "' in bloque_stream,
    "La salida permanente de tm comienza con queue."
)


inicio_grabacion = codigo.find(
    "def iniciar_grabacion_evento"
)

fin_grabacion = codigo.find(
    "def detener_grabacion_evento",
    inicio_grabacion
)

bloque_grabacion = codigo[
    inicio_grabacion:fin_grabacion
]

indice_evento = bloque_grabacion.find(
    'f"name=q_evento_"'
)

antes_evento = (
    bloque_grabacion[
        max(0, indice_evento - 100):
        indice_evento
    ]
    if indice_evento >= 0
    else ""
)

comprobar(
    "q_evento",
    indice_evento >= 0
    and 'f"queue "' in antes_evento,
    "La rama dinámica de grabación inicia con queue."
)


lineas = [
    "B1 - TEE Y QUEUES",
    "Modo: Raspberry Pi / pipeline final",
    "",
]

fallos = 0

for nombre, ok, detalle in comprobaciones:

    estado = "PASS" if ok else "FAIL"

    if not ok:
        fallos += 1

    lineas.append(
        f"[{estado}] {nombre}: {detalle}"
    )

lineas.append("")

if fallos == 0:
    lineas.append(
        "PASS: cada salida definida de los tee "
        "entra primero a una queue independiente."
    )
else:
    lineas.append(
        f"FAIL: se encontraron {fallos} "
        "problemas de topologia."
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
print(" TEST B1 TEE/QUEUES: PASS")
print("========================================")
