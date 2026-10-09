#!/usr/bin/env python3

from pathlib import Path
import sys


if len(sys.argv) != 3:

    print(
        "Uso:"
    )

    print(
        "python3 test_d2_e2e_manual.py "
        "<tiempo_real_s> <tiempo_recibido_s>"
    )

    print()
    print(
        "Ejemplo:"
    )

    print(
        "python3 test_d2_e2e_manual.py "
        "98.82 98.62"
    )

    raise SystemExit(1)


real = float(
    sys.argv[1]
)

recibido = float(
    sys.argv[2]
)


latencia_ms = abs(
    real - recibido
) * 1000.0


RESULTADOS = Path("resultados")

RESULTADOS.mkdir(
    parents=True,
    exist_ok=True
)

REPORTE = RESULTADOS / (
    "D2_e2e_manual_rpi.txt"
)


lineas = [
    "D2 - LATENCIA EXTREMO A EXTREMO",
    "",
    "Metodo independiente:",
    "cronometro visible frente a la camara",
    "y comparacion con la imagen recibida.",
    "",
    f"Tiempo real observado: {real:.3f} s",
    f"Tiempo recibido observado: {recibido:.3f} s",
    f"Latencia E2E: {latencia_ms:.1f} ms",
    "",
    "PASS: existe una medicion E2E "
    "independiente del GST Tracer.",
    "",
    "La fotografia/video usado para obtener "
    "estos valores debe conservarse como evidencia.",
]


REPORTE.write_text(
    "\n".join(lineas) + "\n",
    encoding="utf-8"
)


print(
    "\n".join(lineas)
)

print()
print(
    f"Evidencia textual: {REPORTE}"
)
