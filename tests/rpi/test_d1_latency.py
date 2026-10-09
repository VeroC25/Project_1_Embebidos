#!/usr/bin/env python3

from pathlib import Path
import csv
import os
import re
import signal
import statistics
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
    else "20"
)

RESULTADOS = Path("resultados")
RESULTADOS.mkdir(parents=True, exist_ok=True)

REPORTE = RESULTADOS / "D1_latency_rpi.txt"
LOG = RESULTADOS / "D1_latency_tracer_rpi.log"
CSV = RESULTADOS / "D1_latency_samples_rpi.csv"


entorno = os.environ.copy()

entorno.update(
    {
        "CONTROL_ACCESO_MODE": "rpi",
        "CONTROL_ACCESO_GUI": "0",
        "CONTROL_ACCESO_GPIO": "0",
        "CONTROL_ACCESO_DATA_DIR":
            "/tmp/d1_control_acceso",
        "DEST_HOST": "127.0.0.1",
        "DEST_PORT": "5000",
        "PYTHONUNBUFFERED": "1",

        # Tracer de latencia de GStreamer.
        "GST_TRACERS":
            "latency(flags=pipeline+element)",
        "GST_DEBUG":
            "GST_TRACER:7",
        "GST_DEBUG_NO_COLOR":
            "1",
    }
)


Path(
    "/tmp/d1_control_acceso"
).mkdir(
    parents=True,
    exist_ok=True
)


print("========================================")
print(" D1 - LATENCIA REAL CON GST TRACER")
print("========================================")
print()
print(f"Duracion: {DURACION} s")
print()


with open(
    LOG,
    "w",
    encoding="utf-8"
) as log:

    proceso = subprocess.Popen(
        [
            sys.executable,
            "-u",
            str(APP),
        ],
        stdout=log,
        stderr=subprocess.STDOUT,
        env=entorno,
        text=True,
    )

    time.sleep(DURACION)

    if proceso.poll() is not None:

        print(
            "FAIL: la aplicacion termino "
            "antes de completar D1."
        )

        raise SystemExit(1)

    proceso.send_signal(
        signal.SIGTERM
    )

    try:

        proceso.wait(
            timeout=20
        )

    except subprocess.TimeoutExpired:

        proceso.kill()
        proceso.wait()

        print(
            "FAIL: la aplicacion no termino "
            "correctamente tras SIGTERM."
        )

        raise SystemExit(1)


texto = LOG.read_text(
    encoding="utf-8",
    errors="replace"
)


# Ejemplo de registro esperado:
# latency, ... sink-element=(string)udpsink0,
# time=(guint64)14163000, ...

patron = re.compile(
    r"latency,"
    r".*?"
    r"sink-element=\(string\)"
    r"([^,;]+)"
    r".*?"
    r"time=\(guint64\)"
    r"(\d+)"
)


muestras = []

for match in patron.finditer(texto):

    sink = (
        match.group(1)
        .strip()
        .strip('"')
    )

    tiempo_ns = int(
        match.group(2)
    )

    muestras.append(
        (
            sink,
            tiempo_ns,
        )
    )


# D1 final se enfoca en la rama de streaming.
streaming = [
    tiempo_ns
    for sink, tiempo_ns in muestras
    if "udpsink" in sink.lower()
]


if not streaming:

    print(
        "FAIL: no se encontraron muestras "
        "de latencia hasta udpsink."
    )

    print(
        f"Revisar: {LOG}"
    )

    raise SystemExit(1)


with open(
    CSV,
    "w",
    newline="",
    encoding="utf-8"
) as archivo:

    writer = csv.writer(
        archivo
    )

    writer.writerow(
        [
            "sink",
            "latency_ns",
            "latency_ms",
        ]
    )

    for sink, tiempo_ns in muestras:

        writer.writerow(
            [
                sink,
                tiempo_ns,
                tiempo_ns / 1_000_000.0,
            ]
        )


latencias_ms = [
    valor / 1_000_000.0
    for valor in streaming
]

minimo = min(
    latencias_ms
)

promedio = statistics.mean(
    latencias_ms
)

maximo = max(
    latencias_ms
)


lineas = [
    "D1 - LATENCIA MEDIDA CON GST TRACER",
    "",
    "Plataforma: Raspberry Pi real / Yocto",
    f"Duracion de medicion: {DURACION} s",
    f"Muestras hasta udpsink: {len(latencias_ms)}",
    "",
    f"Latencia minima: {minimo:.3f} ms",
    f"Latencia promedio: {promedio:.3f} ms",
    f"Latencia maxima: {maximo:.3f} ms",
    "",
]


ok = (
    len(latencias_ms) >= 10
    and proceso.returncode == 0
)


if ok:

    lineas.extend(
        [
            "PASS: la latencia fue medida "
            "directamente con GST Tracer.",
            "",
            "No se utilizo una estimacion "
            "teorica para D1.",
        ]
    )

else:

    lineas.append(
        "FAIL: no se obtuvieron suficientes "
        "muestras validas."
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
print(CSV)


if not ok:
    raise SystemExit(1)


print()
print("========================================")
print(" TEST D1 LATENCIA: PASS")
print("========================================")
