#!/usr/bin/env python3

from pathlib import Path
import sys

APP = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "prueba_integrada_h1.py"
)

FPS = float(
    sys.argv[2]
    if len(sys.argv) > 2
    else "30.0"
)

RESULTADO = Path(
    "resultados/B3_queue_latency_rpi.txt"
)

RESULTADO.parent.mkdir(
    parents=True,
    exist_ok=True
)

if FPS <= 0:
    print("FAIL: FPS invalido.")
    raise SystemExit(1)

codigo = APP.read_text(
    encoding="utf-8"
)

queues = [
    (
        "q_preview",
        2,
        "leaky=downstream"
    ),
    (
        "q_qr",
        2,
        "leaky=downstream"
    ),
    (
        "q_multimedia",
        8,
        "leaky=no"
    ),
    (
        "q_stream",
        2,
        "leaky=no"
    ),
    (
        "q_evento_",
        8,
        "leaky=no"
    ),
]

periodo_ms = 1000.0 / FPS

lineas = [
    "B3 - PROFUNDIDAD Y PRESUPUESTO DE QUEUES",
    f"Framerate real usado: {FPS:.3f} fps",
    f"Periodo por cuadro: {periodo_ms:.3f} ms",
    "",
]

fallos = 0


for nombre, buffers, politica in queues:

    indice = codigo.find(
        f"name={nombre}"
    )

    if indice < 0:
        indice = codigo.find(
            f'"name={nombre}'
        )

    if indice < 0:

        lineas.append(
            f"[FAIL] {nombre}: no encontrada."
        )

        fallos += 1
        continue

    bloque = codigo[
        indice:indice + 350
    ]

    profundidad_ok = (
        f"max-size-buffers={buffers}"
        in bloque
    )

    bytes_ok = (
        "max-size-bytes=0"
        in bloque
    )

    tiempo_ok = (
        "max-size-time=0"
        in bloque
    )

    politica_ok = (
        politica in bloque
    )

    ok = (
        profundidad_ok
        and bytes_ok
        and tiempo_ok
        and politica_ok
    )

    if not ok:
        fallos += 1

    presupuesto_ms = (
        buffers * periodo_ms
    )

    estado = (
        "PASS"
        if ok
        else "FAIL"
    )

    lineas.append(
        f"[{estado}] {nombre}"
    )

    lineas.append(
        f"  Profundidad: {buffers} buffers"
    )

    lineas.append(
        f"  Politica: {politica}"
    )

    lineas.append(
        "  Limites por bytes/tiempo: "
        "deshabilitados"
    )

    lineas.append(
        "  Presupuesto por profundidad "
        f"a {FPS:.3f} fps: "
        f"{presupuesto_ms:.3f} ms"
    )

    lineas.append("")


lineas.append(
    "Nota: este valor es el presupuesto "
    "derivado de profundidad/FPS real, "
    "no una medicion E2E."
)

lineas.append("")


if fallos == 0:

    lineas.append(
        "PASS: todas las queues tienen "
        "profundidad y politica declaradas."
    )

else:

    lineas.append(
        f"FAIL: {fallos} queues no coinciden "
        "con la configuracion esperada."
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
print(" TEST B3 PROFUNDIDAD/LATENCIA: PASS")
print("========================================")
