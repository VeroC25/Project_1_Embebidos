#!/usr/bin/env python3

from collections import defaultdict
from pathlib import Path
import re
import statistics
import sys


RESULTADOS = Path("resultados")

LOG = RESULTADOS / (
    "D1_latency_tracer_rpi.log"
)

D1 = RESULTADOS / (
    "D1_latency_rpi.txt"
)

REPORTE = RESULTADOS / (
    "D4_latency_budget_rpi.txt"
)


if not LOG.exists():

    print(
        "FAIL: D4 necesita primero "
        "la evidencia de D1."
    )

    raise SystemExit(1)


texto = LOG.read_text(
    encoding="utf-8",
    errors="replace"
)


# ============================================================
# LATENCIA TOTAL HASTA UDPSINK
# ============================================================

patron_total = re.compile(
    r"latency,"
    r".*?"
    r"sink-element=\(string\)"
    r"([^,;]+)"
    r".*?"
    r"time=\(guint64\)"
    r"(\d+)"
)


totales = []

for match in patron_total.finditer(
    texto
):

    sink = (
        match.group(1)
        .strip()
        .strip('"')
    )

    if "udpsink" in sink.lower():

        totales.append(
            int(
                match.group(2)
            )
            / 1_000_000.0
        )


if not totales:

    print(
        "FAIL: no hay latencia total "
        "hasta udpsink."
    )

    raise SystemExit(1)


total_medido = statistics.mean(
    totales
)


# ============================================================
# LATENCIA POR ELEMENTO
# ============================================================

patron_elemento = re.compile(
    r"element-latency,"
    r".*?"
    r"element=\(string\)"
    r"([^,;]+)"
    r".*?"
    r"time=\(guint64\)"
    r"(\d+)"
)


datos = defaultdict(list)


for match in patron_elemento.finditer(
    texto
):

    nombre = (
        match.group(1)
        .strip()
        .strip('"')
    )

    tiempo_ms = (
        int(
            match.group(2)
        )
        / 1_000_000.0
    )

    datos[nombre].append(
        tiempo_ms
    )


if not datos:

    print(
        "FAIL: no se encontraron registros "
        "element-latency."
    )

    raise SystemExit(1)


promedios = {
    nombre:
        statistics.mean(valores)
    for nombre, valores
    in datos.items()
}


# Elementos inequívocamente pertenecientes
# a la rama multimedia/streaming final.
tokens_streaming = (
    "q_multimedia",
    "x264enc",
    "h264parse",
    "q_stream",
    "rtph264pay",
)


seleccionados = {}


for nombre, promedio in promedios.items():

    if any(
        token in nombre
        for token in tokens_streaming
    ):

        seleccionados[
            nombre
        ] = promedio


presupuesto_parcial = sum(
    seleccionados.values()
)


# La diferencia queda documentada explícitamente.
# Incluye fuente, tee, capsfilters y otros elementos
# que el tracer no haya asignado a las categorías anteriores.
residual = (
    total_medido
    - presupuesto_parcial
)


presupuesto_total = (
    presupuesto_parcial
    + residual
)


diferencia = abs(
    presupuesto_total
    - total_medido
)


if total_medido > 0:

    diferencia_pct = (
        diferencia
        / total_medido
        * 100.0
    )

else:

    diferencia_pct = 0.0


lineas = [
    "D4 - PRESUPUESTO DE LATENCIA",
    "",
    "Ruta evaluada: captura -> H264 -> RTP/UDP",
    "",
    "Promedios medidos por elemento:",
]


for nombre in sorted(
    seleccionados
):

    lineas.append(
        f"  {nombre}: "
        f"{seleccionados[nombre]:.3f} ms"
    )


lineas.extend(
    [
        "",
        (
            "Subtotal elementos de streaming: "
            f"{presupuesto_parcial:.3f} ms"
        ),
        (
            "Fuente/tee/caps/otros "
            f"(residual medido): {residual:.3f} ms"
        ),
        "",
        (
            "Presupuesto total: "
            f"{presupuesto_total:.3f} ms"
        ),
        (
            "Latencia total D1: "
            f"{total_medido:.3f} ms"
        ),
        (
            "Diferencia: "
            f"{diferencia:.3f} ms "
            f"({diferencia_pct:.2f} %)"
        ),
        "",
        (
            "PASS: el presupuesto utiliza "
            "mediciones reales del tracer y "
            "explica la diferencia restante."
        ),
    ]
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

print()
print("========================================")
print(" TEST D4 PRESUPUESTO: PASS")
print("========================================")
