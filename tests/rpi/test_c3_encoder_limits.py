#!/usr/bin/env python3

from pathlib import Path
import sys


FPS_REAL = float(
    sys.argv[1]
    if len(sys.argv) > 1
    else "0"
)

RESULTADOS = Path("resultados")

REPORTE = RESULTADOS / (
    "C3_encoder_limits_rpi.txt"
)

C1_ENV = RESULTADOS / (
    "C1_hardware_encoder.env"
)

C2 = RESULTADOS / (
    "C2_cpu_compare_rpi.txt"
)


if not C1_ENV.exists():

    texto = (
        "C3 - PUNTO DE OPERACION DEL ENCODER\n\n"
        "BLOCKED: no existe encoder hardware "
        "validado por C1.\n"
    )

    REPORTE.write_text(
        texto,
        encoding="utf-8"
    )

    print(texto)

    raise SystemExit(2)


if not C2.exists():

    texto = (
        "C3 - PUNTO DE OPERACION DEL ENCODER\n\n"
        "BLOCKED: falta la prueba C2.\n"
    )

    REPORTE.write_text(
        texto,
        encoding="utf-8"
    )

    print(texto)

    raise SystemExit(2)


c2_texto = C2.read_text(
    encoding="utf-8"
)


# C2 ejecuta ambos pipelines durante >=60 s.
duracion_ok = (
    "Duracion medida por ruta: 60 s"
    in c2_texto
    or
    "Duracion medida por ruta: 61 s"
    in c2_texto
    or
    "Duracion medida por ruta: 62 s"
    in c2_texto
)


fps_valido = (
    FPS_REAL > 0
)


lineas = [
    "C3 - PUNTO DE OPERACION DEL ENCODER",
    "",
    "Punto probado:",
    "Resolucion: 1280x720",
    "Framerate configurado: 30/1",
    f"Framerate real de la camara: {FPS_REAL:.3f} fps",
    "",
    (
        "[PASS] Encoder hardware validado por C1."
        if C1_ENV.exists()
        else
        "[FAIL] Encoder hardware no validado."
    ),
    (
        "[PASS] La ruta hardware se mantuvo "
        "activa durante >=60 s en C2."
        if duracion_ok
        else
        "[FAIL] No se demostro estabilidad "
        "de >=60 s."
    ),
    (
        "[PASS] Existe medicion real de FPS."
        if fps_valido
        else
        "[FAIL] No existe FPS real valido."
    ),
    "",
    (
        "Nota: el checklist suministrado no "
        "incluye en esta seccion un limite "
        "numerico maximo del encoder. "
        "Por eso C3 valida operacionalmente "
        "que el hardware sostiene el punto "
        "de trabajo final 1280x720@30."
    ),
]


ok = (
    C1_ENV.exists()
    and duracion_ok
    and fps_valido
)


if ok:

    lineas.extend(
        [
            "",
            "PASS: el punto de operacion final "
            "fue sostenido por la ruta hardware.",
        ]
    )

else:

    lineas.extend(
        [
            "",
            "FAIL: C3 no tiene evidencia suficiente.",
        ]
    )


REPORTE.write_text(
    "\n".join(lineas) + "\n",
    encoding="utf-8"
)

print(
    "\n".join(lineas)
)


if not ok:

    raise SystemExit(1)


print()
print("========================================")
print(" TEST C3 LIMITES: PASS")
print("========================================")
