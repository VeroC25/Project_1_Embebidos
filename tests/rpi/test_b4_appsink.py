#!/usr/bin/env python3

from pathlib import Path
import sys

APP = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "prueba_integrada_h1.py"
)

RESULTADO = Path(
    "resultados/B4_appsink_rpi.txt"
)

RESULTADO.parent.mkdir(
    parents=True,
    exist_ok=True
)

codigo = APP.read_text(
    encoding="utf-8"
)

indice = codigo.find(
    '"appsink "'
)

if indice < 0:
    print("FAIL: no se encontro appsink.")
    raise SystemExit(1)

bloque = codigo[
    indice:indice + 500
]

esperados = [
    "name=sink",
    "emit-signals=true",
    "max-buffers=2",
    "drop=true",
    "sync=false",
]

lineas = [
    "B4 - CONFIGURACION APPSINK",
    "Modo: Raspberry Pi / pipeline final",
    "",
]

fallos = 0

for propiedad in esperados:

    ok = propiedad in bloque

    estado = (
        "PASS"
        if ok
        else "FAIL"
    )

    lineas.append(
        f"[{estado}] {propiedad}"
    )

    if not ok:
        fallos += 1

lineas.append("")


if fallos == 0:

    lineas.append(
        "PASS: appsink tiene limites y "
        "politica de descarte explicitos."
    )

else:

    lineas.append(
        f"FAIL: faltan {fallos} propiedades."
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
print(" TEST B4 APPSINK: PASS")
print("========================================")
